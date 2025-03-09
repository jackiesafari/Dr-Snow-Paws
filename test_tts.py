import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

async def test_tts():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # The create method is async, need to await it
    response = await client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input="Hello! I'm Doctor Snow Leopard, and I'm here to help you feel better."
    )
    
    # Save the audio file
    with open("test.mp3", "wb") as file:
        file.write(response.content)
    
    print("Audio file 'test.mp3' created successfully!")

if __name__ == "__main__":
    asyncio.run(test_tts()) 