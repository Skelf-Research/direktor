"""
Video creation processor.
"""
import os
import subprocess
from typing import Dict, Any, List, Optional
from PIL import Image

from ..core.base_processor import BaseStageProcessor, ProcessingResult, ValidationMixin, FileManagerMixin, register_processor


@register_processor('video')
class VideoProcessor(BaseStageProcessor, ValidationMixin, FileManagerMixin):
    """Processor for creating videos from audio and images."""

    def __init__(self, stage_name: str):
        """Initialize video processor."""
        super().__init__(stage_name)

    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        """Process audio and images into final video.

        Args:
            input_data: Must contain 'audio_file', 'image_files', 'image_prompts'
            job_id: Unique job identifier

        Returns:
            Processing result with video file path
        """
        try:
            # Validate input
            required_fields = ['audio_file', 'image_files', 'image_prompts']
            self.validate_input(input_data, required_fields)

            audio_file = input_data['audio_file']
            image_files = input_data['image_files']
            image_prompts = input_data['image_prompts']
            keywords = input_data.get('keywords', self._get_default_keywords())

            # Validate files exist
            self.validate_file_exists(audio_file)
            for image_file in image_files:
                self.validate_file_exists(image_file)

            logger = self.get_logger(job_id)

            # Create video
            output_file = self._create_video(
                audio_file, image_files, image_prompts, keywords, job_id
            )

            if not output_file or not os.path.exists(output_file):
                raise ValueError("Video creation failed - no output file created")

            return ProcessingResult(
                success=True,
                output_data={
                    'video_file': output_file,
                    'audio_file': audio_file,
                    'image_files': image_files,
                    'job_id': job_id
                }
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )

    def _create_video(self,
                     audio_file: str,
                     image_files: List[str],
                     image_prompts: List[Dict[str, Any]],
                     keywords: List[tuple],
                     job_id: str) -> str:
        """Create video from audio and images.

        Args:
            audio_file: Path to audio file
            image_files: List of image file paths
            image_prompts: List of image prompts with timestamps
            keywords: List of (keyword, start_time, end_time) tuples
            job_id: Job identifier

        Returns:
            Path to created video file
        """
        logger = self.get_logger(job_id)
        output_file = self.get_temp_file_path(job_id, "output.mp4")

        # Check if video already exists
        if os.path.exists(output_file):
            logger.info("Video file already exists, skipping creation")
            return output_file

        logger.info("Starting video creation process")

        # Convert WebP images to PNG if needed
        png_image_files = self._convert_images_to_png(image_files, job_id)

        # Create video from images
        temp_video = self._create_image_video(png_image_files, image_prompts, job_id)

        # Combine with audio and add overlays
        final_video = self._combine_audio_video(
            temp_video, audio_file, keywords, job_id, output_file
        )

        # Cleanup temporary files
        self._cleanup_temp_video_files(temp_video, png_image_files, image_files, job_id)

        logger.info(f"Video created successfully: {output_file}")
        return final_video

    def _convert_images_to_png(self, image_files: List[str], job_id: str) -> List[str]:
        """Convert WebP images to PNG format.

        Args:
            image_files: List of image file paths
            job_id: Job identifier

        Returns:
            List of PNG image file paths
        """
        logger = self.get_logger(job_id)
        png_image_files = []

        for image_file in image_files:
            if image_file.lower().endswith('.webp'):
                png_file = self.get_temp_file_path(
                    job_id,
                    os.path.splitext(os.path.basename(image_file))[0] + '.png'
                )

                try:
                    with Image.open(image_file) as img:
                        img.save(png_file, 'PNG')
                    png_image_files.append(png_file)
                    logger.debug(f"Converted {image_file} to PNG")

                except Exception as e:
                    logger.warning(f"Failed to convert {image_file} to PNG: {e}")
                    # Use original file if conversion fails
                    png_image_files.append(image_file)
            else:
                png_image_files.append(image_file)

        return png_image_files

    def _create_image_video(self,
                           image_files: List[str],
                           image_prompts: List[Dict[str, Any]],
                           job_id: str) -> str:
        """Create video from images with timing.

        Args:
            image_files: List of image file paths
            image_prompts: List of prompts with timing data
            job_id: Job identifier

        Returns:
            Path to temporary video file
        """
        logger = self.get_logger(job_id)
        temp_video = self.get_temp_file_path(job_id, "temp_video.mp4")
        concat_file = self.get_temp_file_path(job_id, "concat.txt")

        # Create concat file for FFmpeg
        try:
            with open(concat_file, "w") as f:
                for i, (image_file, prompt) in enumerate(zip(image_files, image_prompts)):
                    image_basename = os.path.basename(image_file)

                    # Calculate duration for this image
                    if i == 0:
                        duration = prompt['time']
                    else:
                        duration = prompt['time'] - image_prompts[i-1]['time']

                    f.write(f"file '{image_basename}'\n")
                    f.write(f"duration {duration}\n")

                # Add final image with short duration
                if image_files:
                    last_image_basename = os.path.basename(image_files[-1])
                    f.write(f"file '{last_image_basename}'\n")
                    f.write("duration 0.1\n")

        except Exception as e:
            logger.error(f"Failed to create concat file: {e}")
            raise

        # Create video with FFmpeg
        temp_dir = self.get_temp_dir(job_id)
        ffmpeg_command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", "concat.txt",
            "-vsync", "vfr",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "temp_video.mp4"
        ]

        try:
            subprocess.run(
                ffmpeg_command,
                check=True,
                cwd=temp_dir,
                capture_output=True
            )
            logger.info("Image video created successfully")

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg video creation failed: {e}")
            if e.stdout:
                logger.error(f"FFmpeg stdout: {e.stdout.decode()}")
            if e.stderr:
                logger.error(f"FFmpeg stderr: {e.stderr.decode()}")
            raise

        return temp_video

    def _combine_audio_video(self,
                            temp_video: str,
                            audio_file: str,
                            keywords: List[tuple],
                            job_id: str,
                            output_file: str) -> str:
        """Combine video with audio and add keyword overlays.

        Args:
            temp_video: Path to temporary video file
            audio_file: Path to audio file
            keywords: List of (keyword, start_time, end_time) tuples
            job_id: Job identifier
            output_file: Path to final output file

        Returns:
            Path to final video file
        """
        logger = self.get_logger(job_id)
        temp_dir = self.get_temp_dir(job_id)

        # Prepare FFmpeg command
        output_command = [
            "ffmpeg",
            "-i", os.path.basename(temp_video),
            "-i", os.path.basename(audio_file),
            "-c:a", "aac",
            "-shortest"
        ]

        # Add keyword overlay filter if keywords exist
        if keywords:
            drawtext_filter = self._create_keyword_overlay_filter(keywords)
            if drawtext_filter:
                output_command.extend(["-filter_complex", drawtext_filter])

        output_command.append(os.path.basename(output_file))

        try:
            subprocess.run(
                output_command,
                check=True,
                cwd=temp_dir,
                capture_output=True
            )
            logger.info("Audio-video combination completed")

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg audio-video combination failed: {e}")
            if e.stdout:
                logger.error(f"FFmpeg stdout: {e.stdout.decode()}")
            if e.stderr:
                logger.error(f"FFmpeg stderr: {e.stderr.decode()}")
            raise

        return output_file

    def _create_keyword_overlay_filter(self, keywords: List[tuple]) -> Optional[str]:
        """Create FFmpeg filter for keyword overlays.

        Args:
            keywords: List of (keyword, start_time, end_time) tuples

        Returns:
            FFmpeg filter string or None if no keywords
        """
        if not keywords:
            return None

        filter_parts = []
        font_path = "mexcellent_3d.ttf"  # Assume font is in working directory

        for i, (keyword, start_time, end_time) in enumerate(keywords):
            escaped_keyword = keyword.replace("'", "\\'")
            filter_part = (
                f"drawtext=fontfile={font_path}:fontsize=24:fontcolor=white:"
                f"box=1:boxcolor=black@0.5:boxborderw=5:x=(w-tw)/2:y=h-th-20:"
                f"text='{escaped_keyword}':enable='between(t,{start_time},{end_time})'"
            )
            filter_parts.append(filter_part)

        return ",".join(filter_parts)

    def _cleanup_temp_video_files(self,
                                 temp_video: str,
                                 png_image_files: List[str],
                                 original_image_files: List[str],
                                 job_id: str) -> None:
        """Clean up temporary video creation files.

        Args:
            temp_video: Path to temporary video file
            png_image_files: List of PNG image files
            original_image_files: List of original image files
            job_id: Job identifier
        """
        logger = self.get_logger(job_id)

        # Remove temporary video file
        try:
            if os.path.exists(temp_video):
                os.remove(temp_video)
        except OSError as e:
            logger.warning(f"Failed to remove temp video: {e}")

        # Remove concat file
        try:
            concat_file = self.get_temp_file_path(job_id, "concat.txt")
            if os.path.exists(concat_file):
                os.remove(concat_file)
        except OSError as e:
            logger.warning(f"Failed to remove concat file: {e}")

        # Remove converted PNG files (but not original PNGs)
        for png_file in png_image_files:
            if (png_file.lower().endswith('.png') and
                png_file not in original_image_files and
                os.path.exists(png_file)):
                try:
                    os.remove(png_file)
                except OSError as e:
                    logger.warning(f"Failed to remove converted PNG: {e}")

    def _get_default_keywords(self) -> List[tuple]:
        """Get default keywords for video overlay.

        Returns:
            List of default (keyword, start_time, end_time) tuples
        """
        return [
            ("Direktor", 0, 5),
            ("AI Video", 5, 10),
            ("Automation", 10, 15)
        ]

    def get_logger(self, job_id: str):
        """Get stage logger for this job."""
        from ..core.logging_config import get_stage_logger
        return get_stage_logger(self.stage_name, job_id)

    def get_next_stage(self) -> Optional[str]:
        """Get next stage in pipeline (None for final stage)."""
        return None