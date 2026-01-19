"""
Validate IAI System - Test Full Implementation Locally
======================================================
Tests the complete IAI system against 9 seasons of historical data
WITHOUT touching the production cloud app.
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add iai_betting to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from iai_core.orchestrator import IAIOrchestrator
from iai_core.hypotheses import ALL_HYPOTHESES


def load_historical_data():
    """Load all historical football data."""
    data_dir = Path(__file__).parent.parent.parent.parent / "data" / "football"
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Load EPL and Bundesliga data
    leagues = {
        'E0': 'Premier League',
        'D1': 'Bundesliga'
    }
    
    all_matches = []
    
    for league_code, league_name in leagues.items():
        print(f"\nLoading {league_name} data...")
        
        # Find all files for this league
        files = sorted(data_dir.glob(f"{league_code}_*.csv"))
        
        for file in files:
            # Extract season from filename (e.g., E0_1920.csv -> 2019-20)
            season_code = file.stem.split('_')[1]
            if len(season_code) == 4:
                season = f"20{season_code[:2]}-{season_code[2:]}"
            else:
                season = "unknown"
            
            try:
                df = pd.read_csv(file)
                df['League'] = league_code
                df['LeagueName'] = league_name
                df['Season'] = season
                all_matches.append(df)
                print(f"  {season}: {len(df)} matches")
            except Exception as e:
                print(f"  Error loading {file.name}: {e}")
    
    if not all_matches:
        raise ValueError("No data loaded!")
    
    combined = pd.concat(all_matches, ignore_index=True)
    print(f"\nTotal matches loaded: {len(combined)}")
    
    # Ensure required columns exist
    required_cols = ['Date', 'HomeTeam', 'AwayTeam', 'FTR', 'B365H', 'B365D', 'B365A']
    missing = [col for col in required_cols if col not in combined.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Clean data
    combined = combined.dropna(subset=required_cols)
    print(f"After cleaning: {len(combined)} matches with complete data")
    
    return combined


def print_hypothesis_summary(hypotheses):
    """Print summary of all hypotheses."""
    print("\n" + "="*80)
    print("HYPOTHESIS DEFINITIONS")
    print("="*80)
    
    for h in hypotheses:
        print(f"\n{h.id}: {h.name}")
        print(f"  Description: {h.description}")
        print(f"  Strategy: {h.selection} @ {h.odds_min}-{h.odds_max} odds, {h.stake_pct}% stake")
        print(f"  Expected Edge: {h.expected_edge:.2f}%")
        print(f"  Status: {h.status}")


def print_evaluation_results(results):
    """Print detailed evaluation results."""
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80)
    
    for result in results:
        print(f"\n{result.hypothesis_id}: {result.hypothesis_name}")
        print(f"  Total Bets: {result.total_bets}")
        print(f"  Win Rate: {result.win_rate:.1f}% ({result.wins}W - {result.losses}L)")
        print(f"  Edge: {result.edge:.2f}% (CI: [{result.edge_ci_lower:.2f}%, {result.edge_ci_upper:.2f}%])")
        print(f"  ROI: {result.roi:.2f}%")
        print(f"  P-value: {result.p_value:.4f} {'✓ Significant' if result.is_significant else '✗ Not significant'}")
        print(f"  Stability: std={result.edge_std:.2f}% {'✓ Stable' if result.is_stable else '✗ Unstable'}")
        print(f"  Invariant: {'✓ PASSES' if result.passes_invariant else '✗ FAILS'}")
        print(f"  Recommendation: {result.recommendation}")


def print_authority_decisions(decisions):
    """Print Authority decisions with reasoning."""
    print("\n" + "="*80)
    print("AUTHORITY DECISIONS")
    print("="*80)
    
    for decision in decisions:
        print(f"\n{decision.hypothesis_id}: {decision.hypothesis_name}")
        print(f"  DECISION: {decision.decision}")
        print(f"  Reasoning:")
        for reason in decision.reasoning:
            print(f"    - {reason}")


def print_summary(orchestrator):
    """Print final summary."""
    report = orchestrator.generate_full_report()
    
    print("\n" + "="*80)
    print("IAI SYSTEM SUMMARY")
    print("="*80)
    
    print(f"\nChallenger Status:")
    print(f"  Total Hypotheses: {report['challenger']['total_hypotheses']}")
    print(f"  Proposed: {report['challenger']['proposed']}")
    print(f"  Evaluating: {report['challenger']['evaluating']}")
    print(f"  Accepted: {report['challenger']['accepted']}")
    print(f"  Rejected: {report['challenger']['rejected']}")
    print(f"  Deployed: {report['challenger']['deployed']}")
    
    print(f"\nAuthority Review:")
    print(f"  Total Decisions: {report['authority']['total_decisions']}")
    print(f"  Accepted: {report['authority']['accepted']}")
    print(f"  Rejected: {report['authority']['rejected']}")
    print(f"  Deferred: {report['authority']['deferred']}")
    if report['authority']['total_decisions'] > 0:
        print(f"  Acceptance Rate: {report['authority']['acceptance_rate']}")
    
    print(f"\nDeployment Ready: {report['deployment_ready']} hypotheses")
    
    # List deployment-ready hypotheses
    ready = orchestrator.get_deployment_ready_hypotheses()
    if ready:
        print("\nREADY FOR DEPLOYMENT:")
        for h in ready:
            print(f"  ✓ {h.id}: {h.name} (Edge: {h.evaluation_result['edge']:.2f}%)")


def main():
    """Run IAI validation."""
    print("="*80)
    print("IAI BETTING SYSTEM - LOCAL VALIDATION")
    print("Testing full Invariant-Anchored Intelligence implementation")
    print("="*80)
    
    # Load data
    print("\n[1/5] Loading historical data...")
    matches = load_historical_data()
    
    # Create orchestrator
    print("\n[2/5] Initializing IAI system...")
    orchestrator = IAIOrchestrator(
        invariant_edge=2.0,  # Require 2% edge minimum
        min_bets=30  # Require 30 bets for decision
    )
    
    # Show hypotheses
    print("\n[3/5] Reviewing hypotheses...")
    print_hypothesis_summary(ALL_HYPOTHESES)
    
    # Run evaluation cycle
    print("\n[4/5] Running evaluation cycle...")
    print("\nEvaluating all proposed hypotheses against historical data...")
    cycle_result = orchestrator.run_evaluation_cycle(matches, initial_bankroll=1000)
    
    print(f"\nCycle completed:")
    print(f"  Hypotheses evaluated: {cycle_result['hypotheses_evaluated']}")
    print(f"  Accepted: {cycle_result['summary']['accepted']}")
    print(f"  Rejected: {cycle_result['summary']['rejected']}")
    print(f"  Deferred: {cycle_result['summary']['deferred']}")
    
    # Print detailed results
    print_evaluation_results(orchestrator.evaluation_results)
    print_authority_decisions(orchestrator.authority_decisions)
    
    # Final summary
    print("\n[5/5] Generating summary...")
    print_summary(orchestrator)
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print("\n✓ IAI system tested locally against 9 seasons of historical data")
    print("✓ Production cloud app UNTOUCHED and still running")
    print("\nNext steps:")
    print("1. Review accepted hypotheses above")
    print("2. Compare with current baseline (H1)")
    print("3. If better strategies found, create cloud-v3/ for deployment")
    print("4. Keep cloud/ running until v3 validated")


if __name__ == "__main__":
    main()
