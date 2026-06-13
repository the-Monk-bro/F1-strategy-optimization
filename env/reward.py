class RewardCalculator:
    def compute(self, lap_time, base_time, start_pos, end_pos , gap_leader, prev_gap_leader):
        reward = (base_time -lap_time) + (start_pos-end_pos)*10 + (prev_gap_leader - gap_leader) 
        
        return reward
       
