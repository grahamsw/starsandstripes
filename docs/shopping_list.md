# Physical LED Flag: Hardware Shopping List

This shopping list outlines the exact components, quantities, and tools needed to build the physical animated LED flag. Choose **Option A** for a professional, high-density panel or **Option B** for a custom, hand-soldered layout.

---

## 1. Core Controller (Same for Both Options)

You need a powerful 32-bit microcontroller to handle the fast floating-point trigonometric wave shading and color transitions.

| Component | Qty | Specifications / Notes | Search Keywords |
| :--- | :---: | :--- | :--- |
| **ESP32 NodeMCU Development Board** | 1 | Choose the standard 30-pin or 38-pin ESP-WROOM-32 board. Do **not** get a standard 8-bit Arduino. | `ESP32 Development Board WROOM` |
| **Micro-USB or USB-C Cable** | 1 | For uploading code from your computer to the ESP32. | `USB C data cable fast charging` |

---

## 2. Option A: HUB75 LED Panels (Highly Recommended)
*This is the cleanest, easiest, and highest-resolution route. The panels come pre-assembled with a dense grid of LEDs.*

```mermaid
graph LR
    PSU[Power Supply] -->|DC Input| Panel[HUB75 RGB LED Panels]
    PSU -->|DC Input| ESP32[ESP32 Controller]
    ESP32 -->|Matrix Shield / Ribbon Cable| Panel
```

### Display & Driver Components
| Component | Qty | Specifications / Notes | Search Keywords |
| :--- | :--- | :--- | :--- |
| **HUB75 RGB LED Matrix Panels** | 2 | **For $128 \times 64$ Resolution:** Buy two $64 \times 64$ panels (Pitch 2.5mm or 3mm).<br>**For $64 \times 32$ Resolution:** Buy one $64 \times 32$ panel. | `HUB75 RGB LED Matrix 64x64 P3` or `P2.5` |
| **ESP32 HUB75 Matrix Driver Shield** | 1 | A plug-and-play adapter board that slots onto the ESP32 and provides a ribbon cable header and screw terminals. (e.g. *ESP32 Trinity* by Brian Lough, or *Adafruit Matrix Portal ESP32*). | `ESP32 HUB75 driver board` or `Matrix Portal ESP32` |
| **16-pin HUB75 Ribbon Cable** | 1 | Usually comes free with the panels, but buy a spare if chaining panels. | `HUB75 ribbon cable 16pin` |

---

## 3. Safe Power Option (Zero AC Wiring - Recommended for Safety)
*This alternative completely replaces the Mean Well open-frame power supplies. It uses a sealed laptop-style AC power brick and a waterproof step-down converter, requiring zero exposed mains AC wiring.*

```
┌──────────────────┐  24V @ 5A  ┌─────────────────┐  5V @ 20A  ┌────────────────┐
│  24V Power Brick │───────────>│ 24V-to-5V Buck  │───────────>│  HUB75 Panel / │
│  (Wall Outlet)   │  (Safe DC) │ Converter       │  (Safe DC) │  ESP32 Shield  │
└──────────────────┘            └─────────────────┘            └────────────────┘
```

### Required Parts for Safe 5V 20A Power:
| Component | Qty | Specifications / Notes | Search Keywords |
| :--- | :--- | :--- | :--- |
| **24V 5A (120W) AC Power Adapter Brick** | 1 | A standard fully sealed plastic laptop-style power brick. Includes a safe AC wall plug and outputs 24V DC. Choose a UL-listed brand. | `24V 5A power adapter charger 120W` |
| **24V-to-5V 20A Buck Converter** | 1 | A sealed, waterproof aluminum step-down regulator. Takes 24V input and converts it to a stable 5V DC output at up to 20A. | `24V to 5V 20A buck converter regulator` |
| **Female DC Barrel Jack to Screw Terminal Adapter** | 1 | Plugs into the 24V brick's barrel jack, allowing you to screw the buck converter's input wires straight in with no wire cutting. | `5.5mm x 2.1mm female DC barrel jack adapter` |
| **Wago 221 Lever-Nut Connectors (3-port)** | 1 pack | Safe, solderless terminal blocks to connect the buck converter's output wires to the power cables of the HUB75 panels/shield. | `Wago 221 lever nuts 3 conductors` |

---

## 4. Option B: WS2812B Addressable LED Strips (DIY Route)
*This route allows you to build a custom-sized flag (e.g., the $74 \times 39$ layout with perfect integer stripes). Note: Requires a significant amount of cutting and soldering.*

### LED & Electronics Components
| Component | Qty | Specifications / Notes | Search Keywords |
| :--- | :--- | :--- | :--- |
| **WS2812B Addressable LED Strips** | ~3000 LEDs | **For $74 \times 39$ (2,886 LEDs):** Buy 5 meters of 60 LEDs/meter strips (approx. 10 rolls) or 144 LEDs/meter strips for a smaller, denser flag. | `WS2812B LED strip 60 leds/m 5m` |
| **74AHCT125 Level Shifter Chip** | 1 | Converts the ESP32's 3.3V data signal to the 5V logic signal required by the LED strips, preventing flickering. | `74AHCT125 level shifter DIP` |
| **1000µF 6.3V (or 10V) Capacitor** | 1 | Placed across the 5V and GND power terminals to prevent initial power surges from blowing the first LED. | `1000uF 10V electrolytic capacitor` |
| **330 Ohm Resistor** | 1 | Placed on the data line between the ESP32 pin and the first LED strip to protect the data pin. | `330 ohm resistor 1/4W` |

---

## 5. Where to Buy

1. **AliExpress:** (Cheapest option, 2-week shipping). Best for HUB75 panels, ESP32 boards, and LED strips.
2. **Amazon:** (Fastest option, 1-2 days). Best for power brick, buck converter, Wago connectors, level shifters, and wiring accessories.
3. **Adafruit / Pimoroni:** Great for premium, pre-built driver shields (like the *Adafruit Matrix Portal*) and high-quality mounting brackets.
