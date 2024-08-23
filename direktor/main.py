import argparse
import json
import time
import requests
import subprocess
import os
import hashlib
from openai import OpenAI
import tiktoken
from tqdm import tqdm
from halo import Halo
from dotenv import load_dotenv
import replicate
import boto3
from botocore.client import Config

# Load environment variables from .env file
load_dotenv()

# Constants for API endpoints and tokens
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DISTIL_MODEL = os.getenv("DISTIL_MODEL")
BARK_MODEL = os.getenv("BARK_MODEL")
FLUX_MODEL = os.getenv("FLUX_MODEL")

GPT4_MAX_TOKENS = int(os.getenv("GPT4_MAX_TOKENS", 8000))
GPT4_MODEL = os.getenv("GPT4_MODEL")

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_ENDPOINT_URL = "https://s3.us-west-000.backblazeb2.com"
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

client = OpenAI(api_key=OPENAI_API_KEY)
encoding = tiktoken.encoding_for_model(GPT4_MODEL)

def create_temp_dir(input_file):
    with open(input_file, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    temp_dir = os.path.join('temp', file_hash)
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def run_replicate_model(model, input_data):
    spinner = Halo(text='Running Replicate model', spinner='dots')
    spinner.start()
    
    prediction = replicate.predictions.create(
        model=model,
        input=input_data
    )
    
    while prediction.status not in {"succeeded", "failed", "canceled"}:
        time.sleep(1)
        prediction.reload()
    
    spinner.stop()
    
    if prediction.status == "succeeded":
        return prediction.output
    else:
        raise Exception(f"Prediction failed with status: {prediction.status}")

def split_text(text, max_tokens):
    tokens = encoding.encode(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for token in tokens:
        if current_length + 1 > max_tokens:
            chunks.append(encoding.decode(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(token)
        current_length += 1

    if current_chunk:
        chunks.append(encoding.decode(current_chunk))

    return chunks

def generate_podcast_script(input_text, temp_dir):
    script_file = os.path.join(temp_dir, 'podcast_script.txt')
    if os.path.exists(script_file):
        with open(script_file, 'r') as f:
            return f.read()

    chunks = split_text(input_text, GPT4_MAX_TOKENS - 1000)
    script_parts = []

    for chunk in tqdm(chunks, desc="Generating podcast script"):
        response = client.chat.completions.create(
            model=GPT4_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that creates engaging single-person podcast scripts from input text."
                },
                {
                    "role": "user",
                    "content": f"Create an engaging single-person podcast script based on the following text, please do not add any additional text like host, pauses etc.:\n\n{chunk}"
                }
            ]
        )
        script_parts.append(response.choices[0].message.content)

    script = " ".join(script_parts)
    with open(script_file, 'w') as f:
        f.write(script)
    return script

def aggregate_chunks(chunks, target_duration=30):
    aggregated_chunks = []
    current_chunk = {"text": "", "timestamp": [chunks[0]["timestamp"][0], 0]}
    
    for chunk in chunks:
        if chunk["timestamp"][1] - current_chunk["timestamp"][0] > target_duration:
            current_chunk["timestamp"][1] = chunk["timestamp"][0]
            aggregated_chunks.append(current_chunk)
            current_chunk = {"text": chunk["text"], "timestamp": chunk["timestamp"]}
        else:
            current_chunk["text"] += " " + chunk["text"]
            current_chunk["timestamp"][1] = chunk["timestamp"][1]
    
    if current_chunk["text"]:
        aggregated_chunks.append(current_chunk)
    
    return aggregated_chunks

def generate_image_prompts(transcript, temp_dir):
    prompts_file = os.path.join(temp_dir, 'image_prompts.json')
    if os.path.exists(prompts_file):
        with open(prompts_file, 'r') as f:
            return json.load(f)

    client = OpenAI()
    all_prompts = []

    # Aggregate chunks to approximately 30-second segments
    aggregated_chunks = aggregate_chunks(transcript['chunks'], target_duration=30)

    for chunk in tqdm(aggregated_chunks, desc="Generating image prompts"):
        response = client.chat.completions.create(
            model=GPT4_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that generates image prompts based on podcast transcripts. Generate a single, vivid image prompt that captures the main theme or most striking visual element from the given text."
                },
                {
                    "role": "user",
                    "content": f"Generate an stable diffusion generation prompt for the following podcast transcript segment:\n\nText: {chunk['text']}\nTimestamp: {chunk['timestamp'][0]} - {chunk['timestamp'][1]}"
                }
            ]
        )
        
        prompt = response.choices[0].message.content.strip()
        all_prompts.append({
            "time": chunk['timestamp'][0],
            "prompt": prompt
        })

    with open(prompts_file, 'w') as f:
        json.dump(all_prompts, f)
    
    return all_prompts

