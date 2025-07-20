#!/bin/bash

# ClipScribe Single Video Demo Script
# Target: Analyst Co-Founders - Act 2
# Duration: 5 minutes
# Purpose: Show core extraction capabilities

set -e

echo "🔍 ClipScribe Single Video Demo"
echo "==============================="
echo "Act 2: Core Extraction Demo"
echo ""

# Configuration
VIDEO_URL="https://www.youtube.com/watch?v=tRvZty3Ub4g"
OUTPUT_DIR="demo/single_demo"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Prerequisites check
print_status "Checking ClipScribe installation..."
if ! poetry run clipscribe --help &> /dev/null; then
    echo "❌ ClipScribe not found. Run 'poetry install' first."
    exit 1
fi

print_success "ClipScribe ready!"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo ""
echo "🎬 Processing single CNBC video..."
echo "URL: $VIDEO_URL"
echo ""

# Core extraction command
poetry run clipscribe transcribe "$VIDEO_URL" \
    --mode video \
    --enhance-transcript \
    --clean-graph \
    --output-dir "$OUTPUT_DIR"

print_success "Single video processing complete!"
echo ""

# Show results
print_status "Results available in: $OUTPUT_DIR"
if [ -f "$OUTPUT_DIR/knowledge_graph.json" ]; then
    echo "✅ Knowledge graph generated"
fi
if [ -f "$OUTPUT_DIR/entities.json" ]; then
    echo "✅ Entities extracted"
fi
if [ -f "$OUTPUT_DIR/relationships.json" ]; then
    echo "✅ Relationships mapped"
fi

echo ""
print_success "Ready for Act 3: Multi-Video Magic! 🚀" 