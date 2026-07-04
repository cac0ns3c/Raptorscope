// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import { useApi } from "../context/ApiContext";
import { IconLogo } from "../ui/icons";

export function Login({ onAuth }: { onAuth: (token: string) => void }) {
  const api = useApi();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { token } = await api.login(username, password);
      onAuth(token);
    } catch {
      setError("Invalid username or password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={submit}>
        <span className="hero-mark">
          <IconLogo width={24} height={24} />
        </span>
        <h2>Raptorscope</h2>
        <p className="muted">Sign in to continue</p>
        <label>
          Username
          <input
            aria-label="username"
            value={username}
            autoComplete="username"
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label>
          Password
          <input
            aria-label="password"
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <p className="login-error">{error}</p>}
        <button className="q-run login-btn" type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
