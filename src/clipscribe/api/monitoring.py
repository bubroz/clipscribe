"""
Monitoring System for ClipScribe - Comprehensive metrics, alerts, and health checks.
"""

import time
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import os

# Import psutil conditionally
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

# Import redis conditionally to avoid import errors in environments without it
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """Represents a single metric measurement."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    condition: str  # e.g., "cpu_usage > 90"
    threshold: float
    duration: int  # seconds
    severity: str  # "info", "warning", "error", "critical"
    cooldown: int  # seconds between alerts


@dataclass
class Alert:
    """Active alert instance."""
    rule_name: str
    message: str
    severity: str
    timestamp: datetime
    value: float
    threshold: float


class MetricsCollector:
    """Collects and stores system and application metrics."""

    def __init__(self, redis_conn = None):
        self.redis = redis_conn if REDIS_AVAILABLE else None
        self._custom_metrics: Dict[str, float] = {}

    def _get_metric_key(self, name: str, timestamp: Optional[datetime] = None) -> str:
        """Get Redis key for metric storage."""
        ts = timestamp or datetime.now()
        return f"cs:metrics:{name}:{ts.strftime('%Y%m%d%H%M')}"

    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric value."""
        if labels is None:
            labels = {}

        metric = MetricValue(name, value, datetime.now(), labels)

        # Store in Redis for historical data
        if REDIS_AVAILABLE and self.redis:
            try:
                key = self._get_metric_key(name)
                # Use a sorted set for time-series data
                ts_key = f"cs:timeseries:{name}"
                self.redis.zadd(ts_key, {json.dumps({
                    'value': value,
                    'timestamp': metric.timestamp.isoformat(),
                    'labels': labels
                }): metric.timestamp.timestamp()})

                # Keep only last 1000 data points per metric
                self.redis.zremrangebyrank(ts_key, 0, -1001)

            except Exception as e:
                logger.warning(f"Failed to store metric {name}: {e}")

        # Store in memory for quick access
        self._custom_metrics[name] = value

    def get_metric(self, name: str) -> Optional[float]:
        """Get latest metric value."""
        return self._custom_metrics.get(name)

    def collect_system_metrics(self):
        """Collect system-level metrics."""
        if not PSUTIL_AVAILABLE or not psutil:
            logger.warning("psutil not available, skipping system metrics collection")
            return

        try:
            # CPU metrics
            self.record_metric("cpu_usage_percent", psutil.cpu_percent(interval=1))
            self.record_metric("cpu_count", psutil.cpu_count())

            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_metric("memory_usage_percent", memory.percent)
            self.record_metric("memory_used_gb", memory.used / (1024**3))
            self.record_metric("memory_available_gb", memory.available / (1024**3))

            # Disk metrics
            disk = psutil.disk_usage('/')
            self.record_metric("disk_usage_percent", disk.percent)
            self.record_metric("disk_free_gb", disk.free / (1024**3))

            # Network metrics (basic)
            network = psutil.net_io_counters()
            if network:
                self.record_metric("network_bytes_sent", network.bytes_sent)
                self.record_metric("network_bytes_recv", network.bytes_recv)

        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")

    def collect_application_metrics(self, redis_conn = None):
        """Collect application-specific metrics."""
        try:
            if REDIS_AVAILABLE and redis_conn:
                # Job queue metrics
                try:
                    short_queue_len = redis_conn.llen("cs:queue:short") or 0
                    long_queue_len = redis_conn.llen("cs:queue:long") or 0
                    self.record_metric("queue_short_length", short_queue_len)
                    self.record_metric("queue_long_length", long_queue_len)
                    self.record_metric("queue_total_length", short_queue_len + long_queue_len)
                except:
                    pass

                # Active jobs
                try:
                    pattern = "cs:job:*"
                    active_jobs = 0
                    for key in redis_conn.scan_iter(pattern):
                        try:
                            state = redis_conn.hget(key, "state")
                            if state and state.decode() == "PROCESSING":
                                active_jobs += 1
                        except:
                            pass
                    self.record_metric("active_jobs", active_jobs)
                except:
                    pass

                # Error rates
                try:
                    failed_jobs = len(redis_conn.keys("cs:job:*") or [])
                    total_jobs = failed_jobs  # Simplified
                    if total_jobs > 0:
                        error_rate = (failed_jobs / total_jobs) * 100
                        self.record_metric("job_error_rate_percent", error_rate)
                except:
                    pass

        except Exception as e:
            logger.warning(f"Failed to collect application metrics: {e}")

    def get_timeseries_data(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical timeseries data for a metric."""
        if not REDIS_AVAILABLE or not self.redis:
            return []

        try:
            ts_key = f"cs:timeseries:{metric_name}"
            cutoff = (datetime.now() - timedelta(hours=hours)).timestamp()

            # Get data points within time range
            data = self.redis.zrangebyscore(ts_key, cutoff, '+inf', withscores=True)

            result = []
            for item, score in data:
                try:
                    point = json.loads(item.decode())
                    point['timestamp'] = datetime.fromtimestamp(score)
                    result.append(point)
                except:
                    pass

            return result
        except Exception as e:
            logger.warning(f"Failed to get timeseries data for {metric_name}: {e}")
            return []


class AlertManager:
    """Manages alerts based on metric thresholds."""

    def __init__(self, redis_conn = None):
        self.redis = redis_conn if REDIS_AVAILABLE else None
        self._alert_rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}

    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self._alert_rules[rule.name] = rule

    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule."""
        self._alert_rules.pop(rule_name, None)

    def check_alerts(self, metrics: MetricsCollector) -> List[Alert]:
        """Check all alert rules and return triggered alerts."""
        triggered_alerts = []

        for rule in self._alert_rules.values():
            try:
                # Evaluate condition
                if self._evaluate_condition(rule.condition, metrics):
                    alert_key = f"{rule.name}_{datetime.now().strftime('%Y%m%d%H%M')}"

                    # Check if alert is already active and in cooldown
                    if alert_key in self._active_alerts:
                        existing_alert = self._active_alerts[alert_key]
                        if (datetime.now() - existing_alert.timestamp).seconds < rule.cooldown:
                            continue

                    # Get current value
                    metric_name = rule.condition.split()[0]  # Simple parsing
                    current_value = metrics.get_metric(metric_name) or 0

                    # Create alert
                    alert = Alert(
                        rule_name=rule.name,
                        message=f"{rule.name}: {rule.condition} (current: {current_value:.2f})",
                        severity=rule.severity,
                        timestamp=datetime.now(),
                        value=current_value,
                        threshold=rule.threshold
                    )

                    triggered_alerts.append(alert)
                    self._active_alerts[alert_key] = alert

                    # Store in Redis
                    if REDIS_AVAILABLE and self.redis:
                        alert_data = {
                            'rule_name': alert.rule_name,
                            'message': alert.message,
                            'severity': alert.severity,
                            'timestamp': alert.timestamp.isoformat(),
                            'value': alert.value,
                            'threshold': alert.threshold
                        }
                        self.redis.set(f"cs:alert:{alert_key}", json.dumps(alert_data), ex=3600)

            except Exception as e:
                logger.warning(f"Failed to check alert rule {rule.name}: {e}")

        return triggered_alerts

    def _evaluate_condition(self, condition: str, metrics: MetricsCollector) -> bool:
        """Evaluate a simple alert condition."""
        try:
            # Simple condition parsing: "metric_name > threshold"
            parts = condition.split()
            if len(parts) != 3:
                return False

            metric_name, operator, threshold_str = parts
            threshold = float(threshold_str)
            current_value = metrics.get_metric(metric_name) or 0

            if operator == ">":
                return current_value > threshold
            elif operator == "<":
                return current_value < threshold
            elif operator == ">=":
                return current_value >= threshold
            elif operator == "<=":
                return current_value <= threshold
            elif operator == "==":
                return current_value == threshold

        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")

        return False

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        alerts = []

        if REDIS_AVAILABLE and self.redis:
            try:
                pattern = "cs:alert:*"
                keys = self.redis.keys(pattern) or []
                for key in keys:
                    try:
                        data = self.redis.get(key)
                        if data:
                            alerts.append(json.loads(data.decode()))
                    except:
                        pass
            except:
                pass

        # Add in-memory alerts
        for alert in self._active_alerts.values():
            alert_dict = {
                'rule_name': alert.rule_name,
                'message': alert.message,
                'severity': alert.severity,
                'timestamp': alert.timestamp.isoformat(),
                'value': alert.value,
                'threshold': alert.threshold
            }
            if alert_dict not in alerts:
                alerts.append(alert_dict)

        return alerts


class HealthChecker:
    """Performs comprehensive health checks."""

    def __init__(self, redis_conn = None):
        self.redis = redis_conn if REDIS_AVAILABLE else None
        self._health_checks: Dict[str, Callable[[], bool]] = {}

    def add_health_check(self, name: str, check_func: Callable[[], bool]):
        """Add a custom health check."""
        self._health_checks[name] = check_func

    def perform_health_check(self) -> Dict[str, Any]:
        """Perform all health checks."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }

        # Built-in checks
        checks = {
            "redis": self._check_redis,
            "disk_space": self._check_disk_space,
            "memory": self._check_memory,
            "cpu": self._check_cpu,
        }

        # Add custom checks
        checks.update(self._health_checks)

        for check_name, check_func in checks.items():
            try:
                status = check_func()
                results["checks"][check_name] = {
                    "status": "healthy" if status else "unhealthy",
                    "timestamp": datetime.now().isoformat()
                }
                if not status:
                    results["overall_status"] = "unhealthy"
            except Exception as e:
                results["checks"][check_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results["overall_status"] = "unhealthy"

        return results

    def _check_redis(self) -> bool:
        """Check Redis connectivity."""
        if not REDIS_AVAILABLE or not self.redis:
            return False
        try:
            return self.redis.ping()
        except:
            return False

    def _check_disk_space(self) -> bool:
        """Check available disk space."""
        if not PSUTIL_AVAILABLE or not psutil:
            return True  # Assume healthy if psutil not available

        try:
            disk = psutil.disk_usage('/')
            return disk.percent < 90  # Less than 90% usage
        except:
            return False

    def _check_memory(self) -> bool:
        """Check memory usage."""
        if not PSUTIL_AVAILABLE or not psutil:
            return True  # Assume healthy if psutil not available

        try:
            memory = psutil.virtual_memory()
            return memory.percent < 95  # Less than 95% usage
        except:
            return False

    def _check_cpu(self) -> bool:
        """Check CPU usage."""
        if not PSUTIL_AVAILABLE or not psutil:
            return True  # Assume healthy if psutil not available

        try:
            return psutil.cpu_percent(interval=1) < 95  # Less than 95% usage
        except:
            return False


# Default instances
metrics_collector: Optional[MetricsCollector] = None
alert_manager: Optional[AlertManager] = None
health_checker: Optional[HealthChecker] = None


def get_metrics_collector(redis_conn = None) -> MetricsCollector:
    """Get or create metrics collector instance."""
    global metrics_collector
    if metrics_collector is None:
        metrics_collector = MetricsCollector(redis_conn)
    return metrics_collector


def get_alert_manager(redis_conn = None) -> AlertManager:
    """Get or create alert manager instance."""
    global alert_manager
    if alert_manager is None:
        alert_manager = AlertManager(redis_conn)
    return alert_manager


def get_health_checker(redis_conn = None) -> HealthChecker:
    """Get or create health checker instance."""
    global health_checker
    if health_checker is None:
        health_checker = HealthChecker(redis_conn)
    return health_checker


def setup_default_alerts(alert_manager: AlertManager):
    """Setup default alert rules."""
    default_rules = [
        AlertRule("high_cpu", "cpu_usage_percent > 90", 90, 300, "warning", 3600),
        AlertRule("high_memory", "memory_usage_percent > 95", 95, 300, "error", 1800),
        AlertRule("low_disk_space", "disk_usage_percent > 85", 85, 300, "warning", 3600),
        AlertRule("queue_backlog", "queue_total_length > 50", 50, 300, "warning", 1800),
        AlertRule("high_error_rate", "job_error_rate_percent > 20", 20, 600, "error", 3600),
    ]

    for rule in default_rules:
        alert_manager.add_alert_rule(rule)
