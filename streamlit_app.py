import streamlit as st
import os
import json
import numpy as np
import whisper
import requests
from openai import OpenAI
import tempfile
from pathlib import Path

# Load credentials from config.json
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config

# Page config
st.set_page_config(page_title="TalkyBuddy", page_icon="🎨", layout="wide")
st.title("🎨 TalkyBuddy - Learn English Together")

# Load config and initialize clients
config = load_config()
OPENAI_KEY = config["openai_api_key"]
DEEPGRAM_KEY = config["deepgram_api_key"]
openai_client = OpenAI(api_key=OPENAI_KEY)

# Load Whisper model once
@st.cache_resource
def load_whisper_model():
    try:
        model = whisper.load_model("base")
        return model
    except Exception as e:
        st.error(f"Error loading Whisper model: {e}")
        return None

whisper_model = load_whisper_model()

def transcribe_audio(audio_bytes, sample_rate=16000):
    """Transcribe audio using local Whisper"""
    try:
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            import soundfile as sf
            sf.write(tmp_file.name, audio_bytes, sample_rate)
            tmp_path = tmp_file.name
        
        # Transcribe
        result = whisper_model.transcribe(tmp_path, language="en")
        text = result["text"].strip()
        
        # Clean up
        os.unlink(tmp_path)
        
        return text
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return ""

def get_chat_response(user_text, messages):
    """Get response from GPT-4o-mini"""
    try:
        messages.append({"role": "user", "content": user_text})
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        ai_text = response.choices[0].message.content
        messages.append({"role": "assistant", "content": ai_text})
        return ai_text, messages
    except Exception as e:
        st.error(f"Chat error: {e}")
        return "", messages

def get_deepgram_tts(text):
    """Generate speech using Deepgram"""
    try:
        url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
        headers = {
            "Authorization": f"Token {DEEPGRAM_KEY.strip()}",
            "Content-Type": "application/json"
        }
        payload = {"text": text}
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.content
        elif response.status_code == 401:
            st.error("❌ Deepgram API Key Error - check your config.json")
            return None
        elif response.status_code == 429:
            st.error("❌ Rate limit exceeded - please wait a moment")
            return None
        else:
            st.error(f"❌ Deepgram error: {response.status_code}\n{response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("❌ TTS timeout - Deepgram took too long to respond")
        return None
    except Exception as e:
        st.error(f"❌ TTS error: {str(e)}")
        return None

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a patient, friendly English teacher for kids. Keep responses short and simple. Ask one question at a time."}
    ]

# Sidebar
with st.sidebar:
    st.header("Settings")
    input_mode = st.radio("How do you want to input?", ["🎤 Voice", "⌨️ Text"])
    st.divider()
    st.write("**Recording Settings**")
    duration = st.slider("Recording duration (seconds)", 3, 15, 8)
    st.divider()
    if st.button("🔄 Clear Conversation"):
        st.session_state.messages = [
            {"role": "system", "content": "You are a patient, friendly English teacher for kids. Keep responses short and simple. Ask one question at a time."}
        ]
        st.success("Conversation cleared!")

# Main chat interface
st.write("👋 Welcome! Let's practice English together.")

# Display conversation history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages[1:]:  # Skip system message
        if message["role"] == "user":
            st.chat_message("user").write(f"👦 You: {message['content']}")
        else:
            st.chat_message("assistant").write(f"🤖 Buddy: {message['content']}")

st.divider()

# Input section
if input_mode == "🎤 Voice":
    st.subheader("🎤 Voice Input")
    st.info("📌 Click the microphone icon → Speak → Click stop button → Wait for transcription", icon="ℹ️")
    audio_data = st.audio_input("Click microphone to record", sample_rate=16000)
    
    if audio_data and "last_audio" not in st.session_state:
        st.session_state.last_audio = audio_data
        st.write("🎧 Processing your audio...")
        
        # Convert audio data
        audio_array = np.frombuffer(audio_data.getbuffer(), dtype=np.int16).astype(np.float32) / 32768.0
        
        # Transcribe
        with st.spinner("⏳ Transcribing..."):
            user_text = transcribe_audio(audio_array, sample_rate=16000)
        
        if user_text:
            st.success(f"👦 You: {user_text}")
            
            # Get response
            with st.spinner("⏳ Thinking..."):
                ai_response, st.session_state.messages = get_chat_response(user_text, st.session_state.messages)
            
            if ai_response:
                st.success(f"🤖 Buddy: {ai_response}")
                
                # Generate speech
                with st.spinner("🔊 Generating speech..."):
                    audio_bytes = get_deepgram_tts(ai_response)
                
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.success("✅ Done!")
        else:
            st.warning("⚠️ Couldn't understand. Try again!")
    elif audio_data is None:
        # Reset when user clears the recording
        if "last_audio" in st.session_state:
            del st.session_state.last_audio

else:  # Text input
    st.subheader("⌨️ Text Input")
    user_text = st.text_input("Type your message:")
    
    if st.button("📨 Send Message", use_container_width=True, type="primary"):
        if user_text:
            st.write(f"👦 You: {user_text}")
            
            # Get response
            with st.spinner("⏳ Thinking..."):
                ai_response, st.session_state.messages = get_chat_response(user_text, st.session_state.messages)
            
            if ai_response:
                st.success(f"🤖 Buddy: {ai_response}")
                
                # Generate speech
                with st.spinner("🔊 Generating speech..."):
                    audio_bytes = get_deepgram_tts(ai_response)
                
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.success("✅ Done!")
        else:
            st.warning("Please type a message first!")

# Footer
st.divider()
st.caption("🎨 TalkyBuddy - Your friendly English learning companion")
