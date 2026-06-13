# Custom Image Styles

Learn how to customize the visual style of your generated images.

## Understanding Image Prompts

Direktor generates image prompts based on your transcript content. These prompts are stored in `image_prompts.json`:

```json
[
  {
    "time": 0,
    "prompt": "A stunning view of the James Webb Space Telescope floating in deep space, golden hexagonal mirrors gleaming against a backdrop of distant galaxies"
  },
  {
    "time": 30,
    "prompt": "An artistic rendering of an exoplanet with visible water vapor in its atmosphere, illuminated by a distant star"
  }
]
```

## Editing Prompts Manually

After running stage 4, edit the prompts before generating images:

```bash
# Run through stage 4
direktor input.txt --stage 4

# Edit prompts
nano temp/*/image_prompts.json

# Continue with image generation
direktor input.txt --stage 5
```

## Style Modifiers

Add style modifiers to your prompts for consistent aesthetics:

### Photorealistic Style

```json
{
  "prompt": "your scene description, photorealistic, 8k resolution, detailed lighting, professional photography"
}
```

### Artistic Style

```json
{
  "prompt": "your scene description, digital art, vibrant colors, concept art style, trending on artstation"
}
```

### Minimalist Style

```json
{
  "prompt": "your scene description, minimalist design, clean lines, simple shapes, modern aesthetic"
}
```

## Programmatic Customization

You can modify prompts programmatically after generation:

```python
import json
from direktor.core.images import generate_images

# Load existing prompts
with open("temp/abc123/image_prompts.json", "r") as f:
    prompts = json.load(f)

# Add style modifier to all prompts
style = ", digital art, vibrant colors, highly detailed"
for prompt in prompts:
    prompt["prompt"] += style

# Save modified prompts
with open("temp/abc123/image_prompts.json", "w") as f:
    json.dump(prompts, f)

# Generate images with new prompts
images = generate_images(prompts, "temp/abc123")
```

## Custom Prompt Generator

Override the default prompt generation:

```python
from openai import OpenAI

def custom_prompt_generator(text_segment, timestamp):
    """Generate a custom image prompt for a transcript segment."""
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {
                "role": "system",
                "content": """Generate an image prompt in a specific style.
                Style: Cinematic, dramatic lighting, wide angle shot.
                Format: Scene description only, no meta text."""
            },
            {
                "role": "user",
                "content": f"Create an image prompt for: {text_segment}"
            }
        ]
    )

    return {
        "time": timestamp,
        "prompt": response.choices[0].message.content.strip()
    }
```

## Image Generation Parameters

The FLUX model accepts several parameters you can customize:

```python
input_data = {
    "prompt": "your prompt",
    "num_outputs": 1,
    "aspect_ratio": "16:9",    # Options: "1:1", "16:9", "9:16", "4:3"
    "output_format": "webp",    # Options: "webp", "png", "jpg"
    "output_quality": 80,       # 1-100
    "seed": 0,                  # For reproducibility
}
```

## Tips for Better Images

1. **Be Specific**: Include details about lighting, perspective, and mood
2. **Avoid Negatives**: Describe what you want, not what you don't want
3. **Keep Consistent**: Use similar style modifiers across prompts
4. **Test First**: Generate one image to test your style before full batch
