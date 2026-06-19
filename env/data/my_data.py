import fastf1
import pandas as pd
import numpy as np
from collections import defaultdict


class F1TrackDataLoader:

    TRACKS = {
        "Monaco": "Monaco Grand Prix",
        "Monza": "Italian Grand Prix",
        "Silverstone": "British Grand Prix"
    }

    COMPOUND_MAP = {
        "SOFT": 0,
        "MEDIUM": 1,
        "HARD": 2
    }

    def __init__(self):
        fastf1.Cache.enable_cache("env/data/my_cache")

    def get_race_data(self, track: str, year: int):

        session = fastf1.get_session(
            year,
            self.TRACKS[track],
            "R"
        )

        session.load(
            laps=True,
            telemetry=False,
            weather=False,
            messages=True
        )

        laps = session.laps.copy()
        starting_grid = self._get_starting_grid(session)

        return {
            "starting_grid":
                starting_grid,

            "safety_car":
                self._get_safety_car_flags(session),

            "lap_times":
                self._get_lap_times(laps, starting_grid),

            "tyre_loss":
                self._get_tyre_degradation(laps),

            "pit_loss":
                self._get_average_pit_loss(laps),

            "base_time":
                self._get_base_time(laps),

            "max_laps":
                int(laps["LapNumber"].max()) if len(laps) > 0 else 70,

            "total_drivers":
                len(starting_grid) if starting_grid else laps["Driver"].nunique()
        }

    # --------------------------------------------------
    # STARTING GRID
    # --------------------------------------------------

    def _get_starting_grid(self, session):

        grid = session.results.sort_values("GridPosition")

        return grid["Abbreviation"].tolist()

    # --------------------------------------------------
    # SAFETY CAR
    # --------------------------------------------------

    def _get_safety_car_flags(self, session):

        max_laps = int(session.laps["LapNumber"].max())

        sc_flags = [False] * (max_laps + 1)

        race_control = session.race_control_messages

        if race_control is None:
            return sc_flags

        for _, msg in race_control.iterrows():

            txt = str(msg["Message"]).upper()

            if "SAFETY CAR DEPLOYED" in txt:

                lap = int(msg["Lap"])

                if lap <= max_laps:
                    sc_flags[lap] = True

        return sc_flags

    # --------------------------------------------------
    # LAP TIMES
    # --------------------------------------------------

    def _get_lap_times(self, laps, starting_grid=None):

        drivers_set = set(laps["Driver"].dropna().unique())
        if starting_grid is not None:
            drivers_set.update(starting_grid)
        drivers = sorted(list(drivers_set))

        max_laps = int(laps["LapNumber"].max()) if len(laps) > 0 else 0

        lap_dict = {}

        lap_dict[0] = {
            d: 0.0
            for d in drivers
        }

        for lap_no in range(1, max_laps + 1):

            lap_dict[lap_no] = {}

            current = laps[
                laps["LapNumber"] == lap_no
            ]

            for d in drivers:

                driver_lap = current[
                    current["Driver"] == d
                ]

                if len(driver_lap):

                    t = driver_lap.iloc[0]["LapTime"]

                    if pd.notna(t):
                        lap_dict[lap_no][d] = (
                            t.total_seconds()
                        )

        return lap_dict

    # --------------------------------------------------
    # TYRE DEGRADATION
    # --------------------------------------------------

    def _get_tyre_degradation(self, laps):
        # Determine maximum tyre age to populate (limit_age)
        max_laps = int(laps["LapNumber"].max()) if len(laps) > 0 else 70
        max_tyre_life = int(laps["TyreLife"].max()) if "TyreLife" in laps and len(laps) > 0 else 0
        limit_age = max(max_laps, max_tyre_life, 10)
        fuel_burn_per_lap = 3.5 / max_laps if max_laps > 0 else 0.05

        # Helper function to generate default/fallback curve up to limit_age
        def get_default_curve(compound, limit):
            if compound == "SOFT":
                base = {1:0.00, 2:0.03, 3:0.07, 4:0.12, 5:0.18, 6:0.25, 7:0.34, 8:0.45, 9:0.58, 10:0.73}
                last_diff = 0.15
            elif compound == "MEDIUM":
                base = {1:0.00, 2:0.02, 3:0.05, 4:0.09, 5:0.14, 6:0.20, 7:0.27, 8:0.35, 9:0.44, 10:0.54}
                last_diff = 0.10
            else: # HARD
                base = {1:0.00, 2:0.01, 3:0.03, 4:0.05, 5:0.08, 6:0.11, 7:0.15, 8:0.19, 9:0.24, 10:0.30}
                last_diff = 0.06
                
            curve = {}
            for age in range(1, limit + 1):
                if age <= 10:
                    curve[age] = base[age]
                else:
                    curve[age] = base[10] + (age - 10) * last_diff
            return curve

        deg = {}
        for compound in ["SOFT", "MEDIUM", "HARD"]:
            compound_id = self.COMPOUND_MAP[compound]
            subset = laps[laps["Compound"] == compound].copy()
            
            # 1. Extract all clean laps
            d_clean = subset.dropna(subset=["LapTime", "TrackStatus", "IsAccurate", "TyreLife"])
            d_clean = d_clean[(d_clean["TrackStatus"] == "1") & (d_clean["IsAccurate"] == True)]
            
            default_curve = get_default_curve(compound, limit_age)
            increases_by_age = defaultdict(list)
            
            # 2. Group by Driver and Stint
            for (driver, stint), d_group in d_clean.groupby(["Driver", "Stint"]):
                if len(d_group) < 2:
                    continue
                
                # Make a working copy and get lap times in seconds
                d_stint = d_group.copy()
                d_stint["LapTimeSec"] = d_stint["LapTime"].dt.total_seconds()
                
                # Robustly filter out outlier lap times in this stint (within 5.0 seconds of the median)
                median_time = d_stint["LapTimeSec"].median()
                d_stint_filtered = d_stint[np.abs(d_stint["LapTimeSec"] - median_time) < 5.0]
                
                if len(d_stint_filtered) < 2:
                    continue
                
                # Group by TyreLife and compute the median lap time for each tyre age in this stint
                d_stint_filtered = d_stint_filtered.sort_values("TyreLife")
                stint_by_age = d_stint_filtered.groupby("TyreLife")["LapTimeSec"].median()
                
                # Determine minimum age in clean laps for anchoring
                min_age = min(stint_by_age.keys())
                
                # 3. Anchor the stint if min_age is reasonably small (e.g. <= 4)
                if min_age <= 4:
                    base_time = stint_by_age[min_age]
                    default_offset = default_curve[min_age]
                    for age, time_val in stint_by_age.items():
                        raw_increase = time_val - base_time
                        # Fuel burn correction between min_age and age
                        fuel_correction = (age - min_age) * fuel_burn_per_lap
                        increases_by_age[int(age)].append(raw_increase + fuel_correction + default_offset)
            
            # Aggregate across all drivers and stints
            known_ages = [1]
            known_values = [0.0]
            
            for age in sorted(increases_by_age.keys()):
                if age <= 1:
                    continue
                samples = increases_by_age[age]
                # Require at least 2 samples for robust averaging
                if len(samples) >= 2:
                    avg_increase = float(np.median(samples))
                    known_ages.append(age)
                    known_values.append(avg_increase)
            
            # Fallback check: need at least 2 known ages, positive final value and slope
            is_fallback = False
            if len(known_ages) < 2:
                is_fallback = True
            else:
                max_known_age = known_ages[-1]
                slope = known_values[-1] / (max_known_age - 1)
                if known_values[-1] < 0.05 or slope < 0.002:
                    is_fallback = True
            
            if is_fallback:
                deg[compound_id] = default_curve
                continue
            
            # Build the complete curve for all ages from 1 to limit_age
            compound_curve = {}
            max_known_age = known_ages[-1]
            extrap_slope = max(0.005, known_values[-1] / (max_known_age - 1))
            
            for age in range(1, limit_age + 1):
                if age == 1:
                    compound_curve[age] = 0.0
                elif age <= max_known_age:
                    val = float(np.interp(age, known_ages, known_values))
                    # Enforce non-decreasing
                    compound_curve[age] = max(compound_curve[age - 1], val)
                else:
                    compound_curve[age] = compound_curve[max_known_age] + (age - max_known_age) * extrap_slope
                    
            deg[compound_id] = compound_curve
            
        return deg
            
     

    # --------------------------------------------------
    # PIT LOSS
    # --------------------------------------------------

    def _get_average_pit_loss(self, laps):
        pit_losses = []
        
        for driver in laps["Driver"].unique():
            d = laps[laps["Driver"] == driver].copy()
            d = d.sort_values("LapNumber")
            
            # Normal laps: accurate, not pit-in/out, green track status
            normal_laps = d[
                pd.isna(d["PitInTime"]) & 
                pd.isna(d["PitOutTime"]) & 
                (d["IsAccurate"] == True) & 
                pd.notna(d["LapTime"])
            ]
            
            if len(normal_laps) == 0:
                normal_laps = d[pd.notna(d["LapTime"])]
                
            if len(normal_laps) == 0:
                continue
                
            avg_lap_time = normal_laps["LapTime"].dt.total_seconds().mean()
            
            for i in range(1, len(d)):
                prev = d.iloc[i - 1]
                curr = d.iloc[i]
                
                # Check for pit stop: curr is pit-out, prev is pit-in
                if pd.notna(curr["PitOutTime"]) and pd.notna(prev["PitInTime"]):
                    if pd.notna(curr["LapTime"]) and pd.notna(prev["LapTime"]):
                        pit_time = curr["LapTime"].total_seconds() + prev["LapTime"].total_seconds()
                        pit_loss = pit_time - 2 * avg_lap_time
                        pit_losses.append(max(0.0, pit_loss))
                        
        if len(pit_losses) > 0:
            return float(np.mean(pit_losses))
            
        return 20.0

    # --------------------------------------------------
    # BASE TIME
    # --------------------------------------------------

    def _get_base_time(self, laps):
        # Overall fallback base time
        all_times = laps["LapTime"].dropna()
        all_times = all_times.dt.total_seconds().values
        if len(all_times) > 0:
            all_times = np.sort(all_times)
            k = max(1, int(len(all_times) * 0.10))
            overall_base = float(np.mean(all_times[:k]))
        else:
            overall_base = 80.0

        base_times = {}
        
        for compound_name, compound_id in self.COMPOUND_MAP.items():
            comp_laps = laps[laps["Compound"] == compound_name].copy()
            
            # Ensure LapTime, TrackStatus, TyreLife, IsAccurate are not NaN
            comp_laps = comp_laps.dropna(subset=["LapTime", "TrackStatus", "TyreLife", "IsAccurate"])
            
            # Fresh tyre flying laps without disturbance (TrackStatus == '1' and IsAccurate == True)
            fresh_no_disturb = comp_laps[
                (comp_laps["TrackStatus"] == "1") & 
                (comp_laps["IsAccurate"] == True) & 
                (comp_laps["TyreLife"] <= 3)
            ]
            
            times = fresh_no_disturb["LapTime"].dt.total_seconds().values
            
            if len(times) > 0:
                base_times[compound_id] = float(np.mean(times))
                continue
                
            # Fallback 1: Relax TyreLife to <= 5
            fresh_no_disturb_5 = comp_laps[
                (comp_laps["TrackStatus"] == "1") & 
                (comp_laps["IsAccurate"] == True) & 
                (comp_laps["TyreLife"] <= 5)
            ]
            times = fresh_no_disturb_5["LapTime"].dt.total_seconds().values
            if len(times) > 0:
                base_times[compound_id] = float(np.mean(times))
                continue
                
            # Fallback 2: Any accurate lap of that compound with TrackStatus == '1'
            any_no_disturb = comp_laps[
                (comp_laps["TrackStatus"] == "1") & 
                (comp_laps["IsAccurate"] == True)
            ]
            times = any_no_disturb["LapTime"].dt.total_seconds().values
            if len(times) > 0:
                times = np.sort(times)
                k = max(1, int(len(times) * 0.20))
                base_times[compound_id] = float(np.mean(times[:k]))
                continue
                
            # Fallback 3: Any accurate lap of that compound
            any_accurate = comp_laps[comp_laps["IsAccurate"] == True]
            times = any_accurate["LapTime"].dt.total_seconds().values
            if len(times) > 0:
                times = np.sort(times)
                k = max(1, int(len(times) * 0.20))
                base_times[compound_id] = float(np.mean(times[:k]))
                continue
                
            # Fallback 4: Overall base time
            base_times[compound_id] = overall_base

        return base_times

  
   








