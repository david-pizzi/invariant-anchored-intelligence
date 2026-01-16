#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-run analysis script for IAI Evolution experiments.

Generates:
- evolution_history.csv: Consolidated metrics for all generations
- experiment_summary.json: Complete structured log
- Matplotlib plots (PNG): Visual evolution analysis

Usage:
    python analyze_evolution.py [--run-dir runs/iai_evolution]
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import io

# Force UTF-8 for stdout to handle emojis on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


def load_generation_data(run_dir: Path) -> list[dict]:
    """Load all generation data from run directory."""
    generations = []
    
    gen_dirs = sorted([d for d in run_dir.iterdir() if d.is_dir() and d.name.startswith('generation_')])
    
    for gen_dir in gen_dirs:
        gen_num = int(gen_dir.name.split('_')[1])
        gen_data = {'generation': gen_num}
        
        # Load summary
        summary_file = gen_dir / 'summary.json'
        if summary_file.exists():
            with open(summary_file) as f:
                gen_data['summary'] = json.load(f)
        
        # Load proposal
        proposal_file = gen_dir / 'proposal.json'
        if proposal_file.exists():
            with open(proposal_file) as f:
                gen_data['proposal'] = json.load(f)
        
        # Load decision
        decision_file = gen_dir / 'decision.json'
        if decision_file.exists():
            with open(decision_file) as f:
                gen_data['decision'] = json.load(f)
        
        # Load invariants
        invariants_file = gen_dir / 'invariants.json'
        if invariants_file.exists():
            with open(invariants_file) as f:
                gen_data['invariants'] = json.load(f)
        
        generations.append(gen_data)
    
    return generations


def load_authority_decisions(run_dir: Path) -> list[dict]:
    """Load authority decisions with full context."""
    decisions_file = run_dir / 'authority_decisions.json'
    if decisions_file.exists():
        with open(decisions_file) as f:
            return json.load(f)
    return []


def extract_baseline_metrics(authority_decisions: list[dict]) -> dict:
    """Extract baseline metrics from first authority decision."""
    if not authority_decisions:
        return {}
    
    first_decision = authority_decisions[0]
    prompt = first_decision.get('prompt', '')
    
    # Parse baseline from prompt (it's embedded in the text)
    # This is a bit hacky but works for current format
    baseline = {
        'best_system': 'thompson',
        'best_regret': None,
        'best_reward': None
    }
    
    # Try to extract from the structured data if available
    if 'baseline_metrics' in first_decision:
        bm = first_decision['baseline_metrics']
        baseline['best_regret'] = bm.get('best_regret')
        baseline['best_reward'] = bm.get('best_reward')
    
    return baseline


def create_evolution_csv(generations: list[dict], authority_decisions: list[dict], 
                         baseline_regret: float, output_path: Path):
    """Create consolidated CSV with all generation metrics."""
    rows = []
    
    for gen in generations:
        gen_num = gen['generation']
        summary = gen.get('summary', {})
        proposal = gen.get('proposal', {})
        decision = gen.get('decision', {})
        invariants = gen.get('invariants', {})
        
        # Extract strain signals
        strain_signals = proposal.get('strain_signals', {})
        
        row = {
            'generation': gen_num,
            'avg_regret': summary.get('avg_regret'),
            'avg_reward': summary.get('avg_reward'),
            'switch_rate': summary.get('switch_rate'),
            'baseline_regret': baseline_regret,
            'regret_vs_baseline': (summary.get('avg_regret', 0) / baseline_regret * 100 - 100) if baseline_regret else None,
            'strain_detected': bool(proposal.get('proposed_metrics')),
            'strain_signals': ', '.join([
                k for k, v in strain_signals.items() 
                if isinstance(v, bool) and v
            ]),
            'regret_slope_early': strain_signals.get('regret_slope_early'),
            'regret_slope_recent': strain_signals.get('regret_slope_recent'),
            'regret_slope_increasing': strain_signals.get('regret_slope_increasing'),
            'switch_rate_unstable': strain_signals.get('switch_rate_unstable'),
            'absolute_regret_high': strain_signals.get('absolute_regret_high'),
            'regret_vs_baseline_ratio': strain_signals.get('regret_vs_baseline_ratio'),
            'decision_verdict': decision.get('verdict'),
            'decision_confidence': decision.get('confidence'),
            'decision_rationale': decision.get('rationale'),
            'proposal_name': proposal.get('proposed_metrics', [{}])[0].get('name') if proposal.get('proposed_metrics') else None,
            'invariant_metric': invariants.get('metric'),
            'num_runs': len(summary.get('runs', [])),
        }
        
        # Add per-run regret stats
        runs = summary.get('runs', [])
        if runs:
            regrets = [r.get('final_regret', 0) for r in runs]
            row['regret_min'] = min(regrets)
            row['regret_max'] = max(regrets)
            row['regret_std'] = np.std(regrets)
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"✓ Saved: {output_path}")
    return df


