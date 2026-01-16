"""Live updating dashboard with fixed terminal layout - no scrolling!

Provides real-time view with:
- Fixed layout that updates in place
- Current generation status
- Live performance metrics
- LLM decision display
- All visible without scrolling
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.syntax import Syntax
from rich import box
import json
from typing import Dict, Any
from datetime import datetime


class LiveDashboard:
    """Fixed terminal dashboard that updates in place."""
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        
        # State
        self.config = {}
        self.baseline_results = {}
        self.current_gen = 0
        self.total_gens = 0
        self.iai_results = {}
        self.proposal = {}
        self.decision = {}
        self.phase = "Starting..."
        self.status_message = ""
        self.generation_history = []  # Track evolution across generations
        
    def create_layout(self):
        """Create the fixed layout structure."""
        self.layout.split_column(
            Layout(name="header", size=5),
            Layout(name="main", ratio=2),
            Layout(name="footer", minimum_size=12)
        )
        
        self.layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        
    def update_header(self):
        """Update header with current phase."""
        header_text = Text()
        header_text.append("🧠 IAI EVOLUTION DASHBOARD\n", style="bold cyan")
        header_text.append(f"Phase: {self.phase}\n", style="bold yellow")
        if self.total_gens > 0:
            header_text.append(f"Generation: {self.current_gen}/{self.total_gens-1}", style="bold white")
        
        self.layout["header"].update(Panel(header_text, border_style="cyan"))
    
    def update_left_panel(self):
        """Update left panel with config and baseline."""
        content = ""
        
        # Configuration
        if self.config:
            config_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
            config_table.add_column(style="cyan")
            config_table.add_column(style="white")
            
            config_table.add_row("🎯 Generations", str(self.config.get('generations', '-')))
            config_table.add_row("📊 Steps", str(self.config.get('steps', '-')))
            config_table.add_row("🔄 Runs", str(self.config.get('runs', '-')))
            config_table.add_row("🤖 Model", self.config.get('model', '-'))
            
            content = Panel(config_table, title="[bold]Configuration", border_style="cyan")
        
        # Baseline Results
        if self.baseline_results:
            baseline_table = Table(box=box.ROUNDED)
            baseline_table.add_column("System", style="cyan")
            baseline_table.add_column("Reward", style="green", justify="right")
            baseline_table.add_column("Regret", style="yellow", justify="right")
            baseline_table.add_column("Status", justify="center")
            
            best = self.baseline_results.get('best_system', '')
            for sys in self.baseline_results.get('all_systems', []):
                is_best = sys['system'] == best
                status = "🏆" if is_best else "·"
                style = "bold green" if is_best else ""
                
                baseline_table.add_row(
                    sys['system'],
                    f"{sys.get('final_reward', 0):.1f}",
                    f"{sys['final_regret']:.1f}",
                    status,
                    style=style
                )
            
            baseline_panel = Panel(baseline_table, title="[bold]Baseline", border_style="green")
            
            # Add IAI results if available
            iai_panel = None
            if self.iai_results:
                iai_table = Table(box=box.ROUNDED, show_header=False)
                iai_table.add_column("Metric", style="white")
                iai_table.add_column("Value", style="bold cyan", justify="right")
                iai_table.add_row("Regret", f"{self.iai_results.get('avg_regret', 0):.2f}")
                iai_table.add_row("Reward", f"{self.iai_results.get('avg_reward', 0):.2f}")
                iai_panel = Panel(iai_table, title="[bold]IAI Performance", border_style="cyan")
            
            if content and iai_panel:
                from rich.console import Group
                self.layout["left"].update(Group(content, baseline_panel, iai_panel))
            elif content:
                from rich.console import Group
                self.layout["left"].update(Group(content, baseline_panel))
            elif iai_panel:
                from rich.console import Group
                self.layout["left"].update(Group(baseline_panel, iai_panel))
            else:
                self.layout["left"].update(baseline_panel)
        elif content:
            self.layout["left"].update(content)
    
    def update_right_panel(self):
        """Update right panel with current generation info."""
        panels = []
        
        # Challenger Analysis
        if self.proposal:
            if self.proposal.get('proposed_metrics'):
                prop_text = Text()
                prop_text.append("⚠️  Strain Detected\n\n", style="bold yellow")
                
                for crit in self.proposal.get('critiques', [])[:2]:  # Show max 2
                    prop_text.append(f"• {crit.get('signal', 'unknown')}\n", style="yellow")
                
                prop_text.append(f"\nProposal: ", style="bold cyan")
                if self.proposal.get('proposed_metrics'):
                    prop_text.append(f"{self.proposal['proposed_metrics'][0].get('name', 'unknown')}", style="cyan")
                
                panels.append(Panel(prop_text, title="[bold]Challenger", border_style="yellow"))
            else:
                panels.append(Panel(
                    Text("✓ No strain detected", style="green"),
                    title="[bold]Challenger",
                    border_style="green"
                ))
        
        # LLM Decision (always visible with generation info)
        if self.decision:
            verdict = self.decision.get('verdict', 'PENDING')
            color = {"ACCEPT": "green", "REJECT": "red", "MODIFY": "yellow", "NO_CHANGE": "dim"}.get(verdict, "white")
            emoji = {"ACCEPT": "✅", "REJECT": "❌", "MODIFY": "🔧", "NO_CHANGE": "✓"}.get(verdict, "⏳")
            
            # Build title with generation info
            gen_info = f" - Gen {self.decision_generation}" if hasattr(self, 'decision_generation') and self.decision_generation is not None else ""
            panel_title = f"[bold]Latest Authority Decision{gen_info}"
            
            decision_text = Text()
            decision_text.append(f"{emoji} {verdict}\n", style=f"bold {color}")
            decision_text.append("─" * 40 + "\n", style="dim")
            
            # Confidence
            decision_text.append("Confidence: ", style="bold white")
            decision_text.append(f"{self.decision.get('confidence', 0):.2f}\n\n", style="bold cyan")
            
            # Full rationale (no truncation)
            rationale = self.decision.get('rationale', '')
            decision_text.append("Rationale:\n", style="bold white")
            decision_text.append(rationale, style="white")
            
            # Show any modifications if present
            if verdict == 'MODIFY' and self.decision.get('modifications'):
                decision_text.append("\n\n", style="white")
                decision_text.append("Modifications:\n", style="bold yellow")
                mods = self.decision.get('modifications', '')
                decision_text.append(str(mods), style="yellow")
            
            panels.append(Panel(decision_text, title=panel_title, border_style=color))
        else:
            # Show summary of recent decisions if available
            if self.generation_history:
                summary = Text()
                summary.append("💤 Idle\n", style="bold dim")
                summary.append("─" * 40 + "\n", style="dim")
                summary.append("No current proposals to review\n\n", style="dim")
                
                # Count decisions
                total_gens = len(self.generation_history)
                accepts = sum(1 for h in self.generation_history if h['decision'] == 'ACCEPT')
                rejects = sum(1 for h in self.generation_history if h['decision'] == 'REJECT')
                modifies = sum(1 for h in self.generation_history if h['decision'] == 'MODIFY')
                no_review = total_gens - accepts - rejects - modifies
                
                summary.append("Decision Summary:\n", style="bold white")
                if accepts > 0:
                    summary.append(f"  ✅ Accepted: {accepts}\n", style="green")
                if rejects > 0:
                    summary.append(f"  ❌ Rejected: {rejects}\n", style="red")
                if modifies > 0:
                    summary.append(f"  🔧 Modified: {modifies}\n", style="yellow")
                if no_review > 0:
                    summary.append(f"  — No Review: {no_review}\n", style="dim")
                
                panels.append(Panel(summary, title="[bold]LLM Authority", border_style="dim"))
            else:
                idle_text = Text()
                idle_text.append("💤 Idle\n\n", style="bold dim")
                idle_text.append("No proposals to review\n", style="dim")
                idle_text.append("(Triggered only when Challenger detects strain)", style="dim italic")
                panels.append(Panel(idle_text, title="[bold]LLM Authority", border_style="dim"))
        
        if panels:
            from rich.console import Group
            self.layout["right"].update(Group(*panels))
    
    def update_footer(self):
        """Update footer with evolution history for traceability."""
        if self.generation_history:
            # Show only last 5 generations to keep it scalable
            MAX_VISIBLE_GENERATIONS = 5
            total_gens = len(self.generation_history)
            visible_history = self.generation_history[-MAX_VISIBLE_GENERATIONS:] if total_gens > MAX_VISIBLE_GENERATIONS else self.generation_history
            skipped_count = total_gens - len(visible_history)
            
            # Build title with count info
            title = "📊 Evolution History"
            if skipped_count > 0:
                title += f" (showing last {len(visible_history)} of {total_gens})"
            
            # Build history table
            history_table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan", title=title)
            history_table.add_column("Gen", justify="center", width=5)
            history_table.add_column("Reward", justify="right", width=9)
            history_table.add_column("Rwd vs Prev", justify="right", width=11)
            history_table.add_column("Rwd vs Base", justify="right", width=11)
            history_table.add_column("Regret", justify="right", width=9)
            history_table.add_column("Reg vs Prev", justify="right", width=11)
            history_table.add_column("Reg vs Base", justify="right", width=11)
            history_table.add_column("Strain?", justify="center", width=8)
            history_table.add_column("LLM", justify="center", width=10)
            history_table.add_column("Status", justify="left", width=15)
            
            baseline_regret = self.baseline_results.get('best_regret', 0)
            
            for idx, h in enumerate(visible_history):
                strain_icon = "⚠️  Yes" if h['strain'] else "✓ No"
                strain_color = "yellow" if h['strain'] else "green"
                
                decision_text = h['decision']
                if decision_text == 'ACCEPT':
                    decision_display = "[green]✅ Accept[/green]"
                    status = "[green]Updated[/green]"
                elif decision_text == 'REJECT':
                    decision_display = "[red]❌ Reject[/red]"
                    status = "[red]Rejected[/red]"
                elif decision_text == 'MODIFY':
                    decision_display = "[yellow]🔧 Modify[/yellow]"
                    status = "[yellow]Modified[/yellow]"
                else:
                    decision_display = "[dim]—[/dim]"
                    status = "[dim]Stable[/dim]"
                
                # Calculate REWARD performance vs previous generation
                baseline_reward = self.baseline_results.get('best_reward', 0)
                if idx > 0:
                    prev_reward = visible_history[idx - 1]['reward']
                    prev_reward_diff = ((h['reward'] - prev_reward) / prev_reward * 100) if prev_reward > 0 else 0
                    if abs(prev_reward_diff) < 0.1:
                        rwd_vs_prev = "[dim]~0%[/dim]"
                    elif prev_reward_diff > 0:
                        rwd_vs_prev = f"[green]+{prev_reward_diff:.1f}%[/green]"
                    else:
                        rwd_vs_prev = f"[red]{prev_reward_diff:.1f}%[/red]"
                else:
                    rwd_vs_prev = "[dim]—[/dim]"
                
                # Calculate REWARD vs baseline
                reward_diff = ((h['reward'] - baseline_reward) / baseline_reward * 100) if baseline_reward > 0 else 0
                if abs(reward_diff) < 0.1:
                    rwd_vs_baseline = "[dim]~0%[/dim]"
                elif reward_diff > 0:
                    rwd_vs_baseline = f"[green]+{reward_diff:.1f}%[/green]"
                else:
                    rwd_vs_baseline = f"[red]{reward_diff:.1f}%[/red]"
                
                # Calculate REGRET performance vs previous generation
                if idx > 0:
                    prev_regret = visible_history[idx - 1]['regret']
                    prev_regret_diff = ((h['regret'] - prev_regret) / prev_regret * 100) if prev_regret > 0 else 0
                    if abs(prev_regret_diff) < 0.1:
                        reg_vs_prev = "[dim]~0%[/dim]"
                    elif prev_regret_diff > 0:
                        reg_vs_prev = f"[red]+{prev_regret_diff:.1f}%[/red]"
                    else:
                        reg_vs_prev = f"[green]{prev_regret_diff:.1f}%[/green]"
                else:
                    reg_vs_prev = "[dim]—[/dim]"
                
                # Calculate REGRET vs baseline
                regret_diff = ((h['regret'] - baseline_regret) / baseline_regret * 100) if baseline_regret > 0 else 0
                if abs(regret_diff) < 0.1:
                    reg_vs_baseline = "[dim]~0%[/dim]"
                elif regret_diff > 0:
                    reg_vs_baseline = f"[red]+{regret_diff:.1f}%[/red]"
                else:
                    reg_vs_baseline = f"[green]{regret_diff:.1f}%[/green]"
                
                history_table.add_row(
                    str(h['gen']),
                    f"{h['reward']:.1f}",
                    rwd_vs_prev,
                    rwd_vs_baseline,
                    f"{h['regret']:.1f}",
                    reg_vs_prev,
                    reg_vs_baseline,
                    f"[{strain_color}]{strain_icon}[/{strain_color}]",
                    decision_display,
                    status
                )
            
            # Add status message below history table
            status_text = Text()
            status_text.append(self.status_message or "Ready", style="dim italic")
            status_text.append(f"  •  {datetime.now().strftime('%H:%M:%S')}", style="dim")
            
            from rich.console import Group
            footer_content = Panel(Group(history_table, status_text), border_style="cyan")
        else:
            footer_text = Text()
            footer_text.append(self.status_message or "Waiting for results...", style="dim")
            footer_text.append(f"\n{datetime.now().strftime('%H:%M:%S')}", style="dim")
            footer_content = Panel(footer_text, border_style="dim")
        
        self.layout["footer"].update(footer_content)
    
    def update_display(self):
        """Refresh the entire display."""
        self.update_header()
        self.update_left_panel()
        self.update_right_panel()
        self.update_footer()
    
    def set_config(self, config: Dict[str, Any]):
        """Set configuration."""
        self.config = config
        self.total_gens = config.get('generations', 0)
    
    def set_phase(self, phase: str):
        """Set current phase."""
        self.phase = phase
    
    def set_status(self, message: str):
        """Set status message."""
        self.status_message = message
    
    def set_baseline_results(self, results: Dict[str, Any]):
        """Set baseline results."""
        self.baseline_results = results
        # Extract best reward for comparison
        if 'all_systems' in results:
            best_system_name = results.get('best_system', '')
            for sys in results['all_systems']:
                if sys['system'] == best_system_name:
                    self.baseline_results['best_reward'] = sys.get('final_reward', 0)
                    break
    
    def set_generation(self, gen: int):
        """Set current generation."""
        self.current_gen = gen
    
    def set_iai_results(self, results: Dict[str, Any]):
        """Set IAI results."""
        self.iai_results = results
    
    def set_proposal(self, proposal: Dict[str, Any]):
        """Set Challenger proposal."""
        self.proposal = proposal
    
    def set_decision(self, decision: Dict[str, Any], generation: int = None):
        """Set Authority decision with generation info - keeps it visible."""
        self.decision = decision
        self.decision_generation = generation  # Track which generation this decision is for
    
    def add_generation_result(self, gen: int, regret: float, reward: float, strain_detected: bool, decision_verdict: str = None):
        """Add a generation result to history for tracking evolution."""
        self.generation_history.append({
            'gen': gen,
            'regret': regret,
            'reward': reward,
            'strain': strain_detected,
            'decision': decision_verdict or 'NO_REVIEW'
        })
    
    def clear_generation_state(self):
        """Clear generation-specific state, but KEEP the last decision visible."""
        self.iai_results = {}
        self.proposal = {}
        # Don't clear decision or decision_generation - keep them visible permanently
    
    def show_final_summary(self, report: str, analysis_paths: dict = None):
        """Show final summary in scrollable format with links to generated files."""
        self.console.clear()
        self.console.print("\n" + "═" * 80 + "\n", style="bold green")
        self.console.print("🎉 EVOLUTION COMPLETE", style="bold green", justify="center")
        self.console.print("\n" + "═" * 80 + "\n", style="bold green")
        self.console.print(report)
        
        # Show generated analysis report
        if analysis_paths and analysis_paths.get('success'):
            self.console.print("\n" + "═" * 80, style="bold cyan")
            self.console.print("📊 ANALYSIS REPORT", style="bold cyan", justify="center")
            self.console.print("═" * 80 + "\n", style="bold cyan")
            
            if analysis_paths.get('markdown'):
                md_path = analysis_paths['markdown']
                self.console.print("[bold yellow]📋 Full Analysis Report (with plots & data links):[/bold yellow]")
                self.console.print(f"   [link={md_path}]{md_path}[/link]", style="bold cyan")
                self.console.print("")
                self.console.print("[dim]Open in VS Code to view embedded plots, metrics tables, and data file links.[/dim]")
            
            # Also show direct links to raw data files
            self.console.print("\n[bold]Raw Data Files:[/bold]")
            if analysis_paths.get('csv'):
                self.console.print(f"  📄 [link={analysis_paths['csv']}]evolution_history.csv[/link] - Metrics per generation", style="dim cyan")
            if analysis_paths.get('json'):
                self.console.print(f"  📄 [link={analysis_paths['json']}]experiment_summary.json[/link] - Structured data", style="dim cyan")
            if analysis_paths.get('plots_dir'):
                self.console.print(f"  📁 [link={analysis_paths['plots_dir']}]plots/[/link] - PNG visualizations", style="dim cyan")
        
        self.console.print("\n" + "═" * 80 + "\n", style="bold green")
