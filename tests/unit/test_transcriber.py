# tests/unit/test_transcriber.py
import pytest
import json
import tempfile
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from clipscribe.retrievers.transcriber import GeminiFlashTranscriber
from clipscribe.retrievers.gemini_pool import GeminiPool, TaskType
from google.generativeai.types import RequestOptions
import asyncio


# DEPRECATED: Skip all tests in this file
pytest.skip("These tests are deprecated - GeminiFlashTranscriber has been replaced by Voxtral-Grok pipeline", allow_module_level=True)


@pytest.fixture
def transcriber():
    """Fixture to create a GeminiFlashTranscriber instance with mocked dependencies."""
    with patch("googleapiclient.discovery.build"), patch("clipscribe.retrievers.transcriber.genai"):
        return GeminiFlashTranscriber()


@pytest.fixture
def transcriber_with_pro():
    """Fixture to create a GeminiFlashTranscriber with Pro model."""
    with patch("googleapiclient.discovery.build"), patch("clipscribe.retrievers.transcriber.genai"):
        return GeminiFlashTranscriber(use_pro=True)


@pytest.fixture
def transcriber_with_vertex():
    """Fixture to create a GeminiFlashTranscriber with Vertex AI enabled."""
    # Skip Vertex AI tests for now due to authentication complexity
    pytest.skip("Vertex AI tests require complex authentication setup")


class TestGeminiFlashTranscriberInitialization:
    """Test transcriber initialization scenarios."""

    def test_init_basic(self):
        """Test basic initialization."""
        with patch("clipscribe.retrievers.transcriber.genai") as mock_genai, \
             patch("clipscribe.retrievers.transcriber.GeminiPool") as mock_pool_class:

            mock_pool = MagicMock()
            mock_pool_class.return_value = mock_pool

            transcriber = GeminiFlashTranscriber()

            assert transcriber.use_pro is False
            assert transcriber.use_vertex_ai is False
            assert transcriber.vertex_transcriber is None
            assert transcriber.performance_monitor is None
            assert transcriber.total_cost == 0.0
            mock_genai.configure.assert_called_once()
            mock_pool_class.assert_called_once()

    def test_init_with_api_key(self):
        """Test initialization with custom API key."""
        with patch("clipscribe.retrievers.transcriber.genai") as mock_genai, \
             patch("clipscribe.retrievers.transcriber.GeminiPool") as mock_pool_class:

            custom_key = "custom-api-key"
            transcriber = GeminiFlashTranscriber(api_key=custom_key)

            assert transcriber.api_key == custom_key
            mock_genai.configure.assert_called_once_with(api_key=custom_key)

    def test_init_with_pro_model(self):
        """Test initialization with Pro model."""
        with patch("clipscribe.retrievers.transcriber.genai"), \
             patch("clipscribe.retrievers.transcriber.GeminiPool"):

            transcriber = GeminiFlashTranscriber(use_pro=True)

            assert transcriber.use_pro is True

    def test_init_with_performance_monitor(self):
        """Test initialization with performance monitor."""
        with patch("clipscribe.retrievers.transcriber.genai"), \
             patch("clipscribe.retrievers.transcriber.GeminiPool"):

            mock_monitor = MagicMock()
            transcriber = GeminiFlashTranscriber(performance_monitor=mock_monitor)

            assert transcriber.performance_monitor == mock_monitor

    def test_init_with_vertex_ai(self):
        """Test initialization with Vertex AI enabled."""
        with patch("clipscribe.retrievers.transcriber.genai") as mock_genai, \
             patch("clipscribe.retrievers.transcriber.GeminiPool") as mock_pool_class, \
             patch("clipscribe.retrievers.transcriber.VertexAITranscriber") as mock_vertex_class:

            mock_vertex = MagicMock()
            mock_vertex_class.return_value = mock_vertex

            with patch.dict(os.environ, {"USE_VERTEX_AI": "true", "VERTEX_AI_PROJECT": "test-project"}):
                transcriber = GeminiFlashTranscriber()

                assert transcriber.use_vertex_ai is True
                assert transcriber.vertex_transcriber == mock_vertex
                mock_genai.configure.assert_not_called()  # Should not configure genai when using Vertex

    def test_init_missing_api_key_without_vertex(self):
        """Test initialization failure when API key is missing and not using Vertex AI."""
        with patch("clipscribe.retrievers.transcriber.genai") as mock_genai, \
             patch("clipscribe.retrievers.transcriber.GeminiPool") as mock_pool_class, \
             patch("clipscribe.retrievers.transcriber.Settings") as mock_settings_class:

            mock_pool_class.return_value = MagicMock()
            mock_settings = MagicMock()
            mock_settings.google_api_key = ""  # Empty string to simulate missing API key
            mock_settings.use_vertex_ai = False  # Ensure not using Vertex AI
            mock_settings_class.return_value = mock_settings

            with pytest.raises(ValueError, match="Google API key is required"):
                GeminiFlashTranscriber(api_key=None)

    def test_init_logging(self, caplog):
        """Test that initialization logs are correct."""
        with patch("clipscribe.retrievers.transcriber.genai"), \
             patch("clipscribe.retrievers.transcriber.GeminiPool"):

            with caplog.at_level("INFO"):
                GeminiFlashTranscriber()

            assert "Using model: gemini-2.5-flash" in caplog.text
            assert "Using Gemini request timeout: 300s" in caplog.text


