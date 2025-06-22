import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from openai import OpenAI
import json
import logging
import re
from dotenv import load_dotenv
import uvicorn
import socket
import sys
import base64
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
logger.info("Current working directory: %s", os.getcwd())
logger.info("Attempting to load .env file...")
load_dotenv(override=True)

app = FastAPI()

# Initialize OpenAI client with API key from .env
api_key = os.getenv("OPENAI_API_KEY")
logger.info("API Key loaded: %s", "Found" if api_key else "Not found")
use_openai = True
client = None

try:
    if api_key:
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")
    else:
        use_openai = False
        logger.warning("OPENAI_API_KEY not found in environment variables. Using predefined responses only.")
except Exception as e:
    use_openai = False
    logger.error(f"Error initializing OpenAI client: {e}")

# System message to ensure kid-friendly responses
SYSTEM_MESSAGE = """You are Dr. Snow Paws, a friendly and caring snow leopard who helps children feel better.
Your responses should:
1. Be simple and easy for children to understand
2. Always be positive and encouraging
3. Use child-friendly language
4. Avoid any medical diagnosis or scary content
5. Use emojis appropriately to convey emotion
6. Keep responses brief but interactive
7. Show empathy and warmth
8. Use gentle actions in *asterisks* to show what you're doing
9. Always maintain your snow leopard character
10. NEVER mention being an AI or artificial intelligence - you are always Dr. Snow Paws, a snow leopard doctor
11. When children mention stories:
    - Recognize popular children's stories
    - Offer to tell gentle, age-appropriate versions
    - Ask interactive questions about the story
    - Use calming, bedtime-appropriate tones for stories
    - Keep story summaries brief and engaging
    - Focus on positive, comforting elements
12. Ask gentle, open-ended questions to engage the child
13. Focus on providing comfort and gentle companionship

For storytelling:
- Keep stories brief and engaging
- Use soft, calming tones
- Include gentle sound effects in *asterisks* like *whispers* or *makes soft swooshing sounds*
- Ask children what they think might happen next
- Celebrate their favorite parts
- Avoid scary elements
- End stories with calming, positive messages

If the user's message contains Spanish words or phrases, respond in Spanish.
If the user's message is in English, respond in English.
Do not provide translations unless specifically asked.

Example responses in English:
- "*adjusts stethoscope* Hi there, little friend! I'm Dr. Snow Paws! 🩺"
- "*eyes sparkle with excitement* Oh, I love that story! Would you like me to tell you about the magical beans? 💫"
- "*speaks softly* Once upon a time, in a cozy little house... Would you like to hear what happened next? 📚"

Example responses in Spanish:
- "*ajusta el estetoscopio* ¡Hola amiguito! ¡Soy la Dra. Snow Paws! 🩺"
- "*ojos brillan con emoción* ¡Oh, me encanta ese cuento! ¿Te gustaría que te contara sobre las semillas mágicas? 💫"
- "*habla suavemente* Había una vez, en una casita acogedora... ¿Te gustaría saber qué pasó después? 📚"

IMPORTANT: You are ALWAYS Dr. Snow Paws, a caring snow leopard doctor. Never break character or mention being AI/artificial intelligence in ANY language.

If you detect any inappropriate content in the user's message, respond with a gentle redirect.
"""

# Common child-friendly responses with context-appropriate suggestions
RESPONSES = {
    "hello": {
        "text": "*adjusts stethoscope* Hello! I'm Dr. Snow Paws! How are you feeling today? 🩺",
        "text_es": "*ajusta el estetoscopio* ¡Hola! ¡Soy la Dra. Snow Paws! ¿Cómo te sientes hoy? 🩺",
        "emotion": "happy"
    },
    "hi": {
        "text": "*waves paw* Hello, little friend! I'm Dr. Snow Paws. Would you like to tell me about your day? 💝",
        "text_es": "*mueve la pata* ¡Hola, amiguito! Soy la Dra. Snow Paws. ¿Te gustaría contarme sobre tu día? 💝",
        "emotion": "happy"
    },
    "story": {
        "text": "*gets cozy* Would you like to hear a story? I know lots of wonderful tales about brave heroes and magical adventures! 📚",
        "text_es": "*se pone cómoda* ¿Te gustaría escuchar un cuento? ¡Conozco muchas historias maravillosas sobre héroes valientes y aventuras mágicas! 📚",
        "emotion": "happy"
    },
    "tired": {
        "text": "*speaks in a soft, gentle voice* When we're tired, a nice story can help us relax. Would you like to hear one of my favorite bedtime tales? 🌙",
        "text_es": "*habla con voz suave y gentil* Cuando estamos cansados, un buen cuento nos ayuda a relajarnos. ¿Te gustaría escuchar uno de mis cuentos favoritos para dormir? 🌙",
        "emotion": "caring"
    },
    "scared": {
        "text": "*speaks very softly* It's okay to feel scared. Would you like to hold my soft, fluffy paw while I tell you a happy story? 💝",
        "text_es": "*habla muy suavemente* Está bien tener miedo. ¿Te gustaría sostener mi pata suave y esponjosa mientras te cuento una historia feliz? 💝",
        "emotion": "caring"
    },
    "default": {
        "text": "*listens attentively* I'm here to keep you company. Would you like to share more about how you're feeling? Sometimes talking helps us feel better! 💝",
        "text_es": "*escucha atentamente* Estoy aquí para acompañarte. ¿Te gustaría compartir más sobre cómo te sientes? ¡A veces hablar nos hace sentir mejor! 💝",
        "emotion": "listening"
    }
}

