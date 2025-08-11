"""
Performance Dashboard for ClipScribe Streamlit UI.

This module provides interactive dashboards for monitoring ClipScribe performance
including model cache efficiency, batch processing metrics, and system health.
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import time

# Optional Plotly imports for advanced visualizations
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from ..extractors.model_manager import get_model_manager


class PerformanceDashboard:
    """Interactive performance dashboard for ClipScribe."""

    def __init__(self, output_dir: Path):
        """Initialize the performance dashboard."""
        self.output_dir = Path(output_dir)
        self.performance_dir = self.output_dir / "performance"
        self.performance_dir.mkdir(parents=True, exist_ok=True)

    def render_dashboard(self):
        """Render the main performance dashboard."""
        st.header(" ClipScribe Performance Dashboard")
        st.markdown("Real-time monitoring of ClipScribe performance metrics and system health.")

        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            [" Model Cache", " Batch Processing", " System Health", " Historical Reports"]
        )

        with tab1:
            self._render_model_cache_dashboard()

        with tab2:
            self._render_batch_processing_dashboard()

        with tab3:
            self._render_system_health_dashboard()

        with tab4:
            self._render_historical_reports_dashboard()

    def _render_model_cache_dashboard(self):
        """Render the model cache performance dashboard."""
        st.subheader(" Model Cache Performance")

        # Get current cache information
        model_manager = get_model_manager()
        cache_info = model_manager.get_cache_info()
        perf_summary = model_manager.get_performance_summary()

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Cached Models",
                cache_info["model_count"],
                help="Number of models currently cached in memory",
            )

        with col2:
            hit_rate = cache_info["hit_rate"]
            st.metric(
                "Cache Hit Rate",
                f"{hit_rate:.1%}",
                delta=f"{hit_rate - 0.8:.1%}" if hit_rate > 0 else None,
                help="Percentage of model requests served from cache",
            )

        with col3:
            total_accesses = cache_info["total_accesses"]
            st.metric(
                "Total Accesses", total_accesses, help="Total number of model access requests"
            )

        with col4:
            time_saved = perf_summary["cache_efficiency"].get("estimated_time_saved", 0)
            st.metric(
                "Time Saved",
                f"{time_saved:.1f}s",
                help="Estimated time saved through model caching",
            )

        # Cache details
        if cache_info["cached_models"]:
            st.subheader(" Cached Models Details")

            model_data = []
            for model in cache_info["cached_models"]:
                load_time = cache_info["load_times"].get(model, 0)
                access_count = cache_info["access_counts"].get(model, 0)

                model_data.append(
                    {
                        "Model": model,
                        "Load Time (s)": f"{load_time:.2f}",
                        "Access Count": access_count,
                        "Time Saved (s)": (
                            f"{load_time * (access_count - 1):.2f}" if access_count > 1 else "0.00"
                        ),
                    }
                )

            df = pd.DataFrame(model_data)
            st.dataframe(df, use_container_width=True)

            # Visualizations if Plotly is available
            if PLOTLY_AVAILABLE and len(model_data) > 0:
                st.subheader(" Cache Performance Visualization")

                # Create access count bar chart
                fig = go.Figure(
                    data=[
                        go.Bar(
                            x=[item["Model"] for item in model_data],
                            y=[item["Access Count"] for item in model_data],
                            marker_color="lightblue",
                            text=[item["Access Count"] for item in model_data],
                            textposition="auto",
                        )
                    ]
                )

                fig.update_layout(
                    title="Model Access Frequency",
                    xaxis_title="Model",
                    yaxis_title="Access Count",
                    showlegend=False,
                )

                st.plotly_chart(fig, use_container_width=True)

        # Performance recommendations
        recommendations = perf_summary.get("recommendations", [])
        if recommendations:
            st.subheader(" Performance Recommendations")
            for rec in recommendations:
                st.info(rec)

        # Cache controls
        st.subheader(" Cache Controls")
        col1, col2 = st.columns(2)

        with col1:
            if st.button(" Clear Model Cache"):
                get_model_manager().clear_cache()
                st.success("Model cache cleared successfully!")
                st.rerun()

        with col2:
            if st.button(" Refresh Cache Info"):
                st.rerun()

    def _render_batch_processing_dashboard(self):
        """Render the batch processing performance dashboard."""
        st.subheader(" Batch Processing Performance")

        # Check if there's a performance monitor in session state
        if (
            "performance_monitor" not in st.session_state
            or not st.session_state.performance_monitor
        ):
            st.info(
                "No active batch processing session. Start a batch operation to see metrics here."
            )
            return

        perf_monitor = st.session_state.performance_monitor
        batch_stats = perf_monitor.get_batch_stats()

        if not batch_stats:
            st.info("No batch processing data available yet.")
            return

        # Batch metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Videos Processed",
                batch_stats["videos_processed"],
                help="Total number of videos processed in current batch",
            )

        with col2:
            success_rate = batch_stats.get("success_rate", 0)
            st.metric(
                "Success Rate",
                f"{success_rate:.1%}",
                delta=f"{success_rate - 0.9:.1%}" if success_rate > 0 else None,
                help="Percentage of videos processed successfully",
            )

        with col3:
            total_entities = batch_stats["total_entities"]
            st.metric(
                "Total Entities", total_entities, help="Total entities extracted across all videos"
            )

        with col4:
            total_time = batch_stats["total_time_seconds"]
            st.metric(
                "Total Time", f"{total_time:.1f}s", help="Total time spent on batch processing"
            )

        # Throughput metrics
        throughput = batch_stats.get("throughput", {})
        if throughput:
            st.subheader(" Throughput Metrics")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Videos/min",
                    f"{throughput['videos_per_minute']:.1f}",
                    help="Videos processed per minute",
                )

            with col2:
                st.metric(
                    "Entities/min",
                    f"{throughput['entities_per_minute']:.0f}",
                    help="Entities extracted per minute",
                )

            with col3:
                st.metric(
                    "Relationships/min",
                    f"{throughput['relationships_per_minute']:.0f}",
                    help="Relationships extracted per minute",
                )

        # Performance metrics
        perf_metrics = batch_stats.get("performance_metrics", {})
        if perf_metrics:
            st.subheader(" Performance Metrics")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Avg Processing Time",
                    f"{perf_metrics['avg_processing_time']:.1f}s",
                    help="Average time per video",
                )

            with col2:
                st.metric(
                    "Min Processing Time",
                    f"{perf_metrics['min_processing_time']:.1f}s",
                    help="Fastest video processing time",
                )

            with col3:
                st.metric(
                    "Max Processing Time",
                    f"{perf_metrics['max_processing_time']:.1f}s",
                    help="Slowest video processing time",
                )

        # Real-time progress if batch is active
        if st.session_state.get("research_in_progress", False):
            st.subheader(" Real-time Progress")

            batch_progress = st.session_state.get("batch_progress", {})
            if batch_progress:
                progress_value = batch_progress.get("completed", 0) / max(
                    batch_progress.get("total", 1), 1
                )

                st.progress(
                    progress_value,
                    text=f"Processing: {batch_progress.get('completed', 0)}/{batch_progress.get('total', 0)} videos",
                )

                if batch_progress.get("current_video"):
                    st.text(f"Current: {batch_progress['current_video'][:60]}...")

                # ETA calculation
                if batch_progress.get("start_time") and batch_progress.get("completed", 0) > 0:
                    elapsed = time.time() - batch_progress["start_time"]
                    remaining = batch_progress.get("total", 0) - batch_progress.get("completed", 0)
                    if remaining > 0:
                        eta = (elapsed / batch_progress["completed"]) * remaining
                        st.text(f"ETA: {eta:.0f} seconds")

    def _render_system_health_dashboard(self):
        """Render the system health monitoring dashboard."""
        st.subheader(" System Health")

        # System information
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(" System Info")

            # Get system information
            import platform

            try:
                import psutil

                PSUTIL_AVAILABLE = True
            except ImportError:
                PSUTIL_AVAILABLE = False
                st.warning("psutil not available. Install with: pip install psutil")

            system_info = {
                "OS": platform.system(),
                "Python Version": platform.python_version(),
            }

            if PSUTIL_AVAILABLE:
                system_info.update(
                    {
                        "CPU Cores": psutil.cpu_count(),
                        "Memory (GB)": f"{psutil.virtual_memory().total / (1024**3):.1f}",
                        "Available Memory (GB)": f"{psutil.virtual_memory().available / (1024**3):.1f}",
                        "Memory Usage": f"{psutil.virtual_memory().percent:.1f}%",
                    }
                )

            for key, value in system_info.items():
                st.text(f"{key}: {value}")

        with col2:
            st.subheader(" Resource Usage")

            if PSUTIL_AVAILABLE:
                # CPU and Memory usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent

                # Create gauge charts if Plotly is available
                if PLOTLY_AVAILABLE:
                    fig = go.Figure()

                    fig.add_trace(
                        go.Indicator(
                            mode="gauge+number",
                            value=cpu_percent,
                            domain={"x": [0, 0.5], "y": [0, 1]},
                            title={"text": "CPU Usage (%)"},
                            gauge={
                                "axis": {"range": [None, 100]},
                                "bar": {"color": "darkblue"},
                                "steps": [
                                    {"range": [0, 50], "color": "lightgray"},
                                    {"range": [50, 80], "color": "yellow"},
                                ],
                                "threshold": {
                                    "line": {"color": "red", "width": 4},
                                    "thickness": 0.75,
                                    "value": 90,
                                },
                            },
                        )
                    )

                    fig.add_trace(
                        go.Indicator(
                            mode="gauge+number",
                            value=memory_percent,
                            domain={"x": [0.5, 1], "y": [0, 1]},
                            title={"text": "Memory Usage (%)"},
                            gauge={
                                "axis": {"range": [None, 100]},
                                "bar": {"color": "darkgreen"},
                                "steps": [
                                    {"range": [0, 50], "color": "lightgray"},
                                    {"range": [50, 80], "color": "yellow"},
                                ],
                                "threshold": {
                                    "line": {"color": "red", "width": 4},
                                    "thickness": 0.75,
                                    "value": 90,
                                },
                            },
                        )
                    )

                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.metric("CPU Usage", f"{cpu_percent:.1f}%")
                    st.metric("Memory Usage", f"{memory_percent:.1f}%")
            else:
                st.info("Install psutil for detailed resource monitoring")

        # Environment check
        st.subheader(" Environment Check")

        env_checks = {
            "Google API Key": "GOOGLE_API_KEY" in st.secrets
            or "GOOGLE_API_KEY" in st.session_state,
            "Plotly Available": PLOTLY_AVAILABLE,
            "Model Manager": True,  # Runtime always has a manager instance in UI
            "Output Directory": self.output_dir.exists(),
        }

        for check, status in env_checks.items():
            if status:
                st.success(f" {check}")
            else:
                st.error(f" {check}")

        # Disk space check
        if PSUTIL_AVAILABLE:
            disk_usage = psutil.disk_usage(str(self.output_dir))
            disk_free_gb = disk_usage.free / (1024**3)
            disk_total_gb = disk_usage.total / (1024**3)
            disk_used_percent = (disk_usage.used / disk_usage.total) * 100

            st.subheader(" Disk Space")
            st.metric(
                "Available Space",
                f"{disk_free_gb:.1f} GB / {disk_total_gb:.1f} GB",
                delta=f"-{disk_used_percent:.1f}% used",
            )

            if disk_free_gb < 1:
                st.warning(" Low disk space! Consider cleaning up output files.")

    def _render_historical_reports_dashboard(self):
        """Render the historical performance reports dashboard."""
        st.subheader(" Historical Performance Reports")

        # Find all performance reports
        report_files = list(self.performance_dir.glob("performance_report_*.json"))

        if not report_files:
            st.info(
                "No historical performance reports found. Run some batch operations to generate reports."
            )
            return

        # Sort by creation time (newest first)
        report_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        st.write(f"Found {len(report_files)} performance reports")

        # Report selection
        selected_report = st.selectbox(
            "Select a report to view:",
            options=report_files,
            format_func=lambda x: f"{x.stem} ({datetime.fromtimestamp(x.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')})",
        )

        if selected_report:
            try:
                with open(selected_report, "r", encoding="utf-8") as f:
                    report_data = json.load(f)

                self._display_performance_report(report_data)

            except Exception as e:
                st.error(f"Error loading report: {e}")

        # Bulk operations
        st.subheader(" Report Management")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(" Clear Old Reports"):
                # Keep only the 10 most recent reports
                if len(report_files) > 10:
                    for report in report_files[10:]:
                        report.unlink()
                    st.success(f"Removed {len(report_files) - 10} old reports")
                    st.rerun()
                else:
                    st.info("No old reports to remove")

        with col2:
            if st.button(" Generate Summary Report"):
                summary = self._generate_summary_report(report_files[:5])  # Last 5 reports
                st.json(summary)

    def _display_performance_report(self, report_data: Dict[str, Any]):
        """Display a detailed performance report."""
        summary = report_data.get("summary", {})

        # Report header
        st.subheader(f" Report: {summary.get('session_id', 'Unknown')}")
        st.text(f"Generated: {summary.get('timestamp', 'Unknown')}")

        # Model cache stats
        cache_stats = summary.get("model_cache_stats", {})
        if cache_stats:
            st.subheader(" Model Cache Performance")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Hit Rate", f"{cache_stats.get('hit_rate', 0):.1%}")

            with col2:
                st.metric("Total Hits", cache_stats.get("total_hits", 0))

            with col3:
                st.metric("Total Misses", cache_stats.get("total_misses", 0))

            # Per-model performance
            cache_performance = cache_stats.get("cache_performance", {})
            if cache_performance:
                st.subheader(" Per-Model Performance")

                model_data = []
                for model, perf in cache_performance.items():
                    model_data.append(
                        {
                            "Model": model,
                            "Hit Rate": f"{perf['hit_rate']:.1%}",
                            "Hits": perf["hits"],
                            "Misses": perf["misses"],
                            "Total Requests": perf["total_requests"],
                        }
                    )

                df = pd.DataFrame(model_data)
                st.dataframe(df, use_container_width=True)

        # Batch stats
        batch_stats = summary.get("batch_stats", {})
        if batch_stats:
            st.subheader(" Batch Processing Stats")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Videos Processed", batch_stats.get("videos_processed", 0))

            with col2:
                st.metric("Success Rate", f"{batch_stats.get('success_rate', 0):.1%}")

            with col3:
                st.metric("Total Entities", batch_stats.get("total_entities", 0))

            with col4:
                st.metric("Total Time", f"{batch_stats.get('total_time_seconds', 0):.1f}s")

        # Recommendations
        recommendations = summary.get("recommendations", [])
        if recommendations:
            st.subheader(" Recommendations")
            for rec in recommendations:
                st.info(rec)

        # Raw data expander
        with st.expander(" Raw Report Data"):
            st.json(report_data)

    def _generate_summary_report(self, report_files: List[Path]) -> Dict[str, Any]:
        """Generate a summary report from multiple performance reports."""
        summary = {
            "reports_analyzed": len(report_files),
            "time_range": {},
            "aggregate_stats": {
                "total_videos_processed": 0,
                "total_entities_extracted": 0,
                "average_success_rate": 0,
                "average_cache_hit_rate": 0,
            },
            "trends": {},
        }

        if not report_files:
            return summary

        # Collect data from all reports
        success_rates = []
        cache_hit_rates = []
        videos_processed = []
        entities_extracted = []
        timestamps = []

        for report_file in report_files:
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                report_summary = data.get("summary", {})

                # Extract metrics
                batch_stats = report_summary.get("batch_stats", {})
                cache_stats = report_summary.get("model_cache_stats", {})

                if batch_stats:
                    success_rates.append(batch_stats.get("success_rate", 0))
                    videos_processed.append(batch_stats.get("videos_processed", 0))
                    entities_extracted.append(batch_stats.get("total_entities", 0))

                if cache_stats:
                    cache_hit_rates.append(cache_stats.get("hit_rate", 0))

                # Extract timestamp
                timestamp = report_summary.get("timestamp", "")
                if timestamp:
                    timestamps.append(timestamp)

            except Exception:
                continue

        # Calculate aggregates
        if success_rates:
            summary["aggregate_stats"]["average_success_rate"] = sum(success_rates) / len(
                success_rates
            )

        if cache_hit_rates:
            summary["aggregate_stats"]["average_cache_hit_rate"] = sum(cache_hit_rates) / len(
                cache_hit_rates
            )

        summary["aggregate_stats"]["total_videos_processed"] = sum(videos_processed)
        summary["aggregate_stats"]["total_entities_extracted"] = sum(entities_extracted)

        # Time range
        if timestamps:
            summary["time_range"] = {"earliest": min(timestamps), "latest": max(timestamps)}

        return summary


def create_performance_dashboard(output_dir: Path) -> PerformanceDashboard:
    """Create a new performance dashboard instance."""
    return PerformanceDashboard(output_dir)
