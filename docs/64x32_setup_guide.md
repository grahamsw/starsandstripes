# Building the 64x32 LED Matrix Flag (Wall Adapter Edition)

This is the perfect, safest, and most cost-effective way to get started. A single $64 \times 32$ matrix contains 2,048 RGB LEDs. Because of HUB75 scanning multiplexing, the maximum current draw is only about **4 Amps** at 5V, meaning you can power the entire display with a standard, sealed wall-wart style power supply.

---

## 1. Hardware Parts List

To build this setup, you need the following 4 core parts:

### Part 1: The LED Display Panel
- **What to buy:** One **$64 \times 32$ HUB75 RGB LED Panel**.
- **Pixel Pitch (Spacing):** 
  - **P3 (3mm pitch):** Size is $19.2\text{ cm} \times 9.6\text{ cm}$ (compact, sharp desktop size).
  - **P4 (4mm pitch):** Size is $25.6\text{ cm} \times 12.8\text{ cm}$ (slightly larger, good for a frame).
- **Search Keyword:** `HUB75 64x32 LED panel P3` or `HUB75 64x32 LED panel P4`

### Part 2: The Brains (Choose Option A or B)
- **Option A (Easiest - Adafruit Matrix Portal S3):** 
  - A specialized ESP32-S3 board that plugs directly into the back of the HUB75 panel. It has a built-in USB-C port, a DC screw terminal block, and handles both programming and power routing.
  - *Search Keyword:* `Adafruit Matrix Portal S3`
- **Option B (DIY - ESP32 + Shield):**
  - A standard **ESP32 NodeMCU** development board paired with a **HUB75 Driver Board/Shield** (e.g., Brian Lough's *ESP32 Trinity* or a generic *ESP32 HUB75 shield*).
  - *Search Keyword:* `ESP32 NodeMCU` + `ESP32 HUB75 driver board shield`

### Part 3: The Wall Power Supply
- **What to buy:** A sealed, plastic **5V 4A (or 5V 5A) AC-to-DC Wall Power Adapter**. It plugs directly into the wall and has a standard 5.5mm x 2.1mm DC barrel connector.
- **Search Keyword:** `5V 4A power adapter 5.5mm` or `5V 5A power supply brick`

### Part 4: DC Barrel Jack Screw Terminal Adapter
- **What to buy:** A female DC barrel jack adapter (usually comes free with the power supply).
- **Why you need it:** You plug the wall supply's barrel jack into this, and screw the red/black power wires of the LED panel and ESP32 straight into the screw terminals. (Note: If you use the *Adafruit Matrix Portal S3*, this is not needed, as the board already has screw terminals).
- **Search Keyword:** `5.5mm x 2.1mm female DC barrel jack adapter`

---

## 2. Wiring Schematic (Solderless)

```
                       ┌─────────────────────────┐
                       │    5V Wall Adapter      │
                       └────────────┬────────────┘
                                    │ (5.5mm Barrel Plug)
                                    ▼
                       ┌─────────────────────────┐
                       │ DC Barrel Jack Adapter  │
                       │    (Screw Terminals)    │
                       └──────┬────────────┬─────┘
                              │            │
                    +5V (Red) │            │ GND (Black)
                              ▼            ▼
                   ┌───────────────────────────┐
                   │    ESP32 Shield / Panel   │
                   └───────────────────────────┘
```

1. **Panel Ribbon Cable:** Plug the 16-pin ribbon cable between the ESP32 Driver Shield and the `DATA IN` port on the back of the panel.
2. **Panel Power Cable:** Plug the white VH4 power cable into the back of the LED panel.
3. **Connecting Power:** 
   - Connect the **Red wire** (+5V) of the panel power cable to the `+` screw terminal of the DC Barrel Jack Adapter.
   - Connect the **Black wire** (GND) of the panel power cable to the `-` screw terminal of the DC Barrel Jack Adapter.
   - Run a second set of thinner wires (included with your ESP32 board) from the same screw terminals to the `5V` and `GND` pins on your ESP32 board.
4. **Turn it On:** Plug the 5V wall adapter into the wall, and plug the DC barrel connector into your adapter. The ESP32 and panel will power up instantly!
