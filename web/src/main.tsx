// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./App";
import { createHttpClient, type TokenRef } from "./api/client";
import { AuthGate } from "./components/AuthGate";
import { ApiProvider } from "./context/ApiContext";
import "./index.css";

const base = import.meta.env.VITE_API_BASE ?? "/api";

// A stable token holder shared with the client; seeded from localStorage.
const tokenHolder: TokenRef = { current: localStorage.getItem("rs_token") };
const client = createHttpClient(base, tokenHolder);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ApiProvider client={client}>
      <AuthGate tokenHolder={tokenHolder}>
        <App />
      </AuthGate>
    </ApiProvider>
  </React.StrictMode>,
);
