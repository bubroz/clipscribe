#!/usr/bin/env python3
"""
Speaker Quality Improvement Algorithms

Research-based post-processing to improve speaker diarization quality.
Addresses:
1. Interjection mis-attribution ("Yeah", "Right" assigned to wrong speaker)
2. Over-segmentation (same person split into multiple IDs)
3. Short segment noise (<1 second artifacts)
"""

import json
from typing import List, Dict, Set, Tuple
from collections import Counter


def analyze_speaker_distribution(segments: List[Dict]) -> Dict:
    """
    Analyze speaker distribution to identify major vs minor speakers.
    
    Returns:
        {
            'major_speakers': ['SPEAKER_01', 'SPEAKER_05'],  # >10% of content
            'minor_speakers': ['SPEAKER_00', 'SPEAKER_02'],  # <10% of content
            'speaker_stats': {...}  # Detailed stats per speaker
        }
    """
    total_segments = len(segments)
    speaker_stats = {}
    
    for seg in segments:
        speaker = seg.get('speaker', 'UNKNOWN')
        if speaker not in speaker_stats:
            speaker_stats[speaker] = {
                'count': 0,
                'total_duration': 0.0,
                'segments': []
            }
        
        speaker_stats[speaker]['count'] += 1
        speaker_stats[speaker]['total_duration'] += seg.get('end', 0) - seg.get('start', 0)
        speaker_stats[speaker]['segments'].append(seg)
    
    # Classify major vs minor speakers
    major_speakers = []
    minor_speakers = []
    
    for speaker, stats in speaker_stats.items():
        pct = (stats['count'] / total_segments) * 100
        if pct >= 10.0:  # 10% threshold for "major" speaker
            major_speakers.append(speaker)
        else:
            minor_speakers.append(speaker)
    
    return {
        'major_speakers': major_speakers,
        'minor_speakers': minor_speakers,
        'speaker_stats': speaker_stats
    }


def merge_interjections(segments: List[Dict], major_speakers: List[str]) -> List[Dict]:
    """
    Merge short interjections back to the speaker who's turn it is.
    
    Algorithm:
    1. If segment is <2 seconds AND <5 words
    2. Look at surrounding segments (before AND after)
    3. If both neighbors are same major speaker, assign to that speaker
    4. Otherwise, assign to nearest major speaker
    
    This handles:
    - "Yeah" → SPEAKER_01 (during their turn)
    - "Right" → SPEAKER_05 (brief agreement)
    - "Mm-hmm" → Context-appropriate speaker
    """
    merged = []
    major_set = set(major_speakers)
    
    for i, seg in enumerate(segments):
        duration = seg.get('end', 0) - seg.get('start', 0)
        word_count = len(seg.get('text', '').split())
        current_speaker = seg.get('speaker', 'UNKNOWN')
        
        # Check if this is a short interjection
        if duration < 2.0 and word_count <= 5 and current_speaker not in major_set:
            # Look at surrounding context
            before_speaker = segments[i-1].get('speaker') if i > 0 else None
            after_speaker = segments[i+1].get('speaker') if i < len(segments)-1 else None
            
            # Case 1: Sandwiched between same major speaker (A → X → A)
            if before_speaker == after_speaker and before_speaker in major_set:
                seg_copy = seg.copy()
                seg_copy['speaker'] = before_speaker
                seg_copy['original_speaker'] = current_speaker
                seg_copy['merge_reason'] = 'sandwiched_interjection'
                merged.append(seg_copy)
            
            # Case 2: Before or after is major speaker
            elif before_speaker in major_set:
                seg_copy = seg.copy()
                seg_copy['speaker'] = before_speaker
                seg_copy['original_speaker'] = current_speaker
                seg_copy['merge_reason'] = 'continuation'
                merged.append(seg_copy)
            
            elif after_speaker in major_set:
                seg_copy = seg.copy()
                seg_copy['speaker'] = after_speaker
                seg_copy['original_speaker'] = current_speaker
                seg_copy['merge_reason'] = 'anticipation'
                merged.append(seg_copy)
            
            else:
                # Keep as-is if no clear assignment
                merged.append(seg)
        else:
            # Not an interjection, keep as-is
            merged.append(seg)
    
    return merged


def merge_ultra_short_segments(segments: List[Dict]) -> List[Dict]:
    """
    Merge segments <0.5 seconds (likely diarization artifacts).
    
    These are almost always:
    - Breathing sounds
    - Background noise
    - Diarization errors
    
    Merge into previous segment if exists, otherwise next.
    """
    merged = []
    skip_next = False
    
    for i, seg in enumerate(segments):
        if skip_next:
            skip_next = False
            continue
        
        duration = seg.get('end', 0) - seg.get('start', 0)
        
        if duration < 0.5:
            # Try to merge with previous
            if merged:
                prev = merged[-1]
                prev['end'] = seg.get('end', prev['end'])
                prev['text'] += ' ' + seg.get('text', '')
                prev['merged_segments'] = prev.get('merged_segments', []) + [seg]
            # Otherwise merge with next
            elif i < len(segments) - 1:
                next_seg = segments[i+1].copy()
                next_seg['start'] = seg.get('start', next_seg['start'])
                next_seg['text'] = seg.get('text', '') + ' ' + next_seg['text']
                next_seg['merged_segments'] = [seg]
                merged.append(next_seg)
                skip_next = True
            else:
                # Last segment and very short, just keep it
                merged.append(seg)
        else:
            merged.append(seg)
    
    return merged


