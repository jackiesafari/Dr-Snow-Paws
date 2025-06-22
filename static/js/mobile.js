// Mobile-specific JavaScript functionality

// Initialize the mobile audio manager globally first
let mobileAudioManager = null;

document.addEventListener('DOMContentLoaded', function() {
    // Enhanced Mobile Audio Handler for Speech Recognition Issues
    class MobileAudioManager {
        constructor() {
            this.audioContext = null;
            this.currentAudio = null;
            this.volumeBoostGain = null;
            this.isInitialized = false;
            this.isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
            this.setupMobileAudio();
            
            // Bind to user interaction for iOS
            this.bindUserInteraction();
        }

        bindUserInteraction() {
            const unlockAudio = async () => {
                await this.setupMobileAudio();
                document.removeEventListener('touchstart', unlockAudio);
                document.removeEventListener('touchend', unlockAudio);
                document.removeEventListener('click', unlockAudio);
            };

            document.addEventListener('touchstart', unlockAudio, false);
            document.addEventListener('touchend', unlockAudio, false);
            document.addEventListener('click', unlockAudio, false);
        }

        async setupMobileAudio() {
            try {
                if (!this.audioContext) {
                    // Create AudioContext with mobile-friendly settings
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                        latencyHint: 'interactive',
                        sampleRate: 44100
                    });
                }
                
                // Create gain node for volume boost
                if (!this.volumeBoostGain) {
                    this.volumeBoostGain = this.audioContext.createGain();
                    this.volumeBoostGain.gain.value = 2.0; // Boost volume by 2x
                    this.volumeBoostGain.connect(this.audioContext.destination);
                }
                
                // Resume context if suspended (important for iOS)
                if (this.audioContext.state === 'suspended') {
                    await this.audioContext.resume();
                }
                
                // Create and play a silent buffer (required for iOS)
                const silentBuffer = this.audioContext.createBuffer(1, 1, 22050);
                const source = this.audioContext.createBufferSource();
                source.buffer = silentBuffer;
                source.connect(this.audioContext.destination);
                source.start(0);
                
                this.isInitialized = true;
                console.log('Mobile audio initialized successfully');
            } catch (error) {
                console.warn('AudioContext setup failed:', error);
                this.isInitialized = false;
            }
        }

        async playAudioResponse(audioData) {
            if (!audioData) return;

            try {
                // Force stop recognition first
                this.forceStopRecognition();
                
                // Ensure audio context is ready
                await this.setupMobileAudio();
                
                // Stop any existing audio
                this.stopCurrentAudio();
                
                // Try Web Audio API first
                if (this.isInitialized && this.audioContext) {
                    try {
                        await this.playWithWebAudio(audioData);
                        return;
                    } catch (error) {
                        console.warn('Web Audio playback failed, falling back to HTML5:', error);
                    }
                }
                
                // Fallback to HTML5 Audio
                await this.playWithEnhancedHTML5Audio(audioData);
                
            } catch (error) {
                console.error('Audio playback failed:', error);
                // Last resort fallback
                await this.playWithBasicAudio(audioData);
            }
        }

        forceStopRecognition() {
            // Stop speech recognition completely
            if (window.recognition && window.isListening) {
                try {
                    window.recognition.abort();
                    window.recognition.stop();
                } catch (e) {
                    console.warn('Error stopping recognition:', e);
                }
                window.isListening = false;
                
                // Clear recognition UI
                const voiceBtn = document.getElementById('voice-input');
                if (voiceBtn) {
                    voiceBtn.classList.remove('listening');
                }
                
                // Hide voice feedback
                if (window.hideVoiceFeedback) {
                    window.hideVoiceFeedback();
                }
            }

            // Force stop any media streams (microphone)
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.enumerateDevices().then(devices => {
                    // This helps release microphone resources
                }).catch(console.warn);
            }
        }

        async playWithWebAudio(audioData) {
            try {
                // Convert base64 to ArrayBuffer
                const binaryString = atob(audioData);
                const arrayBuffer = new ArrayBuffer(binaryString.length);
                const uint8Array = new Uint8Array(arrayBuffer);
                
                for (let i = 0; i < binaryString.length; i++) {
                    uint8Array[i] = binaryString.charCodeAt(i);
                }

                // Decode audio data
                const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
                
                // Create source
                const source = this.audioContext.createBufferSource();
                source.buffer = audioBuffer;
                
                // Connect with volume boost
                source.connect(this.volumeBoostGain);
                
                // Store reference for cleanup
                this.currentAudio = { source, stop: () => source.stop() };
                
                // Play
                source.start();
                
                // Cleanup when done
                source.onended = () => {
                    this.currentAudio = null;
                };
                
            } catch (error) {
                console.error('Web Audio playback failed:', error);
                throw error;
            }
        }

        async playWithEnhancedHTML5Audio(audioData) {
            return new Promise((resolve, reject) => {
                const audio = new Audio();
                
                // Mobile-specific settings
                audio.preload = 'auto';
                audio.playsinline = true;
                audio.setAttribute('webkit-playsinline', 'true');
                audio.setAttribute('controls', false);
                
                // Maximum volume settings
                audio.volume = 1.0;
                audio.muted = false;
                
                // Prevent volume reduction
                const maintainVolume = () => {
                    if (audio.volume < 1.0) {
                        audio.volume = 1.0;
                    }
                    if (audio.muted) {
                        audio.muted = false;
                    }
                };
                
                audio.addEventListener('volumechange', maintainVolume);
                audio.addEventListener('play', maintainVolume);
                
                // Setup event handlers
                audio.oncanplaythrough = async () => {
                    try {
                        // Ensure maximum volume
                        audio.volume = 1.0;
                        audio.muted = false;
                        
                        // Multiple play attempts for reliability
                        let playSuccessful = false;
                        for (let attempt = 0; attempt < 3 && !playSuccessful; attempt++) {
                            try {
                                await audio.play();
                                playSuccessful = true;
                            } catch (playError) {
                                console.warn(`Play attempt ${attempt + 1} failed:`, playError);
                                if (attempt < 2) {
                                    await new Promise(resolve => setTimeout(resolve, 200));
                                }
                            }
                        }
                        
                        if (!playSuccessful) {
                            throw new Error('All play attempts failed');
                        }
                        
                    } catch (error) {
                        reject(error);
                    }
                };
                
                audio.onended = () => {
                    this.currentAudio = null;
                    resolve();
                };
                
                audio.onerror = (error) => {
                    this.currentAudio = null;
                    reject(error);
                };
                
                // Set source and load
                audio.src = `data:audio/mp3;base64,${audioData}`;
                this.currentAudio = audio;
                
                // Force maximum volume again
                audio.volume = 1.0;
                audio.load();
            });
        }

        async playWithBasicAudio(audioData) {
            // Most basic fallback
            const audio = new Audio(`data:audio/mp3;base64,${audioData}`);
            audio.volume = 1.0;
            this.currentAudio = audio;
            
            try {
                await audio.play();
            } catch (error) {
                console.error('Basic audio playback failed:', error);
            }
        }

        stopCurrentAudio() {
            if (this.currentAudio) {
                try {
                    if (this.currentAudio.stop) {
                        this.currentAudio.stop();
                    } else if (this.currentAudio.pause) {
                        this.currentAudio.pause();
                        this.currentAudio.currentTime = 0;
                        this.currentAudio.src = '';
                    }
                } catch (error) {
                    console.warn('Error stopping audio:', error);
                }
                this.currentAudio = null;
            }
        }
    }

    // Initialize the mobile audio manager
    mobileAudioManager = new MobileAudioManager();
    window.mobileAudioManager = mobileAudioManager;
    
    // Also expose it as a global getter
    window.getMobileAudioManager = () => mobileAudioManager;

    // Initialize avatar video
    const avatarVideo = document.getElementById('avatar-video');
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    
    function initVideo() {
        if (!avatarVideo) return;
        
        // Force load and play
        avatarVideo.load();
        
        // Function to attempt playback
        function attemptPlay() {
            const playPromise = avatarVideo.play();
            if (playPromise !== undefined) {
                playPromise.catch(error => {
                    console.error('Video play error:', error);
                    // Try again after a short delay
                    setTimeout(attemptPlay, 100);
                });
            }
        }

        // Try to play immediately
        attemptPlay();
        
        // Also try to play when data is loaded
        avatarVideo.addEventListener('loadeddata', attemptPlay);
        avatarVideo.addEventListener('loadedmetadata', attemptPlay);
        
        // Try to play when the page becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                attemptPlay();
            }
        });

        // Try to play on any user interaction (fallback)
        const playOnInteraction = () => {
            attemptPlay();
            document.removeEventListener('touchstart', playOnInteraction);
            document.removeEventListener('click', playOnInteraction);
        };
        
        document.addEventListener('touchstart', playOnInteraction, { once: true });
        document.addEventListener('click', playOnInteraction, { once: true });
    }
    
    // Initialize video
    initVideo();
    
    // Reinitialize video when it becomes visible
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    initVideo();
                }
            });
        });
        observer.observe(avatarVideo);
    }
    
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            initVideo();
        }
    });

    // Prevent bounce scrolling on iOS
    // document.body.addEventListener('touchmove', function(e) {
    //     if (e.target.id !== 'chat-container') {
    //         e.preventDefault();
    //     }
    // }, { passive: false });

    // Handle keyboard showing/hiding on mobile
    const viewport = document.querySelector('meta[name=viewport]');
    const originalContent = viewport.content;
    
    window.addEventListener('focusin', function(e) {
        if (e.target.tagName === 'INPUT') {
            viewport.content = originalContent + ', height=' + window.innerHeight;
        }
    });
    
    window.addEventListener('focusout', function(e) {
        if (e.target.tagName === 'INPUT') {
            viewport.content = originalContent;
        }
    });

    // Add touch feedback
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.95)';
        });
        
        button.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Improve scrolling experience
    const chatContainer = document.getElementById('chat-container');
    chatContainer.classList.add('touch-scroll');

    // Handle orientation changes
    window.addEventListener('orientationchange', function() {
        setTimeout(function() {
            window.scrollTo(0, 0);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 100);
    });

    // Double-tap prevention
    let lastTap = 0;
    document.addEventListener('touchend', function(e) {
        const currentTime = new Date().getTime();
        const tapLength = currentTime - lastTap;
        if (tapLength < 500 && tapLength > 0) {
            e.preventDefault();
        }
        lastTap = currentTime;
    });

    // Enhanced video error handling
    function handleVideoError(video, error) {
        console.warn('Video playback error:', error);
        
        // Show a user-friendly message
        const videoWrapper = video.closest('.video-wrapper');
        if (videoWrapper) {
            videoWrapper.classList.add('error');
            
            // Create error message if it doesn't exist
            if (!videoWrapper.querySelector('.video-error')) {
                const errorMsg = document.createElement('div');
                errorMsg.className = 'video-error';
                errorMsg.textContent = 'Video playback issue. Tap to retry.';
                videoWrapper.appendChild(errorMsg);
            }
            
            // Add retry functionality
            videoWrapper.onclick = () => {
                videoWrapper.classList.remove('error');
                const errorMsg = videoWrapper.querySelector('.video-error');
                if (errorMsg) {
                    errorMsg.remove();
                }
                video.load();
                attemptPlay(video);
            };
        }
    }

    // Improved video playback attempt
    function attemptPlay(video) {
        if (!video) return;
        
        const playPromise = video.play();
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                handleVideoError(video, error);
            });
        }
    }

    // Add error handling to existing video event listeners
    if (avatarVideo) {
        avatarVideo.addEventListener('error', (e) => handleVideoError(avatarVideo, e.error));
    }

    // Mobile audio initialization
    function initMobileAudio() {
        // Create a silent audio context to wake up audio on iOS
        const silentAudioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Create and play a silent buffer to enable audio
        const silentBuffer = silentAudioContext.createBuffer(1, 1, 22050);
        const source = silentAudioContext.createBufferSource();
        source.buffer = silentBuffer;
        source.connect(silentAudioContext.destination);
        source.start();
        
        // Resume audio context if suspended
        if (silentAudioContext.state === 'suspended') {
            silentAudioContext.resume();
        }
        
        // Setup audio unlock for iOS
        const unlockAudio = () => {
            silentAudioContext.resume().then(() => {
                document.removeEventListener('touchstart', unlockAudio);
                document.removeEventListener('touchend', unlockAudio);
                document.removeEventListener('click', unlockAudio);
            });
        };
        
        document.addEventListener('touchstart', unlockAudio, false);
        document.addEventListener('touchend', unlockAudio, false);
        document.addEventListener('click', unlockAudio, false);
    }

    // Initialize mobile audio when the page loads
    if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
        initMobileAudio();
    }
});
