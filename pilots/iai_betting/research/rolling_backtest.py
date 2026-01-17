"""Rolling backtest - simulate real betting year by year.

Train on all previous seasons, bet on next season.
This simulates what you'd actually experience.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pilots.iai_betting.data import FootballDataLoader, Match
from typing import List, Dict


def simulate_season(
    matches: List[Match],
    selection: str,
    min_odds: float,
    max_odds: float,
    stake: float = 50.0,  # £50 per bet
) -> Dict:
    """Simulate betting on a season with fixed stake."""
    
    bets = []
    for m in matches:
        if selection == "H":
            odds = m.odds.home_odds
            won = m.result == "H"
        elif selection == "D":
            odds = m.odds.draw_odds
            won = m.result == "D"
        else:
            odds = m.odds.away_odds
            won = m.result == "A"
        
        if min_odds <= odds < max_odds:
            profit = stake * (odds - 1) if won else -stake
            bets.append({
                "odds": odds,
                "won": won,
                "stake": stake,
                "profit": profit,
            })
    
    if not bets:
        return {"n": 0, "profit": 0, "roi": 0}
    
    total_staked = sum(b["stake"] for b in bets)
    total_profit = sum(b["profit"] for b in bets)
    wins = sum(1 for b in bets if b["won"])
    
    return {
        "n": len(bets),
        "wins": wins,
        "win_rate": wins / len(bets),
        "staked": total_staked,
        "profit": total_profit,
        "roi": total_profit / total_staked if total_staked > 0 else 0,
    }


def main():
    print("="*70)
    print("ROLLING BACKTEST - HOME UNDERDOG STRATEGY")
    print("="*70)
    print("\nSimulating: Bet £50 on home teams @ 4.0-6.0 odds")
    print("This is what you'd experience betting season by season.\n")
    
    loader = FootballDataLoader()
    
    seasons = ["1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324"]
    all_matches = {}
    
    for season in seasons:
        try:
            matches = loader.load_season("E0", season)
            if matches:
                all_matches[season] = matches
        except:
            pass
    
    print(f"{'Season':<10} {'Bets':>6} {'Wins':>6} {'Win%':>8} {'Staked':>10} {'Profit':>10} {'ROI':>8}")
    print("-"*70)
    
    cumulative_profit = 0
    cumulative_staked = 0
    total_bets = 0
    total_wins = 0
    
    for season in sorted(all_matches.keys()):
        matches = all_matches[season]
        stats = simulate_season(matches, "H", 4.0, 6.0, stake=50.0)
        
        if stats["n"] > 0:
            cumulative_profit += stats["profit"]
            cumulative_staked += stats["staked"]
            total_bets += stats["n"]
            total_wins += stats["wins"]
            
            marker = "✓" if stats["profit"] > 0 else "✗"
            print(f"{season:<10} {stats['n']:>6} {stats['wins']:>6} {stats['win_rate']*100:>7.1f}% "
                  f"£{stats['staked']:>8.0f} £{stats['profit']:>+9.0f} {stats['roi']*100:>+7.1f}% {marker}")
    
    print("="*70)
    print(f"{'TOTAL':<10} {total_bets:>6} {total_wins:>6} {total_wins/total_bets*100:>7.1f}% "
          f"£{cumulative_staked:>8.0f} £{cumulative_profit:>+9.0f} {cumulative_profit/cumulative_staked*100:>+7.1f}%")
    
    print("\n" + "="*70)
    print("BANKROLL SIMULATION")
    print("="*70)
    print("\nStarting with £1000 bankroll, betting 5% per bet:")
    
    bankroll = 1000.0
    history = [bankroll]
    
    for season in sorted(all_matches.keys()):
        matches = all_matches[season]
        
        for m in matches:
            odds = m.odds.home_odds
            if 4.0 <= odds < 6.0:
                stake = bankroll * 0.05
                won = m.result == "H"
                
                if won:
                    bankroll += stake * (odds - 1)
                else:
                    bankroll -= stake
                
                history.append(bankroll)
    
    peak = max(history)
    trough = min(history[history.index(peak):]) if peak != history[-1] else history[-1]
    max_dd = (peak - trough) / peak * 100
    
    print(f"\nFinal bankroll: £{bankroll:.2f}")
    print(f"Total return: {(bankroll - 1000) / 1000 * 100:+.1f}%")
    print(f"Max drawdown: {max_dd:.1f}%")
    print(f"Peak bankroll: £{peak:.2f}")
    
    # Also test other strategy: Home @ 1.5-2.0
    print("\n" + "="*70)
    print("COMPARISON: HOME FAVORITES @ 1.5-2.0")
    print("="*70)
    
    bankroll2 = 1000.0
    for season in sorted(all_matches.keys()):
        matches = all_matches[season]
        
        for m in matches:
            odds = m.odds.home_odds
            if 1.5 <= odds < 2.0:
                stake = bankroll2 * 0.02  # Lower stake for more frequent bets
                won = m.result == "H"
                
                if won:
                    bankroll2 += stake * (odds - 1)
                else:
                    bankroll2 -= stake
    
    print(f"Final bankroll: £{bankroll2:.2f}")
    print(f"Total return: {(bankroll2 - 1000) / 1000 * 100:+.1f}%")


if __name__ == "__main__":
    main()
