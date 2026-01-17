"""Live Betting Tracker - Find betting opportunities in upcoming matches.

This tool:
1. Loads the current season's fixtures
2. Applies your strategy rules
3. Shows which bets qualify
4. Calculates recommended stake

For LIVE betting, you can:
- Manually enter today's odds
- Use upcoming fixtures from football-data.co.uk
- Connect to an odds API (requires setup)
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, date
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, FloatPrompt, Confirm
from rich import box
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class BettingOpportunity:
    """A potential betting opportunity."""
    match: str
    home_team: str
    away_team: str
    kickoff: Optional[str]
    selection: str
    odds: float
    implied_prob: float
    historical_edge: float
    recommended_stake: float
    expected_value: float


@dataclass
class StrategyConfig:
    """Strategy configuration."""
    selection: str  # H, D, A
    min_odds: float
    max_odds: float
    edge: float
    stake_pct: float
    confidence: str


# Default optimal strategy (from optimizer)
DEFAULT_STRATEGY = StrategyConfig(
    selection="H",
    min_odds=4.0,
    max_odds=6.0,
    edge=0.052,  # 5.2% historical edge
    stake_pct=3.0,  # Conservative stake
    confidence="HIGH",
)


class LiveBettingTracker:
    """Track live betting opportunities."""
    
    def __init__(self, strategy: StrategyConfig, bankroll: float = 1000.0):
        self.strategy = strategy
        self.bankroll = bankroll
        self.console = Console()
        self.opportunities: List[BettingOpportunity] = []
        self.bet_log_file = Path(__file__).parent / "bet_log.json"
        
    def check_match(
        self,
        home_team: str,
        away_team: str,
        home_odds: float,
        draw_odds: float,
        away_odds: float,
        kickoff: Optional[str] = None,
    ) -> Optional[BettingOpportunity]:
        """Check if a match qualifies for betting."""
        
        # Get the relevant odds based on selection
        if self.strategy.selection == "H":
            odds = home_odds
            selection_name = "Home"
        elif self.strategy.selection == "D":
            odds = draw_odds
            selection_name = "Draw"
        else:
            odds = away_odds
            selection_name = "Away"
        
        # Check if within odds range
        if not (self.strategy.min_odds <= odds < self.strategy.max_odds):
            return None
        
        # Calculate expected value
        implied_prob = 1 / odds
        expected_prob = implied_prob + self.strategy.edge
        expected_value = (expected_prob * odds) - 1  # EV as decimal
        
        # Calculate recommended stake (Kelly-adjusted)
        kelly = self.strategy.edge / (odds - 1) if odds > 1 else 0
        stake = self.bankroll * min(self.strategy.stake_pct / 100, kelly * 0.25)
        
        return BettingOpportunity(
            match=f"{home_team} vs {away_team}",
            home_team=home_team,
            away_team=away_team,
            kickoff=kickoff,
            selection=selection_name,
            odds=odds,
            implied_prob=implied_prob,
            historical_edge=self.strategy.edge,
            recommended_stake=stake,
            expected_value=expected_value,
        )
    
    def add_match_manual(self):
        """Manually add a match to check."""
        self.console.print("\n[bold cyan]➕ Add Match Manually[/bold cyan]\n")
        
        home_team = Prompt.ask("Home team")
        away_team = Prompt.ask("Away team")
        home_odds = FloatPrompt.ask("Home odds", default=2.0)
        draw_odds = FloatPrompt.ask("Draw odds", default=3.5)
        away_odds = FloatPrompt.ask("Away odds", default=4.0)
        kickoff = Prompt.ask("Kickoff time (optional)", default="")
        
        opp = self.check_match(home_team, away_team, home_odds, draw_odds, away_odds, kickoff or None)
        
        if opp:
            self.opportunities.append(opp)
            self.console.print(f"\n[green]✅ QUALIFYING BET FOUND![/green]")
            self._show_opportunity(opp)
        else:
            self.console.print(f"\n[yellow]⚠️ No qualifying bet - odds outside range {self.strategy.min_odds}-{self.strategy.max_odds}[/yellow]")
    
    def load_fixtures_from_file(self, filepath: str):
        """Load fixtures from a CSV file."""
        import csv
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    home = row.get('HomeTeam', row.get('Home', ''))
                    away = row.get('AwayTeam', row.get('Away', ''))
                    home_odds = float(row.get('B365H', row.get('HomeOdds', 0)) or 0)
                    draw_odds = float(row.get('B365D', row.get('DrawOdds', 0)) or 0)
                    away_odds = float(row.get('B365A', row.get('AwayOdds', 0)) or 0)
                    date_str = row.get('Date', row.get('Kickoff', ''))
                    
                    if home and away and home_odds > 1:
                        opp = self.check_match(home, away, home_odds, draw_odds, away_odds, date_str)
                        if opp:
                            self.opportunities.append(opp)
            
            self.console.print(f"[green]✓ Loaded fixtures from {filepath}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]Error loading file: {e}[/red]")
    
    def _show_opportunity(self, opp: BettingOpportunity):
        """Display a single opportunity."""
        ev_color = "green" if opp.expected_value > 0 else "red"
        
        self.console.print(Panel(f"""