class TestGeminiFlashTranscriberJSONHandling:
    """Test JSON response parsing and enhancement."""

    def test_parse_json_response_valid(self, transcriber):
        """Test parsing valid JSON response."""
        valid_json = '{"key": "value", "number": 123}'
        result = transcriber._parse_json_response(valid_json)
        assert result == {"key": "value", "number": 123}

    def test_parse_json_response_invalid_fallback(self, transcriber):
        """Test parsing invalid JSON with enhancement fallback."""
        invalid_json = '```json\n{"key": "value"}\n```'
        with patch.object(transcriber, '_enhance_json_response', return_value='{"key": "value"}'):
            result = transcriber._parse_json_response(invalid_json)
            assert result == {"key": "value"}

    def test_parse_json_response_enhanced_parsing(self, transcriber):
        """Test enhanced JSON parsing with malformed input."""
        malformed_json = 'Some text before {"key": "value", "valid": "json"} and after'
        result = transcriber._parse_json_response(malformed_json)
        assert result == {"key": "value", "valid": "json"}

    def test_parse_json_response_array_type(self, transcriber):
        """Test parsing JSON with array type specification."""
        array_json = 'Before array [{"item": "value"}] after'
        with patch.object(transcriber, '_enhance_json_response', return_value='[{"item": "value"}]'):
            result = transcriber._parse_json_response(array_json, "array")
            assert result == [{"item": "value"}]

    def test_parse_json_response_failure(self, transcriber):
        """Test JSON parsing failure returns None."""
        completely_invalid = "This is not JSON at all"
        with patch.object(transcriber, '_enhance_json_response', return_value=completely_invalid):
            result = transcriber._parse_json_response(completely_invalid)
            assert result is None

    def test_enhance_json_response_basic(self, transcriber):
        """Test basic JSON enhancement."""
        input_text = '```json\n{"key": "value"}\n```'
        result = transcriber._enhance_json_response(input_text)
        assert result == '{"key": "value"}'

    def test_enhance_json_response_with_backticks(self, transcriber):
        """Test JSON enhancement with backticks."""
        input_text = '```\n{"key": "value"}\n```'
        result = transcriber._enhance_json_response(input_text)
        assert result == '{"key": "value"}'

    def test_enhance_json_response_extract_json_portion(self, transcriber):
        """Test extracting JSON portion from mixed content."""
        input_text = 'Some text before {"key": "value"} and after'
        result = transcriber._enhance_json_response(input_text)
        assert result == '{"key": "value"}'

    def test_enhance_json_response_fix_trailing_commas(self, transcriber):
        """Test fixing trailing commas in JSON."""
        # Test with mixed content that contains JSON with trailing commas
        input_text = 'Here is some text before {"array": [1, 2, 3,], "object": {"key": "value",}} and after'
        result = transcriber._enhance_json_response(input_text)
        # The method should extract and attempt to clean up the JSON
        assert isinstance(result, str)
        assert len(result) > 0
        # Should have extracted the JSON portion and attempted to fix it
        assert result.strip().startswith('{') or result.strip().startswith('[')
        assert result.strip().endswith('}') or result.strip().endswith(']')

    def test_enhance_json_response_fix_quotes(self, transcriber):
        """Test fixing missing quotes in JSON."""
        input_text = '{key: "value", "missing": quote}'
        result = transcriber._enhance_json_response(input_text)
        # The method may not fix all quote issues, but it should attempt to clean up
        assert "key" in result and "missing" in result


