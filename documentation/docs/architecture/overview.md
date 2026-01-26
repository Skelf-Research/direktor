# System Overview

Direktor's architecture is designed for modularity, resumability, and extensibility.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                              CLI / API                               │
│                          (cli.py / __init__.py)                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Pipeline Orchestrator                        │
│                            (pipeline.py)                             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  narrative  │         │ transcript  │         │   images    │
│             │         │             │         │             │
│ - optimize  │         │ - script    │         │ - prompts   │
│ - enhance   │         │ - transcribe│         │ - generate  │
└─────────────┘         └─────────────┘         └─────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│    audio    │         │    video    │         │    utils    │
│             │         │             │         │             │
│ - generate  │         │ - create    │         │ - temp dir  │
│ - concat    │         │ - overlay   │         │ - download  │
└─────────────┘         └─────────────┘         └─────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            Configuration                             │
│                             (config.py)                              │
│                                                                      │
│  - Environment variables                                             │
│  - API clients (OpenAI, Replicate)                                   │
│  - Model configurations                                              │
│  - Asset paths                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### config.py
- Load environment variables
- Initialize API clients
- Define constants and paths
- Validate configuration

### utils.py
- File operations (create dirs, download files)
- Text processing (split, tokenize)
- Cloud storage operations
- Replicate API wrapper

### narrative.py
- Content optimization
- NLP-based text enhancement
- Engagement improvements

### transcript.py
- Podcast script generation
- Audio transcription
- Timestamp management
- Chunk aggregation

### audio.py
- Text-to-speech conversion
- Audio chunk management
- FFmpeg concatenation

### images.py
- Image prompt generation
- FLUX model integration
- Batch image generation

### video.py
- Image conversion
- FFmpeg video creation
- Audio-video synchronization
- Text overlay rendering

### pipeline.py
- Stage orchestration
- Checkpoint management
- Error handling
- Progress coordination

## Design Principles

### 1. Modularity
Each module handles a single concern and can be used independently:

```python
# Use just the audio module
from direktor.core.audio import generate_audio
audio = generate_audio("text", "temp_dir")
```

### 2. Checkpointing
Every stage saves its output, enabling:
- Resume after failures
- Manual editing of intermediate outputs
- Selective re-processing

### 3. Configuration Over Code
Behavior is controlled through environment variables:
- Model selection
- Token limits
- API endpoints

### 4. Graceful Degradation
Components handle failures gracefully:
- Content optimization failures fall back to original text
- Failed audio chunks are skipped
- Logging captures errors for debugging

## File Organization

```
direktor/
├── __init__.py          # Package entry point
├── cli.py               # CLI interface
├── assets/              # Static assets
│   └── mexcellent_3d.ttf
└── core/                # Core modules
    ├── __init__.py
    ├── config.py
    ├── utils.py
    ├── audio.py
    ├── transcript.py
    ├── images.py
    ├── video.py
    ├── pipeline.py
    └── narrative.py
```

## Extension Points

### Custom Models
Change AI models via environment variables:

```env
BARK_MODEL=your-custom-tts-model
FLUX_MODEL=your-custom-image-model
```

### Custom Processing
Override any stage by using modules directly:

```python
from direktor.core.transcript import generate_podcast_script
from direktor.core.audio import generate_audio

# Custom script generation
script = my_custom_script_generator(text)

# Use Direktor's audio generation
audio = generate_audio(script, temp_dir)
```
