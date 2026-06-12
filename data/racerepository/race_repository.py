import logging 
from typing import Dict, List, Optional, Tuple

from data.models.race import Race
from data.models.lap import Lap
from data.sources.fastf1_source import FastF1DataSource
from data.validators.race_validator import RaceValidator, ValidationResult
from data.processors.gap_processor import GapProcessor
from data.processors.pit_window_processor import PitWindowProcessor
from data.statebuilder.state_builder import StateBuilder
from data.config import CACHE_DIR

logger = logging.getLogger(__name__)

class RaceRepository:
    def __init__(self,
                 cache_dir: str = CACHE_DIR,
                 source: Optional[FastF1DataSource]= None,
                 validator: Optional[RaceValidator] = None,
                 gap_proc: Optional[GapProcessor]= None,
                 pit_proc: Optional[PitWindowProcessor]= None,
                 builder: Optional[StateBuilder]= None,
    ):
        self._source = source or FastF1DataSource(cache_dir)
        self._validator = validator or RaceValidator()
        self._gap_proc = gap_proc or GapProcessor()
        self._pit_proc = pit_proc or PitWindowProcessor()
        self._builder = builder or StateBuilder()

        self._cache: Dict[str, Race] = {}
        logger.info("RaceRepository ready.")

    def get_race(
            self,
            track_name: str,
            year: int,
            force_reload: bool = False,
    ) -> Race:
        key = f"{track_name}_{year}"

        if not force_reload  and key in self._cache:
            logger.debug(f"Memory cache HIT; {key}")
            return self._cache[key]
        
        logger.info(f"Loading {year} {track_name} (full pipeline)...")

        race = self._source.load_race(track_name, year)

        result = self._validator.validate(race)
        if not result.is_valid:
            raise ValueError(
                f"Data validation FAILED for {year} {track_name}:\n"
                f"{result.summary()}"
            )
        
        for w in result.warnings:
            logger.warning(f" {w}")

        self._gap_proc.process(race)

        self._pit_proc.process(race)

        self._cache[key] = race
        logger.info(f"Cached: {key} -> {race}")
        return race
    def get_states(
            self,
            track_name: str,
            year: int,
            driver: str,
    ) -> List[List[float]]:
        
        race = self.get_race(track_name, year)
        self._check_driver(race, driver)
        
        laps = race.get_valid_laps(driver)
        states = self._builder.build_all(race, driver)

        if len(states) != len(laps):
            raise ValueError(
                f"State count mismatch for {driver} in {year} {track_name}"
                f"{len(states)} states but {len(laps)} valid laps."
            )
        for lap, state in zip(laps, states):
            if not self._validator.validate_state_vector(state, lap):
                raise ValueError(
                    f"Invalid state vector generated for"
                    f"{driver} lap {lap.lap_number} in {year} {track_name}: "
                    f"{state}"
                )
        return states
    
    def get_laps(
            self,
            track_name: str,
            year: int,
            driver: str,
    ) -> List[Lap]:
        race = self.get_race(track_name, year)
        self._check_driver(race, driver)
        return race.get_valid_laps(driver)
    
    def preload(self, races: List[Tuple[str, int]]) -> None:
        total = len(races)
        logger.info(f"Preloading {total} races...")
        for i , (track, year) in enumerate(races, 1):
            try:
                self.get_race(track, year)
                logger.info(f" [{i}/{total}] {year} {track} loaded")
            except Exception as e:
                logger.error(f"[{i}/{total}] {year} {track} FAILED: {e}")

    def cache_summary(self) -> Dict[str, int]:
        return{
            key: sum(len(laps) for laps in race.laps_by_driver.values())
            for key, race in self._cache.items()
        }
    def clear_cache(self) -> None:
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} races from memory cache.")

    def _check_driver(self, race: Race, driver: str) -> None:

        if driver not in race.drivers:
            raise ValueError(
                f"Driver '{driver}' not in {race.year} {race.track.name}. \n"
                f"Available drivers: {race.drivers}"
            )