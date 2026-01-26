# API Reference Overview

This section provides detailed documentation for all Direktor modules and functions.

## Package Structure

```
direktor/
├── __init__.py          # Main exports: generate_video, optimize_content
├── cli.py               # Command-line interface
└── core/
    ├── __init__.py      # Core module exports
    ├── config.py        # Configuration and constants
    ├── utils.py         # Utility functions
    ├── audio.py         # Audio generation
    ├── transcript.py    # Script and transcript generation
    ├── images.py        # Image prompt and generation
    ├── video.py         # Video creation
    ├── pipeline.py      # Main orchestration
    └── narrative.py     # Content optimization
```

## Main Package

### direktor

The main package exports two primary functions:

```python
from direktor import generate_video, optimize_content
```

## Core Modules

### [audio](audio.md)

Audio generation using BARK text-to-speech.

```python
from direktor.core.audio import generate_audio
```

### [video](video.md)

Video creation using FFmpeg.

```python
from direktor.core.video import create_video
```

### [transcript](transcript.md)

Script and transcript generation.

```python
from direktor.core.transcript import (
    generate_podcast_script,
    generate_transcript,
    aggregate_chunks
)
```

### [images](images.md)

Image prompt generation and image creation.

```python
from direktor.core.images import (
    generate_image_prompts,
    generate_images
)
```

### [utils](utils.md)

Utility functions for file operations and API calls.

```python
from direktor.core.utils import (
    create_temp_dir,
    run_replicate_model,
    split_text,
    download_file,
    upload_to_r2
)
```

### [pipeline](pipeline.md)

Main pipeline orchestration.

```python
from direktor.core.pipeline import main
```

### [narrative](narrative.md)

Content optimization.

```python
from direktor.core.narrative import optimize_content
```

## Type Hints

Direktor uses standard Python type hints. Key types include:

```python
# Transcript structure
Transcript = {
    "chunks": List[{
        "text": str,
        "timestamp": List[float, float]
    }]
}

# Image prompt structure
ImagePrompt = {
    "time": float,
    "prompt": str
}

# Keyword overlay
Keyword = Tuple[str, float, float]  # (text, start_time, end_time)
```
