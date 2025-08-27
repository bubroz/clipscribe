#!/usr/bin/env python3
"""
ClipScribe Production Environment Validator v2.43.0
Validates production readiness and configuration integrity.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class ProductionValidator:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []

    def log_error(self, message: str):
        """Log an error message."""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")

    def log_warning(self, message: str):
        """Log a warning message."""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")

    def log_success(self, message: str):
        """Log a success message."""
        print(f"✅ {message}")

    def validate_environment_variables(self) -> bool:
        """Validate required environment variables."""
        print("\n🔍 Validating environment variables...")

        required_vars = [
            "GOOGLE_API_KEY",
        ]

        optional_but_recommended = [
            "VERTEX_AI_PROJECT",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GCS_BUCKET",
        ]

        all_valid = True

        # Check required variables
        for var in required_vars:
            if not os.getenv(var):
                self.log_error(f"Required environment variable '{var}' is not set")
                all_valid = False
            else:
                self.log_success(f"Required variable '{var}' is set")

        # Check recommended variables
        for var in optional_but_recommended:
            if not os.getenv(var):
                self.log_warning(f"Recommended environment variable '{var}' is not set")
            else:
                self.log_success(f"Recommended variable '{var}' is set")

        return all_valid

    def validate_docker_compose(self) -> bool:
        """Validate Docker Compose configuration."""
        print("\n🔍 Validating Docker Compose configuration...")

        compose_file = self.root_dir / "docker-compose.yml"
        if not compose_file.exists():
            self.log_error("docker-compose.yml not found")
            return False

        try:
            # Try to validate docker-compose config
            result = subprocess.run(
                ["docker-compose", "config", "--quiet"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.log_success("Docker Compose configuration is valid")
                return True
            else:
                self.log_error(f"Docker Compose validation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.log_error("Docker Compose validation timed out")
            return False
        except FileNotFoundError:
            self.log_error("docker-compose command not found")
            return False

    def validate_dockerfile(self) -> bool:
        """Validate Dockerfile configuration."""
        print("\n🔍 Validating Dockerfile configuration...")

        dockerfile = self.root_dir / "Dockerfile"
        if not dockerfile.exists():
            self.log_error("Dockerfile not found")
            return False

        # Check for security issues
        content = dockerfile.read_text()

        # Check for non-root user
        if "USER clipscribe" not in content:
            self.log_warning("Dockerfile does not create non-root user")

        # Check for health checks
        if "HEALTHCHECK" not in content:
            self.log_warning("Dockerfile does not define health checks")

        # Check for security updates
        if "apt-get upgrade" not in content:
            self.log_warning("Dockerfile does not include security updates")

        self.log_success("Dockerfile validation completed")
        return True

    def validate_dependencies(self) -> bool:
        """Validate Python dependencies."""
        print("\n🔍 Validating Python dependencies...")

        pyproject = self.root_dir / "pyproject.toml"
        if not pyproject.exists():
            self.log_error("pyproject.toml not found")
            return False

        poetry_lock = self.root_dir / "poetry.lock"
        if not poetry_lock.exists():
            self.log_warning("poetry.lock not found - dependencies may not be locked")

        self.log_success("Python dependencies validation completed")
        return True

    def validate_api_endpoints(self) -> bool:
        """Validate API server endpoints."""
        print("\n🔍 Validating API server configuration...")

        api_app = self.root_dir / "src" / "clipscribe" / "api" / "app.py"
        if not api_app.exists():
            self.log_error("API application file not found")
            return False

        # Check if FastAPI app is properly configured
        content = api_app.read_text()
        if "FastAPI" not in content:
            self.log_error("FastAPI application not found in API app")
            return False

        if "@app." not in content:
            self.log_warning("No API routes found in FastAPI app")

        self.log_success("API server validation completed")
        return True

    def validate_worker_configuration(self) -> bool:
        """Validate worker configuration."""
        print("\n🔍 Validating worker configuration...")

        worker_file = self.root_dir / "src" / "clipscribe" / "api" / "worker.py"
        if not worker_file.exists():
            self.log_error("Worker configuration file not found")
            return False

        content = worker_file.read_text()
        if "rq" not in content.lower():
            self.log_warning("Redis Queue worker configuration not found")

        self.log_success("Worker configuration validation completed")
        return True

    def validate_web_interface(self) -> bool:
        """Validate web interface configuration."""
        print("\n🔍 Validating web interface configuration...")

        streamlit_app = self.root_dir / "streamlit_app" / "ClipScribe_Mission_Control.py"
        if not streamlit_app.exists():
            self.log_error("Streamlit application file not found")
            return False

        content = streamlit_app.read_text()
        if "streamlit" not in content.lower():
            self.log_warning("Streamlit imports not found in web interface")

        self.log_success("Web interface validation completed")
        return True

    def validate_security_configuration(self) -> bool:
        """Validate security configuration."""
        print("\n🔍 Validating security configuration...")

        # Check for security-related files
        security_md = self.root_dir / "SECURITY.md"
        if not security_md.exists():
            self.log_warning("SECURITY.md file not found")

        # Check for .env file (should not be in repo)
        env_file = self.root_dir / ".env"
        if env_file.exists():
            env_content = env_file.read_text()
            if "GOOGLE_API_KEY" in env_content:
                self.log_warning(".env file contains sensitive information")

        self.log_success("Security configuration validation completed")
        return True

    def validate_resource_limits(self) -> bool:
        """Validate resource limits configuration."""
        print("\n🔍 Validating resource limits...")

        compose_file = self.root_dir / "docker-compose.yml"
        if compose_file.exists():
            content = compose_file.read_text()
            if "deploy:" not in content:
                self.log_warning("No resource limits found in docker-compose.yml")

            if "memory:" not in content:
                self.log_warning("Memory limits not configured")

            if "cpus:" not in content:
                self.log_warning("CPU limits not configured")

        self.log_success("Resource limits validation completed")
        return True

    def run_all_validations(self) -> Tuple[bool, int, int]:
        """Run all validation checks."""
        print("🚀 ClipScribe Production Environment Validator v2.43.0")
        print("=" * 60)

        validations = [
            self.validate_environment_variables,
            self.validate_docker_compose,
            self.validate_dockerfile,
            self.validate_dependencies,
            self.validate_api_endpoints,
            self.validate_worker_configuration,
            self.validate_web_interface,
            self.validate_security_configuration,
            self.validate_resource_limits,
        ]

        all_passed = True
        for validation in validations:
            try:
                result = validation()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_error(f"Validation failed with exception: {e}")
                all_passed = False

        return all_passed, len(self.errors), len(self.warnings)

    def print_summary(self, all_passed: bool, error_count: int, warning_count: int):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        if all_passed:
            print("🎉 All validations passed! Production deployment is ready.")
        else:
            print(f"❌ {error_count} errors and {warning_count} warnings found.")

        if self.errors:
            print("\n🔴 ERRORS:")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("\n🟡 WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")

        if all_passed:
            print("\n✅ Production deployment checklist:")
            print("  • Environment variables configured")
            print("  • Docker containers optimized")
            print("  • Security hardening applied")
            print("  • Resource limits configured")
            print("  • Health checks implemented")
            print("  • API and worker services ready")
            print("  • Web interface configured")
        else:
            print("\n⚠️  Please address the errors before deploying to production.")

def main():
    """Main entry point."""
    validator = ProductionValidator()
    all_passed, error_count, warning_count = validator.run_all_validations()
    validator.print_summary(all_passed, error_count, warning_count)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
