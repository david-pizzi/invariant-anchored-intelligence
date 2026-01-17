"""Multi-League Simulator with Per-League Authority

Simulates betting across multiple leagues using per-league configurations.
Each league has its own Authority instance with calibrated thresholds.

LOCAL RESEARCH ONLY - does not affect cloud/production code.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add the iai_betting directory to path for imports
iai_betting_dir = Path(__file__).parent.parent
sys.path.insert(0, str(iai_betting_dir))

from core.data import FootballDataLoader, Match
from league_config import (
    LEAGUE_CONFIGS, 
    LeagueConfig, 
    get_enabled_leagues,
    get_league_config,
)


@dataclass
class BetRecord:
    """Record of a single bet."""
    date: datetime
    league: str
    home_team: str
    away_team: str
    selection: str
    odds: float
    stake: float
    won: bool
    profit: float
    
    # Authority state at time of bet
    authority_stake_modifier: float = 1.0
    authority_status: str = "normal"


@dataclass
class LeagueState:
    """Tracks the state for a single league."""
    config: LeagueConfig
    
    # Performance tracking
    bets: List[BetRecord] = field(default_factory=list)
    current_streak: int = 0  # Negative = losses, positive = wins
    
    # Authority state
    stake_modifier: float = 1.0
    status: str = "normal"  # normal, reduced_1, reduced_2, paused
    
    @property
    def total_bets(self) -> int:
        return len(self.bets)
    
    @property
    def wins(self) -> int:
        return sum(1 for b in self.bets if b.won)
    
    @property
    def win_rate(self) -> float:
        return self.wins / self.total_bets if self.total_bets > 0 else 0
    
    @property
    def total_profit(self) -> float:
        return sum(b.profit for b in self.bets)
    
    @property
    def total_staked(self) -> float:
        return sum(b.stake for b in self.bets)
    
    @property
    def roi(self) -> float:
        return self.total_profit / self.total_staked if self.total_staked > 0 else 0


class LeagueAuthority:
    """Authority instance for a specific league."""
    
    def __init__(self, config: LeagueConfig):
        self.config = config
        self.auth = config.authority
        self.strat = config.strategy
        
        # State
        self.current_streak = 0
        self.stake_modifier = 1.0
        self.status = "normal"
        self.recent_results: List[bool] = []
        
    def process_result(self, won: bool) -> Dict:
        """Process a bet result and update authority state."""
        self.recent_results.append(won)
        
        if won:
            self.current_streak = max(0, self.current_streak) + 1
            self._check_recovery()
        else:
            self.current_streak = min(0, self.current_streak) - 1
            self._check_strain()
        
        # Check win rate if enough bets
        alerts = []
        if len(self.recent_results) >= self.auth.min_bets_for_analysis:
            recent_win_rate = sum(self.recent_results[-self.auth.min_bets_for_analysis:]) / self.auth.min_bets_for_analysis
            recent_win_rate_pct = recent_win_rate * 100
            
            if recent_win_rate_pct < self.auth.win_rate_critical:
                alerts.append(f"CRITICAL: Win rate {recent_win_rate_pct:.1f}% below {self.auth.win_rate_critical}%")
            elif recent_win_rate_pct < self.auth.win_rate_warning:
                alerts.append(f"WARNING: Win rate {recent_win_rate_pct:.1f}% below {self.auth.win_rate_warning}%")
        
        return {
            "streak": self.current_streak,
            "stake_modifier": self.stake_modifier,
            "status": self.status,
            "alerts": alerts,
        }
    
    def _check_strain(self):
        """Check if we need to reduce stake or pause."""
        loss_streak = abs(self.current_streak)
        
        if loss_streak >= self.auth.loss_streak_pause:
            self.status = "paused"
            self.stake_modifier = 0.0
        elif loss_streak >= self.auth.loss_streak_reduce_2:
            self.status = "reduced_2"
            self.stake_modifier = self.auth.stake_reduction_2
        elif loss_streak >= self.auth.loss_streak_reduce_1:
            self.status = "reduced_1"
            self.stake_modifier = self.auth.stake_reduction_1
    
    def _check_recovery(self):
        """Check if we can restore normal stake."""
        if self.current_streak >= self.auth.wins_to_restore_stake:
            self.status = "normal"
            self.stake_modifier = 1.0
    
    def get_stake(self, bankroll: float) -> float:
        """Get the stake for the next bet."""
        if self.status == "paused":
            return 0.0
        
        base_stake = bankroll * (self.strat.base_stake_pct / 100)
        return base_stake * self.stake_modifier
    
    def should_bet(self) -> bool:
        """Whether we should place a bet."""
        return self.status != "paused"


class MultiLeagueSimulator:
    """Simulates betting across multiple leagues with per-league authority."""
    
    def __init__(
        self, 
        leagues: List[str] = None,
        initial_bankroll: float = 1000.0,
        seasons: List[str] = None,
    ):
        """
        Initialize simulator.
        
        Args:
            leagues: League codes to simulate (default: enabled leagues)
            initial_bankroll: Starting bankroll
            seasons: Seasons to simulate
        """
        self.initial_bankroll = initial_bankroll
        self.bankroll = initial_bankroll
        self.seasons = seasons or ["1718", "1819", "1920", "2021", "2122", "2223", "2324"]
        
        # Get league configs
        if leagues:
            self.leagues = {code: get_league_config(code) for code in leagues if get_league_config(code)}
        else:
            self.leagues = {cfg.code: cfg for cfg in get_enabled_leagues()}
        
        # Initialize authorities for each league
        self.authorities: Dict[str, LeagueAuthority] = {
            code: LeagueAuthority(cfg) for code, cfg in self.leagues.items()
        }
        
        # Track state per league
        self.league_states: Dict[str, LeagueState] = {
            code: LeagueState(config=cfg) for code, cfg in self.leagues.items()
        }
        
        # Overall tracking
        self.all_bets: List[BetRecord] = []
        self.bankroll_history: List[Tuple[datetime, float]] = []
        
        # Data loader
        self.loader = FootballDataLoader(data_dir="data/football")
    
    def run(self, verbose: bool = True) -> Dict:
        """Run the simulation."""
        if verbose:
            print("=" * 80)
            print("MULTI-LEAGUE SIMULATION WITH PER-LEAGUE AUTHORITY")
            print("=" * 80)
            print(f"\nLeagues: {', '.join(self.leagues.keys())}")
            print(f"Seasons: {self.seasons[0]} to {self.seasons[-1]}")
            print(f"Initial bankroll: £{self.initial_bankroll:.2f}")
        
        # Load all matches for all leagues
        all_matches: List[Tuple[Match, str]] = []  # (match, league_code)
        
        for league_code in self.leagues:
            for season in self.seasons:
                try:
                    matches = self.loader.load_season(league_code, season)
                    for m in matches:
                        all_matches.append((m, league_code))
                except Exception as e:
                    continue
        
        # Sort by date
        all_matches.sort(key=lambda x: x[0].date)
        
        if verbose:
            print(f"\nTotal matches loaded: {len(all_matches)}")
            print("\nSimulating...")
        
        # Process matches chronologically
        for match, league_code in all_matches:
            self._process_match(match, league_code)
        
        return self._generate_report(verbose)
    
    def _process_match(self, match: Match, league_code: str):
        """Process a single match."""
        config = self.leagues[league_code]
        authority = self.authorities[league_code]
        state = self.league_states[league_code]
        
        # Check if match qualifies
        strat = config.strategy
        if strat.selection == "H":
            odds = match.odds.home_odds
            won = match.result == "H"
        elif strat.selection == "D":
            odds = match.odds.draw_odds
            won = match.result == "D"
        else:
            odds = match.odds.away_odds
            won = match.result == "A"
        
        # Check odds range
        if not (strat.min_odds <= odds < strat.max_odds):
            return
        
        # Check if authority allows betting
        if not authority.should_bet():
            return
        
        # Calculate stake
        stake = authority.get_stake(self.bankroll)
        if stake <= 0:
            return
        
        # Execute bet
        profit = stake * (odds - 1) if won else -stake
        self.bankroll += profit
        
        # Record bet
        bet = BetRecord(
            date=match.date,
            league=league_code,
            home_team=match.home_team,
            away_team=match.away_team,
            selection=strat.selection,
            odds=odds,
            stake=stake,
            won=won,
            profit=profit,
            authority_stake_modifier=authority.stake_modifier,
            authority_status=authority.status,
        )
        
        self.all_bets.append(bet)
        state.bets.append(bet)
        self.bankroll_history.append((match.date, self.bankroll))
        
        # Update authority
        authority.process_result(won)
    
    def _generate_report(self, verbose: bool) -> Dict:
        """Generate simulation report."""
        
        # Overall stats
        total_bets = len(self.all_bets)
        total_wins = sum(1 for b in self.all_bets if b.won)
        total_staked = sum(b.stake for b in self.all_bets)
        total_profit = sum(b.profit for b in self.all_bets)
        
        # Per-league stats
        league_reports = {}
        for code, state in self.league_states.items():
            league_reports[code] = {
                "name": state.config.name,
                "bets": state.total_bets,
                "wins": state.wins,
                "win_rate": state.win_rate * 100,
                "profit": state.total_profit,
                "roi": state.roi * 100,
                "expected_roi": state.config.strategy.expected_roi,
                "final_status": self.authorities[code].status,
            }
        
        # Bankroll stats
        if self.bankroll_history:
            peak = max(br for _, br in self.bankroll_history)
            values = [br for _, br in self.bankroll_history]
            max_dd = 0
            peak_so_far = values[0]
            for v in values:
                if v > peak_so_far:
                    peak_so_far = v
                dd = (peak_so_far - v) / peak_so_far
                if dd > max_dd:
                    max_dd = dd
        else:
            peak = self.initial_bankroll
            max_dd = 0
        
        report = {
            "total_bets": total_bets,
            "total_wins": total_wins,
            "win_rate": total_wins / total_bets * 100 if total_bets > 0 else 0,
            "total_staked": total_staked,
            "total_profit": total_profit,
            "roi": total_profit / total_staked * 100 if total_staked > 0 else 0,
            "final_bankroll": self.bankroll,
            "return_pct": (self.bankroll - self.initial_bankroll) / self.initial_bankroll * 100,
            "peak_bankroll": peak,
            "max_drawdown": max_dd * 100,
            "leagues": league_reports,
        }
        
        if verbose:
            self._print_report(report)
        
        return report
    
    def _print_report(self, report: Dict):
        """Print the simulation report."""
        print("\n" + "=" * 80)
        print("SIMULATION RESULTS")
        print("=" * 80)
        
        print(f"\n{'OVERALL':}")
        print(f"  Total bets: {report['total_bets']}")
        print(f"  Win rate: {report['win_rate']:.1f}%")
        print(f"  Total profit: £{report['total_profit']:+.2f}")
        print(f"  ROI: {report['roi']:+.1f}%")
        print(f"  Final bankroll: £{report['final_bankroll']:.2f}")
        print(f"  Total return: {report['return_pct']:+.1f}%")
        print(f"  Max drawdown: {report['max_drawdown']:.1f}%")
        
        print("\n" + "-" * 80)
        print("PER-LEAGUE BREAKDOWN")
        print("-" * 80)
        print(f"{'League':<20} {'Bets':>6} {'Win%':>7} {'Profit':>10} {'ROI':>8} {'Expected':>10} {'Status':>10}")
        print("-" * 80)
        
        for code, data in report['leagues'].items():
            diff = data['roi'] - data['expected_roi']
            diff_marker = "✓" if diff > -5 else "✗"
            print(f"{data['name']:<20} {data['bets']:>6} {data['win_rate']:>6.1f}% "
                  f"£{data['profit']:>+8.2f} {data['roi']:>+7.1f}% "
                  f"{data['expected_roi']:>+9.1f}% {data['final_status']:>10} {diff_marker}")
        
        print("=" * 80)


def compare_with_without_authority():
    """Compare results with and without per-league authority."""
    print("=" * 80)
    print("COMPARISON: WITH vs WITHOUT PER-LEAGUE AUTHORITY")
    print("=" * 80)
    
    # Run with authority
    print("\n--- WITH Per-League Authority ---")
    sim_with = MultiLeagueSimulator(initial_bankroll=1000.0)
    results_with = sim_with.run(verbose=False)
    
    # Run without authority (set all thresholds very high)
    print("\n--- WITHOUT Authority (static betting) ---")
    # Temporarily modify configs
    from league_config import LEAGUE_CONFIGS
    original_thresholds = {}
    
    for code, cfg in LEAGUE_CONFIGS.items():
        if cfg.enabled:
            original_thresholds[code] = (
                cfg.authority.loss_streak_pause,
                cfg.authority.loss_streak_reduce_1,
                cfg.authority.loss_streak_reduce_2,
            )
            cfg.authority.loss_streak_pause = 999
            cfg.authority.loss_streak_reduce_1 = 999
            cfg.authority.loss_streak_reduce_2 = 999
    
    sim_without = MultiLeagueSimulator(initial_bankroll=1000.0)
    results_without = sim_without.run(verbose=False)
    
    # Restore original thresholds
    for code, thresholds in original_thresholds.items():
        LEAGUE_CONFIGS[code].authority.loss_streak_pause = thresholds[0]
        LEAGUE_CONFIGS[code].authority.loss_streak_reduce_1 = thresholds[1]
        LEAGUE_CONFIGS[code].authority.loss_streak_reduce_2 = thresholds[2]
    
    # Print comparison
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print(f"\n{'Metric':<25} {'With Authority':>15} {'Without':>15} {'Difference':>15}")
    print("-" * 70)
    
    metrics = [
        ("Final Bankroll", f"£{results_with['final_bankroll']:.2f}", 
         f"£{results_without['final_bankroll']:.2f}",
         f"£{results_with['final_bankroll'] - results_without['final_bankroll']:+.2f}"),
        ("Total Return %", f"{results_with['return_pct']:+.1f}%",
         f"{results_without['return_pct']:+.1f}%",
         f"{results_with['return_pct'] - results_without['return_pct']:+.1f}%"),
        ("Max Drawdown", f"{results_with['max_drawdown']:.1f}%",
         f"{results_without['max_drawdown']:.1f}%",
         f"{results_with['max_drawdown'] - results_without['max_drawdown']:+.1f}%"),
        ("ROI", f"{results_with['roi']:+.1f}%",
         f"{results_without['roi']:+.1f}%",
         f"{results_with['roi'] - results_without['roi']:+.1f}%"),
    ]
    
    for name, with_val, without_val, diff in metrics:
        print(f"{name:<25} {with_val:>15} {without_val:>15} {diff:>15}")
    
    print("\n" + "=" * 80)
    if results_with['max_drawdown'] < results_without['max_drawdown']:
        print("✓ Authority REDUCED drawdown (better risk management)")
    else:
        print("✗ Authority did not reduce drawdown")
    
    if results_with['final_bankroll'] >= results_without['final_bankroll'] * 0.95:
        print("✓ Authority maintained returns (within 5%)")
    else:
        print("◐ Authority reduced returns (trade-off for safety)")
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-league betting simulation")
    parser.add_argument("--compare", action="store_true", 
                        help="Compare with/without authority")
    parser.add_argument("--leagues", type=str, nargs="+",
                        help="Specific leagues to simulate (e.g., E0 D1)")
    args = parser.parse_args()
    
    if args.compare:
        compare_with_without_authority()
    else:
        leagues = args.leagues if args.leagues else None
        sim = MultiLeagueSimulator(leagues=leagues, initial_bankroll=1000.0)
        sim.run(verbose=True)
