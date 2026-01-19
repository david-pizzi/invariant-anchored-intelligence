# Safe IAI Deployment Guide

## Current Status ✅

✅ All IAI code committed to git (2 commits)
- `50bd24f` - IAI core framework
- `b900d0a` - Cloud V3 deployment

✅ Production V2 is **SAFE and RUNNING**
- URL: https://iai-betting-tracker.azurewebsites.net/api/dashboard
- 6 pending bets
- £1000 bankroll
- Timer runs daily at 18:00 UTC

✅ V3 is ready to deploy (but **NOT deployed yet**)
- Will create NEW function app: `iai-betting-tracker-v3`
- Uses same storage (shares predictions with V2)
- Easy rollback: just use V2 URL

## Deploy V3 (When Ready)

### Step 1: Navigate to V3 directory

```powershell
cd pilots/iai_betting/cloud-v3-iai
```

### Step 2: Deploy V3

```powershell
.\deploy-v3.ps1
```

This will:
1. Create `iai-betting-tracker-v3` function app
2. Configure settings (API keys, storage)
3. Deploy IAI-enhanced code
4. V2 remains untouched

**Expected output:**
```
╔══════════════════════════════════════════════════════════════╗
║                  DEPLOYMENT SUCCESSFUL!                      ║
╚══════════════════════════════════════════════════════════════╝

IAI V3 Endpoints:
  Dashboard: https://iai-betting-tracker-v3.azurewebsites.net/api/dashboard
  Run Now:   https://iai-betting-tracker-v3.azurewebsites.net/api/run_now
```

### Step 3: Test V3

```powershell
# Check dashboard
curl https://iai-betting-tracker-v3.azurewebsites.net/api/dashboard

# Should see:
# - Same 6 pending bets (shared storage)
# - IAI evaluation status
# - Active strategy (H1 initially)
```

### Step 4: Monitor Both (1 week)

**V2 (current production):**
```
https://iai-betting-tracker.azurewebsites.net/api/dashboard
```

**V3 (IAI-enhanced):**
```
https://iai-betting-tracker-v3.azurewebsites.net/api/dashboard
```

Both will:
- Use same storage
- See same bets
- Track same bankroll

Difference:
- V3 runs IAI evaluation weekly
- V3 adapts if better strategy found
- V2 always uses H1

### Step 5: After 1 Week

If V3 working well:
- Use V3 URL as primary
- Keep V2 as backup

If any issues:
- Keep using V2 URL
- No data lost (shared storage)
- Delete V3 if needed

## Rollback Plan (If Needed)

### Option 1: Quick Rollback (No Action Required)
Just keep using V2 URL - it never stopped working!

### Option 2: Delete V3

```powershell
az functionapp delete --name iai-betting-tracker-v3 --resource-group IAI
```

### Option 3: Redeploy V3 (If Fixing Issues)

```powershell
cd pilots/iai_betting/cloud-v3-iai
# Make fixes
git add .
git commit -m "Fix V3 issue"
git push

# Redeploy
func azure functionapp publish iai-betting-tracker-v3 --python
```

## What V3 Does Differently

### Week 1-3 (Stable Market)
- V2: Bets on H1 (Home @ 4-6 odds)
- V3: Bets on H1 (same - IAI validates it's best)
- **Result: Identical**

### Week 4 (Market Changes - Hypothetical)
- V2: Still bets H1 (loses money as edge disappeared)
- V3: IAI detects edge < 2%, switches to H3 or stops betting
- **Result: V3 protects capital, V2 loses money**

### Week 7 (First IAI Evaluation)
V3 automatically:
1. Loads last 6 months of data
2. Tests all 8 hypotheses
3. Authority reviews (edge > 2% invariant)
4. Keeps H1 if still best, switches if not
5. Logs decision in predictions.json

V2: Does nothing, keeps using H1

## IAI Features You Get

✅ **Continuous Learning**: Re-evaluates weekly
✅ **Automatic Adaptation**: Switches when better strategy appears
✅ **Capital Protection**: Stops betting if no edge
✅ **Multi-Strategy**: Can run portfolio (H1 + H3)
✅ **Hypothesis Tracking**: Full audit trail
✅ **Statistical Validation**: 95% CI, p-values

## Cost

- **Storage**: Same account (no extra cost)
- **V3 Function App**: Consumption plan (~£2-3/month)
- **Total**: <£5/month for both V2+V3

## Safety Checklist

Before deploying V3:

- [x] IAI code validated locally (5,618 historical matches)
- [x] All code committed to git (2 commits)
- [x] V2 production running and safe
- [x] V3 uses NEW function app (separate from V2)
- [x] Shared storage (easy comparison)
- [x] Rollback plan documented
- [x] Deploy script tested and ready

After deploying V3:

- [ ] V3 dashboard accessible
- [ ] V3 shows same 6 pending bets
- [ ] V3 run_now works
- [ ] V3 timer trigger configured
- [ ] V2 still working (verify)
- [ ] Monitor both for 7 days

## When to Switch to V3

✅ **Switch to V3 when:**
- Both running successfully for 7 days
- No errors in V3 logs
- Performance matches or exceeds V2
- IAI evaluation runs cleanly

⚠️ **Keep V2 if:**
- V3 has errors
- Unexpected behavior
- Want more testing time
- Risk-averse (totally fine!)

## Next Steps

**Right now:**
- Don't deploy yet if you want to wait
- Everything is safe in git
- V2 keeps running

**When ready:**
```powershell
cd pilots/iai_betting/cloud-v3-iai
.\deploy-v3.ps1
```

**Questions before deploying?**
- Test locally: `cd cloud-v3-iai; func start`
- Check logs: V3 has extensive logging
- Monitor: Both apps share storage

Your production system is **SAFE**. V3 is a **parallel deployment** for testing.
