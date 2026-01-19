"""
Forex Challenger - Detects regime changes and proposes strategy switches.
Inherits from base IAI Challenger.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from iai_core.challenger import BaseChallenger
from iai_core.types import Proposal, Invariants, StrainSignals, StrainSignal, Critique, Severity


class ForexChallenger(BaseChallenger):
    """
    Challenger for forex trading.
    
    Detects:
    - Strategy performance degradation
    - Market regime changes
    - Alternative strategies with better performance
    """
    
    def __init__(
        self,
        evaluation_window: int = 60,  # days
        improvement_threshold: float = 0.3,  # 30% better Sharpe required
    ):
        super().__init__()
        self.evaluation_window = evaluation_window
        self.improvement_threshold = improvement_threshold
    
    def _detect_strain_signals(
        self,
        current_metrics: Dict[str, Any],
        historical_metrics: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Detect strain indicators in current performance."""
        current_sharpe = current_metrics.get("sharpe_ratio", 0)
        
        strain_signals = {
            "severe_degradation": current_sharpe < 1.0,
            "sharpe_below_threshold": current_sharpe < 1.5,
            "high_drawdown": current_metrics.get("max_drawdown", 0) > 0.10,
        }
        
        return strain_signals
    
    def _propose_alternatives(
        self,
        strain_signals: Dict[str, Any],
        current_metrics: Dict[str, Any],
    ) -> List[Proposal]:
        """Propose alternative strategies based on strain."""
        proposals = []
        
        if strain_signals.get("severe_degradation"):
            proposals.append(Proposal(
                id="pause_trading",
                description="PAUSE trading due to severe performance degradation",
                evidence={"current_sharpe": current_metrics.get("sharpe_ratio", 0)},
                invariants_affected=["min_sharpe"],
            ))
        
        return proposals
    
    def detect_strain(
        self,
        current_metrics: Dict[str, Any],
        historical_metrics: List[Dict[str, Any]],
        invariants: Invariants,
    ) -> List[Proposal]:
        """
        Detect strain in current strategy.
        
        Proposes:
        - PAUSE if strategy failing
        - SWITCH if better alternative exists
        """
        proposals = []
        
        print(f"\n{'='*70}")
        print(f"CHALLENGER EVALUATION")
        print(f"{'='*70}")
        
        current_strategy = current_metrics.get("strategy", "Unknown")
        current_sharpe = current_metrics.get("sharpe_ratio", 0)
        current_drawdown = current_metrics.get("max_drawdown", 0)
        
        print(f"\nCurrent Strategy: {current_strategy}")
        print(f"  Sharpe:   {current_sharpe:.2f}")
        print(f"  Drawdown: {current_drawdown*100:.1f}%")
        
        # Check for severe degradation
        if current_sharpe < 1.0:
            # Create strain signal
            strain_signal = StrainSignal(
                name="sharpe_degradation",
                detected=True,
                value=current_sharpe,
                threshold=1.0,
                description=f"{current_strategy} Sharpe {current_sharpe:.2f} < 1.0 threshold"
            )
            
            # Create critique
            critique = Critique(
                severity=Severity.CRITICAL,
                signal="min_sharpe",
                description=f"Strategy {current_strategy} severely underperforming - PAUSE trading immediately",
                evidence={
                    "current_sharpe": current_sharpe,
                    "threshold": 1.0
                }
            )
            
            proposals.append(Proposal(
                strain_signals=StrainSignals(signals={"sharpe_degradation": strain_signal}),
                critiques=[critique],
                proposed_metrics=[],
                evidence={
                    "current_sharpe": current_sharpe,
                    "threshold": 1.0,
                    "reason": "severe_degradation"
                }
            ))
        
        # Check alternatives (if provided)
        if "alternatives" in current_metrics:
            alternatives = current_metrics["alternatives"]
            
            print(f"\nTesting Alternatives:")
            for alt_name, alt_metrics in alternatives.items():
                alt_sharpe = alt_metrics.get("sharpe_ratio", 0)
                alt_drawdown = alt_metrics.get("max_drawdown", 0)
                
                print(f"  {alt_name}: Sharpe {alt_sharpe:.2f}, Drawdown {alt_drawdown*100:.1f}%")
                
                # Propose switch if significantly better
                improvement = (alt_sharpe - current_sharpe) / current_sharpe if current_sharpe > 0 else float('inf')
                
                if alt_sharpe > current_sharpe * (1 + self.improvement_threshold):
                    # Create strain signal
                    strain_signal = StrainSignal(
                        name=f"better_alternative_{alt_name}",
                        detected=True,
                        value=alt_sharpe,
                        threshold=current_sharpe * (1 + self.improvement_threshold),
                        description=f"{alt_name} outperforms {current_strategy} by {improvement*100:.1f}%"
                    )
                    
                    # Create critique
                    critique = Critique(
                        severity=Severity.MEDIUM,
                        signal="min_sharpe",
                        description=f"SWITCH from {current_strategy} to {alt_name} - {improvement*100:.1f}% improvement",
                        evidence={
                            "improvement": improvement,
                            "alt_sharpe": alt_sharpe
                        }
                    )
                    
                    proposals.append(Proposal(
                        strain_signals=StrainSignals(signals={f"better_alternative_{alt_name}": strain_signal}),
                        critiques=[critique],
                        proposed_metrics=[],
                        evidence={
                            "current_strategy": current_strategy,
                            "current_sharpe": current_sharpe,
                            "alternative_strategy": alt_name,
                            "alternative_sharpe": alt_sharpe,
                            "improvement": improvement,
                            **alt_metrics
                        }
                    ))
        
        if len(proposals) == 0:
            print(f"\n[+] No strain detected - current strategy performing adequately")
        else:
            print(f"\n⚠️  Generated {len(proposals)} proposal(s)")
            for p in proposals:
                if p.critiques:
                    print(f"  • {p.critiques[0].description}")
                else:
                    print(f"  • {len(p.strain_signals.signals)} strain signal(s) detected")
        
        return proposals
    
    def analyze_regime(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze market regime from recent data.
        
        Returns:
            Dict with regime characteristics
        """
        if len(df) < 20:
            return {"regime": "unknown", "volatility": 0, "trend_strength": 0}
        
        recent = df.tail(60)  # Last 60 days
        
        # Volatility
        returns = recent['Close'].pct_change()
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        # Trend strength (ADX approximation)
        if 'SMA_20' in recent.columns and 'SMA_50' in recent.columns:
            sma_diff = abs(recent['SMA_20'].iloc[-1] - recent['SMA_50'].iloc[-1])
            trend_strength = sma_diff / recent['Close'].iloc[-1]
        else:
            trend_strength = 0
        
        # ATR regime
        if 'ATR' in recent.columns:
            atr = recent['ATR'].iloc[-1]
            atr_avg = recent['ATR'].mean()
            atr_regime = "high" if atr > atr_avg * 1.5 else "low" if atr < atr_avg * 0.5 else "normal"
        else:
            atr_regime = "unknown"
        
        # Classify regime
        if volatility > 0.20:
            regime = "high_volatility"
        elif volatility < 0.10:
            regime = "low_volatility"
        elif trend_strength > 0.02:
            regime = "trending"
        else:
            regime = "ranging"
        
        return {
            "regime": regime,
            "volatility": volatility,
            "trend_strength": trend_strength,
            "atr_regime": atr_regime,
        }
