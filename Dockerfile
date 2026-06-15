# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm

# Install system dependencies including ffmpeg (required for video/audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy project metadata first for better layer caching
COPY pyproject.toml uv.lock ./
COPY direktor ./direktor
COPY tests ./tests
COPY README.md LICENSE sample.env ./

# Install dependencies and the project
RUN uv sync --all-extras --dev

# Default command: run the full test suite
CMD ["uv", "run", "pytest", "-q"]
