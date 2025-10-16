# ClipScribe / Station10.media - Project Structure

**Last Updated:** October 15, 2025  
**Status:** Clean and organized  
**Purpose:** Reference for project organization and file locations

---

## 📁 Root Directory (Essential Files Only)

```
clipscribe/
├── README.md                    # Project overview
├── ROADMAP.md                   # Product roadmap (SaaS direction)
├── CHANGELOG.md                 # Version history
├── CONTINUATION_PROMPT.md       # AI assistant context
├── CONTRIBUTING.md              # Contribution guidelines
├── SECURITY.md                  # Security policy
├── LICENSE                      # Apache 2.0
├── pyproject.toml              # Python dependencies (Poetry)
├── poetry.lock                 # Locked dependencies
├── pytest.ini                  # Test configuration
├── .gitignore                  # Git ignore rules
├── .env (git-ignored)          # Local environment variables
└── .env.production (git-ignored) # Production config
```

**Deployment configs:**
```
├── Dockerfile                  # Multi-stage (API, worker, CLI)
├── Dockerfile.api              # API service
├── Dockerfile.job              # Cloud Run Job worker
├── cloudbuild.yaml             # Main build config
├── cloudbuild-jobs.yaml        # Job worker deployment
├── cloudbuild-worker.yaml      # Worker service deployment
├── docker-compose.yml          # Local dev environment
└── cors.json                   # CORS config for GCS
```

---

## 📚 Documentation (`docs/`)

```
docs/
├── README.md                   # Docs navigation
├── CLI_REFERENCE.md            # Command reference
├── QUICK_REFERENCE.md          # Quick start guide
├── ASYNC_MONITOR_ARCHITECTURE.md # RSS monitoring architecture
│
├── planning/                   # Planning & architecture docs
│   ├── SAAS_PRODUCT_ROADMAP.md        # 16-week execution plan
│   ├── PHASE_1_DETAILED_PLAN.md       # Week-by-week details
│   ├── PRICING_AND_ECONOMICS.md       # Pricing strategy
│   ├── CLOUD_RUN_ARCHITECTURE.md      # Production infrastructure
│   └── CLEANUP_PLAN.md                # Oct 15 cleanup (complete)
│
├── advanced/
│   └── testing/
│       └── MASTER_TEST_VIDEO_TABLE.md # Comprehensive test suite
│
├── archive/                    # Historical documentation
│   └── [97 archived docs]
│
└── images/                     # Documentation images
```

---

## 💻 Source Code (`src/clipscribe/`)

```
src/clipscribe/
├── __init__.py
├── models.py                   # Pydantic data models
├── core_data.py               # Core data structures
│
├── commands/                   # CLI commands (Click)
│   ├── cli.py                 # Main CLI entry point
│   └── [other commands]
│
├── transcribers/              # Transcription engines (NEW)
│   ├── voxtral_transcriber.py     # Standard tier (Voxtral API)
│   ├── whisperx_transcriber.py    # Premium tier (WhisperX)
│   └── dual_mode_transcriber.py   # Intelligent tier selection
│
├── processors/                # Video processing pipelines
│   ├── hybrid_processor.py    # Voxtral + Grok pipeline
│   └── [other processors]
│
├── retrievers/                # Video download & metadata
│   ├── video_retriever_v2.py  # Main video intelligence retriever
│   ├── universal_video_client.py # Multi-platform downloader
│   └── [other retrievers]
│
├── extractors/                # Entity extraction
├── database/                  # Single-user SQLite
│   ├── schema.sql            # Videos, entities, relationships
│   └── db_manager.py         # Database operations
│
├── api/                       # FastAPI backend (for Cloud Run)
├── storage/                   # GCS integration
├── utils/                     # Utilities
│   ├── error_handler.py      # Error categorization (new)
│   └── [other utils]
│
└── [other packages]
```

---

## 🧪 Tests (`tests/`)

```
tests/
├── unit/                      # Unit tests
├── integration/               # Integration tests
├── fixtures/                  # Test data
└── conftest.py               # Pytest configuration
```

