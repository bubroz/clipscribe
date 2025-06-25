"""
Performance monitoring and metrics collection for ClipScribe.

This module provides utilities to track API response times, extraction quality,
and other performance-related metrics to identify bottlenecks and opportunities
for optimization.
"""
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class PerformanceMonitor:
    """A class to handle performance metric collection and reporting."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir / "performance"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metrics: List[Dict[str, Any]] = []

    def start_timer(self, event_name: str, **kwargs) -> Dict[str, Any]:
        """
        Start a timer for a specific event.

        Args:
            event_name: The name of the event being timed.
            **kwargs: Additional metadata to store with the event.

        Returns:
            A dictionary representing the running event timer.
        """
        event = {
            "event": event_name,
            "start_time": time.monotonic(),
            "end_time": None,
            "duration": None,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        return event

    def stop_timer(self, event: Dict[str, Any]):
        """
        Stop a timer and record the metric.

        Args:
            event: The event dictionary returned by start_timer.
        """
        if event and "start_time" in event and event.get("end_time") is None:
            event["end_time"] = time.monotonic()
            event["duration"] = event["end_time"] - event["start_time"]
            self.metrics.append(event)

    def record_metric(self, event_name: str, value: Any, **kwargs):
        """
        Record a single, non-timed metric.

        Args:
            event_name: The name of the metric.
            value: The value of the metric.
            **kwargs: Additional metadata.
        """
        metric = {
            "event": event_name,
            "value": value,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        self.metrics.append(metric)

    def save_report(self):
        """Save the collected performance metrics to a JSON file."""
        if not self.metrics:
            return

        report_path = self.output_dir / f"performance_report_{self.session_id}.json"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=2)
        except IOError as e:
            print(f"Error saving performance report: {e}")

# Global instance (optional, can be instantiated per run)
# For now, let's not use a global instance to avoid state issues between runs. 