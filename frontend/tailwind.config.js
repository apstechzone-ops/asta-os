/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        core: {
          bg: "#05070d",
          panel: "rgba(15, 23, 42, 0.55)",
          border: "rgba(56, 189, 248, 0.25)",
          cyan: "#22d3ee",
          violet: "#818cf8",
          text: "#e2e8f0",
        },
      },
      backdropBlur: {
        glass: "18px",
      },
      boxShadow: {
        neon: "0 0 20px rgba(34, 211, 238, 0.35)",
      },
      fontFamily: {
        display: ["'Orbitron'", "sans-serif"],
        body: ["'Rajdhani'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
