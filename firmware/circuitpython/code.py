# Physical LED Matrix Flag - CircuitPython Edition
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
    bit_depth=3,  # Capped at 3 bits for high FPS in Python interpreter
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
bitmap = displayio.Bitmap(64, 32, 256) # 256 colors maximum index

# Build a palette of colors
# Indices: 
# 0..63: Red gradient (for waves)
# 64..127: White/Grey gradient
# 128..191: Blue/Canton gradient
# 192..255: Custom Accent / Star gradient
palette = displayio.Palette(256)

def update_palette(t, theme):
    # Base colors (R, G, B) for the theme
    if theme == "thin_blue":
        color_a = (15, 15, 15)      # Black
        color_b = (210, 210, 210)   # Silver
        color_canton = (15, 15, 15)
        color_star = (240, 240, 240)
    elif theme == "thin_red":
        color_a = (15, 15, 15)
        color_b = (210, 210, 210)
        color_canton = (15, 15, 15)
        color_star = (240, 240, 240)
    else:
        color_a = (180, 25, 45)      # Classic Red
        color_b = (255, 255, 255)    # Classic White
        color_canton = (50, 50, 110) # Classic Blue
        color_star = (255, 255, 255)
        
    # Generate 64-step brightness gradients for wave shading
    for i in range(64):
        shading = 0.70 + 0.30 * (i / 63.0)
        
        # Stripe A gradient (0-63)
        palette[i] = (
            int(color_a[0] * shading),
            int(color_a[1] * shading),
            int(color_a[2] * shading)
        )
        # Stripe B gradient (64-127)
        palette[64 + i] = (
            int(color_b[0] * shading),
            int(color_b[1] * shading),
            int(color_b[2] * shading)
        )
        # Canton background gradient (128-191)
        palette[128 + i] = (
            int(color_canton[0] * shading),
            int(color_canton[1] * shading),
            int(color_canton[2] * shading)
        )
        # Stars gradient (192-255)
        palette[192 + i] = (
            int(color_star[0] * shading),
            int(color_star[1] * shading),
            int(color_star[2] * shading)
        )

# Initialize palette
theme = "classic" # Options: "classic", "thin_blue", "thin_red"
star_layout = 0   # 0 = 50-star grid, 1 = 13-star circle (Betsy Ross)
update_palette(0.0, theme)

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

start_time = time.monotonic()

print("Flag Matrix Running. Edit theme or star_layout in code.py to customize!")

while True:
    t = time.monotonic() - start_time
    
    # Calculate wave shading indices for every cell (0 to 63)
    # We do a fast approximation of the diagonal sine wave shading
    for y in range(32):
        v = y / 31.0
        
        # Canton height boundary
        in_canton_y = (y < 17)
        stripe_idx = (y * 13) // 32
        
        # Decide base palette color offsets
        # Red/StripeA = 0, White/StripeB = 64, Canton = 128, Star = 192
        if theme == "thin_blue" and stripe_idx == 7:
            # Special Blue stripe
            stripe_color_offset = 128 # Map to canton blue slots
        elif theme == "thin_red" and stripe_idx == 7:
            stripe_color_offset = 0 # Map to red slots
        else:
            stripe_color_offset = 0 if (stripe_idx % 2 == 0) else 64
            
        for x in range(64):
            u = x / 63.0
            
            # Diagonal wave phase calculation
            phase = u * 4.5 + (1.0 - v) * 2.5 - t * 2.2
            shading_val = 0.76 + 0.24 * math.sin(phase)
            shading_idx = int(shading_val * 63) # Normalize to 0-63 range
            shading_idx = max(0, min(63, shading_idx))
            
            # 1. Determine base region (Canton vs Stripes)
            if x < 26 and in_canton_y:
                # Canton area
                # Check if pixel is part of a star
                is_star = False
                if star_layout == 0:
                    for s_x, s_y in stars_50:
                        dx = abs(x - s_x)
                        dy = abs(y - s_y)
                        if dx <= 1 and dy <= 1 and (dx + dy) <= 1:
                            is_star = True
                            break
                else:
                    for s_x, s_y in stars_13:
                        dx = abs(x - s_x)
                        dy = abs(y - s_y)
                        if dx <= 1 and dy <= 1 and (dx + dy) <= 1:
                            is_star = True
                            break
                            
                if is_star:
                    bitmap[x, y] = 192 + shading_idx # Stars
                else:
                    bitmap[x, y] = 128 + shading_idx # Canton background
            else:
                # Stripes area
                bitmap[x, y] = stripe_color_offset + shading_idx

    # Refresh the display matrix
    display.refresh()
    time.sleep(0.016) # Cap around 60 FPS
