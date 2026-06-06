import pandas as pd

class RaceBackend:

    def __init__(self, race_df):

        self.df = race_df

    def get_lap(self, lap):
        return self.df.iloc[lap]