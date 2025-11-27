# ClipScribe Development Guide

**Version:** v3.1.10  
**Last Updated:** November 2025  
**Status:** Provider-based architecture, GEOINT engine (Beta)

---

## Setup Development Environment

### Prerequisites
- Python 3.11-3.12
- Poetry (dependency management)
- Apple Silicon Mac (for local testing) OR
- Modal account (for cloud GPU) OR
- Both (recommended)

### Installation

```bash
# Clone repository
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe

# Install all dependencies
poetry install

# Configure environment
cp .env.example .env
# Add your API keys (see below)
```

### Environment Variables

```bash
# For Voxtral provider
MISTRAL_API_KEY=your_mistral_key

# For Grok intelligence
XAI_API_KEY=your_xai_key

# For WhisperX Local diarization
HUGGINGFACE_TOKEN=your_hf_token

# For WhisperX Modal (optional)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET=your-bucket-name
```

---

## Running Tests

### Unit Tests (Fast, Mocked)

```bash
# All unit tests
poetry run pytest tests/unit/ -v

# Provider tests specifically
poetry run pytest tests/unit/providers/ -v

# Expected: All pass, <10 seconds, $0 cost
```

### Integration Tests (Mocked APIs)

```bash
# All integration tests
poetry run pytest tests/integration/ -v

# Provider pipeline tests
poetry run pytest tests/integration/test_provider_pipeline.py -v
```

### Validation Tests (Real Audio)

```bash
# Test all providers with real audio
poetry run clipscribe process test_videos/medical_lxFd5xAN4cg.mp3 -t voxtral --no-diarize
poetry run clipscribe process test_videos/medical_lxFd5xAN4cg.mp3 -t whisperx-local
poetry run clipscribe process test_videos/medical_lxFd5xAN4cg.mp3 -t whisperx-modal
```

---

## Adding New Providers

### Step 1: Create Provider Class

```python
# src/clipscribe/providers/transcription/new_provider.py
from ..base import TranscriptionProvider, TranscriptResult

class NewProvider(TranscriptionProvider):
    @property
    def name(self) -> str:
        return "new-provider"
    
    @property
    def supports_diarization(self) -> bool:
        return True  # or False
    
    async def transcribe(self, audio_path, language=None, diarize=True):
        # Your implementation
        # Can wrap existing code or call new API
        return TranscriptResult(...)
    
    def estimate_cost(self, duration_seconds):
        # Cost calculation
        return cost
    
    def validate_config(self):
        # Check API keys, etc.
        return bool(api_key)
```

### Step 2: Register in Factory

```python
# src/clipscribe/providers/factory.py
from .transcription.new_provider import NewProvider

providers = {
    "voxtral": VoxtralProvider,
    "whisperx-modal": WhisperXModalProvider,
    "whisperx-local": WhisperXLocalProvider,
    "new-provider": NewProvider,  # Add here
}
```

### Step 3: Update CLI

```python
# src/clipscribe/commands/cli.py
@click.option(
    "--transcription-provider",
    type=click.Choice(["voxtral", "whisperx-modal", "whisperx-local", "new-provider"]),
    ...
)
```

### Step 4: Add Tests

```python
# tests/unit/providers/test_new_provider.py
def test_new_provider():
    provider = get_transcription_provider("new-provider")
    assert provider.name == "new-provider"
    # Add more tests
```

### Step 5: Document

- Add to docs/PROVIDERS.md
- Update cost comparison tables
- Add setup instructions

---

## Provider Development Best Practices

### Wrapping Existing Code (Recommended)

**Don't rewrite - wrap:**

```python
# GOOD: Wrap existing working code
class VoxtralProvider:
    def __init__(self):
        self.transcriber = VoxtralTranscriber()  # Reuse existing
    
    async def transcribe(self, audio_path):
        result = await self.transcriber.transcribe_audio(audio_path)
        return TranscriptResult(...)  # Convert format
```

**Benefits:**
- Single source of truth
- Bug fixes propagate
- Low risk
- Less code to maintain

### Testing Providers

**Mock the underlying client, not the provider:**

```python
@patch("clipscribe.transcribers.voxtral_transcriber.VoxtralTranscriber.transcribe_audio")
async def test_voxtral(mock_transcribe):
    mock_transcribe.return_value = VoxtralTranscriptionResult(...)
    
    provider = VoxtralProvider()
    result = await provider.transcribe("test.mp3")
    
    assert result.provider == "voxtral"
```

