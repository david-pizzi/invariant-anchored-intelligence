# 🎯 Live Betting System

Forward-testing the IAI betting strategy with **timestamped predictions**.

## Strategy
- **Selection:** Home Win
- **Odds Range:** 4.0 - 6.0
- **Stake:** 3% of bankroll
- **Expected Edge:** +5.2%

## Workflow

### 1. Find Matches
```bash
# Check upcoming Premier League fixtures
python fetch_fixtures.py
```

Or check manually:
- [BBC Sport](https://www.bbc.co.uk/sport/football/premier-league/scores-fixtures)
- [Sky Bet](https://www.skybet.com/football/premier-league)
- [Bet365](https://www.bet365.com)

### 2. Add Predictions (BEFORE the match)
```bash
python add_prediction.py
```
- Enter match details
- Enter current home odds
- System checks if it qualifies (4.0-6.0)
- **Timestamp proves you predicted before result**

### 3. Check Results (AFTER matches)
```bash
python check_results.py
```
- Enter actual results
- System calculates profit/loss
- Updates bankroll

### 4. View Performance
```bash
python dashboard.py
```
- See all predictions
- Track win rate and ROI
- Monitor bankroll

## Files

| File | Purpose |
|------|---------|
| `predictions.json` | Database of all predictions |
| `add_prediction.py` | Add new prediction |
| `check_results.py` | Enter match results |
| `dashboard.py` | View performance |
| `fetch_fixtures.py` | Get upcoming matches |

## Why Timestamps Matter

Each prediction is stored with:
```json
{
  "created_at": "2026-01-16T14:30:00",
  "match_date": "2026-01-18",
  "match_time": "15:00",
  "home_team": "Crystal Palace",
  "away_team": "Liverpool",
  "odds": 5.5,
  "status": "pending"
}
```

This proves you made the prediction **before** the match, not after. 
It's the difference between backtesting and genuine forward-testing.

## Expected Performance

Based on 9 seasons of historical data:
- Win rate: ~26%
- ROI: +5-10% long term
- Profitable seasons: 7/9 (78%)

**Note:** Short-term results will be volatile. Need 50+ bets to assess.
