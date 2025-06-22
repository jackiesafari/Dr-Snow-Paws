from typing import Tuple
import logging
from openai import AsyncOpenAI

class TranslationHandler:
    """Handles language detection and translation for Dr. Snow Paws."""
    
    def __init__(self, client: AsyncOpenAI):
        self.client = client
        self.session_languages = {}  # Store preferred language for each session
        
        # Extended lists of common words in Spanish and English
        self.common_spanish = {
            "hola", "si", "sí", "no", "gracias", "adios", "adiós",
            "por favor", "buenos días", "buenas tardes", "buenas noches",
            "como", "cómo", "que", "qué", "donde", "dónde", "por qué",
            "porque", "cuando", "cuándo", "quien", "quién", "cual", "cuál",
            "esto", "esta", "ese", "esa", "mi", "tu", "su", "nuestro",
            "y", "o", "pero", "para", "con", "sin", "de", "el", "la", "los", "las"
        }
        self.common_english = {
            "hi", "hey", "hello", "yes", "no", "ok", "okay", 
            "thanks", "thank you", "bye", "goodbye", "please",
            "good morning", "good afternoon", "good night",
            "what", "when", "where", "why", "who", "which", "how",
            "this", "that", "these", "those", "my", "your", "our", "their",
            "and", "or", "but", "for", "with", "without", "of", "the", "a", "an"
        }
    
    async def detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        if not text or text.isspace():
            return "en"  # Default to English for empty text
            
        text_lower = text.lower().strip()
        
        # Quick checks first
        # Check for Spanish accents and punctuation
        if any(c in text_lower for c in "áéíóúñ¿¡"):
            return "es"
            
        # Check common phrases
        words = set(text_lower.split())
        spanish_matches = sum(1 for word in words if word in self.common_spanish)
        english_matches = sum(1 for word in words if word in self.common_english)
        
        # If we have a clear winner based on common words
        if spanish_matches > english_matches:
            return "es"
        if english_matches > spanish_matches:
            return "en"
            
        # For longer or ambiguous text, use the LLM
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a language detector. Respond ONLY with 'en' for English or 'es' for Spanish."},
                    {"role": "user", "content": f"Determine if this text is in English or Spanish and respond only with 'en' or 'es': {text}"}
                ],
                temperature=0,
                max_tokens=1,
                presence_penalty=0,
                frequency_penalty=0
            )
            detected = response.choices[0].message.content.strip().lower()
            return detected if detected in ["en", "es"] else "en"
        except Exception as e:
            logging.error(f"Error detecting language: {e}")
            return "en"  # Default to English on error
    
    async def translate_to_english(self, text: str, source_lang: str) -> str:
        """Translate text to English if it's not already in English."""
        if source_lang == "en":
            return text
            
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo",  # Using more capable model for better translations
                messages=[
                    {"role": "system", "content": "Translate the following Spanish text to English. Preserve emojis, formatting, and proper nouns. Respond ONLY with the translation."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Error translating to English: {e}")
            return text
    
    async def translate_from_english(self, text: str, target_lang: str) -> str:
        """Translate text from English to target language."""
        if target_lang == "en":
            return text
            
        try:
            # More detailed prompt for Spanish translation
            system_prompt = """
            Translate the following English text to natural, fluent Spanish suitable for children.
            Important guidelines:
            1. Maintain a consistent, child-friendly tone throughout
            2. Preserve all emojis exactly as they appear
            3. Keep any *actions* or special formatting unchanged
            4. Use proper Spanish punctuation (¿, ¡)
            5. Use appropriate accents on Spanish words
            6. Ensure the translation sounds native and NOT machine-translated
            7. Maintain the same level of enthusiasm throughout the message
            
            Respond ONLY with the Spanish translation.
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo",  # Using more capable model for better translations
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Error translating from English: {e}")
            return text
    
    def set_session_language(self, session_id: str, lang_code: str):
        """Set the preferred language for a session."""
        self.session_languages[session_id] = lang_code
    
    def get_session_language(self, session_id: str) -> str:
        """Get the preferred language for a session."""
        return self.session_languages.get(session_id, "en")
    
    async def process_message(self, text: str, session_id: str = "default") -> Tuple[str, str, str]:
        """
        Process a message: detect language, translate if needed, and return original text,
        English translation (if needed), and detected language code.
        """
        # Get previous session language
        prev_lang = self.get_session_language(session_id)
        
        # Detect language
        detected_lang = await self.detect_language(text)
        
        # If previous interaction was in Spanish, bias towards Spanish for short messages
        if prev_lang == "es" and len(text.strip()) <= 15:
            detected_lang = "es"
        
        # Update session language preference
        self.set_session_language(session_id, detected_lang)
        
        # Translate to English if needed
        english_text = await self.translate_to_english(text, detected_lang)
        
        return english_text, detected_lang, text
        
    async def translate_response(self, english_response: str, target_lang: str) -> str:
        """Translate bot response from English to target language if needed."""
        if target_lang == "en":
            return english_response
            
        # Translate to target language (currently only Spanish is supported)
        translated_response = await self.translate_from_english(english_response, target_lang)
        return translated_response
    