"""
Audio generation processor.
"""
import os
import re
import subprocess
import logging
from typing import Dict, Any, List
import replicate

from ..core.base_processor import BaseStageProcessor, ProcessingResult, ValidationMixin, FileManagerMixin, register_processor
from ..core.utils import download_file


@register_processor('audio')
class AudioProcessor(BaseStageProcessor, ValidationMixin, FileManagerMixin):
    """Processor for generating audio from podcast scripts."""

    def __init__(self, stage_name: str):
        """Initialize audio processor."""
        super().__init__(stage_name)
        # Set up logging for audio generation
        self.audio_logger = logging.getLogger('audio_generation')
        self.audio_logger.setLevel(logging.ERROR)

        # Create file handler if it doesn't exist
        if not self.audio_logger.handlers:
            handler = logging.FileHandler('audio_generation.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.audio_logger.addHandler(handler)

    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        """Process podcast script into audio.

        Args:
            input_data: Must contain 'script_content'
            job_id: Unique job identifier

        Returns:
            Processing result with audio file path
        """
        try:
            # Validate input
            self.validate_input(input_data, ['script_content'])

            script_content = input_data['script_content']
            logger = self.get_logger(job_id)

            # Generate audio from script
            audio_file = self._generate_audio(script_content, job_id)

            if not audio_file or not os.path.exists(audio_file):
                raise ValueError("Audio generation failed - no output file created")

            return ProcessingResult(
                success=True,
                output_data={
                    'audio_file': audio_file,
                    'script_content': script_content,
                    'job_id': job_id
                }
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )

    def _generate_audio(self, text: str, job_id: str) -> str:
        """Generate audio from text using BARK model.

        Args:
            text: Script text to convert to audio
            job_id: Job identifier

        Returns:
            Path to generated audio file
        """
        logger = self.get_logger(job_id)
        audio_file = self.get_temp_file_path(job_id, 'audio.mp3')

        # Check if audio already exists
        if os.path.exists(audio_file):
            logger.info("Audio file already exists, skipping generation")
            return audio_file

        # Split text into manageable chunks
        sentences = self._split_into_sentences(text)
        chunks = self._group_sentences(sentences, self.config.max_chunk_chars)

        all_audio_files = []
        failed_chunks = []

        logger.info(f"Generating audio from {len(chunks)} chunk(s)")

        for i, chunk in enumerate(chunks):
            chunk_audio_file = f'audio_chunk_{i}.mp3'
            full_chunk_audio_path = self.get_temp_file_path(job_id, chunk_audio_file)

            try:
                logger.debug(f"Processing audio chunk {i+1}/{len(chunks)}")
                self._generate_chunk_audio(chunk, full_chunk_audio_path)
                all_audio_files.append(chunk_audio_file)

            except Exception as e:
                error_msg = f"Failed to generate audio for chunk {i}: {str(e)}"
                self.audio_logger.error(error_msg)
                self.audio_logger.error(f"Chunk text: {chunk}")
                logger.warning(error_msg)
                failed_chunks.append(i)

        # Filter out failed chunks
        successful_audio_files = [
            audio_file for i, audio_file in enumerate(all_audio_files)
            if i not in failed_chunks
        ]

        if not successful_audio_files:
            raise ValueError("No audio chunks were successfully generated")

        # Concatenate audio files if needed
        final_audio_file = self._concatenate_audio_files(
            successful_audio_files, job_id, audio_file
        )

        logger.info(f"Generated audio file: {final_audio_file}")
        return final_audio_file

    def _generate_chunk_audio(self, text: str, output_path: str) -> None:
        """Generate audio for a single text chunk.

        Args:
            text: Text to convert to audio
            output_path: Path to save audio file
        """
        input_data = {
            "text": text,
            "alpha": 0.3,
            "beta": 0.7,
            "diffusion_steps": 10,
            "embedding_scale": 1.5,
            "seed": 0
        }

        # Run the model
        output = self._run_replicate_model(self.config.models.bark_model, input_data)

        # Download the audio file
        download_file(output, output_path)

    def _run_replicate_model(self, model: str, input_data: Dict[str, Any]) -> str:
        """Run a Replicate model and wait for completion.

        Args:
            model: Model identifier
            input_data: Input parameters for the model

        Returns:
            Model output URL
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

    def _concatenate_audio_files(self, audio_files: List[str], job_id: str, output_file: str) -> str:
        """Concatenate multiple audio files into one.

        Args:
            audio_files: List of audio file names (relative to temp dir)
            job_id: Job identifier
            output_file: Path to output file

        Returns:
            Path to concatenated audio file
        """
        logger = self.get_logger(job_id)
        temp_dir = self.get_temp_dir(job_id)

        if len(audio_files) == 1:
            # Single file - just rename it
            single_file_path = self.get_temp_file_path(job_id, audio_files[0])
            try:
                os.rename(single_file_path, output_file)
                return output_file
            except OSError as e:
                logger.error(f"Failed to rename audio file: {e}")
                raise

        # Multiple files - concatenate with FFmpeg
        concat_list_file = self.get_temp_file_path(job_id, "concat_list.txt")

        with open(concat_list_file, "w") as f:
            for audio_file_name in audio_files:
                f.write(f"file '{audio_file_name}'\n")

        try:
            subprocess.run([
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", "concat_list.txt",
                "-c", "copy",
                "audio.mp3"
            ], check=True, cwd=temp_dir, capture_output=True)

        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg concatenation failed: {str(e)}"
            self.audio_logger.error(error_msg)
            logger.error(error_msg)
            raise

        # Clean up individual chunk files and concat list
        for chunk_file in audio_files:
            try:
                os.remove(self.get_temp_file_path(job_id, chunk_file))
            except OSError:
                pass  # Ignore cleanup errors

        try:
            os.remove(concat_list_file)
        except OSError:
            pass  # Ignore cleanup errors

        return output_file

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Split on sentence-ending punctuation followed by whitespace
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _group_sentences(self, sentences: List[str], max_chars: int = 150) -> List[str]:
        """Group sentences into chunks under character limit.

        Args:
            sentences: List of sentences
            max_chars: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def get_logger(self, job_id: str):
        """Get stage logger for this job."""
        from ..core.logging_config import get_stage_logger
        return get_stage_logger(self.stage_name, job_id)

    def get_next_stage(self) -> str:
        """Get next stage in pipeline."""
        return 'transcript'