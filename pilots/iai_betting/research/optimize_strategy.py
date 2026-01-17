"""Strategy Optimizer - Find the best betting parameters automatically.

Analyzes all combinations of selection/odds ranges and ranks them by:
- Overall edge (higher is better)
- Consistency (profitable in more seasons = more reliable)
- Sample size (more bets = more confidence)
- Recent performance (last 2 seasons matter more)

Outputs a recommended strategy with confidence level.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pilots.iai_betting.data import FootballDataLoader, Match


@dataclass
class StrategyResult:
    """Result of testing a strategy."""
    selection: str  # H, D, A
    min_odds: float
    max_odds: float
    total_bets: int
    total_wins: int
    win_rate: float
    implied_prob: float
    edge: float
    seasons_positive: int
    total_seasons: int
    recent_edge: float  # Last 2 seasons
    score: float  # Combined score


def analyze_strategy(
    matches: Dict[str, List[Match]],
    selection: str,
    min_odds: float,
    max_odds: float,
) -> StrategyResult:
    """Analyze a single strategy across all seasons."""
    
    season_results = {}
    total_bets = 0
    total_wins = 0
    implied_sum = 0
    
    for season, season_matches in matches.items():
        season_bets = 0
        season_wins = 0
        season_implied = 0
        
        for m in season_matches:
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
                season_bets += 1
                total_bets += 1
                season_implied += 1/odds
                implied_sum += 1/odds
                
                if won:
                    season_wins += 1
                    total_wins += 1
        
        if season_bets > 0:
            actual = season_wins / season_bets
            implied = season_implied / season_bets
            edge = actual - implied
            season_results[season] = {
                "bets": season_bets,
                "wins": season_wins,
                "edge": edge,
            }
    
    if total_bets == 0:
        return None
    
    # Calculate overall stats
    win_rate = total_wins / total_bets
    implied_prob = implied_sum / total_bets
    edge = win_rate - implied_prob
    
    # Count positive seasons
    seasons_positive = sum(1 for s in season_results.values() if s["edge"] > 0)
    total_seasons = len(season_results)
    
    # Recent performance (last 2 seasons)
    recent_seasons = sorted(season_results.keys())[-2:]
    recent_bets = sum(season_results[s]["bets"] for s in recent_seasons if s in season_results)
    recent_wins = sum(season_results[s]["wins"] for s in recent_seasons if s in season_results)
    
    if recent_bets > 0:
        recent_implied = sum(
            season_results[s]["bets"] * (implied_prob) 
            for s in recent_seasons if s in season_results
        ) / recent_bets
        recent_edge = (recent_wins / recent_bets) - recent_implied
    else:
        recent_edge = 0
    
    # Calculate combined score
    # Weights: edge (40%), consistency (30%), sample size (20%), recent (10%)
    consistency_score = seasons_positive / total_seasons if total_seasons > 0 else 0
    sample_score = min(1.0, total_bets / 300)  # 300 bets = max score
    recent_score = max(0, recent_edge * 10)  # Normalize
    
    score = (
        edge * 100 * 0.4 +          # Edge contribution
        consistency_score * 10 * 0.3 +  # Consistency contribution
        sample_score * 5 * 0.2 +     # Sample size contribution
        recent_score * 0.1           # Recent performance
    )
    
    return StrategyResult(
        selection=selection,
        min_odds=min_odds,
        max_odds=max_odds,
        total_bets=total_bets,
        total_wins=total_wins,
        win_rate=win_rate,
        implied_prob=implied_prob,
        edge=edge,
        seasons_positive=seasons_positive,
        total_seasons=total_seasons,
        recent_edge=recent_edge,
        score=score,
    )


def find_optimal_strategy(matches: Dict[str, List[Match]]) -> List[StrategyResult]:
    """Test all strategy combinations and rank them."""
    
    # Define search space
    selections = ["H", "D", "A"]
    odds_ranges = [
        (1.2, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0),
        (3.0, 3.5), (3.5, 4.0), (4.0, 5.0), (4.0, 6.0),
        (5.0, 7.0), (6.0, 10.0),
    ]
    
    results = []
    
    for selection in selections:
        for min_odds, max_odds in odds_ranges:
            result = analyze_strategy(matches, selection, min_odds, max_odds)
            if result and result.total_bets >= 50:  # Minimum sample size
                results.append(result)
    
    # Sort by score (descending)
    results.sort(key=lambda x: x.score, reverse=True)
    
    return results


def main():
    console = Console()
    
    console.print()
    console.print("╔" + "═" * 78 + "╗", style="bold cyan")
    console.print("║" + " " * 22 + "🎯 STRATEGY OPTIMIZER 🎯" + " " * 29 + "║", style="bold cyan")
    console.print("╚" + "═" * 78 + "╝", style="bold cyan")
    console.print()
    
    # Load all data
    loader = FootballDataLoader()
    seasons = ["1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324"]
    
    console.print("[yellow]Loading historical data...[/yellow]")
    matches = {}
    for season in seasons:
        try:
            data = loader.load_season("E0", season)
            if data:
                matches[season] = data
        except:
            pass
    
    console.print(f"[green]✓ Loaded {sum(len(m) for m in matches.values())} matches from {len(matches)} seasons[/green]\n")
    
    # Find optimal strategies
    console.print("[yellow]Analyzing all strategy combinations...[/yellow]\n")
    results = find_optimal_strategy(matches)
    
    # Display top strategies
    console.print("[bold cyan]📊 TOP 10 STRATEGIES (ranked by combined score)[/bold cyan]\n")
    
    table = Table(box=box.ROUNDED)
    table.add_column("Rank", style="bold", justify="center")
    table.add_column("Selection", justify="center")
    table.add_column("Odds Range", justify="center")
    table.add_column("Bets", justify="right")
    table.add_column("Win %", justify="right")
    table.add_column("Edge", justify="right")
    table.add_column("Consistency", justify="center")
    table.add_column("Recent", justify="right")
    table.add_column("Score", justify="right", style="bold")
    
    selection_names = {"H": "Home", "D": "Draw", "A": "Away"}
    
    for i, r in enumerate(results[:10], 1):
        edge_color = "green" if r.edge > 0.02 else "yellow" if r.edge > 0 else "red"
        recent_color = "green" if r.recent_edge > 0 else "red"
        consistency = f"{r.seasons_positive}/{r.total_seasons}"
        consistency_pct = r.seasons_positive / r.total_seasons if r.total_seasons > 0 else 0
        cons_color = "green" if consistency_pct >= 0.7 else "yellow" if consistency_pct >= 0.5 else "red"
        
        table.add_row(
            f"#{i}" if i > 1 else "🏆",
            selection_names[r.selection],
            f"{r.min_odds}-{r.max_odds}",
            str(r.total_bets),
            f"{r.win_rate*100:.1f}%",
            f"[{edge_color}]{r.edge*100:+.1f}%[/{edge_color}]",
            f"[{cons_color}]{consistency}[/{cons_color}]",
            f"[{recent_color}]{r.recent_edge*100:+.1f}%[/{recent_color}]",
            f"{r.score:.1f}",
        )
    
    console.print(table)
    
    # Recommendation
    best = results[0] if results else None
    
    if best:
        console.print()
        
        # Confidence level
        if best.edge > 0.03 and best.seasons_positive >= 6 and best.recent_edge > 0:
            confidence = "HIGH"
            conf_color = "green"
            conf_emoji = "🟢"
        elif best.edge > 0.02 and best.seasons_positive >= 5:
            confidence = "MEDIUM"
            conf_color = "yellow"
            conf_emoji = "🟡"
        else:
            confidence = "LOW"
            conf_color = "red"
            conf_emoji = "🔴"
        
        rec_text = f"""
