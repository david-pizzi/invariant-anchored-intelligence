# IAI Bandit Proof of Concept

**Pilot 0**: Multi-Armed Bandit Domain  
**Status**: Active Development  
**Framework**: Invariant-Anchored Intelligence (IAI)

## Quick Start

### Run Experiment
```bash
python run_iai_live.py --generations 5 --runs 3
```

### View Results
All runs are saved in timestamped folders under `../../runs/iai_evolution/`:
- `RUN_INDEX.md` - Master index of all experiment runs
- Each run folder contains:
  - `ANALYSIS_REPORT.md` - Consolidated analysis with embedded plots
  - `evolution_history.csv` - Metrics data
  - `plots/` - Visualization PNG files

## Directory Structure

```
iai_bandit_poc/
├── run_iai_live.py          # Main entry point
├── requirements.txt         # Python dependencies
│
├── src/                     # Core implementation modules (11 files)
│   ├── orchestrator_live.py    # Main orchestrator with timestamped runs
│   ├── orchestrator.py         # Base orchestrator
│   ├── authority.py            # LLM Authority for decision-making
│   ├── challenger.py           # Strain detection and proposal generation
│   ├── evaluator.py            # Performance evaluation
│   ├── bandits.py              # Bandit environment
│   ├── policies.py             # Policy implementations
│   ├── dashboard_live.py       # Live terminal dashboard (Rich)
│   ├── dashboard_rich.py       # Rich terminal utilities
│   ├── dashboard_streamlit.py  # Experimental Streamlit dashboard
│   └── analyze_evolution.py    # Post-run analysis and reporting
│
├── docs/                    # Documentation (8 files)
│   ├── QUICK_START.md
│   ├── UNDERSTANDING_RESULTS.md
│   ├── STRAIN_DETECTION.md
│   ├── DASHBOARDS.md
│   ├── VISUAL_DASHBOARD_DEMO.md
│   ├── FIXES_SUMMARY.md
│   ├── README_v2.md
│   └── README.md (old)
│
└── runs/                    # Generated results (gitignored)
    └── iai_evolution/
        ├── RUN_INDEX.md
        └── [timestamped folders]
```

## What is IAI?

Invariant-Anchored Intelligence is a framework where:
1. **Invariants** define performance expectations/constraints
2. **Challenger** detects when invariants are strained
3. **Authority** (LLM) reviews proposals for invariant changes
4. **System evolves** through multiple generations

## Key Features

- **Timestamped Runs**: Each experiment saved in separate folder with timestamp
- **Master Index**: `RUN_INDEX.md` tracks all runs with parameters and results
- **Auto-Analysis**: Generates plots, CSV, JSON, and markdown reports automatically
- **Live Dashboard**: Real-time terminal UI showing evolution progress
- **Strain Detection**: Automated detection of performance degradation
- **LLM Authority**: GPT-4 class model reviews all proposed changes

## Command-Line Options

```bash
python run_iai_live.py [OPTIONS]

Options:
  --generations N       Number of evolution generations (default: 5)
  --steps N            Steps per bandit run (default: 5000)
  --runs N             Runs per generation (default: 3)
  --model MODEL        Foundry model name (default: qwen2.5-0.5b)
  --strictness LEVEL   Authority strictness: strict/balanced/lenient (default: balanced)
  --no-timestamp       Disable timestamped output folders
```

## Documentation

See [`docs/`](docs/) folder for detailed guides:
- **QUICK_START.md** - Get started quickly
- **UNDERSTANDING_RESULTS.md** - Interpret experiment results
- **STRAIN_DETECTION.md** - How strain detection works
- **DASHBOARDS.md** - Dashboard features and usage

## Results Location

Experimental results are stored in:
```
../../runs/iai_evolution/
├── RUN_INDEX.md              # Master index of all runs
├── runs_index.json           # JSON version for programmatic access
├── 2026-01-15_170050/        # Timestamped run folder
│   ├── ANALYSIS_REPORT.md    # Main consolidated report
│   ├── evolution_history.csv
│   ├── experiment_summary.json
│   ├── authority_decisions.json
│   ├── plots/
│   │   ├── regret_evolution.png
│   │   ├── regret_vs_baseline.png
│   │   ├── strain_and_decisions.png
│   │   └── evolution_dashboard.png
│   └── generation_*/         # Per-generation data
└── 2026-01-15_164300/        # Another run...
```

## Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- numpy
- pandas
- matplotlib
- rich (for terminal UI)
- azure-ai-inference (for LLM Authority)

## Related Documentation

- **White Paper**: `../../WHITE-PAPER.md` - Full IAI framework description
- **Proposal**: `../../PROPOSAL.md` - Research proposal
- **Context**: `../../context/` - Design documents and related work
