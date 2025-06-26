# ClipScribe Changelog

All notable changes to ClipScribe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - The Synthesis Update (v2.14.0)

### Changed
- **GEXF 1.3 Graph Export**: Upgraded the graph export to the modern GEXF 1.3 standard for full compatibility with the latest network analysis tools. This includes updating namespaces, schemas, and using the `hex` attribute for colors.

### Planned
- **Knowledge Synthesis Engine**: Evolve the multi-video processor to generate a structured, multi-faceted analysis.
  - **Consolidated Event Timeline**: A chronological sequence of key events, facts, and talking points as they are introduced across all videos.
  - **Dynamic Knowledge Panels**: "Wikipedia-style" info boxes for major entities, synthesizing all descriptions, relationships, and key statements.
  - **Information Flow Maps**: Map the "journey" of key concepts in a series, showing introduction, elaboration, and connections.
- **Streamlit "Mission Control"**: A dedicated UI for managing and analyzing collections.
  - **Collection Workbench**: Drag-and-drop interface to build, save, and manage video collections.
  - **Synthesis Dashboard**: Interactive visualizations of the Event Timeline and Knowledge Panels.
  - **Live Synthesis View**: A live-updating visualization of the unified knowledge graph as it's built.

## [2.13.0] - 2025-06-25

### Added
- **Multi-Video Intelligence Architecture**: Comprehensive system for processing multiple related videos with unified analysis
  - Cross-video entity resolution with 85% similarity threshold and AI validation
  - Unified knowledge graph generation with temporal context and relationship bridging
  - Collection-level insights and strategic intelligence extraction
  - Support for series, topic research, channel analysis, and cross-source analysis
- **Automatic Series Detection**: AI-powered pattern recognition for video series
  - Title pattern analysis (Part 1, Episode 2, etc.) with regex matching
  - Temporal consistency analysis for upload timing patterns
  - Content similarity analysis through entity and topic overlap
  - Channel consistency verification and metadata validation
  - User confirmation workflows with confidence scoring
- **Gemini 2.5 Pro Integration**: Intelligence-grade analysis for all new multi-video features
  - Collection summary generation with strategic focus and rich context
  - Entity validation with temporal context and disambiguation analysis
  - Key insights extraction focusing on information architecture
  - Narrative flow analysis for series content with story progression tracking
- **CLI Multi-Video Commands**: New command-line interfaces for multi-video workflows
  - `process-collection`: Process multiple videos as unified collection with configurable types
  - `process-series`: Dedicated series processing with automatic detection and narrative analysis
  - Support for auto-detection, user confirmation, and custom collection types
- **Enhanced Data Models**: Comprehensive multi-video data structures
  - `MultiVideoIntelligence`: Master container for unified analysis results
  - `CrossVideoEntity`: Entities resolved across videos with aliases and temporal context
  - `CrossVideoRelationship`: Relationships validated across multiple videos
  - `SeriesMetadata`: Auto-detected series information with confidence scores
  - `TopicEvolution`: Topic development tracking across video sequences
  - `NarrativeSegment`: Story flow analysis for series content
  - `VideoCollectionType`: Enum for different collection processing strategies
- **Topic Evolution Tracking**: Analysis of how topics develop across video sequences
  - Milestone identification and progression tracking
  - Thematic arc analysis with coherence scoring
  - Information dependency mapping across videos
- **Strategic Intelligence Extraction**: Pro-level insights focusing on relationships and architecture
  - Information architecture assessment and relationship dynamics analysis
  - Temporal intelligence with context-aware entity resolution
  - Cross-video validation and confidence scoring

### Changed
- **Version Updated**: Bumped to v2.13.0 across all project files
- **CLI Async Handling**: Extended async command support for new multi-video commands
- **Architecture Documentation**: Created comprehensive `MULTI_VIDEO_INTELLIGENCE_ARCHITECTURE.md`

### Technical Details
- Hybrid output approach preserves individual video outputs while adding unified collection intelligence
- Configurable quality levels (Fast/Standard/Premium/Research) with different AI usage patterns
- Cost structure: Flash for transcription (~$0.40/video), Pro for multi-video analysis (~$0.30 additional)
- Conservative edge case handling with user validation and temporal tagging
- Template-based fallback analysis if AI services fail

