#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
.venv/bin/python -m pytest -q
EMBEDDING_BACKEND=hash .venv/bin/python -m scripts.evaluate
(cd frontend && npm run build)
