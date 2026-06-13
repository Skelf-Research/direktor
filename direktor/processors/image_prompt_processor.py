"""
Image prompt generation processor.
"""
import os
import json
from typing import Dict, Any, List
from openai import OpenAI

from ..core.base_processor import BaseStageProcessor, ProcessingResult, ValidationMixin, FileManagerMixin, register_processor


@register_processor('prompts')
class ImagePromptProcessor(BaseStageProcessor, ValidationMixin, FileManagerMixin):
    """Processor for generating image prompts from transcript data."""

    def __init__(self, stage_name: str):
        """Initialize image prompt processor."""
        super().__init__(stage_name)
        self.client = OpenAI(api_key=self.config.apis.openai_key)

    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        """Process transcript into image prompts.

        Args:
            input_data: Must contain 'transcript'
            job_id: Unique job identifier

        Returns:
            Processing result with image prompts
        """
        try:
            # Validate input
            self.validate_input(input_data, ['transcript'])

            transcript = input_data['transcript']
            logger = self.get_logger(job_id)

            # Generate image prompts
            prompts = self._generate_image_prompts(transcript, job_id)

            if not prompts:
                raise ValueError("No image prompts were generated")

            # Save prompts to file
            prompts_file = self.get_temp_file_path(job_id, 'image_prompts.json')
            with open(prompts_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, indent=2)

            return ProcessingResult(
                success=True,
                output_data={
                    'image_prompts': prompts,
                    'prompts_file': prompts_file,
                    'transcript': transcript,
                    'job_id': job_id
                }
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )

    def _generate_image_prompts(self, transcript: Dict[str, Any], job_id: str) -> List[Dict[str, Any]]:
        """Generate image prompts from transcript chunks.

        Args:
            transcript: Transcript data with chunks
            job_id: Job identifier

        Returns:
            List of image prompts with timestamps
        """
        logger = self.get_logger(job_id)

        # Check if prompts already exist
        prompts_file = self.get_temp_file_path(job_id, 'image_prompts.json')
        if os.path.exists(prompts_file):
            logger.info("Image prompts file already exists, loading from cache")
            with open(prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Aggregate chunks to target duration segments
        aggregated_chunks = self._aggregate_chunks(
            transcript['chunks'],
            self.config.target_segment_duration
        )

        all_prompts = []

        logger.info(f"Generating image prompts for {len(aggregated_chunks)} segment(s)")

        for i, chunk in enumerate(aggregated_chunks):
            logger.debug(f"Processing segment {i+1}/{len(aggregated_chunks)}")

            try:
                prompt = self._generate_prompt_for_chunk(chunk)
                all_prompts.append({
                    "time": chunk['timestamp'][0],
                    "prompt": prompt
                })

            except Exception as e:
                logger.warning(f"Failed to generate prompt for segment {i+1}: {e}")
                # Continue with other segments

        if not all_prompts:
            raise ValueError("Failed to generate any image prompts")

        logger.info(f"Generated {len(all_prompts)} image prompts")
        return all_prompts

    def _aggregate_chunks(self, chunks: List[Dict], target_duration: int = 30) -> List[Dict]:
        """Aggregate transcript chunks into target duration segments.

        Args:
            chunks: List of transcript chunks
            target_duration: Target duration in seconds

        Returns:
            List of aggregated chunks
        """
        if not chunks:
            return []

        aggregated_chunks = []
        current_chunk = {
            "text": "",
            "timestamp": [chunks[0]["timestamp"][0], 0]
        }

        for chunk in chunks:
            segment_duration = chunk["timestamp"][1] - current_chunk["timestamp"][0]

            if segment_duration > target_duration:
                # Finish current chunk
                current_chunk["timestamp"][1] = chunk["timestamp"][0]
                aggregated_chunks.append(current_chunk)

                # Start new chunk
                current_chunk = {
                    "text": chunk["text"],
                    "timestamp": chunk["timestamp"]
                }
            else:
                # Add to current chunk
                if current_chunk["text"]:
                    current_chunk["text"] += " " + chunk["text"]
                else:
                    current_chunk["text"] = chunk["text"]
                current_chunk["timestamp"][1] = chunk["timestamp"][1]

        # Add final chunk if it has content
        if current_chunk["text"]:
            aggregated_chunks.append(current_chunk)

        return aggregated_chunks

    def _generate_prompt_for_chunk(self, chunk: Dict[str, Any]) -> str:
        """Generate image prompt for a transcript chunk.

        Args:
            chunk: Transcript chunk with text and timestamp

        Returns:
            Generated image prompt
        """
        response = self.client.chat.completions.create(
            model=self.config.models.gpt4_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant that generates image prompts based on podcast transcripts. "
                        "Generate a single, vivid image prompt that captures the main theme or most striking "
                        "visual element from the given text. The prompt should be suitable for stable diffusion "
                        "image generation."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate a stable diffusion image generation prompt for the following podcast "
                        f"transcript segment:\n\nText: {chunk['text']}\n"
                        f"Timestamp: {chunk['timestamp'][0]} - {chunk['timestamp'][1]} seconds"
                    )
                }
            ],
            max_tokens=150,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    def get_logger(self, job_id: str):
        """Get stage logger for this job."""
        from ..core.logging_config import get_stage_logger
        return get_stage_logger(self.stage_name, job_id)

    def get_next_stage(self) -> str:
        """Get next stage in pipeline."""
        return 'images'