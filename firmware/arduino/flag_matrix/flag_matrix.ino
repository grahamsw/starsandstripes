/*
 * Physical LED Matrix Flag - Adafruit Matrix Portal M4 Firmware
 * 
 * Target Board: Adafruit Matrix Portal M4 (SAMD51)
 * Display: 64x32 RGB HUB75 LED Panel (1/16 Scan)
 * 
 * Required Libraries (install via Arduino Library Manager):
 * - Adafruit Protomatter (High-speed HUB75 DMA engine)
 * - Adafruit GFX Library (Core graphics functions)
 * - Adafruit LIS3DH (Accelerometer support)
 * - Adafruit Unified Sensor (Core sensor interface)
 */

#include <Adafruit_Protomatter.h>
#include <Adafruit_LIS3DH.h>
#include <Adafruit_Sensor.h>
#include <math.h>

// Matrix Portal M4 Pin Configuration for HUB75 Panels
uint8_t rgbPins[]  = {2, 3, 4, 5, 6, 7}; // R1, G1, B1, R2, G2, B2
uint8_t addrPins[] = {A0, A1, A2, A3};   // Row address lines (4 lines = 1/16 scan)
uint8_t clockPin   = 8;                  // CLK
uint8_t latchPin   = 9;                  // LAT
uint8_t oePin      = 10;                 // OE

// Display dimensions
const uint16_t WIDTH = 64;
const uint16_t HEIGHT = 32;

// Initialize the Protomatter double-buffered matrix driver
Adafruit_Protomatter matrix(
  WIDTH,          // Width in pixels
  4,              // Color bit depth (4 bits = 4096 colors, very smooth)
  1, rgbPins,     // 1 matrix chain, RGB output pins
  sizeof(addrPins), addrPins, // Address pins
  clockPin, latchPin, oePin,
  true            // Double-buffering enabled for tear-free animation
);

// Initialize LIS3DH accelerometer on I2C
Adafruit_LIS3DH lis = Adafruit_LIS3DH();
bool accelEnabled = false;
bool verticalMode = false; // Toggled dynamically by accelerometer orientation

// Theme Selection
enum Theme {
  THEME_CLASSIC,
  THEME_THIN_BLUE_LINE,
  THEME_THIN_RED_LINE,
  THEME_FIRST_RESPONDERS,
  THEME_THIN_GREEN_LINE,
  THEME_THIN_GOLD_LINE,
  THEME_ALL_RESPONDERS,
  THEME_RAINBOW,
  THEME_VAPORWAVE,
  THEME_MONOCHROME
};

// Global active configuration
Theme currentTheme = THEME_CLASSIC;
int starLayout = 0; // 0 = 50-star grid, 1 = 13-star circle (Betsy Ross)

// Wave motion variables
float waveFrequency = 5.2;
float animationSpeed = 3.6;
float waveAmplitude = 0.15;

// Simple RGB Color struct
struct ColorRGB {
  uint8_t r;
  uint8_t g;
  uint8_t b;
};

// Forward declarations
float fract(float val);
ColorRGB hsvToRgb(float h, float s, float v);

// Returns stripe color for the specified theme and time offset
ColorRGB getStripeColor(int stripeIdx, float t) {
  if (currentTheme == THEME_RAINBOW) {
    float hue = fract((float)stripeIdx / 12.0 * 1.3 - t * 0.45);
    return hsvToRgb(hue, 1.0, 1.0);
  }
  
  ColorRGB colorA, colorB;
  switch (currentTheme) {
    case THEME_THIN_BLUE_LINE:
      colorA = {18, 18, 18}; // Dark Charcoal
      colorB = {210, 210, 210}; // Grey
      if (stripeIdx == 7) return {0, 45, 255}; // Blue
      break;
      
    case THEME_THIN_RED_LINE:
      colorA = {18, 18, 18};
      colorB = {210, 210, 210};
      if (stripeIdx == 7) return {229, 0, 0}; // Red
      break;
      
    case THEME_FIRST_RESPONDERS:
      colorA = {18, 18, 18};
      colorB = {210, 210, 210};
      if (stripeIdx == 7) return {0, 45, 255}; // Blue
      if (stripeIdx == 9) return {229, 0, 0};  // Red
      break;

    case THEME_THIN_GREEN_LINE:
      colorA = {18, 18, 18};
      colorB = {210, 210, 210};
      if (stripeIdx == 7) return {0, 163, 0}; // Green
      break;

    case THEME_THIN_GOLD_LINE:
      colorA = {18, 18, 18};
      colorB = {210, 210, 210};
      if (stripeIdx == 7) return {255, 215, 0}; // Gold
      break;
      
    case THEME_ALL_RESPONDERS:
      colorA = {20, 20, 20}; // Black
      colorB = {210, 210, 210}; // Grey
      if (stripeIdx == 1) return {127, 127, 127}; // Corrections Grey
      if (stripeIdx == 3) return {255, 215, 0};   // Dispatcher Gold
      if (stripeIdx == 5) return {0, 163, 0};     // Military Green
      if (stripeIdx == 7) return {0, 45, 255};    // Police Blue
      if (stripeIdx == 9) return {229, 0, 0};     // Firefighter Red
      if (stripeIdx == 11) return {255, 255, 255}; // EMS White
      break;
      
    case THEME_VAPORWAVE:
      colorA = {255, 113, 206}; // Hot Pink
      colorB = {185, 103, 255}; // Purple
      break;
      
    case THEME_MONOCHROME:
      colorA = {43, 43, 43};
      colorB = {226, 232, 240};
      break;
      
    case THEME_CLASSIC:
    default:
      colorA = {178, 34, 52}; // Old Glory Red
      colorB = {255, 255, 255}; // White
      break;
  }
  
  // US flag stripes alternate: Red (even index counting from top 1..13) and White (odd index)
  return (stripeIdx % 2 == 0) ? colorA : colorB;
}

