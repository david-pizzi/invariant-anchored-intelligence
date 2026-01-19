"""
Forex Authority - Guardian of trading invariants.
Inherits from base IAI Authority.
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from iai_core.authority import BaseAuthority
from iai_core.types import Proposal, AuthorityDecision, Verdict


class ForexAuthority(BaseAuthority):
    """
    Authority for forex trading.
    
    Enforces invariants:
    - Min Sharpe ratio > 1.5
    - Max drawdown < 15%
    - Min win rate > 45%
    """
    
    def __init__(
        self,
        min_sharpe: float = 1.5,
        max_drawdown: float = 0.15,
        min_win_rate: float = 0.45,
        strictness: str = "balanced",
    ):
        super().__init__(strictness=strictness)
        self.min_sharpe = min_sharpe
        self.max_drawdown = max_drawdown
        self.min_win_rate = min_win_rate
    
    def review_proposal(self, proposal: Proposal) -> AuthorityDecision:
        """
        Review a strategy proposal.
        
        Checks if proposed strategy meets invariants.
        """
        print(f"\n{'='*70}")
        print(f"AUTHORITY REVIEW")
        print(f"{'='*70}")
        
        # Extract description from critiques
        if proposal.critiques:
            description = proposal.critiques[0].description
            print(f"Proposal: {description}")
        else:
            print(f"Proposal: {len(proposal.strain_signals.signals)} strain signal(s)")
        
        # Extract metrics from proposal
        evidence = proposal.evidence or {}
        
        # Get proposed strategy metrics
        sharpe = evidence.get("alternative_sharpe", evidence.get("sharpe_ratio", 0))
        drawdown = evidence.get("max_drawdown", 1.0)
        win_rate = evidence.get("win_rate", 0)
        total_return = evidence.get("total_return", 0)
        
        print(f"\nProposed Strategy Metrics:")
        print(f"  Sharpe Ratio:    {sharpe:.2f} (min: {self.min_sharpe:.2f})")
        print(f"  Max Drawdown:    {drawdown*100:.1f}% (max: {self.max_drawdown*100:.1f}%)")
        print(f"  Win Rate:        {win_rate*100:.1f}% (min: {self.min_win_rate*100:.1f}%)")
        print(f"  Total Return:    {total_return*100:.1f}%")
        
        # Check invariants
        violations = []
        
        if sharpe < self.min_sharpe:
            violations.append(f"Sharpe {sharpe:.2f} below minimum {self.min_sharpe:.2f}")
        
        if drawdown > self.max_drawdown:
            violations.append(f"Drawdown {drawdown*100:.1f}% exceeds limit {self.max_drawdown*100:.1f}%")
        
        if win_rate < self.min_win_rate:
            violations.append(f"Win rate {win_rate*100:.1f}% below minimum {self.min_win_rate*100:.1f}%")
        
        # Decision
        if violations:
            verdict = Verdict.REJECT
            rationale = "Invariant violations:\n  - " + "\n  - ".join(violations)
            print(f"\n[X] VERDICT: REJECT")
            print(f"\nReasons:")
            for v in violations:
                print(f"  • {v}")
        else:
            verdict = Verdict.ACCEPT
            rationale = f"All invariants satisfied. Sharpe {sharpe:.2f}, Drawdown {drawdown*100:.1f}%, Win rate {win_rate*100:.1f}%"
            print(f"\n[+] VERDICT: ACCEPT")
            print(f"All invariants satisfied.")
        
        return AuthorityDecision(
            verdict=verdict,
            rationale=rationale,
            confidence=1.0,
            concerns=violations if violations else []
        )
    
    def check_current_performance(self, metrics: Dict[str, Any]) -> bool:
        """
        Check if current trading performance meets invariants.
        
        Returns:
            True if should continue trading, False if should pause
        """
        sharpe = metrics.get("sharpe_ratio", 0)
        drawdown = metrics.get("max_drawdown", 0)
        win_rate = metrics.get("win_rate", 0)
        
        print(f"\n{'='*70}")
        print(f"AUTHORITY PERFORMANCE CHECK")
        print(f"{'='*70}")
        print(f"Sharpe:   {sharpe:.2f} (min: {self.min_sharpe:.2f})")
        print(f"Drawdown: {drawdown*100:.1f}% (max: {self.max_drawdown*100:.1f}%)")
        print(f"Win Rate: {win_rate*100:.1f}% (min: {self.min_win_rate*100:.1f}%)")
        
        # Check for violations
        if sharpe < self.min_sharpe:
            print(f"\n⚠️  PAUSE TRADING: Sharpe {sharpe:.2f} below minimum {self.min_sharpe:.2f}")
            return False
        
        if drawdown > self.max_drawdown:
            print(f"\n⚠️  PAUSE TRADING: Drawdown {drawdown*100:.1f}% exceeds {self.max_drawdown*100:.1f}%")
            return False
        
        if win_rate < self.min_win_rate:
            print(f"\n⚠️  PAUSE TRADING: Win rate {win_rate*100:.1f}% below {self.min_win_rate*100:.1f}%")
            return False
        
        print(f"\n[+] CONTINUE TRADING: All invariants satisfied")
        return True
