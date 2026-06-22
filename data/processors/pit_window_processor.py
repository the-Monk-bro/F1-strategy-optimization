import logging 
from data.models.race import Race
from data.models.lap import Lap
from data.config import PIT_WINDOW

logger = logging.getLogger(__name__)

class PitWindowProcessor:
    def process(self,race: Race) -> None:
        logger.info(f"PitWindowProcessor running on {race}...")
        pit_loss = race.track.pit_loss_time_s
        win_start = race.track.pit_window_start
        win_end = race.track.pit_window_end

        for driver in race.drivers:
            for lap in race.get_driver_laps(driver):
                lap.pit_window = self._evaluate(lap, pit_loss, win_start, win_end)
        
        logger.info("PitWindowProcessor complete.")
    def _evaluate(
            self, lap,pit_loss_time_s:float, window_start: int, window_end: int,)->bool:
        tyre_old_enough = lap.tyre_age >= PIT_WINDOW["MIN_TYRE_AGE_TO_PIT"]

        if not tyre_old_enough:
            return False
        
        if lap.track_status.is_slow_zone:
            return True
         
        in_window = window_start <= lap.lap_number <= window_end
        if not in_window:
            return False
        
        if not tyre_old_enough:
            return False
        
        
        safe_gap = lap.gap_behind_s > pit_loss_time_s
        if not safe_gap:
            return False
        
        return True
        
        
    