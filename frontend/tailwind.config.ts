import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#041627",
          800: "#1a2b3c",
        },
        ghost: "rgba(4, 22, 39, 0.15)",
        surface: "#f7fafc",
        editorial: {
          card: "#ffffff",
          muted: "#64748b",
          error: "#BA1A1A",
          success: "#047857",
          medium: "#B45309",
        },
      },
      fontFamily: {
        headline: ["Newsreader", "serif"],
        body: ["Inter", "sans-serif"],
      },
      boxShadow: {
        editorial: "0 10px 30px rgba(24, 28, 30, 0.04)",
      },
      borderRadius: {
        editorial: "12px",
      },
    },
  },
  plugins: [],
};

export default config;
