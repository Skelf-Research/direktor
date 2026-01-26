# Installation

## Prerequisites

Before installing Direktor, ensure you have the following:

### System Requirements

- **Python 3.11 or higher**
- **FFmpeg** - Required for audio/video processing

#### Installing FFmpeg

=== "Ubuntu/Debian"
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```

=== "macOS"
    ```bash
    brew install ffmpeg
    ```

=== "Windows"
    Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### API Keys Required

You'll need API keys from the following services:

| Service | Purpose | Get Key |
|---------|---------|---------|
| OpenAI | Text generation (GPT models) | [platform.openai.com](https://platform.openai.com/api-keys) |
| Replicate | Audio, transcription, images | [replicate.com](https://replicate.com/account/api-tokens) |
| Cloudflare R2 or S3 | Audio file storage | [cloudflare.com](https://dash.cloudflare.com/) |

## Installation Methods

### Using uv (Recommended)

```bash
uv add direktor
```

### Using pip

```bash
pip install direktor
```

### From Source (Development)

```bash
git clone https://github.com/Skelf-Research/direktor.git
cd direktor
uv sync --all-extras
```

## Configuration

Create a `.env` file in your project directory:

```env
# Required API Keys
REPLICATE_API_TOKEN=your_replicate_token
OPENAI_API_KEY=your_openai_key

# Model Configuration
DISTIL_MODEL=vaibhavs10/incredibly-fast-whisper:3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c
BARK_MODEL=suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787
FLUX_MODEL=black-forest-labs/flux-schnell
GPT4_MODEL=gpt-4-turbo-preview
GPT4_MAX_TOKENS=8000

# Cloud Storage (Cloudflare R2 or S3-compatible)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com
AWS_BUCKET_NAME=your_bucket_name
```

## Verify Installation

```bash
# Check CLI installation
direktor --help

# Check Python import
python -c "import direktor; print(direktor.__version__)"
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Create your first video
- [Configuration Reference](configuration.md) - Detailed configuration options
