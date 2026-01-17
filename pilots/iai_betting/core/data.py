"""Data loading for UK Football betting.

Loads historical match data and odds from Football-Data.co.uk
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import urllib.request
import urllib.error


@dataclass
class BettingOdds:
    """Betting odds for a match."""
    # 1X2 odds (Home/Draw/Away)
    home_odds: float
    draw_odds: float
    away_odds: float
    
    # Implied probabilities
    @property
    def home_prob(self) -> float:
        return 1 / self.home_odds if self.home_odds > 0 else 0
    
    @property
    def draw_prob(self) -> float:
        return 1 / self.draw_odds if self.draw_odds > 0 else 0
    
    @property
    def away_prob(self) -> float:
        return 1 / self.away_odds if self.away_odds > 0 else 0
    
    @property
    def overround(self) -> float:
        """Bookmaker's margin (should be > 100%)."""
        return (self.home_prob + self.draw_prob + self.away_prob) * 100
    
    def fair_odds(self) -> "BettingOdds":
        """Return odds with overround removed."""
        total = self.home_prob + self.draw_prob + self.away_prob
        return BettingOdds(
            home_odds=total / self.home_prob if self.home_prob > 0 else 0,
            draw_odds=total / self.draw_prob if self.draw_prob > 0 else 0,
            away_odds=total / self.away_prob if self.away_prob > 0 else 0,
        )


@dataclass
class Match:
    """A football match with result and odds."""
    date: datetime
    home_team: str
    away_team: str
    
    # Result
    home_goals: int
    away_goals: int
    result: str  # "H", "D", "A"
    
    # Odds (from multiple bookmakers, we'll use Bet365 or average)
    odds: BettingOdds
    
    # Optional additional data
    league: str = ""
    season: str = ""
    
    @property
    def total_goals(self) -> int:
        return self.home_goals + self.away_goals
    
    @property
    def over_25(self) -> bool:
        return self.total_goals > 2.5
    
    def get_winner_odds(self) -> float:
        """Return odds of the actual winner."""
        if self.result == "H":
            return self.odds.home_odds
        elif self.result == "D":
            return self.odds.draw_odds
        else:
            return self.odds.away_odds