import re

def split_into_sentences(text):
    # Split the text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return sentences

def group_sentences(sentences, max_chars=100):
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

import logging

logging.basicConfig(filename='audio_generation.log', level=logging.ERROR)

def generate_audio(text, temp_dir):
    audio_file = os.path.join(temp_dir, 'audio.mp3')
    if os.path.exists(audio_file):
        return audio_file

    # Split the text into sentences and group them into chunks
    sentences = split_into_sentences(text)
    chunks = group_sentences(sentences, max_chars=150)

    all_audio_files = []
    failed_chunks = []

    for i, chunk in enumerate(chunks):
        chunk_audio_file = f'audio_chunk_{i}.mp3'
        full_chunk_audio_path = os.path.join(temp_dir, chunk_audio_file)
        
        input_data = {
            "text": chunk,
            "alpha": 0.3,
            "beta": 0.7,
            "diffusion_steps": 10,
            "embedding_scale": 1.5,
            "seed": 0
        }
        
        try:
            output = run_replicate_model(BARK_MODEL, input_data)
            download_file(output, full_chunk_audio_path)
            all_audio_files.append(chunk_audio_file)
        except Exception as e:
            logging.error(f"Failed to generate audio for chunk {i}: {str(e)}")
            logging.error(f"Chunk text: {chunk}")
            logging.error(f"Input parameters: {input_data}")
            failed_chunks.append(i)

    # Remove failed chunks from the list
    for i in failed_chunks[::-1]:
        del chunks[i]

    # If there's more than one successful chunk, concatenate them
    if len(all_audio_files) > 1:
        concat_list_file = "concat_list.txt"
        full_concat_list_path = os.path.join(temp_dir, concat_list_file)
        with open(full_concat_list_path, "w") as f:
            for audio_file in all_audio_files:
                f.write(f"file '{audio_file}'\n")

        subprocess.run([
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_file,
            "-c", "copy",
            "audio.mp3"
        ], check=True, cwd=temp_dir)

        # Clean up individual chunk files
        for chunk_file in all_audio_files:
            os.remove(os.path.join(temp_dir, chunk_file))
        os.remove(full_concat_list_path)
    elif len(all_audio_files) == 1:
        # If there's only one chunk, just rename it
        os.rename(os.path.join(temp_dir, all_audio_files[0]), audio_file)
    else:
        logging.error("No audio chunks were successfully generated.")
        return None

    return audio_file

def upload_to_r2(file_path, object_name):
    print(AWS_ENDPOINT_URL)
    s3 = boto3.client('s3',
                      endpoint_url=AWS_ENDPOINT_URL,
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      config=Config(signature_version='s3v4'),
                      region_name='auto')

    try:
        s3.upload_file(file_path, AWS_BUCKET_NAME, object_name)
        url = s3.generate_presigned_url('get_object',
                                        Params={'Bucket': AWS_BUCKET_NAME,
                                                'Key': object_name},
                                        ExpiresIn=3600)  # 1 hour in seconds
        return url
    except Exception as e:
        print(f"Failed to upload file to R2: {e}")
        return None

