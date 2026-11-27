#!/usr/bin/env bash
set -euo pipefail
pip install -r backend/requirements.lock
python scripts/prepare_assets.py
PYTHONPATH=backend python -m fitness.setup