class FootballDataLoader:
    """
    Load historical football data from Football-Data.co.uk.
    
    This site provides free historical data including:
    - Match results
    - Closing odds from multiple bookmakers
    - Basic match statistics
    """
    
    # Football-Data.co.uk URLs
    BASE_URL = "https://www.football-data.co.uk/mmz4281"
    
    # League codes
    LEAGUES = {
        "E0": "Premier League",
        "E1": "Championship",
        "E2": "League One",
        "E3": "League Two",
        "SC0": "Scottish Premiership",
        "D1": "Bundesliga",
        "SP1": "La Liga",
        "I1": "Serie A",
        "F1": "Ligue 1",
    }
    
    def __init__(self, data_dir: str = "data/football"):
        """
        Initialize data loader.
        
        Args:
            data_dir: Directory to cache downloaded data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def download_season(
        self,
        league: str,
        season: str,
        force: bool = False,
    ) -> Path:
        """
        Download a season's data.
        
        Args:
            league: League code (e.g., "E0" for Premier League)
            season: Season string (e.g., "2324" for 2023-24)
            force: Force re-download even if file exists
            
        Returns:
            Path to downloaded CSV file
        """
        filename = f"{league}_{season}.csv"
        filepath = self.data_dir / filename
        
        if filepath.exists() and not force:
            print(f"✓ Using cached: {filename}")
            return filepath
        
        url = f"{self.BASE_URL}/{season}/{league}.csv"
        print(f"Downloading: {url}")
        
        try:
            # Add browser-like headers to avoid being blocked
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/csv,text/plain,*/*",
                    "Accept-Language": "en-GB,en;q=0.9",
                }
            )
            with urllib.request.urlopen(request) as response:
                content = response.read()
                
                # Validate it's actually CSV (not HTML error page)
                content_text = content.decode("utf-8", errors="ignore")[:200]
                if content_text.strip().startswith("<!DOCTYPE") or "<html" in content_text.lower():
                    print(f"✗ Got HTML instead of CSV (likely blocked by corporate firewall)")
                    raise ValueError("Download returned HTML (blocked by proxy/firewall)")
                
                with open(filepath, "wb") as f:
                    f.write(content)
            print(f"✓ Downloaded: {filename}")
        except urllib.error.HTTPError as e:
            print(f"✗ HTTP Error {e.code}: {e.reason}")
            raise
        except Exception as e:
            print(f"✗ Failed to download: {e}")
            raise
        
        return filepath
    
    def load_season(
        self,
        league: str,
        season: str,
        min_odds: float = 1.01,
    ) -> List[Match]:
        """
        Load a season's matches.
        
        Args:
            league: League code
            season: Season string
            min_odds: Minimum valid odds (filter out zeros/invalids)
            
        Returns:
            List of Match objects
        """
        filepath = self.download_season(league, season)
        matches = []
        
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    match = self._parse_row(row, league, season, min_odds)
                    if match:
                        matches.append(match)
                except Exception as e:
                    continue  # Skip invalid rows
        
        print(f"Loaded {len(matches)} matches from {league} {season}")
        return matches
    
    def _parse_row(
        self,
        row: Dict[str, str],
        league: str,
        season: str,
        min_odds: float,
    ) -> Optional[Match]:
        """Parse a CSV row into a Match object."""
        
        # Parse date (format varies by season)
        date_str = row.get("Date", "")
        date = self._parse_date(date_str)
        if not date:
            return None
        
        # Get result
        home_goals = int(row.get("FTHG", 0))
        away_goals = int(row.get("FTAG", 0))
        result = row.get("FTR", "")  # H, D, A
        
        if result not in ("H", "D", "A"):
            return None
        
        # Get odds - prefer Bet365, fallback to average or Pinnacle
        home_odds = self._get_odds(row, ["B365H", "BbAvH", "PSH", "WHH"])
        draw_odds = self._get_odds(row, ["B365D", "BbAvD", "PSD", "WHD"])
        away_odds = self._get_odds(row, ["B365A", "BbAvA", "PSA", "WHA"])
        
        # Validate odds
        if any(o < min_odds for o in [home_odds, draw_odds, away_odds]):
            return None
        
        return Match(
            date=date,
            home_team=row.get("HomeTeam", "Unknown"),
            away_team=row.get("AwayTeam", "Unknown"),
            home_goals=home_goals,
            away_goals=away_goals,
            result=result,
            odds=BettingOdds(
                home_odds=home_odds,
                draw_odds=draw_odds,
                away_odds=away_odds,
            ),
            league=self.LEAGUES.get(league, league),
            season=season,
        )
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date from various formats."""
        formats = [
            "%d/%m/%Y",
            "%d/%m/%y",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _get_odds(self, row: Dict[str, str], columns: List[str]) -> float:
        """Get odds from first available column."""
        for col in columns:
            try:
                value = float(row.get(col, 0))
                if value > 1.0:
                    return value
            except (ValueError, TypeError):
                continue
        return 0.0
    
    def load_multiple_seasons(
        self,
        league: str,
        seasons: List[str],
    ) -> List[Match]:
        """Load multiple seasons of data."""
        all_matches = []
        for season in seasons:
            try:
                matches = self.load_season(league, season)
                all_matches.extend(matches)
            except Exception as e:
                print(f"Failed to load {league} {season}: {e}")
        
        # If no matches loaded, try sample data
        if not all_matches:
            print("⚠️  No data from downloads. Looking for sample files...")
            all_matches = self._load_sample_data(league)
        
        # Sort by date
        all_matches.sort(key=lambda m: m.date)
        return all_matches
    
    def _load_sample_data(self, league: str) -> List[Match]:
        """Load sample data from local files (when downloads blocked)."""
        sample_files = list(self.data_dir.glob(f"{league}_*_sample.csv"))
        if not sample_files:
            # Try parent directory
            parent_sample = self.data_dir.parent / "football" / f"{league}_*_sample.csv"
            sample_files = list(Path(parent_sample.parent).glob(f"{league}_*_sample.csv"))
        
        matches = []
        for filepath in sample_files:
            try:
                loaded = self._load_csv_file(filepath, league, "sample")
                matches.extend(loaded)
                print(f"✓ Loaded {len(loaded)} matches from sample: {filepath.name}")
            except Exception as e:
                print(f"Failed to load sample {filepath}: {e}")
        
        return matches
    
    def _load_csv_file(
        self, 
        filepath: Path, 
        league: str, 
        season: str,
        min_odds: float = 1.01
    ) -> List[Match]:
        """Load matches from a CSV file."""
        matches = []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    match = self._parse_row(row, league, season, min_odds)
                    if match:
                        matches.append(match)
                except Exception:
                    continue
        return matches
    
    def get_available_seasons(self) -> List[str]:
        """Return list of typically available seasons."""
        # Football-Data typically has data from 1993 onwards
        # Format: YYMM where YY is start year, MM is end year
        return [
            "1920", "2021", "2122", "2223", "2324", "2425",
        ]
    
    def summary(self, matches: List[Match]) -> Dict[str, any]:
        """Generate summary statistics for loaded matches."""
        if not matches:
            return {}
        
        home_wins = sum(1 for m in matches if m.result == "H")
        draws = sum(1 for m in matches if m.result == "D")
        away_wins = sum(1 for m in matches if m.result == "A")
        
        avg_home_odds = sum(m.odds.home_odds for m in matches) / len(matches)
        avg_draw_odds = sum(m.odds.draw_odds for m in matches) / len(matches)
        avg_away_odds = sum(m.odds.away_odds for m in matches) / len(matches)
        
        return {
            "total_matches": len(matches),
            "date_range": f"{matches[0].date.date()} to {matches[-1].date.date()}",
            "home_wins": home_wins,
            "draws": draws,
            "away_wins": away_wins,
            "home_win_pct": home_wins / len(matches) * 100,
            "draw_pct": draws / len(matches) * 100,
            "away_win_pct": away_wins / len(matches) * 100,
            "avg_home_odds": avg_home_odds,
            "avg_draw_odds": avg_draw_odds,
            "avg_away_odds": avg_away_odds,
            "avg_overround": sum(m.odds.overround for m in matches) / len(matches),
        }


# Convenience function
def load_premier_league(seasons: List[str] = None) -> List[Match]:
    """Load Premier League data for specified seasons."""
    if seasons is None:
        seasons = ["2122", "2223", "2324"]
    
    loader = FootballDataLoader()
    return loader.load_multiple_seasons("E0", seasons)
