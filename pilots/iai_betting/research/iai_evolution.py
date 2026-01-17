"""IAI Betting Evolution - The ACTUAL IAI loop for betting.

This implements the core IAI concept:
- Invariants = Strategy parameters (odds range, stake %)
- Challenger = Detects when strategy is failing (losing streaks, edge decay)  
- Authority = Decides whether to adjust, pause, or continue

The question: Does IAI adaptation BEAT a static strategy?
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pilots.iai_betting.data import FootballDataLoader, Match


@dataclass
class BettingInvariants:
    """The invariants (strategy parameters) that Authority can adjust."""
    selection: str = "H"  # H, D, A
    min_odds: float = 4.0
    max_odds: float = 6.0
    stake_pct: float = 3.0
    min_edge_required: float = 0.03  # Pause if edge drops below this
    max_consecutive_losses: int = 8  # Pause after this many losses
    
    def to_dict(self) -> Dict:
        return {
            "selection": self.selection,
            "min_odds": self.min_odds,
            "max_odds": self.max_odds,
            "stake_pct": self.stake_pct,
            "min_edge_required": self.min_edge_required,
            "max_consecutive_losses": self.max_consecutive_losses,
        }


@dataclass
class StrainSignal:
    """Signals that the strategy might need adjustment."""
    consecutive_losses: int = 0
    recent_win_rate: float = 0.0  # Last N bets
    recent_edge: float = 0.0  # Actual - implied for recent bets
    is_underperforming: bool = False
    is_critical: bool = False  # Should pause betting


@dataclass 
class AuthorityDecision:
    """What the Authority decides to do."""
    action: str  # "CONTINUE", "ADJUST", "PAUSE"
    confidence: float
    rationale: str
    new_invariants: Optional[BettingInvariants] = None


class BettingChallenger:
    """Detects strain in the betting strategy."""
    
    def __init__(self, lookback: int = 20):
        self.lookback = lookback
        self.recent_bets: List[Dict] = []
    
    def record_bet(self, odds: float, won: bool):
        """Record a bet result."""
        self.recent_bets.append({
            "odds": odds,
            "won": won,
            "implied_prob": 1 / odds,
        })
        # Keep only recent
        if len(self.recent_bets) > self.lookback * 2:
            self.recent_bets = self.recent_bets[-self.lookback:]
    
    def analyze(self, invariants: BettingInvariants) -> StrainSignal:
        """Analyze recent performance for strain signals."""
        signal = StrainSignal()
        
        if len(self.recent_bets) < 5:
            return signal
        
        recent = self.recent_bets[-self.lookback:]
        
        # Count consecutive losses from end
        consecutive_losses = 0
        for bet in reversed(recent):
            if not bet["won"]:
                consecutive_losses += 1
            else:
                break
        signal.consecutive_losses = consecutive_losses
        
        # Recent win rate
        wins = sum(1 for b in recent if b["won"])
        signal.recent_win_rate = wins / len(recent)
        
        # Recent edge (actual - implied)
        implied = sum(b["implied_prob"] for b in recent) / len(recent)
        signal.recent_edge = signal.recent_win_rate - implied
        
        # Is underperforming?
        signal.is_underperforming = signal.recent_edge < 0
        
        # Is critical? (should pause)
        signal.is_critical = (
            consecutive_losses >= invariants.max_consecutive_losses or
            (len(recent) >= 15 and signal.recent_edge < -0.05)  # Very negative edge
        )
        
        return signal


class BettingAuthority:
    """Makes decisions about whether to adjust strategy.
    
    CONSERVATIVE approach: The edge was discovered through historical analysis.
    Authority should PROTECT the strategy, not over-optimize it.
    
    Key insight from testing: The original strategy (H @ 4.0-6.0) worked.
    Over-adjusting destroyed the edge. Authority should be MINIMAL.
    """
    
    def __init__(self):
        self.decisions_log: List[AuthorityDecision] = []
        self.paused = False
        self.pause_counter = 0
        self.bets_since_last_decision = 0
        self.original_invariants: Optional[BettingInvariants] = None
    
    def review(
        self,
        invariants: BettingInvariants,
        strain: StrainSignal,
        overall_roi: float,
    ) -> AuthorityDecision:
        """Review current state and decide action.
        
        CONSERVATIVE PRINCIPLES:
        1. Don't adjust based on short-term noise
        2. Never expand beyond the validated range
        3. Only pause in truly extreme circumstances
        4. When in doubt, CONTINUE
        """
        
        # Store original invariants
        if self.original_invariants is None:
            self.original_invariants = BettingInvariants(
                selection=invariants.selection,
                min_odds=invariants.min_odds,
                max_odds=invariants.max_odds,
                stake_pct=invariants.stake_pct,
            )
        
        self.bets_since_last_decision += 1
        
        # If paused, check if we should resume
        if self.paused:
            self.pause_counter -= 1
            if self.pause_counter <= 0:
                self.paused = False
                # Reset to original invariants when resuming
                decision = AuthorityDecision(
                    action="CONTINUE",
                    confidence=0.7,
                    rationale="Pause period ended, resuming with original strategy",
                    new_invariants=self.original_invariants,
                )
                return decision
            else:
                return AuthorityDecision(
                    action="PAUSE",
                    confidence=0.9,
                    rationale=f"Paused ({self.pause_counter} matches remaining)",
                )
        
        # ONLY pause after SEVERE losing streak (10+ losses)
        # and negative edge over meaningful sample
        if strain.consecutive_losses >= 10 and strain.recent_edge < -0.08:
            self.paused = True
            self.pause_counter = 5  # Short pause
            self.bets_since_last_decision = 0
            decision = AuthorityDecision(
                action="PAUSE",
                confidence=0.75,
                rationale=f"Severe losing streak ({strain.consecutive_losses} losses). "
                          f"Short pause to let variance normalize.",
            )
            self.decisions_log.append(decision)
            return decision
        
        # REDUCE stake if massively underperforming (but don't stop)
        # Only after 50+ bets to avoid noise
        if (self.bets_since_last_decision >= 50 and 
            strain.recent_edge < -0.05 and 
            invariants.stake_pct > 1.5):
            
            self.bets_since_last_decision = 0
            new_inv = BettingInvariants(
                selection=invariants.selection,
                min_odds=invariants.min_odds,  # Keep odds range!
                max_odds=invariants.max_odds,
                stake_pct=max(1.5, invariants.stake_pct - 1.0),  # Reduce stake
                min_edge_required=invariants.min_edge_required,
                max_consecutive_losses=invariants.max_consecutive_losses,
            )
            decision = AuthorityDecision(
                action="ADJUST",
                confidence=0.6,
                rationale=f"Reducing stake from {invariants.stake_pct}% to {new_inv.stake_pct}% "
                          f"due to sustained underperformance",
                new_invariants=new_inv,
            )
            self.decisions_log.append(decision)
            return decision
        
        # NEVER expand beyond original range - that's overfitting!
        # The edge was validated at 4.0-6.0, stick to it
        
        # Default: continue (this should be 95%+ of decisions)
        return AuthorityDecision(
            action="CONTINUE",
            confidence=0.9,
            rationale="Strategy within expected variance",
        )


def run_static_strategy(
    matches: List[Match],
    invariants: BettingInvariants,
    starting_bankroll: float = 1000.0,
) -> Tuple[float, List[Dict]]:
    """Run a static (non-adaptive) strategy."""
    bankroll = starting_bankroll
    bets = []
    
    for m in matches:
        if invariants.selection == "H":
            odds = m.odds.home_odds
            won = m.result == "H"
        elif invariants.selection == "D":
            odds = m.odds.draw_odds
            won = m.result == "D"
        else:
            odds = m.odds.away_odds
            won = m.result == "A"
        
        if invariants.min_odds <= odds < invariants.max_odds:
            stake = bankroll * (invariants.stake_pct / 100)
            profit = stake * (odds - 1) if won else -stake
            bankroll += profit
            bets.append({
                "match": f"{m.home_team} vs {m.away_team}",
                "odds": odds,
                "stake": stake,
                "won": won,
                "profit": profit,
                "bankroll": bankroll,
            })
    
    return bankroll, bets


def run_iai_strategy(
    matches: List[Match],
    starting_invariants: BettingInvariants,
    starting_bankroll: float = 1000.0,
) -> Tuple[float, List[Dict], List[AuthorityDecision]]:
    """Run the IAI adaptive strategy."""
    bankroll = starting_bankroll
    invariants = starting_invariants
    
    challenger = BettingChallenger(lookback=20)
    authority = BettingAuthority()
    
    bets = []
    decisions = []
    skipped = 0
    
    for m in matches:
        if invariants.selection == "H":
            odds = m.odds.home_odds
            won = m.result == "H"
        elif invariants.selection == "D":
            odds = m.odds.draw_odds
            won = m.result == "D"
        else:
            odds = m.odds.away_odds
            won = m.result == "A"
        
        if invariants.min_odds <= odds < invariants.max_odds:
            # Get strain signal
            strain = challenger.analyze(invariants)
            
            # Get authority decision
            current_roi = (bankroll - starting_bankroll) / starting_bankroll if starting_bankroll > 0 else 0
            decision = authority.review(invariants, strain, current_roi)
            
            if decision.action == "PAUSE":
                skipped += 1
                if decision not in decisions:
                    decisions.append(decision)
                continue
            
            if decision.action == "ADJUST" and decision.new_invariants:
                decisions.append(decision)
                invariants = decision.new_invariants
                # Re-check if still qualifies under new invariants
                if not (invariants.min_odds <= odds < invariants.max_odds):
                    continue
            
            # Place bet
            stake = bankroll * (invariants.stake_pct / 100)
            profit = stake * (odds - 1) if won else -stake
            bankroll += profit
            
            # Record for challenger
            challenger.record_bet(odds, won)
            
            bets.append({
                "match": f"{m.home_team} vs {m.away_team}",
                "odds": odds,
                "stake": stake,
                "won": won,
                "profit": profit,
                "bankroll": bankroll,
                "invariants": invariants.to_dict(),
            })
    
    return bankroll, bets, decisions


def main():
    console = Console()
    
    console.print()
    console.print("╔" + "═" * 78 + "╗", style="bold cyan")
    console.print("║" + " " * 15 + "🧠 IAI BETTING: STATIC vs ADAPTIVE 🧠" + " " * 22 + "║", style="bold cyan")
    console.print("╚" + "═" * 78 + "╝", style="bold cyan")
    console.print()
    console.print("[bold]Question: Does IAI's adaptive Authority BEAT a static strategy?[/bold]\n")
    
    # Load data
    loader = FootballDataLoader()
    seasons = ["1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324"]
    
    all_matches = []
    for season in seasons:
        try:
            matches = loader.load_season("E0", season)
            if matches:
                all_matches.extend(matches)
        except:
            pass
    
    console.print(f"[green]✓ Loaded {len(all_matches)} matches[/green]\n")
    
    # Define starting strategy
    starting_invariants = BettingInvariants(
        selection="H",
        min_odds=4.0,
        max_odds=6.0,
        stake_pct=3.0,
    )
    
    starting_bankroll = 1000.0
    
    # Run STATIC strategy
    console.print("[bold yellow]Running STATIC strategy...[/bold yellow]")
    static_final, static_bets = run_static_strategy(all_matches, starting_invariants, starting_bankroll)
    static_roi = (static_final - starting_bankroll) / starting_bankroll * 100
    static_wins = sum(1 for b in static_bets if b["won"])
    
    console.print(f"  Bets: {len(static_bets)}, Wins: {static_wins} ({static_wins/len(static_bets)*100:.1f}%)")
    console.print(f"  Final: £{static_final:.0f}, ROI: {static_roi:+.1f}%\n")
    
    # Run IAI strategy
    console.print("[bold cyan]Running IAI ADAPTIVE strategy...[/bold cyan]")
    iai_final, iai_bets, iai_decisions = run_iai_strategy(all_matches, starting_invariants, starting_bankroll)
    iai_roi = (iai_final - starting_bankroll) / starting_bankroll * 100
    iai_wins = sum(1 for b in iai_bets if b["won"])
    
    console.print(f"  Bets: {len(iai_bets)}, Wins: {iai_wins} ({iai_wins/len(iai_bets)*100:.1f}% if iai_bets else 0)")
    console.print(f"  Final: £{iai_final:.0f}, ROI: {iai_roi:+.1f}%")
    console.print(f"  Authority decisions: {len(iai_decisions)}\n")
    
    # Comparison
    console.print("━" * 80)
    console.print("[bold]COMPARISON[/bold]\n")
    
    table = Table(box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Static", justify="right")
    table.add_column("IAI Adaptive", justify="right")
    table.add_column("Winner", justify="center")
    
    # ROI comparison
    roi_winner = "IAI 🏆" if iai_roi > static_roi else "Static 🏆" if static_roi > iai_roi else "Tie"
    table.add_row(
        "Final Bankroll",
        f"£{static_final:,.0f}",
        f"£{iai_final:,.0f}",
        roi_winner,
    )
    table.add_row(
        "ROI",
        f"{static_roi:+.1f}%",
        f"{iai_roi:+.1f}%",
        roi_winner,
    )
    table.add_row(
        "Total Bets",
        str(len(static_bets)),
        str(len(iai_bets)),
        "-",
    )
    table.add_row(
        "Win Rate",
        f"{static_wins/len(static_bets)*100:.1f}%",
        f"{iai_wins/len(iai_bets)*100:.1f}%" if iai_bets else "N/A",
        "-",
    )
    
    # Max drawdown
    def calc_max_dd(bets):
        if not bets:
            return 0
        peak = 1000
        max_dd = 0
        for b in bets:
            if b["bankroll"] > peak:
                peak = b["bankroll"]
            dd = (peak - b["bankroll"]) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return max_dd
    
    static_dd = calc_max_dd(static_bets)
    iai_dd = calc_max_dd(iai_bets)
    dd_winner = "IAI 🏆" if iai_dd < static_dd else "Static 🏆" if static_dd < iai_dd else "Tie"
    
    table.add_row(
        "Max Drawdown",
        f"{static_dd:.1f}%",
        f"{iai_dd:.1f}%",
        dd_winner,
    )
    
    console.print(table)
    
    # Show Authority decisions
    if iai_decisions:
        console.print("\n[bold cyan]Authority Decisions Made:[/bold cyan]\n")
        for i, d in enumerate(iai_decisions[:10], 1):  # Show first 10
            color = "yellow" if d.action == "PAUSE" else "cyan" if d.action == "ADJUST" else "green"
            console.print(f"  [{color}]{i}. {d.action}[/{color}]: {d.rationale}")
        
        if len(iai_decisions) > 10:
            console.print(f"  ... and {len(iai_decisions) - 10} more decisions")
    
    # Verdict
    console.print("\n" + "━" * 80)
    
    if iai_roi > static_roi:
        verdict = f"[bold green]✅ IAI WINS![/bold green] +{iai_roi - static_roi:.1f}% better ROI"
        explanation = "Authority's adaptive decisions improved returns by avoiding losing streaks."
    elif static_roi > iai_roi:
        verdict = f"[bold yellow]⚠️ STATIC WINS[/bold yellow] by +{static_roi - iai_roi:.1f}% ROI"
        explanation = "On this dataset, the static strategy outperformed. IAI may have over-adjusted."
    else:
        verdict = "[bold]TIE[/bold]"
        explanation = "Both strategies performed similarly."
    
    console.print(f"\n{verdict}")
    console.print(f"[dim]{explanation}[/dim]\n")
    
    # Risk-adjusted comparison
    static_sharpe = static_roi / static_dd if static_dd > 0 else 0
    iai_sharpe = iai_roi / iai_dd if iai_dd > 0 else 0
    
    console.print("[bold]Risk-Adjusted (ROI / MaxDD):[/bold]")
    console.print(f"  Static: {static_sharpe:.2f}")
    console.print(f"  IAI:    {iai_sharpe:.2f}")
    
    if iai_sharpe > static_sharpe:
        console.print("  [green]→ IAI has better risk-adjusted returns[/green]")
    elif static_sharpe > iai_sharpe:
        console.print("  [yellow]→ Static has better risk-adjusted returns[/yellow]")


if __name__ == "__main__":
    main()
