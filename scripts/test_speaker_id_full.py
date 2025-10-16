#!/usr/bin/env python3
"""
Full speaker identification validation test.

Tests speaker ID on REAL transcribed videos with actual speaker diarization.
Uses Voxtral (fast) for transcription, pyannote for diarization.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clipscribe.transcribers.voxtral_transcriber import VoxtralTranscriber
from clipscribe.utils.voxtral_chunker import VoxtralChunker
from clipscribe.intelligence.speaker_identifier import SpeakerIdentifier


async def test_full_pipeline(audio_file: str, video_metadata: dict):
    """
    Full test: Transcribe → Diarize → Identify speakers
    
    This is the REAL test using actual transcription with chunking for large files.
    """
    
    print(f"\n{'='*80}")
    print(f"TESTING: {video_metadata['title'][:60]}")
    print(f"{'='*80}\n")
    
    audio_path = Path(audio_file)
    if not audio_path.exists():
        print(f"ERROR: File not found: {audio_file}")
        return
    
    # Step 1: Transcribe with Voxtral (with chunking for large files)
    print("Step 1: Transcribing with Voxtral (auto-chunking for large files)...")
    
    chunker = VoxtralChunker()
    chunks = await chunker.split_audio(str(audio_path))
    print(f"  Split into {len(chunks)} chunks")
    
    if len(chunks) == 1:
        # Small file, transcribe directly
        transcriber = VoxtralTranscriber()
        result = await transcriber.transcribe_audio(str(audio_path))
        transcript = result.text
    else:
        # Large file, transcribe chunks and merge
        transcriber = VoxtralTranscriber()
        chunk_results = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"  Transcribing chunk {i}/{len(chunks)}...")
            result = await transcriber.transcribe_audio(chunk['path'])
            chunk_results.append({
                "transcript": {"text": result.text},
                "start_time": chunk['start_time'],
                "cost": result.cost
            })
        
        # Merge chunks
        merged = chunker.merge_chunk_transcripts(chunk_results)
        transcript = merged['text']
    
    print(f"  ✓ Transcribed: {len(transcript)} chars")
    
    # Step 2: Diarize speakers with pyannote
    print("Step 2: Identifying speaker segments with pyannote...")
    from pyannote.audio import Pipeline
    import os
    
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        print("  ✗ HUGGINGFACE_TOKEN not set - can't diarize")
        return
    
    diarize_pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token
    )
    
    diarization = diarize_pipeline(str(audio_path))
    
    # Convert to speaker segments
    speaker_dict = {}
    transcript_with_speakers = []
    
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if speaker not in speaker_dict:
            speaker_dict[speaker] = {
                "speaker": speaker,
                "total_time": 0,
                "segments": 0
            }
        speaker_dict[speaker]["total_time"] += turn.end - turn.start
        speaker_dict[speaker]["segments"] += 1
    
    speaker_segments = list(speaker_dict.values())
    print(f"  ✓ Found {len(speaker_segments)} speakers:")
    for spk in speaker_segments:
        print(f"    {spk['speaker']}: {spk['total_time']:.1f}s, {spk['segments']} segments")
    
    # Build transcript with speaker labels (simplified for testing)
    # In production, this would align speakers with transcript text
    transcript_with_labels = f"[Context from {len(speaker_segments)} speakers]\n\n{transcript[:5000]}"
    
    # Step 3: Identify speakers with Grok
    print("\nStep 3: Identifying speakers with Grok...")
    identifier = SpeakerIdentifier()
    
    identities = await identifier.identify_speakers(
        transcript_with_speakers=transcript_with_labels,
        speaker_segments=speaker_segments,
        video_metadata=video_metadata
    )
    
    # Step 4: Display results
    print(f"\n{'='*80}")
    print("SPEAKER IDENTIFICATION RESULTS")
    print(f"{'='*80}\n")
    
    for ident in identities:
        print(f"{ident.speaker_label}:")
        if ident.identified_name:
            print(f"  ✓ Identified as: {ident.identified_name}")
        else:
            print(f"  ✗ Unknown (confidence too low)")
        print(f"  Confidence: {ident.confidence:.1%}")
        print(f"  Role: {ident.role or 'Unknown'}")
        print(f"  Evidence:")
        for ev in ident.evidence[:3]:  # Show first 3 pieces
            print(f"    - {ev}")
        print()
    
    # Save results
    output_file = audio_path.parent / f"{audio_path.stem}_speaker_id_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "video": video_metadata,
            "speakers_found": len(speaker_segments),
            "speakers_identified": sum(1 for i in identities if i.identified_name),
            "identifications": [
                {
                    "label": i.speaker_label,
                    "name": i.identified_name,
                    "confidence": i.confidence,
                    "role": i.role,
                    "evidence": i.evidence
                }
                for i in identities
            ]
        }, f, indent=2)
    
    print(f"Results saved to: {output_file.name}")
    
    # Return summary
    identified_count = sum(1 for i in identities if i.identified_name)
    return {
        "total_speakers": len(speaker_segments),
        "identified": identified_count,
        "success_rate": identified_count / len(speaker_segments) if speaker_segments else 0
    }


async def run_test_suite():
    """Run speaker ID tests on all test videos."""
    
    test_videos = [
        {
            "file": "test_videos/wlONOh_iUXY_Marjorie Taylor Greene Emergency Podcast ｜ The Tim.mp3",
            "metadata": {
                "title": "Marjorie Taylor Greene Emergency Podcast | The Tim Dillon Show #465",
                "channel": "The Tim Dillon Show",
                "description": "Tim Dillon sits down with Congresswoman Marjorie Taylor Greene to discuss the Epstein files...",
                "expected_speakers": 2
            }
        },
        {
            "file": "test_videos/IbnrclsPGPQ_Trump Brokers Gaza Peace Deal, National Guard in C.mp3",
            "metadata": {
                "title": "Trump Brokers Gaza Peace Deal, National Guard in Chicago, OpenAI/AMD, AI Roundtripping, Gold Rally",
                "channel": "All-In Podcast",
                "description": "Chamath, Jason, David Sacks, and Friedberg discuss...",
                "expected_speakers": 4
            }
        },
        {
            "file": "test_videos/U3w93r5QRb8_The View Full Broadcast – October 14, 2025.mp3",
            "metadata": {
                "title": "The View Full Broadcast – October 14, 2025",
                "channel": "The View",
                "description": "Daily panel discussion",
                "expected_speakers": 5
            }
        }
    ]
    
    results = []
    
    for test in test_videos:
        if not Path(test["file"]).exists():
            print(f"Skipping {test['file']} (not found)")
            continue
        
        result = await test_full_pipeline(test["file"], test["metadata"])
        if result:
            results.append({
                "video": test["metadata"]["title"][:40],
                **result
            })
        
        print("\n" + "="*80 + "\n")
    
    # Summary
    print("TEST SUITE SUMMARY")
    print("="*80)
    for r in results:
        success_pct = r['success_rate'] * 100
        print(f"{r['video']}: {r['identified']}/{r['total_speakers']} identified ({success_pct:.0f}%)")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Single video test
        audio_file = sys.argv[1]
        
        # Get metadata from filename
        filename = Path(audio_file).stem
        metadata = {
            "title": filename,
            "channel": "Unknown",
            "description": ""
        }
        
        asyncio.run(test_full_pipeline(audio_file, metadata))
    else:
        # Full test suite
        print("Running full speaker ID validation suite...")
        print("This will test: 2-speaker, 4-speaker, and 5+ speaker scenarios\n")
        asyncio.run(run_test_suite())

