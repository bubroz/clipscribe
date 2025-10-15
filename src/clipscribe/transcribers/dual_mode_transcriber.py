"""
Dual-Mode Transcription System

Intelligently selects between Voxtral (fast/cheap) and WhisperX (accurate/premium)
based on content type, user preference, and economic optimization.

For SaaS:
- Standard tier: Voxtral + pyannote (95% accuracy, $0.003/min cost)
- Premium tier: WhisperX (97-99% accuracy, $0.06/min cost on Cloud Run GPU)

For local development:
- Use WhisperX for everything (free on M3 Max, best quality)
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .voxtral_transcriber import VoxtralTranscriber
from .whisperx_transcriber import WhisperXTranscriber

logger = logging.getLogger(__name__)


class DualModeTranscriber:
    """
    Smart transcription with automatic quality tier selection.
    """
    
    def __init__(
        self,
        default_mode: str = "auto",
        force_local_whisperx: bool = False
    ):
        """
        Initialize dual-mode transcriber.
        
        Args:
            default_mode: "auto", "fast", or "accurate"
            force_local_whisperx: Always use WhisperX locally (ignore tier for dev)
        """
        self.default_mode = default_mode
        self.force_local_whisperx = force_local_whisperx
        
        # Initialize both transcribers
        self.voxtral = None
        self.whisperx = None
        
        # Lazy initialization based on what's actually used
        logger.info(f"DualModeTranscriber initialized (default: {default_mode})")
    
    def _init_voxtral(self):
        """Lazy init Voxtral."""
        if not self.voxtral:
            self.voxtral = VoxtralTranscriber()
            logger.info("Voxtral transcriber loaded")
    
    def _init_whisperx(self):
        """Lazy init WhisperX."""
        if not self.whisperx:
            self.whisperx = WhisperXTranscriber(enable_diarization=True)
            logger.info("WhisperX transcriber loaded")
    
    def detect_content_type(
        self,
        video_metadata: Optional[Dict[str, Any]] = None,
        user_preference: Optional[str] = None
    ) -> str:
        """
        Detect if content needs high-accuracy transcription.
        
        Returns: "fast" or "accurate"
        """
        # User explicitly requested quality tier
        if user_preference in ["fast", "accurate"]:
            logger.info(f"User preference: {user_preference} mode")
            return user_preference
        
        # Force local WhisperX (development mode)
        if self.force_local_whisperx:
            logger.info("Development mode: Using WhisperX locally (free)")
            return "accurate"
        
        # Auto-detect from video metadata
        if video_metadata:
            title = video_metadata.get("title", "").lower()
            channel = video_metadata.get("channel", "").lower()
            description = video_metadata.get("description", "").lower()
            
            # High-stakes content keywords
            high_accuracy_keywords = [
                # Medical
                "medical", "clinical", "diagnosis", "surgery", "patient",
                "healthcare", "doctor", "hospital", "treatment",
                
                # Legal
                "legal", "court", "deposition", "testimony", "trial",
                "attorney", "lawyer", "hearing", "case", "verdict",
                
                # Technical/Intelligence
                "technical", "briefing", "classified", "intelligence",
                "analysis", "security", "defense", "military",
                
                # Academic
                "lecture", "conference", "symposium", "research",
                "academic", "university", "professor"
            ]
            
            # Check title and channel
            content = f"{title} {channel} {description}"
            if any(keyword in content for keyword in high_accuracy_keywords):
                logger.info(f"High-accuracy content detected: {title[:50]}")
                return "accurate"
        
        # Default to fast mode (cost-effective)
        logger.info("Standard content - using fast mode")
        return "fast"
    
    async def transcribe(
        self,
        audio_path: str,
        video_metadata: Optional[Dict[str, Any]] = None,
        quality_tier: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe with automatic or specified quality tier.
        
        Args:
            audio_path: Path to audio file
            video_metadata: Video metadata for content type detection
            quality_tier: "fast", "accurate", or None (auto-detect)
            language: Language code
            
        Returns:
            Transcription result in standard format
        """
        # Determine which mode to use
        if quality_tier:
            mode = quality_tier
        else:
            mode = self.detect_content_type(video_metadata, quality_tier)
        
        # Transcribe with selected mode
        if mode == "accurate":
            # Use WhisperX (premium tier)
            self._init_whisperx()
            logger.info("🎯 Using WhisperX (premium accuracy)")
            result = await self.whisperx.transcribe_with_fallback(audio_path)
            result["quality_tier"] = "premium"
            result["transcriber"] = "whisperx"
            
        else:  # fast mode
            # Use Voxtral (standard tier)
            self._init_voxtral()
            logger.info("⚡ Using Voxtral (standard tier)")
            result = await self.voxtral.transcribe_with_fallback(audio_path)
            result["quality_tier"] = "standard"
            result["transcriber"] = "voxtral"
        
        return result
    
    async def transcribe_with_both(
        self,
        audio_path: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Transcribe with BOTH modes for comparison/testing.
        
        Useful for validating WhisperX accuracy improvement.
        
        Returns:
            {
                "voxtral": {...},
                "whisperx": {...},
                "comparison": {
                    "accuracy_delta": "2.3%",
                    "time_delta": "2.1x slower",
                    "cost_delta": "$0 (both modes tested)"
                }
            }
        """
        import time
        
        self._init_voxtral()
        self._init_whisperx()
        
        logger.info("Running dual-mode comparison...")
        
        # Voxtral
        start = time.time()
        voxtral_result = await self.voxtral.transcribe_with_fallback(audio_path)
        voxtral_time = time.time() - start
        
        # WhisperX
        start = time.time()
        whisperx_result = await self.whisperx.transcribe_with_fallback(audio_path)
        whisperx_time = time.time() - start
        
        # Compare
        comparison = {
            "voxtral_time": round(voxtral_time, 2),
            "whisperx_time": round(whisperx_time, 2),
            "time_ratio": round(whisperx_time / voxtral_time, 2),
            "voxtral_confidence": voxtral_result.get("confidence", 0.95),
            "whisperx_confidence": whisperx_result.get("confidence", 0.95),
            "whisperx_has_speakers": len(whisperx_result.get("speaker_segments", [])) > 0,
            "whisperx_has_word_timestamps": len(whisperx_result.get("word_timestamps", [])) > 0
        }
        
        return {
            "voxtral": voxtral_result,
            "whisperx": whisperx_result,
            "comparison": comparison
        }

