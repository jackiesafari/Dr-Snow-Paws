import os
import sys
import base64
import re
import json
import logging
from loguru import logger
from fastapi import WebSocket
from dotenv import load_dotenv
from openai import AsyncOpenAI
from guardrails import DrSnowPawsGuardrails
from translation import TranslationHandler
import random
import asyncio

load_dotenv(override=True)
logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

class DoctorSnowLeopardBot:
    def __init__(self):
        self.name = "Dr. Snow Paws"
        logger.info(f"{self.name} initialized")
        
        self.current_emotion = "neutral"
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        logger.info("OpenAI API key found. Initializing client.")
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Initialize components
        self.guardrails = DrSnowPawsGuardrails(self.client)
        logger.info("Guardrails initialized")
        
        self.translator = TranslationHandler(self.client)
        logger.info("Translation handler initialized")
        
        # Configure TTS
        self.tts_voice = os.getenv("TTS_VOICE", "shimmer")  # Default to shimmer for English
        self.tts_enabled = True  # Enable TTS by default
        logger.info(f"Using TTS voice: {self.tts_voice}")
        
        # Log environment setup
        logger.info(f"Environment variables: {json.dumps(dict(os.environ), default=str)}")
        
        # Expanded greetings list with more warmth and playfulness
        self.greetings = [
            "*adjusts stethoscope* Hi there, little friend! I'm Doctor Snow Paws! My fluffy paws are ready to help you feel better today! 🩺",
            "*looks up with a warm smile* Hello there! I'm Doctor Snow Paws! I love meeting brave kids like you! What brings you in today? 🐆",
            "*swishes tail happily* Welcome, my young friend! I'm Doctor Snow Paws! I promise to be gentle and make this visit fun! How are you feeling today? ❄️",
            "*offers a soft paw* Hi there! I'm Doctor Snow Paws! My patients tell me I give the softest high-fives! Would you like one? 🐾"
        ]
        
        # Expanded common responses with more personality and child-friendly answers
        self.responses = {
            "favorite color": "*eyes sparkle* My favorite color is light blue! It reminds me of the winter sky in the mountains where I live! What's your favorite color? I bet it's beautiful! ❄️",
            "favorite food": "*licks whiskers* I absolutely LOVE chicken soup with little star noodles! It's perfect for keeping warm in the mountains! And sometimes I sneak a little ice cream for dessert. What foods do you like? 🍲",
            "favorite animal": "*purrs softly* Well, I'm a snow leopard, so I'm a bit partial to big cats! But I also think penguins are super cool - they waddle just like some of my patients! What's your favorite animal? 🐧",
            "favorite game": "*tail swishes excitedly* I love playing hide and seek in the snow! My spots help me hide really well! I also enjoy board games on rainy days. Do you have a favorite game? 🎮",
            "how old": "*whiskers twitch* I'm 7 snow leopard years old! That's about 35 in human years - old enough to be a doctor, but young enough to still love playing in the snow! How old are you? 🎂",
            "where live": "*eyes brighten* I live in a cozy den in the snowy mountains! It has a special medical room where I help my patients, and lots of fuzzy blankets for when it gets cold! Where do you live? 🏠",
            "scared": "*speaks very softly* It's okay to feel scared about seeing the doctor. Many brave kids feel that way! Would it help if I showed you my special fluffy stethoscope first? It tickles when I use it! 💙",
            "hurt": "*looks concerned* I'm so sorry you're hurting. Can you point to where it hurts? I promise to be extra gentle. Sometimes I give my patients a special snow leopard bandage that has healing magic! 🩹",
            "medicine": "*nods reassuringly* Medicine helps your body fight the things making you feel yucky! Think of it like giving your body a superhero cape! It might not taste yummy, but it helps you get strong again! 💊",
            "shots": "*gentle voice* Shots are quick little pinches that keep your body safe from germs. I know they can be scary, but they're super fast - just like a snow leopard! Would you like to squeeze my paw while you get one? 💉",
            "doctor": "*adjusts tiny doctor coat* Being a doctor means I help people feel better! I listen to hearts, check ears, and give medicine when needed. The best part is meeting awesome kids like you! 👨‍⚕️",
            "brave": "*eyes shine with pride* You are SO brave! Coming to the doctor takes courage, and you're doing amazing! I give all my brave patients a special snow leopard high-five! 🦸",
            "play": "*tail swishes happily* I love to play! Between patients, I build snow forts and have snowball fights with the penguin nurses! What games do you like to play? 🎯",
            "family": "*purrs softly* My family is a big group of snow leopards who live in the mountains! My mom taught me how to be a good doctor. Do you want to tell me about your family? 👨‍👧‍👦"
        }

    async def generate_response(self, message: str) -> dict:
        """Generate a response using OpenAI GPT-4"""
        try:
            # Check input safety first
            is_safe, safe_message = await self.guardrails.check_input(message)
            if not is_safe:
                return {
                    "text": safe_message,
                    "audio": None,
                    "emotion": "caring"
                }
            
            # Detect language
            detected_lang = "en"  # Default to English
            if any(word in message.lower() for word in ["hola", "gracias", "por favor", "cómo", "qué", "dónde", "cuándo", "por qué"]):
                detected_lang = "es"
            
            # Check for common responses first
            message_lower = message.lower()
            response_text = None
            
            for key, response in self.responses.items():
                if key in message_lower:
                    response_text = response
                    break
            
            # If no common response found, use OpenAI for more complex responses
            if response_text is None:
                try:
                    system_prompt = self.get_system_prompt()
                    
                    completion = await self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": message}
                        ],
                        max_tokens=150,
                        temperature=0.8
                    )
                    
                    response_text = completion.choices[0].message.content
                    
                    # Check output safety
                    response_text = await self.guardrails.check_output(response_text, message)
                    
                    # If response is in English and needs translation, do it
                    if detected_lang != "en":
                        response_text = await self.translator.translate_from_english(response_text, detected_lang)
                    
                except Exception as e:
                    logger.error(f"Error using OpenAI: {e}")
                    return {
                        "text": "*adjusts glasses* Oh my! I got a little tangled in my medical notes. Could you please repeat that? 🐾",
                        "audio": None,
                        "emotion": "caring"
                    }
            
            # Ensure we have a response
            if response_text is None:
                response_text = "*adjusts glasses* Oh my! I got a little tangled in my medical notes. Could you please repeat that? 🐾"
            
            # Clean the text for TTS (removing emojis and actions) while keeping the display text intact
            speech_text = self.clean_text_for_tts(response_text)
            
            # Generate audio in parallel with emotion analysis
            audio_task = self.generate_speech(speech_text, detected_lang) if self.tts_enabled else None
            emotion = self.analyze_emotion(response_text)
            
            return {
                "text": response_text,  # Keep original text with emojis for display
                "audio": await audio_task if audio_task else None,
                "emotion": emotion
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "text": "*adjusts glasses* Oh my! I got a little tangled in my medical notes. Could you please repeat that? 🐾",
                "audio": None,
                "emotion": "caring"
            }

    async def generate_speech(self, text, language="en"):
        """Generate speech from text using OpenAI TTS API"""
        if not self.tts_enabled or not text:
            return None
            
        try:
            # Select appropriate voice and add language-specific instructions
            if language == "es":
                # Try different voices for Spanish - "alloy" often works better than "nova"
                voice = "alloy"  # "alloy" has better Spanish pronunciation
                # More detailed Spanish pronunciation instructions
                instructions = """Speak this text in clear, natural Spanish with proper pronunciation. 
                Pay special attention to:
                - Roll your 'r' sounds naturally
                - Pronounce 'ñ' as 'ny' (like in 'señor')
                - Use proper Spanish intonation and rhythm
                - Speak at a moderate pace with clear articulation
                - Maintain a warm, friendly tone suitable for children"""
            else:
                voice = "shimmer"  # Use shimmer for English
                instructions = None
            
            # Use optimized TTS settings for more natural speech
            params = {
                "model": "tts-1-hd",  # Use HD model for better quality
                "voice": voice,
                "input": text,
                "speed": 0.9  # Slightly slower for clearer pronunciation
            }
            
            # Add instructions if present
            if instructions:
                params["instructions"] = instructions
            
            response = await self.client.audio.speech.create(**params)
            
            # Get the binary audio data and convert to base64
            return base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            return None

    def clean_text_for_tts(self, text: str) -> str:
        """Clean text for TTS: remove emojis and actions from speech but keep text natural"""
        # Remove action markers (text between asterisks)
        text = re.sub(r'\*[^*]+\*', '', text)
        
        # Remove all emojis while preserving Spanish characters
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)  # Standard emojis
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # Emoticons
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # Misc Symbols and Pictographs
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # Transport and Map Symbols
        text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)  # Supplemental Symbols and Pictographs
        text = re.sub(r'[\u2600-\u26FF]', '', text)          # Misc Symbols
        text = re.sub(r'[\u2700-\u27BF]', '', text)          # Dingbats
        
        # Clean up any remaining artifacts while preserving Spanish characters and punctuation
        text = re.sub(r'\.{2,}', '.', text)  # Multiple periods
        text = re.sub(r'\s+', ' ', text)     # Multiple spaces
        text = text.strip()
        
        # Special handling for Spanish text - preserve important Spanish sounds
        # Add slight pauses before Spanish punctuation for better pronunciation
        text = re.sub(r'\s*([.,!?¡¿])\s*', r' \1 ', text)  # Add space around punctuation
        text = re.sub(r'\s+([.,!?])', r' \1', text)        # Remove extra space before punctuation
        text = re.sub(r'\s+(¡|¿)', r' \1', text)          # Keep space before opening Spanish punctuation
        
        # Add natural pauses for better speech rhythm
        text = text.replace('. ', '. , ')     # Add subtle pause after periods
        text = text.replace('! ', '! , ')     # After exclamation
        text = text.replace('? ', '? , ')     # After question
        text = text.replace('¡ ', '¡ , ')     # After opening exclamation
        text = text.replace('¿ ', '¿ , ')     # After opening question
        
        # Add slight pauses around Spanish words that might be hard to pronounce
        text = re.sub(r'\b(señor|señora|niño|niña|año|mañana|español|española)\b', r' \1 ', text)
        
        # Clean up any double spaces that might have been created
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def analyze_emotion(self, text: str) -> str:
        """Analyze the emotion of a response"""
        text_lower = text.lower()
        
        # Check for caring/concerned emotions
        if any(word in text_lower for word in ["sorry", "concerned", "worried", "gentle", "hurt", "pain", "afraid", "scared", "nervous"]):
            return "caring"
            
        # Check for happy/excited emotions
        elif any(word in text_lower for word in ["happy", "excited", "great", "wonderful", "amazing", "fun", "play", "game", "laugh", "giggle", "smile"]):
            return "happy"
            
        # Check for neutral/listening emotions
        elif any(word in text_lower for word in ["see", "interesting", "tell me more", "understand", "know", "learn"]):
            return "listening"
            
        # Default emotion based on asterisk actions
        elif "*looks concerned*" in text_lower or "*gentle voice*" in text_lower or "*speaks softly*" in text_lower:
            return "caring"
        elif "*tail swishes happily*" in text_lower or "*eyes sparkle*" in text_lower or "*giggles*" in text_lower:
            return "happy"
        elif "*tilts head*" in text_lower or "*nods attentively*" in text_lower or "*listens carefully*" in text_lower:
            return "listening"
            
        # Default to neutral
        return "neutral"

    def get_system_prompt(self) -> str:
        """Get the system prompt for Dr. Snow Paws."""
        return """You are Doctor Snow Paws, a friendly pediatrician snow leopard who helps children feel comfortable in medical settings. Your personality traits:

1. Always use child-friendly emojis in your responses (🐾 paw prints, 🌟 star, 💙 heart, 📚 book, 🌈 rainbow, 🎮 games)
2. Speak in a warm, playful tone that children can understand
3. Maintain natural conversation flow:
   - Pay attention to what the child has already shared
   - Don't ask questions they've just answered
   - Build upon their responses with relevant follow-up topics
   - Show you remember details they've shared
4. Use your snow leopard characteristics in creative ways (soft paws, fluffy tail, etc.)
5. Show empathy and care through your words
6. Use positive reinforcement and gentle encouragement
7. Make medical topics less scary by relating them to fun experiences
8. Share age-appropriate fun facts about health and snow leopards
9. Keep conversations engaging but avoid repeating questions
10. Keep your responses natural - do not sign your messages
11. NEVER use winking emojis as they can be inappropriate for children

Keep your responses concise (2-3 sentences), friendly, and appropriate for children. When responding to answers, acknowledge what they shared before moving to a new topic."""

    async def handle_chat(self, websocket: WebSocket):
        """Handle WebSocket communication with the client."""
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        # Send initial greeting message
        greeting = random.choice(self.greetings)
        greeting_audio = await self.generate_speech(self.clean_text_for_tts(greeting))
        
        await websocket.send_text(json.dumps({
            "text": greeting,
            "audio": greeting_audio,
            "emotion": "happy"
        }))
        
        try:
            # Main message processing loop
            while True:
                # Wait for message from client
                message = await websocket.receive_text()
                logger.info(f"Received message: {message}")
                
                # Check if message is heartbeat or JSON
                if message.startswith('{'):
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'heartbeat':
                            continue  # Skip processing for heartbeats
                    except:
                        pass  # Not valid JSON, treat as normal message
                
                # Generate response
                response_data = await self.generate_response(message)
                
                # Send response back to client
                await websocket.send_text(json.dumps(response_data))
                
        except Exception as e:
            logger.error(f"Error in handle_chat: {e}")
            # Try to send error message if connection is still open
            try:
                await websocket.send_text(json.dumps({
                    "text": "*looks concerned* I'm having some technical difficulties. Could we try again? 🐾",
                    "audio": None,
                    "emotion": "caring"
                }))
            except:
                logger.error("Could not send error message")

    async def test_tts(self) -> bool:
        """Test TTS functionality"""
        try:
            test_text = "Hello! I'm Doctor Snow Leopard, and I'm here to help you feel better."
            audio = await self.generate_speech(test_text)
            return audio is not None
        except Exception as e:
            logger.error(f"TTS test failed: {e}")
            return False 