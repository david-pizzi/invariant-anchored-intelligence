"""Multi-generation IAI orchestrator for bandit experiments.

Runs the full IAI loop:
1. RUN: Execute bandit experiments with current invariants
2. CHALLENGE: Detect strain signals and propose alternatives
3. REVIEW: LLM Authority decides whether to accept/reject
4. UPDATE: Apply changes if accepted
5. REPEAT: Next generation with updated invariants
"""

from pathlib import Path
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List

from authority import FoundryLocalAuthority
from challenger import Challenger
from bandits import BernoulliBandit, make_drift_pair
from policies import (
    EpsilonGreedy, ThompsonBernoulli, UCB1, 
    FixedPolicy, IAIPolicySelector
)
from evaluator import Evaluator


class IAIOrchestrator:
    """
    Orchestrates multi-generation IAI evolution for bandit experiments.
    """
    
    def __init__(
        self,
        output_dir: str = "runs/iai_evolution",
        model_alias: str = "qwen2.5-0.5b",
        strictness: str = "balanced"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model_alias = model_alias
        self.strictness = strictness
        
        print(f"\n{'#'*70}")
        print(f"# IAI ORCHESTRATOR")
        print(f"{'#'*70}")
        print(f"Output directory: {self.output_dir}")
        
        # Initialize LLM Authority
        self.authority = FoundryLocalAuthority(
            model_alias=model_alias,
            strictness=strictness
        )
        
        # Initialize Challenger (baseline_regret set after baseline run)
        self.challenger = Challenger(window_size=1000)
        
        # Track evolution
        self.generation_history = []
        self.current_invariants = {'metric': 'cumulative_reward'}
        self.baseline_results = None
        
        # Evolution history for Authority context (last N generations)
        self.evolution_history = []
        
        # Meta-metrics for tracking proposal effectiveness
        self.meta_metrics = {
            'proposals_made': 0,
            'proposals_accepted': 0,
            'proposals_rejected': 0,
            'proposals_modified': 0,
            'improvements_after_accept': 0,
            'regressions_after_accept': 0,
            'per_generation': []  # Detailed per-gen tracking
        }
        
    def run_evolution(
        self,
        max_generations: int = 5,
        n_steps: int = 10000,
        n_runs: int = 3,
        drift_step: int = 7000
    ):
        """
        Run full IAI evolution across multiple generations.
        
        Args:
            max_generations: Number of evolution cycles
            n_steps: Steps per bandit experiment
            n_runs: Random seeds per system for statistical validity
            drift_step: When to introduce distribution drift
        """
        print(f"\n{'#'*70}")
        print(f"# STARTING IAI EVOLUTION")
        print(f"# Generations: {max_generations}")
        print(f"# Steps per run: {n_steps}")
        print(f"# Runs per system: {n_runs}")
        print(f"{'#'*70}\n")
        
        # Run baseline systems once for comparison
        print("=" * 70)
        print("BASELINE: Running standard bandit algorithms")
        print("=" * 70)
        self.baseline_results = self._run_baseline(n_steps, n_runs, drift_step)
        
        # Update Challenger with baseline regret for absolute comparison
        baseline_regret = self.baseline_results['summary']['best_regret']
        self.challenger.baseline_regret = baseline_regret
        print(f"\n  Challenger updated: baseline_regret = {baseline_regret:.2f}")
        
        # Evolution loop
        for gen in range(max_generations):
            print(f"\n{'='*70}")
            print(f"GENERATION {gen}")
            print(f"{'='*70}")
            print(f"Current Invariants: {self.current_invariants}\n")
            
            # STEP 1: RUN with current invariants
            gen_results = self._run_generation(gen, n_steps, n_runs, drift_step)
            
            # STEP 2: CHALLENGE - Detect strain, propose alternatives
            proposal = self._run_challenge(gen_results)
            
            # Track meta-metrics: was a proposal made?
            gen_meta = {
                'generation': gen,
                'proposal_made': bool(proposal['proposed_metrics']),
                'strain_signals': proposal['strain_signals'],
                'current_regret': gen_results['summary']['avg_regret'],
                'decision': None,
                'next_gen_improved': None  # Set after next generation
            }
            
            if not proposal['proposed_metrics']:
                print(f"\n✓ No strain detected - system stable at generation {gen}")
                self._save_generation(gen, gen_results, proposal, None)
                gen_meta['decision'] = 'NO_PROPOSAL'
                self.meta_metrics['per_generation'].append(gen_meta)
                continue
            
            self.meta_metrics['proposals_made'] += 1
            
            # STEP 3: AUTHORITY REVIEW - LLM decides (with historical context)
            decision = self.authority.review_proposal(
                challenger_output=proposal,
                current_metrics=gen_results['summary'],
                baseline_metrics=self.baseline_results['summary'],
                current_invariants=self.current_invariants,
                generation=gen,
                evolution_history=self.evolution_history
            )
            
            self._print_decision(decision)
            
            # STEP 4: UPDATE invariants if accepted
            updated = False
            if decision['verdict'] == 'ACCEPT':
                self.current_invariants = self._apply_proposal(
                    proposal['proposed_metrics'][0]
                )
                print(f"\n✅ Invariants UPDATED: {self.current_invariants}")
                updated = True
                self.meta_metrics['proposals_accepted'] += 1
                gen_meta['decision'] = 'ACCEPT'
            elif decision['verdict'] == 'MODIFY':
                if decision['modified_proposal']:
                    self.current_invariants = self._apply_proposal(
                        decision['modified_proposal']
                    )
                    print(f"\n✅ Invariants MODIFIED: {self.current_invariants}")
                    updated = True
                    self.meta_metrics['proposals_modified'] += 1
                    gen_meta['decision'] = 'MODIFY'
            else:
                print(f"\n❌ Proposal REJECTED - continuing with current invariants")
                self.meta_metrics['proposals_rejected'] += 1
                gen_meta['decision'] = 'REJECT'
            
            self.meta_metrics['per_generation'].append(gen_meta)
            
            # Update evolution history for next generation (keep last 10)
            self.evolution_history.append({
                'generation': gen,
                'metrics': gen_results['summary'],
                'invariants': self.current_invariants.copy(),
                'decision': decision['verdict'],
                'rationale': decision.get('rationale', '')[:150]  # Truncated for prompt size
            })
            if len(self.evolution_history) > 10:
                self.evolution_history.pop(0)
            
            # Track improvement after accepted proposals (compare to previous gen)
            if updated and len(self.meta_metrics['per_generation']) >= 2:
                prev_gen_meta = self.meta_metrics['per_generation'][-2]
                if prev_gen_meta.get('current_regret') is not None:
                    prev_regret = prev_gen_meta['current_regret']
                    curr_regret = gen_meta['current_regret']
                    if curr_regret < prev_regret:
                        prev_gen_meta['next_gen_improved'] = True
                        self.meta_metrics['improvements_after_accept'] += 1
                    else:
                        prev_gen_meta['next_gen_improved'] = False
                        self.meta_metrics['regressions_after_accept'] += 1
            
            # Save generation snapshot
            self._save_generation(gen, gen_results, proposal, decision)
            
            # Track in history
            self.generation_history.append({
                'generation': gen,
                'invariants': self.current_invariants.copy(),
                'proposal': proposal,
                'decision': decision,
                'updated': updated
            })
        
        # Generate final report
        report = self._generate_report()
        print(f"\n{'#'*70}")
        print(f"# EVOLUTION COMPLETE")
        print(f"{'#'*70}")
        print(report)
        
        return report
    
    def _run_baseline(self, n_steps: int, n_runs: int, drift_step: int) -> Dict[str, Any]:
        """Run baseline bandit algorithms once."""
        print("Running baseline systems: thompson, ucb1, epsilon_greedy")
        
        systems = {
            'thompson': lambda rng: ThompsonBernoulli(),
            'ucb1': lambda rng: UCB1(),
            'epsilon_greedy': lambda rng: EpsilonGreedy(epsilon=0.1)
        }
        
        all_trajectories = {}
        results_summary = []
        
        for system_name, make_policy in systems.items():
            print(f"\n  Running {system_name}...")
            for seed in range(n_runs):
                # Create environment
                rng_env = np.random.default_rng(seed)
                pre, post, _, _ = make_drift_pair(k=5, rng=rng_env)
                env = BernoulliBandit(means_pre=pre, means_post=post, drift_step=drift_step, rng=rng_env)
                
                # Create policy and evaluator
                rng_pol = np.random.default_rng(seed * 1000)
                policy = make_policy(rng_pol)
                policy.reset(env.k, rng_pol)
                
                evaluator = Evaluator(true_means_fn=env.true_means, k=env.k, max_steps=n_steps)
                
                # Run
                df = evaluator.run(policy=policy, env=env, steps=n_steps, system_name=system_name)
                all_trajectories[f'{system_name}_seed{seed}'] = df
                
                final_regret = df['cum_regret'].iloc[-1]
                results_summary.append({
                    'system': system_name,
                    'seed': seed,
                    'final_regret': final_regret,
                    'final_reward': df['cum_reward'].iloc[-1]
                })
        
        # Compute summary stats
        summary_df = pd.DataFrame(results_summary)
        best_system = summary_df.groupby('system')['final_regret'].mean().idxmin()
        best_regret = summary_df.groupby('system')['final_regret'].mean().min()
        best_reward = summary_df.groupby('system')['final_reward'].mean().max()
        
        # Also compute best system's average reward for comparison
        best_system_reward = summary_df[summary_df['system'] == best_system]['final_reward'].mean()
        
        print(f"\n  Best baseline: {best_system} (avg regret: {best_regret:.2f}, avg reward: {best_system_reward:.2f})")
        
        return {
            'trajectories': all_trajectories,
            'summary': {
                'best_system': best_system,
                'best_regret': float(best_regret),
                'best_reward': float(best_system_reward),
                'avg_regret': float(best_regret),  # For comparison - use best baseline
                'avg_reward': float(best_system_reward),  # For comparison - use best baseline
                'all_systems': summary_df.to_dict('records')
            }
        }
    
    def _run_generation(self, gen: int, n_steps: int, n_runs: int, drift_step: int) -> Dict[str, Any]:
        """Run IAI system for current generation."""
        print(f"\nRunning IAI system (generation {gen})...")
        
        all_trajectories = {}
        results_summary = []
        
        for seed in range(n_runs):
            print(f"  Run {seed+1}/{n_runs}...")
            
            # Create environment
            rng_env = np.random.default_rng(seed)
            pre, post, _, _ = make_drift_pair(k=5, rng=rng_env)
            env = BernoulliBandit(means_pre=pre, means_post=post, drift_step=drift_step, rng=rng_env)
            
            # Create IAI selector
            rng_pol = np.random.default_rng(seed * 1000)
            policy = IAIPolicySelector(
                base_policies=[EpsilonGreedy(epsilon=0.1), UCB1(), ThompsonBernoulli()],
                gamma=0.05
            )
            policy.reset(env.k, rng_pol)
            
            evaluator = Evaluator(true_means_fn=env.true_means, k=env.k, max_steps=n_steps)
            
            # Run
            df = evaluator.run(policy=policy, env=env, steps=n_steps, system_name='iai')
            all_trajectories[f'iai_seed{seed}'] = df
            
            results_summary.append({
                'system': 'iai',
                'seed': seed,
                'final_regret': df['cum_regret'].iloc[-1],
                'final_reward': df['cum_reward'].iloc[-1],
                'avg_switch_rate': df['switched'].mean()
            })
        
        # Compute summary
        summary_df = pd.DataFrame(results_summary)
        avg_regret = summary_df['final_regret'].mean()
        avg_reward = summary_df['final_reward'].mean()
        
        print(f"  IAI avg regret: {avg_regret:.2f}")
        
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
    
    def _run_challenge(self, gen_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run Challenger analysis on IAI system."""
        print(f"\n{'─'*60}")
        print("CHALLENGER: Analyzing IAI performance for strain signals")
        print(f"{'─'*60}")
        
        # Analyze first seed's trajectory
        iai_trajectory = gen_results['trajectories']['iai_seed0']
        proposal = self.challenger.analyse(iai_trajectory, 'iai')
        
        if proposal['proposed_metrics']:
            print(f"⚠ Strain detected - {len(proposal['critiques'])} critique(s)")
            for critique in proposal['critiques']:
                print(f"  - {critique['signal']}: {critique['description']}")
        else:
            print(f"✓ No significant strain detected")
        
        return proposal
    
    def _apply_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Convert proposal to new invariant specification."""
        # For now, just track the change - actual implementation would
        # modify how the bandit is evaluated
        return {
            'metric': proposal.get('name', 'cumulative_reward'),
            'description': proposal.get('description', ''),
            'formula': proposal.get('formula', '')
        }
    
    def _print_decision(self, decision: Dict[str, Any]):
        """Pretty print Authority decision."""
        print(f"\n{'─'*60}")
        print(f"AUTHORITY DECISION: {decision['verdict']}")
        print(f"{'─'*60}")
        print(f"Confidence: {decision['confidence']:.2f}")
        print(f"\nRationale:")
        print(f"  {decision['rationale']}")
        if decision['concerns']:
            print(f"\nConcerns:")
            for concern in decision['concerns']:
                print(f"  - {concern}")
        print(f"{'─'*60}")
    
    def _save_generation(self, gen: int, results: Dict, proposal: Dict, decision: Dict | None):
        """Save complete generation data."""
        gen_dir = self.output_dir / f"generation_{gen:03d}"
        gen_dir.mkdir(exist_ok=True)
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(v) for v in obj]
            elif isinstance(obj, (bool, np.bool_)):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        # Save proposal
        with open(gen_dir / "proposal.json", 'w') as f:
            json.dump(convert_types(proposal), f, indent=2)
        
        # Save decision if available
        if decision:
            with open(gen_dir / "decision.json", 'w') as f:
                json.dump(convert_types(decision), f, indent=2)
        
        # Save invariants snapshot
        with open(gen_dir / "invariants.json", 'w') as f:
            json.dump(self.current_invariants, f, indent=2)
        
        # Save summary
        with open(gen_dir / "summary.json", 'w') as f:
            json.dump(convert_types(results['summary']), f, indent=2)
        
        # Save trajectories
        traj_dir = gen_dir / "trajectories"
        traj_dir.mkdir(exist_ok=True)
        for name, df in results['trajectories'].items():
            df.to_csv(traj_dir / f"{name}.csv", index=False)
        
        # Append to master experiment log
        self._append_to_experiment_log(gen, results, proposal, decision)
        
        print(f"\n💾 Generation {gen} data saved to {gen_dir}")
    
    def _append_to_experiment_log(self, gen: int, results: Dict, proposal: Dict, decision: Dict | None):
        """Append generation summary to master experiment log CSV."""
        log_path = Path("experiment_log.csv")
        
        # Prepare log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'run_id': self.output_dir.name,
            'generation': gen,
            'system': 'iai',
            'avg_regret': results['summary']['avg_regret'],
            'avg_reward': results['summary']['avg_reward'],
            'strain_detected': len(proposal.get('proposed_metrics', [])) > 0,
            'proposal_name': proposal['proposed_metrics'][0]['name'] if proposal.get('proposed_metrics') else None,
            'decision': decision['verdict'] if decision else 'NO_REVIEW',
            'decision_confidence': decision['confidence'] if decision else None,
            'invariants': json.dumps(self.current_invariants)
        }
        
        # Create or append to CSV
        df_new = pd.DataFrame([log_entry])
        if log_path.exists():
            df_existing = pd.read_csv(log_path)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(log_path, index=False)
        else:
            df_new.to_csv(log_path, index=False)
    
    def _generate_report(self) -> str:
        """Generate evolution summary report."""
        report = []
        report.append("\n" + "="*70)
        report.append("EVOLUTION SUMMARY")
        report.append("="*70)
        
        report.append(f"\nTotal generations: {len(self.generation_history)}")
        report.append(f"Final invariants: {self.current_invariants}")
        
        # Count decisions
        accepted = sum(1 for h in self.generation_history if h.get('decision') and h['decision']['verdict'] == 'ACCEPT')
        rejected = sum(1 for h in self.generation_history if h.get('decision') and h['decision']['verdict'] == 'REJECT')
        modified = sum(1 for h in self.generation_history if h.get('decision') and h['decision']['verdict'] == 'MODIFY')
        no_proposal = len(self.generation_history) - (accepted + rejected + modified)
        
        report.append(f"\nDecision breakdown:")
        report.append(f"  Accepted: {accepted}")
        report.append(f"  Rejected: {rejected}")
        report.append(f"  Modified: {modified}")
        report.append(f"  No proposal: {no_proposal}")
        
        # Evolution path
        report.append(f"\nInvariant evolution:")
        for i, h in enumerate(self.generation_history):
            status = "→" if h['updated'] else "·"
            report.append(f"  Gen {i}: {status} {h['invariants']}")
        
        # DETAILED PERFORMANCE HISTORY
        report.append(f"\n" + "="*70)
        report.append("DETAILED PERFORMANCE HISTORY")
        report.append("="*70)
        report.append(f"\n{'Gen':<5} {'Reward':<10} {'Rwd vsPrev':^12} {'Rwd vsBase':^12} {'Regret':<10} {'Reg vsPrev':^12} {'Reg vsBase':^12} {'Strain':<8} {'Decision':<12} {'Status':<15}")
        report.append("-"*120)
        
        # Load baseline for comparison - handle different key structures
        baseline_summary = self.baseline_results.get('summary', self.baseline_results)
        baseline_regret = baseline_summary.get('avg_regret', baseline_summary.get('final_regret', 0))
        baseline_reward = baseline_summary.get('avg_reward', baseline_summary.get('final_reward', 0))
        
        for i, h in enumerate(self.generation_history):
            # Load generation summary to get metrics
            gen_summary_path = self.output_dir / f"generation_{i:03d}" / "summary.json"
            if gen_summary_path.exists():
                with open(gen_summary_path) as f:
                    gen_summary = json.load(f)
                
                regret = gen_summary.get('avg_regret', 0)
                reward = gen_summary.get('avg_reward', 0)
                
                # Calculate REWARD vs previous
                if i > 0:
                    prev_gen_path = self.output_dir / f"generation_{i-1:03d}" / "summary.json"
                    with open(prev_gen_path) as f:
                        prev_summary = json.load(f)
                    prev_reward = prev_summary.get('avg_reward', 0)
                    rwd_prev_diff = ((reward - prev_reward) / prev_reward * 100) if prev_reward > 0 else 0
                    rwd_vs_prev = f"{rwd_prev_diff:+.1f}%"
                    
                    prev_regret = prev_summary.get('avg_regret', 0)
                    reg_prev_diff = ((regret - prev_regret) / prev_regret * 100) if prev_regret > 0 else 0
                    reg_vs_prev = f"{reg_prev_diff:+.1f}%"
                else:
                    rwd_vs_prev = "—"
                    reg_vs_prev = "—"
                
                # Calculate vs baseline
                rwd_base_diff = ((reward - baseline_reward) / baseline_reward * 100) if baseline_reward > 0 else 0
                rwd_vs_base = f"{rwd_base_diff:+.1f}%"
                
                reg_base_diff = ((regret - baseline_regret) / baseline_regret * 100) if baseline_regret > 0 else 0
                reg_vs_base = f"{reg_base_diff:+.1f}%"
                
                # Get strain and decision info
                strain = "Yes" if h.get('proposal') and h['proposal'].get('proposed_metrics') else "No"
                decision = h.get('decision', {}).get('verdict', 'NO_REVIEW') if h.get('decision') else 'NO_REVIEW'
                status = "Updated" if h['updated'] else "Stable"
                
                report.append(f"{i:<5} {reward:<10.2f} {rwd_vs_prev:^12} {rwd_vs_base:^12} {regret:<10.2f} {reg_vs_prev:^12} {reg_vs_base:^12} {strain:<8} {decision:<12} {status:<15}")
        
        # META-IMPROVEMENT METRICS
        report.append(f"\n" + "="*70)
        report.append("META-IMPROVEMENT METRICS")
        report.append("="*70)
        mm = self.meta_metrics
        report.append(f"\nProposal Statistics:")
        report.append(f"  Total proposals made: {mm['proposals_made']}")
        report.append(f"  Accepted: {mm['proposals_accepted']}")
        report.append(f"  Modified: {mm['proposals_modified']}")
        report.append(f"  Rejected: {mm['proposals_rejected']}")
        
        if mm['proposals_accepted'] + mm['proposals_modified'] > 0:
            total_accepted = mm['proposals_accepted'] + mm['proposals_modified']
            report.append(f"\nProposal Effectiveness:")
            report.append(f"  Improvements after accept/modify: {mm['improvements_after_accept']}")
            report.append(f"  Regressions after accept/modify: {mm['regressions_after_accept']}")
            if total_accepted > 0:
                effectiveness = mm['improvements_after_accept'] / total_accepted * 100
                report.append(f"  Proposal effectiveness rate: {effectiveness:.1f}%")
        
        # Strain detection accuracy (did strain signals predict high regret?)
        strain_detected_count = sum(1 for g in mm['per_generation'] if g.get('proposal_made'))
        high_regret_count = sum(
            1 for g in mm['per_generation'] 
            if g.get('current_regret') and self.baseline_results and 
               g['current_regret'] > 1.3 * self.baseline_results['summary']['best_regret']
        )
        
        report.append(f"\nStrain Detection Analysis:")
        report.append(f"  Generations with strain detected: {strain_detected_count}")
        report.append(f"  Generations with high regret (>1.3x baseline): {high_regret_count}")
        report.append(f"  Baseline regret: {self.baseline_results['summary']['best_regret']:.2f}")
        
        # Per-generation detail
        if mm['per_generation']:
            report.append(f"\nPer-Generation Strain Signals:")
            for g in mm['per_generation']:
                signals = g.get('strain_signals', {})
                abs_high = signals.get('absolute_regret_high', False)
                ratio = signals.get('regret_vs_baseline_ratio', 'N/A')
                if ratio != 'N/A' and ratio is not None:
                    ratio_str = f"{ratio:.2f}x"
                else:
                    ratio_str = "N/A"
                report.append(f"  Gen {g['generation']}: regret={g['current_regret']:.1f}, "
                            f"vs_baseline={ratio_str}, absolute_strain={abs_high}")
        
        # Save authority decision history
        self.authority.save_decision_history(str(self.output_dir))
        
        report_text = "\n".join(report)
        
        # Save report with UTF-8 encoding for Unicode characters
        with open(self.output_dir / "EVOLUTION_REPORT.txt", 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        # Generate ANALYSIS_REPORT.md with plots immediately
        self._generate_analysis_report()
        
        return report_text
    
    def _generate_analysis_report(self):
        """Run analyze_evolution.py to generate ANALYSIS_REPORT.md with plots."""
        import subprocess
        import sys
        
        script_path = Path(__file__).parent / "analyze_evolution.py"
        
        try:
            print("\nGenerating analysis reports and plots...")
            result = subprocess.run(
                [sys.executable, str(script_path), "--run-dir", str(self.output_dir)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"✓ Analysis report generated: {self.output_dir / 'ANALYSIS_REPORT.md'}")
            else:
                print(f"Analysis warning: {result.stderr[:200]}")
                
        except Exception as e:
            print(f"⚠ Failed to generate analysis report: {e}")