[bold]RECOMMENDED STRATEGY[/bold]

Selection: [cyan]{selection_names[best.selection]}[/cyan] Win
Odds Range: [cyan]{best.min_odds} - {best.max_odds}[/cyan]

[bold]Why this strategy?[/bold]
• Historical edge: [green]{best.edge*100:+.1f}%[/green] above implied probability
• Win rate: {best.win_rate*100:.1f}% actual vs {best.implied_prob*100:.1f}% implied
• Consistency: Profitable in {best.seasons_positive}/{best.total_seasons} seasons ({best.seasons_positive/best.total_seasons*100:.0f}%)
• Sample size: {best.total_bets} historical bets
• Recent form: {best.recent_edge*100:+.1f}% edge in last 2 seasons

[bold]Confidence Level: [{conf_color}]{conf_emoji} {confidence}[/{conf_color}][/bold]
"""
        
        console.print(Panel(
            rec_text,
            title="[bold green]✅ OPTIMAL STRATEGY FOUND",
            border_style="green",
            padding=(1, 2),
        ))
        
        # Staking recommendation
        console.print()
        console.print("[bold cyan]💰 STAKING RECOMMENDATION[/bold cyan]\n")
        
        # Kelly criterion: edge / (odds - 1)
        avg_odds = (best.min_odds + best.max_odds) / 2
        kelly = best.edge / (avg_odds - 1) if avg_odds > 1 else 0
        
        console.print(f"  Full Kelly: {kelly*100:.1f}% of bankroll per bet")
        console.print(f"  Quarter Kelly (safer): {kelly*25:.1f}% of bankroll per bet")
        console.print(f"  Fixed stake (safest): 2-5% of bankroll per bet")
        console.print()
        console.print("[dim]  Note: Quarter Kelly is recommended for most bettors to reduce variance.[/dim]")
        
        # Output machine-readable config
        console.print()
        console.print("[bold cyan]📋 STRATEGY CONFIG (copy this)[/bold cyan]\n")
        
        config = f"""STRATEGY_CONFIG = {{
    "selection": "{best.selection}",  # H=Home, D=Draw, A=Away
    "min_odds": {best.min_odds},
    "max_odds": {best.max_odds},
    "stake_pct": {min(5, kelly*25*100):.1f},  # Quarter Kelly, capped at 5%
    "edge": {best.edge:.4f},
    "confidence": "{confidence}",
}}"""
        
        console.print(Panel(config, border_style="dim"))
    
    # Show strategies to AVOID
    console.print()
    console.print("[bold red]🚫 STRATEGIES TO AVOID[/bold red]\n")
    
    worst = [r for r in results if r.edge < -0.02][:5]
    if worst:
        for r in worst:
            console.print(f"  ❌ {selection_names[r.selection]} @ {r.min_odds}-{r.max_odds}: "
                         f"[red]{r.edge*100:.1f}%[/red] edge ({r.seasons_positive}/{r.total_seasons} seasons positive)")
    else:
        console.print("  No strongly negative strategies found in search space.")


if __name__ == "__main__":
    main()
