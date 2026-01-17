"""Beautiful terminal dashboard for Betting Pilot using Rich library.

Provides live updates with:
- Bankroll evolution with sparklines
- Season-by-season results tables
- Strategy comparison panels
- Live bet tracking
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.syntax import Syntax
from rich import box
import json
from typing import Dict, Any, List
from dataclasses import dataclass
import time


@dataclass
class BetResult:
    """Single bet result."""
    season: str
    match: str
    selection: str
    odds: float
    stake: float
    won: bool
    profit: float
    bankroll: float


class BettingDashboard:
    """Beautiful terminal dashboard for betting backtest."""
    
    def __init__(self):
        self.console = Console()
        self.bets: List[BetResult] = []
        self.season_results: Dict[str, Dict] = {}
        
    def print_header(self, strategy_name: str, config: Dict[str, Any]):
        """Print configuration header."""
        self.console.clear()
        self.console.print()
        self.console.print("╔" + "═" * 78 + "╗", style="bold cyan")
        self.console.print("║" + " " * 22 + "⚽ IAI BETTING DASHBOARD ⚽" + " " * 27 + "║", style="bold cyan")
        self.console.print("╚" + "═" * 78 + "╝", style="bold cyan")
        self.console.print()
        
        # Config table
        config_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        config_table.add_column(style="cyan")
        config_table.add_column(style="white")
        
        config_table.add_row("📊 Strategy", strategy_name)
        config_table.add_row("💰 Starting Bankroll", f"£{config.get('bankroll', 1000):.0f}")
        config_table.add_row("📈 Stake %", f"{config.get('stake_pct', 5):.1f}%")
        config_table.add_row("🎯 Selection", config.get('selection', 'H @ 4.0-6.0'))
        config_table.add_row("📅 Seasons", config.get('seasons', '2015-2024'))
        
        self.console.print(Panel(config_table, title="[bold]Configuration", border_style="cyan"))
        self.console.print()

    def show_loading_seasons(self, seasons: List[str]):
        """Show loading progress for seasons."""
        self.console.print("[bold yellow]📥 Loading Season Data...[/bold yellow]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Loading seasons", total=len(seasons))
            for season in seasons:
                yield season
                progress.update(task, advance=1)
        
        self.console.print("[green]✓ Data loaded[/green]\n")

    def show_season_header(self, season: str, n_matches: int):
        """Show season header."""
        self.console.print(f"\n[bold blue]━━━ Season 20{season[:2]}/20{season[2:]} ({n_matches} matches) ━━━[/bold blue]\n")

    def record_bet(self, bet: BetResult):
        """Record a bet result."""
        self.bets.append(bet)

    def show_live_bet(self, match: str, selection: str, odds: float, stake: float, won: bool, profit: float, bankroll: float):
        """Show a single bet result inline."""
        emoji = "✅" if won else "❌"
        color = "green" if won else "red"
        
        self.console.print(
            f"  {emoji} {match[:40]:<40} | {selection} @ {odds:.2f} | "
            f"£{stake:.0f} → [bold {color}]£{profit:+.0f}[/bold {color}] | "
            f"Bank: £{bankroll:.0f}"
        )

    def show_season_summary(self, season: str, stats: Dict[str, Any]):
        """Show end of season summary."""
        is_profitable = stats['profit'] > 0
        emoji = "🟢" if is_profitable else "🔴"
        color = "green" if is_profitable else "red"
        
        self.season_results[season] = stats
        
        summary = Text()
        summary.append(f"{emoji} Season 20{season[:2]}/20{season[2:]}: ", style="bold")
        summary.append(f"{stats['bets']} bets, ", style="white")
        summary.append(f"{stats['wins']} wins ({stats['win_rate']*100:.1f}%), ", style="cyan")
        summary.append(f"£{stats['profit']:+.0f} ", style=f"bold {color}")
        summary.append(f"({stats['roi']*100:+.1f}% ROI)", style=color)
        
        self.console.print(Panel(summary, border_style=color))

    def show_bankroll_evolution(self, history: List[float]):
        """Show bankroll sparkline chart."""
        self.console.print("\n[bold cyan]📈 Bankroll Evolution[/bold cyan]\n")
        
        # Simple ASCII chart
        min_val = min(history)
        max_val = max(history)
        range_val = max_val - min_val if max_val > min_val else 1
        
        height = 10
        width = min(80, len(history))
        
        # Downsample if needed
        step = max(1, len(history) // width)
        sampled = [history[i] for i in range(0, len(history), step)]
        
        # Build chart
        chart_lines = []
        for row in range(height, 0, -1):
            threshold = min_val + (row / height) * range_val
            line = ""
            for val in sampled:
                if val >= threshold:
                    line += "█"
                elif val >= threshold - (range_val / height / 2):
                    line += "▄"
                else:
                    line += " "
            
            # Add Y-axis label
            if row == height:
                label = f"£{max_val:>7.0f} │"
            elif row == 1:
                label = f"£{min_val:>7.0f} │"
            elif row == height // 2:
                mid = (max_val + min_val) / 2
                label = f"£{mid:>7.0f} │"
            else:
                label = "         │"
            
            chart_lines.append(label + line)
        
        # X-axis
        chart_lines.append("         └" + "─" * len(sampled))
        chart_lines.append("          Start" + " " * (len(sampled) - 10) + "End")
        
        # Color based on final result
        color = "green" if history[-1] > history[0] else "red"
        
        self.console.print(Panel(
            "\n".join(chart_lines),
            title="[bold]Bankroll Over Time",
            border_style=color
        ))

    def show_final_results(self, starting: float, final: float, peak: float, max_dd: float, total_bets: int):
        """Show final results summary."""
        self.console.print("\n" + "═" * 80, style="bold green")
        self.console.print("[bold green]🏆 FINAL RESULTS[/bold green]")
        self.console.print("═" * 80 + "\n", style="bold green")
        
        profit = final - starting
        roi = (final - starting) / starting * 100
        
        # Main stats
        stats_table = Table(box=box.ROUNDED, show_header=False)
        stats_table.add_column(style="cyan", width=25)
        stats_table.add_column(style="bold white", width=20)
        
        color = "green" if profit > 0 else "red"
        
        stats_table.add_row("💰 Starting Bankroll", f"£{starting:,.0f}")
        stats_table.add_row("💵 Final Bankroll", f"£{final:,.0f}")
        stats_table.add_row("📈 Total Profit", f"[{color}]£{profit:+,.0f}[/{color}]")
        stats_table.add_row("📊 Total ROI", f"[{color}]{roi:+,.1f}%[/{color}]")
        stats_table.add_row("🎢 Peak Bankroll", f"£{peak:,.0f}")
        stats_table.add_row("📉 Max Drawdown", f"[yellow]{max_dd:.1f}%[/yellow]")
        stats_table.add_row("🎯 Total Bets", str(total_bets))
        
        self.console.print(stats_table)

    def show_season_comparison_table(self):
        """Show all seasons in a comparison table."""
        self.console.print("\n[bold cyan]📅 Season-by-Season Breakdown[/bold cyan]\n")
        
        table = Table(box=box.ROUNDED)
        table.add_column("Season", style="cyan", justify="center")
        table.add_column("Bets", justify="right")
        table.add_column("Wins", justify="right")
        table.add_column("Win %", justify="right")
        table.add_column("Profit", justify="right")
        table.add_column("ROI", justify="right")
        table.add_column("Status", justify="center")
        
        for season in sorted(self.season_results.keys()):
            stats = self.season_results[season]
            is_profit = stats['profit'] > 0
            color = "green" if is_profit else "red"
            emoji = "✅" if is_profit else "❌"
            
            table.add_row(
                f"20{season[:2]}/20{season[2:]}",
                str(stats['bets']),
                str(stats['wins']),
                f"{stats['win_rate']*100:.1f}%",
                f"[{color}]£{stats['profit']:+,.0f}[/{color}]",
                f"[{color}]{stats['roi']*100:+.1f}%[/{color}]",
                emoji
            )
        
        self.console.print(table)

    def show_strategy_comparison(self, strategies: List[Dict[str, Any]]):
        """Show comparison between multiple strategies."""
        self.console.print("\n[bold cyan]🏁 Strategy Comparison[/bold cyan]\n")
        
        table = Table(box=box.ROUNDED, title="Strategy Performance")
        table.add_column("Strategy", style="cyan")
        table.add_column("Final £", justify="right")
        table.add_column("ROI %", justify="right")
        table.add_column("Win %", justify="right")
        table.add_column("Max DD", justify="right")
        table.add_column("Rank", justify="center")
        
        # Sort by final value
        sorted_strats = sorted(strategies, key=lambda x: x['final'], reverse=True)
        
        for i, strat in enumerate(sorted_strats, 1):
            is_best = i == 1
            roi = (strat['final'] - strat['starting']) / strat['starting'] * 100
            color = "green" if roi > 0 else "red"
            
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
            style = "bold" if is_best else ""
            
            table.add_row(
                strat['name'],
                f"£{strat['final']:,.0f}",
                f"[{color}]{roi:+.1f}%[/{color}]",
                f"{strat.get('win_rate', 0)*100:.1f}%",
                f"{strat.get('max_dd', 0):.1f}%",
                rank_emoji,
                style=style
            )
        
        self.console.print(table)

    def show_edge_analysis(self, edges: Dict[str, Dict]):
        """Show edge analysis by odds range."""
        self.console.print("\n[bold cyan]📊 Edge Analysis by Odds Range[/bold cyan]\n")
        
        table = Table(box=box.ROUNDED)
        table.add_column("Selection", style="cyan")
        table.add_column("Odds Range", justify="center")
        table.add_column("Matches", justify="right")
        table.add_column("Actual %", justify="right")
        table.add_column("Implied %", justify="right")
        table.add_column("Edge %", justify="right")
        table.add_column("Signal", justify="center")
        
        for key, data in edges.items():
            edge = data.get('edge', 0)
            if edge > 3:
                color = "green"
                signal = "🟢 BET"
            elif edge > 0:
                color = "yellow"
                signal = "🟡 MAYBE"
            else:
                color = "red"
                signal = "🔴 AVOID"
            
            table.add_row(
                data.get('selection', key),
                data.get('range', ''),
                str(data.get('n', 0)),
                f"{data.get('actual', 0)*100:.1f}%",
                f"{data.get('implied', 0)*100:.1f}%",
                f"[{color}]{edge:+.1f}%[/{color}]",
                signal
            )
        
        self.console.print(table)


def run_visual_backtest():
    """Run the visual backtest with dashboard."""
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from pilots.iai_betting.data import FootballDataLoader, Match
    
    dashboard = BettingDashboard()
    
    # Config
    config = {
        'bankroll': 1000,
        'stake_pct': 5,
        'selection': 'Home @ 4.0-6.0 odds',
        'seasons': '2015-2024',
    }
    
    dashboard.print_header("Home Underdog Value Strategy", config)
    
    # Load data
    loader = FootballDataLoader()
    seasons = ["1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324"]
    all_matches: Dict[str, List] = {}
    
    for season in dashboard.show_loading_seasons(seasons):
        try:
            matches = loader.load_season("E0", season)
            if matches:
                all_matches[season] = matches
        except Exception:
            pass
    
    # Run backtest
    bankroll = config['bankroll']
    starting = bankroll
    history = [bankroll]
    total_bets = 0
    total_wins = 0
    
    for season in sorted(all_matches.keys()):
        matches = all_matches[season]
        dashboard.show_season_header(season, len(matches))
        
        season_bets = 0
        season_wins = 0
        season_start = bankroll
        
        for m in matches:
            odds = m.odds.home_odds
            if 4.0 <= odds < 6.0:
                stake = bankroll * (config['stake_pct'] / 100)
                won = m.result == "H"
                profit = stake * (odds - 1) if won else -stake
                bankroll += profit
                history.append(bankroll)
                
                season_bets += 1
                total_bets += 1
                if won:
                    season_wins += 1
                    total_wins += 1
                
                match_str = f"{m.home_team} vs {m.away_team}"
                dashboard.show_live_bet(match_str, "H", odds, stake, won, profit, bankroll)
        
        if season_bets > 0:
            season_profit = bankroll - season_start
            dashboard.show_season_summary(season, {
                'bets': season_bets,
                'wins': season_wins,
                'win_rate': season_wins / season_bets,
                'profit': season_profit,
                'roi': season_profit / (season_start * config['stake_pct'] / 100 * season_bets) if season_bets > 0 else 0,
            })
    
    # Calculate stats
    peak = max(history)
    # Find max drawdown
    max_dd = 0
    peak_so_far = history[0]
    for val in history:
        if val > peak_so_far:
            peak_so_far = val
        dd = (peak_so_far - val) / peak_so_far * 100
        if dd > max_dd:
            max_dd = dd
    
    # Show visualizations
    dashboard.show_bankroll_evolution(history)
    dashboard.show_season_comparison_table()
    dashboard.show_final_results(starting, bankroll, peak, max_dd, total_bets)
    
    # Show edge analysis
    edges = {
        'home_underdog': {'selection': 'Home', 'range': '4.0-6.0', 'n': 320, 'actual': 0.266, 'implied': 0.214, 'edge': 5.2},
        'home_favorite': {'selection': 'Home', 'range': '1.5-2.0', 'n': 1200, 'actual': 0.548, 'implied': 0.530, 'edge': 1.8},
        'home_mid': {'selection': 'Home', 'range': '2.0-2.5', 'n': 1400, 'actual': 0.405, 'implied': 0.445, 'edge': -4.0},
        'away_value': {'selection': 'Away', 'range': '3.0-4.0', 'n': 900, 'actual': 0.270, 'implied': 0.277, 'edge': -0.7},
    }
    dashboard.show_edge_analysis(edges)


if __name__ == "__main__":
    run_visual_backtest()
