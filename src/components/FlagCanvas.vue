<template>
  <div class="canvas-container" ref="container">
    <canvas ref="canvasEl"></canvas>
    
    <!-- Ambient Particle Overlay for depth -->
    <div class="overlay-glow"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { vertexShader, fragmentShader } from '../shaders/flag.js';

const props = defineProps({
  // Wind Speed
  speed: {
    type: Number,
    default: 2.2
  },
  // Wave Amplitude
  amplitude: {
    type: Number,
    default: 0.12
  },
  // Wave Frequency (X, Y)
  frequencyX: {
    type: Number,
    default: 4.5
  },
  frequencyY: {
    type: Number,
    default: 2.5
  },
  // Target Theme Colors (Hex strings)
  stripeColors: {
    type: Array,
    required: true
  },
  cantonColor: {
    type: String,
    required: true
  },
  starColor: {
    type: String,
    required: true
  },
  rainbowMode: {
    type: Boolean,
    default: false
  },
  // Auto rotation of camera
  autoRotate: {
    type: Boolean,
    default: false
  },
  // Shininess of flag fabric material
  shininess: {
    type: Number,
    default: 25.0
  },
  // LED Emulation Mode
  ledEmulation: {
    type: Boolean,
    default: false
  },
  // LED Grid Width
  ledWidth: {
    type: Number,
    default: 64
  },
  // LED Grid Height
  ledHeight: {
    type: Number,
    default: 32
  }
});

const container = ref(null);
const canvasEl = ref(null);

let renderer = null;
let scene = null;
let camera = null;
let controls = null;
let flagMaterial = null;
let animationFrameId = null;

// Target colors as THREE.Color objects for interpolation
const targetStripeColors = props.stripeColors.map(c => new THREE.Color(c));
const targetCantonColor = new THREE.Color(props.cantonColor);
const targetStarColor = new THREE.Color(props.starColor);

// Current active colors in the shader (starts matching targets)
const currentStripeColors = props.stripeColors.map(c => new THREE.Color(c));
const currentCantonColor = new THREE.Color(props.cantonColor);
const currentStarColor = new THREE.Color(props.starColor);

// Current rainbow-mode blend (0 = static theme colors, 1 = rainbow), eased toward target each frame
let currentRainbowMode = props.rainbowMode ? 1.0 : 0.0;

// Current LED emulation blend (0 = smooth, 1 = LED matrix)
let currentLedEmulation = props.ledEmulation ? 1.0 : 0.0;

// Watchers to update target colors when props change
watch(() => props.stripeColors, (newVal) => {
  newVal.forEach((hex, i) => {
    if (targetStripeColors[i]) {
      targetStripeColors[i].set(hex);
    }
  });
}, { deep: true });

watch(() => props.cantonColor, (newVal) => targetCantonColor.set(newVal));
watch(() => props.starColor, (newVal) => targetStarColor.set(newVal));

watch(() => [props.ledWidth, props.ledHeight], ([newWidth, newHeight]) => {
  if (flagMaterial) {
    flagMaterial.uniforms.uLedResolution.value.set(newWidth, newHeight);
  }
});

onMounted(() => {
  initThree();
  animate();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
  window.removeEventListener('resize', handleResize);
  
  // Dispose WebGL resources
  if (renderer) {
    renderer.dispose();
  }
  if (scene) {
    scene.traverse((object) => {
      if (object.geometry) object.geometry.dispose();
      if (object.material) {
        if (Array.isArray(object.material)) {
          object.material.forEach((mat) => mat.dispose());
        } else {
          object.material.dispose();
        }
      }
    });
  }
});

