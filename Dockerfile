FROM python:3.10-slim

LABEL maintainer="PolarisLLM Team"
LABEL description="PolarisLLM Runtime Engine - Multi-model LLM serving platform"

# Set environment variables
ENV PYTHONPATH=/app/src
ENV POLARIS_CONFIG=/app/config/runtime.yaml
ENV HF_HUB_CACHE=/app/cache/huggingface
ENV CUDA_VISIBLE_DEVICES=0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install ms-swift
RUN pip install ms-swift[llm] --upgrade

# Copy application code
COPY src/ src/
COPY config/ config/
COPY main.py .
COPY cli.py .
COPY README.md .

# Create necessary directories
RUN mkdir -p logs cache/huggingface models

# Make CLI executable
RUN chmod +x cli.py

# Expose ports (main server + model ports range)
EXPOSE 7860 8000-8100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Default command
CMD ["python", "main.py"]