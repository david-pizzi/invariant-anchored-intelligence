"""
Shared code - Data fetching from Football-Data.co.uk
"""

import csv
import logging
import requests
from datetime import datetime
from io import StringIO

logger = logging.getLogger(__name__)

# Football-Data.co.uk current season URLs
LEAGUE_URLS = {
    "E0": {
        "name": "Premier League",
        "url": "https://www.football-data.co.uk/mmz4281/2526/E0.csv",
        "country": "England"
    },
    "D1": {
        "name": "Bundesliga",
        "url": "https://www.football-data.co.uk/mmz4281/2526/D1.csv",
        "country": "Germany"
    }
}

# Active leagues for tracking
ACTIVE_LEAGUES = ["E0", "D1"]


def fetch_matches():
    """Fetch current season matches from all active leagues."""
    all_matches = []
    for league_code in ACTIVE_LEAGUES:
        league_matches = fetch_league_matches(league_code)
        all_matches.extend(league_matches)
    logger.info(f"Fetched {len(all_matches)} total matches across {len(ACTIVE_LEAGUES)} leagues")
    return all_matches


def fetch_league_matches(league_code: str):
    """Fetch current season matches for a specific league."""
    if league_code not in LEAGUE_URLS:
        logger.error(f"Unknown league: {league_code}")
        return []
    
    league_info = LEAGUE_URLS[league_code]
    url = league_info["url"]
    logger.info(f"Fetching {league_info['name']} data from {url}")
    
    try:
        response = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=30
        )
        response.raise_for_status()
        content = response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {league_info['name']} data: {e}")
        return []
    
    # Parse CSV
    matches = []
    reader = csv.DictReader(StringIO(content))
    
    for row in reader:
        try:
            # Parse date (DD/MM/YYYY format)
            date_str = row.get('Date', '')
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    if len(year) == 2:
                        year = '20' + year
                    match_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    continue
            else:
                continue
            
            # Get odds (try multiple bookmakers)
            home_odds = 0
            for odds_col in ['B365H', 'BWH', 'IWH', 'PSH', 'WHH']:
                try:
                    home_odds = float(row.get(odds_col, 0) or 0)
                    if home_odds > 1:
                        break
                except ValueError:
                    continue
            
            # Get result if available
            result = row.get('FTR', '')
            
            matches.append({
                'date': match_date,
                'time': row.get('Time', '15:00'),
                'home': row.get('HomeTeam', ''),
                'away': row.get('AwayTeam', ''),
                'home_odds': home_odds,
                'result': result if result in ['H', 'D', 'A'] else None,
                'home_goals': row.get('FTHG', ''),
                'away_goals': row.get('FTAG', ''),
                'league': league_code,
                'league_name': league_info['name']
            })
        except (ValueError, KeyError) as e:
            logger.warning(f"Error parsing row: {e}")
            continue
    
    logger.info(f"Fetched {len(matches)} {league_info['name']} matches")
    return matches


def get_match_key(home, away, date):
    """Create unique key for a match."""
    return f"{date}_{home}_{away}".lower().replace(' ', '_')
