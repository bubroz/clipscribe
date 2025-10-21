#!/bin/bash
# Download CHiME-6 dev set audio for validation
# Size: 11GB, Time: 10-30 minutes depending on connection

cd /Users/base/Projects/clipscribe

echo "🔬 CHiME-6 AUDIO DOWNLOAD"
echo "========================================================================"
echo "Downloading dev set (11GB) for validation"
echo "This will take 10-30 minutes depending on your connection"
echo ""

# Create directory
mkdir -p validation_data/chime6_audio
cd validation_data/chime6_audio

# Download from OpenSLR (multiple mirrors available)
echo "Downloading from OpenSLR (EU mirror)..."
echo "URL: https://openslr.trmal.net/resources/150/CHiME6_dev.tar.gz"
echo ""

curl -L --progress-bar -o CHiME6_dev.tar.gz \
    "https://openslr.trmal.net/resources/150/CHiME6_dev.tar.gz"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ EU mirror failed, trying CN mirror..."
    curl -L --progress-bar -o CHiME6_dev.tar.gz \
        "https://openslr.magicdatatech.com/resources/150/CHiME6_dev.tar.gz"
fi

if [ ! -f "CHiME6_dev.tar.gz" ]; then
    echo "❌ Download failed from all mirrors"
    exit 1
fi

echo ""
echo "✓ Download complete: $(ls -lh CHiME6_dev.tar.gz | awk '{print $5}')"
echo ""
echo "Extracting archive (this will take 5-10 minutes)..."

tar -xzf CHiME6_dev.tar.gz

echo ""
echo "✓ Extraction complete"
echo ""
echo "Verifying audio files..."

# Count audio files
audio_count=$(find . -name "*.wav" | wc -l | tr -d ' ')
echo "  Audio files: $audio_count"

# Check for dev sessions S02 and S09
if [ -d "audio/dev" ] || [ -d "dev" ] || find . -name "*S02*.wav" -o -name "*S09*.wav" | grep -q .; then
    echo "  ✓ Dev sessions found"
else
    echo "  ⚠️  Dev sessions not in expected location"
    echo "  Directory structure:"
    find . -maxdepth 3 -type d
fi

echo ""
echo "🎉 CHiME-6 DEV AUDIO READY FOR VALIDATION"
echo "========================================================================"
echo ""
echo "Next steps:"
echo "  1. Locate S02 and S09 audio files"
echo "  2. Run: poetry run python scripts/validation/test_chime6.py"
echo "  3. Process with Modal, calculate metrics"
echo ""
echo "Download location: $(pwd)"
echo ""

