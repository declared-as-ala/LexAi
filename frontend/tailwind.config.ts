import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        gold: {
          50:  "#FFFDF0",
          100: "#FFF8D6",
          200: "#FAEDB0",
          300: "#F0D55A",
          400: "#E8C547",
          500: "#C9A336",
          600: "#A88420",
          700: "#856510",
          800: "#5C4408",
          900: "#332602",
          DEFAULT: "#C9A336",
        },
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"Plus Jakarta Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        lex: "inset 0 1px 0 rgba(255,255,255,0.95), 0 4px 20px rgba(201,163,54,0.08), 0 1px 4px rgba(28,26,8,0.06)",
        "lex-gold": "0 4px 24px rgba(201,163,54,0.25), 0 1px 4px rgba(201,163,54,0.15)",
        "lex-hover": "inset 0 1px 0 rgba(255,255,255,0.95), 0 8px 32px rgba(201,163,54,0.14), 0 2px 6px rgba(28,26,8,0.08)",
      },
    },
  },
  plugins: [],
} satisfies Config;
