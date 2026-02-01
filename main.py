import os
import requests
from openai import OpenAI

# Keys
OPENAI_KEY = "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"
DEEPGRAM_KEY = "YOa5a0fac313f6c4ccef637b549c715120d706e5b0UR_DEEPGRAM_API_KEY"

client = OpenAI(api_key=OPENAI_KEY)

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
        user_input = input("👦 You (Type or speak): ")
        if user_input.lower() in ["exit", "bye"]: break
        
        # 1. Brain (GPT-4o-mini is ultra-cheap)
        messages.append({"role": "user", "content": user_input})
        res = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        ai_text = res.choices[0].message.content
        print(f"🤖 AI: {ai_text}")
        
        # 2. Voice (Deepgram is ultra-cheap)
        if get_deepgram_tts(ai_text):
            os.system("afplay output.mp3") # Mac. Use 'start' for Windows.

if __name__ == "__main__":
    chat_loop()