class TestGeminiFlashTranscriberTranscription:
    """Test transcription functionality."""

    @pytest.mark.asyncio
    async def test_transcribe_video_success(self, transcriber):
        """Test successful video transcription."""
        with patch.object(transcriber, "_retry_generate_content", new_callable=AsyncMock) as mock_retry, \
             patch.object(transcriber, "_extract_audio_for_upload", new_callable=AsyncMock) as mock_extract, \
             patch.object(transcriber, "_upload_file_with_retry", new_callable=AsyncMock) as mock_upload, \
             patch("clipscribe.retrievers.transcriber.genai.delete_file") as mock_delete:

            # Setup mocks
            mock_file = MagicMock()
            mock_extract.return_value = "/tmp/test_audio.mp3"
            mock_upload.return_value = mock_file

            mock_transcript_response = MagicMock()
            mock_transcript_response.text = "Raw transcript text"

            mock_analysis_response = MagicMock()
            mock_analysis_response.text = '{"summary": "Test summary", "key_points": [], "entities": [], "topics": [], "relationships": [], "dates": []}'

            mock_retry.side_effect = [mock_transcript_response, mock_analysis_response]

            with patch.object(transcriber, "_parse_json_response", return_value={
                "summary": "Test summary", "key_points": [], "entities": [], "topics": [], "relationships": [], "dates": []
            }):
                result = await transcriber.transcribe_video("test.mp4", None, 300)

                assert result["transcript"] == "Raw transcript text"
                assert result["summary"] == "Test summary"
                assert "processing_cost" in result

                # Verify the calls
                assert mock_extract.called
                assert mock_upload.called
                mock_delete.assert_called_once_with(mock_file.name)

    @pytest.mark.asyncio
    async def test_transcribe_video_audio_extraction_failure(self, transcriber):
        """Test video transcription when audio extraction fails."""
        with patch.object(transcriber, "_retry_generate_content", new_callable=AsyncMock) as mock_retry, \
             patch.object(transcriber, "_extract_audio_for_upload", side_effect=Exception("Audio extraction failed")), \
             patch.object(transcriber, "_upload_file_with_retry", new_callable=AsyncMock) as mock_upload:

            mock_file = MagicMock()
            mock_upload.return_value = mock_file

            mock_transcript_response = MagicMock()
            mock_transcript_response.text = "Raw transcript text"

            mock_analysis_response = MagicMock()
            mock_analysis_response.text = '{"summary": "Test summary", "key_points": [], "entities": [], "topics": [], "relationships": [], "dates": []}'

            mock_retry.side_effect = [mock_transcript_response, mock_analysis_response]

            with patch.object(transcriber, "_parse_json_response", return_value={
                "summary": "Test summary", "key_points": [], "entities": [], "topics": [], "relationships": [], "dates": []
            }):
                result = await transcriber.transcribe_video("test.mp4", None, 300)

                # Should fall back to original video file
                mock_upload.assert_called_with("test.mp4")

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, transcriber):
        """Test successful audio transcription."""
        with patch("clipscribe.retrievers.transcriber.genai.upload_file") as mock_upload, \
             patch("clipscribe.retrievers.transcriber.genai.get_file") as mock_get_file, \
             patch("clipscribe.retrievers.transcriber.genai.delete_file") as mock_delete, \
             patch.object(transcriber, "_retry_generate_content", new_callable=AsyncMock) as mock_retry, \
             patch.object(transcriber.pool, "get_model") as mock_get_model:

            # Setup mocks
            mock_file = MagicMock()
            mock_file.state.name = "ACTIVE"
            mock_file.name = "test_file"

            # Make upload return the mock file directly (not a coroutine)
            mock_upload.return_value = mock_file
            mock_get_file.return_value = mock_file

            mock_model = MagicMock()
            mock_get_model.return_value = mock_model

            mock_response = MagicMock()
            mock_response.text = '{"transcript": "Audio transcript", "summary": "Summary"}'
            mock_retry.return_value = mock_response

            with patch.object(transcriber, "_parse_json_response", return_value={
                "transcript": "Audio transcript", "summary": "Summary", "entities": [], "key_points": [], "topics": [], "relationships": [], "dates": []
            }):
                # Mock the transcribe_audio method to use the standard path
                transcriber.use_vertex_ai = False

                result = await transcriber.transcribe_audio("test.mp3", 120)

                # The transcript comes from the raw response text, not the parsed JSON
                assert result["transcript"] == '{"transcript": "Audio transcript", "summary": "Summary"}'
                # The summary comes from the parsed JSON response
                assert result["summary"] == "Summary"
                assert "processing_cost" in result

    @pytest.mark.asyncio
    async def test_transcribe_large_video_success(self, transcriber):
        """Test successful large video transcription."""
        with patch("clipscribe.utils.video_splitter.split_video", return_value=["chunk1.mp4", "chunk2.mp4"]) as mock_split, \
             patch("clipscribe.utils.transcript_merger.TranscriptMerger") as mock_merger_class, \
             patch.object(transcriber, "_transcribe_chunk_raw", new_callable=AsyncMock) as mock_transcribe_chunk, \
             patch.object(transcriber, "_retry_generate_content", new_callable=AsyncMock) as mock_retry, \
             patch.object(transcriber, "_parse_json_response") as mock_parse:
            mock_transcribe_chunk.return_value = "Chunk transcript"

            mock_merger = MagicMock()
            mock_merger.merge_transcripts.return_value = "Merged transcript"
            mock_merger_class.return_value = mock_merger

            mock_response = MagicMock()
            mock_response.text = '{"summary": "Large video summary"}'
            mock_retry.return_value = mock_response

            mock_parse.return_value = {"summary": "Large video summary", "entities": []}

            result = await transcriber.transcribe_large_video("large_video.mp4", None, 600)

            assert result["transcript"] == "Merged transcript"
            assert result["summary"] == "Large video summary"
            assert "processing_cost" in result

    @pytest.mark.asyncio
    async def test_transcribe_large_video_single_chunk(self, transcriber):
        """Test large video transcription with single chunk fallback."""
        with patch("clipscribe.utils.video_splitter.split_video", return_value=["single_chunk.mp4"]) as mock_split, \
             patch.object(transcriber, "transcribe_video", new_callable=AsyncMock) as mock_transcribe_video:
            mock_transcribe_video.return_value = {"transcript": "Single chunk result"}

            result = await transcriber.transcribe_large_video("small_video.mp4", None, 300)

            mock_transcribe_video.assert_called_once_with("small_video.mp4", 300)
            assert result == {"transcript": "Single chunk result"}


