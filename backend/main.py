from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import shutil
import os
import requests
import subprocess
import httpx
import logging, json
from gtts import gTTS
import time

from pydantic import BaseModel
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast

app = FastAPI()

model = MBartForConditionalGeneration.from_pretrained("mbart-dhodfi-model")
tokenizer = MBart50TokenizerFast.from_pretrained("mbart-dhodfi-model")
tokenizer.src_lang = "en_XX"
forced_bos_token_id = tokenizer.lang_code_to_id["en_XX"]

@app.post("/translate-audio")
async def translate_audio(file: UploadFile = File(...)):
    # Save uploaded file
    audio_path = f"{file.filename}"
    print(audio_path)

    file_size_bytes = os.path.getsize(audio_path)
    print(f"File size: {file_size_bytes} bytes")

    video_path = f"{audio_path}.mp4"

    convert_wav_to_mp4(audio_path, video_path)

    file_size_bytes = os.path.getsize(video_path)
    print(f"File size: {file_size_bytes} bytes")
    # Run everything
    video_id = upload_video(video_path)

    sentence = ""
    if video_id:
        task_id = start_transcription(video_id)
        #task_id = "654fe914-060a-4e77-883d-2cba864aca88"
        if task_id:
            success = wait_for_task_completion(video_id, task_id, API_KEY)
            if success:
                response_str = download_transcript(video_id, task_id)
                transcript_data = json.loads(response_str)
                # Build the sentence
                sentence = ""
                for word in transcript_data:
                    if word["type"] == "punctuation":
                        sentence += word["text"]
                    else:
                        if sentence:  # Add space before word unless it's the first word
                            sentence += " "
                        sentence += word["text"]

    print("Final sentence:", sentence)
    inputs = tokenizer(sentence, return_tensors="pt")
    tokens = model.generate(**inputs, forced_bos_token_id=forced_bos_token_id)
    result = tokenizer.decode(tokens[0], skip_special_tokens=True)
    print("translation done")
    print(result)
    tts = gTTS(text=result, lang='gu')
    tts.save("output_gujarati_name.mp3")
    print("done")
    return "ok"

@app.get("/translate-audio")
async def translate_audio():
    print("hello")


VIDEO_PATH = "output_video.mp4"
LANGUAGE_CODE = "en"  # Gujarati

# Step 1: Upload video to ZapCap
def upload_video(file_path):
    print("Uploading video...")
    print(file_path)
    with open(file_path, "rb") as file:
        response = requests.post(
            "https://api.zapcap.ai/videos",
            headers={"x-api-key": API_KEY},
            files={"file": (os.path.basename(file_path), file, "video/mp4")}
        )
    if response.status_code == 201:
        video_id = response.json().get("id")
        print(f"Uploaded successfully: Video ID = {video_id}")
        return video_id
    else:
        print("Upload failed:", response.text)
        return None

# Step 2: Create transcription task
def start_transcription(video_id):
    print("Creating transcription task...")
    data = {
        "autoApprove": True,
        "language": LANGUAGE_CODE,
        "templateId": "a51c5222-47a7-4c37-b052-7b9853d66bf6",
    }
    response = requests.post(
        f"https://api.zapcap.ai/videos/{video_id}/task",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=data,
    )
    if response.status_code == 201:
        task_id = response.json().get("taskId")
        print(f"Task created: Task ID = {task_id}")
        return task_id
    else:
        print("Task creation failed:", response.text)
        return None

# Step 3 (Optional): Check task status
def check_task_status(video_id, task_id):
    response = requests.get(
        f"https://api.zapcap.ai/videos/{video_id}/task/{task_id}",
        headers={"x-api-key": API_KEY},
    )
    print("Task status:", response.json())

def convert_wav_to_mp4(audio_path, output_path="output_video.mp4", image_path=None):
    if not os.path.exists(audio_path):
        print(f"Audio file not found: {audio_path}")
        return

    if image_path and not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        return

    if image_path:
        # Use image as video background
        command = [
            "ffmpeg",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            output_path
        ]
    else:
        # Use black screen background
        command = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", "color=c=black:s=1280x720:d=5",
            "-i", audio_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]

    print("🚀 Running FFmpeg...")
    try:
        subprocess.run(command, check=True)
        print(f"Successfully created video: {output_path}")
    except subprocess.CalledProcessError as e:
        print("Error:", e)

def download_transcript(video_id, task_id, output_file="transcript.txt"):
#     print("Downloading transcript...")
#     url = f"https://api.zapcap.ai/videos/{video_id}/task/{task_id}/transcript"
#
#
#     session = requests.Session()
#     session.headers.clear()  # 🧹 Wipe all default headers
#     session.headers.update({
#             "x-api-key": API_KEY.strip(),
#             "User-Agent": "ZapCapClient/1.0",
#             "Accept": "application/json",
#     })

#     with httpx.Client() as client:
#             response = client.get(url, headers=headers)

 #   response = session.get(url)

# Temporarily doing it from curl
    url = f"https://api.zapcap.ai/videos/{video_id}/task/{task_id}/transcript"
    print(url)
    command = [
            "curl",
            "-s",
            "-X", "GET", url,
            "-H", f"x-api-key: {API_KEY}",
            "-H", "Accept: application/json",
            "-H", "User-Agent: ZapCapClient/1.0"
    ]
    print(command)
    result = subprocess.run(command, capture_output=True, text=True)
    print("Response:", result.stdout)
    return result.stdout

#     if response.status_code == 200:
#         transcript = response.json().get("transcript")
#         if transcript:
#             with open(output_file, "w", encoding="utf-8") as f:
#                 f.write(transcript)
#             print(f"Transcript saved to: {output_file}")
#         else:
#             print("Transcript not found in response.")
#     else:
#         print("Failed to download transcript:", response.text)


def wait_for_task_completion(video_id, task_id, api_key, check_interval=5, timeout=300):
    """
    Polls the ZapCap API every `check_interval` seconds until the task is completed or failed.
    Stops checking after `timeout` seconds.
    """
    start_time = time.time()
    headers = {"x-api-key": api_key}
    status_url = f"https://api.zapcap.ai/videos/{video_id}/task/{task_id}"

    while True:
        response = requests.get(status_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            print(f"ask Status: {status}")

            if status == "completed":
                print("Task completed successfully!")
                return True
            elif status == "failed":
                print("Task failed.")
                return False
        else:
            print("Failed to get task status:", response.text)

        # Check timeout
        if time.time() - start_time > timeout:
            print("Timeout reached. Stopping the check.")
            return False

        time.sleep(check_interval)
