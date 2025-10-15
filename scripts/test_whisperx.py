#!/usr/bin/env python3
"""
Test WhisperX and save full results to file for review.
"""
import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clipscribe.transcribers.whisperx_transcriber import WhisperXTranscriber


async def test_and_save(audio_file: str):
    """Test WhisperX and save full results."""
    
    audio_path = Path(audio_file)
    if not audio_path.exists():
        print(f"ERROR: File not found: {audio_file}")
        return
    
    print(f"Testing WhisperX on: {audio_path.name}")
    print("This will take ~20 minutes...")
    print()
    
    # Initialize transcriber
    transcriber = WhisperXTranscriber(enable_diarization=True)
    
    # Transcribe
    result = await transcriber.transcribe_audio(str(audio_path))
    
    # Save full results to file
    output_file = audio_path.parent / f"{audio_path.stem}_whisperx_results.txt"
    
    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("WHISPERX FULL TRANSCRIPTION RESULTS\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"File: {audio_path.name}\n")
        f.write(f"Duration: {result.duration:.1f} seconds ({result.duration/60:.1f} minutes)\n")
        f.write(f"Language: {result.language}\n")
        f.write(f"Confidence: {result.confidence:.2%}\n")
        f.write(f"Words: {len(result.word_level_timestamps)}\n")
        f.write(f"Speakers: {len(result.speaker_segments)}\n")
        f.write(f"Cost: ${result.cost:.4f}\n")
        f.write("\n" + "="*80 + "\n")
        f.write("FULL TRANSCRIPT\n")
        f.write("="*80 + "\n\n")
        f.write(result.text)
        f.write("\n\n" + "="*80 + "\n")
        f.write("SPEAKER BREAKDOWN\n")
        f.write("="*80 + "\n\n")
        
        for speaker in result.speaker_segments:
            f.write(f"{speaker['speaker']}:\n")
            f.write(f"  Total time: {speaker['total_time']:.1f}s ({speaker['total_time']/60:.1f} min)\n")
            f.write(f"  Segments: {speaker['segments']}\n\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("SAMPLE WORD-LEVEL TIMESTAMPS (first 50 words)\n")
        f.write("="*80 + "\n\n")
        
        for i, word_data in enumerate(result.word_level_timestamps[:50]):
            speaker = word_data.get('speaker', 'UNKNOWN')
            f.write(f"[{word_data['start']:.1f}s] {speaker}: {word_data['word']}\n")
    
    # Also save as JSON
    json_file = audio_path.parent / f"{audio_path.stem}_whisperx_results.json"
    with open(json_file, 'w') as f:
        json.dump({
            "file": audio_path.name,
            "duration": result.duration,
            "language": result.language,
            "confidence": result.confidence,
            "transcript": result.text,
            "word_count": len(result.word_level_timestamps),
            "speaker_count": len(result.speaker_segments),
            "speakers": result.speaker_segments,
            "word_timestamps": result.word_level_timestamps[:100]  # First 100 words
        }, f, indent=2)
    
    print(f"\n✅ Results saved to:")
    print(f"   {output_file}")
    print(f"   {json_file}")
    print(f"\nReview the full transcript and speaker breakdown in the .txt file")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_whisperx.py <audio_file>")
        sys.exit(1)
    
    asyncio.run(test_and_save(sys.argv[1]))

