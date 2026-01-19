"""
Backtest forex strategies on historical data.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from typing import List
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pilots.iai_forex.core.data_fetcher import ForexDataFetcher
from pilots.iai_forex.core.strategies import Signal, get_strategy


@dataclass
class Trade:
    """Completed trade."""
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    pair: str
    direction: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    pips: float
    profit_pct: float
    profit_usd: float
    strategy: str
    exit_reason: str  # "TP", "SL", "TIME"


class ForexBacktester:
    """Backtest forex strategies."""
    
    def __init__(
        self,
        initial_capital: float = 10000,
        risk_per_trade: float = 0.02,  # 2% risk
        pip_value: float = 10.0,  # $10 per pip for standard lot
        max_hold_days: int = 10,  # Changed from hours to days
    ):
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.pip_value = pip_value
        self.max_hold_days = max_hold_days
        
        self.capital = initial_capital
        self.trades: List[Trade] = []
        self.equity_curve = []
    
    def calculate_pips(self, entry: float, exit: float, direction: str, pair: str) -> float:
        """Calculate pips based on pair."""
        # For JPY pairs, 1 pip = 0.01, otherwise 0.0001
        pip_size = 0.01 if "JPY" in pair else 0.0001
        
        if direction == "BUY":
            pips = (exit - entry) / pip_size
        else:  # SELL
            pips = (entry - exit) / pip_size
        
        return pips
    
    def simulate_trade(
        self,
        signal: Signal,
        df: pd.DataFrame,
        current_idx: int
    ) -> Trade:
        """
        Simulate a trade from signal.
        
        Returns:
            Trade object with results
        """
        entry_time = signal.timestamp
        entry_price = signal.entry_price
        stop_loss = signal.stop_loss
        take_profit = signal.take_profit
        
        # Default SL/TP if not set
        if stop_loss is None:
            stop_loss = entry_price * 0.98 if signal.direction == "BUY" else entry_price * 1.02
        if take_profit is None:
            take_profit = entry_price * 1.015 if signal.direction == "BUY" else entry_price * 0.985
        
        # Find exit
        exit_time = None
        exit_price = None
        exit_reason = None
        
        for i in range(current_idx + 1, len(df)):
            candle = df.iloc[i]
            time_diff_days = (df.index[i] - entry_time).days
            
            # Check time limit
            if time_diff_days > self.max_hold_days:
                exit_time = df.index[i]
                exit_price = candle['Close']
                exit_reason = "TIME"
                break
            
            # Check stop loss and take profit
            if signal.direction == "BUY":
                if candle['Low'] <= stop_loss:
                    exit_time = df.index[i]
                    exit_price = stop_loss
                    exit_reason = "SL"
                    break
                elif candle['High'] >= take_profit:
                    exit_time = df.index[i]
                    exit_price = take_profit
                    exit_reason = "TP"
                    break
            else:  # SELL
                if candle['High'] >= stop_loss:
                    exit_time = df.index[i]
                    exit_price = stop_loss
                    exit_reason = "SL"
                    break
                elif candle['Low'] <= take_profit:
                    exit_time = df.index[i]
                    exit_price = take_profit
                    exit_reason = "TP"
                    break
        
        # If no exit found, close at last candle
        if exit_time is None:
            exit_time = df.index[-1]
            exit_price = df.iloc[-1]['Close']
            exit_reason = "END"
        
        # Calculate results
        pips = self.calculate_pips(entry_price, exit_price, signal.direction, signal.pair)
        profit_pct = pips * (0.01 if "JPY" in signal.pair else 0.0001) / entry_price
        
        # Position sizing: risk 2% of capital
        position_size = (self.capital * self.risk_per_trade) / abs(entry_price - stop_loss)
        profit_usd = position_size * (exit_price - entry_price) if signal.direction == "BUY" else position_size * (entry_price - exit_price)
        
        return Trade(
            entry_time=entry_time,
            exit_time=exit_time,
            pair=signal.pair,
            direction=signal.direction,
            entry_price=entry_price,
            exit_price=exit_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            pips=pips,
            profit_pct=profit_pct,
            profit_usd=profit_usd,
            strategy=signal.strategy,
            exit_reason=exit_reason,
        )
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        pair: str,
        strategy_name: str,
    ) -> dict:
        """
        Run backtest for a strategy.
        
        Returns:
            Dictionary with performance metrics
        """
        # Get strategy
        strategy = get_strategy(strategy_name)
        
        # Generate signals
        print(f"\nGenerating signals for {strategy.name}...")
        signals = strategy.generate_signals(df, pair)
        print(f"Generated {len(signals)} signals")
        
        if len(signals) == 0:
            return {"error": "No signals generated"}
        
        # Simulate trades
        self.trades = []
        self.capital = self.initial_capital
        self.equity_curve = [self.initial_capital]
        
        print(f"\nSimulating trades...")
        for signal in signals:
            # Find index of signal
            idx = df.index.get_loc(signal.timestamp)
            
            # Simulate trade
            trade = self.simulate_trade(signal, df, idx)
            self.trades.append(trade)
            
            # Update capital
            self.capital += trade.profit_usd
            self.equity_curve.append(self.capital)
        
        # Calculate metrics
        return self.calculate_metrics()
    
    def calculate_metrics(self) -> dict:
        """Calculate performance metrics."""
        if len(self.trades) == 0:
            return {"error": "No trades"}
        
        # Basic stats
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.profit_usd > 0]
        losing_trades = [t for t in self.trades if t.profit_usd < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Profit stats
        total_profit = sum(t.profit_usd for t in self.trades)
        avg_win = np.mean([t.profit_usd for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.profit_usd for t in losing_trades]) if losing_trades else 0
        
        # Risk-adjusted metrics
        returns = np.array([t.profit_usd for t in self.trades])
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0
        
        # Drawdown
        equity = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max
        max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0
        
        # Return
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "total_return": total_return,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "final_capital": self.capital,
            "avg_pips_per_trade": np.mean([t.pips for t in self.trades]),
        }
    
    def print_results(self, metrics: dict):
        """Print backtest results."""
        print("\n" + "="*70)
        print("BACKTEST RESULTS")
        print("="*70)
        
        if "error" in metrics:
            print(f"Error: {metrics['error']}")
            return
        
        print(f"\nTotal Trades:      {metrics['total_trades']}")
        print(f"Win Rate:          {metrics['win_rate']*100:.1f}%")
        print(f"Total Profit:      ${metrics['total_profit']:.2f}")
        print(f"Total Return:      {metrics['total_return']*100:.1f}%")
        print(f"\nAvg Win:           ${metrics['avg_win']:.2f}")
        print(f"Avg Loss:          ${metrics['avg_loss']:.2f}")
        print(f"Profit Factor:     {metrics['profit_factor']:.2f}")
        print(f"\nSharpe Ratio:      {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:      {metrics['max_drawdown']*100:.1f}%")
        print(f"\nFinal Capital:     ${metrics['final_capital']:.2f}")
        print(f"Avg Pips/Trade:    {metrics['avg_pips_per_trade']:.1f}")
        
        # Show last 5 trades
        print("\n" + "-"*70)
        print("LAST 5 TRADES")
        print("-"*70)
        for trade in self.trades[-5:]:
            profit_marker = "+" if trade.profit_usd > 0 else "-"
            print(f"{profit_marker} {trade.entry_time.date()} | {trade.direction:4} | "
                  f"{trade.pips:+6.1f} pips | ${trade.profit_usd:+8.2f} | {trade.exit_reason}")


def main():
    """Run backtest on EUR/USD."""
    print("="*70)
    print("FOREX BACKTESTER")
    print("="*70)
    
    # Fetch data (use daily for better coverage)
    fetcher = ForexDataFetcher()
    df = fetcher.fetch_pair(
        "EUR/USD",
        start_date="2020-01-01",
        end_date="2024-01-01",
        interval="1d"
    )
    
    # Add indicators
    df = fetcher.add_technical_indicators(df)
    
    print(f"\nData: {len(df)} daily candles")
    print(f"Period: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"Price range: ${df['Close'].min():.4f} - ${df['Close'].max():.4f}")
    
    # Test all strategies
    backtester = ForexBacktester(initial_capital=10000)
    
    strategies = ["H1", "H2", "H3", "H4"]
    results = {}
    
    for strat in strategies:
        print(f"\n{'='*70}")
        print(f"Testing {strat}")
        print(f"{'='*70}")
        
        metrics = backtester.run_backtest(df, "EUR/USD", strat)
        backtester.print_results(metrics)
        results[strat] = metrics
    
    # Compare strategies
    print("\n" + "="*70)
    print("STRATEGY COMPARISON")
    print("="*70)
    print(f"{'Strategy':<20} {'Trades':>8} {'Win%':>8} {'Return':>10} {'Sharpe':>8} {'Drawdown':>10}")
    print("-"*70)
    
    for strat, metrics in results.items():
        if "error" not in metrics:
            print(f"{strat:<20} {metrics['total_trades']:>8} "
                  f"{metrics['win_rate']*100:>7.1f}% "
                  f"{metrics['total_return']*100:>9.1f}% "
                  f"{metrics['sharpe_ratio']:>8.2f} "
                  f"{metrics['max_drawdown']*100:>9.1f}%")


if __name__ == "__main__":
    main()
