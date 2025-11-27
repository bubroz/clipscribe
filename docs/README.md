# ClipScribe Documentation

**Version:** v3.1.10  
**Last Updated:** November 2025  
**Status:** Provider-based architecture, file-first processing, GEOINT engine (Beta)

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

**[Output Format](OUTPUT_FORMAT.md)** - Complete schema reference
- Full JSON structure
- All data fields explained
- Entity types reference
- Usage examples (Pandas, SQL)

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

## Advanced Features

### Geolocation Intelligence (Beta)

**[GEOINT Engine](advanced/GEOINT.md)** - Geospatial telemetry extraction
- Consumer drone telemetry (DJI, Autel)
- Military KLV support (MISB ST 0601)
- Automatic GPS coordinate correlation
- Google Earth KML export
- Interactive HTML maps

**[DJI Requirements](advanced/GEOINT_DJI_REQUIREMENTS.md)** - File format specifications
- Exact file format requirements
- How to enable telemetry
- Supported drone models
- Validation checklist

**[OSINT Workflows](advanced/OSINT_GEOINT_WORKFLOWS.md)** - Use case examples
- Geolocation verification
- Timeline analysis
- Cross-reference with audio intelligence
- Social media claims validation

**Note:** GEOINT is an optional advanced feature. Core intelligence extraction works without it.

---

## Technical Documentation

### For Developers

**[Architecture](ARCHITECTURE.md)** - System design
- Provider architecture overview
- GEOINT engine (optional component)
- Processing flows (CLI + API)
- Data structures
- Cost model
- Extensibility (how to add providers)

**[Development](DEVELOPMENT.md)** - Contributing guide
- Development setup
- Adding new providers
- Adding new telemetry formats
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

## What's New in v3.1.10

**IAM SignBlob Integration:**
- Presigned URL generation using IAM SignBlob API
- Cloud Run deployment compatibility
- API container dependency fixes

## What's New in v3.1.0

**Geolocation Intelligence (Beta):**
- Consumer drone telemetry extraction (DJI/Autel)
- Automatic GPS coordinate correlation with transcript
- Google Earth KML export
- Interactive HTML map generation
- Zero-dependency KLV parser (military/government support)

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

**All documentation validated November 2025 with v3.1.10 testing.**
