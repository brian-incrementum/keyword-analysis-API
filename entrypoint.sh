#!/bin/sh
set -e

echo "Starting Keyword Analysis API..."
echo "Port: 8000"

# Start uvicorn
exec uvicorn app:app --host 0.0.0.0 --port 8000