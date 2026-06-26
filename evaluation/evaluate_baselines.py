import numpy as np

from env.f1_env import F1StrategyEnv
from agents.dqn.dqn_agent import DQNAgent, DQNConfig


ACTION_NAMES = {
    0: "stay out",
    1: "pit soft",
    2: "pit medium",
    3: "pit hard",
    4: "pit intermediate",
    5: "pit wet",
}


class RandomPolicy:
    """
    Baseline 1:
    Randomly choose any action from the environment action space.
    """

    name = "Random"

    def reset(self):
        pass

    def act(self, env, obs):
        return env.action_space.sample()


class AlwaysStayOutPolicy:
    """
    Baseline 2:
    Never pit. Always choose action 0.
    """

    name = "Always Stay Out"

    def reset(self):
        pass

    def act(self, env, obs):
        return 0


class OneStopHardPolicy:
    """
    Baseline 3:
    Simple one-stop dry strategy.

    Logic:
        - Stay out in early race.
        - Around mid race, if tyre age is large enough, pit once to hard.
        - After that, stay out.
    """

    name = "One Stop Hard"

    def __init__(self):
        self.has_pitted = False

    def reset(self):
        self.has_pitted = False

    def act(self, env, obs):
        current_lap = env.state.current_lap
        max_laps = env.max_laps
        tyre_age = env.state.tyre_age
        track_wetness = env.state.track_wetness

        # If track is wet, do not use this dry one-stop logic.
        if track_wetness > 0:
            return 0

        # Pit once around middle of race if tyres are old enough.
        if (
            not self.has_pitted
            and current_lap >= int(0.45 * max_laps)
            and tyre_age >= 15
        ):
            self.has_pitted = True
            return 3  # pit hard

        return 0


class RuleAwareHeuristicPolicy:
    """
    Baseline 4:
    A stronger hand-written F1 strategy.

    Logic:
        - Use wet/intermediate only when track wetness demands it.
        - Avoid repeated pit stops.
        - Pit once in dry race when tyre age is high.
        - If compound rule is not met near the end, pit to another dry compound.
    """

    name = "Rule Aware Heuristic"

    def __init__(self):
        self.last_pit_lap = -999

    def reset(self):
        self.last_pit_lap = -999

    def act(self, env, obs):
        current_lap = env.state.current_lap
        max_laps = env.max_laps
        tyre_age = env.state.tyre_age
        current_compound = env.state.tyre_compound
        track_wetness = env.state.track_wetness

        laps_remaining = max_laps - current_lap

        # Avoid pitting again immediately.
        if current_lap - self.last_pit_lap <= 3:
            return 0

        # Heavy wet condition: use wet tyre.
        if track_wetness >= 1.5 and current_compound != 4:
            self.last_pit_lap = current_lap
            return 5  # pit wet

        # Intermediate condition: use intermediate tyre.
        if 0 < track_wetness < 1.5 and current_compound != 3:
            self.last_pit_lap = current_lap
            return 4  # pit intermediate

        # Dry race logic.
        if track_wetness == 0:
            dry_used = env.compounds_used & {0, 1, 2}

            # If rule not met near end, force a dry compound change.
            if len(dry_used) < 2 and laps_remaining <= 8:
                if current_compound != 2:
                    self.last_pit_lap = current_lap
                    return 3  # pit hard
                else:
                    self.last_pit_lap = current_lap
                    return 2  # pit medium

            # Normal dry one-stop logic.
            if current_lap >= int(0.45 * max_laps) and tyre_age >= 18:
                if current_compound != 2:
                    self.last_pit_lap = current_lap
                    return 3  # pit hard
                else:
                    self.last_pit_lap = current_lap
                    return 2  # pit medium

        return 0


class DQNPolicy:
    """
    Trained DQN policy loaded from checkpoint.
    """

    def __init__(self, checkpoint_path):
        self.name = f"DQN ({checkpoint_path})"
        self.checkpoint_path = checkpoint_path
        self.agent = None

    def reset(self):
        pass

    def build_agent(self, seed):
        config = DQNConfig(
            obs_dim=15,
            action_dim=6,
            seed=seed,
        )

        self.agent = DQNAgent(config)
        self.agent.load(self.checkpoint_path)
        self.agent.online_net.eval()
        self.agent.target_net.eval()

    def act(self, env, obs):
        return self.agent.select_action(obs, evaluation=True)


