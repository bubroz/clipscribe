# ClipScribe Documentation

**Version:** v3.0.0  
**Last Updated:** November 13, 2025  
**Status:** Provider-based architecture, file-first processing

---

## Quick Start

**New to ClipScribe?** Start here:

1. **[Installation & Setup](CLI.md#installation)** - Get ClipScribe running
2. **[Provider Selection Guide](PROVIDERS.md#provider-selection-guide)** - Choose optimal provider
3. **[Your First Processing Job](CLI.md#common-workflows)** - Process your first file

---

## User Guides

### Essential Documentation

**[CLI Reference](CLI.md)** - Complete command-line reference
- `clipscribe process` command
- All provider flags
- Common workflows
- Environment variables

**[Provider System](PROVIDERS.md)** - Choose optimal providers
- Voxtral (Mistral API): Cheap, no speakers
- WhisperX Local (Apple Silicon): FREE, speakers
- WhisperX Modal (Cloud GPU): Quality, speakers
- Cost comparison & selection guide

**[API Reference](API.md)** - GCS-first API usage
- Presigned upload flow (step-by-step)
- Job submission & tracking
- Endpoint reference
- Example clients (Python, cURL)

**[Local Processing](LOCAL_PROCESSING.md)** - FREE Apple Silicon guide
- Setup instructions
- Performance expectations
- Cost analysis (FREE!)
- Troubleshooting

**[Troubleshooting](TROUBLESHOOTING.md)** - Common issues & solutions
- API key errors
- Provider errors  
- File issues
- Performance problems
- Modal-specific issues

---

## Technical Documentation

### For Developers

**[Architecture](ARCHITECTURE.md)** - System design
- Provider architecture overview
- Processing flows (CLI + API)
- Data structures
- Cost model
- Extensibility (how to add providers)

**[Development](DEVELOPMENT.md)** - Contributing guide
- Development setup
- Adding new providers
- Testing strategy
- Code organization

**[Performance Benchmarks](PERFORMANCE_BENCHMARKS.md)** - Validated metrics
- All provider performance data
- Realtime factors
- Memory usage
- Cost per minute

---

## Testing Resources


---

## Quick Navigation

**By Use Case:**
- **Budget processing** → [Voxtral provider](PROVIDERS.md#voxtral-mistral-api)
- **FREE processing** → [WhisperX Local](LOCAL_PROCESSING.md)
- **Cloud quality** → [WhisperX Modal](PROVIDERS.md#whisperx-modal-cloud-gpu)
- **Multi-speaker** → [Provider Selection](PROVIDERS.md#provider-selection-guide)
- **API integration** → [API Reference](API.md)

**By Task:**
- **First time setup** → [CLI Installation](CLI.md#installation)
- **Choose provider** → [Selection Guide](PROVIDERS.md#provider-selection-guide)
- **Fix errors** → [Troubleshooting](TROUBLESHOOTING.md)
- **Add provider** → [Architecture: Extensibility](ARCHITECTURE.md#extensibility)
- **Check performance** → [Benchmarks](PERFORMANCE_BENCHMARKS.md)

---

## What's New in v3.0.0

**Breaking Changes:**
- File-first processing (no URL support)
- Provider selection required
- GCS-only API (presigned uploads)

**New Features:**
- Provider abstraction (swappable components)
- 3 transcription providers
- FREE local processing option
- Improved cost transparency

**Documentation:**
- Complete rewrite for v3.0.0
- All guides updated
- Actual validation data
- No outdated content

---

**All documentation validated November 13, 2025 with v3.0.0 testing.**
