# 🚀 ClipScribe Quick Demo Setup

**Get ClipScribe running in 3 minutes!** Perfect for colleagues who want to see what this video intelligence tool can do.

## ⚡ One-Command Setup

```bash
# Clone and setup (requires Python 3.11+)
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

# Quick test with a real PBS video (recommended by Zac)
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=6ZVj1_SE4Mo"

# Or run the TWO-PART demo script for a complete batch showcase
poetry run python demo.py

# Launch the full Streamlit UI
streamlit run app.py
```

## 🎯 Demo Features

### 1. **Streamlit Research UI** (Most Impressive!)
- Visit `http://localhost:8501` after running `streamlit run app.py`
- Try the "Research" tab with search term: `"PBS NewsHour"`
- Watch real-time progress tracking and analytics
- Upload the demo's two-part video results for comparison
- Download results in Excel, CSV, or Markdown

### 2. **Entity Source Analysis**
```bash
# Analyze extraction method effectiveness
poetry run python scripts/analyze_entity_sources.py --output-dir demo_output --create-visualizations --save-excel
```

### 3. **Performance Dashboard**
- In Streamlit, click the "Performance Dashboard" tab
- See real-time system monitoring and cache performance
- Interactive charts showing model efficiency

### 4. **Advanced CLI Features**
```bash
# Research with filtering
poetry run clipscribe research "climate change" --max-results 5

# Single video with all formats
poetry run clipscribe transcribe "https://youtube.com/watch?v=VIDEO_ID" --save-all-formats
```

## 🎨 What You'll See

- **Batch Processing**: Two-part PBS video series processed together
- **Interactive Visualizations**: Plotly charts showing cross-video entity comparison
- **Excel Reports**: Multi-sheet exports with video comparison analytics
- **Real-time Progress**: Live updates during multi-video processing
- **Knowledge Graphs**: Visual relationship networks across videos
- **Performance Insights**: Model cache efficiency and batch optimization
- **Video Comparison**: Side-by-side analysis of entity extraction effectiveness

## 🏆 Best Demo Videos

Use these for impressive results ([per Zac's preference][[memory:3676380518053530236]]):

- **PBS Two-Part Series**: 
  - Part 1: `https://www.youtube.com/watch?v=6ZVj1_SE4Mo`
  - Part 2: `https://www.youtube.com/watch?v=xYMWTXIkANM`
- **NPR News**: Search "NPR" in the research tab
- **BBC News**: Search "BBC News" for current events

Avoid music videos - they don't showcase the entity extraction and relationship mapping capabilities effectively.

## 🆘 Need Help?

- **Issues?** Check `docs/TROUBLESHOOTING.md`
- **Features?** See `docs/CLI_REFERENCE.md`
- **Questions?** The code is well-documented with docstrings

## 💡 Pro Tips

1. **Use .env file** - Never put API keys in shell history
2. **Start with Streamlit** - Most user-friendly interface
3. **Use news content** - Shows off entity extraction best
4. **Try batch processing** - Shows the real power
5. **Check performance dashboard** - See the optimization in action

---

**That's it!** You now have a powerful video intelligence tool that can extract structured knowledge from any video content. Perfect for research, analysis, and knowledge discovery. 