# agents/dqn/evaluate_dqn.py

import numpy as np

from config import DQNConfig
from dqn_agent import DQNAgent
from actions import action_to_name


from env.environment.f1_env import F1Env


def evaluate_dqn(num_episodes: int = 10):
    config = DQNConfig()

    env = F1Env()

    agent = DQNAgent(config)
    agent.load(config.model_path)

    rewards = []

    for episode in range(1, num_episodes + 1):
        state, info = env.reset()

        action_mask = info.get("action_mask", None)

        done = False
        episode_reward = 0.0
        actions_taken = []

        while not done:
            action = agent.select_action(
                state=state,
                action_mask=action_mask,
                training=False,
            )

            next_state, reward, terminated, truncated, next_info = env.step(action)

            done = terminated or truncated

            actions_taken.append(action_to_name(action))

            state = next_state
            action_mask = next_info.get("action_mask", None)
            episode_reward += reward

        rewards.append(episode_reward)

        print("=" * 70)
        print(f"Evaluation episode: {episode}")
        print(f"Total reward: {episode_reward:.2f}")
        print(f"Actions taken: {actions_taken}")

    print("=" * 70)
    print(f"Average reward over {num_episodes} episodes: {np.mean(rewards):.2f}")
    print("=" * 70)


if __name__ == "__main__":
    evaluate_dqn()