import os
import requests
import json
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

def record_audio(filename="input.wav", duration=10, rate=16000):
    """Records audio from microphone (cross-platform)"""
    print("Recording...")
    try:
        # Find the first input device with input channels
        devices = sd.query_devices()
        input_device = None
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_device = i
                print(f"Using input device: {device['name']}")
                break
        
        if input_device is None:
            print("No input device found! Available devices:")
            print(devices)
            return
        
        audio = sd.rec(int(duration * rate), samplerate=rate, channels=1, dtype='float32', device=input_device)
        sd.wait()
        sf.write(filename, audio, rate)
        print("Recording saved!")
    except Exception as e:
        print(f"Recording error: {e}")

def transcribe_audio(filename="input.wav"):
    """Converts speech to text using Whisper"""
    with open(filename, "rb") as f:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
    return transcript.text

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
    messages = [{"role": "system", "content": "You are a friendly teacher. Speak simply."}]
    
    while True:
        print("🎤 Listening...")
        record_audio()
        user_input = transcribe_audio()
        print(f"👦 You: {user_input}")
        
        if user_input.lower() in ["exit", "bye"]: break
        
        messages.append({"role": "user", "content": user_input})
        res = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        ai_text = res.choices[0].message.content
        print(f"🤖 AI: {ai_text}")
        
        if get_deepgram_tts(ai_text):
            os.system("afplay output.mp3")

if __name__ == "__main__":
    chat_loop()
