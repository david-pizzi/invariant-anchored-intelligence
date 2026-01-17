"""
CHECK RESULTS - Update predictions with actual match results
=============================================================
Run this after matches have finished to record wins/losses.

Usage:
    python check_results.py
"""

import json
from datetime import datetime
from pathlib import Path

PREDICTIONS_FILE = Path(__file__).parent / "predictions.json"


def load_data():
    """Load predictions database."""
    with open(PREDICTIONS_FILE, 'r') as f:
        return json.load(f)


def save_data(data):
    """Save predictions database."""
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def update_summary(data):
    """Recalculate results summary."""
    predictions = data['predictions']
    
    total = len(predictions)
    wins = sum(1 for p in predictions if p['status'] == 'won')
    losses = sum(1 for p in predictions if p['status'] == 'lost')
    pending = sum(1 for p in predictions if p['status'] == 'pending')
    
    profit = sum(p['profit_loss'] or 0 for p in predictions)
    total_staked = sum(p['stake'] for p in predictions if p['status'] in ['won', 'lost'])
    roi = (profit / total_staked * 100) if total_staked > 0 else 0
    
    data['results_summary'] = {
        "total_bets": total,
        "wins": wins,
        "losses": losses,
        "pending": pending,
        "profit": round(profit, 2),
        "roi_pct": round(roi, 1)
    }
    
    # Update bankroll
    data['bankroll']['current'] = round(data['bankroll']['initial'] + profit, 2)


def check_results():
    """Interactive prompt to enter results for pending predictions."""
    data = load_data()
    pending = [p for p in data['predictions'] if p['status'] == 'pending']
    
    if not pending:
        print("\n✅ No pending predictions to check")
        return
    
    print("\n" + "="*60)
    print(f"📊 CHECK RESULTS ({len(pending)} pending)")
    print("="*60)
    
    for pred in pending:
        print(f"\n#{pred['id']} | {pred['match_date']} {pred['match_time']}")
        print(f"   {pred['home_team']} vs {pred['away_team']}")
        print(f"   Prediction: HOME WIN @ {pred['odds']}")
        print(f"   Stake: £{pred['stake']:.2f}")
        
        print("\n   Result? (h=home win, a=away win, d=draw, s=skip, q=quit)")
        result = input("   > ").strip().lower()
        
        if result == 'q':
            break
        elif result == 's':
            continue
        elif result == 'h':
            # Home win - we won!
            profit = pred['stake'] * (pred['odds'] - 1)
            pred['status'] = 'won'
            pred['result'] = 'H'
            pred['profit_loss'] = round(profit, 2)
            pred['settled_at'] = datetime.now().isoformat()
            print(f"   ✅ WON! +£{profit:.2f}")
        elif result in ['a', 'd']:
            # Away win or draw - we lost
            pred['status'] = 'lost'
            pred['result'] = 'A' if result == 'a' else 'D'
            pred['profit_loss'] = -pred['stake']
            pred['settled_at'] = datetime.now().isoformat()
            print(f"   ❌ Lost -£{pred['stake']:.2f}")
        else:
            print("   ⚠️ Invalid input, skipping")
            continue
    
    # Update summary and save
    update_summary(data)
    save_data(data)
    
    print("\n" + "-"*40)
    print("UPDATED SUMMARY")
    print("-"*40)
    s = data['results_summary']
    print(f"Total bets: {s['total_bets']}")
    print(f"Wins: {s['wins']} | Losses: {s['losses']} | Pending: {s['pending']}")
    print(f"Profit: £{s['profit']:+.2f}")
    print(f"ROI: {s['roi_pct']:+.1f}%")
    print(f"Current bankroll: £{data['bankroll']['current']:,.2f}")


def main():
    check_results()


if __name__ == "__main__":
    main()
