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

## Get started

### Prerequisites
- Python 3.8 - 3.11 (Python 3.13 is not yet supported)
- pip
- virtualenv or venv

### Installation

```python
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
pip install -r requirements.txt

cp env.example .env # and add your credentials
```


## Run the server

```bash
python3 main.py
```

Then, visit `http://localhost:7860/` in your browser to start a chatbot session.

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
