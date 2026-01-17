"""TODAY'S BETS - The only output that matters.

This script tells you EXACTLY what to bet on right now.
No graphs. No theory. Just: BET THIS.

Usage:
    python todays_bets.py

Or with custom bankroll:
    python todays_bets.py --bankroll 500
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, date
from dataclasses import dataclass
from typing import List, Optional
import urllib.request
import csv
import io

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class TodaysBet:
    """A bet recommendation."""
    home_team: str
    away_team: str
    league: str
    selection: str
    odds: float
    stake: float
    potential_profit: float
    edge: float
    confidence: str


# The strategy from optimizer
STRATEGY = {
    "selection": "H",  # Home win
    "min_odds": 4.0,
    "max_odds": 6.0,
    "edge": 0.052,  # 5.2% historical edge
    "stake_pct": 3.0,
}


def get_current_fixtures() -> List[dict]:
    """
    Try to get current fixtures.
    
    In a real setup, this would connect to:
    - An odds API (Odds API, Betfair API)
    - A fixtures API (football-data.org)
    
    For now, returns sample data or prompts manual entry.
    """
    # Try to load from a local file first
    fixtures_file = Path(__file__).parent / "upcoming_fixtures.csv"
    
    if fixtures_file.exists():
        fixtures = []
        with open(fixtures_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fixtures.append(row)
        return fixtures
    
    return []


def find_qualifying_bets(fixtures: List[dict], bankroll: float) -> List[TodaysBet]:
    """Find bets that match our strategy."""
    bets = []
    
    for f in fixtures:
        home_odds = float(f.get('home_odds', f.get('B365H', 0)) or 0)
        
        if STRATEGY["min_odds"] <= home_odds < STRATEGY["max_odds"]:
            stake = bankroll * (STRATEGY["stake_pct"] / 100)
            potential_profit = stake * (home_odds - 1)
            
            # Determine confidence based on odds
            if 4.5 <= home_odds <= 5.5:
                confidence = "HIGH"  # Sweet spot
            elif 4.0 <= home_odds < 4.5 or 5.5 < home_odds < 6.0:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"
            
            bets.append(TodaysBet(
                home_team=f.get('home', f.get('HomeTeam', 'Unknown')),
                away_team=f.get('away', f.get('AwayTeam', 'Unknown')),
                league=f.get('league', 'Premier League'),
                selection="HOME WIN",
                odds=home_odds,
                stake=stake,
                potential_profit=potential_profit,
                edge=STRATEGY["edge"],
                confidence=confidence,
            ))
    
    return bets


def manual_entry(bankroll: float) -> List[TodaysBet]:
    """Manually enter today's fixtures."""
    print("\n" + "="*60)
    print("ENTER TODAY'S FIXTURES")
    print("="*60)
    print(f"\nLooking for: HOME teams with odds {STRATEGY['min_odds']} - {STRATEGY['max_odds']}")
    print("Enter 'done' when finished.\n")
    
    bets = []
    
    while True:
        home = input("Home team (or 'done'): ").strip()
        if home.lower() == 'done':
            break
        
        away = input("Away team: ").strip()
        
        try:
            home_odds = float(input("Home win odds: "))
        except ValueError:
            print("Invalid odds, skipping...")
            continue
        
        if STRATEGY["min_odds"] <= home_odds < STRATEGY["max_odds"]:
            stake = bankroll * (STRATEGY["stake_pct"] / 100)
            
            if 4.5 <= home_odds <= 5.5:
                confidence = "HIGH"
            else:
                confidence = "MEDIUM"
            
            bet = TodaysBet(
                home_team=home,
                away_team=away,
                league="Premier League",
                selection="HOME WIN",
                odds=home_odds,
                stake=stake,
                potential_profit=stake * (home_odds - 1),
                edge=STRATEGY["edge"],
                confidence=confidence,
            )
            bets.append(bet)
            print(f"  ✅ QUALIFIES! Bet £{stake:.2f} on {home}")
        else:
            print(f"  ❌ Doesn't qualify (odds {home_odds} not in {STRATEGY['min_odds']}-{STRATEGY['max_odds']})")
        
        print()
    
    return bets


def display_bets(bets: List[TodaysBet], bankroll: float):
    """Display the betting recommendations."""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*18 + "⚽ TODAY'S BETS ⚽" + " "*19 + "║")
    print("╚" + "═"*58 + "╝")
    print()
    
    if not bets:
        print("❌ NO QUALIFYING BETS TODAY")
        print()
        print("Strategy requires: Home team odds between 4.0 and 6.0")
        print("Check again when underdogs are playing at home.")
        return
    
    print(f"📅 Date: {date.today().strftime('%A, %d %B %Y')}")
    print(f"💰 Bankroll: £{bankroll:,.0f}")
    print(f"📊 Strategy: Home Win @ 4.0-6.0 odds (+5.2% edge)")
    print()
    print("─"*60)
    
    total_stake = 0
    
    for i, bet in enumerate(bets, 1):
        conf_emoji = "🟢" if bet.confidence == "HIGH" else "🟡"
        
        print(f"\n  BET #{i}: {conf_emoji} {bet.confidence} CONFIDENCE")
        print(f"  ├─ Match: {bet.home_team} vs {bet.away_team}")
        print(f"  ├─ Selection: {bet.selection}")
        print(f"  ├─ Odds: {bet.odds:.2f}")
        print(f"  ├─ Stake: £{bet.stake:.2f}")
        print(f"  └─ Potential Profit: £{bet.potential_profit:.2f}")
        
        total_stake += bet.stake
    
    print()
    print("─"*60)
    print(f"\n  TOTAL STAKE: £{total_stake:.2f}")
    print(f"  REMAINING:   £{bankroll - total_stake:.2f}")
    print()
    
    # Summary box
    print("╭" + "─"*58 + "╮")
    print("│" + " "*20 + "PLACE THESE BETS:" + " "*19 + "│")
    print("├" + "─"*58 + "┤")
    for bet in bets:
        line = f"  £{bet.stake:.0f} on {bet.home_team} to WIN @ {bet.odds:.2f}"
        print(f"│{line:<58}│")
    print("╰" + "─"*58 + "╯")
    print()
    
    # Disclaimer
    print("[Remember: Only bet what you can afford to lose]")
    print("[Historical edge: +5.2% over 9 seasons, but no guarantees]")


def main():
    parser = argparse.ArgumentParser(description="Get today's betting recommendations")
    parser.add_argument('--bankroll', type=float, default=1000.0, help='Your current bankroll')
    parser.add_argument('--manual', action='store_true', help='Manually enter fixtures')
    args = parser.parse_args()
    
    bankroll = args.bankroll
    
    print("\n" + "="*60)
    print("IAI BETTING - TODAY'S RECOMMENDATIONS")
    print("="*60)
    
    if args.manual:
        bets = manual_entry(bankroll)
    else:
        # Try to load fixtures
        fixtures = get_current_fixtures()
        
        if fixtures:
            print(f"\n✓ Loaded {len(fixtures)} fixtures from file")
            bets = find_qualifying_bets(fixtures, bankroll)
        else:
            print("\nNo fixtures file found.")
            print("Options:")
            print("  1. Create 'upcoming_fixtures.csv' with columns: home,away,home_odds")
            print("  2. Run with --manual to enter odds yourself")
            print()
            
            response = input("Enter odds manually now? (y/n): ").strip().lower()
            if response == 'y':
                bets = manual_entry(bankroll)
            else:
                bets = []
    
    display_bets(bets, bankroll)


if __name__ == "__main__":
    main()
