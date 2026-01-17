"""Quick start script for IAI Betting pilot.

Run this to test the betting pilot on UK football data.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pilots.iai_betting.simulator import BettingSimulator, SimulationConfig
from pilots.iai_betting.strategies import (
    FlatBettingStrategy,
    KellyStrategy,
    FractionalKellyStrategy,
    IAIStrategy,
    SelectiveEdgeStrategy,
    UnderdogValueStrategy,
    train_edge_model,
)


def run_quick_test():
    """Run a quick test of the betting system."""
    
    print("="*70)
    print("IAI BETTING PILOT - QUICK TEST")
    print("="*70)
    
    # Configure for Premier League - more seasons for validation
    config = SimulationConfig(
        initial_bankroll=1000.0,
        leagues=["E0"],  # Premier League
        seasons=["1819", "1920", "2021", "2122", "2223", "2324"],  # 6 seasons for validation
        train_fraction=0.8,  # Use 80% for training, 20% for test
    )
    
    # Create simulator
    simulator = BettingSimulator(config)
    
    # Load data
    print("\n📊 Loading Premier League data...")
    train, test = simulator.load_data()
    
    # Train edge model on historical data
    print("\n🎓 Training edge model on historical data...")
    train_edge_model(train)
    
    # Show summary
    summary = simulator.get_data_summary()
    print(f"\n📈 Data Summary:")
    print(f"   Home win rate: {summary.get('home_win_pct', 0):.1f}%")
    print(f"   Draw rate: {summary.get('draw_pct', 0):.1f}%")
    print(f"   Away win rate: {summary.get('away_win_pct', 0):.1f}%")
    print(f"   Avg overround: {summary.get('avg_overround', 0):.1f}%")
    
    # Compare strategies with realistic settings
    print("\n🎯 Running strategy comparison...")
    strategies = [
        # Baseline: bet on everything
        FlatBettingStrategy(stake_fraction=0.02, min_edge=0.00),
        
        # Selective: only bet on proven profitable ranges
        SelectiveEdgeStrategy(stake_fraction=0.03, min_edge=0.02),
        
        # Targeted: home underdogs at 4.0-6.0 (highest edge in data)
        UnderdogValueStrategy(stake_fraction=0.05, min_odds=4.0, max_odds=6.0),
        
        # Also try home underdogs at 3.0-6.0 (wider range)
        UnderdogValueStrategy(stake_fraction=0.04, min_odds=3.0, max_odds=6.0),
        
        # Kelly with edge requirement
        FractionalKellyStrategy(kelly_fraction=0.25, min_edge=0.02),
        
        # IAI (default params)
        IAIStrategy(),
    ]
    
    results = simulator.compare_strategies(strategies)
    
    print("\n✅ Quick test complete!")
    print("\nNext steps:")
    print("  1. Run full IAI evolution: python run_iai_evolution.py")
    print("  2. Adjust parameters in strategies.py")
    print("  3. Try different leagues/seasons")
    
    return results


def run_full_evolution():
    """Run full IAI evolution (requires LLM)."""
    
    print("="*70)
    print("IAI BETTING PILOT - FULL EVOLUTION")
    print("="*70)
    
    try:
        from pilots.iai_betting.orchestrator import BettingOrchestrator
        
        # Create orchestrator
        orchestrator = BettingOrchestrator(
            model_alias="phi-3.5-mini",  # Or "qwen2.5-0.5b" for faster/smaller
            strictness="balanced",
        )
        
        # Run evolution
        results = orchestrator.run_full_experiment(
            max_generations=5,
            leagues=["E0"],
            seasons=["2122", "2223", "2324"],
        )
        
        return results
        
    except ImportError as e:
        print(f"\n⚠️  LLM dependencies not available: {e}")
        print("Run quick_test() instead, or install foundry-local-sdk")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="IAI Betting Pilot")
    parser.add_argument(
        "--mode",
        choices=["quick", "full"],
        default="quick",
        help="Test mode: 'quick' for strategy comparison, 'full' for IAI evolution"
    )
    
    args = parser.parse_args()
    
    if args.mode == "quick":
        run_quick_test()
    else:
        run_full_evolution()