def detect_speaker_anomalies(segments: List[Dict]) -> Dict:
    """
    Detect patterns that indicate quality issues.
    
    Returns problematic patterns for review.
    """
    issues = {
        'rapid_switches': [],  # A→B→A patterns
        'ultra_short': [],      # <0.5 second segments
        'single_word': [],      # 1-word segments
        'suspicious_transitions': []  # Unusual speaker patterns
    }
    
    # Find rapid A→B→A switches
    for i in range(len(segments) - 2):
        s1 = segments[i].get('speaker')
        s2 = segments[i+1].get('speaker')
        s3 = segments[i+2].get('speaker')
        
        if s1 == s3 and s1 != s2:
            issues['rapid_switches'].append({
                'index': i,
                'pattern': f"{s1}→{s2}→{s1}",
                'middle_text': segments[i+1].get('text', ''),
                'timestamp': segments[i].get('start', 0)
            })
    
    # Find ultra-short segments
    for i, seg in enumerate(segments):
        duration = seg.get('end', 0) - seg.get('start', 0)
        if duration < 0.5:
            issues['ultra_short'].append({
                'index': i,
                'duration': duration,
                'speaker': seg.get('speaker'),
                'text': seg.get('text', ''),
                'timestamp': seg.get('start', 0)
            })
    
    # Find single-word segments
    for i, seg in enumerate(segments):
        words = seg.get('text', '').strip().split()
        if len(words) == 1:
            issues['single_word'].append({
                'index': i,
                'speaker': seg.get('speaker'),
                'word': words[0] if words else '',
                'timestamp': seg.get('start', 0)
            })
    
    return issues


def apply_all_improvements(segments: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    Apply all quality improvements in sequence.
    
    Returns:
        (improved_segments, stats)
    """
    original_count = len(segments)
    
    # Step 1: Analyze distribution
    analysis = analyze_speaker_distribution(segments)
    major_speakers = analysis['major_speakers']
    
    print(f"Identified {len(major_speakers)} major speakers: {major_speakers}")
    print(f"Found {len(analysis['minor_speakers'])} minor speakers (will attempt to merge)")
    print()
    
    # Step 2: Merge ultra-short segments first
    segments = merge_ultra_short_segments(segments)
    after_ultra_short = len(segments)
    print(f"After ultra-short merge: {original_count} → {after_ultra_short} segments")
    
    # Step 3: Merge interjections
    segments = merge_interjections(segments, major_speakers)
    after_interjections = len(segments)
    print(f"After interjection merge: {after_ultra_short} → {after_interjections} segments")
    
    # Step 4: Re-analyze
    final_analysis = analyze_speaker_distribution(segments)
    
    # Step 5: Detect remaining issues
    remaining_issues = detect_speaker_anomalies(segments)
    
    stats = {
        'original_segments': original_count,
        'final_segments': len(segments),
        'segments_merged': original_count - len(segments),
        'original_speakers': len(analysis['speaker_stats']),
        'final_speakers': len(final_analysis['speaker_stats']),
        'major_speakers': major_speakers,
        'remaining_issues': {
            'rapid_switches': len(remaining_issues['rapid_switches']),
            'ultra_short': len(remaining_issues['ultra_short']),
            'single_word': len(remaining_issues['single_word'])
        }
    }
    
    return segments, stats


def generate_quality_report(original_segments: List[Dict], 
                           improved_segments: List[Dict],
                           stats: Dict) -> str:
    """Generate a quality improvement report."""
    
    report = []
    report.append("=" * 80)
    report.append("QUALITY IMPROVEMENT REPORT")
    report.append("=" * 80)
    report.append("")
    
    report.append("BEFORE:")
    report.append(f"  Segments: {stats['original_segments']}")
    report.append(f"  Speakers: {stats['original_speakers']}")
    report.append("")
    
    report.append("AFTER:")
    report.append(f"  Segments: {stats['final_segments']} ({stats['segments_merged']} merged)")
    report.append(f"  Speakers: {stats['final_speakers']}")
    report.append(f"  Major speakers: {', '.join(stats['major_speakers'])}")
    report.append("")
    
    report.append("IMPROVEMENTS:")
    reduction = stats['original_speakers'] - stats['final_speakers']
    report.append(f"  Speakers reduced: {stats['original_speakers']} → {stats['final_speakers']} (-{reduction})")
    report.append(f"  Segments cleaned: {stats['segments_merged']} merged")
    report.append("")
    
    report.append("REMAINING ISSUES:")
    report.append(f"  Rapid switches: {stats['remaining_issues']['rapid_switches']}")
    report.append(f"  Ultra-short segments: {stats['remaining_issues']['ultra_short']}")
    report.append(f"  Single-word segments: {stats['remaining_issues']['single_word']}")
    report.append("")
    
    return "\n".join(report)


# CLI usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python quality_improvements.py <transcript.json>")
        sys.exit(1)
    
    # Load transcript
    with open(sys.argv[1]) as f:
        data = json.load(f)
    
    original_segments = data['segments']
    
    print("=" * 80)
    print("SPEAKER QUALITY IMPROVEMENT")
    print("=" * 80)
    print()
    
    # Apply improvements
    improved_segments, stats = apply_all_improvements(original_segments)
    
    # Generate report
    report = generate_quality_report(original_segments, improved_segments, stats)
    print(report)
    
    # Save improved version
    output_file = sys.argv[1].replace('.json', '_improved.json')
    data['segments'] = improved_segments
    data['improvement_stats'] = stats
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Improved transcript saved to: {output_file}")