### Cost Tracking

**Always track actual costs:**

```python
async def transcribe(self, audio_path):
    result = await self.client.transcribe(audio_path)
    
    actual_cost = result.cost  # From API response
    
    return TranscriptResult(
        ...,
        cost=actual_cost,  # Not estimated!
    )
```

---

## Project Structure

```
src/clipscribe/
├── providers/              # Provider abstraction layer
│   ├── base.py            # Abstract interfaces
│   ├── factory.py         # Provider selection
│   ├── transcription/     # Transcription providers
│   │   ├── voxtral.py
│   │   ├── whisperx_local.py
│   │   └── whisperx_modal.py
│   └── intelligence/      # Intelligence providers
│       └── grok.py
├── extractors/            # Intelligence extractors
│   ├── metadata_extractor.py  # GEOINT telemetry extraction
│   └── ...
├── processors/            # Processing pipelines
│   ├── geoint_processor.py    # GEOINT orchestration
│   ├── geo_correlator.py       # Telemetry-transcript correlation
│   └── ...
├── exporters/             # Output formatters
│   ├── geoint_exporter.py      # KML/HTML map generation
│   └── ...
├── utils/klv/             # GEOINT parsing (zero-dependency)
│   ├── parser.py          # KLV stream parser
│   ├── decoder.py         # Value decoders
│   ├── registry.py        # Tag registry
│   └── geometry.py        # Spatial calculations
├── utils/                  # Utilities
│   ├── dji_parser.py      # DJI/Autel subtitle parser
│   └── ...
├── transcribers/          # Existing transcriber implementations
│   ├── voxtral_transcriber.py
│   └── whisperx_transcriber.py
├── retrievers/            # Core components
│   ├── grok_client.py
│   └── output_formatter.py
├── commands/              # CLI
│   └── cli.py
└── api/                   # API server
    ├── app.py
    └── job_worker.py

tests/
├── unit/
│   └── providers/         # Provider unit tests
└── integration/           # Integration tests
```

---

## GEOINT Engine Architecture

### Overview

The GEOINT engine is an optional component that extracts geospatial telemetry from video files. It uses a unified schema approach where different telemetry formats (KLV, DJI subtitles) are normalized to the same internal representation.

### Adding New Telemetry Formats

To add support for a new telemetry format (e.g., Parrot drones, custom formats):

1. **Create Parser** (if needed)
   ```python
   # src/clipscribe/utils/custom_parser.py
   class CustomTelemetryParser:
       def parse(self, video_path: str) -> List[Dict]:
           # Extract telemetry from your format
           # Return list of dicts with unified schema keys
           return [
               {
                   "SensorLatitude": lat,
                   "SensorLongitude": lon,
                   "SensorTrueAltitude": alt,
                   "video_time": seconds,  # or PrecisionTimeStamp for absolute
               }
           ]
   ```

2. **Update MetadataExtractor**
   ```python
   # src/clipscribe/extractors/metadata_extractor.py
   def extract_metadata(self, video_path: str):
       # Try KLV first
       klv_data = self._extract_klv(video_path)
       if klv_data:
           return klv_data
       
       # Try DJI subtitles
       subtitle_data = self._extract_subtitle_telemetry(video_path)
       if subtitle_data:
           return subtitle_data
       
       # Add your format here
       custom_data = self._extract_custom_telemetry(video_path)
       if custom_data:
           return custom_data
       
       return []
   ```

3. **Unified Schema**

All parsers must output the same schema keys:
- `SensorLatitude` (float, degrees)
- `SensorLongitude` (float, degrees)
- `SensorTrueAltitude` (float, meters MSL)
- `PrecisionTimeStamp` (int, microseconds, for absolute time) OR
- `video_time` (float, seconds, for relative time)

Downstream processors (correlator, exporter) work with this unified format.

### Testing New Formats

```python
# tests/unit/test_custom_parser.py
def test_custom_parser():
    parser = CustomTelemetryParser()
    data = parser.parse("test_video.mp4")
    assert "SensorLatitude" in data[0]
    assert "SensorLongitude" in data[0]
```

---

## Common Tasks

### Run Provider Locally

```bash
# Test Voxtral
poetry run clipscribe process test.mp3 -t voxtral --no-diarize

# Test WhisperX Local (FREE!)
poetry run clipscribe process test.mp3 -t whisperx-local

# Test WhisperX Modal
poetry run clipscribe process test.mp3 -t whisperx-modal
```

