# Quick Demo Setup Guide

*Last Updated: July 20, 2025*  
*Estimated Time: 2 minutes*

## 🚀 One-Minute Demo

### 1. Process a News Video
```bash
# Extract comprehensive intelligence from a news video
poetry run clipscribe process "https://www.youtube.com/watch?v=6ZVj1_SE4Mo" \
  --format all \
  --clean-graph \
  -o demo/pegasus_analysis
```

### 2. Launch Mission Control
```bash
# Open the web interface
poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py
```

### 3. View Results
1. Navigate to **Collections** → Select your processed video
2. Explore **Entities** tab (16+ entities with metadata)
3. Check **Knowledge Synthesis** (52+ relationships with evidence)
4. Download results in any format

## 🎯 What You'll See

### Extraction Quality (v2.19.0)
- **16+ meaningful entities** (people, orgs, locations, events)
- **52+ relationships** with evidence chains and quotes
- **88+ node knowledge graph** with rich connections
- **$0.0083 processing cost** for comprehensive intelligence

### Key Features Demonstrated
- **Entity Extraction**: Comprehensive extraction targeting 100% completeness
- **Relationship Mapping**: Evidence-backed connections with quotes
- **Knowledge Graphs**: Visual network of all connections
- **Cross-Video Synthesis**: Multi-video entity correlation (if processing collections)

## 💡 Extended Demo Options

### Option 1: Multi-Video Collection
```bash
# Process a collection for cross-video intelligence
poetry run clipscribe process-collection \
  "Pegasus Investigation" \
  "https://www.youtube.com/watch?v=6ZVj1_SE4Mo" \
  "https://www.youtube.com/watch?v=xYMWTXIkANM" \
  --format all
```

### Option 2: News Playlist Analysis
```bash
# Process CNBC playlist for market intelligence
poetry run clipscribe process-collection \
  "CNBC Market Analysis" \
  "https://www.youtube.com/playlist?list=PLVbP054jv0Ko..." \
  --format all
```

## 📊 Cost Transparency

- **Single 5-min video**: ~$0.008
- **30-min documentary**: ~$0.048  
- **10-video collection**: ~$0.08-0.10

## 🎬 Best Demo Content

1. **News/Documentary**: PBS Frontline, 60 Minutes, investigative journalism
2. **Educational**: TED Talks, lectures, tutorials
3. **Business**: Earnings calls, market analysis, industry reports

Avoid: Music videos, entertainment content (poor extraction quality)

## 🚧 Common Questions

**Q: Why are there 88+ nodes but only 16 entities?**  
A: The knowledge graph includes entities, relationships, and conceptual nodes - creating a rich network.

**Q: How is this different from transcription?**  
A: We extract structured intelligence - who said what about whom, with evidence and context.

**Q: Can I process my own videos?**  
A: Yes! Upload to any supported platform (YouTube, Vimeo, etc.) or use local files.

---

**Ready to extract intelligence?** ClipScribe transforms videos into structured knowledge! 🎯 