## [2.12.1] - 2025-06-25

### Added
- **Two-Part PBS Demo**: Real video processing demo showcasing batch capabilities
  - Processes two actual PBS NewsHour videos: Part 1 (6ZVj1_SE4Mo) and Part 2 (xYMWTXIkANM)
  - Demonstrates cross-video entity extraction comparison
  - Shows real batch processing workflow with performance analytics
  - Generates interactive visualizations across multiple videos
  - Creates comprehensive Excel reports with video comparison data
- **Security Enhancements**: Improved API key management practices
  - Replaced shell export commands with secure .env file approach
  - Updated all documentation to use echo > .env method
  - Added security best practices section to deployment guide
  - Prevents API keys from appearing in shell history
- **Demo Infrastructure**: Complete demo-ready setup for colleague sharing
  - `demo.py` script processes real PBS videos with batch analysis
  - `QUICK_DEMO_SETUP.md` for 3-minute colleague onboarding
  - `DEPLOYMENT_GUIDE.md` with comprehensive hosting options
  - Updated documentation with secure API key practices

### Changed
- **Demo Approach**: Switched from synthetic data to real video processing
- **Security Practices**: All documentation now promotes .env files over export commands
- **Documentation Updates**: Refreshed all guides to reflect June 2025 state
- **Example URLs**: Updated to use actual PBS NewsHour video series

### Fixed
- **API Key Security**: Eliminated shell history exposure risk
- **Demo Authenticity**: Removed all synthetic/fake data generation
- **Documentation Accuracy**: Updated dates and version references

## [2.12.0] - 2025-06-25

### Added
- **Advanced Plotly Visualizations**: Interactive charts for comprehensive entity source analysis
  - Pie charts for source distribution with hover effects and professional styling
  - Bar charts and horizontal charts for entity type visualization
  - Gauge visualizations for quality metrics dashboards
  - Radar charts for method effectiveness comparison
  - Graceful fallback to simple charts when Plotly unavailable
- **Excel Export Capabilities**: Multi-sheet Excel workbooks with professional formatting
  - Summary sheet with key metrics and quality statistics
  - Source Distribution sheet with detailed method performance breakdown
  - Entity Types sheet with complete analysis sorted by frequency
  - Per-Video Analysis sheet for batch processing results
  - One-click generation through Streamlit interface and CLI tools
- **Performance Dashboard Integration**: Dedicated Streamlit tab for comprehensive system monitoring
  - Real-time system health monitoring (CPU, memory, disk usage)
  - Model cache analytics with hit rates, load times, and efficiency metrics
  - Interactive gauge visualizations for performance metrics
  - Historical performance reports and trend analysis
- **Enhanced Entity Source Analysis**: Comprehensive CLI tool improvements
  - Interactive visualizations enabled by default (--create-visualizations)
  - Excel export option (--save-excel) with multi-sheet professional formatting
  - Enhanced CSV formatting with detailed source breakdowns
  - Quality insights and automated recommendations
  - Support for both single video and batch analysis modes

### Changed
- **Streamlit UI Enhancements**: Major improvements to web interface
  - Added dedicated Performance Dashboard tab with comprehensive monitoring
  - Enhanced entity analysis with interactive visualizations and export options
  - Improved batch processing interface with real-time analytics
  - One-click Excel and CSV downloads for analysis results
- **Version Updated**: Bumped to v2.12.0 across all project files
- **Dependencies**: Added openpyxl for Excel export capabilities (already in pyproject.toml)

### Fixed
- **Performance Monitor**: Fixed batch processing metrics and report generation
- **Excel Generation**: Proper multi-sheet Excel workbook creation with professional formatting
- **Visualization Dependencies**: Graceful handling when Plotly unavailable
- **Streamlit Integration**: Seamless integration of performance dashboard components

### Technical Details
- All v2.12.0 enhancement tests pass (7/7)
- Comprehensive test coverage for new visualization and export features
- Backward compatibility maintained with existing analysis workflows
- Performance improvements through enhanced model cache monitoring

## [2.10.1] - 2025-06-25

