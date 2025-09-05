"""
Optimized chunking strategy for Voxtral transcription.
Handles Voxtral's 15-minute limit intelligently.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import subprocess
import json

logger = logging.getLogger(__name__)


class VoxtralChunker:
    """
    Smart chunking for Voxtral's transcription limits.
    
    Key features:
    - Respects 15-minute limit for voxtral-mini-2507
    - Respects 20-minute limit for voxtral-mini-latest
    - Optimizes chunk size to minimize API calls
    - Preserves context with intelligent overlap
    """
    
    # Model-specific limits (with safety margin)
    MODEL_LIMITS = {
        "voxtral-mini-2507": 840,  # 14 minutes (15 min limit - 1 min safety)
        "voxtral-mini-latest": 1140,  # 19 minutes (20 min limit - 1 min safety)
        "voxtral-small-latest": 1140,  # 19 minutes (20 min limit - 1 min safety)
    }
    
    # Optimal overlap percentages
    OVERLAP_RATIOS = {
        "short": 0.05,  # 5% overlap for videos < 30 min
        "medium": 0.07,  # 7% overlap for videos 30-60 min
        "long": 0.10,   # 10% overlap for videos > 60 min
    }
    
    def __init__(self, model: str = "voxtral-mini-2507"):
        """
        Initialize chunker for specific Voxtral model.
        
        Args:
            model: Voxtral model to optimize for
        """
        self.model = model
        self.chunk_limit = self.MODEL_LIMITS.get(model, 840)
        logger.info(f"VoxtralChunker initialized for {model} with {self.chunk_limit}s chunks")
    
    def calculate_optimal_chunking(self, duration: int) -> Tuple[int, int, int]:
        """
        Calculate optimal chunk size and overlap for given duration.
        
        Args:
            duration: Total video duration in seconds
            
        Returns:
            Tuple of (chunk_size, overlap, num_chunks)
        """
        # No chunking needed if under limit
        if duration <= self.chunk_limit:
            return duration, 0, 1
        
        # Determine overlap ratio based on video length
        if duration < 1800:  # < 30 min
            overlap_ratio = self.OVERLAP_RATIOS["short"]
        elif duration < 3600:  # < 60 min
            overlap_ratio = self.OVERLAP_RATIOS["medium"]
        else:  # >= 60 min
            overlap_ratio = self.OVERLAP_RATIOS["long"]
        
        # Calculate overlap in seconds
        overlap = int(self.chunk_limit * overlap_ratio)
        
        # Calculate effective chunk size (chunk - overlap)
        effective_chunk = self.chunk_limit - overlap
        
        # Calculate number of chunks needed
        num_chunks = 1 + ((duration - self.chunk_limit) + effective_chunk - 1) // effective_chunk
        
        logger.info(f"Optimal chunking for {duration}s video: {num_chunks} chunks of {self.chunk_limit}s with {overlap}s overlap")
        
        return self.chunk_limit, overlap, num_chunks
    
    async def split_audio(
        self,
        audio_path: str,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Split audio file into optimal chunks for Voxtral.
        
        Args:
            audio_path: Path to audio file
            output_dir: Directory for chunk files
            
        Returns:
            List of chunk metadata dicts with paths and timings
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Get duration
        duration = await self._get_audio_duration(str(audio_path))
        
        # Calculate optimal chunking
        chunk_size, overlap, num_chunks = self.calculate_optimal_chunking(duration)
        
        # No chunking needed
        if num_chunks == 1:
            return [{
                "path": str(audio_path),
                "start_time": 0,
                "end_time": duration,
                "chunk_index": 0,
                "total_chunks": 1
            }]
        
        # Create output directory
        if output_dir:
            chunk_dir = Path(output_dir)
        else:
            chunk_dir = audio_path.parent / f"{audio_path.stem}_voxtral_chunks"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        
        # Split into chunks
        chunks = []
        start_time = 0
        
        for i in range(num_chunks):
            # Calculate chunk timing
            end_time = min(start_time + chunk_size, duration)
            
            # Create chunk file
            chunk_path = chunk_dir / f"{audio_path.stem}_chunk_{i:03d}.mp3"
            
            # FFmpeg command for extraction
            cmd = [
                "ffmpeg",
                "-i", str(audio_path),
                "-ss", str(start_time),
                "-t", str(chunk_size),
                "-acodec", "copy",  # Fast copy without re-encoding
                "-y",  # Overwrite
                str(chunk_path)
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                
                chunks.append({
                    "path": str(chunk_path),
                    "start_time": start_time,
                    "end_time": end_time,
                    "chunk_index": i,
                    "total_chunks": num_chunks,
                    "overlap_start": max(0, start_time - overlap) if i > 0 else 0,
                    "overlap_end": min(duration, end_time + overlap) if i < num_chunks - 1 else end_time
                })
                
                logger.info(f"Created chunk {i+1}/{num_chunks}: {start_time:.1f}s - {end_time:.1f}s")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create chunk {i}: {e}")
                raise
            
            # Move start time for next chunk (with overlap)
            start_time = end_time - overlap
            if start_time >= duration:
                break
        
        return chunks
    
    async def _get_audio_duration(self, audio_path: str) -> int:
        """Get duration of audio file in seconds."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "json",
                    audio_path
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            duration = float(data["format"]["duration"])
            return int(duration)
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to get audio duration: {e}")
            # Fallback: assume it needs chunking
            return 3600  # 1 hour default
    
    def merge_chunk_transcripts(
        self,
        chunks: List[Dict[str, Any]],
        remove_overlap: bool = True
    ) -> Dict[str, Any]:
        """
        Merge transcripts from chunks into single coherent transcript.
        
        Args:
            chunks: List of chunk results with transcripts
            remove_overlap: Whether to remove duplicate text in overlaps
            
        Returns:
            Merged transcript with preserved timing
        """
        if not chunks:
            return {"text": "", "segments": []}
        
        # Single chunk - return as is
        if len(chunks) == 1:
            return chunks[0].get("transcript", {"text": "", "segments": []})
        
        merged_text = []
        merged_segments = []
        
        for i, chunk in enumerate(chunks):
            transcript = chunk.get("transcript", {})
            text = transcript.get("text", "")
            segments = transcript.get("segments", [])
            
            # Adjust segment timings to global timeline
            chunk_start = chunk.get("start_time", 0)
            adjusted_segments = []
            
            for segment in segments:
                adjusted_segment = segment.copy()
                if "start" in adjusted_segment:
                    adjusted_segment["start"] += chunk_start
                if "end" in adjusted_segment:
                    adjusted_segment["end"] += chunk_start
                adjusted_segments.append(adjusted_segment)
            
            # Handle overlap removal
            if remove_overlap and i > 0:
                # Simple deduplication - can be improved with fuzzy matching
                overlap_duration = chunk.get("overlap_start", 0)
                if overlap_duration > 0 and merged_text:
                    # Remove potential duplicate from start of current chunk
                    # This is simplified - production would use better algorithms
                    words = text.split()
                    if len(words) > 10:
                        text = " ".join(words[5:])  # Skip first few words
            
            merged_text.append(text)
            merged_segments.extend(adjusted_segments)
        
        return {
            "text": " ".join(merged_text),
            "segments": merged_segments,
            "chunks_processed": len(chunks),
            "merge_method": "overlap_removal" if remove_overlap else "simple_concatenation"
        }


