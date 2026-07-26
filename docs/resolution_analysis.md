# Physical LED Flag: Grid Resolution & Dimension Analysis

To render 13 stripes and a 50-star canton, the vertical resolution ($H$) and horizontal resolution ($W$) must be chosen carefully to maintain the flag's official $1.9:1.0$ aspect ratio and fit the star grid.

---

## 1. Resolution Comparison Table

Below is an analysis of the three most practical configurations for a physical LED build:

| Configuration | Matrix Size ($W \times H$) | Total LEDs | Stripe Height (pixels) | Canton Area ($W \times H$ pixels) | Star Spacing (Vert / Horiz) | Star Render Style |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Standard Retro** | $64 \times 32$ | 2,048 | ~2.46 | $26 \times 17$ | 1.72 px / 2.16 px | Single-pixel dots or 5-pixel cross |
| **2. High Detail** | $128 \times 64$ | 8,192 | ~4.92 | $51 \times 34$ | 3.45 px / 4.27 px | $3 \times 3$ custom 5-point star |
| **3. Custom Strip Grid**| $74 \times 39$ | 2,886 | **3.00 (Integer)** | $30 \times 21$ | 2.10 px / 2.50 px | Single-pixel or 5-pixel cross |

---

## 2. Detailed Configuration Breakdown

### Option 1: the $64 \times 32$ Grid (Most Common & Low-Cost)
Using a standard $64 \times 32$ HUB75 panel (typically $25.6\text{cm} \times 12.8\text{cm}$ in physical size):
- **Stripe Mapping:** Since $32 / 13 \approx 2.46$ pixels per stripe, stripes are drawn using a sub-pixel float check in shader code. The lines will look straight and clean, but some stripes will physically span 2 pixels and others 3.
- **Canton Mapping:** Canton is $26 \times 17$ pixels.
- **Star Spacing:** 9 rows of stars mapped to 17 vertical pixels means the center-to-center distance between rows is only **1.72 pixels**.
  - **Star Render Limits:** Since rows are spaced by 1.72 pixels, **stars must be single pixels** (or a 5-pixel cross shape). If a star is larger, the rows will bleed together.
  - **Visual Look:** Single-pixel stars on a dark background will look like sharp, twinkling stars in a night sky. This has a clean, high-contrast retro-cyberpunk aesthetic.
- **Power Draw:** ~5A to 8A at 5V (~25W - 40W).

---

### Option 2: the $128 \times 64$ Grid (High Detail - Recommended)
Built using two $64 \times 64$ HUB75 panels side-by-side (physical size: $51.2\text{cm} \times 25.6\text{cm}$):
- **Stripe Mapping:** ~4.92 pixels per stripe. With 5 pixels per stripe, lines are thick and extremely smooth.
- **Canton Mapping:** Canton is $51 \times 34$ pixels.
- **Star Spacing:** Vertical spacing of star rows is **3.45 pixels**; horizontal spacing is **4.27 pixels**.
  - **Star Render Limits:** Because we have 3.45 pixels of vertical space, we can render **$3 \times 3$ star shapes** (a center pixel, 4 adjacent pixels, and 4 corner pixels running at 50% brightness). Using our signed distance function (SDF) with anti-aliasing, these pixels will blend to look like actual 5-pointed stars.
  - **Visual Look:** Extremely smooth, high-fidelity reproduction. The wave movements will look fluid, and the fabric specularity will shine realistically.
- **Power Draw:** ~12A to 18A at 5V (~60W - 90W). Requires a robust 5V 20A power supply.

---

### Option 3: the $74 \times 39$ Custom Grid (Perfect Integer Geometry)
Created by hand-wiring WS2812B addressable strips (e.g. cutting 39 strips of 74 LEDs each and gluing them to a backing board):
- **Stripe Mapping:** **Exactly 3 pixels per stripe** ($13 \times 3 = 39$). Every stripe is perfectly uniform and aligns with the physical LED grid.
- **Canton Mapping:** **Exactly $30 \times 21$ pixels** ($40\%$ width, $7/13$ height).
- **Star Spacing:** Vertical row spacing is **2.1 pixels**; horizontal column spacing is **2.5 pixels**.
  - **Star Render Limits:** Stars must be single LEDs or 5-LED crosses.
  - **Visual Look:** Cleanest geometry because the stripes align perfectly with the physical rows.
- **Power Draw:** ~7A to 11A at 5V (~35W - 55W).

---

## 3. Emulation Recommendation

To help you choose the best resolution before buying components, I recommend we implement a **Pixelated LED Emulator** in our WebGL app first.

I will configure the emulator with a dropdown containing three options:
1. **$64 \times 32$ (Retro Grid)**
2. **$128 \times 64$ (High-Detail Grid)**
3. **$74 \times 39$ (Custom Integer Grid)**

The WebGL shader will draw black grids between circular glowing pixels to let you see exactly how the stripes and stars render at each size.
