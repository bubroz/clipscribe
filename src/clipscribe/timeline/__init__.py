"""Timeline Intelligence v2.0 - Comprehensive Temporal Intelligence Package.

Timeline Intelligence v2.0 represents a revolutionary advancement in video temporal analysis,
addressing the fundamental flaws of v1.0 through breakthrough yt-dlp integration:

CRITICAL FIXES DELIVERED:
✅ 44-duplicate crisis: EventDeduplicator eliminates entity combination explosion
✅ Wrong date crisis: ContentDateExtractor extracts dates from content, never video publish dates
✅ No temporal intelligence: TemporalExtractorV2 leverages yt-dlp's 61 temporal features
✅ Entity explosion: Intelligent consolidation instead of separate events per entity combination

BREAKTHROUGH CAPABILITIES:
🚀 yt-dlp Integration: Chapter-aware extraction with sub-second precision
📊 Quality Filtering: Comprehensive validation and noise elimination  
🎬 Chapter Segmentation: Intelligent content boundaries using yt-dlp chapters
🔗 Cross-Video Synthesis: Multi-video timeline correlation and synthesis

ARCHITECTURAL TRANSFORMATION:
- v1.0: Blind transcript splitting → broken timeline with duplicates and wrong dates
- v2.0: Intelligent yt-dlp-powered extraction → meaningful temporal intelligence

Expected Results:
- Transform 82 broken events → ~40 unique, accurate temporal events
- 95%+ correct dates extracted from content (not video publish dates)
- Sub-second timestamp precision using yt-dlp word-level timing
- Chapter-aware event contextualization with SponsorBlock filtering

Timeline Intelligence v2.0: From broken to brilliant temporal intelligence :-)
"""

# Core Models
from .models import (
    TemporalEvent,
    ExtractedDate,
    ConsolidatedTimeline,
    TimelineQualityMetrics,
    ChapterSegment,
    DatePrecision,
    EventType,
    ValidationStatus
)

# Enhanced Temporal Extraction (Core v2.0 Component)
from .temporal_extractor_v2 import (
    TemporalExtractorV2,
    TemporalExtractionContext
)

# Event Deduplication (Fixes 44-duplicate Crisis)
from .event_deduplicator import (
    EventDeduplicator
)

# Content Date Extraction (Fixes Wrong Date Crisis)
from .date_extractor import (
    ContentDateExtractor
)

# Quality Filtering (Ensures High-Quality Output)
from .quality_filter import (
    TimelineQualityFilter
)

# Chapter Segmentation (Leverages yt-dlp Chapter Intelligence)
from .chapter_segmenter import (
    ChapterSegmenter,
    SegmentationStrategy
)

# Cross-Video Synthesis (Multi-Video Timeline Building)
from .cross_video_synthesizer import (
    CrossVideoSynthesizer,
    SynthesisStrategy
)

# Performance Optimization (Component 5)
from .performance_optimizer import (
    TimelineV2PerformanceOptimizer,
    PerformanceMetrics,
    BatchProcessingConfig
)

# Package metadata
__version__ = "2.0.0"
__description__ = "Timeline Intelligence v2.0 - Revolutionary temporal intelligence with yt-dlp integration"

# Public API - Only what actually exists
__all__ = [
    # Core Models
    "TemporalEvent",
    "ExtractedDate", 
    "ConsolidatedTimeline",
    "TimelineQualityMetrics",
    "ChapterSegment",
    "DatePrecision",
    "EventType",
    "ValidationStatus",
    
    # Core Components (Timeline v2.0)
    "TemporalExtractorV2",           # 🚀 Heart of v2.0 - yt-dlp temporal intelligence
    "EventDeduplicator",             # 🔧 Fixes 44-duplicate crisis
    "ContentDateExtractor",          # 📅 Fixes wrong date crisis  
    "TimelineQualityFilter",         # ✨ Ensures high-quality output
    "ChapterSegmenter",              # 🎬 yt-dlp chapter intelligence
    "CrossVideoSynthesizer",         # 🔗 Multi-video timeline building
    
    # Performance Optimization (Component 5)
    "TimelineV2PerformanceOptimizer", # ⚡ Large collection optimization
    "PerformanceMetrics",            # 📊 Performance tracking
    "BatchProcessingConfig",         # ⚙️ Optimization configuration
    
    # Supporting Classes
    "TemporalExtractionContext",
    "SegmentationStrategy", 
    "SynthesisStrategy",
] 