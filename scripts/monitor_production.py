#!/usr/bin/env python3
"""
ClipScribe Production Monitoring Script v2.43.0
Monitors production services and provides health metrics.
"""

import asyncio
import time
import json
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionMonitor:
    def __init__(self):
        self.base_url = "http://localhost"
        self.api_port = 8000
        self.web_port = 8080
        self.redis_port = 6379
        self.check_interval = 30  # seconds
        self.alert_threshold = 3  # consecutive failures before alert

    async def check_api_health(self) -> Dict[str, Any]:
        """Check API server health."""
        try:
            # Check main API endpoint
            response = requests.get(f"{self.base_url}:{self.api_port}/docs", timeout=5)
            api_status = response.status_code == 200

            # Check API metrics endpoint (if available)
            metrics_status = False
            try:
                response = requests.get(f"{self.base_url}:{self.api_port}/v1/metrics", timeout=5)
                metrics_status = response.status_code == 200
            except:
                pass

            return {
                "service": "api",
                "healthy": api_status,
                "metrics_available": metrics_status,
                "response_time": response.elapsed.total_seconds() if api_status else None,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "service": "api",
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def check_web_health(self) -> Dict[str, Any]:
        """Check web interface health."""
        try:
            response = requests.get(f"{self.base_url}:{self.web_port}/_stcore/health", timeout=10)
            healthy = response.status_code == 200

            return {
                "service": "web",
                "healthy": healthy,
                "response_time": response.elapsed.total_seconds() if healthy else None,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "service": "web",
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            import redis
            r = redis.Redis(host='localhost', port=self.redis_port, decode_responses=True)
            pong = r.ping()

            # Get Redis stats
            info = r.info()
            memory_used = info.get('used_memory_human', 'N/A')
            connected_clients = info.get('connected_clients', 0)

            return {
                "service": "redis",
                "healthy": pong,
                "memory_used": memory_used,
                "connected_clients": connected_clients,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "service": "redis",
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used // (1024 * 1024)  # MB
            memory_total = memory.total // (1024 * 1024)  # MB

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free // (1024 * 1024 * 1024)  # GB

            return {
                "service": "system",
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_used_mb": memory_used,
                "memory_total_mb": memory_total,
                "disk_percent": disk_percent,
                "disk_free_gb": disk_free,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "service": "system",
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def check_docker_containers(self) -> Dict[str, Any]:
        """Check Docker container status."""
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
                clipscribe_containers = [c for c in containers if 'clipscribe' in c.get('Names', '')]

                return {
                    "service": "docker",
                    "healthy": True,
                    "running_containers": len(clipscribe_containers),
                    "containers": [{"name": c.get("Names"), "status": c.get("Status")} for c in clipscribe_containers],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "service": "docker",
                    "healthy": False,
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "service": "docker",
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        logger.info("Running production health check...")

        # Run all checks concurrently
        api_health, web_health, redis_health = await asyncio.gather(
            self.check_api_health(),
            self.check_web_health(),
            self.check_redis_health()
        )

        # Run system checks (synchronous)
        system_health = self.check_system_resources()
        docker_health = await self.check_docker_containers()

        # Compile results
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_healthy": all([
                api_health.get("healthy", False),
                web_health.get("healthy", False),
                redis_health.get("healthy", False),
                docker_health.get("healthy", False)
            ]),
            "services": {
                "api": api_health,
                "web": web_health,
                "redis": redis_health,
                "docker": docker_health,
                "system": system_health
            }
        }

        return results

    def print_health_report(self, results: Dict[str, Any]):
        """Print formatted health report."""
        print(f"\n🏥 ClipScribe Production Health Report - {results['timestamp']}")
        print("=" * 60)

        overall_status = "✅ HEALTHY" if results["overall_healthy"] else "❌ ISSUES DETECTED"
        print(f"Overall Status: {overall_status}")
        print()

        for service_name, service_data in results["services"].items():
            healthy = service_data.get("healthy", False)
            status_icon = "✅" if healthy else "❌"

            print(f"{status_icon} {service_name.upper()}")

            if not healthy:
                error = service_data.get("error", "Unknown error")
                print(f"   Error: {error}")

            # Service-specific metrics
            if service_name == "system":
                if healthy:
                    print(f"   CPU: {service_data.get('cpu_percent', 'N/A')}%")
                    print(f"   Memory: {service_data.get('memory_used_mb', 'N/A')}MB / {service_data.get('memory_total_mb', 'N/A')}MB")
                    print(f"   Disk: {service_data.get('disk_free_gb', 'N/A')}GB free")

            elif service_name == "api" and healthy:
                response_time = service_data.get("response_time")
                if response_time:
                    print(".3f"
            elif service_name == "web" and healthy:
                response_time = service_data.get("response_time")
                if response_time:
                    print(".3f"
            elif service_name == "redis" and healthy:
                memory = service_data.get("memory_used", "N/A")
                clients = service_data.get("connected_clients", "N/A")
                print(f"   Memory: {memory}")
                print(f"   Clients: {clients}")

            elif service_name == "docker" and healthy:
                containers = service_data.get("running_containers", 0)
                print(f"   Running: {containers} containers")

            print()

    def save_health_log(self, results: Dict[str, Any], log_file: Path):
        """Save health check results to log file."""
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Read existing logs if file exists
            existing_data = []
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        existing_data = json.load(f)
                except:
                    existing_data = []

            # Add new results
            existing_data.append(results)

            # Keep only last 100 entries
            if len(existing_data) > 100:
                existing_data = existing_data[-100:]

            # Save updated logs
            with open(log_file, 'w') as f:
                json.dump(existing_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save health log: {e}")

    async def monitor_loop(self, log_file: Path = None):
        """Run continuous monitoring loop."""
        logger.info("Starting production monitoring loop...")

        if log_file is None:
            log_file = Path("logs/health_monitor.json")

        consecutive_failures = 0

        while True:
            try:
                results = await self.run_health_check()
                self.print_health_report(results)

                if log_file:
                    self.save_health_log(results, log_file)

                # Reset consecutive failures on success
                if results["overall_healthy"]:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1

                # Alert if too many consecutive failures
                if consecutive_failures >= self.alert_threshold:
                    logger.error(f"🚨 ALERT: {consecutive_failures} consecutive health check failures!")
                    # Here you could send email alerts, Slack notifications, etc.

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

            await asyncio.sleep(self.check_interval)

async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ClipScribe Production Monitor")
    parser.add_argument("--once", action="store_true", help="Run single health check")
    parser.add_argument("--log-file", type=Path, default=Path("logs/health_monitor.json"), help="Health log file path")

    args = parser.parse_args()

    monitor = ProductionMonitor()

    if args.once:
        results = await monitor.run_health_check()
        monitor.print_health_report(results)
        if args.log_file:
            monitor.save_health_log(results, args.log_file)
    else:
        await monitor.monitor_loop(args.log_file)

if __name__ == "__main__":
    asyncio.run(main())
