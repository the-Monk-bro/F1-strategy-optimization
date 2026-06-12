import os
import logging 
from typing import Dict, List
import pandas as pd

try:
    import fastf1
    FASTF1_AVAILABLE = True
except ImportError:
    FASTF1_AVAILABLE = False

from data.models.lap import Lap, CompoundType, TrackStatus
from data.models.race import Race, TrackInfo, TRACK_CONFIGS
from data.config import CACHE_DIR, VALIDATION

logger = logging.getLogger(__name__)

COMPOUND_MAP: Dict[str, CompoundType] = {
    "SOFT":         CompoundType.SOFT,
    "MEDIUM":       CompoundType.MEDIUM,
    "HARD":         CompoundType.HARD,
    "INTERMEDIATE": CompoundType.INTERMEDIATE,
    "WET":          CompoundType.WET,
    
    "SUPERSOFT":    CompoundType.SOFT,
    "ULTRASOFT":    CompoundType.SOFT,
    "HYPERSOFT":    CompoundType.SOFT,

    "C1": CompoundType.HARD,
    "C2": CompoundType.HARD,
    "C3": CompoundType.MEDIUM,
    "C4": CompoundType.SOFT,
    "C5": CompoundType.SOFT,
}
 
STATUS_MAP: Dict[str, TrackStatus] = {
    "1": TrackStatus.GREEN,
    "2": TrackStatus.YELLOW,
    "4": TrackStatus.SAFETY_CAR,
    "5": TrackStatus.RED_FLAG,
    "6": TrackStatus.VIRTUAL_SC,
}

class FastF1DataSource:
 
    def __init__(self, cache_dir: str = CACHE_DIR):
        if not FASTF1_AVAILABLE:
            raise RuntimeError(
                "FastF1 is not installed.\n"
                "Run: pip install fastf1"
            )
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)
        logger.info(f"FastF1DataSource ready. Cache at: {cache_dir}")
 
 
    def load_race(self, track_name: str, year: int) -> Race:
        if track_name not in TRACK_CONFIGS:
            raise ValueError(
                f"Unknown track: '{track_name}'\n"
                f"Available: {list(TRACK_CONFIGS.keys())}"
            )
        if not (2018 <= year <= 2023):
            raise ValueError(
                f"Year {year} out of range. Supported: 2018-2023."
            )
 
        track_info = TRACK_CONFIGS[track_name]
        logger.info(f"Loading {year} {track_name}...")

        raw_session = self._fetch_session(track_name, year)
 
        laps_by_driver = self._convert_all_drivers(raw_session, track_info)

        race = Race(
            track          = track_info,
            year           = year,
            laps_by_driver = laps_by_driver,
        )
        logger.info(f"Loaded: {race}")
        return race
 
 
    def _fetch_session(self, track_name: str, year: int):
        try:
            session = fastf1.get_session(year, track_name, "R")
            session.load(
                laps      = True,  
                telemetry = False,  
                weather   = False,  
                messages  = False,  
            )
            return session
        except Exception as e:
            raise RuntimeError(
                f"Failed to load {year} {track_name} from FastF1.\n"
                f"Error: {e}\n"
                f"Check: internet connection and FastF1 installation."
            ) from e
 
    def _convert_all_drivers(
        self,
        raw_session,
        track_info: TrackInfo,
    ) -> Dict[str, List[Lap]]:
        all_laps_df = raw_session.laps
        drivers = all_laps_df["Driver"].unique()
        result: Dict[str, List[Lap]] = {}
 
        for driver in drivers:
            
            driver_df = (
                all_laps_df[all_laps_df["Driver"] == driver]
                .copy()
                .sort_values("LapNumber")
                .reset_index(drop=True)
            )
            laps = self._convert_driver_laps(driver_df, driver, track_info)
            if laps:
                result[driver] = laps
                logger.debug(f"  {driver}: {len(laps)} laps converted")
 
        return result
 
    def _convert_driver_laps(
        self,
        df: pd.DataFrame,
        driver: str,
        track_info: TrackInfo,
    ) -> List[Lap]:
        laps = []
        for _, row in df.iterrows():
            try:
                lap = self._row_to_lap(row, driver, track_info)
                laps.append(lap)
            except Exception as e:
                lap_n = row.get("LapNumber", "?")
                logger.warning(f"Skipping lap {lap_n} for {driver}: {e}")
        return laps

    
    def _row_to_lap(
        self,
        row: pd.Series,
        driver: str,
        track_info: TrackInfo,
    ) -> Lap:
        
        lt = row.get("LapTime")
        lap_time_s = lt.total_seconds() if pd.notna(lt) else None
 
        cpd = str(row.get("Compound", "")).strip().upper()
        compound = COMPOUND_MAP.get(cpd, CompoundType.UNKNOWN)
 
        status = str(row.get("TrackStatus", "1")).strip()
        track_status = STATUS_MAP.get(status, TrackStatus.UNKNOWN)
 
        pit_in  = row.get("PitInTime")
        pit_out = row.get("PitOutTime")
        pitted  = pd.notna(pit_in)
 
        pit_time_s = None
        if pitted and pd.notna(pit_out) and pd.notna(pit_in):
            raw = (pit_out - pit_in).total_seconds()
           
            if VALIDATION["MIN_PIT_TIME_S"] <= raw <= VALIDATION["MAX_PIT_TIME_S"]:
                pit_time_s = raw

 
        return Lap(
            driver          = driver,
            lap_number      = self._safe_int(row.get("LapNumber"), default=1),
            total_laps      = track_info.total_laps,
            lap_time_s      = lap_time_s,
            compound_type   = compound,
            tyre_age        = self._safe_int(row.get("TyreLife"), default= 0),
            position        =self._safe_int(row.get("Position"), default=20),
            track_status    = track_status,
            pitted          = pitted,
            pit_time_s      = pit_time_s,
           
            gap_to_leader_s = 0.0,
            gap_ahead_s     = 999.0,
            gap_behind_s    = 999.0,
            
            lap_delta_s     = 0.0,
            pit_window      = False,
        )



    @staticmethod    
    def _safe_int( value, default: int = 0) -> int:
        if pd.isna(value):
            return default
        try:
            return int(value)
        except(TypeError, ValueError):
            return default
    

 