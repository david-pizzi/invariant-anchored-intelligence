"""Multi-League Edge Analysis

Analyze if the home underdog edge (4.0-6.0) exists across multiple leagues.
This is LOCAL-ONLY research - does not touch cloud/production code.

Football-Data.co.uk leagues:
- E0: Premier League (England)
- E1: Championship (England) 
- E2: League One (England)
- E3: League Two (England)
- SC0: Scottish Premiership
- D1: Bundesliga (Germany)
- SP1: La Liga (Spain)
- I1: Serie A (Italy)
- F1: Ligue 1 (France)
- N1: Eredivisie (Netherlands)
- B1: Jupiler League (Belgium)
- P1: Primeira Liga (Portugal)
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Add the iai_betting directory to path for imports
iai_betting_dir = Path(__file__).parent.parent
sys.path.insert(0, str(iai_betting_dir))

from core.data import FootballDataLoader, Match


# Leagues to analyze - extend as needed
LEAGUES_TO_ANALYZE = {
    # Top 5 European leagues
    "E0": "Premier League",
    "D1": "Bundesliga", 
    "SP1": "La Liga",
    "I1": "Serie A",
    "F1": "Ligue 1",
    # English pyramid
    "E1": "Championship",
    "E2": "League One",
    # Others
    "SC0": "Scottish Prem",
    "N1": "Eredivisie",
    "B1": "Jupiler League",
    "P1": "Primeira Liga",
}

# Seasons to analyze (last 6-7 seasons typically available)
SEASONS = ["1718", "1819", "1920", "2021", "2122", "2223", "2324"]

# The edge we're testing (from EPL analysis)
EPL_VALIDATED_EDGE = {
    "selection": "H",
    "min_odds": 4.0,
    "max_odds": 6.0,
    "description": "Home underdog @ 4.0-6.0"
}


@dataclass
class LeagueStats:
    """Statistics for a league."""
    league_code: str
    league_name: str
    total_matches: int
    total_bets: int
    total_wins: int
    actual_win_rate: float
    implied_win_rate: float
    edge: float
    roi: float
    profitable_seasons: int
    total_seasons: int
    
    @property
    def edge_pct(self) -> str:
        return f"{self.edge * 100:+.1f}%"
    
    @property
    def roi_pct(self) -> str:
        return f"{self.roi * 100:+.1f}%"


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
        return {"n": 0, "wins": 0, "edge": 0, "roi": 0}
    
    wins = sum(1 for _, _, won in filtered if won)
    avg_odds = sum(odds for _, odds, _ in filtered) / len(filtered)
    implied = sum(1/odds for _, odds, _ in filtered) / len(filtered)
    actual = wins / len(filtered)
    
    # ROI = (avg_odds * win_rate) - 1
    roi = (actual * avg_odds) - 1
    
    return {
        "n": len(filtered),
        "wins": wins,
        "actual_rate": actual,
        "implied_rate": implied,
        "edge": actual - implied,
        "roi": roi,
        "avg_odds": avg_odds,
    }


def analyze_league(
    loader: FootballDataLoader,
    league_code: str,
    league_name: str,
    seasons: List[str],
    selection: str,
    min_odds: float,
    max_odds: float,
) -> Tuple[LeagueStats, Dict[str, Dict]]:
    """Analyze edge across all seasons for a league."""
    
    season_results = {}
    total_bets = 0
    total_wins = 0
    total_implied = 0
    total_matches = 0
    profitable_seasons = 0
    
    for season in seasons:
        try:
            matches = loader.load_season(league_code, season)
            if not matches:
                continue
                
            total_matches += len(matches)
            stats = analyze_odds_range(matches, selection, min_odds, max_odds)
            
            if stats["n"] > 0:
                season_results[season] = stats
                total_bets += stats["n"]
                total_wins += stats["wins"]
                total_implied += stats["implied_rate"] * stats["n"]
                
                if stats["edge"] > 0:
                    profitable_seasons += 1
                    
        except Exception as e:
            # League/season not available
            continue
    
    if total_bets == 0:
        return None, {}
    
    actual_rate = total_wins / total_bets
    implied_rate = total_implied / total_bets
    
    # Calculate overall ROI
    total_odds = sum(s.get("avg_odds", 0) * s.get("n", 0) for s in season_results.values())
    avg_odds = total_odds / total_bets if total_bets > 0 else 0
    roi = (actual_rate * avg_odds) - 1
    
    league_stats = LeagueStats(
        league_code=league_code,
        league_name=league_name,
        total_matches=total_matches,
        total_bets=total_bets,
        total_wins=total_wins,
        actual_win_rate=actual_rate,
        implied_win_rate=implied_rate,
        edge=actual_rate - implied_rate,
        roi=roi,
        profitable_seasons=profitable_seasons,
        total_seasons=len(season_results),
    )
    
    return league_stats, season_results


def print_league_summary(stats: LeagueStats, season_results: Dict[str, Dict]):
    """Print detailed results for a league."""
    print(f"\n{'='*70}")
    print(f"{stats.league_name} ({stats.league_code})")
    print(f"{'='*70}")
    print(f"Total matches: {stats.total_matches} | Qualifying bets: {stats.total_bets}")
    print(f"\n{'Season':<10} {'Bets':>6} {'Wins':>6} {'Actual':>8} {'Implied':>8} {'Edge':>8} {'ROI':>8}")
    print("-"*70)
    
    for season in sorted(season_results.keys()):
        s = season_results[season]
        marker = "✓" if s["edge"] > 0 else "✗"
        print(f"{season:<10} {s['n']:>6} {s['wins']:>6} "
              f"{s['actual_rate']*100:>7.1f}% {s['implied_rate']*100:>7.1f}% "
              f"{s['edge']*100:>+7.1f}% {s['roi']*100:>+7.1f}% {marker}")
    
    print("-"*70)
    edge_quality = "✓✓✓" if stats.edge > 0.03 else ("✓✓" if stats.edge > 0.01 else ("✓" if stats.edge > 0 else "✗"))
    print(f"{'OVERALL':<10} {stats.total_bets:>6} {stats.total_wins:>6} "
          f"{stats.actual_win_rate*100:>7.1f}% {stats.implied_win_rate*100:>7.1f}% "
          f"{stats.edge_pct:>8} {stats.roi_pct:>8} {edge_quality}")
    print(f"\nProfitable seasons: {stats.profitable_seasons}/{stats.total_seasons}")


def main():
    print("="*70)
    print("MULTI-LEAGUE EDGE ANALYSIS")
    print("="*70)
    print(f"\nTesting: {EPL_VALIDATED_EDGE['description']}")
    print(f"Selection: {EPL_VALIDATED_EDGE['selection']} @ {EPL_VALIDATED_EDGE['min_odds']}-{EPL_VALIDATED_EDGE['max_odds']}")
    print(f"Seasons: {SEASONS[0]} to {SEASONS[-1]}")
    print(f"\nDownloading and analyzing data... (this may take a minute)\n")
    
    loader = FootballDataLoader(data_dir="data/football")
    
    all_league_stats: List[LeagueStats] = []
    all_season_results: Dict[str, Dict] = {}
    
    for league_code, league_name in LEAGUES_TO_ANALYZE.items():
        print(f"\n--- Analyzing {league_name} ({league_code}) ---")
        
        stats, season_results = analyze_league(
            loader=loader,
            league_code=league_code,
            league_name=league_name,
            seasons=SEASONS,
            selection=EPL_VALIDATED_EDGE["selection"],
            min_odds=EPL_VALIDATED_EDGE["min_odds"],
            max_odds=EPL_VALIDATED_EDGE["max_odds"],
        )
        
        if stats:
            all_league_stats.append(stats)
            all_season_results[league_code] = season_results
    
    # Print detailed results for each league
    print("\n" + "="*70)
    print("DETAILED RESULTS BY LEAGUE")
    print("="*70)
    
    for stats in all_league_stats:
        print_league_summary(stats, all_season_results[stats.league_code])
    
    # Print comparison summary
    print("\n" + "="*70)
    print("LEAGUE COMPARISON SUMMARY")
    print("="*70)
    print(f"\n{'League':<20} {'Bets':>6} {'Win%':>8} {'Edge':>8} {'ROI':>8} {'Seasons':>10} {'Grade':>8}")
    print("-"*70)
    
    # Sort by edge (best first)
    for stats in sorted(all_league_stats, key=lambda x: x.edge, reverse=True):
        if stats.edge > 0.03:
            grade = "A (Strong)"
        elif stats.edge > 0.01:
            grade = "B (Good)"
        elif stats.edge > 0:
            grade = "C (Marginal)"
        else:
            grade = "D (None)"
        
        print(f"{stats.league_name:<20} {stats.total_bets:>6} "
              f"{stats.actual_win_rate*100:>7.1f}% {stats.edge_pct:>8} {stats.roi_pct:>8} "
              f"{stats.profitable_seasons:>3}/{stats.total_seasons:<3}    {grade:>8}")
    
    # Recommendations
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    
    strong_edges = [s for s in all_league_stats if s.edge > 0.03]
    good_edges = [s for s in all_league_stats if 0.01 < s.edge <= 0.03]
    marginal_edges = [s for s in all_league_stats if 0 < s.edge <= 0.01]
    no_edges = [s for s in all_league_stats if s.edge <= 0]
    
    if strong_edges:
        print(f"\n✓ STRONG EDGE (>3%): {', '.join(s.league_name for s in strong_edges)}")
        print("  → Consider adding to live tracking")
    
    if good_edges:
        print(f"\n◐ GOOD EDGE (1-3%): {', '.join(s.league_name for s in good_edges)}")
        print("  → Monitor, may need larger sample or adjusted parameters")
    
    if marginal_edges:
        print(f"\n○ MARGINAL EDGE (0-1%): {', '.join(s.league_name for s in marginal_edges)}")
        print("  → Probably not worth pursuing after transaction costs")
    
    if no_edges:
        print(f"\n✗ NO EDGE: {', '.join(s.league_name for s in no_edges)}")
        print("  → Strategy does not work in these leagues")
    
    # Cross-league edge exploration
    print("\n" + "="*70)
    print("ALTERNATIVE ODDS RANGES TO EXPLORE")
    print("="*70)
    print("\nIf the 4.0-6.0 range doesn't work well in some leagues,")
    print("run this with different parameters to find league-specific edges.")
    print("\nExamples to try:")
    print("  - Lower odds (2.5-3.5): Works in leagues with home advantage")
    print("  - Higher odds (6.0-10.0): Works if market undervalues big underdogs")
    print("  - Draw betting: Some leagues have more draws")


def explore_all_ranges(league_code: str = "D1", league_name: str = "Bundesliga"):
    """Explore all odds ranges for a specific league to find the best edge."""
    print("="*70)
    print(f"EXPLORING ALL ODDS RANGES FOR {league_name}")
    print("="*70)
    
    loader = FootballDataLoader(data_dir="data/football")
    
    # Load all matches
    all_matches = []
    for season in SEASONS:
        try:
            matches = loader.load_season(league_code, season)
            all_matches.extend(matches)
        except:
            pass
    
    print(f"\nTotal matches: {len(all_matches)}")
    
    # Test different ranges
    ranges = [
        ("H", 1.5, 2.0),
        ("H", 2.0, 2.5),
        ("H", 2.5, 3.0),
        ("H", 3.0, 4.0),
        ("H", 4.0, 6.0),  # Our default
        ("H", 6.0, 10.0),
        ("D", 3.0, 3.5),
        ("D", 3.5, 4.0),
        ("A", 2.0, 2.5),
        ("A", 2.5, 3.0),
        ("A", 3.0, 4.0),
    ]
    
    print(f"\n{'Selection':<10} {'Range':<12} {'Bets':>6} {'Win%':>8} {'Edge':>8} {'ROI':>8}")
    print("-"*60)
    
    results = []
    for selection, min_odds, max_odds in ranges:
        stats = analyze_odds_range(all_matches, selection, min_odds, max_odds)
        if stats["n"] >= 20:  # Minimum sample size
            results.append((selection, min_odds, max_odds, stats))
    
    # Sort by edge
    for selection, min_odds, max_odds, stats in sorted(results, key=lambda x: x[3]["edge"], reverse=True):
        marker = "✓✓✓" if stats["edge"] > 0.03 else ("✓" if stats["edge"] > 0 else "✗")
        print(f"{selection:<10} {min_odds:.1f}-{max_odds:.1f}     {stats['n']:>6} "
              f"{stats['actual_rate']*100:>7.1f}% {stats['edge']*100:>+7.1f}% {stats['roi']*100:>+7.1f}% {marker}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-league betting edge analysis")
    parser.add_argument("--explore", type=str, help="Explore all odds ranges for a specific league code (e.g., D1)")
    args = parser.parse_args()
    
    if args.explore:
        league_code = args.explore.upper()
        league_name = LEAGUES_TO_ANALYZE.get(league_code, league_code)
        explore_all_ranges(league_code, league_name)
    else:
        main()
