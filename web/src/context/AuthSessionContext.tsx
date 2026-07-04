// SPDX-License-Identifier: GPL-3.0-or-later
import { createContext, useContext, type ReactNode } from "react";

export interface AuthSession {
  /** True once the API has required a login this session. */
  gated: boolean;
  logout: () => void;
}

const AuthSessionContext = createContext<AuthSession>({
  gated: false,
  logout: () => {},
});

export function AuthSessionProvider({
  value,
  children,
}: {
  value: AuthSession;
  children: ReactNode;
}) {
  return (
    <AuthSessionContext.Provider value={value}>
      {children}
    </AuthSessionContext.Provider>
  );
}

export function useAuthSession(): AuthSession {
  return useContext(AuthSessionContext);
}
