#!/usr/bin/env python3
"""
Run Station10 Intelligence Dashboard TUI.

Usage:
    poetry run python scripts/run_tui.py [video_id]

Example:
    poetry run python scripts/run_tui.py P-2
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.clipscribe.tui.intelligence_dashboard import IntelligenceDashboard

if __name__ == "__main__":
    app = IntelligenceDashboard()
    app.run()

