#!/bin/sh
set -e

echo "Running initial CSV load..."
python load_history.py || echo "ERROR - load_history.py failed (maybe data already loaded)"

echo "Starting FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
