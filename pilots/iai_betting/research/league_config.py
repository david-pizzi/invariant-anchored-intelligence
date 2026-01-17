"""Per-League Configuration for IAI Betting

This module defines league-specific parameters for:
1. Strategy settings (odds ranges, selection types)
2. Authority thresholds (strain detection, stake sizing)
3. Expected performance metrics

LOCAL RESEARCH ONLY - does not affect cloud/production code.

Usage:
    from league_config import LEAGUE_CONFIGS, get_league_config
    
    config = get_league_config("D1")  # Bundesliga
    print(config.strategy.min_odds)   # 4.0
    print(config.authority.loss_streak_reduce_1)  # 5
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List


@dataclass
class StrategyConfig:
    """Strategy parameters for a league."""
    # Core betting parameters
    selection: str = "H"          # H, D, or A
    min_odds: float = 4.0         # Minimum odds to bet
    max_odds: float = 6.0         # Maximum odds to bet
    
    # Stake sizing
    base_stake_pct: float = 3.0   # Base stake as % of bankroll
    
    # Expected performance (from backtesting)
    expected_edge: float = 5.0    # Expected edge %
    expected_win_rate: float = 26.0  # Expected win rate %
    expected_roi: float = 25.0    # Expected ROI %
    
    # Confidence in the edge
    edge_confidence: str = "high"  # high, medium, low
    profitable_seasons: int = 5    # Out of 7 tested
    total_seasons: int = 7


@dataclass
class AuthorityConfig:
    """Authority (risk management) thresholds for a league."""
    # Stake reduction triggers (based on loss streaks)
    loss_streak_reduce_1: int = 5      # Reduce stake after N losses
    loss_streak_reduce_2: int = 8      # Reduce more after N losses
    loss_streak_pause: int = 10        # Pause betting after N losses
    
    # Stake reduction amounts
    stake_reduction_1: float = 0.67    # Reduce to 67% of normal
    stake_reduction_2: float = 0.50    # Reduce to 50% of normal
    
    # Win rate monitoring
    min_bets_for_analysis: int = 20    # Need N bets before analyzing
    win_rate_warning: float = 20.0     # Warning if win rate below
    win_rate_critical: float = 15.0    # Critical if win rate below
    
    # Recovery thresholds
    wins_to_restore_stake: int = 3     # Wins needed to restore stake
    
    # Edge decay detection
    edge_decay_window: int = 50        # Rolling window for edge calc
    edge_decay_threshold: float = -2.0 # Alert if edge drops below


@dataclass
class LeagueConfig:
    """Complete configuration for a league."""
    code: str                      # E.g., "E0", "D1"
    name: str                      # E.g., "Premier League"
    country: str                   # E.g., "England"
    
    # Season info
    matches_per_season: int        # Typical matches per season
    season_start_month: int = 8    # August
    season_end_month: int = 5      # May
    
    # Strategy and Authority configs
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    authority: AuthorityConfig = field(default_factory=AuthorityConfig)
    
    # Status
    enabled: bool = True           # Is this league active for tracking?
    notes: str = ""                # Any special notes


# =============================================================================
# LEAGUE CONFIGURATIONS
# =============================================================================
# Based on multi_league_analysis.py results (2017-2024 data)

LEAGUE_CONFIGS: Dict[str, LeagueConfig] = {
    
    # =========================================================================
    # TIER 1: STRONG EDGE (>3%) - Recommended for live tracking
    # =========================================================================
    
    "E0": LeagueConfig(
        code="E0",
        name="Premier League",
        country="England",
        matches_per_season=380,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=3.0,
            expected_edge=5.6,
            expected_win_rate=27.1,
            expected_roi=27.5,
            edge_confidence="high",
            profitable_seasons=5,
            total_seasons=7,
        ),
        authority=AuthorityConfig(
            loss_streak_reduce_1=5,
            loss_streak_reduce_2=8,
            loss_streak_pause=10,
            min_bets_for_analysis=20,
            win_rate_warning=20.0,
            win_rate_critical=15.0,
            wins_to_restore_stake=3,
        ),
        enabled=True,
        notes="Baseline league. Edge validated over 9 seasons.",
    ),
    
    "D1": LeagueConfig(
        code="D1",
        name="Bundesliga",
        country="Germany",
        matches_per_season=306,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=3.0,
            expected_edge=4.3,
            expected_win_rate=25.9,
            expected_roi=21.7,
            edge_confidence="high",
            profitable_seasons=6,
            total_seasons=7,
        ),
        authority=AuthorityConfig(
            # Slightly tighter thresholds due to fewer matches
            loss_streak_reduce_1=4,
            loss_streak_reduce_2=7,
            loss_streak_pause=9,
            min_bets_for_analysis=15,  # Fewer bets per season
            win_rate_warning=19.0,
            win_rate_critical=14.0,
            wins_to_restore_stake=3,
        ),
        enabled=True,
        notes="Strong edge similar to EPL. Fewer matches per season.",
    ),
    
    # =========================================================================
    # TIER 2: MARGINAL EDGE (1-3%) - Monitor only
    # =========================================================================
    
    "B1": LeagueConfig(
        code="B1",
        name="Jupiler League",
        country="Belgium",
        matches_per_season=306,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=2.0,  # Lower stake due to lower confidence
            expected_edge=1.2,
            expected_win_rate=22.8,
            expected_roi=6.8,
            edge_confidence="medium",
            profitable_seasons=4,
            total_seasons=7,
        ),
        authority=AuthorityConfig(
            loss_streak_reduce_1=4,
            loss_streak_reduce_2=6,
            loss_streak_pause=8,
            min_bets_for_analysis=20,
            win_rate_warning=17.0,
            win_rate_critical=12.0,
            wins_to_restore_stake=3,
        ),
        enabled=False,  # Monitor only, not active
        notes="Marginal edge. Needs more data before activating.",
    ),
    
    # =========================================================================
    # TIER 3: NO EDGE - Strategy doesn't work, but could explore alternatives
    # =========================================================================
    
    "SP1": LeagueConfig(
        code="SP1",
        name="La Liga",
        country="Spain",
        matches_per_season=380,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=0.0,  # No betting - edge is negative
            expected_edge=-3.7,
            expected_win_rate=17.8,
            expected_roi=-16.2,
            edge_confidence="none",
            profitable_seasons=3,
            total_seasons=7,
        ),
        authority=AuthorityConfig(),  # Default, not used
        enabled=False,
        notes="No edge at 4.0-6.0. Consider exploring other ranges.",
    ),
    
    "I1": LeagueConfig(
        code="I1",
        name="Serie A",
        country="Italy",
        matches_per_season=380,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=0.0,
            expected_edge=-6.0,
            expected_win_rate=15.2,
            expected_roi=-27.3,
            edge_confidence="none",
            profitable_seasons=2,
            total_seasons=7,
        ),
        authority=AuthorityConfig(),
        enabled=False,
        notes="No edge. Italian home underdogs underperform significantly.",
    ),
    
    "F1": LeagueConfig(
        code="F1",
        name="Ligue 1",
        country="France",
        matches_per_season=380,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=0.0,
            expected_edge=-4.1,
            expected_win_rate=17.8,
            expected_roi=-17.8,
            edge_confidence="none",
            profitable_seasons=1,
            total_seasons=7,
        ),
        authority=AuthorityConfig(),
        enabled=False,
        notes="No edge. Only 1/7 seasons profitable.",
    ),
    
    "E1": LeagueConfig(
        code="E1",
        name="Championship",
        country="England",
        matches_per_season=552,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=0.0,
            expected_edge=-2.6,
            expected_win_rate=19.4,
            expected_roi=-10.6,
            edge_confidence="none",
            profitable_seasons=3,
            total_seasons=7,
        ),
        authority=AuthorityConfig(),
        enabled=False,
        notes="No edge. EPL edge doesn't carry down to Championship.",
    ),
    
    "E2": LeagueConfig(
        code="E2",
        name="League One",
        country="England",
        matches_per_season=552,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=0.0,
            expected_edge=-3.1,
            expected_win_rate=19.0,
            expected_roi=-13.0,
            edge_confidence="none",
            profitable_seasons=1,
            total_seasons=7,
        ),
        authority=AuthorityConfig(),
        enabled=False,
        notes="No edge.",
    ),
    
    "SC0": LeagueConfig(
        code="SC0",
        name="Scottish Premiership",
        country="Scotland",
        matches_per_season=228,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=0.0,
            expected_edge=-2.4,
            expected_win_rate=19.4,
            expected_roi=-10.0,
            edge_confidence="none",
            profitable_seasons=2,
            total_seasons=7,
        ),
        authority=AuthorityConfig(),
        enabled=False,
        notes="No edge. Small sample size per season.",
    ),
    
    "N1": LeagueConfig(
        code="N1",
        name="Eredivisie",
        country="Netherlands",
        matches_per_season=306,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=0.0,
            expected_edge=-2.9,
            expected_win_rate=18.3,
            expected_roi=-12.6,
            edge_confidence="none",
            profitable_seasons=3,
            total_seasons=7,
        ),
        authority=AuthorityConfig(),
        enabled=False,
        notes="No edge. High variance between seasons.",
    ),
    
    "P1": LeagueConfig(
        code="P1",
        name="Primeira Liga",
        country="Portugal",
        matches_per_season=306,
        strategy=StrategyConfig(
            selection="H",
            min_odds=4.0,
            max_odds=6.0,
            base_stake_pct=0.0,
            expected_edge=-5.5,
            expected_win_rate=15.7,
            expected_roi=-24.8,
            edge_confidence="none",
            profitable_seasons=2,
            total_seasons=7,
        ),
        authority=AuthorityConfig(),
        enabled=False,
        notes="No edge. Home underdogs heavily underperform.",
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_league_config(league_code: str) -> Optional[LeagueConfig]:
    """Get configuration for a specific league."""
    return LEAGUE_CONFIGS.get(league_code.upper())


def get_enabled_leagues() -> List[LeagueConfig]:
    """Get all leagues that are enabled for tracking."""
    return [cfg for cfg in LEAGUE_CONFIGS.values() if cfg.enabled]


def get_leagues_by_tier() -> Dict[str, List[LeagueConfig]]:
    """Group leagues by edge tier."""
    tiers = {
        "strong": [],    # Edge > 3%
        "marginal": [],  # Edge 0-3%
        "none": [],      # Edge <= 0
    }
    
    for cfg in LEAGUE_CONFIGS.values():
        if cfg.strategy.expected_edge > 3.0:
            tiers["strong"].append(cfg)
        elif cfg.strategy.expected_edge > 0:
            tiers["marginal"].append(cfg)
        else:
            tiers["none"].append(cfg)
    
    return tiers


def print_config_summary():
    """Print a summary of all league configurations."""
    print("=" * 80)
    print("LEAGUE CONFIGURATION SUMMARY")
    print("=" * 80)
    
    tiers = get_leagues_by_tier()
    
    print("\n✓ STRONG EDGE (>3%) - Recommended for live tracking:")
    print("-" * 80)
    for cfg in tiers["strong"]:
        status = "ENABLED" if cfg.enabled else "disabled"
        print(f"  {cfg.code}: {cfg.name:<20} | Edge: {cfg.strategy.expected_edge:+.1f}% | "
              f"ROI: {cfg.strategy.expected_roi:+.1f}% | [{status}]")
        print(f"       Strategy: {cfg.strategy.selection} @ {cfg.strategy.min_odds}-{cfg.strategy.max_odds} | "
              f"Stake: {cfg.strategy.base_stake_pct}%")
        print(f"       Authority: Reduce stake after {cfg.authority.loss_streak_reduce_1} losses | "
              f"Pause after {cfg.authority.loss_streak_pause}")
    
    print("\n◐ MARGINAL EDGE (0-3%) - Monitor only:")
    print("-" * 80)
    for cfg in tiers["marginal"]:
        status = "ENABLED" if cfg.enabled else "disabled"
        print(f"  {cfg.code}: {cfg.name:<20} | Edge: {cfg.strategy.expected_edge:+.1f}% | "
              f"ROI: {cfg.strategy.expected_roi:+.1f}% | [{status}]")
    
    print("\n✗ NO EDGE - Strategy doesn't work:")
    print("-" * 80)
    for cfg in tiers["none"]:
        print(f"  {cfg.code}: {cfg.name:<20} | Edge: {cfg.strategy.expected_edge:+.1f}% | "
              f"ROI: {cfg.strategy.expected_roi:+.1f}%")
    
    print("\n" + "=" * 80)
    enabled = get_enabled_leagues()
    print(f"ENABLED LEAGUES: {', '.join(c.code for c in enabled)}")
    print("=" * 80)


# =============================================================================
# VALIDATION
# =============================================================================

def validate_authority_thresholds(config: LeagueConfig) -> List[str]:
    """Validate that authority thresholds are sensible."""
    issues = []
    auth = config.authority
    strat = config.strategy
    
    # Loss streak thresholds should be progressive
    if auth.loss_streak_reduce_1 >= auth.loss_streak_reduce_2:
        issues.append(f"{config.code}: loss_streak_reduce_1 should be < reduce_2")
    
    if auth.loss_streak_reduce_2 >= auth.loss_streak_pause:
        issues.append(f"{config.code}: loss_streak_reduce_2 should be < pause")
    
    # Win rate thresholds should be below expected
    if auth.win_rate_warning >= strat.expected_win_rate:
        issues.append(f"{config.code}: win_rate_warning should be < expected_win_rate")
    
    # Min bets should allow for meaningful analysis
    if auth.min_bets_for_analysis < 10:
        issues.append(f"{config.code}: min_bets_for_analysis should be >= 10")
    
    return issues


def validate_all_configs() -> List[str]:
    """Validate all league configurations."""
    all_issues = []
    for code, config in LEAGUE_CONFIGS.items():
        if config.enabled:
            issues = validate_authority_thresholds(config)
            all_issues.extend(issues)
    return all_issues


if __name__ == "__main__":
    print_config_summary()
    
    print("\n\nVALIDATION:")
    issues = validate_all_configs()
    if issues:
        for issue in issues:
            print(f"  ⚠ {issue}")
    else:
        print("  ✓ All enabled configurations are valid")
