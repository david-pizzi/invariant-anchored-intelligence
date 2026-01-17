# IAI Betting Pilot

Football betting system using Invariant-Anchored Intelligence.

## Quick Start

```bash
# View live dashboard
https://iai-betting-tracker.azurewebsites.net/api/dashboard?format=html
```

## Architecture

```
iai_betting/
├── cloud/                    # ✅ PRODUCTION - Azure Functions
│   ├── shared/               # Core logic
│   │   ├── storage.py        # Blob storage operations
│   │   ├── data.py           # Football-Data.co.uk integration
│   │   ├── odds_api.py       # The Odds API integration
│   │   └── authority.py      # IAI Authority (risk management)
│   ├── daily_tracker/        # Timer function (18:00 UTC)
│   ├── dashboard/            # HTTP endpoint (view results)
│   └── run_now/              # HTTP endpoint (manual trigger)
│
├── core/                     # Shared modules (data, strategies)
│   ├── data.py               # Data loading utilities
│   ├── strategies.py         # Strategy definitions
│   └── simulator.py          # Simulation engine
│
├── research/                 # Historical analysis & backtesting
│   ├── optimize_strategy.py  # Find best parameters
│   ├── rolling_backtest.py   # Season-by-season analysis
│   ├── analyze_edges.py      # Edge detection
│   ├── iai_evolution.py      # Static vs Adaptive comparison
│   └── honest_assessment.py  # When IAI helps/doesn't help
│
└── deprecated/               # Old/unused code (kept for reference)
```

## Strategy

**Validated Edge:** Home Win @ 4.0-6.0 odds
- Expected edge: +5.2%
- Win rate: ~26%
- 7/9 seasons profitable (2015-2024)

## IAI Authority Role

The Authority is a **GUARDIAN**, not an optimizer:

| ✅ Authority DOES | ❌ Authority DOESN'T |
|-------------------|----------------------|
| Reduce stake during losing streaks | Change odds range |
| Alert if win rate drops significantly | Adjust strategy parameters |
| Track edge decay over time | Market timing |
| Pause during severe drawdowns | Predict individual matches |

## Endpoints

| Function | URL |
|----------|-----|
| Dashboard | https://iai-betting-tracker.azurewebsites.net/api/dashboard?format=html |
| API (JSON) | https://iai-betting-tracker.azurewebsites.net/api/dashboard |
| Manual Run | POST https://iai-betting-tracker.azurewebsites.net/api/run_now |

## Costs

- Azure Functions: Free tier (1M executions/month)
- Blob Storage: ~£0.02/month
- The Odds API: Free tier (500 requests/month, we use ~30)
- **Total: < £1/month**
