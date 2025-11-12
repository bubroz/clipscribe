"""
Video Knowledge Base Manager

Manages xAI Collections API for building searchable knowledge base from processed videos.
Enables cross-video entity linking, temporal intelligence, and semantic search.

Collections API introduced August 2025.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import VideoIntelligence
from ..retrievers.grok_client import GrokAPIClient, GrokAPIError

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from knowledge base search."""

    video_id: str
    title: str
    relevance_score: float
    matched_content: str
    timestamp: Optional[float] = None
    entities: List[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class VideoReference:
    """Reference to a video containing an entity."""

    video_id: str
    title: str
    entity_mentions: int
    contexts: List[str]
    timestamps: List[float]
    confidence: float


class VideoKnowledgeBase:
    """
    Manages searchable knowledge base of processed videos using Collections API.

    Features:
    - Upload processed transcripts to Collections
    - Semantic search across all videos
    - Cross-reference entities across videos
    - Build temporal intelligence from collection
    - Entity co-occurrence analysis

    Collection structure:
    - Each video uploaded as a file
    - Files added to collection
    - Semantic search via embeddings
    - Cross-video entity linking
    """

    def __init__(
        self,
        api_key: str,
        collection_id: Optional[str] = None,
        collection_name: str = "clipscribe-videos",
        model: str = "grok-4-fast-reasoning",
    ):
        """
        Initialize knowledge base manager.

        Args:
            api_key: xAI API key
            collection_id: Existing collection ID (will create if None)
            collection_name: Name for new collection
            model: Model to use for embeddings
        """
        self.client = GrokAPIClient(api_key=api_key)
        self.collection_id = collection_id
        self.collection_name = collection_name
        self.model = model

        # Track uploaded videos
        self.video_files: Dict[str, str] = {}  # video_id -> file_id

        logger.info(f"VideoKnowledgeBase initialized (collection: {collection_id or 'new'})")

    async def initialize_collection(self) -> str:
        """
        Initialize or retrieve collection.

        Returns:
            Collection ID
        """
        if self.collection_id:
            # Verify existing collection
            try:
                collections = await self.client.list_collections()
                collection_exists = any(
                    c.get("id") == self.collection_id for c in collections.get("data", [])
                )

                if collection_exists:
                    logger.info(f"Using existing collection: {self.collection_id}")
                    return self.collection_id
                else:
                    logger.warning(f"Collection {self.collection_id} not found, creating new")

            except GrokAPIError as e:
                logger.warning(f"Error verifying collection: {e}, creating new")

        # Create new collection
        try:
            result = await self.client.create_collection(
                name=self.collection_name,
                description="ClipScribe video intelligence knowledge base",
                model=self.model,
            )

            self.collection_id = result.get("id")
            logger.info(f"Created new collection: {self.collection_id}")

            return self.collection_id

        except GrokAPIError as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    async def add_video_to_knowledge_base(
        self,
        video_id: str,
        transcript: str,
        intelligence: VideoIntelligence,
        temp_dir: Optional[Path] = None,
    ) -> str:
        """
        Add processed video to knowledge base.

        Args:
            video_id: Video identifier
            transcript: Full transcript text
            intelligence: Extracted intelligence
            temp_dir: Temporary directory for file creation

        Returns:
            File ID of uploaded content
        """
        # Ensure collection exists
        if not self.collection_id:
            await self.initialize_collection()

        # Create structured document for upload
        document = self._create_video_document(video_id, transcript, intelligence)

        # Save to temporary file
        temp_dir = temp_dir or Path("output/.kb_temp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        doc_path = temp_dir / f"{video_id}.json"
        with open(doc_path, "w", encoding="utf-8") as f:
            json.dump(document, f, indent=2, ensure_ascii=False)

        try:
            # Upload file
            file_result = await self.client.upload_file(file_path=doc_path, purpose="assistants")

            file_id = file_result.get("id")
            logger.info(f"Uploaded video {video_id} as file {file_id}")

            # Add to collection
            await self.client.add_files_to_collection(
                collection_id=self.collection_id, file_ids=[file_id]
            )

            logger.info(f"Added file {file_id} to collection {self.collection_id}")

            # Track video
            self.video_files[video_id] = file_id

            # Clean up temp file
            doc_path.unlink()

            return file_id

        except GrokAPIError as e:
            logger.error(f"Failed to add video to knowledge base: {e}")
            # Clean up temp file
            if doc_path.exists():
                doc_path.unlink()
            raise

    async def search_knowledge_base(
        self, query: str, filters: Optional[Dict[str, Any]] = None, top_k: int = 5
    ) -> List[SearchResult]:
        """
        Search knowledge base for relevant videos.

        Args:
            query: Search query
            filters: Optional filters (date range, entity types, etc.)
            top_k: Number of results to return

        Returns:
            List of search results with relevance scores
        """
        if not self.collection_id:
            logger.warning("No collection initialized")
            return []

        try:
            # Search collection
            results = await self.client.search_collection(
                collection_id=self.collection_id, query=query, top_k=top_k
            )

            # Parse results
            return self._parse_search_results(results, filters)

        except GrokAPIError as e:
            logger.error(f"Knowledge base search failed: {e}")
            return []

    async def cross_reference_entity(
        self, entity_name: str, entity_type: Optional[str] = None
    ) -> List[VideoReference]:
        """
        Find all videos mentioning a specific entity.

        Args:
            entity_name: Entity to search for
            entity_type: Optional entity type filter

        Returns:
            List of video references containing the entity
        """
        query = f"entity: {entity_name}"
        if entity_type:
            query += f" type:{entity_type}"

        search_results = await self.search_knowledge_base(query, top_k=20)

        # Group by video and extract references
        video_refs = []
        for result in search_results:
            # Parse entity mentions from result
            video_ref = VideoReference(
                video_id=result.video_id,
                title=result.title,
                entity_mentions=result.matched_content.count(entity_name),
                contexts=[result.matched_content],
                timestamps=[result.timestamp] if result.timestamp else [],
                confidence=result.relevance_score,
            )
            video_refs.append(video_ref)

        logger.info(f"Found {len(video_refs)} videos mentioning '{entity_name}'")
        return video_refs

    async def find_entity_cooccurrences(self, entity1: str, entity2: str) -> List[VideoReference]:
        """
        Find videos where two entities are mentioned together.

        Args:
            entity1: First entity
            entity2: Second entity

        Returns:
            Videos where both entities appear
        """
        query = f"{entity1} AND {entity2}"
        results = await self.search_knowledge_base(query, top_k=10)

        # Convert to video references
        video_refs = []
        for result in results:
            video_ref = VideoReference(
                video_id=result.video_id,
                title=result.title,
                entity_mentions=2,  # Both entities present
                contexts=[result.matched_content],
                timestamps=[],
                confidence=result.relevance_score,
            )
            video_refs.append(video_ref)

        logger.info(f"Found {len(video_refs)} videos with both '{entity1}' and '{entity2}'")
        return video_refs

    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.

        Returns:
            Collection statistics
        """
        if not self.collection_id:
            return {"initialized": False}

        try:
            # Get collection info
            collections = await self.client.list_collections()

            collection_data = next(
                (c for c in collections.get("data", []) if c.get("id") == self.collection_id), None
            )

            if not collection_data:
                return {"initialized": False}

            return {
                "initialized": True,
                "collection_id": self.collection_id,
                "name": collection_data.get("name"),
                "files_count": len(self.video_files),
                "videos": list(self.video_files.keys()),
                "model": self.model,
            }

        except GrokAPIError as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"initialized": False, "error": str(e)}

    def _create_video_document(
        self, video_id: str, transcript: str, intelligence: VideoIntelligence
    ) -> Dict[str, Any]:
        """
        Create structured document for knowledge base.

        Args:
            video_id: Video identifier
            transcript: Full transcript
            intelligence: Extracted intelligence

        Returns:
            Structured document
        """
        return {
            "video_id": video_id,
            "metadata": {
                "title": intelligence.metadata.title,
                "channel": intelligence.metadata.channel,
                "published_at": intelligence.metadata.published_at,
                "duration": intelligence.metadata.duration,
                "url": intelligence.metadata.url,
            },
            "transcript": transcript,
            "entities": [
                {"name": e.name, "type": e.type, "confidence": e.confidence, "evidence": e.evidence}
                for e in intelligence.entities
            ],
            "relationships": [
                {
                    "subject": r.subject,
                    "predicate": r.predicate,
                    "object": r.object,
                    "evidence": r.evidence,
                    "confidence": r.confidence,
                }
                for r in intelligence.relationships
            ],
            "topics": [
                {"name": t.name, "relevance": t.relevance, "time_range": t.time_range}
                for t in intelligence.topics
            ],
            "summary": intelligence.summary,
            "indexed_at": datetime.now().isoformat(),
        }

    def _parse_search_results(
        self, results: Dict[str, Any], filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Parse search results from Collections API.

        Args:
            results: Raw API results
            filters: Optional filters to apply

        Returns:
            List of SearchResult objects
        """
        search_results = []

        for result in results.get("results", []):
            # Extract relevant fields
            video_id = result.get("metadata", {}).get("video_id", "unknown")
            title = result.get("metadata", {}).get("title", "Unknown")
            score = result.get("score", 0.0)
            content = result.get("content", "")

            # Apply filters if provided
            if filters:
                if not self._apply_filters(result, filters):
                    continue

            search_result = SearchResult(
                video_id=video_id,
                title=title,
                relevance_score=score,
                matched_content=content[:500],  # Truncate
                entities=result.get("metadata", {}).get("entities", []),
                metadata=result.get("metadata", {}),
            )

            search_results.append(search_result)

        return search_results

    def _apply_filters(self, result: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Apply filters to search result."""
        # Example filter logic
        metadata = result.get("metadata", {})

        if "min_date" in filters:
            pub_date = metadata.get("published_at", 0)
            if pub_date < filters["min_date"]:
                return False

        if "entity_types" in filters:
            entities = metadata.get("entities", [])
            entity_types = {e.get("type") for e in entities}
            if not entity_types.intersection(filters["entity_types"]):
                return False

        return True

    async def close(self):
        """Close the API client."""
        await self.client.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
