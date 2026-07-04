// SPDX-License-Identifier: GPL-3.0-or-later
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AuthError } from "../api/client";
import { AuthGate } from "./AuthGate";
import { useAuthSession } from "../context/AuthSessionContext";
import { makeFakeClient } from "../test/fakeClient";
import { renderWithApi } from "../test/renderWithApi";

function LogoutButton() {
  const { logout } = useAuthSession();
  return <button onClick={logout}>do-logout</button>;
}

describe("AuthGate", () => {
  it("renders children when the API is open (auth disabled)", async () => {
    renderWithApi(
      <AuthGate tokenHolder={{ current: null }}>
        <div>protected content</div>
      </AuthGate>,
    );
    expect(await screen.findByText("protected content")).toBeInTheDocument();
  });

  it("shows login on 401 and reveals content after signing in", async () => {
    const holder = { current: null as string | null };
    const client = {
      ...makeFakeClient(),
      listCases: async () => {
        if (!holder.current) throw new AuthError("unauthorized");
        return [];
      },
    };
    renderWithApi(
      <AuthGate tokenHolder={holder}>
        <div>protected content</div>
      </AuthGate>,
      client,
    );
    // gated: login screen appears
    await screen.findByRole("button", { name: /sign in/i });
    await userEvent.type(screen.getByLabelText("username"), "analyst");
    await userEvent.type(screen.getByLabelText("password"), "s3cret");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    // token set -> re-probe succeeds -> content shows
    expect(await screen.findByText("protected content")).toBeInTheDocument();
  });

  it("logout clears the token and returns to login", async () => {
    const holder = { current: null as string | null };
    const client = {
      ...makeFakeClient(),
      listCases: async () => {
        if (!holder.current) throw new AuthError("unauthorized");
        return [];
      },
    };
    renderWithApi(
      <AuthGate tokenHolder={holder}>
        <LogoutButton />
      </AuthGate>,
      client,
    );
    // sign in
    await screen.findByRole("button", { name: /sign in/i });
    await userEvent.type(screen.getByLabelText("username"), "analyst");
    await userEvent.type(screen.getByLabelText("password"), "s3cret");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    await screen.findByText("do-logout");
    // log out -> back to login
    await userEvent.click(screen.getByText("do-logout"));
    expect(holder.current).toBeNull();
    expect(await screen.findByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });
});
