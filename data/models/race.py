from dataclasses import dataclass, field
from typing import Dict, List, Optional 
from .lap import Lap

@dataclass
class TrackInfo:
    name: str
    total_laps: int
    pit_loss_time_s: float          
    pit_window_start: int = 15      
    pit_window_end: int = 45       
 
TRACK_CONFIG: Dict[str, TrackInfo] = {
    "Monaco": TrackInfo(
        name = "Monaco",
        total_laps = 78,
        pit_loss_time_s = 24.0,   
        pit_window_start = 25,      
        pit_window_end = 55,
    ),
    "Monza": TrackInfo(
        name = "Monza",
        total_laps = 53,
        pit_loss_time_s = 22.0,   
        pit_window_start = 15,
        pit_window_end = 35,
    ),
    "Silverstone": TrackInfo(
        name   = "Silverstone",
        total_laps  = 52,
        pit_loss_time_s = 23.0,
        pit_window_start = 18,
        pit_window_end  = 35,
    ),
}
  
@dataclass
class Race:
    track: TrackInfo
    year: int
    laps_by_driver:  Dict[str, List[Lap]] = field(default_factory=dict)

    @property
    def drivers(self) -> List[str]:
        return list(self.laps_by_driver.keys())
 
    @property
    def total_laps(self) -> int:
        return self.track.total_laps
    def get_driver_laps(self, driver: str) -> List[Lap]:
        return self.laps_by_driver.get(driver, [])
 
    def get_valid_laps(self, driver: str) -> List[Lap]:
        return [lap for lap in self.get_driver_laps(driver) if lap.is_valid]
 
    def get_best_lap_time(self, driver: str) -> Optional[float]:
        valid = self.get_valid_laps(driver)
        if not valid:
            return None
        return min(lap.lap_time_s for lap in valid)
 
    def get_position_map(self, lap_number: int) -> Dict[int, str]:
        pos_map: Dict[int, str] = {}
        for driver, laps in self.laps_by_driver.items():
            for lap in laps:
                if lap.lap_number == lap_number:
                    pos_map[lap.position] = driver
                    break
        return pos_map
 
    def __repr__(self) -> str:
        total = sum(len(v) for v in self.laps_by_driver.values())
        return (
            f"Race({self.year} {self.track.name} | "
            f"{len(self.drivers)} drivers | "
            f"{total} laps)"
        )
 