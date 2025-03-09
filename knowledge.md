# Doctor Snow Leopard Project Knowledge

## Overview
This project implements a child-friendly AI assistant in the form of a snow leopard doctor. The assistant uses a video avatar to create an engaging and comforting experience for children in medical settings.

## Avatar Implementation
- The avatar uses a video file (`a084a8d3-56cc-4cb5-90ac-031710411944 2.MP4`) for a more dynamic representation
- The avatar displays different emotions based on the conversation context
- Emotions are mapped to CSS animations (happy, caring, listening, neutral)
- The video is synchronized with the audio responses

## Key Components
- `static/index.html`: Main interface with video avatar and chat functionality
- `bot.py`: Handles conversation logic and emotion analysis
- `avatar_controller.py`: Manages WebSocket connections and avatar state updates

## Future Improvements
- Implement more sophisticated lip-syncing with the video
- Add more emotion states and corresponding animations
- Create custom video segments for different medical explanations
- Implement voice activity detection for more natural interactions

## Technical Notes
- The video avatar is implemented using HTML5 video element
- Emotions are applied using CSS classes and animations
- WebSocket is used for real-time communication between the frontend and backend
