# Quick Start

Create your first video with Direktor in 5 minutes.

## Step 1: Prepare Your Content

Create a text file with the content you want to convert to video:

```bash
# Create a sample input file
cat > my_article.txt << 'EOF'
Artificial Intelligence is transforming how we work and live.
From voice assistants to autonomous vehicles, AI technologies
are becoming increasingly integrated into our daily routines.

Machine learning algorithms can now recognize images, understand
natural language, and even generate creative content. These
capabilities are opening up new possibilities in healthcare,
education, and entertainment.

As we move forward, the collaboration between humans and AI
will shape the future of innovation and productivity.
EOF
```

## Step 2: Run the Pipeline

### Using CLI

```bash
# Run complete pipeline (all 6 stages)
direktor my_article.txt

# Or run up to a specific stage
direktor my_article.txt --stage 3
```

### Using Python API

```python
from direktor import generate_video

# Generate a complete video
generate_video("my_article.txt")

# Or run up to stage 3 (generate transcript)
generate_video("my_article.txt", stage=3)
```

## Step 3: Find Your Output

The output will be in a `temp/<hash>/` directory:

```
temp/
└── a1b2c3d4.../
    ├── podcast_script.txt    # Stage 1 output
    ├── audio.mp3             # Stage 2 output
    ├── transcript.json       # Stage 3 output
    ├── image_prompts.json    # Stage 4 output
    ├── images/               # Stage 5 output
    │   ├── image_0.webp
    │   ├── image_1.webp
    │   └── ...
    └── output.mp4            # Stage 6 - Final video!
```

## Pipeline Stages Explained

| Stage | Description | Output |
|-------|-------------|--------|
| 1 | Generate podcast script | `podcast_script.txt` |
| 2 | Generate audio from script | `audio.mp3` |
| 3 | Transcribe audio with timestamps | `transcript.json` |
| 4 | Generate image prompts | `image_prompts.json` |
| 5 | Generate images | `images/` directory |
| 6 | Create final video | `output.mp4` |

## Resuming from a Stage

If a stage fails, you can resume from where you left off:

```bash
# Resume from stage 4 (image prompts)
direktor my_article.txt --stage 4
```

!!! tip "Cost Optimization"
    Run stages 1-3 first to review the script and audio before
    generating images (which uses more API credits).

## Next Steps

- [Configuration Guide](configuration.md) - Customize models and settings
- [Pipeline Stages](../guide/pipeline-stages.md) - Deep dive into each stage
- [Tutorials](../tutorials/first-video.md) - Advanced usage examples
