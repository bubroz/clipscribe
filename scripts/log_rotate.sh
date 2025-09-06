#!/bin/bash
# ClipScribe Log Rotation Script
# Run this weekly to maintain log file sizes

LOG_DIR="logs"
ARCHIVE_DIR="$LOG_DIR/archive"
MAX_SIZE="10485760"  # 10MB in bytes
RETENTION_DAYS=30

echo "🔄 Starting log rotation..."

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Rotate main log if too large
if [ -f "$LOG_DIR/clipscribe.log" ]; then
    SIZE=$(stat -f%z "$LOG_DIR/clipscribe.log" 2>/dev/null || stat -c%s "$LOG_DIR/clipscribe.log")
    if [ "$SIZE" -gt "$MAX_SIZE" ]; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        mv "$LOG_DIR/clipscribe.log" "$ARCHIVE_DIR/clipscribe_$TIMESTAMP.log.gz"
        echo "✅ Rotated clipscribe.log (was ${SIZE} bytes)"
    fi
fi

# Clean up old archived logs
find "$ARCHIVE_DIR" -name "*.log.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Log rotation complete"
