"""
Transcription engines for ClipScribe.

Dual-mode architecture:
- Voxtral: Fast, cost-effective (95% accuracy)
- WhisperX: Premium, medical/legal grade (97-99% accuracy)
"""

from .dual_mode_transcriber import DualModeTranscriber
from .voxtral_transcriber import VoxtralTranscriber
from .whisperx_transcriber import WhisperXTranscriber

__all__ = [
    "VoxtralTranscriber",
    "WhisperXTranscriber",
    "DualModeTranscriber",
]
