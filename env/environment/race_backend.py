from tyre_model import TyreModel
from traffic_model import TrafficModel


class RaceBackend:
    def __init__(
        self,
        track_name: str,
        pit_loss_time_s: float,
        base_track_time_s: float | None = None,
    ):
        self.track_name = track_name
        self.pit_loss_time_s = pit_loss_time_s
        self.fastest_lap = float("inf")

        # Temporary MVP values.
        # Later, calculate base time from data-layer lap times.
        default_base_track_time = {
            "Monaco": 70.8,
            "Monza": 79.6,
            "Silverstone": 86.8,
        }

        if base_track_time_s is not None:
            self.base_track_time_s = base_track_time_s
        else:
            self.base_track_time_s = default_base_track_time[self.track_name]

        # Compound offsets:
        # 0 = soft, 1 = medium, 2 = hard
        self.compound_offset_s = {
            0: -0.8,
            1: 0.0,
            2: 0.9,
        }

        self.sc_multiplier = 1.35

        self.tyre_model = TyreModel()
        self.traffic_model = TrafficModel()

    def simulated_lap_time(
        self,
        current_lap: int,
        tyre_compound: int,
        tyre_age: int,
        total_laps: int,
        pitted: bool,
        gap_ahead: float,
        safety_car: bool,
    ) -> tuple[float, float]:
        base_time = (
            self.base_track_time_s
            + self.compound_offset_s[tyre_compound]
        )

        fuel_time_penalty = 0.035 * 100 * (1 - (current_lap / total_laps))

        tyre_degradation_penalty = self.tyre_model.degradation(
            tyre_compound,
            tyre_age,
        )

        pit_loss = 0.0
        if pitted:
            pit_loss = self.pit_loss_time_s

            if safety_car:
                pit_loss *= 0.5

        traffic_loss = self.traffic_model.get_traffic_loss(
            gap_ahead,
            current_lap,
        )

        lap_time = (
            base_time
            + tyre_degradation_penalty
            + fuel_time_penalty
            + pit_loss
            + traffic_loss
        )

        if safety_car:
            lap_time *= self.sc_multiplier

        self.fastest_lap = min(self.fastest_lap, lap_time)
        lap_delta = lap_time - self.fastest_lap

        return lap_time, lap_delta