### Added
- **Entity Source Tracking**: New `entity_sources.json` and `entity_sources.csv` files show which extraction method (SpaCy, GLiNER, REBEL) found each entity
- **Model Manager**: Singleton pattern for ML model instances prevents repeated loading in batch processing
- **Retry Logic**: Automatic retry for ffmpeg errors with exponential backoff

### Fixed
- **Model Reloading**: Models are now cached and reused across batch processing (3-5x performance improvement)
- **Tokenizer Warnings**: Suppressed sentencepiece tokenizer warnings from GLiNER model loading
- **ffmpeg Errors**: Exit code 183 errors now retry automatically up to 3 times
- **Python Version**: Relaxed constraint to support Python 3.12+ (was 3.12,<3.13)

### Changed
- Improved batch processing performance through model caching
- Better error handling and logging for download failures
- Added source tracking to entity properties for better analysis

### Documentation
- Added troubleshooting entries for Python version warning and tokenizer warning
- Updated documentation to reflect new entity source tracking feature

## [2.2.0] - 2025-01-15

### Added
- **REBEL Integration** - Extract entity relationships from video transcripts
  - Extracts (subject, predicate, object) triples
  - Builds comprehensive fact databases from videos
  - Example: "Elon Musk → founded → SpaceX"
- **GLiNER Integration** - Detect custom entity types beyond standard NER
  - Domain-specific entities (weapons, operations, technologies)
  - Specialized extraction for military, tech, finance, medical domains
  - Detects ANY entity type you specify
- **Knowledge Graph Generation** - Build NetworkX-compatible graphs
  - Nodes from entities, edges from relationships
  - Graph statistics (density, connected components)
  - Export to JSON for visualization tools
- **Advanced Hybrid Extractor** - Complete intelligence extraction pipeline
  - SpaCy for basic NER (free)
  - GLiNER for custom entities
  - REBEL for relationships
  - Selective LLM validation for low-confidence items
  - 98.6% cost reduction vs pure LLM approach
- **Domain-Specific Extraction** - Optimized for different content types
  - Military: weapons, operations, units, bases
  - Technology: software, algorithms, frameworks
  - Finance: stocks, metrics, investments
  - Medical: diseases, treatments, procedures
- **New Output Formats**:
  - `relationships.json` - All extracted relationships with confidence
  - `knowledge_graph.json` - Complete graph structure
  - `facts.txt` - Human-readable fact list
- **Advanced Extraction Demo** - `examples/advanced_extraction_demo.py`
  - Shows entity distribution, top relationships, key facts
  - Visualizes knowledge graph statistics
  - Domain-specific extraction examples
- **Processing Statistics** - Track extraction performance
  - Entity counts by source (SpaCy vs GLiNER)
  - Relationship extraction metrics
  - Graph complexity measures

### Changed
- `VideoIntelligence` model now includes relationships and knowledge_graph fields
- `VideoIntelligenceRetriever` supports `use_advanced_extraction` parameter
- Manifest format updated to version 2.2 with extraction stats
- Dependencies updated to include torch, transformers, gliner, networkx
- Enhanced transcriber to support both audio and video file processing
- Updated CLI with helpful mode selection guidance
- UniversalVideoClient now supports downloading full video files

### Technical Details
- ~2GB model download on first run (cached thereafter)
- GPU acceleration supported (CUDA, MPS/Apple Metal)
- Processes in chunks to handle long transcripts
- Async processing for efficient extraction

### Previous Updates (Moved from Unreleased)
- Meaningful filename generation for transcripts
  - Transcripts now saved using video title as filename
  - Automatic filename sanitization for OS compatibility
  - Duplicate handling with numbered suffixes
  - `create_output_filename()` utility function
- Structured machine-readable output format
  - Directory naming: `{date}_{platform}_{video_id}/`
  - Multiple output formats saved simultaneously (txt, json, srt, vtt)
  - Manifest file with file index and checksums
  - Metadata file with video info and statistics
  - Entities file for knowledge graph integration
  - Chimera-compatible format for easy integration
  - `save_all_formats()` method for complete output
  - `structured_output_demo.py` example
