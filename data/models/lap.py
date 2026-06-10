from dataclasses import dataclass
from enum import Enum
from typing import Optional

class CompoundType(Enum):
    SOFT = 0
    MEDIUM = 1
    HARD = 2
    INTERMEDIATE = 3
    WET = 4
    UNKNOWN = -1
class TrackStatus(Enum):
    GREEN = 1
    YELLOW = 2
    SAFETY_CAR = 3
    RED_FLAG = 5
    VIRTUAL_SC = 6
    UNKNOWN = 0

    @property
    def is_slow_zone(self) -> bool:
        return self in(TrackStatus.SAFETY_CAR, TrackStatus.VIRTUAL_SC)
    
@dataclass
class Lap:
    driver: str
    lap_number: int
    lap_time_s: Optional[float]

    compound_type: CompoundType
    tyre_age: int
    
    position: int

    gap_behind_s: float
    gap_ahead_s: float
    gap_to_leader_s: float

    track_status: TrackStatus

    pitted: bool = False
    pit_time_s: Optional[float] = None
    lap_delta_s: float = 0.0

    pit_window: bool = False

    total_laps: int = 78

    @property
    def laps_remaining(self) -> int:
        return max(0, self.total_laps - self.lap_number)
    
    @property
    def safety_car_flag(self) -> bool:
        return self.track_status.is_slow_zone
    
    @property
    def is_valid(self)  -> bool:
        if self.lap_time_s is None:
            return False
        return 60.0<=self.lap_time_s <=300.0
    
    def __repr__(self) -> str:
        t   = f"{self.lap_time_s:.3f}s" if self.lap_time_s is not None else "N/A"
        sc  = " SC!"  if self.safety_car_flag else ""
        pit = " PIT"  if self.pitted else ""
        win = " WIN"  if self.pit_window else ""
        return (
            f"Lap({self.lap_number} {self.driver} | "
            f"{self.compound.name}/{self.tyre_age}L | "
            f"{t} | P{self.position} | "
            f"delta={self.lap_delta_s:.2f}s | "
            f"gap={self.gap_to_leader_s:.1f}s | "
            f"ahd={self.gap_ahead_s:.1f}s | "
            f"bhd={self.gap_behind_s:.1f}s"
            f"{sc}{pit}{win})"
        )