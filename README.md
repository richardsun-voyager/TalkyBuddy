# TalkyBuddy

A conversational AI educational tool for children learning English. TalkyBuddy listens, understands, and responds naturally—combining speech recognition, language processing, and speech synthesis into an interactive learning experience.

## Features

- **Speech-to-Speech Pipeline**: Records audio → transcribes with Whisper → responds with GPT-4o-mini → speaks with Deepgram
- **Child-Friendly Personality**: Tailored system prompts for patient, simple English instruction
- **Cost-Optimized**: Uses Deepgram for TTS (~5x cheaper than OpenAI)
- **Cross-Platform Audio**: Works on macOS, Windows, and Linux
- **Conversation Context**: Maintains message history for coherent multi-turn dialogues

## Quick Start

### Prerequisites
- Python 3.8+
- Conda (recommended) or pip
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [Deepgram API Key](https://console.deepgram.com/)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd TalkyBuddy
   ```

2. **Set up the environment**
   ```bash
   conda activate myLLM
   # Or create a new environment:
   conda create -n talkybuddy python=3.10
   conda activate talkybuddy
   ```

3. **Install dependencies**
   ```bash
   pip install openai requests sounddevice soundfile deepgram-sdk
   ```

4. **Add API Keys**
   
   Edit the top of your chosen script and set:
   ```python
   OPENAI_KEY = "your-openai-key-here"
   DEEPGRAM_KEY = "your-deepgram-key-here"
   ```
   
   > ⚠️ **Security Note**: For production, use environment variables instead of hardcoding keys.

### Running TalkyBuddy

Choose one of three variants:

**Option 1: Full Audio Pipeline (Recommended for Demo)**
```bash
python main_whisper.py
```
Records audio from your microphone, transcribes speech, generates responses, and plays them back.

**Option 2: Text Input (Quick Testing)**
```bash
python main2.py
```
Type messages instead of speaking; best for rapid iteration and debugging.

**Option 3: Minimal Variant**
```bash
python main.py
```
Simple text-based chat loop; good for understanding core functionality.

## Project Structure

```
TalkyBuddy/
├── main_whisper.py    # Full audio pipeline with Whisper transcription
├── main2.py           # Refined text input variant with better error handling
├── main.py            # Minimal chat implementation
├── input.wav          # Recorded audio sample
├── output.mp3         # Generated speech output
└── .github/
    └── copilot-instructions.md  # AI agent guidelines
```

## Architecture

### Data Flow
1. **Input Stage**: User speaks or types
2. **Transcription**: Whisper API converts speech to text (main_whisper.py only)
3. **Reasoning**: GPT-4o-mini generates contextual responses
4. **Synthesis**: Deepgram Aura model converts response text to speech
5. **Playback**: Platform-specific audio player (afplay/start/mpg123)

### Key Functions

| Function | Purpose | Used In |
|----------|---------|---------|
| `record_audio()` | Captures audio from microphone with device detection | main_whisper.py |
| `transcribe_audio()` | Calls Whisper API to convert speech to text | main_whisper.py |
| `get_deepgram_tts()` | Calls Deepgram REST API to synthesize speech | All variants |
| `play_audio()` | Cross-platform audio playback | main2.py |
| `chat_loop()` | Main conversation loop with message history | All variants |

## Configuration

### Change the AI Personality
Edit the system prompt in `chat_loop()`:
```python
messages = [{
    "role": "system", 
    "content": "You are a patient, fun English teacher for kids..."
}]
```

### Use a Different Voice Model
Update the Deepgram URL in `get_deepgram_tts()`:
```python
url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
# Try other models like: aura-athena-en, aura-angus-en, etc.
```

### Switch LLM Models
Modify the model parameter in `chat_loop()`:
```python
completion = client.chat.completions.create(
    model="gpt-4o-mini",  # Try: gpt-4o, gpt-3.5-turbo, etc.
    messages=messages
)
```

## Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| `openai` | GPT-4o-mini chat & Whisper transcription | Latest |
| `requests` | HTTP requests to Deepgram API | Latest |
| `sounddevice` | Cross-platform audio recording | 0.4.5+ |
| `soundfile` | WAV file I/O for recording | 0.12+ |
| `deepgram-sdk` | Deepgram client library (optional) | Latest |

## Troubleshooting

### Deepgram Error: 401/403
- Verify your API key is correct and not expired
- Check that key has whitespace (main2.py uses `.strip()`)

### Audio Recording Fails
- Run `python -c "import sounddevice; print(sounddevice.query_devices())"` to see available input devices
- main_whisper.py auto-detects the first device with input channels

### No Audio Playback
- macOS: Ensure `afplay` is available (built-in)
- Windows: Ensure MP3 codec is installed or use a different format
- Linux: Install `mpg123` via `apt install mpg123`

### OpenAI Rate Limits
- Requests are metered by OpenAI; monitor API usage on your account dashboard
- Consider adding delays between requests during heavy testing

## Contributing

This is an experimental learning project. Feel free to iterate on:
- System prompts for different age groups
- Integration with speech-to-text alternatives (Google Cloud Speech-to-Text, etc.)
- Persistent conversation storage
- Multi-language support

## Future Roadmap

- [ ] Migrate hardcoded API keys to environment variables
- [ ] Add conversation history logging
- [ ] Support for different Deepgram voices
- [ ] Lesson progression tracking
- [ ] Vocabulary level customization

## License

Open for educational use. Please comply with OpenAI and Deepgram terms of service.

---

**Made with ❤️ for English learners everywhere.**
