#!/bin/bash
# Round 3 Research: Execution Architecture Design
# Run in external terminal (takes 30-60 min)

cd /Users/base/Projects/clipscribe

echo "🔬 ROUND 3 RESEARCH: EXECUTION ARCHITECTURE"
echo "======================================================================"
echo "Storage strategy, batch processing, timeline estimation"
echo ""

# =============================================================================
# STORAGE ARCHITECTURE ANALYSIS
# =============================================================================

echo "💾 STORAGE ARCHITECTURE RESEARCH"
echo "======================================================================"
echo ""

poetry run python << 'EOF'
print("STORAGE REQUIREMENTS ANALYSIS:")
print("="*80)
print()

datasets = {
    "AnnoMI": {"audio": 5, "transcripts": 0.01, "processed": 0.1},
    "CHiME-6 (dev)": {"audio": 11, "transcripts": 0.002, "processed": 0.2},
    "CHiME-6 (full)": {"audio": 120, "transcripts": 0.002, "processed": 0.7},
    "AMI": {"audio": 50, "transcripts": 0.02, "processed": 0.3},
    "ICSI": {"audio": 50, "transcripts": 0.02, "processed": 0.3},
    "AISHELL-4": {"audio": 100, "transcripts": 0.05, "processed": 0.5},
    "AISHELL-5": {"audio": 50, "transcripts": 0.03, "processed": 0.3},
    "AliMeeting": {"audio": 80, "transcripts": 0.04, "processed": 0.4},
    "MAGICDATA": {"audio": 120, "transcripts": 0.05, "processed": 0.6}
}

print("STORAGE BY PHASE:")
print("-"*80)

# Phase 1: AnnoMI + CHiME-6
phase1_storage = (
    datasets["AnnoMI"]["audio"] + 
    datasets["CHiME-6 (dev)"]["audio"] +
    datasets["AnnoMI"]["processed"] +
    datasets["CHiME-6 (dev)"]["processed"]
)
print(f"Phase 1 (AnnoMI + CHiME-6 dev): {phase1_storage:.1f} GB")

# Phase 2: Add AMI/ICSI
phase2_add = datasets["AMI"]["audio"] + datasets["ICSI"]["audio"] + 0.6
phase2_total = phase1_storage + phase2_add
print(f"Phase 2 (+AMI/ICSI): {phase2_total:.1f} GB")

# Phase 3: Add Mandarin
mandarin_storage = sum(
    datasets[d]["audio"] + datasets[d]["processed"]
    for d in ["AISHELL-4", "AISHELL-5", "AliMeeting", "MAGICDATA"]
)
phase3_total = phase2_total + mandarin_storage
print(f"Phase 3 (+Mandarin): {phase3_total:.1f} GB")

print()
print("STORAGE OPTIONS:")
print("-"*80)
print()

options = [
    ("4TB External SSD", 100, "Buy once, use forever", "Local"),
    ("1TB Cloud Storage", 10, "/month subscription", "GCS/S3"),
    ("Hybrid (500GB local)", 50, "External + cloud cache", "Mixed")
]

for name, cost, note, location in options:
    sufficient = "✅" if (name.startswith("4TB") or name.startswith("Hybrid")) else "⚠️"
    print(f"{sufficient} {name}:")
    print(f"   Cost: ${cost} {note}")
    print(f"   Location: {location}")
    print()

print("RECOMMENDATION:")
print("  4TB External SSD ($100) = best value")
print("  - Holds all datasets + results")
print("  - No monthly fees")
print("  - Fast local access")
print("  - Modal can read from mounted drives")

# Save storage plan
with open('validation_data/research/storage_plan.txt', 'w') as f:
    f.write("Storage Architecture Plan\n")
    f.write("="*80 + "\n\n")
    f.write(f"Phase 1: {phase1_storage:.1f} GB\n")
    f.write(f"Phase 2: {phase2_total:.1f} GB\n")
    f.write(f"Phase 3: {phase3_total:.1f} GB\n\n")
    f.write("Recommended: 4TB External SSD ($100)\n")
    f.write("Alternative: 1TB cloud storage ($10/month)\n")

