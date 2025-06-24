# ClipScribe Output Formats Documentation

*Last Updated: June 23, 2025 at 10:20 PM PDT*

This document provides detailed information about all output formats available in ClipScribe.

## Overview

ClipScribe can save transcripts and analysis in multiple formats, either individually or as a complete structured output package. The structured output is optimized for machine readability and Chimera integration.

## Structured Output Format

When using `save_all_formats()`, ClipScribe creates a machine-readable directory structure:

```
{date}_{platform}_{video_id}/
├── transcript.txt       # Plain text transcript
├── transcript.json      # Complete data with analysis
├── transcript.srt       # Subtitle file (SRT format)
├── transcript.vtt       # Web subtitle file (WebVTT)
├── metadata.json        # Video metadata & statistics
├── entities.json        # Extracted entities for knowledge graph
├── manifest.json        # File index with checksums
└── chimera_format.json  # Chimera-compatible format
```

### Directory Naming Convention
- **Pattern**: `{date}_{platform}_{video_id}/`
- **Example**: `20250623_youtube_dQw4w9WgXcQ/`
- **Components**:
  - `date`: YYYYMMDD format
  - `platform`: youtube, vimeo, tiktok, etc.
  - `video_id`: Platform-specific video identifier

## Individual File Formats

### 1. Plain Text (transcript.txt)

Simple, human-readable transcript without formatting.

**Format**:
```
This is the full transcript of the video. It contains everything that was said
without any timestamps or additional metadata. Perfect for reading, searching,
or copy-pasting into other documents.
```

**Use Cases**:
- Reading and analysis
- Full-text search
- Copy/paste into documents
- Text processing pipelines

### 2. Full JSON (transcript.json)

Complete data structure with all transcript, analysis, and metadata.

**Format**:
```json
{
  "metadata": {
    "title": "Video Title",
    "url": "https://youtube.com/watch?v=...",
    "channel": "Channel Name",
    "duration": 300,
    "published_at": "2025-06-20T10:30:00Z",
    "view_count": 150000,
    "description": "Video description..."
  },
  "transcript": {
    "full_text": "Complete transcript text...",
    "segments": [
      {
        "start": 0.0,
        "end": 5.5,
        "text": "Segment text"
      }
    ],
    "language": "en",
    "confidence": 0.95
  },
  "analysis": {
    "summary": "Executive summary of the video content",
    "key_points": [
      {
        "timestamp": 45,
        "text": "Important point discussed",
        "importance": 0.9,
        "context": "Surrounding context"
      }
    ],
    "entities": [
      {
        "name": "Elon Musk",
        "type": "PERSON",
        "confidence": 0.98,
        "properties": {},
        "timestamp": 120
      }
    ],
    "topics": ["AI", "Technology", "Future"],
    "sentiment": null
  },
  "processing": {
    "cost": 0.0045,
    "time": 23.5,
    "processed_at": "2025-06-23T22:14:39.074128",
    "model": "gemini-1.5-flash"
  }
}
```

**Use Cases**:
- Complete data export
- Database import
- Custom analysis
- API responses

### 3. SRT Subtitles (transcript.srt)

Standard subtitle format compatible with most video players.

**Format**:
```
1
00:00:00,000 --> 00:00:05,500
Hello everyone, welcome to today's video.

2
00:00:05,500 --> 00:00:10,000
Today we'll be discussing artificial intelligence.

3
00:00:10,000 --> 00:00:15,000
Let's start with the basics.
```

**Use Cases**:
- Upload to YouTube
- Video editing software
- Media players (VLC, etc.)
- Accessibility compliance

### 4. WebVTT Subtitles (transcript.vtt)

Web-standard subtitle format for HTML5 video players.

**Format**:
```
WEBVTT

00:00:00.000 --> 00:00:05.500
Hello everyone, welcome to today's video.

00:00:05.500 --> 00:00:10.000
Today we'll be discussing artificial intelligence.

00:00:10.000 --> 00:00:15.000
Let's start with the basics.
```

**Use Cases**:
- Web video players
- Streaming platforms
- HTML5 `<video>` element
- Better styling options than SRT

### 5. Metadata File (metadata.json)

Lightweight file containing video information and processing statistics.

**Format**:
```json
{
  "video": {
    "title": "Video Title",
    "url": "https://youtube.com/watch?v=...",
    "channel": "Channel Name",
    "duration": 300,
    "published_at": "2025-06-20T10:30:00Z",
    "view_count": 150000,
    "description": "Video description..."
  },
  "processing": {
    "cost": 0.0045,
    "time": 23.5,
    "processed_at": "2025-06-23T22:14:39.074128",
    "clipscribe_version": "2.0.0"
  },
  "statistics": {
    "transcript_length": 5432,
    "word_count": 876,
    "entity_count": 12,
    "key_point_count": 8,
    "topic_count": 4
  }
}
```

