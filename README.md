# Direktor

Transform text into professional podcast-style videos using AI. Distributed processing with zero dependencies.

## Quick Start

```bash
# Install
pip install direktor

# Run (starts everything needed)
direktor tracker &
direktor workers &
direktor submit article.txt --watch
```

Done! Your video will be generated automatically.

## What It Does

Direktor converts text articles into engaging videos with:
- AI-generated narration (BARK)
- Context-aware visuals (FLUX)
- Synchronized audio and video
- Professional overlays and effects

## How It Works

```
Text → Script → Audio → Images → Video
 📝      🎵      🖼️       🎬
```

Each stage can run on different machines for scaling.

## Environment Setup

Create `.env` file:

```env
# Required
OPENAI_API_KEY=your_key_here
REPLICATE_API_TOKEN=your_token_here

# Cloud Storage (AWS S3/Cloudflare R2)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_ENDPOINT_URL=your_endpoint
AWS_BUCKET_NAME=your_bucket
```

## Common Commands

```bash
direktor submit file.txt          # Submit job
direktor status job_12345         # Check progress
direktor stats                    # View queues
direktor worker script            # Run specific worker
```

## Scaling

**Single Machine:**
```bash
direktor tracker &    # Job coordination
direktor workers &    # All processing stages
```

**Multiple Machines:**
```bash
# Machine 1 (coordinator)
direktor tracker

# Machine 2 (CPU work)
direktor worker script
direktor worker audio

# Machine 3 (GPU work)
direktor worker images
direktor worker video
```

## Requirements

- Python 3.11+
- FFmpeg
- OpenAI API key
- Replicate API key
- Cloud storage (S3/R2)

## Documentation

- [Architecture](docs/architecture.md) - System design and components
- [Deployment](docs/deployment.md) - Production setup guides
- [Development](docs/development.md) - Contributing and extending
- [API Reference](docs/api.md) - Python API documentation

## License

MIT