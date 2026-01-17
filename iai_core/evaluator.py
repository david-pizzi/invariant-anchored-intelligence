"""Evaluator component for IAI.

The Evaluator:
- Computes external performance metrics
- Enforces invariant constraints
- Detects invariant violations
- Remains external to the learning system

This module provides:
- BaseEvaluator: Abstract interface for domain-specific Evaluators
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class InvariantViolation:
    """Record of an invariant violation."""
    timestamp: datetime
    violation_type: str
    description: str
    severity: str  # "warning" | "error" | "critical"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of evaluating a system's performance."""
    metrics: Dict[str, float]
    summary: Dict[str, Any]
    violations: List[InvariantViolation] = field(default_factory=list)
    raw_data: Optional[Any] = None  # Domain-specific trajectory data
    
    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0
    
    @property
    def critical_violations(self) -> List[InvariantViolation]:
        return [v for v in self.violations if v.severity == "critical"]


class BaseEvaluator(ABC):
    """
    Abstract base class for IAI Evaluator.
    
    The Evaluator is the external authority that computes performance metrics
    and enforces invariant constraints. It must remain outside the learning
    system's control to maintain the invariant anchoring property.
    
    Key responsibilities:
    - Compute domain-specific metrics from performance data
    - Detect and log invariant violations
    - Provide ground truth for success/failure
    - Remain immutable to the learning system
    
    Domain-specific implementations must override:
    - evaluate(): Run evaluation and compute metrics
    - _compute_metrics(): Calculate domain-specific metrics
    - _check_violations(): Check for invariant violations
    """
    
    def __init__(self, constraints: Optional[Dict[str, Any]] = None):
        """
        Initialize Evaluator.
        
        Args:
            constraints: Invariant constraints to enforce
        """
        self.constraints = constraints or {}
        self.violations: List[InvariantViolation] = []
    
    @abstractmethod
    def evaluate(
        self,
        system: Any,
        environment: Any,
        **kwargs,
    ) -> EvaluationResult:
        """
        Evaluate a system's performance.
        
        Args:
            system: The system/policy being evaluated
            environment: The environment/context for evaluation
            **kwargs: Domain-specific evaluation parameters
            
        Returns:
            EvaluationResult with metrics, summary, and violations
        """
        pass
    
    @abstractmethod
    def _compute_metrics(self, raw_data: Any) -> Dict[str, float]:
        """
        Compute domain-specific metrics from raw data.
        
        Returns:
            Dictionary of metric names to values
        """
        pass
    
    @abstractmethod
    def _check_violations(
        self,
        raw_data: Any,
        metrics: Dict[str, float],
    ) -> List[InvariantViolation]:
        """
        Check for invariant violations.
        
        Returns:
            List of detected violations
        """
        pass
    
    def summarise(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Create a summary from computed metrics.
        
        Override for domain-specific summarization.
        """
        return {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
        }
    
    def log_violation(
        self,
        violation_type: str,
        description: str,
        severity: str = "error",
        context: Optional[Dict[str, Any]] = None,
    ):
        """Log an invariant violation."""
        violation = InvariantViolation(
            timestamp=datetime.now(),
            violation_type=violation_type,
            description=description,
            severity=severity,
            context=context or {},
        )
        self.violations.append(violation)
        return violation
    
    def get_violations(self) -> List[InvariantViolation]:
        """Return all recorded violations."""
        return self.violations
    
    def clear_violations(self):
        """Clear violation history."""
        self.violations = []
    
    def update_constraints(self, constraints: Dict[str, Any]):
        """Update invariant constraints."""
        self.constraints.update(constraints)
