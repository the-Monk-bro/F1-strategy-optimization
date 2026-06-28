# Quantum RL Agent for F1 Race Strategy Optimization

This project focuses on building an intelligent race strategy optimization system for Formula 1 using Reinforcement Learning. The current implementation includes a structured data layer, a custom F1 simulation environment, and a Deep Q-Network based agent for learning pit-stop and race strategy decisions.

The long-term objective of this project is to compare classical reinforcement learning methods with quantum reinforcement learning approaches for F1 race strategy optimization.

---

## Project Overview 

Formula 1 race strategy involves making sequential decisions across multiple laps. Important decisions include when to pit, which tyre compound to choose, how tyre degradation affects pace, how traffic impacts lap times, and how safety car situations can influence strategy.

This project converts F1 race data into a simulation-ready format and trains an RL agent to make strategy decisions in a custom race environment.

The project is currently divided into the following major parts:

1. Data Layer
2. Environment Layer
3. DQN Agent Layer
4. Training Pipeline
5. Evaluation Pipeline
6. Checkpoint Management
7. Reports and Documentation
8. Testing

---

## Current Work Completed

The following work has been completed so far:

### 1. Data Layer

The data layer has been designed to collect, process, validate, and prepare F1 race data for reinforcement learning.

It includes:

- Data models for representing races and laps
- Data sources for loading race information
- Processors for preparing derived race features
- Validators for checking the correctness of race data
- State builder logic for converting race information into RL-compatible state vectors
- Cache support for storing processed race data
- Configuration file for shared constants and project settings

This layer acts as the foundation of the complete project because the environment and RL agent depend on clean and structured race data.

---

### 2. Environment Layer

The environment layer represents the Formula 1 race simulation system.

It includes:

- A custom F1 environment
- Race backend logic
- Race session management
- Race state representation
- Reward calculation
- Pit stop modeling
- Tyre degradation modeling
- Traffic modeling

This layer is responsible for simulating how a race progresses lap by lap and how the agent's decisions affect the final race outcome.

---

### 3. DQN Agent Layer

The DQN agent layer contains the reinforcement learning logic.

It includes:

- DQN agent implementation
- Neural network model
- Replay buffer
- Action masking logic

The DQN agent learns from interaction with the F1 environment. It stores experiences, trains a neural network, selects actions, and improves strategy over time.

---

### 4. Training Pipeline

The training pipeline contains the main training script for the DQN agent.

The training script connects:

- The F1 environment
- The DQN agent
- The replay buffer
- The neural network
- The checkpoint saving system

The goal of training is to allow the agent to learn better race strategies over many simulated episodes.

---

### 5. Evaluation Pipeline

The evaluation folder contains scripts for testing trained DQN models and comparing them with baseline strategies.

It includes:

- Evaluation of trained DQN models
- Evaluation of baseline DQN or rule-based approaches

This helps measure whether the trained agent is actually learning useful race strategies.

---

### 6. Checkpoint System

The project stores trained DQN model checkpoints in the `checkpoints/` directory.

The current checkpoint structure contains:

- `best.pt` — the best performing model checkpoint
- `latest.pt` — the latest saved model checkpoint
- `final.pt` — the final model after training completion

This allows training to be resumed, evaluated, and compared without retraining from the beginning.

---

### 7. Reports

The `reports/` folder currently contains the mid-evaluation report:

- `mid_eval_report_qc_3.pdf`

This report documents the progress made so far in the project.

---

### 8. Tests

The project includes a test file for checking the data layer pipeline:

- `test_data_layer_pipeline.py`

This helps ensure that the data layer works correctly and that race data can flow through the pipeline without breaking.

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
├── data/
│   ├── cache/
│   ├── exporters/
│   ├── models/
│   ├── processors/
│   ├── racerepository/
│   ├── sources/
│   ├── statebuilder/
│   ├── validators/
│   ├── __init__.py
│   └── config.py
│
├── env/
│   ├── data/
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
├── tests/
│   └── test_data_layer_pipeline.py
│
├── training/
│   └── train_dqn.py
│
├── .gitignore
├── README.md
└── pytest.ini