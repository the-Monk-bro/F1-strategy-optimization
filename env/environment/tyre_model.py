class TyreModel:
    def __init__(self):

        self.curves = {
            0: 0.15,  #soft
            1: 0.08,  #medium
            2: 0.05,  #hard
        }

    def degradation(self,compound, age):
        return self.curves[compound] * age