"""
AUTOMATED IAI BETTING SYSTEM
=============================
Fully automated: fetches odds, makes predictions, checks results.

Run this daily - it handles everything:
    python auto_tracker.py

What it does:
1. Fetches latest Premier League data (fixtures + odds)
2. Identifies qualifying bets (Home @ 4.0-6.0)
3. Stores predictions BEFORE matches kick off
4. Checks results for completed matches
5. Updates performance tracking
"""

import json
import csv
import urllib.request
import urllib.error
import os
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO

# Paths
SYSTEM_DIR = Path(__file__).parent
PREDICTIONS_FILE = SYSTEM_DIR / "predictions.json"
CACHE_DIR = SYSTEM_DIR / "cache"

# Football-Data.co.uk current season
CURRENT_SEASON_URL = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"

# Strategy parameters
STRATEGY = {
    "name": "Home Underdog Edge",
    "selection": "H",
    "odds_min": 4.0,
    "odds_max": 6.0,
    "stake_pct": 3.0,
    "expected_edge": 5.2
}


def load_predictions():
    """Load predictions database."""
    if not PREDICTIONS_FILE.exists():
        return {
            "strategy": STRATEGY,
            "bankroll": {"initial": 1000, "current": 1000},
            "predictions": [],
            "results_summary": {
                "total_bets": 0, "wins": 0, "losses": 0, 
                "pending": 0, "profit": 0, "roi_pct": 0
            },
            "last_updated": None
        }
    with open(PREDICTIONS_FILE, 'r') as f:
        return json.load(f)


def save_predictions(data):
    """Save predictions database."""
    data['last_updated'] = datetime.now().isoformat()
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def fetch_current_season_data():
    """Fetch current season data from Football-Data.co.uk."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / "current_season.csv"
    cache_meta = CACHE_DIR / "cache_meta.json"
    
    # Check if cache is fresh (less than 6 hours old)
    use_cache = False
    if cache_file.exists() and cache_meta.exists():
        with open(cache_meta, 'r') as f:
            meta = json.load(f)
        cache_time = datetime.fromisoformat(meta['fetched_at'])
        if datetime.now() - cache_time < timedelta(hours=6):
            use_cache = True
            print("   ✓ Using cached data (< 6 hours old)")
    
    if use_cache:
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        print("   ↓ Downloading latest data...")
        try:
            req = urllib.request.Request(
                CURRENT_SEASON_URL,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
            with open(cache_meta, 'w') as f:
                json.dump({'fetched_at': datetime.now().isoformat()}, f)
            print("   ✓ Downloaded and cached")
            
        except urllib.error.URLError as e:
            print(f"   ⚠️ Network error: {e}")
            if cache_file.exists():
                print("   → Using older cached data")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                return []
    
    # Parse CSV
    matches = []
    reader = csv.DictReader(StringIO(content))
    
    for row in reader:
        try:
            # Parse date (DD/MM/YYYY format)
            date_str = row.get('Date', '')
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    if len(year) == 2:
                        year = '20' + year
                    match_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    continue
            else:
                continue
            
            # Get odds
            home_odds = float(row.get('B365H', 0) or row.get('BWH', 0) or 0)
            
            # Get result if available
            result = row.get('FTR', '')  # H, D, A or empty
            
            matches.append({
                'date': match_date,
                'time': row.get('Time', '15:00'),
                'home': row.get('HomeTeam', ''),
                'away': row.get('AwayTeam', ''),
                'home_odds': home_odds,
                'result': result if result in ['H', 'D', 'A'] else None,
                'home_goals': row.get('FTHG', ''),
                'away_goals': row.get('FTAG', '')
            })
        except (ValueError, KeyError):
            continue
    
    return matches


def get_match_key(home, away, date):
    """Create unique key for a match."""
    return f"{date}_{home}_{away}".lower().replace(' ', '_')


def process_matches(data, matches):
    """Process matches: add new predictions, check results."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    
    existing_keys = {
        get_match_key(p['home_team'], p['away_team'], p['match_date'])
        for p in data['predictions']
    }
    
    new_predictions = 0
    results_updated = 0
    
    for match in matches:
        match_key = get_match_key(match['home'], match['away'], match['date'])
        home_odds = match['home_odds']
        
        # Skip if no odds data
        if home_odds <= 1:
            continue
        
        # Check if qualifies for our strategy
        qualifies = STRATEGY['odds_min'] <= home_odds <= STRATEGY['odds_max']
        
        # NEW PREDICTION: Match is upcoming and qualifies and not already tracked
        if match['date'] >= today and qualifies and match_key not in existing_keys:
            stake = data['bankroll']['current'] * (STRATEGY['stake_pct'] / 100)
            potential_profit = stake * (home_odds - 1)
            
            prediction = {
                "id": len(data['predictions']) + 1,
                "created_at": datetime.now().isoformat(),
                "match_date": match['date'],
                "match_time": match['time'] or "15:00",
                "home_team": match['home'],
                "away_team": match['away'],
                "selection": "H",
                "odds": home_odds,
                "qualifies": True,
                "stake": round(stake, 2),
                "potential_profit": round(potential_profit, 2),
                "status": "pending",
                "result": None,
                "profit_loss": None
            }
            
            data['predictions'].append(prediction)
            existing_keys.add(match_key)
            new_predictions += 1
            print(f"   📝 NEW: {match['home']} vs {match['away']} @ {home_odds}")
        
        # CHECK RESULT: Match has result and we have a pending prediction
        if match['result'] and match_key in existing_keys:
            for pred in data['predictions']:
                pred_key = get_match_key(pred['home_team'], pred['away_team'], pred['match_date'])
                if pred_key == match_key and pred['status'] == 'pending':
                    if match['result'] == 'H':
                        # We won!
                        profit = pred['stake'] * (pred['odds'] - 1)
                        pred['status'] = 'won'
                        pred['result'] = 'H'
                        pred['profit_loss'] = round(profit, 2)
                        pred['settled_at'] = datetime.now().isoformat()
                        pred['score'] = f"{match['home_goals']}-{match['away_goals']}"
                        print(f"   ✅ WON: {pred['home_team']} beat {pred['away_team']} +£{profit:.2f}")
                    else:
                        # We lost
                        pred['status'] = 'lost'
                        pred['result'] = match['result']
                        pred['profit_loss'] = -pred['stake']
                        pred['settled_at'] = datetime.now().isoformat()
                        pred['score'] = f"{match['home_goals']}-{match['away_goals']}"
                        print(f"   ❌ LOST: {pred['home_team']} vs {pred['away_team']} -£{pred['stake']:.2f}")
                    
                    results_updated += 1
                    break
    
    return new_predictions, results_updated


