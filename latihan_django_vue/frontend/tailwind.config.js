/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["\"Space Grotesk\"", "ui-sans-serif", "system-ui"],
        body: ["\"Plus Jakarta Sans\"", "ui-sans-serif", "system-ui"],
      },
      boxShadow: {
        soft: "0 10px 30px rgba(15, 23, 42, 0.12)",
        glow: "0 0 0 6px rgba(16, 185, 129, 0.12)",
      },
      colors: {
        sand: "#F6F1EA",
        ink: "#1F2937",
        coral: "#F97316",
        moss: "#16A34A",
        ocean: "#0EA5E9",
      },
    },
  },
  plugins: [],
}