print()
print("✅ Storage plan saved")
EOF

echo ""

# =============================================================================
# BATCH PROCESSING ARCHITECTURE
# =============================================================================

echo "⚡ BATCH PROCESSING ARCHITECTURE"
echo "======================================================================"
echo ""

poetry run python << 'EOF'
print("MODAL BATCH PROCESSING ANALYSIS:")
print("="*80)
print()

# Calculate processing costs and time
datasets_hours = {
    "AnnoMI": 20,
    "CHiME-6 (dev)": 12,
    "CHiME-6 (full)": 40,
    "AMI": 100,
    "ICSI": 70,
    "AISHELL-4": 120,
    "AISHELL-5": 50,
    "AliMeeting": 120,
    "MAGICDATA": 180
}

cost_per_min = 0.0018  # Average from our tests
realtime_factor = 10.6  # Average from our tests

print("PROCESSING ESTIMATES:")
print("-"*80)
print(f"{'Dataset':<20} {'Hours':<10} {'Cost':<10} {'Processing Time':<20}")
print("-"*80)

total_hours = 0
total_cost = 0

for name, hours in datasets_hours.items():
    cost = hours * 60 * cost_per_min
    proc_time = hours * 60 / realtime_factor
    total_hours += hours
    total_cost += cost
    print(f"{name:<20} {hours:<10} ${cost:>7.2f}  {proc_time:>8.1f} min ({proc_time/60:>5.1f} hrs)")

print("-"*80)
print(f"{'TOTAL':<20} {total_hours:<10} ${total_cost:>7.2f}  {total_hours*60/realtime_factor:>8.1f} min")
print()

print("PARALLELIZATION:")
print("-"*80)
print("Serial processing: {:.1f} hours".format(total_hours * 60 / realtime_factor / 60))
print()
print("Parallel processing (10 jobs):")
print("  Time: {:.1f} hours".format(total_hours * 60 / realtime_factor / 60 / 10))
print("  Cost: Same (${:.2f})".format(total_cost))
print()
print("Parallel processing (50 jobs):")
print("  Time: {:.1f} hours".format(total_hours * 60 / realtime_factor / 60 / 50))
print("  Cost: Same (${:.2f})".format(total_cost))
print()

print("MODAL LIMITS:")
print("  Max concurrent: 100+ (configurable)")
print("  Recommended: 20-50 parallel jobs")
print("  Why: Avoid API rate limits, manageable monitoring")
print()

# Save processing plan
with open('validation_data/research/processing_plan.txt', 'w') as f:
    f.write("Batch Processing Architecture\n")
    f.write("="*80 + "\n\n")
    f.write(f"Total hours to process: {total_hours}\n")
    f.write(f"Total cost: ${total_cost:.2f}\n")
    f.write(f"Serial time: {total_hours*60/realtime_factor/60:.1f} hours\n")
    f.write(f"Parallel (20 jobs): {total_hours*60/realtime_factor/60/20:.1f} hours\n\n")
    f.write("Recommended: 20-30 parallel Modal jobs\n")
    f.write("Cost: Same ($), faster completion\n")

print("✅ Processing plan saved")
EOF

echo ""

# =============================================================================
# TIMELINE ESTIMATION
# =============================================================================

echo "📅 PROJECT TIMELINE ESTIMATION"
echo "======================================================================"
echo ""

poetry run python << 'EOF'
print("COMPREHENSIVE VALIDATION TIMELINE:")
print("="*80)
print()