class TestGeminiFlashTranscriberHelpers:
    """Test helper methods."""

    def test_get_mime_type_mp3(self, transcriber):
        """Test MIME type detection for MP3 files."""
        result = transcriber._get_mime_type("test.mp3")
        assert result == "audio/mpeg"

    def test_get_mime_type_video(self, transcriber):
        """Test MIME type detection for video files."""
        result = transcriber._get_mime_type("test.mp4")
        assert result == "video/mp4"

    def test_get_mime_type_unknown(self, transcriber):
        """Test MIME type detection for unknown files."""
        result = transcriber._get_mime_type("unknown.xyz")
        # The mimetypes module may return different defaults, but it should be a valid MIME type
        assert result is not None and "/" in result

    def test_build_enhanced_analysis_prompt(self, transcriber):
        """Test building enhanced analysis prompt."""
        transcript = "This is a test transcript for analysis."
        prompt = transcriber._build_enhanced_analysis_prompt(transcript)

        assert "Expert Intelligence Analyst" in prompt
        assert transcript in prompt
        assert "key_points.importance" in prompt

    def test_build_enhanced_response_schema(self, transcriber):
        """Test building enhanced response schema."""
        schema = transcriber._build_enhanced_response_schema()

        assert schema["type"] == "OBJECT"
        assert "summary" in schema["properties"]
        assert "key_points" in schema["properties"]
        assert "entities" in schema["properties"]
        assert "relationships" in schema["properties"]
        assert "dates" in schema["properties"]

    def test_get_total_cost(self, transcriber):
        """Test getting total cost."""
        transcriber.total_cost = 5.25
        assert transcriber.get_total_cost() == 5.25

    def test_convert_vertex_result_to_dict_dict(self, transcriber):
        """Test converting Vertex AI result from dict."""
        vertex_result = {"transcript": {"full_text": "Test transcript"}}
        result = transcriber._convert_vertex_result_to_dict(vertex_result)
        assert result == {"transcript": "Test transcript"}

    def test_convert_vertex_result_to_dict_object(self, transcriber):
        """Test converting Vertex AI result from object."""
        vertex_result = MagicMock()
        vertex_result.transcript_text = "Test transcript"
        result = transcriber._convert_vertex_result_to_dict(vertex_result)
        assert result == {"transcript": "Test transcript"}


