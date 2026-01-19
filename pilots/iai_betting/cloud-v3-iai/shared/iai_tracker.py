"""
IAI-Enhanced Betting Tracker
============================
Integrates continuous IAI evaluation with the betting tracker.

Every week:
1. Fetch new match data
2. Re-evaluate all hypotheses on rolling 6-month window
3. Authority reviews and selects best strategy(ies)
4. Update active strategy if needed
5. Place bets with current best strategy
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

from .iai_core.orchestrator import IAIOrchestrator
from .iai_core.hypotheses import ALL_HYPOTHESES
from .storage import load_predictions, save_predictions, STRATEGY
from .data import load_recent_matches


def should_run_iai_evaluation(predictions: Dict) -> bool:
    """
    Determine if we should run full IAI evaluation.
    
    Run weekly (every 7 days since last evaluation).
    """
    last_eval = predictions.get('iai_last_evaluation')
    
    if not last_eval:
        return True
    
    last_eval_date = datetime.fromisoformat(last_eval)
    days_since = (datetime.utcnow() - last_eval_date).days
    
    return days_since >= 7


def run_iai_evaluation(predictions: Dict) -> Dict[str, Any]:
    """
    Run full IAI evaluation cycle and update active strategy.
    
    Returns:
        dict with evaluation results and any strategy changes
    """
    logging.info("Running IAI evaluation cycle...")
    
    # Load historical data for evaluation (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    try:
        # Load recent matches from football-data.co.uk
        matches_df = load_recent_matches(since_date=six_months_ago)
        
        if len(matches_df) < 100:
            logging.warning(f"Insufficient data for IAI evaluation ({len(matches_df)} matches)")
            return {
                'status': 'SKIPPED',
                'reason': 'Insufficient historical data',
                'matches_available': len(matches_df)
            }
        
        # Create orchestrator
        orchestrator = IAIOrchestrator(invariant_edge=2.0, min_bets=30)
        
        # Run evaluation cycle
        cycle_result = orchestrator.run_evaluation_cycle(
            matches_df, 
            initial_bankroll=predictions['bankroll']
        )
        
        # Get best accepted hypothesis
        accepted = orchestrator.get_deployment_ready_hypotheses()
        
        current_strategy_id = predictions.get('active_strategy_id', 'H1')
        
        if accepted:
            # Sort by edge and pick best
            best = max(accepted, key=lambda h: h.evaluation_result['edge'])
            best_id = best.id
            best_edge = best.evaluation_result['edge']
            
            # Check if we should switch
            if best_id != current_strategy_id:
                logging.info(f"IAI ADAPTATION: {current_strategy_id} → {best_id}")
                logging.info(f"New edge: {best_edge:.2f}%")
                
                # Update predictions with new strategy
                predictions['active_strategy_id'] = best_id
                predictions['active_strategy'] = {
                    'id': best.id,
                    'name': best.name,
                    'selection': best.selection,
                    'odds_min': best.odds_min,
                    'odds_max': best.odds_max,
                    'stake_pct': best.stake_pct,
                    'edge': best_edge
                }
                
                adaptation_record = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'from': current_strategy_id,
                    'to': best_id,
                    'reason': f"Edge improved: {best_edge:.2f}%",
                    'evaluation': cycle_result
                }
                
                # Track adaptations
                if 'iai_adaptations' not in predictions:
                    predictions['iai_adaptations'] = []
                predictions['iai_adaptations'].append(adaptation_record)
                
                return {
                    'status': 'ADAPTED',
                    'from': current_strategy_id,
                    'to': best_id,
                    'new_edge': best_edge,
                    'cycle_result': cycle_result
                }
            else:
                logging.info(f"IAI: Keeping {current_strategy_id} (still optimal)")
                return {
                    'status': 'UNCHANGED',
                    'strategy': current_strategy_id,
                    'edge': best_edge,
                    'cycle_result': cycle_result
                }
        else:
            # No hypothesis passed Authority review!
            logging.warning("IAI: NO hypotheses passed Authority review")
            logging.warning("This means ALL strategies have insufficient edge")
            logging.warning("Consider STOPPING betting until edge returns")
            
            # Mark current strategy as under review
            predictions['active_strategy_warning'] = "No strategy currently meets invariant (edge > 2%)"
            
            return {
                'status': 'NO_EDGE',
                'warning': 'All strategies failed Authority review',
                'recommendation': 'STOP BETTING',
                'cycle_result': cycle_result
            }
    
    except Exception as e:
        logging.error(f"IAI evaluation failed: {e}")
        return {
            'status': 'ERROR',
            'error': str(e)
        }


def get_active_strategy(predictions: Dict) -> Dict[str, Any]:
    """
    Get the currently active strategy from IAI or fall back to baseline.
    
    Returns:
        dict with strategy parameters
    """
    active = predictions.get('active_strategy')
    
    if active:
        return active
    
    # Fallback to baseline
    return {
        'id': 'H1',
        'name': 'Baseline: Home Underdogs',
        'selection': 'H',
        'odds_min': 4.0,
        'odds_max': 6.0,
        'stake_pct': 3.0,
        'edge': 5.18  # Historical
    }


def track_with_iai(upcoming_matches: List[Dict], results: List[Dict], 
                   bankroll: float) -> Dict[str, Any]:
    """
    Main IAI-enhanced tracking function.
    
    1. Load predictions
    2. Check if IAI evaluation needed
    3. Run evaluation if needed
    4. Get active strategy
    5. Place bets with active strategy
    6. Update results
    7. Save predictions
    
    Returns:
        dict with tracking summary
    """
    # Load current state
    predictions = load_predictions()
    
    if not predictions:
        predictions = {
            'bankroll': bankroll,
            'bets': [],
            'active_strategy_id': 'H1',
            'iai_last_evaluation': None,
            'iai_adaptations': []
        }
    
    # Check if IAI evaluation needed
    iai_result = None
    if should_run_iai_evaluation(predictions):
        iai_result = run_iai_evaluation(predictions)
        predictions['iai_last_evaluation'] = datetime.utcnow().isoformat()
        predictions['iai_last_result'] = iai_result
    
    # Get active strategy
    strategy = get_active_strategy(predictions)
    
    logging.info(f"Active strategy: {strategy['id']} - {strategy['name']}")
    logging.info(f"Edge: {strategy['edge']:.2f}%")
    
    # Rest of tracking logic uses strategy parameters...
    # (This integrates with existing tracker code)
    
    return {
        'iai_evaluation': iai_result,
        'active_strategy': strategy,
        'predictions': predictions
    }
