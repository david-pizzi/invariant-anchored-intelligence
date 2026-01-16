from __future__ import annotations
import numpy as np
import pandas as pd

class Evaluator:
    """External evaluator.

    - Has access to environment true means to compute regret.
    - Produces metrics for reporting.
    - Detects invariant violations (attempts to manipulate reward, budget exhaustion).
    """

    def __init__(self, true_means_fn, k: int, max_steps: int):
        # Store function that provides true arm reward probabilities at each timestep
        self.true_means_fn = true_means_fn
        # Number of bandit arms
        self.k = k
        # Maximum allowed steps (budget constraint)
        self.max_steps = max_steps
        # List to track any detected invariant violations
        self.violations = []

    def run(self, policy, env, steps: int, system_name: str) -> pd.DataFrame:
        # Initialize cumulative metrics
        cum_reward = 0  # Total reward accumulated
        cum_regret = 0.0  # Total regret accumulated
        last_arm = None  # Track previous arm selection for switch detection
        rows = []  # Store trajectory data

        for t in range(steps):
            # Check for budget exhaustion (invariant violation)
            if t >= self.max_steps:
                self.violations.append({
                    't': t,
                    'system': system_name,
                    'type': 'budget_exhaustion',
                    'description': f'Exceeded max steps {self.max_steps}'
                })
                break
            
            # Ask policy to select which arm to pull
            arm = int(policy.select_arm(t))
            
            # Validate arm selection (detect invalid arm indices as invariant violation)
            if arm < 0 or arm >= self.k:
                self.violations.append({
                    't': t,
                    'system': system_name,
                    'type': 'invalid_action',
                    'description': f'Selected arm {arm} out of bounds [0, {self.k})'
                })
                arm = min(max(0, arm), self.k - 1)  # Clip to valid range
            
            # Pull the selected arm and observe reward
            reward = int(env.pull(arm, t))
            # Let the policy learn from this observation
            policy.update(arm, reward)

            # Calculate regret (difference from optimal arm's expected reward)
            means = self.true_means_fn(t)  # Get true arm probabilities at this timestep
            optimal = float(np.max(means))  # Best possible expected reward
            inst_regret = optimal - float(means[arm])  # How much we lost by not choosing optimally
            cum_reward += reward  # Update cumulative reward
            cum_regret += inst_regret  # Update cumulative regret

            switched = int(last_arm is not None and arm != last_arm)
            last_arm = arm

            rows.append((t, system_name, arm, reward, cum_reward, inst_regret, cum_regret, switched))

        return pd.DataFrame(rows, columns=[
            "t","system","arm","reward","cum_reward","inst_regret","cum_regret","switched"
        ])

def summarise_run(df: pd.DataFrame, drift_step: int | None) -> dict:
    """Extract summary statistics from a single run's trajectory."""
    out = {}
    # Extract basic run information
    out["system"] = df["system"].iloc[0]  # Which policy was used
    out["steps"] = int(df["t"].max() + 1)  # Total timesteps
    out["cum_reward"] = int(df["cum_reward"].iloc[-1])  # Final cumulative reward
    out["cum_regret"] = float(df["cum_regret"].iloc[-1])  # Final cumulative regret
    out["switch_rate"] = float(df["switched"].mean())  # Fraction of steps where arm changed

    # If distribution drift occurred, measure recovery performance
    if drift_step is not None and drift_step < out["steps"]:
        post = df[df["t"] >= drift_step].copy()  # Get all steps after drift
        w = max(1, int(0.05 * len(post)))  # Window = first 5% of post-drift steps
        # Average regret in immediate recovery window
        out["post_drift_regret_mean_5pct"] = float(post["inst_regret"].head(w).mean())
        # Average regret across entire post-drift period
        out["post_drift_regret_mean_all"] = float(post["inst_regret"].mean())
    else:
        out["post_drift_regret_mean_5pct"] = np.nan
        out["post_drift_regret_mean_all"] = np.nan

    return out
