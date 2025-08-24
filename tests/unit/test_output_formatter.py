"""Unit tests for output_formatter.py module."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from clipscribe.retrievers.output_formatter import OutputFormatter
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript, EnhancedEntity
from datetime import datetime


@pytest.fixture
def output_formatter():
    """Create an OutputFormatter instance for testing."""
    return OutputFormatter()


@pytest.fixture
def temp_output_dir(temp_directory):
    """Create a temporary output directory."""
    output_dir = temp_directory / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def mock_video_metadata():
    """Create comprehensive mock video metadata."""
    return VideoMetadata(
        video_id="test_123",
        url="https://www.youtube.com/watch?v=test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="test_channel",
        published_at=datetime(2024, 1, 15, 14, 30, 0),
        duration=300,
        view_count=1000,
        description="Test description",
        tags=["test", "video"]
    )


@pytest.fixture
def mock_transcript():
    """Create mock transcript."""
    return VideoTranscript(
        full_text="This is a comprehensive test transcript with multiple sentences and various topics for testing the output formatter functionality.",
        segments=[
            {"text": "This is a comprehensive test transcript", "start": 0.0, "end": 5.0},
            {"text": "with multiple sentences and various topics", "start": 5.0, "end": 10.0},
            {"text": "for testing the output formatter functionality.", "start": 10.0, "end": 15.0}
        ],
        language="en",
        confidence=0.95
    )


@pytest.fixture
def mock_entities():
    """Create mock entities for testing."""
    return [
        EnhancedEntity(
            name="John Doe",
            type="PERSON",
            mention_count=2,
            extraction_sources=["SpaCy"],
            canonical_form="John Doe",
            context_windows=[],
            aliases=["John", "Doe"],
            temporal_distribution=[],
        ),
        EnhancedEntity(
            name="Google",
            type="ORGANIZATION",
            mention_count=1,
            extraction_sources=["SpaCy"],
            canonical_form="Google",
            context_windows=[],
            aliases=["Alphabet"],
            temporal_distribution=[],
        ),
        EnhancedEntity(
            name="Machine Learning",
            type="CONCEPT",
            mention_count=3,
            extraction_sources=["GLiNER"],
            canonical_form="Machine Learning",
            context_windows=[],
            aliases=["ML", "AI"],
            temporal_distribution=[],
        )
    ]


@pytest.fixture
def mock_relationships():
    """Create mock relationships for testing."""
    return [
        {
            "subject": "John Doe",
            "predicate": "works_at",
            "object": "Google",
            "source": "REBEL",
            "evidence_chain": [
                {
                    "direct_quote": "John Doe works at Google as a machine learning engineer",
                    "timestamp": "00:02:15",
                    "speaker": "Narrator",
                    "visual_context": "Company logo",
                    "context_window": "John Doe works at Google as a machine learning engineer",
                    "evidence_type": "spoken"
                }
            ],
            "supporting_mentions": 1,
            "contradictions": [],
            "visual_correlation": True,
            "properties": {}
        },
        {
            "subject": "Google",
            "predicate": "develops",
            "object": "Machine Learning",
            "source": "REBEL",
            "evidence_chain": [
                {
                    "direct_quote": "Google develops advanced machine learning technologies",
                    "timestamp": "00:05:30",
                    "speaker": "Narrator",
                    "visual_context": "Product demo",
                    "context_window": "Google develops advanced machine learning technologies",
                    "evidence_type": "spoken"
                }
            ],
            "supporting_mentions": 1,
            "contradictions": [],
            "visual_correlation": True,
            "properties": {}
        }
    ]


@pytest.fixture
def mock_video_intelligence(mock_video_metadata, mock_transcript, mock_entities, mock_relationships):
    """Create comprehensive mock VideoIntelligence object."""
    return VideoIntelligence(
        metadata=mock_video_metadata,
        transcript=mock_transcript,
        summary="This is a comprehensive test summary demonstrating the output formatter functionality.",
        entities=mock_entities,
        relationships=mock_relationships,
        key_points=[
            {"text": "First key point about testing", "importance": 0.9},
            {"text": "Second key point about validation", "importance": 0.8},
            {"text": "Third key point about functionality", "importance": 0.7}
        ],
        topics=[
            {"name": "technology", "confidence": 0.9},
            {"name": "AI", "confidence": 0.8},
            {"name": "testing", "confidence": 0.7},
            {"name": "validation", "confidence": 0.6}
        ],
        processing_cost=0.25,
        knowledge_graph={
            "nodes": [
                {"id": "John Doe", "type": "PERSON", "confidence": 0.9, "mention_count": 2, "occurrences": 1},
                {"id": "Google", "type": "ORGANIZATION", "confidence": 0.8, "mention_count": 1, "occurrences": 1},
                {"id": "Machine Learning", "type": "CONCEPT", "confidence": 0.9, "mention_count": 3, "occurrences": 1}
            ],
            "edges": [
                {"source": "John Doe", "target": "Google", "predicate": "works_at", "confidence": 0.85},
                {"source": "Google", "target": "Machine Learning", "predicate": "develops", "confidence": 0.92}
            ],
            "node_count": 3,
            "edge_count": 2
        }
    )


class TestOutputFormatter:
    """Test cases for OutputFormatter class."""

    def test_init(self, output_formatter):
        """Test OutputFormatter initialization."""
        assert output_formatter is not None

    def test_save_transcript_txt(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test saving transcript as text file."""
        paths = output_formatter.save_transcript(mock_video_intelligence, str(temp_output_dir), ["txt"])

        assert "txt" in paths
        txt_file = Path(paths["txt"])
        assert txt_file.exists()
        assert txt_file.read_text() == mock_video_intelligence.transcript.full_text

    def test_save_transcript_json(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test saving transcript as JSON file."""
        paths = output_formatter.save_transcript(mock_video_intelligence, str(temp_output_dir), ["json"])

        assert "json" in paths
        json_file = Path(paths["json"])
        assert json_file.exists()

        with open(json_file) as f:
            data = json.load(f)

        assert data["metadata"]["title"] == "Test Video"
        assert data["transcript"]["full_text"] == mock_video_intelligence.transcript.full_text
        assert data["summary"] == mock_video_intelligence.summary

    def test_save_transcript_multiple_formats(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test saving transcript in multiple formats."""
        paths = output_formatter.save_transcript(mock_video_intelligence, str(temp_output_dir), ["txt", "json"])

        assert "txt" in paths
        assert "json" in paths
        assert Path(paths["txt"]).exists()
        assert Path(paths["json"]).exists()

    def test_save_transcript_invalid_format(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test handling of invalid format in save_transcript."""
        paths = output_formatter.save_transcript(mock_video_intelligence, str(temp_output_dir), ["invalid_format"])

        # Should return empty dict for invalid format
        assert paths == {}

    def test_save_all_formats_comprehensive(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test comprehensive save_all_formats functionality."""
        paths = output_formatter.save_all_formats(mock_video_intelligence, str(temp_output_dir))

        # Check that all expected files are created
        # The paths dictionary contains the actual file paths, not just filenames
        expected_filenames = [
            "transcript.txt",
            "transcript.json",
            "metadata.json",
            "entities.json",
            "relationships.json",
            "knowledge_graph.json",
            "report.md",
            "manifest.json"
        ]

        # Check that the expected files exist in the directory structure
        for filename in expected_filenames:
            expected_path = temp_output_dir / filename
            # For files in subdirectory, check if the file exists anywhere in the temp directory
            found_files = list(temp_output_dir.rglob(filename))
            assert len(found_files) > 0, f"File {filename} should exist"

        # Check that paths dictionary contains the expected file types
        assert "transcript_txt" in paths or "transcript.txt" in [p.name for p in paths.values()]
        assert "transcript_json" in paths or "transcript.json" in [p.name for p in paths.values()]
        assert "metadata" in paths or "metadata.json" in [p.name for p in paths.values()]
        assert "entities" in paths or "entities.json" in [p.name for p in paths.values()]
        assert "relationships" in paths or "relationships.json" in [p.name for p in paths.values()]
        assert "manifest" in paths or "manifest.json" in [p.name for p in paths.values()]

    def test_save_all_formats_with_knowledge_graph(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test save_all_formats with knowledge graph."""
        paths = output_formatter.save_all_formats(mock_video_intelligence, str(temp_output_dir))

        # Should create GEXF file when knowledge graph exists
        gexf_files = [path for path in paths.values() if str(path).endswith('.gexf')]
        assert len(gexf_files) > 0, "Should create GEXF file when knowledge graph exists"

    def test_save_all_formats_chimera_format(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test save_all_formats with Chimera format enabled."""
        paths = output_formatter.save_all_formats(mock_video_intelligence, str(temp_output_dir), include_chimera_format=True)

        # Should create chimera_format.json
        chimera_files = [path for path in paths.values() if 'chimera' in str(path)]
        assert len(chimera_files) > 0, "Should create Chimera format file"

    def test_get_video_metadata_dict(self, output_formatter, mock_video_intelligence):
        """Test extraction of video metadata into dictionary."""
        metadata_dict = output_formatter._get_video_metadata_dict(mock_video_intelligence)

        assert metadata_dict["title"] == "Test Video"
        assert metadata_dict["url"] == "https://www.youtube.com/watch?v=test123"
        assert metadata_dict["channel"] == "Test Channel"
        assert metadata_dict["duration"] == 300
        assert "published_at" in metadata_dict

    def test_get_video_metadata_dict_none_video(self, output_formatter):
        """Test metadata extraction with None video."""
        metadata_dict = output_formatter._get_video_metadata_dict(None)

        assert metadata_dict["title"] == "Unknown"
        assert metadata_dict["url"] == "Unknown"
        assert metadata_dict["channel"] == "Unknown"
        assert metadata_dict["duration"] == 0

    def test_save_transcript_custom_output_dir(self, output_formatter, mock_video_intelligence, temp_directory):
        """Test saving transcript to custom output directory."""
        custom_dir = temp_directory / "custom_output"
        custom_dir.mkdir()

        paths = output_formatter.save_transcript(mock_video_intelligence, str(custom_dir), ["txt"])

        txt_file = Path(paths["txt"])
        assert txt_file.parent == custom_dir

    def test_save_all_formats_creates_structure(self, output_formatter, mock_video_intelligence, temp_directory):
        """Test that save_all_formats creates proper directory structure."""
        paths = output_formatter.save_all_formats(mock_video_intelligence, str(temp_directory))

        # Should create a subdirectory with video ID
        created_dirs = [path.parent for path in paths.values() if path.parent != temp_directory]
        assert len(set(created_dirs)) == 1  # All files should be in same directory

        main_dir = list(paths.values())[0].parent
        assert main_dir.exists()
        assert main_dir.is_dir()
        assert main_dir != temp_directory  # Should not be the temp root directory

    def test_entities_file_creation(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test entities.json file creation."""
        paths = output_formatter.save_all_formats(mock_video_intelligence, str(temp_output_dir))

        entities_file = None
        for path in paths.values():
            if "entities.json" in str(path):
                entities_file = path
                break

        assert entities_file is not None
        assert entities_file.exists()

        with open(entities_file) as f:
            data = json.load(f)

        assert "video_url" in data
        assert "entities" in data
        assert len(data["entities"]) == 3
        assert data["entities"][0]["name"] == "John Doe"

    def test_relationships_file_creation(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test relationships.json file creation."""
        paths = output_formatter.save_all_formats(mock_video_intelligence, str(temp_output_dir))

        relationships_file = None
        for path in paths.values():
            if "relationships.json" in str(path):
                relationships_file = path
                break

        assert relationships_file is not None
        assert relationships_file.exists()

        with open(relationships_file) as f:
            data = json.load(f)

        assert "video_url" in data
        assert "relationships" in data
        assert len(data["relationships"]) == 2
        assert data["relationships"][0]["subject"] == "John Doe"

    def test_knowledge_graph_file_creation(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test knowledge_graph.json file creation."""
        paths = output_formatter.save_all_formats(mock_video_intelligence, str(temp_output_dir))

        kg_file = None
        for path in paths.values():
            if "knowledge_graph.json" in str(path):
                kg_file = path
                break

        assert kg_file is not None
        assert kg_file.exists()

        with open(kg_file) as f:
            data = json.load(f)

        assert "nodes" in data
        assert "edges" in data
        assert "node_count" in data
        assert "edge_count" in data
        assert data["node_count"] == 3
        assert data["edge_count"] == 2

    def test_report_file_creation(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test report.md file creation."""
        paths = output_formatter.save_all_formats(mock_video_intelligence, str(temp_output_dir))

        report_file = None
        for path in paths.values():
            if "report.md" in str(path):
                report_file = path
                break

        assert report_file is not None
        assert report_file.exists()

        content = report_file.read_text()
        assert "# Video Intelligence Report:" in content
        assert "Test Video" in content
        assert "This is a comprehensive test summary demonstrating the output formatter functionality" in content
        assert "John Doe" in content
        assert "Google" in content

    def test_manifest_file_creation(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test manifest.json file creation."""
        paths = output_formatter.save_all_formats(mock_video_intelligence, str(temp_output_dir))

        manifest_file = None
        for path in paths.values():
            if "manifest.json" in str(path):
                manifest_file = path
                break

        assert manifest_file is not None
        assert manifest_file.exists()

        with open(manifest_file) as f:
            data = json.load(f)

        assert "version" in data
        assert "created_at" in data
        assert "video" in data
        assert "files" in data
        assert data["video"]["title"] == "Test Video"

    def test_to_chimera_format(self, output_formatter, mock_video_intelligence):
        """Test conversion to Chimera format."""
        chimera_data = output_formatter._to_chimera_format(mock_video_intelligence)

        assert chimera_data["type"] == "video"
        assert chimera_data["source"] == "video_intelligence"
        assert chimera_data["url"] == "https://www.youtube.com/watch?v=test123"
        assert chimera_data["title"] == "Test Video"
        assert chimera_data["content"] == mock_video_intelligence.transcript.full_text
        assert chimera_data["summary"] == mock_video_intelligence.summary

    def test_to_chimera_format_with_none_values(self, output_formatter, mock_video_metadata, mock_transcript):
        """Test Chimera format conversion with None values."""
        # Create video intelligence with empty string for summary
        video_intel = VideoIntelligence(
            metadata=mock_video_metadata,
            transcript=mock_transcript,
            summary="",  # Empty string instead of None
            entities=[],
            relationships=[],
            key_points=[],
            topics=[]
        )

        chimera_data = output_formatter._to_chimera_format(video_intel)

        assert chimera_data["summary"] == ""  # Empty string instead of None
        assert chimera_data["metadata"]["published_at"] is not None  # Should be converted to string

    def test_save_transcript_with_empty_transcript(self, output_formatter, temp_output_dir):
        """Test saving transcript with empty transcript."""
        metadata = VideoMetadata(
            video_id="test_123",
            url="https://www.youtube.com/watch?v=test123",
            title="Test Video",
            channel="Test Channel",
            channel_id="test_channel",
            published_at=datetime.now(),
            duration=300,
            view_count=1000,
            description="Test description",
            tags=["test"]
        )

        transcript = VideoTranscript(
            full_text="",
            segments=[],
        )

        video_intel = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary="Test summary",
            entities=[],
            relationships=[],
            key_points=[],
            topics=[]
        )

        paths = output_formatter.save_transcript(video_intel, str(temp_output_dir), ["txt"])

        txt_file = Path(paths["txt"])
        assert txt_file.exists()
        assert txt_file.read_text() == ""

    def test_save_all_formats_with_empty_video(self, output_formatter, temp_output_dir):
        """Test save_all_formats with minimal video data."""
        metadata = VideoMetadata(
            video_id="test_123",
            url="https://www.youtube.com/watch?v=test123",
            title="Test Video",
            channel="Test Channel",
            channel_id="test_channel",
            published_at=datetime.now(),
            duration=300,
            view_count=1000,
            description="Test description",
            tags=["test"]
        )

        transcript = VideoTranscript(
            full_text="Test",
            segments=[{"text": "Test", "start": 0.0, "end": 5.0}],
        )

        video_intel = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary="Test",
            entities=[],
            relationships=[],
            key_points=[],
            topics=[]
        )

        # Should not raise any exceptions
        paths = output_formatter.save_all_formats(video_intel, str(temp_output_dir))
        assert len(paths) > 0

    def test_directory_creation_error(self, output_formatter, mock_video_intelligence):
        """Test handling of directory creation errors."""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                output_formatter.save_transcript(mock_video_intelligence, "/invalid/path", ["txt"])

    def test_file_write_error(self, output_formatter, mock_video_intelligence, temp_output_dir):
        """Test handling of file write errors."""
        with patch('builtins.open', side_effect=PermissionError("Write permission denied")):
            with pytest.raises(PermissionError):
                output_formatter.save_transcript(mock_video_intelligence, str(temp_output_dir), ["txt"])

    def test_save_all_formats_with_complex_entities(self, output_formatter, temp_output_dir):
        """Test save_all_formats with complex entity data."""
        metadata = VideoMetadata(
            video_id="complex_test",
            url="https://www.youtube.com/watch?v=complex",
            title="Complex Entity Test",
            channel="Test Channel",
            channel_id="test_channel",
            published_at=datetime.now(),
            duration=600,
            view_count=5000,
            description="Complex entity testing",
            tags=["complex", "entities"]
        )

        transcript = VideoTranscript(
            full_text="Complex entity extraction test with multiple types.",
            segments=[{"text": "Complex entity extraction test", "start": 0.0, "end": 10.0}]
        )

        entities = [
            EnhancedEntity(
                name="Dr. Sarah Johnson",
                type="PERSON",
                mention_count=5,
                extraction_sources=["SpaCy", "GLiNER"],
                canonical_form="Sarah Johnson",
                context_windows=[
                    {"text": "Dr. Sarah Johnson is the lead researcher", "timestamp": "00:01:40", "speaker": "Narrator"}
                ],
                aliases=["Dr. Johnson", "Sarah", "Dr. Sarah"],
                temporal_distribution=[
                    {"timestamp": "00:02:00", "duration": 60.0, "context_type": "spoken"},
                    {"timestamp": "00:05:00", "duration": 120.0, "context_type": "both"}
                ]
            ),
            EnhancedEntity(
                name="Massachusetts Institute of Technology",
                type="ORGANIZATION",
                mention_count=8,
                extraction_sources=["SpaCy"],
                canonical_form="MIT",
                context_windows=[
                    {"text": "Massachusetts Institute of Technology conducted", "timestamp": "00:03:20", "speaker": "Professor"}
                ],
                aliases=["MIT", "M.I.T.", "Massachusetts Tech"],
                temporal_distribution=[
                    {"timestamp": "00:03:00", "duration": 120.0, "context_type": "visual"},
                    {"timestamp": "00:06:40", "duration": 200.0, "context_type": "both"}
                ]
            )
        ]

        video_intel = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary="Complex entity extraction test",
            entities=entities,
            relationships=[],
            key_points=[],
            topics=[]
        )

        paths = output_formatter.save_all_formats(video_intel, str(temp_output_dir))

        # Verify entities file contains complex data
        entities_file = None
        for path in paths.values():
            if "entities.json" in str(path):
                entities_file = path
                break

        with open(entities_file) as f:
            data = json.load(f)

        assert len(data["entities"]) == 2
        assert data["entities"][0]["name"] == "Dr. Sarah Johnson"
        assert data["entities"][0]["type"] == "PERSON"
        assert len(data["entities"][0]["aliases"]) == 3
        assert len(data["entities"][0]["context_windows"]) == 1
        assert len(data["entities"][0]["temporal_distribution"]) == 2

    def test_save_all_formats_with_relationship_evidence(self, output_formatter, temp_output_dir):
        """Test save_all_formats with relationship evidence chains."""
        metadata = VideoMetadata(
            video_id="evidence_test",
            url="https://www.youtube.com/watch?v=evidence",
            title="Evidence Chain Test",
            channel="Test Channel",
            channel_id="test_channel",
            published_at=datetime.now(),
            duration=300,
            view_count=1000,
            description="Evidence chain testing",
            tags=["evidence", "relationships"]
        )

        transcript = VideoTranscript(
            full_text="Evidence chain testing for relationships.",
            segments=[{"text": "Evidence chain testing", "start": 0.0, "end": 10.0}]
        )

        entities = [
            EnhancedEntity(name="Person A", type="PERSON", mention_count=1, extraction_sources=["SpaCy"], canonical_form="Person A", context_windows=[], aliases=[], temporal_distribution=[]),
            EnhancedEntity(name="Company X", type="ORGANIZATION", mention_count=1, extraction_sources=["SpaCy"], canonical_form="Company X", context_windows=[], aliases=[], temporal_distribution=[])
        ]

        relationships = [
            {
                "subject": "Person A",
                "predicate": "founded",
                "object": "Company X",
                "confidence": 0.95,
                "extraction_source": "REBEL",
                "evidence_chain": [
                    {"direct_quote": "Person A founded Company X in 2010", "timestamp": "00:00:50", "context_window": "startup focused on AI"},
                    {"direct_quote": "Company X was established by Person A", "timestamp": "00:01:30", "context_window": "successful entrepreneur"},
                    {"direct_quote": "Person A is the founder of Company X", "timestamp": "00:02:15", "context_window": "innovative leader"}
                ],
                "context_window": {
                    "text": "Person A founded Company X in 2010 as a startup focused on AI",
                    "start": 50,
                    "end": 100
                }
            }
        ]

        video_intel = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary="Evidence chain test",
            entities=entities,
            relationships=relationships,
            key_points=[],
            topics=[]
        )

        paths = output_formatter.save_all_formats(video_intel, str(temp_output_dir))

        # Verify relationships file contains evidence chains
        relationships_file = None
        for path in paths.values():
            if "relationships.json" in str(path):
                relationships_file = path
                break

        with open(relationships_file) as f:
            data = json.load(f)

        assert len(data["relationships"]) == 1
        relationship = data["relationships"][0]
        assert relationship["subject"] == "Person A"
        assert relationship["predicate"] == "founded"
        assert relationship["object"] == "Company X"
        assert len(relationship["evidence_chain"]) == 3
        assert "context" in relationship

    def test_save_all_formats_large_dataset(self, output_formatter, temp_output_dir):
        """Test save_all_formats with large dataset."""
        metadata = VideoMetadata(
            video_id="large_test",
            url="https://www.youtube.com/watch?v=large",
            title="Large Dataset Test",
            channel="Test Channel",
            channel_id="test_channel",
            published_at=datetime.now(),
            duration=3600,
            view_count=100000,
            description="Large dataset testing",
            tags=["large", "dataset"]
        )

        # Create large transcript
        large_text = " ".join([f"This is sentence number {i} in a large dataset test." for i in range(1000)])
        transcript = VideoTranscript(
            full_text=large_text,
            segments=[{"text": large_text[:100], "start": 0.0, "end": 10.0}]
        )

        # Create many entities
        entities = [
            EnhancedEntity(
                name=f"Entity{i}",
                type="PERSON" if i % 2 == 0 else "ORGANIZATION",
                mention_count=i + 1,
                extraction_sources=["SpaCy"],
                canonical_form=f"Entity{i}",
                context_windows=[],
                aliases=[],
                temporal_distribution=[]
            )
            for i in range(100)
        ]

        # Create many relationships
        relationships = [
            {
                "subject": f"Entity{i}",
                "predicate": "related_to",
                "object": f"Entity{i+1}",
                "confidence": 0.8,
                "extraction_source": "REBEL"
            }
            for i in range(99)
        ]

        video_intel = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary="Large dataset test",
            entities=entities,
            relationships=relationships,
            key_points=[],
            topics=[]
        )

        # Should handle large dataset without issues
        paths = output_formatter.save_all_formats(video_intel, str(temp_output_dir))

        # Verify all files were created
        assert len(paths) >= 8

        # Verify content in key files
        with open([p for p in paths.values() if "entities.json" in str(p)][0]) as f:
            entities_data = json.load(f)
            assert len(entities_data["entities"]) == 100

        with open([p for p in paths.values() if "relationships.json" in str(p)][0]) as f:
            relationships_data = json.load(f)
            assert len(relationships_data["relationships"]) == 99