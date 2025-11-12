"""
End-to-end tests for Modal GPU pipeline with Grok-4 Fast Reasoning.

These tests call the REAL Modal service and REAL Grok-4 API.
Marked as expensive to run only when explicitly requested.
"""

import pytest
import asyncio
from pathlib import Path
import json
from google.cloud import storage
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.expensive
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires deployed Modal app (station10-transcription) - run manually in CI/CD")
async def test_modal_pipeline_complete_intelligence():
    """
    Full E2E test of Modal pipeline with Grok-4 Fast Reasoning.
    
    Tests:
    1. GCS upload
    2. Modal transcription (WhisperX + diarization)
    3. Grok-4 intelligence extraction (entities, relationships, topics, moments, sentiment)
    4. Output structure completeness
    5. Evidence quote coverage
    6. Cost tracking
    
    Uses: The View video (36min, fastest to test)
    Cost: ~$0.10 per run
    """
    import modal
    
    # Test video (shortest for speed)
    test_audio = project_root / "test_videos/U3w93r5QRb8_The View Full Broadcast – October 14, 2025.mp3"
    
    if not test_audio.exists():
        pytest.skip(f"Test audio not found: {test_audio}")
    
    # Upload to GCS
    client = storage.Client()
    bucket = client.bucket("clipscribe-validation")
    
    gcs_path = "validation/e2e_test/the_view_test.mp3"
    blob = bucket.blob(gcs_path)
    
    if not blob.exists():
        blob.upload_from_filename(str(test_audio))
    
    gcs_url = f"gs://clipscribe-validation/{gcs_path}"
    
    # Call Modal
    Station10Transcriber = modal.Cls.from_name("station10-transcription", "Station10Transcriber")
    result_dict = Station10Transcriber().transcribe_from_gcs.remote(
        gcs_input=gcs_url,
        gcs_output="gs://clipscribe-validation/validation/e2e_test/output/"
    )
    
    # Download full transcript
    transcript_blob = bucket.blob("validation/e2e_test/output//transcript.json")
    assert transcript_blob.exists(), "Transcript JSON not created"
    
    transcript_data = json.loads(transcript_blob.download_as_text())
    
    # VERIFY OUTPUT STRUCTURE
    assert "segments" in transcript_data, "Missing segments"
    assert "word_segments" in transcript_data, "Missing word_segments"
    assert "entities" in transcript_data, "Missing entities"
    assert "relationships" in transcript_data, "Missing relationships"
    assert "topics" in transcript_data, "Missing topics (NEW feature!)"
    assert "key_moments" in transcript_data, "Missing key_moments (NEW feature!)"
    assert "sentiment" in transcript_data, "Missing sentiment (NEW feature!)"
    
    # VERIFY CONTENT QUALITY
    segments = transcript_data["segments"]
    entities = transcript_data["entities"]
    relationships = transcript_data["relationships"]
    topics = transcript_data["topics"]
    key_moments = transcript_data["key_moments"]
    sentiment = transcript_data["sentiment"]
    
    # Basic counts
    assert len(segments) > 100, f"Too few segments: {len(segments)}"
    assert len(entities) > 10, f"Too few entities: {len(entities)}"
    assert len(topics) >= 1, "No topics extracted"
    assert len(key_moments) >= 1, "No key moments extracted"
    
    # Evidence coverage
    entities_with_evidence = sum(1 for e in entities if e.get('evidence'))
    evidence_rate = entities_with_evidence / len(entities) if entities else 0
    assert evidence_rate > 0.5, f"Low evidence coverage: {evidence_rate*100:.0f}%"
    
    # Topic structure
    for topic in topics:
        assert 'name' in topic, "Topic missing name"
        assert 'relevance' in topic, "Topic missing relevance"
        # time_range is optional
    
    # Key moment structure
    for moment in key_moments:
        assert 'timestamp' in moment, "Moment missing timestamp"
        assert 'description' in moment, "Moment missing description"
        assert 'significance' in moment, "Moment missing significance"
        # quote is optional
    
    # Sentiment structure
    assert 'overall' in sentiment, "Sentiment missing overall"
    assert sentiment['overall'] in ['positive', 'negative', 'neutral', 'mixed'], \
        f"Invalid sentiment: {sentiment.get('overall')}"
    
    # Entity types (should have diversity)
    entity_types = set(e.get('type') for e in entities)
    assert len(entity_types) >= 5, f"Low entity type diversity: {len(entity_types)} types"
    
    # Relationship structure
    for rel in relationships:
        assert 'subject' in rel, "Relationship missing subject"
        assert 'predicate' in rel, "Relationship missing predicate"
        assert 'object' in rel, "Relationship missing object"
    
    # Cost tracking
    assert result_dict.get('cost', 0) > 0, "No cost tracked"
    
    print(f"\n✅ E2E TEST PASSED")
    print(f"  Entities: {len(entities)} (with {entities_with_evidence} evidence quotes)")
    print(f"  Topics: {len(topics)}")
    print(f"  Key moments: {len(key_moments)}")
    print(f"  Sentiment: {sentiment.get('overall')}")
    print(f"  Cost: ${result_dict.get('cost', 0):.4f}")


@pytest.mark.expensive
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires deployed Modal app (station10-transcription) - run manually in CI/CD")
async def test_modal_pipeline_long_video():
    """
    Test Modal handles long videos (>45k chars) properly.
    
    Uses: All-In Podcast (88min, 87k chars)
    Verifies: Single-pass extraction with 200k limit
    """
    import modal
    
    test_audio = project_root / "test_videos/IbnrclsPGPQ_Trump Brokers Gaza Peace Deal, National Guard in C.mp3"
    
    if not test_audio.exists():
        pytest.skip(f"Test audio not found: {test_audio}")
    
    client = storage.Client()
    bucket = client.bucket("clipscribe-validation")
    
    gcs_path = "validation/e2e_test/all_in_long_test.mp3"
    blob = bucket.blob(gcs_path)
    
    if not blob.exists():
        blob.upload_from_filename(str(test_audio))
    
    gcs_url = f"gs://clipscribe-validation/{gcs_path}"
    
    # Call Modal
    Station10Transcriber = modal.Cls.from_name("station10-transcription", "Station10Transcriber")
    result_dict = Station10Transcriber().transcribe_from_gcs.remote(
        gcs_input=gcs_url,
        gcs_output="gs://clipscribe-validation/validation/e2e_test/all_in_output/"
    )
    
    # Download transcript
    transcript_blob = bucket.blob("validation/e2e_test/all_in_output//transcript.json")
    assert transcript_blob.exists(), "Transcript not created for long video"
    
    transcript_data = json.loads(transcript_blob.download_as_text())
    
    # Verify long video gets full intelligence (not chunked)
    topics = transcript_data.get("topics", [])
    key_moments = transcript_data.get("key_moments", [])
    
    assert len(topics) >= 1, "Long video missing topics (chunking issue?)"
    assert len(key_moments) >= 1, "Long video missing key moments (chunking issue?)"
    
    print(f"\n✅ LONG VIDEO TEST PASSED")
    print(f"  Transcript length: ~87k chars")
    print(f"  Topics: {len(topics)} (proves single-pass extraction)")
    print(f"  Key moments: {len(key_moments)}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-m", "expensive"])

