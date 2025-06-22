# Doctor Snow Paws

A friendly pediatrician snow leopard chatbot that helps make medical visits less scary for children. Uses OpenAI's GPT-4 for chat and TTS for speech.

## Features
- Interactive chat with a friendly snow leopard doctor
- Text-to-speech responses
- Emotion-based responses and animations
- Child-friendly medical explanations

## Tech Stack
- FastAPI
- OpenAI GPT-4
- OpenAI TTS
- WebSocket for real-time communication

## Technical Stack

Language: Python (3.8 - 3.11 recommended)
AI Model: OpenAI's GPT-4
Text-to-Speech: Cartesia TTS Service
Audio Processing: Silero VAD (Voice Activity Detection)
Real-time Communication: Daily.co API

## Key Components

IntakeProcessor: Manages the conversation flow and information gathering process.
DailyTransport: Handles real-time audio communication.
CartesiaTTSService: Converts text responses to speech.
OpenAILLMService: Processes natural language and generates appropriate responses.
Pipeline: Orchestrates the flow of information between different components.

How It Works

The chatbot introduces itself and verifies the patient's identity.
It systematically collects information about prescriptions, allergies, medical conditions, and the reason for the visit.
The conversation is guided by a series of function calls that transition between different stages of the intake process.
All collected information is logged for later use by medical professionals.

ℹ️ The first time, things might take extra time to get started since VAD (Voice Activity Detection) model needs to be downloaded.

## Prerequisites
- Python 3.11 (recommended, as Python 3.13 is not yet supported)
- pip
- virtualenv or venv

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd drsnowpaws
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment with Python 3.11
python3.11 -m venv venv311

# Activate virtual environment
# On macOS/Linux:
source venv311/bin/activate
# On Windows:
# venv311\Scripts\activate
```

3. Install dependencies:
```bash
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_openai_api_key_here
```

## Running the Server

1. Make sure you're in the project directory:
```bash
cd drsnowpaws
```

2. Activate the virtual environment if not already activated:
```bash
source ../venv311/bin/activate  # Adjust path if needed
```

3. Start the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

4. Open your browser and visit:
```
http://localhost:8000
```

## Troubleshooting

If you encounter any issues:

1. Make sure you're using Python 3.11 (not 3.13)
2. Verify you're in the correct directory (drsnowpaws)
3. Check that the virtual environment is activated
4. Ensure port 8000 is not in use by another process
5. Verify your OpenAI API key is set in the .env file

To check if the server is running:
```bash
curl http://localhost:8000/health
```

## Build and test the Docker image

```
docker build -t chatbot .
docker run --env-file .env -p 7860:7860 chatbot
```
## Cartesia best practices

Since this example is using Cartesia, checkout the best practices given in Cartesia's docs. LLM prompts should be modified accordingly.
<https://docs.cartesia.ai/build-with-sonic/formatting-text-for-sonic/best-practices>

<https://docs.cartesia.ai/build-with-sonic/formatting-text-for-sonic/inserting-breaks-pauses>

<https://docs.cartesia.ai/build-with-sonic/formatting-text-for-sonic/spelling-out-input-text>
### Example
```python
messages = [
    {
        "role": "system",
        "content": '''You are a helpful AI assistant. Format all responses following these guidelines:

1. Use proper punctuation and end each response with appropriate punctuation
2. Format dates as MM/DD/YYYY
3. Insert pauses using - or <break time='1s' /> for longer pauses
4. Use ?? for emphasized questions
5. Avoid quotation marks unless citing
6. Add spaces between URLs/emails and punctuation marks
7. For domain-specific terms or proper nouns, provide pronunciation guidance in [brackets]
8. Keep responses clear and concise
9. Use appropriate voice/language pairs for multilingual content

Your goal is to demonstrate these capabilities in a succinct way. Your output will be converted to audio, so maintain natural communication flow. Respond creatively and helpfully, but keep responses brief. Start by introducing yourself.'''
    }
]
```

## Avatar Animation Setup

### 1. Emotion States
The snow leopard doctor responds with different animations based on emotional states:
- Happy (greeting, positive responses)
- Listening (when patient is speaking)
- Speaking (when delivering responses)
- Thinking (when processing input)
- Idle (default state)

### 2. Implementation
Place your animation files in:
```
project_root/
├── static/
│   ├── images/        # Fallback static images
│   └── animations/    # Animation files for each state
```

### 3. Frontend Integration
Add this to your HTML:

```html:static/index.html
<div class="avatar-container">
  <video id="doctor-avatar" autoplay loop muted>
    <source src="/static/animations/idle.mp4" type="video/mp4" id="avatar-source">
    <!-- Fallback image -->
    <img src="/static/images/doctor-snow-paws.png" alt="Doctor Snow Paws">
  </video>
</div>

<script>
const avatar = document.getElementById('doctor-avatar');
const avatarSource = document.getElementById('avatar-source');

// Function to change animation based on state
function updateAvatarState(state) {
  const animations = {
    happy: '/static/animations/happy.mp4',
    listening: '/static/animations/listening.mp4',
    speaking: '/static/animations/speaking.mp4',
    thinking: '/static/animations/thinking.mp4',
    idle: '/static/animations/idle.mp4'
  };
  
  avatarSource.src = animations[state];
  avatar.load();
  avatar.play();
}

// Example usage:
// updateAvatarState('happy'); // When greeting
// updateAvatarState('listening'); // When user is speaking
// updateAvatarState('speaking'); // When doctor is speaking
</script>

<style>
.avatar-container {
  width: 300px;
  height: 300px;
  border-radius: 15px;
  overflow: hidden;
}

#doctor-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>

### 4. Animation Files
Required MP4 files for each state:
- `static/animations/idle.mp4`
- `static/animations/happy.mp4`
- `static/animations/listening.mp4`
- `static/animations/speaking.mp4`
- `static/animations/thinking.mp4`

You can create these animations using:
- 3D animation software (Blender, Maya)
- 2D animation tools (Adobe After Effects)
- AI animation tools (D-ID, Synthesia)

## Environment Variables

The following environment variables need to be set:

- `OPENAI_API_KEY`: Your OpenAI API key (required for GPT-4 and TTS functionality)
- `TTS_VOICE`: The voice to use for TTS (optional, defaults to "alloy")

### Setting up Environment Variables in Railway

1. Go to your project in the Railway dashboard
2. Click on the "Variables" tab
3. Add the following variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `TTS_VOICE`: (Optional) The voice to use for TTS (alloy, echo, fable, onyx, nova, shimmer)

### Setting up Environment Variables Locally

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
