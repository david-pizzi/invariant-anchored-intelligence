"""
FETCH FIXTURES - Get upcoming Premier League matches with odds
==============================================================
Uses free APIs to get fixtures and odds.

Note: Free odds APIs are limited. For production, consider:
- The Odds API (free tier: 500 requests/month)
- Odds-API.com
- Manual entry from betting sites

Usage:
    python fetch_fixtures.py
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

PREDICTIONS_FILE = Path(__file__).parent / "predictions.json"

# Free football API (no odds, but has fixtures)
FOOTBALL_API = "https://www.thesportsdb.com/api/v1/json/3/eventsround.php"

# Premier League ID in TheSportsDB
PREMIER_LEAGUE_ID = "4328"


def load_data():
    """Load predictions database."""
    with open(PREDICTIONS_FILE, 'r') as f:
        return json.load(f)


def get_current_season():
    """Get current season string (e.g., '2025-2026')."""
    now = datetime.now()
    if now.month >= 8:  # Season starts in August
        return f"{now.year}-{now.year + 1}"
    else:
        return f"{now.year - 1}-{now.year}"


def fetch_upcoming_fixtures():
    """Fetch upcoming Premier League fixtures."""
    print("\n🔍 Fetching upcoming fixtures...")
    print("   (Using TheSportsDB free API - no odds data)")
    
    season = get_current_season()
    
    # Try to get next few rounds
    fixtures = []
    
    for round_num in range(1, 39):
        url = f"{FOOTBALL_API}?id={PREMIER_LEAGUE_ID}&r={round_num}&s={season}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                if data.get('events'):
                    for event in data['events']:
                        match_date = event.get('dateEvent', '')
                        match_time = event.get('strTime', '15:00:00')[:5]
                        
                        # Check if match is upcoming
                        try:
                            match_dt = datetime.strptime(f"{match_date} {match_time}", "%Y-%m-%d %H:%M")
                            if match_dt > datetime.now():
                                fixtures.append({
                                    'date': match_date,
                                    'time': match_time,
                                    'home': event.get('strHomeTeam', ''),
                                    'away': event.get('strAwayTeam', ''),
                                    'round': round_num
                                })
                        except:
                            pass
                    
                    # If we found upcoming matches, we can stop
                    if len(fixtures) >= 10:
                        break
                        
        except urllib.error.URLError as e:
            print(f"   ⚠️ Network error: {e}")
            break
        except Exception as e:
            continue
    
    return fixtures


def display_fixtures(fixtures):
    """Display fixtures and prompt for odds entry."""
    data = load_data()
    strategy = data['strategy']
    
    if not fixtures:
        print("\n❌ No upcoming fixtures found")
        print("   You may need to enter matches manually using add_prediction.py")
        return
    
    print(f"\n📅 UPCOMING FIXTURES ({len(fixtures)} found)")
    print("="*60)
    print(f"Looking for: HOME WIN @ {strategy['odds_min']}-{strategy['odds_max']} odds")
    print("="*60)
    
    for i, f in enumerate(fixtures[:10], 1):
        print(f"\n{i}. {f['date']} {f['time']}")
        print(f"   {f['home']} vs {f['away']}")
    
    print("\n" + "-"*60)
    print("To add a prediction with odds:")
    print("  1. Check betting site for current odds")
    print("  2. Run: python add_prediction.py")
    print("  3. Enter the match details and odds")
    print("-"*60)
    
    # Quick add option
    print("\nQuick add? Enter match number and home odds (e.g., '3 4.5')")
    print("Or press Enter to skip")
    
    choice = input("\n> ").strip()
    if choice:
        try:
            parts = choice.split()
            match_num = int(parts[0]) - 1
            odds = float(parts[1])
            
            if 0 <= match_num < len(fixtures):
                fixture = fixtures[match_num]
                
                # Check if qualifies
                qualifies = strategy['odds_min'] <= odds <= strategy['odds_max']
                stake = data['bankroll']['current'] * (strategy['stake_pct'] / 100)
                potential_profit = stake * (odds - 1)
                
                prediction = {
                    "id": len(data['predictions']) + 1,
                    "created_at": datetime.now().isoformat(),
                    "match_date": fixture['date'],
                    "match_time": fixture['time'],
                    "home_team": fixture['home'],
                    "away_team": fixture['away'],
                    "selection": "H",
                    "odds": odds,
                    "qualifies": qualifies,
                    "stake": round(stake, 2),
                    "potential_profit": round(potential_profit, 2),
                    "status": "pending",
                    "result": None,
                    "profit_loss": None
                }
                
                qual_str = "✅ QUALIFIES" if qualifies else "⚠️ Outside range"
                print(f"\n{fixture['home']} vs {fixture['away']}")
                print(f"HOME @ {odds} - {qual_str}")
                print(f"Stake: £{stake:.2f} | Potential: £{potential_profit:.2f}")
                
                confirm = input("\nSave? (y/n): ").strip().lower()
                if confirm == 'y':
                    data['predictions'].append(prediction)
                    data['results_summary']['pending'] += 1
                    with open(PREDICTIONS_FILE, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"✅ Prediction #{prediction['id']} saved!")
        except (ValueError, IndexError):
            print("Invalid input")


def main():
    fixtures = fetch_upcoming_fixtures()
    display_fixtures(fixtures)


if __name__ == "__main__":
    main()
