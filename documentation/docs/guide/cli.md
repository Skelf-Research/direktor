# CLI Usage

Direktor provides a command-line interface for generating videos from text files.

## Basic Usage

```bash
direktor <input_file> [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `input_file` | Path to the input text file (required) |

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--stage` | `6` | Stage to run up to (1-6) |
| `--help` | - | Show help message |

## Examples

### Run Complete Pipeline

```bash
direktor article.txt
```

### Run Specific Stages

```bash
# Only generate script (stage 1)
direktor article.txt --stage 1

# Generate script and audio (stages 1-2)
direktor article.txt --stage 2

# Generate through transcript (stages 1-3)
direktor article.txt --stage 3
```

### Resume from a Stage

If you've already completed earlier stages:

```bash
# Resume from image prompts (stage 4)
direktor article.txt --stage 4

# Resume from image generation (stage 5)
direktor article.txt --stage 5

# Resume from video creation (stage 6)
direktor article.txt --stage 6
```

## Output Location

All outputs are stored in a temporary directory based on the input file's hash:

```
temp/<md5_hash>/
├── podcast_script.txt
├── audio.mp3
├── transcript.json
├── image_prompts.json
├── images/
└── output.mp4
```

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | Input file not found |
| `1` | Missing environment variables |

## Environment

The CLI automatically loads environment variables from a `.env` file in the current directory.

```bash
# Create .env file
cp sample.env .env

# Edit with your API keys
nano .env

# Run
direktor input.txt
```
