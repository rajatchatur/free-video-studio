#!/usr/bin/env bash
cd "$(dirname "$0")/.."
source .venv/bin/activate
export WHISPER_MODEL="${WHISPER_MODEL:-base}"
echo "Open http://127.0.0.1:8000 in your browser"
python server.py
