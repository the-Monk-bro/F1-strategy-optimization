import logging 
from typing import Dict, List, Optional

from data.models.race import Race
from data.models.lap  import Lap

logger = logging.getLogger(__name__)

class GapProcessor:
    def process(self, race: Race) -> None:
        logger.info(f"GapProcessor running on {race}")
        self._compute_gap_to_leader(race)
        self._compute_position_gaps(race)
        self._compute_lap_delta(race)
        logger.info("GapProcessor complete.")

    def _compute_gap_to_leader(self, race: Race):
        cum: Dict[str, Dict[int, float]] = {}
        for driver in race.drivers:
            cum[driver] = {}
            total = 0.0
            for lap in sorted(race.get_driver_laps(driver), key= lambda x : x.lap_number):
                if lap.lap_time_s is not None:
                    total += lap.lap_time_s
                cum[driver][lap.lap_number] = total
        
        all_lap_nums = {
            lap.lap_number
            for laps in race.laps_by_driver.values()
            for lap in laps
        }
        
        leader_time: Dict[int, float] = {}
        for n in all_lap_nums:
            times_this_lap = {
                d: cum[d][n]
                for d in cum
                if n in cum[d]
            }
            if times_this_lap:
                leader_time[n] = min(times_this_lap.values())
    

    def _compute_position_gaps(self, race: Race) -> None:
        all_lap_nums = {
            lap.lap_number
            for laps in race.laps_by_driver.values()
            for lap in laps
        }
        pos_to_driver: Dict[int, Dict[int, str]] = {}  
        gap_lookup:    Dict[str, Dict[int, float]] = {} 
 
        for driver in race.drivers:
            gap_lookup[driver] = {}
            for lap in race.get_driver_laps(driver):
                gap_lookup[driver][lap.lap_number] = lap.gap_to_leader_s
                if lap.lap_number not in pos_to_driver:
                    pos_to_driver[lap.lap_number] = {}
                pos_to_driver[lap.lap_number][lap.position] = driver
 
        
        for driver in race.drivers:
            for lap in race.get_driver_laps(driver):
                n   = lap.lap_number
                pos = lap.position
                pm  = pos_to_driver.get(n, {})
 
               
                driver_ahead = pm.get(pos - 1)  
                if driver_ahead and driver_ahead in gap_lookup:
                    gap_self  = gap_lookup[driver].get(n, 0.0)
                    gap_front = gap_lookup[driver_ahead].get(n, 0.0)
                   
                    lap.gap_ahead_s = round(max(0.0, gap_self - gap_front), 3)
 
                
                driver_behind = pm.get(pos + 1)  
                if driver_behind and driver_behind in gap_lookup:
                    gap_self  = gap_lookup[driver].get(n, 0.0)
                    gap_back  = gap_lookup[driver_behind].get(n, 999.0)
                    lap.gap_behind_s = round(max(0.0, gap_back - gap_self), 3)
   
   
    def _compute_lap_delta(self, race: Race) -> None:
        for driver in race.drivers:
            best = race.get_best_lap_time(driver)
            if best in None: 
                continue
            
            for lap in race.get_driver_laps(driver):
                if lap.lap_time_s is not None:
                    delta = lap.lap_time_s - best
                    lap.lap_delta_s = round(max(0.0,delta),3)
                    




        

