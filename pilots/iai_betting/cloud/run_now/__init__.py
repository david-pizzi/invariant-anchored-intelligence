"""
RUN NOW - Manual trigger for daily tracker
==========================================
POST to this endpoint to run the tracker immediately.
Useful for testing or when you want to update outside schedule.
"""

import azure.functions as func
import logging
import json
import sys
from datetime import datetime
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.storage import load_predictions, save_predictions, update_summary, STRATEGY
from shared.data import fetch_matches, get_match_key
from shared.odds_api import fetch_upcoming_fixtures_with_odds, fetch_results
from shared.authority import get_authority

logger = logging.getLogger(__name__)


def process_matches(data, matches, authority):
    """Process matches - same as daily_tracker."""
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
        
        if home_odds <= 1:
            continue
        
        qualifies = STRATEGY['odds_min'] <= home_odds <= STRATEGY['odds_max']
        
        if match['date'] >= today and qualifies and match_key not in existing_keys:
            # Ask Authority for stake
            stake, stake_reason = authority.calculate_stake(
                data['bankroll']['current'], 
                data['predictions']
            )
            
            # Authority may pause betting
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
        
        if match['result'] and match_key in existing_keys:
            for pred in data['predictions']:
                pred_key = get_match_key(
                    pred['home_team'], pred['away_team'], pred['match_date']
                )
                if pred_key == match_key and pred['status'] == 'pending':
                    if match['result'] == 'H':
                        profit = pred['stake'] * (pred['odds'] - 1)
                        pred['status'] = 'won'
                        pred['result'] = 'H'
                        pred['profit_loss'] = round(profit, 2)
                        pred['settled_at'] = datetime.utcnow().isoformat()
                        pred['score'] = f"{match['home_goals']}-{match['away_goals']}"
                    else:
                        pred['status'] = 'lost'
                        pred['result'] = match['result']
                        pred['profit_loss'] = -pred['stake']
                        pred['settled_at'] = datetime.utcnow().isoformat()
                        pred['score'] = f"{match['home_goals']}-{match['away_goals']}"
                    
                    results_updated += 1
                    break
    
    return new_predictions, results_updated


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Manual trigger endpoint."""
    logger.info("Manual run triggered")
    
    try:
        run_time = datetime.utcnow().isoformat()
        
        # Initialize Authority
        authority = get_authority()
        
        # Load current state
        data = load_predictions()
        
        # Get Authority report
        authority_report = authority.generate_report(data['predictions'])
        
        # Fetch from multiple sources
        upcoming = fetch_upcoming_fixtures_with_odds()
        results = fetch_results()
        historical = fetch_matches()
        
        # Combine all matches
        all_matches = upcoming + results + historical
        
        sources_info = {
            "odds_api_upcoming": len(upcoming),
            "odds_api_results": len(results),
            "football_data": len(historical)
        }
        
        if not all_matches:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "No match data available from any source"}),
                mimetype="application/json",
                status_code=500
            )
        
        new_preds, updated = process_matches(data, all_matches, authority)
        update_summary(data)
        
        # Log run
        data['run_history'] = data.get('run_history', [])
        data['run_history'].append({
            "timestamp": run_time,
            "trigger": "manual",
            "new_predictions": new_preds,
            "results_updated": updated,
            "bankroll": data['bankroll']['current'],
            "authority_status": authority_report['status']
        })
        data['run_history'] = data['run_history'][-30:]
        
        # Store Authority report
        data['authority_report'] = authority_report
        
        save_predictions(data)
        
        result = {
            "status": "success",
            "timestamp": run_time,
            "sources": sources_info,
            "new_predictions": new_preds,
            "results_updated": updated,
            "bankroll": data['bankroll']['current'],
            "summary": data['results_summary'],
            "authority": authority_report
        }
        
        return func.HttpResponse(
            json.dumps(result, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error in manual run: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )
