import logging
import math
from typing import List 

from data.models.lap import Lap, CompoundType
from data.models.race import Race
from data.config import NORMALIZATION

logger = logging.getLogger(__name__)

class StateBuilder:
    def build(self, lap: Lap, total_laps: int) -> List[float]:
        current_lap = self._clamp(lap.lap_number / total_laps)
        lap_delta = self._clamp(
            lap.lap_delta_s / NORMALIZATION["MAX_LAP_DELTA_S"]
        )
        laps_remaining = self._clamp(lap.laps_remaining / total_laps)
        position = self._clamp(lap.position / NORMALIZATION["MAX_POSITION"])
        compound_val = lap.compound.value if lap.compound.value >= 0 else 1
        tyre_compound = self._clamp(compound_val / NORMALIZATION["MAX_COMPOUND"])

        tyre_age = self._clamp(lap.tyre_age/ NORMALIZATION["MAX_TYRE_AGE"])
        gap_to_leader = self._clamp(
            lap.gap_to_leader_s / NORMALIZATION["MAX_GAP_TO_LEADER_S"]
        )
        gap_ahead = self._clamp(lap.gap_ahead_s / NORMALIZATION["MAX_GAP_CLOSE_ s"])
        gap_behind= self._clamp(lap.gap_behind_s / NORMALIZATION["MAX_GAP_CLOSE_ s"])
        safety_car = 1.0 if lap.safety_car_flag else 0.0
        pit_window = 1.0 if lap.pit_window else 0.0

        state = [
            round(current_lap, 4),
            round(lap_delta, 4),
            round(laps_remaining, 4),
            round(position, 4),
            round(tyre_age, 4),
            round(gap_to_leader, 4),
            round(gap_ahead, 4),
            round(gap_behind, 4),
            round(safety_car, 4),
            round(pit_window, 4),
        ]
        lap.state_vector = state 
        return state 
   
    def build_all(self, race: Race, driver: str) -> List[List[float]]:
        valid_laps = race.get_valid_laps(driver)
        if not valid_laps:
            logger.warning(f"No valid laps for {driver} in {race}")
            return[]
        total = race.total_laps
        states = [self.build(lap,total) for lap in valid_laps]

        logger.debug(
            f"Built {len(states)} state vectors for {driver}"
            f"({race.track.name} {race.year})"
        )
        return states
    
    @staticmethod
    def _clamp(value: float, high: float = 1.0 , low:float=0.0) -> float:
        if math.isnan(value):
            return low
        return max(low, min(high, value))