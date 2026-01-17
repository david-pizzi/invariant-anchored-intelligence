"""Dashboard components for IAI.

Provides terminal and web-based dashboards for monitoring
IAI evolution in real-time.

This module provides:
- BaseDashboard: Abstract interface for dashboards
- RichDashboard: Beautiful terminal dashboard using Rich library
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from .types import (
    Proposal,
    AuthorityDecision,
    GenerationResult,
    Invariants,
    Verdict,
)


class BaseDashboard(ABC):
    """
    Abstract base class for IAI Dashboard.
    
    Dashboards provide visual feedback during IAI evolution,
    showing progress, decisions, and metrics.
    """
    
    @abstractmethod
    def print_header(self, config: Dict[str, Any]):
        """Display initial configuration header."""
        pass
    
    @abstractmethod
    def show_generation_start(
        self,
        generation: int,
        total: int,
        invariants: Invariants,
    ):
        """Show start of a new generation."""
        pass
    
    @abstractmethod
    def show_generation_result(self, result: GenerationResult):
        """Show generation results."""
        pass
    
    @abstractmethod
    def show_proposal(self, proposal: Proposal):
        """Show Challenger proposal."""
        pass
    
    @abstractmethod
    def show_decision(self, decision: AuthorityDecision):
        """Show Authority decision."""
        pass
    
    @abstractmethod
    def show_baseline_results(self, results: Dict[str, Any]):
        """Show baseline comparison results."""
        pass
    
    @abstractmethod
    def show_summary(self, meta_metrics: Dict[str, Any]):
        """Show final evolution summary."""
        pass


class RichDashboard(BaseDashboard):
    """Beautiful terminal dashboard using Rich library."""
    
    def __init__(self):
        from rich.console import Console
        self.console = Console()
    
    def print_header(self, config: Dict[str, Any]):
        """Display configuration header."""
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        
        self.console.clear()
        self.console.print()
        self.console.print("╔" + "═" * 78 + "╗", style="bold cyan")
        self.console.print(
            "║" + " " * 15 + 
            "INVARIANT-ANCHORED INTELLIGENCE EVOLUTION" + 
            " " * 21 + "║", 
            style="bold cyan"
        )
        self.console.print("╚" + "═" * 78 + "╝", style="bold cyan")
        self.console.print()
        
        # Config table
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        table.add_column(style="cyan")
        table.add_column(style="white")
        
        for key, value in config.items():
            table.add_row(f"📊 {key}", str(value))
        
        self.console.print(Panel(table, title="[bold]Configuration", border_style="cyan"))
        self.console.print()
    
    def show_generation_start(
        self,
        generation: int,
        total: int,
        invariants: Invariants,
    ):
        """Show generation header."""
        from rich.panel import Panel
        
        self.console.print()
        self.console.print(f"{'═'*80}", style="bold yellow")
        self.console.print(
            f"  GENERATION {generation + 1}/{total}", 
            style="bold yellow"
        )
        self.console.print(f"{'═'*80}", style="bold yellow")
        
        self.console.print(Panel(
            f"Primary Metric: {invariants.primary_metric}\n"
            f"Thresholds: {invariants.thresholds}",
            title="Current Invariants",
            border_style="blue",
        ))
    
    def show_generation_result(self, result: GenerationResult):
        """Show generation results."""
        from rich.table import Table
        from rich import box
        
        table = Table(
            title=f"Generation {result.generation} Results",
            box=box.ROUNDED,
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        for name, value in result.metrics.items():
            if isinstance(value, float):
                table.add_row(name, f"{value:.4f}")
            else:
                table.add_row(name, str(value))
        
        self.console.print(table)
    
    def show_proposal(self, proposal: Proposal):
        """Show Challenger proposal."""
        from rich.panel import Panel
        from rich.text import Text
        
        if not proposal.strain_signals.any_detected:
            self.console.print(
                "\n✅ [green]No strain detected - system stable[/green]\n"
            )
            return
        
        # Strain signals
        signals_text = Text()
        for name, signal in proposal.strain_signals.signals.items():
            if signal.detected:
                signals_text.append(f"⚠️  {name}: ", style="yellow")
                signals_text.append(f"{signal.value:.3f} ", style="red")
                signals_text.append(f"(threshold: {signal.threshold:.3f})\n")
        
        self.console.print(Panel(
            signals_text,
            title="[bold yellow]Strain Signals Detected",
            border_style="yellow",
        ))
        
        # Critiques
        if proposal.critiques:
            critique_text = ""
            for c in proposal.critiques:
                severity_color = {
                    "low": "blue",
                    "medium": "yellow", 
                    "high": "red",
                    "critical": "bold red",
                }.get(c.severity.value, "white")
                critique_text += f"[{severity_color}]{c.severity.value.upper()}[/{severity_color}]: {c.description}\n"
            
            self.console.print(Panel(
                critique_text,
                title="Critiques",
                border_style="yellow",
            ))
        
        # Proposed metrics
        if proposal.proposed_metrics:
            for pm in proposal.proposed_metrics:
                self.console.print(Panel(
                    f"Formula: {pm.formula}\n"
                    f"Rationale: {pm.rationale}",
                    title=f"[bold]Proposed: {pm.name}",
                    border_style="magenta",
                ))
    
    def show_decision(self, decision: AuthorityDecision):
        """Show Authority decision."""
        from rich.panel import Panel
        
        verdict_style = {
            Verdict.ACCEPT: "bold green",
            Verdict.REJECT: "bold red",
            Verdict.MODIFY: "bold yellow",
        }.get(decision.verdict, "white")
        
        verdict_emoji = {
            Verdict.ACCEPT: "✅",
            Verdict.REJECT: "❌",
            Verdict.MODIFY: "🔧",
        }.get(decision.verdict, "")
        
        content = f"""
{verdict_emoji} Verdict: [{verdict_style}]{decision.verdict.value}[/{verdict_style}]
📊 Confidence: {decision.confidence:.1%}

