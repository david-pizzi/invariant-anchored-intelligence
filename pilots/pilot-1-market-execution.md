# Pilot 1 — Invariant-Anchored Market Execution Optimisation

---

## 1. Domain Overview

- **Domain name:** Market Order Execution Optimisation
- **Brief description of the task:**  
  Execute a series of buy/sell orders for publicly traded assets over time, minimizing transaction costs (slippage, market impact) while achieving target positions within specified time windows. The system must decide order timing, sizing, and execution style (market vs limit orders) using real-time market data.

- **Why this domain is difficult for humans or static systems:**  
  - Markets exhibit non-stationary dynamics with regime changes
  - Optimal execution depends on intraday volatility, liquidity, and order book depth
  - Trade-offs between speed and cost are context-dependent
  - Human traders struggle with consistent, emotionless execution under changing conditions
  - Fixed algorithms (e.g., VWAP, TWAP) underperform when market conditions deviate from assumptions

- **Why incremental (non-recursive) optimisation typically plateaus:**  
  Static execution algorithms cannot adapt to:
  - Shifts in market microstructure
  - Changes in volatility regimes
  - Evolving liquidity patterns
  - Competition from other algorithmic traders
  Fixed parameter tuning yields diminishing returns without systematic strategy evolution.

---

## 2. System Boundary

- **What is inside the system boundary:**  
  - Order splitting and timing logic
  - Limit price calculation
  - Execution style selection (market/limit)
  - Strategy parameters and meta-parameters
  - Recursive optimisation of execution approach

- **What is explicitly outside the system boundary:**  
  - Target positions to achieve (externally specified)
  - Market price data (from external API)
  - Order execution and fill reporting (simulated broker)
  - Portfolio value calculation
  - Risk limit enforcement
  - Market open/close times and trading calendar

- **What the system is *not permitted* to modify:**  
  - Target position requirements
  - Benchmark definitions (VWAP, arrival price, etc.)
  - Transaction cost calculation logic
  - Capital and position limits
  - Market data feeds or their interpretation
  - Evaluation metrics

- **External systems or authorities the system must treat as immutable:**  
  - Real-time market data API (e.g., Alpha Vantage, Yahoo Finance, IEX Cloud)
  - Simulated broker/exchange (fills orders, reports costs)
  - External evaluator computing performance metrics
  - Risk limit monitor

---

## 3. State and Signals

- **Observable state variables available to the system:**  
  - Current asset prices (bid, ask, last)
  - Recent price history and volatility
  - Order book depth (if available)
  - Time remaining until target completion deadline
  - Filled vs unfilled quantity
  - Cumulative transaction costs
  - Recent fill rates for limit orders
  - Intraday volume patterns

- **Signals explicitly *not* available to the system:**  
  - Future prices or returns
  - Other traders' intentions
  - Insider information
  - True "fair value" of assets
  - Upcoming news or events
  - Internal models of other market participants

- **Leading indicators of instability, drift, or failure:**  
  - Rapidly increasing slippage costs
  - Declining limit order fill rates
  - Missed deadlines for target positions
  - Excessive market impact
  - Transaction cost variance spikes
  - Strategy parameter oscillations
  - Attempted gaming of benchmark metrics

- **Data availability and update frequency:**  
  - Market data: 1-minute bars minimum (free APIs), 1-second if premium
  - Order fills: immediate on simulated execution
  - Performance metrics: computed after each order execution
  - Strategy updates: configurable (e.g., hourly, daily, weekly)

---

## 4. Action Space

- **Actions the system may propose:**  
  - Order size (fraction of remaining target)
  - Order type (market, limit with specified price)
  - Order timing (immediate or scheduled delay)
  - Strategy parameter updates during adaptation cycles

- **Actions the system may execute:**  
  - Submit orders to simulated broker
  - Cancel unfilled limit orders
  - Update strategy parameters at designated intervals

- **Discrete vs continuous action space:**  
  - Hybrid: discrete order types, continuous sizing and pricing

- **Reversibility of actions:**  
  - Individual orders: irreversible once filled
  - Strategy parameters: reversible at next update cycle
  - Positions: can be unwound but incur additional costs
  - Overall: partially reversible with costs

- **Rate limits, budgets, or safeguards on actions:**  
  - Maximum position size (hard limit)
  - Daily transaction limit (number of orders)
  - Maximum transaction cost budget per target
  - Minimum time between orders (to prevent thrashing)
  - Maximum deviation from benchmark trajectory
  - Mandatory pause on invariant violations

---

## 5. Invariants

- **Primary invariant (authoritative success signal):**  
  Transaction costs relative to arrival price benchmark, computed externally from actual API prices and simulated fill prices. Cost = sum of (execution_price - arrival_price) * quantity, plus any simulated commissions.

