import os
import requests
import json
import numpy as np
from openai import OpenAI
import sounddevice as sd
import soundfile as sf

# Load credentials from config.json
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config

config = load_config()
OPENAI_KEY = config["openai_api_key"]
DEEPGRAM_KEY = config["deepgram_api_key"]

client = OpenAI(api_key=OPENAI_KEY)

def record_audio(filename="input.wav", duration=8, rate=16000):
    """
    Records audio from microphone with fixed duration.
    Uses simpler, more reliable recording approach.
    
    Args:
        filename: Output file path
        duration: Recording duration in seconds
        rate: Sample rate in Hz
    """
    print(f"🎤 Recording for {duration} seconds... speak now!")
    try:
        # Find the first input device with input channels
        devices = sd.query_devices()
        input_device = None
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_device = i
                print(f"   Using device: {device['name']}")
                break
        
        if input_device is None:
            print("❌ No input device found!")
            return
        
        # Simple fixed-duration recording
        print("   Listening...")
        audio = sd.rec(int(duration * rate), samplerate=rate, channels=1, dtype='float32', device=input_device)
        sd.wait()
        
        # Check if we got any audio
        max_amplitude = np.max(np.abs(audio))
        print(f"   Audio level: {max_amplitude:.4f}")
        
        if max_amplitude < 0.001:
            print("⚠️  Very quiet audio detected. Check your microphone!")
        
        sf.write(filename, audio, rate)
        print("✅ Recording saved!")
        
    except Exception as e:
        print(f"❌ Recording error: {e}")

def transcribe_audio(filename="input.wav"):
    """Converts speech to text using Whisper with progress feedback"""
    print("⏳ Transcribing...")
    try:
        with open(filename, "rb") as f:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
        return transcript.text
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return ""

def get_deepgram_tts(text, filename="output.mp3"):
    """Uses Deepgram's Aura-2 for 5x cheaper speech than OpenAI"""
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"text": text}
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        return True
    return False

def chat_loop():
    messages = [{"role": "system", "content": "You are a patient, friendly English teacher for kids. Keep responses short and simple. Ask one question at a time."}]
    
    print("🎨 Welcome to TalkyBuddy! (Say 'exit' or 'bye' to quit)\n")
    
    while True:
        record_audio()
        user_input = transcribe_audio()
        
        if not user_input:
            print("❌ Couldn't understand. Try again!\n")
            continue
            
        print(f"👦 You: {user_input}\n")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("🤖 Goodbye! See you next time!")
            break
        
        print("⏳ Thinking...")
        messages.append({"role": "user", "content": user_input})
        res = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        ai_text = res.choices[0].message.content
        messages.append({"role": "assistant", "content": ai_text})
        print(f"🤖 Buddy: {ai_text}")
        
        print("🔊 Speaking...")
        if get_deepgram_tts(ai_text):
            os.system("afplay output.mp3")
        print()

if __name__ == "__main__":
    chat_loop()