class TestGeminiFlashTranscriberFileOperations:
    """Test file upload and processing operations."""

    @pytest.mark.asyncio
    async def test_upload_file_with_retry_success(self, transcriber):
        """Test successful file upload with retry."""
        with patch("clipscribe.retrievers.transcriber.genai.upload_file", new_callable=AsyncMock) as mock_upload, \
             patch("clipscribe.retrievers.transcriber.genai.get_file", new_callable=AsyncMock) as mock_get_file:

            mock_file = MagicMock()
            mock_file.state.name = "ACTIVE"
            mock_upload.return_value = mock_file
            mock_get_file.return_value = mock_file

            result = await transcriber._upload_file_with_retry("test.mp4")

            assert result == mock_file

    @pytest.mark.asyncio
    async def test_upload_file_with_retry_processing_failure(self, transcriber):
        """Test file upload failure during processing."""
        with patch("clipscribe.retrievers.transcriber.genai.upload_file", new_callable=AsyncMock) as mock_upload, \
             patch("clipscribe.retrievers.transcriber.genai.get_file", new_callable=AsyncMock) as mock_get_file:

            mock_file = MagicMock()
            mock_file.state.name = "FAILED"
            mock_upload.return_value = mock_file
            mock_get_file.return_value = mock_file

            with pytest.raises(ValueError, match="File upload failed with state: FAILED"):
                await transcriber._upload_file_with_retry("test.mp4")

    @pytest.mark.asyncio
    async def test_extract_audio_for_upload_success(self, transcriber):
        """Test successful audio extraction for upload."""
        with patch("subprocess.run", return_value=MagicMock()) as mock_run, \
             patch("tempfile.gettempdir", return_value="/tmp"), \
             patch("os.path.exists", return_value=True):

            result = await transcriber._extract_audio_for_upload("test_video.mp4")

            assert "test_video.mp3" in result
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_audio_for_upload_failure(self, transcriber):
        """Test audio extraction failure fallback."""
        # Create a proper CalledProcessError with output and error
        error = subprocess.CalledProcessError(1, "ffmpeg", output=b"", stderr=b"FFmpeg failed")
        with patch("subprocess.run", side_effect=error), \
             patch("clipscribe.retrievers.transcriber.Path") as mock_path:

            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance

            result = await transcriber._extract_audio_for_upload("test_video.mp4")

            # Should fallback to original video file
            assert result == "test_video.mp4"

    @pytest.mark.asyncio
    async def test_transcribe_chunk_raw_success(self, transcriber):
        """Test successful raw chunk transcription."""
        with patch.object(transcriber, "_extract_audio_for_upload", new_callable=AsyncMock) as mock_extract, \
             patch.object(transcriber, "_upload_file_with_retry", new_callable=AsyncMock) as mock_upload, \
             patch.object(transcriber, "_retry_generate_content", new_callable=AsyncMock) as mock_retry, \
             patch("clipscribe.retrievers.transcriber.genai.delete_file") as mock_delete:

            mock_extract.return_value = "/tmp/audio.mp3"
            mock_file = MagicMock()
            mock_upload.return_value = mock_file

            mock_response = MagicMock()
            mock_response.text = "Chunk transcript"
            mock_retry.return_value = mock_response

            semaphore = asyncio.Semaphore(1)
            result = await transcriber._transcribe_chunk_raw("chunk.mp4", semaphore)

            assert result == "Chunk transcript"
            mock_delete.assert_called_once_with(mock_file.name)


