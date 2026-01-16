# Quick Start Guide - Live Dashboard

## 🎯 Live Fixed Dashboard (No Scrolling!)

**Best for monitoring** - Everything visible at once, updates in place like `top` or `htop`.

```bash
cd pilots/iai_bandit_poc
python run_iai_live.py --generations 3 --steps 5000
```

**What you see:**
```
┌────────────────────────────────────────────────────────────────┐
│ 🧠 IAI EVOLUTION DASHBOARD                                     │
│ Phase: EVOLUTION - Generation 1                                │
│ Generation: 1/2                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ ┌─ Configuration ──┐  ┌─ IAI Performance ───┐                 │
│ │ 🎯 Generations: 3 │  │ Regret: 45.23       │                 │
│ │ 📊 Steps: 5000    │  │ Reward: 1254.50     │                 │
│ │ 🔄 Runs: 3        │  └─────────────────────┘                 │
│ │ 🤖 Model: qwen    │                                           │
│ └───────────────────┘  ┌─ Challenger ────────┐                 │
│                        │ ⚠️  Strain Detected  │                 │
│ ┌─ Baseline ────────┐ │ • switch_rate_unstbl │                 │
│ │ thompson    37 🏆 │ │                       │                 │
│ │ ucb1       123 ·  │ │ Proposal:            │                 │
│ │ eps_greedy  56 ·  │ │ reward_with_stability│                 │
│ └───────────────────┘ └──────────────────────┘                 │
│                                                                │
│                        ┌─ LLM Authority ──────┐                 │
│                        │ ✅ ACCEPT             │                 │
│                        │ Confidence: 0.85     │                 │
│                        │                       │                 │
│                        │ The proposed metric  │                 │
│                        │ effectively addresses│                 │
│                        │ the drift issue...   │                 │
│                        └──────────────────────┘                 │
├────────────────────────────────────────────────────────────────┤
│ Authority decision: ACCEPT                                     │
│ 10:45:23                                                       │
└────────────────────────────────────────────────────────────────┘
```

**This updates in place - NO SCROLLING!** ✨

---

## 📊 Viewing Results

After a run completes, all data is saved to `runs/iai_evolution/`:
- `baseline_results.json` - Baseline performance
- `authority_decisions.json` - All LLM decisions
- `evolution_report.txt` - Summary report
- `generation_XXX/` - Per-generation data

You can explore these JSON files directly or view the summary report.

---

## 🚀 Try It Now!

**For the best experience (fixed layout, no scrolling):**
```bash
cd pilots/iai_bandit_poc
python run_iai_live.py --generations 2 --steps 5000 --runs 3
```

Watch as the display **updates in place** showing:
- ✅ Current phase and generation
- ✅ Configuration and baseline results
- ✅ Live IAI performance
- ✅ Challenger analysis as it happens
- ✅ LLM Authority decision with reasoning
- ✅ All visible without scrolling!

When it finishes, you'll see a scrollable summary report, then it waits for you to press Enter.

---

## 💡 Pro Tip

Use `--steps 10000` for longer runs to see IAI adaptation better. Check the evolution report after completion for a summary of all changes across generations.
