/** Genzura palette (Alier, UI/UX): Dark Navy background, Gold buttons, white text. */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  // Tailwind's reset is off so it doesn't change the existing styles.css design.
  corePlugins: { preflight: false },
  theme: {
    extend: {
      colors: {
        navy: { 900: "#0A192F", 800: "#112240", 700: "#1D3557", 600: "#233554" },
        gold: { 500: "#D4AF37", 400: "#E2C45F", 600: "#B8962E" },
        risk: { high: "#DC2626", medium: "#F59E0B", low: "#22C55E" },
        ink: "#FFFFFF",
      },
      fontFamily: {
        display: ["Oswald Variable", "Arial Narrow", "Impact", "sans-serif"],
        mono: ["Space Mono", "ui-monospace", "Courier New", "monospace"],
        sans: ["Space Mono", "ui-monospace", "Courier New", "monospace"],
      },
      // Design rule: touch targets at least 44px.
      minHeight: { touch: "44px" },
      minWidth: { touch: "44px" },
    },
  },
  plugins: [],
};