[bold]{opp.match}[/bold]
{f"Kickoff: {opp.kickoff}" if opp.kickoff else ""}

Selection: [cyan]{opp.selection} Win[/cyan]
Odds: [bold]{opp.odds:.2f}[/bold]

Implied probability: {opp.implied_prob*100:.1f}%
Historical edge: [green]+{opp.historical_edge*100:.1f}%[/green]
Expected value: [{ev_color}]{opp.expected_value*100:+.1f}%[/{ev_color}]

[bold]Recommended stake: £{opp.recommended_stake:.2f}[/bold]
Potential profit: £{opp.recommended_stake * (opp.odds - 1):.2f}
""", border_style="green"))
    
    def show_all_opportunities(self):
        """Show all qualifying opportunities."""
        if not self.opportunities:
            self.console.print("\n[yellow]No qualifying bets found.[/yellow]")
            return
        
        self.console.print(f"\n[bold green]🎯 {len(self.opportunities)} QUALIFYING BETS[/bold green]\n")
        
        table = Table(box=box.ROUNDED)
        table.add_column("Match", style="cyan")
        table.add_column("Kickoff")
        table.add_column("Bet", justify="center")
        table.add_column("Odds", justify="right")
        table.add_column("Edge", justify="right")
        table.add_column("EV", justify="right")
        table.add_column("Stake", justify="right", style="bold")
        
        total_stake = 0
        for opp in self.opportunities:
            ev_color = "green" if opp.expected_value > 0 else "red"
            table.add_row(
                opp.match,
                opp.kickoff or "-",
                opp.selection,
                f"{opp.odds:.2f}",
                f"[green]+{opp.historical_edge*100:.1f}%[/green]",
                f"[{ev_color}]{opp.expected_value*100:+.1f}%[/{ev_color}]",
                f"£{opp.recommended_stake:.2f}",
            )
            total_stake += opp.recommended_stake
        
        self.console.print(table)
        self.console.print(f"\n[bold]Total stake: £{total_stake:.2f}[/bold]")
        self.console.print(f"[dim]Remaining bankroll: £{self.bankroll - total_stake:.2f}[/dim]")
    
    def log_bet(self, opp: BettingOpportunity, placed: bool = True):
        """Log a bet for tracking."""
        log = []
        if self.bet_log_file.exists():
            with open(self.bet_log_file, 'r') as f:
                log = json.load(f)
        
        log.append({
            "date": datetime.now().isoformat(),
            "match": opp.match,
            "selection": opp.selection,
            "odds": opp.odds,
            "stake": opp.recommended_stake,
            "placed": placed,
            "result": None,  # To be updated later
        })
        
        with open(self.bet_log_file, 'w') as f:
            json.dump(log, f, indent=2)
        
        self.console.print(f"[green]✓ Bet logged to {self.bet_log_file}[/green]")
    
    def record_result(self):
        """Record the result of a previous bet."""
        if not self.bet_log_file.exists():
            self.console.print("[yellow]No bet log found.[/yellow]")
            return
        
        with open(self.bet_log_file, 'r') as f:
            log = json.load(f)
        
        pending = [b for b in log if b.get("result") is None]
        
        if not pending:
            self.console.print("[yellow]No pending bets to update.[/yellow]")
            return
        
        self.console.print("\n[bold cyan]📝 Record Results[/bold cyan]\n")
        
        for i, bet in enumerate(pending):
            self.console.print(f"{i+1}. {bet['match']} - {bet['selection']} @ {bet['odds']:.2f}")
        
        idx = int(Prompt.ask("Select bet #", default="1")) - 1
        if 0 <= idx < len(pending):
            won = Confirm.ask("Did the bet win?")
            
            # Find and update in log
            for b in log:
                if b["date"] == pending[idx]["date"]:
                    b["result"] = "won" if won else "lost"
                    b["profit"] = b["stake"] * (b["odds"] - 1) if won else -b["stake"]
            
            with open(self.bet_log_file, 'w') as f:
                json.dump(log, f, indent=2)
            
            self.console.print(f"[green]✓ Result recorded[/green]")
    
    def show_performance(self):
        """Show betting performance from log."""
        if not self.bet_log_file.exists():
            self.console.print("[yellow]No bet log found.[/yellow]")
            return
        
        with open(self.bet_log_file, 'r') as f:
            log = json.load(f)
        
        completed = [b for b in log if b.get("result") is not None]
        
        if not completed:
            self.console.print("[yellow]No completed bets to analyze.[/yellow]")
            return
        
        wins = sum(1 for b in completed if b["result"] == "won")
        total_stake = sum(b["stake"] for b in completed)
        total_profit = sum(b.get("profit", 0) for b in completed)
        
        self.console.print("\n[bold cyan]📊 BETTING PERFORMANCE[/bold cyan]\n")
        
        self.console.print(f"Total bets: {len(completed)}")
        self.console.print(f"Wins: {wins} ({wins/len(completed)*100:.1f}%)")
        self.console.print(f"Total staked: £{total_stake:.2f}")
        
        profit_color = "green" if total_profit > 0 else "red"
        self.console.print(f"Total profit: [{profit_color}]£{total_profit:+.2f}[/{profit_color}]")
        self.console.print(f"ROI: [{profit_color}]{total_profit/total_stake*100:+.1f}%[/{profit_color}]")


def main():
    console = Console()
    
    console.print()
    console.print("╔" + "═" * 78 + "╗", style="bold cyan")
    console.print("║" + " " * 20 + "⚽ LIVE BETTING TRACKER ⚽" + " " * 29 + "║", style="bold cyan")
    console.print("╚" + "═" * 78 + "╝", style="bold cyan")
    console.print()
    
    # Show current strategy
    console.print("[bold]Current Strategy:[/bold]")
    console.print(f"  Selection: {DEFAULT_STRATEGY.selection} (Home Win)")
    console.print(f"  Odds Range: {DEFAULT_STRATEGY.min_odds} - {DEFAULT_STRATEGY.max_odds}")
    console.print(f"  Historical Edge: +{DEFAULT_STRATEGY.edge*100:.1f}%")
    console.print(f"  Stake: {DEFAULT_STRATEGY.stake_pct}% of bankroll")
    console.print()
    
    # Get bankroll
    bankroll = FloatPrompt.ask("Enter your current bankroll (£)", default=1000.0)
    
    tracker = LiveBettingTracker(DEFAULT_STRATEGY, bankroll)
    
    while True:
        console.print("\n[bold cyan]What would you like to do?[/bold cyan]")
        console.print("  1. Add match manually (enter odds)")
        console.print("  2. Load fixtures from CSV file")
        console.print("  3. Show all qualifying bets")
        console.print("  4. Record bet result")
        console.print("  5. Show performance")
        console.print("  6. Exit")
        
        choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "6"], default="1")
        
        if choice == "1":
            tracker.add_match_manual()
        elif choice == "2":
            filepath = Prompt.ask("Enter CSV file path")
            tracker.load_fixtures_from_file(filepath)
        elif choice == "3":
            tracker.show_all_opportunities()
        elif choice == "4":
            tracker.record_result()
        elif choice == "5":
            tracker.show_performance()
        elif choice == "6":
            console.print("\n[bold green]Good luck with your bets! 🍀[/bold green]")
            break


if __name__ == "__main__":
    main()
