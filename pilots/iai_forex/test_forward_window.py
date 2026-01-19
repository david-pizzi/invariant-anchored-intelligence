"""Test if forward window generates any trades"""
import pandas as pd
import yfinance as yf
from research.backtest import ForexBacktester
from core.strategies import STRATEGIES

# Download EUR/USD data
print("Downloading EUR/USD data...")
df = yf.download("EURUSD=X", start="2023-01-01", end="2024-01-01", progress=False)
df.reset_index(inplace=True)
print(f"Downloaded {len(df)} days of data")

# Test a 7-day forward window
print("\n" + "="*70)
print("Testing 7-day forward window with H4_TrendFollowing")
print("="*70)

# Use days 90-97 as forward window
df_forward = df.iloc[90:97].copy()
print(f"\nForward window: {df_forward.iloc[0]['Date']} to {df_forward.iloc[-1]['Date']}")
print(f"Days: {len(df_forward)}")

# Run backtest on this 7-day window
backtester = ForexBacktester(initial_capital=10000)
metrics = backtester.run_backtest(df_forward, "EUR/USD", "H4")

print(f"\nResults:")
print(f"  Trades: {metrics.get('num_trades', 0)}")
print(f"  Return: {metrics.get('total_return', 0)*100:.2f}%")
print(f"  Sharpe: {metrics.get('sharpe_ratio', 0):.2f}")

# Try multiple windows
print("\n" + "="*70)
print("Testing multiple 7-day windows")
print("="*70)

strategies_to_test = ["H1", "H2", "H3", "H4"]

for strategy in strategies_to_test:
    total_trades = 0
    total_periods = 0
    
    for i in range(0, len(df)-7, 7):  # Test every 7 days
        df_window = df.iloc[i:i+7].copy()
        bt = ForexBacktester(initial_capital=10000)
        m = bt.run_backtest(df_window, "EUR/USD", strategy)
        trades = m.get('num_trades', 0)
        total_trades += trades
        total_periods += 1
    
    avg_trades = total_trades / total_periods if total_periods > 0 else 0
    print(f"{strategy}: {total_trades} total trades across {total_periods} periods (avg {avg_trades:.2f} trades/period)")

print("\n" + "="*70)
print("DIAGNOSIS")
print("="*70)
print("If avg trades/period is very low (< 0.5), then 7-day windows are")
print("too short for strategies to generate signals. Consider:")
print("  1. Longer forward windows (14 or 30 days)")
print("  2. Less frequent re-evaluation (weekly → monthly)")
print("  3. Accumulate returns over multiple short periods")
