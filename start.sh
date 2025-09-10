#!/bin/bash

# Production startup script for the API

# Exit on error
set -e

# Set default values if not provided
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-4}

echo "Starting Keyword Analysis API..."
echo "Port: $PORT"
echo "Workers: $WORKERS"

# Run migrations or setup if needed (placeholder)
# python manage.py migrate

# Start the application with gunicorn
exec gunicorn app:app \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --access-logfile - \
    --error-logfile - \
    --log-level info