- Updated examples to save transcripts with video titles
- Enhanced `VideoIntelligenceRetriever` with `save_transcript()` method
- Enhanced `VideoIntelligenceRetriever` with `save_all_formats()` method
- Improved filename utilities with platform/video ID extraction
- Transitioned to Poetry-only dependency management
- Removed all pip/tox references from project

## [2.1.0] - 2025-06-23

### Added
- Hybrid entity extraction system using SpaCy + selective LLM validation
- Proper subtitle segment generation (30-second segments)
- Comprehensive output format documentation (`docs/OUTPUT_FORMATS.md`)
- `SpacyEntityExtractor` for zero-cost named entity recognition
- `HybridEntityExtractor` with confidence-based routing
- Cost tracking for entity extraction operations
- Test script for improvements (`examples/test_improvements.py`)

### Changed
- Entity extraction now uses hybrid approach (98.6% cost reduction)
- SRT/VTT files now have proper time segments instead of one giant block
- Added spacy dependency for reliable entity extraction

## [2.0.0] - 2025-06-23

### Added
- Complete project restructure with `src/clipscribe/` layout
- Comprehensive documentation suite in `docs/` directory
- 7 production-ready example scripts with full documentation
- CONTINUATION_PROMPT.md for session continuity
- Pydantic models for type-safe data structures
- VideoIntelligenceRetriever for unified video processing
- Cost tracking ($0.002/minute with Gemini)
- Processing time metrics
- Entity extraction (people, places, organizations, products)
- Key points extraction with timestamps
- Sentiment analysis
- Topic identification
- Summary generation
- SRT subtitle generation
- JSON metadata export

### Changed
- Migrated from old flat structure to modern Python project layout
- Updated to use Gemini 1.5 Flash (from 2.5 Flash preview)
- Improved error handling with proper retry logic
- Better platform-specific configurations
- Enhanced progress tracking during processing

### Fixed
- Python 3.13 compatibility issues
- Data model mapping between transcriber and retriever
- Import errors in example scripts
- Virtual environment setup issues

### Removed
- Legacy ML dependencies (temporarily removed for compatibility)
- Old file structure and scripts
- Large files from git history (WAV files, venv binaries)

## [1.0.0] - 2024-12-01

### Added
- Initial release with Google Cloud Speech-to-Text v2
- Basic YouTube video transcription
- Simple file output

## [2.2.2] - 2025-06-24

## [2.4.1] - 2024-06-25

### Fixed
- Fixed GEXF edge generation - edges now properly connect entities with predicates as attributes
- Added validation to REBEL extractor to fix malformed relationships where predicates appear as subjects/objects
- Replaced NetworkX GEXF export with custom generator for more control over format

## [2.4.0] - 2024-06-24

### Added
- GEXF format for Gephi visualization
  - Node colors by entity type
  - Node sizes by confidence scores
  - Edge attributes for relationship predicates
  - Direct import into Gephi network analysis tool

### Removed
- SRT subtitle format (use transcript.txt instead for plain text)
- VTT subtitle format (use transcript.json for structured data)

### Changed
- Focused output formats on intelligence extraction (9 formats total)
- Improved documentation for visualization tools

## [2.3.0] - 2025-06-24

### Added
- Configurable Gemini API timeout via `GEMINI_REQUEST_TIMEOUT` environment variable
- Support for processing videos up to 4 hours long (previously limited by ~15 minute timeout)
- RequestOptions timeout parameter to all Gemini API calls
- Missing `youtube-search-python` dependency
- Direct LLM relationship extraction to complement REBEL extraction
- `convert_to_chimera.py` script to generate chimera_format.json from existing outputs
- Chimera format output generated by default for all transcriptions

### Changed
- Improved relationship extraction prompts to prefer specific predicates over generic ones
- Enhanced key points extraction to capture 30-50 points for hour-long videos (was ~11)
- Expanded fact extraction to combine relationships, key points, and entity properties (up to 100 facts)
- Better fact diversity by interleaving different types of facts

### Fixed
- Timeout errors when processing videos longer than 15 minutes
- Missing dependency that prevented ClipScribe from running
- Generic relationship predicates like "mentioned" replaced with specific actions

## [2.4.2] - 2025-01-24

