import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0b0f14",
          raised: "#111827",
          border: "#1f2937",
        },
        ok: {
          DEFAULT: "#22c55e",
          bg: "#052e16",
        },
        warning: {
          DEFAULT: "#f59e0b",
          bg: "#451a03",
        },
        danger: {
          DEFAULT: "#ef4444",
          bg: "#450a0a",
        },
        muted: {
          DEFAULT: "#6b7280",
          bg: "#111827",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
