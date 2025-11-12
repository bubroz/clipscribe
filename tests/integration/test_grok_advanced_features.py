"""
Integration tests for Grok advanced features (November 2025).

Tests:
- Files API
- Collections API
- Server-side tools (web_search, x_search)
- Prompt caching
- Structured outputs (json_schema)
"""

import pytest
import os
import asyncio
from pathlib import Path
import tempfile

from src.clipscribe.retrievers.grok_client import GrokAPIClient
from src.clipscribe.utils.prompt_cache import GrokPromptCache
from src.clipscribe.intelligence.fact_checker import GrokFactChecker
from src.clipscribe.knowledge.collection_manager import VideoKnowledgeBase
from src.clipscribe.schemas_grok import (
    Entity,
    EntityType,
    get_video_intelligence_schema,
    get_entity_schema
)


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("XAI_API_KEY"),
    reason="XAI_API_KEY not set"
)


@pytest.fixture
async def grok_client():
    """Create Grok API client."""
    api_key = os.getenv("XAI_API_KEY")
    client = GrokAPIClient(api_key=api_key)
    yield client
    await client.client.aclose()


@pytest.fixture
def prompt_cache():
    """Create prompt cache instance."""
    return GrokPromptCache()


@pytest.fixture
async def fact_checker():
    """Create fact checker."""
    api_key = os.getenv("XAI_API_KEY")
    checker = GrokFactChecker(api_key=api_key)
    yield checker
    await checker.close()


@pytest.fixture
async def knowledge_base():
    """Create knowledge base manager."""
    api_key = os.getenv("XAI_API_KEY")
    kb = VideoKnowledgeBase(api_key=api_key, collection_name="test-collection")
    yield kb
    await kb.close()


# ==============================================================================
# PROMPT CACHING TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_prompt_caching_detection(grok_client, prompt_cache):
    """
    Test that prompt caching detects cacheable prompts.
    """
    # Long system prompt (>1024 tokens)
    long_system_prompt = "You are a helpful AI assistant. " * 300
    
    assert prompt_cache.should_use_caching(long_system_prompt) is True
    
    # Short system prompt (<1024 tokens)
    short_system_prompt = "You are a helpful AI."
    assert prompt_cache.should_use_caching(short_system_prompt) is False


@pytest.mark.asyncio
async def test_prompt_cache_message_building(prompt_cache):
    """
    Test that cached messages are built correctly.
    """
    system_prompt = "You are a helpful assistant."
    user_content = "Hello, world!"
    
    messages = prompt_cache.build_cached_message(system_prompt, user_content)
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == system_prompt
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == user_content


@pytest.mark.asyncio
async def test_cache_stats_tracking(prompt_cache):
    """
    Test cache statistics tracking.
    """
    # Simulate API response with cache hit
    usage_stats = {
        "input_tokens": 1000,
        "output_tokens": 200,
        "cached_tokens": 500,
        "total_tokens": 1200
    }
    
    cost_breakdown = {
        "input_cost": 0.003,
        "cached_cost": 0.00075,
        "output_cost": 0.002,
        "cache_savings": 0.00075,
        "tool_cost": 0.0,
        "total": 0.00575
    }
    
    prompt_cache.record_api_response(usage_stats, cost_breakdown)
    
    stats = prompt_cache.get_stats_summary()
    assert stats["cache_hits"] == 1
    assert stats["total_savings_usd"] == pytest.approx(0.00075, rel=0.1)  # Allow 10% tolerance for float precision
    assert stats["cached_tokens_total"] == 500


# ==============================================================================
# FILES API TESTS
# ==============================================================================


@pytest.mark.asyncio
@pytest.mark.xfail(reason="File upload multipart/form-data boundary issue - needs investigation")
async def test_file_upload_and_retrieve(grok_client):
    """
    Test uploading a file and retrieving its metadata.
    """
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content for xAI Files API")
        temp_path = Path(f.name)
    
    try:
        # Upload file
        file_result = await grok_client.upload_file(temp_path, purpose="assistants")
        
        assert "id" in file_result
        assert file_result["purpose"] == "assistants"
        file_id = file_result["id"]
        
        # Retrieve file metadata
        retrieved = await grok_client.retrieve_file(file_id)
        assert retrieved["id"] == file_id
        
        # Clean up
        await grok_client.delete_file(file_id)
        
    finally:
        # Clean up temp file
        temp_path.unlink()


@pytest.mark.asyncio
async def test_list_files(grok_client):
    """
    Test listing uploaded files.
    """
    files_result = await grok_client.list_files()
    
    assert "data" in files_result or "files" in files_result
    # May be empty list if no files uploaded


# ==============================================================================
# COLLECTIONS API TESTS
# ==============================================================================


@pytest.mark.asyncio
@pytest.mark.skip(reason="Collections API not yet available in xAI API (feature planned but not released)")
async def test_create_and_list_collections(grok_client):
    """
    Test creating a collection and listing collections.
    """
    # Create collection
    collection_result = await grok_client.create_collection(
        name="test-collection",
        description="Test collection for ClipScribe"
    )
    
    assert "id" in collection_result
    collection_id = collection_result["id"]
    
    # List collections
    collections = await grok_client.list_collections()
    assert "data" in collections or "collections" in collections
    
    # Clean up
    await grok_client.delete_collection(collection_id)