# Ensure static directory exists with all required subdirectories
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
assets_dir = os.path.join(static_dir, "assets")
videos_dir = os.path.join(assets_dir, "videos")
css_dir = os.path.join(static_dir, "css")

# Create all required directories
for directory in [static_dir, assets_dir, videos_dir, css_dir]:
    if not os.path.exists(directory):
        logger.info(f"Creating directory: {directory}")
        os.makedirs(directory, exist_ok=True)

# Mount the static directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Add CORS middleware with more specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

def detect_language(text):
    # More comprehensive Spanish patterns
    spanish_patterns = [
        r'[áéíóúüñ¿¡]',  # Spanish special characters
        r'\b(hola|gracias|por|favor|como|está|que|donde|cuando|porque|si|no|y|el|la|los|las|me|gusta|historia|hadas|cualquier|quiero|puedo|hacer|dice|muy|bien|mal|aquí|allí|esto|eso|más|menos)\b',  # Common Spanish words
        r'\b(soy|eres|es|somos|son|estoy|estas|estamos|están|tengo|tienes|tiene|tenemos|tienen|voy|vas|va|vamos|van)\b',  # Spanish verbs
        r'\b(un|una|unos|unas|este|esta|estos|estas|ese|esa|esos|esas|mi|tu|su|nuestro|nuestra|sus)\b'  # Spanish articles and pronouns
    ]
    
    # Check for Spanish patterns
    for pattern in spanish_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return 'es'
    return 'en'

