import logging
from difflib import SequenceMatcher
from typing import List

logger = logging.getLogger(__name__)


class TranscriptMerger:
    """
    Intelligently merges overlapping transcript chunks into a single,
    coherent transcript.
    """

    def merge_transcripts(self, transcripts: List[str]) -> str:
        """
        Merges a list of transcript strings, removing overlaps.

        Args:
            transcripts: A list of transcript strings, in order.

        Returns:
            A single, merged transcript string.
        """
        if not transcripts:
            return ""

        merged_transcript = transcripts[0]
        for i in range(1, len(transcripts)):
            prev_chunk = merged_transcript
            next_chunk = transcripts[i]

            # Find the best overlap point
            overlap_len = self._find_best_overlap(prev_chunk, next_chunk)

            # Append the non-overlapping part of the next chunk
            if overlap_len > 0:
                merged_transcript += next_chunk[overlap_len:]
            else:
                # If no overlap, just append with a space
                merged_transcript += " " + next_chunk

        return merged_transcript.strip()

    def _find_best_overlap(self, s1: str, s2: str, min_overlap: int = 20) -> int:
        """
        Finds the length of the best overlap between the end of s1 and the
        start of s2.
        """
        max_overlap = 0

        # We search for an overlap in the last part of s1 and the first part of s2
        # A reasonable search window is a few hundred characters
        search_window = min(len(s1), len(s2), 400)

        s1_end = s1[-search_window:]
        s2_start = s2[:search_window]

        matcher = SequenceMatcher(None, s1_end, s2_start, autojunk=False)

        # Get the longest matching block
        match = matcher.find_longest_match(0, len(s1_end), 0, len(s2_start))

        # Check if the match is at the very end of s1_end and start of s2_start
        # This indicates a true suffix-prefix overlap
        if (match.a + match.size == len(s1_end)) and (match.b == 0):
            if match.size >= min_overlap:
                max_overlap = match.size
                logger.debug(f"Found overlap of length {max_overlap}")

        return max_overlap


if __name__ == "__main__":
    # Example for testing
    merger = TranscriptMerger()

    chunk1 = "This is the first part of the transcript, and it continues for a while."
    chunk2 = "continues for a while. Now we are into the second part, which has its own content."
    chunk3 = "its own content. Finally, we have reached the end of the video."

    transcripts = [chunk1, chunk2, chunk3]

    merged = merger.merge_transcripts(transcripts)

    print("--- CHUNKS ---")
    for i, t in enumerate(transcripts):
        print(f"Chunk {i+1}: {t}")

    print("\n--- MERGED ---")
    print(merged)

    expected = "This is the first part of the transcript, and it continues for a while. Now we are into the second part, which has its own content. Finally, we have reached the end of the video."

    print(f"\nMerge successful: {merged == expected}")
