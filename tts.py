import base64
from openai import AsyncOpenAI

async def convert_text_to_speech(text: str, client: AsyncOpenAI, voice: str = "shimmer", language: str = "en") -> str:
    """Convert text to speech using OpenAI's TTS API."""
    try:
        # Select appropriate voice for language
        if language == "es":
            voice = "nova"  # nova for Spanish
        else:
            voice = "shimmer"  # shimmer for English - warm and friendly tone
        
        response = await client.audio.speech.create(
            model="tts-1-hd",  # Using HD model for better quality
            voice=voice,
            input=text,
            speed=0.95  # Slightly slower for more warmth and clarity
        )
        
        # Convert to base64 for sending over websocket
        audio_bytes = response.read()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        return audio_base64
        
    except Exception as e:
        print(f"Error in TTS conversion: {e}")
        return None