def evaluate_policy(policy, episodes=20, seed=10_000):
    """
    Runs one policy for multiple episodes and returns summary metrics.
    """

    env = F1StrategyEnv()

    if isinstance(policy, DQNPolicy):
        policy.build_agent(seed)

    returns = []
    final_positions = []
    pit_counts = []
    rule_violations = []
    wet_tyre_on_dry_counts = []
    action_histories = []

    for episode in range(1, episodes + 1):
        policy.reset()

        obs, info = env.reset(seed=seed + episode)

        done = False
        episode_return = 0.0
        pit_count = 0
        wet_tyre_on_dry = 0
        actions = []

        while not done:
            action = policy.act(env, obs)

            actions.append(action)

            if action != 0:
                pit_count += 1

            obs, reward, terminated, truncated, info = env.step(action)

            done = terminated or truncated
            episode_return += reward

            # Check if wet/intermediate tyre is being used on dry track.
            if env.state.track_wetness == 0 and env.state.tyre_compound in [3, 4]:
                wet_tyre_on_dry += 1

        is_wet_race = any(w > 0 for w in env.track_wetness)
        dry_used = env.compounds_used & {0, 1, 2}
        violated_rule = (not is_wet_race and len(dry_used) < 2)

        returns.append(episode_return)
        final_positions.append(env.state.end_position)
        pit_counts.append(pit_count)
        rule_violations.append(int(violated_rule))
        wet_tyre_on_dry_counts.append(wet_tyre_on_dry)
        action_histories.append(actions)

    summary = {
        "policy": policy.name,
        "mean_return": float(np.mean(returns)),
        "mean_final_position": float(np.mean(final_positions)),
        "best_final_position": int(np.min(final_positions)),
        "worst_final_position": int(np.max(final_positions)),
        "mean_pit_count": float(np.mean(pit_counts)),
        "min_pit_count": int(np.min(pit_counts)),
        "max_pit_count": int(np.max(pit_counts)),
        "rule_violations": int(np.sum(rule_violations)),
        "mean_wet_tyre_on_dry_laps": float(np.mean(wet_tyre_on_dry_counts)),
        "sample_actions": action_histories[0],
    }

    return summary


def print_summary(summary):
    print("\n====================================")
    print("Policy:", summary["policy"])
    print("====================================")
    print("Mean return:", summary["mean_return"])
    print("Mean final position:", summary["mean_final_position"])
    print("Best final position:", summary["best_final_position"])
    print("Worst final position:", summary["worst_final_position"])
    print("Mean pit count:", summary["mean_pit_count"])
    print("Min pit count:", summary["min_pit_count"])
    print("Max pit count:", summary["max_pit_count"])
    print("Rule violations:", summary["rule_violations"])
    print("Mean wet/intermediate-on-dry laps:", summary["mean_wet_tyre_on_dry_laps"])
    print("Sample actions:", [ACTION_NAMES[a] for a in summary["sample_actions"]])


def main():
    episodes = 20
    seed = 10_000

    policies = [
        RandomPolicy(),
        AlwaysStayOutPolicy(),
        OneStopHardPolicy(),
        RuleAwareHeuristicPolicy(),
        DQNPolicy("checkpoints/final.pt"),
        DQNPolicy("checkpoints/latest.pt"),
        DQNPolicy("checkpoints/best.pt"),
    ]

    all_summaries = []

    for policy in policies:
        summary = evaluate_policy(
            policy=policy,
            episodes=episodes,
            seed=seed,
        )

        all_summaries.append(summary)
        print_summary(summary)

    print("\n\nFinal Comparison Table")
    print("======================")
    print(
        f"{'Policy':35s} | "
        f"{'Mean Return':>12s} | "
        f"{'Mean Pos':>8s} | "
        f"{'Mean Pits':>9s} | "
        f"{'Rule Viol':>9s}"
    )
    print("-" * 85)

    for s in all_summaries:
        print(
            f"{s['policy'][:35]:35s} | "
            f"{s['mean_return']:12.2f} | "
            f"{s['mean_final_position']:8.2f} | "
            f"{s['mean_pit_count']:9.2f} | "
            f"{s['rule_violations']:9d}"
        )


if __name__ == "__main__":
    main()