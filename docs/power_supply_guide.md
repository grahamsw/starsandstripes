# Power Supply Guide: Mean Well LRS Series & Safety

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

---

## 3. Crucial Safety: Eliminating Exposed AC Live Contacts

Wiring AC mains voltage (110V/220V) can be intimidating, and leaving the screw terminals exposed is highly dangerous. To ensure **zero exposed live power**, use one of the following methods:

### Method A: Use a 3D-Printed or Injection-Molded Terminal Cover (Highly Recommended)
The LRS power supply has screw holes near the terminals designed specifically to attach a protective housing.
1. **Print or Buy a Cover:** Search for `Mean Well LRS-50 terminal cover` (or `LRS-100` depending on your model) on Thingiverse, Printables, or Amazon. These are custom-designed plastic caps that snap or screw onto the end of the metal PSU.
2. **How it works:** The AC power cord enters through a tight rubber grommet (strain relief) into the plastic cap, connects to the screws inside, and the cap is screwed shut. The terminals are completely sealed, leaving no metal contacts exposed to human touch.

### Method B: Build a Fused AC Rocker Switch Inlet (Professional Setup)
Instead of wiring a power cord directly to the terminals:
1. Buy an **IEC320 C14 Fused Power Socket with Rocker Switch** (approx \$3 on Amazon). This is the standard 3-prong power plug socket found on the back of desktop computers.
2. Wire the terminals of the LRS supply to the back of this socket, and enclose the entire assembly inside a 3D-printed terminal box.
3. **How it works:** All raw AC wiring is sealed inside the box. On the outside, you simply flip a rocker switch and plug in a standard, safe computer power cable. If there is a short, the built-in fuse blows instantly, protecting your home.

---

## 4. The "Zero AC Wiring" Alternative: Closed Desktop Power Bricks

If you do not want to wire AC mains voltage under any circumstances, you can completely bypass it! 

You can buy a **sealed consumer desktop power adapter brick** (similar to a laptop power brick) that outputs 5V DC directly.

### What to Buy:
- **5V 10A Closed Power Brick:** Search for `5V 10A AC adapter brick` (brands like ALITOVE or BTF-LIGHTING).
- This block plugs directly into the wall, is completely sealed in plastic, and outputs safe 5V DC power via a standard **5.5mm x 2.1mm DC barrel jack**.

### How to Connect it to the Flag:
1. **If using a Driver Board/Shield (e.g., Adafruit Matrix Portal):** Many of these shields already have a DC barrel jack socket or a high-current USB-C port built-in. You simply plug the power brick directly into the shield.
2. **If wiring directly:** Buy a **DC Female Barrel Jack to Screw Terminal Adapter** (often comes free with the power brick). You plug the brick into the jack, and run your red/black panel cables straight out of the screw terminals.

---

## 5. Power Requirements: HUB75 Multiplexing vs. LED Strips

You might expect that an $128 \times 64$ LED flag (8,192 pixels) would require a massive, dangerous power supply. However, **HUB75 panels use scan-rate multiplexing**, which dramatically reduces power draw:

- **WS2812B LED Strips:** Every single LED is powered continuously. 2,000 LEDs at 100% white draw a constant $\approx 120\text{A}$!
- **HUB75 Panels:** The panel is divided into rows and scanned sequentially (e.g., $1/16$ or $1/32$ scan rate). At any microsecond, only 1 or 2 rows of LEDs are physically on. They flash so fast (thousands of times per second) that they appear solid to the human eye, but the physical power draw is divided by the scan rate.
  - A single $64 \times 32$ panel draws at most **$3.5\text{A} - 4.5\text{A}$** at 5V.
  - A $128 \times 64$ matrix (two $64 \times 64$ panels) draws at most **$8\text{A} - 10\text{A}$** at 5V.

### Model Recommendation:
- **For $64 \times 32$ Panel:** Buy the **Mean Well LRS-50-5** (5V 10A / 50W) or a **5V 6A / 10A closed power brick**.
- **For $128 \times 64$ Panel:** Buy the **Mean Well LRS-100-5** (5V 20A / 100W) or a **5V 10A / 12A closed power brick**.
