# Advanced Workflows

Advanced usage patterns and customizations for Direktor.

## Custom Pipeline

### Override Script Generation

```python
from direktor.core.audio import generate_audio
from direktor.core.transcript import generate_transcript
from direktor.core.images import generate_image_prompts, generate_images
from direktor.core.video import create_video
from direktor.core.utils import create_temp_dir

def custom_pipeline(input_file, custom_script):
    """Run pipeline with a custom script."""
    temp_dir = create_temp_dir(input_file)

    # Save custom script
    script_file = f"{temp_dir}/podcast_script.txt"
    with open(script_file, "w") as f:
        f.write(custom_script)

    # Continue with remaining stages
    audio_file = generate_audio(custom_script, temp_dir)
    transcript = generate_transcript(audio_file, temp_dir)
    prompts = generate_image_prompts(transcript, temp_dir)
    images = generate_images(prompts, temp_dir)

    video = create_video(audio_file, images, prompts, temp_dir)
    return video

# Use with custom script
my_script = """
Hey everyone! Today I'm going to share something amazing with you.
Let's dive right into the fascinating world of quantum computing.
"""

video = custom_pipeline("input.txt", my_script)
```

### Custom Image Style Pipeline

```python
import json
from direktor.core.images import generate_images
from direktor.core.utils import create_temp_dir

def add_style_to_prompts(prompts, style):
    """Add a consistent style to all prompts."""
    styled_prompts = []
    for prompt in prompts:
        styled_prompts.append({
            "time": prompt["time"],
            "prompt": f"{prompt['prompt']}, {style}"
        })
    return styled_prompts

# Load existing prompts
with open("temp/abc123/image_prompts.json", "r") as f:
    prompts = json.load(f)

# Add cyberpunk style
style = "cyberpunk aesthetic, neon lights, rain-soaked streets, high contrast"
styled_prompts = add_style_to_prompts(prompts, style)

# Save and regenerate
with open("temp/abc123/image_prompts.json", "w") as f:
    json.dump(styled_prompts, f)

images = generate_images(styled_prompts, "temp/abc123")
```

## Integration Examples

### Web Application Integration

```python
from flask import Flask, request, jsonify
from direktor import generate_video
import threading
import uuid

app = Flask(__name__)
jobs = {}

def process_video(job_id, text):
    """Background video processing."""
    try:
        # Write text to temp file
        input_file = f"/tmp/{job_id}.txt"
        with open(input_file, "w") as f:
            f.write(text)

        generate_video(input_file)
        jobs[job_id] = {"status": "completed"}
    except Exception as e:
        jobs[job_id] = {"status": "failed", "error": str(e)}

@app.route("/generate", methods=["POST"])
def start_generation():
    text = request.json.get("text")
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing"}

    thread = threading.Thread(target=process_video, args=(job_id, text))
    thread.start()

    return jsonify({"job_id": job_id})

@app.route("/status/<job_id>")
def check_status(job_id):
    return jsonify(jobs.get(job_id, {"status": "not_found"}))
```

### Webhook Notifications

```python
import requests
from direktor import generate_video

def generate_with_webhook(input_file, webhook_url):
    """Generate video and notify via webhook."""
    try:
        generate_video(input_file)

        requests.post(webhook_url, json={
            "status": "success",
            "input_file": input_file
        })
    except Exception as e:
        requests.post(webhook_url, json={
            "status": "failed",
            "input_file": input_file,
            "error": str(e)
        })

generate_with_webhook("article.txt", "https://example.com/webhook")
```

## Custom Content Processing

### Pre-processing Pipeline

```python
import re
from direktor import generate_video
from direktor.core.narrative import optimize_content

def preprocess_content(text):
    """Custom content preprocessing."""

    # Remove URLs
    text = re.sub(r'http\S+', '', text)

    # Remove citations like [1], [2]
    text = re.sub(r'\[\d+\]', '', text)

    # Expand abbreviations
    abbreviations = {
        "AI": "artificial intelligence",
        "ML": "machine learning",
        "NLP": "natural language processing"
    }
    for abbr, full in abbreviations.items():
        text = re.sub(rf'\b{abbr}\b', full, text)

    return text

# Read and preprocess
with open("technical_article.txt", "r") as f:
    raw_text = f.read()

processed_text = preprocess_content(raw_text)
optimized_text = optimize_content(processed_text)

# Save processed text
with open("processed_article.txt", "w") as f:
    f.write(optimized_text)

# Generate video
generate_video("processed_article.txt")
```

### Multi-Language Support

```python
from openai import OpenAI

def translate_and_generate(input_file, target_language="Spanish"):
    """Translate content and generate video."""

    client = OpenAI()

    with open(input_file, "r") as f:
        original_text = f.read()

    # Translate
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {
                "role": "system",
                "content": f"Translate the following text to {target_language}. Maintain the same tone and style."
            },
            {
                "role": "user",
                "content": original_text
            }
        ]
    )

    translated_text = response.choices[0].message.content

    # Save translated text
    translated_file = f"translated_{input_file}"
    with open(translated_file, "w") as f:
        f.write(translated_text)

    # Generate video
    from direktor import generate_video
    generate_video(translated_file)
```

## Error Handling and Recovery

### Robust Processing

```python
import logging
from direktor import generate_video
from direktor.core.config import validate_env_vars

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def robust_generate(input_file, max_retries=3):
    """Generate video with retry logic."""

    # Validate configuration first
    try:
        validate_env_vars()
    except EnvironmentError as e:
        logger.error(f"Configuration error: {e}")
        return None

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            generate_video(input_file)
            logger.info("Video generation successful")
            return True
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                logger.info("Retrying...")
            else:
                logger.error("All retries exhausted")
                return False

    return False

robust_generate("article.txt")
```

### Stage-Level Recovery

```python
import os
from direktor import generate_video

def recover_and_continue(input_file):
    """Detect failed stage and continue from there."""

    # Determine output directory
    import hashlib
    with open(input_file, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    temp_dir = os.path.join("temp", file_hash)

    # Check what stages are complete
    stages = {
        1: "podcast_script.txt",
        2: "audio.mp3",
        3: "transcript.json",
        4: "image_prompts.json",
        5: "images",
        6: "output.mp4"
    }

    last_complete = 0
    for stage, output in stages.items():
        path = os.path.join(temp_dir, output)
        if os.path.exists(path):
            last_complete = stage
        else:
            break

    if last_complete == 6:
        print("Video already complete!")
        return

    # Resume from next stage
    next_stage = last_complete + 1
    print(f"Resuming from stage {next_stage}")
    generate_video(input_file, stage=next_stage)

recover_and_continue("article.txt")
```
