#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; fi
(cd frontend && npm ci)
echo 'Ready. Run ./run_backend.sh and ./run_frontend.sh in separate terminals.'
