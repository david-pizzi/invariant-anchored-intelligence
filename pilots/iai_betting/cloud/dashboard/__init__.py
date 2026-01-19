"""
DASHBOARD API - Azure HTTP Function
====================================
Returns current predictions and performance as JSON.
Access via: https://<function-app>.azurewebsites.net/api/dashboard

Optional query params:
- format=html  (returns HTML instead of JSON)
"""

import azure.functions as func
import logging
import json
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.storage import load_predictions
from shared.authority import get_authority

logger = logging.getLogger(__name__)


def generate_html(data):
    """Generate HTML dashboard."""
    bankroll = data['bankroll']
    summary = data['results_summary']
    predictions = data['predictions']
    
    # Get live Authority status
    authority = get_authority()
    auth_report = authority.generate_report(predictions)
    
    profit = bankroll['current'] - bankroll['initial']
    profit_color = "green" if profit >= 0 else "red"
    
    pending = [p for p in predictions if p['status'] == 'pending']
    settled = [p for p in predictions if p['status'] in ['won', 'lost']]
    
    # Sort pending bets by date (earliest first)
    pending.sort(key=lambda x: x['match_date'])
    
    # Calculate projected balance if all pending bets win
    projected_balance = bankroll['current'] + sum(p.get('potential_profit', 0) for p in pending)
    projected_profit = projected_balance - bankroll['initial']
    projected_color = "green" if projected_profit >= 0 else "red"
    
    # Get last pending bet date for projection
    last_bet_date = max([p['match_date'] for p in pending]) if pending else 'N/A'
    projected_label = f"Projected by {last_bet_date}" if pending else "Projected"
    
    # Get first bet date for initial bankroll label
    first_bet_date = min([p['created_at'][:10] for p in predictions]) if predictions else 'N/A'
    initial_label = f"Initial ({first_bet_date})"
    
    if summary['wins'] + summary['losses'] > 0:
        win_rate = summary['wins'] / (summary['wins'] + summary['losses']) * 100
    else:
        win_rate = 0
    
    # Authority status styling
    auth_status = auth_report['status']
    auth_color = {"NORMAL": "#00ff88", "REDUCED": "#ffaa00", "PAUSED": "#ff4444"}.get(auth_status, "#888")
    
    # Build recommendations list
    recs_html = "".join(f"<li>{r}</li>" for r in auth_report['recommendations'])
    
    # Build pending table
    pending_rows = ""
    for p in pending:
        stake_note = f" ({p.get('stake_reason', '')})" if 'stake_reason' in p else ""
        league_name = p.get('league_name', 'EPL' if p.get('league', 'E0') == 'E0' else 'Bundesliga')
        implied_prob = (1 / p['odds']) * 100  # Bookmaker's implied probability
        pending_rows += f"""
        <tr>
            <td>{p['match_date']}</td>
            <td>{league_name}</td>
            <td><strong>{p['home_team']}</strong> vs {p['away_team']}</td>
            <td>{p['odds']:.2f}</td>
            <td>{implied_prob:.1f}%</td>
            <td>£{p['stake']:.2f}</td>
            <td>£{p['potential_profit']:.2f}</td>
        </tr>
        """
    
    # Build recent results table
    results_rows = ""
    for p in settled[-10:]:
        if p['status'] == 'won':
            status = '<span style="color:green">✅ WON</span>'
            pl = f'<span style="color:green">+£{p["profit_loss"]:.2f}</span>'
        else:
            status = '<span style="color:red">❌ LOST</span>'
            pl = f'<span style="color:red">-£{abs(p["profit_loss"]):.2f}</span>'
        
        league_name = p.get('league_name', 'EPL' if p.get('league', 'E0') == 'E0' else 'Bundesliga')
        results_rows += f"""
        <tr>
            <td>{p['match_date']}</td>
            <td>{league_name}</td>
            <td>{p['home_team']} vs {p['away_team']}</td>
            <td>🏠 {p['home_team']} Win</td>
            <td>{p['odds']:.2f}</td>
            <td>{p.get('score', '-')}</td>
            <td>{status}</td>
            <td>{pl}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IAI Betting Tracker</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   max-width: 1400px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #eee; }}
            h1 {{ color: #00d9ff; }}
            h2 {{ color: #ff6b6b; border-bottom: 1px solid #333; padding-bottom: 10px; }}
            .card {{ background: #16213e; border-radius: 10px; padding: 20px; margin: 20px 0; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
            .stat {{ text-align: center; padding: 15px; background: #0f3460; border-radius: 8px; }}
            .stat-value {{ font-size: 24px; font-weight: bold; }}
            .stat-label {{ font-size: 12px; color: #aaa; margin-top: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #333; white-space: nowrap; }}
            th {{ color: #00d9ff; }}
            .profit {{ color: {profit_color}; font-size: 24px; font-weight: bold; }}
            .updated {{ color: #666; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>🤖 IAI Betting Tracker</h1>
        
        <div class="card">
            <h2>💰 Bankroll</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">£{bankroll['initial']:,.0f}</div>
                    <div class="stat-label">{initial_label}</div>
                </div>
                <div class="stat">
                    <div class="stat-value">£{bankroll['current']:,.0f}</div>
                    <div class="stat-label">Current</div>
                </div>
                <div class="stat">
                    <div class="stat-value profit">£{profit:+,.0f}</div>
                    <div class="stat-label">Profit</div>
                </div>
                <div class="stat">
                    <div class="stat-value" style="color: {projected_color}">£{projected_balance:,.0f}</div>
                    <div class="stat-label">{projected_label}</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📊 Performance</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{summary['total_bets']}</div>
                    <div class="stat-label">Total Bets</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{summary['wins']}W - {summary['losses']}L</div>
                    <div class="stat-label">Record</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{win_rate:.1f}%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat">
                    <div class="stat-value" style="color: {profit_color}">{summary['roi_pct']:+.1f}%</div>
                    <div class="stat-label">ROI</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>⏳ Pending Bets ({len(pending)})</h2>
            {f'''<table>
                <tr><th>Date</th><th>League</th><th>Match</th><th>Odds</th><th>Prob%</th><th>Stake</th><th>Pot. Win</th></tr>
                {pending_rows}
            </table>''' if pending else '<p>No pending bets</p>'}
        </div>
        
        <div class="card">
            <h2>📋 Recent Results</h2>
            {f'''<table>
                <tr><th>Date</th><th>League</th><th>Match</th><th>Bet</th><th>Odds</th><th>Score</th><th>Result</th><th>P/L</th></tr>
                {results_rows}
            </table>''' if settled else '<p>No results yet</p>'}
        </div>
        
        <div class="card">
            <h2>🛡️ IAI Authority</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" style="color: {auth_color}">{auth_report['status_emoji']} {auth_status}</div>
                    <div class="stat-label">Status</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{auth_report['stake_multiplier']*100:.0f}%</div>
                    <div class="stat-label">Stake Level</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{auth_report['edge_status']}</div>
                    <div class="stat-label">Edge Status</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{auth_report['performance'].get('current_streak', 0)}</div>
                    <div class="stat-label">{auth_report['performance'].get('streak_type', 'N/A').title() if auth_report['performance'].get('streak_type') else 'N/A'} Streak</div>
                </div>
            </div>
            <div style="margin-top: 15px; padding: 10px; background: #0f3460; border-radius: 8px;">
                <strong>Recommendations:</strong>
                <ul style="margin: 10px 0; padding-left: 20px;">{recs_html}</ul>
            </div>
        </div>
        
        <div class="card">
            <h2>🔄 Manual Actions</h2>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button onclick="runNow()" style="padding: 15px 30px; background: #00d9ff; color: #000; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer;">
                    🔄 Run Tracker Now
                </button>
                <button onclick="location.reload()" style="padding: 15px 30px; background: #ff6b6b; color: #fff; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer;">
                    🔃 Refresh Dashboard
                </button>
            </div>
            <p id="status" style="margin-top: 15px; font-weight: bold;"></p>
        </div>
        
        <p class="updated">Last updated: {data.get('last_updated', 'Never')}</p>
        <p class="updated">Strategy: HOME WIN @ 4.0-6.0 odds, 3% stake (EPL + Bundesliga)</p>
        
        <script>
        async function runNow() {{
            const statusEl = document.getElementById('status');
            statusEl.textContent = '⏳ Running tracker...';
            statusEl.style.color = '#ffaa00';
            
            try {{
                const response = await fetch('/api/run_now', {{ method: 'POST' }});
                const result = await response.json();
                
                if (response.ok) {{
                    statusEl.textContent = '✅ Tracker completed! Refresh page to see updates.';
                    statusEl.style.color = '#00ff88';
                    
                    // Auto-refresh after 3 seconds
                    setTimeout(() => location.reload(), 3000);
                }} else {{
                    statusEl.textContent = '❌ Error: ' + (result.error || 'Unknown error');
                    statusEl.style.color = '#ff4444';
                }}
            }} catch (error) {{
                statusEl.textContent = '❌ Network error: ' + error.message;
                statusEl.style.color = '#ff4444';
            }}
        }}
        </script>
    </body>
    </html>
    """
    return html


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function - HTTP endpoint."""
    logger.info("Dashboard request received")
    
    try:
        data = load_predictions()
        
        # Check format parameter
        format_param = req.params.get('format', 'json')
        
        if format_param == 'html':
            html = generate_html(data)
            return func.HttpResponse(
                html,
                mimetype="text/html",
                status_code=200
            )
        else:
            return func.HttpResponse(
                json.dumps(data, indent=2),
                mimetype="application/json",
                status_code=200
            )
            
    except Exception as e:
        logger.error(f"Error in dashboard: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
