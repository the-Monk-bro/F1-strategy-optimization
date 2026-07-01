from env.f1_env import F1StrategyEnv

env = F1StrategyEnv()
obs, info = env.reset()

done = False
total_reward=0

while not  done:
    env.render()

    action =  env.action_space.sample()

    obs, reward, done, _, _ = env.step(action)
    total_reward += reward
    print("Total Reward:" , total_reward)

env.render()