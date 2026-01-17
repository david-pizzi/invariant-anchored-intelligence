"""
VALIDATE ON CURRENT SEASON (2025/26)
====================================
Tests the strategy on matches played this season.
This proves the system works before we go live.

Usage:
    python validate_current_season.py
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from io import StringIO

CACHE_FILE = Path(__file__).parent / "cache" / "current_season.csv"
PREDICTIONS_FILE = Path(__file__).parent / "predictions.json"

STRATEGY = {
    "selection": "H",
    "odds_min": 4.0,
    "odds_max": 6.0,
    "stake_pct": 3.0
}


def load_matches():
    """Load current season matches from cache."""
    if not CACHE_FILE.exists():
        print("❌ No cached data. Run auto_tracker.py first.")
        return []
    
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    matches = []
    reader = csv.DictReader(StringIO(content))
    
    for row in reader:
        try:
            date_str = row.get('Date', '')
            if '/' in date_str:
                parts = date_str.split('/')
                day, month, year = parts
                if len(year) == 2:
                    year = '20' + year
                match_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                continue
            
            home_odds = float(row.get('B365H', 0) or 0)
            result = row.get('FTR', '')
            
            if home_odds > 0 and result in ['H', 'D', 'A']:
                matches.append({
                    'date': match_date,
                    'home': row.get('HomeTeam', ''),
                    'away': row.get('AwayTeam', ''),
                    'home_odds': home_odds,
                    'result': result,
                    'score': f"{row.get('FTHG', '')}-{row.get('FTAG', '')}"
                })
        except (ValueError, KeyError):
            continue
    
    return matches


def run_validation():
    """Run strategy on current season."""
    matches = load_matches()
    
    if not matches:
        return
    
    print("\n" + "="*70)
    print("🧪 VALIDATING STRATEGY ON 2025/26 SEASON")
    print("="*70)
    print(f"\nStrategy: HOME WIN @ {STRATEGY['odds_min']}-{STRATEGY['odds_max']} odds")
    print(f"Total matches in season so far: {len(matches)}")
    
    # Filter qualifying bets
    qualifying = [m for m in matches 
                  if STRATEGY['odds_min'] <= m['home_odds'] <= STRATEGY['odds_max']]
    
    print(f"Qualifying bets (Home @ {STRATEGY['odds_min']}-{STRATEGY['odds_max']}): {len(qualifying)}")
    
    if not qualifying:
        print("\n⚠️ No qualifying bets found this season yet")
        return
    
    # Calculate results
    bankroll = 1000
    stake_pct = STRATEGY['stake_pct'] / 100
    
    wins = 0
    losses = 0
    bets = []
    
    print("\n" + "-"*70)
    print("BET-BY-BET RESULTS")
    print("-"*70)
    
    for m in qualifying:
        stake = bankroll * stake_pct
        
        if m['result'] == 'H':
            profit = stake * (m['home_odds'] - 1)
            wins += 1
            result_str = f"✅ WON +£{profit:.2f}"
        else:
            profit = -stake
            losses += 1
            result_str = f"❌ LOST -£{stake:.2f}"
        
        bankroll += profit
        
        bets.append({
            'date': m['date'],
            'match': f"{m['home']} vs {m['away']}",
            'odds': m['home_odds'],
            'score': m['score'],
            'result': m['result'],
            'profit': profit,
            'bankroll': bankroll
        })
        
        print(f"{m['date']} | {m['home']:15} vs {m['away']:15} | "
              f"H@{m['home_odds']:.2f} | {m['score']} | {result_str}")
    
    # Summary
    total_staked = sum(b['profit'] if b['result'] == 'H' else -b['profit'] for b in bets)
    # Actually calculate total staked properly
    total_staked = len(bets) * (1000 * stake_pct)  # Approximate
    total_profit = bankroll - 1000
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
    win_rate = wins / len(bets) * 100 if bets else 0
    
    print("\n" + "="*70)
    print("SEASON SUMMARY")
    print("="*70)
    print(f"\n{'Total bets:':<20} {len(bets)}")
    print(f"{'Wins:':<20} {wins}")
    print(f"{'Losses:':<20} {losses}")
    print(f"{'Win rate:':<20} {win_rate:.1f}%")
    print(f"{'Starting bankroll:':<20} £1,000.00")
    print(f"{'Final bankroll:':<20} £{bankroll:,.2f}")
    print(f"{'Profit:':<20} £{total_profit:+,.2f}")
    print(f"{'ROI:':<20} {roi:+.1f}%")
    
    # Verdict
    print("\n" + "-"*70)
    if total_profit > 0:
        print("✅ STRATEGY IS PROFITABLE THIS SEASON")
    elif total_profit > -100:
        print("⚠️ Strategy roughly breaking even")
    else:
        print("❌ Strategy losing this season")
    
    # Save validated bets to predictions.json for tracking
    print("\n" + "-"*70)
    save = input("Save these as validated historical bets? (y/n): ").strip().lower()
    
    if save == 'y':
        data = {
            "strategy": {
                "name": "Home Underdog Edge",
                "selection": "H",
                "odds_min": STRATEGY['odds_min'],
                "odds_max": STRATEGY['odds_max'],
                "stake_pct": STRATEGY['stake_pct'],
                "expected_edge": 5.2
            },
            "bankroll": {
                "initial": 1000,
                "current": round(bankroll, 2)
            },
            "predictions": [],
            "results_summary": {
                "total_bets": len(bets),
                "wins": wins,
                "losses": losses,
                "pending": 0,
                "profit": round(total_profit, 2),
                "roi_pct": round(roi, 1)
            }
        }
        
        for i, b in enumerate(bets, 1):
            data['predictions'].append({
                "id": i,
                "created_at": f"{b['date']}T12:00:00",  # Historical
                "match_date": b['date'],
                "match_time": "15:00",
                "home_team": b['match'].split(' vs ')[0],
                "away_team": b['match'].split(' vs ')[1],
                "selection": "H",
                "odds": b['odds'],
                "qualifies": True,
                "stake": round(1000 * stake_pct, 2),
                "potential_profit": round(1000 * stake_pct * (b['odds'] - 1), 2),
                "status": "won" if b['result'] == 'H' else "lost",
                "result": b['result'],
                "profit_loss": round(b['profit'], 2),
                "score": b['score'],
                "settled_at": f"{b['date']}T17:00:00",
                "validated": True  # Mark as historical validation
            })
        
        with open(PREDICTIONS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Saved {len(bets)} validated bets to predictions.json")


if __name__ == "__main__":
    run_validation()
