"""
Forex IAI Dashboard
Visualizes rolling evaluation results and strategy adaptation
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys
from pathlib import Path
import io
import contextlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pilots.iai_forex.test_rolling_iai import rolling_iai_evaluation
from pilots.iai_forex.core.strategies import STRATEGIES


st.set_page_config(
    page_title="Forex IAI Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Forex IAI Dashboard")
st.markdown("**Invariant-Anchored Intelligence for Forex Trading**")

st.info("""
📊 **How This Works:**
- **Evaluation Metrics** (Sharpe, Return %): Based on 90-day historical backtests used to select best strategy
- **Capital & Profit**: Based on forward-looking trades in the next re-evaluation period
- This simulates realistic trading where decisions are made on historical data, then executed going forward

⚠️ **Data Granularity:** YFinance provides hourly data for ~60 days only. For historical analysis (2022-2024), daily candles are used automatically.
For high-frequency trading analysis, use recent dates (last 60 days) to get hourly data.
""")

st.markdown("---")

# Sidebar controls
st.sidebar.header("Configuration")

pair = st.sidebar.selectbox("Currency Pair", ["EUR/USD", "GBP/USD", "USD/JPY"], index=0)
start_date = st.sidebar.date_input("Start Date", datetime(2022, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime(2024, 1, 1))

# Add preset for recent high-frequency analysis
use_recent = st.sidebar.checkbox("🔥 High-Frequency Mode (last 60 days with hourly data)", value=False)
if use_recent:
    from datetime import date, timedelta
    end_date = date.today()
    start_date = end_date - timedelta(days=60)
    st.sidebar.success(f"Using {start_date} to {end_date}")

eval_window = st.sidebar.slider("Evaluation Window (days)", 30, 180, 90)
reeval_freq = st.sidebar.slider("Re-evaluation Frequency (days)", 1, 14, 7)
forward_window = st.sidebar.slider("Forward P&L Window (days)", 1, 30, 7, help="With HOURLY data, even 1 day = 24 candles for indicators!")
initial_capital = st.sidebar.number_input("Initial Capital ($)", min_value=1000, max_value=1000000, value=10000, step=1000)

run_button = st.sidebar.button("🚀 Run Evaluation", type="primary")

# Cache the evaluation results
@st.cache_data(show_spinner=False)
def run_evaluation(pair, start, end, window, freq, fwd_window, init_cap):
    """Run the rolling evaluation and cache results"""
    # Suppress print output
    with contextlib.redirect_stdout(io.StringIO()):
        decisions = rolling_iai_evaluation(
            pair=pair,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            evaluation_window=window,
            re_eval_frequency=freq,
            forward_window_days=fwd_window,
            initial_capital=init_cap
        )
    return decisions

if run_button or 'decisions' not in st.session_state:
    with st.spinner("Running rolling evaluation..."):
        try:
            decisions = run_evaluation(
                pair, start_date, end_date, 
                eval_window, reeval_freq, forward_window, initial_capital
            )
            st.session_state.decisions = decisions
            st.session_state.config = {
                'pair': pair,
                'start': start_date,
                'end': end_date,
                'window': eval_window,
                'freq': reeval_freq,
                'initial_capital': initial_capital
            }
            st.success(f"✅ Completed {len(decisions)} evaluations!")
        except Exception as e:
            st.error(f"Error: {type(e).__name__}: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

if 'decisions' not in st.session_state:
    st.info("👈 Click 'Run Evaluation' to start")
    st.stop()

decisions = st.session_state.decisions
config = st.session_state.config

# Convert to DataFrame
df = pd.DataFrame(decisions)
# Handle timezone-aware datetimes
df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_localize(None)

# Summary metrics
st.header("📊 Summary")

# Money metrics (most important!)
final_capital = df['capital_after'].iloc[-1]
initial_capital = df['capital_before'].iloc[0]
total_profit = final_capital - initial_capital
total_return_pct = (final_capital / initial_capital - 1) * 100

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Initial Capital", 
        f"${initial_capital:,.0f}",
        help="Starting capital"
    )

with col2:
    st.metric(
        "Final Capital", 
        f"${final_capital:,.0f}",
        delta=f"${total_profit:,.0f}",
        help="Current capital after all trades"
    )

with col3:
    st.metric(
        "Total Profit", 
        f"${total_profit:,.0f}",
        delta=f"{total_return_pct:.1f}%",
        help="Total profit/loss in dollars"
    )

with col4:
    st.metric(
        "Total Return", 
        f"{total_return_pct:.1f}%",
        help="Percentage return on initial capital"
    )

# Action metrics
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Evaluations", len(decisions))

with col2:
    continues = len([d for d in decisions if d['action'] == 'CONTINUE'])
    st.metric("CONTINUE", continues, delta=f"{continues/len(decisions)*100:.0f}%")

with col3:
    switches = len([d for d in decisions if d['action'] == 'SWITCH'])
    st.metric("SWITCH", switches, delta=f"{switches/len(decisions)*100:.0f}%")

with col4:
    pauses = len([d for d in decisions if d['action'] == 'PAUSE'])
    st.metric("PAUSE", pauses, delta=f"{pauses/len(decisions)*100:.0f}%")

with col5:
    resumes = len([d for d in decisions if d['action'] == 'RESUME'])
    st.metric("RESUME", resumes)

st.markdown("---")

# Capital Growth Chart
st.header("💰 Capital Growth Over Time")

fig_capital = go.Figure()

# Capital line
fig_capital.add_trace(go.Scatter(
    x=df['date'],
    y=df['capital_after'],
    mode='lines',
    name='Capital',
    line=dict(color='#2ecc71', width=3),
    fill='tonexty',
    fillcolor='rgba(46, 204, 113, 0.1)'
))

# Initial capital reference line
fig_capital.add_hline(
    y=initial_capital, 
    line_dash="dash", 
    line_color="gray", 
    annotation_text=f"Initial: ${initial_capital:,.0f}",
    annotation_position="right"
)

# Mark strategy switches
switches_df = df[df['action'].isin(['SWITCH', 'RESUME'])].copy()
if len(switches_df) > 0:
    fig_capital.add_trace(go.Scatter(
        x=switches_df['date'],
        y=switches_df['capital_after'],
        mode='markers',
        name='Strategy Change',
        marker=dict(
            size=12,
            symbol='star',
            color='gold',
            line=dict(color='black', width=2)
        ),
        hovertemplate='<b>%{text}</b><br>Capital: $%{y:,.0f}<extra></extra>',
        text=[f"{row['action']} to {row['strategy_after']}" for _, row in switches_df.iterrows()]
    ))

# Mark pauses
pauses_df = df[df['action'] == 'PAUSE'].copy()
if len(pauses_df) > 0:
    fig_capital.add_trace(go.Scatter(
        x=pauses_df['date'],
        y=pauses_df['capital_after'],
        mode='markers',
        name='PAUSE',
        marker=dict(
            size=10,
            symbol='x',
            color='red',
            line=dict(width=2)
        ),
        hovertemplate='<b>PAUSE</b><br>Capital: $%{y:,.0f}<extra></extra>'
    ))

fig_capital.update_layout(
    height=400,
    hovermode='x unified',
    yaxis_title="Capital ($)",
    xaxis_title="Date",
    showlegend=True
)

st.plotly_chart(fig_capital, use_container_width=True)

# Profit/Loss per Evaluation
st.header("📈 Profit/Loss per Evaluation")

df['profit_loss'] = df['profit']
df['cumulative_profit'] = df['profit_loss'].cumsum()

fig_pnl = make_subplots(
    rows=2, cols=1,
    subplot_titles=('Profit/Loss per Period', 'Cumulative Profit'),
    vertical_spacing=0.12,
    shared_xaxes=True
)

# Bar chart for P&L
colors = ['green' if x >= 0 else 'red' for x in df['profit_loss']]
fig_pnl.add_trace(
    go.Bar(
        x=df['date'],
        y=df['profit_loss'],
        name='P&L',
        marker_color=colors,
        hovertemplate='Date: %{x}<br>P&L: $%{y:,.2f}<extra></extra>'
    ),
    row=1, col=1
)

# Cumulative profit line
fig_pnl.add_trace(
    go.Scatter(
        x=df['date'],
        y=df['cumulative_profit'],
        mode='lines',
        name='Cumulative',
        line=dict(color='#3498db', width=2),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.1)'
    ),
    row=2, col=1
)

fig_pnl.update_xaxes(title_text="Date", row=2, col=1)
fig_pnl.update_yaxes(title_text="P&L ($)", row=1, col=1)
fig_pnl.update_yaxes(title_text="Cumulative ($)", row=2, col=1)

fig_pnl.update_layout(height=600, showlegend=False, hovermode='x unified')

st.plotly_chart(fig_pnl, use_container_width=True)

st.markdown("---")

# Strategy Timeline
st.header("🔄 Strategy Timeline")

fig_timeline = go.Figure()

# Color map for strategies
strategy_colors = {
    'H1': '#FF6B6B',  # Red
    'H2': '#4ECDC4',  # Teal
    'H3': '#45B7D1',  # Blue
    'H4': '#96CEB4',  # Green
    'PAUSED': '#95A5A6'  # Gray
}

# Create segments for each strategy period
current_strategy = decisions[0]['strategy_after']
start_idx = 0

for i in range(1, len(decisions)):
    if decisions[i]['strategy_after'] != current_strategy:
        # Add segment
        fig_timeline.add_trace(go.Scatter(
            x=[df['date'].iloc[start_idx], df['date'].iloc[i-1]],
            y=[1, 1],
            mode='lines',
            line=dict(color=strategy_colors.get(current_strategy, '#000'), width=20),
            name=current_strategy,
            showlegend=True if current_strategy not in [d['strategy_after'] for d in decisions[:i]] else False,
            hovertemplate=f"<b>{current_strategy}</b><br>%{{x}}<extra></extra>"
        ))
        
        # Add marker for switch/resume
        action = decisions[i]['action']
        marker_symbol = 'star' if action == 'SWITCH' else 'diamond' if action == 'RESUME' else 'circle'
        fig_timeline.add_trace(go.Scatter(
            x=[df['date'].iloc[i]],
            y=[1],
            mode='markers',
            marker=dict(
                size=15,
                symbol=marker_symbol,
                color='gold',
                line=dict(color='black', width=2)
            ),
            name=f"{action} Event",
            showlegend=False,
            hovertemplate=f"<b>{action}</b><br>To: {decisions[i]['strategy_after']}<extra></extra>"
        ))
        
        current_strategy = decisions[i]['strategy_after']
        start_idx = i

# Add final segment
fig_timeline.add_trace(go.Scatter(
    x=[df['date'].iloc[start_idx], df['date'].iloc[-1]],
    y=[1, 1],
    mode='lines',
    line=dict(color=strategy_colors.get(current_strategy, '#000'), width=20),
    name=current_strategy,
    showlegend=True if current_strategy not in [d['strategy_after'] for d in decisions[:-1]] else False
))

fig_timeline.update_layout(
    height=200,
    showlegend=True,
    yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
    xaxis=dict(title="Date"),
    hovermode='x unified',
    margin=dict(l=50, r=50, t=30, b=50)
)

st.plotly_chart(fig_timeline, use_container_width=True)

# Performance Metrics Over Time
st.header("📈 Performance Metrics Over Time")

fig_metrics = make_subplots(
    rows=3, cols=1,
    subplot_titles=('Sharpe Ratio', 'Total Return (%)', 'Max Drawdown (%)'),
    vertical_spacing=0.08,
    shared_xaxes=True
)

# Sharpe Ratio
fig_metrics.add_trace(
    go.Scatter(
        x=df['date'],
        y=df['sharpe'],
        mode='lines+markers',
        name='Sharpe',
        line=dict(color='#3498db', width=2),
        marker=dict(size=6)
    ),
    row=1, col=1
)
fig_metrics.add_hline(y=1.5, line_dash="dash", line_color="red", annotation_text="Min Threshold", row=1, col=1)

# Total Return
fig_metrics.add_trace(
    go.Scatter(
        x=df['date'],
        y=df['return'] * 100,
        mode='lines+markers',
        name='Return',
        line=dict(color='#2ecc71', width=2),
        marker=dict(size=6),
        fill='tozeroy'
    ),
    row=2, col=1
)

# Max Drawdown
fig_metrics.add_trace(
    go.Scatter(
        x=df['date'],
        y=df['drawdown'] * 100,
        mode='lines+markers',
        name='Drawdown',
        line=dict(color='#e74c3c', width=2),
        marker=dict(size=6)
    ),
    row=3, col=1
)
fig_metrics.add_hline(y=15, line_dash="dash", line_color="red", annotation_text="Max Threshold", row=3, col=1)

fig_metrics.update_xaxes(title_text="Date", row=3, col=1)
fig_metrics.update_yaxes(title_text="Sharpe", row=1, col=1)
fig_metrics.update_yaxes(title_text="Return %", row=2, col=1)
fig_metrics.update_yaxes(title_text="Drawdown %", row=3, col=1)

fig_metrics.update_layout(height=800, showlegend=False, hovermode='x unified')

st.plotly_chart(fig_metrics, use_container_width=True)

# Strategy Distribution
st.header("🥧 Strategy Distribution")

col1, col2 = st.columns(2)

with col1:
    # Count strategy usage
    strategy_counts = df['strategy_after'].value_counts()
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=strategy_counts.index,
        values=strategy_counts.values,
        marker=dict(colors=[strategy_colors.get(s, '#000') for s in strategy_counts.index]),
        hole=0.4
    )])
    
    fig_pie.update_layout(
        title="Strategy Usage by Period",
        height=400
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Action distribution
    action_counts = df['action'].value_counts()
    
    action_colors = {
        'CONTINUE': '#2ecc71',
        'SWITCH': '#f39c12',
        'PAUSE': '#e74c3c',
        'RESUME': '#3498db'
    }
    
    fig_actions = go.Figure(data=[go.Bar(
        x=action_counts.index,
        y=action_counts.values,
        marker=dict(color=[action_colors.get(a, '#000') for a in action_counts.index])
    )])
    
    fig_actions.update_layout(
        title="Action Distribution",
        height=400,
        xaxis_title="Action",
        yaxis_title="Count"
    )
    
    st.plotly_chart(fig_actions, use_container_width=True)

# Decision Log Table
st.header("📋 Decision Log")

# Format the table
display_df = df[['date', 'action', 'strategy_before', 'strategy_after', 'capital_after', 'profit_loss', 'sharpe', 'return', 'drawdown']].copy()
display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
display_df['capital_after'] = display_df['capital_after'].apply(lambda x: f"${x:,.0f}")
display_df['profit_loss'] = display_df['profit_loss'].apply(lambda x: f"${x:+,.0f}")
display_df['sharpe'] = display_df['sharpe'].round(2)
display_df['return'] = (display_df['return'] * 100).round(1).astype(str) + '%'
display_df['drawdown'] = (display_df['drawdown'] * 100).round(1).astype(str) + '%'

display_df.columns = ['Date', 'Action', 'From', 'To', 'Capital', 'P&L', 'Sharpe', 'Return', 'Drawdown']

# Color code actions
def highlight_action(row):
    if row['Action'] == 'PAUSE':
        return ['background-color: #ffe6e6'] * len(row)
    elif row['Action'] == 'SWITCH':
        return ['background-color: #fff4e6'] * len(row)
    elif row['Action'] == 'RESUME':
        return ['background-color: #e6f7ff'] * len(row)
    else:
        return [''] * len(row)

st.dataframe(
    display_df.style.apply(highlight_action, axis=1),
    use_container_width=True,
    height=400
)

# Key Events
st.header("⭐ Key Events")

# Find switches
switches_df = df[df['action'] == 'SWITCH'].copy()
if len(switches_df) > 0:
    st.subheader("Strategy Switches")
    for idx, row in switches_df.iterrows():
        st.markdown(f"**{row['date'].strftime('%Y-%m-%d')}**: Switched from **{row['strategy_before']}** to **{row['strategy_after']}** "
                   f"(Sharpe: {row['sharpe']:.2f}, Return: {row['return']*100:.1f}%)")

# Find pauses
pauses_df = df[df['action'] == 'PAUSE'].copy()
if len(pauses_df) > 0:
    st.subheader("Trading Pauses")
    st.markdown(f"Trading was paused **{len(pauses_df)} times** due to invariant violations:")
    for idx, row in pauses_df.head(5).iterrows():
        st.markdown(f"- **{row['date'].strftime('%Y-%m-%d')}**: {row['strategy_before']} failed "
                   f"(Sharpe: {row['sharpe']:.2f})")
    if len(pauses_df) > 5:
        st.markdown(f"... and {len(pauses_df) - 5} more")

# Configuration info
st.sidebar.markdown("---")
st.sidebar.markdown("### Current Configuration")
st.sidebar.markdown(f"**Pair**: {config['pair']}")
st.sidebar.markdown(f"**Period**: {config['start']} to {config['end']}")
st.sidebar.markdown(f"**Window**: {config['window']} days")
st.sidebar.markdown(f"**Re-eval**: Every {config['freq']} days")
st.sidebar.markdown(f"**Initial Capital**: ${config.get('initial_capital', 10000):,.0f}")
st.sidebar.markdown(f"**Evaluations**: {len(decisions)}")
