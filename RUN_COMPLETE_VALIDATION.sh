#!/bin/bash
# COMPLETE COMPREHENSIVE VALIDATION - Grok-4 Fast Reasoning
# 
# This script ensures COMPLETE COMPLETE validation:
# 1. All 3 diverse videos
# 2. All intelligence features (entities, relationships, topics, moments, sentiment)
# 3. Accurate cost tracking (official xAI pricing)
# 4. Evidence quotes validation
# 5. Full output verification
#
# Run this in an EXTERNAL terminal for visibility

cd /Users/base/Projects/clipscribe

echo "================================================================================"
echo "COMPLETE COMPREHENSIVE VALIDATION - Grok-4 Fast Reasoning"
echo "================================================================================"
echo ""
echo "This will test:"
echo "  ✓ 3 diverse videos (All-In 88min, The View 36min, MTG 71min)"
echo "  ✓ Entity extraction (18 spaCy types)"
echo "  ✓ Relationship mapping"
echo "  ✓ Topics extraction (NEW!)"
echo "  ✓ Key moments extraction (NEW!)"
echo "  ✓ Sentiment analysis (NEW!)"
echo "  ✓ Evidence quotes (NEW!)"
echo "  ✓ Accurate cost tracking (official xAI pricing)"
echo ""
echo "Model: grok-4-fast-reasoning"
echo "Chunk limit: 200k chars (ensures ALL videos get full intelligence)"
echo ""
echo "Expected runtime: 25-30 minutes"
echo "Expected cost: ~$2.00-3.00 total"
echo ""
echo "================================================================================"
read -p "Press Enter to start complete validation..."

# Run the comprehensive validation
poetry run python scripts/validation/comprehensive_validation_grok4.py

echo ""
echo "================================================================================"
echo "VALIDATION COMPLETE"
echo "================================================================================"
echo ""
echo "Results saved to:"
echo "  - validation_data/grok4_complete_validation.json"
echo "  - GCS: gs://clipscribe-validation/validation/grok4_results/"
echo ""
echo "Next steps:"
echo "  1. Review validation results"
echo "  2. Verify topics/moments/sentiment extracted"
echo "  3. Compare cost to previous Grok-2 run"
echo "  4. Proceed to Week 5-8 features if passed"
echo ""
echo "================================================================================"

