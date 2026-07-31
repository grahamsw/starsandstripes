<template>
  <main class="app-container">
    <!-- WebGL Canvas Background -->
    <FlagCanvas
      :speed="controls.speed"
      :amplitude="controls.amplitude"
      :frequency-x="controls.frequencyX"
      :frequency-y="controls.frequencyY"
      :stripe-colors="stripeColors"
      :canton-color="cantonColor"
      :star-color="starColor"
      :rainbow-mode="rainbowMode"
      :auto-rotate="controls.autoRotate"
      :shininess="controls.shininess"
      :led-emulation="ledEmulation"
      :led-width="ledWidth"
      :led-height="ledHeight"
      :star-layout="starLayout"
      :vertical-mode="verticalMode"
    />

    <!-- Floating Show Button (Visible only when panel is collapsed) -->
    <button 
      v-if="isSidebarCollapsed"
      class="show-controls-btn glass-panel" 
      @click="toggleSidebar" 
      aria-label="Show Controls"
    >
      <span class="toggle-text">☰ Controls</span>
    </button>

    <!-- Dashboard Sidebar Panel -->
    <aside class="dashboard glass-panel" :class="{ 'collapsed': isSidebarCollapsed }">
      <!-- Close Button (Inside panel, top right) -->
      <button class="hide-controls-btn" @click="toggleSidebar" aria-label="Hide Controls">
        ✕
      </button>
      <div class="dashboard-content">
        <!-- Header -->
        <header class="header">
          <div class="badge">WebGL 3D Studio</div>
          <h1 class="title">STARS & STRIPES</h1>
          <p class="subtitle">Procedural flag shader & real-time color animator</p>
        </header>

        <!-- LED Matrix Emulator Section -->
        <section class="section">
          <h2 class="section-title">LED Matrix Emulator</h2>
          
          <label class="toggle-group mb-4">
            <input type="checkbox" v-model="ledEmulation" />
            <span class="toggle-label font-semibold">Enable LED Matrix Mode</span>
          </label>

          <div v-if="ledEmulation" class="control-group fade-in">
            <div class="control-label mb-2">
              <span>Grid Resolution</span>
            </div>
            <div class="resolution-options">
              <label class="radio-label">
                <input type="radio" value="64x32" v-model="selectedResolution" />
                <span>64x32 (Retro)</span>
              </label>
              <label class="radio-label">
                <input type="radio" value="74x39" v-model="selectedResolution" />
                <span>74x39 (Custom)</span>
              </label>
              <label class="radio-label">
                <input type="radio" value="128x64" v-model="selectedResolution" />
                <span>128x64 (Detail)</span>
              </label>
            </div>
            
            <div class="resolution-info glass-panel-dark">
              <p><strong>Total LEDs:</strong> {{ (ledWidth * ledHeight).toLocaleString() }} bulbs</p>
              <p><strong>Stripe Height:</strong> {{ selectedResolution === '74x39' ? '3 LEDs (Perfect integer)' : (selectedResolution === '64x32' ? '~2.46 LEDs (Scaled)' : '~4.92 LEDs (Scaled)') }}</p>
              <p><strong>Star Rendering:</strong> {{ selectedResolution === '128x64' ? '3x3 Pixel detailed stars' : '1-Pixel glowing points' }}</p>
            </div>
          </div>
        </section>

        <!-- Canton Star Layout Section -->
        <section class="section">
          <h2 class="section-title">Canton Stars</h2>
          <div class="resolution-options mb-3">
            <label class="radio-label">
              <input type="radio" :value="0" v-model="starLayout" />
              <span>50 Stars (Modern)</span>
            </label>
            <label class="radio-label">
              <input type="radio" :value="1" v-model="starLayout" />
              <span>13 Stars (Betsy Ross Circle)</span>
            </label>
          </div>
          <label class="toggle-group">
            <input type="checkbox" v-model="verticalMode" />
            <span class="toggle-label font-semibold">Vertical Hanging Layout</span>
          </label>
        </section>

        <!-- Color Themes Section -->
        <section class="section">
          <h2 class="section-title">Color Themes</h2>
          
          <div class="theme-grid">
            <button 
              v-for="(theme, key) in THEMES" 
              :key="key"
              class="theme-card"
              :class="{ 'active': activeThemeKey === key }"
              @click="selectTheme(key, true)"
            >
              <div class="theme-card-left">
                <input 
                  type="checkbox" 
                  :value="key" 
                  v-model="enabledThemes" 
                  @click.stop
                  class="theme-checkbox" 
                  title="Include in Auto-Cycle"
                />
                <div v-if="theme.rainbowMode" class="flag-thumbnail rainbow-gradient">
                  <div class="thumbnail-canton" style="background-color: #3C3B6E;">
                    <span class="thumbnail-star-dot" style="background-color: #ffffff;"></span>
                  </div>
                </div>
                <div v-else class="flag-thumbnail">
                  <div class="thumbnail-stripes">
                    <div v-for="(color, idx) in theme.stripeColors" :key="idx" class="thumbnail-stripe" :style="{ backgroundColor: color }"></div>
                  </div>
                  <div class="thumbnail-canton" :style="{ backgroundColor: theme.cantonColor }">
                    <span class="thumbnail-star-dot" :style="{ backgroundColor: theme.starColor }"></span>
                  </div>
                </div>
              </div>
              <span class="theme-name">{{ theme.name }}</span>
            </button>
          </div>
          
          <!-- Auto Cycle Controls -->
          <div class="cycle-controls">
            <button 
              class="cycle-btn" 
              :class="{ 'cycling': isCycling }" 
              @click="toggleCycle"
            >
              <span class="cycle-indicator"></span>
              {{ isCycling ? 'Auto-Cycling Active' : 'Enable Auto-Cycle' }}
            </button>

            <div class="control-group mt-2">
              <div class="control-label">
                <span>Cycle Duration</span>
                <span class="control-val">{{ cycleSpeed.toFixed(1) }}s</span>
              </div>
              <input 
                type="range" 
                min="1.0" 
                max="15.0" 
                step="0.5" 
                v-model.number="cycleSpeed" 
                class="cycle-speed-slider"
              />
            </div>
          </div>
        </section>

        <!-- Custom Color Customizer -->
        <section class="section">
          <h2 class="section-title">Custom Palette</h2>
          <div class="custom-palette">
            <div class="color-picker-group">
              <label>
                <div class="color-preview" :style="{ backgroundColor: activeColors.stripeA }">
                  <input type="color" v-model="activeColors.stripeA" @input="onCustomColorChange" />
                </div>
                <span>Stripe A</span>
              </label>
            </div>
            <div class="color-picker-group">
              <label>
                <div class="color-preview" :style="{ backgroundColor: activeColors.stripeB }">
                  <input type="color" v-model="activeColors.stripeB" @input="onCustomColorChange" />
                </div>
                <span>Stripe B</span>
              </label>
            </div>
            <div class="color-picker-group">
              <label>
                <div class="color-preview" :style="{ backgroundColor: activeColors.canton }">
                  <input type="color" v-model="activeColors.canton" @input="onCustomColorChange" />
                </div>
                <span>Canton</span>
              </label>
            </div>
            <div class="color-picker-group">
              <label>
                <div class="color-preview" :style="{ backgroundColor: activeColors.star }">
                  <input type="color" v-model="activeColors.star" @input="onCustomColorChange" />
                </div>
                <span>Stars</span>
              </label>
            </div>
          </div>
        </section>

        <!-- Wave / Physics Simulation Section -->
        <section class="section">
          <h2 class="section-title">Wind & Simulation</h2>
          
          <div class="control-group">
            <div class="control-label">
              <span>Wind Velocity</span>
              <span class="control-val">{{ controls.speed.toFixed(1) }}</span>
            </div>
            <input type="range" min="0.5" max="5.0" step="0.1" v-model.number="controls.speed" />
          </div>

          <div class="control-group">
            <div class="control-label">
              <span>Wave Amplitude</span>
              <span class="control-val">{{ controls.amplitude.toFixed(2) }}</span>
            </div>
            <input type="range" min="0.01" max="0.30" step="0.01" v-model.number="controls.amplitude" />
          </div>

          <div class="control-group">
            <div class="control-label">
              <span>Wave Frequency X</span>
              <span class="control-val">{{ controls.frequencyX.toFixed(1) }}</span>
            </div>
            <input type="range" min="1.0" max="10.0" step="0.1" v-model.number="controls.frequencyX" />
          </div>

          <div class="control-group">
            <div class="control-label">
              <span>Wave Frequency Y</span>
              <span class="control-val">{{ controls.frequencyY.toFixed(1) }}</span>
            </div>
            <input type="range" min="1.0" max="10.0" step="0.1" v-model.number="controls.frequencyY" />
          </div>
        </section>

        <!-- Camera & Material Settings -->
        <section class="section">
          <h2 class="section-title">Camera & Material</h2>
          
          <div class="control-group">
            <div class="control-label">
              <span>Fabric Reflectivity</span>
              <span class="control-val">{{ controls.shininess.toFixed(0) }}</span>
            </div>
            <input type="range" min="5.0" max="100.0" step="1" v-model.number="controls.shininess" />
          </div>

          <label class="toggle-group">
            <input type="checkbox" v-model="controls.autoRotate" />
            <span class="toggle-label">Auto Orbit Camera</span>
          </label>
        </section>
      </div>

      <!-- Footer Info -->
      <footer class="footer">
        <p>Rotate camera with mouse/drag. Pinch to zoom.</p>
        <p>Shader: GPU Vertex Displacement + SDF stars</p>
      </footer>
    </aside>
  </main>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import FlagCanvas from './components/FlagCanvas.vue';
