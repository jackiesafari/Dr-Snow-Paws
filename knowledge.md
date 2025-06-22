# Doctor Snow Leopard Project Knowledge

## Overview
This project implements a child-friendly AI assistant in the form of a snow leopard doctor. The assistant uses a video avatar to create an engaging and comforting experience for children in medical settings.

## Avatar Implementation
- The avatar uses a video file for a more dynamic representation
- The avatar displays different emotions based on the conversation context
- Emotions are mapped to CSS animations (happy, caring, listening, neutral)
- The video is synchronized with the audio responses

## Key Components
- `static/templates/index.html`: Main interface with video avatar and chat functionality
- `app/core/bot.py`: Handles conversation logic and emotion analysis
- `app/api/routes.py`: API endpoints for the application
- `static/css/main.css`: Main styling
- `static/css/mobile.css`: Mobile-specific styling
- `static/js/mobile.js`: Mobile interaction handling

## Mobile Optimization
- Responsive design with mobile-first approach
- Touch-optimized interface with proper button sizes
- iOS-specific fixes for keyboard and scrolling
- iPad-specific layout optimizations
- Improved touch feedback and gesture handling

## Future Improvements
- Implement more sophisticated lip-syncing with the video
- Add more emotion states and corresponding animations
- Create custom video segments for different medical explanations
- Implement voice activity detection for more natural interactions
- Add offline support through service workers
- Implement PWA capabilities

## Technical Notes
- The video avatar is implemented using HTML5 video element
- Emotions are applied using CSS classes and animations
- WebSocket is used for real-time communication between the frontend and backend
- Mobile optimization includes touch event handling and viewport management