---

## 📜 Scripts (`scripts/`)

```
scripts/
├── test_whisperx.py           # WhisperX full result validation
└── [91 other utility scripts]
```

---

## 📦 Examples (`examples/`)

```
examples/
├── README.md
├── quick_start.py
├── advanced_features_demo.py
├── batch_processing.py
└── [other examples]
```

---

## 🗃️ Archive (`archive/`)

```
archive/
├── telegram_exploration_oct_2025/  # Oct 12-15 Telegram bot exploration
│   ├── SALVAGE_PLAN.md
│   ├── STATION10_*.md (6 docs)
│   └── STATUS_OCT12.md
│
├── roadmaps/                  # Historical roadmaps
│   ├── ROADMAP.md (Sep 2025)
│   ├── ROADMAP_FEATURES.md (Aug 2025)
│   └── ROADMAP_PHASES.md (Sep 2025)
│
├── planning_oct_2025/         # Oct planning docs
│   ├── OUTPUT_MANAGEMENT_README.md
│   ├── PRODUCTION_README.md
│   └── TODO.md
│
└── legacy_web_2025aug/        # Old static landing page
    └── index.html
```

---

## 🚫 Git-Ignored Directories

```
# Generated/Temporary (Not in Git)
cache/          # Video cache (cleaned, now 976KB)
logs/           # Application logs (24MB)
output/         # Processing results (14MB)
test_videos/    # Test audio files (188MB, NEW)
htmlcov/        # Test coverage (deleted)
.video_cache/   # Video download cache (5.4MB)

# Secrets (NEVER in Git)
secrets/        # GCP service account JSON
.env            # Local environment variables
.env.production # Production config
```

---

## 📊 Project Statistics

```
Total size: 1.7GB
Tracked files (in git): 430 files
Documentation: ~100 files (including archives)
Source code: ~100 Python files
Tests: ~60 test files
Scripts: 91 utility scripts
```

---

## ✅ Security Status

### Properly Secured
- ✅ secrets/ directory (git-ignored, contains service-account.json)
- ✅ .env files (git-ignored)
- ✅ test_videos/ (git-ignored, prevents large file commits)
- ✅ cache/ (git-ignored)
- ✅ output/ (git-ignored)

### Historical Issues (Resolved)
- ⚠️ .env accidentally committed July 25, 2025 (removed same day)
- ✅ No secrets in current repo
- ✅ No secrets in recent commits

---

## 📋 Maintenance Guidelines

### Root Directory Rules
**Only keep:**
- Standard project files (README, CHANGELOG, LICENSE, CONTRIBUTING, SECURITY)
- Product docs (ROADMAP, CONTINUATION_PROMPT)
- Build configs (Dockerfiles, cloudbuild yamls)
- Python configs (pyproject.toml, poetry.lock, pytest.ini)

**Never add:**
- Planning docs (→ docs/planning/)
- Test files (→ tests/ or scripts/)
- Temporary files (→ .gitignore)

### Documentation Organization
- **Root:** User-facing docs only (README, ROADMAP, CHANGELOG)
- **docs/:** All other documentation
- **docs/planning/:** Architecture, planning, economics
- **docs/archive/:** Historical documents
- **docs/advanced/:** Advanced guides and specs

### Secrets Management
- **Always use:** .env files (git-ignored)
- **Never commit:** API keys, tokens, passwords, service account JSONs
- **Check before commit:** `git status` to verify no secrets staged

---

## 🎯 Current Organization Status

**✅ Clean Root:** 6 essential .md files (was 11)
**✅ Docs Organized:** Planning docs in docs/planning/
**✅ Security Verified:** No secrets in repo
**✅ Git Ignore Updated:** test_videos/, htmlcov/, test outputs
**✅ Cache Cleaned:** 2GB freed (cache now 976KB)
**✅ Archives Organized:** 3 archive subdirectories, well-documented

**Project is clean, organized, and ready for Week 1 development.** 🚀

