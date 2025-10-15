#!/bin/bash
# Safe deployment archive creator for Station10

echo "Creating deployment archive..."
echo ""

# Show what we're INCLUDING
echo "✓ Including:"
echo "  - src/ (Python source code)"
echo "  - tests/ (test suite)"
echo "  - pyproject.toml & poetry.lock (dependencies)"
echo "  - README.md, LICENSE, CHANGELOG.md (docs)"
echo "  - pytest.ini (test config)"
echo "  - env.example (example env file)"
echo ""

# Show what we're EXCLUDING
echo "✗ Excluding (for security/size):"
echo "  - .env & secrets/ (API keys, credentials)"
echo "  - cache/ (2GB of cached videos)"
echo "  - .git/ (1GB git history)"
echo "  - output/ & logs/ (38MB generated files)"
echo "  - All Python cache (__pycache__, .pytest_cache, etc.)"
echo "  - All media files (*.mp4, *.mp3, etc.)"
echo "  - Temporary research docs (STATION10_*.md)"
echo "  - Docker files (not needed for Poetry deploy)"
echo ""

# Create archive with comprehensive exclusions
tar czf clipscribe-deploy.tar.gz \
  --exclude='.env' \
  --exclude='.env.production' \
  --exclude='env.production' \
  --exclude='secrets' \
  --exclude='service-account.json' \
  --exclude='cache' \
  --exclude='.git' \
  --exclude='.github' \
  --exclude='output' \
  --exclude='logs' \
  --exclude='htmlcov' \
  --exclude='MagicMock' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='.pytest_cache' \
  --exclude='.mypy_cache' \
  --exclude='.ruff_cache' \
  --exclude='*.egg-info' \
  --exclude='.coverage' \
  --exclude='coverage.xml' \
  --exclude='.cursor' \
  --exclude='.vscode' \
  --exclude='.DS_Store' \
  --exclude='.video_cache' \
  --exclude='*.mp4' \
  --exclude='*.mp3' \
  --exclude='*.avi' \
  --exclude='*.mov' \
  --exclude='*.mkv' \
  --exclude='*.webm' \
  --exclude='test_*.py' \
  --exclude='test_*.log' \
  --exclude='STATION10_*.md' \
  --exclude='NEXT_SESSION_*.md' \
  --exclude='STATUS.md' \
  --exclude='demo' \
  --exclude='structured_output' \
  --exclude='streamlit_app' \
  --exclude='static_web' \
  --exclude='docker' \
  --exclude='docker-compose.yml' \
  --exclude='Dockerfile*' \
  --exclude='cloudbuild*.yaml' \
  --exclude='archive' \
  --exclude='obama_response.json' \
  --exclude='direct_upload_*.json' \
  --exclude='success_Method_*.json' \
  --exclude='lib' \
  .

# Check archive size
ARCHIVE_SIZE=$(du -h clipscribe-deploy.tar.gz | cut -f1)
echo ""
echo "✓ Archive created: clipscribe-deploy.tar.gz ($ARCHIVE_SIZE)"
echo ""

# List what's actually in the archive (top-level only)
echo "Archive contents (top-level):"
tar tzf clipscribe-deploy.tar.gz | head -30

echo ""
echo "Ready to transfer to VPS!"
