#!/bin/bash
# Run this in EXTERNAL terminal to avoid Cursor timeouts
# Speaker Diarization Threshold Testing

cd /Users/base/Projects/clipscribe

echo "================================"
echo "THRESHOLD BINARY SEARCH"
echo "================================"
echo ""
echo "Current findings:"
echo "  0.70: 6 speakers, 17% accuracy"
echo "  0.95: 2 speakers, 37% accuracy"
echo "  1.20: 2 speakers, 37% accuracy"
echo ""
echo "Next test: 0.80 (closer to working threshold)"
echo ""
echo "Manual steps:"
echo "1. Edit deploy/station10_modal.py line 182"
echo "   Change: CLUSTERING_THRESHOLD = 0.80"
echo ""
echo "2. Deploy:"
echo "   git add deploy/station10_modal.py"
echo "   git commit -m 'test(diarization): threshold 0.80'"
echo "   git push"
echo "   poetry run modal deploy deploy/station10_modal.py"
echo ""
echo "3. Test:"
echo "   gsutil rm -r gs://clipscribe-validation/validation/results/ 2>/dev/null"
echo "   poetry run python scripts/validation/test_chime6.py"
echo ""
echo "4. Record result and proceed to next test based on outcome"
echo ""
echo "================================"

