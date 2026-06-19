class TyreModel:
    def __init__(self, data):
    
        self.degradation_curves = data["tyre_loss"]


    def degradation(self,compound, age):
        return self.degradation_curves[compound][age]