"""
IAI AUTHORITY - Risk Management for Betting System
===================================================
The Authority is a GUARDIAN, not an optimizer.

Based on our analysis (iai_evolution.py, honest_assessment.py):
- Static strategy BEATS adaptive parameter tuning
- Authority should PROTECT the edge, not modify it
- Useful for: stake sizing, drawdown protection, edge monitoring

Key Insight: The edge (Home @ 4.0-6.0) was validated statistically.
Adjusting it based on recent results = overfitting to noise.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Invariants - these are FIXED, Authority cannot change them
INVARIANTS = {
    "selection": "H",           # Home win
    "odds_min": 4.0,            # Minimum odds
    "odds_max": 6.0,            # Maximum odds
    "base_stake_pct": 3.0,      # Base stake percentage
    "expected_edge": 5.2,       # Expected edge %
    "expected_win_rate": 26.0,  # Expected win rate %
}

# Authority thresholds - can be tuned
AUTHORITY_CONFIG = {
    # Stake reduction triggers
    "loss_streak_reduce_1": 5,      # After 5 losses, reduce stake
    "loss_streak_reduce_2": 8,      # After 8 losses, reduce more
    "loss_streak_pause": 10,        # After 10 losses, pause betting
    
    # Stake reduction amounts
    "stake_reduction_1": 0.67,      # Reduce to 67% (2% instead of 3%)
    "stake_reduction_2": 0.50,      # Reduce to 50% (1.5% instead of 3%)
    
    # Win rate monitoring
    "min_bets_for_analysis": 20,    # Need this many bets before analyzing
    "win_rate_warning": 20.0,       # Warning if win rate drops below this
    "win_rate_critical": 15.0,      # Critical if win rate drops below this
    
    # Recovery
    "wins_to_restore_stake": 3,     # After 3 wins, restore normal stake
}


class BettingAuthority:
    """
    IAI Authority for betting - manages risk, not strategy.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or AUTHORITY_CONFIG
        self.invariants = INVARIANTS.copy()
    
    def analyze_performance(self, predictions: List[Dict]) -> Dict:
        """
        Analyze current performance and return metrics.
        """
        settled = [p for p in predictions if p['status'] in ['won', 'lost']]
        pending = [p for p in predictions if p['status'] == 'pending']
        
        if not settled:
            return {
                "total_bets": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0,
                "current_streak": 0,
                "streak_type": None,
                "status": "INSUFFICIENT_DATA"
            }
        
        wins = sum(1 for p in settled if p['status'] == 'won')
        losses = len(settled) - wins
        win_rate = (wins / len(settled)) * 100
        
        # Calculate current streak
        streak = 0
        streak_type = None
        for p in reversed(settled):
            if streak_type is None:
                streak_type = p['status']
                streak = 1
            elif p['status'] == streak_type:
                streak += 1
            else:
                break
        
        return {
            "total_bets": len(settled),
            "pending_bets": len(pending),
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 1),
            "expected_win_rate": self.invariants["expected_win_rate"],
            "current_streak": streak,
            "streak_type": streak_type,
            "status": "OK"
        }
    
    def get_stake_multiplier(self, predictions: List[Dict]) -> Tuple[float, str]:
        """
        Determine stake multiplier based on current state.
        Returns (multiplier, reason).
        
        This is the ONLY thing Authority controls.
        """
        perf = self.analyze_performance(predictions)
        
        # Not enough data
        if perf["total_bets"] < 5:
            return 1.0, "NORMAL: Building initial data"
        
        # Check for losing streak
        if perf["streak_type"] == "lost":
            if perf["current_streak"] >= self.config["loss_streak_pause"]:
                return 0.0, f"PAUSED: {perf['current_streak']} consecutive losses - review required"
            elif perf["current_streak"] >= self.config["loss_streak_reduce_2"]:
                return self.config["stake_reduction_2"], f"REDUCED: {perf['current_streak']} losses - 50% stake"
            elif perf["current_streak"] >= self.config["loss_streak_reduce_1"]:
                return self.config["stake_reduction_1"], f"REDUCED: {perf['current_streak']} losses - 67% stake"
        
        # Check win rate over longer period
        if perf["total_bets"] >= self.config["min_bets_for_analysis"]:
            if perf["win_rate"] < self.config["win_rate_critical"]:
                return 0.5, f"CAUTION: Win rate {perf['win_rate']}% below critical threshold"
            elif perf["win_rate"] < self.config["win_rate_warning"]:
                return 0.75, f"WARNING: Win rate {perf['win_rate']}% below expected"
        
        # Check for winning streak (can restore after losses)
        if perf["streak_type"] == "won" and perf["current_streak"] >= self.config["wins_to_restore_stake"]:
            return 1.0, f"RESTORED: {perf['current_streak']} consecutive wins"
        
        return 1.0, "NORMAL: Operating within expected parameters"
    
    def calculate_stake(self, bankroll: float, predictions: List[Dict]) -> Tuple[float, str]:
        """
        Calculate actual stake for next bet.
        """
        base_stake = bankroll * (self.invariants["base_stake_pct"] / 100)
        multiplier, reason = self.get_stake_multiplier(predictions)
        
        actual_stake = base_stake * multiplier
        
        return round(actual_stake, 2), reason
    
    def should_bet(self, match: Dict, predictions: List[Dict]) -> Tuple[bool, str]:
        """
        Determine if we should bet on this match.
        
        Authority can only say NO for risk reasons,
        never modifies the qualifying criteria.
        """
        # Check if match qualifies (INVARIANT - never changed)
        odds = match.get('home_odds', 0)
        if not (self.invariants["odds_min"] <= odds <= self.invariants["odds_max"]):
            return False, f"Does not qualify: odds {odds} outside {self.invariants['odds_min']}-{self.invariants['odds_max']}"
        
        # Check if Authority wants to pause
        multiplier, reason = self.get_stake_multiplier(predictions)
        if multiplier == 0:
            return False, reason
        
        return True, f"Qualifies: HOME @ {odds} (stake: {multiplier*100:.0f}%)"
    
    def generate_report(self, predictions: List[Dict]) -> Dict:
        """
        Generate Authority report for dashboard.
        """
        perf = self.analyze_performance(predictions)
        multiplier, stake_reason = self.get_stake_multiplier(predictions)
        
        # Determine overall status
        if multiplier == 0:
            status = "PAUSED"
            status_emoji = "🛑"
        elif multiplier < 1:
            status = "REDUCED"
            status_emoji = "⚠️"
        else:
            status = "NORMAL"
            status_emoji = "✅"
        
        # Check for edge decay
        edge_status = "HEALTHY"
        if perf["total_bets"] >= 50:
            if perf["win_rate"] < self.invariants["expected_win_rate"] - 5:
                edge_status = "DECLINING"
            elif perf["win_rate"] < self.invariants["expected_win_rate"] - 10:
                edge_status = "CRITICAL"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "status_emoji": status_emoji,
            "stake_multiplier": multiplier,
            "stake_reason": stake_reason,
            "performance": perf,
            "edge_status": edge_status,
            "invariants": self.invariants,
            "recommendations": self._get_recommendations(perf, multiplier)
        }
    
    def _get_recommendations(self, perf: Dict, multiplier: float) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        
        if perf["total_bets"] < 20:
            recs.append("📊 Continue collecting data - need 20+ bets for reliable analysis")
        
        if multiplier == 0:
            recs.append("🛑 System is paused - review recent results before resuming")
            recs.append("💡 Consider if market conditions have changed")
        elif multiplier < 1:
            recs.append(f"⚠️ Stake reduced to {multiplier*100:.0f}% due to recent losses")
            recs.append("💡 This is normal variance - strategy will recover if edge is real")
        
        if perf.get("win_rate", 0) > 30 and perf["total_bets"] >= 20:
            recs.append("🎯 Win rate above expected - could be positive variance")
        
        if perf.get("pending_bets", 0) > 5:
            recs.append(f"⏳ {perf['pending_bets']} bets pending - results coming soon")
        
        if not recs:
            recs.append("✅ System operating normally within expected parameters")
        
        return recs


# Singleton instance
_authority = None

def get_authority() -> BettingAuthority:
    """Get or create Authority instance."""
    global _authority
    if _authority is None:
        _authority = BettingAuthority()
    return _authority