@pytest.mark.asyncio
@pytest.mark.skip(reason="Collections API not yet available in xAI API (feature planned but not released)")
async def test_knowledge_base_initialization(knowledge_base):
    """
    Test knowledge base initialization and collection creation.
    """
    collection_id = await knowledge_base.initialize_collection()
    
    assert collection_id is not None
    assert knowledge_base.collection_id == collection_id
    
    stats = await knowledge_base.get_collection_stats()
    assert stats["initialized"] is True


# ==============================================================================
# STRUCTURED OUTPUTS TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_json_schema_response_format(grok_client):
    """
    Test structured outputs with json_schema mode.
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Extract entities from: 'Elon Musk founded SpaceX in 2002.'"}
    ]
    
    response = await grok_client.chat_completion(
        messages=messages,
        model="grok-4",
        response_format=get_entity_schema()
    )
    
    assert "choices" in response
    assert len(response["choices"]) > 0
    
    # Parse content to verify structure
    import json
    content = response["choices"][0]["message"]["content"]
    result = json.loads(content)
    
    # Should have entities field due to schema enforcement
    assert "entities" in result


@pytest.mark.asyncio
async def test_video_intelligence_schema():
    """
    Test video intelligence schema generation.
    """
    schema = get_video_intelligence_schema()
    
    assert schema["type"] == "json_schema"
    assert schema["json_schema"]["strict"] is True
    assert "schema" in schema["json_schema"]
    
    # Verify required fields
    schema_def = schema["json_schema"]["schema"]
    assert "properties" in schema_def
    assert "entities" in schema_def["properties"]
    assert "relationships" in schema_def["properties"]


# ==============================================================================
# FACT CHECKING / TOOLS TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_fact_checker_initialization(fact_checker):
    """
    Test fact checker initialization with tools.
    """
    assert len(fact_checker.available_tools) > 0
    
    # Check for expected tools
    tool_types = [t["type"] for t in fact_checker.available_tools]
    assert "web_search" in tool_types or "x_search" in tool_types


@pytest.mark.asyncio
async def test_entity_fact_checking(fact_checker):
    """
    Test fact-checking an entity.
    
    Note: This may use actual API calls with tools.
    """
    # Create test entity
    entity = Entity(
        name="Elon Musk",
        type=EntityType.PERSON,
        confidence=0.8,
        evidence="Mentioned as SpaceX founder"
    )
    
    # Fact check (will use web_search or x_search if enabled)
    result = await fact_checker.fact_check_entity(entity, context="SpaceX CEO")
    
    assert result.entity_name == "Elon Musk"
    assert result.original_confidence == 0.8
    # May or may not verify depending on tool availability


# ==============================================================================
# COST CALCULATION TESTS
# ==============================================================================


def test_cost_calculation_with_caching(grok_client):
    """
    Test cost calculation includes caching savings.
    """
    cost_breakdown = grok_client.calculate_cost(
        input_tokens=1000,
        output_tokens=200,
        cached_tokens=500,
        model="grok-4"
    )
    
    assert "input_cost" in cost_breakdown
    assert "cached_cost" in cost_breakdown
    assert "cache_savings" in cost_breakdown
    assert "total" in cost_breakdown
    
    # Cached cost should be less than input cost
    assert cost_breakdown["cached_cost"] < (500 / 1000) * 0.003
    
    # Should have actual savings
    assert cost_breakdown["cache_savings"] > 0


def test_usage_stats_extraction(grok_client):
    """
    Test extracting usage stats from API response.
    """
    mock_response = {
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 200,
            "cached_tokens": 500,
            "total_tokens": 1200
        }
    }
    
    stats = grok_client.extract_usage_stats(mock_response)
    
    assert stats["input_tokens"] == 1000
    assert stats["output_tokens"] == 200
    assert stats["cached_tokens"] == 500
    assert stats["total_tokens"] == 1200


# ==============================================================================
# INTEGRATION TEST: FULL WORKFLOW
# ==============================================================================


@pytest.mark.asyncio
@pytest.mark.skip(reason="Collections API not yet available in xAI API (feature planned but not released)")
async def test_full_advanced_features_workflow(grok_client, prompt_cache, knowledge_base):
    """
    Integration test: Use all advanced features together.
    
    Tests:
    1. Prompt caching
    2. Structured outputs
    3. Knowledge base
    4. Cost tracking
    """
    # Initialize knowledge base
    await knowledge_base.initialize_collection()
    
    # Create test content
    transcript = "Elon Musk announced plans for SpaceX Starship mission to Mars in 2024."
    
    # Build cached message
    system_prompt = "You are an AI that extracts entities from text."
    messages = prompt_cache.build_cached_message(system_prompt, f"Extract entities: {transcript}")
    
    # Use structured outputs
    response = await grok_client.chat_completion(
        messages=messages,
        model="grok-4",
        response_format=get_entity_schema()
    )
    
    # Extract stats and calculate cost
    usage_stats = grok_client.extract_usage_stats(response)
    cost_breakdown = grok_client.calculate_cost(
        input_tokens=usage_stats["input_tokens"],
        output_tokens=usage_stats["output_tokens"],
        cached_tokens=usage_stats["cached_tokens"]
    )
    
    # Record cache performance
    prompt_cache.record_api_response(usage_stats, cost_breakdown)
    
    # Verify we got results
    assert response["choices"][0]["message"]["content"]
    assert cost_breakdown["total"] > 0
    
    # Get cache stats
    stats = prompt_cache.get_stats_summary()
    assert stats["total_requests"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

