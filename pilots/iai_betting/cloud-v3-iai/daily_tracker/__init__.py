"""
DAILY TRACKER - Azure Timer Function
=====================================
Runs every day at 18:00 UTC (after most PL matches finish).

1. Fetches upcoming fixtures with odds from The Odds API
2. Creates predictions for qualifying matches (Home @ 4.0-6.0)
3. Fetches results and checks pending predictions
4. Updates bankroll and saves to blob storage

Data sources:
- The Odds API: Upcoming fixtures with live odds (primary)
- Football-Data.co.uk: Historical results (fallback)
"""

import azure.functions as func
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.storage import (
    load_predictions, save_predictions, update_summary, STRATEGY
)
from shared.data import fetch_matches, get_match_key
from shared.odds_api import fetch_upcoming_fixtures_with_odds, fetch_results
from shared.authority import get_authority

logger = logging.getLogger(__name__)


def process_matches(data, matches, authority):
    """Process matches: add new predictions, check results."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    existing_keys = {
        get_match_key(p['home_team'], p['away_team'], p['match_date'])
        for p in data['predictions']
    }
    
    new_predictions = 0
    results_updated = 0
    
    for match in matches:
        match_key = get_match_key(match['home'], match['away'], match['date'])
        home_odds = match.get('home_odds', 0)

        # Check if qualifies for our strategy (needs valid odds)
        qualifies = home_odds > 1 and STRATEGY['odds_min'] <= home_odds <= STRATEGY['odds_max']

        # NEW PREDICTION: Match is upcoming and qualifies
        if match['date'] >= today and qualifies and match_key not in existing_keys:
            # Ask Authority for stake (may be reduced based on recent performance)
            stake, stake_reason = authority.calculate_stake(
                data['bankroll']['current'], 
                data['predictions']
            )
            
            # Authority may pause betting entirely
            if stake == 0:
                logger.info(f"SKIPPED by Authority: {match['home']} - {stake_reason}")
                continue
            
            potential_profit = stake * (home_odds - 1)
            
            prediction = {
                "id": len(data['predictions']) + 1,
                "created_at": datetime.utcnow().isoformat(),
                "match_date": match['date'],
                "match_time": match['time'] or "15:00",
                "home_team": match['home'],
                "away_team": match['away'],
                "league": match.get('league', 'E0'),
                "league_name": match.get('league_name', 'Premier League'),
                "selection": "H",
                "odds": home_odds,
                "qualifies": True,
                "stake": round(stake, 2),
                "stake_reason": stake_reason,
                "potential_profit": round(potential_profit, 2),
                "status": "pending",
                "result": None,
                "profit_loss": None
            }
            
            data['predictions'].append(prediction)
            existing_keys.add(match_key)
            new_predictions += 1
            logger.info(f"NEW: {match['home']} vs {match['away']} @ {home_odds}")
        
        # CHECK RESULT: Match has result and we have a pending prediction
        if match['result'] and match_key in existing_keys:
            for pred in data['predictions']:
                pred_key = get_match_key(
                    pred['home_team'], pred['away_team'], pred['match_date']
                )
                if pred_key == match_key and pred['status'] == 'pending':
                    if match['result'] == 'H':
                        # We won!
                        profit = pred['stake'] * (pred['odds'] - 1)
                        pred['status'] = 'won'
                        pred['result'] = 'H'
                        pred['profit_loss'] = round(profit, 2)
                        pred['settled_at'] = datetime.utcnow().isoformat()
                        pred['score'] = match.get('score', f"{match.get('home_goals', match.get('home_score', ''))}-{match.get('away_goals', match.get('away_score', ''))}")
                        logger.info(f"WON: {pred['home_team']} +£{profit:.2f}")
                    else:
                        # We lost
                        pred['status'] = 'lost'
                        pred['result'] = match['result']
                        pred['profit_loss'] = -pred['stake']
                        pred['settled_at'] = datetime.utcnow().isoformat()
                        pred['score'] = match.get('score', f"{match.get('home_goals', match.get('home_score', ''))}-{match.get('away_goals', match.get('away_score', ''))}")
                        logger.info(f"LOST: {pred['home_team']} -£{pred['stake']:.2f}")
                    
                    results_updated += 1
                    break
    
    return new_predictions, results_updated


def main(timer: func.TimerRequest) -> None:
    """Main function - runs on schedule."""
    run_time = datetime.utcnow().isoformat()
    logger.info(f"Daily tracker starting at {run_time}")
    
    try:
        # Initialize Authority
        authority = get_authority()
        
        # Load current state
        data = load_predictions()
        logger.info(f"Loaded {len(data['predictions'])} predictions")
        
        # Get Authority report
        authority_report = authority.generate_report(data['predictions'])
        logger.info(f"Authority status: {authority_report['status']} - {authority_report['stake_reason']}")
        
        # STEP 1: Fetch upcoming fixtures with odds from The Odds API
        upcoming = fetch_upcoming_fixtures_with_odds()
        logger.info(f"Fetched {len(upcoming)} upcoming fixtures with odds")
        
        # STEP 2: Fetch recent results from The Odds API
        results = fetch_results()
        logger.info(f"Fetched {len(results)} recent results")
        
        # STEP 3: Also fetch from Football-Data.co.uk (for any we missed)
        historical = fetch_matches()
        logger.info(f"Fetched {len(historical)} matches from Football-Data.co.uk")
        
        # Combine all matches
        all_matches = upcoming + results + historical
        
        if not all_matches:
            logger.warning("No match data available from any source")
            return
        
        # Process matches (Authority controls stake sizing)
        new_preds, updated = process_matches(data, all_matches, authority)
        logger.info(f"Processed: {new_preds} new predictions, {updated} results updated")
        
        # Update summary
        update_summary(data)
        
        # Store Authority report
        data['authority'] = authority_report
        
        # Log run
        data['run_history'] = data.get('run_history', [])
        data['run_history'].append({
            "timestamp": run_time,
            "sources": {
                "odds_api_upcoming": len(upcoming),
                "odds_api_results": len(results),
                "football_data": len(historical)
            },
            "new_predictions": new_preds,
            "results_updated": updated,
            "bankroll": data['bankroll']['current'],
            "authority_status": authority_report['status']
        })
        # Keep only last 30 runs
        data['run_history'] = data['run_history'][-30:]
        
        # Save
        save_predictions(data)
        
        logger.info(f"Completed. Bankroll: £{data['bankroll']['current']:.2f}")
        
    except Exception as e:
        logger.error(f"Error in daily tracker: {e}")
        raise
