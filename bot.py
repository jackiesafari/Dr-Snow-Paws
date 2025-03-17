#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

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
            logger.warning("OpenAI API key not found! Running in text-only mode.")
            self.client = None
            self.tts_enabled = False
        else:
            self.client = AsyncOpenAI(api_key=api_key)
            # TTS settings
            self.tts_enabled = True
            
        # Get TTS voice from environment variable or use default
        self.tts_voice = os.getenv("TTS_VOICE", "nova")  # Changed default to nova for a warmer voice
        logger.info(f"Using TTS voice: {self.tts_voice}")
        
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

    # Remove the test_tts from __init__ and make it a separate method
    async def test_tts(self):
        """Test TTS functionality"""
        try:
            test_response = await self.client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input="Test message"
            )
            logger.info("TTS service test successful")
            return True
        except Exception as e:
            logger.error(f"TTS service test failed: {e}")
            return False

    async def chat_endpoint(self, websocket):
        """
        Handle WebSocket chat endpoint.
        
        Args:
            websocket: The WebSocket connection
        """
        # The connection is already accepted in main.py, so we don't need to accept it again
        # Just send a welcome message
        await self.send_message(websocket, "Hi there! I'm Dr. Snow Paws, your friendly pediatrician snow leopard. How can I help you today?", "happy")
        
        try:
            # Listen for messages
            async for message in websocket.iter_text():
                logger.info(f"Received message: {message}")
                
                # Process the message and generate a response
                response = await self.generate_response(message)
                
                # Send the response back
                await self.send_message(websocket, response, "caring")
                
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            await self.send_message(websocket, f"I'm sorry, something went wrong. Please try again later.", "default")
    
    async def generate_response(self, message):
        """
        Generate a response to the user's message.
        
        Args:
            message: The user's message
            
        Returns:
            str: The bot's response
        """
        message_lower = message.lower()
        
        # Check for predefined responses first
        for key, response in self.responses.items():
            if key in message_lower:
                return response
        
        # Check for greetings
        greetings = ["hi", "hello", "hey", "howdy", "hiya"]
        if any(greeting in message_lower for greeting in greetings):
            return random.choice(self.greetings)
        
        # More specific response patterns for common child questions/concerns
        if "how are you" in message_lower:
            return "*tail swishes happily* I'm doing PAW-some today! My whiskers are tingling with excitement to help you! How are YOU feeling? Any sniffles or ouches we should look at? 🌈"
        
        if "your name" in message_lower or "who are you" in message_lower:
            return "*adjusts name tag* I'm Dr. Snow Paws! I'm a snow leopard doctor who specializes in helping awesome kids like you! My spots help me blend into the snow where I come from! 🐆"
        
        if "what do you do" in message_lower or "what's your job" in message_lower:
            return "*proudly shows stethoscope* I help kids feel better when they're sick or hurt! I listen to hearts, check throats, and sometimes give medicine. But my MOST important job is making doctor visits fun and not scary! 🩺"
        
        if any(word in message_lower for word in ["hurt", "pain", "ouch", "ow", "boo boo"]):
            return "*looks concerned* Oh no! I'm sorry you're hurting. Can you point to where it hurts? On a scale of tiny ant bite to big dragon sneeze, how much does it hurt? I promise to be super gentle when I check it. 🩹"
        
        if any(word in message_lower for word in ["scared", "afraid", "nervous", "worry", "worried", "frightened"]):
            return "*speaks very softly* It's completely okay to feel nervous about seeing the doctor. Even brave knights and superheroes get scared sometimes! Would it help if I showed you my special fluffy stethoscope first? Or maybe you'd like to hear a silly joke? 💙"
        
        if "joke" in message_lower or "funny" in message_lower:
            jokes = [
                "*giggles* Why don't snow leopards like playing cards? Because they're afraid of cheetahs! *laughs at own joke* 😹",
                "*eyes twinkle* What do you call a snow leopard doctor? A PURR-pediatrician! *swishes tail proudly* 😸",
                "*whiskers twitch with amusement* Why did the snow leopard go to school? To improve his SPOT test scores! *giggles* 🐾"
            ]
            return random.choice(jokes)
        
        if "bye" in message_lower or "goodbye" in message_lower:
            return "*waves paw gently* Goodbye, my brave friend! Remember to drink lots of water, get plenty of rest, and keep that amazing smile shining! Come back and see me anytime! Stay PAW-some! 👋"
        
        # Default responses with more personality and warmth
        default_responses = [
            "*tilts head curiously* That's really interesting! Can you tell me more about that? I'm all ears... and spots! 👂",
            "*nods attentively* I see! And how does that make you feel? Dr. Snow Paws is here to listen to everything! 💙",
            "*looks thoughtful* Hmm, that's very important to know! Is there anything else you'd like to share with me? 🤔",
            "*leans in gently* You're doing great at explaining! This helps me understand how to make you feel better! 🌟",
            "*smiles warmly* Thank you for telling me that! You're being so brave and helpful. Is there anything you'd like to ask me? 💫"
        ]
        
        return random.choice(default_responses)
    
    async def send_message(self, websocket, text, emotion="default"):
        """
        Send a message to the client.
        
        Args:
            websocket: The WebSocket connection
            text: The message text
            emotion: The emotion to display (default, happy, caring, listening)
        """
        try:
            # Create the message payload
            payload = {
                "text": text,
                "emotion": emotion
            }
            
            # Send the message
            await websocket.send_text(json.dumps(payload))
            logger.info(f"Sent message: {text}")
            
            # Add a small delay to make the conversation feel more natural
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)

    async def handle_chat(self, websocket: WebSocket):
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        messages = [{
            "role": "system",
            "content": """You are Doctor Snow Paws, a friendly pediatrician snow leopard. Always:
            1. Be warm, empathetic and playful - this is for children
            2. Start with an action in *asterisks* that shows your personality
            3. End with an emoji that matches the mood
            4. Keep responses child-friendly and reassuring
            5. Use simple language a child would understand
            6. Show excitement with occasional CAPS for emphasis
            7. Ask questions to engage the child
            8. Mention your snow leopard traits (spots, paws, tail) occasionally
            """
        }]
        
        # Send initial greeting - randomly select one
        initial_greeting = random.choice(self.greetings)
        audio = await self.generate_speech(initial_greeting)
        await websocket.send_json({
            "text": initial_greeting,
            "audio": audio,
            "emotion": "happy"
        })
        
        try:
            while True:
                try:
                    # Get message from user
                    message = await websocket.receive_text()
                    logger.info(f"Received message: {message}")
                    
                    # First check for predefined responses
                    response = None
                    message_lower = message.lower()
                    
                    for key, value in self.responses.items():
                        if key in message_lower:
                            response = value
                            break
                    
                    # If no predefined response, check other patterns
                    if not response:
                        # Try the generate_response method first
                        response = await self.generate_response(message)
                    
                    # If still no response or if we want to use OpenAI for all responses
                    # (currently disabled to save API calls, but can be enabled)
                    use_openai = False  # Set to True if you want to use OpenAI for all responses
                    
                    if not response or use_openai:
                        if self.client:
                            messages.append({"role": "user", "content": message})
                            
                            chat = await self.client.chat.completions.create(
                                model="gpt-4",
                                messages=messages
                            )
                            
                            response = chat.choices[0].message.content
                            messages.append({"role": "assistant", "content": response})
                    
                    # Determine emotion from response
                    emotion = self.analyze_emotion(response)
                    
                    # Generate speech
                    audio = await self.generate_speech(self.clean_text_for_tts(response))
                    
                    # Send response
                    await websocket.send_json({
                        "text": response,
                        "audio": audio,
                        "emotion": emotion
                    })
                    
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send_json({
                        "text": "*tilts head with concern* I didn't quite catch that. Could you try again, please? My snow leopard ears are listening carefully! 🐆",
                        "emotion": "caring"
                    })
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    async def generate_speech(self, text):
        """Generate speech from text using OpenAI TTS API"""
        if not self.tts_enabled or self.client is None:
            logger.info("TTS is disabled or OpenAI client not initialized. Skipping speech generation.")
            return None
            
        try:
            logger.info(f"Generating speech for: {text[:30]}...")
            
            # The create method IS async, we need to await it
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=self.tts_voice,
                input=text
            )
            
            # Get the binary audio data
            audio_data = response.content
            logger.info(f"Generated audio data of size: {len(audio_data)} bytes")
            
            # Convert to base64 for sending over websocket
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            logger.info(f"Base64 audio data length: {len(audio_base64)}")
            
            return audio_base64
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            return None

    def clean_text_for_tts(self, text: str) -> str:
        """Clean text for better TTS output, making it sound more natural and child-friendly"""
        # Remove action markers but keep the action description for context
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        
        # Remove emojis
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        
        # Add pauses for more natural speech
        text = text.replace('. ', '. <break time="0.5s"/> ')
        text = text.replace('! ', '! <break time="0.5s"/> ')
        text = text.replace('? ', '? <break time="0.5s"/> ')
        
        # Add emphasis to certain words kids might find engaging
        text = re.sub(r'\b(amazing|super|awesome|brave|special|magic|fun)\b', r'<emphasis level="moderate">\1</emphasis>', text, flags=re.IGNORECASE)
        
        # Add a slight pitch increase for questions to sound more engaging
        text = re.sub(r'([^.!?]+\?)', r'<prosody pitch="+10%">\1</prosody>', text)
        
        # Make "Snow Paws" sound consistent
        text = text.replace("Snow Paws", "Snow Paws")
        text = text.replace("snow leopard", "snow leopard")
        
        # Add warmth to greeting words
        text = re.sub(r'\b(hi|hello|welcome)\b', r'<prosody rate="90%" pitch="+5%">\1</prosody>', text, flags=re.IGNORECASE)
        
        # Slow down when explaining medical terms
        text = re.sub(r'\b(medicine|doctor|stethoscope|bandage|treatment)\b', r'<prosody rate="90%">\1</prosody>', text, flags=re.IGNORECASE)
        
        return text.strip()

    def analyze_emotion(self, text: str) -> str:
        """Analyze the emotion of a response to determine the avatar state"""
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
            
        # Default to neutral if no specific emotion detected
        return "neutral"