ColorRGB getCantonBgColor(float t) {
  if (currentTheme == THEME_RAINBOW) {
    return hsvToRgb(fract(t * 0.08), 0.9, 0.22);
  }
  if (currentTheme == THEME_THIN_BLUE_LINE || currentTheme == THEME_THIN_RED_LINE || 
      currentTheme == THEME_FIRST_RESPONDERS || currentTheme == THEME_ALL_RESPONDERS ||
      currentTheme == THEME_THIN_GREEN_LINE || currentTheme == THEME_THIN_GOLD_LINE) {
    return {26, 26, 26}; // Tactical Black canton
  }
  if (currentTheme == THEME_VAPORWAVE) {
    return {1, 205, 254}; // Vaporwave Cyan
  }
  if (currentTheme == THEME_MONOCHROME) {
    return {15, 23, 42};
  }
  return {60, 59, 110}; // Old Glory Blue
}

ColorRGB getStarColor(float t) {
  if (currentTheme == THEME_RAINBOW) {
    return hsvToRgb(fract(t * 0.25), 0.85, 1.0);
  }
  if (currentTheme == THEME_VAPORWAVE) {
    return {255, 251, 150}; // Neon Yellow
  }
  return {255, 255, 255};
}

void setup() {
  Serial.begin(115200);

  // Initialize Matrix Driver
  ProtomatterStatus status = matrix.begin();
  Serial.print("Protomatter status: ");
  Serial.println((int)status);
  
  if (status != PROTOMATTER_OK) {
    while (1) delay(10);
  }

  // Initialize LIS3DH Accelerometer
  if (lis.begin(0x19)) {
    lis.setRange(LIS3DH_RANGE_2_G);
    accelEnabled = true;
    Serial.println("LIS3DH Accelerometer started successfully.");
  } else {
    Serial.println("Could not start LIS3DH. Defaulting to landscape orientation.");
  }
}

