import asyncio
import os
from dotenv import load_dotenv
from bot import DoctorSnowLeopardBot

# Load environment variables
load_dotenv()

async def test_spanish_tts():
    # Create doctor bot instance
    doctor = DoctorSnowLeopardBot()
    
    # Test cases with Spanish text
    test_cases = [
        {
            "text": "¡Hola! ¿Cómo estás hoy?",
            "language": "es",
            "description": "Simple greeting"
        },
        {
            "text": "Me alegro de que estés aquí. Vamos a hacer que tu visita sea divertida y cómoda.",
            "language": "es",
            "description": "Longer sentence with accents"
        },
        {
            "text": "*ajusta el estetoscopio* No te preocupes, seré muy gentil. 🩺",
            "language": "es",
            "description": "Text with actions and emojis"
        }
    ]
    
    print("\nTesting Spanish TTS functionality:")
    print("==================================")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['description']}")
        print(f"Original text: {test['text']}")
        
        # Clean the text for TTS
        cleaned_text = doctor.clean_text_for_tts(test['text'])
        print(f"Cleaned text: {cleaned_text}")
        
        # Generate speech
        try:
            audio = await doctor.generate_speech(cleaned_text, test['language'])
            if audio:
                print("✅ Speech generated successfully")
                
                # Save the audio to a file for manual verification
                audio_bytes = audio.encode('utf-8')
                with open(f"test_audio_{i}.mp3", "wb") as f:
                    f.write(audio_bytes)
                print(f"Audio saved to test_audio_{i}.mp3")
            else:
                print("❌ Failed to generate speech")
        except Exception as e:
            print(f"❌ Error generating speech: {e}")

if __name__ == "__main__":
    asyncio.run(test_spanish_tts()) 