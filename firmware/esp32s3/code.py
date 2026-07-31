# Test script for ESP32-S3 DevKitC-1 N16R8 with SeenGreat RGB Matrix Adapter Board (E) Rev 2.2
# Display: Single 64x64 RGB HUB75 LED Panel (1/32 Scan)
# 
# Save this file as 'code.py' on your CIRCUITPY drive.

import board
import rgbmatrix
import framebufferio
import displayio
import time

# Release any active displays to free up pins
displayio.release_displays()

# SeenGreat Adapter Board (E) Rev 2.2 Pin Mapping for ESP32-S3 DevKitC-1
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

print("Initializing RGBMatrix (64x64, 1/32 scan)...")
matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=64,
    bit_depth=4,
    rgb_pins=[R1, G1, B1, R2, G2, B2],
    addr_pins=[A, B, C, D, E],
    clock_pin=CLK,
    latch_pin=LAT,
    output_enable_pin=OE
)

# Associate matrix with displayio framebuffer
display = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)

# Create a display group
group = displayio.Group()
display.root_group = group

# Create a 64x64 bitmap with a palette
bitmap = displayio.Bitmap(64, 64, 4)
palette = displayio.Palette(4)
palette[0] = 0x000000 # Black
palette[1] = 0xFF0000 # Red
palette[2] = 0x00FF00 # Green
palette[3] = 0x0000FF # Blue

# Draw a test pattern:
# 1. Red border around the screen
for x in range(64):
    bitmap[x, 0] = 1
    bitmap[x, 63] = 1
for y in range(64):
    bitmap[0, y] = 1
    bitmap[63, y] = 1

# 2. Green square in the center (size 16x16)
for x in range(24, 40):
    for y in range(24, 40):
        bitmap[x, y] = 2

# 3. Blue diagonal lines in the canton area
for i in range(1, 20):
    bitmap[i, i] = 3

tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
group.append(tile_grid)

print("Test pattern displayed successfully!")

while True:
    # Loop and pulse the green square to show active running code
    for i in range(5):
        palette[2] = 0x00FF00 # Bright Green
        time.sleep(0.5)
        palette[2] = 0x005500 # Dim Green
        time.sleep(0.5)
