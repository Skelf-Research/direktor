"""
Transcript generation processor.
"""
import os
import json
import subprocess
import hashlib
from typing import Dict, Any
import replicate
import boto3
from botocore.client import Config

from ..core.base_processor import BaseStageProcessor, ProcessingResult, ValidationMixin, FileManagerMixin, register_processor


@register_processor('transcript')
class TranscriptProcessor(BaseStageProcessor, ValidationMixin, FileManagerMixin):
    """Processor for generating transcripts from audio files."""

    def __init__(self, stage_name: str):
        """Initialize transcript processor."""
        super().__init__(stage_name)

        # Initialize S3 client for R2 storage
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.config.aws.endpoint_url,
            aws_access_key_id=self.config.aws.access_key_id,
            aws_secret_access_key=self.config.aws.secret_access_key,
            config=Config(signature_version='s3v4'),
            region_name=self.config.aws.region_name
        )

    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        """Process audio file into transcript.

        Args:
            input_data: Must contain 'audio_file'
            job_id: Unique job identifier

        Returns:
            Processing result with transcript data
        """
        try:
            # Validate input
            self.validate_input(input_data, ['audio_file'])

            audio_file = input_data['audio_file']
            self.validate_file_exists(audio_file)

            logger = self.get_logger(job_id)

            # Generate transcript
            transcript = self._generate_transcript(audio_file, job_id)

            if not transcript:
                raise ValueError("Transcript generation failed")

            # Save transcript to file
            transcript_file = self.get_temp_file_path(job_id, 'transcript.json')
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript, f, indent=2)

            return ProcessingResult(
                success=True,
                output_data={
                    'transcript': transcript,
                    'transcript_file': transcript_file,
                    'audio_file': audio_file,
                    'job_id': job_id
                }
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )

    def _generate_transcript(self, audio_file: str, job_id: str) -> Dict[str, Any]:
        """Generate transcript from audio file.

        Args:
            audio_file: Path to audio file
            job_id: Job identifier

        Returns:
            Transcript data with timestamps
        """
        logger = self.get_logger(job_id)

        # Check if transcript already exists
        transcript_file = self.get_temp_file_path(job_id, 'transcript.json')
        if os.path.exists(transcript_file):
            logger.info("Transcript file already exists, loading from cache")
            with open(transcript_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Convert audio to WAV format for transcription
        wav_file = self._convert_to_wav(audio_file, job_id)

        # Upload WAV file to cloud storage
        audio_url = self._upload_audio_file(wav_file, job_id)

        if not audio_url:
            raise ValueError("Failed to upload audio file for transcription")

        # Run transcription model
        logger.info("Running speech-to-text transcription")
        transcript = self._run_transcription_model(audio_url)

        # Clean up temporary WAV file
        try:
            os.remove(wav_file)
        except OSError:
            pass  # Ignore cleanup errors

        logger.info("Transcript generation completed")
        return transcript

    def _convert_to_wav(self, audio_file: str, job_id: str) -> str:
        """Convert audio file to WAV format for transcription.

        Args:
            audio_file: Path to input audio file
            job_id: Job identifier

        Returns:
            Path to converted WAV file
        """
        logger = self.get_logger(job_id)

        # Generate hash for unique filename
        with open(audio_file, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        wav_file = self.get_temp_file_path(job_id, f"{file_hash}.wav")

        # Check if WAV file already exists
        if os.path.exists(wav_file):
            logger.info("WAV file already exists, skipping conversion")
            return wav_file

        logger.info("Converting audio to WAV format")

        try:
            subprocess.run([
                "ffmpeg",
                "-i", audio_file,
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                wav_file
            ], check=True, capture_output=True)

            logger.info(f"Audio converted to WAV: {wav_file}")
            return wav_file

        except subprocess.CalledProcessError as e:
            logger.error(f"Audio conversion failed: {e}")
            raise ValueError(f"Failed to convert audio to WAV: {e}")

    def _upload_audio_file(self, wav_file: str, job_id: str) -> str:
        """Upload audio file to cloud storage.

        Args:
            wav_file: Path to WAV file
            job_id: Job identifier

        Returns:
            Public URL to uploaded file
        """
        logger = self.get_logger(job_id)

        # Generate object name
        file_hash = os.path.splitext(os.path.basename(wav_file))[0]
        object_name = f"{file_hash}.wav"

        try:
            # Upload file
            self.s3_client.upload_file(
                wav_file,
                self.config.aws.bucket_name,
                object_name
            )

            # Generate presigned URL (valid for 1 hour)
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.config.aws.bucket_name,
                    'Key': object_name
                },
                ExpiresIn=3600
            )

            logger.info(f"Audio file uploaded to cloud storage")
            return url

        except Exception as e:
            logger.error(f"Failed to upload audio file: {e}")
            return None

    def _run_transcription_model(self, audio_url: str) -> Dict[str, Any]:
        """Run transcription model on audio file.

        Args:
            audio_url: URL to audio file

        Returns:
            Transcript data
        """
        input_data = {
            "audio": audio_url,
            "task": "transcribe",
            "language": "english",
            "timestamp": "chunk",
        }

        prediction = replicate.predictions.create(
            model=self.config.models.distil_model,
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
            raise ValueError(f"Transcription failed with status: {prediction.status}")

    def get_logger(self, job_id: str):
        """Get stage logger for this job."""
        from ..core.logging_config import get_stage_logger
        return get_stage_logger(self.stage_name, job_id)

    def get_next_stage(self) -> str:
        """Get next stage in pipeline."""
        return 'prompts'