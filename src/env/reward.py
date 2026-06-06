class RewardCalculator:
    def compute(
            self,
            prev_position,
            new_position,
            pit_loss,
            pitted,
            safety_car
    ):
        reward= 0
        reward+= (prev_position- new_position)

        if pitted:
            reward -= pit_loss/10
        
        if pitted and safety_car : 
            reward +=3
        
        return reward
