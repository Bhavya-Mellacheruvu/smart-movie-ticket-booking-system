import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "../styles.css";
import "../auth.css";
import "../city.css";
import "../movies.css";

createRoot(document.getElementById("root")).render(<App />);
