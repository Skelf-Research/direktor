# Direktor

**Transform text content into engaging podcast-style videos with AI**

Direktor is a Python library that converts written content into visually engaging podcast-style videos. Using state-of-the-art AI models, it automatically generates narration, creates synchronized visuals, and produces professional-quality video content.

## Key Features

- **AI-Powered Script Generation** - Converts any text into engaging podcast scripts using GPT models
- **Text-to-Speech** - High-quality voice synthesis using the BARK model
- **Dynamic Image Generation** - Creates contextual visuals using FLUX image generation
- **Automatic Synchronization** - Aligns audio, images, and text overlays seamlessly
- **Resumable Pipeline** - 6-stage processing allows resuming from any point
- **Configurable** - Extensive customization options via environment variables

## Quick Start

```bash
# Install Direktor
uv add direktor

# Set up your API keys in .env file
# Run the pipeline
direktor input.txt
```

## Pipeline Overview

Direktor uses a 6-stage pipeline:

1. **Content Optimization** - Enhances text for better narration
2. **Script Generation** - Creates an engaging podcast script
3. **Audio Generation** - Converts script to speech
4. **Transcript Generation** - Creates timestamped transcript
5. **Image Generation** - Generates contextual visuals
6. **Video Creation** - Combines everything into final video

## Requirements

- Python 3.11+
- FFmpeg (system dependency)
- API keys for: OpenAI, Replicate
- Cloud storage (Cloudflare R2 or S3-compatible)

## Next Steps

- [Installation Guide](getting-started/installation.md) - Detailed setup instructions
- [Quick Start Tutorial](getting-started/quickstart.md) - Create your first video
- [API Reference](api/overview.md) - Detailed API documentation
