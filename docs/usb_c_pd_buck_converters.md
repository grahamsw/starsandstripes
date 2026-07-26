# High-Power USB-C PD & Step-Down Buck Converters (5V @ 20A)

It is highly intuitive to look at a modern 200W or 300W USB-C desktop charger and assume it should be able to output 5V at 20A (100W). However, there is a fundamental physical and electrical limitation that prevents this, and a clever way to work around it using **Step-Down Buck Converters**.

---

## 1. The USB-C Physical Limitation: Why 5V @ 20A Doesn't Exist Directly
The USB-C connector pins and standard copper cables are physically very small.
- **The 5-Amp Cap:** Under the official USB-C Power Delivery (PD) specification, the maximum physical current (amperage) that can flow through a USB-C cable is strictly capped at **5 Amps** (and that requires a special "e-marked" cable; standard cables are capped at **3 Amps**).
- **The Melting Point:** If you tried to push 20 Amps of current through the tiny contacts of a USB-C plug, the electrical resistance would generate intense heat ($P = I^2 R$), melting the connector and cable instantly.
- **How USB-C Achieves 240W:** To deliver high wattage without melting cables, USB-C PD **increases the voltage, not the current**.
  - 100W is delivered as **20V @ 5A**
  - 140W is delivered as **28V @ 5A**
  - 240W is delivered as **48V @ 5A**
- **The 5V Default:** Because of this, when a device requests the standard 5V rail, all USB-C chargers limit the current to **3 Amps** (15W). Even a 300W charger will only supply 3A max at 5V.

---

## 2. The Solution: USB-C PD Decoy + Buck Converter
To safely extract 5V at 20A from a standard 100W+ USB-C charger, you can use a two-step process: **negotiate high voltage, then step it down**.

```
┌──────────────────┐  20V @ 5A  ┌───────────────┐  20V @ 5A  ┌─────────────────┐  5V @ 20A  ┌───────────┐
│ 100W USB-C Charger│──────────>│ USB-C Decoy   │───────────>│ DC-to-DC Buck   │───────────>│ LED Flag  │
│ (Wall Outlet)    │ (USB-C)    │ Trigger Board │ (Low Amp)  │ Converter       │ (High Amp) │ (5V Grid) │
└──────────────────┘            └───────────────┘            └─────────────────┘            └───────────┘
```

### How it works:
1. **USB-C PD Decoy Trigger Board:** You plug a tiny chip called a USB-C decoy trigger (approx. \$4) into your 100W USB-C charger. This chip communicates with the charger and tricks it into outputting **20V @ 5A** (100W) instead of 5V.
2. **DC-to-DC Buck Converter (Step-Down):** You wire the 20V output from the decoy board into a high-efficiency **5V Buck Converter** (approx. \$10).
   - A buck converter steps down voltage while **increasing current** (because Power = Voltage × Current is conserved).
   - Stepping down **20V @ 5A** (100W input) yields **5V @ 20A** (100W output, minus 5-7% heat loss).
3. **Safety Benefit:** The USB-C cable only carries a safe 5A at 20V. The high-current 20A loop is kept entirely local, flowing over short, thick wires directly between the buck converter and the LED panel.

*Search keywords:* `USB-C PD decoy trigger 20V` + `24V to 5V 20A buck converter`

---

## 3. The Easiest Alternative: Sealed 24V Brick + 5V Buck Converter
If you want to avoid dealing with USB-C negotiation chips and protocol handshakes, you can achieve the exact same result using a standard, sealed consumer power brick:

1. **24V 4A (96W) Power Adapter Brick:** Buy a fully sealed, UL-listed power brick (looks like a laptop charger) that outputs 24V DC. It plugs directly into the wall and has a standard inline switch.
2. **Waterproof 24V to 5V 20A Buck Converter:** (Approx. \$12 on Amazon). These are sealed aluminum blocks with built-in mounting brackets, commonly used in automotive and golf cart electronics.
3. **Wiring:**
   - Plug the 24V brick into the buck converter's input wires.
   - Run the buck converter's output wires (which now output exactly 5V at up to 20A) directly to your LED flag.
   - **Why it is safe:** The high-voltage AC mains are fully sealed inside the 24V brick. The buck converter is completely waterproof, shockproof, and handles the step-down conversion without exposing any high-voltage contacts.

*Search keywords:* `24V 4A power supply adapter` + `24V to 5V 20A buck converter regulator`
