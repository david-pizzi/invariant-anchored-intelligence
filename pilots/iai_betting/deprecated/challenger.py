"""Betting challenger for IAI.

Detects strain signals in betting performance and proposes
alternative strategies or parameter changes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List, Optional

from iai_core.challenger import BaseChallenger
from iai_core.types import (
    StrainSignals,
    StrainSignal,
    ProposedMetric,
    Critique,
    Severity,
)

from .strategies import BettingState, Bet


class BettingChallenger(BaseChallenger):
    """
    Challenger for betting domain.
    
    Detects:
    - Declining ROI over time
    - Excessive drawdowns
    - Bet sizing inefficiency
    - Market selection problems
    
    Proposes:
    - Alternative success metrics
    - Parameter adjustments
    """
    
    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        baseline_roi: Optional[float] = None,
    ):
        """
        Initialize betting challenger.
        
        Args:
            thresholds: Strain detection thresholds
            baseline_roi: Baseline ROI for comparison
        """
        default_thresholds = {
            "roi_degradation_ratio": 0.5,  # Recent ROI < 50% of early ROI
            "drawdown_warning": 0.2,  # 20% drawdown triggers warning
            "drawdown_critical": 0.35,  # 35% drawdown is critical
            "win_rate_degradation": 0.1,  # Win rate drop > 10%
            "losing_streak_warning": 5,  # 5 consecutive losses
            "variance_spike_ratio": 2.0,  # Recent variance > 2x early
            "stake_efficiency_threshold": 0.8,  # Stake too high relative to edge
        }
        
        super().__init__(
            thresholds={**default_thresholds, **(thresholds or {})},
            baseline_performance=baseline_roi,
        )
    
    def _detect_strain_signals(
        self,
        performance_data: BettingState,
    ) -> StrainSignals:
        """Detect betting-specific strain signals."""
        signals = {}
        bets = [b for b in performance_data.bets if b.profit is not None]
        
        if len(bets) < 20:
            # Not enough data for meaningful signals
            return StrainSignals(signals={})
        
        # Split into early and recent periods
        mid = len(bets) // 2
        early_bets = bets[:mid]
        recent_bets = bets[mid:]
        
        # Signal 1: ROI Degradation
        early_roi = self._calculate_roi(early_bets)
        recent_roi = self._calculate_roi(recent_bets)
        roi_ratio = recent_roi / early_roi if early_roi != 0 else 1.0
        
        signals["roi_degradation"] = StrainSignal(
            name="roi_degradation",
            detected=roi_ratio < self.thresholds["roi_degradation_ratio"],
            value=roi_ratio,
            threshold=self.thresholds["roi_degradation_ratio"],
            description=f"Recent ROI ({recent_roi:.1%}) vs early ({early_roi:.1%})",
        )
        
        # Signal 2: Excessive Drawdown
        signals["drawdown_warning"] = StrainSignal(
            name="drawdown_warning",
            detected=performance_data.max_drawdown > self.thresholds["drawdown_warning"],
            value=performance_data.max_drawdown,
            threshold=self.thresholds["drawdown_warning"],
            description=f"Max drawdown: {performance_data.max_drawdown:.1%}",
        )
        
        signals["drawdown_critical"] = StrainSignal(
            name="drawdown_critical",
            detected=performance_data.max_drawdown > self.thresholds["drawdown_critical"],
            value=performance_data.max_drawdown,
            threshold=self.thresholds["drawdown_critical"],
            description=f"Critical drawdown: {performance_data.max_drawdown:.1%}",
        )
        
        # Signal 3: Win Rate Degradation
        early_wr = sum(1 for b in early_bets if b.won) / len(early_bets)
        recent_wr = sum(1 for b in recent_bets if b.won) / len(recent_bets)
        wr_drop = early_wr - recent_wr
        
        signals["win_rate_degradation"] = StrainSignal(
            name="win_rate_degradation",
            detected=wr_drop > self.thresholds["win_rate_degradation"],
            value=wr_drop,
            threshold=self.thresholds["win_rate_degradation"],
            description=f"Win rate: {early_wr:.1%} → {recent_wr:.1%}",
        )
        
        # Signal 4: Losing Streak
        longest_streak = self._longest_losing_streak(bets)
        signals["losing_streak"] = StrainSignal(
            name="losing_streak",
            detected=longest_streak >= self.thresholds["losing_streak_warning"],
            value=float(longest_streak),
            threshold=self.thresholds["losing_streak_warning"],
            description=f"Longest losing streak: {longest_streak}",
        )
        
        # Signal 5: Variance Spike
        early_var = self._calculate_variance(early_bets)
        recent_var = self._calculate_variance(recent_bets)
        var_ratio = recent_var / early_var if early_var > 0 else 1.0
        
        signals["variance_spike"] = StrainSignal(
            name="variance_spike",
            detected=var_ratio > self.thresholds["variance_spike_ratio"],
            value=var_ratio,
            threshold=self.thresholds["variance_spike_ratio"],
            description=f"Profit variance ratio: {var_ratio:.2f}x",
        )
        
        # Signal 6: Baseline Comparison (if available)
        if self.baseline_performance is not None:
            overall_roi = self._calculate_roi(bets)
            roi_vs_baseline = overall_roi / self.baseline_performance if self.baseline_performance != 0 else 1.0
            
            signals["underperforming_baseline"] = StrainSignal(
                name="underperforming_baseline",
                detected=roi_vs_baseline < 0.8,  # More than 20% worse than baseline
                value=roi_vs_baseline,
                threshold=0.8,
                description=f"ROI vs baseline: {roi_vs_baseline:.1%}",
            )
        
        return StrainSignals(signals=signals)
    
    def _propose_alternatives(
        self,
        strain_signals: StrainSignals,
        critiques: List[Critique],
    ) -> List[ProposedMetric]:
        """Propose alternative metrics based on detected strain."""
        proposals = []
        
        # Check specific signals and propose relevant alternatives
        signals = strain_signals.signals
        
        if signals.get("drawdown_warning", StrainSignal("", False, 0, 0)).detected:
            proposals.append(ProposedMetric(
                name="Drawdown-Adjusted ROI",
                formula="ROI / (1 + max_drawdown)",
                rationale="Penalizes high returns achieved through excessive risk",
                expected_improvement="More stable returns with lower volatility",
            ))
            
            proposals.append(ProposedMetric(
                name="Reduced Kelly Fraction",
                formula="kelly_fraction = current * 0.7",
                rationale="Drawdown suggests over-betting; reduce stake sizes",
                expected_improvement="Lower variance, reduced ruin probability",
            ))
        
        if signals.get("roi_degradation", StrainSignal("", False, 0, 0)).detected:
            proposals.append(ProposedMetric(
                name="Rolling ROI Focus",
                formula="avg(ROI over last 50 bets)",
                rationale="Recent performance matters more than historical",
                expected_improvement="Faster adaptation to market changes",
            ))
            
            proposals.append(ProposedMetric(
                name="Increase Min Edge",
                formula="min_edge = current * 1.3",
                rationale="Declining ROI suggests betting on low-value opportunities",
                expected_improvement="Higher quality bets, fewer losing trades",
            ))
        
        if signals.get("variance_spike", StrainSignal("", False, 0, 0)).detected:
            proposals.append(ProposedMetric(
                name="Sharpe Ratio Primary",
                formula="mean(profit) / std(profit) * sqrt(n)",
                rationale="Raw profit ignores variance; Sharpe balances both",
                expected_improvement="Risk-adjusted performance focus",
            ))
        
        if signals.get("losing_streak", StrainSignal("", False, 0, 0)).detected:
            proposals.append(ProposedMetric(
                name="Streak-Adjusted Sizing",
                formula="stake = base_stake * (0.9 ^ consecutive_losses)",
                rationale="Reduce exposure during losing streaks",
                expected_improvement="Capital preservation during downturns",
            ))
        
        return proposals
    
    def _propose_parameter_changes(
        self,
        performance_data: BettingState,
        strain_signals: StrainSignals,
    ) -> Dict[str, Any]:
        """Propose specific parameter changes."""
        changes = {}
        signals = strain_signals.signals
        
        # Drawdown → reduce Kelly
        if signals.get("drawdown_critical", StrainSignal("", False, 0, 0)).detected:
            changes["kelly_fraction"] = {"action": "multiply", "factor": 0.5}
        elif signals.get("drawdown_warning", StrainSignal("", False, 0, 0)).detected:
            changes["kelly_fraction"] = {"action": "multiply", "factor": 0.75}
        
        # ROI degradation → tighten edge requirement
        if signals.get("roi_degradation", StrainSignal("", False, 0, 0)).detected:
            changes["min_edge"] = {"action": "multiply", "factor": 1.3}
        
        # Variance spike → reduce max stake
        if signals.get("variance_spike", StrainSignal("", False, 0, 0)).detected:
            changes["max_stake_fraction"] = {"action": "multiply", "factor": 0.8}
        
        return changes
    
    def _collect_evidence(
        self,
        performance_data: BettingState,
        strain_signals: StrainSignals,
    ) -> Dict[str, Any]:
        """Collect evidence for Authority review."""
        bets = [b for b in performance_data.bets if b.profit is not None]
        
        if not bets:
            return {"n_bets": 0}
        
        return {
            "n_bets": len(bets),
            "total_profit": performance_data.total_profit,
            "roi": performance_data.roi,
            "win_rate": performance_data.win_rate,
            "max_drawdown": performance_data.max_drawdown,
            "final_bankroll": performance_data.bankroll,
            "initial_bankroll": performance_data.initial_bankroll,
            "strain_signals_detected": strain_signals.count_detected,
        }
    
    # Helper methods
    
    def _calculate_roi(self, bets: List[Bet]) -> float:
        """Calculate ROI for a set of bets."""
        if not bets:
            return 0.0
        total_staked = sum(b.stake for b in bets)
        total_profit = sum(b.profit for b in bets if b.profit is not None)
        return total_profit / total_staked if total_staked > 0 else 0.0
    
    def _calculate_variance(self, bets: List[Bet]) -> float:
        """Calculate profit variance."""
        if len(bets) < 2:
            return 0.0
        profits = [b.profit for b in bets if b.profit is not None]
        mean = sum(profits) / len(profits)
        return sum((p - mean) ** 2 for p in profits) / (len(profits) - 1)
    
    def _longest_losing_streak(self, bets: List[Bet]) -> int:
        """Find longest losing streak."""
        max_streak = 0
        current = 0
        
        for bet in bets:
            if bet.won:
                current = 0
            else:
                current += 1
                max_streak = max(max_streak, current)
        
        return max_streak
