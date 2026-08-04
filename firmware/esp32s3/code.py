# ESP32-S3 DevKitC-1 N16R8 & SeenGreat RGB Matrix Adapter Board (E) Rev 2.2 Flag Controller
# Display: Dual 64x64 RGB HUB75 LED Panels chained side-by-side (128x64 resolution, 1/32 Scan)
# (Left 64x64 panel displays on a single panel setup, showing the complete canton and stars)

import board
import rgbmatrix
import framebufferio
import displayio

# 1. Release any active displays to free up pins
displayio.release_displays()

# 2. SeenGreat Adapter Board (E) Rev 2.2 Pin Mapping for ESP32-S3 DevKitC-1
R1 = board.IO18
G1 = board.IO8
B1 = board.IO17
R2 = board.IO16
G2 = board.IO1
B2 = board.IO15

A = board.IO7
B = board.IO48
C = board.IO6
D = board.IO47
E = board.IO2

CLK = board.IO5
LAT = board.IO21
OE = board.IO4

matrix = None
display = None
bitmap = None
palette = None
tile_grid = None
group = None
current_bit_depth = 2

def init_display_with_depth(depth):
    global matrix, display, bitmap, palette, tile_grid, group, current_bit_depth
    
    # 1. Release existing display if any
    displayio.release_displays()
    if matrix is not None:
        try:
            matrix.deinit()
        except Exception:
            pass
            
    import gc
    gc.collect()
    
    print("Initializing RGBMatrix with bit_depth={}...".format(depth))
    matrix = rgbmatrix.RGBMatrix(
        width=128,
        height=64,
        bit_depth=depth,
        rgb_pins=[R1, G1, B1, R2, G2, B2],
        addr_pins=[A, B, C, D, E],
        clock_pin=CLK,
        latch_pin=LAT,
        output_enable_pin=OE
    )
    display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)
    display.rotation = 180
    
    # Re-create bitmap and palette
    bitmap = displayio.Bitmap(128, 64, 256)
    palette = displayio.Palette(256)
    
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
    tile_grid.flip_x = True # Flip horizontally to correct mirrored physical LED panel wiring
    
    group = displayio.Group()
    group.append(tile_grid)
    display.root_group = group
    
    current_bit_depth = depth

# Allocate 2-bit matrix immediately at boot when SRAM is cleanest
init_display_with_depth(2)

# 3. Import remaining libraries (which can be loaded in fragmented memory)
import time
import math
import os
import json
import microcontroller
import wifi
import socketpool
from adafruit_httpserver import Server, Request, Response, GET, POST

# Configurable Parameters
THEMES = [
    "classic",
    "pride6",
    "pride8",
    "transgender",
    "bisexual",
    "lesbian",
    "nonbinary",
    "thin_blue",
    "thin_red",
    "first_responders",
    "thin_green",
    "thin_gold",
    "all_responders"
]

# Active State Variables
star_layout = 0            # 0 = 50-star grid, 1 = 13-star circle (Betsy Ross)
vertical_mode = 0          # 0 = horizontal (landscape), 1 = vertical (portrait)
is_cycling = True          # Enable/disable theme cycling
enabled_themes = THEMES.copy() # List of themes allowed in cycle loop
active_theme = THEMES[0]
cycle_interval = 10.0      # Cycle to next flag every X seconds
brightness = 1.0           # LED matrix brightness (0.0 to 1.0) via software color scaling
active_mode = "flag"       # "flag" or "image"
image_buffer = bytearray(4864) # 768 bytes palette + 4096 bytes indices
transition_state = "running" # "running", "fade_out", "hold_black", "fade_in"
transition_frame = 0
next_theme = active_theme
transition_scale = 1.0

NVM_SIGNATURE = b"FLAGCONF:"

def save_config():
    """Saves the current config to the board's microcontroller.nvm."""
    try:
        config = {
            "star_layout": star_layout,
            "vertical_mode": vertical_mode,
            "is_cycling": is_cycling,
            "enabled_themes": enabled_themes,
            "active_theme": active_theme,
            "cycle_interval": cycle_interval,
            "brightness": brightness
        }
        config_str = json.dumps(config)
        config_bytes = config_str.encode("utf-8")
        
        # Construct payload: signature + length (2 bytes) + data
        payload = NVM_SIGNATURE + len(config_bytes).to_bytes(2, "big") + config_bytes
        
        if len(payload) > len(microcontroller.nvm):
            print("Config payload exceeds NVM capacity!")
            return
            
        # Write to NVM
        microcontroller.nvm[0:len(payload)] = payload
        # Add a null terminator in NVM if there is space
        if len(payload) < len(microcontroller.nvm):
            microcontroller.nvm[len(payload)] = 0
            
        print("Configuration saved successfully to microcontroller NVM.")
    except Exception as e:
        print("Could not save config to NVM:", e)

def load_config():
    """Loads the config from microcontroller.nvm if it exists and matches signature."""
    global star_layout, vertical_mode, is_cycling, enabled_themes, active_theme, cycle_interval, brightness
    try:
        nvm = microcontroller.nvm
        sig_len = len(NVM_SIGNATURE)
        # Check signature
        if nvm[0:sig_len] != NVM_SIGNATURE:
            print("No saved config signature found in NVM. Using defaults.")
            return
            
        # Read payload length (2 bytes)
        payload_len = int.from_bytes(nvm[sig_len:sig_len+2], "big")
        if payload_len <= 0 or payload_len > (len(nvm) - sig_len - 2):
            print("Invalid config length in NVM. Using defaults.")
            return
            
        # Read JSON string
        data_start = sig_len + 2
        data_end = data_start + payload_len
        config_str = nvm[data_start:data_end].decode("utf-8")
        
        config = json.loads(config_str)
        if "star_layout" in config:
            star_layout = config["star_layout"]
        if "vertical_mode" in config:
            vertical_mode = config["vertical_mode"]
        if "is_cycling" in config:
            is_cycling = config["is_cycling"]
        if "enabled_themes" in config:
            enabled_themes = [t for t in config["enabled_themes"] if t in THEMES]
        if "active_theme" in config:
            if config["active_theme"] in THEMES:
                active_theme = config["active_theme"]
        if "cycle_interval" in config:
            cycle_interval = float(config["cycle_interval"])
        if "brightness" in config:
            brightness = float(config["brightness"])
        print("Loaded configuration from microcontroller NVM successfully.")
    except Exception as e:
        print("Failed to load config from NVM:", e)

