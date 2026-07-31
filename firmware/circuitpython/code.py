# Physical LED Matrix Flag - Auto-Cycling, Fading, Accelerometer, and Phone Web Server
# Target Board: Adafruit Matrix Portal M4 (SAMD51)
# Display: 64x32 RGB HUB75 LED Panel (1/16 Scan)
# 
# Save this file as 'code.py' on your CIRCUITPY drive.

import board
import rgbmatrix
import framebufferio
import displayio
import time
import math
import os
import json
import microcontroller
from digitalio import DigitalInOut

# Release any active displays to free up pins
displayio.release_displays()

# Pin configuration for Adafruit Matrix Portal M4 HUB75 Display
matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=32,
    bit_depth=4,  # Smooth color depth
    rgb_pins=[
        board.MTX_R1, board.MTX_G1, board.MTX_B1,
        board.MTX_R2, board.MTX_G2, board.MTX_B2
    ],
    addr_pins=[
        board.MTX_ADDRA, board.MTX_ADDRB,
        board.MTX_ADDRC, board.MTX_ADDRD
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE
)

# Associate matrix with displayio framebuffer
display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)

# Configurable Parameters
THEMES = [
    "classic",
    "pride6",
    "pride8",
    "transgender",
    "bisexual",
    "lesbian",
    "nonbinary",
    "rainbow_wave",
    "thin_blue",
    "thin_red",
    "first_responders",
    "thin_green",
    "thin_gold",
    "all_responders"
]
TRANSITION_SPEED = 0.08    # Interpolation rate per frame (~1.2s crossfade)

# Active State Variables
star_layout = 0            # 0 = 50-star grid, 1 = 13-star circle (Betsy Ross)
vertical_mode = 0          # 0 = horizontal (landscape), 1 = vertical (portrait)
is_cycling = True          # Enable/disable theme cycling
enabled_themes = THEMES.copy() # List of themes allowed in cycle loop
active_theme = THEMES[0]
cycle_interval = 10.0      # Cycle to next flag every X seconds
brightness = 1.0           # LED matrix brightness (0.0 to 1.0)


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
display.brightness = brightness

# 1. Connect to local WiFi using SPI co-processor (ESP32 AirLift)
ip_address = "No WiFi"
esp = None
try:
    import busio
    from adafruit_esp32spi import adafruit_esp32spi
    
    # Initialize ESP32 SPI connection
    esp32_cs = DigitalInOut(board.ESP_CS)
    esp32_ready = DigitalInOut(board.ESP_BUSY)
    esp32_reset = DigitalInOut(board.ESP_RESET)
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
    
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    
    if ssid and password:
        print("WiFi: Connecting...")
        display.refresh()
        esp.connect_AP(ssid, password)
        ip_address = esp.pretty_ip(esp.ip_address)
        print("WiFi Connected!")
        print("IP Address:")
        print(ip_address)
        display.refresh()
        # Sleep for 5 seconds to let the user read the IP address on the default terminal screen
        time.sleep(5.0)
    else:
        print("WiFi: No config")
        display.refresh()
except Exception as e:
    print("WiFi Failed:", e)
    display.refresh()
    time.sleep(2.0)

