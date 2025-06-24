"""ClipScribe configuration settings.

Uses Pydantic BaseSettings for environment variable management and validation.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Keys
    google_api_key: str = Field(
        default=os.getenv("GOOGLE_API_KEY", ""),
        description="Google API key for Gemini 2.5 Flash"
    )
    
    # AI Model Configuration
    ai_model: str = Field(
        default="google_genai:gemini-1.5-flash",
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
    concurrent_downloads: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum concurrent video downloads"
    )
    chunk_size: int = Field(
        default=600,  # 10 minutes
        description="Audio chunk size in seconds for processing"
    )
    
    # Cost Tracking
    enable_cost_tracking: bool = Field(
        default=True,
        description="Track AI API costs"
    )
    cost_warning_threshold: float = Field(
        default=1.0,
        description="Warn when single operation exceeds this cost (USD)"
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
    def validate_api_key(cls, v: str) -> str:
        """Validate Google API key is set."""
        if not v:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required. "
                "Get one at: https://makersuite.google.com/app/apikey"
            )
        return v
    
    @field_validator("output_dir", "log_dir", mode="before")
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("default_output_formats")
    def validate_output_formats(cls, v: List[str]) -> List[str]:
        """Validate output formats."""
        valid_formats = {"txt", "json", "srt", "vtt"}
        for format in v:
            if format not in valid_formats:
                raise ValueError(f"Invalid output format: {format}")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
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
    
    def estimate_cost(self, audio_duration_seconds: int) -> float:
        """Estimate transcription cost based on audio duration.
        
        Gemini 2.5 Flash pricing (as of 2025):
        - Audio input: $0.0001875 per 1,000 tokens
        - ~25 tokens per second of audio
        - Output: ~$0.00075 per 1,000 tokens
        """
        # Rough estimation
        input_tokens = (audio_duration_seconds * 25)  # ~25 tokens per second
        output_tokens = input_tokens * 0.15  # Output is typically 15% of input for transcription
        
        input_cost = (input_tokens / 1000) * 0.0001875
        output_cost = (output_tokens / 1000) * 0.00075
        
        return input_cost + output_cost 