"""Challenger component for IAI Bandit PoC.

The Challenger:
- Detects invariant strain signals
- Generates evidence-based critiques
- Proposes alternative formulations
- Remains advisory-only (cannot enact changes)
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Any


class Challenger:
    """Detects invariant strain and generates advisory challenger outputs."""
    
    def __init__(
        self, 
        window_size: int = 1000, 
        drift_step: int | None = None,
        baseline_regret: float | None = None,
        # Configurable thresholds (for meta-improvement)
        thresholds: dict[str, float] | None = None
    ):
        # Size of rolling window for computing recent statistics
        self.window_size = window_size
        # Known distribution drift point (if applicable) for recovery analysis
        self.drift_step = drift_step
        # Baseline regret for absolute comparison (e.g., Thompson Sampling)
        self.baseline_regret = baseline_regret
        
        # Default thresholds - can be overridden for meta-improvement
        default_thresholds = {
            'regret_slope_ratio': 1.2,      # Flag if recent > ratio × early
            'switch_rate_std': 0.15,         # Flag if std > threshold
            'reward_var_ratio': 1.15,        # Flag if recent > ratio × early
            'post_drift_regret': 0.15,       # Flag if recovery regret > threshold
            'absolute_regret_ratio': 1.3,    # Flag if regret > ratio × baseline
        }
        self.thresholds = {**default_thresholds, **(thresholds or {})}
    
    def analyse(self, df: pd.DataFrame, system_name: str) -> dict[str, Any]:
        """Analyse trajectory for invariant strain signals.
        
        Returns:
            Dictionary with strain signals, critiques, and proposed alternatives
        """
        outputs = {
            'system': system_name,
            'strain_signals': self._detect_strain_signals(df),
            'critiques': [],
            'proposed_metrics': [],
            'evidence': {}
        }
        
        # Generate evidence-based critiques when strain signals are detected
        # Each critique identifies a potential inadequacy in current invariants
        signals = outputs['strain_signals']
        
        # Critique 1: Accelerating regret suggests current metric doesn't penalize this
        if signals['regret_slope_increasing']:
            outputs['critiques'].append({
                'severity': 'high',
                'signal': 'regret_slope_increasing',
                'description': 'Cumulative regret slope increased significantly in recent window',
                'evidence': {
                    'early_slope': signals['regret_slope_early'],
                    'recent_slope': signals['regret_slope_recent'],
                    'ratio': signals['regret_slope_recent'] / max(signals['regret_slope_early'], 1e-6)
                }
            })
        
        if signals['switch_rate_unstable']:
            outputs['critiques'].append({
                'severity': 'medium',
                'signal': 'switch_rate_unstable',
                'description': 'Action switching rate exhibits high variance',
                'evidence': {
                    'mean_switch_rate': signals['switch_rate_mean'],
                    'switch_rate_std': signals['switch_rate_std'],
                    'coefficient_of_variation': signals['switch_rate_std'] / max(signals['switch_rate_mean'], 1e-6)
                }
            })
        
        if signals['reward_variance_spike']:
            outputs['critiques'].append({
                'severity': 'medium',
                'signal': 'reward_variance_spike',
                'description': 'Reward variance increased substantially',
                'evidence': {
                    'early_variance': signals['reward_var_early'],
                    'recent_variance': signals['reward_var_recent'],
                    'ratio': signals['reward_var_recent'] / max(signals['reward_var_early'], 1e-6)
                }
            })
        
        if signals['post_drift_recovery_slow'] and self.drift_step is not None:
            outputs['critiques'].append({
                'severity': 'high',
                'signal': 'post_drift_recovery_slow',
                'description': 'System failed to recover quickly after distribution drift',
                'evidence': {
                    'recovery_window_regret': signals['post_drift_regret_mean'],
                    'drift_step': self.drift_step
                }
            })
        
        # Critique 5: Absolute regret significantly worse than baseline
        if signals.get('absolute_regret_high'):
            outputs['critiques'].append({
                'severity': 'high',
                'signal': 'absolute_regret_high',
                'description': 'Cumulative regret significantly exceeds baseline performance',
                'evidence': {
                    'cum_regret': signals['cum_regret'],
                    'baseline_regret': signals['baseline_regret'],
                    'ratio': signals['regret_vs_baseline_ratio'],
                    'threshold': self.thresholds['absolute_regret_ratio']
                }
            })
        
        # Propose alternative metric formulations if strain detected
        if len(outputs['critiques']) > 0:
            outputs['proposed_metrics'] = self._propose_alternatives(signals, outputs['critiques'])
        
        # Propose parameter changes based on observed behavior (ICL extension)
        outputs['proposed_parameter_changes'] = self._propose_parameter_changes(
            df, system_name, signals
        )
        
        # Collect evidence package
        outputs['evidence'] = {
            'total_steps': int(df['t'].max() + 1),
            'cum_reward': int(df['cum_reward'].iloc[-1]),
            'cum_regret': float(df['cum_regret'].iloc[-1]),
            'switch_rate': float(df['switched'].mean()),
            'strain_signal_count': sum(1 for k, v in signals.items() if isinstance(v, bool) and v)
        }
        
        return outputs
    
    def _detect_strain_signals(self, df: pd.DataFrame) -> dict[str, Any]:
        """Detect specific strain signals from pilot spec.
        
        Compares early vs recent behavior to identify degradation or instability.
        Uses configurable thresholds to support meta-improvement.
        """
        n = len(df)  # Total timesteps in trajectory
        signals = {}
        t = self.thresholds  # Shorthand for threshold access
        
        # 1. Increasing regret slope - indicates worsening performance over time
        early_end = min(self.window_size, n // 3)  # First portion of run
        recent_start = max(0, n - self.window_size)  # Last window_size steps
        
        # Split trajectory into early and recent windows
        early = df.iloc[:early_end]
        recent = df.iloc[recent_start:]
        
        # Compute regret slopes via linear regression (how fast regret grows)
        if len(early) > 1:
            early_slope = np.polyfit(early['t'], early['cum_regret'], 1)[0]  # Slope = regret/timestep
        else:
            early_slope = 0.0
        
        if len(recent) > 1:
            recent_slope = np.polyfit(recent['t'], recent['cum_regret'], 1)[0]
        else:
            recent_slope = 0.0
        
        signals['regret_slope_early'] = float(early_slope)
        signals['regret_slope_recent'] = float(recent_slope)
        # Flag if regret is accelerating (configurable threshold)
        signals['regret_slope_increasing'] = (
            recent_slope > t['regret_slope_ratio'] * early_slope and early_slope > 0
        )
        
        # 2. Excessive action switching - erratic behavior suggests exploration issues
        window_switches = df['switched'].rolling(window=min(100, n)).mean()  # Switching rate over time
        signals['switch_rate_mean'] = float(window_switches.mean())  # Average switching rate
        signals['switch_rate_std'] = float(window_switches.std())  # Variability in switching
        signals['switch_rate_unstable'] = signals['switch_rate_std'] > t['switch_rate_std']
        
        # 3. Reward variance spikes - environment may have changed or policy is destabilizing
        early_reward_var = early['reward'].var() if len(early) > 1 else 0.0
        recent_reward_var = recent['reward'].var() if len(recent) > 1 else 0.0
        
        signals['reward_var_early'] = float(early_reward_var)
        signals['reward_var_recent'] = float(recent_reward_var)
        # Flag if reward became significantly more variable (configurable threshold)
        signals['reward_variance_spike'] = (
            recent_reward_var > t['reward_var_ratio'] * early_reward_var and early_reward_var > 0
        )
        
        # 4. Post-drift recovery - measures adaptation speed after distribution shift
        if self.drift_step is not None and self.drift_step < n:
            post_drift = df[df['t'] >= self.drift_step]  # All steps after drift point
            recovery_window = min(self.window_size // 2, len(post_drift))  # Look at initial recovery period
            if recovery_window > 0:
                recovery_data = post_drift.head(recovery_window)  # First steps after drift
                recovery_regret = recovery_data['inst_regret'].mean()  # Average regret during recovery
                signals['post_drift_regret_mean'] = float(recovery_regret)
                # Flag slow recovery (configurable threshold)
                signals['post_drift_recovery_slow'] = recovery_regret > t['post_drift_regret']
            else:
                signals['post_drift_regret_mean'] = np.nan
                signals['post_drift_recovery_slow'] = False
        else:
            signals['post_drift_regret_mean'] = np.nan
            signals['post_drift_recovery_slow'] = False
        
        # 5. NEW: Absolute regret comparison to baseline
        # This catches cases where regret stabilizes at a bad level
        cum_regret = float(df['cum_regret'].iloc[-1])
        signals['cum_regret'] = cum_regret
        signals['baseline_regret'] = self.baseline_regret
        if self.baseline_regret is not None and self.baseline_regret > 0:
            regret_ratio = cum_regret / self.baseline_regret
            signals['regret_vs_baseline_ratio'] = regret_ratio
            signals['absolute_regret_high'] = regret_ratio > t['absolute_regret_ratio']
        else:
            signals['regret_vs_baseline_ratio'] = None
            signals['absolute_regret_high'] = False
        
        return signals
    
    def _propose_alternatives(self, signals: dict, critiques: list[dict]) -> list[dict]:
        """Propose alternative invariant formulations based on detected strain.
        
        These are advisory only - Challenger cannot implement them.
        External Authority must decide whether to adopt proposed changes.
        """
        proposals = []
        
        # Proposal 1: Add regret-rate penalty if regret is accelerating
        if signals.get('regret_slope_increasing'):
            proposals.append({
                'type': 'metric_modification',
                'name': 'regret_rate_penalty',
                'description': 'Add penalty for increasing regret rate over time',
                'formula': 'reward - lambda * max(0, d/dt[regret](t) - threshold)',
                'rationale': 'Current cumulative reward metric doesn\'t penalize accelerating regret'
            })
        
        # If switching unstable, propose stability-regularized objective
        if signals.get('switch_rate_unstable'):
            proposals.append({
                'type': 'composite_metric',
                'name': 'reward_with_stability',
                'description': 'Weighted combination of reward and switching penalty',
                'formula': 'alpha * reward - beta * switching_rate',
                'rationale': 'High switching variance indicates exploration-exploitation imbalance'
            })
        
        # If post-drift recovery slow, propose drift-aware evaluation
        if signals.get('post_drift_recovery_slow'):
            proposals.append({
                'type': 'evaluation_window',
                'name': 'post_drift_recovery_metric',
                'description': 'Evaluate recovery speed explicitly',
                'formula': 'integral(regret, t=drift_step, t=drift_step+window) / window',
                'rationale': 'Current metrics don\'t explicitly measure adaptation to distribution shift'
            })
        
        # Proposal 4: Baseline-relative performance if absolute regret is high
        if signals.get('absolute_regret_high'):
            baseline = signals.get('baseline_regret', 0)
            ratio = signals.get('regret_vs_baseline_ratio', 0)
            proposals.append({
                'type': 'baseline_comparison',
                'name': 'baseline_relative_regret',
                'description': f'Regret is {ratio:.1f}x baseline ({baseline:.1f}), consider fundamental approach change',
                'formula': 'regret / baseline_regret <= threshold',
                'rationale': 'System performance significantly worse than established baseline algorithms'
            })
        
        return proposals
    
    def _propose_parameter_changes(self, df: pd.DataFrame, system_name: str, signals: dict) -> list[dict]:
        """Propose parameter adjustments based on observed behavior.
        
        Analyzes performance patterns to suggest tuning for next run.
        Advisory only - cannot change parameters directly.
        Conforms to ICL Parameter Suggestion Extension spec.
        """
        suggestions = []
        
        # For epsilon-greedy: analyze exploration vs exploitation balance
        if system_name == 'epsilon_greedy':
            switch_rate = signals['switch_rate_mean']
            regret_slope = signals['regret_slope_recent']
            
            # Too much exploration (high switching, high regret)
            if switch_rate > 0.2 and regret_slope > 0.05:
                suggestions.append({
                    'parameter': 'epsilon',
                    'direction': 'decrease',
                    'suggested_values': [0.05, 0.07, 0.08],
                    'reason': f'High switching rate ({switch_rate:.3f}) with increasing regret suggests over-exploration',
                    'evidence': {
                        'switch_rate': switch_rate,
                        'regret_slope': regret_slope
                    }
                })
            # Too little exploration (low switching, increasing regret)
            elif switch_rate < 0.05 and signals.get('regret_slope_increasing'):
                suggestions.append({
                    'parameter': 'epsilon',
                    'direction': 'increase',
                    'suggested_values': [0.15, 0.20, 0.25],
                    'reason': f'Low switching rate ({switch_rate:.3f}) with increasing regret suggests under-exploration',
                    'evidence': {
                        'switch_rate': switch_rate,
                        'regret_slope': regret_slope
                    }
                })
        
        # For IAI selector: analyze meta-policy exploration parameter
        if system_name == 'iai_selector':
            switch_rate = signals['switch_rate_mean']
            regret = signals['regret_slope_recent']
            
            # Meta-policy switching too much (high gamma)
            if switch_rate > 0.4:
                suggestions.append({
                    'parameter': 'iai_gamma',
                    'direction': 'decrease',
                    'suggested_values': [0.01, 0.02, 0.03],
                    'reason': f'Very high policy switching rate ({switch_rate:.3f}) suggests excessive meta-exploration',
                    'evidence': {
                        'switch_rate': switch_rate,
                        'regret_slope': regret
                    }
                })
            # Meta-policy not exploring enough (stuck on one policy)
            elif switch_rate < 0.1 and signals.get('regret_slope_increasing'):
                suggestions.append({
                    'parameter': 'iai_gamma',
                    'direction': 'increase',
                    'suggested_values': [0.08, 0.10, 0.15],
                    'reason': f'Low policy switching rate ({switch_rate:.3f}) with increasing regret suggests meta-policy too greedy',
                    'evidence': {
                        'switch_rate': switch_rate,
                        'regret_slope': regret
                    }
                })
        
        # Post-drift recovery suggestions apply to all adaptive policies
        if signals.get('post_drift_recovery_slow') and system_name in ['epsilon_greedy', 'iai_selector']:
            if system_name == 'epsilon_greedy':
                suggestions.append({
                    'parameter': 'epsilon',
                    'direction': 'increase_slightly',
                    'suggested_values': [0.15, 0.20],
                    'reason': f'Slow post-drift recovery (regret={signals["post_drift_regret_mean"]:.3f}) suggests need for more exploration after environmental change',
                    'evidence': {
                        'post_drift_regret': signals['post_drift_regret_mean']
                    }
                })
            elif system_name == 'iai_selector':
                suggestions.append({
                    'parameter': 'iai_gamma',
                    'direction': 'increase_slightly',
                    'suggested_values': [0.08, 0.10],
                    'reason': f'Slow post-drift recovery (regret={signals["post_drift_regret_mean"]:.3f}) suggests meta-policy should explore alternative base policies more',
                    'evidence': {
                        'post_drift_regret': signals['post_drift_regret_mean']
                    }
                })
        
        return suggestions
