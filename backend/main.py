from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import shutil
import os

app = FastAPI()

@app.post("/translate-audio")
async def translate_audio(file: UploadFile = File(...)):
    # Save uploaded file
    audio_path = f"temp_{file.filename}"
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Dummy translated file (you'd replace with real translation logic)
    translated_audio = "translated_output.wav"
    shutil.copy(audio_path, translated_audio)

    # Clean up uploaded file
    os.remove(audio_path)

    return FileResponse(translated_audio, media_type="audio/wav", filename="output.wav")