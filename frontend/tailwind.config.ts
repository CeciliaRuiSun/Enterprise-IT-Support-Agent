import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#07111f",
          900: "#0f1728",
          800: "#172338",
          700: "#24324b",
          200: "#d9e2f1"
        },
        teal: {
          500: "#22c1c3",
          600: "#0ea5a3"
        },
        amber: {
          400: "#f5b942",
          500: "#f59e0b"
        }
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(34, 193, 195, 0.12), 0 24px 60px rgba(7, 17, 31, 0.45)"
      }
    }
  },
  plugins: []
};

export default config;

