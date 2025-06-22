import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

class SnowLeopardAvatar {
    constructor() {
        // Set up Three.js scene
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer();
        
        // Lighting setup for medical room environment
        this.addLighting();
        
        // Load the snow leopard model
        this.loadAvatarModel();
        
        // Expression mappings
        this.expressions = {
            'happy': { morphTargetInfluences: [0.8, 0.2, 0] },
            'caring': { morphTargetInfluences: [0.3, 0.7, 0.1] },
            'listening': { morphTargetInfluences: [0.2, 0.1, 0.4] }
        };
    }

    addLighting() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        this.scene.add(ambientLight);
        this.scene.add(directionalLight);
    }

    async loadAvatarModel() {
        const loader = new GLTFLoader();
        this.model = await loader.loadAsync('/models/snow_leopard_doctor.glb');
        this.scene.add(this.model.scene);
    }

    setExpression(emotion) {
        if (this.expressions[emotion]) {
            this.model.morphTargetInfluences = this.expressions[emotion];
        }
    }

    speak(text) {
        // Lip sync animation based on audio
        this.startLipSync(text);
    }
} 