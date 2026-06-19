from typing import Dict

from data.racerepository.race_repository import RaceRepository

from data.models.race import Race
from race_data import EnvironmentRaceData


class RaceDataAdapter:
    def __init__(self, repository: RaceRepository):
        self.repository = repository

    def load(self, track_name: str, year: int) -> EnvironmentRaceData:
        race = self.repository.get_race(track_name, year)
        sim_data = self.repository.get_simulation_data(track_name, year)

        return self._convert_race(race, sim_data)

    def _convert_race(self, race: Race, sim_data: Dict) -> EnvironmentRaceData:
        lap_times_by_lap: Dict[int, Dict[str, float]] = {}
        positions_by_lap: Dict[int, Dict[str, int]] = {}
        safety_car_by_lap: Dict[int, bool] = {}
        pit_window_by_lap: Dict[int, Dict[str, bool]] = {}

        # Add lap 0 so RaceSession can initialize cleanly.
        lap_times_by_lap[0] = {
            driver: 0.0
            for driver in race.drivers
        }
        positions_by_lap[0] = {}
        safety_car_by_lap[0] = False
        pit_window_by_lap[0] = {
            driver: False
            for driver in race.drivers
        }

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

                lap_times_by_lap[lap_num][driver] = (
                    float(lap.lap_time_s)
                    if lap.lap_time_s is not None
                    else 0.0
                )

                positions_by_lap[lap_num][driver] = lap.position

                safety_car_by_lap[lap_num] = (
                    safety_car_by_lap[lap_num] or lap.safety_car_flag
                )

                pit_window_by_lap[lap_num][driver] = lap.pit_window

        return EnvironmentRaceData(
            track_name=race.track.name,
            year=race.year,

            total_laps=sim_data["total_laps"],
            total_drivers=sim_data["total_drivers"],
            drivers=race.drivers,
            starting_position=sim_data["starting_position"],

            pit_loss_time_s=sim_data["pit_loss"],
            pit_window_start=race.track.pit_window_start,
            pit_window_end=race.track.pit_window_end,

            tyre_loss=sim_data["tyre_loss"],
            base_time_by_compound=sim_data["base_time"],

            lap_times_by_lap=lap_times_by_lap,
            positions_by_lap=positions_by_lap,
            safety_car_by_lap=safety_car_by_lap,
            pit_window_by_lap=pit_window_by_lap,
        )