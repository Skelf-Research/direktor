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
| `--output`, `-o` | temp dir | Directory for the final `output.mp4` |
| `--temp-dir` | `temp/<hash>` | Temporary working directory |
| `--keywords-file` | - | JSON file with keyword overlays |
| `--resume` / `--no-resume` | `True` | Skip stages whose outputs already exist |
| `--clean` | `False` | Remove the temporary directory before starting |
| `--no-optimize` | `False` | Skip narrative content optimization |
| `--verbose`, `-v` | `False` | Enable DEBUG logging |
| `--version` | - | Show version and exit |
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

If you've already completed earlier stages, use `--resume` (the default):

```bash
# Resume from image prompts (stage 4)
direktor article.txt --stage 4

# Resume from image generation (stage 5)
direktor article.txt --stage 5

# Resume from video creation (stage 6)
direktor article.txt --stage 6
```

### Custom Output and Keyword Overlays

```bash
# Write final video to a specific directory
direktor article.txt --output ./videos/

# Add keyword overlays from a JSON file
direktor article.txt --keywords-file keywords.json
```

The keyword file format is:

```json
[["Introduction", 0, 10], ["Main Topic", 10, 60]]
```

## Output Location

By default, outputs are stored in a temporary directory based on the input file's hash:

```
temp/<md5_hash>/
├── podcast_script.txt
├── audio.mp3
├── transcript.json
├── image_prompts.json
├── images/
└── output.mp4
```

Use `--output` to copy the final `output.mp4` to a different directory.

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | Input file not found, missing environment variables, or pipeline failure |

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
