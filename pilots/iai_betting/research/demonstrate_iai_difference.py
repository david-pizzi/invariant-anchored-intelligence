"""
IAI Continuous Learning Demo
============================
Shows how IAI is NOT just "pick one strategy and stop" - 
it's a CONTINUOUS learning system that can adapt.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from iai_core.orchestrator import IAIOrchestrator
from iai_core.hypotheses import BettingHypothesis, ALL_HYPOTHESES
from research.validate_iai import load_historical_data


def simulate_market_shift():
    """
    Simulate what happens if market conditions change.
    
    IAI would detect this and switch strategies automatically.
    Production system would keep using the old strategy and lose money.
    """
    print("="*80)
    print("SCENARIO: Market Conditions Change")
    print("="*80)
    
    print("\nImagine bookmakers adjust their odds after 2 years...")
    print("They notice home underdogs @ 4-6 odds are being exploited")
    print("So they reduce those odds slightly, making that strategy unprofitable")
    print("\nWhat happens?")
    
    print("\n" + "-"*80)
    print("CURRENT PRODUCTION SYSTEM (No IAI):")
    print("-"*80)
    print("✗ Keeps betting Home @ 4-6 odds")
    print("✗ Doesn't detect edge has disappeared")
    print("✗ Loses money for months before you manually notice")
    print("✗ You have to manually research alternatives")
    print("✗ You have to manually code new strategy")
    print("✗ You have to manually deploy")
    
    print("\n" + "-"*80)
    print("IAI SYSTEM (Continuous Learning):")
    print("-"*80)
    print("✓ Re-evaluates all 8 hypotheses weekly")
    print("✓ Detects H1 edge dropped below 2%")
    print("✓ Authority REJECTS H1 automatically")
    print("✓ Evaluator finds H3 (Home Extreme 6-10) now has 4% edge")
    print("✓ Authority ACCEPTS H3")
    print("✓ System switches to H3 automatically")
    print("✓ Continues making money with new strategy")
    print("\nNo manual intervention needed!")


def demonstrate_multi_strategy():
    """Show that IAI can run multiple strategies simultaneously."""
    print("\n" + "="*80)
    print("IAI CAPABILITY: Multi-Strategy Portfolio")
    print("="*80)
    
    print("\nIAI doesn't have to pick ONE strategy - it can run MULTIPLE!")
    
    print("\nExample portfolio:")
    print("  • 60% bankroll → H1 (Home 4-6 odds) - Edge 3.3%")
    print("  • 30% bankroll → H3 (Home 6-10 odds) - Edge 2.5%")
    print("  • 10% bankroll → H7 (Away 6-10 odds) - Edge 1.0%")
    
    print("\nBenefits:")
    print("  ✓ Diversification - reduces variance")
    print("  ✓ More betting opportunities")
    print("  ✓ Exploits multiple market inefficiencies")
    print("  ✓ Authority continuously rebalances based on performance")


def demonstrate_hypothesis_generation():
    """Show how to dynamically generate new hypotheses."""
    print("\n" + "="*80)
    print("IAI CAPABILITY: Dynamic Hypothesis Generation")
    print("="*80)
    
    print("\nIAI can GENERATE new hypotheses based on patterns:")
    
    # Example: Generate hypotheses for different leagues
    leagues = ["E0", "E1", "E2", "D1", "D2", "F1", "I1", "SP1"]
    
    print("\nExample: League-specific strategies")
    new_hypotheses = []
    for league in leagues[:3]:  # Show first 3
        h = BettingHypothesis(
            id=f"H_LEAGUE_{league}",
            name=f"Home Underdogs in {league}",
            description=f"Home 4-6 odds specifically in {league}",
            selection="H",
            odds_min=4.0,
            odds_max=6.0,
            stake_pct=3.0,
            expected_edge=0.0,  # Unknown - to be discovered
            expected_win_rate=0.0,
            status="PROPOSED"
        )
        new_hypotheses.append(h)
        print(f"  ✓ {h.id}: {h.name}")
    
    print("\nIAI can also generate hypotheses for:")
    print("  • Time-based patterns (day of week, month, season)")
    print("  • Team-specific patterns (form, home/away record)")
    print("  • Odds movements (line shopping, steam moves)")
    print("  • Combination strategies (home underdog + total goals)")
    
    print("\nThe system tests EVERYTHING and keeps what works!")


def show_adaptation_cycle():
    """Show the continuous adaptation cycle."""
    print("\n" + "="*80)
    print("IAI CONTINUOUS CYCLE")
    print("="*80)
    
    print("""
    Week 1:
    ┌─────────────────────────────────────────────────────┐
    │ Deploy baseline: H1 (Home 4-6 odds)                │
    │ Track performance: Edge = 3.3%                     │
    └─────────────────────────────────────────────────────┘
    
    Week 2-5: Collect data
    ┌─────────────────────────────────────────────────────┐
    │ H1 performance: 12 bets, 3 wins, +£45               │
    │ Authority: Still ACCEPTED (within variance)        │
    └─────────────────────────────────────────────────────┘
    
    Week 6: Re-evaluation
    ┌─────────────────────────────────────────────────────┐
    │ Challenger proposes: Should we try H3?             │
    │ Evaluator tests H3 on last 20 matches              │
    │ Result: H3 edge = 4.2% > H1 edge = 2.8%           │
    │ Authority: ACCEPT H3, REDUCE H1 allocation         │
    │ New portfolio: 40% H1, 40% H3, 20% cash           │
    └─────────────────────────────────────────────────────┘
    
    Week 12: Continuous improvement
    ┌─────────────────────────────────────────────────────┐
    │ Challenger generates new hypothesis H9             │
    │ Based on pattern: "Home teams after 3+ losses"    │
    │ Evaluator tests on historical data                 │
    │ Edge = 5.1% - BEST EVER!                          │
    │ Authority: ACCEPT H9, make it 50% of portfolio    │
    └─────────────────────────────────────────────────────┘
    
    This happens AUTOMATICALLY, CONTINUOUSLY, FOREVER.
    """)


def compare_systems():
    """Direct comparison."""
    print("\n" + "="*80)
    print("PRODUCTION vs IAI: Side-by-Side")
    print("="*80)
    
    comparison = """
    ┌──────────────────────────────┬─────────────────────────┬─────────────────────────┐
    │ Capability                   │ Current Production      │ IAI System              │
    ├──────────────────────────────┼─────────────────────────┼─────────────────────────┤
    │ Strategy                     │ Fixed: Home @ 4-6 odds  │ Dynamic: Best of 8+     │
    ├──────────────────────────────┼─────────────────────────┼─────────────────────────┤
    │ Learns from data?            │ ✗ No                    │ ✓ Yes                   │
    ├──────────────────────────────┼─────────────────────────┼─────────────────────────┤
    │ Adapts to market changes?    │ ✗ No                    │ ✓ Yes                   │
    ├──────────────────────────────┼─────────────────────────┼─────────────────────────┤
    │ Tests alternatives?          │ ✗ No                    │ ✓ Yes (continuously)    │
    ├──────────────────────────────┼─────────────────────────┼─────────────────────────┤
    │ Detects edge disappearing?   │ ✗ No                    │ ✓ Yes (Authority check) │
    ├──────────────────────────────┼─────────────────────────┼─────────────────────────┤
    │ Multi-strategy?              │ ✗ No (single)           │ ✓ Yes (portfolio)       │
    ├──────────────────────────────┼─────────────────────────┼─────────────────────────┤
    │ Generates new hypotheses?    │ ✗ No                    │ ✓ Yes (Challenger)      │
    ├──────────────────────────────┼─────────────────────────┼─────────────────────────┤
    │ Statistical validation?      │ ✗ Manual only           │ ✓ Automatic (95% CI)    │
    ├──────────────────────────────┼─────────────────────────┼─────────────────────────┤
    │ Evidence-based decisions?    │ ✗ Human intuition       │ ✓ Authority + data      │
    ├──────────────────────────────┼─────────────────────────┼─────────────────────────┤
    │ Self-improving?              │ ✗ No                    │ ✓ Yes                   │
    └──────────────────────────────┴─────────────────────────┴─────────────────────────┘
    """
    print(comparison)


def main():
    print("="*80)
    print("IAI IS NOT 'PICK ONE STRATEGY AND STOP'")
    print("It's a Continuous Learning Intelligence System")
    print("="*80)
    
    simulate_market_shift()
    demonstrate_multi_strategy()
    demonstrate_hypothesis_generation()
    show_adaptation_cycle()
    compare_systems()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print("""
The IAI system you now have locally is FAR more sophisticated than production:

1. CURRENT PRODUCTION: 
   "Always bet Home @ 4-6 odds, hope it keeps working"
   
2. IAI SYSTEM:
   "Test 8+ strategies, pick the best, monitor continuously, switch when
    market changes, generate new ideas, keep improving forever"

RIGHT NOW, both say "use H1 (Home @ 4-6)" because that's empirically best.
But in 3 months, if H3 becomes better, IAI switches automatically.
Production would still be using H1 and losing money.

This is the difference between:
- Optimization: "I found a good rule"
- Intelligence: "I continuously discover the best rules"

Want me to show you how to deploy the continuous learning version?
    """)


if __name__ == "__main__":
    main()
