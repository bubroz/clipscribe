# ClipScribe Sample Outputs

**Real examples from ClipScribe v3.0.0-rc processing**

These are actual outputs from production processing - not mocked or sanitized. Download and inspect to see exactly what ClipScribe delivers.

---

## Sample Files

### 1. multispeaker_panel_36min.json (1.1MB)

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

**Use case:** Multi-speaker content analysis, political intelligence, news monitoring

---

### 2. business_interview_30min.json (983KB)

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

**Use case:** Financial analysis, competitive intelligence, executive monitoring

---

### 3. technical_single_speaker_16min.json (219KB)

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

**Use case:** Medical research, technical documentation, educational content

---

## How to Use These

### Inspect the Data

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

### Import to Pandas

```python
import json
import pandas as pd

# Load
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

**Data Richness:**
- 50-70+ structured data points per 30min video
- Evidence for every extraction (100% coverage)
- Speaker attribution (up to 12 speakers)
- Time-based context (topic ranges, key moment timestamps)

**Real-World Applicability:**
- Import to research databases
- Query with SQL
- Analyze with Pandas
- Build knowledge graphs
- Feed into visualization tools

**Cost Efficiency:**
- $0.003-0.06 per 30min
- vs $0.60-1.20 for transcription-only services
- Intelligence extraction included (not extra)

---

**These are production outputs. No sanitization, no cherry-picking. This is what ClipScribe delivers.**

**Want to try it?** See [README.md](../../README.md) for installation and usage.