def update_summary(data):
    """Recalculate results summary."""
    predictions = data['predictions']
    
    wins = sum(1 for p in predictions if p['status'] == 'won')
    losses = sum(1 for p in predictions if p['status'] == 'lost')
    pending = sum(1 for p in predictions if p['status'] == 'pending')
    
    profit = sum(p['profit_loss'] or 0 for p in predictions)
    total_staked = sum(p['stake'] for p in predictions if p['status'] in ['won', 'lost'])
    roi = (profit / total_staked * 100) if total_staked > 0 else 0
    
    data['results_summary'] = {
        "total_bets": len(predictions),
        "wins": wins,
        "losses": losses,
        "pending": pending,
        "profit": round(profit, 2),
        "roi_pct": round(roi, 1)
    }
    
    data['bankroll']['current'] = round(data['bankroll']['initial'] + profit, 2)


def display_status(data):
    """Display current status."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box
        
        console = Console()
        
        # Header
        console.print()
        console.print(Panel.fit(
            "[bold cyan]🤖 IAI AUTOMATED BETTING TRACKER[/bold cyan]",
            border_style="cyan"
        ))
        
        # Strategy
        console.print(f"\n[bold]Strategy:[/bold] HOME WIN @ {STRATEGY['odds_min']}-{STRATEGY['odds_max']} odds")
        
        # Bankroll
        bankroll = data['bankroll']
        profit = bankroll['current'] - bankroll['initial']
        profit_color = "green" if profit >= 0 else "red"
        
        console.print(f"\n[bold]💰 Bankroll:[/bold] £{bankroll['current']:,.2f} ([{profit_color}]{profit:+.2f}[/{profit_color}])")
        
        # Summary
        s = data['results_summary']
        if s['wins'] + s['losses'] > 0:
            win_rate = s['wins'] / (s['wins'] + s['losses']) * 100
        else:
            win_rate = 0
        
        roi_color = "green" if s['roi_pct'] >= 0 else "red"
        console.print(f"[bold]📊 Record:[/bold] {s['wins']}W - {s['losses']}L ({s['pending']} pending)")
        console.print(f"[bold]📈 Win Rate:[/bold] {win_rate:.1f}% | [bold]ROI:[/bold] [{roi_color}]{s['roi_pct']:+.1f}%[/{roi_color}]")
        
        # Pending bets
        pending = [p for p in data['predictions'] if p['status'] == 'pending']
        if pending:
            console.print()
            table = Table(title=f"⏳ Pending Bets ({len(pending)})", box=box.ROUNDED)
            table.add_column("Date", style="cyan")
            table.add_column("Match")
            table.add_column("Odds", justify="right")
            table.add_column("Stake", justify="right")
            table.add_column("Pot. Win", justify="right", style="green")
            
            for p in pending:
                table.add_row(
                    p['match_date'],
                    f"{p['home_team']} vs {p['away_team']}",
                    f"{p['odds']:.2f}",
                    f"£{p['stake']:.2f}",
                    f"£{p['potential_profit']:.2f}"
                )
            console.print(table)
        
        # Recent results
        settled = [p for p in data['predictions'] if p['status'] in ['won', 'lost']]
        if settled:
            console.print()
            table = Table(title="📋 Recent Results (last 5)", box=box.ROUNDED)
            table.add_column("Date", style="dim")
            table.add_column("Match")
            table.add_column("Odds")
            table.add_column("Result")
            table.add_column("P/L", justify="right")
            
            for p in settled[-5:]:
                if p['status'] == 'won':
                    result_str = f"[green]✅ {p.get('score', 'W')}[/green]"
                    pl_str = f"[green]+£{p['profit_loss']:.2f}[/green]"
                else:
                    result_str = f"[red]❌ {p.get('score', 'L')}[/red]"
                    pl_str = f"[red]-£{abs(p['profit_loss']):.2f}[/red]"
                
                table.add_row(
                    p['match_date'],
                    f"{p['home_team']} vs {p['away_team']}",
                    f"{p['odds']:.2f}",
                    result_str,
                    pl_str
                )
            console.print(table)
        
        # Last updated
        if data.get('last_updated'):
            console.print(f"\n[dim]Last updated: {data['last_updated'][:19]}[/dim]")
        
        console.print()
        
    except ImportError:
        # Plain text fallback
        print("\n" + "="*60)
        print("🤖 IAI AUTOMATED BETTING TRACKER")
        print("="*60)
        s = data['results_summary']
        print(f"\nBankroll: £{data['bankroll']['current']:,.2f}")
        print(f"Record: {s['wins']}W - {s['losses']}L ({s['pending']} pending)")
        print(f"ROI: {s['roi_pct']:+.1f}%")
        print("="*60)


def run():
    """Main automated run."""
    print("\n🤖 IAI AUTOMATED BETTING SYSTEM")
    print("="*50)
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Strategy: Home @ {STRATEGY['odds_min']}-{STRATEGY['odds_max']} odds")
    print()
    
    # Load data
    print("1️⃣  Loading predictions database...")
    data = load_predictions()
    print(f"   ✓ {len(data['predictions'])} predictions loaded")
    
    # Fetch latest matches
    print("\n2️⃣  Fetching latest Premier League data...")
    matches = fetch_current_season_data()
    print(f"   ✓ {len(matches)} matches found")
    
    if not matches:
        print("\n⚠️ No match data available")
        return
    
    # Process matches
    print("\n3️⃣  Processing matches...")
    new_preds, updated = process_matches(data, matches)
    
    if new_preds == 0 and updated == 0:
        print("   ✓ No changes (all up to date)")
    else:
        print(f"   ✓ {new_preds} new predictions, {updated} results updated")
    
    # Update summary
    update_summary(data)
    
    # Save
    print("\n4️⃣  Saving...")
    save_predictions(data)
    print("   ✓ Saved to predictions.json")
    
    # Display status
    print("\n" + "="*50)
    display_status(data)


if __name__ == "__main__":
    run()
