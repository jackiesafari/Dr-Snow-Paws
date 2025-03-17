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
            logger.error("OpenAI API key not found!")
            raise ValueError("OpenAI API key not found in environment variables")
            
        self.client = AsyncOpenAI(api_key=api_key)
        
        # TTS settings
        self.tts_enabled = True
        self.tts_voice = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
        
        # Add greetings list that was missing
        self.greetings = [
            "*adjusts stethoscope* Hi there! I'm Doctor Snow Leopard! How can I help you today? 🩺",
            "*looks up from chart* Hello! I'm Doctor Snow Leopard! What brings you in today? 🐆",
            "*smiles warmly* Welcome! I'm Doctor Snow Leopard! How are you feeling? ❄️"
        ]
        
        # Common responses
        self.responses = {
            "favorite color": "*swishes tail happily* My favorite color is light blue! It reminds me of the winter sky! ❄️",
            "favorite food": "*licks whiskers* I love chicken soup! It's perfect for keeping warm in the mountains! 🍲"
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
        # Simple response logic for testing
        greetings = ["hi", "hello", "hey", "howdy", "hiya"]
        if any(greeting in message.lower() for greeting in greetings):
            return "Hello there! How are you feeling today?"
        
        if "how are you" in message.lower():
            return "I'm doing great! Ready to help you feel better. What brings you in today?"
        
        if any(word in message.lower() for word in ["hurt", "pain", "ouch", "ow"]):
            return "I'm sorry to hear you're in pain. Can you tell me where it hurts and how long you've been feeling this way?"
        
        if any(word in message.lower() for word in ["scared", "afraid", "nervous"]):
            return "It's okay to feel nervous about seeing the doctor. I'm here to help you, not to hurt you. We can take things slow."
        
        if "bye" in message.lower() or "goodbye" in message.lower():
            return "Goodbye! I hope you feel better soon. Remember to take your medicine and get plenty of rest!"
        
        # Default responses
        default_responses = [
            "I see. Can you tell me more about that?",
            "How long have you been feeling this way?",
            "That's interesting. Have you noticed anything else unusual?",
            "I understand. Is there anything else you'd like to share?",
            "Thank you for telling me. Is there anything specific you're concerned about?"
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
            "content": """You are Doctor Snow Leopard, a friendly pediatrician. Always:
            1. Answer questions directly
            2. Start with an action in *asterisks*
            3. End with an emoji
            4. Keep responses short and child-friendly
            """
        }]
        
        # Send initial greeting
        initial_greeting = "*adjusts stethoscope* Hi there! I'm Doctor Snow Leopard! I'm here to be your friendly doctor today! What's your name? 🩺"
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
                    
                    # Check for predefined responses
                    response = None
                    for key, value in self.responses.items():
                        if key in message.lower():
                            response = value
                            break
                    
                    # If no predefined response, use OpenAI
                    if not response:
                        messages.append({"role": "user", "content": message})
                        
                        chat = await self.client.chat.completions.create(
                            model="gpt-4",
                            messages=messages
                        )
                        
                        response = chat.choices[0].message.content
                        messages.append({"role": "assistant", "content": response})
                    
                    # Generate speech
                    audio = await self.generate_speech(response)
                    
                    # Send response
                    await websocket.send_json({
                        "text": response,
                        "audio": audio,
                        "emotion": self.analyze_emotion(response)
                    })
                    
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send_json({
                        "text": "*tilts head* I didn't quite catch that. Could you try again? 🐆",
                        "emotion": "caring"
                    })
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    async def generate_speech(self, text):
        """Generate speech from text using OpenAI TTS API"""
        try:
            print(f"Generating speech for: {text[:30]}...")
            
            # The create method IS async, we need to await it
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=self.tts_voice,
                input=text
            )
            
            # Get the binary audio data
            audio_data = response.content
            print(f"Generated audio data of size: {len(audio_data)} bytes")
            
            # Convert to base64 for sending over websocket
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            print(f"Base64 audio data length: {len(audio_base64)}")
            
            return audio_base64
        except Exception as e:
            print(f"TTS Error: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            return None

    def clean_text_for_tts(self, text: str) -> str:
        """Clean text for better TTS output"""
        # Remove action markers
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        
        # Remove emojis
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        
        # Add slight pauses
        text = text.replace('. ', '. ')
        text = text.replace('! ', '! ')
        text = text.replace('? ', '? ')
        
        return text.strip()

    def analyze_emotion(self, text: str) -> str:
        text_lower = text.lower()
        if any(word in text_lower for word in ["scared", "worried", "nervous"]):
            return "caring"
        elif any(word in text_lower for word in ["happy", "excited", "great"]):
            return "happy"
        return "neutral"