
from env.tyre_model import TyreModel
from env.traffic_model import TrafficModel
from env.pit_model import PitModel


class RaceBackend:
    def __init__(self, data):

        self.fastest_lap = float("inf")

        self.base_track_time = data["base_time"]
       
        
        self.tyre_model = TyreModel(data)
        self.traffic_model = TrafficModel()
        self.pit_model  = PitModel(data)

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
        
        base_time = self.base_track_time[tyre_compound]
      

        fuel_time_penalty = 0.035 * 100 * (1 - (current_lap / total_laps))

        tyre_degradation_penalty = self.tyre_model.degradation(
            tyre_compound,
            tyre_age
        )

        pit_loss = 0.0
        if pitted: pit_loss = self.pit_model.get_loss(safety_car)



        traffic_loss = self.traffic_model.get_traffic_loss(
            gap_ahead,
            current_lap
        )

        lap_time = (
            base_time
            + tyre_degradation_penalty
            + fuel_time_penalty
            + pit_loss
            + traffic_loss
        )

        if safety_car:
            lap_time *= 1.35

        self.fastest_lap = min(self.fastest_lap, lap_time)
        lap_delta = lap_time - self.fastest_lap

        return lap_time, lap_delta