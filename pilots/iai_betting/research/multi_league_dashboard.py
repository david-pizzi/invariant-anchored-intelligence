"""Multi-League Streamlit Dashboard

Interactive dashboard showing:
- Per-league performance comparison
- Bankroll evolution over time
- Authority interventions
- Edge analysis by league

Run with:
    streamlit run pilots/iai_betting/research/multi_league_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add the iai_betting directory to path for imports
iai_betting_dir = Path(__file__).parent.parent
sys.path.insert(0, str(iai_betting_dir))

from core.data import FootballDataLoader, Match
from research.league_config import (
    LEAGUE_CONFIGS, 
    LeagueConfig, 
    get_enabled_leagues,
    get_league_config,
    get_leagues_by_tier,
)
from research.multi_league_simulator import MultiLeagueSimulator, BetRecord

# Page config
st.set_page_config(
    page_title="IAI Multi-League Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DATA LOADING & CACHING
# =============================================================================

@st.cache_data(ttl=3600)
def load_league_analysis():
    """Load edge analysis for all leagues."""
    loader = FootballDataLoader(data_dir="data/football")
    seasons = ["1718", "1819", "1920", "2021", "2122", "2223", "2324"]
    
    results = []
    for code, config in LEAGUE_CONFIGS.items():
        league_data = {
            "code": code,
            "name": config.name,
            "country": config.country,
            "enabled": config.enabled,
            "expected_edge": config.strategy.expected_edge,
            "expected_roi": config.strategy.expected_roi,
            "expected_win_rate": config.strategy.expected_win_rate,
            "min_odds": config.strategy.min_odds,
            "max_odds": config.strategy.max_odds,
            "selection": config.strategy.selection,
        }
        results.append(league_data)
    
    return pd.DataFrame(results)


@st.cache_data(ttl=3600)
def run_simulation(leagues: List[str], initial_bankroll: float, use_authority: bool):
    """Run simulation and return results."""
    # Temporarily disable authority if requested
    if not use_authority:
        for code in leagues:
            cfg = get_league_config(code)
            if cfg:
                cfg.authority.loss_streak_pause = 999
                cfg.authority.loss_streak_reduce_1 = 999
                cfg.authority.loss_streak_reduce_2 = 999
    
    sim = MultiLeagueSimulator(
        leagues=leagues,
        initial_bankroll=initial_bankroll,
    )
    report = sim.run(verbose=False)
    
    # Build dataframes
    bets_df = pd.DataFrame([
        {
            "date": b.date,
            "league": b.league,
            "home_team": b.home_team,
            "away_team": b.away_team,
            "selection": b.selection,
            "odds": b.odds,
            "stake": b.stake,
            "won": b.won,
            "profit": b.profit,
            "authority_status": b.authority_status,
        }
        for b in sim.all_bets
    ])
    
    bankroll_df = pd.DataFrame([
        {"date": d, "bankroll": br}
        for d, br in sim.bankroll_history
    ])
    
    # Restore authority settings
    if not use_authority:
        for code in leagues:
            cfg = get_league_config(code)
            if cfg:
                original = LEAGUE_CONFIGS[code]
                cfg.authority.loss_streak_pause = original.authority.loss_streak_pause
                cfg.authority.loss_streak_reduce_1 = original.authority.loss_streak_reduce_1
                cfg.authority.loss_streak_reduce_2 = original.authority.loss_streak_reduce_2
    
    return report, bets_df, bankroll_df, sim


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar():
    """Render sidebar with controls."""
    st.sidebar.title("⚽ IAI Multi-League")
    st.sidebar.markdown("---")
    
    # League selection
    st.sidebar.subheader("📊 League Selection")
    
    tiers = get_leagues_by_tier()
    
    # Strong edge leagues
    st.sidebar.markdown("**Strong Edge (>3%)**")
    strong_leagues = []
    for cfg in tiers["strong"]:
        if st.sidebar.checkbox(f"{cfg.name} ({cfg.code})", value=cfg.enabled, key=f"league_{cfg.code}"):
            strong_leagues.append(cfg.code)
    
    # Marginal edge leagues
    st.sidebar.markdown("**Marginal Edge (0-3%)**")
    marginal_leagues = []
    for cfg in tiers["marginal"]:
        if st.sidebar.checkbox(f"{cfg.name} ({cfg.code})", value=False, key=f"league_{cfg.code}"):
            marginal_leagues.append(cfg.code)
    
    # No edge leagues (collapsed)
    with st.sidebar.expander("No Edge Leagues (not recommended)"):
        no_edge_leagues = []
        for cfg in tiers["none"]:
            if st.sidebar.checkbox(f"{cfg.name} ({cfg.code})", value=False, key=f"league_{cfg.code}"):
                no_edge_leagues.append(cfg.code)
    
    selected_leagues = strong_leagues + marginal_leagues + no_edge_leagues
    
    st.sidebar.markdown("---")
    
    # Simulation settings
    st.sidebar.subheader("⚙️ Simulation Settings")
    initial_bankroll = st.sidebar.number_input(
        "Initial Bankroll (£)", 
        min_value=100, 
        max_value=100000, 
        value=1000,
        step=100
    )
    
    use_authority = st.sidebar.checkbox("Enable Authority (Risk Management)", value=True)
    
    st.sidebar.markdown("---")
    
    # Run button
    run_sim = st.sidebar.button("🚀 Run Simulation", type="primary", use_container_width=True)
    
    return selected_leagues, initial_bankroll, use_authority, run_sim


# =============================================================================
# MAIN CONTENT
# =============================================================================

def render_league_overview():
    """Render league edge overview."""
    st.header("📊 League Edge Overview")
    
    df = load_league_analysis()
    
    # Create a bar chart of edges
    fig = go.Figure()
    
    # Color by edge tier
    colors = []
    for edge in df["expected_edge"]:
        if edge > 3:
            colors.append("#28a745")  # Green
        elif edge > 0:
            colors.append("#ffc107")  # Yellow
        else:
            colors.append("#dc3545")  # Red
    
    fig.add_trace(go.Bar(
        x=df["name"],
        y=df["expected_edge"],
        marker_color=colors,
        text=[f"{e:+.1f}%" for e in df["expected_edge"]],
        textposition="outside",
    ))
    
    fig.update_layout(
        title="Expected Edge by League (Home @ 4.0-6.0)",
        xaxis_title="League",
        yaxis_title="Edge (%)",
        yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black'),
        height=400,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary table
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Profitable Leagues")
        profitable = df[df["expected_edge"] > 0].sort_values("expected_edge", ascending=False)
        st.dataframe(
            profitable[["name", "expected_edge", "expected_roi", "expected_win_rate"]].rename(columns={
                "name": "League",
                "expected_edge": "Edge %",
                "expected_roi": "ROI %",
                "expected_win_rate": "Win Rate %"
            }),
            hide_index=True
        )
    
    with col2:
        st.subheader("❌ Non-Profitable Leagues")
        non_profitable = df[df["expected_edge"] <= 0].sort_values("expected_edge", ascending=False)
        st.dataframe(
            non_profitable[["name", "expected_edge", "expected_roi", "expected_win_rate"]].rename(columns={
                "name": "League",
                "expected_edge": "Edge %",
                "expected_roi": "ROI %",
                "expected_win_rate": "Win Rate %"
            }),
            hide_index=True
        )


def render_simulation_results(report: Dict, bets_df: pd.DataFrame, bankroll_df: pd.DataFrame):
    """Render simulation results."""
    st.header("📈 Simulation Results")
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Final Bankroll", f"£{report['final_bankroll']:.0f}")
    with col2:
        st.metric("Total Return", f"{report['return_pct']:+.1f}%")
    with col3:
        st.metric("Total Bets", report['total_bets'])
    with col4:
        st.metric("Win Rate", f"{report['win_rate']:.1f}%")
    with col5:
        st.metric("Max Drawdown", f"{report['max_drawdown']:.1f}%")
    
    st.markdown("---")
    
    # Bankroll chart
    st.subheader("💰 Bankroll Evolution")
    
    if not bankroll_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=bankroll_df["date"],
            y=bankroll_df["bankroll"],
            mode="lines",
            name="Bankroll",
            line=dict(color="#2196F3", width=2),
            fill="tozeroy",
            fillcolor="rgba(33, 150, 243, 0.1)"
        ))
        
        fig.update_layout(
            title="Bankroll Over Time",
            xaxis_title="Date",
            yaxis_title="Bankroll (£)",
            height=400,
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Per-league breakdown
    st.subheader("🏆 Per-League Performance")
    
    league_data = []
    for code, data in report['leagues'].items():
        league_data.append({
            "League": data['name'],
            "Bets": data['bets'],
            "Win Rate": f"{data['win_rate']:.1f}%",
            "Profit": f"£{data['profit']:+,.0f}",
            "ROI": f"{data['roi']:+.1f}%",
            "Expected ROI": f"{data['expected_roi']:+.1f}%",
            "Status": data['final_status'],
        })
    
    st.dataframe(pd.DataFrame(league_data), hide_index=True, use_container_width=True)
    
    # Profit by league pie chart
    if len(report['leagues']) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            profits = {data['name']: max(0, data['profit']) for code, data in report['leagues'].items()}
            fig = px.pie(
                names=list(profits.keys()),
                values=list(profits.values()),
                title="Profit Distribution by League"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            bets_count = {data['name']: data['bets'] for code, data in report['leagues'].items()}
            fig = px.pie(
                names=list(bets_count.keys()),
                values=list(bets_count.values()),
                title="Bets Distribution by League"
            )
            st.plotly_chart(fig, use_container_width=True)


def render_authority_analysis(bets_df: pd.DataFrame):
    """Render Authority intervention analysis."""
    st.header("🛡️ Authority Interventions")
    
    if bets_df.empty:
        st.info("Run a simulation to see Authority analysis")
        return
    
    # Count by status
    status_counts = bets_df["authority_status"].value_counts()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Status Distribution")
        for status, count in status_counts.items():
            pct = count / len(bets_df) * 100
            emoji = "✅" if status == "normal" else ("⚠️" if "reduced" in status else "🛑")
            st.write(f"{emoji} **{status}**: {count} bets ({pct:.1f}%)")
    
    with col2:
        fig = px.pie(
            names=status_counts.index,
            values=status_counts.values,
            title="Bets by Authority Status",
            color_discrete_map={
                "normal": "#28a745",
                "reduced_1": "#ffc107",
                "reduced_2": "#fd7e14",
                "paused": "#dc3545"
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Authority status over time
    if "date" in bets_df.columns:
        st.subheader("Authority Status Over Time")
        
        # Add league to the analysis
        bets_df_sorted = bets_df.sort_values("date")
        
        for league in bets_df["league"].unique():
            league_bets = bets_df_sorted[bets_df_sorted["league"] == league]
            
            fig = go.Figure()
            
            status_map = {"normal": 0, "reduced_1": 1, "reduced_2": 2, "paused": 3}
            y_vals = [status_map.get(s, 0) for s in league_bets["authority_status"]]
            
            colors = ["#28a745" if s == "normal" else "#ffc107" if s == "reduced_1" 
                      else "#fd7e14" if s == "reduced_2" else "#dc3545" 
                      for s in league_bets["authority_status"]]
            
            fig.add_trace(go.Scatter(
                x=league_bets["date"],
                y=y_vals,
                mode="markers",
                marker=dict(color=colors, size=8),
                name=league,
                hovertext=[f"{s} - {'Win' if w else 'Loss'}" 
                          for s, w in zip(league_bets["authority_status"], league_bets["won"])]
            ))
            
            fig.update_layout(
                title=f"Authority Status: {LEAGUE_CONFIGS[league].name}",
                xaxis_title="Date",
                yaxis=dict(
                    tickmode="array",
                    tickvals=[0, 1, 2, 3],
                    ticktext=["Normal", "Reduced 1", "Reduced 2", "Paused"]
                ),
                height=250,
            )
            
            st.plotly_chart(fig, use_container_width=True)


def render_bet_browser(bets_df: pd.DataFrame):
    """Render individual bet browser."""
    st.header("📋 Bet Browser")
    
    if bets_df.empty:
        st.info("Run a simulation to see individual bets")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        league_filter = st.multiselect(
            "Filter by League",
            options=bets_df["league"].unique(),
            default=list(bets_df["league"].unique())
        )
    
    with col2:
        result_filter = st.selectbox(
            "Filter by Result",
            options=["All", "Wins", "Losses"]
        )
    
    with col3:
        status_filter = st.multiselect(
            "Filter by Authority Status",
            options=bets_df["authority_status"].unique(),
            default=list(bets_df["authority_status"].unique())
        )
    
    # Apply filters
    filtered_df = bets_df[bets_df["league"].isin(league_filter)]
    filtered_df = filtered_df[filtered_df["authority_status"].isin(status_filter)]
    
    if result_filter == "Wins":
        filtered_df = filtered_df[filtered_df["won"] == True]
    elif result_filter == "Losses":
        filtered_df = filtered_df[filtered_df["won"] == False]
    
    # Display
    display_df = filtered_df.copy()
    display_df["date"] = pd.to_datetime(display_df["date"]).dt.strftime("%Y-%m-%d")
    display_df["profit"] = display_df["profit"].apply(lambda x: f"£{x:+.2f}")
    display_df["stake"] = display_df["stake"].apply(lambda x: f"£{x:.2f}")
    display_df["odds"] = display_df["odds"].apply(lambda x: f"{x:.2f}")
    display_df["won"] = display_df["won"].apply(lambda x: "✅" if x else "❌")
    
    st.dataframe(
        display_df[["date", "league", "home_team", "away_team", "odds", "stake", "won", "profit", "authority_status"]],
        hide_index=True,
        use_container_width=True
    )
    
    st.caption(f"Showing {len(filtered_df)} of {len(bets_df)} bets")


def render_config_viewer():
    """Render configuration viewer."""
    st.header("⚙️ League Configurations")
    
    for code, config in LEAGUE_CONFIGS.items():
        if not config.enabled and config.strategy.expected_edge <= 0:
            continue
            
        with st.expander(f"{config.name} ({code}) - {'✅ Enabled' if config.enabled else '❌ Disabled'}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Strategy Settings**")
                st.write(f"- Selection: {config.strategy.selection}")
                st.write(f"- Odds Range: {config.strategy.min_odds} - {config.strategy.max_odds}")
                st.write(f"- Base Stake: {config.strategy.base_stake_pct}%")
                st.write(f"- Expected Edge: {config.strategy.expected_edge:+.1f}%")
                st.write(f"- Expected ROI: {config.strategy.expected_roi:+.1f}%")
            
            with col2:
                st.markdown("**Authority Thresholds**")
                st.write(f"- Reduce stake after: {config.authority.loss_streak_reduce_1} losses")
                st.write(f"- Reduce more after: {config.authority.loss_streak_reduce_2} losses")
                st.write(f"- Pause after: {config.authority.loss_streak_pause} losses")
                st.write(f"- Win rate warning: {config.authority.win_rate_warning}%")
                st.write(f"- Min bets for analysis: {config.authority.min_bets_for_analysis}")
            
            if config.notes:
                st.info(config.notes)


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Sidebar
    selected_leagues, initial_bankroll, use_authority, run_sim = render_sidebar()
    
    # Title
    st.title("⚽ IAI Multi-League Betting Dashboard")
    st.markdown("Analyze and simulate betting strategies across multiple football leagues")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 League Overview", 
        "📈 Simulation", 
        "🛡️ Authority", 
        "📋 Bets",
        "⚙️ Config"
    ])
    
    # Store simulation results in session state
    if "sim_results" not in st.session_state:
        st.session_state.sim_results = None
        st.session_state.bets_df = pd.DataFrame()
        st.session_state.bankroll_df = pd.DataFrame()
    
    # Run simulation if requested
    if run_sim and selected_leagues:
        with st.spinner("Running simulation..."):
            report, bets_df, bankroll_df, sim = run_simulation(
                selected_leagues, 
                initial_bankroll, 
                use_authority
            )
            st.session_state.sim_results = report
            st.session_state.bets_df = bets_df
            st.session_state.bankroll_df = bankroll_df
        st.success("Simulation complete!")
    
    with tab1:
        render_league_overview()
    
    with tab2:
        if st.session_state.sim_results:
            render_simulation_results(
                st.session_state.sim_results,
                st.session_state.bets_df,
                st.session_state.bankroll_df
            )
        else:
            st.info("👈 Select leagues and click 'Run Simulation' to see results")
    
    with tab3:
        render_authority_analysis(st.session_state.bets_df)
    
    with tab4:
        render_bet_browser(st.session_state.bets_df)
    
    with tab5:
        render_config_viewer()


if __name__ == "__main__":
    main()
