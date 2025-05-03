import sounddevice as sd
from scipy.io.wavfile import write

fs = 44100  # Sample rate
seconds = 3  # Duration of recording

print("🎙️ Start speaking...")
audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
sd.wait()  # Wait until recording is finished
write("gujarati_1.wav", fs, audio)  # Save as WAV file
print("✅ Saved as gujarati_audio.wav")

