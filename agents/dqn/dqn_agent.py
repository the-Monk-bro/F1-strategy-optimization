import os
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from agents.dqn.network import DQNNetwork
from agents.dqn.replay_buffer import ReplayBuffer
from agents.dqn.config import DQNConfig
from agents.dqn.utils import validate_state, validate_action_mask


class DQNAgent:
    def __init__(self, config: DQNConfig):
        self.config = config

        self.state_size = config.state_size
        self.action_size = config.action_size

        self.gamma = config.gamma
        self.batch_size = config.batch_size

        self.epsilon = config.epsilon_start
        self.epsilon_end = config.epsilon_end
        self.epsilon_decay = config.epsilon_decay

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.policy_network = DQNNetwork(
            state_size=config.state_size,
            action_size=config.action_size,
            hidden_size=config.hidden_size,
        ).to(self.device)

        self.target_network = DQNNetwork(
            state_size=config.state_size,
            action_size=config.action_size,
            hidden_size=config.hidden_size,
        ).to(self.device)

        self.optimizer = optim.Adam(
            self.policy_network.parameters(),
            lr=config.learning_rate,
        )

        self.loss_fn = nn.SmoothL1Loss()

        self.replay_buffer = ReplayBuffer(
            capacity=config.replay_buffer_size
        )

        self.update_target_network()

    def select_action(
        self,
        state,
        action_mask=None,
        training: bool = True,
    ) -> int:
        state = validate_state(state, self.state_size)
        action_mask = validate_action_mask(
            action_mask,
            self.action_size,
        )

        valid_actions = np.where(action_mask)[0]

        if training and random.random() < self.epsilon:
            return int(random.choice(valid_actions))

        state_tensor = torch.tensor(
            state,
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(0)

        mask_tensor = torch.tensor(
            action_mask,
            dtype=torch.bool,
            device=self.device,
        ).unsqueeze(0)

        with torch.no_grad():
            q_values = self.policy_network(state_tensor)

            q_values = q_values.masked_fill(
                ~mask_tensor,
                -1e9,
            )

            action = q_values.argmax(dim=1).item()

        return int(action)

    def store_transition(
        self,
        state,
        action,
        reward,
        next_state,
        done,
        next_action_mask=None,
    ):
        state = validate_state(state, self.state_size)
        next_state = validate_state(next_state, self.state_size)

        next_action_mask = validate_action_mask(
            next_action_mask,
            self.action_size,
        )

        self.replay_buffer.push(
            state=state,
            action=int(action),
            reward=float(reward),
            next_state=next_state,
            done=bool(done),
            next_action_mask=next_action_mask,
        )

    def learn(self):
        if len(self.replay_buffer) < self.batch_size:
            return None

        transitions = self.replay_buffer.sample(self.batch_size)

        states = np.array(
            [t.state for t in transitions],
            dtype=np.float32,
        )

        actions = np.array(
            [t.action for t in transitions],
            dtype=np.int64,
        )

        rewards = np.array(
            [t.reward for t in transitions],
            dtype=np.float32,
        )

        next_states = np.array(
            [t.next_state for t in transitions],
            dtype=np.float32,
        )

        dones = np.array(
            [t.done for t in transitions],
            dtype=np.float32,
        )

        next_action_masks = np.array(
            [t.next_action_mask for t in transitions],
            dtype=np.bool_,
        )

        states_tensor = torch.tensor(
            states,
            dtype=torch.float32,
            device=self.device,
        )

        actions_tensor = torch.tensor(
            actions,
            dtype=torch.long,
            device=self.device,
        ).unsqueeze(1)

        rewards_tensor = torch.tensor(
            rewards,
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(1)

        next_states_tensor = torch.tensor(
            next_states,
            dtype=torch.float32,
            device=self.device,
        )

        dones_tensor = torch.tensor(
            dones,
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(1)

        next_masks_tensor = torch.tensor(
            next_action_masks,
            dtype=torch.bool,
            device=self.device,
        )

        current_q_values = self.policy_network(
            states_tensor
        ).gather(1, actions_tensor)

        with torch.no_grad():
            next_q_values = self.target_network(next_states_tensor)

            next_q_values = next_q_values.masked_fill(
                ~next_masks_tensor,
                -1e9,
            )

            max_next_q_values = next_q_values.max(
                dim=1,
                keepdim=True,
            )[0]

            target_q_values = rewards_tensor + (
                self.gamma * max_next_q_values * (1 - dones_tensor)
            )

        loss = self.loss_fn(
            current_q_values,
            target_q_values,
        )

        self.optimizer.zero_grad()
        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            self.policy_network.parameters(),
            max_norm=10.0,
        )

        self.optimizer.step()

        return float(loss.item())

    def update_target_network(self):
        self.target_network.load_state_dict(
            self.policy_network.state_dict()
        )

    def decay_epsilon(self):
        self.epsilon = max(
            self.epsilon_end,
            self.epsilon * self.epsilon_decay,
        )

    def save(self, path: str | None = None):
        save_path = path or self.config.model_path

        os.makedirs(
            os.path.dirname(save_path),
            exist_ok=True,
        )

        checkpoint = {
            "policy_network": self.policy_network.state_dict(),
            "target_network": self.target_network.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "config": self.config,
        }

        torch.save(checkpoint, save_path)

    def load(self, path: str | None = None):
        load_path = path or self.config.model_path

        checkpoint = torch.load(
            load_path,
            map_location=self.device,
        )

        self.policy_network.load_state_dict(
            checkpoint["policy_network"]
        )

        self.target_network.load_state_dict(
            checkpoint["target_network"]
        )

        self.optimizer.load_state_dict(
            checkpoint["optimizer"]
        )

        self.epsilon = checkpoint.get(
            "epsilon",
            self.config.epsilon_end,
        )