### Deploy Modal

```bash
# Deploy
poetry run modal deploy deploy/station10_modal.py

# Test deployment
poetry run modal run deploy/station10_modal.py::test_gcs_transcription

# Check logs
poetry run modal app logs clipscribe-transcription
```

### Format Code

```bash
# Format with Black
poetry run black src/

# Check with Ruff
poetry run ruff check src/

# Sort imports
poetry run isort src/
```

### Run Validation

```bash
# Full validation suite
poetry run python scripts/validation/test_provider_system.py
```

---

## Debugging

### Enable Debug Logging

```bash
poetry run clipscribe --debug process file.mp3
```

### Check Provider Configuration

```bash
poetry run clipscribe utils check-auth
```

### Modal Debugging

```bash
# View Modal logs
poetry run modal app logs clipscribe-transcription

# Check app status
poetry run modal app list
```

---

## Release Process

**For v3.x releases:**

1. **Test all providers:**
   ```bash
   poetry run pytest
   poetry run clipscribe process test.mp3 -t voxtral --no-diarize
   poetry run clipscribe process test.mp3 -t whisperx-local
   poetry run clipscribe process test.mp3 -t whisperx-modal
   ```

2. **Update version:**
   - `pyproject.toml`: version = "3.x.x"
   - `src/clipscribe/version.py`: __version__ = "3.x.x"
   - `CHANGELOG.md`: Add entry

3. **Commit and tag:**
   ```bash
   git commit -m "chore: Release v3.x.x"
   git tag -a v3.x.x -m "v3.x.x: Description"
   git push origin main --tags
   ```

4. **Deploy Modal** (if changed):
   ```bash
   poetry run modal deploy deploy/station10_modal.py
   ```

---

## Deployment

### Cloud Run Deployment

ClipScribe API is deployed to Google Cloud Run using GitHub Actions with Workload Identity Federation (WIF).

#### Workload Identity Federation Setup

**Project Information:**
- **Project ID:** `clipscribe-prod`
- **Project Number:** `16459511304`
- **Region:** `us-central1`

**Service Account:**
- **Email:** `clipscribe-api@clipscribe-prod.iam.gserviceaccount.com`
- **Display Name:** ClipScribe CI/CD

**Workload Identity Pool:**
- **Pool Name:** `github-pool`
- **Provider Name:** `github`
- **Repository Binding:** `bubroz/clipscribe`

**Required IAM Permissions:**
- `roles/run.admin` - Deploy and manage Cloud Run services
- `roles/artifactregistry.writer` - Push Docker images to Artifact Registry
- `roles/aiplatform.user` - Access Vertex AI (for E2E tests)
- `roles/storage.objectAdmin` - Manage GCS objects
- `roles/iam.serviceAccountUser` on Cloud Run service account
- `roles/iam.workloadIdentityUser` - Allow GitHub Actions to impersonate service account
- `roles/iam.serviceAccountTokenCreator` - Create tokens for service account

**GitHub Secrets Required:**
- `WIF_PROVIDER`: `projects/16459511304/locations/global/workloadIdentityPools/github-pool/providers/github`
- `WIF_SERVICE_ACCOUNT_EMAIL`: `clipscribe-api@clipscribe-prod.iam.gserviceaccount.com`
- `VERTEX_AI_PROJECT`: `clipscribe-prod`

**Deployment Workflow:**
1. Push tag (e.g., `v3.1.10`) or use `workflow_dispatch`
2. GitHub Actions authenticates via WIF
3. Builds Docker image and pushes to Artifact Registry
4. Deploys to Cloud Run service `clipscribe-api`

**Verification:**
```bash
# Check service status
gcloud run services describe clipscribe-api --region=us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=clipscribe-api" --limit=50
```

#### Presigned URL Generation

The API uses IAM SignBlob API to generate GCS v4 signed URLs without requiring service account private keys. This is necessary because Cloud Run's default service account uses token-based credentials.

**Implementation:** `src/clipscribe/utils/gcs_signing.py`

**Required Permission:** The Cloud Run service account must have `roles/iam.serviceAccountTokenCreator` on itself to use SignBlob API.

**For complete deployment status, see [DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md)**

---

**For complete architecture, see [ARCHITECTURE.md](ARCHITECTURE.md)**  
**For provider details, see [PROVIDERS.md](PROVIDERS.md)**
