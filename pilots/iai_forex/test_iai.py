"""
Run IAI-enhanced forex trading with adaptive strategy selection.
"""

import sys
from pathlib import Path

# Add pilots directory to path
pilot_dir = Path(__file__).parent
sys.path.insert(0, str(pilot_dir.parent.parent))

from pilots.iai_forex.core.data_fetcher import ForexDataFetcher
from pilots.iai_forex.core.strategies import get_strategy, STRATEGIES
from pilots.iai_forex.research.backtest import ForexBacktester
from pilots.iai_forex.iai.authority import ForexAuthority
from pilots.iai_forex.iai.challenger import ForexChallenger
from pilots.iai_forex.iai.evaluator import ForexEvaluator


def run_iai_forex(
    pair: str = "EUR/USD",
    start_date: str = "2020-01-01",
    end_date: str = "2024-01-01",
    initial_strategy: str = "H3",
):
    """
    Run IAI-enhanced forex trading.
    
    Process:
    1. Load data
    2. Test current strategy
    3. Evaluator measures performance
    4. Challenger tests alternatives
    5. Authority decides: CONTINUE, SWITCH, or PAUSE
    """
    print("="*70)
    print("IAI FOREX TRADING SYSTEM")
    print("="*70)
    
    # Initialize components
    authority = ForexAuthority(
        min_sharpe=1.5,
        max_drawdown=0.15,
        min_win_rate=0.45,
    )
    
    challenger = ForexChallenger(
        evaluation_window=60,
        improvement_threshold=0.3,  # 30% better required
    )
    
    evaluator = ForexEvaluator()
    
    # Fetch data
    print(f"\nFetching {pair} data...")
    fetcher = ForexDataFetcher()
    df = fetcher.fetch_pair(pair, start_date, end_date, "1d")
    df = fetcher.add_technical_indicators(df)
    print(f"Loaded {len(df)} daily candles")
    
    # Test current strategy
    print(f"\n{'='*70}")
    print(f"TESTING CURRENT STRATEGY: {initial_strategy}")
    print(f"{'='*70}")
    
    backtester = ForexBacktester(initial_capital=10000)
    current_metrics = backtester.run_backtest(df, pair, initial_strategy)
    backtester.print_results(current_metrics)
    
    # Add strategy name to metrics
    current_metrics["strategy"] = initial_strategy
    
    # Test alternative strategies
    print(f"\n{'='*70}")
    print(f"TESTING ALTERNATIVE STRATEGIES")
    print(f"{'='*70}")
    
    alternatives = {}
    for strat_name in STRATEGIES.keys():
        if strat_name == initial_strategy:
            continue
        
        print(f"\nTesting {strat_name}...")
        alt_backtester = ForexBacktester(initial_capital=10000)
        alt_metrics = alt_backtester.run_backtest(df, pair, strat_name)
        
        if "error" not in alt_metrics:
            alternatives[strat_name] = alt_metrics
            print(f"  Sharpe: {alt_metrics['sharpe_ratio']:.2f}, "
                  f"Return: {alt_metrics['total_return']*100:.1f}%, "
                  f"Drawdown: {alt_metrics['max_drawdown']*100:.1f}%")
    
    current_metrics["alternatives"] = alternatives
    
    # Challenger detects strain
    from iai_core.types import Invariants
    invariants = Invariants(primary_metric="sharpe_ratio")  # Set primary metric
    
    proposals = challenger.detect_strain(
        current_metrics=current_metrics,
        historical_metrics=[],
        invariants=invariants,
    )
    
    # Authority reviews proposals
    if len(proposals) == 0:
        print(f"\n{'='*70}")
        print(f"NO PROPOSALS - CONTINUE WITH {initial_strategy}")
        print(f"{'='*70}")
        
        # Still check if current strategy meets invariants
        should_continue = authority.check_current_performance(current_metrics)
        
        if should_continue:
            print(f"\n✅ FINAL DECISION: Continue trading with {initial_strategy}")
        else:
            print(f"\n⚠️  FINAL DECISION: PAUSE trading (invariants violated)")
    else:
        print(f"\n{'='*70}")
        print(f"REVIEWING {len(proposals)} PROPOSAL(S)")
        print(f"{'='*70}")
        
        for proposal in proposals:
            decision = authority.review_proposal(proposal)
            
            print(f"\nProposal: {proposal.description}")
            print(f"Verdict: {decision.verdict.value}")
            print(f"Reasoning: {decision.reasoning}")
            
            if decision.verdict.value == "ACCEPT":
                print(f"\n✅ FINAL DECISION: {proposal.description}")
                break
        else:
            print(f"\n⚠️  FINAL DECISION: All proposals rejected - continue with {initial_strategy}")
    
    # Market regime analysis
    regime = challenger.analyze_regime(df)
    print(f"\n{'='*70}")
    print(f"MARKET REGIME ANALYSIS")
    print(f"{'='*70}")
    print(f"Regime:         {regime['regime']}")
    print(f"Volatility:     {regime['volatility']*100:.1f}%")
    print(f"Trend Strength: {regime['trend_strength']*100:.1f}%")
    print(f"ATR Regime:     {regime['atr_regime']}")
    
    return current_metrics, alternatives, proposals


def main():
    """Run IAI forex with EUR/USD."""
    metrics, alternatives, proposals = run_iai_forex(
        pair="EUR/USD",
        start_date="2020-01-01",
        end_date="2024-01-01",
        initial_strategy="H3",  # Start with best strategy
    )
    
    print(f"\n{'='*70}")
    print(f"IAI SYSTEM COMPLETE")
    print(f"{'='*70}")
    print(f"\nThe system has:")
    print(f"  ✓ Evaluated current strategy (H3)")
    print(f"  ✓ Tested alternatives (H1, H2, H4)")
    print(f"  ✓ Challenger detected strain (or not)")
    print(f"  ✓ Authority reviewed proposals")
    print(f"  ✓ Made evidence-based decision")
    print(f"\nThis is the IAI loop in action!")


if __name__ == "__main__":
    main()