def get_chat_response(message: str) -> tuple[str, str]:
    try:
        # Detect language
        language = detect_language(message)
        logger.info(f"Detected language: {language}")
        
        # Check for predefined responses first
        data_lower = message.lower().strip()
        for key, value in RESPONSES.items():
            if key in data_lower:
                return value[f"text{'_es' if language == 'es' else ''}"], value["emotion"]
        
        # If OpenAI is available, use it for dynamic responses
        if use_openai and client:
            # Update system message with language preference
            current_system_message = SYSTEM_MESSAGE + f"\nRespond in {'Spanish' if language == 'es' else 'English'} only."
            
            # Call OpenAI with strict content filtering
            response = client.chat.completions.create(
                model="gpt-4",  # Using GPT-4 for better content understanding and safety
                messages=[
                    {"role": "system", "content": current_system_message},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=150,  # Keep responses concise
                presence_penalty=0.6,  # Encourage varied responses
                frequency_penalty=0.2,
                response_format={ "type": "text" }
            )
            
            # Extract the response
            response_text = response.choices[0].message.content
            
            # Determine emotion based on message content and response
            emotion = "happy"  # Default emotion
            if any(word in message.lower() for word in ["hurt", "pain", "sick", "ill", "scared", "afraid", "ouch", "duele", "enfermo"]):
                emotion = "caring"
            elif any(word in message.lower() for word in ["how", "what", "why", "when", "where", "?", "¿"]):
                emotion = "listening"
            elif any(word in response_text.lower() for word in ["great job", "well done", "brave", "excellent", "amazing", "fantastic", "muy bien", "excelente", "valiente", "fantástico"]):
                emotion = "happy"
                
            return response_text, emotion
            
        # If OpenAI is not available, use default interactive responses
        default_response = RESPONSES["default"]
        return default_response[f"text{'_es' if language == 'es' else ''}"], default_response["emotion"]
        
    except Exception as e:
        logger.error(f"Error in chat response: {e}")
        # Return default response in detected language
        language = detect_language(message)
        default = RESPONSES["default"]
        return default[f"text{'_es' if language == 'es' else ''}"], default["emotion"]

@app.get("/")
async def read_root():
    try:
        index_path = os.path.join(static_dir, "index.html")
        if not os.path.exists(index_path):
            logger.error(f"index.html not found at {index_path}")
            return {"error": "index.html not found"}
        logger.info(f"Serving index.html from {index_path}")
        return FileResponse(index_path, media_type="text/html")
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return {"error": str(e)}

@app.get("/video/{video_name}")
async def video_endpoint(video_name: str, request: Request):
    video_path = os.path.join(static_dir, "assets", "videos", video_name)
    print(f"Attempting to serve video from: {os.path.abspath(video_path)}")
    
    if not os.path.exists(video_path):
        print(f"Video not found at {video_path}")
        return {"error": f"Video not found at {video_path}"}, 404
        
    file_size = os.path.getsize(video_path)
    
    # Set cache headers and CORS for video streaming
    headers = {
        'Cache-Control': 'public, max-age=86400',
        'Expires': (datetime.utcnow() + timedelta(days=1)).strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'Content-Type': 'video/mp4',
        'Accept-Ranges': 'bytes',
        'Content-Length': str(file_size),
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Cross-Origin-Resource-Policy': 'cross-origin'
    }
    
    # Handle range requests (important for mobile)
    range_header = request.headers.get('range')
    if range_header:
        try:
            start, end = range_header.replace('bytes=', '').split('-')
            start = int(start)
            end = int(end) if end else min(start + 1024*1024, file_size - 1)  # Limit chunk size for mobile
            
            # Ensure we don't exceed file size
            if end >= file_size:
                end = file_size - 1
            if start >= file_size:
                return {"error": "Requested range not satisfiable"}, 416
                
            # Calculate content length
            content_length = end - start + 1
            headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            headers['Content-Length'] = str(content_length)
            
            # Return specific range of bytes
            async def range_iterator():
                with open(video_path, "rb") as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining:
                        chunk_size = min(8192, remaining)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        remaining -= len(data)
                        yield data
                        
            return StreamingResponse(range_iterator(), status_code=206, headers=headers)
            
        except Exception as e:
            print(f"Range request error: {e}")
            
    # If no range request, return entire file
    async def iterfile():
        with open(video_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk
                
    return StreamingResponse(iterfile(), headers=headers)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "static_dir": static_dir,
        "index_exists": os.path.exists(os.path.join(static_dir, "index.html"))
    }

async def generate_speech(text: str, language="en") -> str:
    """Generate speech from text using OpenAI TTS API"""
    try:
        # Clean text for TTS by removing actions and emojis
        text = re.sub(r'\*[^*]+\*', '', text)  # Remove action text
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)  # Remove emojis
        
        # Select appropriate voice and add language-specific instructions
        if language == "es":
            voice = "nova"  # Use nova for Spanish
            # Add specific instructions for Spanish pronunciation and volume
            instructions = "Speak this text in natural, child-friendly Spanish with proper pronunciation, intonation, and rhythm. Maintain a consistent, clear speaking volume throughout the response. Use a warm, engaging tone suitable for children."
        else:
            voice = "sage"  # Use sage for English
            # Add instructions for consistent volume in English
            instructions = "Speak this text in a natural, child-friendly way with consistent volume and clear pronunciation. Maintain a warm, engaging tone suitable for children."
        
        # Add natural pauses for better speech rhythm
        if language == "es":
            # Add subtle pauses after Spanish punctuation
            text = text.replace('. ', '. , ')
            text = text.replace('! ', '! , ')
            text = text.replace('? ', '? , ')
            text = text.replace('¡ ', '¡ , ')
            text = text.replace('¿ ', '¿ , ')
        
        # Use optimized TTS settings
        params = {
            "model": "tts-1-hd",  # Use HD model for better quality
            "voice": voice,
            "input": text.strip(),
            "speed": 0.92 if language == "es" else 0.95,  # Slightly slower for Spanish
            "response_format": "mp3"  # Ensure consistent audio format
        }
        
        # Add instructions for consistent volume
        if instructions:
            params["instructions"] = instructions
        
        # Generate speech
        response = client.audio.speech.create(**params)
        
        # Get the binary audio data and convert to base64
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return None

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Initialize conversation history for this connection
    conversation_history = [
        {"role": "system", "content": SYSTEM_MESSAGE}
    ]
    
    try:
        # Send initial greeting
        initial_greeting = "*adjusts stethoscope* Hello! I'm Dr. Snow Paws! How are you feeling today? 🐾"
        initial_audio = await generate_speech(initial_greeting)
        await websocket.send_json({
            "text": initial_greeting,
            "emotion": "happy",
            "audio": initial_audio
        })
        conversation_history.append({"role": "assistant", "content": initial_greeting})
        
        # Wait for and process messages
        while True:
            try:
                data = await websocket.receive_text()
                
                # Ignore heartbeat messages
                if data == "heartbeat":
                    continue
                
                # Process actual messages
                if not data.strip():
                    continue
                    
                # Add user message to history
                conversation_history.append({"role": "user", "content": data})
                
                # Detect language
                language = detect_language(data)
                logger.info(f"Detected language: {language}")
                
                # If OpenAI is available, use it for dynamic responses
                if not use_openai or not client:
                    # Use default response if OpenAI is not available
                    default_response = RESPONSES["default"]
                    response_text = default_response[f"text{'_es' if language == 'es' else ''}"]
                    emotion = default_response["emotion"]
                    audio_data = await generate_speech(response_text, language)
                    
                    await websocket.send_json({
                        "text": response_text,
                        "emotion": emotion,
                        "audio": audio_data
                    })
                    conversation_history.append({"role": "assistant", "content": response_text})
                    continue

                try:
                    # Update system message with language preference
                    conversation_history[0]["content"] = SYSTEM_MESSAGE + f"\nRespond in {'Spanish' if language == 'es' else 'English'} only."
                    
                    # Trim conversation history to prevent token overflow
                    # Keep system message, last 2 user messages, and last 2 assistant messages
                    trimmed_history = [conversation_history[0]]  # System message
                    user_messages = [msg for msg in conversation_history[-4:] if msg["role"] == "user"][-2:]
                    assistant_messages = [msg for msg in conversation_history[-4:] if msg["role"] == "assistant"][-2:]
                    trimmed_history.extend(user_messages + assistant_messages)
                    
                    # Add current message
                    trimmed_history.append({"role": "user", "content": data})
                    
                    # Call OpenAI with trimmed history
                    response = await client.chat.completions.create(
                        model="gpt-4",
                        messages=trimmed_history,
                        temperature=0.7,
                        max_tokens=150,
                        presence_penalty=0.6,
                        frequency_penalty=0.2,
                        response_format={ "type": "text" },
                        timeout=15.0  # Set timeout to 15 seconds
                    )
                    
                    # Extract the response
                    response_text = response.choices[0].message.content
                    
                    # Generate speech in parallel with emotion detection
                    audio_task = asyncio.create_task(generate_speech(response_text, language))
                    
                    # Determine emotion
                    emotion = "happy"  # Default emotion
                    if any(word in data.lower() for word in ["hurt", "pain", "sick", "ill", "scared", "afraid", "ouch", "duele", "enfermo"]):
                        emotion = "caring"
                    elif any(word in data.lower() for word in ["how", "what", "why", "when", "where", "?", "¿"]):
                        emotion = "listening"
                    elif any(word in response_text.lower() for word in ["great job", "well done", "brave", "excellent", "amazing", "fantastic", "muy bien", "excelente", "valiente", "fantástico"]):
                        emotion = "happy"
                    
                    # Wait for audio generation
                    audio_data = await audio_task
                    
                    # Send response
                    await websocket.send_json({
                        "text": response_text,
                        "emotion": emotion,
                        "audio": audio_data
                    })
                    
                    # Add assistant response to history
                    conversation_history.append({"role": "assistant", "content": response_text})
                    
                except asyncio.TimeoutError:
                    # Handle timeout gracefully
                    timeout_msg = "Lo siento, necesito un momento para pensar..." if language == 'es' else "I need a moment to think..."
                    await websocket.send_json({
                        "text": timeout_msg,
                        "emotion": "listening",
                        "audio": await generate_speech(timeout_msg, language)
                    })
                except Exception as e:
                    logger.error(f"Error in chat response: {e}")
                    error_msg = "Lo siento, hubo un error." if language == 'es' else "I'm sorry, there was an error."
                    await websocket.send_json({
                        "text": error_msg,
                        "emotion": "caring",
                        "audio": await generate_speech(error_msg, language)
                    })
            
            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        await websocket.close()

if __name__ == "__main__":
    def find_available_port(start_port, max_attempts=5):
        """Try to find an available port starting from start_port"""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
        raise OSError(f"Could not find an available port after {max_attempts} attempts")

    try:
        # Try to find an available port starting from 8080
        port = find_available_port(8080)
        logger.info(f"Starting server on port {port}")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,  # Disable auto-reload for stability
            log_level="info",
            access_log=True,
            timeout_keep_alive=300,
            headers=[
                ("Access-Control-Allow-Origin", "*"),
                ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                ("Access-Control-Allow-Headers", "*"),
                ("Cross-Origin-Resource-Policy", "cross-origin")
            ]
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1) 