# Load saved configurations before starting WiFi
load_config()

# Served Control Panel Dashboard HTML
INDEX_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ESP32-S3 Flag Control Panel</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #090d16;
      color: #f8fafc;
      padding: 16px;
      margin: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .card {
      background: rgba(30, 41, 59, 0.45);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 20px;
      padding: 24px;
      width: 100%;
      max-width: 440px;
      box-sizing: border-box;
      margin-bottom: 20px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    h1 {
      margin: 0 0 8px 0;
      color: #38bdf8;
      text-align: center;
      font-size: 24px;
      font-weight: 800;
    }
    h2 {
      margin: 0 0 16px 0;
      color: #94a3b8;
      font-size: 16px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      padding-bottom: 8px;
    }
    .status {
      text-align: center;
      font-size: 14px;
      color: #64748b;
      margin-bottom: 24px;
      background: rgba(15, 23, 42, 0.4);
      padding: 6px 12px;
      border-radius: 30px;
      display: inline-block;
      align-self: center;
    }
    .btn-container {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .btn {
      background: #0284c7;
      color: white;
      border: none;
      padding: 14px 20px;
      border-radius: 12px;
      font-size: 15px;
      cursor: pointer;
      width: 100%;
      font-weight: 700;
      transition: background 0.15s, transform 0.1s;
      display: flex;
      justify-content: center;
      align-items: center;
      box-sizing: border-box;
    }
    .btn:active {
      transform: scale(0.98);
      background: #0369a1;
    }
    .btn-secondary {
      background: rgba(71, 85, 105, 0.4);
      border: 1px solid rgba(255,255,255,0.05);
    }
    .btn-secondary:active {
      background: rgba(51, 65, 85, 0.6);
    }
    .btn-accent {
      background: #10b981;
    }
    .btn-accent:active {
      background: #059669;
    }
    .theme-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    .theme-row:last-child {
      border-bottom: none;
    }
    .theme-info {
      display: flex;
      flex-direction: column;
    }
    .theme-name {
      font-weight: 600;
      text-transform: capitalize;
    }
    .theme-active-tag {
      font-size: 11px;
      color: #38bdf8;
      font-weight: bold;
    }
    .switch {
      position: relative;
      display: inline-block;
      width: 46px;
      height: 24px;
    }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: #334155;
      transition: 0.3s;
      border-radius: 24px;
    }
    .slider:before {
      position: absolute;
      content: "";
      height: 16px; width: 16px; left: 4px; bottom: 4px;
      background-color: #f8fafc;
      transition: 0.25s;
      border-radius: 50%;
    }
    input:checked + .slider { background-color: #0284c7; }
    input:checked + .slider:before { transform: translateX(22px); }
  </style>
</head>
<body>
  <div class="card" style="display: flex; flex-direction: column; gap: 15px;">
    <h1>🇺🇸 ESP32-S3 Flag Controller</h1>
    <div class="status" id="status-text">Connecting...</div>
    
    <div class="btn-container">
      <button class="btn" id="btn-cycle" onclick="toggleCycle()">Theme Cycling: ON</button>
      <button class="btn btn-secondary" onclick="toggleStarLayout()">Toggle Star Layout</button>
      <button class="btn btn-secondary" onclick="toggleVerticalLayout()">Toggle Vertical Layout</button>
      <button class="btn btn-secondary" id="btn-restore-flag" onclick="restoreFlagMode()" style="display:none; border: 1px solid #10b981; color: #10b981;">Restore Flag Animation</button>
    </div>
    
    <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 10px; border-top: 1px solid #334155; padding-top: 15px;">
      <div class="control-group">
        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #94a3b8; font-weight: 500;">
          <span>Cycle Interval</span>
          <span id="cycle-interval-val">--s</span>
        </div>
        <input type="range" min="1" max="60" step="1" id="cycle-interval-slider" oninput="handleIntervalInput(this.value)" onchange="updateCycleInterval(this.value)" style="width: 100%; margin-top: 5px;" />
      </div>

      <div class="control-group">
        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #94a3b8; font-weight: 500;">
          <span>LED Brightness</span>
          <span id="brightness-val">--%</span>
        </div>
        <input type="range" min="10" max="100" step="5" id="brightness-slider" oninput="handleBrightnessInput(this.value)" onchange="updateBrightness(this.value)" style="width: 100%; margin-top: 5px;" />
      </div>
    </div>
  </div>

  <!-- Custom Image Upload Section -->
  <div class="card" style="display: flex; flex-direction: column; gap: 15px;">
    <h2>🖼️ Custom Image Display</h2>
    <div style="font-size: 13px; color: #94a3b8; line-height: 1.4;">
      Select an image to display. The app center-crops it, builds an optimized palette, and applies Floyd-Steinberg error diffusion dithering for smooth color gradients.
    </div>
    
    <div style="display: flex; flex-direction: column; gap: 12px; border-top: 1px solid #334155; padding-top: 10px;">
      <div class="control-group">
        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #94a3b8; font-weight: 500;">
          <span>Image Brightness</span>
          <span id="img-brightness-val">70%</span>
        </div>
        <input type="range" min="10" max="100" step="5" id="img-brightness" value="70" oninput="document.getElementById('img-brightness-val').innerText = this.value + '%'" onchange="processAndUploadImage()" style="width: 100%; margin-top: 5px;" />
      </div>

      <div class="control-group">
        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #94a3b8; font-weight: 500;">
          <span>Image Contrast</span>
          <span id="img-contrast-val">-15</span>
        </div>
        <input type="range" min="-50" max="50" step="5" id="img-contrast" value="-15" oninput="document.getElementById('img-contrast-val').innerText = this.value" onchange="processAndUploadImage()" style="width: 100%; margin-top: 5px;" />
      </div>

      <div class="control-group">
        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #94a3b8; font-weight: 500;">
          <span>Gamma Correction</span>
          <span id="img-gamma-val">2.2</span>
        </div>
        <input type="range" min="1.0" max="3.0" step="0.1" id="img-gamma" value="2.2" oninput="document.getElementById('img-gamma-val').innerText = this.value" onchange="processAndUploadImage()" style="width: 100%; margin-top: 5px;" />
      </div>
    </div>
    
    <div class="btn-container" style="margin-top: 10px;">
      <input type="file" id="image-input" accept="image/*" style="display:none;" onchange="handleImageUpload(this.files[0])" />
      <button class="btn btn-accent" onclick="document.getElementById('image-input').click()">Upload & Display Image</button>
    </div>
    <div id="upload-status" style="font-size: 13px; color: #10b981; text-align: center; font-weight: 600;"></div>
  </div>
  
  <div class="card" id="themes-card">
    <h2>Cycle List & Themes</h2>
    <div id="themes-list"></div>
  </div>

  <script>
    let state = {};
    let uploadedFile = null;
    
    function handleIntervalInput(val) {
      document.getElementById('cycle-interval-val').innerText = val + 's';
    }
    
    function handleBrightnessInput(val) {
      document.getElementById('brightness-val').innerText = val + '%';
    }

    async function updateCycleInterval(val) {
      handleIntervalInput(val);
      await fetch('/api/control?cycle_interval=' + val);
      loadState();
    }
    
    async function updateBrightness(val) {
      handleBrightnessInput(val);
      let b = val / 100.0;
      await fetch('/api/control?brightness=' + b);
      loadState();
    }

    async function restoreFlagMode() {
      await fetch('/api/control?mode=flag');
      loadState();
    }

    async function loadState() {
      try {
        let res = await fetch('/api/state');
        state = await res.json();
        
        const isImageMode = state.mode === 'image';
        
        if (isImageMode) {
          document.getElementById('status-text').innerText = 'Active: Rendering Image';
          document.getElementById('btn-restore-flag').style.display = 'block';
          document.getElementById('themes-card').style.opacity = '0.5';
          document.getElementById('btn-cycle').disabled = true;
        } else {
          document.getElementById('status-text').innerText = 'Active: ' + state.active_theme.replace('_', ' ');
          document.getElementById('btn-restore-flag').style.display = 'none';
          document.getElementById('themes-card').style.opacity = '1.0';
          document.getElementById('btn-cycle').disabled = false;
        }
        
        document.getElementById('btn-cycle').innerText = 'Theme Cycling: ' + (state.cycling ? 'ON' : 'OFF');
        document.getElementById('btn-cycle').className = state.cycling ? 'btn' : 'btn btn-secondary';
        
        document.getElementById('cycle-interval-slider').value = state.cycle_interval;
        document.getElementById('cycle-interval-val').innerText = state.cycle_interval + 's';
        
        let bPercent = Math.round(state.brightness * 100);
        document.getElementById('brightness-slider').value = bPercent;
        document.getElementById('brightness-val').innerText = bPercent + '%';
        
        let html = '';
        state.themes.forEach(theme => {
          let checked = state.enabled_themes.includes(theme) ? 'checked' : '';
          let isActive = state.active_theme === theme && !isImageMode;
          let labelText = theme.replace('_', ' ');
          
          html += `<div class="theme-row">
            <div class="theme-info" onclick="selectTheme('${theme}')" style="cursor: pointer; flex-grow: 1;">
              <span class="theme-name" style="${isActive ? 'color: #38bdf8;' : ''}">${labelText}</span>
              ${isActive ? '<span class="theme-active-tag">CURRENTLY RENDERING</span>' : ''}
            </div>
            <label class="switch">
              <input type="checkbox" ${checked} onchange="toggleTheme('${theme}', this.checked)" ${isImageMode ? 'disabled' : ''}>
              <span class="slider"></span>
            </label>
          </div>`;
        });
        document.getElementById('themes-list').innerHTML = html;
      } catch (e) {
        document.getElementById('status-text').innerText = 'Connection Error';
      }
    }
    
    async function toggleCycle() {
      await fetch('/api/control?cycling=' + (!state.cycling));
      loadState();
    }
    
    async function toggleStarLayout() {
      let next = state.star_layout === 0 ? 1 : 0;
      await fetch('/api/control?star_layout=' + next);
      loadState();
    }
    
    async function toggleVerticalLayout() {
      let next = state.vertical_mode === 0 ? 1 : 0;
      await fetch('/api/control?vertical_mode=' + next);
      loadState();
    }
    
    async function selectTheme(theme) {
      if (state.mode === 'image') return;
      await fetch('/api/control?theme=' + theme);
      loadState();
    }
    
    async function toggleTheme(theme, checked) {
      let list = [...state.enabled_themes];
      if (checked) {
        if (!list.includes(theme)) list.push(theme);
      } else {
        list = list.filter(t => t !== theme);
      }
      await fetch('/api/control?enabled_themes=' + list.join(','));
      loadState();
    }

    function handleImageUpload(file) {
      if (!file) return;
      uploadedFile = file;
      processAndUploadImage();
    }

    // Median-Cut Color Quantization algorithm (custom 256 palette generator)
    function quantizeMedianCut(pixels) {
      let points = [];
      for (let i = 0; i < 4096; i++) {
        points.push({
          r: pixels[i * 4],
          g: pixels[i * 4 + 1],
          b: pixels[i * 4 + 2],
          idx: i
        });
      }
      
      let boxes = [points];
      
      while (boxes.length < 256) {
        let splitIdx = -1;
        let maxRange = -1;
        let splitChan = 'r';
        
        for (let i = 0; i < boxes.length; i++) {
          let box = boxes[i];
          if (box.length <= 1) continue;
          
          let minR = 255, maxR = 0;
          let minG = 255, maxG = 0;
          let minB = 255, maxB = 0;
          for (let p of box) {
            if (p.r < minR) minR = p.r; if (p.r > maxR) maxR = p.r;
            if (p.g < minG) minG = p.g; if (p.g > maxG) maxG = p.g;
            if (p.b < minB) minB = p.b; if (p.b > maxB) maxB = p.b;
          }
          
          let rRange = maxR - minR;
          let gRange = maxG - minG;
          let bRange = maxB - minB;
          let range = Math.max(rRange, gRange, bRange);
          
          if (range > maxRange) {
            maxRange = range;
            splitIdx = i;
            splitChan = (rRange >= gRange && rRange >= bRange) ? 'r' : (gRange >= bRange ? 'g' : 'b');
          }
        }
        
        if (splitIdx === -1) break;
        
        let boxToSplit = boxes[splitIdx];
        boxToSplit.sort((a, b) => a[splitChan] - b[splitChan]);
        
        let median = Math.floor(boxToSplit.length / 2);
        let box1 = boxToSplit.slice(0, median);
        let box2 = boxToSplit.slice(median);
        
        boxes.splice(splitIdx, 1, box1, box2);
      }
      
      let palette = new Uint8Array(256 * 3);
      let indices = new Uint8Array(4096);
      
      for (let i = 0; i < boxes.length; i++) {
        let box = boxes[i];
        let sumR = 0, sumG = 0, sumB = 0;
        for (let p of box) {
          sumR += p.r; sumG += p.g; sumB += p.b;
        }
        let avgR = Math.round(sumR / box.length);
        let avgG = Math.round(sumG / box.length);
        let avgB = Math.round(sumB / box.length);
        
        palette[i * 3] = avgR;
        palette[i * 3 + 1] = avgG;
        palette[i * 3 + 2] = avgB;
        
        for (let p of box) {
          indices[p.idx] = i;
        }
      }
      
      // Zero out trailing empty slots if image has fewer than 256 unique colors
      for (let i = boxes.length; i < 256; i++) {
        palette[i * 3] = 0; palette[i * 3 + 1] = 0; palette[i * 3 + 2] = 0;
      }
      
      return { palette, indices };
    }

    // Helper to find closest palette index using Euclidean distance squared
    function findClosestPaletteColor(r, g, b, palette) {
      let minDistance = Infinity;
      let bestIndex = 0;
      for (let i = 0; i < 256; i++) {
        const pr = palette[i * 3];
        const pg = palette[i * 3 + 1];
        const pb = palette[i * 3 + 2];
        const distance = (pr - r) * (pr - r) + (pg - g) * (pg - g) + (pb - b) * (pb - b);
        if (distance < minDistance) {
          minDistance = distance;
          bestIndex = i;
        }
      }
      return bestIndex;
    }

    async function processAndUploadImage() {
      if (!uploadedFile) return;
      const statusText = document.getElementById('upload-status');
      statusText.innerText = "Processing image...";
      
      const gamma = parseFloat(document.getElementById('img-gamma').value);
      const brightness = parseFloat(document.getElementById('img-brightness').value) / 100.0;
      const contrast = parseFloat(document.getElementById('img-contrast').value);
      
      const img = new Image();
      img.src = URL.createObjectURL(uploadedFile);
      img.onload = async () => {
        const canvas = document.createElement('canvas');
        canvas.width = 64;
        canvas.height = 64;
        const ctx = canvas.getContext('2d');
        
        // Center crop to preserve aspect ratio
        const minDim = Math.min(img.width, img.height);
        const sx = (img.width - minDim) / 2;
        const sy = (img.height - minDim) / 2;
        ctx.drawImage(img, sx, sy, minDim, minDim, 0, 0, 64, 64);
        
        const imgData = ctx.getImageData(0, 0, 64, 64);
        const pixels = imgData.data;
        
        // Calculate contrast factor
        const factor = (259 * (contrast + 255)) / (255 * (259 - contrast));
        
        // Apply Contrast, Brightness and Gamma scaling, storing as floats for dither precision
        const fPixels = new Float32Array(4096 * 3);
        const adjustedPixelsForPalette = new Uint8Array(4096 * 4);
        for (let i = 0; i < 4096; i++) {
          let r = pixels[i * 4];
          let g = pixels[i * 4 + 1];
          let b = pixels[i * 4 + 2];
          
          // Contrast
          r = factor * (r - 128) + 128;
          g = factor * (g - 128) + 128;
          b = factor * (b - 128) + 128;
          
          r = Math.max(0, Math.min(255, r));
          g = Math.max(0, Math.min(255, g));
          b = Math.max(0, Math.min(255, b));
          
          // Brightness & Gamma Correction
          r = Math.pow((r / 255.0) * brightness, gamma) * 255;
          g = Math.pow((g / 255.0) * brightness, gamma) * 255;
          b = Math.pow((b / 255.0) * brightness, gamma) * 255;
          
          fPixels[i * 3] = r;
          fPixels[i * 3 + 1] = g;
          fPixels[i * 3 + 2] = b;
          
          // Quantizer wants round integers
          adjustedPixelsForPalette[i * 4] = Math.round(r);
          adjustedPixelsForPalette[i * 4 + 1] = Math.round(g);
          adjustedPixelsForPalette[i * 4 + 2] = Math.round(b);
          adjustedPixelsForPalette[i * 4 + 3] = 255;
        }
        
        // Run Median-Cut Quantization on the adjusted pixels to build custom palette
        const quantized = quantizeMedianCut(adjustedPixelsForPalette);
        const palette = quantized.palette;
        
        // Apply Floyd-Steinberg Error Diffusion Dithering
        const indices = new Uint8Array(4096);
        for (let y = 0; y < 64; y++) {
          for (let x = 0; x < 64; x++) {
            const idx = y * 64 + x;
            
            // Get current color values (including accumulated neighbor errors)
            const oldR = fPixels[idx * 3];
            const oldG = fPixels[idx * 3 + 1];
            const oldB = fPixels[idx * 3 + 2];
            
            // Find closest palette index
            const bestIndex = findClosestPaletteColor(oldR, oldG, oldB, palette);
            indices[idx] = bestIndex;
            
            // Get matching palette color
            const newR = palette[bestIndex * 3];
            const newG = palette[bestIndex * 3 + 1];
            const newB = palette[bestIndex * 3 + 2];
            
            // Calculate errors
            const errR = oldR - newR;
            const errG = oldG - newG;
            const errB = oldB - newB;
            
            // Distribute error to 4 neighbors:
            // 1. Right (x+1, y) -> 7/16
            if (x < 63) {
              const nIdx = idx + 1;
              fPixels[nIdx * 3]     = Math.max(0, Math.min(255, fPixels[nIdx * 3]     + errR * 7/16));
              fPixels[nIdx * 3 + 1] = Math.max(0, Math.min(255, fPixels[nIdx * 3 + 1] + errG * 7/16));
              fPixels[nIdx * 3 + 2] = Math.max(0, Math.min(255, fPixels[nIdx * 3 + 2] + errB * 7/16));
            }
            // 2. Bottom-Left (x-1, y+1) -> 3/16
            if (x > 0 && y < 63) {
              const nIdx = idx + 63;
              fPixels[nIdx * 3]     = Math.max(0, Math.min(255, fPixels[nIdx * 3]     + errR * 3/16));
              fPixels[nIdx * 3 + 1] = Math.max(0, Math.min(255, fPixels[nIdx * 3 + 1] + errG * 3/16));
              fPixels[nIdx * 3 + 2] = Math.max(0, Math.min(255, fPixels[nIdx * 3 + 2] + errB * 3/16));
            }
            // 3. Bottom (x, y+1) -> 5/16
            if (y < 63) {
              const nIdx = idx + 64;
              fPixels[nIdx * 3]     = Math.max(0, Math.min(255, fPixels[nIdx * 3]     + errR * 5/16));
              fPixels[nIdx * 3 + 1] = Math.max(0, Math.min(255, fPixels[nIdx * 3 + 1] + errG * 5/16));
              fPixels[nIdx * 3 + 2] = Math.max(0, Math.min(255, fPixels[nIdx * 3 + 2] + errB * 5/16));
            }
            // 4. Bottom-Right (x+1, y+1) -> 1/16
            if (x < 63 && y < 63) {
              const nIdx = idx + 65;
              fPixels[nIdx * 3]     = Math.max(0, Math.min(255, fPixels[nIdx * 3]     + errR * 1/16));
              fPixels[nIdx * 3 + 1] = Math.max(0, Math.min(255, fPixels[nIdx * 3 + 1] + errG * 1/16));
              fPixels[nIdx * 3 + 2] = Math.max(0, Math.min(255, fPixels[nIdx * 3 + 2] + errB * 1/16));
            }
          }
        }
        
        // Build unified payload: 768 bytes palette + 4096 bytes dithered indices = 4864 bytes
        const payload = new Uint8Array(4864);
        payload.set(palette, 0);
        payload.set(indices, 768);
        
        // Upload in 5 chunks of 1024 bytes (last chunk is 768 bytes)
        const chunkSize = 1024;
        try {
          for (let offset = 0; offset < 4864; offset += chunkSize) {
            statusText.innerText = `Uploading chunk ${offset / chunkSize + 1}/5...`;
            const chunk = payload.slice(offset, offset + chunkSize);
            
            let res = await fetch(`/api/upload_chunk?offset=${offset}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/octet-stream' },
              body: chunk
            });
            if (!res.ok) throw new Error("Chunk upload failed");
          }
          statusText.innerText = "Displaying Image!";
          setTimeout(() => { statusText.innerText = ""; }, 3000);
          loadState();
        } catch (e) {
          statusText.innerText = "Upload failed: network error";
          statusText.style.color = "#ef4444";
          setTimeout(() => { statusText.innerText = ""; statusText.style.color = "#10b981"; }, 4000);
        }
      };
    }
    
    // Poll for status updates
    setInterval(async () => {
      try {
        let res = await fetch('/api/state');
        let data = await res.json();
        state.active_theme = data.active_theme;
        state.cycling = data.cycling;
        state.mode = data.mode;
        
        const isImageMode = state.mode === 'image';
        if (isImageMode) {
          document.getElementById('status-text').innerText = 'Active: Rendering Image';
          document.getElementById('btn-restore-flag').style.display = 'block';
          document.getElementById('btn-cycle').disabled = true;
        } else {
          document.getElementById('status-text').innerText = 'Active: ' + state.active_theme.replace('_', ' ');
          document.getElementById('btn-restore-flag').style.display = 'none';
          document.getElementById('btn-cycle').disabled = false;
        }
      } catch (e) {}
    }, 3000);
    
    loadState();
  </script>
</body>
</html>
"""

# Connect to WiFi and Initialize native HTTP Server
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

ip_address = "No WiFi"
server = None
if ssid and password:
    try:
        print("WiFi: Connecting...")
        wifi.radio.connect(ssid, password)
        ip_address = str(wifi.radio.ipv4_address)
        print("WiFi Connected!")
        print("IP Address:", ip_address)
        
        # Setup Server on native socketpool
        pool = socketpool.SocketPool(wifi.radio)
        server = Server(pool)
        
        @server.route("/")
        def index_route(request: Request):
            return Response(request, INDEX_HTML, content_type="text/html; charset=utf-8")
            
        @server.route("/api/state")
        def state_route(request: Request):
            data = {
                "active_theme": active_theme,
                "cycling": is_cycling,
                "star_layout": star_layout,
                "vertical_mode": vertical_mode,
                "themes": THEMES,
                "enabled_themes": enabled_themes,
                "cycle_interval": cycle_interval,
                "brightness": brightness,
                "mode": active_mode
            }
            return Response(request, json.dumps(data), content_type="application/json")
            
        @server.route("/api/control")
        def control_route(request: Request):
            global is_cycling, star_layout, vertical_mode, active_theme, enabled_themes, cycle_interval, brightness, active_mode, transition_state, transition_frame, next_theme, current_bit_depth
            params = request.query_params
            needs_save = False
            
            if "cycling" in params:
                is_cycling = (params["cycling"] == "true")
                needs_save = True
                
            if "star_layout" in params:
                star_layout = int(params["star_layout"])
                needs_save = True
                
            if "vertical_mode" in params:
                vertical_mode = int(params["vertical_mode"])
                needs_save = True
                
            if "theme" in params:
                if params["theme"] in THEMES:
                    next_theme = params["theme"]
                    transition_state = "fade_out"
                    transition_frame = 0
                    is_cycling = False # Stop cycling when theme manually forced
                    active_mode = "flag"
                    needs_save = True
                    
            if "mode" in params:
                val = params["mode"]
                if val == "flag":
                    active_mode = "flag"
                    is_cycling = True
                    if current_bit_depth != 2:
                        init_display_with_depth(2)
                    render_static_bitmap(star_layout, vertical_mode)
                    transition_state = "fade_in"
                    transition_frame = 0
                    transition_scale = 0.0
                    needs_save = True
                    
            if "enabled_themes" in params:
                val = params["enabled_themes"]
                if val:
                    enabled_themes = [t for t in val.split(",") if t in THEMES]
                else:
                    enabled_themes = []
                needs_save = True
                
            if "cycle_interval" in params:
                cycle_interval = float(params["cycle_interval"])
                needs_save = True
                
            if "brightness" in params:
                brightness = float(params["brightness"])
                needs_save = True
                
            if needs_save:
                save_config()
                
            return Response(request, json.dumps({"status": "ok"}), content_type="application/json")

        @server.route("/api/upload_chunk", methods=[POST])
        def upload_chunk_route(request: Request):
            global is_cycling, active_mode
            params = request.query_params
            offset = int(params.get("offset", 0))
            chunk_data = request.body
            
            # Write chunk directly to our static buffer
            image_buffer[offset:offset+len(chunk_data)] = chunk_data
            
            # If all 5 chunks are fully received (reaches 4864 bytes)
            if offset + len(chunk_data) == 4864:
                is_cycling = False
                active_mode = "image"
                
                # Reinitialize display to 5-bit for rich custom pictures!
                if current_bit_depth != 5:
                    init_display_with_depth(5)
                
                # 1. Unpack custom 256-color palette (first 768 bytes) into hardware display palette
                for idx in range(256):
                    r_c = image_buffer[idx * 3]
                    g_c = image_buffer[idx * 3 + 1]
                    b_c = image_buffer[idx * 3 + 2]
                    palette[idx] = (r_c, g_c, b_c)
                
                # 2. Draw quantized indices (remaining 4096 bytes) to the left-hand panel (columns 0 to 63)
                pixel_offset = 768
                for y in range(64):
                    for x in range(64):
                        bitmap[x, y] = image_buffer[pixel_offset + y * 64 + x]
                
                # 3. Push frame immediately to the screen
                display.refresh()
                
            return Response(request, json.dumps({"status": "ok"}), content_type="application/json")
            
        # Start server listening on all interfaces ("0.0.0.0") on port 8080
        server.start(port=8080)
        print("HTTP Server successfully started on port 8080.")
    except Exception as e:
        print("WiFi/Server setup failed:", e)
else:
    print("WiFi: No SSID or password set in settings.toml")

def hsv_to_rgb(h, s, v):
    """Utility to convert HSV values (0..1) to RGB (0..255)."""
    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    
    r, g, b = 0.0, 0.0, 0.0
    if i % 6 == 0:
        r, g, b = v, t, p
    elif i % 6 == 1:
        r, g, b = q, v, p
    elif i % 6 == 2:
        r, g, b = p, v, t
    elif i % 6 == 3:
        r, g, b = p, q, v
    elif i % 6 == 4:
        r, g, b = t, p, v
    elif i % 6 == 5:
        r, g, b = v, p, q
        
    return (int(r * 255), int(g * 255), int(b * 255))

def get_theme_colors(theme_name, t=0.0):
    """Returns 13 stripe colors, canton color, and star color for the specified theme."""
    stripes = [(0, 0, 0)] * 13
    
    # 1. Classic Old Glory
    if theme_name == "classic":
        red = (178, 34, 52)
        white = (255, 255, 255)
        for i in range(13):
            stripes[i] = red if (i % 2 == 0) else white
        canton = (40, 39, 90)
        star = (255, 255, 255)
        
    # 2. Pride 6-Stripe Rainbow
    elif theme_name == "pride6":
        violet = (120, 32, 128)
        blue = (0, 0, 255)
        green = (0, 128, 0)
        yellow = (255, 255, 0)
        orange = (255, 165, 0)
        red = (255, 0, 0)
        stripes[0] = stripes[1] = violet
        stripes[2] = stripes[3] = blue
        stripes[4] = stripes[5] = green
        stripes[6] = stripes[7] = yellow
        stripes[8] = stripes[9] = orange
        stripes[10] = stripes[11] = stripes[12] = red
        canton = (26, 14, 64)
        star = (255, 255, 255)

    # 3. Gilbert Baker Pride (8-Stripe)
    elif theme_name == "pride8":
        violet = (120, 32, 128)
        indigo = (26, 15, 92)
        turquoise = (0, 162, 255)
        green = (0, 128, 0)
        yellow = (255, 255, 0)
        orange = (255, 165, 0)
        red = (255, 0, 0)
        pink = (255, 105, 180)
        stripes[0] = violet
        stripes[1] = indigo
        stripes[2] = stripes[3] = turquoise
        stripes[4] = green
        stripes[5] = stripes[6] = yellow
        stripes[7] = orange
        stripes[8] = stripes[9] = red
        stripes[10] = stripes[11] = stripes[12] = pink
        canton = (43, 16, 74)
        star = (255, 255, 255)

    # 4. Trans Pride
    elif theme_name == "transgender":
        l_blue = (91, 206, 250)
        pink = (245, 169, 184)
        white = (255, 255, 255)
        stripes[0] = stripes[1] = stripes[2] = l_blue
        stripes[3] = stripes[4] = stripes[5] = pink
        stripes[6] = stripes[7] = white
        stripes[8] = stripes[9] = stripes[10] = pink
        stripes[11] = stripes[12] = l_blue
        canton = (91, 206, 250)
        star = (255, 255, 255)

    # 5. Bi Pride
    elif theme_name == "bisexual":
        blue = (0, 38, 168)
        purple = (155, 79, 150)
        pink = (214, 2, 112)
        for i in range(5): stripes[i] = blue
        for i in range(5, 8): stripes[i] = purple
        for i in range(8, 13): stripes[i] = pink
        canton = (155, 79, 150)
        star = (214, 2, 112)

    # 6. Lesbian Pride
    elif theme_name == "lesbian":
        dark_rose = (163, 2, 98)
        pink = (196, 64, 139)
        white = (255, 255, 255)
        l_orange = (228, 98, 34)
        d_orange = (165, 0, 0)
        stripes[0] = stripes[1] = stripes[2] = dark_rose
        stripes[3] = stripes[4] = pink
        stripes[5] = stripes[6] = white
        stripes[7] = stripes[8] = stripes[9] = l_orange
        stripes[10] = stripes[11] = stripes[12] = d_orange
        canton = (163, 2, 98)
        star = (255, 255, 255)

    # 7. Non-Binary Pride
    elif theme_name == "nonbinary":
        black = (20, 20, 20)
        purple = (156, 89, 209)
        white = (255, 255, 255)
        yellow = (255, 244, 48)
        stripes[0] = stripes[1] = stripes[2] = black
        stripes[3] = stripes[4] = stripes[5] = purple
        stripes[6] = stripes[7] = stripes[8] = white
        stripes[9] = stripes[10] = stripes[11] = stripes[12] = yellow
        canton = (156, 89, 209)
        star = (255, 244, 48)

    # 8. Tactical Thin Line themes
    else:
        black = (18, 18, 18)
        grey = (210, 210, 210)
        for i in range(13):
            stripes[i] = black if (i % 2 == 0) else grey
        canton = (12, 12, 12)
        star = (240, 240, 240)
        
        if theme_name == "thin_blue":
            stripes[7] = (0, 45, 255)
        elif theme_name == "thin_red":
            stripes[7] = (229, 0, 0)
        elif theme_name == "first_responders":
            stripes[7] = (0, 45, 255)
            stripes[9] = (229, 0, 0)
        elif theme_name == "thin_green":
            stripes[7] = (0, 163, 0)
        elif theme_name == "thin_gold":
            stripes[7] = (255, 215, 0)
        elif theme_name == "all_responders":
            stripes[1] = (127, 127, 127)  # Corrections Grey
            stripes[3] = (255, 215, 0)    # Dispatcher Gold
            stripes[5] = (0, 163, 0)      # Military Green
            stripes[7] = (0, 45, 255)     # Police Blue
            stripes[9] = (229, 0, 0)      # Firefighter Red
            stripes[11] = (255, 255, 255) # EMS White
            
    return stripes, canton, star

target_stripes, target_canton, target_star = get_theme_colors(active_theme, 0.0)

current_stripes = [[float(c) for c in s] for s in target_stripes]
current_canton = [float(c) for c in target_canton]
current_star = [float(c) for c in target_star]

def update_hardware_palette():
    """Builds a 16-step flat palette gradient using the active colors with software brightness scaling."""
    for i in range(13):
        color = current_stripes[i]
        for s in range(16):
            shading = 0.70 + 0.30 * (s / 15.0)
            palette[i * 16 + s] = (
                int(color[0] * shading * brightness * transition_scale),
                int(color[1] * shading * brightness * transition_scale),
                int(color[2] * shading * brightness * transition_scale)
            )
            
    for s in range(16):
        shading = 0.70 + 0.30 * (s / 15.0)
        palette[208 + s] = (
            int(current_canton[0] * shading * brightness * transition_scale),
            int(current_canton[1] * shading * brightness * transition_scale),
            int(current_canton[2] * shading * brightness * transition_scale)
        )
        
    for s in range(16):
        shading = 0.70 + 0.30 * (s / 15.0)
        palette[224 + s] = (
            int(current_star[0] * shading * brightness * transition_scale),
            int(current_star[1] * shading * brightness * transition_scale),
            int(current_star[2] * shading * brightness * transition_scale)
        )

# Pre-calculate star coordinate sets (Landscape layout, 128x64 flag size)
stars_50_horizontal = []
for r in range(1, 10):
    for c in range(1, 12):
        if (r % 2 == 1 and c % 2 == 1) or (r % 2 == 0 and c % 2 == 0):
            stars_50_horizontal.append((int((c / 12.0) * 51.0), int((r / 10.0) * 34.0)))

stars_13_horizontal = []
for i in range(13):
    angle = (i * 2.0 * math.pi) / 13.0
    star_x = int(math.cos(angle) * 12.5 + 25.5)
    star_y = int(math.sin(angle) * 12.5 + 17.0)
    stars_13_horizontal.append((star_x, star_y))

# Pre-calculate star coordinate sets (Portrait layout, 64x128 flag size drawn inside 128x64 canvas)
stars_50_vertical = []
for r in range(1, 10):
    for c in range(1, 12):
        if (r % 2 == 1 and c % 2 == 1) or (r % 2 == 0 and c % 2 == 0):
            star_y = int((c / 12.0) * 34.0)
            star_x = int((r / 10.0) * 51.0) + 13
            stars_50_vertical.append((star_x, star_y))

stars_13_vertical = []
for i in range(13):
    angle = (i * 2.0 * math.pi) / 13.0
    star_y = int(math.cos(angle) * 12.5 + 17.0)
    star_x = int(math.sin(angle) * 12.5 + 38.5)
    stars_13_vertical.append((star_x, star_y))

stars_50_horizontal_set = set(stars_50_horizontal)
stars_13_horizontal_set = set(stars_13_horizontal)
stars_50_vertical_set = set(stars_50_vertical)
stars_13_vertical_set = set(stars_13_vertical)

def is_in_star(x, y, active_stars):
    """Checks if a pixel coordinate is part of a 3x3 pixel detailed star shape (5-pixel cross)."""
    if (x, y) in active_stars:
        return True
    if (x - 1, y) in active_stars:
        return True
    if (x + 1, y) in active_stars:
        return True
    if (x, y - 1) in active_stars:
        return True
    if (x, y + 1) in active_stars:
        return True
    return False

def render_static_bitmap(layout_mode, vert_mode):
    """Draws the flag shapes on the 128x64 bitmap once."""
    if vert_mode == 1:
        active_stars = stars_13_vertical_set if layout_mode == 1 else stars_50_vertical_set
    else:
        active_stars = stars_13_horizontal_set if layout_mode == 1 else stars_50_horizontal_set
        
    for y in range(64):
        for x in range(128):
            if vert_mode == 1:
                # Rotated flag layout: canton in the top right
                in_canton = (y < 34 and x >= 13 and x < 64)
                stripe_idx = (y * 13) // 64
            else:
                # Standard flag layout: canton on the left of the single panel (columns 0-50)
                in_canton = (x >= 0 and x < 51 and y < 34)
                stripe_idx = (y * 13) // 64
                
            stripe_base_offset = stripe_idx * 16
            
            if in_canton:
                if is_in_star(x, y, active_stars):
                    bitmap[x, y] = 224 + 15  # Index 224 + 15 = Star color
                else:
                    bitmap[x, y] = 208 + 15  # Index 208 + 15 = Canton background color
            else:
                bitmap[x, y] = stripe_base_offset + 15  # Stripes gradient indices

# Initial setup
render_static_bitmap(star_layout, vertical_mode)
update_hardware_palette()

start_time = time.monotonic()
last_cycle_time = start_time
last_star_layout = star_layout
last_vertical_mode = vertical_mode

print("Animated Flag Matrix running loop!")

while True:
    now = time.monotonic()
    t = now - start_time
    
    # 1. HTTP Server loop poll
    if server:
        try:
            server.poll()
        except Exception as e:
            print("HTTP Server poll error:", e)
            
    # If rendering an image, skip animation calculations to save CPU cycle overhead
    if active_mode == "image":
        time.sleep(0.016)
        continue
            
    # 2. Check layout or orientation change
    if (star_layout != last_star_layout) or (vertical_mode != last_vertical_mode):
        last_star_layout = star_layout
        last_vertical_mode = vertical_mode
        print("Changing layout. Vertical Mode:", vertical_mode)
        render_static_bitmap(star_layout, vertical_mode)
        
    # 3. Handle dip-to-black transition state
    global transition_state, transition_frame, active_theme, next_theme, transition_scale
    if transition_state == "fade_out":
        transition_frame += 1
        transition_scale = 1.0 - (transition_frame / 20.0)
        if transition_frame >= 20:
            transition_state = "hold_black"
            transition_frame = 0
            transition_scale = 0.0
    elif transition_state == "hold_black":
        transition_frame += 1
        transition_scale = 0.0
        if transition_frame >= 5:
            active_theme = next_theme
            if active_mode == "flag" and current_bit_depth != 2:
                init_display_with_depth(2)
            render_static_bitmap(star_layout, vertical_mode)
            transition_state = "fade_in"
            transition_frame = 0
    elif transition_state == "fade_in":
        transition_frame += 1
        transition_scale = transition_frame / 20.0
        if transition_frame >= 20:
            transition_state = "running"
            transition_frame = 0
            transition_scale = 1.0
            
    # 4. Cycle theme timer (only if is_cycling is enabled and not transitioning)
    if is_cycling and transition_state == "running" and (now - last_cycle_time > cycle_interval):
        last_cycle_time = now
        if enabled_themes:
            try:
                current_idx = enabled_themes.index(active_theme)
                next_idx = (current_idx + 1) % len(enabled_themes)
                new_theme = enabled_themes[next_idx]
            except ValueError:
                new_theme = enabled_themes[0]
            next_theme = new_theme
            transition_state = "fade_out"
            transition_frame = 0
            print("Cycling to theme:", next_theme)
            
    # Fetch theme colors
    target_stripes, target_canton, target_star = get_theme_colors(active_theme, t)
    
    # 5. Abrupt transitions: set current colors directly to target
    for i in range(13):
        for c in range(3):
            current_stripes[i][c] = target_stripes[i][c]
    for c in range(3):
        current_canton[c] = target_canton[c]
        current_star[c] = target_star[c]
        
    update_hardware_palette()
    display.refresh()
    time.sleep(0.016)
