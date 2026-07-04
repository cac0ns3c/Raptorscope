// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState, type ReactNode } from "react";

import { AuthError, type TokenRef } from "../api/client";
import { AuthSessionProvider } from "../context/AuthSessionContext";
import { useApi } from "../context/ApiContext";
import { Login } from "./Login";

/** Probes the API; if it answers 401, shows the login screen until a token is
 *  obtained. When auth is disabled server-side the probe succeeds and children
 *  render immediately. Exposes a `logout` to children via AuthSessionContext. */
export function AuthGate({
  tokenHolder,
  children,
}: {
  tokenHolder: TokenRef;
  children: ReactNode;
}) {
  const api = useApi();
  const [status, setStatus] = useState<"checking" | "ok" | "login">("checking");
  const [gated, setGated] = useState(false);

  function probe() {
    setStatus("checking");
    api.listCases().then(
      () => setStatus("ok"),
      (e: unknown) => {
        if (e instanceof AuthError) {
          setGated(true);
          setStatus("login");
        } else {
          setStatus("ok");
        }
      },
    );
  }

  useEffect(probe, [api]);

  function logout() {
    tokenHolder.current = null;
    try {
      window.localStorage.removeItem("rs_token");
    } catch {
      /* ignore */
    }
    setStatus("login");
  }

  if (status === "checking") {
    return (
      <div className="state center">
        <span className="spinner" /> Connecting…
      </div>
    );
  }
  if (status === "login") {
    return (
      <Login
        onAuth={(token) => {
          tokenHolder.current = token;
          try {
            window.localStorage.setItem("rs_token", token);
          } catch {
            /* ignore */
          }
          probe();
        }}
      />
    );
  }
  return (
    <AuthSessionProvider value={{ gated, logout }}>
      {children}
    </AuthSessionProvider>
  );
}
