#!/usr/bin/env python3
"""
Calculates actual costs and profit margins for different pricing models.
This script uses the corrected, duration-based cost estimation logic from settings.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table

from src.clipscribe.config.settings import Settings


def run_simulation():
    """Run the cost and pricing simulation."""
    settings = Settings()
    console = Console()

    # --- 1. Calculate Base Costs ---
    console.print("\n[bold blue]1. Base Cost Calculation (per minute)[/bold blue]")

    flash_cost_per_minute = settings.estimate_cost(duration_seconds=60, is_pro_model=False)
    pro_cost_per_minute = settings.estimate_cost(duration_seconds=60, is_pro_model=True)
    cost_ratio = pro_cost_per_minute / flash_cost_per_minute if flash_cost_per_minute > 0 else 0

    cost_table = Table(title="Actual Per-Minute Processing Costs")
    cost_table.add_column("Model", style="cyan")
    cost_table.add_column("Cost/Minute", style="yellow")
    cost_table.add_column("Cost/Hour", style="green")
    cost_table.add_column("Cost Ratio vs Flash", style="magenta")

    cost_table.add_row(
        "Gemini 2.5 Flash",
        f"${flash_cost_per_minute:.5f}",
        f"${flash_cost_per_minute * 60:.3f}",
        "1.0x",
    )
    cost_table.add_row(
        "Gemini 2.5 Pro",
        f"${pro_cost_per_minute:.5f}",
        f"${pro_cost_per_minute * 60:.3f}",
        f"{cost_ratio:.1f}x",
    )
    console.print(cost_table)
    console.print(
        "[dim]Note: Costs are for ClipScribe's audio-processing pipeline.[/dim]"
    )

    # --- 2. Define Pricing Plans & Credit System ---
    console.print("\n[bold blue]2. Proposed Pricing Plans & Credit System[/bold blue]")
    flash_credits_per_minute = 1
    pro_credits_per_minute = 2

    plans = [
        {"name": "Starter", "price_usd": 29.0, "credits": 3000},
        {"name": "Pro", "price_usd": 99.0, "credits": 12000},
        {"name": "Business", "price_usd": 299.0, "credits": 40000},
        {"name": "Student (80% off Starter)", "price_usd": 5.80, "credits": 3000},
    ]

    plan_table = Table(title="Subscription Plans")
    plan_table.add_column("Plan", style="cyan")
    plan_table.add_column("Price", style="yellow")
    plan_table.add_column("Credits", style="green")
    plan_table.add_column("Flash Minutes", style="white")
    plan_table.add_column("Pro Minutes", style="white")

    for plan in plans:
        plan["flash_minutes"] = plan["credits"] / flash_credits_per_minute
        plan["pro_minutes"] = plan["credits"] / pro_credits_per_minute
        plan_table.add_row(
            plan["name"],
            f"${plan['price_usd']:.2f}",
            f"{plan['credits']:,}",
            f"{plan['flash_minutes']:,.0f} min",
            f"{plan['pro_minutes']:,.0f} min",
        )
    console.print(plan_table)

    # --- 3. Margin Analysis ---
    console.print("\n[bold blue]3. Profit Margin Analysis[/bold blue]")

    margin_table = Table(title="Margin Analysis per Plan")
    margin_table.add_column("Plan", style="cyan")
    margin_table.add_column("Scenario", style="yellow")
    margin_table.add_column("Revenue", style="green")
    margin_table.add_column("Total Cost", style="red")
    margin_table.add_column("Profit", style="magenta")
    margin_table.add_column("Margin %", style="bold white")

    for i, plan in enumerate(plans):
        # Scenario 1: User only uses Flash
        flash_only_cost = plan["flash_minutes"] * flash_cost_per_minute
        flash_only_profit = plan["price_usd"] - flash_only_cost
        flash_only_margin = (flash_only_profit / plan["price_usd"]) * 100 if plan["price_usd"] > 0 else 0
        margin_table.add_row(
            plan["name"],
            "100% Flash Usage",
            f"${plan['price_usd']:.2f}",
            f"${flash_only_cost:.2f}",
            f"${flash_only_profit:.2f}",
            f"{flash_only_margin:.1f}%",
        )

        # Scenario 2: User only uses Pro (worst-case for you)
        pro_only_cost = plan["pro_minutes"] * pro_cost_per_minute
        pro_only_profit = plan["price_usd"] - pro_only_cost
        pro_only_margin = (pro_only_profit / plan["price_usd"]) * 100 if plan["price_usd"] > 0 else 0
        margin_table.add_row(
            plan["name"],
            "100% Pro Usage (Worst Case)",
            f"${plan['price_usd']:.2f}",
            f"${pro_only_cost:.2f}",
            f"${pro_only_profit:.2f}",
            f"{pro_only_margin:.1f}%",
        )

        if i < len(plans) - 1:
            margin_table.add_row("---", "---", "---", "---", "---", "---")

    console.print(margin_table)


if __name__ == "__main__":
    run_simulation()