class VoxtralBatchProcessor:
    """
    Process multiple videos efficiently with Voxtral.
    """
    
    def __init__(
        self,
        model: str = "voxtral-mini-2507",
        max_concurrent: int = 5
    ):
        """
        Initialize batch processor.
        
        Args:
            model: Voxtral model to use
            max_concurrent: Maximum concurrent transcriptions
        """
        self.model = model
        self.chunker = VoxtralChunker(model)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def process_batch(
        self,
        audio_paths: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple audio files in parallel.
        
        Args:
            audio_paths: List of audio file paths
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of transcription results
        """
        tasks = []
        for i, path in enumerate(audio_paths):
            task = self._process_with_limit(path, i, len(audio_paths), progress_callback)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle errors
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to process {audio_paths[i]}: {result}")
                processed_results.append({
                    "error": str(result),
                    "path": audio_paths[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _process_with_limit(
        self,
        audio_path: str,
        index: int,
        total: int,
        progress_callback: Optional[callable]
    ) -> Dict[str, Any]:
        """Process single audio with concurrency limit."""
        async with self.semaphore:
            if progress_callback:
                await progress_callback(index, total, f"Processing {Path(audio_path).name}")
            
            # Check if chunking is needed
            chunks = await self.chunker.split_audio(audio_path)
            
            if len(chunks) == 1:
                # Direct transcription
                from ..retrievers.voxtral_transcriber import VoxtralTranscriber
                transcriber = VoxtralTranscriber(model=self.model)
                result = await transcriber.transcribe_audio(audio_path)
                return {
                    "path": audio_path,
                    "transcript": result.text,
                    "cost": result.cost,
                    "chunks": 1
                }
            else:
                # Chunked transcription
                chunk_results = []
                for chunk in chunks:
                    transcriber = VoxtralTranscriber(model=self.model)
                    result = await transcriber.transcribe_audio(chunk["path"])
                    chunk_results.append({
                        "transcript": {"text": result.text},
                        "start_time": chunk["start_time"],
                        "cost": result.cost
                    })
                
                # Merge results
                merged = self.chunker.merge_chunk_transcripts(chunk_results)
                total_cost = sum(c["cost"] for c in chunk_results)
                
                return {
                    "path": audio_path,
                    "transcript": merged["text"],
                    "cost": total_cost,
                    "chunks": len(chunks)
                }
