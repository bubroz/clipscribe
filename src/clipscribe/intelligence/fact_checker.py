"""
Grok Fact Checker using Server-Side Tools

Leverages xAI's server-side tools (October 2025) for fact-checking and enrichment:
- web_search: Search the web for factual verification
- x_search: Search X/Twitter for real-time information
- code_execution: Verify calculations and data
- collections_search: Search knowledge base
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ..retrievers.grok_client import GrokAPIClient, GrokAPIError
from ..schemas_grok import Entity, Relationship

logger = logging.getLogger(__name__)


class ToolType(str, Enum):
    """Available server-side tools."""

    WEB_SEARCH = "web_search"
    X_SEARCH = "x_search"
    CODE_EXECUTION = "code_execution"
    COLLECTIONS_SEARCH = "collections_search"


@dataclass
class FactCheckResult:
    """Result of fact-checking operation."""

    entity_name: str
    original_confidence: float
    verified: bool
    verification_confidence: float
    sources: List[str]
    evidence: List[str]
    tool_used: str
    enrichment_data: Optional[Dict[str, Any]] = None


class GrokFactChecker:
    """
    Fact-check entities and relationships using Grok's server-side tools.

    Available tools (October 2025):
    - web_search: Search web for verification
    - x_search: Search X/Twitter for real-time context
    - code_execution: Verify calculations/statistics
    - collections_search: Search our knowledge base

    Features:
    - Real-time fact verification
    - Cross-reference with web/X data
    - Automatic tool selection
    - Evidence aggregation
    """

    def __init__(
        self,
        api_key: str,
        enable_web_search: bool = True,
        enable_x_search: bool = True,
        enable_code_execution: bool = False,
        collection_id: Optional[str] = None,
        model: str = "grok-4-1-fast-reasoning",
    ):
        """
        Initialize fact checker.

        Args:
            api_key: xAI API key
            enable_web_search: Enable web search tool
            enable_x_search: Enable X/Twitter search tool
            enable_code_execution: Enable code execution tool
            collection_id: Collection ID for knowledge base search
            model: Grok model to use
        """
        self.client = GrokAPIClient(api_key=api_key)
        self.enable_web_search = enable_web_search
        self.enable_x_search = enable_x_search
        self.enable_code_execution = enable_code_execution
        self.collection_id = collection_id
        self.model = model

        # Build available tools list
        self.available_tools = self._build_tools_list()

        logger.info(
            f"GrokFactChecker initialized with {len(self.available_tools)} tools: "
            f"{[t['type'] for t in self.available_tools]}"
        )

    def _build_tools_list(self) -> List[Dict[str, Any]]:
        """
        Build list of available tools based on configuration.

        Returns:
            List of tool specifications
        """
        tools = []

        if self.enable_web_search:
            tools.append(
                {
                    "type": ToolType.WEB_SEARCH.value,
                    "description": "Search the web for factual verification and current information",
                }
            )

        if self.enable_x_search:
            tools.append(
                {
                    "type": ToolType.X_SEARCH.value,
                    "description": "Search X/Twitter for real-time information and trending topics",
                }
            )

        if self.enable_code_execution:
            tools.append(
                {
                    "type": ToolType.CODE_EXECUTION.value,
                    "description": "Execute code to verify calculations, statistics, and data analysis",
                }
            )

        if self.collection_id:
            tools.append(
                {
                    "type": ToolType.COLLECTIONS_SEARCH.value,
                    "description": "Search our knowledge base of processed videos for related information",
                    "collection_id": self.collection_id,
                }
            )

        return tools

    async def fact_check_entity(
        self, entity: Entity, context: str = "", auto_select_tool: bool = True
    ) -> FactCheckResult:
        """
        Fact-check a single entity using appropriate tools.

        Args:
            entity: Entity to fact-check
            context: Additional context (e.g., surrounding transcript)
            auto_select_tool: Let Grok automatically select best tool

        Returns:
            FactCheckResult with verification status
        """
        # Build verification prompt
        prompt = self._build_verification_prompt(entity, context)

        messages = [
            {
                "role": "system",
                "content": "You are a fact-checking assistant. Use available tools to verify information and provide evidence. Be thorough but conservative.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            # Use tools with auto-selection
            response = await self.client.chat_completion(
                messages=messages,
                model=self.model,
                tools=self.available_tools,
                tool_choice="auto" if auto_select_tool else "required",
                temperature=0.1,
            )

            # Parse tool results
            return self._parse_verification_response(entity, response)

        except GrokAPIError as e:
            logger.error(f"Fact-checking failed for {entity.name}: {e}")
            return FactCheckResult(
                entity_name=entity.name,
                original_confidence=entity.confidence,
                verified=False,
                verification_confidence=entity.confidence,
                sources=[],
                evidence=[entity.evidence],
                tool_used="none",
            )

    async def fact_check_entities(
        self,
        entities: List[Entity],
        use_x_search: bool = True,
        use_web_search: bool = True,
        confidence_threshold: float = 0.7,
    ) -> List[FactCheckResult]:
        """
        Fact-check multiple entities.

        Args:
            entities: List of entities to verify
            use_x_search: Use X/Twitter search
            use_web_search: Use web search
            confidence_threshold: Only check entities below this confidence

        Returns:
            List of fact-check results
        """
        results = []

        # Filter entities that need fact-checking
        entities_to_check = [e for e in entities if e.confidence < confidence_threshold]

        logger.info(
            f"Fact-checking {len(entities_to_check)}/{len(entities)} entities "
            f"below confidence threshold {confidence_threshold}"
        )

        for entity in entities_to_check:
            result = await self.fact_check_entity(entity)
            results.append(result)

        return results

    async def enrich_with_current_info(
        self, entity: Entity, search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enrich entity with current information from web/X.

        Args:
            entity: Entity to enrich
            search_query: Custom search query (defaults to entity name)

        Returns:
            Enrichment data with current context
        """
        query = search_query or f"{entity.name} {entity.type.lower()} latest news"

        messages = [
            {
                "role": "system",
                "content": "You are an information enrichment assistant. Find current, relevant information about the given entity.",
            },
            {"role": "user", "content": f"Find latest information about: {query}"},
        ]

        try:
            response = await self.client.chat_completion(
                messages=messages,
                model=self.model,
                tools=self.available_tools,
                tool_choice="auto",
                temperature=0.1,
            )

            # Extract enrichment data
            return self._extract_enrichment_data(response)

        except GrokAPIError as e:
            logger.error(f"Enrichment failed for {entity.name}: {e}")
            return {}

    async def verify_relationship(
        self, relationship: Relationship, context: str = ""
    ) -> FactCheckResult:
        """
        Verify a relationship between entities.

        Args:
            relationship: Relationship to verify
            context: Additional context

        Returns:
            FactCheckResult with verification status
        """
        prompt = f"""
        Verify this relationship:
        Subject: {relationship.subject}
        Predicate: {relationship.predicate}
        Object: {relationship.object}

        Evidence provided: {relationship.evidence}

        Context: {context}

        Is this relationship factually accurate? Provide evidence.
        """

        messages = [
            {
                "role": "system",
                "content": "You are a fact-checking assistant. Verify relationships between entities using available tools.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.client.chat_completion(
                messages=messages,
                model=self.model,
                tools=self.available_tools,
                tool_choice="auto",
                temperature=0.1,
            )

            # Parse verification result
            return self._parse_relationship_verification(relationship, response)

        except GrokAPIError as e:
            logger.error(f"Relationship verification failed: {e}")
            return FactCheckResult(
                entity_name=f"{relationship.subject} → {relationship.object}",
                original_confidence=relationship.confidence,
                verified=False,
                verification_confidence=relationship.confidence,
                sources=[],
                evidence=[relationship.evidence],
                tool_used="none",
            )

    def _build_verification_prompt(self, entity: Entity, context: str) -> str:
        """Build verification prompt for entity."""
        return f"""
        Verify this entity:
        Name: {entity.name}
        Type: {entity.type}
        Confidence: {entity.confidence}
        Evidence: {entity.evidence}

        Context: {context}

        Use available tools to verify this entity is accurate. Provide sources.
        """

    def _parse_verification_response(
        self, entity: Entity, response: Dict[str, Any]
    ) -> FactCheckResult:
        """
        Parse verification response from Grok.

        Args:
            entity: Original entity
            response: API response with tool results

        Returns:
            FactCheckResult
        """
        # Extract tool calls and results
        tool_calls = response.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        sources = []
        evidence = [entity.evidence]
        tool_used = "none"

        # Process tool calls
        for tool_call in tool_calls:
            tool_type = tool_call.get("function", {}).get("name", "")
            tool_result = tool_call.get("function", {}).get("arguments", {})

            if tool_type:
                tool_used = tool_type

                # Extract sources from tool results
                if isinstance(tool_result, dict):
                    if "sources" in tool_result:
                        sources.extend(tool_result["sources"])
                    if "results" in tool_result:
                        for result in tool_result.get("results", []):
                            if isinstance(result, dict) and "url" in result:
                                sources.append(result["url"])

        # Simple heuristic: if we found sources, consider it verified
        verified = len(sources) > 0
        verification_confidence = (
            min(1.0, entity.confidence + 0.1) if verified else entity.confidence
        )

        if content:
            evidence.append(content)

        return FactCheckResult(
            entity_name=entity.name,
            original_confidence=entity.confidence,
            verified=verified,
            verification_confidence=verification_confidence,
            sources=sources,
            evidence=evidence,
            tool_used=tool_used,
        )

    def _parse_relationship_verification(
        self, relationship: Relationship, response: Dict[str, Any]
    ) -> FactCheckResult:
        """Parse relationship verification response."""
        # Similar to entity verification
        return self._parse_verification_response(
            Entity(
                name=f"{relationship.subject} → {relationship.object}",
                type="RELATIONSHIP",
                confidence=relationship.confidence,
                evidence=relationship.evidence,
            ),
            response,
        )

    def _extract_enrichment_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enrichment data from API response."""
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        tool_calls = response.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])

        enrichment = {"summary": content, "sources": [], "related_topics": [], "tool_results": []}

        for tool_call in tool_calls:
            tool_result = tool_call.get("function", {}).get("arguments", {})
            enrichment["tool_results"].append(tool_result)

            # Extract structured data
            if isinstance(tool_result, dict):
                if "sources" in tool_result:
                    enrichment["sources"].extend(tool_result["sources"])
                if "related" in tool_result:
                    enrichment["related_topics"].extend(tool_result["related"])

        return enrichment

    async def close(self):
        """Close the API client."""
        await self.client.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
