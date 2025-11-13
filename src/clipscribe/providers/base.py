"""Base classes and data models for ClipScribe providers.

Defines standard interfaces for transcription and intelligence providers,
ensuring consistent behavior and enabling easy testing/mocking.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    """Single transcript segment with timing and optional speaker attribution."""
    
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcript text for this segment")
    speaker: Optional[str] = Field(None, description="Speaker label if diarization enabled")
    words: Optional[List[Dict]] = Field(None, description="Word-level timing and speaker data")
    confidence: float = Field(1.0, description="Confidence score for this segment")


class TranscriptResult(BaseModel):
    """Standardized transcription output from any provider."""
    
    segments: List[TranscriptSegment] = Field(..., description="List of transcript segments")
    language: str = Field(..., description="Detected or specified language code")
    duration: float = Field(..., description="Audio duration in seconds")
    speakers: int = Field(0, description="Number of unique speakers detected")
    word_level: bool = Field(False, description="Whether word-level timing is available")
    provider: str = Field(..., description="Provider name (voxtral, whisperx-modal, whisperx-local)")
    model: str = Field(..., description="Model used for transcription")
    cost: float = Field(0.0, description="Actual processing cost in USD")
    metadata: Dict = Field(default_factory=dict, description="Provider-specific metadata")


class IntelligenceResult(BaseModel):
    """Standardized intelligence extraction output from any provider."""
    
    entities: List[Dict] = Field(..., description="Extracted entities with evidence")
    relationships: List[Dict] = Field(..., description="Relationships between entities")
    topics: List[Dict] = Field(..., description="Main topics discussed")
    key_moments: List[Dict] = Field(..., description="Significant moments with timestamps")
    sentiment: Dict = Field(..., description="Overall and per-topic sentiment")
    provider: str = Field(..., description="Provider name (grok, claude, etc.)")
    model: str = Field(..., description="Model used for extraction")
    cost: float = Field(0.0, description="Actual processing cost in USD")
    cost_breakdown: Dict = Field(
        default_factory=dict,
        description="Detailed cost breakdown (input, output, cached, savings)"
    )
    cache_stats: Dict = Field(
        default_factory=dict,
        description="Cache performance stats (hits, misses, savings)"
    )
    metadata: Dict = Field(default_factory=dict, description="Provider-specific metadata")


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class ConfigurationError(ProviderError):
    """Configuration or authentication error."""
    pass


class ProcessingError(ProviderError):
    """Processing or API error."""
    pass


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers.
    
    All transcription providers must implement this interface to ensure
    consistent behavior and enable easy swapping/testing.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'voxtral', 'whisperx-modal')."""
        pass
    
    @property
    @abstractmethod
    def supports_diarization(self) -> bool:
        """Whether this provider supports speaker diarization."""
        pass
    
    @abstractmethod
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        diarize: bool = True,
    ) -> TranscriptResult:
        """Transcribe audio file.
        
        Args:
            audio_path: Path to audio/video file
            language: Optional language code (auto-detected if None)
            diarize: Enable speaker diarization if supported
            
        Returns:
            TranscriptResult with segments, language, speakers, etc.
            
        Raises:
            ConfigurationError: If provider not properly configured
            ProcessingError: If transcription fails
            ValueError: If diarize=True but not supported
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, duration_seconds: float) -> float:
        """Estimate processing cost for given audio duration.
        
        Args:
            duration_seconds: Audio duration in seconds
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration.
        
        Returns:
            True if properly configured, False otherwise
        """
        pass


class IntelligenceProvider(ABC):
    """Abstract base class for intelligence extraction providers.
    
    All intelligence providers must implement this interface to ensure
    consistent behavior and enable easy swapping/testing.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'grok', 'claude')."""
        pass
    
    @abstractmethod
    async def extract(
        self,
        transcript: TranscriptResult,
        metadata: Optional[Dict] = None,
    ) -> IntelligenceResult:
        """Extract intelligence from transcript.
        
        Args:
            transcript: Transcription result
            metadata: Optional video/context metadata
            
        Returns:
            IntelligenceResult with entities, relationships, topics, etc.
            
        Raises:
            ConfigurationError: If provider not properly configured
            ProcessingError: If extraction fails
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, transcript_length: int) -> float:
        """Estimate processing cost for given transcript length.
        
        Args:
            transcript_length: Transcript text length in characters
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration.
        
        Returns:
            True if properly configured, False otherwise
        """
        pass

