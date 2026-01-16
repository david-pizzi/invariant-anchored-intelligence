"""Beautiful terminal dashboard using Rich library.

Provides live updates with:
- Progress bars for experiments
- Formatted panels for LLM decisions
- Tables for metrics
- Syntax-highlighted JSON
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.syntax import Syntax
from rich import box
import json
from typing import Dict, Any


class RichDashboard:
    """Beautiful terminal dashboard for IAI evolution."""
    
    def __init__(self):
        self.console = Console()
        self.current_gen = 0
        self.total_gens = 0
        
    def print_header(self, config: Dict[str, Any]):
        """Print configuration header."""
        self.console.clear()
        self.console.print()
        self.console.print("╔" + "═" * 78 + "╗", style="bold cyan")
        self.console.print("║" + " " * 20 + "IAI EVOLUTION WITH LLM AUTHORITY" + " " * 26 + "║", style="bold cyan")
        self.console.print("╚" + "═" * 78 + "╝", style="bold cyan")
        self.console.print()
        
        # Config table
        config_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        config_table.add_column(style="cyan")
        config_table.add_column(style="white")
        
        config_table.add_row("🎯 Generations", str(config['generations']))
        config_table.add_row("📊 Steps per run", str(config['steps']))
        config_table.add_row("🔄 Runs per system", str(config['runs']))
        config_table.add_row("🤖 LLM Model", config['model'])
        config_table.add_row("⚖️  Strictness", config['strictness'])
        
        self.console.print(Panel(config_table, title="[bold]Configuration", border_style="cyan"))
        self.console.print()
    
    def show_baseline_progress(self, systems: list):
        """Show progress for baseline systems."""
        self.console.print("\n[bold yellow]⚡ Running Baseline Systems...[/bold yellow]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            
            for system in systems:
                task = progress.add_task(f"[cyan]{system}", total=100)
                yield progress, task
    
    def show_baseline_results(self, results: Dict[str, Any]):
        """Show baseline results table."""
        self.console.print("\n[bold green]✓ Baseline Complete[/bold green]\n")
        
        table = Table(title="Baseline Results", box=box.ROUNDED)
        table.add_column("System", style="cyan", justify="left")
        table.add_column("Avg Regret", style="yellow", justify="right")
        table.add_column("Avg Reward", style="green", justify="right")
        table.add_column("Status", style="white", justify="center")
        
        best_system = results['best_system']
        for sys_data in results['all_systems']:
            system = sys_data['system']
            is_best = system == best_system
            status = "🏆 BEST" if is_best else "·"
            style = "bold green" if is_best else ""
            
            table.add_row(
                system,
                f"{sys_data['final_regret']:.2f}",
                f"{sys_data['final_reward']:.2f}",
                status,
                style=style
            )
        
        self.console.print(table)
        self.console.print()
    
    def show_generation_header(self, gen: int, total: int, invariants: Dict):
        """Show generation header."""
        self.current_gen = gen
        self.total_gens = total
        
        self.console.print("\n" + "━" * 80 + "\n", style="bold blue")
        self.console.print(f"[bold blue]GENERATION {gen}/{total-1}[/bold blue]")
        self.console.print("━" * 80 + "\n", style="bold blue")
        
        # Show current invariants
        inv_panel = Panel(
            Syntax(json.dumps(invariants, indent=2), "json", theme="monokai"),
            title="[bold]Current Invariants",
            border_style="blue"
        )
        self.console.print(inv_panel)
        self.console.print()
    
    def show_iai_progress(self, n_runs: int):
        """Show IAI system progress."""
        self.console.print("[bold cyan]🤖 Running IAI System...[/bold cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"[cyan]IAI Runs", total=n_runs)
            return progress, task
    
    def show_iai_results(self, results: Dict[str, Any], baseline_best: float):
        """Show IAI results compared to baseline."""
        self.console.print("\n[bold green]✓ IAI Run Complete[/bold green]\n")
        
        iai_regret = results['avg_regret']
        improvement = ((baseline_best - iai_regret) / baseline_best * 100) if baseline_best > 0 else 0
        
        # Results panel
        results_text = Text()
        results_text.append(f"Avg Regret: ", style="white")
        results_text.append(f"{iai_regret:.2f}\n", style="bold yellow")
        results_text.append(f"Avg Reward: ", style="white")
        results_text.append(f"{results['avg_reward']:.2f}\n", style="bold green")
        results_text.append(f"vs Best Baseline: ", style="white")
        
        if improvement > 0:
            results_text.append(f"↓ {improvement:.1f}% lower regret", style="bold green")
        else:
            results_text.append(f"↑ {abs(improvement):.1f}% higher regret", style="bold red")
        
        # Add explanation if IAI is worse
        if improvement < 0:
            results_text.append(f"\n\n", style="dim")
            results_text.append(f"Note: IAI may underperform initially due to:\n", style="dim")
            results_text.append(f"• Policy switching overhead\n", style="dim")
            results_text.append(f"• Learning which policy works best\n", style="dim")
            results_text.append(f"• Short run length vs exploration needs", style="dim")
        
        self.console.print(Panel(results_text, title="[bold]IAI Performance", border_style="cyan"))
        self.console.print()
    
    def show_challenger_analysis(self, proposal: Dict[str, Any]):
        """Show Challenger analysis with strain signals."""
        self.console.print("[bold magenta]🔍 Challenger Analysis...[/bold magenta]\n")
        
        if not proposal.get('proposed_metrics'):
            self.console.print(Panel(
                "[green]✓ No significant strain detected\nSystem appears stable[/green]",
                title="[bold]Challenger Result",
                border_style="green"
            ))
            return
        
        # Strain signals table
        signals = proposal.get('strain_signals', {})
        table = Table(title="Strain Signals Detected", box=box.ROUNDED)
        table.add_column("Signal", style="cyan")
        table.add_column("Value", style="yellow")
        table.add_column("Status", style="white")
        
        for key, value in signals.items():
            if isinstance(value, bool):
                if value:
                    table.add_row(key, "True", "⚠️  TRIGGERED", style="yellow")
            elif isinstance(value, (int, float)):
                table.add_row(key, f"{value:.3f}", "·")
        
        self.console.print(table)
        self.console.print()
        
        # Critiques
        if proposal.get('critiques'):
            self.console.print("[bold yellow]📋 Critiques:[/bold yellow]")
            for i, critique in enumerate(proposal['critiques'], 1):
                critique_panel = Panel(
                    f"[yellow]{critique['description']}[/yellow]\n\n"
                    f"[dim]Severity: {critique.get('severity', 'unknown')}[/dim]",
                    title=f"[bold]Critique {i}: {critique.get('signal', 'unknown')}",
                    border_style="yellow"
                )
                self.console.print(critique_panel)
            self.console.print()
        
        # Proposals
        if proposal.get('proposed_metrics'):
            self.console.print("[bold cyan]💡 Proposed Changes:[/bold cyan]")
            for i, prop in enumerate(proposal['proposed_metrics'], 1):
                self.console.print(Panel(
                    f"[cyan]{prop.get('description', 'No description')}[/cyan]\n\n"
                    f"[dim]Rationale: {prop.get('rationale', 'N/A')}[/dim]",
                    title=f"[bold]Proposal {i}: {prop.get('name', 'Unnamed')}",
                    border_style="cyan"
                ))
            self.console.print()
    
    def show_llm_thinking(self):
        """Show LLM is processing."""
        self.console.print("[bold magenta]🧠 LLM Authority Reviewing...[/bold magenta]")
        self.console.print("[dim]  (This may take 10-30 seconds)[/dim]\n")
    
    def show_authority_decision(self, decision: Dict[str, Any]):
        """Show Authority decision with full reasoning."""
        verdict = decision['verdict']
        
        # Color and emoji based on verdict
        if verdict == 'ACCEPT':
            color = "green"
            emoji = "✅"
            border = "green"
        elif verdict == 'REJECT':
            color = "red"
            emoji = "❌"
            border = "red"
        else:  # MODIFY
            color = "yellow"
            emoji = "🔧"
            border = "yellow"
        
        self.console.print(f"\n[bold {color}]{emoji} AUTHORITY DECISION: {verdict}[/bold {color}]\n")
        
        # Decision panel with reasoning
        decision_text = Text()
        decision_text.append("Confidence: ", style="white")
        decision_text.append(f"{decision['confidence']:.2f}\n\n", style="bold cyan")
        decision_text.append("Rationale:\n", style="bold white")
        decision_text.append(f"{decision['rationale']}\n", style=color)
        
        if decision.get('concerns'):
            decision_text.append("\nConcerns:\n", style="bold white")
            for concern in decision['concerns']:
                decision_text.append(f"  • {concern}\n", style="yellow")
        
        self.console.print(Panel(
            decision_text,
            title=f"[bold]LLM Authority Decision",
            border_style=border,
            padding=(1, 2)
        ))
        self.console.print()
    
    def show_invariant_update(self, old_inv: Dict, new_inv: Dict):
        """Show invariant evolution."""
        self.console.print("[bold green]🔄 Invariants Updated[/bold green]\n")
        
        # Side-by-side comparison
        layout = Layout()
        layout.split_row(
            Layout(Panel(
                Syntax(json.dumps(old_inv, indent=2), "json", theme="monokai"),
                title="[bold]Previous",
                border_style="dim"
            )),
            Layout(Panel(
                Syntax(json.dumps(new_inv, indent=2), "json", theme="monokai"),
                title="[bold]Updated",
                border_style="green"
            ))
        )
        self.console.print(layout)
        self.console.print()
    
    def show_evolution_summary(self, report: str):
        """Show final evolution summary."""
        self.console.print("\n" + "═" * 80 + "\n", style="bold green")
        self.console.print("[bold green]🎉 EVOLUTION COMPLETE[/bold green]")
        self.console.print("═" * 80 + "\n", style="bold green")
        
        # Parse and display report nicely
        self.console.print(Panel(
            report,
            title="[bold]Evolution Summary",
            border_style="green",
            padding=(1, 2)
        ))
        self.console.print()
