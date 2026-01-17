# IAI Betting Cloud System

Fully automated cloud-based betting tracker using Azure.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Functions                          │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Daily Tracker   │    │ HTTP Dashboard  │                │
│  │ (Timer: 18:00)  │    │ (View results)  │                │
│  └────────┬────────┘    └────────┬────────┘                │
│           │                      │                          │
│           ▼                      ▼                          │
│  ┌───────────────────────────────────────┐                 │
│  │         Azure Blob Storage            │                 │
│  │  - predictions.json                   │                 │
│  │  - history/YYYY-MM-DD.json            │                 │
│  └───────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Components

1. **Daily Tracker** (Timer Trigger @ 18:00 UK time)
   - Fetches latest odds from Football-Data.co.uk
   - Creates predictions for qualifying matches
   - Checks results for past matches
   - Updates bankroll

2. **Dashboard API** (HTTP Trigger)
   - View current predictions
   - Check performance stats
   - No authentication (read-only)

3. **Blob Storage**
   - `predictions.json` - Current state
   - `history/` - Daily snapshots for audit

## Setup

See [DEPLOYMENT.md](DEPLOYMENT.md) for setup instructions.
