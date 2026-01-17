"""
ADD PREDICTION - Store a bet BEFORE the match kicks off
=========================================================
This creates a timestamped record that proves you predicted before the result.

Usage:
    python add_prediction.py
    
Then follow the prompts to enter match details.
"""

import json
import os
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


def add_prediction():
    """Interactive prompt to add a new prediction."""
    data = load_data()
    strategy = data['strategy']
    
    print("\n" + "="*60)
    print("📝 ADD NEW PREDICTION")
    print("="*60)
    print(f"\nStrategy: {strategy['name']}")
    print(f"Looking for: HOME WIN @ {strategy['odds_min']}-{strategy['odds_max']} odds")
    print(f"Current bankroll: £{data['bankroll']['current']:,.2f}")
    print()
    
    # Get match details
    print("Enter match details (or 'q' to quit):\n")
    
    home_team = input("Home team: ").strip()
    if home_team.lower() == 'q':
        return
        
    away_team = input("Away team: ").strip()
    if away_team.lower() == 'q':
        return
    
    # Get match date/time
    match_date = input("Match date (YYYY-MM-DD) [today]: ").strip()
    if not match_date:
        match_date = datetime.now().strftime("%Y-%m-%d")
    
    match_time = input("Kick-off time (HH:MM) [15:00]: ").strip()
    if not match_time:
        match_time = "15:00"
    
    # Get odds
    try:
        home_odds = float(input(f"Home win odds for {home_team}: "))
    except ValueError:
        print("❌ Invalid odds")
        return
    
    # Check if qualifies
    if home_odds < strategy['odds_min'] or home_odds > strategy['odds_max']:
        print(f"\n⚠️  Odds {home_odds} outside range {strategy['odds_min']}-{strategy['odds_max']}")
        confirm = input("Add anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Prediction not added.")
            return
        qualifies = False
    else:
        qualifies = True
    
    # Calculate stake
    stake = data['bankroll']['current'] * (strategy['stake_pct'] / 100)
    potential_profit = stake * (home_odds - 1)
    
    # Create prediction record
    prediction = {
        "id": len(data['predictions']) + 1,
        "created_at": datetime.now().isoformat(),
        "match_date": match_date,
        "match_time": match_time,
        "home_team": home_team,
        "away_team": away_team,
        "selection": "H",
        "odds": home_odds,
        "qualifies": qualifies,
        "stake": round(stake, 2),
        "potential_profit": round(potential_profit, 2),
        "status": "pending",
        "result": None,
        "profit_loss": None
    }
    
    # Show summary
    print("\n" + "-"*40)
    print("PREDICTION SUMMARY")
    print("-"*40)
    print(f"Match: {home_team} vs {away_team}")
    print(f"Date: {match_date} {match_time}")
    print(f"Selection: HOME WIN @ {home_odds}")
    print(f"Qualifies: {'✅ YES' if qualifies else '⚠️ NO (outside range)'}")
    print(f"Stake: £{stake:.2f}")
    print(f"Potential profit: £{potential_profit:.2f}")
    print("-"*40)
    
    confirm = input("\nSave this prediction? (y/n): ").strip().lower()
    if confirm == 'y':
        data['predictions'].append(prediction)
        data['results_summary']['pending'] += 1
        save_data(data)
        print(f"\n✅ Prediction #{prediction['id']} saved!")
        print(f"   Timestamp: {prediction['created_at']}")
    else:
        print("Prediction not saved.")


def show_pending():
    """Show all pending predictions."""
    data = load_data()
    pending = [p for p in data['predictions'] if p['status'] == 'pending']
    
    if not pending:
        print("\n📋 No pending predictions")
        return
    
    print("\n" + "="*60)
    print(f"📋 PENDING PREDICTIONS ({len(pending)})")
    print("="*60)
    
    for p in pending:
        qual = "✅" if p['qualifies'] else "⚠️"
        print(f"\n#{p['id']} | {p['match_date']} {p['match_time']}")
        print(f"   {p['home_team']} vs {p['away_team']}")
        print(f"   HOME @ {p['odds']} {qual} | Stake: £{p['stake']:.2f}")


def main():
    """Main menu."""
    while True:
        print("\n" + "="*60)
        print("🎯 LIVE PREDICTION TRACKER")
        print("="*60)
        print("\n1. Add new prediction")
        print("2. Show pending predictions")
        print("3. Quit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            add_prediction()
        elif choice == '2':
            show_pending()
        elif choice == '3':
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