# 2. Setup WSGI HTTP Server
wsgi_server = None
if esp and esp.is_connected:
    try:
        # Inject our custom socket module into sys.modules to satisfy the WSGI library
        # because the board's frozen adafruit_esp32spi lacks adafruit_esp32spi_socket.
        import sys
        import adafruit_esp32spi
        import adafruit_esp32spi_socket
        adafruit_esp32spi.adafruit_esp32spi_socket = adafruit_esp32spi_socket
        sys.modules['adafruit_esp32spi.adafruit_esp32spi_socket'] = adafruit_esp32spi_socket
        
        import adafruit_wsgi.esp32spi_wsgiserver as server
        from adafruit_wsgi.wsgi_app import WSGIApp
        import adafruit_esp32spi.adafruit_esp32spi_socket as socket
        
        web_app = WSGIApp()
        
        INDEX_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LED Flag Control Panel</title>
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
    <h1>🇺🇸 Flag Control</h1>
    <div class="status" id="status-text">Connecting...</div>
    
    <div class="btn-container">
      <button class="btn" id="btn-cycle" onclick="toggleCycle()">Theme Cycling: ON</button>
      <button class="btn btn-secondary" onclick="toggleStarLayout()">Toggle Star Layout</button>
      <button class="btn btn-secondary" onclick="toggleVerticalLayout()">Toggle Vertical Layout</button>
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
  
  <div class="card">
    <h2>Cycle List & Themes</h2>
    <div id="themes-list"></div>
  </div>

  <script>
    let state = {};
    
    function parseQuery(q) {
      return q;
    }
    
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

    async function loadState() {
      try {
        let res = await fetch('/api/state');
        state = await res.json();
        
        document.getElementById('status-text').innerText = 'Active: ' + state.active_theme.replace('_', ' ');
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
          let isActive = state.active_theme === theme;
          let labelText = theme.replace('_', ' ');
          
          html += `<div class="theme-row">
            <div class="theme-info" onclick="selectTheme('${theme}')" style="cursor: pointer; flex-grow: 1;">
              <span class="theme-name" style="${isActive ? 'color: #38bdf8;' : ''}">${labelText}</span>
              ${isActive ? '<span class="theme-active-tag">CURRENTLY RENDERING</span>' : ''}
            </div>
            <label class="switch">
              <input type="checkbox" ${checked} onchange="toggleTheme('${theme}', this.checked)">
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
    
    // Poll for status updates
    setInterval(async () => {
      try {
        let res = await fetch('/api/state');
        let data = await res.json();
        state.active_theme = data.active_theme;
        state.cycling = data.cycling;
        document.getElementById('status-text').innerText = 'Active: ' + state.active_theme.replace('_', ' ');
        document.getElementById('btn-cycle').innerText = 'Theme Cycling: ' + (state.cycling ? 'ON' : 'OFF');
        document.getElementById('btn-cycle').className = state.cycling ? 'btn' : 'btn btn-secondary';
      } catch (e) {}
    }, 3000);
    
    loadState();
  </script>
</body>
</html>
"""



        @web_app.route("/")
        def index_route(request):
            return ("200 OK", [("Content-Type", "text/html")], [INDEX_HTML])

        @web_app.route("/api/state")
        def state_route(request):
            data = {
                "active_theme": active_theme,
                "cycling": is_cycling,
                "star_layout": star_layout,
                "vertical_mode": vertical_mode,
                "themes": THEMES,
                "enabled_themes": enabled_themes,
                "cycle_interval": cycle_interval,
                "brightness": brightness
            }
            return ("200 OK", [("Content-Type", "application/json")], [json.dumps(data)])

        @web_app.route("/api/control")
        def control_route(request):
            global is_cycling, star_layout, vertical_mode, active_theme, enabled_themes, cycle_interval, brightness
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
                    active_theme = params["theme"]
                    is_cycling = False # Stop cycling when theme manually forced
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
                display.brightness = brightness
                needs_save = True
                
            if needs_save:
                save_config()
                
            return ("200 OK", [("Content-Type", "application/json")], [json.dumps({"status": "ok"})])

        server.set_interface(esp)
        socket.set_interface(esp)
        wsgi_server = server.WSGIServer(port=80, application=web_app)
        wsgi_server.start()
        print("WSGI HTTP Server successfully started on port 80.")
    except Exception as e:
        print("Failed to initialize WSGI HTTP Server:", e)

# 3. Create 64x32 bitmap for draw operations
bitmap = displayio.Bitmap(64, 32, 256)
palette = displayio.Palette(256)

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

    # 8. Dynamic Scrolling Rainbow
    elif theme_name == "rainbow_wave":
        for i in range(13):
            hue = (i / 12.0 * 1.3 - t * 0.45) % 1.0
            stripes[i] = hsv_to_rgb(hue, 1.0, 1.0)
        canton = hsv_to_rgb((t * 0.08) % 1.0, 0.9, 0.22)
        star = hsv_to_rgb((t * 0.25) % 1.0, 0.85, 1.0)
        
    # 9. Tactical Thin Line themes
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
                int(color[0] * shading * brightness),
                int(color[1] * shading * brightness),
                int(color[2] * shading * brightness)
            )
            
    for s in range(16):
        shading = 0.70 + 0.30 * (s / 15.0)
        palette[208 + s] = (
            int(current_canton[0] * shading * brightness),
            int(current_canton[1] * shading * brightness),
            int(current_canton[2] * shading * brightness)
        )
        
    for s in range(16):
        shading = 0.70 + 0.30 * (s / 15.0)
        palette[224 + s] = (
            int(current_star[0] * shading * brightness),
            int(current_star[1] * shading * brightness),
            int(current_star[2] * shading * brightness)
        )

# Pre-calculate star coordinate sets (Landscape layout)
stars_50_horizontal = []
for r in range(1, 10):
    for c in range(1, 12):
        if (r % 2 == 1 and c % 2 == 1) or (r % 2 == 0 and c % 2 == 0):
            stars_50_horizontal.append((int((c / 12.0) * 26.0), int((r / 10.0) * 17.0)))

stars_13_horizontal = []
for i in range(13):
    angle = i * (2.0 * math.pi / 13.0) - math.pi / 2.0
    star_x = int((math.cos(angle) / 1.529) * 0.33 * 26.0 + 13.0)
    star_y = int(math.sin(angle) * 0.33 * 17.0 + 8.5)
    stars_13_horizontal.append((star_x, star_y))

# Pre-calculate star coordinate sets (Portrait layout)
stars_50_vertical = []
for r in range(1, 10):
    for c in range(1, 12):
        if (r % 2 == 1 and c % 2 == 1) or (r % 2 == 0 and c % 2 == 0):
            star_y = int((c / 12.0) * 17.0)
            star_x = int((r / 10.0) * 26.0) + 38
            stars_50_vertical.append((star_x, star_y))

stars_13_vertical = []
for i in range(13):
    angle = i * (2.0 * math.pi / 13.0) - math.pi / 2.0
    star_y = int((math.cos(angle) * 0.6538) * 0.33 * 17.0 + 8.5)
    star_x = int(math.sin(angle) * 0.33 * 26.0 + 13.0) + 38
    stars_13_vertical.append((star_x, star_y))

stars_50_horizontal_set = set(stars_50_horizontal)
stars_13_horizontal_set = set(stars_13_horizontal)
stars_50_vertical_set = set(stars_50_vertical)
stars_13_vertical_set = set(stars_13_vertical)

def render_static_bitmap(layout_mode, vert_mode):
    """Draws the flag shapes on the bitmap once."""
    if vert_mode == 1:
        active_stars = stars_13_vertical_set if layout_mode == 1 else stars_50_vertical_set
    else:
        active_stars = stars_13_horizontal_set if layout_mode == 1 else stars_50_horizontal_set
        
    for y in range(32):
        for x in range(64):
            if vert_mode == 1:
                in_canton = (y < 17 and x >= 38)
                stripe_idx = (y * 13) // 32
            else:
                in_canton = (x < 26 and y < 17)
                stripe_idx = (y * 13) // 32
                
            stripe_base_offset = stripe_idx * 16
            
            if in_canton:
                if (x, y) in active_stars:
                    bitmap[x, y] = 224 + 15
                else:
                    bitmap[x, y] = 208 + 15
            else:
                bitmap[x, y] = stripe_base_offset + 15

# Initial setup
render_static_bitmap(star_layout, vertical_mode)
update_hardware_palette()

# Display configuration
tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
group = displayio.Group()
group.append(tile_grid)
display.root_group = group

# Initialize Accelerometer
accelerometer = None
try:
    import adafruit_lis3dh
    i2c = board.I2C()
    accelerometer = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x19)
    accelerometer.range = adafruit_lis3dh.RANGE_2_G
    print("LIS3DH Accelerometer initialized successfully!")
except Exception as e:
    print("Accelerometer not initialized:", e)

start_time = time.monotonic()
last_cycle_time = start_time
last_star_layout = star_layout
last_vertical_mode = vertical_mode

print("Animated Flag Matrix running loop!")

while True:
    now = time.monotonic()
    t = now - start_time
    
    # 1. WSGI Server loop check
    if wsgi_server:
        try:
            wsgi_server.update_poll()
        except Exception as e:
            print("WSGI Server loop error:", e)
            
    # 2. Read Accelerometer for auto-rotation
    if accelerometer:
        try:
            x_acc, y_acc, z_acc = accelerometer.acceleration
            if abs(x_acc) > abs(y_acc) + 2.0:
                vertical_mode = 1
            elif abs(y_acc) > abs(x_acc) + 2.0:
                vertical_mode = 0
        except Exception as e:
            print("Error polling accelerometer:", e)
            
    # 3. Check layout or orientation change
    if (star_layout != last_star_layout) or (vertical_mode != last_vertical_mode):
        last_star_layout = star_layout
        last_vertical_mode = vertical_mode
        print("Changing layout. Vertical Mode:", vertical_mode)
        render_static_bitmap(star_layout, vertical_mode)
        
    # 4. Cycle theme timer (only if is_cycling is enabled)
    if is_cycling and (now - last_cycle_time > cycle_interval):
        last_cycle_time = now
        if enabled_themes:
            try:
                current_idx = enabled_themes.index(active_theme)
                next_idx = (current_idx + 1) % len(enabled_themes)
                active_theme = enabled_themes[next_idx]
            except ValueError:
                active_theme = enabled_themes[0]
            print("Cycling to theme:", active_theme)
            
    # Fetch theme colors
    target_stripes, target_canton, target_star = get_theme_colors(active_theme, t)
    
    # 5. Lerp active colors towards target
    for i in range(13):
        for c in range(3):
            current_stripes[i][c] += (target_stripes[i][c] - current_stripes[i][c]) * TRANSITION_SPEED
    for c in range(3):
        current_canton[c] += (target_canton[c] - current_canton[c]) * TRANSITION_SPEED
        current_star[c] += (target_star[c] - current_star[c]) * TRANSITION_SPEED
        
    update_hardware_palette()
    display.refresh()
    time.sleep(0.016)
