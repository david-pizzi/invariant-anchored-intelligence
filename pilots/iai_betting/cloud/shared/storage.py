"""
Shared code for Azure Functions - Blob Storage operations
"""

import json
import os
import logging
from datetime import datetime
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)

# Configuration
CONTAINER_NAME = "iai-betting"
PREDICTIONS_BLOB = "predictions.json"

# Strategy parameters
STRATEGY = {
    "name": "Home Underdog Edge (EPL + Bundesliga)",
    "selection": "H",
    "odds_min": 4.0,
    "odds_max": 6.0,
    "stake_pct": 3.0,
    "expected_edge": 5.0,  # Avg of EPL 5.6% and D1 4.3%
    "leagues": ["E0", "D1"]
}

INITIAL_BANKROLL = 1000


def get_blob_service_client():
    """Get Azure Blob Storage client."""
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING not set")
    return BlobServiceClient.from_connection_string(connection_string)


def ensure_container_exists():
    """Create container if it doesn't exist."""
    client = get_blob_service_client()
    container_client = client.get_container_client(CONTAINER_NAME)
    try:
        container_client.get_container_properties()
    except Exception:
        container_client.create_container()
        logger.info(f"Created container: {CONTAINER_NAME}")


def load_predictions():
    """Load predictions from blob storage."""
    try:
        client = get_blob_service_client()
        blob_client = client.get_blob_client(CONTAINER_NAME, PREDICTIONS_BLOB)
        
        try:
            data = blob_client.download_blob().readall()
            return json.loads(data)
        except Exception:
            # Initialize with empty predictions
            return create_initial_state()
    except Exception as e:
        logger.error(f"Error loading predictions: {e}")
        return create_initial_state()


def create_initial_state():
    """Create initial predictions state."""
    return {
        "strategy": STRATEGY,
        "bankroll": {
            "initial": INITIAL_BANKROLL,
            "current": INITIAL_BANKROLL
        },
        "predictions": [],
        "results_summary": {
            "total_bets": 0,
            "wins": 0,
            "losses": 0,
            "pending": 0,
            "profit": 0,
            "roi_pct": 0
        },
        "last_updated": None,
        "run_history": []
    }


def save_predictions(data):
    """Save predictions to blob storage."""
    data['last_updated'] = datetime.utcnow().isoformat()
    
    client = get_blob_service_client()
    ensure_container_exists()
    
    # Save current state
    blob_client = client.get_blob_client(CONTAINER_NAME, PREDICTIONS_BLOB)
    blob_client.upload_blob(
        json.dumps(data, indent=2),
        overwrite=True
    )
    
    # Save daily snapshot for audit trail
    today = datetime.utcnow().strftime("%Y-%m-%d")
    history_blob = f"history/{today}.json"
    history_client = client.get_blob_client(CONTAINER_NAME, history_blob)
    history_client.upload_blob(
        json.dumps(data, indent=2),
        overwrite=True
    )
    
    logger.info(f"Saved predictions to blob storage")


def update_summary(data):
    """Recalculate results summary."""
    predictions = data['predictions']
    
    wins = sum(1 for p in predictions if p['status'] == 'won')
    losses = sum(1 for p in predictions if p['status'] == 'lost')
    pending = sum(1 for p in predictions if p['status'] == 'pending')
    
    profit = sum(p['profit_loss'] or 0 for p in predictions)
    total_staked = sum(p['stake'] for p in predictions if p['status'] in ['won', 'lost'])
    roi = (profit / total_staked * 100) if total_staked > 0 else 0
    
    data['results_summary'] = {
        "total_bets": len(predictions),
        "wins": wins,
        "losses": losses,
        "pending": pending,
        "profit": round(profit, 2),
        "roi_pct": round(roi, 1)
    }
    
    data['bankroll']['current'] = round(data['bankroll']['initial'] + profit, 2)
