#!/usr/bin/env python3
"""
ClipScribe Google Cloud Project Setup Script
Sets up a new GCP project for ClipScribe deployment.
"""

import subprocess
import json
import time
from pathlib import Path
import argparse
import sys


class GCPProjectSetup:
    def __init__(self, project_name: str, billing_account: str = None):
        self.project_name = project_name
        self.project_id = f"clipscribe-{project_name.lower().replace('_', '-')}"
        self.billing_account = billing_account
        self.region = "us-central1"

    def run_command(self, command: list, check: bool = True) -> subprocess.CompletedProcess:
        """Run a gcloud command with error handling."""
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

    def authenticate(self):
        """Authenticate with Google Cloud."""
        print("🔐 Authenticating with Google Cloud...")
        try:
            self.run_command(["auth", "login"])
        except:
            print("Please run: gcloud auth login")
            sys.exit(1)

    def create_project(self):
        """Create new GCP project."""
        print(f"🏗️ Creating project: {self.project_id}")

        # Create project
        self.run_command([
            "projects", "create", self.project_id,
            "--name", f"ClipScribe {self.project_name}",
            "--set-as-default"
        ])

        print(f"✅ Project created: {self.project_id}")

    def setup_billing(self):
        """Set up billing for the project."""
        if not self.billing_account:
            print("⚠️  No billing account specified. Please run:")
            print(f"gcloud billing accounts list")
            print(f"gcloud billing projects link {self.project_id} --billing-account=YOUR_BILLING_ACCOUNT")
            return

        print("💳 Setting up billing...")
        self.run_command([
            "billing", "projects", "link", self.project_id,
            "--billing-account", self.billing_account
        ])
        print("✅ Billing configured")

    def enable_apis(self):
        """Enable required Google Cloud APIs."""
        print("🔌 Enabling required APIs...")

        apis = [
            "cloudbuild.googleapis.com",
            "run.googleapis.com",
            "aiplatform.googleapis.com",
            "storage.googleapis.com",
            "translate.googleapis.com",
            "redis.googleapis.com",
            "cloudresourcemanager.googleapis.com"
        ]

        for api in apis:
            try:
                self.run_command(["services", "enable", api])
                print(f"✅ Enabled {api}")
            except:
                print(f"⚠️  Could not enable {api}")

    def create_service_account(self):
        """Create service account with necessary permissions."""
        print("👤 Creating service account...")

        sa_name = "clipscribe-sa"
        sa_email = f"{sa_name}@{self.project_id}.iam.gserviceaccount.com"

        # Create service account
        self.run_command([
            "iam", "service-accounts", "create", sa_name,
            "--description", "ClipScribe production service account",
            "--display-name", "ClipScribe Service Account"
        ])

        # Grant roles
        roles = [
            "roles/cloudtranslate.user",
            "roles/storage.admin",
            "roles/aiplatform.user",
            "roles/redis.editor",
            "roles/iam.serviceAccountUser"
        ]

        for role in roles:
            self.run_command([
                "projects", "add-iam-policy-binding", self.project_id,
                "--member", f"serviceAccount:{sa_email}",
                "--role", role
            ])

        # Create and download key
        key_file = f"clipscribe-{self.project_name}-key.json"
        self.run_command([
            "iam", "service-accounts", "keys", "create", key_file,
            "--iam-account", sa_email
        ])

        print(f"✅ Service account created: {sa_email}")
        print(f"🔑 Key saved to: {key_file}")

        return key_file

    def create_storage_bucket(self):
        """Create GCS bucket for file storage."""
        print("🪣 Creating storage bucket...")

        bucket_name = f"{self.project_id}-storage"

        self.run_command([
            "storage", "buckets", "create",
            f"gs://{bucket_name}",
            "--location", self.region,
            "--uniform-bucket-level-access"
        ])

        print(f"✅ Bucket created: gs://{bucket_name}")
        return bucket_name

    def create_redis_instance(self):
        """Create Redis instance."""
        print("🗄️ Creating Redis instance...")

        instance_name = "clipscribe-redis"

        self.run_command([
            "redis", "instances", "create", instance_name,
            "--size", "1",
            "--region", self.region,
            "--redis-version", "redis_7",
            "--tier", "basic"
        ])

        print(f"✅ Redis instance created: {instance_name}")
        return instance_name

    def setup_environment_file(self, key_file: str, bucket_name: str, redis_host: str):
        """Create environment configuration file."""
        print("📝 Creating environment configuration...")

        env_content = f"""# ClipScribe Production Environment
GOOGLE_API_KEY=your_api_key_here
VERTEX_AI_PROJECT={self.project_id}
GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/service-account.json
GCS_BUCKET={bucket_name}

# Redis Configuration
REDIS_URL=redis://{redis_host}:6379

# Application Configuration
CLIPSCRIBE_LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
PYTHONPATH=/app/src

# API Configuration
WORKER_TIMEOUT=3600
MAX_WORKERS=4

# Web Configuration
PORT=8080

# Security
SECRET_KEY=your_secret_key_here
"""

        with open(".env.production", "w") as f:
            f.write(env_content)

        print("✅ Environment file created: .env.production")
        print("⚠️  Please:")
        print("   1. Get your Gemini API key from https://makersuite.google.com/app/apikey")
        print("   2. Generate a secure SECRET_KEY")
        print("   3. Update GOOGLE_API_KEY and SECRET_KEY in .env.production")

    def get_redis_host(self, instance_name: str):
        """Get Redis instance host."""
        result = self.run_command([
            "redis", "instances", "describe", instance_name,
            "--region", self.region,
            "--format", "value(host)"
        ])
        return result.stdout.strip()

    def run_setup(self):
        """Run complete GCP project setup."""
        print(f"🚀 Setting up ClipScribe GCP Project: {self.project_id}")
        print("=" * 60)

        steps = [
            ("Authenticating", self.authenticate),
            ("Creating project", self.create_project),
            ("Setting up billing", self.setup_billing),
            ("Enabling APIs", self.enable_apis),
        ]

        for step_name, step_func in steps:
            try:
                print(f"\n🔧 {step_name}...")
                step_func()
            except Exception as e:
                print(f"❌ {step_name} failed: {e}")
                if input("Continue with remaining steps? (yes/no): ").lower() != "yes":
                    return

        # Continue with resource creation
        try:
            print("
👤 Creating service account..."            key_file = self.create_service_account()

            print("
🪣 Creating storage bucket..."            bucket_name = self.create_storage_bucket()

            print("
🗄️ Creating Redis instance..."            redis_instance = self.create_redis_instance()

            # Wait for Redis to be ready
            print("⏳ Waiting for Redis instance to be ready...")
            time.sleep(60)

            redis_host = self.get_redis_host(redis_instance)

            print("
📝 Setting up environment..."            self.setup_environment_file(key_file, bucket_name, redis_host)

            print("
🎉 GCP Project setup completed!"            print(f"Project ID: {self.project_id}")
            print("Next steps:"
            print("1. Update .env.production with your API keys"
            print("2. Move the service account key to a secure location"
            print("3. Run: ./scripts/setup_staging.py --project-id", self.project_id

        except Exception as e:
            print(f"❌ Resource creation failed: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ClipScribe GCP Project Setup")
    parser.add_argument("--project-name", required=True, help="Project name (e.g., 'production')")
    parser.add_argument("--billing-account", help="Billing account ID")

    args = parser.parse_args()

    setup = GCPProjectSetup(args.project_name, args.billing_account)
    setup.run_setup()


if __name__ == "__main__":
    main()