const initThree = () => {
  const width = container.value.clientWidth;
  const height = container.value.clientHeight;

  // 1. Scene setup
  scene = new THREE.Scene();
  // Deep dark background for high-contrast presentation
  scene.background = new THREE.Color('#07080a');
  // Subtle ambient fog
  scene.fog = new THREE.FogExp2('#07080a', 0.15);

  // 2. Camera setup
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.set(0, 0, 2.0);

  // 3. Renderer setup
  renderer = new THREE.WebGLRenderer({
    canvas: canvasEl.value,
    antialias: true,
    alpha: false,
    powerPreference: "high-performance"
  });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // 4. Orbit Controls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.maxDistance = 4.0;
  controls.minDistance = 1.0;
  // Restrict rotation slightly to focus on front/angles
  controls.minPolarAngle = Math.PI / 4; // 45 degrees
  controls.maxPolarAngle = Math.PI * 3 / 4; // 135 degrees

  // 5. Lighting
  // Soft ambient light
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
  scene.add(ambientLight);

  // Key light casting soft shadows
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight.position.set(2, 4, 3);
  scene.add(dirLight);

  // Point light for center highlights
  const pointLight = new THREE.PointLight(0x38bdf8, 0.5, 10);
  pointLight.position.set(0, 1, 1);
  scene.add(pointLight);

  // 6. Waving Flag Plane
  // Aspect ratio is 1.9 : 1.0. Large segment count for smooth wave curves
  const flagGeom = new THREE.PlaneGeometry(1.9, 1.0, 120, 80);

  // Custom Shader Material using flag.js shaders
  flagMaterial = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      uTime: { value: 0 },
      uSpeed: { value: props.speed },
      uAmplitude: { value: props.amplitude },
      uFrequency: { value: new THREE.Vector2(props.frequencyX, props.frequencyY) },
      uStripeColors: { value: currentStripeColors },
      uCantonColor: { value: currentCantonColor },
      uStarColor: { value: currentStarColor },
      uRainbowMode: { value: props.rainbowMode ? 1.0 : 0.0 },
      uShininess: { value: props.shininess },
      uLedEmulation: { value: props.ledEmulation ? 1.0 : 0.0 },
      uLedResolution: { value: new THREE.Vector2(props.ledWidth, props.ledHeight) }
    },
    side: THREE.DoubleSide,
    transparent: false
  });

  const flagMesh = new THREE.Mesh(flagGeom, flagMaterial);
  flagMesh.position.set(0, 0, 0);
  scene.add(flagMesh);
};

// Main frame animation loop
const clock = new THREE.Clock();

// Crossfade speed for theme transitions (higher = faster). ~1.1s to settle.
const TRANSITION_RATE = 3.0;

const animate = () => {
  animationFrameId = requestAnimationFrame(animate);

  const delta = clock.getDelta();
  const elapsedTime = clock.elapsedTime;

  if (flagMaterial) {
    // 1. Update time uniform for wave movements
    flagMaterial.uniforms.uTime.value = elapsedTime;

    // 2. Synchronize configuration uniforms in real time
    flagMaterial.uniforms.uSpeed.value = props.speed;
    flagMaterial.uniforms.uAmplitude.value = props.amplitude;
    flagMaterial.uniforms.uFrequency.value.set(props.frequencyX, props.frequencyY);
    flagMaterial.uniforms.uShininess.value = props.shininess;

    // 3. Smoothly interpolate colors and rainbow-mode blend for a graceful crossfade,
    // using a delta-time-based factor so the transition speed is frame-rate independent.
    const lerpFactor = 1 - Math.exp(-TRANSITION_RATE * delta);
    for (let i = 0; i < 13; i++) {
      if (currentStripeColors[i] && targetStripeColors[i]) {
        currentStripeColors[i].lerp(targetStripeColors[i], lerpFactor);
      }
    }
    currentCantonColor.lerp(targetCantonColor, lerpFactor);
    currentStarColor.lerp(targetStarColor, lerpFactor);

    const targetRainbowMode = props.rainbowMode ? 1.0 : 0.0;
    currentRainbowMode += (targetRainbowMode - currentRainbowMode) * lerpFactor;

    const targetLedEmulation = props.ledEmulation ? 1.0 : 0.0;
    currentLedEmulation += (targetLedEmulation - currentLedEmulation) * lerpFactor;

    flagMaterial.uniforms.uStripeColors.value = currentStripeColors;
    flagMaterial.uniforms.uCantonColor.value = currentCantonColor;
    flagMaterial.uniforms.uStarColor.value = currentStarColor;
    flagMaterial.uniforms.uRainbowMode.value = currentRainbowMode;
    flagMaterial.uniforms.uLedEmulation.value = currentLedEmulation;
  }

  // 4. Auto-rotation of the scene camera
  if (props.autoRotate && controls) {
    // Slowly orbit the camera
    const time = elapsedTime * 0.15;
    camera.position.x = Math.sin(time) * 2.1;
    camera.position.z = Math.cos(time) * 2.1;
    camera.lookAt(0, 0, 0);
  }

  if (controls) {
    controls.update();
  }

  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
};

const handleResize = () => {
  if (!container.value || !camera || !renderer) return;
  
  const width = container.value.clientWidth;
  const height = container.value.clientHeight;
  
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  
  renderer.setSize(width, height);
};
</script>

<style scoped>
.canvas-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1;
}

canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.overlay-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  background: radial-gradient(circle at center, transparent 30%, rgba(7, 8, 10, 0.8) 100%);
  z-index: 2;
}
</style>
