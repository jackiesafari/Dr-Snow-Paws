import os
import asyncio
from dotenv import load_dotenv
from bot import DoctorSnowLeopardProcessor
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.openai import OpenAILLMContext

# Load environment variables
load_dotenv()

async def run_demo():
    # Initialize services
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="CHILD_FRIENDLY_VOICE_ID"
    )
    
    # Create context
    context = OpenAILLMContext()
    doctor = DoctorSnowLeopardProcessor(context)
    
    # Simulate a conversation
    responses = [
        "Hi, I'm Sarah!",
        "I'm a little scared about getting a shot today...",
        "I like cats, especially snow leopards!",
        "Thank you for making me feel better!"
    ]
    
    for response in responses:
        # Process child's response
        result = await doctor.process_response(
            text=response,
            audio=None,  # In real implementation, this would be audio data
            client_id="demo_session"
        )
        
        # Convert response to speech
        audio = await tts.convert_text_to_speech(result.text)
        print(f"\nChild: {response}")
        print(f"Doctor Snow Leopard: {result.text}")
        print(f"Emotion: {doctor.current_emotion}")

if __name__ == "__main__":
    asyncio.run(run_demo()) 