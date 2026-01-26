# Configuration

Direktor is configured primarily through environment variables. This guide covers all available options.

## Environment Variables

### Required Variables

| Variable | Description |
|----------|-------------|
| `REPLICATE_API_TOKEN` | API token for Replicate services |
| `OPENAI_API_KEY` | API key for OpenAI GPT models |
| `DISTIL_MODEL` | Replicate model ID for transcription |
| `BARK_MODEL` | Replicate model ID for text-to-speech |
| `FLUX_MODEL` | Replicate model ID for image generation |
| `GPT4_MODEL` | OpenAI model name for text generation |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GPT4_MAX_TOKENS` | `8000` | Maximum tokens per GPT request |
| `AWS_ENDPOINT_URL` | `https://s3.us-west-000.backblazeb2.com` | S3-compatible endpoint |

### Cloud Storage

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | S3/R2 access key |
| `AWS_SECRET_ACCESS_KEY` | S3/R2 secret key |
| `AWS_BUCKET_NAME` | Bucket name for audio uploads |

## Configuration File

Create a `.env` file in your project root:

```env
# API Keys
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Models
DISTIL_MODEL=vaibhavs10/incredibly-fast-whisper:3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c
BARK_MODEL=suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787
FLUX_MODEL=black-forest-labs/flux-schnell
GPT4_MODEL=gpt-4-turbo-preview
GPT4_MAX_TOKENS=8000

# Cloud Storage
AWS_ACCESS_KEY_ID=xxxxxxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_ENDPOINT_URL=https://xxxxxxxxxx.r2.cloudflarestorage.com
AWS_BUCKET_NAME=direktor-audio
```

## Model Selection

### Text-to-Speech Models

The default BARK model provides high-quality voice synthesis. You can use alternative models on Replicate:

```env
# Default (recommended)
BARK_MODEL=suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787
```

### Transcription Models

Distil-Whisper provides fast, accurate transcription:

```env
DISTIL_MODEL=vaibhavs10/incredibly-fast-whisper:3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c
```

### Image Generation Models

FLUX provides high-quality image generation:

```env
# Fast generation
FLUX_MODEL=black-forest-labs/flux-schnell

# Higher quality (slower)
FLUX_MODEL=black-forest-labs/flux-dev
```

### GPT Models

```env
# Recommended for quality
GPT4_MODEL=gpt-4-turbo-preview

# Budget option
GPT4_MODEL=gpt-3.5-turbo
```

## Programmatic Configuration

You can also configure Direktor programmatically:

```python
import os
from direktor import generate_video

# Set environment variables
os.environ["GPT4_MODEL"] = "gpt-4-turbo-preview"
os.environ["GPT4_MAX_TOKENS"] = "4000"

# Run with custom settings
generate_video("input.txt")
```

## Validating Configuration

Check if all required variables are set:

```python
from direktor.core.config import validate_env_vars

try:
    validate_env_vars()
    print("Configuration is valid!")
except EnvironmentError as e:
    print(f"Missing configuration: {e}")
```
