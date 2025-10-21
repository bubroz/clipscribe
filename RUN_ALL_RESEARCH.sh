#!/bin/bash
# Master Script: Run All 4 Research Rounds
# Total time: 3-5 hours with downloads

cd /Users/base/Projects/clipscribe

echo "🚀 COMPREHENSIVE VALIDATION RESEARCH"
echo "======================================================================"
echo "Running all 4 research rounds systematically"
echo "Estimated time: 3-5 hours"
echo ""
echo "Press ENTER to continue or Ctrl+C to abort..."
read

# Round 1: Format Deep Dive
echo ""
echo "=" *80
echo "ROUND 1: FORMAT DEEP DIVE"
echo "="*80
./RESEARCH_ROUND1_COMMANDS.sh
echo ""
echo "✅ Round 1 complete. Press ENTER for Round 2..."
read

# Round 2: Benchmarking Standards  
echo ""
echo "="*80
echo "ROUND 2: BENCHMARKING STANDARDS"
echo "="*80
./RESEARCH_ROUND2_COMMANDS.sh
echo ""
echo "✅ Round 2 complete. Press ENTER for Round 3..."
read

# Round 3: Execution Architecture
echo ""
echo "="*80
echo "ROUND 3: EXECUTION ARCHITECTURE"
echo "="*80
./RESEARCH_ROUND3_COMMANDS.sh
echo ""
echo "✅ Round 3 complete. Press ENTER for Round 4..."
read

# Round 4: Mandarin Deep Dive
echo ""
echo "="*80
echo "ROUND 4: MANDARIN DEEP DIVE"
echo "="*80
./RESEARCH_ROUND4_COMMANDS.sh

echo ""
echo "="*80
echo "🎉 ALL 4 RESEARCH ROUNDS COMPLETE!"
echo "="*80
echo ""
echo "FINDINGS SAVED TO:"
echo "  - VALIDATION_RESEARCH_ROUND1_FINDINGS.md"
echo "  - VALIDATION_RESEARCH_ROUND2.md"
echo "  - validation_data/research/*.txt"
echo ""
echo "NEXT STEPS:"
echo "  1. Review all findings"
echo "  2. Make go/no-go decision"
echo "  3. Build validation pipeline (if proceeding)"
echo ""
echo "Total datasets researched: 8"
echo "Total investment to validate all: ~$12, 70 hours, 500GB"
echo ""
echo "Recommendation: Start with AnnoMI + CHiME-6 (Phases 1-2)"
echo ""

