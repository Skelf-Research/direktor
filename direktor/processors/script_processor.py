"""
Script generation processor.
"""
import os
from typing import Dict, Any
from openai import OpenAI
import tiktoken

from ..core.base_processor import BaseStageProcessor, ProcessingResult, ValidationMixin, FileManagerMixin, register_processor
from ..core.narrative import optimize_content


@register_processor('script')
class ScriptProcessor(BaseStageProcessor, ValidationMixin, FileManagerMixin):
    """Processor for generating podcast scripts from text content."""

    def __init__(self, stage_name: str):
        """Initialize script processor."""
        super().__init__(stage_name)
        self.client = OpenAI(api_key=self.config.apis.openai_key)
        self.encoding = tiktoken.encoding_for_model(self.config.models.gpt4_model)

    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        """Process text content into podcast script.

        Args:
            input_data: Must contain 'text_content' and optionally 'optimize_content'
            job_id: Unique job identifier

        Returns:
            Processing result with script content
        """
        try:
            # Validate input
            self.validate_input(input_data, ['text_content'])

            text_content = input_data['text_content']
            should_optimize = input_data.get('optimize_content', True)

            # Apply content optimization if requested
            if should_optimize:
                try:
                    text_content = optimize_content(text_content)
                except Exception as e:
                    # Log warning but continue with original text
                    logger = self.get_logger(job_id)
                    logger.warning(f"Content optimization failed: {e}. Using original text.")

            # Generate podcast script
            script = self._generate_podcast_script(text_content, job_id)

            # Save script to temp file
            script_file = self.get_temp_file_path(job_id, 'podcast_script.txt')
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script)

            return ProcessingResult(
                success=True,
                output_data={
                    'script_content': script,
                    'script_file': script_file,
                    'job_id': job_id
                }
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )

    def _generate_podcast_script(self, input_text: str, job_id: str) -> str:
        """Generate podcast script from input text.

        Args:
            input_text: Source text content
            job_id: Job identifier for logging

        Returns:
            Generated podcast script
        """
        logger = self.get_logger(job_id)

        # Check if script already exists
        script_file = self.get_temp_file_path(job_id, 'podcast_script.txt')
        if os.path.exists(script_file):
            logger.info("Script file already exists, loading from cache")
            with open(script_file, 'r', encoding='utf-8') as f:
                return f.read()

        # Split text into chunks if needed
        chunks = self._split_text(input_text)
        script_parts = []

        logger.info(f"Generating script from {len(chunks)} text chunk(s)")

        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)}")

            try:
                response = self.client.chat.completions.create(
                    model=self.config.models.gpt4_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an AI assistant that creates engaging single-person podcast scripts from input text."
                        },
                        {
                            "role": "user",
                            "content": f"Create an engaging single-person podcast script based on the following text. Do not add any additional text like host introductions, pauses, or stage directions:\n\n{chunk}"
                        }
                    ],
                    max_tokens=self.config.models.gpt4_max_tokens // 2,  # Leave room for response
                    temperature=0.7
                )
                script_parts.append(response.choices[0].message.content)

            except Exception as e:
                logger.error(f"Failed to process chunk {i+1}: {e}")
                # Continue with other chunks
                continue

        if not script_parts:
            raise ValueError("Failed to generate any script content")

        script = " ".join(script_parts)
        logger.info(f"Generated script with {len(script)} characters")

        return script

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks based on token limits.

        Args:
            text: Input text to split

        Returns:
            List of text chunks
        """
        max_tokens = self.config.models.gpt4_max_tokens - 1000  # Reserve tokens for prompt and response
        tokens = self.encoding.encode(text)

        if len(tokens) <= max_tokens:
            return [text]

        chunks = []
        current_chunk = []
        current_length = 0

        for token in tokens:
            if current_length + 1 > max_tokens:
                chunks.append(self.encoding.decode(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(token)
            current_length += 1

        if current_chunk:
            chunks.append(self.encoding.decode(current_chunk))

        return chunks

    def get_logger(self, job_id: str):
        """Get stage logger for this job."""
        from ..core.logging_config import get_stage_logger
        return get_stage_logger(self.stage_name, job_id)

    def get_next_stage(self) -> str:
        """Get next stage in pipeline."""
        return 'audio'