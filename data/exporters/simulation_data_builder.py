from __future__ import annotations

import math
from typing import Dict, List, Optional

from data.models.race import Race
from data.models.lap import CompoundType
from data.config import TYRE_LOSS


class SimulationDataBuilder:
    def build(self, race: Race) -> Dict:
        return {
            "total_laps": self._get_total_laps(race),
            "total_drivers": self._get_total_drivers(race),
            "starting_position": self._get_starting_position(race),
            "safety_car": self._get_safety_car_list(race),
            "lap_time_data": self._get_lap_time_data(race),
            "tyre_loss": dict(TYRE_LOSS),
            "pit_loss": self._get_pit_loss(race),
            "base_time": self._get_base_time_by_compound(race),
        }

    def _get_total_laps(self, race: Race) -> int:
        return race.total_laps

    def _get_total_drivers(self, race: Race) -> int:
        return len(race.drivers)

    def _get_starting_position(self, race: Race) -> List[str]:
        position_map = race.get_position_map(1)

        return [
            driver
            for position, driver in sorted(position_map.items())
        ]

    def _get_safety_car_list(self, race: Race) -> List[bool]:
        safety_car = [False] * (race.total_laps + 1)

        for lap_number in range(1, race.total_laps + 1):
            lap_has_safety_car = False

            for driver in race.drivers:
                for lap in race.get_driver_laps(driver):
                    if lap.lap_number == lap_number and lap.safety_car_flag:
                        lap_has_safety_car = True
                        break

                if lap_has_safety_car:
                    break

            safety_car[lap_number] = lap_has_safety_car

        return safety_car

    def _get_lap_time_data(self, race: Race) -> Dict[int, Dict[str, float]]:
        data: Dict[int, Dict[str, float]] = {}

        data[0] = {
            driver: 0.0
            for driver in race.drivers
        }

        for lap_number in range(1, race.total_laps + 1):
            data[lap_number] = {}

            for driver in race.drivers:
                lap_time = 0.0

                for lap in race.get_driver_laps(driver):
                    if lap.lap_number == lap_number:
                        lap_time = (
                            float(lap.lap_time_s)
                            if lap.lap_time_s is not None
                            else 0.0
                        )
                        break

                data[lap_number][driver] = round(lap_time, 3)

        return data

    def _get_pit_loss(self, race: Race) -> float:
        return float(race.track.pit_loss_time_s)

    def _get_base_time_by_compound(self, race: Race) -> Dict[int, Optional[float]]:
        compounds_to_include = [
            CompoundType.SOFT,
            CompoundType.MEDIUM,
            CompoundType.HARD,
        ]

        base_time_by_compound: Dict[int, Optional[float]] = {}

        for compound in compounds_to_include:
            lap_times: List[float] = []

            for driver in race.drivers:
                for lap in race.get_valid_laps(driver):
                    if lap.lap_time_s is None:
                        continue

                    if lap.compound_type != compound:
                        continue

                    if lap.pitted:
                        continue

                    if lap.safety_car_flag:
                        continue

                    lap_times.append(float(lap.lap_time_s))

            if not lap_times:
                base_time_by_compound[compound.value] = None
                continue

            lap_times.sort()

            top_count = max(1, math.ceil(len(lap_times) * 0.10))
            fastest_laps = lap_times[:top_count]

            base_time = sum(fastest_laps) / len(fastest_laps)

            base_time_by_compound[compound.value] = round(base_time, 3)

        return base_time_by_compound