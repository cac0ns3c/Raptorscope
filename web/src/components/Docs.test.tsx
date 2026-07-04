// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { Docs } from "./Docs";
import { renderWithApi } from "../test/renderWithApi";

describe("Docs", () => {
  it("lists docs and renders the selected one as HTML", async () => {
    renderWithApi(<Docs onClose={() => {}} />);
    const dialog = await screen.findByRole("dialog", { name: "documentation" });
    expect(within(dialog).getByText("Overview")).toBeInTheDocument();
    expect(within(dialog).getByText("Using Kibana")).toBeInTheDocument();
    // markdown rendered to an actual heading element
    expect(await within(dialog).findByRole("heading")).toBeInTheDocument();
  });

  it("switches the rendered doc when a nav item is clicked", async () => {
    renderWithApi(<Docs onClose={() => {}} />);
    const dialog = await screen.findByRole("dialog", { name: "documentation" });
    await userEvent.click(within(dialog).getByRole("button", { name: "Using Kibana" }));
    expect(
      await within(dialog).findByRole("heading", { name: /kibana/i }),
    ).toBeInTheDocument();
  });

  it("closes via the close button", async () => {
    const onClose = vi.fn();
    renderWithApi(<Docs onClose={onClose} />);
    await userEvent.click(await screen.findByLabelText("close docs"));
    expect(onClose).toHaveBeenCalled();
  });
});
