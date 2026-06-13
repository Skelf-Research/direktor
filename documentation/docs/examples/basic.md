# Basic Usage Examples

Common usage patterns for Direktor.

## CLI Examples

### Simple Video Generation

```bash
# Generate video from text file
direktor article.txt
```

### Stage-by-Stage Processing

```bash
# Generate only the script
direktor article.txt --stage 1

# Generate script and audio
direktor article.txt --stage 2

# Generate everything up to images
direktor article.txt --stage 5

# Complete the video
direktor article.txt --stage 6
```

## Python API Examples

### Basic Video Generation

```python
from direktor import generate_video

# Generate a complete video
generate_video("input.txt")
```

### With Custom Keywords

```python
from direktor import generate_video

keywords = [
    ("Introduction", 0, 10),
    ("Main Topic", 10, 60),
    ("Conclusion", 120, 130),
]

generate_video("input.txt", keywords=keywords)
```

### Stage Control

```python
from direktor import generate_video

# Generate only through transcript
generate_video("input.txt", stage=3)

# Later, complete the video
generate_video("input.txt", stage=6)
```

## Working with Modules Directly

### Generate Just Audio

```python
from direktor.core.audio import generate_audio
from direktor.core.utils import create_temp_dir

temp_dir = create_temp_dir("input.txt")

script = """
Welcome to today's episode! We're going to explore
some fascinating topics that will blow your mind.
"""

audio_path = generate_audio(script, temp_dir)
print(f"Audio saved to: {audio_path}")
```

### Generate Just Images

```python
from direktor.core.images import generate_images

prompts = [
    {"time": 0, "prompt": "A serene mountain landscape at sunset"},
    {"time": 30, "prompt": "A bustling city street with neon lights"},
    {"time": 60, "prompt": "An abstract cosmic nebula with vibrant colors"},
]

images = generate_images(prompts, "temp/custom")
print(f"Generated {len(images)} images")
```

### Generate Just Script

```python
from direktor.core.transcript import generate_podcast_script
from direktor.core.utils import create_temp_dir

temp_dir = create_temp_dir("input.txt")

with open("article.txt", "r") as f:
    article = f.read()

script = generate_podcast_script(article, temp_dir)
print(script[:500])  # Preview first 500 chars
```

## Batch Processing

### Process Multiple Files

```python
import os
from direktor import generate_video

input_dir = "articles/"
files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]

for filename in files:
    filepath = os.path.join(input_dir, filename)
    print(f"Processing: {filename}")

    try:
        generate_video(filepath)
        print(f"Completed: {filename}")
    except Exception as e:
        print(f"Failed: {filename} - {e}")
```

### Parallel Processing

```python
import concurrent.futures
from direktor import generate_video

files = ["article1.txt", "article2.txt", "article3.txt"]

def process_file(filepath):
    try:
        generate_video(filepath)
        return f"Success: {filepath}"
    except Exception as e:
        return f"Failed: {filepath} - {e}"

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    results = executor.map(process_file, files)

for result in results:
    print(result)
```

## Configuration Examples

### Using Different Models

```python
import os

# Use GPT-3.5 for lower cost
os.environ["GPT4_MODEL"] = "gpt-3.5-turbo"

from direktor import generate_video
generate_video("input.txt")
```

### Custom Token Limits

```python
import os

# Reduce token limit for faster processing
os.environ["GPT4_MAX_TOKENS"] = "4000"

from direktor import generate_video
generate_video("input.txt")
```

## Output Handling

### Find Output Files

```python
import os
import hashlib

def get_output_path(input_file):
    """Get the output directory for an input file."""
    with open(input_file, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return os.path.join("temp", file_hash)

input_file = "article.txt"
output_dir = get_output_path(input_file)

print(f"Output directory: {output_dir}")
print(f"Video: {os.path.join(output_dir, 'output.mp4')}")
```

### Copy Output to Custom Location

```python
import shutil
import os

def export_video(input_file, output_path):
    """Export the generated video to a custom location."""
    output_dir = get_output_path(input_file)
    video_path = os.path.join(output_dir, "output.mp4")

    if os.path.exists(video_path):
        shutil.copy2(video_path, output_path)
        print(f"Video exported to: {output_path}")
    else:
        print("Video not found. Run the complete pipeline first.")

export_video("article.txt", "my_video.mp4")
```
