# ClipScribe Sample Outputs

**Real examples from ClipScribe v3.0.0 processing**

These are actual outputs from production processing - not mocked or sanitized. Download and inspect to see exactly what ClipScribe delivers.

**Available Formats:**
- **JSON** - Complete structured data (intelligence + transcript)
- **DOCX** - Professional reports (Google Docs, Word, Pages)
- **PPTX** - Executive presentations (Google Slides, PowerPoint, Keynote)
- **Markdown** - Searchable reports (GitHub, VS Code, Obsidian)
- **CSV** - Data tables (Google Sheets, Excel, Numbers)

---

## Sample Files

### 1. multispeaker_panel_36min (36-minute news panel)

**Source:** 36-minute news panel discussion  
**Speakers:** 12 detected  
**Processing:** WhisperX Local (Apple Silicon, FREE)  
**Cost:** $0.003 total

**What's inside:**
- **45 entities** (President Trump, Marjorie Taylor Greene, Mike Johnson, etc.)
- **11 relationships** (who-said-what-about-whom with evidence)
- **5 topics** with time ranges (Government Shutdown 00:00-15:00, etc.)
- **6 key moments** with timestamps and quotes
- **Sentiment analysis** (overall + per-topic)
- **Speaker-attributed transcript** (12 speakers labeled throughout)

**Available Formats:**
- `multispeaker_panel_36min.json` (1.1MB) - Full structured data
- `multispeaker_panel_36min.docx` (39KB) - Professional Word report
- `multispeaker_panel_36min.pptx` (34KB) - Executive PowerPoint deck
- `multispeaker_panel_36min.md` (6.1KB) - Markdown report
- `multispeaker_panel_36min_csv/` (5 files, 42KB total) - Data tables

**Use case:** Multi-speaker content analysis, political intelligence, news monitoring

---

### 2. business_interview_30min (30-minute executive interview)

**Source:** 30-minute executive interview (Palantir CEO)  
**Speakers:** 2 detected  
**Processing:** WhisperX Modal (Cloud GPU)  
**Cost:** $0.0575 total

**What's inside:**
- **17 entities** (Alex Karp, Palantir, Ukraine, ICE, Israel, etc.)
- **10 relationships** (Palantir works with Ukraine, Karp is CEO of Palantir, etc.)
- **5 topics** (AI applications, surveillance concerns, political views)
- **Competitive intelligence** (company positions, executive statements)
- **Word-level timing** for precise navigation

**Available Formats:**
- `business_interview_30min.json` (983KB) - Full structured data
- `business_interview_30min.docx` (39KB) - Professional Word report
- `business_interview_30min.pptx` (34KB) - Executive PowerPoint deck
- `business_interview_30min.md` (5.5KB) - Markdown report
- `business_interview_30min_csv/` (5 files, 44KB total) - Data tables

**Use case:** Financial analysis, competitive intelligence, executive monitoring

---

### 3. technical_single_speaker_16min (16-minute medical presentation)

**Source:** 16-minute medical/technical presentation  
**Speakers:** 1 detected  
**Processing:** WhisperX Local (Apple Silicon, FREE)  
**Cost:** $0.0018 total

**What's inside:**
- **20 entities** (medical terms, procedures, organizations)
- **6 relationships** (procedure connections, medical references)
- **5 topics** (medical themes with time ranges)
- **Technical accuracy** (medical jargon preserved)
- **Single speaker** (lecture/presentation format)

**Available Formats:**
- `technical_single_speaker_16min.json` (219KB) - Full structured data
- `technical_single_speaker_16min.docx` (39KB) - Professional Word report
- `technical_single_speaker_16min.pptx` (34KB) - Executive PowerPoint deck
- `technical_single_speaker_16min.md` (4.4KB) - Markdown report
- `technical_single_speaker_16min_csv/` (5 files, 21KB total) - Data tables

**Use case:** Medical research, technical documentation, educational content

---

## Format Guide

### DOCX Reports (Word/Google Docs/Pages)

Professional intelligence reports with:
- Executive summary with key metrics
- Entities table (top 20 with evidence)
- Relationships with evidence quotes
- Topics analysis with time ranges
- Key moments timeline
- Sentiment breakdown

**How to open:**
- **Google Docs:** Upload to Google Drive, right-click → "Open with Google Docs"
- **Microsoft Word:** Double-click (Windows/Mac)
- **Apple Pages:** Right-click → "Open With → Pages"
- **LibreOffice:** File → Open

**Best for:** Sharing with non-technical stakeholders, editing/annotating findings, creating reports

---

### CSV Data Tables (Google Sheets/Excel/Numbers)

5 CSV files per sample:
- `entities.csv` - All extracted entities with confidence and evidence
- `relationships.csv` - Subject-predicate-object relationships with evidence
- `topics.csv` - Topics with relevance scores and time ranges
- `key_moments.csv` - Significant moments with timestamps and quotes
- `segments.csv` - Full transcript with speaker attribution and timing

**How to open:**
- **Google Sheets:** Upload to Google Drive, opens automatically
- **Microsoft Excel:** Double-click or File → Open
- **Apple Numbers:** Right-click → "Open With → Numbers"
- **Python/Pandas:** `pd.read_csv('entities.csv')`

**Features:**
- UTF-8 with BOM encoding (Excel-friendly)
- Proper quote escaping
- Unicode support for international characters

