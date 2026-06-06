from dataclasses import dataclass , field
from typing import Optional,Dict,List
from .lap import Lap

@dataclass
class TrackInfo:
    name: str
    total_laps: int
    pit_loss_time_s: float

TRACK_CONFIG = {
    "Monaco": TrackInfo("Monaco",78,24.0),
    "Monza": TrackInfo("Monza",53,22.0),
    "Silverstone": TrackInfo("Silverstone",52,23.0)
}

@dataclass
class Race:
    track: TrackInfo
    year: int
    laps_by_driver: Dict[str,List[Lap]]= field(default_factory = dict)

    @property
    def drivers(self):
        return list(self.laps_by_driver.keys())
    def get_driver_laps(self,driver):
        return self.laps_by_driver.get(driver, [])
    def get_valid_laps(self, driver):
        return [
            lap
            for lap in self.get_driver_laps(driver)
            if lap.lap_time_s is not None
        ]
