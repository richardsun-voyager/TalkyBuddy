import os
import requests
import wave
import sys
from openai import OpenAI
from deepgram import DeepgramClient
# --- Configuration ---
# OPENAI_KEY = "YOUR_OPENAI_KEY"
# DEEPGRAM_KEY = "YOUR_DEEPGRAM_KEY"

OPENAI_KEY = "sk-proj--6-"
DEEPGRAM_KEY = "302e05"
#""


client = OpenAI(api_key=OPENAI_KEY)

def play_audio(filename):
    """Plays audio based on your Operating System."""
    if sys.platform == "darwin":      # Mac
        os.system(f"afplay {filename}")
    elif sys.platform == "win32":     # Windows
        os.system(f"start {filename}")
    else:                             # Linux
        os.system(f"mpg123 {filename}")

def get_deepgram_tts(text, filename="response.mp3"):
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_KEY.strip()}", # .strip() removes accidental spaces
        "Content-Type": "application/json"
    }
    payload = {"text": text}
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        return True
    else:
        # This will tell us EXACTLY why it failed (401, 403, etc.)
        print(f"❌ Deepgram Error: {response.status_code} - {response.text}")
        return False

# def get_deepgram_tts(text, filename="response.mp3"):
    

#     dgclient = DeepgramClient(api_key=DEEPGRAM_KEY)
#     try:
#         response = dgclient.speak.v1.audio.generate(
#             text=text,
#             model="aura-2-thalia-en"
            
#         )
#         print(response)
#         with open(filename, "wb") as audio_file:
#             audio_file.write(response.stream.getvalue())
#         return True
#     except Exception as e:
#         print(f"Error generating audio: {e}")
#         return False

 

def chat_loop():
    # System prompt tailored for children
    messages = [{
        "role": "system", 
        "content": "You are a patient, fun English teacher for kids. Keep sentences short. Ask one simple question at a time to keep the conversation going."
    }]
    
    print("🎨 Buddy is ready! (Type 'exit' to stop)")
    
    while True:
        # Use input for now, or integrate a recording library like 'sounddevice'
        user_input = input("\n👦 You: ")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("🤖 Goodbye! See you next time!")
            break
        
        # 1. Think (Brain)
        messages.append({"role": "user", "content": user_input})
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        ai_text = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": ai_text})
        
        print(f"🤖 Buddy: {ai_text}")
        
        # 2. Speak (Voice)
        if get_deepgram_tts(ai_text):
            play_audio("response.mp3")

if __name__ == "__main__":
    chat_loop()