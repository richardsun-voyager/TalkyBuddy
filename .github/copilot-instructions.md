# TalkyBuddy Copilot Instructions

## Project Overview
TalkyBuddy is a conversational AI educational tool designed for children learning English. It implements a three-stage pipeline: **Speech Recognition → LLM Processing → Speech Synthesis**.

## Architecture & Key Components

### Three Main Implementation Variants
The project has three experimental versions, each iterating on the speech I/O approach:

- **main_whisper.py** - Full audio loop: Records via `sounddevice`, transcribes with OpenAI Whisper, responds with GPT-4o-mini, synthesizes with Deepgram
- **main.py** - Simplified variant: Text input (no recording), same LLM + TTS pipeline
- **main2.py** - Refined version: Text input with better error handling, cross-platform audio playback, `.strip()` safeguard on API keys

### Critical Integration Pattern
The project uses **OpenAI for cognition** (chat completions) and **Deepgram for speech synthesis** - this is a cost optimization choice (Deepgram's Aura model is ~5x cheaper than OpenAI TTS). See how both are initialized at module level:
```python
client = OpenAI(api_key=OPENAI_KEY)
# Deepgram URL: https://api.deepgram.com/v1/speak?model=aura-asteria-en
```

### Data Flow
1. **Input**: Audio recorded (`record_audio()`) or text via `input()`
2. **Transcription**: Whisper API in main_whisper.py, skipped in other variants
3. **Reasoning**: GPT-4o-mini with system prompt defining personality ("friendly teacher", "patient English teacher for kids")
4. **Speech Synthesis**: Deepgram REST API (note: HTTP response.content written directly to .mp3 file)
5. **Playback**: Platform-specific - `afplay` (macOS), `start` (Windows), `mpg123` (Linux)

## Project Conventions & Patterns

### API Key Management
- Keys are hardcoded in files (security risk for production - should use environment variables)
- `DEEPGRAM_KEY.strip()` used in main2.py to handle accidental whitespace
- Same keys appear in multiple files (main2.py has commented fallback)

### Chat Message Structure
Uses OpenAI's message format with persistent conversation history:
```python
messages = [{"role": "system", "content": "...system prompt..."}]
messages.append({"role": "user", "content": user_input})
# ... append assistant response to maintain context
```

### Cross-Platform Compatibility
Audio playback is OS-aware (`sys.platform` checks in main2.py). Always include platform handling when adding features.

### Error Handling Pattern
- Deepgram errors are logged with HTTP status + response text for debugging
- Audio recording errors caught and printed; execution doesn't halt
- Input device discovery loops through available devices (main_whisper.py)

## Critical Developer Workflows

### Running Experiments
```bash
conda activate myLLM  # Project environment (pre-configured)
python main2.py      # Recommended: most refined version
# Or: python main_whisper.py  # For full speech-to-speech testing
```

### Adding Features
1. **New chat behavior**: Modify system prompt in `messages[0]["content"]`
2. **Different voice model**: Change Deepgram URL model parameter (`aura-asteria-en` is current)
3. **Different LLM**: Update `client.chat.completions.create(model=...)` parameter
4. **Recording improvements**: Enhance `record_audio()` and device selection logic

### Testing API Integration
- Deepgram: Check HTTP 200 response; error responses include diagnostic status codes
- OpenAI: Messages array must maintain proper role sequence (system → user → assistant)
- Audio files: .mp3 files are written as binary to disk; ensure filename paths don't have spaces

## Dependencies & External Services
- **OpenAI API**: Whisper (transcription), GPT-4o-mini (chat)
- **Deepgram API**: Aura TTS (speech synthesis via REST)
- **Audio Libraries**: `sounddevice`, `soundfile` (main_whisper.py)
- **Python Core**: `sys`, `os`, `requests`, `wave`

## Key Files Reference
- [main2.py](main2.py) - Best starting point; most polished
- [main_whisper.py](main_whisper.py) - Full audio pipeline; reference for recording logic
- [main.py](main.py) - Minimal variant; good for understanding core chat loop

---
**Note**: This is an experimental/learning project. Hardcoded API keys must be migrated to environment variables before any production use.