### Removed
- Completely removed SRT and VTT subtitle generation code
- Removed subtitle format options from CLI and configuration
- Removed all references to subtitle formats in documentation
- Removed `_generate_srt`, `_generate_vtt`, `_seconds_to_srt_time`, and `_seconds_to_vtt_time` methods

### Changed
- Focused output formats on intelligence extraction (TXT, JSON) rather than video captioning
- Updated all examples to use JSON instead of SRT for structured output

### Fixed
- Fixed missing `use_advanced_extraction` attribute error in VideoIntelligenceRetriever
- Fixed `sys` module import shadowing issue in CLI

## [2.4.3] - 2025-01-24

### Fixed
- **JSON Parsing**: Improved handling of malformed JSON from Gemini API
  - Added automatic fixes for missing commas, trailing commas, unclosed strings
  - Extracts valid portions even from broken JSON responses
  - Better error recovery and detailed logging
- **VideoTranscript Error**: Fixed "'VideoTranscript' object is not subscriptable" error
  - Now correctly uses `transcript.full_text` instead of treating object as string
- **GLiNER Truncation**: Fixed token limit issues for long transcripts
  - Added intelligent text chunking (800 chars max per chunk)
  - Chunks split at sentence boundaries to preserve context
  - Proper offset tracking for accurate entity positions
- **Visualization Path**: Fixed missing visualization script error
  - Corrected path calculation to find scripts in project root
  - `--visualize` flag now works correctly

### Changed
- **Graph Cleaning**: Made AI graph cleaner much less aggressive
  - Now keeps concepts, roles, and generic terms that provide context
  - Only removes true gibberish and meaningless fragments
  - Default behavior is to keep relationships unless clearly invalid
  - Result: Knowledge graphs now retain 80%+ of extracted data (was ~20%)

### Improved
- **Extraction Quality**: Overall extraction is now more robust and comprehensive
  - Better handling of hour-long videos
  - Richer knowledge graphs with more meaningful connections
  - More reliable processing with fewer errors

## [2.5.0] - 2025-01-24

### Added
- **GeminiPool Implementation**: Revolutionary multi-instance Gemini management
  - Manages multiple Gemini model instances for different tasks
  - Prevents token accumulation and context pollution
  - Separate instances for transcription, analysis, summary, and validation
  - Should eliminate timeout issues with long videos
  - Better resource utilization and reliability
- Created `BatchExtractor` for single-API-call extraction (not integrated yet)
- Created `StreamingExtractor` for parallel chunk processing (not integrated yet)

### Changed
- `GeminiFlashTranscriber` now uses GeminiPool instead of single model instance
- `AdvancedHybridExtractor` uses GeminiPool for LLM validation
- Better separation of concerns with dedicated model instances

### Improved
- More reliable processing of hour-long videos
- Reduced chance of hitting token limits
- Better concurrent processing capability

## [2.5.1] - 2024-06-24

### Added
- CSV export for entities and relationships - perfect for data analysis
- Markdown report generation with cost indicators and key statistics
- Dual-pass extraction option for improved entity/relationship capture
- Structured JSON output using Gemini's response_schema for reliability

### Changed
- **MAJOR**: Optimized API calls from 6 to 2-3 using combined extraction
- Raised auto-clean thresholds from 100/150 to 300/500 nodes/relationships
- Increased transcript context from 8000 to 10000 chars for better coverage
- Used official Gemini structured output for guaranteed JSON formatting

### Fixed
- Auto-clean now respects --skip-cleaning flag at higher thresholds
- Better handling of second-pass extraction for sparse results

### Performance
- 50-60% reduction in API calls through intelligent batching
- Significant cost savings while maintaining quality
- Optional second-pass extraction for comprehensive coverage

## [2.6.0] - 2025-06-24

### Added
- **Rich Progress Indicators**: Implemented a beautiful, real-time progress tracking system in the CLI using Rich.
  - Live-updating progress bars show overall completion percentage and current processing phase (e.g., downloading, transcribing, extracting).
  - Includes real-time cost tracking with color-coded alerts (🟢🟡🔴) to monitor API usage.
  - Displays elapsed time and a summary of phase timings upon completion.
