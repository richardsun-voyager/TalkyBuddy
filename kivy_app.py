import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.garden.audiostream import AudioStream
import json
import os
import numpy as np
import threading
import soundfile as sf
import sounddevice as sd
from openai import OpenAI
import requests

# Set window size for testing
Window.size = (400, 800)

class TalkyBuddyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_config()
        self.init_clients()
        self.recording = False
        self.audio_data = None
        
    def load_config(self):
        """Load API keys from config.json"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
            with open(config_path, "r") as f:
                config = json.load(f)
            self.openai_key = config["openai_api_key"]
            self.deepgram_key = config["deepgram_api_key"]
        except Exception as e:
            self.show_error(f"Config error: {e}")
    
    def init_clients(self):
        """Initialize OpenAI client and load Whisper model"""
        try:
            self.openai_client = OpenAI(api_key=self.openai_key)
            self.messages = [
                {"role": "system", "content": "You are a patient, friendly English teacher for kids. Keep responses short and simple. Ask one question at a time."}
            ]
        except Exception as e:
            self.show_error(f"Client init error: {e}")
    
    def build(self):
        """Build the UI"""
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='🎨 TalkyBuddy', size_hint_y=0.1, font_size='24sp', bold=True)
        main_layout.add_widget(title)
        
        # Chat history scroll view
        scroll_view = ScrollView(size_hint=(1, 0.6))
        self.chat_box = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.chat_box.bind(minimum_height=self.chat_box.setter('height'))
        scroll_view.add_widget(self.chat_box)
        main_layout.add_widget(scroll_view)
        
        # Input area
        input_layout = BoxLayout(orientation='vertical', size_hint_y=0.3, spacing=5)
        
        # Text input
        self.text_input = TextInput(
            multiline=False,
            hint_text='Type your message...',
            size_hint_y=0.4
        )
        input_layout.add_widget(self.text_input)
        
        # Button layout
        button_layout = BoxLayout(size_hint_y=0.6, spacing=5)
        
        # Send text button
        send_btn = Button(text='📨 Send', background_color=(0.2, 0.6, 0.8, 1))
        send_btn.bind(on_press=self.on_send_text)
        button_layout.add_widget(send_btn)
        
        # Record button
        self.record_btn = Button(text='🎤 Record', background_color=(0.2, 0.8, 0.6, 1))
        self.record_btn.bind(on_press=self.on_record_toggle)
        button_layout.add_widget(self.record_btn)
        
        # Clear button
        clear_btn = Button(text='🔄 Clear', background_color=(0.8, 0.6, 0.2, 1))
        clear_btn.bind(on_press=self.on_clear)
        button_layout.add_widget(clear_btn)
        
        input_layout.add_widget(button_layout)
        main_layout.add_widget(input_layout)
        
        return main_layout
    
    def add_message(self, role, text):
        """Add message to chat display"""
        if role == "user":
            msg_label = Label(
                text=f'👦 You: {text}',
                size_hint_y=None,
                height=100,
                text_size=(300, None)
            )
            msg_label.color = (0.2, 0.6, 1, 1)
        else:
            msg_label = Label(
                text=f'🤖 Buddy: {text}',
                size_hint_y=None,
                height=100,
                text_size=(300, None)
            )
            msg_label.color = (0.2, 0.8, 0.6, 1)
        
        self.chat_box.add_widget(msg_label)
    
    def show_error(self, error_text):
        """Display error message"""
        error_label = Label(
            text=f'❌ Error: {error_text}',
            size_hint_y=None,
            height=50,
            color=(1, 0.2, 0.2, 1)
        )
        self.chat_box.add_widget(error_label)
    
    def on_send_text(self, instance):
        """Handle text message submission"""
        text = self.text_input.text.strip()
        if not text:
            return
        
        self.text_input.text = ""
        self.add_message("user", text)
        
        # Process in background thread
        thread = threading.Thread(target=self.process_text, args=(text,))
        thread.daemon = True
        thread.start()
    
    def process_text(self, text):
        """Process text through chat and TTS"""
        try:
            # Get chat response
            self.messages.append({"role": "user", "content": text})
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.messages
            )
            ai_text = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": ai_text})
            
            # Display response
            self.add_message("assistant", ai_text)
            
            # Generate speech
            self.generate_and_play_speech(ai_text)
        except Exception as e:
            self.show_error(str(e))
    
    def on_record_toggle(self, instance):
        """Toggle recording on/off"""
        if not self.recording:
            self.recording = True
            self.record_btn.text = "⏹️ Stop"
            self.record_btn.background_color = (0.8, 0.2, 0.2, 1)
            
            # Record in background
            thread = threading.Thread(target=self.record_audio)
            thread.daemon = True
            thread.start()
        else:
            self.recording = False
            self.record_btn.text = "🎤 Record"
            self.record_btn.background_color = (0.2, 0.8, 0.6, 1)
    
    def record_audio(self):
        """Record audio from microphone"""
        try:
            duration = 8
            rate = 16000
            
            self.add_message("user", "🎤 Recording...")
            
            audio = sd.rec(int(duration * rate), samplerate=rate, channels=1, dtype='float32')
            sd.wait()
            
            # Check audio level
            max_amplitude = np.max(np.abs(audio))
            if max_amplitude < 0.001:
                self.show_error("Very quiet - speak louder!")
                return
            
            # Transcribe
            self.add_message("user", "⏳ Transcribing...")
            
            # For now, use text input as fallback (Whisper requires ffmpeg on mobile)
            self.add_message("user", "📝 (Using text input - Whisper not available on mobile yet)")
            
        except Exception as e:
            self.show_error(str(e))
    
    def generate_and_play_speech(self, text):
        """Generate speech from Deepgram and play it"""
        try:
            url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
            headers = {
                "Authorization": f"Token {self.deepgram_key.strip()}",
                "Content-Type": "application/json"
            }
            payload = {"text": text}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                # Save and play audio
                audio_file = "response_mobile.mp3"
                with open(audio_file, "wb") as f:
                    f.write(response.content)
                
                # Note: Playing audio on Android requires additional setup
                self.add_message("assistant", "🔊 [Audio response generated]")
            else:
                self.show_error(f"TTS error: {response.status_code}")
        except Exception as e:
            self.show_error(f"Speech error: {str(e)}")
    
    def on_clear(self, instance):
        """Clear chat history"""
        self.chat_box.clear_widgets()
        self.messages = [
            {"role": "system", "content": "You are a patient, friendly English teacher for kids. Keep responses short and simple. Ask one question at a time."}
        ]
        self.add_message("assistant", "👋 Conversation cleared!")

if __name__ == '__main__':
    TalkyBuddyApp().run()