def generate_transcript(audio_file, temp_dir):
    transcript_file = os.path.join(temp_dir, 'transcript.json')
    if os.path.exists(transcript_file):
        with open(transcript_file, 'r') as f:
            return json.load(f)

    # Generate a hash for the audio file name
    with open(audio_file, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    # Convert audio to WAV format
    wav_file = os.path.join(temp_dir, f"{file_hash}.wav")
    subprocess.run([
        "ffmpeg",
        "-i", audio_file,
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        wav_file
    ], check=True)

    # Upload WAV file to Cloudflare R2
    AWS_object_name = f"{file_hash}.wav"
    audio_url = upload_to_r2(wav_file, AWS_object_name)

    if not audio_url:
        print("Failed to upload audio file to R2. Cannot generate transcript.")
        return None

    input_data = {
        "audio": audio_url,
        "task": "transcribe",
        "language": "english",
        "timestamp": "chunk",
    }
    transcript = run_replicate_model(DISTIL_MODEL, input_data)
    
    with open(transcript_file, 'w') as f:
        json.dump(transcript, f)

    # Clean up the temporary WAV file
    os.remove(wav_file)

    return transcript

def generate_images(prompts, temp_dir):
    image_dir = os.path.join(temp_dir, 'images')
    os.makedirs(image_dir, exist_ok=True)
    image_files = []

    for i, prompt in enumerate(tqdm(prompts, desc="Generating images")):
        image_file = os.path.join(image_dir, f'image_{i}.webp')
        if os.path.exists(image_file):
            image_files.append(image_file)
            continue

        input_data = {
            "prompt": prompt['prompt'],
            "num_outputs": 1,
            "aspect_ratio": "16:9",
            "output_format": "webp",
            "output_quality": 80,
            "seed":0,
            "disable_safety_checker": True
        }
        output = run_replicate_model(FLUX_MODEL, input_data)
        image_file = download_file(output[0], image_file)
        image_files.append(image_file)

    return image_files

def download_file(url, local_filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        block_size = 8192
        with open(local_filename, 'wb') as f, tqdm(
            desc=os.path.basename(local_filename),
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for data in r.iter_content(block_size):
                size = f.write(data)
                progress_bar.update(size)
    return local_filename

def create_video(audio_file, image_files, image_prompts, temp_dir):
    output_file = os.path.join(temp_dir, "output.mp4")
    if os.path.exists(output_file):
        print(f"Video already exists: {output_file}")
        return output_file

    # Create a temporary file for the concat demuxer
    concat_file = os.path.join(temp_dir, "concat.txt")
    
    with open(concat_file, "w") as f:
        for i, (image_file, prompt) in enumerate(zip(image_files, image_prompts)):
            # Get the path relative to the images directory
            relative_path = os.path.relpath(image_file, temp_dir)
            duration = prompt['time'] if i == 0 else prompt['time'] - image_prompts[i-1]['time']
            f.write(f"file '{relative_path}'\n")
            f.write(f"duration {duration}\n")
        
        # Write the last image file again with a small duration to ensure it's shown
        relative_path = os.path.relpath(image_files[-1], os.path.join(temp_dir, 'images'))
        f.write(f"file '{relative_path}'\n")
        f.write("duration 0.1\n")

    # First, create a video from the images
    temp_video = os.path.join(temp_dir, "temp_video.mp4")
    subprocess.run([
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-vsync", "vfr",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        temp_video
    ], check=True, cwd=os.path.join(temp_dir, 'images'))  # Set working directory to images folder

    # Then, combine the video with the audio
    subprocess.run([
        "ffmpeg",
        "-i", os.path.relpath(temp_video, os.path.join(temp_dir, 'images')),
        "-i", os.path.relpath(audio_file, os.path.join(temp_dir, 'images')),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        os.path.relpath(output_file, os.path.join(temp_dir, 'images'))
    ], check=True, cwd=os.path.join(temp_dir, 'images'))  # Set working directory to images folder

    # Clean up temporary files
    os.remove(concat_file)
    os.remove(temp_video)

    print(f"Video created: {output_file}")
    return output_file

def main(input_file, stage):
    # Check if required environment variables are set
    required_vars = ["REPLICATE_API_TOKEN", "OPENAI_API_KEY", "DISTIL_MODEL", "BARK_MODEL", "FLUX_MODEL", "GPT4_MODEL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: The following required environment variables are not set: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file.")
        return

    temp_dir = create_temp_dir(input_file)

    with open(input_file, 'r') as f:
        input_text = f.read()

    if stage <= 1:
        print("Stage 1: Generating podcast script...")
        podcast_script = generate_podcast_script(input_text, temp_dir)
        return
    else:
        with open(os.path.join(temp_dir, 'podcast_script.txt'), 'r') as f:
            podcast_script = f.read()

    if stage <= 2:
        print("Stage 2: Generating audio...")
        audio_file = generate_audio(podcast_script, temp_dir)
        return
    else:
        audio_file = os.path.join(temp_dir, 'audio.mp3')

    if stage <= 3:
        print("Stage 3: Generating transcript...")
        transcript = generate_transcript(audio_file, temp_dir)
        return
    else:
        with open(os.path.join(temp_dir, 'transcript.json'), 'r') as f:
            transcript = json.load(f)

    if stage <= 4:
        print("Stage 4: Generating image prompts...")
        image_prompts = generate_image_prompts(transcript, temp_dir)
        return
    else:
        with open(os.path.join(temp_dir, 'image_prompts.json'), 'r') as f:
            image_prompts = json.load(f)

    if stage <= 5:
        print("Stage 5: Generating images...")
        image_files = generate_images(image_prompts, temp_dir)
        return
    else:
        image_dir = os.path.join(temp_dir, 'images')
        image_files = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith('.webp')]

    if stage <= 6:
        print("Stage 6: Creating video...")
        output_file = create_video(audio_file, image_files, image_prompts, temp_dir)
        print(f"Video created: {output_file}")
    else:
        print(f"All stages completed. Video should be in {temp_dir}")

    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video from text input.")
    parser.add_argument("input_file", help="Path to the input text file")
    parser.add_argument("--stage", type=int, choices=range(1, 7), default=6, help="Stage to start from (1-6)")
    args = parser.parse_args()

    main(args.input_file, args.stage)