# Multi-stage production container build for AI Career Intelligence Platform
FROM python:3.11-slim AS base

# Install system dependencies (ffmpeg, build tools, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create persistent data directories
RUN mkdir -p data/audio data/transcripts data/summaries

# Expose FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Default command: launch unified supervisor or single service
CMD ["python", "run_app.py", "--mode=both"]
