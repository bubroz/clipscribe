#!/bin/bash
# Run this in EXTERNAL TERMINAL
# Tests if entity extraction actually works end-to-end

cd /Users/base/Projects/clipscribe

echo "================================"
echo "ENTITY PIPELINE VALIDATION"
echo "================================"
echo ""
echo "Processing 5 videos from MASTER_TEST_VIDEO_TABLE.md:"
echo "  1. Medical (16 min, 1 speaker)"
echo "  2. MTG Interview (71 min, 2 speakers)"
echo "  3. The View (36 min, 5+ speakers)"
echo "  4. Legal Analysis (60 min, 2+ speakers)"
echo "  5. All-In Podcast (88 min, 4-5 speakers)"
echo ""
echo "Total: ~270 minutes, ~$27 cost"
echo ""
echo "This will validate:"
echo "  ✓ Transcription works"
echo "  ✓ Speakers detected"
echo "  ✅ ENTITIES EXTRACTED (core product!)"
echo "  ✅ SPEAKER-ENTITY ATTRIBUTION"
echo "  ✅ RELATIONSHIPS MAPPED"
echo ""
echo "Run:"
echo "  poetry run python scripts/validation/test_entity_pipeline.py"
echo ""
echo "Expected time: 30-45 minutes"
echo "================================"
echo ""
read -p "Press Enter to start..."

poetry run python scripts/validation/test_entity_pipeline.py

echo ""
echo "================================"
echo "VALIDATION COMPLETE"
echo "================================"
echo ""
echo "Check results: validation_data/entity_pipeline_test_results.json"
