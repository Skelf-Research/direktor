"""
Image generation processor.
"""
import os
from typing import Dict, Any, List
import replicate

from ..core.base_processor import BaseStageProcessor, ProcessingResult, ValidationMixin, FileManagerMixin, register_processor
from ..core.utils import download_file


@register_processor('images')
class ImageProcessor(BaseStageProcessor, ValidationMixin, FileManagerMixin):
    """Processor for generating images from prompts."""

    def __init__(self, stage_name: str):
        """Initialize image processor."""
        super().__init__(stage_name)

    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        """Process image prompts into images.

        Args:
            input_data: Must contain 'image_prompts'
            job_id: Unique job identifier

        Returns:
            Processing result with image file paths
        """
        try:
            # Validate input
            self.validate_input(input_data, ['image_prompts'])

            image_prompts = input_data['image_prompts']
            logger = self.get_logger(job_id)

            # Generate images
            image_files = self._generate_images(image_prompts, job_id)

            if not image_files:
                raise ValueError("No images were generated")

            return ProcessingResult(
                success=True,
                output_data={
                    'image_files': image_files,
                    'image_prompts': image_prompts,
                    'job_id': job_id
                }
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )

    def _generate_images(self, prompts: List[Dict[str, Any]], job_id: str) -> List[str]:
        """Generate images from prompts.

        Args:
            prompts: List of image prompts with timestamps
            job_id: Job identifier

        Returns:
            List of generated image file paths
        """
        logger = self.get_logger(job_id)

        # Create images directory
        image_dir = self.get_temp_file_path(job_id, 'images')
        os.makedirs(image_dir, exist_ok=True)

        image_files = []
        failed_images = []

        logger.info(f"Generating {len(prompts)} image(s)")

        for i, prompt_data in enumerate(prompts):
            image_file = os.path.join(image_dir, f'image_{i}.webp')

            try:
                # Check if image already exists
                if os.path.exists(image_file):
                    logger.debug(f"Image {i} already exists, skipping generation")
                    image_files.append(image_file)
                    continue

                logger.debug(f"Generating image {i+1}/{len(prompts)}")

                # Generate image
                self._generate_single_image(prompt_data, image_file)
                image_files.append(image_file)

                logger.debug(f"Generated image: {image_file}")

            except Exception as e:
                logger.warning(f"Failed to generate image {i}: {e}")
                failed_images.append(i)
                # Continue with other images

        if not image_files:
            raise ValueError("Failed to generate any images")

        success_rate = len(image_files) / len(prompts) * 100
        logger.info(f"Generated {len(image_files)}/{len(prompts)} images ({success_rate:.1f}% success rate)")

        if failed_images:
            logger.warning(f"Failed to generate images for prompts: {failed_images}")

        return image_files

    def _generate_single_image(self, prompt_data: Dict[str, Any], output_file: str) -> None:
        """Generate a single image from prompt.

        Args:
            prompt_data: Prompt data with 'prompt' field
            output_file: Path to save generated image
        """
        input_data = {
            "prompt": prompt_data['prompt'],
            "num_outputs": 1,
            "aspect_ratio": "16:9",
            "output_format": "webp",
            "output_quality": 80,
            "seed": 0,
            "disable_safety_checker": True
        }

        # Run the model
        output = self._run_replicate_model(self.config.models.flux_model, input_data)

        # Download the generated image
        if isinstance(output, list) and output:
            download_file(output[0], output_file, show_progress=False)
        else:
            raise ValueError("Invalid model output format")

    def _run_replicate_model(self, model: str, input_data: Dict[str, Any]) -> Any:
        """Run a Replicate model and wait for completion.

        Args:
            model: Model identifier
            input_data: Input parameters for the model

        Returns:
            Model output
        """
        prediction = replicate.predictions.create(
            model=model,
            input=input_data
        )

        # Wait for completion
        while prediction.status not in {"succeeded", "failed", "canceled"}:
            import time
            time.sleep(1)
            prediction.reload()

        if prediction.status == "succeeded":
            return prediction.output
        else:
            raise Exception(f"Prediction failed with status: {prediction.status}")

    def get_logger(self, job_id: str):
        """Get stage logger for this job."""
        from ..core.logging_config import get_stage_logger
        return get_stage_logger(self.stage_name, job_id)

    def get_next_stage(self) -> str:
        """Get next stage in pipeline."""
        return 'video'