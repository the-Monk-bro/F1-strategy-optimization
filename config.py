from dataclasses import dataclass

@dataclass
class DQNConfig:
    state_size: int = 11
    action_size: int = 4

    gamma: float = 0.99
    learning_rate: float = 1e-4

    replay_buffer_size: int = 100_000
    batch_size: int = 64

    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay: float = 0.995

    target_update_frequency: int = 10

    num_episodes: int = 1000
    max_steps_per_episode: int = 100

    hidden_size: int = 128

    model_path: str = "checkpoints/f1_dqn_agent.pth"

    seed: int = 42