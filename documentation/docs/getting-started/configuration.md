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
| `AWS_ENDPOINT_URL` | `https://s3.us-west-000.backblazeb2.com` | S3-compatible endpoint (default: Backblaze B2 us-west-000) |

The `AWS_ENDPOINT_URL` default points to Backblaze B2. Override it to use Cloudflare R2 (`https://<account>.r2.cloudflarestorage.com`), Amazon S3 (omit, or `https://s3.<region>.amazonaws.com`), or any other S3-compatible service.

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
DISTIL_MODEL=3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c
BARK_MODEL=adirik/styletts2:989cb5ea6d2401314eb30685740cb9f6fd1c9001b8940659b406f952837ab5ac
FLUX_MODEL=black-forest-labs/flux-schnell:fe82ca7f3f7efe4ad452c49a31e20d18b31d498bddbc1d61860703e0339406ba
GPT4_MODEL=gpt-4-vision-preview
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
# Default (StyleTTS2 via Replicate)
BARK_MODEL=adirik/styletts2:989cb5ea6d2401314eb30685740cb9f6fd1c9001b8940659b406f952837ab5ac
```

The `BARK_MODEL` variable name is preserved for backward compatibility but any Replicate TTS model with a compatible input schema (`text`, `alpha`, `beta`, `diffusion_steps`, `embedding_scale`, `seed`) can be used.

### Transcription Models

Distil-Whisper / Incredibly Fast Whisper provides fast transcription with chunk-level timestamps:

```env
DISTIL_MODEL=3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c
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
# Default (matches sample.env)
GPT4_MODEL=gpt-4-vision-preview

# Higher quality / newer
GPT4_MODEL=gpt-4-turbo-preview

# Budget option
GPT4_MODEL=gpt-3.5-turbo
```

The model name is passed directly to `openai.chat.completions.create` and is also used by `tiktoken.encoding_for_model` for token splitting. If a model name is not recognised by `tiktoken`, content splitting will fail.

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
