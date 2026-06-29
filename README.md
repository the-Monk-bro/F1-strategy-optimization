# Quantum RL Agent for F1 Race Strategy Optimization

This project focuses on building an intelligent race strategy optimization system for Formula 1 using Reinforcement Learning. The current implementation includes a structured data layer, a custom F1 simulation environment, and a Deep Q-Network based agent for learning pit-stop and race strategy decisions.

The long-term objective of this project is to compare classical reinforcement learning methods with quantum reinforcement learning approaches for F1 race strategy optimization.

---

## Project Overview 

Formula 1 race strategy involves making sequential decisions across multiple laps. Important decisions include when to pit, which tyre compound to choose, how tyre degradation affects pace, how traffic impacts lap times, and how safety car situations can influence strategy.

This project converts F1 race data into a simulation-ready format and trains an RL agent to make strategy decisions in a custom race environment.

The project is currently divided into the following major parts:

1. Environment
2. DQN Agent
3. Training Pipeline
4. Evaluation Pipeline
5. Checkpoint Management
6. Reports and Documentation

---

## Current Work Completed

The following work has been completed so far:

### 1. Environment

The environment represents the Formula 1 race simulation system.

It includes:

- A custom F1 environment
- Real life historical race data to simulate the environment
- Race backend logic
- Race session management
- Race state representation
- Reward calculation
- Pit stop modeling
- Tyre degradation modeling
- Traffic modeling

This layer is responsible for simulating how a race progresses based on real life historical race data, lap by lap and how the agent's decisions affect the final race outcome.

---

### 2. DQN Agent

The DQN agent contains the reinforcement learning logic.

It includes:

- DQN agent implementation
- Neural network model
- Replay buffer
- Action masking logic

The DQN agent learns from interaction with the F1 environment. It stores experiences, trains a neural network, selects actions, and improves strategy over time.

---

### 3. Training Pipeline

The training pipeline contains the main training script for the DQN agent.

The training script connects:

- The F1 environment
- The DQN agent
- The replay buffer
- The neural network
- The checkpoint saving system

The goal of training is to allow the agent to learn better race strategies over many simulated episodes.

---

### 4. Evaluation Pipeline

The evaluation folder contains scripts for testing trained DQN models and comparing them with baseline strategies.

It includes:

- Evaluation of trained DQN models
- Evaluation of baseline DQN or rule-based approaches

This helps measure whether the trained agent is actually learning useful race strategies.

---

### 5. Checkpoint System

The project stores trained DQN model checkpoints in the `checkpoints/` directory.

The current checkpoint structure contains:

- `best.pt` — the best performing model checkpoint
- `latest.pt` — the latest saved model checkpoint
- `final.pt` — the final model after training completion

This allows training to be resumed, evaluated, and compared without retraining from the beginning.

---

### 6. Reports

The `reports/` folder currently contains the mid-evaluation report:

- `mid_eval_report_qc_3.pdf`

This report documents the progress made so far in the project.

---

## Repository Structure (Current)

```text
project-root/
│
├── agents/
│   └── dqn/
│       ├── action_mask.py
│       ├── dqn_agent.py
│       ├── network.py
│       └── replay_buffer.py
│
├── checkpoints/
│   └── dqn/
│       └── checkpoints_v1/
│           ├── best.pt
│           ├── final.pt
│           └── latest.pt
│
├── env/
│   ├── data/
│   │   ├── my_cache/
│   │   ├── processed_cache/
│   │   ├── data_for_env.py
│   │   └── my_data.py
│   ├── f1_env.py
│   ├── pit_model.py
│   ├── race_backend.py
│   ├── race_session.py
│   ├── race_state.py
│   ├── reward.py
│   ├── traffic_model.py
│   └── tyre_model.py
│
├── evaluation/
│   ├── __init__.py
│   ├── evaluate_baselines_dqn.py
│   └── evaluate_dqn.py
│
├── reports/
│   └── mid_eval_report_qc_3.pdf
│
├── training/
│   └── train_dqn.py
│
├── .gitignore
└── README.md
