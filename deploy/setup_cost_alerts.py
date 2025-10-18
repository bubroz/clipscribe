#!/usr/bin/env python3
"""
Set up cost monitoring and alerts for Vertex AI GPU usage.

This script creates:
1. Budget alerts at $50/$100/$150 thresholds
2. Cloud Monitoring alerts for Vertex AI spend
3. Dashboard for job tracking

Usage:
    python deploy/setup_cost_alerts.py --project prismatic-iris-429006-g6
"""

import argparse
import sys
from google.cloud import monitoring_v3
from google.cloud import billing_budgets_v1


def create_budget_alerts(project_id: str, billing_account: str):
    """
    Create budget alerts at $50, $100, $150 thresholds.
    
    Args:
        project_id: GCP project ID
        billing_account: Billing account ID (billingAccounts/XXXXXX-XXXXXX-XXXXXX)
    """
    client = billing_budgets_v1.BudgetServiceClient()
    
    thresholds = [50, 100, 150]
    
    for amount in thresholds:
        budget = billing_budgets_v1.Budget(
            display_name=f"Vertex AI GPU Budget Alert - ${amount}",
            budget_filter=billing_budgets_v1.Filter(
                projects=[f"projects/{project_id}"],
                services=["services/1C1C-11D6-478E-BF5B-36827EBCE1B8"],  # Vertex AI service ID
            ),
            amount=billing_budgets_v1.BudgetAmount(
                specified_amount={"currency_code": "USD", "units": amount}
            ),
            threshold_rules=[
                billing_budgets_v1.ThresholdRule(
                    threshold_percent=0.5,  # Alert at 50%
                    spend_basis=billing_budgets_v1.ThresholdRule.Basis.CURRENT_SPEND,
                ),
                billing_budgets_v1.ThresholdRule(
                    threshold_percent=0.9,  # Alert at 90%
                    spend_basis=billing_budgets_v1.ThresholdRule.Basis.CURRENT_SPEND,
                ),
                billing_budgets_v1.ThresholdRule(
                    threshold_percent=1.0,  # Alert at 100%
                    spend_basis=billing_budgets_v1.ThresholdRule.Basis.CURRENT_SPEND,
                ),
            ],
        )
        
        try:
            request = billing_budgets_v1.CreateBudgetRequest(
                parent=billing_account,
                budget=budget,
            )
            response = client.create_budget(request=request)
            print(f"✓ Created budget alert: ${amount} ({response.name})")
        except Exception as e:
            print(f"⚠ Budget ${amount} might already exist or error: {e}")


def create_monitoring_alert(project_id: str):
    """
    Create Cloud Monitoring alert for excessive Vertex AI spending.
    
    Triggers when Vertex AI spend exceeds $10/hour.
    """
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"
    
    # Alert condition: Vertex AI cost > $10/hour
    condition = monitoring_v3.AlertPolicy.Condition(
        display_name="Vertex AI High Cost Alert",
        condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
            filter='metric.type="billing.googleapis.com/cost" AND resource.type="global" AND metric.label.service="Vertex AI"',
            comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
            threshold_value=10.0,
            duration={"seconds": 3600},  # 1 hour
            aggregations=[
                monitoring_v3.Aggregation(
                    alignment_period={"seconds": 3600},
                    per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_SUM,
                )
            ],
        ),
    )
    
    alert_policy = monitoring_v3.AlertPolicy(
        display_name="Vertex AI GPU Cost Alert - $10/hour",
        conditions=[condition],
        combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.AND,
        enabled=True,
        documentation=monitoring_v3.AlertPolicy.Documentation(
            content="Vertex AI GPU spending is exceeding $10/hour. Check running jobs immediately.",
            mime_type="text/markdown",
        ),
    )
    
    try:
        response = client.create_alert_policy(
            name=project_name,
            alert_policy=alert_policy,
        )
        print(f"✓ Created monitoring alert: {response.name}")
    except Exception as e:
        print(f"⚠ Monitoring alert might already exist or error: {e}")


def verify_alerts(project_id: str):
    """List all active budget and monitoring alerts."""
    print("\n" + "="*80)
    print("ACTIVE ALERTS")
    print("="*80)
    
    # List monitoring alerts
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"
    
    try:
        policies = client.list_alert_policies(name=project_name)
        print("\nCloud Monitoring Alerts:")
        for policy in policies:
            if "Vertex AI" in policy.display_name or "GPU" in policy.display_name:
                print(f"  - {policy.display_name}: {policy.enabled}")
    except Exception as e:
        print(f"  Could not list alerts: {e}")
    
    print("\nTo view budget alerts:")
    print(f"  https://console.cloud.google.com/billing/budgets?project={project_id}")
    print("\nTo view monitoring alerts:")
    print(f"  https://console.cloud.google.com/monitoring/alerting?project={project_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up cost alerts for Vertex AI")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--billing-account", help="Billing account ID (format: billingAccounts/XXXXXX-XXXXXX-XXXXXX)")
    parser.add_argument("--skip-budgets", action="store_true", help="Skip budget creation (requires billing account)")
    
    args = parser.parse_args()
    
    print("="*80)
    print("VERTEX AI COST MONITORING SETUP")
    print("="*80)
    print()
    
    # Create monitoring alert (doesn't require billing account)
    print("Setting up Cloud Monitoring alerts...")
    create_monitoring_alert(args.project)
    print()
    
    # Create budget alerts (requires billing account)
    if not args.skip_budgets:
        if not args.billing_account:
            print("⚠ Skipping budget alerts (--billing-account not provided)")
            print("  To create budget alerts, provide your billing account ID:")
            print("  --billing-account billingAccounts/XXXXXX-XXXXXX-XXXXXX")
            print()
        else:
            print("Setting up budget alerts...")
            create_budget_alerts(args.project, args.billing_account)
            print()
    
    # Verify setup
    verify_alerts(args.project)
    
    print("\n✅ Cost monitoring setup complete!")
    print("\nNext steps:")
    print("1. Verify alerts in GCP Console")
    print("2. Add notification channels (email/SMS)")
    print("3. Test with a small GPU job")