**Best for:** Data analysis, importing to databases, Excel/Sheets pivoting, research datasets

---

### PPTX Presentations (PowerPoint/Google Slides/Keynote)

Executive 7-slide decks:
1. Title slide with date
2. Executive summary (metrics overview)
3. Key entities (top 10 with confidence)
4. Relationships (top 8 connections)
5. Topics & timeline
6. Key moments (top 6)
7. Sentiment analysis

**How to open:**
- **Google Slides:** Upload to Google Drive, right-click → "Open with Google Slides"
- **Microsoft PowerPoint:** Double-click
- **Apple Keynote:** Right-click → "Open With → Keynote"

**Best for:** Executive briefings, investor presentations, stakeholder updates

---

### Markdown Reports (GitHub/VS Code/Obsidian)

GitHub-flavored markdown with:
- Clean heading hierarchy
- Entities table (top 20)
- Relationships with blockquote evidence
- Topics table
- Key moments with timestamps
- Sentiment breakdown

**How to view:**
- **GitHub:** Renders automatically when pushed to repo
- **VS Code:** Right-click → "Open Preview"
- **Obsidian:** Opens as note
- **Any text editor:** Plain text readable

**Best for:** Version control, note-taking, knowledge management, developer workflows

---

## How to Use These

### Inspect JSON Data

```bash
# View structure
jq 'keys' multispeaker_panel_36min.json

# See entities
jq '.intelligence.entities[] | {name, type, evidence}' multispeaker_panel_36min.json | head -20

# See relationships
jq '.intelligence.relationships[] | {subject, predicate, object}' multispeaker_panel_36min.json

# See speaker distribution
jq '.transcript.segments | group_by(.speaker) | map({speaker: .[0].speaker, count: length})' multispeaker_panel_36min.json
```

### Import JSON to Pandas

```python
import json
import pandas as pd

# Load JSON
with open('multispeaker_panel_36min.json') as f:
    data = json.load(f)

# Entities DataFrame
entities_df = pd.DataFrame(data['intelligence']['entities'])
print(f"Found {len(entities_df)} entities")
print(entities_df[['name', 'type', 'confidence']].head(10))

# Relationships DataFrame  
rels_df = pd.DataFrame(data['intelligence']['relationships'])
print(f"Found {len(rels_df)} relationships")
print(rels_df[['subject', 'predicate', 'object']].head(10))

# Topics with time ranges
topics_df = pd.DataFrame(data['intelligence']['topics'])
print(topics_df[['name', 'relevance', 'time_range']])
```

### Import CSV to Pandas (Faster!)

```python
import pandas as pd

# Load CSV files directly (no JSON parsing needed)
entities_df = pd.read_csv('multispeaker_panel_36min_csv/entities.csv')
relationships_df = pd.read_csv('multispeaker_panel_36min_csv/relationships.csv')
topics_df = pd.read_csv('multispeaker_panel_36min_csv/topics.csv')
moments_df = pd.read_csv('multispeaker_panel_36min_csv/key_moments.csv')
segments_df = pd.read_csv('multispeaker_panel_36min_csv/segments.csv')

print(f"Loaded {len(entities_df)} entities, {len(relationships_df)} relationships")
```

### Import to SQL

```python
import sqlite3
import json

conn = sqlite3.connect('intelligence.db')

with open('multispeaker_panel_36min.json') as f:
    data = json.load(f)

# Create tables
conn.execute('''
    CREATE TABLE IF NOT EXISTS entities (
        name TEXT,
        type TEXT,
        confidence REAL,
        evidence TEXT,
        video_id TEXT
    )
''')

# Insert data
for entity in data['intelligence']['entities']:
    conn.execute(
        "INSERT INTO entities VALUES (?, ?, ?, ?, ?)",
        (entity['name'], entity['type'], entity['confidence'], 
         entity['evidence'], 'multispeaker_panel_36min')
    )

conn.commit()
```

---

## What This Demonstrates

**Multi-Format Flexibility:**
- **JSON** for developers and data pipelines
- **DOCX** for business stakeholders and reports
- **PPTX** for executive briefings and presentations
- **Markdown** for documentation and knowledge bases
- **CSV** for analysis in Excel/Sheets/databases

**Data Richness:**
- 50-70+ structured data points per 30min video
- Evidence for every extraction (100% coverage)
- Speaker attribution (up to 12 speakers)
- Time-based context (topic ranges, key moment timestamps)

**Universal Compatibility:**
- **Google Workspace:** Docs, Sheets, Slides
- **Microsoft Office:** Word, Excel, PowerPoint
- **Apple:** Pages, Numbers, Keynote
- **Developers:** JSON APIs, Pandas, SQL databases
- **Researchers:** Markdown notes, version control

**Real-World Applicability:**
- Import to research databases
- Query with SQL
- Analyze with Pandas/Excel
- Build knowledge graphs
- Create executive presentations
- Feed into visualization tools

**Cost Efficiency:**
- $0.003-0.06 per 30min
- vs $0.60-1.20 for transcription-only services
- Intelligence extraction included (not extra)

---

**These are production outputs. No sanitization, no cherry-picking. This is what ClipScribe delivers.**

**24 sample files across 4 formats - download and inspect to see the quality for yourself.**

**Want to try it?** See [README.md](../../README.md) for installation and usage.

