"""
Transcription engines for ClipScribe.

Provider-based architecture (v3.0.0):
- Voxtral: Fast API transcription, no speakers ($0.001/min)
- WhisperX: GPU transcription with speaker diarization (Modal or Local M3 Max)
"""

from .voxtral_transcriber import VoxtralTranscriber
from .whisperx_transcriber import WhisperXTranscriber

__all__ = [
    "VoxtralTranscriber",
    "WhisperXTranscriber",
]
