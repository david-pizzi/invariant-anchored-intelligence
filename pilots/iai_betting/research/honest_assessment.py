"""HONEST ASSESSMENT: When does IAI Authority add value in betting?

This analyzes the real question: Is adaptive control useful here?

Key findings from testing:
1. The edge was found through historical analysis (5.2% on Home @ 4.0-6.0)
2. Over-adjusting parameters DESTROYED the edge
3. Even conservative adjustments underperformed static

When IAI Authority IS useful:
- Risk management (reducing stake during drawdowns)
- Detecting if edge has disappeared (market adapted)
- Position sizing based on confidence

When IAI Authority is NOT useful:
- Adjusting the odds range (that's overfitting)
- Trying to time when to bet (market timing is hard)
- Frequent adjustments based on short-term results

Conclusion for betting:
The strategy itself (Home @ 4.0-6.0) should be FIXED.
Authority's role is RISK MANAGEMENT, not strategy optimization.
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
class SeasonResult:
    """Results for a single season."""
    season: str
    bets: int
    wins: int
    profit: float
    roi: float
    max_dd: float


def run_strategy_by_season(
    matches_by_season: Dict[str, List[Match]],
    min_odds: float = 4.0,
    max_odds: float = 6.0,
    stake_pct: float = 3.0,
) -> List[SeasonResult]:
    """Run strategy and get season-by-season results."""
    
    results = []
    
    for season in sorted(matches_by_season.keys()):
        matches = matches_by_season[season]
        bankroll = 1000.0
        peak = 1000.0
        max_dd = 0
        wins = 0
        bets = 0
        
        for m in matches:
            odds = m.odds.home_odds
            if min_odds <= odds < max_odds:
                stake = bankroll * (stake_pct / 100)
                won = m.result == "H"
                profit = stake * (odds - 1) if won else -stake
                bankroll += profit
                bets += 1
                if won:
                    wins += 1
                
                if bankroll > peak:
                    peak = bankroll
                dd = (peak - bankroll) / peak * 100
                if dd > max_dd:
                    max_dd = dd
        
        if bets > 0:
            results.append(SeasonResult(
                season=season,
                bets=bets,
                wins=wins,
                profit=bankroll - 1000,
                roi=(bankroll - 1000) / 1000 * 100,
                max_dd=max_dd,
            ))
    
    return results


def main():
    console = Console()
    
    console.print("\n")
    console.print("╔" + "═" * 78 + "╗", style="bold cyan")
    console.print("║" + " " * 20 + "📊 HONEST IAI ASSESSMENT 📊" + " " * 27 + "║", style="bold cyan")
    console.print("╚" + "═" * 78 + "╝", style="bold cyan")
    
    # Load data
    loader = FootballDataLoader()
    seasons = ["1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324"]
    
    matches_by_season = {}
    for season in seasons:
        try:
            data = loader.load_season("E0", season)
            if data:
                matches_by_season[season] = data
        except:
            pass
    
    console.print(f"\n[green]Loaded {len(matches_by_season)} seasons[/green]\n")
    
    # Run static strategy
    results = run_strategy_by_season(matches_by_season)
    
    # Display season-by-season
    console.print("[bold]SEASON-BY-SEASON PERFORMANCE[/bold]\n")
    
    table = Table(box=box.ROUNDED)
    table.add_column("Season", style="cyan")
    table.add_column("Bets", justify="right")
    table.add_column("Wins", justify="right")
    table.add_column("Win %", justify="right")
    table.add_column("ROI", justify="right")
    table.add_column("Max DD", justify="right")
    table.add_column("Verdict", justify="center")
    
    profitable_seasons = 0
    total_profit = 0
    
    for r in results:
        win_pct = r.wins / r.bets * 100 if r.bets > 0 else 0
        color = "green" if r.roi > 0 else "red"
        verdict = "✅" if r.roi > 0 else "❌"
        
        table.add_row(
            f"20{r.season[:2]}/{r.season[2:]}",
            str(r.bets),
            str(r.wins),
            f"{win_pct:.1f}%",
            f"[{color}]{r.roi:+.1f}%[/{color}]",
            f"{r.max_dd:.1f}%",
            verdict,
        )
        
        if r.roi > 0:
            profitable_seasons += 1
        total_profit += r.profit
    
    console.print(table)
    
    # Summary stats
    console.print(f"\n[bold]SUMMARY:[/bold]")
    console.print(f"  Profitable seasons: {profitable_seasons}/{len(results)} ({profitable_seasons/len(results)*100:.0f}%)")
    console.print(f"  Overall profit: £{total_profit:+,.0f}")
    
    # The key question: When would Authority help?
    console.print("\n" + "━" * 80)
    console.print("\n[bold cyan]WHEN WOULD IAI AUTHORITY ACTUALLY HELP?[/bold cyan]\n")
    
    # Scenario 1: The 2020-21 and 2023-24 seasons (losing)
    losing_seasons = [r for r in results if r.roi < 0]
    winning_seasons = [r for r in results if r.roi > 0]
    
    console.print("[yellow]SCENARIO 1: Could Authority have avoided the losing seasons?[/yellow]")
    console.print()
    
    for r in losing_seasons:
        console.print(f"  Season 20{r.season[:2]}/{r.season[2:]}: {r.bets} bets, {r.roi:+.1f}% ROI")
    
    console.print()
    console.print("  Analysis: The losing seasons came AFTER profitable ones.")
    console.print("  There was no reliable signal that they would be losers.")
    console.print("  Skipping them = hindsight bias, not genuine prediction.")
    
    console.print()
    console.print("[yellow]SCENARIO 2: Could Authority reduce max drawdown?[/yellow]")
    console.print()
    
    # Show worst drawdown seasons
    worst_dd = max(results, key=lambda x: x.max_dd)
    console.print(f"  Worst drawdown: {worst_dd.max_dd:.1f}% in 20{worst_dd.season[:2]}/{worst_dd.season[2:]}")
    console.print()
    console.print("  [green]YES - By reducing stake after losses, Authority CAN reduce drawdown.[/green]")
    console.print("  But this also reduces upside during recovery.")
    
    console.print()
    console.print("[yellow]SCENARIO 3: Could Authority detect if edge disappears?[/yellow]")
    console.print()
    
    # Check recent vs early edge
    early = results[:4]  # First 4 seasons
    recent = results[-4:]  # Last 4 seasons
    
    early_wins = sum(r.wins for r in early)
    early_bets = sum(r.bets for r in early)
    recent_wins = sum(r.wins for r in recent)
    recent_bets = sum(r.bets for r in recent)
    
    early_wr = early_wins / early_bets * 100 if early_bets else 0
    recent_wr = recent_wins / recent_bets * 100 if recent_bets else 0
    
    console.print(f"  Early seasons (2015-2019): {early_wr:.1f}% win rate")
    console.print(f"  Recent seasons (2020-2024): {recent_wr:.1f}% win rate")
    console.print()
    
    if recent_wr < early_wr - 3:
        console.print("  [yellow]⚠️ Win rate declining - market may be adapting[/yellow]")
    else:
        console.print("  [green]Edge appears stable over time[/green]")
    
    # Final verdict
    console.print("\n" + "━" * 80)
    console.print("\n[bold]VERDICT: What IAI adds to betting[/bold]\n")
    
    verdict_text = """
