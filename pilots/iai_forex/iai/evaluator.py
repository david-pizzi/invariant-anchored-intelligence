"""
Forex Evaluator - Computes performance metrics.
Inherits from base IAI Evaluator.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from iai_core.evaluator import BaseEvaluator


class ForexEvaluator(BaseEvaluator):
    """
    Evaluator for forex trading.
    
    Computes:
    - Sharpe ratio
    - Max drawdown
    - Win rate
    - Profit factor
    - Other risk-adjusted metrics
    """
    
    def _compute_metrics(self, **kwargs) -> Dict[str, Any]:
        """Compute performance metrics from trades."""
        trades = kwargs.get("trades", [])
        initial_capital = kwargs.get("initial_capital", 10000)
        
        return self.evaluate(trades, initial_capital=initial_capital)
    
    def _check_violations(self, metrics: Dict[str, Any], invariants: Any) -> List[str]:
        """Check if metrics violate invariants."""
        violations = []
        
        # For now, just return empty - Authority will check
        return violations
    
    def evaluate(self, trades: List[Any], **kwargs) -> Dict[str, Any]:
        """
        Evaluate trading performance.
        
        Args:
            trades: List of Trade objects
            
        Returns:
            Dict with performance metrics
        """
        if len(trades) == 0:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "total_return": 0,
            }
        
        # Extract profits
        profits = np.array([t.profit_usd for t in trades])
        
        # Basic stats
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.profit_usd > 0]
        losing_trades = [t for t in trades if t.profit_usd < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Profit stats
        total_profit = profits.sum()
        avg_profit = profits.mean()
        avg_win = np.mean([t.profit_usd for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.profit_usd for t in losing_trades]) if losing_trades else 0
        
        # Sharpe ratio (annualized)
        if np.std(profits) > 0:
            sharpe = (avg_profit / np.std(profits)) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Drawdown calculation
        initial_capital = kwargs.get("initial_capital", 10000)
        equity = [initial_capital]
        for p in profits:
            equity.append(equity[-1] + p)
        
        equity = np.array(equity)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max
        max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0
        
        # Return
        final_capital = equity[-1]
        total_return = (final_capital - initial_capital) / initial_capital
        
        # Profit factor
        total_wins = sum(t.profit_usd for t in winning_trades)
        total_losses = abs(sum(t.profit_usd for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "total_return": total_return,
            "total_profit": total_profit,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "final_capital": final_capital,
        }
