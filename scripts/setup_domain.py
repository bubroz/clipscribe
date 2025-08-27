#!/usr/bin/env python3
"""
ClipScribe Domain Setup Script
Sets up Cloudflare DNS and SSL for ClipScribe deployment.
"""

import subprocess
import json
import time
from pathlib import Path
import argparse
import sys


class DomainSetup:
    def __init__(self, domain: str, api_token: str):
        self.domain = domain
        self.api_token = api_token
        self.cloudflare_api = "https://api.cloudflare.com/client/v4"

    def run_command(self, command: list, check: bool = True) -> subprocess.CompletedProcess:
        """Run a command with error handling."""
        try:
            result = subprocess.run(
                command,
                check=check,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result
        except subprocess.TimeoutExpired:
            print(f"❌ Command timed out: {' '.join(command)}")
            raise
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(command)}")
            print(f"Error: {e.stderr}")
            raise

    def get_zone_id(self):
        """Get Cloudflare zone ID for the domain."""
        print(f"🔍 Getting zone ID for {self.domain}...")

        # Use curl to make API request
        result = self.run_command([
            "curl", "-X", "GET",
            f"{self.cloudflare_api}/zones?name={self.domain}",
            "-H", f"Authorization: Bearer {self.api_token}",
            "-H", "Content-Type: application/json"
        ])

        response = json.loads(result.stdout)

        if not response["success"]:
            print(f"❌ Failed to get zone ID: {response['errors']}")
            sys.exit(1)

        zones = response["result"]
        if not zones:
            print(f"❌ Domain {self.domain} not found in Cloudflare")
            sys.exit(1)

        zone_id = zones[0]["id"]
        print(f"✅ Zone ID: {zone_id}")
        return zone_id

    def create_dns_records(self, zone_id: str, cname_target: str):
        """Create DNS records for the domain."""
        print("📝 Creating DNS records...")

        records = [
            {
                "type": "CNAME",
                "name": "api",
                "content": cname_target,
                "ttl": 300,
                "proxied": True
            },
            {
                "type": "CNAME",
                "name": "app",
                "content": cname_target,
                "ttl": 300,
                "proxied": True
            },
            {
                "type": "CNAME",
                "name": "www",
                "content": cname_target,
                "ttl": 300,
                "proxied": True
            }
        ]

        for record in records:
            record_data = json.dumps({
                "type": record["type"],
                "name": f"{record['name']}.{self.domain}",
                "content": record["content"],
                "ttl": record["ttl"],
                "proxied": record["proxied"]
            })

            result = self.run_command([
                "curl", "-X", "POST",
                f"{self.cloudflare_api}/zones/{zone_id}/dns_records",
                "-H", f"Authorization: Bearer {self.api_token}",
                "-H", "Content-Type: application/json",
                "-d", record_data
            ])

            response = json.loads(result.stdout)

            if response["success"]:
                record_id = response["result"]["id"]
                print(f"✅ Created {record['type']} record: {record['name']}.{self.domain} -> {record['content']}")
            else:
                print(f"⚠️  Failed to create {record['type']} record: {response['errors']}")

    def setup_ssl(self, zone_id: str):
        """Set up SSL/TLS encryption."""
        print("🔒 Setting up SSL/TLS...")

        # Enable SSL
        ssl_data = json.dumps({
            "value": "strict"
        })

        result = self.run_command([
            "curl", "-X", "PATCH",
            f"{self.cloudflare_api}/zones/{zone_id}/settings/ssl",
            "-H", f"Authorization: Bearer {self.api_token}",
            "-H", "Content-Type: application/json",
            "-d", ssl_data
        ])

        response = json.loads(result.stdout)

        if response["success"]:
            print("✅ SSL enabled with strict mode")
        else:
            print(f"⚠️  Failed to enable SSL: {response['errors']}")

        # Enable Always Use HTTPS
        https_data = json.dumps({
            "value": "on"
        })

        result = self.run_command([
            "curl", "-X", "PATCH",
            f"{self.cloudflare_api}/zones/{zone_id}/settings/always_use_https",
            "-H", f"Authorization: Bearer {self.api_token}",
            "-H", "Content-Type: application/json",
            "-d", https_data
        ])

        response = json.loads(result.stdout)

        if response["success"]:
            print("✅ Always Use HTTPS enabled")
        else:
            print(f"⚠️  Failed to enable Always Use HTTPS: {response['errors']}")

    def setup_caching(self, zone_id: str):
        """Set up caching rules."""
        print("💾 Setting up caching rules...")

        # Create cache rule for API responses
        cache_rule = json.dumps({
            "description": "Cache API responses for 5 minutes",
            "expression": "(http.request.uri.path matches \"^/v1/estimate\")",
            "action": "rewrite",
            "action_parameters": {
                "rules": {
                    "cache": True,
                    "edge_ttl": {
                        "mode": "override_origin",
                        "duration": 300
                    }
                }
            }
        })

        result = self.run_command([
            "curl", "-X", "POST",
            f"{self.cloudflare_api}/zones/{zone_id}/rulesets",
            "-H", f"Authorization: Bearer {self.api_token}",
            "-H", "Content-Type: application/json",
            "-d", cache_rule
        ])

        response = json.loads(result.stdout)

        if response["success"]:
            print("✅ API caching rule created")
        else:
            print(f"⚠️  Failed to create cache rule: {response['errors']}")

    def setup_security(self, zone_id: str):
        """Set up security rules."""
        print("🛡️ Setting up security rules...")

        # Enable Under Attack Mode for extra protection
        security_data = json.dumps({
            "value": "off"  # Set to "on" if under attack
        })

        result = self.run_command([
            "curl", "-X", "PATCH",
            f"{self.cloudflare_api}/zones/{zone_id}/settings/security_level",
            "-H", f"Authorization: Bearer {self.api_token}",
            "-H", "Content-Type: application/json",
            "-d", security_data
        ])

        response = json.loads(result.stdout)

        if response["success"]:
            print("✅ Security level configured")
        else:
            print(f"⚠️  Failed to configure security: {response['errors']}")

    def run_setup(self, cname_target: str):
        """Run complete domain setup."""
        print(f"🚀 Setting up domain: {self.domain}")
        print("=" * 60)

        try:
            zone_id = self.get_zone_id()
            self.create_dns_records(zone_id, cname_target)
            self.setup_ssl(zone_id)
            self.setup_caching(zone_id)
            self.setup_security(zone_id)

            print("
🎉 Domain setup completed!"            print(f"Domain: {self.domain}")
            print(f"API: https://api.{self.domain}")
            print(f"App: https://app.{self.domain}")
            print(f"Main: https://{self.domain}")
            print("
⚠️  DNS changes may take up to 24 hours to propagate"            print(f"🔍 Check propagation: https://dns.google/query?name={self.domain}"

        except Exception as e:
            print(f"❌ Domain setup failed: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ClipScribe Domain Setup")
    parser.add_argument("--domain", required=True, help="Domain name (e.g., clipscribe.ai)")
    parser.add_argument("--api-token", required=True, help="Cloudflare API token")
    parser.add_argument("--cname-target", required=True, help="CNAME target (e.g., your-project.region.r.appspot.com)")

    args = parser.parse_args()

    setup = DomainSetup(args.domain, args.api_token)
    setup.run_setup(args.cname_target)


if __name__ == "__main__":
    main()