**Use Cases**:
- Quick metadata access
- Processing analytics
- Cost tracking
- Quality metrics

### 6. Entities File (entities.json)

Extracted entities for knowledge graph integration.

**Format**:
```json
{
  "video_url": "https://youtube.com/watch?v=...",
  "video_title": "Video Title",
  "entities": [
    {
      "name": "OpenAI",
      "type": "ORGANIZATION",
      "confidence": 0.98,
      "properties": {},
      "timestamp": null
    },
    {
      "name": "Sam Altman",
      "type": "PERSON",
      "confidence": 0.95,
      "properties": {},
      "timestamp": 45
    },
    {
      "name": "San Francisco",
      "type": "LOCATION",
      "confidence": 0.92,
      "properties": {},
      "timestamp": 120
    }
  ],
  "topics": ["AI", "Technology", "Future"],
  "key_facts": [
    "OpenAI released GPT-4 in March 2023",
    "The model has 1.7 trillion parameters",
    "Training cost estimated at $100 million"
  ]
}
```

**Entity Types**:
- PERSON - Individual people
- ORGANIZATION - Companies, institutions
- LOCATION - Places, cities, countries
- EVENT - Conferences, launches
- CONCEPT - Abstract ideas
- TECHNOLOGY - Specific technologies
- PRODUCT - Products or services

**Use Cases**:
- Knowledge graph building
- Entity relationship mapping
- Content categorization
- Search indexing

### 7. Manifest File (manifest.json)

Index of all generated files with metadata.

**Format**:
```json
{
  "version": "1.0",
  "created_at": "2025-06-23T22:14:39.074128",
  "video": {
    "title": "Video Title",
    "url": "https://youtube.com/watch?v=...",
    "platform": "youtube"
  },
  "files": {
    "transcript_txt": {
      "path": "transcript.txt",
      "format": "plain_text",
      "size": 5432
    },
    "transcript_json": {
      "path": "transcript.json",
      "format": "json",
      "size": 12456
    },
    "transcript_srt": {
      "path": "transcript.srt",
      "format": "srt_subtitles",
      "size": 6789
    },
    "transcript_vtt": {
      "path": "transcript.vtt",
      "format": "webvtt_subtitles",
      "size": 6890
    },
    "metadata": {
      "path": "metadata.json",
      "format": "json",
      "size": 2345
    },
    "entities": {
      "path": "entities.json",
      "format": "json",
      "size": 1234
    }
  }
}
```

**Use Cases**:
- Programmatic file discovery
- Integrity checking
- Automated processing
- Archive management

### 8. Chimera Format (chimera_format.json)

Specialized format for Chimera Researcher integration.

**Format**:
```json
{
  "type": "video",
  "source": "video_intelligence",
  "url": "https://youtube.com/watch?v=...",
  "title": "Video Title",
  "content": "Full transcript text...",
  "summary": "Executive summary of the video",
  "metadata": {
    "channel": "Channel Name",
    "duration": 300,
    "published_at": "2025-06-20T10:30:00Z",
    "view_count": 150000,
    "key_points": [...],
    "entities": [...],
    "topics": ["AI", "Technology"],
    "sentiment": null,
    "processing_cost": 0.0045
  }
}
```

**Use Cases**:
- Chimera Researcher integration
- Multi-source intelligence gathering
- Research automation
- Content aggregation

## Choosing the Right Format

### For Human Consumption
- **transcript.txt** - Simple reading
- **transcript.srt** - Watch with subtitles

### For Data Processing
- **transcript.json** - Complete data access
- **entities.json** - Knowledge extraction
- **metadata.json** - Quick stats

### For Video Platforms
- **transcript.srt** - YouTube, video editors
- **transcript.vtt** - Web players

### For Integration
- **chimera_format.json** - Chimera Researcher
- **manifest.json** - Automated pipelines

## Usage Examples

### Save All Formats
```python
from clipscribe.retrievers import VideoIntelligenceRetriever

retriever = VideoIntelligenceRetriever()
result = await retriever.process_url(video_url)
paths = retriever.save_all_formats(result, output_dir="output")
```

### Save Specific Formats
```python
# Just text and SRT
paths = retriever.save_transcript(
    result, 
    formats=["txt", "srt"],
    output_dir="transcripts"
)
```

### Access Saved Files
```python
# Load manifest
import json
with open(paths["manifest"], 'r') as f:
    manifest = json.load(f)
    
# Load entities
with open(paths["entities"], 'r') as f:
    entities = json.load(f)
    for entity in entities["entities"]:
        print(f"{entity['name']} ({entity['type']})")
```

## Best Practices

1. **Use structured output** for production systems
2. **Include manifest.json** for file tracking
3. **Store entities.json** for knowledge graphs
4. **Keep chimera_format.json** for integration
5. **Archive complete directories** for reproducibility

Remember: The structured output format provides everything needed for both human review and machine processing! 🎯 