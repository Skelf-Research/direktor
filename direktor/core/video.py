"""
Video creation module for Direktor.

This module handles combining audio and images into the final video.
"""

import os
import subprocess

from PIL import Image

from .config import FONT_PATH


def create_video(audio_file, image_files, image_prompts, temp_dir, keywords=None):
    """
    Create a video from audio and images with optional keyword overlays.

    Args:
        audio_file: Path to the audio file
        image_files: List of paths to image files
        image_prompts: List of image prompts with timestamps
        temp_dir: Temporary directory for intermediate files
        keywords: Optional list of (keyword, start_time, end_time) tuples for overlays

    Returns:
        Path to the output video file, or None on failure
    """
    output_file = os.path.join(temp_dir, "output.mp4")
    if os.path.exists(output_file):
        print(f"Video already exists: {output_file}")
        return output_file

    # Convert WebP images to PNG
    png_image_files = []
    for image_file in image_files:
        if image_file.lower().endswith(".webp"):
            png_file = os.path.join(
                temp_dir, os.path.splitext(os.path.basename(image_file))[0] + ".png"
            )
            try:
                with Image.open(image_file) as img:
                    img.save(png_file, "PNG")
                png_image_files.append(png_file)
            except Exception as e:
                print(f"Warning: Failed to convert {image_file} to PNG: {e}")
                png_image_files.append(image_file)
        else:
            png_image_files.append(image_file)

    # Create a temporary file for the concat demuxer
    concat_file = os.path.join(temp_dir, "concat.txt")

    try:
        with open(concat_file, "w") as f:
            for i, (image_file, prompt) in enumerate(
                zip(png_image_files, image_prompts)
            ):
                image_basename = os.path.basename(image_file)
                duration = (
                    prompt["time"]
                    if i == 0
                    else prompt["time"] - image_prompts[i - 1]["time"]
                )
                f.write(f"file '{image_basename}'\n")
                f.write(f"duration {duration}\n")

            if png_image_files:
                last_image_basename = os.path.basename(png_image_files[-1])
                f.write(f"file '{last_image_basename}'\n")
                f.write("duration 0.1\n")
    except Exception as e:
        print(f"Error creating concat file: {e}")
        return None

    # Create a video from the images
    temp_video = os.path.join(temp_dir, "temp_video.mp4")

    ffmpeg_command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", "concat.txt",
        "-vsync", "vfr",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "temp_video.mp4",
    ]

    try:
        subprocess.run(ffmpeg_command, check=True, cwd=temp_dir, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg video creation failed: {e}")
        print(f"FFmpeg stdout: {e.stdout.decode() if e.stdout else 'None'}")
        print(f"FFmpeg stderr: {e.stderr.decode() if e.stderr else 'None'}")
        return None

    # Prepare the drawtext filter for keyword overlay
    drawtext_filter = ""
    if keywords:
        for i, (keyword, start_time, end_time) in enumerate(keywords):
            escaped_keyword = keyword.replace("'", "\\'")
            drawtext_filter += (
                f"drawtext=fontfile={FONT_PATH}:fontsize=24:fontcolor=white:"
                f"box=1:boxcolor=black@0.5:boxborderw=5:x=(w-tw)/2:y=h-th-20:"
                f"text='{escaped_keyword}':enable='between(t,{start_time},{end_time})'"
            )
            if i < len(keywords) - 1:
                drawtext_filter += ","

    # Combine the video with the audio and add keyword overlay
    output_command = [
        "ffmpeg",
        "-i", "temp_video.mp4",
        "-i", os.path.basename(audio_file),
        "-c:a", "aac",
        "-shortest",
        "output.mp4",
    ]

    # Add drawtext filter if it exists
    if drawtext_filter:
        output_command.insert(-4, "-filter_complex")
        output_command.insert(-4, drawtext_filter)

    try:
        subprocess.run(output_command, check=True, cwd=temp_dir, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg audio-video combination failed: {e}")
        print(f"FFmpeg stdout: {e.stdout.decode() if e.stdout else 'None'}")
        print(f"FFmpeg stderr: {e.stderr.decode() if e.stderr else 'None'}")
        return None

    # Clean up temporary files
    try:
        if os.path.exists(concat_file):
            os.remove(concat_file)
        if os.path.exists(temp_video):
            os.remove(temp_video)
        for png_file in png_image_files:
            if (
                png_file.lower().endswith(".png")
                and png_file not in image_files
                and os.path.exists(png_file)
            ):
                os.remove(png_file)
    except OSError as e:
        print(f"Warning: Failed to clean up temporary files: {e}")

    print(f"Video created: {output_file}")
    return output_file
