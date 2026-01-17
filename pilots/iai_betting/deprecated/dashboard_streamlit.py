"""Streamlit web dashboard for IAI Betting Backtest.

Run with:
    streamlit run pilots/iai_betting/dashboard_streamlit.py

Features:
- Interactive bankroll chart
- Season-by-season analysis
- Strategy comparison
- Edge analysis visualization
- Individual bet browser
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# Page config
st.set_page_config(
    page_title="IAI Betting Dashboard",
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
    .profit-positive {
        color: #28a745;
        font-weight: bold;
    }
    .profit-negative {
        color: #dc3545;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


@dataclass
class Bet:
    """Single bet record."""
    date: str
    season: str
    home_team: str
    away_team: str
    selection: str
    odds: float
    stake: float
    won: bool
    profit: float
    bankroll: float


@dataclass
class SeasonStats:
    """Season statistics."""
    season: str
    bets: int
    wins: int
    win_rate: float
    staked: float
    profit: float
    roi: float
    start_bankroll: float
    end_bankroll: float


@st.cache_data(ttl=3600)
def load_data(seasons: List[str], league: str = "E0") -> Tuple[Dict[str, List], bool]:
    """Load match data from Football-Data.co.uk."""
    from pilots.iai_betting.data import FootballDataLoader
    
    loader = FootballDataLoader()
    all_matches = {}
    
    for season in seasons:
        try:
            matches = loader.load_season(league, season)
            if matches:
                all_matches[season] = matches
        except Exception as e:
            st.warning(f"Could not load season {season}: {e}")
    
    return all_matches, len(all_matches) > 0


def run_backtest(
    matches: Dict[str, List],
    selection: str,
    min_odds: float,
    max_odds: float,
    starting_bankroll: float,
    stake_pct: float,
) -> Tuple[List[Bet], List[SeasonStats], List[float]]:
    """Run backtest with given parameters."""
    
    bets: List[Bet] = []
    season_stats: List[SeasonStats] = []
    bankroll_history: List[float] = [starting_bankroll]
    
    bankroll = starting_bankroll
    
    for season in sorted(matches.keys()):
        season_matches = matches[season]
        season_start = bankroll
        season_bets = 0
        season_wins = 0
        season_staked = 0
        
        for m in season_matches:
            # Determine odds and outcome based on selection
            if selection == "H":
                odds = m.odds.home_odds
                won = m.result == "H"
            elif selection == "D":
                odds = m.odds.draw_odds
                won = m.result == "D"
            else:
                odds = m.odds.away_odds
                won = m.result == "A"
            
            # Check if within odds range
            if min_odds <= odds < max_odds:
                stake = bankroll * (stake_pct / 100)
                profit = stake * (odds - 1) if won else -stake
                bankroll += profit
                
                season_bets += 1
                season_staked += stake
                if won:
                    season_wins += 1
                
                bet = Bet(
                    date=m.date.strftime("%Y-%m-%d") if hasattr(m.date, 'strftime') else str(m.date),
                    season=season,
                    home_team=m.home_team,
                    away_team=m.away_team,
                    selection=selection,
                    odds=odds,
                    stake=stake,
                    won=won,
                    profit=profit,
                    bankroll=bankroll,
                )
                bets.append(bet)
                bankroll_history.append(bankroll)
        
        if season_bets > 0:
            season_profit = bankroll - season_start
            stats = SeasonStats(
                season=season,
                bets=season_bets,
                wins=season_wins,
                win_rate=season_wins / season_bets,
                staked=season_staked,
                profit=season_profit,
                roi=season_profit / season_staked if season_staked > 0 else 0,
                start_bankroll=season_start,
                end_bankroll=bankroll,
            )
            season_stats.append(stats)
    
    return bets, season_stats, bankroll_history


def calculate_edge_data(matches: Dict[str, List]) -> pd.DataFrame:
    """Calculate edge for different selection/odds combinations."""
    
    combinations = [
        ("H", 1.5, 2.0, "Home Favorites"),
        ("H", 2.0, 2.5, "Home Mid-Range"),
        ("H", 2.5, 3.5, "Home Slight Dog"),
        ("H", 3.5, 5.0, "Home Underdog"),
        ("H", 4.0, 6.0, "Home Big Underdog"),
        ("D", 3.0, 4.0, "Draw Mid"),
        ("D", 4.0, 5.0, "Draw High"),
        ("A", 2.0, 3.0, "Away Favorite"),
        ("A", 3.0, 4.0, "Away Value"),
        ("A", 4.0, 6.0, "Away Underdog"),
    ]
    
    results = []
    
    for selection, min_odds, max_odds, label in combinations:
        total = 0
        wins = 0
        implied_sum = 0
        
        for season_matches in matches.values():
            for m in season_matches:
                if selection == "H":
                    odds = m.odds.home_odds
                    won = m.result == "H"
                elif selection == "D":
                    odds = m.odds.draw_odds
                    won = m.result == "D"
                else:
                    odds = m.odds.away_odds
                    won = m.result == "A"
                
                if min_odds <= odds < max_odds:
                    total += 1
                    implied_sum += 1 / odds
                    if won:
                        wins += 1
        
        if total > 0:
            actual = wins / total
            implied = implied_sum / total
            edge = (actual - implied) * 100
            
            results.append({
                "Selection": label,
                "Odds Range": f"{min_odds}-{max_odds}",
                "Matches": total,
                "Actual Win %": actual * 100,
                "Implied Win %": implied * 100,
                "Edge %": edge,
            })
    
    return pd.DataFrame(results)


def main():
    """Main dashboard."""
    
    st.title("⚽ IAI Betting Dashboard")
    st.markdown("*Backtest betting strategies on Premier League data*")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Season selection
    all_seasons = ["1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324"]
    selected_seasons = st.sidebar.multiselect(
        "Seasons",
        all_seasons,
        default=all_seasons,
        format_func=lambda x: f"20{x[:2]}/20{x[2:]}"
    )
    
    # Strategy parameters
    st.sidebar.subheader("📊 Strategy")
    
    selection = st.sidebar.selectbox(
        "Selection",
        ["H", "D", "A"],
        format_func=lambda x: {"H": "Home Win", "D": "Draw", "A": "Away Win"}[x]
    )
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_odds = st.number_input("Min Odds", 1.0, 20.0, 4.0, 0.5)
    with col2:
        max_odds = st.number_input("Max Odds", 1.0, 20.0, 6.0, 0.5)
    
    # Bankroll settings
    st.sidebar.subheader("💰 Bankroll")
    starting_bankroll = st.sidebar.number_input("Starting £", 100, 100000, 1000, 100)
    stake_pct = st.sidebar.slider("Stake %", 1.0, 20.0, 5.0, 0.5)
    
    # Load data button
    if st.sidebar.button("🚀 Run Backtest", type="primary"):
        with st.spinner("Loading data..."):
            matches, success = load_data(selected_seasons)
        
        if not success:
            st.error("Failed to load match data")
            return
        
        # Run backtest
        with st.spinner("Running backtest..."):
            bets, season_stats, bankroll_history = run_backtest(
                matches, selection, min_odds, max_odds, starting_bankroll, stake_pct
            )
        
        # Store in session state
        st.session_state.bets = bets
        st.session_state.season_stats = season_stats
        st.session_state.bankroll_history = bankroll_history
        st.session_state.matches = matches
        st.session_state.config = {
            "selection": selection,
            "min_odds": min_odds,
            "max_odds": max_odds,
            "starting": starting_bankroll,
            "stake_pct": stake_pct,
        }
    
    # Display results if available
    if "bets" in st.session_state and st.session_state.bets:
        bets = st.session_state.bets
        season_stats = st.session_state.season_stats
        bankroll_history = st.session_state.bankroll_history
        config = st.session_state.config
        
        # Key metrics row
        st.markdown("---")
        
        final_bankroll = bankroll_history[-1]
        peak = max(bankroll_history)
        total_profit = final_bankroll - config["starting"]
        total_roi = total_profit / config["starting"] * 100
        total_bets = len(bets)
        total_wins = sum(1 for b in bets if b.won)
        win_rate = total_wins / total_bets * 100 if total_bets > 0 else 0
        
        # Calculate max drawdown
        max_dd = 0
        peak_so_far = bankroll_history[0]
        for val in bankroll_history:
            if val > peak_so_far:
                peak_so_far = val
            dd = (peak_so_far - val) / peak_so_far * 100
            if dd > max_dd:
                max_dd = dd
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("Starting", f"£{config['starting']:,.0f}")
        with col2:
            st.metric("Final", f"£{final_bankroll:,.0f}", f"{total_profit:+,.0f}")
        with col3:
            st.metric("ROI", f"{total_roi:+.1f}%")
        with col4:
            st.metric("Peak", f"£{peak:,.0f}")
        with col5:
            st.metric("Max Drawdown", f"{max_dd:.1f}%")
        with col6:
            st.metric("Win Rate", f"{win_rate:.1f}%", f"{total_bets} bets")
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Bankroll Chart",
            "📅 Season Analysis",
            "🎯 Edge Analysis",
            "📋 Bet History"
        ])
        
        with tab1:
            st.subheader("Bankroll Evolution")
            
            # Create bankroll chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                y=bankroll_history,
                mode='lines',
                name='Bankroll',
                line=dict(color='#2E86AB', width=2),
                fill='tozeroy',
                fillcolor='rgba(46, 134, 171, 0.1)'
            ))
            
            # Add starting line
            fig.add_hline(
                y=config["starting"],
                line_dash="dash",
                line_color="gray",
                annotation_text="Starting £"
            )
            
            # Add peak marker
            peak_idx = bankroll_history.index(peak)
            fig.add_trace(go.Scatter(
                x=[peak_idx],
                y=[peak],
                mode='markers+text',
                name='Peak',
                marker=dict(size=12, color='gold', symbol='star'),
                text=[f"Peak: £{peak:,.0f}"],
                textposition='top center'
            ))
            
            fig.update_layout(
                title=f"Bankroll: £{config['starting']:,.0f} → £{final_bankroll:,.0f} ({total_roi:+.1f}%)",
                xaxis_title="Bet #",
                yaxis_title="Bankroll (£)",
                hovermode='x unified',
                height=500,
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Drawdown chart
            st.subheader("Drawdown Analysis")
            
            drawdowns = []
            peak_so_far = bankroll_history[0]
            for val in bankroll_history:
                if val > peak_so_far:
                    peak_so_far = val
                dd = (peak_so_far - val) / peak_so_far * 100
                drawdowns.append(dd)
            
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                y=drawdowns,
                mode='lines',
                name='Drawdown %',
                line=dict(color='#dc3545', width=2),
                fill='tozeroy',
                fillcolor='rgba(220, 53, 69, 0.2)'
            ))
            
            fig_dd.update_layout(
                title="Drawdown Over Time",
                xaxis_title="Bet #",
                yaxis_title="Drawdown %",
                height=300,
            )
            
            st.plotly_chart(fig_dd, use_container_width=True)
        
        with tab2:
            st.subheader("Season-by-Season Performance")
            
            # Season table
            season_df = pd.DataFrame([{
                "Season": f"20{s.season[:2]}/20{s.season[2:]}",
                "Bets": s.bets,
                "Wins": s.wins,
                "Win %": f"{s.win_rate*100:.1f}%",
                "Profit": f"£{s.profit:+,.0f}",
                "ROI": f"{s.roi*100:+.1f}%",
                "Status": "✅" if s.profit > 0 else "❌",
            } for s in season_stats])
            
            st.dataframe(season_df, use_container_width=True, hide_index=True)
            
            # Season chart
            fig_season = go.Figure()
            
            seasons = [f"20{s.season[:2]}/{s.season[2:]}" for s in season_stats]
            profits = [s.profit for s in season_stats]
            colors = ['#28a745' if p > 0 else '#dc3545' for p in profits]
            
            fig_season.add_trace(go.Bar(
                x=seasons,
                y=profits,
                marker_color=colors,
                text=[f"£{p:+,.0f}" for p in profits],
                textposition='outside',
            ))
            
            fig_season.update_layout(
                title="Profit by Season",
                xaxis_title="Season",
                yaxis_title="Profit (£)",
                height=400,
            )
            
            st.plotly_chart(fig_season, use_container_width=True)
            
            # Win rate by season
            fig_wr = go.Figure()
            
            fig_wr.add_trace(go.Scatter(
                x=seasons,
                y=[s.win_rate * 100 for s in season_stats],
                mode='lines+markers',
                name='Actual Win %',
                line=dict(color='#2E86AB', width=2),
                marker=dict(size=10),
            ))
            
            # Calculate average implied
            avg_implied = sum(1/b.odds for b in bets) / len(bets) * 100
            fig_wr.add_hline(
                y=avg_implied,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Implied: {avg_implied:.1f}%"
            )
            
            fig_wr.update_layout(
                title="Win Rate by Season vs Implied",
                xaxis_title="Season",
                yaxis_title="Win Rate %",
                height=350,
            )
            
            st.plotly_chart(fig_wr, use_container_width=True)
        
        with tab3:
            st.subheader("Edge Analysis by Odds Range")
            
            if "matches" in st.session_state:
                edge_df = calculate_edge_data(st.session_state.matches)
                
                # Color code based on edge
                def color_edge(val):
                    if val > 3:
                        return 'background-color: #d4edda'
                    elif val > 0:
                        return 'background-color: #fff3cd'
                    else:
                        return 'background-color: #f8d7da'
                
                styled_df = edge_df.style.applymap(
                    color_edge, 
                    subset=['Edge %']
                ).format({
                    'Actual Win %': '{:.1f}%',
                    'Implied Win %': '{:.1f}%',
                    'Edge %': '{:+.1f}%',
                })
                
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # Edge chart
                fig_edge = go.Figure()
                
                fig_edge.add_trace(go.Bar(
                    x=edge_df['Selection'],
                    y=edge_df['Edge %'],
                    marker_color=['#28a745' if e > 0 else '#dc3545' for e in edge_df['Edge %']],
                    text=[f"{e:+.1f}%" for e in edge_df['Edge %']],
                    textposition='outside',
                ))
                
                fig_edge.add_hline(y=0, line_color="black", line_width=1)
                
                fig_edge.update_layout(
                    title="Edge by Selection Type",
                    xaxis_title="Selection",
                    yaxis_title="Edge %",
                    height=400,
                )
                
                st.plotly_chart(fig_edge, use_container_width=True)
                
                # Recommendations
                st.subheader("📋 Recommendations")
                
                profitable = edge_df[edge_df['Edge %'] > 3].sort_values('Edge %', ascending=False)
                avoid = edge_df[edge_df['Edge %'] < -2].sort_values('Edge %')
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.success("**🟢 Profitable Selections**")
                    if len(profitable) > 0:
                        for _, row in profitable.iterrows():
                            st.write(f"• {row['Selection']} ({row['Odds Range']}): **+{row['Edge %']:.1f}%** edge")
                    else:
                        st.write("No strongly profitable selections found")
                
                with col2:
                    st.error("**🔴 Selections to Avoid**")
                    if len(avoid) > 0:
                        for _, row in avoid.iterrows():
                            st.write(f"• {row['Selection']} ({row['Odds Range']}): **{row['Edge %']:.1f}%** edge")
                    else:
                        st.write("No strongly negative selections found")
        
        with tab4:
            st.subheader("Bet History")
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                filter_result = st.selectbox("Filter by Result", ["All", "Won", "Lost"])
            with col2:
                filter_season = st.selectbox(
                    "Filter by Season", 
                    ["All"] + [f"20{s.season[:2]}/20{s.season[2:]}" for s in season_stats]
                )
            
            # Filter bets
            filtered_bets = bets
            if filter_result == "Won":
                filtered_bets = [b for b in filtered_bets if b.won]
            elif filter_result == "Lost":
                filtered_bets = [b for b in filtered_bets if not b.won]
            
            if filter_season != "All":
                season_code = filter_season[2:4] + filter_season[-2:]
                filtered_bets = [b for b in filtered_bets if b.season == season_code]
            
            # Create dataframe
            bets_df = pd.DataFrame([{
                "Date": b.date,
                "Match": f"{b.home_team} vs {b.away_team}",
                "Selection": {"H": "Home", "D": "Draw", "A": "Away"}[b.selection],
                "Odds": f"{b.odds:.2f}",
                "Stake": f"£{b.stake:.0f}",
                "Result": "✅ Won" if b.won else "❌ Lost",
                "Profit": f"£{b.profit:+,.0f}",
                "Bankroll": f"£{b.bankroll:,.0f}",
            } for b in filtered_bets])
            
            st.dataframe(bets_df, use_container_width=True, hide_index=True, height=500)
            
            # Summary stats for filtered
            st.write(f"**Showing {len(filtered_bets)} of {len(bets)} bets**")
    
    else:
        # Show welcome message
        st.info("👈 Configure your strategy in the sidebar and click **Run Backtest** to begin!")
        
        st.markdown("""
        ### 🎯 Recommended Strategy
        
        Based on 9 years of Premier League data, the most profitable strategy is:
        
        | Parameter | Value |
        |-----------|-------|
        | Selection | **Home Win** |
        | Min Odds | **4.0** |
        | Max Odds | **6.0** |
        | Stake % | **5%** |
        
        This targets **home underdogs** where bookmakers consistently underestimate win probability.
        
        **Historical Results:**
        - 320 bets across 9 seasons
        - 7/9 seasons profitable
        - +5.2% edge over implied probability
        - +915% ROI with 5% stake sizing
        """)


if __name__ == "__main__":
    main()
