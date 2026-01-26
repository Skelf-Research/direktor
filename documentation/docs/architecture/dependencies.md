# External Dependencies

Direktor relies on several external services and tools.

## System Dependencies

### FFmpeg

**Required for:** Audio/video processing

**Used in:**
- Audio concatenation (`audio.py`)
- Audio format conversion (`transcript.py`)
- Video creation (`video.py`)

**Installation:**

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from ffmpeg.org
```

**Version:** FFmpeg 4.0 or higher recommended

## Python Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `openai` | ^1.42.0 | GPT API client |
| `replicate` | ^0.31.0 | Replicate API client |
| `boto3` | ^1.35.4 | AWS/S3 operations |
| `tiktoken` | ^0.7.0 | Token counting |
| `python-dotenv` | ^1.0.1 | Environment management |
| `pillow` | ^10.4.0 | Image processing |
| `tqdm` | ^4.66.5 | Progress bars |
| `halo` | ^0.0.31 | Loading spinners |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ^7.0.0 | Testing |
| `black` | ^23.0.0 | Code formatting |
| `flake8` | ^6.0.0 | Linting |

### Documentation Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `mkdocs` | ^1.5.0 | Documentation generator |
| `mkdocs-material` | ^9.4.0 | Material theme |
| `mkdocstrings` | ^0.24.0 | API documentation |

## External Services

### OpenAI API

**Purpose:** Text generation and optimization

**Endpoints Used:**
- `chat.completions.create` - Script and prompt generation

**Models:**
- `gpt-4-turbo-preview` (recommended)
- `gpt-3.5-turbo` (budget option)

**Rate Limits:** Varies by plan

**Pricing:** ~$0.01-0.03 per 1K tokens

### Replicate API

**Purpose:** AI model hosting

**Models Used:**

| Model | Purpose | Approximate Cost |
|-------|---------|------------------|
| BARK | Text-to-speech | ~$0.0046/run |
| Distil-Whisper | Transcription | ~$0.0023/run |
| FLUX | Image generation | ~$0.02/image |

**Rate Limits:** Varies by plan

### Cloud Storage (S3/R2)

**Purpose:** Temporary file storage for transcription

**Compatible Services:**
- Cloudflare R2 (recommended, no egress fees)
- Amazon S3
- Any S3-compatible storage

**Required Permissions:**
- `s3:PutObject` - Upload audio files
- `s3:GetObject` - Generate presigned URLs

## Network Requirements

### Outbound Connections

| Service | Domain | Port |
|---------|--------|------|
| OpenAI | api.openai.com | 443 |
| Replicate | api.replicate.com | 443 |
| Cloudflare R2 | *.r2.cloudflarestorage.com | 443 |
| File downloads | Various (replicate outputs) | 443 |

### Bandwidth Estimates

| Stage | Upload | Download |
|-------|--------|----------|
| Script generation | ~10 KB | ~50 KB |
| Audio generation | ~1 KB | ~5 MB |
| Transcription | ~5 MB | ~10 KB |
| Image generation | ~1 KB | ~10 MB |

## Version Compatibility

### Python

- **Minimum:** Python 3.11
- **Recommended:** Python 3.11+

### Operating Systems

- **Linux:** Fully supported (Ubuntu 20.04+, Debian 11+)
- **macOS:** Fully supported (macOS 12+)
- **Windows:** Supported (Windows 10+, requires FFmpeg in PATH)

## Offline Capabilities

Direktor requires internet connectivity for:
- All AI model inference (OpenAI, Replicate)
- Cloud storage operations

Only the final video creation stage can run offline if all previous outputs exist.

## Service Alternatives

### Text-to-Speech Alternatives

If BARK doesn't meet your needs:
- Configure a different Replicate TTS model
- Modify `audio.py` for other services

### Image Generation Alternatives

If FLUX doesn't meet your needs:
- Configure a different Replicate image model
- Modify `images.py` for other services (DALL-E, Midjourney API)

### Storage Alternatives

Any S3-compatible storage works:
- Amazon S3
- Google Cloud Storage (with S3 compatibility)
- MinIO (self-hosted)
- DigitalOcean Spaces
