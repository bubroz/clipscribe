# 🚀 ARGOS Quick Demo Setup

**Get ARGOS running in 3 minutes!** Perfect for colleagues who want to see what this video intelligence tool can do.

## ⚡ One-Command Setup

```bash
# Clone and setup (requires Python 3.12+)
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe
poetry install
```

## 🔑 Get Your FREE API Key (30 seconds)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key" (FREE!)
3. Copy the key (starts with `AIza...`)

## 🎬 Try It Out

```bash
# Create .env file with your API key (SECURE METHOD)
echo "GOOGLE_API_KEY=your_actual_key_here" > .env

# Quick test with enhanced temporal intelligence (v2.17.0)
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=6ZVj1_SE4Mo" --enhanced-temporal

# Or run the TWO-PART demo script for a complete batch showcase
poetry run python demo.py

# Launch Mission Control web interface
poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py
```

## 🎯 Demo Features

### 1. **Mission Control Interface** (Most Impressive!)
- Visit Mission Control after running the streamlit command
- Browse Collections for multi-video analysis
- Explore Knowledge Panels for entity-centric intelligence
- View Information Flow Maps for concept evolution
- Check Analytics dashboard for cost and performance monitoring

### 2. **Enhanced Temporal Intelligence (v2.17.0)**
```bash
# Process with Timeline Building Pipeline
poetry run clipscribe process-collection "demo-collection" \
  "https://www.youtube.com/watch?v=6ZVj1_SE4Mo" \
  "https://www.youtube.com/watch?v=xYMWTXIkANM" \
  --enhanced-temporal
```

### 3. **Entity Source Analysis**
```bash
# Analyze extraction method effectiveness
poetry run python scripts/analyze_entity_sources.py --output-dir demo_output --create-visualizations --save-excel
```

### 4. **Advanced Intelligence Features**
```bash
# Research with enhanced temporal intelligence
poetry run clipscribe research "climate change" --max-results 5

# Full intelligence extraction with relationships
poetry run clipscribe transcribe "https://youtube.com/watch?v=VIDEO_ID" --use-advanced-extraction
```

## 🎨 What You'll See

- **Timeline Building Pipeline**: Enhanced temporal intelligence with web research integration (v2.17.0)
- **Cross-Video Analysis**: Multi-video collection processing with unified knowledge graphs
- **Interactive Visualizations**: Plotly charts showing cross-video entity and concept evolution
- **Excel Reports**: Multi-sheet exports with comprehensive video intelligence analytics
- **Real-time Progress**: Live updates during enhanced temporal processing
- **Knowledge Graphs**: Visual relationship networks with temporal context
- **Performance Insights**: Model cache efficiency and processing optimization
- **Mission Control**: Complete web interface for video intelligence management

## 🏆 Best Demo Videos

Use these for impressive results:

- **PBS Two-Part Series**: 
  - Part 1: `https://www.youtube.com/watch?v=6ZVj1_SE4Mo`
  - Part 2: `https://www.youtube.com/watch?v=xYMWTXIkANM`
- **NPR News**: Search "NPR" in the research command
- **BBC News**: Search "BBC News" for current events

Avoid music videos - they don't showcase the entity extraction and temporal intelligence capabilities effectively.

## 🆘 Need Help?

- **Issues?** Check `docs/TROUBLESHOOTING.md`
- **Features?** See `docs/CLI_REFERENCE.md`
- **Questions?** The code is well-documented with docstrings

## 💡 Pro Tips

1. **Use .env file** - Never put API keys in shell history
2. **Start with Mission Control** - Most comprehensive interface
3. **Use news content** - Shows off temporal intelligence best
4. **Try collection processing** - Shows the real multi-video power
5. **Enable enhanced temporal** - See the v2.17.0 capabilities in action

---

**That's it!** You now have ARGOS - a powerful video intelligence tool with enhanced temporal intelligence that can extract structured knowledge and build comprehensive timelines from any video content. Perfect for research, analysis, and knowledge discovery. 