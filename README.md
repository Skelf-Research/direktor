# Direktor — AI text-to-video pipeline

[![CI](https://github.com/Skelf-Research/direktor/actions/workflows/ci.yml/badge.svg)](https://github.com/Skelf-Research/direktor/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/direktor.svg)](https://pypi.org/project/direktor/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-skelfresearch.com-blue)](https://docs.skelfresearch.com/direktor)

**Text to video pipeline, powered by AI.**

Direktor is a Python library that transforms written content into podcast-style videos. It orchestrates AI models for script generation, voice synthesis, image creation, and video composition through a resumable 6-stage pipeline.

<p align="center">
  <a href="https://direktor.skelfresearch.com"><b>Website</b></a> •
  <a href="https://docs.skelfresearch.com/direktor">Documentation</a> •
  <a href="https://skelfresearch.com">Skelf Research</a>
</p>

## Installation

```bash
pip install direktor
```

Or with uv:

```bash
uv add direktor
```

## Requirements

- Python 3.11+
- FFmpeg
- API keys: OpenAI, Replicate
- S3-compatible storage (Cloudflare R2 recommended)

## Quick Start

```bash
# Configure API keys
cp sample.env .env
# Edit .env with your OPENAI_API_KEY and REPLICATE_API_TOKEN

# Generate video
direktor input.txt
```

## Usage

### CLI

```bash
# Full pipeline
direktor input.txt

# Run up to a specific stage
direktor input.txt --stage 3

# Custom output directory and keyword overlays
direktor input.txt --output ./videos --keywords-file keywords.json

# Skip narrative optimization, use a custom temp directory, and start fresh
direktor input.txt --no-optimize --temp-dir /tmp/direktor --clean
```

See `direktor --help` for all options.

### Python API

```python
from direktor import generate_video

# Generate complete video
result = generate_video("input.txt")
print(result.output_file)

# Run specific stages
result = generate_video("input.txt", stage=3)

# With keyword overlays and custom output directory
keywords = [
    ("Introduction", 0, 10),
    ("Main Topic", 10, 60),
]
result = generate_video(
    "input.txt",
    keywords=keywords,
    output_dir="./videos",
)
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

## Outputs

Direktor writes all intermediate artifacts to a temporary working directory (by default `temp/<md5_hash>/`). The final video is also copied to the location specified by `--output` / `output_dir`.

```
temp/
└── <md5_hash>/
    ├── podcast_script.txt     # Stage 1
    ├── audio.mp3              # Stage 2
    ├── transcript.json        # Stage 3
    ├── image_prompts.json     # Stage 4
    ├── images/                # Stage 5
    │   ├── image_0.webp
    │   └── ...
    └── output.mp4             # Stage 6 (final video)
```

Use `--output` (CLI) or `output_dir` (Python) to copy the final `output.mp4` to a directory of your choice.

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

## Development

```bash
git clone https://github.com/Skelf-Research/direktor.git
cd direktor
uv sync --all-extras --dev
uv run pytest
```

### Running with Docker

A Dockerfile and `docker-compose.yml` are provided for consistent local testing:

```bash
# Run the full test suite in Docker
docker compose up direktor-test --build --abort-on-container-exit

# Run lint and type checks in Docker
docker compose up direktor-lint --build --abort-on-container-exit
```

## Documentation

Full documentation: [docs.skelfresearch.com/direktor](https://docs.skelfresearch.com/direktor)

## License

MIT

---

## Part of Skelf Research

`direktor` is built by **[Skelf Research](https://skelfresearch.com)** — an independent UK AI research lab publishing production-grade open-source projects.

🌐 [Website](https://direktor.skelfresearch.com) · 📚 [Documentation](https://docs.skelfresearch.com/direktor) · 🔬 [All projects](https://skelfresearch.com/projects) · 🤗 [Hugging Face](https://huggingface.co/skelfresearch)

**Related projects:** [anouk](https://anouk.skelfresearch.com) (AI browser extensions), [promptel](https://promptel.skelfresearch.com) (declarative prompt DSL), [blogus](https://blogus.skelfresearch.com) (package.lock for prompts)

<sub>Released under MIT / Apache-2.0. © Skelf Research Limited.</sub>