import { THEMES } from './themes.js';

const activeThemeKey = ref('rainbowWave');
const activeColors = reactive({
  stripeA: '#ff0055',
  stripeB: '#00f6ff',
  canton: '#18003c',
  star: '#ffff00'
});

const controls = reactive({
  speed: 2.2,
  amplitude: 0.11,
  frequencyX: 4.2,
  frequencyY: 2.4,
  shininess: 25.0,
  autoRotate: false
});

const isSidebarCollapsed = ref(false);
const isCycling = ref(false);
const enabledThemes = ref(Object.keys(THEMES));
const cycleSpeed = ref(4.8);
let cycleInterval = null;

// LED Matrix Emulation State
const ledEmulation = ref(false);
const selectedResolution = ref('64x32');
const starLayout = ref(0); // 0 = 50-star grid, 1 = 13-star circle
const verticalMode = ref(false); // true = vertical hanging, false = horizontal

const ledWidth = computed(() => {
  let w = 64;
  if (selectedResolution.value === '128x64') w = 128;
  else if (selectedResolution.value === '74x39') w = 74;
  
  let h = 32;
  if (selectedResolution.value === '128x64') h = 64;
  else if (selectedResolution.value === '74x39') h = 39;
  
  return verticalMode.value ? h : w;
});

const ledHeight = computed(() => {
  let w = 64;
  if (selectedResolution.value === '128x64') w = 128;
  else if (selectedResolution.value === '74x39') w = 74;
  
  let h = 32;
  if (selectedResolution.value === '128x64') h = 64;
  else if (selectedResolution.value === '74x39') h = 39;
  
  return verticalMode.value ? w : h;
});

