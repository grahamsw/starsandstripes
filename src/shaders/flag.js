export const vertexShader = `
uniform float uTime;
uniform float uSpeed;
uniform float uAmplitude;
uniform vec2 uFrequency;

varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vPosition;

// Wave generator function
float getWaveHeight(vec2 pos) {
  // Pin the hoist (left edge at uv.x = 0)
  // Let the wave amplitude scale smoothly from 0.0 at the left to 1.0 at x = 0.15
  float pinFactor = smoothstep(0.0, 0.15, pos.x);
  
  // Wave 1: primary wind waves moving diagonally
  float w1 = sin(pos.x * uFrequency.x - uTime * uSpeed) * cos(pos.y * uFrequency.y - uTime * uSpeed);
  
  // Wave 2: higher-frequency secondary wave for organic cloth jitter
  float w2 = sin(pos.x * uFrequency.x * 2.2 + pos.y * uFrequency.y * 1.3 - uTime * uSpeed * 1.6) * 0.35;
  
  return (w1 + w2) * uAmplitude * pinFactor;
}

void main() {
  vUv = uv;
  vec3 pos = position;
  
  // Apply deformation in Z direction
  float height = getWaveHeight(uv);
  pos.z += height;
  
  // Recalculate normal using central differences in UV space
  float eps = 0.005;
  float heightX = getWaveHeight(uv + vec2(eps, 0.0));
  float heightY = getWaveHeight(uv + vec2(0.0, eps));
  
  // Convert UV offsets to local space tangent vectors
  // Flag dimensions in 3D scene are 1.9 wide by 1.0 high
  vec3 tangentX = vec3(eps * 1.9, 0.0, heightX - height);
  vec3 tangentY = vec3(0.0, eps * 1.0, heightY - height);
  
  vec3 localNormal = normalize(cross(tangentX, tangentY));
  vNormal = normalize(normalMatrix * localNormal);
  
  vec4 modelViewPosition = modelViewMatrix * vec4(pos, 1.0);
  vPosition = modelViewPosition.xyz;
  
  gl_Position = projectionMatrix * modelViewPosition;
}
`;

