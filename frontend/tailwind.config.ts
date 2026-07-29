import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["\"IBM Plex Sans\"", "system-ui", "sans-serif"],
        mono: ["\"IBM Plex Mono\"", "ui-monospace", "monospace"],
      },
      colors: {
        ink: "#0f1c2e",
        mist: "#e8eef5",
        accent: "#0d7377",
        warn: "#c45c26",
        ok: "#2d6a4f",
      },
    },
  },
  plugins: [],
} satisfies Config;
