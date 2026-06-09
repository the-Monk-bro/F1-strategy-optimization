import pandas as pd

from pit_model import PitModel
from tyre_model import TyreModel
from traffic_model import TrafficModel

class RaceBackend:

    def __init__(self, race_df):
        self.fastest_lap= float('inf')
    
        self.base_track_time= {
            "monaco" : 70.8,
            "monza" : 79.6,
            "silverstone" :  86.8    
        } 
        self.offset ={
            0: -0.8,
            1: 0.0,
            2: 0.9
        }
        self.sc_penalty= {
            "monaco" : 10,
            "monza" : 10,
            "silverstone" : 10
        }

        self.pit_model = PitModel()
        self.tyre_model = TyreModel()
        self.traffic_model = TrafficModel()
        
    def simulated_lap_time(self, track, current_lap, tyre_compound,tyre_age , max_laps, pitted, gap_ahead, safety_car):
        base_time =  self.base_track_time[track] + self.offset[tyre_compound] 
        fuel_time_penalty =  0.035* 100* (1- (current_lap / max_laps))
        tyre_degradation_penalty =  self.tyre_model.degradation(tyre_compound, tyre_age)
        sc_time_penalty = int(safety_car)* self.sc_penalty[track]

        pit_loss= 0
        if pitted:  pit_loss = self.pit_model.get_loss(track, safety_car)

        traffic_loss = self.traffic_model.get_traffic_loss(gap_ahead, current_lap)


        lap_time = base_time + tyre_degradation_penalty + fuel_time_penalty + sc_time_penalty + pit_loss + traffic_loss

        self.fastest_lap = min(self.fastest_lap, lap_time)
        lap_delta= lap_time - self.fastest_lap


        return (lap_time,lap_delta)
    
    
    
  


    
    


