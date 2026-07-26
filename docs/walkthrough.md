# Walkthrough - Animated Flag WebGL Studio & LED Emulator

I have successfully implemented, tested, committed, and deployed the new **LED Matrix Emulation Mode** to Firebase Hosting.

---

## Live Deployment Info

- **Live Website**: [https://stars-and-stripes-flag-2026.web.app](https://stars-and-stripes-flag-2026.web.app)
- **Firebase Console**: [Console Overview](https://console.firebase.google.com/project/stars-and-stripes-flag-2026/overview)
- **GitHub Repository**: [https://github.com/grahamsw/starsandstripes.git](https://github.com/grahamsw/starsandstripes.git) (Branch: `main`)

---

## File Changes & Architecture

The following key updates were implemented in the workspace:

### 1. Shader Customization (`src/shaders/flag.js`)
- **UV Quantization:** Added a coordinate snapping check at the top of the fragment shader. When `uLedEmulation` is active, continuous UVs are quantized into discrete matrix coordinates:
  $$\text{uvLed} = \frac{\lfloor \text{vUv} \times \text{uLedResolution} \rfloor + 0.5}{\text{uLedResolution}}$$
  This forces all flag stripes, canton boundaries, and stars to snap to the exact grid pixel boundaries.
- **Physical LED Masking:** Evaluates each high-resolution screen pixel relative to its grid cell center using `fract(vUv * uLedResolution)`.
  - Computes a circular mask (`smoothstep(0.43, 0.39, dist)`) to render round LED bulb shapes.
  - Adds a center light hotspot (`exp(-6.0 * dist) * 0.45`) to simulate LED light dispersion on plastic lenses.
  - Multiplies the flag background color by the mask and hotspot to create black grid lines between the glowing bulbs.

### 2. Parameter Control Integration (`src/components/FlagCanvas.vue`)
- Binds `ledEmulation`, `ledWidth`, and `ledHeight` as reactive props.
- Maps `uLedEmulation` and `uLedResolution` uniforms to the Shader Material.
- **Smooth Dissolve Transition:** Lerps `currentLedEmulation` in the `animate()` requestAnimationFrame loop using a framerate-independent decay formula, creating a smooth dissolve/pixelation effect when toggled on/off.

### 3. Emulation Panel Controls (`src/App.vue`)
- Adds checkbox state (`ledEmulation`) and segmented radio button selectors (`selectedResolution`) in the control dashboard.
- Displays an interactive details card explaining the physical constraints of the selected grid:
  - **$64 \times 32$ (Retro):** 2,048 total LEDs, ~2.46 pixels per stripe. Canton displays retro single-pixel stars.
  - **$74 \times 39$ (Custom Strip Grid):** 2,886 total LEDs, exactly 3.00 pixels per stripe (perfect integer alignment).
  - **$128 \times 64$ (High Detail):** 8,192 total LEDs, ~4.92 pixels per stripe. Canton displays detailed $3 \times 3$ anti-aliased stars.
- Appended styling rules for radio selectors, container fades, and details display panels.

---

## Verification & Testing

1. **Compilation**: Built locally with Vite (`npm run build`). Output is fully compressed and has zero warnings.
2. **Smooth Blending**: Toggling the LED mode in the web app shows a beautiful fade-in of the LED grid lines. The waves deform the virtual LED matrix perfectly, replicating a real flexible LED flag screen.
3. **Git Integration**: Successfully committed and pushed the changes to `origin/main` on GitHub:
   ```bash
   git add . && git commit -m "Add WebGL LED Matrix emulation mode with selectable resolutions" && git push origin main
   ```
