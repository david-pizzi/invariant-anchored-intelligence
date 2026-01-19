"""
Signal Generator for IAI Forex

Generates trading signals based on retail sentiment fade strategy.
Includes position sizing using Kelly Criterion.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum

from .sentiment_fetcher import SentimentReading


class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class TradeSignal:
    """A trading signal with entry, exit, and sizing."""
    pair: str
    direction: TradeDirection
    timestamp: datetime
    
    # Entry details
    sentiment_long_pct: float
    sentiment_short_pct: float
    signal_strength: float  # 0-1, higher = more extreme sentiment
    
    # Position sizing (in % of bankroll)
    position_size_pct: float = 0.0
    
    # Risk management
    stop_loss_pips: float = 50.0
    take_profit_pips: float = 75.0  # 1.5:1 R/R
    
    # Tracking
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl_pips: Optional[float] = None
    result: Optional[str] = None  # "WIN", "LOSS", "OPEN"
    
    def __post_init__(self):
        if isinstance(self.direction, str):
            self.direction = TradeDirection(self.direction)


@dataclass 
class SignalGeneratorConfig:
    """Configuration for signal generation."""
    
    # Sentiment thresholds
    extreme_threshold: float = 75.0  # Only trade at 75%+ extreme
    super_extreme_threshold: float = 85.0  # Increase size at 85%+
    
    # Position sizing
    base_position_pct: float = 1.0  # 1% of bankroll per trade
    max_position_pct: float = 2.0   # Never more than 2%
    
    # Risk management
    default_stop_pips: float = 50.0
    default_tp_pips: float = 75.0  # 1.5:1 R/R ratio
    
    # Pairs to trade (only liquid majors)
    tradeable_pairs: List[str] = field(default_factory=lambda: [
        "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD"
    ])
    
    # Historical edge estimates (for Kelly sizing)
    historical_win_rate: float = 0.54
    historical_avg_win: float = 60.0  # pips
    historical_avg_loss: float = 45.0  # pips


class SignalGenerator:
    """
    Generates trading signals from sentiment data.
    
    The core logic:
    1. When 75%+ of retail is LONG → we go SHORT
    2. When 75%+ of retail is SHORT → we go LONG
    3. Size position based on signal strength
    """
    
    def __init__(self, config: SignalGeneratorConfig = None):
        self.config = config or SignalGeneratorConfig()
    
    def generate_signals(self, readings: List[SentimentReading]) -> List[TradeSignal]:
        """
        Generate trade signals from sentiment readings.
        
        Args:
            readings: List of sentiment readings
            
        Returns:
            List of trade signals for extreme sentiment pairs
        """
        signals = []
        
        for reading in readings:
            # Skip non-tradeable pairs
            if reading.pair not in self.config.tradeable_pairs:
                continue
            
            # Check for extreme sentiment
            if reading.long_pct >= self.config.extreme_threshold:
                # Retail is very LONG → we go SHORT
                signal = self._create_signal(reading, TradeDirection.SHORT)
                signals.append(signal)
                
            elif reading.short_pct >= self.config.extreme_threshold:
                # Retail is very SHORT → we go LONG
                signal = self._create_signal(reading, TradeDirection.LONG)
                signals.append(signal)
        
        return signals
    
    def _create_signal(self, reading: SentimentReading, direction: TradeDirection) -> TradeSignal:
        """Create a trade signal with proper sizing."""
        
        # Calculate signal strength (0-1)
        extreme_pct = reading.long_pct if direction == TradeDirection.SHORT else reading.short_pct
        strength = min((extreme_pct - 75) / 20, 1.0)  # 75-95% → 0-1
        
        # Calculate position size using Kelly Criterion
        position_size = self._calculate_position_size(strength)
        
        return TradeSignal(
            pair=reading.pair,
            direction=direction,
            timestamp=reading.timestamp,
            sentiment_long_pct=reading.long_pct,
            sentiment_short_pct=reading.short_pct,
            signal_strength=strength,
            position_size_pct=position_size,
            stop_loss_pips=self.config.default_stop_pips,
            take_profit_pips=self.config.default_tp_pips,
            result="OPEN"
        )
    
    def _calculate_position_size(self, strength: float) -> float:
        """
        Calculate position size using modified Kelly Criterion.
        
        Kelly: f = (p*b - q) / b
        Where:
            p = probability of winning
            b = win/loss ratio
            q = 1 - p
        
        We use HALF Kelly for safety.
        """
        # Base edge estimates
        p = self.config.historical_win_rate
        win_loss_ratio = self.config.historical_avg_win / self.config.historical_avg_loss
        q = 1 - p
        
        # Full Kelly
        kelly = (p * win_loss_ratio - q) / win_loss_ratio
        
        # Half Kelly for safety
        half_kelly = kelly / 2
        
        # Scale by signal strength
        base_size = self.config.base_position_pct
        scaled_size = base_size * (1 + strength)  # 1-2x base size
        
        # Apply Kelly constraint
        size = min(scaled_size, half_kelly * 100)
        
        # Clamp to max
        return min(size, self.config.max_position_pct)
    
    def print_signals(self, signals: List[TradeSignal]):
        """Display signals in readable format."""
        if not signals:
            print("\n⚪ No trading signals at current sentiment levels.")
            return
        
        print("\n" + "=" * 70)
        print("🎯 TRADING SIGNALS (Retail Fade)")
        print("=" * 70)
        
        for signal in sorted(signals, key=lambda x: -x.signal_strength):
            direction_icon = "🔴" if signal.direction == TradeDirection.SHORT else "🟢"
            print(f"\n{direction_icon} {signal.pair}: {signal.direction.value}")
            print(f"   Sentiment: {signal.sentiment_long_pct:.0f}% Long / {signal.sentiment_short_pct:.0f}% Short")
            print(f"   Strength:  {signal.signal_strength:.0%}")
            print(f"   Size:      {signal.position_size_pct:.1f}% of bankroll")
            print(f"   Stop Loss: {signal.stop_loss_pips:.0f} pips")
            print(f"   Take Profit: {signal.take_profit_pips:.0f} pips")
        
        print("\n" + "-" * 70)
        print(f"Total signals: {len(signals)}")
        total_exposure = sum(s.position_size_pct for s in signals)
        print(f"Total exposure: {total_exposure:.1f}% of bankroll")
        print("=" * 70)


if __name__ == "__main__":
    from .sentiment_fetcher import SentimentFetcher
    
    # Fetch sentiment
    fetcher = SentimentFetcher()
    readings = fetcher.fetch_ig_sentiment()
    
    # Generate signals
    generator = SignalGenerator()
    signals = generator.generate_signals(readings)
    
    # Display
    generator.print_signals(signals)
