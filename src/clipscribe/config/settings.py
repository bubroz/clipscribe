"""ClipScribe configuration settings.

Uses Pydantic BaseSettings for environment variable management and validation.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from dotenv import load_dotenv
from enum import Enum

# Load environment variables from .env file
load_dotenv()


class VideoRetentionPolicy(str, Enum):
    """Video retention policies for source material management."""
    DELETE = "delete"  # Delete source video after processing
    KEEP_PROCESSED = "keep_processed"  # Keep only processed video outputs
    KEEP_ALL = "keep_all"  # Keep source video and all outputs


class TemporalIntelligenceLevel(str, Enum):
    """Levels of temporal intelligence extraction."""
    STANDARD = "standard"  # Basic temporal intelligence (current v2.16.0)
    ENHANCED = "enhanced"  # Enhanced temporal intelligence (v2.17.0)
    MAXIMUM = "maximum"  # Maximum temporal intelligence with all visual cues


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'  # Ignore extra fields from environment
    )
    
    # API Keys
    google_api_key: str = Field(
        default=os.getenv("GOOGLE_API_KEY", ""),
        description="Google API key for Gemini 2.5 Flash"
    )
    
    # Vertex AI Configuration
    use_vertex_ai: bool = Field(default=False)
    vertex_ai_project: str = Field(
        default=os.getenv("VERTEX_AI_PROJECT", os.getenv("VERTEX_AI_PROJECT_ID", "")),
        description="GCP project ID for Vertex AI (env: VERTEX_AI_PROJECT)"
    )
    vertex_ai_location: str = Field(
        default=os.getenv("VERTEX_AI_LOCATION", "us-central1"),
        description="Vertex AI location/region (env: VERTEX_AI_LOCATION)"
    )
    vertex_ai_staging_bucket: Optional[str] = Field(
        default=os.getenv("VERTEX_AI_STAGING_BUCKET", None),
        description="Optional Vertex AI staging bucket (gs://...)"
    )
    
    # AI Model Configuration
    ai_model: str = Field(
        default="google_genai:gemini-2.5-flash",
        description="Default AI model for transcription"
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="AI model temperature"
    )
    
    # Application Settings
    output_dir: Path = Field(
        default=Path("output"),
        description="Default output directory for transcripts"
    )
    default_language: str = Field(
        default="en",
        description="Default transcription language"
    )
    max_video_duration: int = Field(
        default=14400,  # 4 hours in seconds
        description="Maximum video duration to process (seconds)"
    )
    
    # === v2.17.0 ENHANCED TEMPORAL INTELLIGENCE SETTINGS ===
    
    # Temporal Intelligence Configuration
    temporal_intelligence_level: TemporalIntelligenceLevel = Field(
        default=TemporalIntelligenceLevel.ENHANCED,
        description="Level of temporal intelligence extraction"
    )
    extract_visual_temporal_cues: bool = Field(
        default=True,
        description="Extract temporal intelligence from visual cues (charts, graphs, timelines)"
    )
    extract_audio_temporal_cues: bool = Field(
        default=True,
        description="Extract temporal intelligence from audio/speech patterns"
    )
    temporal_intelligence_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for temporal intelligence extraction"
    )
    enable_cross_video_temporal_correlation: bool = Field(
        default=True,
        description="Enable temporal correlation across multiple videos"
    )
    
    # Video Retention System
    video_retention_policy: VideoRetentionPolicy = Field(
        default=VideoRetentionPolicy.DELETE,
        description="Policy for retaining source video files"
    )
    video_archive_directory: Path = Field(
        default=Path("output/video_archive"),
        description="Directory for archived video files"
    )
    retention_cost_threshold: float = Field(
        default=5.0,
        description="USD threshold for automatic retention decisions"
    )
    enable_retention_cost_optimization: bool = Field(
        default=True,
        description="Enable cost-based retention optimization"
    )
    max_archive_size_gb: int = Field(
        default=50,
        description="Maximum archive size in GB before cleanup"
    )
    
    # Timeline Building Configuration
    enable_timeline_synthesis: bool = Field(
        default=True,
        description="Enable timeline building across videos"
    )
    timeline_correlation_window_hours: int = Field(
        default=168,  # 1 week
        description="Time window for correlating events across videos (hours)"
    )
    timeline_confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for timeline event correlation"
    )
    max_timeline_events_per_video: int = Field(
        default=50,
        description="Maximum temporal events to extract per video"
    )
    enable_timeline_date_extraction: bool = Field(
        default=True,
        description="Enable LLM-based date extraction from content"
    )
    
    # === ENHANCED COST MANAGEMENT ===
    
    # Cost Tracking & Optimization
    enable_cost_tracking: bool = Field(
        default=True,
        description="Track AI API costs"
    )
    cost_warning_threshold: float = Field(
        default=1.0,
        description="Warn when single operation exceeds this cost (USD)"
    )
    enhanced_temporal_cost_multiplier: float = Field(
        default=1.15,
        description="Cost multiplier for enhanced temporal intelligence (1.12-1.20)"
    )
    daily_cost_limit: Optional[float] = Field(
        default=None,
        description="Daily spending limit in USD (None = no limit)"
    )
    monthly_cost_limit: Optional[float] = Field(
        default=None,
        description="Monthly spending limit in USD (None = no limit)"
    )
    cost_tracking_granularity: str = Field(
        default="operation",
        description="Cost tracking granularity: operation, video, collection"
    )
    
    # Transcription Settings
    include_timestamps_default: bool = Field(
        default=False,
        description="Include timestamps by default"
    )
    enhance_transcript_default: bool = Field(
        default=False,
        description="Enable AI enhancement by default"
    )
    default_output_formats: List[str] = Field(
        default=["txt"],
        description="Default output formats"
    )
    
    # Performance Settings
    concurrent_downloads: int = Field(default=10)  # Increased for enterprise
    chunk_size: int = Field(
        default=180,  # 3 minutes (smaller chunks improve upload reliability)
        description="Chunk size in seconds for processing (used for large videos)"
    )
    
    # Gemini API Settings
    gemini_request_timeout: int = Field(
        default=14400,  # 4 hours
        description="Timeout for Gemini API requests in seconds"
    )
    gemini_concurrent_requests: int = Field(
        default=3,  # Conservative default to avoid rate limits/connection resets
        description="Maximum number of concurrent requests to Gemini API"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_dir: Path = Field(
        default=Path("logs"),
        description="Directory for log files"
    )
    
    # yt-dlp Settings
    ytdlp_cookies_file: Optional[Path] = Field(
        default=None,
        description="Path to cookies file for yt-dlp"
    )
    ytdlp_proxy: Optional[str] = Field(
        default=None,
        description="Proxy URL for yt-dlp"
    )

    @field_validator("google_api_key")
    def validate_api_key(cls, v: str, values: "ValidationInfo") -> str:
        """Validate Google API key is set, but only if not using Vertex AI."""
        if not values.data.get("use_vertex_ai") and not v:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required when not using Vertex AI. "
                "Get one at: https://makersuite.google.com/app/apikey"
            )
        return v
    
    @field_validator("output_dir", "log_dir", "video_archive_directory", mode="before")
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("default_output_formats")
    def validate_output_formats(cls, v: List[str]) -> List[str]:
        """Validate output formats."""
        valid_formats = {"txt", "json"}
        for format in v:
            if format not in valid_formats:
                raise ValueError(f"Invalid output format: {format}")
        return v
    
    def get_gemini_config(self) -> dict:
        """Get Gemini-specific configuration."""
        return {
            "api_key": self.google_api_key,
            "model": self.ai_model,
            "temperature": self.temperature,
            "safety_settings": {
                "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
            }
        }
    
    def get_temporal_intelligence_config(self) -> dict:
        """Get temporal intelligence-specific configuration."""
        return {
            "level": self.temporal_intelligence_level,
            "extract_visual_cues": self.extract_visual_temporal_cues,
            "extract_audio_cues": self.extract_audio_temporal_cues,
            "confidence_threshold": self.temporal_intelligence_confidence_threshold,
            "cross_video_correlation": self.enable_cross_video_temporal_correlation,
            "cost_multiplier": self.enhanced_temporal_cost_multiplier
        }
    
    def get_video_retention_config(self) -> dict:
        """Get video retention system configuration."""
        return {
            "policy": self.video_retention_policy,
            "archive_directory": self.video_archive_directory,
            "cost_threshold": self.retention_cost_threshold,
            "cost_optimization": self.enable_retention_cost_optimization,
            "max_archive_size_gb": self.max_archive_size_gb
        }
    
    def get_timeline_config(self) -> dict:
        """Get timeline building configuration."""
        return {
            "enable_synthesis": self.enable_timeline_synthesis,
            "correlation_window_hours": self.timeline_correlation_window_hours,
            "confidence_threshold": self.timeline_confidence_threshold,
            "max_events_per_video": self.max_timeline_events_per_video,
            "enable_date_extraction": self.enable_timeline_date_extraction
        }
    
    def estimate_cost(self, audio_duration_seconds: int, 
                     temporal_intelligence_level: Optional[TemporalIntelligenceLevel] = None) -> float:
        """Estimate transcription cost based on audio duration and temporal intelligence level.
        
        Gemini 2.5 Flash pricing (as of 2025):
        - Audio input: $0.0001875 per 1,000 tokens
        - Video input: $0.001875 per 1,000 tokens (10x audio)
        - ~25 tokens per second of audio
        - Enhanced temporal intelligence adds 12-20% cost
        """
        level = temporal_intelligence_level or self.temporal_intelligence_level
        
        # Base estimation
        input_tokens = (audio_duration_seconds * 25)  # ~25 tokens per second
        output_tokens = input_tokens * 0.15  # Output is typically 15% of input
        
        # Determine if we're using video processing for enhanced temporal intelligence
        if level == TemporalIntelligenceLevel.ENHANCED:
            # Enhanced uses video processing for visual temporal cues
            input_cost = (input_tokens / 1000) * 0.001875  # Video rate
            cost_multiplier = self.enhanced_temporal_cost_multiplier
        elif level == TemporalIntelligenceLevel.MAXIMUM:
            # Maximum uses video processing with higher analysis
            input_cost = (input_tokens / 1000) * 0.001875  # Video rate
            cost_multiplier = self.enhanced_temporal_cost_multiplier * 1.2
        else:
            # Standard uses audio processing
            input_cost = (input_tokens / 1000) * 0.0001875  # Audio rate
            cost_multiplier = 1.0
        
        output_cost = (output_tokens / 1000) * 0.00075
        base_cost = input_cost + output_cost
        
        return base_cost * cost_multiplier
    
    def estimate_retention_cost(self, video_path: Path, processing_result: Optional[Dict] = None) -> Dict[str, float]:
        """Estimate costs for different retention policies."""
        if not video_path.exists():
            return {"storage": 0.0, "reprocessing": 0.0}
        
        # Storage cost estimation (very rough - $0.023/GB/month for standard storage)
        file_size_gb = video_path.stat().st_size / (1024**3)
        monthly_storage_cost = file_size_gb * 0.023
        
        # Reprocessing cost estimation
        if processing_result and "duration" in processing_result:
            duration = processing_result["duration"]
        else:
            # Rough estimation - 1GB ≈ 15 minutes for typical video
            duration = file_size_gb * 15 * 60
        
        reprocessing_cost = self.estimate_cost(duration)
        
        return {
            "storage_monthly": monthly_storage_cost,
            "storage_yearly": monthly_storage_cost * 12,
            "reprocessing": reprocessing_cost,
            "breakeven_months": reprocessing_cost / monthly_storage_cost if monthly_storage_cost > 0 else float('inf')
        }


# Create global settings instance
try:
    settings = Settings()
except Exception as e:
    # Fallback for when no API key is set (like in Streamlit without env vars)
    import warnings
    warnings.warn(f"Settings validation failed: {e}. Using fallback settings.")
    
    # Create a minimal settings object for UI purposes
    class FallbackSettings:
        google_api_key = ""
        ai_model = "google_genai:gemini-2.5-flash"
        temperature = 0.3
        output_dir = Path("output")
        default_language = "en"
        max_video_duration = 14400
        include_timestamps_default = False
        enhance_transcript_default = False
        default_output_formats = ["txt"]
        concurrent_downloads = 10
        chunk_size = 600
        gemini_request_timeout = 14400
        enable_cost_tracking = True
        cost_warning_threshold = 1.0
        log_level = "INFO"
        log_dir = Path("logs")
        ytdlp_cookies_file = None
        ytdlp_proxy = None
        
        # v2.17.0 Enhanced settings with defaults
        temporal_intelligence_level = TemporalIntelligenceLevel.ENHANCED
        extract_visual_temporal_cues = True
        extract_audio_temporal_cues = True
        temporal_intelligence_confidence_threshold = 0.7
        enable_cross_video_temporal_correlation = True
        video_retention_policy = VideoRetentionPolicy.DELETE
        video_archive_directory = Path("output/video_archive")
        retention_cost_threshold = 5.0
        enable_retention_cost_optimization = True
        max_archive_size_gb = 50
        enable_timeline_synthesis = True
        timeline_correlation_window_hours = 168
        timeline_confidence_threshold = 0.8
        max_timeline_events_per_video = 50
        enable_timeline_date_extraction = True
        enhanced_temporal_cost_multiplier = 1.15
        daily_cost_limit = None
        monthly_cost_limit = None
        cost_tracking_granularity = "operation"
        
        def get_gemini_config(self):
            return {
                "api_key": self.google_api_key,
                "model": self.ai_model,
                "temperature": self.temperature,
                "safety_settings": {
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
                }
            }
        
        def get_temporal_intelligence_config(self):
            return {
                "level": self.temporal_intelligence_level,
                "extract_visual_cues": self.extract_visual_temporal_cues,
                "extract_audio_cues": self.extract_audio_temporal_cues,
                "confidence_threshold": self.temporal_intelligence_confidence_threshold,
                "cross_video_correlation": self.enable_cross_video_temporal_correlation,
                "cost_multiplier": self.enhanced_temporal_cost_multiplier
            }
        
        def get_video_retention_config(self):
            return {
                "policy": self.video_retention_policy,
                "archive_directory": self.video_archive_directory,
                "cost_threshold": self.retention_cost_threshold,
                "cost_optimization": self.enable_retention_cost_optimization,
                "max_archive_size_gb": self.max_archive_size_gb
            }
        
        def get_timeline_config(self):
            return {
                "enable_synthesis": self.enable_timeline_synthesis,
                "correlation_window_hours": self.timeline_correlation_window_hours,
                "confidence_threshold": self.timeline_confidence_threshold,
                "max_events_per_video": self.max_timeline_events_per_video,
                "enable_date_extraction": self.enable_timeline_date_extraction
            }
        
        def estimate_cost(self, audio_duration_seconds: int, temporal_intelligence_level=None):
            level = temporal_intelligence_level or self.temporal_intelligence_level
            input_tokens = (audio_duration_seconds * 25)
            output_tokens = input_tokens * 0.15
            
            if level == TemporalIntelligenceLevel.ENHANCED:
                input_cost = (input_tokens / 1000) * 0.001875
                cost_multiplier = self.enhanced_temporal_cost_multiplier
            elif level == TemporalIntelligenceLevel.MAXIMUM:
                input_cost = (input_tokens / 1000) * 0.001875
                cost_multiplier = self.enhanced_temporal_cost_multiplier * 1.2
            else:
                input_cost = (input_tokens / 1000) * 0.0001875
                cost_multiplier = 1.0
            
            output_cost = (output_tokens / 1000) * 0.00075
            base_cost = input_cost + output_cost
            return base_cost * cost_multiplier
        
        def estimate_retention_cost(self, video_path, processing_result=None):
            return {"storage_monthly": 0.0, "storage_yearly": 0.0, "reprocessing": 0.0, "breakeven_months": float('inf')}
    
    settings = FallbackSettings()