// Helper to determine dot colors for theme previews
const getThemePreviewColor = (theme, index) => {
  if (theme.rainbowMode) {
    if (index === 0) return '#ff007f'; // Pink
    if (index === 1) return '#39ff14'; // Green
    return '#00f6ff'; // Cyan
  }
  if (index === 0) return theme.stripeColors[12]; // Stripe A color (top)
  if (index === 1) return theme.stripeColors[11]; // Stripe B color
  return theme.cantonColor; // Canton color
};

// Computed properties to feed into FlagCanvas
const stripeColors = computed(() => {
  if (activeThemeKey.value === 'custom') {
    return Array(13).fill().map((_, i) => (i % 2 === 0 ? activeColors.stripeA : activeColors.stripeB));
  }
  return THEMES[activeThemeKey.value].stripeColors;
});

const cantonColor = computed(() => {
  if (activeThemeKey.value === 'custom') {
    return activeColors.canton;
  }
  return THEMES[activeThemeKey.value].cantonColor;
});

const starColor = computed(() => {
  if (activeThemeKey.value === 'custom') {
    return activeColors.star;
  }
  return THEMES[activeThemeKey.value].starColor;
});

const rainbowMode = computed(() => {
  if (activeThemeKey.value === 'custom') {
    return false;
  }
  return THEMES[activeThemeKey.value].rainbowMode;
});

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
};

const selectTheme = (key, isManual = false) => {
  activeThemeKey.value = key;
  if (key !== 'custom') {
    const theme = THEMES[key];
    if (!theme.rainbowMode) {
      activeColors.stripeA = theme.stripeColors[12];
      activeColors.stripeB = theme.stripeColors[11];
      activeColors.canton = theme.cantonColor;
      activeColors.star = theme.starColor;
    }
  }
  
  if (isManual) {
    stopCycling();
  }
};

const onCustomColorChange = () => {
  activeThemeKey.value = 'custom';
  stopCycling();
};

// Cycle through themes automatically
const startCycling = () => {
  isCycling.value = true;
  
  cycleInterval = setInterval(() => {
    let keys = Object.keys(THEMES).filter(key => enabledThemes.value.includes(key));
    if (keys.length === 0) keys = Object.keys(THEMES); // Fallback if none checked
    
    let index = keys.indexOf(activeThemeKey.value);
    if (index === -1) {
      index = 0;
    } else {
      index = (index + 1) % keys.length;
    }
    selectTheme(keys[index], false);
  }, cycleSpeed.value * 1000);
};

