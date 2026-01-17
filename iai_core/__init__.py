"""IAI Core Library - Invariant-Anchored Intelligence Framework.

This library provides the domain-agnostic components of IAI:
- Authority: LLM-based decision maker for invariant changes
- Challenger: Strain detection and proposal generation
- Orchestrator: Evolution loop coordination
- Dashboard: Rich terminal display
- Evaluator: Abstract base for domain-specific evaluation
- Logging: Audit trail and experiment tracking

Domain-specific pilots import and extend these base classes.
"""

from .authority import BaseAuthority, FoundryLocalAuthority
from .challenger import BaseChallenger
from .orchestrator import BaseOrchestrator
from .evaluator import BaseEvaluator
from .dashboard import BaseDashboard, RichDashboard
from .logging import AuditLogger, ExperimentTracker
from .types import (
    Invariants,
    StrainSignals,
    Proposal,
    AuthorityDecision,
    GenerationResult,
)

__version__ = "0.1.0"
__all__ = [
    # Authority
    "BaseAuthority",
    "FoundryLocalAuthority",
    # Challenger
    "BaseChallenger",
    # Orchestrator
    "BaseOrchestrator",
    # Evaluator
    "BaseEvaluator",
    # Dashboard
    "BaseDashboard",
    "RichDashboard",
    # Logging
    "AuditLogger",
    "ExperimentTracker",
    # Types
    "Invariants",
    "StrainSignals",
    "Proposal",
    "AuthorityDecision",
    "GenerationResult",
]