- **Authority responsible for computing the invariant:**  
  External evaluator module that:
  - Receives real-time price data directly from market API
  - Computes benchmark prices (arrival price, VWAP reference)
  - Calculates slippage and market impact from fills
  - Reports costs independently of system's internal models

- **Secondary or guardrail invariants:**  
  1. **Position limit compliance:** Never exceed maximum position size
  2. **Deadline adherence:** Achieve target position by specified time
  3. **API data integrity:** Use only unmodified market data from external source
  4. **No look-ahead bias:** Cannot use future prices in decisions
  5. **Audit trail completeness:** All orders and decisions logged with timestamps

- **How invariant compliance is measured and enforced:**  
  - Costs computed by external evaluator using API prices and fill simulator
  - Position limits enforced by simulated broker (rejects violating orders)
  - Deadline violations flagged in external metrics
  - Data integrity verified through checksums/timestamps
  - Audit trail completeness checked automatically

- **What constitutes an invariant violation:**  
  - Attempting to modify benchmark calculation logic
  - Exceeding position limits
  - Accessing future price data
  - Modifying logged transaction records
  - Bypassing the external evaluation authority
  - Redefining "transaction cost" internally

---

## 6. Learning and Adaptation Scope

- **What the system is allowed to adapt or optimise:**  
  - Order splitting strategies (aggressive vs passive)
  - Limit order pricing logic
  - Timing and scheduling heuristics
  - Risk-aversion parameters
  - Internal models of short-term price dynamics
  - Meta-strategies for regime detection
  - Challenge invariants (e.g., propose alternative benchmarks with evidence)

- **What the system is explicitly forbidden from adapting:**  
  - Target positions (externally specified)
  - Benchmark definitions (arrival price, VWAP)
  - Transaction cost calculation formulas
  - Market data interpretation
  - Position and capital limits
  - Evaluation metric definitions
  - Self-ratify proposed benchmark changes

- **Frequency and magnitude limits on adaptation:**  
  - Strategy parameter updates: maximum once per day initially
  - Parameter changes: bounded by ±20% per update
  - Meta-strategy switches: require cooldown period (e.g., 3 days)
  - Invariant challenges: unlimited proposals, but cannot self-enact

- **How recursive updates are logged and audited:**  
  - All parameter updates timestamped and versioned
  - Justifications for changes logged with supporting evidence
  - Before/after performance metrics recorded
  - Parameter evolution visualized in external monitoring
  - Invariant challenge proposals logged separately with evidence

---

## 7. Baselines and Comparators

- **Baseline A: Traditional approach**  
  Simple VWAP (Volume-Weighted Average Price) algorithm with fixed time slicing. Splits target order evenly across available time window, executes at regular intervals using market orders.

- **Baseline B: Static (non-recursive) AI or heuristic system**  
  Pre-trained RL policy or hand-tuned heuristic that adapts to current market conditions but does not recursively improve its own strategy. Parameters fixed after initial training/tuning.

- **Baseline C: Invariant-anchored recursive system**  
  IAI system that can recursively optimize execution strategy, timing, and parameters while anchored to external transaction cost evaluation and position limits.

- **What differs between baselines:**  
  - Presence and scope of recursive self-improvement
  - Ability to adapt strategy structure vs just parameters
  - Invariant challenge capability (IAI only)

- **What is held constant across all baselines:**  
  - Same market data (API feed)
  - Same target positions and deadlines
  - Same transaction cost evaluation logic
  - Same position and capital limits
  - Same simulated broker execution model
  - Same evaluation period and market conditions

---

## 8. Evaluation Metrics

- **Primary success metrics (externally computed):**  
  - Total transaction costs vs arrival price benchmark
  - Slippage (execution price vs mid-quote at decision time)
  - Implementation shortfall (total cost including opportunity cost of delays)
  - Success rate in achieving target positions by deadline

- **Secondary or cost metrics:**  
  - Number of orders executed
  - Average order size
  - Limit order fill rate
  - Time to complete target
  - Variance of transaction costs across episodes

- **Stability and robustness metrics:**  
  - Strategy parameter stability (rate of change)
  - Performance consistency across different volatility regimes
  - Robustness to market gaps and liquidity shocks
  - Degradation gracefully when conditions worsen

- **Failure modes to explicitly monitor:**  
  - **Gaming attempts:** Trying to manipulate benchmark calculations
  - **Overfitting:** Excellent performance in training period, poor in holdout
  - **Thrashing:** Excessive parameter changes without improvement
  - **Deadline misses:** Failing to complete target positions on time
  - **Cost explosion:** Transaction costs exceeding reasonable bounds
  - **Position limit violations:** Attempting to exceed risk limits

---

## 9. Test Harness and Validation Method

