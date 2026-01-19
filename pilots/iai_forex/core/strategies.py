"""
Forex trading strategies.
Each strategy generates BUY/SELL/HOLD signals.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Literal


@dataclass
class Signal:
    """Trading signal."""
    timestamp: pd.Timestamp
    pair: str
    direction: Literal["BUY", "SELL", "HOLD"]
    strength: float  # 0-1
    strategy: str
    entry_price: float
    stop_loss: float = None
    take_profit: float = None
    metadata: dict = None


class BaseStrategy:
    """Base class for trading strategies."""
    
    def __init__(self, name: str):
        self.name = name
    
    def generate_signals(self, df: pd.DataFrame, pair: str) -> list[Signal]:
        """Generate trading signals from OHLC data."""
        raise NotImplementedError


class MomentumBreakout(BaseStrategy):
    """
    H1: Momentum Breakout Strategy
    Entry: Price crosses 20 SMA with strong momentum
    """
    
    def __init__(self, ma_period: int = 20, momentum_threshold: float = 0.0015):
        super().__init__("H1_MomentumBreakout")
        self.ma_period = ma_period
        self.momentum_threshold = momentum_threshold
    
    def generate_signals(self, df: pd.DataFrame, pair: str) -> list[Signal]:
        signals = []
        
        # Need SMA and momentum
        if 'SMA_20' not in df.columns:
            return signals
        
        for i in range(1, len(df)):
            timestamp = df.index[i]
            close = df.iloc[i]['Close']
            prev_close = df.iloc[i-1]['Close']
            sma = df.iloc[i]['SMA_20']
            atr = df.iloc[i].get('ATR', close * 0.01)
            
            # Momentum as percentage change
            momentum = (close - prev_close) / prev_close
            
            # Bullish: Price crosses above SMA with strong upward momentum
            if close > sma and prev_close <= df.iloc[i-1]['SMA_20'] and momentum > self.momentum_threshold:
                signals.append(Signal(
                    timestamp=timestamp,
                    pair=pair,
                    direction="BUY",
                    strength=min(abs(momentum) / self.momentum_threshold, 1.0),
                    strategy=self.name,
                    entry_price=close,
                    stop_loss=close - (2 * atr),
                    take_profit=close + (3 * atr),
                ))
            
            # Bearish: Price crosses below SMA with strong downward momentum
            elif close < sma and prev_close >= df.iloc[i-1]['SMA_20'] and momentum < -self.momentum_threshold:
                signals.append(Signal(
                    timestamp=timestamp,
                    pair=pair,
                    direction="SELL",
                    strength=min(abs(momentum) / self.momentum_threshold, 1.0),
                    strategy=self.name,
                    entry_price=close,
                    stop_loss=close + (2 * atr),
                    take_profit=close - (3 * atr),
                ))
        
        return signals


class MeanReversion(BaseStrategy):
    """
    H2: Mean Reversion Strategy
    Entry: Price touches Bollinger Band extremes with RSI oversold/overbought
    """
    
    def __init__(self, rsi_oversold: float = 30, rsi_overbought: float = 70):
        super().__init__("H2_MeanReversion")
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
    
    def generate_signals(self, df: pd.DataFrame, pair: str) -> list[Signal]:
        signals = []
        
        if 'BB_lower' not in df.columns or 'RSI' not in df.columns:
            return signals
        
        for i in range(1, len(df)):
            timestamp = df.index[i]
            close = df.iloc[i]['Close']
            bb_lower = df.iloc[i]['BB_lower']
            bb_upper = df.iloc[i]['BB_upper']
            bb_middle = df.iloc[i]['BB_middle']
            rsi = df.iloc[i]['RSI']
            
            # Skip if NaN
            if pd.isna(rsi) or pd.isna(bb_lower):
                continue
            
            # Bullish: Touch lower BB + RSI oversold
            if close <= bb_lower and rsi < self.rsi_oversold:
                signals.append(Signal(
                    timestamp=timestamp,
                    pair=pair,
                    direction="BUY",
                    strength=(self.rsi_oversold - rsi) / self.rsi_oversold,
                    strategy=self.name,
                    entry_price=close,
                    stop_loss=close - (bb_middle - bb_lower),
                    take_profit=bb_middle,
                ))
            
            # Bearish: Touch upper BB + RSI overbought
            elif close >= bb_upper and rsi > self.rsi_overbought:
                signals.append(Signal(
                    timestamp=timestamp,
                    pair=pair,
                    direction="SELL",
                    strength=(rsi - self.rsi_overbought) / (100 - self.rsi_overbought),
                    strategy=self.name,
                    entry_price=close,
                    stop_loss=close + (bb_upper - bb_middle),
                    take_profit=bb_middle,
                ))
        
        return signals


class VolatilityBreakout(BaseStrategy):
    """
    H3: Volatility Breakout Strategy
    Entry: Low volatility followed by directional move
    """
    
    def __init__(self, atr_low_threshold: float = 0.5, breakout_factor: float = 1.5):
        super().__init__("H3_VolatilityBreakout")
        self.atr_low_threshold = atr_low_threshold
        self.breakout_factor = breakout_factor
    
    def generate_signals(self, df: pd.DataFrame, pair: str) -> list[Signal]:
        signals = []
        
        if 'ATR' not in df.columns:
            return signals
        
        # Calculate ATR percentile
        df['ATR_percentile'] = df['ATR'].rolling(window=60).apply(
            lambda x: (x.iloc[-1] - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0.5
        )
        
        for i in range(20, len(df)):  # Need history
            timestamp = df.index[i]
            close = df.iloc[i]['Close']
            atr = df.iloc[i]['ATR']
            atr_pct = df.iloc[i].get('ATR_percentile', 0.5)
            
            if pd.isna(atr_pct):
                continue
            
            # Low volatility condition
            if atr_pct < self.atr_low_threshold:
                # Check for breakout
                high_20 = df.iloc[i-20:i]['High'].max()
                low_20 = df.iloc[i-20:i]['Low'].min()
                
                # Bullish breakout
                if close > high_20:
                    signals.append(Signal(
                        timestamp=timestamp,
                        pair=pair,
                        direction="BUY",
                        strength=1 - atr_pct,  # Stronger signal with lower volatility
                        strategy=self.name,
                        entry_price=close,
                        stop_loss=low_20,
                        take_profit=close + (close - low_20) * self.breakout_factor,
                    ))
                
                # Bearish breakout
                elif close < low_20:
                    signals.append(Signal(
                        timestamp=timestamp,
                        pair=pair,
                        direction="SELL",
                        strength=1 - atr_pct,
                        strategy=self.name,
                        entry_price=close,
                        stop_loss=high_20,
                        take_profit=close - (high_20 - close) * self.breakout_factor,
                    ))
        
        return signals


class TrendFollowing(BaseStrategy):
    """
    H4: Simple Trend Following
    Entry: Multiple moving averages aligned
    """
    
    def __init__(self):
        super().__init__("H4_TrendFollowing")
    
    def generate_signals(self, df: pd.DataFrame, pair: str) -> list[Signal]:
        signals = []
        
        if 'SMA_20' not in df.columns or 'SMA_50' not in df.columns:
            return signals
        
        for i in range(1, len(df)):
            timestamp = df.index[i]
            close = df.iloc[i]['Close']
            sma20 = df.iloc[i]['SMA_20']
            sma50 = df.iloc[i]['SMA_50']
            sma20_prev = df.iloc[i-1]['SMA_20']
            sma50_prev = df.iloc[i-1]['SMA_50']
            atr = df.iloc[i].get('ATR', close * 0.01)
            
            # Skip NaN
            if pd.isna(sma20) or pd.isna(sma50):
                continue
            
            # Bullish: 20 crosses above 50
            if sma20 > sma50 and sma20_prev <= sma50_prev:
                signals.append(Signal(
                    timestamp=timestamp,
                    pair=pair,
                    direction="BUY",
                    strength=0.7,
                    strategy=self.name,
                    entry_price=close,
                    stop_loss=close - (3 * atr),
                    take_profit=close + (4 * atr),
                ))
            
            # Bearish: 20 crosses below 50
            elif sma20 < sma50 and sma20_prev >= sma50_prev:
                signals.append(Signal(
                    timestamp=timestamp,
                    pair=pair,
                    direction="SELL",
                    strength=0.7,
                    strategy=self.name,
                    entry_price=close,
                    stop_loss=close + (3 * atr),
                    take_profit=close - (4 * atr),
                ))
        
        return signals


# Registry of all strategies
STRATEGIES = {
    "H1": MomentumBreakout,
    "H2": MeanReversion,
    "H3": VolatilityBreakout,
    "H4": TrendFollowing,
}


def get_strategy(name: str) -> BaseStrategy:
    """Get strategy instance by name."""
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[name]()