const stopCycling = () => {
  isCycling.value = false;
  if (cycleInterval) {
    clearInterval(cycleInterval);
    cycleInterval = null;
  }
};

const toggleCycle = () => {
  if (isCycling.value) {
    stopCycling();
  } else {
    startCycling();
  }
};

watch(cycleSpeed, () => {
  if (isCycling.value) {
    stopCycling();
    startCycling();
  }
});

let startX = 0;
let startY = 0;

const handleMouseDown = (e) => {
  startX = e.clientX;
  startY = e.clientY;
};

const handleMouseUp = (e) => {
  const diffX = Math.abs(e.clientX - startX);
  const diffY = Math.abs(e.clientY - startY);
  
  // If user moved the cursor more than 5 pixels, it's a drag operation.
  // We ignore it so dragging to rotate the WebGL camera doesn't close the panel.
  if (diffX > 5 || diffY > 5) return;
  
  const panel = document.querySelector('.dashboard');
  const toggleBtn = document.querySelector('.show-controls-btn');
  
  if (panel && !panel.contains(e.target) && (!toggleBtn || !toggleBtn.contains(e.target))) {
    if (!isSidebarCollapsed.value) {
      isSidebarCollapsed.value = true;
    }
  }
};

const handleTouchStart = (e) => {
  if (e.touches.length > 0) {
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
  }
};

const handleTouchEnd = (e) => {
  if (e.changedTouches.length > 0) {
    const diffX = Math.abs(e.changedTouches[0].clientX - startX);
    const diffY = Math.abs(e.changedTouches[0].clientY - startY);
    if (diffX > 5 || diffY > 5) return;
    
    const panel = document.querySelector('.dashboard');
    const toggleBtn = document.querySelector('.show-controls-btn');
    
    if (panel && !panel.contains(e.target) && (!toggleBtn || !toggleBtn.contains(e.target))) {
      if (!isSidebarCollapsed.value) {
        isSidebarCollapsed.value = true;
      }
    }
  }
};

const handleKeyDown = (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    if (!isSidebarCollapsed.value) {
      isSidebarCollapsed.value = true;
    }
  }
};

onMounted(() => {
  startCycling();
  window.addEventListener('mousedown', handleMouseDown);
  window.addEventListener('mouseup', handleMouseUp);
  window.addEventListener('touchstart', handleTouchStart);
  window.addEventListener('touchend', handleTouchEnd);
  window.addEventListener('keydown', handleKeyDown);
});

onBeforeUnmount(() => {
  stopCycling();
  window.removeEventListener('mousedown', handleMouseDown);
  window.removeEventListener('mouseup', handleMouseUp);
  window.removeEventListener('touchstart', handleTouchStart);
  window.removeEventListener('touchend', handleTouchEnd);
  window.removeEventListener('keydown', handleKeyDown);
});
</script>

<style scoped>
.app-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: #07080a;
}

/* Sidebar Dashboard */
.dashboard {
  position: absolute;
  top: 20px;
  left: 20px;
  bottom: 20px;
  width: 360px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  padding: 24px;
  color: var(--text-primary);
  overflow-y: auto;
  overflow-x: hidden;
  max-width: calc(100vw - 40px);
  transition: var(--transition-smooth);
}

.dashboard.collapsed {
  transform: translateX(-390px);
}

.show-controls-btn {
  position: fixed;
  left: 20px;
  top: 40px;
  height: 40px;
  padding: 0 16px;
  z-index: 100;
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: var(--radius-md);
  transition: var(--transition-smooth);
  pointer-events: auto;
}

.show-controls-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: var(--accent);
  box-shadow: 0 0 12px var(--accent-glow);
}

.hide-controls-btn {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-panel);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  transition: var(--transition-smooth);
  z-index: 15;
}

.hide-controls-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.dashboard-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Header */
.header {
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding-bottom: 16px;
}

.badge {
  align-self: flex-start;
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: var(--accent);
  padding: 3px 8px;
  border-radius: 12px;
  font-weight: 600;
}

.title {
  font-size: 1.6rem;
  letter-spacing: -0.01em;
  font-weight: 800;
  background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.3;
}

/* Sections */
.section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 600;
}

/* Themes */
.theme-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.theme-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: var(--radius-md);
  padding: 8px 10px;
  cursor: pointer;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  transition: var(--transition-smooth);
  width: 100%;
  box-sizing: border-box;
}

