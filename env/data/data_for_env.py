from env.data.my_data import F1TrackDataLoader


class Env_data:
    def __init__(self, track, year):
        loader = F1TrackDataLoader()
        self.data = loader.get_race_data(track, year)

