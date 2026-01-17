"""
LIVE DASHBOARD - View all predictions and performance
======================================================
Shows historical performance and pending bets.

Usage:
    python dashboard.py
"""

import json
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better formatting: pip install rich")

PREDICTIONS_FILE = Path(__file__).parent / "predictions.json"


def load_data():
    """Load predictions database."""
    with open(PREDICTIONS_FILE, 'r') as f:
        return json.load(f)


def plain_dashboard():
    """Simple text dashboard without Rich."""
    data = load_data()
    strategy = data['strategy']
    bankroll = data['bankroll']
    summary = data['results_summary']
    predictions = data['predictions']
    
    print("\n" + "="*70)
    print("🎯 LIVE BETTING TRACKER")
    print("="*70)
    
    print(f"\nStrategy: {strategy['name']}")
    print(f"Rule: HOME WIN @ {strategy['odds_min']}-{strategy['odds_max']} odds, {strategy['stake_pct']}% stake")
    print(f"Expected edge: +{strategy['expected_edge']}%")
    
    print(f"\n💰 BANKROLL")
    print(f"   Initial: £{bankroll['initial']:,.2f}")
    print(f"   Current: £{bankroll['current']:,.2f}")
    profit = bankroll['current'] - bankroll['initial']
    print(f"   Profit:  £{profit:+,.2f}")
    
    print(f"\n📊 PERFORMANCE")
    print(f"   Total bets: {summary['total_bets']}")
    print(f"   Wins: {summary['wins']} | Losses: {summary['losses']} | Pending: {summary['pending']}")
    if summary['wins'] + summary['losses'] > 0:
        win_rate = summary['wins'] / (summary['wins'] + summary['losses']) * 100
        print(f"   Win rate: {win_rate:.1f}%")
    print(f"   ROI: {summary['roi_pct']:+.1f}%")
    
    # Pending bets
    pending = [p for p in predictions if p['status'] == 'pending']
    if pending:
        print(f"\n⏳ PENDING BETS ({len(pending)})")
        print("-"*70)
        for p in pending:
            qual = "✅" if p['qualifies'] else "⚠️"
            print(f"  #{p['id']} | {p['match_date']} | {p['home_team']} vs {p['away_team']}")
            print(f"       HOME @ {p['odds']} {qual} | Stake: £{p['stake']:.2f}")
    
    # Recent results
    settled = [p for p in predictions if p['status'] in ['won', 'lost']]
    if settled:
        print(f"\n📋 RECENT RESULTS (last 10)")
        print("-"*70)
        for p in settled[-10:]:
            status = "✅ WON" if p['status'] == 'won' else "❌ LOST"
            print(f"  #{p['id']} | {p['match_date']} | {p['home_team']} vs {p['away_team']}")
            print(f"       {status} | P/L: £{p['profit_loss']:+.2f}")
    
    print("\n" + "="*70)


def rich_dashboard():
    """Rich formatted dashboard."""
    console = Console()
    data = load_data()
    strategy = data['strategy']
    bankroll = data['bankroll']
    summary = data['results_summary']
    predictions = data['predictions']
    
    console.clear()
    
    # Header
    console.print(Panel.fit(
        "[bold cyan]🎯 LIVE BETTING TRACKER[/bold cyan]",
        border_style="cyan"
    ))
    
    # Strategy info
    console.print(f"\n[bold]Strategy:[/bold] {strategy['name']}")
    console.print(f"[dim]Rule: HOME WIN @ {strategy['odds_min']}-{strategy['odds_max']} odds, {strategy['stake_pct']}% stake[/dim]")
    console.print(f"[dim]Expected edge: +{strategy['expected_edge']}%[/dim]")
    
    # Bankroll panel
    profit = bankroll['current'] - bankroll['initial']
    profit_color = "green" if profit >= 0 else "red"
    
    bankroll_text = f"""
[bold]Initial:[/bold] £{bankroll['initial']:,.2f}
[bold]Current:[/bold] £{bankroll['current']:,.2f}
[bold]Profit:[/bold] [{profit_color}]£{profit:+,.2f}[/{profit_color}]
    """
    console.print(Panel(bankroll_text.strip(), title="💰 Bankroll", border_style="yellow"))
    
    # Performance panel
    if summary['wins'] + summary['losses'] > 0:
        win_rate = summary['wins'] / (summary['wins'] + summary['losses']) * 100
    else:
        win_rate = 0
    
    roi_color = "green" if summary['roi_pct'] >= 0 else "red"
    
    perf_text = f"""
[bold]Total bets:[/bold] {summary['total_bets']}
[bold]Record:[/bold] {summary['wins']}W - {summary['losses']}L ({summary['pending']} pending)
[bold]Win rate:[/bold] {win_rate:.1f}%
[bold]ROI:[/bold] [{roi_color}]{summary['roi_pct']:+.1f}%[/{roi_color}]
    """
    console.print(Panel(perf_text.strip(), title="📊 Performance", border_style="blue"))
    
    # Pending bets table
    pending = [p for p in predictions if p['status'] == 'pending']
    if pending:
        table = Table(title=f"⏳ Pending Bets ({len(pending)})", box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("Date")
        table.add_column("Match")
        table.add_column("Odds")
        table.add_column("Stake")
        table.add_column("Pot. Profit")
        
        for p in pending:
            qual = "✅" if p['qualifies'] else "⚠️"
            table.add_row(
                str(p['id']),
                p['match_date'],
                f"{p['home_team']} vs {p['away_team']}",
                f"{p['odds']} {qual}",
                f"£{p['stake']:.2f}",
                f"£{p['potential_profit']:.2f}"
            )
        console.print(table)
    else:
        console.print("\n[dim]No pending bets[/dim]")
    
    # Recent results table
    settled = [p for p in predictions if p['status'] in ['won', 'lost']]
    if settled:
        table = Table(title=f"📋 Recent Results (last 10)", box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("Date")
        table.add_column("Match")
        table.add_column("Odds")
        table.add_column("Result")
        table.add_column("P/L")
        
        for p in settled[-10:]:
            if p['status'] == 'won':
                result_str = "[green]✅ WON[/green]"
                pl_str = f"[green]+£{p['profit_loss']:.2f}[/green]"
            else:
                result_str = "[red]❌ LOST[/red]"
                pl_str = f"[red]-£{abs(p['profit_loss']):.2f}[/red]"
            
            table.add_row(
                str(p['id']),
                p['match_date'],
                f"{p['home_team']} vs {p['away_team']}",
                str(p['odds']),
                result_str,
                pl_str
            )
        console.print(table)
    
    # Win streak / Loss streak
    if settled:
        current_streak = 0
        streak_type = None
        for p in reversed(settled):
            if streak_type is None:
                streak_type = p['status']
                current_streak = 1
            elif p['status'] == streak_type:
                current_streak += 1
            else:
                break
        
        if streak_type == 'won':
            console.print(f"\n[green]🔥 Current win streak: {current_streak}[/green]")
        else:
            console.print(f"\n[red]📉 Current loss streak: {current_streak}[/red]")
    
    console.print()


def main():
    if RICH_AVAILABLE:
        rich_dashboard()
    else:
        plain_dashboard()


if __name__ == "__main__":
    main()
