"""
Sentiment Data Fetcher for IAI Forex

Fetches retail sentiment data from IG and other sources.
When 75%+ of retail is positioned one way, we fade them.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import random

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass
class SentimentReading:
    """Single sentiment reading for a currency pair."""
    pair: str
    timestamp: datetime
    long_pct: float      # Percentage of retail traders LONG
    short_pct: float     # Percentage of retail traders SHORT
    source: str          # Data source (IG, Myfxbook, etc.)
    
    @property
    def extreme_long(self) -> bool:
        """Is retail extremely long? (Bearish signal)"""
        return self.long_pct >= 75
    
    @property
    def extreme_short(self) -> bool:
        """Is retail extremely short? (Bullish signal)"""
        return self.short_pct >= 75
    
    @property
    def signal(self) -> Optional[str]:
        """Trading signal based on sentiment."""
        if self.extreme_long:
            return "SHORT"
        elif self.extreme_short:
            return "LONG"
        return None
    
    @property
    def signal_strength(self) -> float:
        """How strong is the signal (0-1)."""
        extreme = max(self.long_pct, self.short_pct)
        if extreme < 75:
            return 0.0
        # Scale from 75-95% to 0-1
        return min((extreme - 75) / 20, 1.0)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        d['signal'] = self.signal
        d['signal_strength'] = self.signal_strength
        return d


class SentimentFetcher:
    """
    Fetches retail sentiment from various sources.
    
    Primary source: IG Client Sentiment (free, no API key needed)
    Backup: Myfxbook, DailyFX
    """
    
    # Major forex pairs we track
    PAIRS = [
        "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
        "AUD/USD", "USD/CAD", "NZD/USD",
        "EUR/GBP", "EUR/JPY", "GBP/JPY"
    ]
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent.parent / "data" / "sentiment_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_ig_sentiment(self) -> List[SentimentReading]:
        """
        Fetch current sentiment from IG.
        
        IG publishes client sentiment at:
        https://www.ig.com/uk/ig-client-sentiment
        """
        if not HAS_REQUESTS:
            print("⚠️  requests/beautifulsoup not installed. Using mock data.")
            return self._generate_mock_sentiment()
        
        try:
            url = "https://www.ig.com/uk/ig-client-sentiment"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return self._parse_ig_html(response.text)
            
        except Exception as e:
            print(f"⚠️  Failed to fetch IG sentiment: {e}")
            print("    Using cached or mock data instead.")
            return self._load_cached_or_mock()
    
    def _parse_ig_html(self, html: str) -> List[SentimentReading]:
        """Parse IG sentiment page HTML."""
        readings = []
        soup = BeautifulSoup(html, 'html.parser')
        timestamp = datetime.utcnow()
        
        # IG uses data attributes or specific classes for sentiment
        # This is a simplified parser - actual structure may vary
        sentiment_items = soup.find_all(class_=re.compile(r'sentiment|client-sentiment'))
        
        for item in sentiment_items:
            try:
                # Extract pair name and percentages
                pair_elem = item.find(class_=re.compile(r'instrument|pair|name'))
                long_elem = item.find(class_=re.compile(r'long|buy'))
                short_elem = item.find(class_=re.compile(r'short|sell'))
                
                if pair_elem and (long_elem or short_elem):
                    pair = pair_elem.get_text(strip=True)
                    
                    # Normalize pair name
                    pair = self._normalize_pair(pair)
                    if not pair:
                        continue
                    
                    # Extract percentages
                    long_pct = self._extract_percentage(long_elem)
                    short_pct = self._extract_percentage(short_elem)
                    
                    if long_pct is not None and short_pct is not None:
                        readings.append(SentimentReading(
                            pair=pair,
                            timestamp=timestamp,
                            long_pct=long_pct,
                            short_pct=short_pct,
                            source="IG"
                        ))
            except Exception:
                continue
        
        # Cache the results
        if readings:
            self._cache_readings(readings)
        
        return readings
    
    def _normalize_pair(self, pair_str: str) -> Optional[str]:
        """Normalize pair name to standard format."""
        pair_str = pair_str.upper().replace(" ", "").replace("-", "/")
        
        # Handle common variations
        mappings = {
            "EURUSD": "EUR/USD",
            "GBPUSD": "GBP/USD",
            "USDJPY": "USD/JPY",
            "USDCHF": "USD/CHF",
            "AUDUSD": "AUD/USD",
            "USDCAD": "USD/CAD",
            "NZDUSD": "NZD/USD",
            "EURGBP": "EUR/GBP",
            "EURJPY": "EUR/JPY",
            "GBPJPY": "GBP/JPY",
        }
        
        clean = pair_str.replace("/", "")
        return mappings.get(clean, pair_str if "/" in pair_str else None)
    
    def _extract_percentage(self, elem) -> Optional[float]:
        """Extract percentage from element."""
        if not elem:
            return None
        text = elem.get_text(strip=True)
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            return float(match.group(1))
        return None
    
    def _cache_readings(self, readings: List[SentimentReading]):
        """Cache readings to disk."""
        cache_file = self.cache_dir / f"sentiment_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
        data = [r.to_dict() for r in readings]
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_cached_or_mock(self) -> List[SentimentReading]:
        """Load most recent cached data or generate mock."""
        cache_files = sorted(self.cache_dir.glob("sentiment_*.json"), reverse=True)
        
        if cache_files:
            with open(cache_files[0]) as f:
                data = json.load(f)
                return [
                    SentimentReading(
                        pair=d['pair'],
                        timestamp=datetime.fromisoformat(d['timestamp']),
                        long_pct=d['long_pct'],
                        short_pct=d['short_pct'],
                        source=d['source']
                    )
                    for d in data
                ]
        
        return self._generate_mock_sentiment()
    
    def _generate_mock_sentiment(self) -> List[SentimentReading]:
        """Generate realistic mock sentiment for testing."""
        timestamp = datetime.utcnow()
        readings = []
        
        # Realistic sentiment patterns (retail is often wrong)
        mock_data = {
            "EUR/USD": (68, 32),   # Retail slightly long - bearish
            "GBP/USD": (82, 18),   # Retail very long - strong SHORT signal
            "USD/JPY": (35, 65),   # Retail short - no strong signal
            "USD/CHF": (45, 55),   # Neutral
            "AUD/USD": (78, 22),   # Retail long - SHORT signal
            "USD/CAD": (25, 75),   # Retail very short - LONG signal
            "NZD/USD": (71, 29),   # Near threshold
            "EUR/GBP": (58, 42),   # Neutral
            "EUR/JPY": (62, 38),   # Slightly long
            "GBP/JPY": (85, 15),   # Retail very long - strong SHORT signal
        }
        
        for pair, (long_pct, short_pct) in mock_data.items():
            # Add some randomness
            long_pct += random.uniform(-3, 3)
            short_pct = 100 - long_pct
            
            readings.append(SentimentReading(
                pair=pair,
                timestamp=timestamp,
                long_pct=round(long_pct, 1),
                short_pct=round(short_pct, 1),
                source="MOCK"
            ))
        
        return readings
    
    def get_signals(self) -> List[SentimentReading]:
        """
        Get current trading signals based on sentiment.
        Returns only pairs with extreme sentiment.
        """
        readings = self.fetch_ig_sentiment()
        return [r for r in readings if r.signal is not None]
    
    def print_current_sentiment(self):
        """Display current sentiment in table format."""
        readings = self.fetch_ig_sentiment()
        
        print("\n" + "=" * 70)
        print("RETAIL SENTIMENT (IG Client Positioning)")
        print("=" * 70)
        print(f"{'Pair':<12} {'Long %':>10} {'Short %':>10} {'Signal':>12} {'Strength':>10}")
        print("-" * 70)
        
        for r in sorted(readings, key=lambda x: -x.signal_strength):
            signal = r.signal or "-"
            strength = f"{r.signal_strength:.0%}" if r.signal else "-"
            marker = "🔴" if r.signal == "SHORT" else "🟢" if r.signal == "LONG" else "  "
            print(f"{marker} {r.pair:<10} {r.long_pct:>9.1f}% {r.short_pct:>9.1f}% {signal:>12} {strength:>10}")
        
        print("-" * 70)
        signals = [r for r in readings if r.signal]
        print(f"Signals: {len(signals)} pairs at extreme sentiment")
        print(f"Source: {readings[0].source if readings else 'N/A'}")
        print(f"Time: {readings[0].timestamp.strftime('%Y-%m-%d %H:%M UTC') if readings else 'N/A'}")
        print("=" * 70)


if __name__ == "__main__":
    fetcher = SentimentFetcher()
    fetcher.print_current_sentiment()
    
    print("\n📊 Trading Signals:")
    for signal in fetcher.get_signals():
        print(f"  {signal.pair}: {signal.signal} (strength: {signal.signal_strength:.0%})")
