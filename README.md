# Direktor

[![CI](https://github.com/Skelf-Research/direktor/actions/workflows/ci.yml/badge.svg)](https://github.com/Skelf-Research/direktor/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/direktor.svg)](https://pypi.org/project/direktor/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-skelfresearch.com-blue)](https://docs.skelfresearch.com/direktor)

**Text to video pipeline, powered by AI.**

Direktor is a Python library that transforms written content into podcast-style videos. It orchestrates AI models for script generation, voice synthesis, image creation, and video composition through a resumable 6-stage pipeline.

## Installation

```bash
pip install direktor
```

Or with uv:

```bash
uv add direktor
```

## Quick Start

```bash
# Configure API keys
cp sample.env .env
# Edit .env with your OPENAI_API_KEY and REPLICATE_API_TOKEN

# Generate video
direktor input.txt
```

## Requirements

- Python 3.11+
- FFmpeg
- API keys: OpenAI, Replicate
- S3-compatible storage (Cloudflare R2 recommended)

## Usage

### CLI

```bash
# Full pipeline
direktor input.txt

# Run up to specific stage
direktor input.txt --stage 3

# Custom output directory and keyword overlays
direktor input.txt --output ./videos --keywords-file keywords.json
```

### Python API

```python
from direktor import generate_video

# Generate complete video
generate_video("input.txt")

# Run specific stages
generate_video("input.txt", stage=3)

# With keyword overlays
keywords = [
    ("Introduction", 0, 10),
    ("Main Topic", 10, 60),
]
generate_video("input.txt", keywords=keywords)
```

### Module-level Access

```python
from direktor.core.audio import generate_audio
from direktor.core.images import generate_images
from direktor.core.video import create_video
```

## Pipeline Stages

| Stage | Description | Output |
|-------|-------------|--------|
| 1 | Script generation | `podcast_script.txt` |
| 2 | Audio synthesis | `audio.mp3` |
| 3 | Transcript generation | `transcript.json` |
| 4 | Image prompt generation | `image_prompts.json` |
| 5 | Image generation | `images/` |
| 6 | Video composition | `output.mp4` |

Each stage is checkpointed. Resume from any failure point or edit intermediate outputs.

## Configuration

```env
# Required
REPLICATE_API_TOKEN=your_replicate_token
OPENAI_API_KEY=your_openai_key

# Models
BARK_MODEL=suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787
FLUX_MODEL=black-forest-labs/flux-schnell
GPT4_MODEL=gpt-4-turbo-preview

# Storage (S3-compatible)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com
AWS_BUCKET_NAME=your_bucket_name
```

## Documentation

Full documentation: [docs.skelfresearch.com/direktor](https://docs.skelfresearch.com/direktor)

## Development

```bash
git clone https://github.com/Skelf-Research/direktor.git
cd direktor
uv sync --all-extras
uv run pytest
```

## License

MIT
