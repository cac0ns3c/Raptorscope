// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { CasePicker } from "./CasePicker";
import { makeFakeClient } from "../test/fakeClient";
import { renderWithApi } from "../test/renderWithApi";

describe("CasePicker", () => {
  it("lists the available cases", async () => {
    renderWithApi(<CasePicker onSelect={() => {}} />);
    expect(await screen.findByText("mac-victim")).toBeInTheDocument();
    expect(screen.getByText("mac-clean")).toBeInTheDocument();
    expect(screen.getByText("22 docs")).toBeInTheDocument();
  });

  it("fires onSelect with the chosen case name", async () => {
    const onSelect = vi.fn();
    renderWithApi(<CasePicker onSelect={onSelect} />);
    await screen.findByText("mac-victim");
    await userEvent.click(screen.getByText("mac-victim"));
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ name: "mac-victim" }),
    );
  });

  it("shows an empty state when there are no cases", async () => {
    const client = { ...makeFakeClient(), listCases: async () => [] };
    renderWithApi(<CasePicker onSelect={() => {}} />, client);
    await waitFor(() =>
      expect(screen.getByText(/no cases/i)).toBeInTheDocument(),
    );
  });

  it("hunts an IOC across all hosts and pivots to a host", async () => {
    const onSelect = vi.fn();
    renderWithApi(<CasePicker onSelect={onSelect} />);
    await screen.findByText("mac-victim");
    await userEvent.type(
      screen.getByLabelText("hunt indicator across hosts"),
      "45.9.148.99",
    );
    await userEvent.click(screen.getByRole("button", { name: "Hunt" }));
    const result = await screen.findByLabelText("hunt result");
    // correlated across 2 hosts
    expect(result).toHaveTextContent(/found on\s*2\s*of/);
    // clicking a host opens that case
    await userEvent.click(within(result).getByText("mac-victim"));
    expect(onSelect).toHaveBeenCalled();
  });

});