void loop() {
  float t = millis() * 0.001; // Time in seconds

  // 1. Cycle themes every 10 seconds automatically
  static unsigned long lastCycleTime = 0;
  if (millis() - lastCycleTime > 10000) {
    lastCycleTime = millis();
    currentTheme = (Theme)((currentTheme + 1) % 10);
    Serial.print("Cycled Theme: ");
    Serial.println((int)currentTheme);
  }

  // 2. Read accelerometer to auto-rotate layout
  if (accelEnabled) {
    sensors_event_t event;
    lis.getEvent(&event);
    float x_acc = event.acceleration.x;
    float y_acc = event.acceleration.y;
    
    if (abs(x_acc) > abs(y_acc) + 2.0) {
      verticalMode = true; // Rotated to portrait orientation
    } else if (abs(y_acc) > abs(x_acc) + 2.0) {
      verticalMode = false; // Landscape orientation
    }
  }

  // 3. Draw the flag pixel by pixel
  for (int y = 0; y < HEIGHT; y++) {
    for (int x = 0; x < WIDTH; x++) {
      
      // Normalized coordinates
      float u = (float)x / (float)WIDTH;
      float v = (float)y / (float)HEIGHT;
      
      // 1. Determine base color (Canton vs Stripes)
      ColorRGB baseColor;
      bool inCanton = false;
      float cUvX = 0.0;
      float cUvY = 0.0;
      int stripeIdx = 0;
      
      if (verticalMode) {
        // Vertical Hanging layout: Canton is top-left (y < 17, x >= 38)
        inCanton = (y < 17 && x >= 38);
        if (inCanton) {
          cUvX = (float)y / 17.0;
          cUvY = (float)(x - 38) / 26.0;
        } else {
          // Stripes hang vertically, vary along the horizontal axis (y)
          stripeIdx = (y * 13) / HEIGHT;
        }
      } else {
        // Horizontal layout: Canton is top-left (x < 26, y < 17)
        inCanton = (x < 26 && y < 17);
        if (inCanton) {
          cUvX = (float)x / 26.0;
          cUvY = (float)y / 17.0;
        } else {
          // Stripes run horizontally, vary along the vertical axis (y)
          stripeIdx = (y * 13) / HEIGHT;
        }
      }
      
      if (inCanton) {
        // Draw Canton background
        baseColor = getCantonBgColor(t);
        
        bool isStarPixel = false;
        
        if (starLayout == 0) {
          // --- 50-Star Grid ---
          float colF = cUvX * 12.0;
          float rowF = cUvY * 10.0;
          
          int c = (int)round(colF);
          int r = (int)round(rowF);
          
          if (r >= 1 && r <= 9 && c >= 1 && c <= 11) {
            bool isValid = false;
            if (r % 2 == 1 && c % 2 == 1) isValid = true;
            else if (r % 2 == 0 && c % 2 == 0) isValid = true;
            
            if (isValid) {
              float starCenterX, starCenterY;
              float dx, dy;
              
              if (verticalMode) {
                starCenterX = ((float)c / 12.0) * 17.0;
                starCenterY = ((float)r / 10.0) * 26.0 + 38.0;
                dx = abs((float)y - starCenterX);
                dy = abs((float)x - starCenterY);
              } else {
                starCenterX = ((float)c / 12.0) * 26.0;
                starCenterY = ((float)r / 10.0) * 17.0;
                dx = abs((float)x - starCenterX);
                dy = abs((float)y - starCenterY);
              }
              
              if (dx < 0.65 && dy < 0.65) {
                isStarPixel = true;
              } else if ((dx < 1.1 && dy < 0.35) || (dy < 1.1 && dx < 0.35)) {
                isStarPixel = true; 
              }
            }
          }
        } else {
          // --- 13-Star Circle (Betsy Ross) ---
          float aspect = verticalMode ? (17.0 / 26.0) : (26.0 / 17.0);
          float uvCenteredX = (cUvX - 0.5) * aspect;
          float uvCenteredY = cUvY - 0.5;
          
          float minDist = 999.0;
          for (int i = 0; i < 13; i++) {
            float angle = (float)i * (2.0 * M_PI / 13.0) - M_PI / 2.0;
            float starCenterX = cos(angle) * 0.33;
            float starCenterY = sin(angle) * 0.33;
            
            float dx = uvCenteredX - starCenterX;
            float dy = uvCenteredY - starCenterY;
            float dist = sqrt(dx*dx + dy*dy);
            
            if (dist < minDist) {
              minDist = dist;
            }
          }
          
          if (minDist < 0.042) {
            isStarPixel = true;
          }
        }
        
        if (isStarPixel) {
          baseColor = getStarColor(t);
        }
        
      } else {
        baseColor = getStripeColor(stripeIdx, t);
      }
      
      // 2. Apply Wave Illumination Overlay
      float wavePhase;
      if (verticalMode) {
        // Downward waving phase propagation
        wavePhase = u * waveFrequency * 0.65 + (1.0 - v) * waveFrequency * 0.65 - t * animationSpeed;
      } else {
        // Left-to-right waving phase propagation
        wavePhase = u * waveFrequency * 0.65 + (1.0 - v) * waveFrequency * 0.65 - t * animationSpeed;
      }
      float waveShading = 0.76 + 0.24 * sin(wavePhase);
      
      uint8_t finalR = (uint8_t)constrain(baseColor.r * waveShading, 0, 255);
      uint8_t finalG = (uint8_t)constrain(baseColor.g * waveShading, 0, 255);
      uint8_t finalB = (uint8_t)constrain(baseColor.b * waveShading, 0, 255);
      
      // Draw to offscreen buffer
      matrix.drawPixel(x, y, matrix.color565(finalR, finalG, finalB));
    }
  }

  // Swap buffers to display new frame
  matrix.show();
  delay(16); // ~60fps target
}

// Utility: Fraction function matching GLSL fract()
float fract(float val) {
  return val - floor(val);
}

// Utility: HSV to RGB conversion
ColorRGB hsvToRgb(float h, float s, float v) {
  float r = 0, g = 0, b = 0;
  
  int i = floor(h * 6);
  float f = h * 6 - i;
  float p = v * (1 - s);
  float q = v * (1 - f * s);
  float t = v * (1 - (1 - f) * s);
  
  switch (i % 6) {
    case 0: r = v, g = t, b = p; break;
    case 1: r = q, g = v, b = p; break;
    case 2: r = p, g = v, b = t; break;
    case 3: r = p, g = q, b = v; break;
    case 4: r = t, g = p, b = v; break;
    case 5: r = v, g = p, b = q; break;
  }
  
  return { (uint8_t)(r * 255), (uint8_t)(g * 255), (uint8_t)(b * 255) };
}
