// SPDX-License-Identifier: GPL-3.0-or-later
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { Login } from "./Login";
import { renderWithApi } from "../test/renderWithApi";

describe("Login", () => {
  it("signs in with valid credentials and returns the token", async () => {
    const onAuth = vi.fn();
    renderWithApi(<Login onAuth={onAuth} />);
    await userEvent.type(screen.getByLabelText("username"), "analyst");
    await userEvent.type(screen.getByLabelText("password"), "s3cret");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(onAuth).toHaveBeenCalledWith("fake-token");
  });

  it("shows an error on bad credentials", async () => {
    const onAuth = vi.fn();
    renderWithApi(<Login onAuth={onAuth} />);
    await userEvent.type(screen.getByLabelText("username"), "analyst");
    await userEvent.type(screen.getByLabelText("password"), "nope");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText(/invalid/i)).toBeInTheDocument();
    expect(onAuth).not.toHaveBeenCalled();
  });
});