export const fragmentShader = `
uniform vec3 uStripeColors[13];
uniform vec3 uCantonColor;
uniform vec3 uStarColor;
uniform float uRainbowMode;
uniform float uTime;
uniform float uShininess;
uniform float uLedEmulation;
uniform vec2 uLedResolution;

varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vPosition;

// HSV to RGB converter for rainbow shifting
vec3 hsv2rgb(vec3 c) {
  vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
  vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
  return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

// Signed distance function for a 5-pointed star
float sdStar5(in vec2 p, in float r, in float rf) {
  const vec2 k1 = vec2(0.809016994375, -0.587785252292);
  const vec2 k2 = vec2(-k1.x, k1.y);
  p.x = abs(p.x);
  p -= 2.0 * max(dot(k1, p), 0.0) * k1;
  p -= 2.0 * max(dot(k2, p), 0.0) * k2;
  p.x = abs(p.x);
  p.y -= r;
  vec2 ba = rf * vec2(-k1.y, k1.x) - vec2(0.0, 1.0);
  float h = clamp(dot(p, ba) / dot(ba, ba), 0.0, r);
  return length(p - ba * h) * sign(p.y * ba.x - p.x * ba.y);
}

void main() {
  // Quantize coordinates if LED emulation is active
  vec2 uvLed = (floor(vUv * uLedResolution) + vec2(0.5)) / uLedResolution;
  vec2 sampleUv = mix(vUv, uvLed, uLedEmulation);

  // 1. Draw Stripes (13 horizontal bands)
  // Blend continuously between the static theme stripes and the scrolling rainbow
  // so switching themes crossfades instead of popping at the uRainbowMode midpoint.
  float stripeIndex = clamp(floor(sampleUv.y * 13.0), 0.0, 12.0);
  vec3 staticStripeColor = uStripeColors[int(stripeIndex)];
  vec3 rainbowStripeColor = hsv2rgb(vec3(fract(sampleUv.y * 1.3 - uTime * 0.45), 1.0, 1.0));
  vec3 stripeColor = mix(staticStripeColor, rainbowStripeColor, uRainbowMode);
  
  // 2. Draw Canton (Union - top left)
  bool inCanton = (sampleUv.x < 0.4 && sampleUv.y > 6.0 / 13.0);
  
  vec3 cantonColor = uCantonColor;
  
  if (inCanton) {
    // Normalize coordinates inside the canton to [0.0, 1.0]
    vec2 cUv = vec2(sampleUv.x / 0.4, (sampleUv.y - 6.0 / 13.0) / (7.0 / 13.0));
    
    // Grid coordinate calculations for the 50 stars
    float rowF = cUv.y * 10.0;
    float colF = cUv.x * 12.0;
    
    float r = floor(rowF + 0.5);
    float c = floor(colF + 0.5);
    
    float starMask = 0.0;
    float glow = 0.0;
    float starIntensity = 1.0;
    vec3 activeStarColor = uStarColor;
    // Blend continuously between the static canton color and the shifting rainbow background
    vec3 rainbowCantonBg = hsv2rgb(vec3(fract(uTime * 0.08), 0.9, 0.22));
    vec3 activeCantonBg = mix(uCantonColor, rainbowCantonBg, uRainbowMode);

    // Check if the nearest grid node is a valid star center
    if (r >= 1.0 && r <= 9.0 && c >= 1.0 && c <= 11.0) {
      bool isValidStar = false;
      if (mod(r, 2.0) == 1.0 && mod(c, 2.0) == 1.0) {
        isValidStar = true;
      } else if (mod(r, 2.0) == 0.0 && mod(c, 2.0) == 0.0) {
        isValidStar = true;
      }
      
      if (isValidStar) {
        vec2 starCenter = vec2(c / 12.0, r / 10.0);
        
        // Snapping the star center to the nearest LED grid coordinate to prevent spatial grid aliasing
        vec2 starCenterPixels = (floor(starCenter * uLedResolution) + vec2(0.5)) / uLedResolution;
        vec2 snappedStarCenter = mix(starCenter, starCenterPixels, uLedEmulation);
        
        vec2 localUv = cUv - snappedStarCenter;
        
        // Compute boundary fade using unscaled localUv to prevent square grid seams in the glow
        // Spacing is 0.0416 (half-width) and 0.05 (half-height) in canton coordinates
        float borderFadeX = smoothstep(0.0416, 0.033, abs(localUv.x));
        float borderFadeY = smoothstep(0.0500, 0.040, abs(localUv.y));
        float borderFade = borderFadeX * borderFadeY;
        
        // Correct aspect ratio
        localUv.x *= 1.4111;
        
        // Compute signed distance
        float d = sdStar5(localUv, 0.042, 0.381966);
        starMask = smoothstep(0.0025, -0.0025, d);
        
        // Star color & intensity calculation, blended continuously between the static
        // theme's gentle sparkle and rainbow mode's pulsating per-star color cycle
        float starPhase = r * 0.6 + c * 0.4;

        float staticIntensity = 0.8 + 0.2 * sin(uTime * 2.0 + starPhase);
        float rainbowIntensity = 0.35 + 0.65 * sin(uTime * 4.0 + starPhase);
        starIntensity = mix(staticIntensity, rainbowIntensity, uRainbowMode);

        vec3 rainbowStarColor = hsv2rgb(vec3(fract(uTime * 0.25 + starPhase * 0.15), 0.85, 1.0));
        activeStarColor = mix(uStarColor, rainbowStarColor, uRainbowMode);

        // Star glow halo effect outside the boundary (multiplied by borderFade)
        glow = exp(-40.0 * max(d, 0.0)) * 0.32 * borderFade;
        
        // Drop shadow outline to create a "sewn-on" 3D fabric look
        float shadow = smoothstep(0.008, 0.0, d) * 0.32;
        activeCantonBg = activeCantonBg * (1.0 - shadow * (1.0 - starMask));
      }
    }
    
    // Blend star mask with canton background and add outer glow halo
    cantonColor = mix(activeCantonBg, activeStarColor * starIntensity, starMask) + 
                  (activeStarColor * glow * (1.0 - starMask) * starIntensity);
  }
  
  // Base flag color
  vec3 flagColor = inCanton ? cantonColor : stripeColor;
  
  // Apply LED grid mask and dome hotspot glow if emulation is active
  if (uLedEmulation > 0.0) {
    vec2 localCellUv = fract(vUv * uLedResolution);
    float distFromCenter = length(localCellUv - vec2(0.5));
    
    // Circular LED bulb boundary with smooth anti-aliased edge (radius = 0.43)
    float ledMask = smoothstep(0.43, 0.39, distFromCenter);
    
    // Center hotspot mimicking physical LED dome light dispersion
    float hotSpot = exp(-6.0 * distFromCenter) * 0.45;
    
    vec3 ledColor = flagColor * (ledMask + hotSpot);
    flagColor = mix(flagColor, ledColor, uLedEmulation);
  }
  
  // 3. Shading & Lighting (Double-sided Blinn-Phong)
  vec3 V = normalize(-vPosition);
  vec3 N = normalize(vNormal);
  
  // Invert normal for back face lighting
  if (dot(N, V) < 0.0) {
    N = -N;
  }
  
  // View-space light directions (soft spotlight lighting)
  vec3 L = normalize(vec3(0.5, 0.6, 0.8));
  vec3 H = normalize(L + V);
  
  // Ambient, diffuse, and specular terms
  float ambient = 0.32;
  float diffuse = max(dot(N, L), 0.0) * 0.68;
  float specular = pow(max(dot(N, H), 0.0), uShininess) * 0.25;
  
  vec3 finalColor = flagColor * (ambient + diffuse) + vec3(specular);
  
  gl_FragColor = vec4(finalColor, 1.0);
}
`;
