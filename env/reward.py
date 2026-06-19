class RewardCalculator:
    def compute(self, lap_delta, start_pos, end_pos , gap_leader, prev_gap_leader):
        reward =  (start_pos-end_pos)*10 + (prev_gap_leader - gap_leader)  - (lap_delta)
        
        return reward
       
