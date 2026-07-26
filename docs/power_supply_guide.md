# Power Supply Guide: Mean Well LRS Series

If you look up industrial-grade power supplies for LED projects, you will find the **Mean Well LRS Series** (e.g. `LRS-50-5` or `LRS-100-5`). 

Unlike consumer power "bricks" (like a laptop charger), these are **enclosed switching power supplies**. They feature open screw terminal blocks, which require you to wire both the AC mains (wall outlet) and the DC output yourself.

---

## 1. Why use LRS instead of a brick?
- **High Output Current:** Delivering 10A or 20A at 5V requires thick copper wires and efficient cooling. Bricks tend to overheat under constant high loads, whereas LRS units are metal-enclosed and ventilated.
- **Voltage Calibration (+V ADJ):** Long power wires have electrical resistance, causing a voltage drop. If your panel only receives 4.7V, it might flicker. LRS units have a small dial that lets you adjust the output voltage slightly (e.g. from 4.5V to 5.5V) to ensure exactly 5.0V reaches the panel.

---

## 2. Terminal Layout & Wiring

```
  AC INPUT (Mains)                  DC OUTPUT (5V)
┌─────────────────────────┐        ┌──────────────┐
│  L   │  N   │   FG (⏚)  │        │  -V  │  +V   │   [ +V ADJ ]
└─────────────────────────┘        └──────────────┘
  Line   Neut   Ground              GND    +5V       Voltage Dial
 (Hot)
```

### Step 1: AC Input (Wall Connection)
You will need a standard **3-prong AC power cord** (often sold as a "pigtail cord" with bare wire ends, or you can cut the female end off a spare computer power cable).
1. Strip the outer jacket to expose the three wires:
   - **Black (or Brown):** Line/Hot (L)
   - **White (or Blue):** Neutral (N)
   - **Green (or Green/Yellow):** Earth Ground (⏚)
2. Slide the bare wires under the screws of the **L**, **N**, and **⏚** terminals on the power supply, and tighten the screws firmly.

> [!CAUTION]
> **AC Mains Safety:** Double-check that your AC power cord is **unplugged** from the wall while wiring. Make sure no stray wire strands touch adjacent terminals. Once wired, snap the clear plastic protective cover shut over the terminals.

### Step 2: DC Output (LED & ESP32 Connection)
HUB75 LED panels ship with a red/black power cable that has a white **VH4 plug** on one end (plugs into the panel) and **fork spade terminals** on the other end.
1. Connect the **Red Spade Terminal** to the **`+V`** terminal screw.
2. Connect the **Black Spade Terminal** to the **`-V`** (sometimes labeled `COM` or `GND`) terminal screw.
3. Plug the VH4 connector into the power header on the back of the LED panel.

---

## 3. Power Requirements: HUB75 Multiplexing vs. LED Strips

You might expect that an $128 \times 64$ LED flag (8,192 pixels) would require a massive, dangerous power supply. However, **HUB75 panels use scan-rate multiplexing**, which dramatically reduces power draw:

- **WS2812B LED Strips:** Every single LED is powered continuously. 2,000 LEDs at 100% white draw a constant $\approx 120\text{A}$!
- **HUB75 Panels:** The panel is divided into rows and scanned sequentially (e.g., $1/16$ or $1/32$ scan rate). At any microsecond, only 1 or 2 rows of LEDs are physically on. They flash so fast (thousands of times per second) that they appear solid to the human eye, but the physical power draw is divided by the scan rate.
  - A single $64 \times 32$ panel draws at most **$3.5\text{A} - 4.5\text{A}$** at 5V.
  - A $128 \times 64$ matrix (two $64 \times 64$ panels) draws at most **$8\text{A} - 10\text{A}$** at 5V.

### Model Recommendation:
- **For $64 \times 32$ Panel:** Buy the **Mean Well LRS-50-5** (5V 10A / 50W). It is small, fanless, and has plenty of headroom.
- **For $128 \times 64$ Panel:** Buy the **Mean Well LRS-100-5** (5V 20A / 100W). It is also fanless and provides abundant power for both panels and the ESP32.
