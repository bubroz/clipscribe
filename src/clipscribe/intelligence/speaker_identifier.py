"""
AI-Powered Speaker Identification

Uses Grok-4 to infer speaker identities from transcript context.
Analyzes what speakers say, how they're addressed, and contextual clues.

For Station10.media premium tier - adds speaker names to generic labels.
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class SpeakerIdentity:
    """Identified speaker information."""

    speaker_label: str  # e.g., "SPEAKER_00"
    identified_name: Optional[str]  # e.g., "Tim Dillon"
    confidence: float  # 0.0-1.0
    role: Optional[str]  # e.g., "Host", "Guest", "Panelist"
    evidence: List[str]  # Context clues that led to identification


class SpeakerIdentifier:
    """
    Identify speakers using Grok-4 context analysis.

    Analyzes:
    - What each speaker says (content, style, topics)
    - How other speakers address them (names, titles, roles)
    - Video metadata (title, description, channel)
    - Linguistic patterns (formal/informal, expertise level)
    - Self-references ("I'm...", "As a...")
    """

    def __init__(self, grok_model: str = "grok-4-fast-reasoning", confidence_threshold: float = 0.70):
        """
        Initialize speaker identifier.

        Args:
            grok_model: Grok model to use
            confidence_threshold: Only return IDs above this confidence
        """
        self.grok_model = grok_model
        self.confidence_threshold = confidence_threshold

        # Get API key
        self.xai_api_key = os.getenv("XAI_API_KEY", "").strip('"').strip("'")
        if not self.xai_api_key:
            raise ValueError("XAI_API_KEY required for speaker identification")

        self.grok_base_url = "https://api.x.ai/v1"
        self.grok_headers = {
            "Authorization": f"Bearer {self.xai_api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"SpeakerIdentifier initialized with {grok_model}")

    async def identify_speakers(
        self,
        transcript_with_speakers: str,
        speaker_segments: List[Dict[str, Any]],
        video_metadata: Optional[Dict[str, Any]] = None,
        manual_overrides: Optional[Dict[str, str]] = None,
    ) -> List[SpeakerIdentity]:
        """
        Identify speakers from transcript context.

        Args:
            transcript_with_speakers: Full transcript with [SPEAKER_XX] labels
            speaker_segments: List of speaker segment info (from diarization)
            video_metadata: Video title, description, channel (helps context)
            manual_overrides: Dict of speaker_label -> name (user-provided)

        Returns:
            List of SpeakerIdentity objects with names and confidence
        """

        # Apply manual overrides first
        if manual_overrides:
            logger.info(f"Applying {len(manual_overrides)} manual speaker overrides")
            overridden = []
            for segment in speaker_segments:
                label = segment.get("speaker", "")
                if label in manual_overrides:
                    overridden.append(
                        SpeakerIdentity(
                            speaker_label=label,
                            identified_name=manual_overrides[label],
                            confidence=1.0,
                            role="User-specified",
                            evidence=["Manual override by user"],
                        )
                    )

            # Remove overridden speakers from auto-identification
            remaining_speakers = [
                s for s in speaker_segments if s.get("speaker") not in manual_overrides
            ]
        else:
            overridden = []
            remaining_speakers = speaker_segments

        # If no speakers left to identify
        if not remaining_speakers:
            return overridden

        # Build context for Grok
        context = self._build_identification_context(
            transcript_with_speakers, remaining_speakers, video_metadata
        )

        # Ask Grok to identify speakers
        identified = await self._identify_with_grok(context, remaining_speakers)

        # Combine manual + AI identified
        return overridden + identified

    def _build_identification_context(
        self, transcript: str, speakers: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Build context string for Grok analysis."""

        context_parts = []

        # Video metadata provides major clues
        if metadata:
            context_parts.append("VIDEO CONTEXT:")
            context_parts.append(f"Title: {metadata.get('title', 'Unknown')}")
            context_parts.append(f"Channel: {metadata.get('channel', 'Unknown')}")
            if metadata.get("description"):
                # First 500 chars of description
                desc = metadata["description"][:500]
                context_parts.append(f"Description: {desc}...")
            context_parts.append("")

        # Speaker statistics
        context_parts.append("SPEAKERS DETECTED:")
        for spk in speakers:
            label = spk.get("speaker", "UNKNOWN")
            time = spk.get("total_time", 0)
            segs = spk.get("segments", 0)
            context_parts.append(f"{label}: {time:.1f}s speaking time, {segs} segments")
        context_parts.append("")

        # Transcript (first 15,000 chars to stay under token limits)
        context_parts.append("TRANSCRIPT EXCERPT:")
        context_parts.append(transcript[:15000])
        if len(transcript) > 15000:
            context_parts.append("\n[... transcript continues ...]")

        return "\n".join(context_parts)

    async def _identify_with_grok(
        self, context: str, speakers: List[Dict[str, Any]]
    ) -> List[SpeakerIdentity]:
        """
        Use Grok to identify speakers from context.

        Returns speaker identifications with confidence scores.
        """

        speaker_labels = [s.get("speaker", "") for s in speakers]

        prompt = f"""Analyze this video transcript and identify each speaker.

{context}

For each speaker label ({', '.join(speaker_labels)}), provide:

1. **Most likely identity**: Full name or clear role
2. **Confidence**: 0-100% (be conservative - only confident IDs)
3. **Role**: Host, guest, panelist, interviewer, subject, etc.
4. **Evidence**: Specific quotes or context clues that reveal identity

Guidelines:
- Only identify when CONFIDENT (60%+ confidence)
- Use direct evidence: "As Senator X said..." = Senator X
- Pay attention to introductions, names mentioned, how people are addressed
- If uncertain, say "Unknown" with low confidence
- For roles, be specific: "Host" vs "Guest" vs "Subject of discussion"
- Consider video title/description as context

Return JSON array:
[
  {{
    "speaker_label": "SPEAKER_00",
    "identified_name": "Tim Dillon" or null,
    "confidence": 95,
    "role": "Host",
    "evidence": [
      "Introduces show: 'I'm Tim, welcome to my show'",
      "Other speaker addresses him as 'Tim'",
      "Channel is 'The Tim Dillon Show'"
    ]
  }},
  ...
]

Be conservative. Unknown is better than incorrect.
"""

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                data = {
                    "model": self.grok_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert at identifying speakers from context. Be conservative - only identify when confident.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,  # Low temp for factual inference
                    "max_tokens": 2048,
                    "response_format": {"type": "json_object"},
                }

                response = await client.post(
                    f"{self.grok_base_url}/chat/completions", headers=self.grok_headers, json=data
                )

                if response.status_code != 200:
                    logger.error(f"Grok API error: {response.status_code} - {response.text}")
                    return self._fallback_unknown_speakers(speakers)

                result_json = response.json()
                content = result_json["choices"][0]["message"]["content"]

                # Parse Grok's response
                grok_identifications = json.loads(content)

                # Handle both array and object with "speakers" key
                if isinstance(grok_identifications, dict):
                    if "speakers" in grok_identifications:
                        identifications = grok_identifications["speakers"]
                    elif "identifications" in grok_identifications:
                        identifications = grok_identifications["identifications"]
                    else:
                        # Assume it's a single-speaker dict, wrap in array
                        identifications = [grok_identifications]
                else:
                    identifications = grok_identifications

                # Convert to SpeakerIdentity objects
                results = []
                for ident in identifications:
                    conf = ident.get("confidence", 0) / 100.0  # Convert % to 0-1

                    # Only include if above threshold
                    if conf >= self.confidence_threshold:
                        results.append(
                            SpeakerIdentity(
                                speaker_label=ident["speaker_label"],
                                identified_name=ident.get("identified_name"),
                                confidence=conf,
                                role=ident.get("role"),
                                evidence=ident.get("evidence", []),
                            )
                        )
                    else:
                        # Below threshold - mark as unknown
                        results.append(
                            SpeakerIdentity(
                                speaker_label=ident["speaker_label"],
                                identified_name=None,
                                confidence=conf,
                                role=ident.get("role"),
                                evidence=["Confidence below threshold"],
                            )
                        )

                logger.info(
                    f"Identified {sum(1 for r in results if r.identified_name)} of {len(results)} speakers"
                )
                return results

        except Exception as e:
            logger.error(f"Speaker identification failed: {e}")
            return self._fallback_unknown_speakers(speakers)

    def _fallback_unknown_speakers(self, speakers: List[Dict[str, Any]]) -> List[SpeakerIdentity]:
        """Fallback when Grok identification fails."""
        return [
            SpeakerIdentity(
                speaker_label=s.get("speaker", "UNKNOWN"),
                identified_name=None,
                confidence=0.0,
                role="Unknown",
                evidence=["Identification failed"],
            )
            for s in speakers
        ]

    def format_transcript_with_names(
        self, original_transcript: str, identifications: List[SpeakerIdentity]
    ) -> str:
        """
        Replace speaker labels with identified names in transcript.

        Args:
            original_transcript: Transcript with [SPEAKER_00], [SPEAKER_01], etc.
            identifications: Speaker identities from identify_speakers()

        Returns:
            Transcript with [Name] or [SPEAKER_XX (Name)] labels
        """

        # Build replacement map
        replacements = {}
        for ident in identifications:
            label = ident.speaker_label

            if ident.identified_name and ident.confidence >= self.confidence_threshold:
                # High confidence - use name only
                if ident.role:
                    replacements[label] = f"{ident.identified_name} ({ident.role})"
                else:
                    replacements[label] = ident.identified_name
            elif ident.identified_name:
                # Low confidence - show both
                replacements[label] = f"{label} (possibly {ident.identified_name})"
            else:
                # Unknown - keep label
                replacements[label] = label

        # Replace in transcript
        result = original_transcript
        for label, replacement in replacements.items():
            result = result.replace(f"[{label}]", f"[{replacement}]")
            result = result.replace(f"{label}:", f"{replacement}:")

        return result


