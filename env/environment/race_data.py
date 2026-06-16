from dataclasses import dataclass
from typing import Dict, List

@dataclass
class EnvironmentRaceData:
    track_name: str
    year: int
    total_laps: int
    drivers: List[str]

    pit_loss_time_s: float
    pit_window_start: int 
    pit_window_end: int

    lap_times_by_lap: Dict[int, Dict[str, float]]
    positions_by_lap: Dict[int, Dict[str, int]]
    safety_car_by_lap: Dict[int, bool]
    pit_window_by_lap: Dict[int, Dict[str, bool]]