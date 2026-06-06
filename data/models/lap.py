from dataclasses import dataclass
from enum import Enum
from typing import Optional

class CompoundType(Enum):
    SOFT = 0
    MEDIUM = 1
    HARD = 2
    INTERMEDIATE = 3
    WET = 4

class TrackStatus(Enum):
    GREEN = 1
    YELLOW = 2
    SAFETY_CAR = 4
    RED_FLAG = 5
    VIRTUAL_SC = 6
    @property
    def is_slow_down(self):
        return self in(
            TrackStatus.self.SAFETY_CAR,TrackStatus.self.VIRTUAL_SC)

@dataclass
class Lap:
    driver: str
    lap_number: int
    lap_time_s: Optional[float]

    compound: CompoundType
    tyre_age: int

    position: float
    gap_behind_s: float
    gap_ahead_s: float
    gap_to_leader_s: float

    track_status: TrackStatus
    
    pitted: bool = False
    pit_time_s: Optional[float] = None
    lap_delta_s: float = 0.0
    pit_window: int = 0
