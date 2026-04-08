import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          900: "#0f1117",
          800: "#1a1d27",
          700: "#252836",
          600: "#2d3148",
        },
        accent: {
          blue: "#4f8ef7",
          green: "#22c55e",
          yellow: "#f59e0b",
          red: "#ef4444",
          purple: "#a855f7",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