def create_experiment_summary(generations: list[dict], authority_decisions: list[dict],
                               baseline_regret: float, output_path: Path):
    """Create complete structured JSON summary."""
    
    summary = {
        'experiment_info': {
            'timestamp': datetime.now().isoformat(),
            'total_generations': len(generations),
            'baseline_regret': baseline_regret,
        },
        'metrics_evolution': [],
        'decision_summary': {
            'accepted': 0,
            'rejected': 0,
            'modified': 0,
            'no_proposal': 0,
        },
        'strain_detection': {
            'total_strain_detected': 0,
            'total_high_regret': 0,
            'signals_triggered': {},
        },
        'proposal_effectiveness': {
            'proposals_made': 0,
            'improvements_after': 0,
            'regressions_after': 0,
        },
        'authority_decisions': authority_decisions,
    }
    
    prev_regret = None
    prev_decision = None
    
    for gen in generations:
        gen_num = gen['generation']
        s = gen.get('summary', {})
        p = gen.get('proposal', {})
        d = gen.get('decision', {})
        
        regret = s.get('avg_regret', 0)
        strain_signals = p.get('strain_signals', {})
        
        # Track metrics evolution
        summary['metrics_evolution'].append({
            'generation': gen_num,
            'regret': regret,
            'reward': s.get('avg_reward'),
            'vs_baseline_pct': (regret / baseline_regret * 100 - 100) if baseline_regret else None,
            'strain_detected': bool(p.get('proposed_metrics')),
            'decision': d.get('verdict'),
        })
        
        # Count decisions
        verdict = d.get('verdict', 'NO_PROPOSAL')
        if verdict == 'ACCEPT':
            summary['decision_summary']['accepted'] += 1
        elif verdict == 'REJECT':
            summary['decision_summary']['rejected'] += 1
        elif verdict == 'MODIFY':
            summary['decision_summary']['modified'] += 1
        else:
            summary['decision_summary']['no_proposal'] += 1
        
        # Track strain detection
        if p.get('proposed_metrics'):
            summary['strain_detection']['total_strain_detected'] += 1
            summary['proposal_effectiveness']['proposals_made'] += 1
        
        if strain_signals.get('absolute_regret_high'):
            summary['strain_detection']['total_high_regret'] += 1
        
        # Count signal types
        for signal, value in strain_signals.items():
            if isinstance(value, bool) and value:
                summary['strain_detection']['signals_triggered'][signal] = \
                    summary['strain_detection']['signals_triggered'].get(signal, 0) + 1
        
        # Track proposal effectiveness
        if prev_decision in ['ACCEPT', 'MODIFY'] and prev_regret is not None:
            if regret < prev_regret:
                summary['proposal_effectiveness']['improvements_after'] += 1
            else:
                summary['proposal_effectiveness']['regressions_after'] += 1
        
        prev_regret = regret
        prev_decision = d.get('verdict')
    
    # Calculate effectiveness rate
    total_accepted = summary['decision_summary']['accepted'] + summary['decision_summary']['modified']
    if total_accepted > 0:
        summary['proposal_effectiveness']['effectiveness_rate'] = \
            summary['proposal_effectiveness']['improvements_after'] / total_accepted * 100
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved: {output_path}")
    return summary


