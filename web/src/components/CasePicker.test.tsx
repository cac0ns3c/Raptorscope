// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, waitFor } from "@testing-library/react";
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
    expect(onSelect).toHaveBeenCalledWith("mac-victim");
  });

  it("shows an empty state when there are no cases", async () => {
    const client = { ...makeFakeClient(), listCases: async () => [] };
    renderWithApi(<CasePicker onSelect={() => {}} />, client);
    await waitFor(() =>
      expect(screen.getByText(/no cases/i)).toBeInTheDocument(),
    );
  });
});