- **Enhanced Interactive Reports**: Significantly upgraded the generated `report.md`.
  - **Mermaid Diagrams**: Auto-generates Mermaid diagrams for knowledge graph visualization (top 20 relationships) and entity type distribution (pie chart).
  - **Collapsible Sections**: All major sections of the report are now within `<details>` tags for easy navigation of complex reports.
  - **Visual Dashboards**: Added a "Quick Stats" dashboard with emoji-based bar charts and a relationship type distribution table.
- **Data Integrity and Consistency**:
  - **SHA256 Checksums**: The `manifest.json` now includes a SHA256 checksum for every generated file, ensuring data integrity.
  - **Fact Sourcing**: The `facts.txt` file now annotates each fact with its source (e.g., `[Relationship]`, `[Key Point]`).
  - **Consistent `entities.json`**: The entities file now includes entities from all sources (SpaCy, GLiNER, etc.) for consistency with other outputs.

### Changed
- **CLI Output**: Replaced simple status spinners with the new Rich progress system for a better user experience.
- **Documentation**: Updated `README.md` and `docs/OUTPUT_FORMATS.md` to reflect all new features and output enhancements.
- `video_retriever.py` updated to generate the new enhanced markdown format and calculate checksums.
- `advanced_hybrid_extractor.py` now tags all extracted facts with their source.

### Fixed
- Resolved console conflicts between Rich-based logging and the new progress display.
- Corrected entity statistics display to handle Pydantic model objects correctly.
- Ensured Mermaid syntax is clean and renders correctly in compliant viewers.

## [2.5.2-dev] - 2025-06-24

### Added
- **Rich Progress Indicators**: Beautiful real-time progress tracking
  - Live progress bars showing overall completion percentage
  - Phase-by-phase tracking (download, transcribe, extract, etc.)
  - Real-time cost tracking with color coding (🟢 < $0.10, 🟡 < $1.00, 🔴 > $1.00)
  - Elapsed time and estimated time remaining
  - Phase timing breakdown in completion summary
  - Extraction statistics display with entity type breakdown
- Progress utility module (`utils/progress.py`) with ClipScribeProgress class
- Simplified progress display to avoid Rich Live conflicts with logging

### Changed
- VideoIntelligenceRetriever now accepts progress_tracker parameter
- CLI passes progress tracker through to all processing components
- Progress updates throughout the processing pipeline
- Enhanced visual feedback during all processing phases

### Fixed
- Rich console conflicts between logging and progress display
- Entity statistics display now handles both dict and Pydantic objects

## [2.5.3-dev] - 2025-06-24

### Added
- **Enhanced Markdown Reports**: Reports are now significantly more interactive and insightful.
  - **Mermaid Diagrams**: Added auto-generated Mermaid diagrams for:
    - Knowledge graph visualization (top 20 relationships).
    - Entity type distribution (pie chart).
  - **Collapsible Sections**: All major sections are now collapsible for easier navigation.
  - **Visual Dashboards**:
    - "Quick Stats" dashboard with emoji-based bar charts.
    - Relationship type distribution table with percentage bars.
  - **Richer Formatting**:
    - Emoji icons for entity types (e.g., 👤, 🏢, 📍).
    - Confidence indicators for entities (🟩🟨🟥).
    - Importance indicators for key points (🔴🟡⚪).
    - Detailed file index with sizes.

### Changed
- `video_retriever.py` updated to generate the new enhanced markdown format.
- Reports now include a tip on how to view the Mermaid diagrams.

### Fixed
- Ensured Mermaid syntax is clean and renders correctly in viewers.
- Cleaned up entity names for better display in diagrams.

## [2.6.1] - 2025-06-24

### Added
- **Performance Monitoring**: Added a `--performance-report` flag to the `transcribe` command.
  - Generates a detailed JSON report in `output/performance/` containing timing for critical operations.
  - **API Timers**: Tracks the duration of all major Gemini API calls (transcription, analysis, etc.).
  - **Quality Metrics**: Records extraction quality metrics, such as the number of entities and relationships found per minute of video.
  - This provides a foundation for future optimization and for tracking the performance impact of new features.

## [2.7.0] - 2025-06-24

