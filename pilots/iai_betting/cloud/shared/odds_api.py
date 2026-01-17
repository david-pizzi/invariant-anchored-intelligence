"""
Shared code - The Odds API integration for live fixtures and odds
==================================================================
Free tier: 500 requests/month (we use ~30-50)

Sign up at: https://the-odds-api.com/
"""

import logging
import os
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# The Odds API endpoint
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Supported leagues with their Odds API sport keys
LEAGUE_SPORTS = {
    "E0": {
        "sport_key": "soccer_epl",
        "name": "Premier League"
    },
    "D1": {
        "sport_key": "soccer_germany_bundesliga",
        "name": "Bundesliga"
    }
}

# Active leagues for tracking (matches ACTIVE_LEAGUES in data.py)
ACTIVE_LEAGUES = ["E0", "D1"]


def get_api_key():
    """Get API key from environment."""
    key = os.environ.get("ODDS_API_KEY")
    if not key:
        logger.warning("ODDS_API_KEY not set - using Football-Data.co.uk fallback")
    return key


def fetch_upcoming_fixtures_with_odds():
    """
    Fetch upcoming fixtures with odds for all active leagues.
    Returns list of matches with home team, away team, and odds.
    """
    api_key = get_api_key()
    if not api_key:
        return []
    
    all_matches = []
    for league_code in ACTIVE_LEAGUES:
        league_matches = fetch_league_fixtures(league_code, api_key)
        all_matches.extend(league_matches)
    
    logger.info(f"Fetched {len(all_matches)} upcoming fixtures across {len(ACTIVE_LEAGUES)} leagues")
    return all_matches


def fetch_league_fixtures(league_code: str, api_key: str):
    """Fetch upcoming fixtures for a specific league."""
    if league_code not in LEAGUE_SPORTS:
        logger.error(f"Unknown league: {league_code}")
        return []
    
    league_info = LEAGUE_SPORTS[league_code]
    sport_key = league_info["sport_key"]
    
    url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
    params = {
        "apiKey": api_key,
        "regions": "uk",  # UK bookmakers
        "markets": "h2h",  # Match winner (1X2)
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Log remaining quota
        remaining = response.headers.get('x-requests-remaining', 'unknown')
        used = response.headers.get('x-requests-used', 'unknown')
        logger.info(f"Odds API: {remaining} requests remaining ({used} used)")
        
        matches = []
        for event in data:
            match = parse_odds_event(event, league_code, league_info["name"])
            if match:
                matches.append(match)
        
        logger.info(f"Fetched {len(matches)} upcoming {league_info['name']} fixtures with odds")
        return matches
        
    except requests.RequestException as e:
        logger.error(f"Error fetching from Odds API: {e}")
        return []


def parse_odds_event(event, league_code: str = "E0", league_name: str = "Premier League"):
    """Parse a single event from The Odds API."""
    try:
        home_team = event.get('home_team', '')
        away_team = event.get('away_team', '')
        commence_time = event.get('commence_time', '')
        
        # Parse date
        if commence_time:
            dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            match_date = dt.strftime("%Y-%m-%d")
            match_time = dt.strftime("%H:%M")
        else:
            return None
        
        # Get best odds from available bookmakers
        home_odds = 0
        draw_odds = 0
        away_odds = 0
        
        bookmakers = event.get('bookmakers', [])
        for bookmaker in bookmakers:
            markets = bookmaker.get('markets', [])
            for market in markets:
                if market.get('key') == 'h2h':
                    outcomes = market.get('outcomes', [])
                    for outcome in outcomes:
                        name = outcome.get('name', '')
                        price = outcome.get('price', 0)
                        
                        if name == home_team:
                            home_odds = max(home_odds, price)
                        elif name == away_team:
                            away_odds = max(away_odds, price)
                        elif name == 'Draw':
                            draw_odds = max(draw_odds, price)
        
        if home_odds > 0:
            return {
                'date': match_date,
                'time': match_time,
                'home': home_team,
                'away': away_team,
                'home_odds': home_odds,
                'draw_odds': draw_odds,
                'away_odds': away_odds,
                'result': None,  # Upcoming match
                'source': 'odds_api',
                'league': league_code,
                'league_name': league_name
            }
        
        return None
        
    except Exception as e:
        logger.warning(f"Error parsing event: {e}")
        return None


def fetch_results():
    """
    Fetch recent results from all active leagues via The Odds API.
    """
    api_key = get_api_key()
    if not api_key:
        return []
    
    all_results = []
    for league_code in ACTIVE_LEAGUES:
        league_results = fetch_league_results(league_code, api_key)
        all_results.extend(league_results)
    
    logger.info(f"Fetched {len(all_results)} recent results across {len(ACTIVE_LEAGUES)} leagues")
    return all_results


def fetch_league_results(league_code: str, api_key: str):
    """Fetch recent results for a specific league."""
    if league_code not in LEAGUE_SPORTS:
        logger.error(f"Unknown league: {league_code}")
        return []
    
    league_info = LEAGUE_SPORTS[league_code]
    sport_key = league_info["sport_key"]
    
    url = f"{ODDS_API_BASE}/sports/{sport_key}/scores"
    params = {
        "apiKey": api_key,
        "daysFrom": 3,  # Last 3 days
        "dateFormat": "iso"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for event in data:
            if event.get('completed'):
                result = parse_result_event(event, league_code, league_info["name"])
                if result:
                    results.append(result)
        
        logger.info(f"Fetched {len(results)} recent {league_info['name']} results")
        return results
        
    except requests.RequestException as e:
        logger.error(f"Error fetching {league_info['name']} results: {e}")
        return []


def parse_result_event(event, league_code: str = "E0", league_name: str = "Premier League"):
    """Parse a completed match result."""
    try:
        home_team = event.get('home_team', '')
        away_team = event.get('away_team', '')
        commence_time = event.get('commence_time', '')
        
        # Parse date
        if commence_time:
            dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            match_date = dt.strftime("%Y-%m-%d")
        else:
            return None
        
        # Get scores
        scores = event.get('scores', [])
        home_score = 0
        away_score = 0
        
        for score in scores:
            if score.get('name') == home_team:
                home_score = int(score.get('score', 0))
            elif score.get('name') == away_team:
                away_score = int(score.get('score', 0))
        
        # Determine result
        if home_score > away_score:
            result = 'H'
        elif away_score > home_score:
            result = 'A'
        else:
            result = 'D'
        
        return {
            'date': match_date,
            'home': home_team,
            'away': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'result': result,
            'score': f"{home_score}-{away_score}",
            'league': league_code,
            'league_name': league_name
        }
        
    except Exception as e:
        logger.warning(f"Error parsing result: {e}")
        return None


def check_api_quota():
    """Check remaining API quota without using a request."""
    # This would require a request, so we just return info from last call
    # In practice, quota info is returned in response headers
    return {
        "note": "Quota info is returned in API response headers",
        "free_tier": "500 requests/month",
        "our_usage": "~30-50 requests/month"
    }
