# Pilot 2 — Invariant-Anchored Sports Betting Optimization

---

## 1. Domain Overview

- **Domain name:** Sports Betting Portfolio Optimization
- **Brief description of the task:**  
  Select which sporting events to bet on, determine optimal bet sizing, and manage bankroll across multiple opportunities over time to maximize long-term wealth growth while avoiding ruin.

- **Why this domain is difficult for humans or static systems:**  
  - Markets are semi-efficient but beatable by sharp bettors
  - Optimal bet sizing requires balancing edge detection, variance management, and bankroll preservation
  - Fixed strategies (always bet X% of bankroll) fail under changing market conditions
  - Emotional biases (chasing losses, overconfidence after wins) plague human bettors
  - Static models can't adapt to: league-specific patterns, closing line movement, seasonal effects, sharp vs public money detection
  - Multi-sport portfolios require correlation modeling (NBA + NFL games on same night)

- **Why incremental (non-recursive) optimisation typically plateaus:**  
  Fixed Kelly criterion applications assume:
  - You know your true edge (you don't)
  - Edge is stationary (it isn't - books adjust, your model ages)
  - Single-bet independence (correlated parlays break this)
  
  Traditional ML models optimize prediction accuracy but not betting decisions. There's a gap between "predicting outcomes well" and "making profitable bets."

---

## 2. System Boundary

- **What is inside the system boundary:**  
  - Bet selection (which events to bet on)
  - Bet sizing (how much to wager per bet)
  - Market selection (which sportsbooks/lines to use)
  - Bankroll management strategy
  - Edge estimation and confidence calibration
  - Portfolio construction across multiple bets
  - Strategy parameters and meta-parameters
  - Recursive optimization of betting approach

- **What is explicitly outside the system boundary:**  
  - Game outcomes (determined by actual sporting events)
  - Odds/lines offered by sportsbooks (market-determined)
  - Historical game results and statistics (external data)
  - Bet settlement and payout calculation (sportsbook-controlled)
  - Available betting markets (sportsbook-defined)
  - Sports league rules and schedules

- **What the system is *not permitted* to modify:**  
  - Actual game outcomes or odds
  - Payout calculation rules
  - Bet settlement logic
  - Historical performance data once recorded
  - External data sources (scores, stats, injury reports)
  - Success metrics (profit, Sharpe ratio, max drawdown)

- **External systems or authorities the system must treat as immutable:**  
  - Sportsbooks (bet execution and settlement)
  - Sports leagues (game results)
  - External evaluator (profit/loss calculation)
  - Bankroll accounting system

---

## 3. State and Signals

- **Observable state variables available to the system:**  
  - Current bankroll balance
  - Historical bet outcomes (W/L, profit/loss per bet)
  - Available betting lines and odds across sportsbooks
  - Historical odds movement (opening vs closing lines)
  - Public betting percentages (if available)
  - Team statistics, standings, recent form
  - Injury reports and lineup information
  - Weather conditions (for outdoor sports)
  - Historical model performance by sport/league/bet type
  - Current win rate, average edge, return on investment
  - Drawdown from peak bankroll
  - Bet correlation structure (same-game parlays, related events)

- **Signals explicitly *not* available to the system:**  
  - Future game outcomes
  - Private injury information
  - Referee assignments (usually)
  - Insider information or fixed games
  - Future odds movements
  - Other bettors' full portfolios
  - Sportsbook's true risk exposure

- **Leading indicators of instability, drift, or failure:**  
  - Win rate declining below historical baseline
  - Actual edges smaller than estimated edges (model degradation)
  - Increasing bankroll volatility
  - Consecutive losing streaks beyond expected variance
  - Bet sizing approaching Kelly-dangerous levels (>25% of bankroll)
  - Model performing differently across sports (sharp in NBA, poor in NFL)
  - Closing line value turning negative (betting worse than market close)
  - Bankroll approaching ruin threshold

- **Data availability and update frequency:**  
  - Odds: Real-time or near-real-time via sportsbook APIs
  - Game results: Within minutes of game completion
  - Stats and injury updates: Daily or more frequent
  - Strategy evaluation: After each bet settles
  - Recursive optimization: Weekly or after N bets (e.g., every 50 bets)

---

## 4. Action Space

- **Actions the system may propose:**  
  - Place bet on specific event/market (e.g., "Lakers -5.5 @ -110")
  - Bet size (dollar amount or % of bankroll)
  - Skip available opportunities (no bet)
  - Hedge or offset existing positions
  - Adjust confidence thresholds for future bets

- **Actions the system may execute:**  
  Same as proposed (direct execution via API or manual placement)

- **Discrete vs continuous action space:**  
  Hybrid:
  - Bet selection: Discrete (choose from available markets)
  - Bet sizing: Continuous (subject to minimum/maximum constraints)

- **Reversibility of actions:**  
  - Bets are irreversible once placed and accepted by sportsbook
  - Some sportsbooks allow early cashout (partial reversal with penalty)
  - Cannot change bet after game starts

- **Rate limits, budgets, or safeguards on actions:**  
  - Maximum bet size per event (e.g., 5% of bankroll, or fractional Kelly)
  - Maximum total exposure per day/week
  - Minimum bankroll reserve (never bet below $X)
  - Maximum number of simultaneous open bets
  - Mandatory cool-down after large losses
  - Circuit breaker: halt betting if drawdown exceeds threshold (e.g., 30%)

---

## 5. Invariants

- **Primary invariant (authoritative success signal):**  
  Actual game outcomes and resulting profit/loss as settled by sportsbooks.
  
  **Crucially:** The system does NOT get to choose which bets to include in evaluation. All placed bets count.

- **Authority responsible for computing the invariant:**  
  - Sportsbooks settle individual bets
  - External evaluator computes cumulative P&L, ROI, Sharpe ratio
  - Bankroll tracking system (external, append-only ledger)

- **Secondary or guardrail invariants (if any):**  
  - Bankroll must never go below ruin threshold ($0 or defined minimum)
  - Must never bet more than available capital (no leverage)
  - Bet records must be complete and tamper-proof (external logging)
  - Cannot retroactively exclude "inconvenient" bets from evaluation

- **How invariant compliance is measured and enforced:**  
  - Every bet placed is logged externally with timestamp, odds, stake, outcome
  - P&L calculated by independent system from these logs
  - Sportsbook confirmations provide ground truth for bet settlement
  - External authority computes metrics; system receives them read-only

- **What constitutes an invariant violation:**  
  - Attempting to modify historical bet records
  - Cherry-picking which bets "count" for evaluation
  - Claiming bets were "just tests" after losing
  - Circumventing bankroll limits
  - Modifying payout calculations

---

## 6. Learning and Adaptation Scope

- **What the system is allowed to adapt or optimize:**  
  - Predictive models for game outcomes
  - Edge estimation methods
  - Bet sizing formulas (alternatives to Kelly)
  - Market selection strategy (which sportsbooks, which bet types)
  - Confidence calibration curves
  - Sport/league specialization decisions
  - Correlation models for portfolio construction
  - Trigger conditions for placing bets (minimum edge threshold)

- **What the system is explicitly forbidden from adapting:**  
  - Actual game outcomes
  - Odds offered by sportsbooks (can choose, not change)
  - Payout rules and bet settlement
  - How profit/loss is calculated
  - The definition of "bankroll" or "return"
  - Historical performance records

- **Frequency and magnitude limits on adaptation:**  
  - Strategy updates: Weekly or every 50-100 bets (whichever comes first)
  - Bet sizing formula changes: Bounded adjustments (e.g., Kelly fraction 0.1x to 2x)
  - Model retraining: Daily allowed, but deployment gated by validation
  - Parameter updates: Logged with before/after values

- **How recursive updates are logged and audited:**  
  - All strategy changes logged with timestamp and rationale
  - A/B testing: shadow-mode tracking of alternative strategies
  - Version control of betting models and sizing rules
  - External audit log of what changed when and why

---

## 7. Baselines and Comparators

- **Baseline A: Flat betting with ML predictions**  
  Fixed bet size (e.g., 1% of bankroll) on all bets where model predicts edge > 5%

- **Baseline B: Kelly criterion with static edge estimation**  
  Use historical model accuracy to estimate edge, apply full Kelly sizing, no adaptation

- **Baseline C: Fractional Kelly (e.g., quarter-Kelly)**  
  Conservative fixed-fraction Kelly, standard sharp bettor approach

- **Baseline D: Public "tout" service picks**  
  Follow published betting picks from a popular service (control for data/model quality)

- **Baseline E: IAI system**  
  Full recursive optimization of betting strategy with invariant anchoring

- **What differs between baselines:**  
  Presence and depth of self-improvement; bet sizing sophistication; market selection logic

- **What is held constant across all baselines:**  
  - Same historical data and prediction models initially
  - Same available betting markets and odds
  - Same bankroll starting point
  - Same evaluation period and metrics
  - Same external profit/loss calculation

---

## 8. Evaluation Metrics

- **Primary success metrics (externally computed):**  
  - **Net profit**: Absolute dollar return over evaluation period
  - **ROI**: Return on investment (profit / total amount wagered)
  - **Bankroll growth rate**: CAGR or log-wealth accumulation
  - **Sharpe ratio**: Risk-adjusted return (mean return / standard deviation)
  - **Closing Line Value (CLV)**: How IAI's bet prices compare to closing market odds (leading indicator)

- **Secondary or cost metrics:**  
  - Number of bets placed
  - Average bet size
  - Turnover (total amount wagered)
  - Win rate (not as important as profit, but informative)
  - Time invested per bet

- **Stability and robustness metrics:**  
  - **Maximum drawdown**: Largest peak-to-trough decline in bankroll
  - **Recovery time**: How long to recover from drawdowns
  - **Variance of returns**: Consistency of performance
  - **Performance across sports/leagues**: Does IAI specialize or generalize?
  - **Correlation with baselines**: Is IAI doing something fundamentally different?

- **Failure modes to explicitly monitor:**  
  - Bankroll ruin (hitting zero or minimum threshold)
  - Systematic overbetting (Kelly violations)
  - Chasing losses (increasing bet size after losses)
  - Goodhart's Law: Optimizing for metric instead of profit (e.g., cherry-picking high-CLV bets with terrible variance)
  - Model overfitting to recent results
  - Ignoring correlation risk (betting too many same-game events)

---

## 9. Test Harness and Validation Method

- **Offline replay or simulation availability:**  
  YES - extensive historical odds and outcomes data available:
  - Sports databases (Odds Portal, Sportsbook Review archives)
  - Historical closing lines
  - Game outcomes from major leagues (NBA, NFL, MLB, NHL, soccer)
  - Can simulate 5-10 years of betting history

- **Simulator assumptions and limitations:**  
  - Assumes historical odds would have been available at bet placement time (mostly true for closing lines)
  - Cannot perfectly simulate live betting or in-game odds movements
  - Assumes bets would have been accepted at stated odds (liquidity assumption)
  - Does not model sportsbook limits on sharp bettors (real concern for profitable bettors)

- **Shadow-mode feasibility:**  
  YES - highly feasible:
  - Track hypothetical bets alongside real bets (if any)
  - Compare IAI recommendations vs actual decisions
  - Can run shadow mode with zero capital at risk
  - Real-time odds available via APIs

- **Randomisation and repeatability strategy:**  
  - Use fixed random seeds for train/test splits
  - Time-based holdout: Train on 2019-2023, test on 2024-2025
  - Forward-chaining validation: Train on Year N, test on Year N+1, repeat
  - Multiple random initializations of IAI to test consistency

---

## 10. Risks and Mitigations

- **Known or anticipated risks:**  
  1. **Bankroll ruin**: Aggressive betting depletes capital
  2. **Model overfitting**: IAI optimizes for noise in training data
  3. **Market efficiency**: Edges disappear as markets adapt
  4. **Sportsbook limiting**: Profitable bettors get restricted
  5. **Regulatory/legal**: Betting laws vary by jurisdiction
  6. **Gaming the metric**: IAI finds ways to look good on paper but lose money in practice
  7. **Variance underestimation**: Bad luck looks like bad strategy
  8. **Data leakage**: Using future information in training

- **Signals that indicate emerging risk:**  
  - Drawdown exceeding historical worst-case
  - Win rate collapsing suddenly
  - Bet sizes increasing rapidly
  - Model confidence diverging from realized accuracy
  - Negative CLV (betting against sharp money)
  - Decreasing bet acceptance from sportsbooks

- **Mitigation strategies:**  
  1. **Strict bankroll limits**: Never exceed fractional Kelly (e.g., half-Kelly max)
  2. **Circuit breakers**: Auto-pause after 20% drawdown
  3. **Out-of-sample validation**: Always test on future unseen data
  4. **External audit**: All bets logged to tamper-proof system
  5. **Small initial bankroll**: Start with $100-1000, not life savings
  6. **Diversification**: Multiple sports/leagues to reduce correlation
  7. **Regular recalibration**: Check if estimated edges match realized edges
  8. **Shadow mode first**: Run for 100+ bets before risking real money

- **Rollback or shutdown conditions:**  
  - Bankroll drops below 50% of starting value
  - 30-day ROI below -20%
  - IAI proposes bet sizes exceeding full Kelly
  - Detected data leakage or evaluation errors
  - Legal/regulatory issues arise

---

## 11. Expected Outcomes

- **What success would look like:**  
  - IAI outperforms all baselines in both ROI and Sharpe ratio over 500+ bets
  - Positive CLV (betting better than market close)
  - Bankroll grows steadily with controlled drawdowns (<20%)
  - IAI discovers non-obvious betting principles (e.g., "reduce exposure in December," "avoid road divisional underdogs")
  - System adapts to market changes that hurt static strategies
  - Proposed invariant challenges reveal insights (e.g., "profit per hour" better than "ROI")

- **What partial success would demonstrate:**  
  - IAI matches Kelly criterion performance with lower variance
  - Positive ROI but underperforms best baseline slightly
  - Good performance in some sports, poor in others (specialization signal)
  - Useful invariant challenges even if overall profit is marginal
  - Framework validates but needs domain-specific tuning

- **What failure would teach us:**  
  - Sports betting too efficient for IAI to beat (market stronger than expected)
  - IAI's recursive optimization adds noise without signal
  - Invariant anchoring insufficient to prevent Goodhart's Law
  - Bet sizing optimization matters less than prediction accuracy
  - Domain requires human intuition that IAI can't capture
  - Failure modes: which specific breakdowns occurred and why

---

## 12. Implementation Roadmap

### Phase 1: Historical Backtesting (Weeks 1-2)
- Acquire historical odds and outcomes data (2019-2024)
- Implement baselines (flat betting, Kelly, fractional Kelly)
- Build evaluation harness with external P&L calculation
- Run offline simulations, validate metrics

### Phase 2: IAI Implementation (Weeks 3-4)
- Port IAI framework from bandit pilot
- Implement bet sizing strategies and edge estimation
- Add invariant challenge mechanism (alternative success metrics)
- Run historical replay with IAI

### Phase 3: Shadow Mode (Weeks 5-6)
- Set up live odds feeds (Odds API, The Odds API)
- Run IAI in shadow mode (no money at risk)
- Track hypothetical performance vs baselines
- Calibrate predictions against real outcomes

### Phase 4: Live Deployment (Week 7+)
- Start with small bankroll ($100-500)
- Place actual bets following IAI recommendations
- Monitor real P&L vs shadow projections
- Iterate based on real-world feedback

---

## 13. Data Sources and Tools

**Historical Data:**
- Sports Odds History: oddshark.com, oddsportal.com, Sportsbook Review
- Game outcomes: Sports-Reference (basketball-reference.com, pro-football-reference.com)
- Betting lines archive: Kaggle datasets, pre-game.com

**Live Odds APIs:**
- The Odds API (theoddsapi.com) - $Free tier available
- Odds Jam API
- Action Network API

**Prediction Models (Starting Point):**
- Elo ratings (FiveThirtyEight methodology)
- Regression models (team stats → point spread)
- Market-implied probabilities from odds

**Execution:**
- Manual placement initially (lowest friction)
- Later: DraftKings, FanDuel, BetMGM APIs (if available)

---

## 14. Success Criteria for Advancing to Pilot 3

To consider this pilot a success and move to the next domain:

1. **Performance**: IAI achieves positive ROI over 500+ real or simulated bets
2. **Robustness**: Outperforms at least 2/4 baselines on Sharpe ratio
3. **Adaptability**: Demonstrates measurable improvement over time (later bets better than early bets)
4. **Invariant challenges**: Proposes at least one meaningful alternative success metric
5. **Risk management**: No bankroll ruin, max drawdown <30%
6. **Reproducibility**: Results replicate across multiple time periods and random seeds

If these criteria are met, IAI has demonstrated value in a real, adversarial, money-making domain.

---

## Notes

- **Legal disclaimer**: Sports betting legality varies by jurisdiction. Ensure compliance with local laws.
- **Responsible gambling**: Use strict bankroll limits. This is research, not a get-rich-quick scheme.
- **Market impact**: At small scale ($100-10k bankroll), you won't move markets. If successful at larger scale, edge may decay.
- **Time commitment**: Requires daily monitoring during betting periods (sports seasons).
