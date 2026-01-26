# Working with Long Content

Handle large documents efficiently with Direktor.

## Understanding Token Limits

Direktor splits content based on token limits:

- **GPT-4**: ~8,000 tokens per request (configurable)
- **BARK**: ~150 characters per audio chunk
- **Aggregation**: ~30 seconds per image segment

## Processing Long Documents

### Automatic Chunking

Direktor automatically handles long content:

```python
from direktor import generate_video

# Works with any length
generate_video("long_document.txt")
```

The pipeline:
1. Splits text into token-appropriate chunks
2. Processes each chunk through GPT
3. Concatenates audio chunks
4. Aggregates transcript segments

### Manual Chunking for Control

For very long documents, consider manual splitting:

```python
import os
from direktor.core.utils import split_text, create_temp_dir
from direktor.core.config import GPT4_MAX_TOKENS

# Read long document
with open("book_chapter.txt", "r") as f:
    full_text = f.read()

# Split into manageable sections
sections = split_text(full_text, max_tokens=GPT4_MAX_TOKENS - 1000)

print(f"Document split into {len(sections)} sections")

# Process each section separately if needed
for i, section in enumerate(sections):
    with open(f"section_{i}.txt", "w") as f:
        f.write(section)
```

## Optimizing for Long Content

### 1. Pre-process Your Text

Clean up your document before processing:

```python
import re

def preprocess_document(text):
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove page numbers and headers
    text = re.sub(r'Page \d+', '', text)

    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')

    return text.strip()
```

### 2. Use Stage-by-Stage Processing

For documents over 10,000 words:

```bash
# Generate script first (review before expensive stages)
direktor long_doc.txt --stage 1

# Review and edit if needed
less temp/*/podcast_script.txt

# Continue if satisfied
direktor long_doc.txt --stage 6
```

### 3. Monitor Progress

Track progress for long processing:

```python
from direktor.core.transcript import generate_podcast_script
from direktor.core.utils import create_temp_dir, split_text
from direktor.core.config import GPT4_MAX_TOKENS
from tqdm import tqdm

def process_with_progress(input_file):
    temp_dir = create_temp_dir(input_file)

    with open(input_file, "r") as f:
        text = f.read()

    chunks = split_text(text, GPT4_MAX_TOKENS - 1000)

    print(f"Processing {len(chunks)} chunks...")

    # The actual functions already use tqdm
    script = generate_podcast_script(text, temp_dir)

    return script
```

## Cost Estimation

Estimate API costs before processing:

```python
from direktor.core.config import encoding

def estimate_cost(text):
    tokens = len(encoding.encode(text))

    # Approximate costs (adjust based on current pricing)
    gpt_cost = (tokens / 1000) * 0.01  # GPT-4 input

    # Estimate output tokens (roughly 1.5x input for scripts)
    output_tokens = tokens * 1.5
    gpt_cost += (output_tokens / 1000) * 0.03  # GPT-4 output

    # Estimate number of images (1 per 30 seconds, ~150 words/minute)
    words = len(text.split())
    duration_minutes = words / 150
    num_images = int(duration_minutes * 2)  # 2 images per minute

    image_cost = num_images * 0.02  # FLUX approximate cost

    print(f"Estimated costs:")
    print(f"  Input tokens: {tokens:,}")
    print(f"  GPT processing: ${gpt_cost:.2f}")
    print(f"  Images ({num_images}): ${image_cost:.2f}")
    print(f"  Total estimate: ${gpt_cost + image_cost:.2f}")

with open("long_doc.txt", "r") as f:
    estimate_cost(f.read())
```

## Memory Considerations

For very large documents:

```python
import gc

def process_in_batches(input_file, batch_size=5):
    """Process document in batches to manage memory."""

    # Process stages that can be batched
    for stage in range(1, 7):
        print(f"Running stage {stage}...")

        # Run stage
        from direktor import generate_video
        generate_video(input_file, stage=stage)

        # Force garbage collection between stages
        gc.collect()

        print(f"Stage {stage} complete")
```

## Resuming Failed Jobs

Long processing jobs may fail. Resume from checkpoints:

```bash
# Check what's completed
ls temp/*/

# Resume from the failed stage
direktor long_doc.txt --stage 4
```