def create_plots(df: pd.DataFrame, baseline_regret: float, output_dir: Path):
    """Generate matplotlib plots for evolution analysis."""
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig_dir = output_dir / 'plots'
    fig_dir.mkdir(exist_ok=True)
    
    # 1. Regret Evolution Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    generations = df['generation'].values
    regrets = df['avg_regret'].values
    
    # Plot regret line
    ax.plot(generations, regrets, 'b-o', linewidth=2, markersize=8, label='IAI Regret')
    
    # Add baseline reference
    ax.axhline(y=baseline_regret, color='green', linestyle='--', linewidth=2, 
               label=f'Baseline (Thompson): {baseline_regret:.1f}')
    
    # Color points by strain detection
    for i, (gen, reg, strain) in enumerate(zip(generations, regrets, df['strain_detected'])):
        color = 'red' if strain else 'blue'
        ax.scatter([gen], [reg], c=color, s=100, zorder=5)
    
    # Add decision annotations
    for i, (gen, reg, decision) in enumerate(zip(generations, regrets, df['decision_verdict'])):
        if pd.notna(decision):
            symbol = {'ACCEPT': 'A', 'MODIFY': 'M', 'REJECT': 'R', 'NO_CHANGE': '-'}.get(decision, '?')
            ax.annotate(symbol, (gen, reg), textcoords="offset points", 
                       xytext=(0, 15), ha='center', fontsize=12, fontweight='bold')
    
    ax.set_xlabel('Generation', fontsize=12)
    ax.set_ylabel('Average Regret', fontsize=12)
    ax.set_title('IAI Evolution: Regret Over Generations', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    
    # Add legend for strain colors
    strain_patch = mpatches.Patch(color='red', label='Strain Detected')
    no_strain_patch = mpatches.Patch(color='blue', label='No Strain')
    ax.legend(handles=[ax.get_legend_handles_labels()[0][0], ax.get_legend_handles_labels()[0][1],
                       strain_patch, no_strain_patch], loc='upper right')
    
    plt.tight_layout()
    plt.savefig(fig_dir / 'regret_evolution.png', dpi=150)
    print(f"✓ Saved: {fig_dir / 'regret_evolution.png'}")
    plt.close()
    
    # 2. Regret vs Baseline Comparison
    fig, ax = plt.subplots(figsize=(12, 6))
    
    vs_baseline = df['regret_vs_baseline'].values
    colors = ['red' if v > 30 else 'orange' if v > 0 else 'green' for v in vs_baseline]
    
    bars = ax.bar(generations, vs_baseline, color=colors, edgecolor='black', alpha=0.7)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.axhline(y=30, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Threshold (1.3x)')
    
    ax.set_xlabel('Generation', fontsize=12)
    ax.set_ylabel('Regret vs Baseline (%)', fontsize=12)
    ax.set_title('IAI Performance Relative to Baseline', fontsize=14, fontweight='bold')
    
    # Add value labels
    for bar, val in zip(bars, vs_baseline):
        height = bar.get_height()
        ax.annotate(f'{val:+.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                   xytext=(0, 3), textcoords="offset points", ha='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(fig_dir / 'regret_vs_baseline.png', dpi=150)
    print(f"✓ Saved: {fig_dir / 'regret_vs_baseline.png'}")
    plt.close()
    
    # 3. Strain Detection Accuracy
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Left: Strain detection pie chart
    strain_detected = df['strain_detected'].sum()
    no_strain = len(df) - strain_detected
    axes[0].pie([strain_detected, no_strain], labels=['Strain Detected', 'No Strain'],
                colors=['#ff6b6b', '#4ecdc4'], autopct='%1.1f%%', startangle=90)
    axes[0].set_title('Strain Detection Distribution', fontsize=12, fontweight='bold')
    
    # Right: Decision breakdown
    decisions = df['decision_verdict'].value_counts()
    decision_colors = {'ACCEPT': '#2ecc71', 'MODIFY': '#f39c12', 'REJECT': '#e74c3c', 'NO_CHANGE': '#95a5a6'}
    colors = [decision_colors.get(d, '#bdc3c7') for d in decisions.index]
    axes[1].pie(decisions.values, labels=decisions.index, colors=colors,
                autopct='%1.1f%%', startangle=90)
    axes[1].set_title('Authority Decision Distribution', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(fig_dir / 'strain_and_decisions.png', dpi=150)
    print(f"✓ Saved: {fig_dir / 'strain_and_decisions.png'}")
    plt.close()
    
    # 4. Combined Dashboard
    fig = plt.figure(figsize=(16, 10))
    
    # Regret evolution (top left)
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(generations, regrets, 'b-o', linewidth=2, markersize=6)
    ax1.axhline(y=baseline_regret, color='green', linestyle='--', linewidth=2)
    ax1.fill_between(generations, regrets, baseline_regret, alpha=0.3, 
                     where=[r > baseline_regret for r in regrets], color='red')
    ax1.fill_between(generations, regrets, baseline_regret, alpha=0.3,
                     where=[r <= baseline_regret for r in regrets], color='green')
    ax1.set_xlabel('Generation')
    ax1.set_ylabel('Regret')
    ax1.set_title('Regret Evolution', fontweight='bold')
    
    # Reward evolution (top right)
    ax2 = fig.add_subplot(2, 2, 2)
    rewards = df['avg_reward'].values
    ax2.plot(generations, rewards, 'g-s', linewidth=2, markersize=6)
    ax2.set_xlabel('Generation')
    ax2.set_ylabel('Reward')
    ax2.set_title('Reward Evolution', fontweight='bold')
    
    # Strain signals heatmap (bottom left)
    ax3 = fig.add_subplot(2, 2, 3)
    strain_cols = ['regret_slope_increasing', 'switch_rate_unstable', 'absolute_regret_high']
    strain_data = df[strain_cols].fillna(False).astype(int).values.T
    im = ax3.imshow(strain_data, cmap='RdYlGn_r', aspect='auto')
    ax3.set_yticks(range(len(strain_cols)))
    ax3.set_yticklabels(['Regret Slope ↑', 'Switch Unstable', 'Abs Regret High'])
    ax3.set_xticks(range(len(generations)))
    ax3.set_xticklabels(generations)
    ax3.set_xlabel('Generation')
    ax3.set_title('Strain Signals Heatmap', fontweight='bold')
    
    # Per-run variance (bottom right)
    ax4 = fig.add_subplot(2, 2, 4)
    if 'regret_std' in df.columns:
        ax4.bar(generations, df['regret_std'].values, color='purple', alpha=0.7)
        ax4.set_xlabel('Generation')
        ax4.set_ylabel('Regret Std Dev')
        ax4.set_title('Run-to-Run Variance', fontweight='bold')
    
    plt.suptitle('IAI Evolution Analysis Dashboard', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(fig_dir / 'evolution_dashboard.png', dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {fig_dir / 'evolution_dashboard.png'}")
    plt.close()
    
    print(f"\n📊 All plots saved to: {fig_dir}")


def create_markdown_report(df: pd.DataFrame, summary: dict, generations: list[dict],
                           baseline_regret: float, run_dir: Path, output_path: Path):
    """Create a consolidated markdown report with embedded plots and data links."""
    
    exp_info = summary['experiment_info']
    decision_summary = summary['decision_summary']
    strain_det = summary['strain_detection']
    proposal_eff = summary['proposal_effectiveness']
    
    # Build markdown content
    md = []
    
    md.append("# IAI Evolution Analysis Report")
    md.append("")
    md.append(f"**Generated:** {exp_info['timestamp']}")
    md.append(f"**Generations:** {exp_info['total_generations']}")
    md.append(f"**Baseline Regret:** {baseline_regret:.2f}")
    md.append("")
    
    # Quick navigation
    md.append("## Quick Links")
    md.append("")
    md.append("| Resource | Description |")
    md.append("|----------|-------------|")
    md.append("| [evolution_history.csv](evolution_history.csv) | Full metrics per generation (for LLM analysis) |")
    md.append("| [experiment_summary.json](experiment_summary.json) | Structured experiment data |")
    md.append("| [authority_decisions.json](authority_decisions.json) | Full LLM authority prompts & responses |")
    md.append("| [EVOLUTION_REPORT.txt](EVOLUTION_REPORT.txt) | Text-based evolution summary |")
    md.append("")
    
    # Executive summary
    md.append("---")
    md.append("## Executive Summary")
    md.append("")
    
    total_decisions = sum(decision_summary.values())
    acceptance_rate = (decision_summary['accepted'] + decision_summary['modified']) / total_decisions * 100 if total_decisions > 0 else 0
    effectiveness = proposal_eff.get('effectiveness_rate', 0)
    
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Generations Analyzed | {exp_info['total_generations']} |")
    md.append(f"| Baseline Regret | {baseline_regret:.2f} |")
    md.append(f"| Proposal Acceptance Rate | {acceptance_rate:.1f}% |")
    md.append(f"| Proposal Effectiveness | {effectiveness:.1f}% |")
    md.append(f"| Strain Detected | {strain_det['total_strain_detected']} / {exp_info['total_generations']} generations |")
    md.append(f"| High Regret (>1.3x baseline) | {strain_det['total_high_regret']} generations |")
    md.append("")
    
    # Dashboard visualization
    md.append("---")
    md.append("## Evolution Dashboard")
    md.append("")
    md.append("![Evolution Dashboard](plots/evolution_dashboard.png)")
    md.append("")
    
    # Detailed plots
    md.append("---")
    md.append("## Detailed Visualizations")
    md.append("")
    md.append("### Regret Evolution")
    md.append("![Regret Evolution](plots/regret_evolution.png)")
    md.append("")
    md.append("### Performance vs Baseline")
    md.append("![Regret vs Baseline](plots/regret_vs_baseline.png)")
    md.append("")
    md.append("### Strain Detection & Decisions")
    md.append("![Strain and Decisions](plots/strain_and_decisions.png)")
    md.append("")
    
    # Decision breakdown
    md.append("---")
    md.append("## Decision Analysis")
    md.append("")
    md.append("### Authority Decision Breakdown")
    md.append("")
    md.append("| Decision | Count |")
    md.append("|----------|-------|")
    md.append(f"| ✅ Accepted | {decision_summary['accepted']} |")
    md.append(f"| 🔧 Modified | {decision_summary['modified']} |")
    md.append(f"| ❌ Rejected | {decision_summary['rejected']} |")
    md.append(f"| ⏸️ No Proposal | {decision_summary['no_proposal']} |")
    md.append("")
    
    # Proposal effectiveness
    md.append("### Proposal Effectiveness")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Proposals Made | {proposal_eff['proposals_made']} |")
    md.append(f"| Improvements After Accept/Modify | {proposal_eff['improvements_after']} |")
    md.append(f"| Regressions After Accept/Modify | {proposal_eff['regressions_after']} |")
    if 'effectiveness_rate' in proposal_eff:
        md.append(f"| **Effectiveness Rate** | **{proposal_eff['effectiveness_rate']:.1f}%** |")
    md.append("")
    
    # Generation-by-generation table
    md.append("---")
    md.append("## Generation-by-Generation Results")
    md.append("")
    md.append("| Gen | Regret | vs Baseline | Strain | Decision | Rationale |")
    md.append("|-----|--------|-------------|--------|----------|-----------|")
    
    for _, row in df.iterrows():
        gen = int(row['generation'])
        regret = row['avg_regret']
        vs_base = row['regret_vs_baseline']
        strain = "⚠️ Yes" if row['strain_detected'] else "No"
        decision = row['decision_verdict'] or "-"
        rationale = str(row['decision_rationale'])[:60] + "..." if pd.notna(row['decision_rationale']) and len(str(row['decision_rationale'])) > 60 else (row['decision_rationale'] if pd.notna(row['decision_rationale']) else "-")
        
        md.append(f"| {gen} | {regret:.1f} | {vs_base:+.1f}% | {strain} | {decision} | {rationale} |")
    
    md.append("")
    
    # Strain signals analysis
    md.append("---")
    md.append("## Strain Signal Analysis")
    md.append("")
    md.append("### Signals Triggered Per Generation")
    md.append("")
    
    for gen in generations:
        gen_num = gen['generation']
        proposal = gen.get('proposal', {})
        signals = proposal.get('strain_signals', {})
        triggered = [k for k, v in signals.items() if isinstance(v, bool) and v]
        
        if triggered:
            md.append(f"**Generation {gen_num}:** {', '.join(triggered)}")
        else:
            md.append(f"**Generation {gen_num}:** No strain signals")
    
    md.append("")
    
    # Signal frequency
    if strain_det['signals_triggered']:
        md.append("### Signal Frequency Summary")
        md.append("")
        md.append("| Signal | Times Triggered |")
        md.append("|--------|-----------------|")
        for signal, count in sorted(strain_det['signals_triggered'].items(), key=lambda x: -x[1]):
            md.append(f"| `{signal}` | {count} |")
        md.append("")
    
    # Invariant evolution
    md.append("---")
    md.append("## Invariant Evolution")
    md.append("")
    md.append("```")
    for gen in generations:
        gen_num = gen['generation']
        inv = gen.get('invariants', {})
        metric = inv.get('metric', 'cumulative_reward')
        md.append(f"Gen {gen_num}: {metric}")
    md.append("```")
    md.append("")
    
    # Footer
    md.append("---")
    md.append("")
    md.append("*This report was auto-generated by `analyze_evolution.py`*")
    md.append("")
    
    # Write file
    report_content = "\n".join(md)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✓ Saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Analyze IAI Evolution experiment results')
    parser.add_argument('--run-dir', type=str, default='runs/iai_evolution',
                       help='Path to run directory')
    args = parser.parse_args()
    
    # Resolve path relative to script location
    script_dir = Path(__file__).parent
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = script_dir / run_dir
    
    if not run_dir.exists():
        print(f"❌ Run directory not found: {run_dir}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("IAI EVOLUTION ANALYSIS")
    print(f"{'='*60}")
    print(f"Run directory: {run_dir}\n")
    
    # Load data
    print("Loading data...")
    generations = load_generation_data(run_dir)
    authority_decisions = load_authority_decisions(run_dir)
    
    if not generations:
        print("❌ No generation data found")
        sys.exit(1)
    
    print(f"  Found {len(generations)} generations")
    print(f"  Found {len(authority_decisions)} authority decisions")
    
    # Extract baseline regret from first generation's proposal
    baseline_regret = None
    if generations and 'proposal' in generations[0]:
        strain_signals = generations[0]['proposal'].get('strain_signals', {})
        baseline_regret = strain_signals.get('baseline_regret')
    
    if baseline_regret is None:
        # Try to extract from summary
        for gen in generations:
            if 'summary' in gen:
                baseline_regret = gen['summary'].get('baseline_regret', 375.0)
                break
        baseline_regret = baseline_regret or 375.0
    
    print(f"  Baseline regret: {baseline_regret:.2f}")
    
    # Generate outputs
    print("\nGenerating outputs...")
    
    # 1. Evolution history CSV
    csv_path = run_dir / 'evolution_history.csv'
    df = create_evolution_csv(generations, authority_decisions, baseline_regret, csv_path)
    
    # 2. Experiment summary JSON
    json_path = run_dir / 'experiment_summary.json'
    summary = create_experiment_summary(generations, authority_decisions, baseline_regret, json_path)
    
    # 3. Plots
    print("\nGenerating plots...")
    create_plots(df, baseline_regret, run_dir)
    
    # 4. Markdown report (consolidates everything)
    print("\nGenerating markdown report...")
    md_path = run_dir / 'ANALYSIS_REPORT.md'
    create_markdown_report(df, summary, generations, baseline_regret, run_dir, md_path)
    
    # Print summary
    print(f"\n{'='*60}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Generations analyzed: {len(generations)}")
    print(f"Baseline regret: {baseline_regret:.2f}")
    print(f"\nDecision breakdown:")
    for k, v in summary['decision_summary'].items():
        print(f"  {k}: {v}")
    print(f"\nStrain detection:")
    print(f"  Total detected: {summary['strain_detection']['total_strain_detected']}")
    print(f"  High regret (>1.3x): {summary['strain_detection']['total_high_regret']}")
    print(f"\nProposal effectiveness:")
    print(f"  Proposals made: {summary['proposal_effectiveness']['proposals_made']}")
    print(f"  Improvements after: {summary['proposal_effectiveness']['improvements_after']}")
    print(f"  Regressions after: {summary['proposal_effectiveness']['regressions_after']}")
    if 'effectiveness_rate' in summary['proposal_effectiveness']:
        print(f"  Effectiveness rate: {summary['proposal_effectiveness']['effectiveness_rate']:.1f}%")
    
    print(f"\n{'='*60}")
    print("OUTPUT FILES")
    print(f"{'='*60}")
    print(f"📋 {md_path}  <-- MAIN REPORT (view this)")
    print(f"📄 {csv_path}")
    print(f"📄 {json_path}")
    print(f"📁 {run_dir / 'plots'}/")
    print(f"   - regret_evolution.png")
    print(f"   - regret_vs_baseline.png")
    print(f"   - strain_and_decisions.png")
    print(f"   - evolution_dashboard.png")
    print()


if __name__ == '__main__':
    main()
