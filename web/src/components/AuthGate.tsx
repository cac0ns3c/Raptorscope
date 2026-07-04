// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState, type ReactNode } from "react";

import { AuthError, type TokenRef } from "../api/client";
import { useApi } from "../context/ApiContext";
import { Login } from "./Login";

/** Probes the API; if it answers 401, shows the login screen until a token is
 *  obtained. When auth is disabled server-side the probe succeeds and children
 *  render immediately. */
export function AuthGate({
  tokenHolder,
  children,
}: {
  tokenHolder: TokenRef;
  children: ReactNode;
}) {
  const api = useApi();
  const [status, setStatus] = useState<"checking" | "ok" | "login">("checking");

  function probe() {
    setStatus("checking");
    api.listCases().then(
      () => setStatus("ok"),
      (e: unknown) => setStatus(e instanceof AuthError ? "login" : "ok"),
    );
  }

  useEffect(probe, [api]);

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
            localStorage.setItem("rs_token", token);
          } catch {
            /* ignore storage failures */
          }
          probe();
        }}
      />
    );
  }
  return <>{children}</>;
}