async def test_speaker_identification():
    """Test speaker identification on a known video."""

    # Example test transcript
    test_transcript = """
[SPEAKER_00]: Hey everyone, I'm Tim. Welcome to the show.
[SPEAKER_01]: Thanks for having me, Tim.
[SPEAKER_00]: So Congresswoman Greene, let's talk about the Epstein files.
[SPEAKER_01]: Well, as a member of Congress, I've been pushing for transparency...
[SPEAKER_00]: That's interesting. What do you think about AIPAC's influence?
[SPEAKER_01]: As someone who's been critical of foreign policy...
"""

    test_speakers = [
        {"speaker": "SPEAKER_00", "total_time": 2400, "segments": 45},
        {"speaker": "SPEAKER_01", "total_time": 1800, "segments": 32},
    ]

    test_metadata = {
        "title": "Marjorie Taylor Greene Emergency Podcast | The Tim Dillon Show #465",
        "channel": "The Tim Dillon Show",
        "description": "Tim Dillon sits down with Congresswoman Marjorie Taylor Greene...",
    }

    identifier = SpeakerIdentifier()

    print("Testing speaker identification...")
    print("\nContext:")
    print(f"  Title: {test_metadata['title']}")
    print(f"  Speakers: {len(test_speakers)}")
    print("\nTranscript sample:")
    print(test_transcript[:200] + "...")
    print("\nIdentifying speakers with Grok...")

    identities = await identifier.identify_speakers(
        transcript_with_speakers=test_transcript,
        speaker_segments=test_speakers,
        video_metadata=test_metadata,
    )

    print("\n" + "=" * 80)
    print("SPEAKER IDENTIFICATION RESULTS")
    print("=" * 80)

    for ident in identities:
        print(f"\n{ident.speaker_label}:")
        print(f"  Name: {ident.identified_name or 'Unknown'}")
        print(f"  Confidence: {ident.confidence:.1%}")
        print(f"  Role: {ident.role or 'Unknown'}")
        print("  Evidence:")
        for evidence in ident.evidence:
            print(f"    - {evidence}")

    # Test transcript formatting
    print("\n" + "=" * 80)
    print("FORMATTED TRANSCRIPT (with names)")
    print("=" * 80)
    print(identifier.format_transcript_with_names(test_transcript, identities))


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_speaker_identification())
