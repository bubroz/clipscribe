"""
Generate multiple tweet styles from video intelligence.

Each style targets different audiences and engagement patterns.
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)


class TweetStyleGenerator:
    """Generate tweets in different styles."""

    def __init__(self):
        self.xai_api_key = os.getenv("XAI_API_KEY", "").strip('"').strip("'")
        self.grok_base_url = "https://api.x.ai/v1"
        self.grok_headers = {
            "Authorization": f"Bearer {self.xai_api_key}",
            "Content-Type": "application/json",
        }

    async def generate_all_styles(
        self, title: str, summary: str, entities: list, relationships: list
    ) -> dict:
        """
        Generate all 3 tweet styles.

        Returns dict with 'analyst', 'alarm', 'educator' keys.
        """
        entity_names = [
            e.get("name") if isinstance(e, dict) else getattr(e, "name", "") for e in entities[:5]
        ]
        rel_texts = []
        for r in relationships[:3]:
            if isinstance(r, dict):
                subj = r.get("subject", "")
                pred = r.get("predicate", "")
                obj = r.get("object", "")
            else:
                subj = getattr(r, "subject", "")
                pred = getattr(r, "predicate", "")
                obj = getattr(r, "object", "")
            if subj and pred and obj:
                rel_texts.append(f"{subj} {pred} {obj}")

        styles = {}

        # Generate each style
        styles["analyst"] = await self._generate_analyst_style(
            title, summary[:500], entity_names, rel_texts
        )
        styles["alarm"] = await self._generate_alarm_style(
            title, summary[:500], entity_names, rel_texts
        )
        styles["educator"] = await self._generate_educator_style(
            title, summary[:500], entity_names, rel_texts
        )

        return styles

    async def _generate_analyst_style(self, title, summary, entities, relationships):
        """Policy wonk / analyst style."""

        prompt = f"""Write ONE tweet in ANALYST style (policy wonk):

VIDEO: {title}
SUMMARY: {summary}
ENTITIES: {', '.join(entities)}
KEY FACTS: {'; '.join(relationships)}

ANALYST STYLE:
- Detailed, factual, precise
- Names all key players
- States clear relationships
- "Here's what matters:"
- No emotion, pure intel
- Multiple entities named
- Question is analytical (not provocative)

STRUCTURE:
[Key development/decision]. [2-3 entities named]. [Key relationship or detail]. [Analytical question about implications]?

Example tone:
"Senate Judiciary advances AI bill 12-10. Senators Hawley, Warren, Cruz split on enforcement. Key amendment: Federal oversight vs state control. How does this reconcile with existing tech regulation?"

Write tweet. 270 chars max. Complete sentences. NO hashtags.
"""

        return await self._call_grok(prompt, max_tokens=100, temperature=0.2)

    async def _generate_alarm_style(self, title, summary, entities, relationships):
        """Urgent / breaking / controversial style."""

        prompt = f"""Write ONE tweet in ALARM style (urgent/breaking):

VIDEO: {title}
SUMMARY: {summary}
ENTITIES: {', '.join(entities)}
KEY FACTS: {'; '.join(relationships)}

ALARM STYLE:
- Urgent, attention-grabbing
- "While you weren't looking..."
- "Breaking:" or time pressure
- Implies something surprising
- Question shows stakes/concern
- Makes people think "wait, what?"

STRUCTURE:
[Urgent hook]. [2-3 entities + surprising action]. [Stakes/implication]. [Concerned question]?

Example tone:
"While Congress was on recess, DOD quietly restructured Special Operations Command. SOCOM, JSOC, and CIA coordination protocols changed. No congressional oversight cited. Who authorized this restructuring?"

Write tweet. 270 chars max. Complete sentences. NO hashtags.
"""

        return await self._call_grok(prompt, max_tokens=100, temperature=0.3)

    async def _generate_educator_style(self, title, summary, entities, relationships):
        """Explainer / educator style."""

        prompt = f"""Write ONE tweet in EDUCATOR style (explainer):

VIDEO: {title}
SUMMARY: {summary}
ENTITIES: {', '.join(entities)}
KEY FACTS: {'; '.join(relationships)}

EDUCATOR STYLE:
- "Here's what you need to know:"
- "Let me break this down:"
- Simple, accessible language
- No jargon
- Explains WHY it matters
- Question is educational (not gotcha)

STRUCTURE:
[Simple opener]. [Who's involved]. [What happened]. [Why it matters]. [Learning question]?

Example tone:
"New Pentagon directive on urban training. Secretary Hegseth authorized National Guard in major cities. This changes federal-local military coordination. What does this mean for your city?"

Write tweet. 270 chars max. Complete sentences. NO hashtags. NO jargon.
"""

        return await self._call_grok(prompt, max_tokens=100, temperature=0.3)

    async def _call_grok(self, prompt: str, max_tokens: int = 100, temperature: float = 0.3) -> str:
        """Call Grok API for generation."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                data = {
                    "model": "grok-4-0709",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You write engaging X posts in specific styles.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                response = await client.post(
                    f"{self.grok_base_url}/chat/completions", headers=self.grok_headers, json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    tweet = result["choices"][0]["message"]["content"].strip()
                    tweet = tweet.strip('"').strip("'")  # Remove quotes

                    # Smart truncate if needed
                    if len(tweet) > 270:
                        tweet = self._truncate_smart(tweet, 270)

                    return tweet

        except Exception as e:
            logger.warning(f"Style generation failed: {e}")

        # Fallback - return empty (caller will handle)
        return ""

    def _truncate_smart(self, text: str, max_length: int) -> str:
        """Truncate at sentence boundaries."""
        if len(text) <= max_length:
            return text

        search_text = text[:max_length]

        for ending in [". ", "? ", "! "]:
            last_pos = search_text.rfind(ending)
            if last_pos > max_length * 0.7:
                return text[: last_pos + 1].strip()

        last_space = search_text.rfind(" ")
        if last_space > 0:
            return text[:last_space] + "..."

        return text[: max_length - 3] + "..."