phases = {
    "Week 1: Pipeline Development": {
        "tasks": [
            "Build AnnoMI validator",
            "Build CHiME-6 validator",
            "Build metrics module (WER, DER)",
            "Test on 10 samples"
        ],
        "hours": 12,
        "deliverable": "Working validation pipeline"
    },
    "Week 2: Phase 1 Validation": {
        "tasks": [
            "Process all AnnoMI (133 conversations)",
            "Process CHiME-6 dev (12 hours)",
            "Calculate metrics",
            "Generate report"
        ],
        "hours": 8,
        "deliverable": "English dyadic + multi-speaker results"
    },
    "Week 3: AMI/ICSI Parser": {
        "tasks": [
            "Build NXT XML parser",
            "Test on 5 meetings",
            "Integrate with validation pipeline"
        ],
        "hours": 8,
        "deliverable": "AMI/ICSI support"
    },
    "Week 4: Phase 2 Validation": {
        "tasks": [
            "Process AMI meetings",
            "Process ICSI meetings",
            "Comprehensive English report"
        ],
        "hours": 6,
        "deliverable": "Complete English validation"
    },
    "Week 5-6: Mandarin Investigation": {
        "tasks": [
            "Download samples from 4 datasets",
            "Analyze formats",
            "Build parsers if needed",
            "Test WhisperX + Gemini on Mandarin"
        ],
        "hours": 16,
        "deliverable": "Mandarin validation readiness"
    },
    "Week 7-8: Phase 3 Validation": {
        "tasks": [
            "Process Mandarin datasets",
            "Calculate metrics",
            "Comprehensive multilingual report"
        ],
        "hours": 8,
        "deliverable": "Complete validation suite"
    },
    "Week 9: Publication": {
        "tasks": [
            "Write validation paper/report",
            "Update documentation",
            "Publish results",
            "Submit to conference (optional)"
        ],
        "hours": 12,
        "deliverable": "Published validation results"
    }
}

total_hours = 0
print("TIMELINE BREAKDOWN:")
print("-"*80)

for week, info in phases.items():
    hours = info["hours"]
    total_hours += hours
    print(f"\n{week} ({hours} hours):")
    for task in info["tasks"]:
        print(f"  - {task}")
    print(f"  Deliverable: {info['deliverable']}")

print()
print("="*80)
print(f"TOTAL EFFORT: {total_hours} hours (~70 hours)")
print(f"TIMELINE: 9 weeks (2 months)")
print(f"PARALLEL WORK: Some tasks can overlap (e.g., downloads)")
print()

# Critical path
print("CRITICAL PATH:")
print("-"*80)
print("Week 1: Pipeline dev (blocking)")
print("Week 2: Phase 1 validation (proves concept)")
print("  → DECISION GATE: Results good? Continue or fix issues")
print("Week 3-4: AMI/ICSI (English complete)")
print("  → DECISION GATE: Need Mandarin? Or publish English-only")
print("Week 5-8: Mandarin (if proceeding)")
print("Week 9: Publication")
print()

print("REALISTIC ESTIMATE:")
print("  With full-time focus: 2 months")
print("  With part-time (20hrs/week): 3.5 months")
print("  With interruptions: 4-5 months")

# Save timeline
with open('validation_data/research/timeline.txt', 'w') as f:
    f.write("Validation Project Timeline\n")
    f.write("="*80 + "\n\n")
    for week, info in phases.items():
        f.write(f"{week}:\n")
        for task in info["tasks"]:
            f.write(f"  - {task}\n")
        f.write(f"  Effort: {info['hours']} hours\n\n")
    f.write(f"\nTotal: {total_hours} hours (~2 months full-time)\n")

print()
print("✅ Timeline saved")
EOF

echo ""
echo "🎯 ROUND 3 RESEARCH COMPLETE"
echo "======================================================================"
echo ""
echo "ARCHITECTURE DECISIONS:"
echo "  ✅ Storage: 4TB external SSD ($100)"
echo "  ✅ Processing: 20-30 parallel Modal jobs"
echo "  ✅ Timeline: 9 weeks / 70 hours total"
echo ""
echo "CRITICAL PATH:"
echo "  Week 1: Build pipeline (12 hrs)"
echo "  Week 2: Validate concept (8 hrs)"
echo "  Weeks 3-4: English complete (14 hrs)"
echo "  Weeks 5-8: Mandarin (24 hrs)"
echo "  Week 9: Publish (12 hrs)"
echo ""
echo "READY FOR ROUND 4: Mandarin Deep Dive"
echo ""

