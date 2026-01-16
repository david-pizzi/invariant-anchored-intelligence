# Visual Dashboards for IAI Evolution

Two beautiful dashboard options to monitor IAI evolution in real-time!

## 🎨 Option 1: Rich Terminal Dashboard (Recommended for Quick Start)

Beautiful terminal-based interface with live updates, no browser needed.

**Features:**
- ✨ Beautiful progress bars and animations
- 🎨 Color-coded decisions (green=accept, red=reject, yellow=modify)
- 📊 Live performance metrics
- 🧠 LLM reasoning displayed inline
- 📝 Syntax-highlighted JSON
- ⚡ No web browser required

**Usage:**
```bash
python run_iai_visual.py --generations 3 --steps 10000 --runs 3
```

**Preview:**
```
╔══════════════════════════════════════════════════════════════════════╗
║              IAI EVOLUTION WITH LLM AUTHORITY                        ║
╚══════════════════════════════════════════════════════════════════════╝

⚡ Running Baseline Systems...
  [====================================] 100% Thompson
  [====================================] 100% UCB1
  [====================================] 100% Epsilon-Greedy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERATION 0/2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 Running IAI System...
🔍 Challenger Analysis...
🧠 LLM Authority Reviewing...

✅ AUTHORITY DECISION: ACCEPT
  Confidence: 0.85
  Rationale: The proposed metric effectively addresses the drift...
```

---

## 🌐 Option 2: Streamlit Web Dashboard

Interactive web dashboard with real-time charts and full history.

**Features:**
- 📈 Interactive Plotly charts
- 🔄 Auto-refresh every 5 seconds
- 📊 Multi-tab interface (Overview, Generations, Decisions, Baseline)
- 🎯 Drill-down into each generation
- 📱 Responsive design
- 🎨 Professional dark theme

**Usage:**

1. **Start evolution run in one terminal:**
   ```bash
   python run_iai_evolution.py --generations 5 --steps 10000
   ```

2. **Launch dashboard in another terminal:**
   ```bash
   streamlit run dashboard_streamlit.py
   ```

3. **Open browser to:** http://localhost:8501

**Dashboard Tabs:**

- **📈 Overview**: Performance trends, decision timeline, key metrics
- **🎯 Generations**: Detailed view of each generation (invariants, proposals, results)
- **🧠 LLM Decisions**: Full history of Authority decisions with reasoning
- **📊 Baseline**: Comparison of baseline algorithms

---

## 🚀 Quick Comparison

| Feature | Rich Terminal | Streamlit Web |
|---------|---------------|---------------|
| Setup | ✅ Instant | Requires browser |
| Live Updates | ✅ Built-in | ✅ Auto-refresh |
| Performance | ⚡ Fast | Medium |
| Interactivity | Limited | ✅ Full |
| History View | Current only | ✅ Full history |
| Charts | Basic | ✅ Interactive |
| Best For | Live monitoring | Deep analysis |

---

## 🎯 Recommended Workflow

1. **During Evolution Run**: Use **Rich Terminal** for live monitoring
   ```bash
   python run_iai_visual.py --generations 5
   ```

2. **After Completion**: Use **Streamlit Dashboard** for analysis
   ```bash
   streamlit run dashboard_streamlit.py
   ```

3. **For Demos**: Use **Streamlit Dashboard** with auto-refresh
   - Shows real-time updates
   - Professional appearance
   - Easy to share with team

---

## 🎨 Color Coding

Both dashboards use consistent color coding:
- 🟢 **Green**: Accepted proposals, good performance
- 🔴 **Red**: Rejected proposals, poor performance
- 🟡 **Yellow**: Modified proposals, warnings
- 🔵 **Blue**: Information, current generation
- ⚪ **Gray**: Baseline reference

---

## 💡 Tips

**For Rich Terminal:**
- Use `--steps 5000` for faster iterations during testing
- Output is saved to files even with visual mode
- Press Ctrl+C to interrupt gracefully

**For Streamlit:**
- Adjust auto-refresh interval in sidebar (2-30 seconds)
- Click on generations to expand/collapse details
- Use dark theme for better visibility
- Dashboard updates as files are written by orchestrator

---

## 📁 Output Files

Both modes save identical output structure:
```
runs/iai_evolution/
├── baseline_results.json
├── authority_decisions.json
├── evolution_report.txt
└── generation_000/
    ├── invariants.json
    ├── iai_results.json
    ├── proposal.json
    └── decision.json
```

This means you can:
1. Run with Rich Terminal for live feedback
2. Open Streamlit Dashboard later for analysis
3. Share results folder with team
