# Implementation Plan: Physical LED Flag WebGL Emulator

This plan outlines the changes to add an **LED Matrix Emulation Mode** into the existing WebGL waving flag application. This will allow the user to preview how different physical resolutions (standard $64 \times 32$, high-detail $128 \times 64$, or custom $74 \times 39$) look in real-time, helping design the physical LED layout.

---

## User Review Required

> [!NOTE]
> **Analog Emulation Transition:** The transition into and out of LED mode will be animated dynamically. `uLedEmulation` will lerp between `0.0` (smooth flag) and `1.0` (discrete LED matrix), allowing the physical pixel grid to "dissolve" into view smoothly.

---

## Proposed Changes

### 1. Shader Layer

#### [MODIFY] [flag.js](file:///Users/graha/Documents/dev/starsandstripes/src/shaders/flag.js)
- Add uniforms:
  - `uniform float uLedEmulation;` (blend factor: `0.0` = smooth fabric, `1.0` = LED matrix)
  - `uniform vec2 uLedResolution;` (width and height grid boundaries, e.g. `vec2(64.0, 32.0)`)
- **UV Quantization:**
  - Before sampling the stripes, canton, and stars, calculate a pixelated UV coordinate `uvLed`:
    ```glsl
    vec2 uvLed = (floor(vUv * uLedResolution) + vec2(0.5)) / uLedResolution;
    ```
  - Mix between smooth coordinates and pixelated coordinates:
    ```glsl
    vec2 sampleUv = mix(vUv, uvLed, uLedEmulation);
    ```
  - Use `sampleUv` for all downstream flag drawings (stripe index calculation, canton border check, and star coordinate lookups).
- **Physical LED Bulb Rendering:**
  - After calculating the flag base color, apply the LED grid mask if `uLedEmulation > 0.0`:
    ```glsl
    if (uLedEmulation > 0.0) {
      vec2 localCellUv = fract(vUv * uLedResolution);
      float distFromCenter = length(localCellUv - vec2(0.5));
      
      // Anti-aliased circular LED bulb boundary (radius = 0.43)
      float ledMask = smoothstep(0.43, 0.39, distFromCenter);
      
      // Center hotspot mimicking physical LED dome light dispersion
      float hotSpot = exp(-6.0 * distFromCenter) * 0.45;
      
      // Blend normal flat color into the LED grid based on emulation uniform
      vec3 ledColor = flagColor * (ledMask + hotSpot);
      flagColor = mix(flagColor, ledColor, uLedEmulation);
    }
    ```

---

### 2. Canvas Component

#### [MODIFY] [FlagCanvas.vue](file:///Users/graha/Documents/dev/starsandstripes/src/components/FlagCanvas.vue)
- Add props:
  - `ledEmulation`: `Boolean`
  - `ledWidth`: `Number`
  - `ledHeight`: `Number`
- Add uniforms:
  - `uLedEmulation: { value: 0.0 }`
  - `uLedResolution: { value: new THREE.Vector2(64.0, 32.0) }`
- **Render Loop Interpolation:**
  - In `animate()`, lerp the `currentLedEmulation` value towards the target prop value:
    ```javascript
    const targetLedEmulation = props.ledEmulation ? 1.0 : 0.0;
    currentLedEmulation += (targetLedEmulation - currentLedEmulation) * lerpFactor;
    flagMaterial.uniforms.uLedEmulation.value = currentLedEmulation;
    ```
  - Watch for changes in `props.ledWidth` and `props.ledHeight` and update `uLedResolution` uniform:
    ```javascript
    watch(() => [props.ledWidth, props.ledHeight], ([w, h]) => {
      flagMaterial.uniforms.uLedResolution.value.set(w, h);
    });
    ```

---

### 3. User Interface Dashboard

#### [MODIFY] [App.vue](file:///Users/graha/Documents/dev/starsandstripes/src/App.vue)
- Add state variables:
  - `ledEmulation`: `ref(false)`
  - `selectedResolution`: `ref('64x32')` (options: `'64x32'`, `'128x64'`, `'74x39'`)
- Add computed values for resolution dimensions:
  - `ledWidth = computed(() => parseResolution(selectedResolution.value).w)`
  - `ledHeight = computed(() => parseResolution(selectedResolution.value).h)`
- **HTML Control Section:**
  - Render an "LED Matrix Emulator" sidebar panel section.
  - A checkbox to toggle `ledEmulation`.
  - A stylized segmented control or radio button group to switch between the 3 physical resolutions.
  - Display helpful hardware info dynamically below the controls (e.g. total LED count, expected stripe pixels, star spacing style).

---

## Verification Plan

### Automated / Performance Tests
- Verify compilation of shader uniforms and hot module reloading.
- Run `npm run build` to confirm output has no errors.
- Confirm frame rates remain above 60fps even when rendering high-density $128 \times 64$ grid calculations.

### Manual Verification
1. Toggle the LED Emulator mode in the sidebar and verify that the flag transitions from solid cloth to a grid of glowing circular LED bulbs.
2. Switch between resolutions ($64 \times 32$, $74 \times 39$, $128 \times 64$) and verify that the size of the bulbs adjusts, showing:
   - Retro single-pixel stars on $64 \times 32$.
   - Perfect integer-sized 3-pixel stripes on $74 \times 39$.
   - Beautiful $3 \times 3$ anti-aliased stars on $128 \times 64$.
