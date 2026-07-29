# Physical LED Matrix Flag - Auto-Cycling, Fading, and Accelerometer Auto-Rotation
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

# Release any active displays to free up pins
displayio.release_displays()

# Pin configuration for Adafruit Matrix Portal M4
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

# Create 64x32 bitmap for draw operations
bitmap = displayio.Bitmap(64, 32, 256)

# Build a palette of 256 colors segmented into 15 logical groups (16 slots per group)
palette = displayio.Palette(256)

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
CYCLE_INTERVAL = 10.0      # Cycle to next flag every 10 seconds
TRANSITION_SPEED = 0.08    # Interpolation rate per frame (~1.2s crossfade)
star_layout = 0            # 0 = 50-star grid, 1 = 13-star circle (Betsy Ross)
vertical_mode = 0          # 0 = horizontal (landscape), 1 = vertical (portrait)

# Initialize I2C Accelerometer for auto-rotation
accelerometer = None
try:
    import adafruit_lis3dh
    # The LIS3DH on the Matrix Portal M4 is wired to the internal I2C bus:
    i2c = board.I2C()
    # The I2C address of LIS3DH on Matrix Portal is 0x19
    accelerometer = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x19)
    accelerometer.range = adafruit_lis3dh.RANGE_2_G
    print("LIS3DH Accelerometer initialized successfully! Auto-rotation active.")
except Exception as e:
    print("Accelerometer not initialized (missing library or hardware issue):", e)
    print("Falling back to manual horizontal layout mode.")

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

    # 4. Trans Pride 🏳️‍⚧️
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
            stripes[1] = (127, 127, 127)  # Correctional Grey
            stripes[3] = (255, 215, 0)    # Dispatcher Gold
            stripes[5] = (0, 163, 0)      # Military Green
            stripes[7] = (0, 45, 255)     # Police Blue
            stripes[9] = (229, 0, 0)      # Firefighter Red
            stripes[11] = (255, 255, 255) # EMS White
            
    return stripes, canton, star

# Initialize active colors
current_theme_idx = 0
active_theme = THEMES[current_theme_idx]
target_stripes, target_canton, target_star = get_theme_colors(active_theme, 0.0)

current_stripes = [[float(c) for c in s] for s in target_stripes]
current_canton = [float(c) for c in target_canton]
current_star = [float(c) for c in target_star]

def update_hardware_palette():
    """Builds a 16-step flat palette gradient using the active colors (shading level 15 is full brightness)."""
    for i in range(13):
        color = current_stripes[i]
        for s in range(16):
            shading = 0.70 + 0.30 * (s / 15.0)
            palette[i * 16 + s] = (
                int(color[0] * shading),
                int(color[1] * shading),
                int(color[2] * shading)
            )
            
    for s in range(16):
        shading = 0.70 + 0.30 * (s / 15.0)
        palette[208 + s] = (
            int(current_canton[0] * shading),
            int(current_canton[1] * shading),
            int(current_canton[2] * shading)
        )
        
    for s in range(16):
        shading = 0.70 + 0.30 * (s / 15.0)
        palette[224 + s] = (
            int(current_star[0] * shading),
            int(current_star[1] * shading),
            int(current_star[2] * shading)
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

# Pre-calculate star coordinate sets (Portrait layout - rotated 90 degrees)
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

# Convert to sets for fast O(1) hash lookup
stars_50_horizontal_set = set(stars_50_horizontal)
stars_13_horizontal_set = set(stars_13_horizontal)
stars_50_vertical_set = set(stars_50_vertical)
stars_13_vertical_set = set(stars_13_vertical)

def render_static_bitmap(layout_mode, vert_mode):
    """Draws the flag shapes on the bitmap once. Shading index 15 means flat full-brightness."""
    if vert_mode == 1:
        active_stars = stars_13_vertical_set if layout_mode == 1 else stars_50_vertical_set
    else:
        active_stars = stars_13_horizontal_set if layout_mode == 1 else stars_50_horizontal_set
        
    for y in range(32):
        for x in range(64):
            if vert_mode == 1:
                # Vertical hanging mode (Canton is at top-left: y < 17 and x >= 38)
                in_canton = (y < 17 and x >= 38)
                stripe_idx = (y * 13) // 32
            else:
                # Horizontal mode (Canton is at top-left: x < 26 and y < 17)
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

# Initial bitmap draw
render_static_bitmap(star_layout, vertical_mode)
update_hardware_palette()

# Display configuration
tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
group = displayio.Group()
group.append(tile_grid)
display.root_group = group

start_time = time.monotonic()
last_cycle_time = start_time
last_star_layout = star_layout
last_vertical_mode = vertical_mode

print("Animated Flag Matrix Running with Accelerometer Auto-Rotation!")

while True:
    now = time.monotonic()
    t = now - start_time
    
    # 1. Read Accelerometer to determine layout orientation
    if accelerometer:
        try:
            x_acc, y_acc, z_acc = accelerometer.acceleration
            # If long axis (x) has stronger gravitational pull than short axis (y)
            if abs(x_acc) > abs(y_acc) + 2.0:
                vertical_mode = 1 # Portrait
            elif abs(y_acc) > abs(x_acc) + 2.0:
                vertical_mode = 0 # Landscape
        except Exception as e:
            print("Error polling accelerometer:", e)
            
    # 2. Check if layout or orientation changes triggered a redraw
    if (star_layout != last_star_layout) or (vertical_mode != last_vertical_mode):
        last_star_layout = star_layout
        last_vertical_mode = vertical_mode
        print("Flipping display layout. Vertical Mode: " + str(vertical_mode))
        render_static_bitmap(star_layout, vertical_mode)
        
    # 3. Cycle theme timer
    if now - last_cycle_time > CYCLE_INTERVAL:
        last_cycle_time = now
        current_theme_idx = (current_theme_idx + 1) % len(THEMES)
        active_theme = THEMES[current_theme_idx]
        print("Cycling to theme: " + active_theme)
        
    # Retrieve target colors
    target_stripes, target_canton, target_star = get_theme_colors(active_theme, t)
    
    # 4. Lerp active colors towards target colors
    for i in range(13):
        for c in range(3):
            current_stripes[i][c] += (target_stripes[i][c] - current_stripes[i][c]) * TRANSITION_SPEED
    for c in range(3):
        current_canton[c] += (target_canton[c] - current_canton[c]) * TRANSITION_SPEED
        current_star[c] += (target_star[c] - current_star[c]) * TRANSITION_SPEED
        
    # 5. Push colors to hardware palette
    update_hardware_palette()
    
    # Refresh display buffer
    display.refresh()
    time.sleep(0.016)
