# 🎉 Visual Dashboard Demo - What You Get!

## ✨ Two Beautiful Options

### 1. **Rich Terminal Dashboard** - LIVE NOW! ✅

Run with:
```bash
cd pilots/iai_bandit_poc
python run_iai_visual.py --generations 3 --steps 5000
```

**What you see:**

```
╔══════════════════════════════════════════════════════════════╗
║          IAI EVOLUTION WITH LLM AUTHORITY                    ║
╚══════════════════════════════════════════════════════════════╝

╭───────────────────── Configuration ─────────────────────╮
│  🎯 Generations         3                                │
│  📊 Steps per run       5000                             │
│  🔄 Runs per system     3                                │
│  🤖 LLM Model           qwen2.5-0.5b                     │
│  ⚖️  Strictness          balanced                         │
╰──────────────────────────────────────────────────────────╯

━━━ PHASE 1: BASELINE ━━━

✓ Baseline Complete

                Baseline Results                   
╭────────────────┬────────────┬────────────┬─────────╮
│ System         │ Avg Regret │ Avg Reward │ Status  │
├────────────────┼────────────┼────────────┼─────────┤
│ thompson       │      37.14 │    1259.00 │ 🏆 BEST │
│ ucb1           │     123.40 │    1161.50 │    ·    │
│ epsilon_greedy │      56.19 │    1246.50 │    ·    │
╰────────────────┴────────────┴────────────┴─────────╯

━━━ PHASE 2: EVOLUTION ━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERATION 0/2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

╭────────── Current Invariants ──────────╮
│ {                                      │
│   "metric": "cumulative_reward"        │
│ }                                      │
╰────────────────────────────────────────╯

✓ IAI Run Complete

╭──────────── IAI Performance ────────────╮
│ Avg Regret: 68.86                       │
│ Avg Reward: 1232.50                     │
│ vs Baseline: ↓ 85.4% worse              │
╰─────────────────────────────────────────╯

━━━ CHALLENGE PHASE ━━━

🔍 Challenger Analysis...

          Strain Signals Detected
╭────────────────────┬───────┬──────────────╮
│ Signal             │ Value │ Status       │
├────────────────────┼───────┼──────────────┤
│ switch_rate_mean   │ 0.332 │ ·            │
│ switch_rate_std    │ 0.204 │ ·            │
│ switch_rate_unstable│ True  │ ⚠️ TRIGGERED │
╰────────────────────┴───────┴──────────────╯

📋 Critiques:
╭──────── Critique 1: switch_rate_unstable ────────╮
│ Action switching rate exhibits high variance     │
│                                                   │
│ Severity: medium                                  │
╰───────────────────────────────────────────────────╯

💡 Proposed Changes:
╭────── Proposal 1: reward_with_stability ─────────╮
│ Weighted combination of reward and switching     │
│ penalty                                           │
│                                                   │
│ Rationale: High switching variance indicates     │
│ exploration-exploitation imbalance                │
╰───────────────────────────────────────────────────╯

🧠 LLM Authority Reviewing...
  (This may take 10-30 seconds)

✅ AUTHORITY DECISION: ACCEPT

╭────────── LLM Authority Decision ──────────╮
│ Confidence: 0.85                           │
│                                            │
│ Rationale:                                 │
│ The proposed metric effectively addresses  │
│ the drift issue. The switch rate shows    │
│ clear instability that needs correction.   │
│                                            │
│ Concerns:                                  │
│   • Monitor if stability penalty is too    │
│     aggressive                             │
╰────────────────────────────────────────────╯

🔄 Invariants Updated

╭────── Previous ──────╮  ╭────── Updated ───────╮
│ {                    │  │ {                    │
│   "metric":          │  │   "metric":          │
│   "cumulative_reward"│  │   "reward_with_      │
│ }                    │  │   stability"         │
│                      │  │ }                    │
╰──────────────────────╯  ╰──────────────────────╯
```

### 2. **Streamlit Web Dashboard** - ALSO AVAILABLE! 🌐

**Launch in two steps:**

Terminal 1 - Run evolution:
```bash
python run_iai_evolution.py --generations 5 --steps 10000
```

Terminal 2 - Start dashboard:
```bash
streamlit run dashboard_streamlit.py
```

Then open browser to: **http://localhost:8501**

**What you see:**
- 📈 **Overview Tab**: Interactive charts showing performance over generations
- 🎯 **Generations Tab**: Expandable panels for each generation with all details
- 🧠 **LLM Decisions Tab**: Full history of Authority decisions with color coding
- 📊 **Baseline Tab**: Comparison charts and tables
- 🔄 **Auto-refresh**: Dashboard updates every 5 seconds as evolution runs

**Screenshot equivalent:**
```
┌─────────────────────────────────────────────────────────────┐
│  🧠 IAI Evolution Dashboard                                 │
├─────────────────────────────────────────────────────────────┤
│  [Overview] [Generations] [LLM Decisions] [Baseline]        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Current Generation: 2      Current Regret: 45.23          │
│  Proposals Accepted: 1                                      │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │         Performance Evolution                    │       │
│  │                                                  │       │
│  │  Regret                                          │       │
│  │    70 │                                          │       │
│  │    60 │  ●                                       │       │
│  │    50 │     ╲                                    │       │
│  │    40 │        ●────●                            │       │
│  │    30 │         ̶ ̶ ̶ Best Baseline              │       │
│  │       └─────────────────────────────             │       │
│  │         Gen0  Gen1  Gen2                         │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │       Authority Decisions                        │       │
│  │                                                  │       │
│  │   1.0 │                                          │       │
│  │       │  [🟢]                                    │       │
│  │   0.5 │         [🔴]                             │       │
│  │       └─────────────────────────────             │       │
│  │         Gen0    Gen1                             │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
│  ✅ Generation 0: ACCEPTED                                 │
│  ┌─────────────────────────────────────────────────┐       │
│  │  Confidence: 0.85                                │       │
│  │  Rationale: The proposed metric effectively...   │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
│  ❌ Generation 1: REJECTED                                 │
│  ┌─────────────────────────────────────────────────┐       │
│  │  Confidence: 0.72                                │       │
│  │  Rationale: Evidence is not sufficient to...     │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 🎨 Color Coding

Both dashboards use:
- 🟢 **Green**: Accepted, Good, Success
- 🔴 **Red**: Rejected, Poor, Error
- 🟡 **Yellow**: Modified, Warning, Caution
- 🔵 **Blue**: Information, Current
- ⚪ **Gray**: Baseline, Reference

## 🚀 Quick Start Guide

### For Live Monitoring (Recommended):
```bash
cd pilots/iai_bandit_poc
python run_iai_visual.py --generations 3 --steps 5000
```

### For Web Analysis:
Terminal 1:
```bash
python run_iai_evolution.py --generations 5 --steps 10000
```

Terminal 2:
```bash
streamlit run dashboard_streamlit.py
```

## 💡 Pro Tips

1. **Rich Terminal** is faster and shows live progress beautifully
2. **Streamlit** is better for post-analysis and presentations
3. You can use **both**: Run with Rich, then open Streamlit to analyze results
4. All data is saved to `runs/iai_evolution/` regardless of which dashboard you use
5. Streamlit can show history from previous runs - just point it at the directory

## 📁 What Gets Saved

Both modes save the same files:
```
runs/iai_evolution/
├── baseline_results.json
├── authority_decisions.json
├── evolution_report.txt
└── generation_000/
    ├── invariants.json
    ├── iai_results.json
    ├── proposal.json
    └── decision.json
```

This means you can **run once, visualize twice**! 🎉
