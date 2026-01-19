# Cloud V3 - IAI-Enhanced Deployment

## What's Different from V2

**V2 (Current Production - `iai-betting-tracker`):**
- Fixed strategy: Home @ 4-6 odds
- Never adapts
- Works great in stable markets
- Vulnerable to market changes

**V3 (IAI-Enhanced - `iai-betting-tracker-v3`):**
- Full IAI framework integrated
- Re-evaluates all 8 hypotheses weekly
- Authority reviews and selects best strategy
- Adapts automatically when market changes
- Protects capital when edge disappears

## Safety Features

✅ **Separate Function App** - V3 deploys to new app, V2 keeps running
✅ **Shared Storage** - Both use same storage account (no data duplication)
✅ **Easy Rollback** - Just switch back to V2 URL if issues
✅ **Side-by-Side Testing** - Run both for a week to compare
✅ **Git Committed** - All code in version control

## Deployment

### Prerequisites

```powershell
# Must have Azure Functions Core Tools
npm install -g azure-functions-core-tools@4

# Must be logged in to Azure
az login
```

### Deploy V3

```powershell
cd cloud-v3-iai
.\deploy-v3.ps1
```

This will:
1. Create `iai-betting-tracker-v3` function app (V2 untouched)
2. Copy all settings from V2 (ODDS_API_KEY, storage)
3. Add IAI settings (ENABLE_IAI=true)
4. Deploy code using Azure Functions Core Tools
5. Verify deployment

### Test V3

```powershell
# Check dashboard
curl https://iai-betting-tracker-v3.azurewebsites.net/api/dashboard

# Run tracker manually
curl -X POST https://iai-betting-tracker-v3.azurewebsites.net/api/run_now

# View logs
az webapp log tail --name iai-betting-tracker-v3 --resource-group IAI
```

### Compare V2 vs V3

Both apps share the same storage, so they'll see the same predictions.

**Week 1-2: Monitor both**
- V2: https://iai-betting-tracker.azurewebsites.net/api/dashboard
- V3: https://iai-betting-tracker-v3.azurewebsites.net/api/dashboard

**Week 3: If V3 stable**
- Switch production to V3
- Keep V2 as backup

**If Issues: Rollback**
- Just use V2 URL again
- Delete V3 function app
- No data lost (shared storage)

## IAI Features in V3

### Weekly Evaluation Cycle

Every 7 days, V3 automatically:

1. **Loads historical data** (last 6 months)
2. **Tests all 8 hypotheses** using Evaluator
3. **Authority reviews** with invariant (edge > 2%)
4. **Adapts if needed**:
   - If H3 now better than H1 → switches to H3
   - If ALL fail → stops betting (no edge)
   - If H1 still best → keeps H1

### Adaptation Tracking

All adaptations logged in predictions.json:

```json
{
  "iai_adaptations": [
    {
      "timestamp": "2026-01-26T10:00:00Z",
      "from": "H1",
      "to": "H3",
      "reason": "Edge improved: 4.2%",
      "evaluation": {...}
    }
  ]
}
```

### Dashboard Updates

V3 dashboard shows:
- Current active strategy
- Last IAI evaluation date
- Adaptation history
- Edge for each hypothesis
- Authority decisions

## Configuration

Environment variables in V3:

```
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
ODDS_API_KEY=27e87733ca9b5e5022d6ead4aebb3b55
ENABLE_IAI=true
IAI_EVALUATION_INTERVAL_DAYS=7
```

## Files Added for IAI

```
cloud-v3-iai/
├── shared/
│   ├── iai_core/           # Full IAI framework
│   │   ├── __init__.py
│   │   ├── hypotheses.py   # 8 betting strategies
│   │   ├── evaluator.py    # Empirical testing
│   │   ├── authority.py    # Invariant checking
│   │   ├── challenger.py   # Hypothesis management
│   │   └── orchestrator.py # Complete loop
│   └── iai_tracker.py      # IAI integration
├── requirements.txt        # Added: pandas, scipy, numpy
└── deploy-v3.ps1          # Safe deployment script
```

## Rollback Plan

If V3 has issues:

```powershell
# Option 1: Quick rollback (just use V2 URL)
# Nothing to do - V2 still running

# Option 2: Delete V3
az functionapp delete --name iai-betting-tracker-v3 --resource-group IAI

# Option 3: Fix and redeploy V3
cd cloud-v3-iai
# Make fixes
func azure functionapp publish iai-betting-tracker-v3 --python
```

## Cost

V3 uses same consumption plan as V2:
- **Storage**: Same account (no extra cost)
- **Functions**: Pay-per-execution
- **Expected**: <£5/month total for both V2+V3

## Testing Checklist

Before switching production:

- [ ] V3 deployed successfully
- [ ] Dashboard accessible
- [ ] Run Now works
- [ ] Timer trigger executes daily
- [ ] Predictions stored correctly
- [ ] IAI evaluation runs weekly
- [ ] No errors in logs
- [ ] Run side-by-side with V2 for 7 days
- [ ] Compare performance

## Current Status

- ✅ IAI code committed to git (50bd24f)
- ✅ V2 production running (iai-betting-tracker)
- 🔄 V3 ready to deploy (iai-betting-tracker-v3)
- 📊 6 pending bets in V2
- 💰 £1000 bankroll safe
