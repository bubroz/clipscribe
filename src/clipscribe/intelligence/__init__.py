"""
Intelligence extraction and analysis modules.

Includes speaker identification, clip recommendations, entity attribution, and fact-checking.
"""

from .fact_checker import GrokFactChecker
from .speaker_identifier import SpeakerIdentifier

__all__ = ["SpeakerIdentifier", "GrokFactChecker"]
