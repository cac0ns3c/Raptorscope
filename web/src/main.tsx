// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./App";
import { createHttpClient } from "./api/client";
import { ApiProvider } from "./context/ApiContext";
import "./index.css";

const base = import.meta.env.VITE_API_BASE ?? "/api";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ApiProvider client={createHttpClient(base)}>
      <App />
    </ApiProvider>
  </React.StrictMode>,
);
