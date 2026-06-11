import logging 
import math
from dataclasses import dataclass
from typing import List, Tuple

from data.models.race import Race
from data.models.lap import Lap
from data.config import VALIDATION

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def summary(self) -> str:
        """Human-readble summary for logging"""
        status = "PASSED" if self.is_valid else "FAILED"
        lines = [f"Validation {status}"]
        for e in self.errors:
            lines.append(f" ERROR: {e}")
        for w in self.warnings:
            lines.append(f" WARNING: {w}")
        return "\n".join(lines)

class RaceValidator:
    def validate(self, race:Race) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        e,w = self._check_driver_count(race)
        errors.extend(e); warnings.extend(w)

        e,w = self._check_lap_counts(race)
        errors.extend(e); warnings.extend(w)

        e,w = self._check_lap_times(race)
        errors.extend(e); warnings.extend(w)

        e,w = self._check_tyre_ages(race)
        errors.extend(e); warnings.extend(w)

        e,w = self._check_positions(race)
        errors.extend(e); warnings.extend(w)

        e,w = self._check_lap_metadata_sync(race)
        errors.extend(e); warnings.extend(w)

        result = ValidationResult(
            is_valid = len(errors) == 0,
            errors = errors,
            warnings = warnings,
        )

        if result.is_valid:
            logger.info(
                f"Validation passed for {race}"
                f"({len(warnings)}warnings)"
            )
        else:
            logger.error(f"Validation failed:\n{result.summary()}")
        return result
   
    def validate_state_vector(self, state: list, lap: Lap) -> bool:
        if len(state) != 11:
            logger.error(
                f"State has {len(state)} elements , Expected: 11 elements. Lap: {lap}"
            )
            return False
        for i,val in enumerate(state):
            if not isinstance(val,(int,float)):
                logger.error(f"State {i} is not numeric , val:{val} , lap:{lap}")
                return False
            value = float(val)
            if math.isnan(value):
                logger.error(f"State[{i}] is NaN for lap: {lap}")
                return False
            if not (0.0 <= value <= 1.0):
                logger.error(f"State[{i}] = {val: .4f} is outside [0,1]. Lap: {lap}")
                return False
            
        return True
    

    def _check_driver_count(self, race: Race) -> Tuple[List[str], List[str]]:
        errors, warnings = [],[]
        if(len(race.drivers)) < VALIDATION["MIN_DRIVERS"]:
            errors.append(
                f"Only {len(race.drivers)} drivers found "
                f"(minimum: {VALIDATION['MIN_DRIVERS']}). "
                f"Race data may be incomplete."

            )
        return errors, warnings
    
    def _check_lap_counts(self, race: Race) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        for driver in race.drivers:
            count = len(race.get_valid_laps(driver))
            if count < VALIDATION["MIN_LAPS_PER_DRIVER"]:
                warnings.append(
                    f"{driver} has only {count} valid laps "
                    f"(minimum: {VALIDATION['MIN_LAPS_PER_DRIVER']}). "
                    f"Likely retired early — may exclude from training."
                )
        return errors, warnings
    
    def _check_lap_times(self, race: Race) -> Tuple[List[str],List[str]]:
        errors, warnings = [],[]
        mn = VALIDATION["MIN_LAP_TIME_S"]
        mx = VALIDATION["MAX_LAP_TIME_S"]

        for driver in race.drivers:
            for lap in race.get_driver_laps(driver):
                if lap.lap_time_s is None:
                    continue
                if lap.lap_time_s < mn:
                    warnings.append(
                        f"{driver} Lap {lap.lap_number}: "
                        f"suspiciously fast {lap.lap_time_s:.1f}s < {mn}s"
                    )
                if lap.lap_time_s > mx:
                    warnings.append(
                        f"{driver} Lap {lap.lap_number}:"
                        f"suspiciously slow {lap.lap_time_s:.1f}> {mx}s"
                        f"(red flag or major incident lap)"
                    )
        return errors, warnings
    def _check_tyre_ages(
            self, race: Race
    ) -> Tuple[List[str],List[str]]:
        errors, warnings = [],[]
        for driver in race.drivers:
            for lap in race.get_driver_laps(driver):
                if lap.tyre_age < 0:
                    errors.append(
                        f"{driver} Lap {lap.lap_number}: "
                        f"negative tyre age{lap.tyre_age} - data corruption!"
                    )
                if lap.tyre_age > 60:
                    warnings.append(
                        f"{driver} Lap {lap.lap_number}: "
                        f"very high tyre age {lap.tyre_age} - check data"
                    )
        return errors, warnings
    
    def _check_positions(
            self, race: Race
    ) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        for driver in race.drivers:
            for lap in race.get_driver_laps(driver):
                if not (1 <= lap.position <= 20):
                    warnings.append(
                        f"{driver} Lap {lap.lap_number}: "
                        f"position {lap.position} outside 1-20"
                    )
        return errors, warnings
    
    def _check_lap_metadata_sync(self, race: Race) -> Tuple[List[str], List[str]]:
        errors, warnings = [],[]
        for driver in race.drivers:
            for lap in race.get_driver_laps(driver):
                if lap.total_laps != race.total_laps:
                    errors.append(
                    f"{driver} Lap {lap.lap_number}: "
                    f"lap.total_laps={lap.total_laps}, "
                    f"but race.total_laps={race.total_laps}. "
                    f"Call race.sync_lap_metadata()."
                )


        return errors, warnings