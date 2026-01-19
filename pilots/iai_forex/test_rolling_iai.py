"""
Test IAI with high-frequency forex data and rolling re-evaluation.

Unlike betting (discrete matches), forex updates continuously.
This test simulates IAI re-evaluating strategy every week with new data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pilots.iai_forex.core.data_fetcher import ForexDataFetcher
from pilots.iai_forex.core.strategies import STRATEGIES
from pilots.iai_forex.research.backtest import ForexBacktester
from pilots.iai_forex.iai.authority import ForexAuthority
from pilots.iai_forex.iai.challenger import ForexChallenger
from pilots.iai_forex.iai.evaluator import ForexEvaluator


def rolling_iai_evaluation(
    pair: str = "EUR/USD",
    start_date: str = "2022-01-01",
    end_date: str = "2024-01-01",
    evaluation_window: int = 90,  # days
    re_eval_frequency: int = 7,   # re-evaluate every 7 days
    initial_capital: float = 10000.0,
    forward_window_days: int = 7,  # days to measure forward P&L (with hourly data, 7 days = 168 candles!)
):
    """
    Simulate IAI with rolling re-evaluation.
    
    Every week, IAI:
    1. Tests current strategy on last 90 days
    2. Tests alternatives on last 90 days
    3. Decides: continue, switch, or pause
    4. Logs decision
    """
    print("="*70)
    print("IAI FOREX - ROLLING RE-EVALUATION TEST")
    print("="*70)
    print(f"\nPair: {pair}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Evaluation window: {evaluation_window} days")
    print(f"Re-evaluation frequency: {re_eval_frequency} days")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    
    # Fetch full dataset
    # Use hourly candles for more granular trading (24 data points per day)
    fetcher = ForexDataFetcher()
    df_full = fetcher.fetch_pair(pair, start_date, end_date, "1h")
    df_full = fetcher.add_technical_indicators(df_full)
    
    print(f"\nLoaded {len(df_full)} daily candles")
    
    # Initialize IAI components
    authority = ForexAuthority(min_sharpe=1.5, max_drawdown=0.15, min_win_rate=0.45)
    challenger = ForexChallenger(improvement_threshold=0.3)
    evaluator = ForexEvaluator()
    
    # Track state
    current_strategy = "H3"  # Start with best from previous test
    evaluation_dates = []
    decisions = []
    current_capital = initial_capital  # Track running capital
    
    # Rolling evaluation loop
    start_idx = evaluation_window
    
    for i in range(start_idx, len(df_full), re_eval_frequency):
        eval_date = df_full.index[i]
        
        # Get evaluation window (last 90 days)
        window_start = i - evaluation_window
        df_window = df_full.iloc[window_start:i].copy()
        
        print(f"\n{'='*70}")
        print(f"EVALUATION #{len(evaluation_dates) + 1}")
        print(f"Date: {eval_date.date()}")
        print(f"Window: {df_window.index[0].date()} to {df_window.index[-1].date()}")
        print(f"Current Strategy: {current_strategy}")
        print(f"{'='*70}")
        
        # Test current strategy (unless PAUSED)
        if current_strategy == "PAUSED":
            # Create dummy metrics for paused state
            current_metrics = {
                "sharpe_ratio": 0.0,
                "total_return": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "num_trades": 0,
            }
            print(f"\n[PAUSED] Testing alternatives to resume trading...")
        else:
            backtester = ForexBacktester(initial_capital=10000)
            current_metrics = backtester.run_backtest(df_window, pair, current_strategy)
            
            if "error" in current_metrics:
                print(f"Error testing {current_strategy}: {current_metrics['error']}")
                continue
            
            print(f"\n{current_strategy} Performance:")
            print(f"  Sharpe:   {current_metrics['sharpe_ratio']:.2f}")
            print(f"  Return:   {current_metrics['total_return']*100:.1f}%")
            print(f"  Drawdown: {current_metrics['max_drawdown']*100:.1f}%")
            print(f"  Win Rate: {current_metrics['win_rate']*100:.1f}%")
        
        # Get forward-looking window for realistic P&L calculation
        # Use a FIXED forward window (default 30 days) regardless of re-eval frequency
        # This ensures strategies have enough time to generate trade signals
        forward_end = min(i + forward_window_days, len(df_full))
        df_forward = df_full.iloc[i:forward_end].copy()
        
        # Calculate realistic return for this period
        if current_strategy != "PAUSED" and len(df_forward) > 1:
            forward_backtester = ForexBacktester(initial_capital=10000)
            forward_metrics = forward_backtester.run_backtest(df_forward, pair, current_strategy)
            period_return = forward_metrics.get('total_return', 0.0)
            num_trades = forward_metrics.get('num_trades', 0)
            print(f"\nForward Period ({len(df_forward)} days): {num_trades} trades, {period_return*100:.2f}% return")
        else:
            period_return = 0.0  # No return when paused
            if current_strategy == "PAUSED":
                print(f"\nForward Period: PAUSED - No trading")
        
        # Test alternatives
        alternatives = {}
        for strat_name in STRATEGIES.keys():
            if strat_name == current_strategy and current_strategy != "PAUSED":
                continue
            
            alt_backtester = ForexBacktester(initial_capital=10000)
            alt_metrics = alt_backtester.run_backtest(df_window, pair, strat_name)
            
            if "error" not in alt_metrics:
                alternatives[strat_name] = alt_metrics
        
        # Show best alternative
        if alternatives:
            best_alt = max(alternatives.items(), key=lambda x: x[1]["sharpe_ratio"])
            print(f"\nBest Alternative: {best_alt[0]}")
            print(f"  Sharpe: {best_alt[1]['sharpe_ratio']:.2f}")
        
        # Authority check
        if current_strategy == "PAUSED":
            should_continue = False  # Can't continue if paused
        else:
            should_continue = authority.check_current_performance(current_metrics)
        
        # Challenger check - should we switch?
        current_metrics["strategy"] = current_strategy
        current_metrics["alternatives"] = alternatives
        
        from iai_core.types import Invariants
        invariants = Invariants(primary_metric="sharpe_ratio")
        
        proposals = challenger.detect_strain(
            current_metrics=current_metrics,
            historical_metrics=[],
            invariants=invariants,
        )
        
        # Decision logic
        decision = {
            "date": eval_date,
            "strategy_before": current_strategy,
            "strategy_after": current_strategy,
            "action": "CONTINUE",
            "sharpe": current_metrics['sharpe_ratio'],
            "return": current_metrics['total_return'],  # Historical performance for decision
            "drawdown": current_metrics['max_drawdown'],
            "capital_before": current_capital,
            "profit": current_capital * period_return,  # Forward-looking profit
            "capital_after": current_capital * (1 + period_return),  # Forward-looking capital
            "period_return": period_return,  # Actual return for this period
        }
        
        if not should_continue:
            if current_strategy == "PAUSED":
                # Try to resume with best alternative
                if alternatives:
                    # Test each alternative against invariants
                    for alt_name, alt_metrics in sorted(alternatives.items(), 
                                                       key=lambda x: x[1]["sharpe_ratio"], 
                                                       reverse=True):
                        if authority.check_current_performance(alt_metrics):
                            decision["action"] = "RESUME"
                            decision["strategy_after"] = alt_name
                            current_strategy = alt_name
                            print(f"\n[+] DECISION: RESUME trading with {alt_name}")
                            break
                    else:
                        # No viable alternative
                        decision["action"] = "PAUSE"
                        decision["strategy_after"] = "PAUSED"
                        print(f"\n[PAUSED] DECISION: REMAIN PAUSED (no viable alternative)")
                else:
                    decision["action"] = "PAUSE"
                    decision["strategy_after"] = "PAUSED"
                    print(f"\n[PAUSED] DECISION: REMAIN PAUSED")
            else:
                decision["action"] = "PAUSE"
                decision["strategy_after"] = "PAUSED"
                current_strategy = "PAUSED"
                print(f"\n[!] DECISION: PAUSE TRADING")
        elif proposals:
            # Review proposals
            for proposal in proposals:
                auth_decision = authority.review_proposal(proposal)
                
                if auth_decision.verdict.value == "ACCEPT":
                    # Extract new strategy from proposal
                    if "alternative_strategy" in proposal.evidence:
                        new_strategy = proposal.evidence["alternative_strategy"]
                        decision["action"] = "SWITCH"
                        decision["strategy_after"] = new_strategy
                        current_strategy = new_strategy
                        print(f"\n[+] DECISION: SWITCH to {new_strategy}")
                        break
        else:
            print(f"\n[+] DECISION: CONTINUE with {current_strategy}")
        
        # Update capital based on actual performance
        current_capital = decision["capital_after"]
        
        evaluation_dates.append(eval_date)
        decisions.append(decision)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"ROLLING EVALUATION SUMMARY")
    print(f"{'='*70}")
    print(f"\nTotal Evaluations: {len(decisions)}")
    
    # Money metrics
    final_capital = decisions[-1]["capital_after"]
    total_profit = final_capital - initial_capital
    total_return_pct = (final_capital / initial_capital - 1) * 100
    
    print(f"\nMoney Performance:")
    print(f"  Initial Capital:  ${initial_capital:,.2f}")
    print(f"  Final Capital:    ${final_capital:,.2f}")
    print(f"  Total Profit:     ${total_profit:,.2f}")
    print(f"  Total Return:     {total_return_pct:.1f}%")
    
    # Count actions
    actions = [d["action"] for d in decisions]
    print(f"\nActions:")
    print(f"  CONTINUE: {actions.count('CONTINUE')}")
    print(f"  SWITCH:   {actions.count('SWITCH')}")
    print(f"  PAUSE:    {actions.count('PAUSE')}")
    
    # Show all decisions
    print(f"\n{'='*70}")
    print(f"DECISION LOG")
    print(f"{'='*70}")
    print(f"{'Date':<12} {'Action':<10} {'From':<6} {'To':<6} {'Sharpe':>8} {'Return':>8} {'Drawdown':>10}")
    print("-"*70)
    
    for d in decisions:
        print(f"{str(d['date'].date()):<12} {d['action']:<10} {d['strategy_before']:<6} {d['strategy_after']:<6} "
              f"{d['sharpe']:>8.2f} {d['return']*100:>7.1f}% {d['drawdown']*100:>9.1f}%")
    
    return decisions


def test_hourly_data():
    """
    Test with hourly data (last 60 days only due to Yahoo limits).
    This simulates continuous forex updates.
    """
    print("\n" + "="*70)
    print("TESTING WITH HOURLY DATA")
    print("="*70)
    
    fetcher = ForexDataFetcher()
    
    # Yahoo Finance allows hourly data for last ~730 days
    # Let's get last 60 days for testing
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    try:
        df = fetcher.fetch_pair(
            "EUR/USD",
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            interval="1h"
        )
        df = fetcher.add_technical_indicators(df)
        
        print(f"\nFetched {len(df)} hourly candles")
        print(f"Period: {df.index[0]} to {df.index[-1]}")
        
        # Test H3 on hourly data
        backtester = ForexBacktester(initial_capital=10000, max_hold_days=2)
        metrics = backtester.run_backtest(df, "EUR/USD", "H3")
        backtester.print_results(metrics)
        
    except Exception as e:
        print(f"\nHourly data not available: {e}")
        print("Using daily data instead (more reliable for historical testing)")


def main():
    print("="*70)
    print("FOREX HIGH-FREQUENCY IAI TEST")
    print("="*70)
    print("\nForex markets update continuously (24/5)")
    print("IAI must re-evaluate strategies frequently to adapt")
    print("\nThis test simulates:")
    print("  • Weekly re-evaluation (every 7 days)")
    print("  • Rolling 90-day performance window")
    print("  • Automatic strategy switching when better alternative appears")
    
    # Run rolling evaluation
    decisions = rolling_iai_evaluation(
        pair="EUR/USD",
        start_date="2022-01-01",
        end_date="2024-01-01",
        evaluation_window=90,
        re_eval_frequency=7,
        forward_window_days=7,  # With hourly data, 7 days = 168 candles
    )
    
    # Test hourly data capability
    test_hourly_data()
    
    print(f"\n{'='*70}")
    print(f"KEY INSIGHT")
    print(f"{'='*70}")
    print("\nWith {len(decisions)} evaluations over 2 years:")
    
    switches = [d for d in decisions if d["action"] == "SWITCH"]
    if switches:
        print(f"  ✓ IAI switched strategies {len(switches)} times")
        print(f"  ✓ Adapted to market regime changes")
    else:
        print(f"  ✓ Current strategy (H3) remained optimal throughout")
        print(f"  ✓ IAI validated this decision weekly")
    
    pauses = [d for d in decisions if d["action"] == "PAUSE"]
    if pauses:
        print(f"  [!] Trading paused {len(pauses)} times due to invariant violations")
    
    print(f"\nThis is continuous adaptation - not possible with static bots!")


if __name__ == "__main__":
    main()
