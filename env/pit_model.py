class PitModel:
    def __init__(self, data):
        self.pit_loss = data["pit_loss"]  

    def get_loss(self,safety_car= False):
        loss = self.pit_loss

        if safety_car:
            loss *= 0.5
        return loss
    

        