📝 Rationale:
{decision.rationale}
"""
        
        if decision.concerns:
            content += f"\n⚠️  Concerns:\n"
            for concern in decision.concerns:
                content += f"  • {concern}\n"
        
        self.console.print(Panel(
            content,
            title="[bold]Authority Decision",
            border_style=verdict_style.replace("bold ", ""),
        ))
    
    def show_baseline_results(self, results: Dict[str, Any]):
        """Show baseline results."""
        from rich.table import Table
        from rich import box
        
        self.console.print("\n[bold green]✓ Baseline Complete[/bold green]\n")
        
        table = Table(title="Baseline Results", box=box.ROUNDED)
        table.add_column("System", style="cyan")
        table.add_column("Performance", style="yellow", justify="right")
        table.add_column("Status", justify="center")
        
        best = results.get("summary", {}).get("best_system", "")
        
        for system in results.get("systems", []):
            name = system.get("name", "Unknown")
            perf = system.get("performance", 0)
            is_best = name == best
            
            table.add_row(
                name,
                f"{perf:.4f}",
                "🏆 BEST" if is_best else "·",
                style="bold green" if is_best else "",
            )
        
        self.console.print(table)
    
    def show_summary(self, meta_metrics: Dict[str, Any]):
        """Show evolution summary."""
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column(style="cyan")
        table.add_column(style="green", justify="right")
        
        table.add_row("Generations Completed", str(meta_metrics.get("generations_completed", 0)))
        table.add_row("Proposals Made", str(meta_metrics.get("proposals_made", 0)))
        table.add_row("Proposals Accepted", str(meta_metrics.get("proposals_accepted", 0)))
        table.add_row("Proposals Rejected", str(meta_metrics.get("proposals_rejected", 0)))
        table.add_row("Proposals Modified", str(meta_metrics.get("proposals_modified", 0)))
        
        self.console.print()
        self.console.print("╔" + "═" * 78 + "╗", style="bold green")
        self.console.print(
            "║" + " " * 25 + "EVOLUTION COMPLETE" + " " * 35 + "║",
            style="bold green"
        )
        self.console.print("╚" + "═" * 78 + "╝", style="bold green")
        
        self.console.print(Panel(table, title="Summary", border_style="green"))
