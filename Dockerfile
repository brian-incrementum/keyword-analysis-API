FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Healthcheck using Python stdlib (no curl needed)
HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD python -c "import urllib.request,sys; \
    sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/health').getcode()==200 else sys.exit(1)"

# Use exec form for CMD to avoid shell issues
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
