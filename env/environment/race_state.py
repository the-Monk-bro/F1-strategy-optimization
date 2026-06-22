from dataclasses import dataclass

@dataclass
class RaceState:
    current_lap: int
    lap_time: float
    lap_delta : float

    start_position : int
    end_position: int

    tyre_compound : int
    tyre_age: int
    
    gap_leader : float
    gap_ahead: float
    gap_behind: float

    safety_car: bool

    
   
