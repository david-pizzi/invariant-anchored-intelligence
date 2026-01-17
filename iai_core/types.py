"""Type definitions for IAI Core.

These types define the contracts between IAI components,
allowing domain-specific implementations to remain compatible.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class Verdict(Enum):
    """Authority decision verdicts."""
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    MODIFY = "MODIFY"


class Severity(Enum):
    """Critique severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Invariants:
    """
    Current invariant configuration.
    
    Invariants are the externally-owned, authoritative success signals
    that the system cannot modify without Authority approval.
    """
    primary_metric: str
    thresholds: Dict[str, float] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_metric": self.primary_metric,
            "thresholds": self.thresholds,
            "constraints": self.constraints,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Invariants":
        return cls(
            primary_metric=data.get("primary_metric", ""),
            thresholds=data.get("thresholds", {}),
            constraints=data.get("constraints", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class StrainSignal:
    """A single detected strain signal."""
    name: str
    detected: bool
    value: float
    threshold: float
    description: str = ""
    
    
@dataclass
class StrainSignals:
    """Collection of strain signals detected by Challenger."""
    signals: Dict[str, StrainSignal] = field(default_factory=dict)
    
    @property
    def any_detected(self) -> bool:
        return any(s.detected for s in self.signals.values())
    
    @property
    def count_detected(self) -> int:
        return sum(1 for s in self.signals.values() if s.detected)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            name: {
                "detected": s.detected,
                "value": s.value,
                "threshold": s.threshold,
                "description": s.description,
            }
            for name, s in self.signals.items()
        }


@dataclass
class Critique:
    """A critique of the current invariant configuration."""
    severity: Severity
    signal: str
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProposedMetric:
    """A proposed alternative metric or invariant change."""
    name: str
    formula: str
    rationale: str
    expected_improvement: str = ""


@dataclass
class Proposal:
    """Challenger's complete proposal output."""
    strain_signals: StrainSignals
    critiques: List[Critique] = field(default_factory=list)
    proposed_metrics: List[ProposedMetric] = field(default_factory=list)
    proposed_parameter_changes: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strain_signals": self.strain_signals.to_dict(),
            "critiques": [
                {
                    "severity": c.severity.value,
                    "signal": c.signal,
                    "description": c.description,
                    "evidence": c.evidence,
                }
                for c in self.critiques
            ],
            "proposed_metrics": [
                {
                    "name": p.name,
                    "formula": p.formula,
                    "rationale": p.rationale,
                    "expected_improvement": p.expected_improvement,
                }
                for p in self.proposed_metrics
            ],
            "proposed_parameter_changes": self.proposed_parameter_changes,
            "evidence": self.evidence,
        }


@dataclass
class AuthorityDecision:
    """Authority's decision on a proposal."""
    verdict: Verdict
    rationale: str
    confidence: float
    concerns: List[str] = field(default_factory=list)
    modified_proposal: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    model_used: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "concerns": self.concerns,
            "modified_proposal": self.modified_proposal,
            "timestamp": self.timestamp.isoformat(),
            "model_used": self.model_used,
        }


@dataclass
class GenerationResult:
    """Results from a single generation's execution."""
    generation: int
    metrics: Dict[str, float]
    trajectories: Any  # Domain-specific trajectory data
    summary: Dict[str, Any]
    invariants_used: Invariants
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generation": self.generation,
            "metrics": self.metrics,
            "summary": self.summary,
            "invariants_used": self.invariants_used.to_dict(),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EvolutionHistory:
    """Tracks the full evolution across generations."""
    generations: List[GenerationResult] = field(default_factory=list)
    decisions: List[AuthorityDecision] = field(default_factory=list)
    proposals: List[Proposal] = field(default_factory=list)
    
    def add_generation(
        self,
        result: GenerationResult,
        proposal: Optional[Proposal] = None,
        decision: Optional[AuthorityDecision] = None,
    ):
        self.generations.append(result)
        if proposal:
            self.proposals.append(proposal)
        if decision:
            self.decisions.append(decision)
