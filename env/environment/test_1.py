from data.racerepository.race_repository import RaceRepository
from env.environment.race_data_adapter import RaceDataAdapter

repo = RaceRepository()
adapter = RaceDataAdapter(repo)

race_data = adapter.load("Monza", 2022)

print(race_data.total_drivers)