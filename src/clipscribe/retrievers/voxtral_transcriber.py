"""
Voxtral transcription service integration.

This module provides transcription using Mistral's Voxtral models,
offering uncensored, high-accuracy transcription at 70% lower cost than Gemini.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import aiohttp
import tempfile
from dataclasses import dataclass

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


@dataclass
class VoxtralTranscriptionResult:
    """Result from Voxtral transcription."""
    text: str
    language: str
    duration: float
    cost: float
    model: str
    confidence: Optional[float] = None
    segments: Optional[List[Dict[str, Any]]] = None


class VoxtralTranscriber:
    """
    Voxtral transcription service using Mistral API.
    
    Supports multiple models:
    - voxtral-small (24B): Best accuracy (1.8% WER)
    - voxtral-mini (3B): Efficient option
    - voxtral-mini-transcribe: API-optimized variant
    """
    
    BASE_URL = "https://api.mistral.ai/v1"
    COST_PER_MINUTE = 0.001  # $0.001 per minute for all models
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "voxtral-mini-2507",  # Purpose-built for transcription, proven faster
        max_retries: int = 3,
        timeout: int = 300,
    ):
        """
        Initialize Voxtral transcriber.
        
        Args:
            api_key: Mistral API key (or from MISTRAL_API_KEY env var)
            model: Model to use (voxtral-mini-latest, voxtral-small-latest)
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("Mistral API key required (set MISTRAL_API_KEY)")
        
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Validate model choice - using correct model names from docs
        valid_models = ["voxtral-mini-latest", "voxtral-small-latest", "voxtral-mini-2507"]
        if model not in valid_models:
            logger.warning(f"Model {model} not in known list, proceeding anyway")
            # Don't fail - let the API validate
        
        logger.info(f"Initialized Voxtral transcriber with model: {model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type(Exception),
    )
    async def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> VoxtralTranscriptionResult:
        """
        Transcribe audio file using Voxtral.
        
        Args:
            audio_path: Path to audio file
            language: Optional language hint (auto-detected if not provided)
            prompt: Optional context prompt for better accuracy
            
        Returns:
            VoxtralTranscriptionResult with transcript and metadata
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Get audio duration for cost calculation
        duration = await self._get_audio_duration(audio_path)
        
        logger.info(f"Transcribing {duration:.1f} seconds ({duration/60:.1f} min) with Voxtral {self.model}")
        
        async with aiohttp.ClientSession() as session:
            # Option 1: Upload file first, then get signed URL
            file_id = await self._upload_file(session, audio_path)
            
            try:
                # Get signed URL for the uploaded file
                signed_url = await self._get_signed_url(session, file_id)
                
                # Transcribe using the signed URL
                result = await self._transcribe_with_url(session, signed_url, language, prompt)
                
                # Calculate cost
                cost = (duration / 60) * self.COST_PER_MINUTE
                
                return VoxtralTranscriptionResult(
                    text=result["text"],
                    language=result.get("language", language or "en"),
                    duration=duration,
                    cost=cost,
                    model=self.model,
                    confidence=result.get("confidence"),
                    segments=result.get("segments"),
                )
                
            finally:
                # Clean up uploaded file
                await self._delete_file(session, file_id)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _upload_file(self, session: aiohttp.ClientSession, file_path: Path) -> str:
        """Upload audio file to Mistral API with retry logic."""
        url = f"{self.BASE_URL}/files"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # Prepare multipart upload
        data = aiohttp.FormData()
        data.add_field(
            "file",
            open(file_path, "rb"),
            filename=file_path.name,
            content_type=self._get_mime_type(file_path),
        )
        data.add_field("purpose", "audio")
        
        async with session.post(
            url, 
            headers=headers, 
            data=data,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"File upload failed: {response.status} - {error_text}")
            
            result = await response.json()
            file_id = result["id"]
            logger.debug(f"Uploaded file: {file_id}")
            return file_id
    
    async def _get_signed_url(self, session: aiohttp.ClientSession, file_id: str) -> str:
        """Get signed URL for uploaded file."""
        url = f"{self.BASE_URL}/files/{file_id}/url"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        
        # Request signed URL with 24 hour expiry
        params = {"expiry": "24"}
        
        async with session.get(
            url,
            headers=headers,
            params=params,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get signed URL: {response.status} - {error_text}")
            
            result = await response.json()
            signed_url = result.get("url")
            logger.debug(f"Got signed URL for file {file_id}")
            return signed_url
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _transcribe_with_url(
        self,
        session: aiohttp.ClientSession,
        file_url: str,
        language: Optional[str],
        prompt: Optional[str],
    ) -> Dict[str, Any]:
        """Transcribe audio using signed URL with retry logic."""
        url = f"{self.BASE_URL}/audio/transcriptions"
        headers = {
            "x-api-key": self.api_key,  # Use x-api-key header for transcription endpoint
        }
        
        # Use FormData for multipart/form-data request
        data = aiohttp.FormData()
        data.add_field("model", self.model)
        data.add_field("file_url", file_url)  # Use the signed URL
        
        if language:
            data.add_field("language", language)
        
        if prompt:
            data.add_field("prompt", prompt)
        
        async with session.post(
            url,
            headers=headers,
            data=data,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Transcription failed: {response.status} - {error_text}")
            
            result = await response.json()
            logger.debug(f"Transcription complete: {len(result.get('text', ''))} chars")
            return result
    
    async def _delete_file(self, session: aiohttp.ClientSession, file_id: str):
        """Delete uploaded file from Mistral."""
        url = f"{self.BASE_URL}/files/{file_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        try:
            async with session.delete(url, headers=headers) as response:
                # Mistral returns 200 instead of 204 for successful deletion
                if response.status not in [200, 204]:
                    logger.warning(f"Failed to delete file {file_id}: {response.status}")
        except Exception as e:
            logger.warning(f"Error deleting file {file_id}: {e}")
    
    async def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration in seconds using ffprobe."""
        import subprocess
        
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()
            duration = float(stdout.decode().strip())
            return duration
        except Exception as e:
            logger.warning(f"Failed to get duration, estimating: {e}")
            # Estimate based on file size (rough approximation)
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            return file_size_mb * 60  # Rough estimate: 1MB = 1 minute
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for audio file."""
        suffix = file_path.suffix.lower()
        mime_types = {
            ".mp3": "audio/mpeg",
            ".mp4": "audio/mp4",
            ".m4a": "audio/mp4",
            ".wav": "audio/wav",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
            ".webm": "audio/webm",
        }
        return mime_types.get(suffix, "audio/mpeg")
    
    async def transcribe_with_fallback(
        self,
        audio_path: str,
        gemini_transcriber: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Smart fallback transcription strategy.
        
        Try Gemini first for non-sensitive content, fall back to Voxtral if blocked.
        
        Args:
            audio_path: Path to audio file
            gemini_transcriber: Optional Gemini transcriber instance
            
        Returns:
            Transcription result dictionary
        """
        # Phase 1: Try Gemini first if available
        if gemini_transcriber:
            try:
                logger.info("Attempting Gemini transcription first...")
                result = await gemini_transcriber.transcribe_audio(audio_path)
                
                # Check for safety block
                if hasattr(result, "finish_reason") and result.finish_reason != 2:
                    logger.info("Gemini transcription successful")
                    return result
                else:
                    logger.warning("Gemini blocked content, falling back to Voxtral")
            except Exception as e:
                logger.warning(f"Gemini failed: {e}, falling back to Voxtral")
        
        # Phase 2: Use Voxtral for blocked or failed content
        logger.info("Using Voxtral for uncensored transcription")
        voxtral_result = await self.transcribe_audio(audio_path)
        
        # Convert to format compatible with existing code
        return {
            "transcript": voxtral_result.text,
            "language": voxtral_result.language,
            "duration": voxtral_result.duration,
            "processing_cost": voxtral_result.cost,
            "model": f"voxtral/{voxtral_result.model}",
            "segments": voxtral_result.segments,
        }


async def test_voxtral_transcription():
    """Test Voxtral transcription with a sample file."""
    # This would be called with a test audio file
    transcriber = VoxtralTranscriber(model="voxtral-small")
    
    # Create a test audio file (you'd use a real file in practice)
    test_audio = "/path/to/test/audio.mp3"
    
    try:
        result = await transcriber.transcribe_audio(test_audio)
        print(f"Transcription successful!")
        print(f"Text: {result.text[:200]}...")
        print(f"Language: {result.language}")
        print(f"Duration: {result.duration:.1f} seconds")
        print(f"Cost: ${result.cost:.4f}")
        print(f"Model: {result.model}")
    except Exception as e:
        print(f"Transcription failed: {e}")


if __name__ == "__main__":
    # Test the transcriber
    asyncio.run(test_voxtral_transcription())
