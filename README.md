# Direktor

Direktor is a Python library that transforms text content into engaging podcast-style videos with synchronized visuals. It leverages state-of-the-art AI models to create compelling video content from simple text inputs.

## Features

- Convert text articles into podcast-style audio
- Generate relevant images for each segment of the content
- Automatically synchronize audio and visuals
- Add keyword overlays to videos
- Resume processing from any stage of the pipeline
- CLI tool for easy usage

## Installation

```bash
pip install direktor
```

## Setup

1. Create a `.env` file in your project directory with the following variables:

```env
REPLICATE_API_TOKEN=your_replicate_api_token_here
OPENAI_API_KEY=your_openai_api_key_here
DISTIL_MODEL=3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c
BARK_MODEL=adirik/styletts2:989cb5ea6d2401314eb30685740cb9f6fd1c9001b8940659b406f952837ab5ac
FLUX_MODEL=black-forest-labs/flux-schnell:fe82ca7f3f7efe4ad452c49a31e20d18b31d498bddbc1d61860703e0339406ba
GPT4_MODEL=gpt-4-vision-preview
GPT4_MAX_TOKENS=8000
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_ENDPOINT_URL=your_AWS_endpoint_url
AWS_BUCKET_NAME=your_bucket_name
```

2. Install FFmpeg on your system:
   - Ubuntu/Debian: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Windows: Download from https://ffmpeg.org/download.html

## Usage

### As a CLI Tool

```bash
direktor input.txt [--stage N]
```

Where:
- `input.txt` is your text file to convert
- `--stage N` (optional) specifies the stage to start from (1-6)

### As a Python Library

```python
from direktor import generate_video

# Generate a video from text
generate_video("input.txt", stage=6)
```

## How It Works

Direktor processes your text through 6 stages:

1. **Content Optimization**: Improves clarity and engagement of your text
2. **Podcast Script Generation**: Creates a natural-sounding podcast script
3. **Audio Generation**: Converts the script to audio using AI voice synthesis
4. **Transcript Generation**: Creates a timestamped transcript of the audio
5. **Image Prompt Generation**: Creates image prompts for each segment
6. **Video Creation**: Combines audio and images into a synchronized video

## Requirements

- Python 3.11+
- FFmpeg
- API keys for OpenAI and Replicate
- Cloud storage (AWS S3/Cloudflare R2 compatible)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.