### Added
- **Batch Processing (`research` command)**: Implemented the `research` command to enable batch processing of multiple videos.
  - Searches YouTube for videos based on a query.
  - Processes the top N results concurrently using `asyncio.gather`.
  - Duplicates the robust processing logic from the `transcribe` command for each video.
  - Saves all outputs for each video into a dedicated subdirectory.
  - Provides a foundation for future multi-platform searches.

### Fixed
- Resolved multiple dependency and Pydantic validation issues that arose during testing, improving the robustness of the video processing pipeline.
  - Pinned `httpx` version to `0.23.3` to fix `youtube-search-python` incompatibility.
  - Corrected `VideoMetadata` model to handle float `duration` values from `yt-dlp`.
  - Fixed channel metadata parsing for new `youtube-search-python` output format.
  - Resolved `TypeError` in `research` command caused by incorrect `kwargs` passing.

## [2.8.0] - 2025-06-24

### Added
- **Interactive Web UI**: Introduced a Streamlit-based graphical interface (`app.py`) for easy, browser-based analysis. The UI includes URL input, live progress updates, and an interactive display for results and reports.
- **UI-Specific Progress Handling**: The `VideoIntelligenceRetriever` now accepts a `progress_hook` to integrate with front-end components.

## [2.9.0] - 2025-06-24

### Changed
- **Enhanced `research` command**:
  - Now supports searching specific YouTube channels by URL.
  - Added time-based filtering (`--period`) for topic searches.
  - Added sorting capabilities (`--sort-by`) for channel searches.
  - Implemented a concurrency limiter (`asyncio.Semaphore`) to prevent API rate limiting and resource overload.
  - Integrated a new `BatchProgress` dashboard for a clean, readable UI during batch processing.

## [2.8.1] - 2025-06-24

### Added
- **Comprehensive Rules System**: 19 specialized `.cursor/rules/*.mdc` files
  - Master rule (README.mdc) governing all project rules
  - Core identity rule defining project mission
  - File organization rule preventing root pollution
  - Documentation management and update rules
  - Visualization guidelines for knowledge graphs
  - Troubleshooting guide with common issues
  - Aligned with Chimera Researcher patterns

## [2.5.2-dev] - 2025-06-24

### Added
- **Rich Progress Indicators**: Beautiful real-time progress tracking
  - Live progress bars showing overall completion percentage
  - Phase-by-phase tracking (download, transcribe, extract, etc.)
  - Real-time cost tracking with color coding (🟢 < $0.10, 🟡 < $1.00, 🔴 > $1.00)
  - Elapsed time and estimated time remaining
  - Phase timing breakdown in completion summary
  - Extraction statistics display with entity type breakdown
- Progress utility module (`utils/progress.py`) with ClipScribeProgress class
- Simplified progress display to avoid Rich Live conflicts with logging

### Changed
- VideoIntelligenceRetriever now accepts progress_tracker parameter
- CLI passes progress tracker through to all processing components
- Progress updates throughout the processing pipeline
- Enhanced visual feedback during all processing phases

### Fixed
- Rich console conflicts between logging and progress display
- Entity statistics display now handles both dict and Pydantic objects

## [2.5.3-dev] - 2025-06-24

### Added
- **Enhanced Markdown Reports**: Reports are now significantly more interactive and insightful.
  - **Mermaid Diagrams**: Added auto-generated Mermaid diagrams for:
    - Knowledge graph visualization (top 20 relationships).
    - Entity type distribution (pie chart).
  - **Collapsible Sections**: All major sections are now collapsible for easier navigation.
  - **Visual Dashboards**:
    - "Quick Stats" dashboard with emoji-based bar charts.
    - Relationship type distribution table with percentage bars.
  - **Richer Formatting**:
    - Emoji icons for entity types (e.g., 👤, 🏢, 📍).
    - Confidence indicators for entities (🟩🟨🟥).
    - Importance indicators for key points (🔴🟡⚪).
    - Detailed file index with sizes.

### Changed
- `video_retriever.py` updated to generate the new enhanced markdown format.
- Reports now include a tip on how to view the Mermaid diagrams.

### Fixed
- Ensured Mermaid syntax is clean and renders correctly in viewers.
- Cleaned up entity names for better display in diagrams.

## [2.5.0] - 2024-06-24 