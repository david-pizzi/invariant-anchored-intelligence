from __future__ import annotations
from dataclasses import dataclass
import numpy as np

class Policy:
    name: str
    def reset(self, k: int, rng: np.random.Generator): ...
    def select_arm(self, t: int) -> int: ...
    def update(self, arm: int, reward: int): ...

@dataclass
class EpsilonGreedy(Policy):
    """Epsilon-greedy policy: explores randomly with probability epsilon, otherwise exploits best arm."""
    epsilon: float = 0.1  # Probability of random exploration
    name: str = "epsilon_greedy"

    def reset(self, k: int, rng: np.random.Generator):
        # Initialize for k arms
        self.k = k
        self.rng = rng
        self.counts = np.zeros(k, dtype=int)  # How many times each arm has been pulled
        self.values = np.zeros(k, dtype=float)  # Estimated mean reward for each arm

    def select_arm(self, t: int) -> int:
        # With probability epsilon, explore randomly
        if self.rng.random() < self.epsilon:
            return int(self.rng.integers(0, self.k))
        # Otherwise exploit: choose arm with highest estimated value
        return int(np.argmax(self.values))

    def update(self, arm: int, reward: int):
        # Update running average for the pulled arm
        self.counts[arm] += 1
        n = self.counts[arm]
        # Incremental mean update: new_mean = old_mean + (observation - old_mean) / n
        self.values[arm] += (reward - self.values[arm]) / n

@dataclass
class UCB1(Policy):
    """Upper Confidence Bound (UCB1): balances exploitation and exploration using confidence bounds."""
    name: str = "ucb1"

    def reset(self, k: int, rng: np.random.Generator):
        self.k = k
        self.rng = rng
        self.counts = np.zeros(k, dtype=int)  # Pull counts per arm
        self.values = np.zeros(k, dtype=float)  # Estimated mean rewards

    def select_arm(self, t: int) -> int:
        # Ensure each arm is tried at least once (initialization phase)
        for a in range(self.k):
            if self.counts[a] == 0:
                return a
        # Calculate upper confidence bounds: UCB = mean + sqrt(2*log(total_pulls) / arm_pulls)
        total = int(np.sum(self.counts))
        bonus = np.sqrt(2.0 * np.log(total) / self.counts)  # Exploration bonus (higher for less-tried arms)
        # Select arm with highest upper bound (optimism under uncertainty)
        return int(np.argmax(self.values + bonus))

    def update(self, arm: int, reward: int):
        # Update running average for pulled arm
        self.counts[arm] += 1
        n = self.counts[arm]
        self.values[arm] += (reward - self.values[arm]) / n

@dataclass
class ThompsonBernoulli(Policy):
    """Thompson Sampling: Bayesian approach that maintains belief distribution over arm parameters."""
    name: str = "thompson_bernoulli"

    def reset(self, k: int, rng: np.random.Generator):
        self.k = k
        self.rng = rng
        # Maintain Beta(alpha, beta) distribution for each arm's success probability
        self.alpha = np.ones(k, dtype=float)  # Success count + 1 (prior)
        self.beta = np.ones(k, dtype=float)   # Failure count + 1 (prior)

    def select_arm(self, t: int) -> int:
        # Sample a success probability from each arm's Beta distribution
        samples = self.rng.beta(self.alpha, self.beta)
        # Select arm with highest sampled value (probability matching)
        return int(np.argmax(samples))

    def update(self, arm: int, reward: int):
        # Update Beta distribution parameters based on observed reward
        if reward == 1:
            self.alpha[arm] += 1.0  # Observed success
        else:
            self.beta[arm] += 1.0   # Observed failure

@dataclass
class FixedPolicy(Policy):
    """Static baseline - no learning or adaptation.
    
    Selects a predetermined arm every time. This is Baseline B from the pilot spec.
    """
    arm: int = 0
    name: str = "fixed"
    
    def reset(self, k: int, rng: np.random.Generator):
        self.k = k
        self.rng = rng
        # Validate that predetermined arm is valid for this bandit
        if not hasattr(self, 'arm') or self.arm >= k:
            self.arm = 0  # Default to first arm if invalid
    
    def select_arm(self, t: int) -> int:
        # Always return the same fixed arm (no learning)
        return self.arm
    
    def update(self, arm: int, reward: int):
        # No learning or adaptation - static baseline for comparison
        pass

class IAIPolicySelector(Policy):
    """Meta-policy that selects among a fixed menu of base policies.

    This is a *bounded* form of recursive improvement:
    - The action space remains the bandit arms.
    - The selector only adapts its weights over base policies.
    - Reward is still sourced from the environment; the selector cannot redefine it.

    Implementation: EXP3 over policies (adversarial bandit over strategies).
    """

    def __init__(self, base_policies: list[Policy], gamma: float = 0.05, name: str = "iai_selector"):
        self.base_policies = base_policies
        self.gamma = float(gamma)
        self.name = name

    def reset(self, k: int, rng: np.random.Generator):
        self.k = k  # Number of bandit arms
        self.rng = rng
        # Initialize all base policies with same environment
        for p in self.base_policies:
            p.reset(k, rng)
        self.m = len(self.base_policies)  # Number of policies to choose from
        self.w = np.ones(self.m, dtype=float)  # EXP3 weights (start uniform)
        self.last_policy_idx = None  # Track which policy was selected
        # Audit logging for transparency and ICL analysis
        self.audit_log = []  # Records every policy selection and weight update

    def _policy_probs(self) -> np.ndarray:
        """Calculate probability distribution over policies using EXP3 formula."""
        # Mix weighted probabilities with uniform exploration (gamma)
        # This ensures all policies have minimum gamma/m probability
        probs = (1 - self.gamma) * (self.w / np.sum(self.w)) + (self.gamma / self.m)
        return probs

    def select_arm(self, t: int) -> int:
        # Calculate current probability distribution over policies
        probs = self._policy_probs()
        # Sample a policy according to these probabilities
        idx = int(self.rng.choice(self.m, p=probs))
        self.last_policy_idx = idx  # Remember which policy we chose
        # Log this decision to audit trail (for ICL Challenger analysis)
        self.audit_log.append({
            't': t,
            'event': 'policy_selection',
            'policy_idx': idx,
            'policy_name': self.base_policies[idx].name,
            'weights': self.w.copy(),  # Current EXP3 weights
            'probs': probs.copy()  # Probabilities used for selection
        })
        # Delegate arm selection to the chosen policy
        return int(self.base_policies[idx].select_arm(t))

    def update(self, arm: int, reward: int):
        # Let all base policies learn from this observation (shared experience)
        # Each policy maintains its own internal model
        for p in self.base_policies:
            p.update(arm, reward)

        # Update EXP3 weights to favor policies that perform well
        if self.last_policy_idx is None:
            return  # No update if we haven't selected a policy yet
        
        probs = self._policy_probs()
        p_sel = float(probs[self.last_policy_idx])  # Probability we selected this policy
        x_hat = reward / p_sel  # Importance-weighted reward estimate
        old_w = self.w[self.last_policy_idx]
        # Multiplicative weight update (EXP3 algorithm)
        self.w[self.last_policy_idx] *= np.exp((self.gamma * x_hat) / self.m)
        
        # Log weight change to audit trail
        self.audit_log.append({
            't': len(self.audit_log),  # Approximate timestep
            'event': 'weight_update',
            'policy_idx': self.last_policy_idx,
            'reward': reward,
            'old_weight': old_w,
            'new_weight': self.w[self.last_policy_idx],
            'delta': self.w[self.last_policy_idx] - old_w  # How much weight changed
        })
