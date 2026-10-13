#!/usr/bin/env bash
# Create a virtual environment (first run), install dependencies, start the app.
set -e
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
