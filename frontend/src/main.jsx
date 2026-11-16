import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
// Fonts are bundled with the app (no Google Fonts request).
import "@fontsource-variable/fraunces/wght.css";
import "@fontsource-variable/plus-jakarta-sans/wght.css";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
