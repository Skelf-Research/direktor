# Python API

Use Direktor as a Python library for programmatic video generation.

## Quick Start

```python
from direktor import generate_video

# Generate a complete video
generate_video("input.txt")
```

## Main Functions

### generate_video

The primary function for video generation.

```python
from direktor import generate_video

generate_video(
    input_file="article.txt",
    stage=6,           # Run all stages
    keywords=None      # Optional keyword overlays
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_file` | `str` | required | Path to input text file |
| `stage` | `int` | `6` | Stage to run up to (1-6) |
| `keywords` | `list` | `None` | List of (keyword, start, end) tuples |

### optimize_content

Optimize text for better podcast narration.

```python
from direktor import optimize_content

optimized_text = optimize_content(raw_text)
```

## Working with Individual Modules

### Audio Generation

```python
from direktor.core.audio import generate_audio

audio_file = generate_audio(
    text="Your podcast script here...",
    temp_dir="temp/abc123"
)
```

### Transcript Generation

```python
from direktor.core.transcript import (
    generate_podcast_script,
    generate_transcript
)

# Generate podcast script
script = generate_podcast_script(
    input_text="Your article text...",
    temp_dir="temp/abc123"
)

# Generate transcript from audio
transcript = generate_transcript(
    audio_file="temp/abc123/audio.mp3",
    temp_dir="temp/abc123"
)
```

### Image Generation

```python
from direktor.core.images import (
    generate_image_prompts,
    generate_images
)

# Generate prompts
prompts = generate_image_prompts(
    transcript=transcript_data,
    temp_dir="temp/abc123"
)

# Generate images
image_files = generate_images(
    prompts=prompts,
    temp_dir="temp/abc123"
)
```

### Video Creation

```python
from direktor.core.video import create_video

output = create_video(
    audio_file="temp/abc123/audio.mp3",
    image_files=["temp/abc123/images/image_0.webp", ...],
    image_prompts=prompts,
    temp_dir="temp/abc123",
    keywords=[("AI", 0, 5), ("Future", 5, 10)]
)
```

## Utility Functions

```python
from direktor.core.utils import (
    create_temp_dir,
    split_text,
    download_file,
    upload_to_r2
)

# Create temp directory from input file
temp_dir = create_temp_dir("input.txt")

# Split text by tokens
chunks = split_text(long_text, max_tokens=4000)
```

## Configuration Access

```python
from direktor.core.config import (
    client,           # OpenAI client
    encoding,         # Tiktoken encoding
    validate_env_vars # Validation function
)

# Validate configuration
try:
    validate_env_vars()
except EnvironmentError as e:
    print(f"Configuration error: {e}")
```

## Custom Keyword Overlays

Add text overlays to your video:

```python
from direktor import generate_video

keywords = [
    ("Introduction", 0, 10),      # Show "Introduction" from 0-10 seconds
    ("Key Points", 10, 30),       # Show "Key Points" from 10-30 seconds
    ("Conclusion", 60, 70),       # Show "Conclusion" from 60-70 seconds
]

generate_video("input.txt", keywords=keywords)
```

## Error Handling

```python
from direktor import generate_video
from direktor.core.config import validate_env_vars

try:
    validate_env_vars()
    generate_video("input.txt")
except EnvironmentError as e:
    print(f"Missing configuration: {e}")
except FileNotFoundError:
    print("Input file not found")
except Exception as e:
    print(f"Pipeline error: {e}")
```