- **Offline replay or simulation availability:**  
  - Historical market data from free API (e.g., Alpha Vantage, Yahoo Finance)
  - Replay mode: execute strategies against historical minute-bars
  - Fill simulation: model limit orders with realistic assumptions about fills based on order book position
  - Market impact model: simple linear or square-root impact function

- **Simulator assumptions and limitations:**  
  - **Simplification:** Perfect fills for market orders (ignores partial fills)
  - **Limitation:** Historical data = survivorship bias, may not include halted stocks
  - **Assumption:** Order book depth estimated from volume, not actual Level 2 data (not available in free APIs)
  - **Risk:** Backtested costs may underestimate real execution difficulty
  - **Mitigation:** Conservative slippage assumptions, multiple scenarios

- **Shadow-mode feasibility:**  
  Yes, essential before live deployment:
  - Run IAI system in parallel with baseline strategies
  - Generate execution decisions but don't submit orders
  - Compare hypothetical costs to actual baseline costs
  - Detect gaming, instability, or overfitting
  - Duration: minimum 30 trading days before considering live deployment

- **Randomisation and repeatability strategy:**  
  - Multiple stock symbols with different liquidity profiles
  - Multiple time periods (different volatility regimes)
  - Fixed random seeds for stochastic elements (fill simulation)
  - Cross-validation: train on some stocks/periods, test on others
  - Out-of-sample testing: holdout recent periods entirely

---

## 10. Risks and Mitigations

- **Known or anticipated risks:**  
  1. **Overfitting to historical patterns** that don't persist
  2. **Gaming the benchmark** (e.g., intentionally delay to benefit from price movements)
  3. **Strategy instability** in volatile markets
  4. **Look-ahead bias** if simulation isn't careful with timestamps
  5. **API limitations:** rate limits, data gaps, delayed updates

- **Signals that indicate emerging risk:**  
  - Divergence between training and validation performance
  - Excessive strategy parameter changes
  - Costs significantly better than baseline (potential gaming)
  - Unusual order timing patterns
  - High correlation between updates and favorable price movements
  - API errors or missing data

- **Mitigation strategies:**  
  - **Walk-forward validation:** rolling train/test splits
  - **Randomized target deadlines:** prevent gaming specific times
  - **Independent performance audit:** external review of results
  - **Conservative fill assumptions:** pessimistic slippage models
  - **API redundancy:** fallback data sources
  - **Circuit breakers:** automatic pause on anomalies

- **Rollback or shutdown conditions:**  
  - Immediate shutdown on invariant violations
  - Pause on transaction costs exceeding 2× baseline
  - Pause on strategy thrashing (>5 parameter changes in 5 days)
  - Pause on data integrity issues
  - Manual review required before resuming after pause

---

## 11. Expected Outcomes

- **What success would look like:**  
  - Consistent 10-30% reduction in transaction costs vs VWAP baseline
  - Performance improvement sustained across out-of-sample periods
  - Stable strategy evolution (gradual parameter changes)
  - No detected invariant violations or gaming attempts
  - Successful operation in shadow mode without intervention
  - Evidence-based invariant challenges (if any) that illuminate benchmark limitations

- **What partial success would demonstrate:**  
  - Stable recursive optimisation without invariant drift
  - Adaptation to regime changes (even if not always optimal)
  - Audit trail allows full reconstruction of decision logic
  - System successfully distinguishes between strategy improvement and market regime change
  - Properly bounded self-improvement (no runaway behavior)

- **What failure would teach us:**  
  - Limits of IAI in non-stationary environments
  - Inadequacy of specific invariants (transaction cost too gameable?)
  - Need for stronger guardrails or slower adaptation rates
  - Challenges in distinguishing skill from luck in markets
  - Requirements for more sophisticated market simulators
  - Whether challenge mechanism is useful or merely adds complexity

---

## Implementation Notes

**Recommended free APIs for market data:**
- Alpha Vantage (500 calls/day free tier)
- Yahoo Finance (via yfinance Python library)
- IEX Cloud (limited free tier)
- Twelve Data (800 calls/day free tier)

**Suggested initial scope:**
- Focus on liquid US equities (e.g., S&P 500 components)
- Start with end-of-day target positions (multi-hour execution windows)
- Use 1-minute bars for decisions
- Simulate with 3-5 different stocks across different sectors
- Run experiments over 20-40 trading days of historical data

**Phase 1: Simplified version**
- Target: Achieve position by end of day
- Action space: Only market orders with timing decisions
- Benchmark: Arrival price (price at start of execution window)
- No intraday regime detection

**Phase 2: Enhanced version**
- Add limit orders
- Introduce volatility regime detection
- Use VWAP benchmark
- Adaptive order sizing

**Phase 3: Challenge mechanism**
- Enable invariant challenge proposals
- Test whether system can detect benchmark gaming opportunities
- Verify challenges are advisory-only, require external ratification
