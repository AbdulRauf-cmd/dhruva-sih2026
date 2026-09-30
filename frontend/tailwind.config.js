/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'tier-green': '#22c55e',
        'tier-amber': '#f59e0b',
        'tier-red': '#ef4444',
        'tier-black': '#111827',
      }
    },
  },
  plugins: [],
}
