# Text-to-Speech Implementation for Doctor Snow Leopard

## Architecture Overview

The Doctor Snow Leopard chatbot needs to speak responses to create a more engaging experience. We'll use the Cartesia TTS service which is already referenced in the code but not fully implemented.

## Implementation Steps

### 1. Update `bot.py` to Use Cartesia TTS

```python
# In the DoctorSnowLeopardBot class initialization
def __init__(self):
    self.current_emotion = "neutral"
    self.openai_api_key = os.getenv("OPENAI_API_KEY")
    self.cartesia_api_key = os.getenv("CARTESIA_API_KEY")
    
    # Initialize Cartesia TTS client
    if self.cartesia_api_key and len(self.cartesia_api_key) > 20:
        try:
            self.tts_enabled = True
            self.tts_client = httpx.AsyncClient()
            logger.info("TTS client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS client: {e}")
            self.tts_enabled = False
    else:
        logger.warning("Cartesia API key missing or invalid - TTS disabled")
        self.tts_enabled = False
```

### 2. Add Text-to-Speech Conversion Function

```python
async def convert_text_to_speech(self, text):
    """Convert text to speech using Cartesia API"""
    if not self.tts_enabled:
        logger.warning("TTS is disabled - returning None")
        return None
        
    try:
        response = await self.tts_client.post(
            "https://api.cartesia.ai/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {self.cartesia_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "voice_id": "snow_leopard_child_friendly",  # Use appropriate voice ID
                "output_format": "mp3"
            },
            timeout=10.0
        )
        
        if response.status_code == 200:
            # Base64 encode the audio for sending over WebSocket
            audio_data = response.content
            encoded_audio = base64.b64encode(audio_data).decode('utf-8')
            return encoded_audio
        else:
            logger.error(f"TTS API error: {response.text}")
            return None
    except Exception as e:
        logger.error(f"TTS conversion error: {e}")
        return None
```

### 3. Update Handle Chat Function

```python
# In the handle_chat method, modify the response sending code:
# After getting a response from OpenAI or predefined responses:

# Generate speech for the response
audio_data = await self.convert_text_to_speech(response) if self.tts_enabled else None

# Send response with audio
await websocket.send_json({
    "text": response,
    "audio": audio_data,
    "emotion": self.analyze_emotion(response)
})
```

### 4. Update the Frontend to Play the Audio

The frontend already contains some code to handle audio playback, but we need to ensure it's properly implemented:

```javascript
// In static/index.html, ensure this code is in the ws.onmessage handler:

// Play audio if available
if (data.audio) {
    const audio = new Audio('data:audio/mp3;base64,' + data.audio);
    
    // Sync video with speech
    syncVideoWithSpeech(true);
    
    audio.play();
    
    // When audio ends, update video state
    audio.onended = function() {
        syncVideoWithSpeech(false);
    };
}
```

### 5. Ensure Required Libraries are Installed

Update `requirements.txt`:
```
fastapi==0.109.2
uvicorn==0.27.1
python-dotenv==1.0.1
websockets==12.0
loguru==0.7.2
httpx==0.28.1
base64
```

### 6. Update Environment File

Make sure `.env` file has a valid Cartesia API key:
```
CARTESIA_API_KEY=your_cartesia_api_key_here
```

### 7. Add Content Preprocessing for TTS

Add functions to process text before sending to TTS to improve speech quality:

```python
def preprocess_for_tts(self, text):
    """Prepare text for TTS by adding pauses, emphasis, etc."""
    # Remove asterisks used for actions
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    
    # Add pauses after sentences
    text = text.replace('. ', '. <break time="0.5s"/> ')
    text = text.replace('! ', '! <break time="0.5s"/> ')
    text = text.replace('? ', '? <break time="0.5s"/> ')
    
    # Convert emoji descriptions to actual speech
    text = text.replace('❄️', 'snowflake')
    text = text.replace('🍲', 'soup')
    text = text.replace('🩺', '')
    text = text.replace('😊', '')
    text = text.replace('🐆', '')
    
    return text
```

### 8. Testing the Implementation

1. Start the server with `python main.py`
2. Navigate to `http://localhost:8000`
3. Enter a message and check that:
   - The response text is displayed
   - The audio plays the response
   - The avatar reacts appropriately during speech

## Troubleshooting

If TTS is not working:
1. Check the Cartesia API key is valid
2. Ensure the server logs for any API errors
3. Check browser console for any JavaScript errors
4. Test with a simple hard-coded message to isolate the issue
