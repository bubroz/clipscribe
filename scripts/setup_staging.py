#!/usr/bin/env python3
"""
ClipScribe Staging Environment Setup v2.43.0
Automated staging environment configuration and validation.
"""

import os
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import sys


class StagingEnvironment:
    def __init__(self, project_id: str, region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        self.services = ["clipscribe-cli-staging", "clipscribe-api-staging", "clipscribe-web-staging"]
        self.base_dir = Path(__file__).parent.parent

    def run_gcloud_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a gcloud command with proper error handling."""
        try:
            result = subprocess.run(
                ["gcloud"] + command,
                check=check,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result
        except subprocess.TimeoutExpired:
            print(f"❌ Command timed out: gcloud {' '.join(command)}")
            raise
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: gcloud {' '.join(command)}")
            print(f"Error: {e.stderr}")
            raise

    def authenticate_gcp(self):
        """Authenticate with Google Cloud Platform."""
        print("🔐 Authenticating with Google Cloud...")

        # Check if already authenticated
        try:
            self.run_gcloud_command(["auth", "list", "--filter=status:ACTIVE", "--format=value(account)"])
        except:
            print("Please authenticate with: gcloud auth login")
            sys.exit(1)

        # Set project
        self.run_gcloud_command(["config", "set", "project", self.project_id])
        print(f"✅ Authenticated and set project to {self.project_id}")

    def create_service_account(self):
        """Create service account for staging environment."""
        print("👤 Creating service account...")

        sa_name = "clipscribe-staging-sa"
        sa_email = f"{sa_name}@{self.project_id}.iam.gserviceaccount.com"

        try:
            # Create service account
            self.run_gcloud_command([
                "iam", "service-accounts", "create", sa_name,
                "--description", "ClipScribe staging service account",
                "--display-name", "ClipScribe Staging"
            ])

            # Grant necessary roles
            roles = [
                "roles/cloudtranslate.user",
                "roles/storage.objectAdmin",
                "roles/aiplatform.user"
            ]

            for role in roles:
                self.run_gcloud_command([
                    "projects", "add-iam-policy-binding", self.project_id,
                    "--member", f"serviceAccount:{sa_email}",
                    "--role", role
                ])

            print(f"✅ Service account created: {sa_email}")

        except subprocess.CalledProcessError:
            print(f"⚠️  Service account may already exist: {sa_email}")

    def create_gcs_bucket(self):
        """Create GCS bucket for staging."""
        print("🪣 Creating GCS bucket...")

        bucket_name = f"{self.project_id}-clipscribe-staging"

        try:
            self.run_gcloud_command([
                "storage", "buckets", "create",
                f"gs://{bucket_name}",
                "--location", "us-central1",
                "--uniform-bucket-level-access"
            ])

            # Set CORS policy for web interface
            cors_config = {
                "cors": [{
                    "origin": ["*"],
                    "method": ["GET", "POST", "PUT"],
                    "responseHeader": ["Content-Type", "Access-Control-Allow-Origin"],
                    "maxAgeSeconds": 3600
                }]
            }

            cors_file = self.base_dir / "cors.json"
            with open(cors_file, 'w') as f:
                json.dump(cors_config, f)

            self.run_gcloud_command([
                "storage", "buckets", "update", f"gs://{bucket_name}",
                "--cors-file", str(cors_file)
            ])

            print(f"✅ GCS bucket created: gs://{bucket_name}")

        except subprocess.CalledProcessError:
            print(f"⚠️  Bucket may already exist: gs://{bucket_name}")

    def enable_required_apis(self):
        """Enable required Google Cloud APIs."""
        print("🔌 Enabling required APIs...")

        apis = [
            "cloudbuild.googleapis.com",
            "run.googleapis.com",
            "aiplatform.googleapis.com",
            "storage.googleapis.com",
            "translate.googleapis.com"
        ]

        for api in apis:
            try:
                self.run_gcloud_command(["services", "enable", api])
                print(f"✅ Enabled {api}")
            except subprocess.CalledProcessError:
                print(f"⚠️  API may already be enabled: {api}")

    def create_redis_instance(self):
        """Create Redis instance for staging."""
        print("🗄️ Creating Redis instance...")

        instance_name = "clipscribe-staging-redis"

        try:
            self.run_gcloud_command([
                "redis", "instances", "create", instance_name,
                "--size", "1",
                "--region", self.region,
                "--redis-version", "redis_7"
            ])

            # Get Redis connection info
            result = self.run_gcloud_command([
                "redis", "instances", "describe", instance_name,
                "--region", self.region,
                "--format", "value(host)"
            ])

            redis_host = result.stdout.strip()
            print(f"✅ Redis instance created: {instance_name}")
            print(f"   Host: {redis_host}")

        except subprocess.CalledProcessError:
            print(f"⚠️  Redis instance may already exist: {instance_name}")

    def deploy_services(self):
        """Deploy services to staging."""
        print("🚀 Deploying services to staging...")

        # Build and deploy using Cloud Build
        try:
            self.run_gcloud_command([
                "builds", "submit",
                "--config", "cloudbuild.yaml",
                "--substitutions", f"_PROJECT_ID={self.project_id}"
            ])
            print("✅ Services deployed successfully")

        except subprocess.CalledProcessError:
            print("❌ Deployment failed")
            raise

    def configure_dns(self):
        """Configure DNS for staging domain."""
        print("🌐 Configuring DNS...")

        # This would typically involve setting up Cloud DNS
        # For now, just show the service URLs
        for service in self.services:
            try:
                result = self.run_gcloud_command([
                    "run", "services", "describe", service,
                    "--region", self.region,
                    "--format", "value(status.url)"
                ])
                url = result.stdout.strip()
                print(f"📍 {service}: {url}")
            except subprocess.CalledProcessError:
                print(f"⚠️  Could not get URL for {service}")

    def run_smoke_tests(self):
        """Run basic smoke tests on staging environment."""
        print("🧪 Running smoke tests...")

        for service in self.services:
            try:
                # Get service URL
                result = self.run_gcloud_command([
                    "run", "services", "describe", service,
                    "--region", self.region,
                    "--format", "value(status.url)"
                ])
                url = result.stdout.strip()

                if "api" in service:
                    # Test API health
                    response = subprocess.run([
                        "curl", "-f", "--max-time", "10", f"{url}/docs"
                    ], capture_output=True, timeout=15)

                    if response.returncode == 0:
                        print(f"✅ API health check passed for {service}")
                    else:
                        print(f"❌ API health check failed for {service}")

                elif "web" in service:
                    # Test web interface health
                    response = subprocess.run([
                        "curl", "-f", "--max-time", "10", f"{url}/_stcore/health"
                    ], capture_output=True, timeout=15)

                    if response.returncode == 0:
                        print(f"✅ Web health check passed for {service}")
                    else:
                        print(f"❌ Web health check failed for {service}")

                else:
                    print(f"ℹ️  Skipping health check for {service}")

            except subprocess.CalledProcessError:
                print(f"❌ Could not run health check for {service}")

    def generate_config_summary(self):
        """Generate configuration summary."""
        print("\n📋 Staging Environment Configuration Summary")
        print("=" * 60)

        summary = {
            "project_id": self.project_id,
            "region": self.region,
            "services": self.services,
            "apis_enabled": [
                "cloudbuild.googleapis.com",
                "run.googleapis.com",
                "aiplatform.googleapis.com",
                "storage.googleapis.com",
                "translate.googleapis.com"
            ],
            "infrastructure": {
                "redis": "clipscribe-staging-redis",
                "bucket": f"{self.project_id}-clipscribe-staging",
                "service_account": f"clipscribe-staging-sa@{self.project_id}.iam.gserviceaccount.com"
            }
        }

        print(json.dumps(summary, indent=2))

        # Save configuration
        config_file = self.base_dir / "staging-config.json"
        with open(config_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n💾 Configuration saved to {config_file}")

    def setup_monitoring(self):
        """Set up basic monitoring and alerting."""
        print("📊 Setting up monitoring...")

        # Create log sink for error monitoring
        try:
            self.run_gcloud_command([
                "logging", "sinks", "create", "clipscribe-staging-errors",
                "storage.googleapis.com/clipscribe-staging-errors",
                "--log-filter", "severity>=ERROR",
                "--description", "ClipScribe staging error logs"
            ])
            print("✅ Error log monitoring configured")

        except subprocess.CalledProcessError:
            print("⚠️  Error log monitoring may already be configured")

    def cleanup_resources(self):
        """Clean up staging resources (use with caution)."""
        print("🧹 Cleaning up staging resources...")

        if input("⚠️  This will delete all staging resources. Continue? (yes/no): ") != "yes":
            return

        # Delete services
        for service in self.services:
            try:
                self.run_gcloud_command([
                    "run", "services", "delete", service,
                    "--region", self.region,
                    "--quiet"
                ])
                print(f"✅ Deleted service: {service}")
            except:
                print(f"⚠️  Could not delete service: {service}")

        # Delete Redis instance
        try:
            self.run_gcloud_command([
                "redis", "instances", "delete", "clipscribe-staging-redis",
                "--region", self.region,
                "--quiet"
            ])
            print("✅ Deleted Redis instance")
        except:
            print("⚠️  Could not delete Redis instance")

        print("🧹 Cleanup completed")

    def run_full_setup(self):
        """Run complete staging environment setup."""
        print("🚀 ClipScribe Staging Environment Setup v2.43.0")
        print("=" * 60)

        steps = [
            ("Authenticating", self.authenticate_gcp),
            ("Enabling APIs", self.enable_required_apis),
            ("Creating service account", self.create_service_account),
            ("Creating GCS bucket", self.create_gcs_bucket),
            ("Creating Redis instance", self.create_redis_instance),
            ("Deploying services", self.deploy_services),
            ("Configuring monitoring", self.setup_monitoring),
            ("Running smoke tests", self.run_smoke_tests),
            ("Configuring DNS", self.configure_dns),
        ]

        for step_name, step_func in steps:
            try:
                print(f"\n🔧 {step_name}...")
                step_func()
            except Exception as e:
                print(f"❌ {step_name} failed: {e}")
                if input("Continue with remaining steps? (yes/no): ") != "yes":
                    break

        self.generate_config_summary()
        print("\n🎉 Staging environment setup completed!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ClipScribe Staging Environment Setup")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--region", default="us-central1", help="Google Cloud region")
    parser.add_argument("--cleanup", action="store_true", help="Clean up staging resources")
    parser.add_argument("--smoke-test", action="store_true", help="Run only smoke tests")

    args = parser.parse_args()

    staging = StagingEnvironment(args.project_id, args.region)

    if args.cleanup:
        staging.cleanup_resources()
    elif args.smoke_test:
        staging.authenticate_gcp()
        staging.run_smoke_tests()
    else:
        staging.run_full_setup()


if __name__ == "__main__":
    main()
