class PitModel:
    PIT_LOSS = {
        "monaco":20,
        "monza": 24,
        "silverstone": 22
    }

    def get_loss(self,track,safety_car= False):
        loss = self.PIT_LOSS[track]

        if safety_car:
            loss *= 0.5
        return loss
    

        