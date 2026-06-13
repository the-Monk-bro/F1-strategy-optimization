import gymnasium as gym
import numpy as np


from race_state import RaceState
from reward import RewardCalculator
from race_backend import RaceBackend
from race_session import RaceSession

class F1StrategyEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, track = 'monza' , year= 2022, max_laps =70, name='MAK', total_players= 20):
        super().__init__()

        self.track =track
        self.year = year
        self.max_laps = max_laps
        self.total_players = total_players

        self.name = name

        self.reward_calc = RewardCalculator()
    
        self.race_backend = RaceBackend()
        self.race_session = RaceSession()

        self.safety_car_times = self.race_backend.safety_car_times 
    


        self.action_space = gym.spaces.Discrete(4)
        self.observation_space = gym.spaces.Box(
            low= 0,
            high=1,
            shape= (12,),
            dtype= np.float32
        )

    def reset(self, seed=None , options = None):
        super().reset(seed= seed)
        initial_tyre_compound = 1

        self.race_session.step(0, 0, self.name)
        arranged_cars= self.race_session.get_agent_state(self.name)

        gap_ahead = arranged_cars['gap_ahead']

        lap_time, lap_delta = self.race_backend.simulated_lap_time(self.track, 1, initial_tyre_compound, 0, self.max_laps, False, gap_ahead, self.safety_car_times[1])

        self.race_session.step(1, lap_time, self.name)
        initial_state = self.race_session.get_agent_state(self.name)

        self.state = RaceState(
            current_lap = 1,
            lap_time = lap_time,
            lap_delta = lap_delta,
        
            start_position = arranged_cars["current_position"],
            end_position= initial_state['current_position'],

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
            self.state.end_position / self.total_players,                              #current position
            max(0, 1-self.state.lap_delta/3),                              #lap delta

            tyre[0],
            tyre[1],                           #tyre compound
            tyre[2],

            min( self.state.tyre_age / tyre_life[self.state.tyre_compound], 1.0),      #tyre wear

            min(self.state.gap_leader / 40, 1),                         #gap to  leader
            min(self.state.gap_ahead / 10, 1),                          #gap ahead
            min(self.state.gap_behind / 10, 1),                            #gap behind

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

        self.race_session.step(self.state.current_lap, self.state.lap_time,self.name)
        state_now = self.race_session.get_agent_state(agent_name= self.name)

        prev_gap_leader = self.state.gap_leader

        self.state.gap_leader = state_now['gap_leader']
        self.state.gap_ahead = state_now['gap_ahead']
        self.state.gap_behind = state_now['gap_behind']
        self.state.start_position = self.state.end_position
        self.state.end_position = state_now['current_position']
        
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

        terminated =False
        if self.state.current_lap >= self.max_laps  : terminated = True

        reward = self.reward_calc.compute(self.state.lap_time, self.race_backend.base_track_time[self.track] ,self.state.start_position, self.state.end_position, self.state.gap_leader, prev_gap_leader )

        

        return self._get_obs(), reward, terminated, False, {}

      
        

    def render(self):
        tyre_chart = {
            0: 'soft',
            1: 'medium',
            2: 'hard'
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
       


env = F1StrategyEnv()
print(env.action_space)
obs, info = env.reset()

done = False

while not  done:
    env.render()

    action = env.action_space.sample()

    obs, reward, done, _, _ = env.step(action)

env.render()







        

    
