class TrafficModel:
    def __init__(self):
        pass
    

    def get_traffic_loss(self, gap_ahead: float) -> float:
        """
        Model the time loss from running in another car's dirty air.
        - >= 3 s gap : free air, no penalty
        - 1–3 s gap  : turbulence starts to affect aero balance (~0.4 s)
        - < 1 s gap  : heavy dirty air; significant downforce loss (~0.5 s)
        DRS is a track-specific benefit and NOT modelled here as a blanket
        rule — it would create a physically-backwards "faster in dirty air" bug.
        """
        if gap_ahead >= 3:
            return 0.0
        elif gap_ahead >= 1:
            return 0.4
        else:
            return 0.5


   