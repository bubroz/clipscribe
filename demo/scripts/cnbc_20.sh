#!/bin/bash

# ClipScribe 20-Video CNBC Demo Script
# Target: Analyst Co-Founders
# Duration: 15-20 minutes
# Purpose: Demonstrate scale, cost efficiency, and analyst workflow fit

set -e  # Exit on any error

echo "🎯 ClipScribe 20-Video CNBC Demo"
echo "================================="
echo "Target: Analyst Co-Founders"
echo "Duration: 15-20 minutes"
echo ""

# Configuration
PLAYLIST_URL="https://www.youtube.com/playlist?list=PLVbP054jv0KoXU0a-MdzLVguQW6Nh9Wzo"
COLLECTION_NAME="cnbc-market-20"
OUTPUT_DIR="demo/cnbc_20"
LIMIT=20

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install Poetry first."
    exit 1
fi

# Check if we're in the clipscribe directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the clipscribe project root directory."
    exit 1
fi

# Check if clipscribe is installed
if ! poetry run clipscribe --help &> /dev/null; then
    print_error "ClipScribe is not installed. Please run 'poetry install' first."
    exit 1
fi

print_success "Prerequisites check passed!"

# Create output directory
print_status "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo ""
echo "🎬 Demo Flow: From Video Chaos to Actionable Intelligence"
echo "========================================================"
echo ""

# Act 1: The Analyst's Pain (2 min)
echo "📊 Act 1: The Analyst's Pain"
echo "----------------------------"
echo "Imagine analyzing 100 videos of market news manually..."
echo "Hours wasted, insights missed, patterns overlooked."
echo "ClipScribe changes that in minutes."
echo ""

# Act 2: Core Extraction Demo (5 min) - Single video first
echo "🔍 Act 2: Core Extraction Demo"
echo "------------------------------"
echo "Let's start with a single video to show the core extraction:"
echo ""

# Use a known good CNBC video for single demo
SINGLE_VIDEO_URL="https://www.youtube.com/watch?v=tRvZty3Ub4g"
print_status "Processing single video: $SINGLE_VIDEO_URL"

poetry run clipscribe transcribe "$SINGLE_VIDEO_URL" \
    --mode video \
    --enhance-transcript \
    --clean-graph \
    --output-dir "$OUTPUT_DIR/single_demo"

print_success "Single video processing complete!"
echo ""

# Act 3: Multi-Video Magic (7 min) - The main demo
echo "🚀 Act 3: Multi-Video Magic"
echo "---------------------------"
echo "Now let's process 20 videos to show the real power:"
echo ""

print_status "Starting 20-video collection processing..."
print_status "Collection: $COLLECTION_NAME"
print_status "Playlist: $PLAYLIST_URL"
print_status "Limit: $LIMIT videos"
print_status "Output: $OUTPUT_DIR"
echo ""

# The main command from the demo plan
poetry run clipscribe process-collection \
    "$COLLECTION_NAME" \
    "$PLAYLIST_URL" \
    --output-dir "$OUTPUT_DIR" \
    --skip-confirmation \
    --limit "$LIMIT"

print_success "20-video collection processing complete!"
echo ""

# Act 4: Business Case & Close (3 min)
echo "💰 Act 4: Business Case & Close"
echo "-------------------------------"
echo "ROI Analysis:"
echo "- Saved 20+ hours of manual analysis"
echo "- Cost: ~$0.002/minute (95% cheaper than competitors)"
echo "- SDVOSB advantage: $6.5M sole-source threshold for DoD/IC"
echo ""

# Show results summary
print_status "Demo Results Summary:"
echo "=========================="

if [ -d "$OUTPUT_DIR" ]; then
    echo "📁 Output directory: $OUTPUT_DIR"
    
    # Count processed files
    if [ -d "$OUTPUT_DIR/individual_videos" ]; then
        VIDEO_COUNT=$(find "$OUTPUT_DIR/individual_videos" -name "*.json" | wc -l)
        echo "📹 Videos processed: $VIDEO_COUNT"
    fi
    
    # Check for unified graph
    if [ -f "$OUTPUT_DIR/unified_knowledge_graph.json" ]; then
        echo "🕸️  Unified knowledge graph: Generated"
    fi
    
    # Check for temporal analysis
    if [ -f "$OUTPUT_DIR/temporal_analysis.json" ]; then
        echo "⏰ Temporal analysis: Generated"
    fi
    
    # Check for collection summary
    if [ -f "$OUTPUT_DIR/collection_summary.json" ]; then
        echo "📊 Collection summary: Generated"
    fi
fi

echo ""
print_success "Demo completed successfully!"
echo ""
echo "🎯 Next Steps:"
echo "1. Review results in $OUTPUT_DIR"
echo "2. Open Streamlit app: poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py"
echo "3. Rehearse presentation with actual results"
echo "4. Create presentation deck with screenshots"
echo ""

print_success "ClipScribe 20-Video Demo - READY FOR PRESENTATION! 🚀" 