/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        "jic-light": {
          "primary": "#2d6a4f",       /* Deep forest green */
          "primary-content": "#ffffff",
          "secondary": "#52b788",     /* Fresh leaf green */
          "accent": "#d97706",        /* Amber accent for risks/warnings */
          "neutral": "#1e293b",       /* Slate neutral text */
          "base-100": "#ffffff",      /* Main light background */
          "base-200": "#f8fafc",      /* Off-white background */
          "base-300": "#f1f5f9",      /* Section shading */
          "info": "#0284c7",
          "success": "#16a34a",
          "warning": "#ca8a04",
          "error": "#dc2626",
        },
        "jic-dark": {
          "primary": "#22c55e",       /* Vibrant nature green accent */
          "primary-content": "#ffffff",
          "secondary": "#15803d",     /* Deeper nature green */
          "accent": "#fbbf24",        /* High contrast warning amber */
          "neutral": "#1f2937",       /* Dark slate card headers/borders */
          "base-100": "#0b0f19",      /* Deep space/slate dark background */
          "base-200": "#111827",      /* Slate card background */
          "base-300": "#1f2937",      /* Slate shading */
          "info": "#38bdf8",
          "success": "#4ade80",
          "warning": "#facc15",
          "error": "#f87171",
        },
      },
    ],
  }
}
