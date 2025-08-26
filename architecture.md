# Direktor Architecture

Direktor is a Python-based system that transforms text content into engaging podcast-style videos with synchronized visuals. The system leverages AI models for content processing, audio generation, and image creation.

## System Overview

The Direktor system processes text input through multiple stages to create a final video output:

1. Text content optimization and enhancement
2. Podcast script generation
3. Audio generation from script
4. Speech-to-text transcription
5. Image prompt generation from transcript
6. Image generation from prompts
7. Video creation with synchronized audio and visuals

## Core Components

### 1. Content Processing Module (`narrative.py`)
- **Content Optimization**: Improves clarity, engagement, and readability of input text
- **NLP Narrative Enhancement**: Applies neuro-linguistic programming techniques to make content more engaging
- **Grapheme Optimization**: Makes character-level improvements for better readability

### 2. Main Processing Pipeline (`main.py`)
The main pipeline orchestrates the entire video generation process through 6 distinct stages:

#### Stage 1: Podcast Script Generation
- Processes input text using OpenAI's GPT models
- Creates engaging single-person podcast scripts
- Splits large texts into manageable chunks based on token limits

#### Stage 2: Audio Generation
- Uses Replicate's BARK model for text-to-speech conversion
- Splits script into sentence chunks for processing
- Handles audio concatenation for longer scripts
- Manages error handling for failed audio chunks

#### Stage 3: Transcript Generation
- Converts generated audio to WAV format using FFmpeg
- Uploads audio to Cloudflare R2 storage
- Uses Replicate's Distil-Whisper model for speech-to-text transcription
- Generates timestamped transcript chunks

#### Stage 4: Image Prompt Generation
- Analyzes transcript to create image prompts
- Aggregates transcript chunks to ~30-second segments
- Uses GPT models to generate descriptive prompts for each segment

#### Stage 5: Image Generation
- Generates images using Replicate's FLUX model
- Processes prompts to create relevant visuals
- Handles image downloading and storage

#### Stage 6: Video Creation
- Converts WebP images to PNG format
- Creates video from images with timing based on transcript timestamps
- Combines video with audio using FFmpeg
- Adds keyword overlays using custom font

### 3. Utility Functions
- Environment variable management with `.env` file support
- Temporary directory creation based on input file hashing
- File uploading to Cloudflare R2 storage
- Progress tracking with visual indicators

## External Dependencies

### APIs and Models
- **OpenAI API**: GPT models for text processing and prompt generation
- **Replicate API**: 
  - BARK model for text-to-speech
  - Distil-Whisper for speech-to-text transcription
  - FLUX model for image generation

### Libraries
- `openai`: OpenAI API client
- `replicate`: Replicate API client
- `boto3`: AWS SDK for Cloudflare R2 integration
- `tiktoken`: Token counting for OpenAI models
- `tqdm`: Progress bars
- `halo`: Loading spinners
- `python-dotenv`: Environment variable management
- `pillow`: Image processing
- `ffmpeg`: Audio/video processing

### Services
- **Cloudflare R2**: Audio file storage for transcription
- **FFmpeg**: Audio/video processing and concatenation

## Data Flow

```
Input Text
    ↓
Content Enhancement (narrative.py)
    ↓
Podcast Script Generation
    ↓
Audio Generation (BARK)
    ↓
Transcript Generation (Whisper)
    ↓
Image Prompt Generation
    ↓
Image Generation (FLUX)
    ↓
Video Creation + Audio Sync
    ↓
Final Video Output
```

## Configuration

The system requires several environment variables defined in a `.env` file:

- `REPLICATE_API_TOKEN`: Replicate API authentication
- `OPENAI_API_KEY`: OpenAI API authentication
- Model identifiers for Distil-Whisper, BARK, and FLUX models
- GPT model selection
- AWS credentials for Cloudflare R2 integration
- Token limits for GPT models

## Storage Structure

The system uses a temporary directory structure based on MD5 hashes of input files:

```
temp/
└── <md5_hash_of_input_file>/
    ├── podcast_script.txt
    ├── audio.mp3
    ├── transcript.json
    ├── image_prompts.json
    ├── images/
    │   ├── image_0.webp
    │   ├── image_1.webp
    │   └── ...
    └── output.mp4
```

## Error Handling

- Audio generation failures are logged for troubleshooting
- Failed chunks are skipped during audio concatenation
- Missing environment variables are validated at startup
- File operations include proper error handling and cleanup

## Future Enhancements

- Multimodal interaction support
- Emotional intelligence in content generation
- Swarm intelligence for multi-robot coordination
- Augmented reality integration
- Predictive assistance capabilities