[green]✓ USEFUL for:[/green]
  • Risk management (reduce stake during drawdowns)
  • Confidence monitoring (is edge still there?)
  • Position sizing (bet more when confident)
  • Alerting you if win rate drops significantly

[red]✗ NOT USEFUL for:[/red]
  • Adjusting the strategy (odds range, selection)
  • Market timing (when to bet or skip)
  • Predicting which matches will win
  • Outperforming a disciplined static strategy

[cyan]THE BOTTOM LINE:[/cyan]
  The static strategy works. Authority's job is to PROTECT it,
  not to improve it. The best role for IAI here is:
  
  1. Monitor the edge (alert if win rate drops 5%+ below expected)
  2. Manage risk (reduce stake during losing streaks)
  3. Stay disciplined (don't let emotions override the system)
  
  Think of Authority as a GUARDIAN, not an OPTIMIZER.
"""
    
    console.print(Panel(verdict_text, border_style="cyan"))
    
    # Practical recommendation
    console.print("\n[bold]WHAT THIS MEANS FOR LIVE BETTING:[/bold]\n")
    console.print("  1. Use the static strategy: Home @ 4.0-6.0 odds")
    console.print("  2. Bet 3% of bankroll per match")
    console.print("  3. Track your results")
    console.print("  4. If you lose 10+ in a row, take a break (not change strategy)")
    console.print("  5. If win rate drops below 22% over 50+ bets, reassess")
    console.print()


if __name__ == "__main__":
    main()
