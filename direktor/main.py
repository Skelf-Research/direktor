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

# Constants for API endpoints and tokens
REPLICATE_API_TOKEN = "your_replicate_api_token_here"
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
OPENAI_API_KEY = "your_openai_api_key_here"

DISTIL_MODEL = "vaibhavs10/incredibly-fast-whisper:3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c"
BARK_MODEL = "suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787"
FLUX_MODEL = "black-forest-labs/flux-schnell:fe82ca7f3f7efe4ad452c49a31e20d18b31d498bddbc1d61860703e0339406ba"

GPT4_MAX_TOKENS = 8000
GPT4_MODEL = "gpt-4-vision-preview"

client = OpenAI(api_key=OPENAI_API_KEY)
encoding = tiktoken.encoding_for_model(GPT4_MODEL)

def create_temp_dir(input_file):
    with open(input_file, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    temp_dir = os.path.join('temp', file_hash)
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def create_replicate_prediction(model, input_data):
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "version": model,
        "input": input_data,
    }
    response = requests.post(REPLICATE_API_URL, headers=headers, json=data)
    return response.json()

def get_prediction_result(prediction_id):
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    spinner = Halo(text='Waiting for Replicate computation', spinner='dots')
    spinner.start()
    while True:
        response = requests.get(f"{REPLICATE_API_URL}/{prediction_id}", headers=headers)
        data = response.json()
        if data["status"] == "succeeded":
            spinner.stop()
            return data["output"]
        elif data["status"] == "failed":
            spinner.stop()
            raise Exception("Prediction failed")
        time.sleep(1)

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
                    "content": f"Create an engaging single-person podcast script based on the following text:\n\n{chunk}"
                }
            ]
        )
        script_parts.append(response.choices[0].message.content)

    script = " ".join(script_parts)
    with open(script_file, 'w') as f:
        f.write(script)
    return script

def generate_image_prompts(transcript, temp_dir):
    prompts_file = os.path.join(temp_dir, 'image_prompts.json')
    if os.path.exists(prompts_file):
        with open(prompts_file, 'r') as f:
            return json.load(f)

    chunks = split_text(json.dumps(transcript), GPT4_MAX_TOKENS - 1000)
    all_prompts = []

    for chunk in tqdm(chunks, desc="Generating image prompts"):
        response = client.chat.completions.create(
            model=GPT4_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that generates image prompts based on podcast transcripts."
                },
                {
                    "role": "user",
                    "content": f"Generate image prompts with timestamps for the following podcast transcript chunk. Provide one image prompt approximately every 10 seconds. Format the output as a JSON list of objects with 'time' and 'prompt' keys.\n\n{chunk}"
                }
            ]
        )
        prompts = json.loads(response.choices[0].message.content)
        all_prompts.extend(prompts)

    with open(prompts_file, 'w') as f:
        json.dump(all_prompts, f)
    return all_prompts

def generate_audio(text, temp_dir):
    audio_file = os.path.join(temp_dir, 'audio.wav')
    if os.path.exists(audio_file):
        return audio_file

    input_data = {
        "prompt": text,
        "history_prompt": "en_speaker_1",
        "text_temp": 0.7,
        "waveform_temp": 0.7,
    }
    prediction = create_replicate_prediction(BARK_MODEL, input_data)
    audio_url = get_prediction_result(prediction["id"])["audio_out"]
    return download_file(audio_url, audio_file)

def generate_transcript(audio_file, temp_dir):
    transcript_file = os.path.join(temp_dir, 'transcript.json')
    if os.path.exists(transcript_file):
        with open(transcript_file, 'r') as f:
            return json.load(f)

    input_data = {
        "audio": audio_file,
        "task": "transcribe",
        "language": "en",
        "timestamp": "chunk",
    }
    prediction = create_replicate_prediction(DISTIL_MODEL, input_data)
    transcript = get_prediction_result(prediction["id"])
    
    with open(transcript_file, 'w') as f:
        json.dump(transcript, f)
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
        }
        prediction = create_replicate_prediction(FLUX_MODEL, input_data)
        image_url = get_prediction_result(prediction["id"])[0]
        image_file = download_file(image_url, image_file)
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

    filter_file = os.path.join(temp_dir, "filter_complex.txt")
    with open(filter_file, "w") as f:
        f.write("[0:a]aformat=channel_layouts=stereo[aout]\n")
        for i, image in enumerate(image_files):
            f.write(f"[{i+1}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[v{i}]\n")
        
        for i, prompt in enumerate(image_prompts):
            if i == 0:
                f.write(f"[v0]trim=0:{prompt['time']},setpts=PTS-STARTPTS[v{i}out];\n")
            else:
                prev_time = image_prompts[i-1]['time']
                f.write(f"[v{i}]trim=0:{prompt['time']-prev_time},setpts=PTS-STARTPTS[v{i}out];\n")
        
        f.write(f"{''.join([f'[v{i}out]' for i in range(len(image_prompts))])}concat=n={len(image_prompts)}:v=1:a=0[vout]\n")

    cmd = [
        "ffmpeg",
        "-i", audio_file,
    ]
    for image in image_files:
        cmd.extend(["-i", image])
    cmd.extend([
        "-filter_complex_script", filter_file,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_file
    ])

    subprocess.run(cmd, check=True)
    os.remove(filter_file)
    print(f"Video created: {output_file}")
    return output_file

def main(input_file, stage):
    temp_dir = create_temp_dir(input_file)

    with open(input_file, 'r') as f:
        input_text = f.read()

    if stage <= 1:
        print("Stage 1: Generating podcast script...")
        podcast_script = generate_podcast_script(input_text, temp_dir)
    else:
        with open(os.path.join(temp_dir, 'podcast_script.txt'), 'r') as f:
            podcast_script = f.read()

    if stage <= 2:
        print("Stage 2: Generating audio...")
        audio_file = generate_audio(podcast_script, temp_dir)
    else:
        audio_file = os.path.join(temp_dir, 'audio.wav')

    if stage <= 3:
        print("Stage 3: Generating transcript...")
        transcript = generate_transcript(audio_file, temp_dir)
    else:
        with open(os.path.join(temp_dir, 'transcript.json'), 'r') as f:
            transcript = json.load(f)

    if stage <= 4:
        print("Stage 4: Generating image prompts...")
        image_prompts = generate_image_prompts(transcript, temp_dir)
    else:
        with open(os.path.join(temp_dir, 'image_prompts.json'), 'r') as f:
            image_prompts = json.load(f)

    if stage <= 5:
        print("Stage 5: Generating images...")
        image_files = generate_images(image_prompts, temp_dir)
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
