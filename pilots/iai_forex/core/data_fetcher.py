"""
Fetch historical forex data from free sources.
Uses yfinance for historical OHLC data.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


class ForexDataFetcher:
    """Fetch and cache forex data."""
    
    # Yahoo Finance forex symbols
    PAIRS = {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "USDJPY=X",
        "AUD/USD": "AUDUSD=X",
        "USD/CAD": "USDCAD=X",
        "NZD/USD": "NZDUSD=X",
        "EUR/GBP": "EURGBP=X",
        "EUR/JPY": "EURJPY=X",
    }
    
    def __init__(self, cache_dir: str = "data/forex"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_pair(
        self, 
        pair: str, 
        start_date: str = "2020-01-01",
        end_date: str = None,
        interval: str = "1h"  # 1m, 5m, 15m, 30m, 1h, 1d
    ) -> pd.DataFrame:
        """
        Fetch OHLC data for a forex pair.
        
        Args:
            pair: Forex pair (e.g., "EUR/USD")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), default today
            interval: Data interval
            
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Check cache
        cache_file = self.cache_dir / f"{pair.replace('/', '')}_{interval}_{start_date}_{end_date}.csv"
        if cache_file.exists():
            print(f"Loading {pair} from cache: {cache_file}")
            return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        
        # Fetch from Yahoo Finance
        symbol = self.PAIRS.get(pair)
        if not symbol:
            raise ValueError(f"Unknown pair: {pair}. Available: {list(self.PAIRS.keys())}")
        
        print(f"Fetching {pair} ({symbol}) from {start_date} to {end_date}...")
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            # Try daily data if hourly fails (yfinance has limited hourly history)
            if interval != "1d":
                print(f"  ⚠️  Hourly data not available, falling back to daily candles...")
                df = ticker.history(start=start_date, end=end_date, interval="1d")
            
            if df.empty:
                raise ValueError(f"No data returned for {pair}")
        
        # Save to cache
        df.to_csv(cache_file)
        print(f"Saved to cache: {cache_file}")
        print(f"Fetched {len(df)} candles")
        
        return df
    
    def fetch_multiple_pairs(
        self,
        pairs: list,
        start_date: str = "2020-01-01",
        end_date: str = None,
        interval: str = "1h"
    ) -> dict:
        """Fetch data for multiple pairs."""
        data = {}
        for pair in pairs:
            try:
                data[pair] = self.fetch_pair(pair, start_date, end_date, interval)
            except Exception as e:
                print(f"Error fetching {pair}: {e}")
        return data
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add common technical indicators."""
        # Simple Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # Bollinger Bands
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (2 * bb_std)
        df['BB_lower'] = df['BB_middle'] - (2 * bb_std)
        
        # ATR (Average True Range)
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        
        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Momentum
        df['Momentum'] = df['Close'] - df['Close'].shift(10)
        
        # Volume-weighted average (if volume available)
        if 'Volume' in df.columns and df['Volume'].sum() > 0:
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        
        return df


if __name__ == "__main__":
    # Test data fetching
    fetcher = ForexDataFetcher()
    
    print("="*70)
    print("FOREX DATA FETCHER TEST")
    print("="*70)
    
    # Fetch EUR/USD hourly data
    df = fetcher.fetch_pair(
        "EUR/USD",
        start_date="2023-01-01",
        end_date="2024-01-01",
        interval="1h"
    )
    
    print(f"\nData shape: {df.shape}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    print(f"\nLast 5 rows:")
    print(df.tail())
    
    # Add indicators
    print("\nAdding technical indicators...")
    df = fetcher.add_technical_indicators(df)
    print(f"Columns: {df.columns.tolist()}")
    
    print("\n✓ Data fetcher working!")
