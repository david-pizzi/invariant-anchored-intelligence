"""Analyze edge stability across different time periods.

This helps answer: Are the edges we found real, or just noise?
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pilots.iai_betting.data import FootballDataLoader, Match
from typing import List, Dict, Tuple


def analyze_odds_range(
    matches: List[Match], 
    selection: str, 
    min_odds: float, 
    max_odds: float
) -> Dict:
    """Analyze a specific selection/odds range."""
    
    filtered = []
    for m in matches:
        if selection == "H":
            odds = m.odds.home_odds
        elif selection == "D":
            odds = m.odds.draw_odds
        else:
            odds = m.odds.away_odds
        
        if min_odds <= odds < max_odds:
            filtered.append((m, odds, m.result == selection))
    
    if not filtered:
        return {"n": 0}
    
    wins = sum(1 for _, _, won in filtered if won)
    implied = sum(1/odds for _, odds, _ in filtered) / len(filtered)
    actual = wins / len(filtered)
    
    return {
        "n": len(filtered),
        "wins": wins,
        "actual_rate": actual,
        "implied_rate": implied,
        "edge": actual - implied,
        "roi": (actual * (sum(odds for _, odds, _ in filtered) / len(filtered)) - 1),
    }


def main():
    print("="*70)
    print("EDGE STABILITY ANALYSIS")
    print("="*70)
    
    loader = FootballDataLoader()
    
    # Load all available seasons
    seasons = ["1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324"]
    
    all_matches = {}
    for season in seasons:
        try:
            matches = loader.load_season("E0", season)
            if matches:
                all_matches[season] = matches
                print(f"Loaded {len(matches)} matches from {season}")
        except Exception as e:
            print(f"Failed to load {season}: {e}")
    
    print()
    
    # Key ranges to analyze (from our earlier findings)
    ranges_to_check = [
        ("H", 1.5, 2.0, "Home favorites"),
        ("H", 4.0, 6.0, "Home underdogs"),
        ("A", 3.0, 4.0, "Away value"),
        ("H", 2.0, 2.5, "Home mid-range (avoid?)"),
    ]
    
    for selection, min_odds, max_odds, label in ranges_to_check:
        print(f"\n{'='*60}")
        print(f"{label}: {selection} @ {min_odds}-{max_odds}")
        print("="*60)
        print(f"{'Season':<10} {'N':>5} {'Actual':>8} {'Implied':>8} {'Edge':>8} {'ROI':>8}")
        print("-"*60)
        
        total_n = 0
        total_wins = 0
        total_implied = 0
        
        for season, matches in sorted(all_matches.items()):
            stats = analyze_odds_range(matches, selection, min_odds, max_odds)
            
            if stats["n"] > 0:
                edge_str = f"{stats['edge']*100:+.1f}%"
                roi_str = f"{stats['roi']*100:+.1f}%"
                marker = "✓" if stats['edge'] > 0 else "✗"
                print(f"{season:<10} {stats['n']:>5} {stats['actual_rate']*100:>7.1f}% "
                      f"{stats['implied_rate']*100:>7.1f}% {edge_str:>8} {roi_str:>8} {marker}")
                
                total_n += stats["n"]
                total_wins += stats["wins"]
                total_implied += stats["implied_rate"] * stats["n"]
        
        if total_n > 0:
            overall_actual = total_wins / total_n
            overall_implied = total_implied / total_n
            overall_edge = overall_actual - overall_implied
            
            print("-"*60)
            edge_marker = "✓✓✓" if overall_edge > 0.03 else ("✓" if overall_edge > 0 else "✗")
            print(f"{'OVERALL':<10} {total_n:>5} {overall_actual*100:>7.1f}% "
                  f"{overall_implied*100:>7.1f}% {overall_edge*100:+.1f}%          {edge_marker}")
            
            # Count positive edge seasons
            positive_seasons = sum(1 for s, m in all_matches.items() 
                                   if analyze_odds_range(m, selection, min_odds, max_odds).get("edge", 0) > 0)
            print(f"Positive edge in {positive_seasons}/{len(all_matches)} seasons")


if __name__ == "__main__":
    main()
