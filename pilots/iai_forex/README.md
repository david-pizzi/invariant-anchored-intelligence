# IAI Forex Pilot

Forex trading system using real historical data and IAI framework.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run backtest on EUR/USD (2023 data)
python research/backtest.py
```

## What This Tests

**4 Strategies** on **real historical forex data**:
- H1: Momentum Breakout (price crosses MA with momentum)
- H2: Mean Reversion (Bollinger Bands + RSI extremes)
- H3: Volatility Breakout (low ATR → breakout)
- H4: Trend Following (MA crossovers)

**Data Source**: Yahoo Finance (free, no API key needed)

## Expected Output

```
BACKTEST RESULTS
==================================================================
Total Trades:      47
Win Rate:          53.2%
Total Profit:      $1,247.50
Total Return:      12.5%

Sharpe Ratio:      1.68
Max Drawdown:      8.3%
```

## Next Steps

1. **Test on different pairs**: EUR/USD, GBP/USD, USD/JPY
2. **Test different periods**: 2020-2024
3. **Add IAI components**: Authority, Challenger, Evaluator
4. **Paper trading**: OANDA practice account

## Files

```
iai_forex/
├── core/
│   ├── data_fetcher.py    # Fetch historical data (Yahoo Finance)
│   └── strategies.py       # 4 trading strategies
│
└── research/
    └── backtest.py         # Backtest engine
```

## How It Works

### 1. Data Fetching
```python
fetcher = ForexDataFetcher()
df = fetcher.fetch_pair("EUR/USD", "2023-01-01", "2024-01-01", "1h")
# Downloads hourly candles from Yahoo Finance
# Adds: SMA, BB, RSI, ATR indicators
```

### 2. Signal Generation
```python
strategy = get_strategy("H1")  # Momentum Breakout
signals = strategy.generate_signals(df, "EUR/USD")
# Returns list of BUY/SELL signals with entry/SL/TP
```

### 3. Backtesting
```python
backtester = ForexBacktester(initial_capital=10000)
metrics = backtester.run_backtest(df, "EUR/USD", "H1")
# Simulates trades, calculates: win rate, Sharpe, drawdown
```

## Strategy Details

### H1: Momentum Breakout
- **Entry**: Price crosses 20 SMA with >0.15% momentum
- **Stop Loss**: 2x ATR below entry
- **Take Profit**: 3x ATR above entry
- **Best for**: Trending markets

### H2: Mean Reversion
- **Entry**: Price touches Bollinger Band + RSI extreme
- **Stop Loss**: Distance to BB middle
- **Take Profit**: BB middle line
- **Best for**: Range-bound markets

### H3: Volatility Breakout
- **Entry**: Low ATR + breakout above 20-day range
- **Stop Loss**: Opposite end of range
- **Take Profit**: 1.5x range size
- **Best for**: Quiet periods before big moves

### H4: Trend Following
- **Entry**: 20 SMA crosses 50 SMA
- **Stop Loss**: 3x ATR
- **Take Profit**: 4x ATR
- **Best for**: Strong trends

## Limitations (For Now)

❌ No live trading (backtesting only)  
❌ No IAI adaptation yet (coming next)  
❌ No retail sentiment data (planned)  
❌ Limited to Yahoo Finance data  

## Future IAI Integration

Next iteration will add:
1. **Authority**: Pause trading when Sharpe <1.5
2. **Challenger**: Detect regime changes, propose strategy switches
3. **Evaluator**: Compare all 4 strategies weekly
4. **External invariant**: Broker API P&L (OANDA)
