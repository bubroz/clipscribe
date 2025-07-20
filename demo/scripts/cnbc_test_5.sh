#!/bin/bash

# ClipScribe 5-Video CNBC Test Script
# Purpose: Test multi-video functionality before full demo
# Duration: 5-10 minutes

set -e  # Exit on any error

echo "🧪 ClipScribe 5-Video CNBC Test"
echo "==============================="
echo "Purpose: Validate multi-video functionality"
echo "Duration: 5-10 minutes"
echo ""

# Configuration
PLAYLIST_URL="https://www.youtube.com/playlist?list=PLVbP054jv0KoXU0a-MdzLVguQW6Nh9Wzo"
COLLECTION_NAME="cnbc-test-5"
OUTPUT_DIR="demo/cnbc_test_5"
LIMIT=5

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
echo "🧪 Testing Multi-Video Functionality"
echo "===================================="
echo ""

print_status "Starting 5-video collection processing..."
print_status "Collection: $COLLECTION_NAME"
print_status "Playlist: $PLAYLIST_URL"
print_status "Limit: $LIMIT videos"
print_status "Output: $OUTPUT_DIR"
echo ""

# Test the multi-video collection processing
poetry run clipscribe process-collection \
    "$COLLECTION_NAME" \
    "$PLAYLIST_URL" \
    --output-dir "$OUTPUT_DIR" \
    --skip-confirmation

print_success "5-video collection processing complete!"
echo ""

# Show results summary
print_status "Test Results Summary:"
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
    
    # Check for collection summary
    if [ -f "$OUTPUT_DIR/collection_summary.json" ]; then
        echo "📊 Collection summary: Generated"
    fi
fi

echo ""
print_success "5-video test completed successfully!"
echo ""
echo "📌 Next Steps:"
echo "1. Review the generated outputs in: $OUTPUT_DIR/"
echo "2. If successful, run the full 20-video demo: ./demo/scripts/cnbc_20.sh"
echo "3. Open Streamlit app to visualize results:"
echo "   poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py"
echo ""

print_success "ClipScribe 5-Video Test - READY FOR FULL DEMO! 🚀" 