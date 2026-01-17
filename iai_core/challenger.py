"""Challenger component for IAI.

The Challenger:
- Detects invariant strain signals
- Generates evidence-based critiques
- Proposes alternative formulations
- Remains advisory-only (cannot enact changes)

This module provides:
- BaseChallenger: Abstract interface for domain-specific Challengers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from .types import (
    Proposal,
    StrainSignals,
    StrainSignal,
    Critique,
    ProposedMetric,
    Severity,
)


class BaseChallenger(ABC):
    """
    Abstract base class for IAI Challenger.
    
    The Challenger detects strain signals in the current invariant configuration
    and proposes evidence-based alternatives. It remains purely advisory -
    only the Authority can ratify changes.
    
    Domain-specific implementations must override:
    - _detect_strain_signals(): Domain-specific strain detection
    - _propose_alternatives(): Domain-specific alternative metrics
    """
    
    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        baseline_performance: Optional[float] = None,
    ):
        """
        Initialize Challenger.
        
        Args:
            thresholds: Configurable thresholds for strain detection
            baseline_performance: Baseline performance for comparison
        """
        self.baseline_performance = baseline_performance
        
        # Default thresholds - override in domain implementations
        self.default_thresholds = {
            "performance_degradation_ratio": 1.2,
            "variance_spike_ratio": 1.5,
            "stability_threshold": 0.15,
        }
        self.thresholds = {**self.default_thresholds, **(thresholds or {})}
    
    def analyse(
        self,
        performance_data: Any,
        system_name: str,
    ) -> Proposal:
        """
        Analyse performance data for invariant strain.
        
        Args:
            performance_data: Domain-specific performance data
            system_name: Name of the system being analysed
            
        Returns:
            Proposal with strain signals, critiques, and proposed alternatives
        """
        # Detect strain signals (domain-specific)
        strain_signals = self._detect_strain_signals(performance_data)
        
        # Generate critiques for detected strain
        critiques = self._generate_critiques(strain_signals)
        
        # Propose alternatives if strain detected
        proposed_metrics: List[ProposedMetric] = []
        if strain_signals.any_detected:
            proposed_metrics = self._propose_alternatives(strain_signals, critiques)
        
        # Propose parameter changes
        parameter_changes = self._propose_parameter_changes(
            performance_data, strain_signals
        )
        
        # Collect evidence
        evidence = self._collect_evidence(performance_data, strain_signals)
        
        return Proposal(
            strain_signals=strain_signals,
            critiques=critiques,
            proposed_metrics=proposed_metrics,
            proposed_parameter_changes=parameter_changes,
            evidence=evidence,
        )
    
    @abstractmethod
    def _detect_strain_signals(self, performance_data: Any) -> StrainSignals:
        """
        Detect strain signals from performance data.
        
        Domain-specific implementations should detect signals like:
        - Performance degradation over time
        - Variance spikes
        - Instability indicators
        - Comparison to baseline
        
        Returns:
            StrainSignals with all detected signals
        """
        pass
    
    def _generate_critiques(self, strain_signals: StrainSignals) -> List[Critique]:
        """
        Generate critiques from detected strain signals.
        
        Can be overridden for domain-specific critique generation.
        """
        critiques = []
        
        for name, signal in strain_signals.signals.items():
            if signal.detected:
                severity = self._determine_severity(signal)
                critiques.append(Critique(
                    severity=severity,
                    signal=name,
                    description=signal.description or f"Strain detected: {name}",
                    evidence={
                        "value": signal.value,
                        "threshold": signal.threshold,
                        "ratio": signal.value / signal.threshold if signal.threshold else None,
                    },
                ))
        
        return critiques
    
    def _determine_severity(self, signal: StrainSignal) -> Severity:
        """Determine severity based on how much signal exceeds threshold."""
        if signal.threshold == 0:
            return Severity.MEDIUM
        
        ratio = signal.value / signal.threshold
        if ratio >= 2.0:
            return Severity.CRITICAL
        elif ratio >= 1.5:
            return Severity.HIGH
        elif ratio >= 1.2:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    @abstractmethod
    def _propose_alternatives(
        self,
        strain_signals: StrainSignals,
        critiques: List[Critique],
    ) -> List[ProposedMetric]:
        """
        Propose alternative metrics based on detected strain.
        
        Domain-specific implementations should propose meaningful
        alternative invariants that address the detected strain.
        
        Returns:
            List of proposed alternative metrics
        """
        pass
    
    def _propose_parameter_changes(
        self,
        performance_data: Any,
        strain_signals: StrainSignals,
    ) -> Dict[str, Any]:
        """
        Propose parameter changes based on performance.
        
        Override in domain implementations for specific parameter tuning.
        """
        return {}
    
    def _collect_evidence(
        self,
        performance_data: Any,
        strain_signals: StrainSignals,
    ) -> Dict[str, Any]:
        """
        Collect evidence package for Authority review.
        
        Override to add domain-specific evidence.
        """
        return {
            "strain_signal_count": strain_signals.count_detected,
            "any_strain_detected": strain_signals.any_detected,
        }
    
    def update_baseline(self, baseline_performance: float):
        """Update baseline performance for comparison."""
        self.baseline_performance = baseline_performance
    
    def update_thresholds(self, thresholds: Dict[str, float]):
        """Update strain detection thresholds."""
        self.thresholds.update(thresholds)
