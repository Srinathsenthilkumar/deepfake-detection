# Multi-platform Linux container for Deepfake Detector
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8500

# Install essential system dependencies (ffmpeg and graphics libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure temp directory exists
RUN mkdir -p /app/deepfake_detector/temp_downloads && \
    chmod -R 777 /app/deepfake_detector/temp_downloads

EXPOSE 8500

# Run with Gunicorn WSGI server
CMD exec gunicorn --bind 0.0.0.0:${PORT:-8500} --workers 1 --threads 4 --timeout 120 app:app
