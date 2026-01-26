# Create Your First Video

This tutorial walks you through creating your first video with Direktor, from setup to final output.

## Prerequisites

Before starting, ensure you have:

- [x] Direktor installed (`pip install direktor`)
- [x] FFmpeg installed on your system
- [x] API keys configured in `.env` file

## Step 1: Prepare Your Content

Let's create a sample article about space exploration:

```bash
cat > space_article.txt << 'EOF'
The James Webb Space Telescope has revolutionized our understanding of the universe.
Launched in December 2021, this remarkable instrument has captured images of
distant galaxies, exoplanets, and stellar nurseries with unprecedented clarity.

One of its most significant discoveries includes the detection of water vapor
in the atmosphere of a distant exoplanet, bringing us closer to understanding
the potential for life beyond Earth.

The telescope's infrared capabilities allow it to peer through cosmic dust
and observe objects that were previously invisible to us. This has opened
new windows into the early universe, just a few hundred million years after
the Big Bang.

Scientists around the world continue to analyze the wealth of data from Webb,
with each discovery raising new questions about our place in the cosmos.
EOF
```

## Step 2: Run the Pipeline

### Option A: Complete Pipeline

Run all stages at once:

```bash
direktor space_article.txt
```

### Option B: Stage by Stage (Recommended for first time)

Run each stage separately to understand the process:

```bash
# Stage 1: Generate the podcast script
direktor space_article.txt --stage 1

# Review the script
cat temp/*/podcast_script.txt

# Stage 2: Generate audio
direktor space_article.txt --stage 2

# Listen to the audio
# (Play temp/*/audio.mp3 with your media player)

# Stage 3: Generate transcript
direktor space_article.txt --stage 3

# Stage 4: Generate image prompts
direktor space_article.txt --stage 4

# Review the prompts
cat temp/*/image_prompts.json

# Stage 5: Generate images
direktor space_article.txt --stage 5

# Stage 6: Create final video
direktor space_article.txt --stage 6
```

## Step 3: Review Your Output

Find your video in the temp directory:

```bash
ls -la temp/*/output.mp4
```

Play it with any video player:

```bash
# Linux
xdg-open temp/*/output.mp4

# macOS
open temp/*/output.mp4

# Windows
start temp\*\output.mp4
```

## Step 4: Customize (Optional)

### Edit the Script

After stage 1, you can edit the podcast script:

```bash
# Edit the script
nano temp/*/podcast_script.txt

# Then continue from stage 2
direktor space_article.txt --stage 2
```

### Edit Image Prompts

After stage 4, customize the visual style:

```bash
# Edit prompts
nano temp/*/image_prompts.json

# Then continue from stage 5
direktor space_article.txt --stage 5
```

## Common Issues

### "Missing environment variables"

Ensure your `.env` file has all required keys:

```bash
cp sample.env .env
# Edit .env with your API keys
```

### "FFmpeg not found"

Install FFmpeg:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### Audio generation fails

Check the `audio_generation.log` file for details. Common causes:

- Text chunks too long (try shorter input)
- API rate limiting (wait and retry)

## Next Steps

- [Custom Image Styles](custom-images.md) - Learn to control visual generation
- [Working with Long Content](long-content.md) - Handle large documents
- [Python API Guide](../guide/python-api.md) - Programmatic usage
