import gymnasium as gym
import numpy as np

from pit_model  import PitModel
from tyre_model import TyreModel
from race_state import RaceState
from reward import RewardCalculator


class F1StrategyEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, track , year, max_laps =70):
        super().__init__()

        self.track =track
        self.year = year
        self.max_laps = max_laps

        self.race_df = None

        self.reward_calc = RewardCalculator()
        self.tyre_model = TyreModel()
        self.pit_model = PitModel()


        self.action_space = gym.spaces.Discrete(4)
        self.observation_space = gym.spaces.Box(
            low= 0,
            high=1,
            shape= (13,),
            dtype= np.float32
        )

    def reset(self, seed=None , options = None):
        super().reset(seed= seed)

        self.state = RaceState(
            current_lap = 1,
            lap_delta =0,

            position = 10,

            tyre_compound = 1,
            tyre_age=  0,
            
            gap_leader = 20,
            gap_ahead = 2,
            gap_behind= 1,

            safety_car = False
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

    def _apply_action(self, action):
        pitted = False
        pit_loss = 0

        if action !=0 :
            pitted = True
            self.state.tyre_compound = action -1
            self.state.tyre_age = 0

            pit_loss = self.pit_model.get_loss(self.track, self.state.safety_car)

            self.state.gap_leader += pit_loss
        
        return pitted, pit_loss
    
    def step (self, action):

        prev_position =  self.state.position

        pitted, pit_loss= self._apply_action(action)

        self.state.current_lap += 1
        self.state.tyre_age += 1 

        degradation = self.tyre_model.degradation(self.state.tyre_compound, self.state.tyre_age)

        self.state.lap_delta = degradation

        if degradation>2:
            self.state.position += 1

        self.state.position = min (20, max(1,self.state.position))

        reward = self.reward_calc.compute(prev_position , self.state.position, pit_loss, pitted, self.state.safety_car)

        terminated = self.state.current_lap > self.max_laps

        if terminated:
            reward += (21-self.state.position)*5

        return (self._get_obs(), reward, terminated, False, {})
    
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

    obs, reward, done, _, _ = env.step(
        action
    )




        

    
