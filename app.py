"""Vercel entrypoint. Deploy from the repository root so data stays available."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'backend'))
from fitness.api import app  # noqa: E402,F401