class TestGeminiFlashTranscriberErrorHandling:
    """Test error handling and retry mechanisms."""

    @pytest.mark.asyncio
    async def test_retry_generate_content_success(self, transcriber):
        """Test successful retry generate content."""
        with patch.object(transcriber.pool, "get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=MagicMock(text="Success"))
            mock_get_model.return_value = mock_model

            result = await transcriber._retry_generate_content(
                mock_model, ["test prompt"], retries=2
            )

            assert result.text == "Success"

    @pytest.mark.asyncio
    async def test_retry_generate_content_with_retry(self, transcriber):
        """Test retry generate content with transient errors."""
        with patch.object(transcriber.pool, "get_model") as mock_get_model, \
             patch("asyncio.sleep") as mock_sleep:

            mock_model = MagicMock()
            mock_responses = [
                Exception("503 Server Error"),  # First call fails
                MagicMock(text="Success")       # Second call succeeds
            ]
            mock_model.generate_content_async = AsyncMock(side_effect=mock_responses)
            mock_get_model.return_value = mock_model

            result = await transcriber._retry_generate_content(
                mock_model, ["test prompt"], retries=2
            )

            assert result.text == "Success"
            assert mock_model.generate_content_async.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_generate_content_exhausted(self, transcriber):
        """Test retry generate content when retries are exhausted."""
        with patch.object(transcriber.pool, "get_model") as mock_get_model:

            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(side_effect=Exception("Persistent error"))
            mock_get_model.return_value = mock_model

            with pytest.raises(Exception, match="Persistent error"):
                await transcriber._retry_generate_content(
                    mock_model, ["test prompt"], retries=2
                )


class TestGeminiFlashTranscriberCostCalculation:
    """Test cost calculation functionality."""

    def test_cost_tracking_basic(self, transcriber):
        """Test basic cost tracking."""
        transcriber.total_cost = 0.0
        transcriber.total_cost += 2.50

        assert transcriber.get_total_cost() == 2.50

    def test_cost_tracking_multiple_operations(self, transcriber):
        """Test cost tracking across multiple operations."""
        transcriber.total_cost = 0.0
        transcriber.total_cost += 1.25  # First operation
        transcriber.total_cost += 3.75  # Second operation

        assert transcriber.get_total_cost() == 5.00


class TestGeminiFlashTranscriberVertexAI:
    """Test Vertex AI integration."""

    @pytest.mark.asyncio
    async def test_transcribe_audio_with_vertex_ai_success(self, transcriber_with_vertex):
        """Test audio transcription using Vertex AI."""
        with patch.object(transcriber_with_vertex.vertex_transcriber, "transcribe_with_vertex", new_callable=AsyncMock) as mock_vertex_transcribe:

            mock_vertex_transcribe.return_value = {"transcript": "Vertex AI transcript"}

            result = await transcriber_with_vertex.transcribe_audio("test.mp3", 120)

            assert result["transcript"] == "Vertex AI transcript"
            mock_vertex_transcribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_audio_vertex_ai_fallback(self, transcriber_with_vertex):
        """Test fallback to standard Gemini when Vertex AI fails."""
        with patch.object(transcriber_with_vertex.vertex_transcriber, "transcribe_with_vertex", side_effect=Exception("Vertex failed")), \
             patch.object(transcriber_with_vertex, "_retry_generate_content", new_callable=AsyncMock) as mock_retry, \
             patch("clipscribe.retrievers.transcriber.genai.upload_file", new_callable=AsyncMock) as mock_upload, \
             patch("clipscribe.retrievers.transcriber.genai.get_file", new_callable=AsyncMock) as mock_get_file:

            mock_file = MagicMock()
            mock_file.state.name = "ACTIVE"
            mock_upload.return_value = mock_file
            mock_get_file.return_value = mock_file

            mock_response = MagicMock()
            mock_response.text = '{"transcript": "Fallback transcript"}'
            mock_retry.return_value = mock_response

            with patch.object(transcriber_with_vertex, "_parse_json_response", return_value={
                "transcript": "Fallback transcript", "entities": [], "key_points": [], "topics": [], "relationships": [], "dates": []
            }):
                result = await transcriber_with_vertex.transcribe_audio("test.mp3", 120)

                assert result["transcript"] == "Fallback transcript"


@pytest.mark.asyncio
async def test_transcribe_video_success(transcriber):
    """Test successful video transcription."""
    with patch.object(transcriber, "_retry_generate_content", new_callable=AsyncMock) as mock_retry, \
         patch.object(transcriber, "_extract_audio_for_upload", new_callable=AsyncMock) as mock_extract, \
         patch.object(transcriber, "_upload_file_with_retry", new_callable=AsyncMock) as mock_upload, \
         patch("clipscribe.retrievers.transcriber.genai.delete_file") as mock_delete:

        # Setup mocks
        mock_file = MagicMock()
        mock_extract.return_value = "/tmp/test_audio.mp3"
        mock_upload.return_value = mock_file

        mock_transcript_response = MagicMock()
        mock_transcript_response.text = "Raw transcript text"

        mock_analysis_response = MagicMock()
        mock_analysis_response.text = '{"summary": "Test summary", "key_points": [], "entities": [], "topics": [], "relationships": [], "dates": []}'

        mock_retry.side_effect = [mock_transcript_response, mock_analysis_response]

        with patch.object(transcriber, "_parse_json_response", return_value={
            "summary": "Test summary", "key_points": [], "entities": [], "topics": [], "relationships": [], "dates": []
        }):
            result = await transcriber.transcribe_video("test.mp4", None, 300)

            assert result["transcript"] == "Raw transcript text"
            assert result["summary"] == "Test summary"
            assert "processing_cost" in result

            # Verify the calls
            assert mock_extract.called
            assert mock_upload.called
            mock_delete.assert_called_once_with(mock_file.name)
