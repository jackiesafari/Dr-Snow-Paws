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
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = AsyncOpenAI(api_key=api_key)
        self.guardrails = DrSnowPawsGuardrails(self.client)
        self.translator = TranslationHandler(self.client)
        self.tts_voice = os.getenv("TTS_VOICE", "shimmer")
        self.tts_enabled = True
        self.greetings = [
            "*adjusts stethoscope* Hi there, little friend! I'm Doctor Snow Paws! My fluffy paws are ready to help you feel better today! 🩺",
            "*looks up with a warm smile* Hello there! I'm Doctor Snow Paws! I love meeting brave kids like you! What brings you in today? 🐆",
            "*swishes tail happily* Welcome, my young friend! I'm Doctor Snow Paws! I promise to be gentle and make this visit fun! How are you feeling today? ❄️",
            "*offers a soft paw* Hi there! I'm Doctor Snow Paws! My patients tell me I give the softest high-fives! Would you like one? 🐾"
        ]
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
        try:
            logger.debug(f"Processing message: {message}")
            
            is_safe, safe_message = await self.guardrails.check_input(message)
            if not is_safe:
                logger.debug("Message failed safety check")
                return {"text": safe_message, "audio": None, "emotion": "caring"}
            
            # Use the translation handler for proper language detection and processing
            try:
                english_text, detected_lang, original_text = await self.translator.process_message(message)
                logger.debug(f"Translation result - English: '{english_text}', Detected lang: '{detected_lang}', Original: '{original_text}'")
            except Exception as e:
                logger.error(f"Translation error: {e}")
                # Fallback to simple detection
                detected_lang = "es" if any(word in message.lower() for word in ["hola", "gracias", "por favor", "cómo", "qué", "dónde", "cuándo", "por qué"]) else "en"
                english_text = message
                original_text = message
                logger.debug(f"Using fallback detection - Lang: '{detected_lang}'")
            
            message_lower = english_text.lower()  # Use English version for keyword matching
            response_text = None
            
            # Check predefined responses using English version
            for key, response in self.responses.items():
                if key in message_lower:
                    response_text = response
                    logger.debug(f"Found predefined response for key: {key}")
                    break
            
            if response_text is None:
                try:
                    system_prompt = self.get_system_prompt()
                    completion = await self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": english_text}  # Use English for processing
                        ],
                        max_tokens=150,
                        temperature=0.8
                    )
                    response_text = completion.choices[0].message.content
                    response_text = await self.guardrails.check_output(response_text, english_text)
                    logger.debug(f"Generated response: {response_text}")
                    
                except Exception as e:
                    logger.error(f"Error using OpenAI: {e}")
                    response_text = "*adjusts glasses* Oh my! I got a little tangled in my medical notes. Could you please repeat that? 🐾"
            
            # Translate response to target language if needed
            if detected_lang != "en":
                try:
                    response_text = await self.translator.translate_response(response_text, detected_lang)
                    logger.debug(f"Translated response: {response_text}")
                except Exception as e:
                    logger.error(f"Translation error for response: {e}")
                    # Keep English version if translation fails
            
            # Use language-appropriate text cleaning for TTS
            try:
                if detected_lang == "es":
                    speech_text = self.clean_spanish_text_for_tts(response_text)
                    logger.debug(f"Spanish TTS text: '{speech_text}'")
                else:
                    speech_text = self.clean_text_for_tts(response_text)
                    logger.debug(f"English TTS text: '{speech_text}'")
            except Exception as e:
                logger.error(f"Text cleaning error: {e}")
                speech_text = response_text  # Fallback to original
            
            # Generate audio
            audio = None
            if self.tts_enabled and speech_text:
                try:
                    logger.debug(f"Generating TTS for language '{detected_lang}' with text: '{speech_text}'")
                    audio = await self.generate_speech(speech_text, detected_lang)
                    if audio:
                        logger.debug("TTS generation successful")
                    else:
                        logger.warning("TTS generation returned None")
                except Exception as e:
                    logger.error(f"TTS generation error: {e}")
                    audio = None
            
            emotion = self.analyze_emotion(response_text)
            logger.debug(f"Detected emotion: {emotion}")
            
            return {
                "text": response_text,
                "audio": audio,
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
        if not self.tts_enabled or not text:
            logger.debug("TTS disabled or empty text")
            return None
        
        try:
            logger.debug(f"Starting TTS generation - Language: {language}, Text length: {len(text)}")
            
            # Better voice selection for Spanish
            if language == "es":
                voice = "alloy"  # Alloy handles Spanish better than nova
            else:
                voice = "shimmer"
            
            # Adjust speed based on language - Spanish needs normal speed
            speed = 1.0 if language == "es" else 0.9
            
            logger.debug(f"Using voice: {voice}, speed: {speed}")
            
            # Create speech with proper parameters
            response = await self.client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=text,
                speed=speed
            )
            
            logger.debug(f"TTS API response received, content length: {len(response.content) if response.content else 0}")
            
            if response.content:
                audio_b64 = base64.b64encode(response.content).decode('utf-8')
                logger.debug(f"Audio encoded to base64, length: {len(audio_b64)}")
                return audio_b64
            else:
                logger.warning("TTS API returned empty content")
                return None
            
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            return None

    def clean_text_for_tts(self, text: str) -> str:
        """Clean text for English TTS"""
        if not text:
            return ""
            
        # Remove text between asterisks (action descriptions)
        text = re.sub(r'\*[^*]+\*', '', text)
        
        # Remove emojis
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)
        text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)
        text = re.sub(r'[\u2600-\u26FF]', '', text)
        text = re.sub(r'[\u2700-\u27BF]', '', text)
        
        # Clean up multiple dots and spaces
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # English punctuation handling
        text = re.sub(r'\s*([.,!?])\s*', r'\1 ', text)
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        
        # Add natural pauses after punctuation for better speech flow
        text = text.replace('. ', '. ')
        text = text.replace('! ', '! ')
        text = text.replace('? ', '? ')
        
        # Final cleanup
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def clean_spanish_text_for_tts(self, text: str) -> str:
        """Specialized cleaning for Spanish TTS to preserve pronunciation cues"""
        if not text:
            return ""
            
        # Remove action descriptions
        text = re.sub(r'\*[^*]+\*', '', text)
        
        # Remove emojis but preserve Spanish characters
        emoji_pattern = r'[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]'
        text = re.sub(emoji_pattern, '', text)
        
        # Preserve Spanish punctuation and accents
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Proper Spanish punctuation spacing - preserve inverted punctuation
        text = re.sub(r'\s*¡\s*', '¡', text)
        text = re.sub(r'\s*¿\s*', '¿', text)
        
        # Add slight pauses after Spanish punctuation for clarity
        text = text.replace('.', '. ')
        text = text.replace('!', '! ')
        text = text.replace('?', '? ')
        
        # Ensure proper spacing but don't remove Spanish punctuation
        text = re.sub(r'\s*([.,!?])\s*', r'\1 ', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def analyze_emotion(self, text: str) -> str:
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["sorry", "concerned", "worried", "gentle", "hurt", "pain", "afraid", "scared", "nervous", "lo siento", "preocupado", "suave", "dolor", "miedo"]):
            return "caring"
        elif any(word in text_lower for word in ["happy", "excited", "great", "wonderful", "amazing", "fun", "play", "game", "laugh", "giggle", "smile", "feliz", "emocionado", "genial", "maravilloso", "divertido", "jugar", "juego", "reír", "sonreír"]):
            return "happy"
        elif any(word in text_lower for word in ["see", "interesting", "tell me more", "understand", "know", "learn", "ver", "interesante", "cuéntame más", "entender", "saber", "aprender"]):
            return "listening"
        elif "*looks concerned*" in text_lower or "*gentle voice*" in text_lower or "*speaks softly*" in text_lower:
            return "caring"
        elif "*tail swishes happily*" in text_lower or "*eyes sparkle*" in text_lower or "*giggles*" in text_lower:
            return "happy"
        elif "*tilts head*" in text_lower or "*nods attentively*" in text_lower or "*listens carefully*" in text_lower:
            return "listening"
        
        return "neutral"

    def get_system_prompt(self) -> str:
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
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        try:
            greeting = random.choice(self.greetings)
            logger.debug(f"Selected greeting: {greeting}")
            
            # Test TTS with greeting
            greeting_speech_text = self.clean_text_for_tts(greeting)
            logger.debug(f"Greeting speech text: '{greeting_speech_text}'")
            
            greeting_audio = await self.generate_speech(greeting_speech_text, "en")
            logger.debug(f"Greeting audio generated: {greeting_audio is not None}")
            
            await websocket.send_text(json.dumps({
                "text": greeting,
                "audio": greeting_audio,
                "emotion": "happy"
            }))
            logger.debug("Greeting sent successfully")
        except Exception as e:
            logger.error(f"Error sending greeting: {e}")
        
        try:
            while True:
                message = await websocket.receive_text()
                logger.info(f"Received message: {message}")
                
                if message.startswith('{'):
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'heartbeat':
                            continue
                    except:
                        pass
                
                response_data = await self.generate_response(message)
                logger.debug(f"Response data: {json.dumps({k: v if k != 'audio' else f'audio_present: {v is not None}' for k, v in response_data.items()})}")
                await websocket.send_text(json.dumps(response_data))
                
        except Exception as e:
            logger.error(f"Error in handle_chat: {e}")
            try:
                await websocket.send_text(json.dumps({
                    "text": "*looks concerned* I'm having some technical difficulties. Could we try again? 🐾",
                    "audio": None,
                    "emotion": "caring"
                }))
            except:
                logger.error("Could not send error message")

    async def test_tts(self) -> bool:
        try:
            test_text = "Hello! I'm Doctor Snow Leopard, and I'm here to help you feel better."
            logger.debug(f"Testing TTS with: '{test_text}'")
            audio = await self.generate_speech(test_text)
            result = audio is not None
            logger.debug(f"TTS test result: {result}")
            return result
        except Exception as e:
            logger.error(f"TTS test failed: {e}")
            return False