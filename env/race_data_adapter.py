from typing import Dict

from data.racerepository.race_repository import RaceRepository
from data.models.race import Race
from race_data import EnvironmentRaceData


class RaceDataAdapter:
    def __init__(self, repository: RaceRepository):
        self.repository = repository

    def load(self, track_name: str, year: int) -> EnvironmentRaceData:
        race = self.repository.get_race(track_name, year)
        return self._convert_race(race)

    def _convert_race(self, race: Race) -> EnvironmentRaceData:
        lap_times_by_lap: Dict[int, Dict[str, float]] = {}
        positions_by_lap: Dict[int, Dict[str, int]] = {}
        safety_car_by_lap: Dict[int, bool] = {}
        pit_window_by_lap: Dict[int, Dict[str, bool]] = {}

        for lap_num in range(1, race.total_laps + 1):
            lap_times_by_lap[lap_num] = {}
            positions_by_lap[lap_num] = {}
            safety_car_by_lap[lap_num] = False
            pit_window_by_lap[lap_num] = {}

        for driver in race.drivers:
            for lap in race.get_driver_laps(driver):
                lap_num = lap.lap_number

                if lap_num < 1 or lap_num > race.total_laps:
                    continue

                if lap.lap_time_s is not None:
                    lap_times_by_lap[lap_num][driver] = lap.lap_time_s

                positions_by_lap[lap_num][driver] = lap.position

                safety_car_by_lap[lap_num] = (
                    safety_car_by_lap[lap_num] or lap.safety_car_flag
                )

                pit_window_by_lap[lap_num][driver] = lap.pit_window

        return EnvironmentRaceData(
            track_name=race.track.name,
            year=race.year,
            total_laps=race.total_laps,
            drivers=race.drivers,
            pit_loss_time_s=race.track.pit_loss_time_s,
            pit_window_start=race.track.pit_window_start,
            pit_window_end=race.track.pit_window_end,
            lap_times_by_lap=lap_times_by_lap,
            positions_by_lap=positions_by_lap,
            safety_car_by_lap=safety_car_by_lap,
            pit_window_by_lap=pit_window_by_lap,
        )