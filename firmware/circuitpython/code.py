# Physical LED Matrix Flag - Auto-Cycling & Smooth Fading Edition
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
    bit_depth=4,  # Expanded to 4 bits (16 colors per stripe) for smoother gradients
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

# Build a palette of 256 colors segmented into 15 logical groups (16 slots per group):
# Slots 0..207 (13 stripes * 16 = 208 slots): 13 stripes
# Slots 208..223 (16 slots): Canton Background
# Slots 224..239 (16 slots): Stars
palette = displayio.Palette(256)

# Configurable Parameters
THEMES = ["classic", "thin_blue", "thin_red", "first_responders", "thin_green", "thin_gold"]
CYCLE_INTERVAL = 10.0      # Cycle to next flag every 10 seconds
TRANSITION_SPEED = 0.08    # Interpolation rate per frame (0.08 = ~1.2s crossfade)
star_layout = 0            # 0 = 50-star grid, 1 = 13-star circle (Betsy Ross)

def get_theme_colors(theme_name):
    """Returns 13 stripe colors (list of RGB tuples), canton color, and star color."""
    stripes = [(0, 0, 0)] * 13
    
    if theme_name == "classic":
        red = (178, 34, 52)
        white = (255, 255, 255)
        for i in range(13):
            stripes[i] = red if (i % 2 == 0) else white
        canton = (40, 39, 90)
        star = (255, 255, 255)
    else:
        # Thin Line themes share the same base (alternating Black / Silver-grey)
        black = (18, 18, 18)
        grey = (210, 210, 210)
        for i in range(13):
            stripes[i] = black if (i % 2 == 0) else grey
            
        canton = (12, 12, 12)
        star = (240, 240, 240)
        
        # Apply specific colored thin lines on the white stripe slots (Stripe 8 is index 7, Stripe 10 is index 9)
        if theme_name == "thin_blue":
            stripes[7] = (0, 45, 255)       # Thin Blue Line
        elif theme_name == "thin_red":
            stripes[7] = (229, 0, 0)        # Thin Red Line
        elif theme_name == "first_responders":
            stripes[7] = (0, 45, 255)       # Police Blue
            stripes[9] = (229, 0, 0)        # Firefighter Red
        elif theme_name == "thin_green":
            stripes[7] = (0, 163, 0)        # Military/Federal Green
        elif theme_name == "thin_gold":
            stripes[7] = (255, 215, 0)      # Dispatcher Gold
            
    return stripes, canton, star

# Initialize active color buffers (as float lists for smooth interpolation)
current_theme_idx = 0
active_theme = THEMES[current_theme_idx]
target_stripes, target_canton, target_star = get_theme_colors(active_theme)

current_stripes = [[float(c) for c in s] for s in target_stripes]
current_canton = [float(c) for c in target_canton]
current_star = [float(c) for c in target_star]

def update_hardware_palette():
    """Generates 16-step shading gradients for each region in the hardware palette."""
    # 1. Update 13 Stripes
    for i in range(13):
        color = current_stripes[i]
        for s in range(16):
            shading = 0.70 + 0.30 * (s / 15.0) # 16 levels of shading
            palette[i * 16 + s] = (
                int(color[0] * shading),
                int(color[1] * shading),
                int(color[2] * shading)
            )
            
    # 2. Update Canton (Slots 208..223)
    for s in range(16):
        shading = 0.70 + 0.30 * (s / 15.0)
        palette[208 + s] = (
            int(current_canton[0] * shading),
            int(current_canton[1] * shading),
            int(current_canton[2] * shading)
        )
        
    # 3. Update Stars (Slots 224..239)
    for s in range(16):
        shading = 0.70 + 0.30 * (s / 15.0)
        palette[224 + s] = (
            int(current_star[0] * shading),
            int(current_star[1] * shading),
            int(current_star[2] * shading)
        )

# Populate initial colors
update_hardware_palette()

# Create a TileGrid and Group to show it on screen
tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
group = displayio.Group()
group.append(tile_grid)
display.root_group = group

# Pre-calculate star centers for 50-star grid (to optimize frame rate in Python)
stars_50 = []
for r in range(1, 10):
    for c in range(1, 12):
        if (r % 2 == 1 and c % 2 == 1) or (r % 2 == 0 and c % 2 == 0):
            star_x = int((c / 12.0) * 26.0)
            star_y = int((r / 10.0) * 17.0)
            stars_50.append((star_x, star_y))

# Pre-calculate star centers for 13-star Betsy Ross circle
stars_13 = []
for i in range(13):
    angle = i * (2.0 * math.pi / 13.0) - math.pi / 2.0
    star_x = int((math.cos(angle) / 1.529) * 0.33 * 26.0 + 13.0)
    star_y = int(math.sin(angle) * 0.33 * 17.0 + 8.5)
    stars_13.append((star_x, star_y))

# Convert to sets for O(1) hash lookup
stars_50_set = set(stars_50)
stars_13_set = set(stars_13)

start_time = time.monotonic()
last_cycle_time = start_time

print("Animated Flag Matrix Running. Auto-cycling active!")

while True:
    now = time.monotonic()
    t = now - start_time
    
    # 1. Check if it's time to cycle to the next flag theme
    if now - last_cycle_time > CYCLE_INTERVAL:
        last_cycle_time = now
        current_theme_idx = (current_theme_idx + 1) % len(THEMES)
        active_theme = THEMES[current_theme_idx]
        target_stripes, target_canton, target_star = get_theme_colors(active_theme)
        print("Cycling to theme: " + active_theme)
        
    # 2. Smoothly interpolate current colors towards the target theme
    for i in range(13):
        for c in range(3):
            current_stripes[i][c] += (target_stripes[i][c] - current_stripes[i][c]) * TRANSITION_SPEED
    for c in range(3):
        current_canton[c] += (target_canton[c] - current_canton[c]) * TRANSITION_SPEED
        current_star[c] += (target_star[c] - current_star[c]) * TRANSITION_SPEED
        
    # 3. Update the hardware palette colors
    update_hardware_palette()
    
    # Select active star set
    active_stars = stars_13_set if star_layout == 1 else stars_50_set
    
    # 4. Render the pixels with moving diagonal wave shading
    for y in range(32):
        v = y / 31.0
        in_canton_y = (y < 17)
        stripe_idx = (y * 13) // 32
        
        # Base index for stripes: each stripe occupies 16 slots
        stripe_base_offset = stripe_idx * 16
        
        for x in range(64):
            u = x / 63.0
            
            # Shading phase math (rolling diagonal bands)
            phase = u * 4.5 + (1.0 - v) * 2.5 - t * 2.2
            shading_val = 0.76 + 0.24 * math.sin(phase)
            shading_idx = int(shading_val * 15) # Scale to 0-15 shading range
            shading_idx = max(0, min(15, shading_idx))
            
            # Draw Canton vs Stripes
            if x < 26 and in_canton_y:
                # O(1) lookup check for sharp 1-pixel stars
                if (x, y) in active_stars:
                    bitmap[x, y] = 224 + shading_idx # Stars (offset 224)
                else:
                    bitmap[x, y] = 208 + shading_idx # Canton (offset 208)
            else:
                bitmap[x, y] = stripe_base_offset + shading_idx

    # Draw to the screen
    display.refresh()
    time.sleep(0.01) # Small delay for frame spacing
