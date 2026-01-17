"""Quick test of the bandit pilot to verify it still works."""

import sys
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from bandits import BernoulliBandit, make_drift_pair
from policies import EpsilonGreedy, ThompsonBernoulli, UCB1
from evaluator import Evaluator, summarise_run
from challenger import Challenger

print('Testing bandit simulation...')

# Set up random generator
rng = np.random.default_rng(42)
k = 5
drift_step = 500
n_steps = 1000

# Create environment with drift using actual API
pre_means, post_means, best_pre, best_post = make_drift_pair(k=k, rng=rng)

def true_means_fn(t):
    """Return arm probabilities at timestep t."""
    return post_means if t >= drift_step else pre_means

# Create drifting bandit environment
class DriftingBandit:
    def __init__(self, pre, post, drift_step, rng):
        self.pre = pre
        self.post = post
        self.drift_step = drift_step
        self.rng = rng
    
    def pull(self, arm, t):
        means = self.post if t >= self.drift_step else self.pre
        return int(self.rng.random() < means[arm])

# Test policies
def create_policy(policy_class, k, rng, **kwargs):
    """Create and reset a policy."""
    policy = policy_class(**kwargs)
    policy.reset(k, rng)
    return policy

policies_to_test = [
    ('EpsilonGreedy', EpsilonGreedy, {'epsilon': 0.1}),
    ('Thompson', ThompsonBernoulli, {}),
    ('UCB1', UCB1, {}),
]

print('\nRunning 1000 steps per policy...')
for name, policy_class, kwargs in policies_to_test:
    # Fresh RNG and environment for each policy
    rng = np.random.default_rng(42)
    pre_means, post_means, _, _ = make_drift_pair(k=k, rng=rng)
    
    def true_means_fn(t, pre=pre_means, post=post_means):
        return post if t >= drift_step else pre
    
    env = DriftingBandit(pre_means, post_means, drift_step, rng)
    evaluator = Evaluator(true_means_fn=true_means_fn, k=k, max_steps=n_steps)
    policy = create_policy(policy_class, k, rng, **kwargs)
    
    df = evaluator.run(policy, env, steps=n_steps, system_name=name)
    summary = summarise_run(df, drift_step=drift_step)
    print(f'  {name}: reward={summary["cum_reward"]}, regret={summary["cum_regret"]:.2f}')

# Test challenger
print('\nTesting Challenger...')
rng = np.random.default_rng(42)
pre_means, post_means, _, _ = make_drift_pair(k=k, rng=rng)

def true_means_fn(t, pre=pre_means, post=post_means):
    return post if t >= drift_step else pre

env = DriftingBandit(pre_means, post_means, drift_step, rng)
evaluator = Evaluator(true_means_fn=true_means_fn, k=k, max_steps=n_steps)
policy = create_policy(ThompsonBernoulli, k, rng)
df = evaluator.run(policy, env, steps=n_steps, system_name='Thompson')

challenger = Challenger(window_size=200, drift_step=drift_step)
analysis = challenger.analyse(df, 'Thompson')

strain_count = sum(1 for k, v in analysis['strain_signals'].items() if isinstance(v, bool) and v)
print(f'  Strain signals detected: {strain_count}')
print(f'  Critiques: {len(analysis["critiques"])}')

print('\n✓ Bandit pilot functional test PASSED')
