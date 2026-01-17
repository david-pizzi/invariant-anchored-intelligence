"""Betting orchestrator for IAI.

Coordinates the IAI evolution loop for betting optimization.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List, Optional

from iai_core.orchestrator import BaseOrchestrator
from iai_core.authority import FoundryLocalAuthority
from iai_core.types import Invariants, GenerationResult, Proposal, AuthorityDecision, Verdict

from .simulator import BettingSimulator, SimulationConfig
from .strategies import IAIStrategy
from .challenger import BettingChallenger
from .evaluator import BettingEvaluator


class BettingOrchestrator(BaseOrchestrator):
    """
    Orchestrator for betting IAI evolution.
    
    Manages the evolution loop:
    1. Run IAI strategy on matches
    2. Detect strain signals
    3. Authority reviews proposals
    4. Update strategy parameters
    """
    
    def __init__(
        self,
        simulator: Optional[BettingSimulator] = None,
        model_alias: str = "phi-3.5-mini",
        strictness: str = "balanced",
        output_dir: str = "runs/betting_evolution",
    ):
        """
        Initialize betting orchestrator.
        
        Args:
            simulator: Betting simulator (will create if None)
            model_alias: LLM model for Authority
            strictness: Authority strictness level
            output_dir: Output directory for runs
        """
        # Create simulator if needed
        self.simulator = simulator or BettingSimulator()
        
        # Create IAI strategy
        self.iai_strategy = IAIStrategy()
        
        # Create domain-specific challenger
        challenger = BettingChallenger()
        
        # Create evaluator
        evaluator = BettingEvaluator(
            initial_bankroll=self.simulator.config.initial_bankroll
        )
        
        # Create authority with domain context
        domain_context = """
You are reviewing betting strategy optimizations.

Key considerations:
- Bankroll preservation is critical - avoid ruin
- ROI matters more than win rate
- Drawdown indicates risk level
- Kelly criterion is a baseline - IAI should improve on it

When reviewing proposals:
- Accept parameter changes that reduce drawdown without sacrificing too much ROI
- Reject changes that increase ruin probability
- Be cautious about increasing stake sizes
- Consider Sharpe ratio (risk-adjusted returns) over raw profit
"""
        
        authority = FoundryLocalAuthority(
            model_alias=model_alias,
            strictness=strictness,
            domain_context=domain_context,
        )
        
        super().__init__(
            authority=authority,
            challenger=challenger,
            evaluator=evaluator,
            output_dir=output_dir,
        )
    
    def _get_default_invariants(self) -> Invariants:
        """Return default betting invariants."""
        return Invariants(
            primary_metric="roi",
            thresholds={
                "min_roi": 0.0,  # At least break even
                "max_drawdown": 0.3,  # Max 30% drawdown
                "min_sharpe": 0.5,  # Reasonable risk-adjusted returns
            },
            constraints={
                "max_stake_fraction": 0.25,
                "min_bankroll_fraction": 0.1,
            },
        )
    
    def _run_generation(
        self,
        generation: int,
        invariants: Invariants,
        **kwargs,
    ) -> GenerationResult:
        """Run betting strategy for one generation."""
        
        # Get matches (use training set for evolution)
        matches = kwargs.get("matches", self.simulator.train_matches)
        
        if not matches:
            raise ValueError("No matches available. Load data first.")
        
        print(f"Running generation {generation} on {len(matches)} matches...")
        
        # Run strategy
        result = self.simulator.run_strategy(
            self.iai_strategy,
            matches=matches,
        )
        
        # Get betting state for challenger
        betting_state = result.raw_data
        
        return GenerationResult(
            generation=generation,
            metrics=result.metrics,
            trajectories=betting_state,  # BettingState for challenger
            summary=result.summary,
            invariants_used=invariants,
        )
    
    def _run_baseline(self, **kwargs) -> Dict[str, Any]:
        """Run baseline strategies."""
        return self.simulator.run_baseline_comparison()
    
    def _apply_proposal(
        self,
        proposal: Proposal,
        decision: AuthorityDecision,
    ) -> Invariants:
        """Apply accepted proposal by updating IAI strategy parameters."""
        
        # Get parameter changes from proposal
        param_changes = proposal.proposed_parameter_changes
        
        if decision.verdict == Verdict.MODIFY and decision.modified_proposal:
            # Use modified parameters if Authority adjusted
            param_changes = decision.modified_proposal.get(
                "parameter_changes", param_changes
            )
        
        # Apply changes to IAI strategy
        if param_changes:
            new_params = {}
            current_params = self.iai_strategy.params
            
            for param, change in param_changes.items():
                if param in current_params:
                    action = change.get("action", "set")
                    
                    if action == "multiply":
                        new_params[param] = current_params[param] * change.get("factor", 1.0)
                    elif action == "add":
                        new_params[param] = current_params[param] + change.get("value", 0)
                    elif action == "set":
                        new_params[param] = change.get("value", current_params[param])
            
            if new_params:
                self.iai_strategy.update_params(new_params)
        
        # Update invariants if metrics changed
        new_invariants = self.current_invariants
        
        if proposal.proposed_metrics:
            primary = proposal.proposed_metrics[0]
            if primary.name != self.current_invariants.primary_metric:
                new_invariants = Invariants(
                    primary_metric=primary.name,
                    thresholds=self.current_invariants.thresholds.copy(),
                    constraints=self.current_invariants.constraints.copy(),
                    metadata={"changed_at_generation": decision.timestamp},
                )
        
        return new_invariants
    
    def run_full_experiment(
        self,
        max_generations: int = 10,
        leagues: List[str] = None,
        seasons: List[str] = None,
    ):
        """
        Run complete IAI betting experiment.
        
        Args:
            max_generations: Number of evolution cycles
            leagues: Leagues to use (default: Premier League)
            seasons: Seasons to use (default: 2021-2024)
        """
        # Configure simulator
        if leagues or seasons:
            self.simulator.config.leagues = leagues or ["E0"]
            self.simulator.config.seasons = seasons or ["2122", "2223", "2324"]
        
        # Load data
        print("\n" + "="*70)
        print("LOADING DATA")
        print("="*70)
        self.simulator.load_data()
        
        # Print data summary
        summary = self.simulator.get_data_summary()
        print(f"\nData Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Run evolution
        history = self.run_evolution(
            max_generations=max_generations,
            matches=self.simulator.train_matches,
        )
        
        # Final evaluation on test set
        print("\n" + "="*70)
        print("FINAL EVALUATION (Test Set)")
        print("="*70)
        
        final_result = self.simulator.run_strategy(
            self.iai_strategy,
            matches=self.simulator.test_matches,
        )
        
        print(f"\nIAI Strategy Performance on Test Set:")
        print(f"  Profit: £{final_result.summary['total_profit']:.2f}")
        print(f"  ROI: {final_result.summary['roi_pct']:.2f}%")
        print(f"  Win rate: {final_result.summary['win_rate_pct']:.1f}%")
        print(f"  Max drawdown: {final_result.summary['max_drawdown_pct']:.1f}%")
        print(f"  Bets: {final_result.summary['n_bets']}")
        
        # Compare to baselines on test set
        print("\n" + "-"*40)
        print("Baseline Comparison (Test Set)")
        print("-"*40)
        baseline_test = self.simulator.run_baseline_comparison()
        
        return {
            "evolution_history": history,
            "final_iai_result": final_result,
            "baseline_comparison": baseline_test,
            "final_params": self.iai_strategy.params,
        }
