import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Primary (Blue)
        primary: {
          50: "#EFF6FF",
          100: "#DBEAFE",
          200: "#BFDBFE",
          300: "#93C5FD",
          400: "#60A5FA",
          500: "#3B82F6",
          600: "#2563EB",
          700: "#1E40AF",
          800: "#1E3A5F",
          900: "#1E3A8A",
        },
        // Secondary (Saffron)
        saffron: {
          50: "#FFF8F0",
          100: "#FFF3E0",
          200: "#FFE0B2",
          300: "#FFCC80",
          400: "#FFB74D",
          500: "#FF9933",
          600: "#F57C00",
          700: "#E65100",
        },
        // Success (Green)
        success: {
          50: "#F0FDF4",
          100: "#DCFCE7",
          200: "#BBF7D0",
          400: "#4ADE80",
          500: "#16A34A",
          600: "#15803D",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
    },
  },
  plugins: [],
};

export default config;
