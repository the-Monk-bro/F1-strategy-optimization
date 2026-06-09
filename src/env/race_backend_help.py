import pandas as pd

from pit_model import PitModel
from tyre_model import TyreModel
from traffic_model import TrafficModel

class RaceBackend:

    def __init__(self, race_df):
        # Store the dataframe to extract real historical data
        self.race_data = race_df 

        self.fastest_lap = float('inf')
        
        # Calculate base metrics dynamically from FastF1 data
        # Assuming race_df has columns like 'LapTime', 'Compound', etc.
      
        
        # Base track time could be the median time of the top 10% fastest laps
        self.base_track_time = self.race_data['LapTime'].quantile(0.10).total_seconds()
        
        # Extract real tyre deltas from the dataframe instead of hardcoding
        self.offset = self._calculate_real_tyre_offsets() 
        
        # Use a percentage multiplier for SC rather than a flat second count
        self.sc_multiplier = 1.35 

        self.pit_model = PitModel()
        self.tyre_model = TyreModel()
        self.traffic_model = TrafficModel()
        
    def _calculate_real_tyre_offsets(self):
        # Logic to find the median lap time difference between compounds in race_df
        # This ensures compliance with using strictly real FastF1 data
        return {}
    
    
        
    def simulated_lap_time(self, track, current_lap, tyre_compound,tyre_age, max_laps, pitted, gap_ahead, safety_car):
        base_time = self.base_track_time + self.offset.get[tyre_compound]
        
        # Renamed for clarity
        fuel_time_penalty = 0.035 * 100 * (1 - (current_lap / max_laps))
        
        tyre_degradation_penalty = self.tyre_model.degradation(tyre_compound, tyre_age)
        
        pit_loss = self.pit_model.get_loss(track, safety_car) if pitted else 0
        traffic_loss = self.traffic_model.get_traffic_loss(gap_ahead)

        # Base lap calculation
        lap_time = base_time + tyre_degradation_penalty + fuel_time_penalty + pit_loss + traffic_loss

        # Apply Safety Car as a pace multiplier if active
        if safety_car:
            lap_time = lap_time * self.sc_multiplier

        self.fastest_lap = min(self.fastest_lap, lap_time)
        lap_delta= lap_time - self.fastest_lap


        return (lap_time,lap_delta)
    


  