.theme-card:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.1);
}

.theme-card.active {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--accent);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.15);
}

.theme-card-left {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.theme-checkbox {
  accent-color: var(--accent);
  cursor: pointer;
  width: 14px;
  height: 14px;
  margin: 0;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.theme-checkbox:hover {
  opacity: 1;
}

.flag-thumbnail {
  position: relative;
  width: 32px;
  height: 18px;
  border-radius: 2px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  flex-shrink: 0;
}

.thumbnail-stripes {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.thumbnail-stripe {
  flex: 1;
}

.thumbnail-canton {
  position: absolute;
  top: 0;
  left: 0;
  width: 40%;
  height: 53.8%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumbnail-star-dot {
  width: 2px;
  height: 2px;
  border-radius: 50%;
}

.rainbow-gradient {
  background: linear-gradient(to bottom, #782080, #0000FF, #008000, #FFFF00, #FFA500, #FF0000);
}

.theme-name {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-align: left;
  line-height: 1.2;
}

.theme-card.active .theme-name {
  color: var(--text-primary);
}

.cycle-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cycle-speed-slider {
  accent-color: var(--accent);
  cursor: pointer;
}

/* Cycle Button */
.cycle-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-panel);
  border-radius: var(--radius-md);
  padding: 10px;
  color: var(--text-primary);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: var(--transition-smooth);
}

.cycle-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.15);
}

.cycle-btn.cycling {
  background: rgba(56, 189, 248, 0.1);
  border-color: var(--accent);
}

.cycle-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}

.cycling .cycle-indicator {
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent);
  animation: pulse-glow 1.5s infinite ease-in-out;
}

/* Custom Palette */
.custom-palette {
  display: flex;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: var(--radius-md);
  padding: 12px;
}

.color-picker-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.color-picker-group label {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  gap: 6px;
}

.color-picker-group span {
  font-size: 0.65rem;
  color: var(--text-secondary);
}

.color-preview {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  transition: var(--transition-smooth);
}

.color-preview:hover {
  transform: scale(1.1);
  border-color: var(--text-primary);
}

.color-preview input[type="color"] {
  position: absolute;
  top: -10px;
  left: -10px;
  width: 60px;
  height: 60px;
  border: none;
  background: none;
  cursor: pointer;
  opacity: 0;
}

/* Slider Controls */
.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.control-val {
  font-family: monospace;
  color: var(--accent);
}

.toggle-group {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 0;
}

.toggle-group input[type="checkbox"] {
  accent-color: var(--accent);
  width: 15px;
  height: 15px;
  cursor: pointer;
}

.toggle-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* Footer */
.footer {
  margin-top: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.footer p {
  font-size: 0.65rem;
  color: var(--text-muted);
  line-height: 1.4;
  text-align: center;
}

/* LED Matrix Emulation Section Styles */
.mb-4 {
  margin-bottom: 16px;
}

.font-semibold {
  font-weight: 600;
}

.resolution-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
  background: rgba(0, 0, 0, 0.20);
  padding: 10px 12px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
  transition: var(--transition-smooth);
}

.radio-label:hover {
  color: var(--text-primary);
}

.radio-label input[type="radio"] {
  appearance: none;
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border: 1px solid var(--border-panel);
  border-radius: 50%;
  outline: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition-smooth);
  background: transparent;
}

.radio-label input[type="radio"]::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  transform: scale(0);
  transition: var(--transition-smooth);
}

.radio-label input[type="radio"]:checked {
  border-color: var(--accent);
  box-shadow: 0 0 8px var(--accent-glow);
}

.radio-label input[type="radio"]:checked::before {
  transform: scale(1);
}

.resolution-info {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-md);
  padding: 12px;
  font-size: 0.75rem;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.resolution-info p {
  margin: 0;
  line-height: 1.4;
}

.resolution-info strong {
  color: var(--text-secondary);
}

.fade-in {
  animation: fadeIn 0.25s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsiveness */
@media (max-width: 500px) {
  .dashboard {
    top: auto;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: 60vh;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    transform: translateY(0);
    max-width: 100%;
    padding: 16px;
    box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.5);
  }
  
  .dashboard.collapsed {
    transform: translateY(60vh);
  }
  
  .show-controls-btn {
    left: auto;
    right: 20px;
    top: auto;
    bottom: 20px;
    height: 36px;
    padding: 0 12px;
    font-size: 0.75rem;
    border-radius: var(--radius-sm);
  }
  
  .hide-controls-btn {
    top: 16px;
    right: 16px;
    width: 26px;
    height: 26px;
    font-size: 0.7rem;
  }
}
</style>
