// Curated theme palettes mapping to the 13 stripes
export const THEMES = {
  classic: {
    name: 'Old Glory',
    stripeColors: [
      '#B22234', '#FFFFFF', '#B22234', '#FFFFFF', '#B22234', '#FFFFFF',
      '#B22234', '#FFFFFF', '#B22234', '#FFFFFF', '#B22234', '#FFFFFF', '#B22234'
    ],
    cantonColor: '#3C3B6E',
    starColor: '#FFFFFF',
    rainbowMode: false
  },
  rainbowWave: {
    name: 'Rainbow Wave 🏳️‍🌈',
    stripeColors: Array(13).fill('#FF0000'), // generated procedurally on GPU
    cantonColor: '#3C3B6E',
    starColor: '#FFFFFF',
    rainbowMode: true
  },
  pride6: {
    name: 'Pride Rainbow',
    stripeColors: [
      '#782080', '#782080', // Violet (2 stripes)
      '#0000FF', '#0000FF', // Blue (2 stripes)
      '#008000', '#008000', // Green (2 stripes)
      '#FFFF00', '#FFFF00', // Yellow (2 stripes)
      '#FFA500', '#FFA500', // Orange (2 stripes)
      '#FF0000', '#FF0000', '#FF0000' // Red (3 stripes)
    ],
    cantonColor: '#1a0e40',
    starColor: '#FFFFFF',
    rainbowMode: false
  },
  pride8: {
    name: 'Gilbert Baker',
    stripeColors: [
      '#782080', // Violet
      '#1a0f5c', // Indigo
      '#00a2ff', '#00a2ff', // Turquoise
      '#008000', // Green
      '#FFFF00', '#FFFF00', // Yellow
      '#FFA500', // Orange
      '#FF0000', '#FF0000', // Red
      '#ff69b4', '#ff69b4', '#ff69b4' // Pink
    ],
    cantonColor: '#2b104a',
    starColor: '#FFFFFF',
    rainbowMode: false
  },
  transgender: {
    name: 'Trans Pride 🏳️‍⚧️',
    stripeColors: [
      '#5BCEFA', '#5BCEFA', '#5BCEFA', // Light Blue
      '#F5A9B8', '#F5A9B8', '#F5A9B8', // Pink
      '#FFFFFF', '#FFFFFF', // White
      '#F5A9B8', '#F5A9B8', '#F5A9B8', // Pink
      '#5BCEFA', '#5BCEFA' // Light Blue
    ],
    cantonColor: '#5BCEFA',
    starColor: '#FFFFFF',
    rainbowMode: false
  },
  bisexual: {
    name: 'Bi Pride',
    stripeColors: [
      '#0038A8', '#0038A8', '#0038A8', '#0038A8', '#0038A8', // Blue
      '#9B4F96', '#9B4F96', '#9B4F96', // Purple
      '#D60270', '#D60270', '#D60270', '#D60270', '#D60270' // Pink
    ],
    cantonColor: '#9B4F96',
    starColor: '#D60270',
    rainbowMode: false
  },
  lesbian: {
    name: 'Lesbian Pride',
    stripeColors: [
      '#A30262', '#A30262', '#A30262', // Dark Rose
      '#C4408B', '#C4408B', // Pink
      '#FFFFFF', '#FFFFFF', // White
      '#E46222', '#E46222', '#E46222', // Light Orange
      '#A50000', '#A50000', '#A50000' // Dark Orange
    ],
    cantonColor: '#A30262',
    starColor: '#FFFFFF',
    rainbowMode: false
  },
  nonbinary: {
    name: 'Non-Binary',
    stripeColors: [
      '#000000', '#000000', '#000000', // Black
      '#9C59D1', '#9C59D1', '#9C59D1', // Purple
      '#FFFFFF', '#FFFFFF', '#FFFFFF', // White
      '#FFF430', '#FFF430', '#FFF430', '#FFF430' // Yellow
    ],
    cantonColor: '#9C59D1',
    starColor: '#FFF430',
    rainbowMode: false
  },
  neonCyber: {
    name: 'Neon Cyber ⚡',
    stripeColors: [
      '#8a2be2', '#8a2be2', // Neon Violet
      '#ff007f', '#ff007f', // Neon Magenta
      '#00f6ff', '#00f6ff', // Neon Cyan
      '#8a2be2', '#8a2be2',
      '#ff007f', '#ff007f',
      '#00f6ff', '#00f6ff', '#00f6ff'
    ],
    cantonColor: '#ff007f',
    starColor: '#39ff14', // Neon Green
    rainbowMode: false
  },
  neonToxic: {
    name: 'Neon Toxic ☢️',
    stripeColors: [
      '#000000', '#000000',
      '#ff00ff', '#ff00ff', // Hot Pink
      '#000000', '#000000',
      '#39ff14', '#39ff14', // Slime Green
      '#000000', '#000000',
      '#ffff00', '#ffff00', '#ffff00' // Laser Yellow
    ],
    cantonColor: '#000000',
    starColor: '#39ff14',
    rainbowMode: false
  },
  monochrome: {
    name: 'Monochrome 🌑',
    stripeColors: [
      '#2b2b2b', '#e2e8f0', '#2b2b2b', '#e2e8f0', '#2b2b2b', '#e2e8f0',
      '#2b2b2b', '#e2e8f0', '#2b2b2b', '#e2e8f0', '#2b2b2b', '#e2e8f0', '#2b2b2b'
    ],
    cantonColor: '#0f172a',
    starColor: '#f8fafc',
    rainbowMode: false
  },
  sunrise: {
    name: 'Sunrise 🌅',
    stripeColors: [
      '#ff6b6b', '#ffe66d', '#ff6b6b', '#ffe66d', '#ff6b6b', '#ffe66d',
      '#ff6b6b', '#ffe66d', '#ff6b6b', '#ffe66d', '#ff6b6b', '#ffe66d', '#ff6b6b'
    ],
    cantonColor: '#4ecdc4',
    starColor: '#ffffff',
    rainbowMode: false
  },
  vaporwave: {
    name: 'Vaporwave 🌊',
    stripeColors: [
      '#ff71ce', '#b967ff', '#ff71ce', '#b967ff', '#ff71ce', '#b967ff',
      '#ff71ce', '#b967ff', '#ff71ce', '#b967ff', '#ff71ce', '#b967ff', '#ff71ce'
    ],
    cantonColor: '#01cdfe',
    starColor: '#fffb96',
    rainbowMode: false
  },
  vintage: {
    name: 'Vintage 📜',
    stripeColors: [
      '#c05c36', '#e6dfd1', '#c05c36', '#e6dfd1', '#c05c36', '#e6dfd1',
      '#c05c36', '#e6dfd1', '#c05c36', '#e6dfd1', '#c05c36', '#e6dfd1', '#c05c36'
    ],
    cantonColor: '#2c3e50',
    starColor: '#e6dfd1',
    rainbowMode: false
  },
  thinBlueLine: {
    name: 'Thin Blue Line 👮',
    stripeColors: [
      '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A', '#002DFF',
      '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A'
    ],
    cantonColor: '#1A1A1A',
    starColor: '#E2E8F0',
    rainbowMode: false
  },
  thinRedLine: {
    name: 'Thin Red Line 🧑‍🚒',
    stripeColors: [
      '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A', '#E50000',
      '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A'
    ],
    cantonColor: '#1A1A1A',
    starColor: '#E2E8F0',
    rainbowMode: false
  },
  thinRedBlueLine: {
    name: 'First Responders 🚑',
    stripeColors: [
      '#1A1A1A', '#D8D8D8', '#1A1A1A', '#E50000', '#1A1A1A', '#002DFF',
      '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A'
    ],
    cantonColor: '#1A1A1A',
    starColor: '#E2E8F0',
    rainbowMode: false
  },
  thinGreenLine: {
    name: 'Thin Green Line 🪖',
    stripeColors: [
      '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A', '#00A300',
      '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A'
    ],
    cantonColor: '#1A1A1A',
    starColor: '#E2E8F0',
    rainbowMode: false
  },
  thinGoldLine: {
    name: 'Thin Gold Line ☎️',
    stripeColors: [
      '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A', '#FFD700',
      '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A', '#D8D8D8', '#1A1A1A'
    ],
    cantonColor: '#1A1A1A',
    starColor: '#E2E8F0',
    rainbowMode: false
  }
};
