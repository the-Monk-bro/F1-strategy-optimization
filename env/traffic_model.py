class TrafficModel:
    def __init__(self):
        pass
    

    def get_traffic_loss(self, gap_ahead, lap_num):
        loss= 0
        if gap_ahead >= 3 : loss =0
        elif gap_ahead >= 1 : loss = 0.4
        else:
            if lap_num>=3 :
                loss= -0.2
            else:
                loss=0.5
    
        return loss


   

        