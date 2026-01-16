"""Run IAI evolution with LIVE fixed dashboard - no scrolling!

This version updates a fixed terminal layout in place, like htop or top.
No need to scroll to see what's happening!
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from orchestrator_live import IAIOrchestratorLive


def main():
    parser = argparse.ArgumentParser(
        description="Run IAI evolution with live fixed dashboard"
    )
    parser.add_argument(
        '--generations', type=int, default=5,
        help='Number of evolution generations (default: 5)'
    )
    parser.add_argument(
        '--steps', type=int, default=10000,
        help='Steps per bandit run (default: 10000)'
    )
    parser.add_argument(
        '--runs', type=int, default=5,
        help='Random seeds per system (default: 5)'
    )
    parser.add_argument(
        '--drift-step', type=int, default=7000,
        help='When to introduce distribution shift (default: 7000)'
    )
    parser.add_argument(
        '--model', type=str, default='qwen2.5-1.5b',
        choices=['qwen2.5-0.5b', 'qwen2.5-1.5b', 'phi-3.5-mini', 'phi-4-mini', 'llama-3.2-1b'],
        help='Foundry Local model to use (default: qwen2.5-1.5b)'
    )
    parser.add_argument(
        '--strictness', type=str, default='balanced',
        choices=['strict', 'balanced', 'permissive'],
        help='Authority decision strictness (default: balanced)'
    )
    parser.add_argument(
        '--output', type=str, default='runs/iai_evolution',
        help='Base output directory (default: runs/iai_evolution)'
    )
    parser.add_argument(
        '--no-timestamp', action='store_true',
        help='Disable automatic timestamping of output directory'
    )
    
    args = parser.parse_args()
    
    # Create timestamped output directory
    if not args.no_timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        base_dir = Path(args.output)
        output_dir = base_dir / timestamp
    else:
        output_dir = args.output
    
    # Create live orchestrator
    orchestrator = IAIOrchestratorLive(
        output_dir=str(output_dir),
        model_alias=args.model,
        strictness=args.strictness,
        experiment_params={
            'generations': args.generations,
            'steps': args.steps,
            'runs': args.runs,
            'drift_step': args.drift_step,
            'model': args.model,
            'strictness': args.strictness
        }
    )
    
    # Run evolution with live display
    try:
        report = orchestrator.run_evolution(
            max_generations=args.generations,
            n_steps=args.steps,
            n_runs=args.runs,
            drift_step=args.drift_step
        )
        
        # Clean completion message
        orchestrator.dashboard.console.clear()
        orchestrator.dashboard.console.print(
            Panel(
                f"[bold green]✓ Experiment Complete![/bold green]\n\n"
                f"[cyan]Results saved to:[/cyan] {args.output}\n\n"
                f"[yellow]To generate analysis report with plots:[/yellow]\n"
                f"  [bold]python pilots/iai_bandit_poc/src/analyze_evolution.py --run-dir {args.output}[/bold]\n\n"
                f"[dim](Report will be created at: {args.output}/ANALYSIS_REPORT.md)[/dim]",
                title="🎉 IAI Evolution",
                border_style="green"
            )
        )
        
        # Wait for user
        orchestrator.dashboard.console.print(
            "\n[dim]Press Enter to exit...[/dim]"
        )
        input()
        
    except KeyboardInterrupt:
        orchestrator.dashboard.console.clear()
        orchestrator.dashboard.console.print(
            "\n\n[bold yellow]⚠ Evolution interrupted by user[/bold yellow]\n"
        )
    except Exception as e:
        orchestrator.dashboard.console.clear()
        orchestrator.dashboard.console.print(
            f"\n\n[bold red]❌ ERROR: {e}[/bold red]\n"
        )
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
