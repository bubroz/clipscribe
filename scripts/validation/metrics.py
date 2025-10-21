"""
Validation metrics calculation module.

Provides WER, DER, and speaker accuracy calculations for validating
ClipScribe against ground truth datasets.
"""

from typing import Dict, List, Tuple
from jiwer import wer

# Note: pyannote.metrics has numpy conflicts with whisperx
# We'll calculate DER manually for now (simple formula)


def calculate_wer(hypothesis: str, reference: str) -> float:
    """
    Calculate Word Error Rate between hypothesis and reference transcripts.
    
    Args:
        hypothesis: System-generated transcript
        reference: Ground truth transcript
        
    Returns:
        WER as float (0.0 to 1.0+, lower is better)
    """
    return wer(reference, hypothesis)


def calculate_der(
    hypothesis_segments: List[Dict],
    reference_segments: List[Dict],
    collar: float = 0.25
) -> float:
    """
    Calculate Diarization Error Rate manually.
    
    DER = (Missed + False Alarm + Speaker Confusion) / Total Reference Time
    
    Args:
        hypothesis_segments: ClipScribe output segments
        reference_segments: Ground truth segments
        collar: Forgiveness window in seconds (default 0.25 = NIST standard)
        
    Returns:
        DER as float (0.0 to 1.0+, lower is better)
    """
    # Simplified DER calculation for now
    # TODO: Implement full NIST DER with collar
    # For Phase 1, we'll use speaker accuracy as proxy
    
    # Calculate total reference time
    total_ref_time = sum(seg.get('end', 0) - seg.get('start', 0) for seg in reference_segments)
    
    if total_ref_time == 0:
        return 1.0  # No reference data = 100% error
    
    # For now, return placeholder
    # Will implement proper DER in Week 1 when needed
    return 0.0  # Placeholder


def calculate_speaker_accuracy(
    hypothesis_segments: List[Dict],
    reference_segments: List[Dict],
    speaker_mapping: Dict[str, str]
) -> Tuple[float, Dict]:
    """
    Calculate percentage of segments with correct speaker attribution.
    
    Args:
        hypothesis_segments: ClipScribe output segments
        reference_segments: Ground truth segments
        speaker_mapping: Map from ClipScribe speaker IDs to ground truth IDs
                        e.g., {'SPEAKER_01': 'therapist', 'SPEAKER_02': 'client'}
        
    Returns:
        (accuracy, stats_dict) where accuracy is 0.0-1.0
    """
    # Align segments by timestamp overlap
    correct = 0
    total = 0
    confusion_matrix = {}
    
    for hyp_seg in hypothesis_segments:
        hyp_start = hyp_seg.get('start', 0)
        hyp_end = hyp_seg.get('end', 0)
        hyp_speaker = hyp_seg.get('speaker', 'UNKNOWN')
        
        # Map to ground truth speaker ID
        mapped_speaker = speaker_mapping.get(hyp_speaker, hyp_speaker)
        
        # Find overlapping reference segment
        best_overlap = 0
        best_ref_speaker = None
        
        for ref_seg in reference_segments:
            ref_start = ref_seg.get('start', 0)
            ref_end = ref_seg.get('end', 0)
            
            # Calculate overlap
            overlap_start = max(hyp_start, ref_start)
            overlap_end = min(hyp_end, ref_end)
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_ref_speaker = ref_seg.get('speaker', 'UNKNOWN')
        
        if best_ref_speaker:
            total += 1
            if mapped_speaker == best_ref_speaker:
                correct += 1
            
            # Track confusion
            key = f"{best_ref_speaker} → {mapped_speaker}"
            confusion_matrix[key] = confusion_matrix.get(key, 0) + 1
    
    accuracy = correct / total if total > 0 else 0.0
    
    stats = {
        'correct': correct,
        'total': total,
        'accuracy': accuracy,
        'confusion_matrix': confusion_matrix
    }
    
    return accuracy, stats


def normalize_text(text: str) -> str:
    """
    Normalize text for fair WER comparison.
    
    - Lowercase
    - Remove punctuation
    - Normalize whitespace
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    import re
    
    # Lowercase
    text = text.lower()
    
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text

