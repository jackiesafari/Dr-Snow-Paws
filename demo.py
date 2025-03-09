import os
import asyncio
from dotenv import load_dotenv
from bot import DoctorSnowLeopardBot
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

class SimpleTTSService:
    def __init__(self, api_key):
        self.client = AsyncOpenAI(api_key=api_key)
        self.voice = "nova"  # Child-friendly voice
    
    async def convert_text_to_speech(self, text):
        response = await self.client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=text
        )
        # Return audio bytes
        return await response.read()

async def run_demo():
    # Initialize TTS service
    tts = SimpleTTSService(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create doctor bot
    doctor = DoctorSnowLeopardBot()
    
    # Test TTS functionality first
    tts_works = await doctor.test_tts()
    if not tts_works:
        print("Warning: TTS service test failed!")
    
    # Simulate a conversation
    responses = [
        "Hi, I'm Sarah!",
        "I'm a little scared about getting a shot today...",
        "I like cats, especially snow leopards!",
        "Thank you for making me feel better!"
    ]
    
    for response in responses:
        print(f"\nChild: {response}")
        
        # Use the OpenAI client directly to generate a response
        # This simulates what would happen in the chat_endpoint method
        completion = await doctor.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Doctor Snow Leopard, a friendly pediatrician snow leopard who helps children feel comfortable in medical settings. Keep your responses short, friendly, and appropriate for children."},
                {"role": "user", "content": response}
            ],
            max_tokens=150
        )
        
        # Get the assistant's response
        result = completion.choices[0].message.content
        
        # Update the emotion based on the response (simple simulation)
        if "happy" in result.lower() or "!" in result:
            doctor.current_emotion = "happy"
        elif "?" in result:
            doctor.current_emotion = "listening"
        else:
            doctor.current_emotion = "caring"
        
        print(f"Doctor Snow Leopard: {result}")
        print(f"Emotion: {doctor.current_emotion}")
        
        # Convert response to speech
        try:
            audio = await tts.convert_text_to_speech(result)
            print("Audio generated successfully")
        except Exception as e:
            print(f"Audio generation error: {e}")

if __name__ == "__main__":
    asyncio.run(run_demo()) 