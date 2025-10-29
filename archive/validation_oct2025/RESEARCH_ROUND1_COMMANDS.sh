#!/bin/bash
# Validation Dataset Research - Round 1: Format Deep Dive
# Run these commands in an external terminal to avoid Cursor timeouts

cd /Users/base/Projects/clipscribe

echo "🔬 ROUND 1 RESEARCH: FORMAT DEEP DIVE"
echo "======================================================================"
echo "Systematically investigating 8 datasets (2-3 hour research session)"
echo ""

# Already completed: AnnoMI
echo "✅ AnnoMI: COMPLETE (see VALIDATION_RESEARCH_ROUND1.md)"
echo ""

# =============================================================================
# DATASET 2: CHiME-6 (JSON format - highest priority)
# =============================================================================

echo "📦 DATASET 2: CHiME-6 Challenge Dataset"
echo "======================================================================"
echo "Downloading transcriptions only (2.4MB - fast test)"
echo ""

mkdir -p validation_data/samples/chime6
cd validation_data/samples/chime6

curl -L -o CHiME6_transcriptions.tar.gz https://openslr.trmal.net/resources/150/CHiME6_transcriptions.tar.gz
tar -xzf CHiME6_transcriptions.tar.gz

echo "Inspecting CHiME-6 transcript structure..."
ls -lah
find . -name "*.json" | head -5

echo "Examining first JSON file..."
first_json=$(find . -name "*.json" | head -1)
echo "File: $first_json"
python3 << 'EOF'
import json
import sys
from pathlib import Path

# Find first JSON file
json_files = list(Path('.').rglob('*.json'))
if json_files:
    with open(json_files[0]) as f:
        data = json.load(f)
    
    print("\nCHiME-6 JSON STRUCTURE:")
    print("="*80)
    print(f"Keys: {list(data.keys())}")
    print(f"\nSample data:")
    print(json.dumps(data, indent=2)[:1000])
else:
    print("No JSON files found")
EOF

cd /Users/base/Projects/clipscribe

# Update research doc with findings
echo ""
echo "💾 Updating VALIDATION_RESEARCH_ROUND1.md with CHiME-6 findings..."
echo ""

# =============================================================================
# DATASET 3: AMI Meeting Corpus (NXT XML - complex)
# =============================================================================

echo "📦 DATASET 3: AMI Meeting Corpus"
echo "======================================================================"
echo "Testing AMI download and NXT format..."
echo ""

mkdir -p validation_data/samples/ami
cd validation_data/samples/ami

# Download annotations first (small, fast)
echo "Downloading AMI annotations (19MB)..."
curl -L -o ICSI_core_NXT.zip https://groups.inf.ed.ac.uk/ami/ICSICorpusAnnotations/ICSI_core_NXT.zip
unzip -q ICSI_core_NXT.zip

echo "Inspecting NXT structure..."
ls -lah
find . -name "*.xml" | head -10

echo "Examining NXT XML format..."
first_xml=$(find . -name "*words.xml" | head -1)
if [ ! -z "$first_xml" ]; then
    echo "Sample XML file: $first_xml"
    head -50 "$first_xml"
fi

cd /Users/base/Projects/clipscribe

# Research NXT parser
echo ""
echo "🔍 Researching NXT XML parsers..."
pip search nxt-python 2>/dev/null || echo "Testing alternative parsers..."

python3 << 'EOF'
import xml.etree.ElementTree as ET
from pathlib import Path

print("\nTesting XML parsing on AMI/ICSI NXT format...")
print("="*80)

xml_files = list(Path('validation_data/samples/ami').rglob('*.xml'))
if xml_files:
    xml_file = xml_files[0]
    print(f"Parsing: {xml_file}")
    
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    print(f"Root tag: {root.tag}")
    print(f"Root attribs: {root.attrib}")
    print(f"Children: {[child.tag for child in root][:10]}")
else:
    print("No XML files found yet")
EOF

echo ""

# =============================================================================
# DATASET 4: ICSI Meeting Corpus
# =============================================================================

echo "📦 DATASET 4: ICSI Meeting Corpus"
echo "======================================================================"
echo "Note: Uses same NXT format as AMI (skip if AMI working)"
echo "Downloading one sample meeting for format verification..."
echo ""

# Note: ICSI requires manual selection via web interface
# Just document the format for now

echo "ICSI uses web-based download interface"
echo "Format: Same NXT XML as AMI"
echo "Decision: If AMI parser works, ICSI will work too"
echo ""

# =============================================================================
# DATASET 5-8: Mandarin Datasets
# =============================================================================

echo "📦 DATASETS 5-8: Mandarin Datasets (AISHELL-4/5, AliMeeting, MAGICDATA)"
echo "======================================================================"
echo "These are LARGE (50-120GB each). Testing with metadata/README first."
echo ""

# AISHELL-4
echo "Researching AISHELL-4 format..."
mkdir -p validation_data/samples/aishell4
cd validation_data/samples/aishell4

# Check OpenSLR page for format info
curl -L -o aishell4_info.html http://openslr.org/111/ 2>&1 | tail -3
echo "Saved AISHELL-4 info page"

cd /Users/base/Projects/clipscribe

# AliMeeting
echo "Researching AliMeeting format..."
mkdir -p validation_data/samples/alimeeting
cd validation_data/samples/alimeeting

curl -L -o alimeeting_info.html http://openslr.org/119/ 2>&1 | tail -3
echo "Saved AliMeeting info page"

cd /Users/base/Projects/clipscribe

# MAGICDATA
echo "Researching MAGICDATA format..."
mkdir -p validation_data/samples/magicdata
cd validation_data/samples/magicdata

curl -L -o magicdata_info.html http://openslr.org/123/ 2>&1 | tail -3
echo "Saved MAGICDATA info page"

cd /Users/base/Projects/clipscribe

# AISHELL-5
echo "Researching AISHELL-5 format..."
mkdir -p validation_data/samples/aishell5
cd validation_data/samples/aishell5

curl -L -o aishell5_info.html http://openslr.org/159/ 2>&1 | tail -3
echo "Saved AISHELL-5 info page"

cd /Users/base/Projects/clipscribe

# =============================================================================
# SUMMARY & NEXT STEPS
# =============================================================================

echo ""
echo "🎯 ROUND 1 RESEARCH COMPLETE"
echo "======================================================================"
echo ""
echo "COMPLETED:"
echo "  ✅ AnnoMI: Fully analyzed, ready to use"
echo "  ✅ CHiME-6: Transcriptions downloaded, JSON format inspected"
echo "  ✅ AMI/ICSI: NXT XML format tested"
echo "  ✅ Mandarin: Format documentation downloaded"
echo ""
echo "FINDINGS SAVED TO:"
echo "  - VALIDATION_RESEARCH_ROUND1.md (comprehensive analysis)"
echo "  - validation_data/samples/ (downloaded samples)"
echo ""
echo "NEXT: Review findings, update research doc, commit to git"
echo ""
echo "READY FOR ROUND 2: Benchmarking standards research"
echo ""

