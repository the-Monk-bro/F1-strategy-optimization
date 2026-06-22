from collections import deque
import numpy as np

from config import DQNConfig
from dqn_agent import DQNAgent
from utils import set_global_seed
from actions import action_to_name

from env.environment.f1_env import F1Env


def train_dqn():
    config = DQNConfig()
    set_global_seed(config.seed)

    env = F1Env()

    agent = DQNAgent(config)

    recent_rewards = deque(maxlen=100)

    for episode in range(1, config.num_episodes + 1):
        state, info = env.reset()

        action_mask = info.get("action_mask", None)

        done = False
        episode_reward = 0.0
        episode_losses = []
        step_count = 0

        while not done and step_count < config.max_steps_per_episode:
            action = agent.select_action(
                state=state,
                action_mask=action_mask,
                training=True,
            )

            next_state, reward, terminated, truncated, next_info = env.step(action)

            done = terminated or truncated

            next_action_mask = next_info.get("action_mask", None)

            agent.store_transition(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done,
                next_action_mask=next_action_mask,
            )

            loss = agent.learn()

            if loss is not None:
                episode_losses.append(loss)

            state = next_state
            action_mask = next_action_mask
            episode_reward += reward
            step_count += 1

        agent.decay_epsilon()

        if episode % config.target_update_frequency == 0:
            agent.update_target_network()

        recent_rewards.append(episode_reward)

        avg_reward = np.mean(recent_rewards)
        avg_loss = np.mean(episode_losses) if episode_losses else 0.0

        print(
            f"Episode {episode:4d} | "
            f"Reward: {episode_reward:10.2f} | "
            f"Avg100: {avg_reward:10.2f} | "
            f"Epsilon: {agent.epsilon:.3f} | "
            f"Loss: {avg_loss:.5f}"
        )

        if episode % 50 == 0:
            agent.save(config.model_path)

    agent.save(config.model_path)

    print(f"Training complete. Model saved to {config.model_path}")


if __name__ == "__main__":
    train_dqn()