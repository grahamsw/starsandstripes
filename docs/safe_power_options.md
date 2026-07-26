# Consumer-Safe 5V 10A/20A Power Supplies (Zero AC Wiring)

If you do not want to wire AC mains voltage under any circumstances, you do not have to use a Mean Well LRS series supply. There are two highly certified, consumer-safe, fully enclosed options that plug directly into the wall, have **physical power switches**, and easily supply 10A to 20A at 5V.

---

## Option A: ATX Computer Power Supply + Breakout Board (Best for 20A+)
A standard desktop computer power supply (ATX PSU) is fully enclosed, UL-certified, plugs directly into the wall with a standard PC power cable, and has a physical heavy-duty on/off switch on the back.

Even a budget 450W computer power supply has a dedicated **5V rail** that can deliver **15A to 25A of current** safely and silently.

### What to Buy:
1. **Standard ATX PC Power Supply:** Any budget brand-name unit (e.g., Corsair, EVGA, or Thermaltake 450W/500W).
2. **ATX Power Supply Breakout Board:** (Approx. \$5 - \$8 on Amazon). This is a small board that plugs directly into the 24-pin motherboard connector of the power supply.

### How it works:
- You plug the 24-pin cable from the PC power supply into the breakout board.
- The breakout board has a **physical on/off rocker switch** and screw terminals labeled `5V`, `12V`, `3.3V`, and `GND`.
- You screw your LED panel power lines into the `5V` and `GND` terminals.
- **Why it is safe:** The high-voltage AC mains are fully sealed inside the computer power supply. The breakout board only exposes low-voltage, touch-safe 5V DC power. The power supply also has built-in short-circuit protection and will shut down instantly if any wires touch.

*Search keywords:* `ATX power supply breakout board` + `EVGA 500 W1` (or any budget ATX PSU).

---

## Option B: Variable Lab Bench Power Supply (Best for Testing & Safety)
A laboratory bench power supply is a fully enclosed device used by electronics hobbyists and engineers. It plugs into the wall with a standard power cord, has a physical power switch on the front, and lets you dial in the exact voltage and current limits.

### What to Buy:
- **30V 10A Variable DC Bench Power Supply:** (Approx. \$40 - \$60 on Amazon). Brands like Wanptek, KORAD, or Kungber.

### How it works:
- You plug it into the wall and turn it on with the front power button.
- You turn the voltage dial to exactly `5.0V`.
- You connect standard **Banana Plug to Spade/Alligator Clip cables** into the Red (+) and Black (-) jacks on the front, and connect them to your LED panels.
- **Why it is safe:** It is fully enclosed, UL-certified, and has a physical power switch.
- **Bonus Features:**
  - **Real-Time Display:** It shows exactly how many Amps and Watts your flag is drawing in real time.
  - **Over-Current Protection (OCP):** You can set a current limit (e.g. 8A). If there is a short circuit, the power supply will shut down in milliseconds, sounding an alarm and preventing any damage.

*Search keywords:* `Variable DC Bench Power Supply 30V 10A`

---

## Option C: 5V 10A Closed Power Brick + Inline Switch
If you only need 10A (perfect for a $64 \times 32$ or medium-sized flag) and want a simple block like a laptop charger:

### What to Buy:
1. **5V 10A AC-to-DC Desktop Power Adapter:** A sealed plastic brick with a standard AC wall plug on one end and a 5.5mm x 2.1mm DC barrel connector on the other.
2. **Heavy-Duty Inline DC Rocker Switch Cable:** A cable with a male DC barrel jack on one end, a physical rocker switch in the middle, and a female DC barrel jack on the other.

### How it works:
- You plug the brick into the wall.
- You plug the inline switch cable into the brick's DC output cord.
- You plug the other end of the switch cable into your LED driver shield or screw terminal adapter.
- You can turn the DC power on and off using the inline rocker switch.

*Search keywords:* `5V 10A power supply adapter` + `5.5mm x 2.1mm inline rocker switch cable`
