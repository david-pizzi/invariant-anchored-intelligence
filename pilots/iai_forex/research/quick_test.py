"""
Quick test - Run backtests on multiple pairs and periods.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pilots.iai_forex.core.data_fetcher import ForexDataFetcher
from pilots.iai_forex.research.backtest import ForexBacktester


def test_strategy_on_pair(pair: str, strategy: str, start: str, end: str):
    """Test a single strategy on a pair."""
    print(f"\n{'='*70}")
    print(f"{strategy} on {pair} ({start} to {end})")
    print(f"{'='*70}")
    
    # Fetch data
    fetcher = ForexDataFetcher()
    try:
        df = fetcher.fetch_pair(pair, start, end, "1d")
        df = fetcher.add_technical_indicators(df)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
    
    # Backtest
    backtester = ForexBacktester(initial_capital=10000)
    metrics = backtester.run_backtest(df, pair, strategy)
    backtester.print_results(metrics)
    
    return metrics


def main():
    print("="*70)
    print("IAI FOREX QUICK TEST")
    print("="*70)
    
    # Test best strategies (H3 and H4) on multiple pairs
    pairs = ["EUR/USD", "GBP/USD", "USD/JPY"]
    strategies = ["H3", "H4"]
    
    results = {}
    
    for pair in pairs:
        for strat in strategies:
            key = f"{pair}_{strat}"
            metrics = test_strategy_on_pair(
                pair, strat,
                start="2020-01-01",
                end="2024-01-01"
            )
            if metrics and "error" not in metrics:
                results[key] = metrics
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY - BEST STRATEGIES")
    print("="*70)
    print(f"{'Pair + Strategy':<20} {'Trades':>8} {'Win%':>8} {'Return':>10} {'Sharpe':>8}")
    print("-"*70)
    
    # Sort by Sharpe ratio
    sorted_results = sorted(
        results.items(),
        key=lambda x: x[1]["sharpe_ratio"],
        reverse=True
    )
    
    for key, metrics in sorted_results:
        print(f"{key:<20} {metrics['total_trades']:>8} "
              f"{metrics['win_rate']*100:>7.1f}% "
              f"{metrics['total_return']*100:>9.1f}% "
              f"{metrics['sharpe_ratio']:>8.2f}")
    
    # Best strategy
    if sorted_results:
        best_key, best_metrics = sorted_results[0]
        print(f"\n✓ BEST: {best_key} with Sharpe {best_metrics['sharpe_ratio']:.2f}")


if __name__ == "__main__":
    main()
