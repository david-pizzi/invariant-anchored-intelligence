# IAI Bandit with LLM Authority (Version 2)

This version demonstrates the **complete IAI loop** with a local LLM acting as the Authority.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IAI Evolution Loop                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. OPTIMIZER (Bandit Policies)                            │
│     └─> Runs experiments, tries to maximize reward         │
│                                                             │
│  2. CHALLENGER (Strain Detector)                           │
│     └─> Analyzes performance, detects issues               │
│     └─> Proposes alternative metrics                       │
│                                                             │
│  3. AUTHORITY (Local LLM via Foundry)                      │
│     └─> Reviews evidence                                    │
│     └─> Decides: ACCEPT / REJECT / MODIFY                  │
│                                                             │
│  4. ORCHESTRATOR                                            │
│     └─> Manages generations                                 │
│     └─> Updates invariants if approved                     │
│     └─> Repeats                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Run with defaults (3 generations, small test)
python run_iai_evolution.py

# Full run (5 generations)
python run_iai_evolution.py --generations 5 --steps 10000

# Use stricter Authority
python run_iai_evolution.py --strictness strict

# Use better model (requires more memory)
python run_iai_evolution.py --model phi-3.5-mini
```

## What Happens

1. **Baseline Run**: Standard bandit algorithms (Thompson, UCB1, ε-greedy) run once
2. **Generation 0**: IAI system runs, Challenger analyzes, Authority reviews
3. **Generation 1**: If proposal accepted, runs with new invariants
4. **Generation N**: Continues until max generations or convergence

## Output

Results saved to `runs/iai_evolution/`:
- `EVOLUTION_REPORT.txt` - Summary of evolution path
- `authority_decisions.json` - All LLM decisions with prompts
- `generation_000/` - Each generation's data
  - `proposal.json` - Challenger's proposal
  - `decision.json` - Authority's decision
  - `invariants.json` - Current invariants
  - `trajectories/` - Raw performance data

## Key Differences from v1

**v1 (Pilot 0):**
- Manual comparison of policies
- No automatic invariant evolution
- Human decides what to change

**v2 (This version):**
- ✅ Automatic strain detection
- ✅ LLM-based decision making
- ✅ Multi-generation evolution
- ✅ Fully auditable (all decisions logged)
- ✅ Runs locally (no cloud APIs)

## Models Available

- `qwen2.5-0.5b` - Fastest, ~500MB, minimal resources
- `phi-3.5-mini` - Best reasoning, ~3GB
- `llama-3.2-1b` - Balanced, ~1.2GB

## Notes

- First run downloads model (~500MB for qwen)
- Foundry Local service auto-starts
- All inference runs locally on your machine
- No API keys or cloud costs
