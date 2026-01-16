from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class BernoulliBandit:
    means_pre: np.ndarray
    means_post: np.ndarray | None = None
    drift_step: int | None = None
    rng: np.random.Generator | None = None

    def __post_init__(self):
        self.means_pre = np.asarray(self.means_pre, dtype=float)
        if self.means_post is not None:
            self.means_post = np.asarray(self.means_post, dtype=float)
            if self.means_post.shape != self.means_pre.shape:
                raise ValueError("means_post must match means_pre shape")
        if self.rng is None:
            self.rng = np.random.default_rng()

    @property
    def k(self) -> int:
        return int(self.means_pre.shape[0])

    def true_means(self, t: int) -> np.ndarray:
        if self.means_post is None or self.drift_step is None:
            return self.means_pre
        return self.means_post if t >= self.drift_step else self.means_pre

    def pull(self, arm: int, t: int) -> int:
        means = self.true_means(t)
        p = float(means[arm])
        return int(self.rng.random() < p)

def make_random_bandit(k: int, rng: np.random.Generator, gap: float = 0.1):
    # Create a bandit with one clearly-best arm
    base = rng.uniform(0.05, 0.45, size=k)
    best = int(rng.integers(0, k))
    base[best] = min(0.95, base[best] + gap + float(rng.uniform(0, 0.25)))
    return base, best

def make_drift_pair(k: int, rng: np.random.Generator):
    pre, best_pre = make_random_bandit(k, rng)
    post, best_post = make_random_bandit(k, rng)
    return pre, post, best_pre, best_post
