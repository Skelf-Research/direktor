# Data Flow

Understanding how data flows through the Direktor pipeline.

## Pipeline Data Flow

```
                    INPUT
                      │
                      ▼
┌──────────────────────────────────────┐
│           input.txt                  │
│     "Raw article text..."            │
└──────────────────────────────────────┘
                      │
                      │ optimize_content()
                      ▼
┌──────────────────────────────────────┐
│         Optimized Text               │
│  "Enhanced, engaging text..."        │
└──────────────────────────────────────┘
                      │
                      │ generate_podcast_script()
                      ▼
┌──────────────────────────────────────┐
│       podcast_script.txt             │
│  "Welcome to today's episode..."     │
└──────────────────────────────────────┘
                      │
                      │ generate_audio()
                      ▼
┌──────────────────────────────────────┐
│           audio.mp3                  │
│        [Binary audio data]           │
└──────────────────────────────────────┘
                      │
                      │ generate_transcript()
                      ▼
┌──────────────────────────────────────┐
│        transcript.json               │
│  {                                   │
│    "chunks": [                       │
│      {"text": "...",                 │
│       "timestamp": [0.0, 3.5]}       │
│    ]                                 │
│  }                                   │
└──────────────────────────────────────┘
                      │
                      │ generate_image_prompts()
                      ▼
┌──────────────────────────────────────┐
│       image_prompts.json             │
│  [                                   │
│    {"time": 0,                       │
│     "prompt": "A stunning..."}       │
│  ]                                   │
└──────────────────────────────────────┘
                      │
                      │ generate_images()
                      ▼
┌──────────────────────────────────────┐
│          images/                     │
│    image_0.webp                      │
│    image_1.webp                      │
│    image_2.webp                      │
└──────────────────────────────────────┘
                      │
                      │ create_video()
                      ▼
┌──────────────────────────────────────┐
│          output.mp4                  │
│    [Final video with audio,          │
│     images, and overlays]            │
└──────────────────────────────────────┘
```

## Data Structures

### Transcript Format

```json
{
  "chunks": [
    {
      "text": "Welcome to today's episode",
      "timestamp": [0.0, 3.5]
    },
    {
      "text": "where we explore the fascinating world",
      "timestamp": [3.5, 6.2]
    }
  ]
}
```

### Image Prompts Format

```json
[
  {
    "time": 0,
    "prompt": "A stunning cosmic landscape with swirling galaxies and nebulae"
  },
  {
    "time": 30,
    "prompt": "An artist's rendering of an exoplanet with blue oceans"
  }
]
```

### Aggregated Chunks

```json
{
  "text": "Combined text from multiple chunks...",
  "timestamp": [0.0, 30.0]
}
```

## Intermediate Files

All intermediate files are stored in `temp/<hash>/`:

| File | Stage | Format | Description |
|------|-------|--------|-------------|
| `podcast_script.txt` | 1 | Text | Generated podcast script |
| `audio.mp3` | 2 | MP3 | Generated speech audio |
| `audio_chunk_*.mp3` | 2 | MP3 | Individual audio chunks (temporary) |
| `<hash>.wav` | 3 | WAV | Audio converted for transcription (temporary) |
| `transcript.json` | 3 | JSON | Timestamped transcript |
| `image_prompts.json` | 4 | JSON | Generated image prompts |
| `images/image_*.webp` | 5 | WebP | Generated images |
| `images/image_*.png` | 6 | PNG | Converted images (temporary) |
| `concat.txt` | 6 | Text | FFmpeg concat file (temporary) |
| `temp_video.mp4` | 6 | MP4 | Video without audio (temporary) |
| `output.mp4` | 6 | MP4 | Final output video |

## External Service Calls

### OpenAI API

```
Text → GPT Model → Script/Prompts
```

Used in:
- `narrative.py`: Content optimization
- `transcript.py`: Script generation
- `images.py`: Prompt generation

### Replicate API

```
Input → Model → Output URL → Download
```

Used in:
- `audio.py`: BARK text-to-speech
- `transcript.py`: Whisper transcription
- `images.py`: FLUX image generation

### Cloud Storage (R2/S3)

```
Local File → Upload → Presigned URL
```

Used in:
- `transcript.py`: Audio upload for transcription

## Checkpointing Logic

Each function checks for existing output:

```python
def generate_something(input, temp_dir):
    output_file = os.path.join(temp_dir, "output.json")

    # Checkpoint: return existing if available
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            return json.load(f)

    # Process and save
    result = process(input)

    with open(output_file, "w") as f:
        json.dump(result, f)

    return result
```

This enables:
- Automatic resume after failures
- Manual editing of intermediate outputs
- Efficient re-runs (skips completed stages)
