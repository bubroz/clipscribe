# ClipScribe Quick Reference

**Version**: v2.53.0  
**One-page cheat sheet for common tasks**

---

## 🚀 Common Commands

### Process Single Video
```bash
# Basic processing
clipscribe process video "VIDEO_URL"

# With X draft
clipscribe process video "VIDEO_URL" --with-x-draft

# Force reprocess (skip duplicate check)
clipscribe process video "VIDEO_URL" --force

# Debug mode
clipscribe --debug process video "VIDEO_URL"
```

### Monitor Channels
```bash
# Monitor one channel
clipscribe monitor --channels UC123...

# Multiple channels with X drafts
clipscribe monitor --channels UC123,UC456 --with-x-draft

# Custom check interval (seconds)
clipscribe monitor --channels UC123 --interval 300

# Monitor + Obsidian export
clipscribe monitor --channels UC123 --with-obsidian ~/Documents/Vault
```

### View Stats
```bash
# Processing statistics
clipscribe stats

# Shows:
# - Total videos processed
# - Success/failure counts  
# - Success rate
```

---

## 📁 Output Structure

```
output/YYYYMMDD_platform_videoid/
├── core.json              # All data (entities, relationships, metadata)
├── knowledge_graph.json   # Graph structure (nodes, edges)
├── report.md              # Human-readable summary
├── transcript.txt         # Full transcript
├── metadata.json          # Video metadata
└── x_draft/               # If --with-x-draft used
    ├── tweet.txt          # Ready-to-post text (<280 chars)
    ├── thumbnail.jpg      # Video thumbnail
    └── metadata.json      # Generation details
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Rate limiting (default: 10s between requests)
export CLIPSCRIBE_REQUEST_DELAY=5

# Daily cap (default: 100 videos/day per platform)
export CLIPSCRIBE_DAILY_CAP=200

# Log level
export LOG_LEVEL=DEBUG
```

### State Files

```
~/.clipscribe_processing.json     # Processed videos (deduplication)
~/.clipscribe_monitor_state.json  # Monitored channels (seen videos)
```

---

## 🐛 Troubleshooting

### "Already processed" message
**Cause**: Video was processed before (deduplication)  
**Fix**: Use `--force` flag to reprocess

### "Daily cap reached"
**Cause**: Hit 100 videos/day limit  
**Fix**: Wait until tomorrow OR set `CLIPSCRIBE_DAILY_CAP=200`

### "Rate limiting: waiting 10.0s"
**Cause**: ToS compliance delay (normal behavior)  
**Fix**: This is working as intended. Wait or reduce delay.

### "Grok timeout" or "0 entities"
**Cause**: Network issue or very long video  
**Fix**: Retry. Chunking handles long videos automatically.

### Download fails after 3 attempts
**Cause**: Video private, deleted, or geo-restricted  
**Fix**: Check video is accessible in browser. Try `--cookies-from-browser chrome`

---

## 📊 Performance Expectations

| Video Length | Processing Time | Cost | Entities (typical) |
|--------------|----------------|------|-------------------|
| 2 min | ~90s | $0.027 | 10-15 |
| 5 min | ~2min | $0.030 | 15-25 |
| 12 min | ~2-3min | $0.033 | 30-40 |
| 30 min | ~5-7min | $0.05-0.08 | 50-80 |

**Note**: Chunking adds ~$0.02 per chunk for long videos

---

## 🎯 Best Practices

### For Best Entity Extraction
- Educational/training content works best
- News/interviews extract well
- Vlogs/casual content may have fewer entities
- Technical content captures specialized terminology

### For X Drafts
- Works best with clear topic/announcement
- Generates engaging hooks automatically
- Character limit strictly enforced (<280)
- No hashtags (by design)

### For Obsidian
- Process multiple related videos for best graph
- Entity notes accumulate across videos
- Use for building knowledge bases
- Great for research projects

---

## 🔑 Keyboard Shortcuts

### Monitor Mode
- `Ctrl+C` - Stop monitoring
- Monitor runs in foreground (see all output)

### General
- `--help` - Show command help
- `--version` - Show ClipScribe version
- `--debug` - Enable verbose logging

---

## 📞 Quick Help

**Installation issues?** Check Python version (3.12+ required)  
**API key errors?** Verify keys in `.env` file  
**Slow processing?** Normal for first run (downloads models)  
**Missing features?** Check version: `clipscribe --version`

**Still stuck?** zforristall@gmail.com or GitHub Issues

---

**Last Updated**: October 1, 2025

