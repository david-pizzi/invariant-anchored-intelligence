# Strain Detection in IAI Challenger

## Overview

The Challenger component detects **invariant strain** using multiple signals, **not just regret**. It analyzes both performance degradation and behavioral instability to identify when the current invariants may be inadequate.

## Strain Signals

### 1. **Regret Slope Increasing** (High Severity)
- **What**: Measures if cumulative regret is accelerating over time
- **Detection**: `recent_slope > 1.5 × early_slope`
- **Why it matters**: Indicates the policy is getting worse, not just accumulating expected regret
- **Metric**: Compares regret growth rate in first 33% vs last window

### 2. **Reward Variance Spike** (Medium Severity)  
- **What**: Detects if reward variability increased substantially
- **Detection**: `recent_variance > 1.3 × early_variance`
- **Why it matters**: Suggests environment changed OR policy destabilized
- **Metric**: Compares reward variance in early vs recent windows

### 3. **Switch Rate Unstable** (Medium Severity)
- **What**: Measures if action-switching behavior is erratic
- **Detection**: `coefficient_of_variation > 0.2`
- **Why it matters**: Indicates exploration/exploitation balance issues
- **Metric**: Standard deviation / mean of rolling switch rate

### 4. **Post-Drift Recovery Slow** (High Severity)
- **What**: Checks if system failed to adapt after known distribution shift
- **Detection**: `mean_regret_after_drift > 0.3`
- **Why it matters**: Tests explicit adaptation capability
- **Metric**: Average instantaneous regret in recovery window after drift_step

## How It Works

```python
# Challenger.analyse() flow:
1. Compute strain signals from trajectory data
2. Generate critiques for each detected signal
3. Propose alternative metric formulations
4. Package evidence for Authority review
```

## Proposal Generation

When strain is detected, Challenger proposes alternatives:

- **regret_slope_increasing** → `regret_rate_penalty` metric
- **switch_rate_unstable** → `reward_with_stability` composite
- **reward_variance_spike** → `variance_regularized` objective
- **post_drift_recovery_slow** → `adaptive_window` formulation

## Key Insight

**Strain detection is multi-dimensional**: A system with good cumulative reward can still show strain through:
- Accelerating regret (degrading performance)
- Reward variance spikes (environmental changes)
- Switching instability (behavioral issues)

This ensures IAI responds to **early warning signals**, not just final performance collapse.
