import pandas as pd

from pit_model import PitModel
from tyre_model import TyreModel
from traffic_model import TrafficModel

class RaceBackend:

    def __init__(self, race_df= None):
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
        
        self.sc_multiplier = 1.35 
    

        self.safety_car_times =  {1: False, 2: False, 3: False, 4: False, 5: False,
    6: False, 7: False, 8: False, 9: False, 10: False,
    11: False, 12: False, 13: False, 14: False, 15: False,
    16: False, 17: True, 18: False, 19: False, 20: False,
    21: False, 22: False, 23: False, 24: False, 25: False,
    26: False, 27: False, 28: False, 29: False, 30: False,
    31: False, 32: False, 33: False, 34: False, 35: False,
    36: False, 37: False, 38: False, 39: False, 40: False,
    41: False, 42: False, 43: False, 44: False, 45: False,
    46: False, 47: False, 48: False, 49: False, 50: False,
    51: False, 52: False, 53: False, 54: True, 55: False,
    56: False, 57: False, 58: False, 59: False, 60: False,
    61: False, 62: False, 63: False, 64: False, 65: False,
    66: False, 67: False, 68: False, 69: False, 70: False}

        self.pit_model = PitModel()
        self.tyre_model = TyreModel()
        self.traffic_model = TrafficModel()
        
    def simulated_lap_time(self, track, current_lap, tyre_compound,tyre_age , max_laps, pitted, gap_ahead, safety_car):
        base_time =  self.base_track_time[track] + self.offset[tyre_compound] 
        fuel_time_penalty =  0.035* 100* (1- (current_lap / max_laps))
        tyre_degradation_penalty =  self.tyre_model.degradation(tyre_compound, tyre_age)
        

        pit_loss= 0
        if pitted:  pit_loss = self.pit_model.get_loss(track, safety_car)

        traffic_loss = self.traffic_model.get_traffic_loss(gap_ahead, current_lap)

    


        lap_time = base_time + tyre_degradation_penalty + fuel_time_penalty  + pit_loss + traffic_loss
        if safety_car:
            lap_time = lap_time * self.sc_multiplier

        self.fastest_lap = min(self.fastest_lap, lap_time)
        lap_delta= lap_time - self.fastest_lap


        return (lap_time,lap_delta)
    
    
    
  


    
    


