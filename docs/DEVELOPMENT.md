# ClipScribe Development Guide

**Last Updated:** November 12, 2025  
**Version:** v2.62.0  
**Validated:** November 12, 2025 (all commands tested, protocols verified)

---

## Setup Development Environment

### Prerequisites:
- Python 3.12+
- Poetry (dependency management)
- Google Cloud SDK (for GCS access)
- Modal account (for GPU processing)

### Installation:
```bash
# Clone repository
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe

# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Add: XAI_API_KEY, GOOGLE_APPLICATION_CREDENTIALS
```

---

## Running Tests

### All Integration Tests:
```bash
poetry run pytest tests/integration/ -v
```

**Expected:** 24/24 tests passing (10 Grok advanced features, 8 entity search, 6 topic search)

### Specific Tests:
```bash
# Topic search API
poetry run pytest tests/integration/test_topic_search_api.py -v

# Entity search API
poetry run pytest tests/integration/test_entity_search_api.py -v

# Modal pipeline
poetry run pytest tests/integration/test_modal_pipeline_e2e.py -v
```

---

## Deploy to Modal

### Deploy ClipScribe Transcriber:
```bash
poetry run modal deploy deploy/station10_modal.py
```

**Deploys:**
- ClipScribeTranscriber class
- WhisperX + pyannote + grok-4-fast-reasoning pipeline
- Updates live service

### View Modal Apps:
```bash
modal app list
```

### View Logs:
```bash
modal app logs clipscribe-transcription
```

---

## Development Workflows

### Test Modal Changes Locally:
```bash
# Edit deploy/station10_modal.py
# Deploy to Modal
poetry run modal deploy deploy/station10_modal.py

# Test with existing video
poetry run python scripts/test_structured_outputs.py
```

### Add New API Endpoint:
1. Create in `src/clipscribe/api/`
2. Add tests in `tests/integration/`
3. Run tests: `poetry run pytest tests/integration/`

### Update Database Schema:
1. Modify schema in API file
2. Delete local database: `rm data/clipscribe.db`
3. Reload data: `poetry run python scripts/load_validated_*.py`
4. Verify tests pass

---

## Project Structure

```
clipscribe/
├── src/clipscribe/           # Source code
│   ├── api/                  # Search APIs
│   │   ├── topic_search.py
│   │   └── entity_search.py
│   ├── models/               # Pydantic schemas
│   │   └── grok_schemas.py
│   ├── prompts/              # Grok prompts
│   │   └── intelligence_extraction.py
│   └── utils/                # Utilities
│       ├── grokipedia.py
│       └── logger_setup.py
├── deploy/                   # Modal deployment
│   └── station10_modal.py   # Main Modal service
├── tests/                    # Test suite
│   └── integration/          # Integration tests
├── scripts/                  # Utility scripts
│   ├── load_validated_*.py  # Data loaders
│   └── test_*.py            # Validation scripts
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # System architecture (14 Mermaid diagrams)
│   ├── WORKFLOW.md           # Production workflows (Modal + Local CLI)
│   ├── GROK_ADVANCED_FEATURES.md
│   ├── DEVELOPMENT.md         # This file
│   ├── VALIDATION_PROTOCOL.md # Documentation validation method
│   └── REPOSITORY_CLEANUP_PLAYBOOK.md # Cleanup template
└── examples/                 # Usage examples
```

---

## Key Files

**deploy/station10_modal.py:**
- Main Modal service (WhisperX + grok-4-fast-reasoning)
- ClipScribeTranscriber class
- grok-4-fast-reasoning Structured Outputs implementation

**src/clipscribe/api/:**
- topic_search.py - Topic search endpoint
- entity_search.py - Entity search endpoint

**src/clipscribe/models/grok_schemas.py:**
- Pydantic schemas for Structured Outputs
- No min_items (prevents hallucinations)

**tests/integration/:**
- test_topic_search_api.py (6 tests)
- test_entity_search_api.py (8 tests)
- test_grok_advanced_features.py (10 tests)
- test_modal_pipeline_e2e.py (2 tests - requires deployed Modal app)

---

## Common Development Tasks

### Process a Test Video:
```python
# Use Modal workflow (see WORKFLOW.md)
# Upload to GCS → Call Modal → Download results
```

### Run Validation on Existing Videos:
```bash
poetry run python scripts/test_structured_outputs.py
```

### Check Database Contents:
```bash
sqlite3 data/clipscribe.db "SELECT video_id, COUNT(*) FROM topics GROUP BY video_id"
sqlite3 data/clipscribe.db "SELECT type, COUNT(*) FROM entities GROUP BY type"
```

---

## Troubleshooting

**Import errors:**
- Check all dependencies installed: `poetry install`
- Verify Python 3.12+: `python --version`

**Modal errors:**
- Check secrets configured: `modal secret list`
- Required: huggingface, googlecloud-secret, grok-api-key

**Test failures:**
- Check database exists: `ls data/clipscribe.db`
- Reload data if needed: `poetry run python scripts/load_validated_*.py`

---

**This guide documents actual development workflows that work.**

