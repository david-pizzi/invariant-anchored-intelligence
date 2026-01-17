"""Logging components for IAI.

Provides audit logging and experiment tracking for
reproducibility and analysis.

This module provides:
- AuditLogger: Tamper-evident logging for Authority decisions
- ExperimentTracker: Experiment tracking and artifact management
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import hashlib
import csv


class AuditLogger:
    """
    Tamper-evident audit logger for IAI decisions.
    
    All Authority decisions, proposals, and invariant changes are
    logged with timestamps and hashes for auditability.
    """
    
    def __init__(self, log_dir: str = "logs/audit"):
        """
        Initialize AuditLogger.
        
        Args:
            log_dir: Directory for audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.previous_hash = "GENESIS"
        self.entry_count = 0
    
    def log(
        self,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an event with chain hashing.
        
        Args:
            event_type: Type of event (e.g., "PROPOSAL", "DECISION", "INVARIANT_CHANGE")
            data: Event data
            metadata: Optional additional metadata
        """
        entry = {
            "entry_id": self.entry_count,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
            "metadata": metadata or {},
            "previous_hash": self.previous_hash,
        }
        
        # Compute hash of this entry
        entry_json = json.dumps(entry, sort_keys=True, default=str)
        entry_hash = hashlib.sha256(entry_json.encode()).hexdigest()
        entry["hash"] = entry_hash
        
        # Write to log file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
        
        self.previous_hash = entry_hash
        self.entry_count += 1
        
        return entry_hash
    
    def log_proposal(
        self,
        generation: int,
        proposal: Dict[str, Any],
    ) -> str:
        """Log a Challenger proposal."""
        return self.log(
            event_type="PROPOSAL",
            data={"generation": generation, "proposal": proposal},
        )
    
    def log_decision(
        self,
        generation: int,
        decision: Dict[str, Any],
        proposal_hash: str,
    ) -> str:
        """Log an Authority decision."""
        return self.log(
            event_type="DECISION",
            data={
                "generation": generation,
                "decision": decision,
                "proposal_hash": proposal_hash,
            },
        )
    
    def log_invariant_change(
        self,
        generation: int,
        old_invariants: Dict[str, Any],
        new_invariants: Dict[str, Any],
        decision_hash: str,
    ) -> str:
        """Log an invariant change."""
        return self.log(
            event_type="INVARIANT_CHANGE",
            data={
                "generation": generation,
                "old": old_invariants,
                "new": new_invariants,
                "decision_hash": decision_hash,
            },
        )
    
    def verify_chain(self) -> bool:
        """
        Verify the integrity of the audit log.
        
        Returns:
            True if chain is valid, False if tampering detected
        """
        if not self.log_file.exists():
            return True
        
        previous_hash = "GENESIS"
        
        with open(self.log_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                entry = json.loads(line)
                
                # Check chain
                if entry["previous_hash"] != previous_hash:
                    print(f"Chain broken at entry {line_num}")
                    return False
                
                # Verify hash
                stored_hash = entry.pop("hash")
                entry_json = json.dumps(entry, sort_keys=True, default=str)
                computed_hash = hashlib.sha256(entry_json.encode()).hexdigest()
                
                if stored_hash != computed_hash:
                    print(f"Hash mismatch at entry {line_num}")
                    return False
                
                previous_hash = stored_hash
                entry["hash"] = stored_hash  # Restore
        
        return True


class ExperimentTracker:
    """
    Experiment tracking for IAI runs.
    
    Tracks experiments with metrics, parameters, and artifacts
    for reproducibility and analysis.
    """
    
    def __init__(self, base_dir: str = "runs"):
        """
        Initialize ExperimentTracker.
        
        Args:
            base_dir: Base directory for experiment runs
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_run: Optional[Path] = None
        self.run_config: Dict[str, Any] = {}
        self.metrics_log: List[Dict[str, Any]] = []
    
    def start_run(
        self,
        name: str = "",
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Start a new experiment run.
        
        Args:
            name: Optional run name
            config: Run configuration
            
        Returns:
            Path to run directory
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        run_name = f"{timestamp}_{name}" if name else timestamp
        
        self.current_run = self.base_dir / run_name
        self.current_run.mkdir(parents=True, exist_ok=True)
        
        self.run_config = config or {}
        self.metrics_log = []
        
        # Save config
        with open(self.current_run / "config.json", "w") as f:
            json.dump(self.run_config, f, indent=2, default=str)
        
        return self.current_run
    
    def log_metrics(
        self,
        metrics: Dict[str, float],
        step: Optional[int] = None,
        generation: Optional[int] = None,
    ):
        """Log metrics for current run."""
        if not self.current_run:
            raise RuntimeError("No active run. Call start_run() first.")
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "generation": generation,
            **metrics,
        }
        self.metrics_log.append(entry)
        
        # Append to metrics CSV
        metrics_file = self.current_run / "metrics.csv"
        write_header = not metrics_file.exists()
        
        with open(metrics_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=entry.keys())
            if write_header:
                writer.writeheader()
            writer.writerow(entry)
    
    def save_artifact(
        self,
        name: str,
        data: Any,
        artifact_type: str = "json",
    ):
        """
        Save an artifact.
        
        Args:
            name: Artifact name
            data: Artifact data
            artifact_type: Type ("json", "csv", "text")
        """
        if not self.current_run:
            raise RuntimeError("No active run. Call start_run() first.")
        
        artifacts_dir = self.current_run / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        if artifact_type == "json":
            with open(artifacts_dir / f"{name}.json", "w") as f:
                json.dump(data, f, indent=2, default=str)
        elif artifact_type == "csv":
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                data.to_csv(artifacts_dir / f"{name}.csv", index=False)
            else:
                raise ValueError("CSV artifact requires DataFrame")
        else:
            with open(artifacts_dir / f"{name}.txt", "w") as f:
                f.write(str(data))
    
    def end_run(self, summary: Optional[Dict[str, Any]] = None):
        """End current run with optional summary."""
        if not self.current_run:
            return
        
        final_summary = {
            "config": self.run_config,
            "metrics_count": len(self.metrics_log),
            "summary": summary or {},
            "end_time": datetime.now().isoformat(),
        }
        
        with open(self.current_run / "summary.json", "w") as f:
            json.dump(final_summary, f, indent=2, default=str)
        
        self.current_run = None
    
    def list_runs(self) -> List[Dict[str, Any]]:
        """List all experiment runs."""
        runs = []
        for run_dir in sorted(self.base_dir.iterdir()):
            if run_dir.is_dir():
                config_file = run_dir / "config.json"
                if config_file.exists():
                    with open(config_file) as f:
                        config = json.load(f)
                else:
                    config = {}
                
                runs.append({
                    "name": run_dir.name,
                    "path": str(run_dir),
                    "config": config,
                })
        
        return runs
