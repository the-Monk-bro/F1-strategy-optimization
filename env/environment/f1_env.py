import gymnasium as gym
import numpy as np

from race_state import RaceState
from reward import RewardCalculator
from race_backend import RaceBackend
from race_session import RaceSession
from race_data_adapter import RaceDataAdapter
from track_names import normalize_track_name

from data.racerepository.race_repository import RaceRepository


class F1StrategyEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        track="monza",
        year=2022,
        name=None,
    ):
        super().__init__()

        self.track = normalize_track_name(track)
        self.year = year

        self.repository = RaceRepository()
        self.adapter = RaceDataAdapter(self.repository)
        self.race_data = self.adapter.load(self.track, self.year)

        self.max_laps = self.race_data.total_laps
        self.total_players = self.race_data.total_drivers

        if name is None:
            self.name = self.race_data.starting_position[0]
        else:
            self.name = name

        self.reward_calc = RewardCalculator()

        self.race_backend = RaceBackend(
            track_name=self.race_data.track_name,
            pit_loss_time_s=self.race_data.pit_loss_time_s,
            base_time_by_compound=self.race_data.base_time_by_compound,
            tyre_loss=self.race_data.tyre_loss,
        )

        self.race_session = RaceSession(self.race_data)
        self.safety_car_times = self.race_data.safety_car_by_lap

        self.action_space = gym.spaces.Discrete(4)

        self.observation_space = gym.spaces.Box(
            low=0,
            high=1,
            shape=(12,),
            dtype=np.float32,
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        initial_tyre_compound = 1

        self.race_backend.fastest_lap = float("inf")
        self.race_session = RaceSession(self.race_data)

        self.race_session.step(0, 0.0, self.name)
        arranged_cars = self.race_session.get_agent_state(self.name)

        gap_ahead = arranged_cars["gap_ahead"]
        safety_car = self.safety_car_times.get(1, False)

        lap_time, lap_delta = self.race_backend.simulated_lap_time(
            current_lap=1,
            tyre_compound=initial_tyre_compound,
            tyre_age=0,
            total_laps=self.max_laps,
            pitted=False,
            gap_ahead=gap_ahead,
            safety_car=safety_car,
        )

        self.race_session.step(1, lap_time, self.name)
        initial_state = self.race_session.get_agent_state(self.name)

        self.state = RaceState(
            current_lap=1,
            lap_time=lap_time,
            lap_delta=lap_delta,

            start_position=arranged_cars["current_position"],
            end_position=initial_state["current_position"],

            tyre_compound=initial_tyre_compound,
            tyre_age=0,

            gap_leader=initial_state["gap_leader"],
            gap_ahead=initial_state["gap_ahead"],
            gap_behind=initial_state["gap_behind"],

            safety_car=safety_car,
        )

        return self._get_obs(), {}

    def _get_obs(self):
        tyre = [0, 0, 0]

        tyre_life = {
            0: 22,
            1: 35,
            2: 50,
        }

        tyre[self.state.tyre_compound] = 1

        obs = np.array([
            self.state.current_lap / self.max_laps,
            (self.max_laps - self.state.current_lap) / self.max_laps,
            self.state.end_position / self.total_players,
            max(0, 1 - self.state.lap_delta / 3),

            tyre[0],
            tyre[1],
            tyre[2],

            min(
                self.state.tyre_age / tyre_life[self.state.tyre_compound],
                1.0,
            ),

            min(self.state.gap_leader / 40, 1),
            min(self.state.gap_ahead / 10, 1),
            min(self.state.gap_behind / 10, 1),

            float(self.state.safety_car),
        ], dtype=np.float32)

        return obs

    def step(self, action):
        pitted = False

        if action != 0:
            pitted = True
            self.state.tyre_compound = action - 1
            self.state.tyre_age = -1

        self.state.current_lap += 1
        self.state.tyre_age += 1

        self.state.safety_car = self.safety_car_times.get(
            self.state.current_lap,
            False,
        )

        self.race_session.step(
            self.state.current_lap,
            self.state.lap_time,
            self.name,
        )

        state_now = self.race_session.get_agent_state(
            agent_name=self.name,
        )

        prev_gap_leader = self.state.gap_leader

        self.state.gap_leader = state_now["gap_leader"]
        self.state.gap_ahead = state_now["gap_ahead"]
        self.state.gap_behind = state_now["gap_behind"]

        self.state.start_position = self.state.end_position
        self.state.end_position = state_now["current_position"]

        lap_time, lap_delta = self.race_backend.simulated_lap_time(
            current_lap=self.state.current_lap,
            tyre_compound=self.state.tyre_compound,
            tyre_age=self.state.tyre_age,
            total_laps=self.max_laps,
            pitted=pitted,
            gap_ahead=self.state.gap_ahead,
            safety_car=self.state.safety_car,
        )

        self.state.lap_time = lap_time
        self.state.lap_delta = lap_delta

        terminated = self.state.current_lap >= self.max_laps

        base_time = self.race_backend.get_base_time(
            self.state.tyre_compound
        )

        reward = self.reward_calc.compute(
            self.state.lap_time,
            base_time,
            self.state.start_position,
            self.state.end_position,
            self.state.gap_leader,
            prev_gap_leader,
        )

        return self._get_obs(), reward, terminated, False, {}

    def render(self):
        tyre_chart = {
            0: "soft",
            1: "medium",
            2: "hard",
        }

        print(f"""
Lap: {self.state.current_lap}
Lap Time: {self.state.lap_time}
Start Position: {self.state.start_position}
End Position: {self.state.end_position}
Tyre: {tyre_chart[self.state.tyre_compound]}
Tyre Age: {self.state.tyre_age}
Gap Leader: {self.state.gap_leader:.3f}
""")