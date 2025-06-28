# ClipScribe v2.18.4 - Video Intelligence Platform 🧪 VALIDATION PHASE

<p align="center">
  <strong>AI-powered video intelligence for 1800+ platforms</strong>
</p>

<p align="center">
  <em>🧪 VALIDATION PHASE: Systematic testing of all claimed functionality</em>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#validation">Validation</a> •
  <a href="#contributing">Contributing</a>
</p>

---

ClipScribe is a video intelligence tool that leverages Google's Gemini to provide video analysis. It supports **1800+ video platforms** through yt-dlp integration and serves as a video intelligence collector for research workflows.

## 🚨 CURRENT STATUS: VALIDATION PHASE

**v2.18.4 - Critical Bug Fixes + Validation Framework**

We've implemented critical bug fixes and established a comprehensive validation framework. **All features are currently undergoing systematic validation** before being marked as production-ready.

### 🧪 Validation-First Approach
- **150+ validation points** across all workflows
- **Real data testing** with actual video collections  
- **End-to-end user workflows** validation
- **95% pass rate required** before claiming features work
- **Document all failures** and fix before marking complete

### ✅ Recent Fixes (v2.18.4)
- **Timeline Intelligence**: Fixed fundamental date extraction logic
- **Information Flow Maps**: Resolved AttributeError crashes  
- **Validation Framework**: Created comprehensive testing checklist

### ⚠️ Validation Status
**Phase 1 validation showing excellent progress:**
- [x] Single video processing workflows ✅ **VALIDATED** - PBS NewsHour (53min) processed successfully
- [x] Mission Control UI functionality ✅ **VALIDATED** - All pages accessible, navigation working, bug fixes confirmed
- [ ] Multi-video collection processing ⚠️ **NEXT PRIORITY** - Required for Timeline Intelligence features
- [ ] Output format generation ⚠️ **NEEDS TESTING**
- [ ] Cost tracking and optimization ⚠️ **NEEDS TESTING**

See [VALIDATION_CHECKLIST.md](docs/VALIDATION_CHECKLIST.md) for complete validation status.

## ✨ Claimed Features (Under Validation)

- 🎛️ **Mission Control** - Web interface for video intelligence management
- 🌍 **Platform Support** - YouTube, TikTok, Twitter/X, and 1800+ more
- 🚀 **Gemini Integration** - Direct video processing with temporal intelligence
- 📊 **Knowledge Extraction** - Entities, relationships, topics, and timelines
- 🧠 **Multi-Video Analysis** - Collection processing with cross-video intelligence
- 💰 **Cost Optimization** - Intelligent API usage and caching
- 📈 **Multiple Exports** - JSON, Markdown, GEXF, and visualization formats

**Note**: All features are currently being validated. Completion claims will be updated based on validation results.

## 📋 Requirements

- Python 3.12+ (3.13 supported)
- A Google API key with Gemini access enabled
- [FFmpeg](https://ffmpeg.org/download.html) installed on your system

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/bubroz/clipscribe.git
   cd clipscribe
   ```

2. **Install with Poetry**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file with your Google API key
   echo "GOOGLE_API_KEY=your_actual_key_here" > .env
   ```

4. **Verify installation**
   ```bash
   poetry run clipscribe --version
   ```

## 💻 Usage

### Command-Line Interface (CLI)

```bash
# Basic video processing (validation in progress)
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=6ZVj1_SE4Mo"

# Collection processing (validation in progress)  
poetry run clipscribe process-collection "Test-Collection" "URL1" "URL2"

# Configuration
poetry run clipscribe config
```

### Mission Control Web Interface

```bash
# Launch Mission Control (validation in progress)
poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py
```

**✅ Mission Control Status**: UI fully validated and operational! All pages loading correctly with comprehensive navigation. Timeline Intelligence features require collection data (next validation priority).

## 🧪 Validation Process

We're systematically validating all claimed functionality:

### Phase 1: Core Functionality (Current)
- **Week 1**: Single video processing workflows
- **Week 2**: Mission Control UI validation
- **Week 3**: Multi-video collection processing  
- **Week 4**: Output format validation

### Phase 2: Advanced Features
- **Weeks 5-8**: Enhanced temporal intelligence, retention system

### Phase 3: Production Readiness  
- **Weeks 9-12**: Scale testing, documentation validation

See [VALIDATION_CHECKLIST.md](docs/VALIDATION_CHECKLIST.md) for detailed validation criteria.

## 🐍 Python API

```python
import asyncio
from clipscribe.retrievers import VideoIntelligenceRetriever

async def main():
    # Note: API functionality currently under validation
    retriever = VideoIntelligenceRetriever()
    result = await retriever.process_url("https://youtube.com/watch?v=...")
    
    if result:
        print(f"Title: {result.metadata.title}")
        print(f"Entities found: {len(result.entities)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📁 Project Structure

```
clipscribe/
├── src/clipscribe/           # Main package
│   ├── commands/             # CLI implementation  
│   ├── extractors/           # Entity & relationship extraction
│   ├── retrievers/           # Video processing core
│   └── utils/                # Utilities and helpers
├── streamlit_app/            # Mission Control web interface
├── tests/                    # Test suite
├── docs/                     # Documentation
│   └── VALIDATION_CHECKLIST.md  # Comprehensive validation framework
├── examples/                 # Usage examples
└── output/                   # Generated outputs
```

## 🔧 Configuration

Create a `.env` file:

```env
# Required
GOOGLE_API_KEY="your_gemini_api_key_here"

# Optional (defaults shown)
OUTPUT_DIR=output
LOG_LEVEL=INFO
```

## 🛠️ Development

**ClipScribe is developed with AI assistance using [Cursor](https://cursor.sh/)** - demonstrating AI-augmented development workflows.

### Contributing to Validation

Help us validate ClipScribe functionality:

1. **Test workflows** from VALIDATION_CHECKLIST.md
2. **Report failures** with detailed reproduction steps
3. **Document edge cases** and unexpected behaviors
4. **Verify fixes** after implementation

## 📊 Validation Metrics

### Success Criteria
- **Functionality**: 95% of validation checklist passes
- **Performance**: Processing within expected ranges  
- **Reliability**: <5% failure rate on standard inputs
- **Usability**: Users complete workflows without assistance

### Current Status
See [VALIDATION_CHECKLIST.md](docs/VALIDATION_CHECKLIST.md) for real-time validation progress.

## 🚨 Known Issues

- Mission Control UI may have functionality gaps
- Some advanced features need end-to-end validation
- Performance optimization pending validation
- Documentation may not reflect current functionality

All issues are being systematically addressed through our validation process.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for universal video platform support
- [Google Gemini](https://deepmind.google/technologies/gemini/) for AI transcription
- [Click](https://click.palletsprojects.com/) and [Rich](https://rich.readthedocs.io/) for the CLI

---

<p align="center">
  🧪 Currently in validation phase - systematic testing in progress
</p>
