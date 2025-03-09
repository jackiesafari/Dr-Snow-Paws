import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_openai_tts():
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("API Key loaded:", os.getenv("OPENAI_API_KEY")[:10] + "...")

        # Try to create a speech file
        print("Testing TTS service...")
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input="Hello, this is a test message."
        )

        # If we get here, it worked
        print("✅ TTS service is working!")
        
        # Save the audio to test.mp3
        response.stream_to_file("test.mp3")
        print("✅ Audio file saved as test.mp3")

    except Exception as e:
        print("❌ Error:", str(e))

if __name__ == "__main__":
    test_openai_tts() 