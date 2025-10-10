"""
Generate X (Twitter) ready content from video intelligence.

Creates "sticky" summaries optimized for engagement:
- Objective and informative (no hype)
- Engaging hook (fact or question)
- Key entities and relationships
- Under 280 characters
- No hashtags (per consultant feedback)
"""

import logging
import os
import shutil
from typing import Optional
from pathlib import Path
import httpx
import json

logger = logging.getLogger(__name__)


class XContentGenerator:
    """
    Generate X-ready content from video intelligence.
    
    Output:
    - tweet.txt: Sticky summary text
    - thumbnail.jpg: Video thumbnail image
    - metadata.json: Generation metadata
    """
    
    def __init__(self):
        # Get Grok API key for summary generation
        self.xai_api_key = os.getenv("XAI_API_KEY", "").strip('"').strip("'")
        if not self.xai_api_key:
            logger.warning("XAI_API_KEY not set - summary generation will fail")
        
        self.grok_base_url = "https://api.x.ai/v1"
        self.grok_headers = {
            "Authorization": f"Bearer {self.xai_api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_sticky_summary(
        self,
        title: str,
        entities: list,
        relationships: list,
        max_length: int = 250  # Leave room for URL
    ) -> str:
        """
        Generate 'sticky' X summary using Grok-4.
        
        Sticky = objective + informative + engaging
        
        Args:
            title: Video title
            entities: List of entity dicts/objects
            relationships: List of relationship dicts/objects
            max_length: Max characters (default: 250 to leave room for URL)
            
        Returns:
            Sticky summary text (<280 chars total with URL)
        """
        # Extract entity names (handle both dict and object)
        entity_names = []
        for e in entities[:5]:  # Top 5 entities
            name = e.get('name') if isinstance(e, dict) else getattr(e, 'name', str(e))
            entity_names.append(name)
        
        # Extract relationships
        rel_texts = []
        for r in relationships[:3]:  # Top 3 relationships
            if isinstance(r, dict):
                subj = r.get('subject', '')
                pred = r.get('predicate', '')
                obj = r.get('object', '')
            else:
                subj = getattr(r, 'subject', '')
                pred = getattr(r, 'predicate', '')
                obj = getattr(r, 'object', '')
            
            if subj and pred and obj:
                rel_texts.append(f"{subj} {pred} {obj}")
        
        # Build prompt for Grok
        prompt = f"""Write a KILLER X post that stops people mid-scroll.

VIDEO: {title}
ENTITIES: {', '.join(entity_names[:5])}
RELATIONSHIPS: {'; '.join(rel_texts[:2])}

YOUR MISSION: Make this IMPOSSIBLE to ignore.

FORMULA:
1. PUNCH THEM (10-20 words):
   - Shocking fact they didn't know
   - Question that makes them think "wait, what?"
   - Contradiction that seems impossible
   
2. GIVE CONTEXT (15-25 words):
   - Who's involved (name 3-4 key entities)
   - What happened (1-2 key relationships)
   - Why it matters (stakes/implications)
   
3. HOOK THEM (8-12 words):
   - Question they MUST answer
   - Cliffhanger that demands a reply
   - "What do you think?" is BORING - be specific

EXAMPLES OF PUNCHES:
- "While everyone was distracted by [X], [entity] quietly [shocking action]."
- "[Entity] just announced something that changes everything."
- "Three things about [topic] that nobody's talking about:"

RULES:
- {max_length} characters MAX
- Complete sentences ONLY (no cuts mid-sentence)
- NO generic questions ("What are your thoughts?")
- NO hashtags
- NO buzzwords or jargon
- Read like a human wrote it, not AI

Write ONE tweet. Nothing else. Make it fucking engaging.
"""
        
        try:
            # Call Grok-4 for summary generation
            async with httpx.AsyncClient(timeout=60) as client:
                data = {
                    "model": "grok-4-0709",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert at creating engaging, objective social media content. Generate sticky summaries that inform and provoke thought."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,  # Slightly creative but consistent
                    "max_tokens": 100  # Summary should be short
                }
                
                response = await client.post(
                    f"{self.grok_base_url}/chat/completions",
                    headers=self.grok_headers,
                    json=data
                )
                
                if response.status_code != 200:
                    raise Exception(f"Grok API error: {response.status_code}")
                
                result = response.json()
                summary = result["choices"][0]["message"]["content"].strip()
                
                # Remove quotes if Grok added them
                summary = summary.strip('"').strip("'")
                
                # Enforce length limit with smart truncation
                if len(summary) > max_length:
                    logger.warning(f"Summary too long ({len(summary)} chars), smart truncating")
                    summary = self._truncate_smart(summary, max_length)
                
                logger.info(f"Generated sticky summary: {len(summary)} chars")
                return summary
                
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            # Fallback to simple summary
            return self._generate_fallback_summary(title, entity_names, rel_texts, max_length)
    
    def _generate_fallback_summary(
        self,
        title: str,
        entities: list,
        relationships: list,
        max_length: int
    ) -> str:
        """Fallback summary if Grok fails."""
        # Simple template-based summary
        entities_str = ", ".join(entities[:3])
        summary = f"{title}. Key: {entities_str}"
        
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary
    
    def save_x_draft(
        self,
        summary: str,
        video_url: str,
        thumbnail_path: Optional[str],
        output_dir: Path
    ) -> dict:
        """
        Save X draft as tweet.txt + thumbnail.jpg.
        
        Args:
            summary: Generated summary text
            video_url: Original video URL to append
            thumbnail_path: Path to thumbnail image
            output_dir: Where to save draft
            
        Returns:
            Dict with paths to created files
        """
        # Create x_draft subdirectory
        draft_dir = output_dir / "x_draft"
        draft_dir.mkdir(parents=True, exist_ok=True)
        
        # Create tweet text (summary + URL)
        tweet_text = f"{summary}\n\n{video_url}"
        
        # Verify total length
        if len(tweet_text) > 280:
            logger.warning(f"Tweet too long ({len(tweet_text)} chars)! Truncating summary...")
            # Recalculate summary length
            max_summary = 280 - len(video_url) - 3  # 3 for \n\n
            summary = summary[:max_summary-3] + "..."
            tweet_text = f"{summary}\n\n{video_url}"
        
        # Save tweet text
        tweet_file = draft_dir / "tweet.txt"
        tweet_file.write_text(tweet_text)
        
        logger.info(f"Saved X draft: {tweet_file}")
        logger.info(f"  Character count: {len(tweet_text)}/280")
        
        # Copy thumbnail if provided
        thumbnail_dest = None
        if thumbnail_path and Path(thumbnail_path).exists():
            thumbnail_dest = draft_dir / "thumbnail.jpg"
            shutil.copy(thumbnail_path, thumbnail_dest)
            logger.info(f"Copied thumbnail: {thumbnail_dest}")
        
        # Save metadata
        metadata = {
            'summary': summary,
            'url': video_url,
            'character_count': len(tweet_text),
            'generated_at': str(Path(tweet_file).stat().st_mtime),
            'has_thumbnail': thumbnail_dest is not None
        }
        
        metadata_file = draft_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            'tweet_file': str(tweet_file),
            'thumbnail': str(thumbnail_dest) if thumbnail_dest else None,
            'metadata_file': str(metadata_file),
            'directory': str(draft_dir)
        }
    
    def find_thumbnail(self, output_dir: Path) -> Optional[str]:
        """
        Find thumbnail file in output directory.
        
        yt-dlp saves thumbnails as: VideoTitle-videoid.jpg/png/webp
        
        Args:
            output_dir: Directory to search
            
        Returns:
            Path to thumbnail if found
        """
        # Common thumbnail extensions
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            thumbnails = list(output_dir.glob(f'*{ext}'))
            if thumbnails:
                return str(thumbnails[0])
        
        return None

    def _truncate_smart(self, text: str, max_length: int) -> str:
        """Truncate intelligently at sentence boundaries."""
        if len(text) <= max_length:
            return text
        
        search_text = text[:max_length]
        
        for ending in ['. ', '? ', '! ']:
            last_pos = search_text.rfind(ending)
            if last_pos > max_length * 0.7:
                return text[:last_pos + 1].strip()
        
        last_space = search_text.rfind(' ')
        if last_space > 0:
            return text[:last_space] + '...'
        
        return text[:max_length-3] + '...'


async def test_x_generator():
    """Test X content generation."""
    from ..models import VideoIntelligence, VideoMetadata, EnhancedEntity, Relationship
    
    entities = [
        {'name': 'The Stoic Viking', 'type': 'PERSON'},
        {'name': 'Barbell Apparel', 'type': 'ORGANIZATION'},
        {'name': 'Valhalla VFT', 'type': 'PERSON'}
    ]
    
    relationships = [
        {'subject': 'The Stoic Viking', 'predicate': 'partners with', 'object': 'Barbell Apparel'}
    ]
    
    generator = XContentGenerator()
    
    summary = await generator.generate_sticky_summary(
        "Partnering with Barbell Apparel",
        entities,
        relationships
    )
    
    print(f"Generated summary ({len(summary)} chars):")
    print(summary)
    
    draft_files = generator.save_x_draft(
        summary,
        "https://youtube.com/watch?v=test",
        None,
        Path("output/test_x_draft")
    )
    
    print(f"\nSaved to: {draft_files['directory']}")
    print(f"Tweet file: {draft_files['tweet_file']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_x_generator())
