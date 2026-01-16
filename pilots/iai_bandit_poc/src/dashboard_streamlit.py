"""Streamlit web dashboard for IAI evolution.

Run with:
    streamlit run dashboard_streamlit.py

Features:
- Live monitoring of evolution progress
- Interactive charts with Plotly
- LLM decision reasoning display
- Evolution history timeline
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import time
from pathlib import Path
from datetime import datetime


# Page config
st.set_page_config(
    page_title="IAI Evolution Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stAlert > div {
        padding: 1rem;
    }
    .decision-accept {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .decision-reject {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .decision-modify {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def load_evolution_data(run_dir: Path):
    """Load all data from an evolution run."""
    if not run_dir.exists():
        return None
    
    data = {
        'generations': [],
        'decisions': [],
        'baseline': {}
    }
    
    # Load baseline
    baseline_file = run_dir / 'baseline_results.json'
    if baseline_file.exists():
        with open(baseline_file, 'r') as f:
            data['baseline'] = json.load(f)
    
    # Load generations
    gen_dirs = sorted([d for d in run_dir.iterdir() if d.is_dir() and d.name.startswith('generation_')])
    
    for gen_dir in gen_dirs:
        gen_num = int(gen_dir.name.split('_')[1])
        
        gen_data = {
            'number': gen_num,
            'invariants': None,
            'results': None,
            'proposal': None,
            'decision': None
        }
        
        # Load files
        inv_file = gen_dir / 'invariants.json'
        if inv_file.exists():
            with open(inv_file, 'r') as f:
                gen_data['invariants'] = json.load(f)
        
        results_file = gen_dir / 'iai_results.json'
        if results_file.exists():
            with open(results_file, 'r') as f:
                gen_data['results'] = json.load(f)
        
        proposal_file = gen_dir / 'proposal.json'
        if proposal_file.exists():
            with open(proposal_file, 'r') as f:
                gen_data['proposal'] = json.load(f)
        
        decision_file = gen_dir / 'decision.json'
        if decision_file.exists():
            with open(decision_file, 'r') as f:
                gen_data['decision'] = json.load(f)
        
        data['generations'].append(gen_data)
    
    # Load authority decisions
    decisions_file = run_dir / 'authority_decisions.json'
    if decisions_file.exists():
        with open(decisions_file, 'r') as f:
            data['decisions'] = json.load(f)
    
    return data


def plot_performance_evolution(data):
    """Plot performance over generations."""
    if not data or not data['generations']:
        return None
    
    # Extract metrics
    gens = []
    iai_regrets = []
    
    for gen in data['generations']:
        if gen['results']:
            gens.append(gen['number'])
            iai_regrets.append(gen['results'].get('avg_regret', 0))
    
    if not gens:
        return None
    
    # Create figure
    fig = go.Figure()
    
    # IAI performance
    fig.add_trace(go.Scatter(
        x=gens,
        y=iai_regrets,
        mode='lines+markers',
        name='IAI',
        line=dict(color='#00D9FF', width=3),
        marker=dict(size=10)
    ))
    
    # Baseline reference
    if data['baseline']:
        best_baseline = None
        for sys, res in data['baseline'].items():
            if best_baseline is None or res['final_regret'] < best_baseline:
                best_baseline = res['final_regret']
        
        if best_baseline:
            fig.add_hline(
                y=best_baseline,
                line_dash="dash",
                line_color="gray",
                annotation_text="Best Baseline",
                annotation_position="right"
            )
    
    fig.update_layout(
        title="Performance Evolution",
        xaxis_title="Generation",
        yaxis_title="Average Regret",
        template="plotly_dark",
        height=400,
        hovermode='x unified'
    )
    
    return fig


def plot_decision_timeline(data):
    """Plot Authority decisions timeline."""
    if not data or not data['decisions']:
        return None
    
    decisions = data['decisions']
    
    # Colors for verdicts
    colors = {
        'ACCEPT': '#28a745',
        'REJECT': '#dc3545',
        'MODIFY': '#ffc107'
    }
    
    gens = [d['generation'] for d in decisions]
    confidences = [d['confidence'] for d in decisions]
    verdicts = [d['verdict'] for d in decisions]
    verdict_colors = [colors.get(v, 'gray') for v in verdicts]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=gens,
        y=confidences,
        marker_color=verdict_colors,
        text=verdicts,
        textposition='auto',
        name='Decisions'
    ))
    
    fig.update_layout(
        title="Authority Decisions",
        xaxis_title="Generation",
        yaxis_title="Confidence",
        template="plotly_dark",
        height=300,
        showlegend=False
    )
    
    return fig


def display_decision(decision, gen):
    """Display a decision with styling."""
    verdict = decision['verdict']
    
    if verdict == 'ACCEPT':
        st.markdown(f"""
        <div class="decision-accept">
            <h4>✅ Generation {gen}: ACCEPTED</h4>
            <p><strong>Confidence:</strong> {decision['confidence']:.2f}</p>
            <p><strong>Rationale:</strong> {decision['rationale']}</p>
        </div>
        """, unsafe_allow_html=True)
    elif verdict == 'REJECT':
        st.markdown(f"""
        <div class="decision-reject">
            <h4>❌ Generation {gen}: REJECTED</h4>
            <p><strong>Confidence:</strong> {decision['confidence']:.2f}</p>
            <p><strong>Rationale:</strong> {decision['rationale']}</p>
        </div>
        """, unsafe_allow_html=True)
    else:  # MODIFY
        st.markdown(f"""
        <div class="decision-modify">
            <h4>🔧 Generation {gen}: MODIFIED</h4>
            <p><strong>Confidence:</strong> {decision['confidence']:.2f}</p>
            <p><strong>Rationale:</strong> {decision['rationale']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    if decision.get('concerns'):
        with st.expander("View Concerns"):
            for concern in decision['concerns']:
                st.warning(concern)


def main():
    # Header
    st.title("🧠 IAI Evolution Dashboard")
    st.markdown("Real-time monitoring of Invariant-Anchored Intelligence evolution")
    
    # Sidebar
    st.sidebar.header("⚙️ Configuration")
    
    run_dir = st.sidebar.text_input(
        "Run Directory",
        value="runs/iai_evolution",
        help="Path to evolution run directory"
    )
    
    auto_refresh = st.sidebar.checkbox(
        "Auto-refresh",
        value=True,
        help="Automatically refresh every 5 seconds"
    )
    
    if auto_refresh:
        refresh_interval = st.sidebar.slider(
            "Refresh interval (seconds)",
            min_value=2,
            max_value=30,
            value=5
        )
    
    # Load button
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()
    
    # Load data
    data = load_evolution_data(Path(run_dir))
    
    if not data:
        st.error(f"No data found in {run_dir}")
        st.info("Start an IAI evolution run to see live data here")
        return
    
    # Status
    if data['generations']:
        latest_gen = data['generations'][-1]['number']
        st.sidebar.success(f"📊 Latest Generation: {latest_gen}")
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🎯 Generations", "🧠 LLM Decisions", "📊 Baseline"])
    
    with tab1:
        st.header("Performance Overview")
        
        # Metrics row
        col1, col2, col3 = st.columns(3)
        
        if data['generations']:
            latest = data['generations'][-1]
            
            with col1:
                st.metric(
                    "Current Generation",
                    latest['number'],
                    delta=None
                )
            
            with col2:
                if latest['results']:
                    st.metric(
                        "Current Regret",
                        f"{latest['results'].get('avg_regret', 0):.2f}",
                        delta=None
                    )
            
            with col3:
                if data['decisions']:
                    accepts = sum(1 for d in data['decisions'] if d['verdict'] == 'ACCEPT')
                    st.metric(
                        "Proposals Accepted",
                        accepts,
                        delta=None
                    )
        
        # Performance chart
        perf_fig = plot_performance_evolution(data)
        if perf_fig:
            st.plotly_chart(perf_fig, use_container_width=True)
        
        # Decision timeline
        decision_fig = plot_decision_timeline(data)
        if decision_fig:
            st.plotly_chart(decision_fig, use_container_width=True)
    
    with tab2:
        st.header("Generation Details")
        
        if data['generations']:
            for gen_data in reversed(data['generations']):
                with st.expander(f"Generation {gen_data['number']}", expanded=(gen_data == data['generations'][-1])):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Invariants")
                        if gen_data['invariants']:
                            st.json(gen_data['invariants'])
                    
                    with col2:
                        st.subheader("Performance")
                        if gen_data['results']:
                            st.metric("Avg Regret", f"{gen_data['results'].get('avg_regret', 0):.2f}")
                            st.metric("Avg Reward", f"{gen_data['results'].get('avg_reward', 0):.2f}")
                    
                    if gen_data['proposal'] and gen_data['proposal'].get('proposed_metrics'):
                        st.subheader("📋 Challenger Proposal")
                        
                        if gen_data['proposal'].get('critiques'):
                            st.markdown("**Critiques:**")
                            for critique in gen_data['proposal']['critiques']:
                                st.warning(f"**{critique.get('signal', 'Unknown')}**: {critique.get('description', 'N/A')}")
                        
                        if gen_data['proposal'].get('proposed_metrics'):
                            st.markdown("**Proposed Changes:**")
                            for prop in gen_data['proposal']['proposed_metrics']:
                                st.info(f"**{prop.get('name', 'Unnamed')}**: {prop.get('description', 'N/A')}")
    
    with tab3:
        st.header("🧠 LLM Authority Decisions")
        
        if data['decisions']:
            for decision in reversed(data['decisions']):
                display_decision(decision, decision['generation'])
                st.divider()
        else:
            st.info("No decisions yet")
    
    with tab4:
        st.header("📊 Baseline Performance")
        
        if data['baseline']:
            # Create comparison table
            baseline_df = pd.DataFrame([
                {
                    'System': sys,
                    'Avg Regret': res['final_regret'],
                    'Avg Reward': res['final_reward']
                }
                for sys, res in data['baseline'].items()
            ])
            
            st.dataframe(
                baseline_df.style.highlight_min(subset=['Avg Regret'], color='lightgreen'),
                use_container_width=True
            )
            
            # Bar chart
            fig = px.bar(
                baseline_df,
                x='System',
                y='Avg Regret',
                title='Baseline Comparison',
                color='Avg Regret',
                color_continuous_scale='RdYlGn_r'
            )
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
