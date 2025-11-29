"""Shared fixtures for provider tests."""

import pytest

from clipscribe.providers.base import IntelligenceResult, TranscriptResult, TranscriptSegment


@pytest.fixture
def mock_transcript_result():
    """Mock transcript result for testing intelligence providers."""
    return TranscriptResult(
        segments=[
            TranscriptSegment(
                start=0.0,
                end=5.0,
                text="Hello, this is a test transcript.",
                speaker="SPEAKER_01",
            ),
            TranscriptSegment(
                start=5.0,
                end=10.0,
                text="This is speaker two speaking.",
                speaker="SPEAKER_02",
            ),
        ],
        language="en",
        duration=10.0,
        speakers=2,
        word_level=True,
        provider="test",
        model="test-model",
        cost=0.0,
    )


@pytest.fixture
def mock_intelligence_result():
    """Mock intelligence result for testing."""
    return IntelligenceResult(
        entities=[
            {"name": "Test Entity", "type": "PERSON", "confidence": 0.9, "evidence": "test quote"}
        ],
        relationships=[
            {
                "subject": "A",
                "predicate": "knows",
                "object": "B",
                "confidence": 0.8,
                "evidence": "quote",
            }
        ],
        topics=[{"name": "Testing", "relevance": 0.9, "time_range": "00:00-10:00"}],
        key_moments=[
            {
                "timestamp": "00:05",
                "description": "Key moment",
                "significance": 0.8,
                "quote": "quote",
            }
        ],
        sentiment={"overall": "neutral", "confidence": 0.7, "per_topic": {}},
        provider="test",
        model="test-model",
        cost=0.005,
        cost_breakdown={"total": 0.005},
        cache_stats={},
    )
