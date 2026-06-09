import gymnasium as gym
import numpy as np


from race_state import RaceState
from reward import RewardCalculator
from race_backend import RaceBackend
from race_session import RaceSession

class F1StrategyEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, track , year, max_laps =70, name='VER'):
        super().__init__()

        self.track =track
        self.year = year
        self.max_laps = max_laps

        self.name = name

        self.safety_car_times = {}


        self.reward_calc = RewardCalculator()
    
        self.race_backend = RaceBackend()
        self.race_session = RaceSession()
    


        self.action_space = gym.spaces.Discrete(4)
        self.observation_space = gym.spaces.Box(
            low= 0,
            high=1,
            shape= (12,),
            dtype= np.float32
        )

    def reset(self, seed=None , options = None):
        super().reset(seed= seed)
        
        self.race_session.step(0, agent_time= None)

        initial_tyre_compound = 1

        initial_state = self.race_session.get_agent_state( agent_name= self.name)

        gap_ahead = initial_state['gap_ahead']

        lap_time, lap_delta = self.race_backend.simulated_lap_time(self.track, 1, initial_tyre_compound, 0, self.max_laps, False, gap_ahead, self.safety_car_times[1])

        self.state = RaceState(
            current_lap = 1,
            lap_time = lap_time,
            lap_delta = lap_delta,
        
            position = initial_state["current_position"],

            tyre_compound = initial_tyre_compound,
            tyre_age=  0,
            
            gap_leader = initial_state["gap_leader"],
            gap_ahead =  initial_state["gap_ahead"],
            gap_behind=  initial_state["gap_behind"],

            safety_car = self.safety_car_times[1]
        )
        return self._get_obs() , {}

    def  _get_obs(self):
        tyre= [0,0,0]
        tyre_life = {
            0: 22,   #soft
            1: 35,     #medium
            2: 50     #hard
        }
        tyre[self.state.tyre_compound] = 1
      

        obs = np.array([
            self.state.current_lap / self.max_laps,                            #race progress
            (self.max_laps -self.state.current_lap)/ self.max_laps,           #remaining laps
            self.state.position /20,                                          #current position

            tyre[0],
            tyre[1],                           #tyre compound
            tyre[2],

            min( self.state.tyre_age / tyre_life[self.state.tyre_compound], 1.0),      #tyre wear

            min(self.state.lap_delta / 5, 1),                         #lap delta

            min(self.state.gap_leader / 60, 1),                         #gap to  leader
            min(self.state.gap_ahead / 20, 1),                          #gap ahead
            min(self.state.gap_behind / 20, 1),                            #gap behind

            float(self.state.safety_car),                         #safety car


        ], dtype=np.float32)

        return obs

    
    def step (self, action):
        pitted = False

        if action !=0:
            pitted = True
            self.state.tyre_compound = action -1
            self.state.tyre_age = -1
        
        self.state.current_lap += 1
        self.state.tyre_age += 1
        self.state.safety_car = self.safety_car_times[self.state.current_lap]

        self.race_session.step(self.state.current_lap, agent_time = self.state.lap_time)
        state_now = self.race_session.get_agent_state(agent_name= self.name)

        self.state.gap_leader = state_now['gap_leader']
        self.state.gap_ahead = state_now['gap_ahead']
        self.state.gap_behind = state_now['gap_behind']
        
        lap_time, lap_delta = self.race_backend.simulated_lap_time(
            self.track,
            self.state.current_lap,
            self.state.tyre_compound,
            self.state.tyre_age,
            self.max_laps,
            pitted,
            self.state.gap_ahead,
            self.state.safety_car
            )
        
        self.state.lap_time = lap_time
        self.state.lap_delta = lap_delta

        reward = self.reward_calc.compute()

        terminated =False
        if self.state.current_lap >= self.max_laps  : terminated = True

        truncated = False

        return self._get_obs(), reward, terminated, truncated, {}

      
        

    def render(self):
        print(f"""
Lap: {self.state.current_lap}
Position: {self.state.position}
Tyre: {self.state.tyre_compound}
Tyre Age: {self.state.tyre_age}
Gap Leader: {self.state.gap_leader:.2f}

""")
       


env = F1StrategyEnv("monaco", 2023)

obs, info = env.reset()

done = False

while not done:

    env.render()

    action = env.action_space.sample()

    obs, reward, done, _, _ = env.step(action)

env.render()




        

    
