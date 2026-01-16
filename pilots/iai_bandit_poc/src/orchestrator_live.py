"""Visual orchestrator with LIVE fixed dashboard - no scrolling!"""

from orchestrator import IAIOrchestrator
from dashboard_live import LiveDashboard
from rich.live import Live
from pathlib import Path
import time
import numpy as np
import pandas as pd
from bandits import make_drift_pair, BernoulliBandit
from policies import IAIPolicySelector, EpsilonGreedy, UCB1, ThompsonBernoulli
from evaluator import Evaluator


class IAIOrchestratorLive(IAIOrchestrator):
    """Orchestrator with live fixed dashboard."""
    
    def __init__(self, output_dir='runs/iai_evolution', model_alias='qwen2.5-1.5b', strictness='balanced', experiment_params=None):
        super().__init__(output_dir, model_alias, strictness)
        self.dashboard = LiveDashboard()
        self.experiment_params = experiment_params or {}
    
    def _run_generation(self, generation, n_steps, n_runs, drift_step):
        """Override to show progress for each individual run."""
        all_trajectories = {}
        results_summary = []
        
        for run in range(n_runs):
            # Show progress for this run
            self.dashboard.set_status(f"Gen {generation}: Running seed {run+1}/{n_runs}...")
            self.dashboard.update_display()
            
            # Run single IAI experiment with specific seed
            # Use generation-aware seed to ensure different experiments have different randomness
            seed = generation * 1000 + run
            
            # Create environment with this seed
            rng_env = np.random.default_rng(seed)
            pre, post, _, _ = make_drift_pair(k=5, rng=rng_env)
            env = BernoulliBandit(means_pre=pre, means_post=post, drift_step=drift_step, rng=rng_env)
            
            # Create IAI selector with offset seed for policy
            rng_pol = np.random.default_rng(seed * 1000)
            policy = IAIPolicySelector(
                base_policies=[EpsilonGreedy(epsilon=0.1), UCB1(), ThompsonBernoulli()],
                gamma=0.05
            )
            policy.reset(env.k, rng_pol)
            
            # Run evaluation
            evaluator = Evaluator(true_means_fn=env.true_means, k=env.k, max_steps=n_steps)
            df = evaluator.run(policy=policy, env=env, steps=n_steps, system_name='iai')
            
            all_trajectories[f'iai_seed{run}'] = df
            results_summary.append({
                'system': 'iai',
                'seed': run,
                'final_regret': df['cum_regret'].iloc[-1],
                'final_reward': df['cum_reward'].iloc[-1],
                'avg_switch_rate': df['switched'].mean()
            })
            
            # Show intermediate average
            if len(results_summary) > 0:
                summary_df = pd.DataFrame(results_summary)
                current_avg = summary_df['final_regret'].mean()
                self.dashboard.set_iai_results({
                    'avg_regret': current_avg,
                    'avg_reward': summary_df['final_reward'].mean()
                })
                self.dashboard.set_status(f"Gen {generation}: {run+1}/{n_runs} runs complete (avg regret: {current_avg:.1f})")
                self.dashboard.update_display()
        
        # Compute final summary
        summary_df = pd.DataFrame(results_summary)
        avg_regret = summary_df['final_regret'].mean()
        avg_reward = summary_df['final_reward'].mean()
        
        return {
            'trajectories': all_trajectories,
            'summary': {
                'system': 'iai',
                'avg_regret': float(avg_regret),
                'avg_reward': float(avg_reward),
                'cum_reward': int(avg_reward),
                'cum_regret': float(avg_regret),
                'switch_rate': float(summary_df['avg_switch_rate'].mean()),
                'runs': results_summary
            }
        }
    
    def run_evolution(self, max_generations=5, n_steps=10000, n_runs=3, drift_step=7000):
        """Run evolution with live fixed display."""
        
        # Setup
        self.dashboard.create_layout()
        self.dashboard.set_config({
            'generations': max_generations,
            'steps': n_steps,
            'runs': n_runs,
            'model': self.model_alias,
            'strictness': self.strictness
        })
        
        with Live(self.dashboard.layout, console=self.dashboard.console, refresh_per_second=4) as live:
            # Phase 1: Baseline
            self.dashboard.set_phase("BASELINE")
            self.dashboard.set_status("Running baseline algorithms...")
            self.dashboard.update_display()
            
            self.baseline_results = self._run_baseline(n_steps, n_runs, drift_step)
            
            # Extract for display
            best_system = self.baseline_results['summary']['best_system']
            best_regret = self.baseline_results['summary']['best_regret']
            
            # Group by system
            system_stats = {}
            for rec in self.baseline_results['summary']['all_systems']:
                sys_name = rec['system']
                if sys_name not in system_stats:
                    system_stats[sys_name] = {'regrets': [], 'rewards': []}
                system_stats[sys_name]['regrets'].append(rec['final_regret'])
                system_stats[sys_name]['rewards'].append(rec['final_reward'])
            
            self.dashboard.set_baseline_results({
                'best_system': best_system,
                'best_regret': best_regret,
                'all_systems': [
                    {
                        'system': sys_name,
                        'final_regret': sum(stats['regrets']) / len(stats['regrets']),
                        'final_reward': sum(stats['rewards']) / len(stats['rewards'])
                    }
                    for sys_name, stats in system_stats.items()
                ]
            })
            
            # Update Challenger with baseline regret for absolute comparison
            self.challenger.baseline_regret = best_regret
            self.dashboard.console.print(f"\n  [dim]Challenger updated: baseline_regret = {best_regret:.2f}[/dim]")
            
            self.dashboard.set_status(f"Baseline complete. Best: {best_system} ({best_regret:.1f} regret)")
            self.dashboard.update_display()
            time.sleep(2)
            
            # Phase 2: Evolution
            for gen in range(max_generations):
                self.dashboard.set_phase(f"EVOLUTION - Generation {gen}")
                self.dashboard.set_generation(gen)
                # Don't clear IAI results - keep them visible
                # Only clear proposal/decision for new generation
                self.dashboard.proposal = {}
                self.dashboard.decision = {}
                self.dashboard.set_status(f"Running IAI system...")
                self.dashboard.update_display()
                
                # Run IAI with live progress updates
                self.dashboard.console.print(f"\n[bold cyan]▶ Running Generation {gen}...[/bold cyan]")
                gen_results = self._run_generation(gen, n_steps, n_runs, drift_step)
                
                avg_regret = gen_results['summary']['avg_regret']
                avg_reward = gen_results['summary']['avg_reward']
                
                # Update dashboard immediately with results
                self.dashboard.set_iai_results({
                    'avg_regret': avg_regret,
                    'avg_reward': avg_reward
                })
                self.dashboard.set_status(f"Gen {gen} complete: IAI Regret {avg_regret:.1f} (10 runs avg)")
                self.dashboard.update_display()
                
                # Challenge
                self.dashboard.console.print(f"\n[bold magenta]▶ Challenger analyzing...[/bold magenta]")
                proposal = self._run_challenge(gen_results)
                self.dashboard.set_proposal(proposal)
                
                # Track meta-metrics: was a proposal made?
                proposal_made = bool(proposal.get('proposed_metrics'))
                if proposal_made:
                    self.meta_metrics['proposals_made'] += 1
                
                # Show simple summary
                if proposal_made:
                    self.dashboard.console.print(f"  [yellow]⚠️  Strain detected: {proposal['proposed_metrics'][0]['name']}[/yellow]")
                else:
                    self.dashboard.console.print(f"  [green]✓ No strain detected[/green]")
                
                time.sleep(0.5)
                
                # Authority review - ALWAYS invoked per authority-heartbeat.md
                # Authority provides governance even when no strain detected
                self.dashboard.set_status("LLM Authority reviewing (routine governance)...")
                self.dashboard.update_display()
                
                decision = self.authority.review_proposal(
                    challenger_output=proposal,
                    current_metrics=gen_results['summary'],
                    baseline_metrics=self.baseline_results['summary'],
                    current_invariants=self.current_invariants,
                    generation=gen
                )
                
                # Set decision with generation info - keep it visible
                self.dashboard.set_decision(decision, generation=gen)
                self.dashboard.set_status(f"Authority decision (Gen {gen}): {decision['verdict']}")
                self.dashboard.update_display()
                
                # Pause to let user read the decision
                time.sleep(5)  # Increased from 2 to 5 seconds
                
                # Apply if accepted
                updated = False
                if decision['verdict'] in ['ACCEPT', 'MODIFY']:
                    old_invariants = self.current_invariants.copy()
                    updated = True
                    
                    if decision['verdict'] == 'ACCEPT' and proposal.get('proposed_metrics'):
                        self.current_invariants = self._apply_proposal(proposal['proposed_metrics'][0])
                        self.meta_metrics['proposals_accepted'] += 1
                    elif decision.get('modified_proposal'):
                        self.current_invariants = self._apply_proposal(decision['modified_proposal'])
                        self.meta_metrics['proposals_modified'] += 1
                    
                    self.dashboard.set_status(f"Invariants updated: {list(self.current_invariants.keys())}")
                    self.dashboard.update_display()
                    time.sleep(1)
                elif decision['verdict'] == 'REJECT':
                    self.meta_metrics['proposals_rejected'] += 1
                    self.dashboard.set_status("Proposal rejected - no changes")
                    self.dashboard.update_display()
                    time.sleep(0.5)
                
                # Track per-generation meta-metrics
                gen_meta = {
                    'generation': gen,
                    'proposal_made': proposal_made,
                    'strain_signals': proposal.get('strain_signals', {}),
                    'current_regret': gen_results['summary']['avg_regret'],
                    'decision': decision.get('verdict'),
                    'next_gen_improved': None  # Set after next generation
                }
                self.meta_metrics['per_generation'].append(gen_meta)
                
                # Check if previous generation's change led to improvement
                if updated and len(self.meta_metrics['per_generation']) >= 2:
                    prev_gen_meta = self.meta_metrics['per_generation'][-2]
                    if prev_gen_meta.get('decision') in ['ACCEPT', 'MODIFY']:
                        current_regret = gen_results['summary']['avg_regret']
                        prev_regret = prev_gen_meta['current_regret']
                        if current_regret < prev_regret:
                            self.meta_metrics['improvements_after_accept'] += 1
                            prev_gen_meta['next_gen_improved'] = True
                        else:
                            self.meta_metrics['regressions_after_accept'] += 1
                            prev_gen_meta['next_gen_improved'] = False
                
                # Save generation and update dashboard history
                self._save_generation(gen, gen_results, proposal, decision)
                
                # Add to history IMMEDIATELY so user sees it building up
                self.dashboard.add_generation_result(
                    gen=gen,
                    regret=gen_results['summary']['avg_regret'],
                    reward=gen_results['summary']['avg_reward'],
                    strain_detected=bool(proposal.get('proposed_metrics')),
                    decision_verdict=decision.get('verdict')
                )
                
                # Update display to show new history entry NOW
                self.dashboard.set_status(f"Gen {gen} saved to history")
                self.dashboard.update_display()
                time.sleep(1)
                
                self.generation_history.append({
                    'generation': gen,
                    'invariants': self.current_invariants.copy(),
                    'proposal': proposal,
                    'decision': decision,  # Always present now with heartbeat
                    'updated': decision['verdict'] in ['ACCEPT', 'MODIFY']
                })
                
                self.dashboard.console.print(f"\n[dim]{'='*60}[/dim]")
        
        # Final report (scrollable)
        report = self._generate_report()
        self.authority.save_decision_history(self.output_dir)
        
        # Auto-generate analysis with plots
        analysis_paths = self._run_analysis()
        
        # Update run index
        self._update_run_index(analysis_paths)
        
        self.dashboard.show_final_summary(report, analysis_paths)
        
        return report
    
    def _update_run_index(self, analysis_paths: dict):
        """Update the master index of all runs."""
        import json
        from datetime import datetime
        
        output_path = Path(self.output_dir)
        
        # Find the base directory (parent of timestamped run)
        # If output is "runs/iai_evolution/2026-01-15_164500", base is "runs/iai_evolution"
        if output_path.parent.name == 'iai_evolution':
            base_dir = output_path.parent
        else:
            # No timestamping, skip index
            return
        
        index_file = base_dir / 'RUN_INDEX.md'
        json_index = base_dir / 'runs_index.json'
        
        # Load existing index
        if json_index.exists():
            with open(json_index, 'r') as f:
                runs_data = json.load(f)
        else:
            runs_data = {'runs': []}
        
        # Get summary data
        summary_file = output_path / 'experiment_summary.json'
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                summary = json.load(f)
        else:
            summary = {}
        
        # Add this run
        run_entry = {
            'timestamp': datetime.now().isoformat(),
            'directory': output_path.name,
            'parameters': self.experiment_params,
            'results': {
                'generations': summary.get('experiment_info', {}).get('total_generations', 0),
                'baseline_regret': summary.get('experiment_info', {}).get('baseline_regret', 0),
                'proposals_made': summary.get('proposal_effectiveness', {}).get('proposals_made', 0),
                'acceptance_rate': (
                    (summary.get('decision_summary', {}).get('accepted', 0) + 
                     summary.get('decision_summary', {}).get('modified', 0)) / 
                    max(1, sum(summary.get('decision_summary', {}).values())) * 100
                ) if summary.get('decision_summary') else 0,
                'effectiveness_rate': summary.get('proposal_effectiveness', {}).get('effectiveness_rate', 0)
            },
            'report_path': f"{output_path.name}/ANALYSIS_REPORT.md"
        }
        
        runs_data['runs'].append(run_entry)
        
        # Save JSON index
        with open(json_index, 'w') as f:
            json.dump(runs_data, f, indent=2)
        
        # Generate markdown index
        self._generate_markdown_index(runs_data, index_file)
        
        self.dashboard.console.print(f"\n[bold green]✓ Run index updated:[/bold green] [link={index_file}]{index_file}[/link]")
    
    def _generate_markdown_index(self, runs_data: dict, output_path: Path):
        """Generate markdown index of all runs."""
        md = []
        
        md.append("# IAI Evolution Experiment Runs")
        md.append("")
        md.append(f"**Total Runs:** {len(runs_data['runs'])}")
        md.append("")
        md.append("---")
        md.append("")
        
        # Table of all runs
        md.append("## All Runs")
        md.append("")
        md.append("| Timestamp | Gens | Steps | Runs | Model | Baseline Regret | Accept% | Effectiveness% | Report |")
        md.append("|-----------|------|-------|------|-------|-----------------|---------|----------------|--------|")
        
        for run in sorted(runs_data['runs'], key=lambda x: x['timestamp'], reverse=True):
            ts = run['timestamp'][:19].replace('T', ' ')
            params = run['parameters']
            results = run['results']
            report_link = f"[📋 View]({run['report_path']})"
            
            md.append(
                f"| {ts} | "
                f"{results['generations']} | "
                f"{params.get('steps', 'N/A')} | "
                f"{params.get('runs', 'N/A')} | "
                f"{params.get('model', 'N/A')} | "
                f"{results['baseline_regret']:.1f} | "
                f"{results['acceptance_rate']:.1f}% | "
                f"{results['effectiveness_rate']:.1f}% | "
                f"{report_link} |"
            )
        
        md.append("")
        md.append("---")
        md.append("")
        
        # Detailed run summaries
        md.append("## Run Details")
        md.append("")
        
        for i, run in enumerate(sorted(runs_data['runs'], key=lambda x: x['timestamp'], reverse=True), 1):
            ts_display = run['timestamp'][:19].replace('T', ' ')
            params = run['parameters']
            results = run['results']
            
            md.append(f"### Run {i}: {run['directory']}")
            md.append("")
            md.append(f"**Timestamp:** {ts_display}")
            md.append("")
            md.append("**Parameters:**")
            md.append(f"- Generations: {params.get('generations', 'N/A')}")
            md.append(f"- Steps: {params.get('steps', 'N/A')}")
            md.append(f"- Runs per generation: {params.get('runs', 'N/A')}")
            md.append(f"- Model: {params.get('model', 'N/A')}")
            md.append(f"- Strictness: {params.get('strictness', 'N/A')}")
            md.append("")
            md.append("**Results:**")
            md.append(f"- Baseline Regret: {results['baseline_regret']:.2f}")
            md.append(f"- Proposals Made: {results['proposals_made']}")
            md.append(f"- Acceptance Rate: {results['acceptance_rate']:.1f}%")
            md.append(f"- Effectiveness Rate: {results['effectiveness_rate']:.1f}%")
            md.append("")
            md.append(f"📋 **[Full Analysis Report]({run['report_path']})**")
            md.append("")
            md.append("---")
            md.append("")
        
        # Write markdown
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md))
    
    def _run_analysis(self) -> dict:
        """Run post-evolution analysis to generate consolidated logs and plots."""
        from pathlib import Path
        import subprocess
        import sys
        
        self.dashboard.console.print("\n[bold cyan]Generating analysis reports and plots...[/bold cyan]")
        
        # Find the analyze_evolution.py script (same dir as this file)
        script_dir = Path(__file__).parent.resolve()
        analyze_script = script_dir / "analyze_evolution.py"
        
        # Resolve output_dir to absolute path
        output_dir_abs = Path(self.output_dir).resolve()
        
        paths = {
            'markdown': None,
            'csv': None,
            'json': None,
            'plots_dir': None,
            'success': False
        }
        
        if analyze_script.exists():
            try:
                # Run the analysis script with absolute paths
                result = subprocess.run(
                    [sys.executable, str(analyze_script), "--run-dir", str(output_dir_abs)],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=120,
                    cwd=str(script_dir)  # Run from script directory
                )
                
                if result.returncode == 0:
                    paths['markdown'] = output_dir_abs / "ANALYSIS_REPORT.md"
                    paths['csv'] = output_dir_abs / "evolution_history.csv"
                    paths['json'] = output_dir_abs / "experiment_summary.json"
                    paths['plots_dir'] = output_dir_abs / "plots"
                    paths['success'] = True
                    self.dashboard.console.print("[bold green]✓ Analysis complete![/bold green]")
                else:
                    self.dashboard.console.print(f"[yellow]Analysis warning: {result.stderr[:200]}[/yellow]")
                    # Try to use whatever was generated
                    if (output_dir_abs / "ANALYSIS_REPORT.md").exists():
                        paths['markdown'] = output_dir_abs / "ANALYSIS_REPORT.md"
                        paths['csv'] = output_dir_abs / "evolution_history.csv"
                        paths['json'] = output_dir_abs / "experiment_summary.json"
                        paths['plots_dir'] = output_dir_abs / "plots"
                        paths['success'] = True
            except subprocess.TimeoutExpired:
                self.dashboard.console.print("[yellow]Analysis timed out[/yellow]")
            except Exception as e:
                self.dashboard.console.print(f"[yellow]Analysis error: {str(e)[:80]}[/yellow]")
        else:
            self.dashboard.console.print(f"[yellow]Analysis script not found at: {analyze_script}[/yellow]")
        
        return paths
