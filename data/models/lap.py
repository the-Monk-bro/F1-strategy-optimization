from dataclasses import dataclass, field
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
    SAFETY_CAR= 4
    RED_FLAG  = 5
    VIRTUAL_SC = 6
    UNKNOWN = 0

    @property 
    def is_slow_zone(self)-> bool:
        return self in (TrackStatus.SAFETY_CAR,TrackStatus.VIRTUAL_SC)
@dataclass
class Lap:
    driver:          str                # e.g. "VER", "HAM", "LEC"
    lap_number:      int                # 1, 2, 3 ... up to total_laps
    lap_time_s:      Optional[float]    # seconds, e.g. 83.456. None if aborted.
 
    compound:        CompoundType       # SOFT / MEDIUM / HARD / INTER / WET
    tyre_age:        int                # how many laps on this exact set
 
    position:        int                # 1=leader, 20=last               ← FIXED
 
    gap_behind_s:    float              # seconds to car directly behind you
    gap_ahead_s:     float              # seconds to car directly in front of you
    gap_to_leader_s: float              # seconds behind the race leader (0 if P1)
 
    track_status:    TrackStatus        # GREEN / SAFETY_CAR / VIRTUAL_SC / etc.

 
    pitted:       bool           = False  # did this car pit on THIS lap?
    pit_time_s:   Optional[float] = None  # pit stop duration in seconds (None = no pit)
    lap_delta_s:  float           = 0.0  # how much slower than driver's best lap
 
    pit_window:   bool            = False  # is this a good lap to pit?   ← FIXED
 
    total_laps:   int             = 78    # total laps in this race        ← ADDED
 
    @property
    def laps_remaining(self) -> int:
        return max(0, self.total_laps - self.lap_number)
 
    @property
    def safety_car_flag(self) -> bool:
        return self.track_status.is_slow_zone
 
    @property
    def is_valid(self) -> bool:
        if self.lap_time_s is None:
            return False
        return 60.0 <= self.lap_time_s <= 300.0
 
    def __repr__(self) -> str:
        t   = f"{self.lap_time_s:.3f}s" if self.lap_time_s else "N/A"
        sc  = " SC!"  if self.safety_car_flag else ""
        pit = " PIT"  if self.pitted else ""
        win = " WIN"  if self.pit_window else ""
        return (
            f"Lap({self.lap_number} {self.driver} | "
            f"{self.compound.name}/{self.tyre_age}L | "
            f"{t} | P{self.position} | "
            f"Δ={self.lap_delta_s:.2f}s | "
            f"gap={self.gap_to_leader_s:.1f}s | "
            f"ahd={self.gap_ahead_s:.1f}s | "
            f"bhd={self.gap_behind_s:.1f}s"
            f"{sc}{pit}{win})"
        )
