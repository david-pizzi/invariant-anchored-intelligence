"""Orchestrator component for IAI.

The Orchestrator coordinates the IAI evolution loop:
1. RUN: Execute system with current invariants
2. CHALLENGE: Detect strain and propose alternatives
3. REVIEW: Authority decides on proposals
4. UPDATE: Apply accepted changes
5. REPEAT: Next generation

This module provides:
- BaseOrchestrator: Abstract interface with the core evolution loop
"""

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import json

from .types import (
    Invariants,
    Proposal,
    AuthorityDecision,
    GenerationResult,
    EvolutionHistory,
    Verdict,
)
from .authority import BaseAuthority
from .challenger import BaseChallenger
from .evaluator import BaseEvaluator


class BaseOrchestrator(ABC):
    """
    Abstract base class for IAI Orchestrator.
    
    Coordinates the multi-generation evolution loop, managing the
    interaction between system execution, Challenger, and Authority.
    
    Domain-specific implementations must override:
    - _run_generation(): Execute domain-specific system
    - _run_baseline(): Run baseline comparators
    - _apply_proposal(): Apply accepted invariant changes
    """
    
    def __init__(
        self,
        authority: BaseAuthority,
        challenger: BaseChallenger,
        evaluator: BaseEvaluator,
        output_dir: str = "runs/evolution",
    ):
        """
        Initialize Orchestrator.
        
        Args:
            authority: Authority for reviewing proposals
            challenger: Challenger for detecting strain
            evaluator: Evaluator for computing metrics
            output_dir: Directory for saving run artifacts
        """
        self.authority = authority
        self.challenger = challenger
        self.evaluator = evaluator
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Evolution state
        self.current_invariants = self._get_default_invariants()
        self.evolution_history = EvolutionHistory()
        self.baseline_results: Optional[Dict[str, Any]] = None
        
        # Meta-metrics for tracking
        self.meta_metrics = {
            "proposals_made": 0,
            "proposals_accepted": 0,
            "proposals_rejected": 0,
            "proposals_modified": 0,
            "generations_completed": 0,
        }
        
        print(f"\n{'#'*70}")
        print(f"# IAI ORCHESTRATOR INITIALIZED")
        print(f"{'#'*70}")
        print(f"Output directory: {self.output_dir}")
    
    @abstractmethod
    def _get_default_invariants(self) -> Invariants:
        """Return default invariant configuration for domain."""
        pass
    
    @abstractmethod
    def _run_generation(
        self,
        generation: int,
        invariants: Invariants,
        **kwargs,
    ) -> GenerationResult:
        """
        Run a single generation with given invariants.
        
        Args:
            generation: Generation number
            invariants: Current invariant configuration
            **kwargs: Domain-specific parameters
            
        Returns:
            GenerationResult with metrics and trajectories
        """
        pass
    
    @abstractmethod
    def _run_baseline(self, **kwargs) -> Dict[str, Any]:
        """
        Run baseline systems for comparison.
        
        Returns:
            Dictionary with baseline results and summary
        """
        pass
    
    @abstractmethod
    def _apply_proposal(
        self,
        proposal: Proposal,
        decision: AuthorityDecision,
    ) -> Invariants:
        """
        Apply an accepted proposal to update invariants.
        
        Args:
            proposal: The accepted proposal
            decision: Authority decision (may contain modifications)
            
        Returns:
            Updated Invariants
        """
        pass
    
    def run_evolution(
        self,
        max_generations: int = 5,
        **kwargs,
    ) -> EvolutionHistory:
        """
        Run the full IAI evolution loop.
        
        Args:
            max_generations: Maximum number of evolution cycles
            **kwargs: Domain-specific parameters
            
        Returns:
            EvolutionHistory with all generations, proposals, and decisions
        """
        print(f"\n{'#'*70}")
        print(f"# STARTING IAI EVOLUTION")
        print(f"# Max generations: {max_generations}")
        print(f"{'#'*70}\n")
        
        # Create run directory
        run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        run_dir = self.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 0: Run baselines
        print("=" * 70)
        print("BASELINE: Running baseline systems")
        print("=" * 70)
        self.baseline_results = self._run_baseline(**kwargs)
        self._update_challenger_baseline()
        
        # Evolution loop
        for gen in range(max_generations):
            print(f"\n{'='*70}")
            print(f"GENERATION {gen}")
            print(f"{'='*70}")
            print(f"Current Invariants: {self.current_invariants.to_dict()}\n")
            
            # Step 1: RUN with current invariants
            gen_result = self._run_generation(
                generation=gen,
                invariants=self.current_invariants,
                **kwargs,
            )
            
            # Step 2: CHALLENGE - Detect strain
            proposal = self._run_challenge(gen_result)
            
            if not proposal.strain_signals.any_detected:
                print(f"\n✓ No strain detected - system stable at generation {gen}")
                self._save_generation(run_dir, gen, gen_result, proposal, None)
                self.evolution_history.add_generation(gen_result, proposal)
                continue
            
            self.meta_metrics["proposals_made"] += 1
            
            # Step 3: AUTHORITY REVIEW
            decision = self.authority.review_proposal(
                proposal=proposal,
                current_metrics=gen_result.metrics,
                baseline_metrics=self.baseline_results.get("summary", {}),
                current_invariants=self.current_invariants,
                generation=gen,
                evolution_history=self._get_evolution_context(),
            )
            
            self._print_decision(decision)
            
            # Step 4: UPDATE if accepted
            if decision.verdict == Verdict.ACCEPT:
                self.current_invariants = self._apply_proposal(proposal, decision)
                print(f"\n✅ Invariants UPDATED: {self.current_invariants.to_dict()}")
                self.meta_metrics["proposals_accepted"] += 1
                
            elif decision.verdict == Verdict.MODIFY:
                if decision.modified_proposal:
                    self.current_invariants = self._apply_proposal(proposal, decision)
                    print(f"\n✅ Invariants MODIFIED: {self.current_invariants.to_dict()}")
                    self.meta_metrics["proposals_modified"] += 1
                    
            else:
                print(f"\n❌ Proposal REJECTED - continuing with current invariants")
                self.meta_metrics["proposals_rejected"] += 1
            
            # Save and track
            self._save_generation(run_dir, gen, gen_result, proposal, decision)
            self.evolution_history.add_generation(gen_result, proposal, decision)
            self.meta_metrics["generations_completed"] += 1
        
        # Save final summary
        self._save_summary(run_dir)
        
        print(f"\n{'#'*70}")
        print(f"# EVOLUTION COMPLETE")
        print(f"# Generations: {self.meta_metrics['generations_completed']}")
        print(f"# Proposals: {self.meta_metrics['proposals_made']}")
        print(f"# Accepted: {self.meta_metrics['proposals_accepted']}")
        print(f"{'#'*70}\n")
        
        return self.evolution_history
    
    def _run_challenge(self, gen_result: GenerationResult) -> Proposal:
        """Run Challenger on generation results."""
        return self.challenger.analyse(
            performance_data=gen_result.trajectories,
            system_name=f"generation_{gen_result.generation}",
        )
    
    def _update_challenger_baseline(self):
        """Update Challenger with baseline performance."""
        if self.baseline_results and "summary" in self.baseline_results:
            summary = self.baseline_results["summary"]
            if "best_performance" in summary:
                self.challenger.update_baseline(summary["best_performance"])
    
    def _get_evolution_context(self) -> List[Dict[str, Any]]:
        """Get recent evolution history for Authority context."""
        context = []
        for i, gen in enumerate(self.evolution_history.generations[-10:]):
            context.append({
                "generation": gen.generation,
                "metrics": gen.metrics,
                "invariants": gen.invariants_used.to_dict(),
            })
        return context
    
    def _print_decision(self, decision: AuthorityDecision):
        """Print Authority decision."""
        print(f"\n{'─'*60}")
        print(f"AUTHORITY DECISION: {decision.verdict.value}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Rationale: {decision.rationale}")
        if decision.concerns:
            print(f"Concerns: {', '.join(decision.concerns)}")
        print(f"{'─'*60}")
    
    def _save_generation(
        self,
        run_dir: Path,
        generation: int,
        result: GenerationResult,
        proposal: Proposal,
        decision: Optional[AuthorityDecision],
    ):
        """Save generation artifacts."""
        gen_dir = run_dir / f"generation_{generation:03d}"
        gen_dir.mkdir(exist_ok=True)
        
        # Save result summary
        with open(gen_dir / "result.json", "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        
        # Save proposal
        with open(gen_dir / "proposal.json", "w") as f:
            json.dump(proposal.to_dict(), f, indent=2, default=str)
        
        # Save decision if present
        if decision:
            with open(gen_dir / "decision.json", "w") as f:
                json.dump(decision.to_dict(), f, indent=2, default=str)
        
        # Save invariants
        with open(gen_dir / "invariants.json", "w") as f:
            json.dump(self.current_invariants.to_dict(), f, indent=2)
    
    def _save_summary(self, run_dir: Path):
        """Save evolution summary."""
        summary = {
            "meta_metrics": self.meta_metrics,
            "final_invariants": self.current_invariants.to_dict(),
            "baseline_results": self.baseline_results,
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(run_dir / "evolution_summary.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)
