# Pipeline Stages

Direktor uses a 6-stage pipeline to transform text into video. Each stage produces intermediate outputs that can be reviewed and customized.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT TEXT                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Content Optimization & Script Generation              │
│  Input: Raw text                                                 │
│  Output: podcast_script.txt                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: Audio Generation                                       │
│  Input: Podcast script                                           │
│  Output: audio.mp3                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Transcript Generation                                  │
│  Input: Audio file                                               │
│  Output: transcript.json                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 4: Image Prompt Generation                                │
│  Input: Transcript                                               │
│  Output: image_prompts.json                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 5: Image Generation                                       │
│  Input: Image prompts                                            │
│  Output: images/*.webp                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 6: Video Creation                                         │
│  Input: Audio + Images + Prompts                                 │
│  Output: output.mp4                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Stage 1: Content Optimization & Script Generation

**Purpose:** Transform raw text into an engaging podcast script.

**Process:**

1. Content is first optimized using NLP techniques for clarity and engagement
2. Text is split into chunks based on token limits
3. GPT generates a conversational podcast script for each chunk
4. Scripts are combined into a single coherent narrative

**Output:** `podcast_script.txt`

**Technologies:** OpenAI GPT models

## Stage 2: Audio Generation

**Purpose:** Convert the podcast script into natural-sounding speech.

**Process:**

1. Script is split into sentences
2. Sentences are grouped into chunks (max 150 characters)
3. BARK model generates audio for each chunk
4. FFmpeg concatenates chunks into a single audio file

**Output:** `audio.mp3`

**Technologies:** Replicate BARK model, FFmpeg

## Stage 3: Transcript Generation

**Purpose:** Create a timestamped transcript from the audio.

**Process:**

1. Audio is converted to WAV format (16kHz)
2. WAV file is uploaded to cloud storage
3. Distil-Whisper transcribes with timestamps
4. Transcript is saved with chunk-level timestamps

**Output:** `transcript.json`

**Technologies:** Replicate Distil-Whisper, FFmpeg, Cloudflare R2

## Stage 4: Image Prompt Generation

**Purpose:** Generate visual descriptions for each segment.

**Process:**

1. Transcript chunks are aggregated into ~30-second segments
2. GPT analyzes each segment's content
3. Vivid image prompts are generated for each segment
4. Prompts are saved with timestamps

**Output:** `image_prompts.json`

**Technologies:** OpenAI GPT models

## Stage 5: Image Generation

**Purpose:** Create visual images from the prompts.

**Process:**

1. Each prompt is sent to the FLUX model
2. Images are generated in 16:9 aspect ratio
3. Images are saved in WebP format

**Output:** `images/image_0.webp`, `images/image_1.webp`, etc.

**Technologies:** Replicate FLUX model

## Stage 6: Video Creation

**Purpose:** Combine all elements into the final video.

**Process:**

1. WebP images are converted to PNG
2. Images are scaled to 1920x1080
3. Video is created with image timing based on prompts
4. Audio is combined with video
5. Optional keyword overlays are added

**Output:** `output.mp4`

**Technologies:** FFmpeg, Pillow

## Resuming from a Stage

Each stage checks for existing outputs before processing:

```python
# Stage 1 already complete? Skip to Stage 2
direktor input.txt --stage 2
```

This allows you to:

- Review intermediate outputs
- Manually edit scripts or prompts
- Retry failed stages without reprocessing

## Cost Considerations

| Stage | API Calls | Relative Cost |
|-------|-----------|---------------|
| 1 | GPT (text) | Low |
| 2 | Replicate (audio) | Medium |
| 3 | Replicate (transcription) | Low |
| 4 | GPT (text) | Low |
| 5 | Replicate (images) | High |
| 6 | None (local) | Free |

!!! tip "Cost Optimization"
    Run stages 1-4 first to review prompts before generating images.
