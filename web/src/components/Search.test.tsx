// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { Search } from "./Search";
import { renderWithApi } from "../test/renderWithApi";

const DATASETS = ["macos.persistence", "macos.process", "macos.tcc"];

describe("Search", () => {
  it("runs a free-text query and shows matching rows", async () => {
    renderWithApi(
      <Search caseName="mac-victim" datasets={DATASETS} onPivot={() => {}} />,
    );
    await userEvent.type(screen.getByLabelText("query"), "/private/tmp");
    await userEvent.click(screen.getByRole("button", { name: "Search" }));
    const results = await screen.findByLabelText("search results");
    expect(within(results).getAllByTestId("search-row").length).toBeGreaterThan(0);
  });

  it("pivots to evidence when a result row is clicked", async () => {
    const onPivot = vi.fn();
    renderWithApi(
      <Search caseName="mac-victim" datasets={DATASETS} onPivot={onPivot} />,
    );
    await userEvent.type(screen.getByLabelText("query"), "helper");
    await userEvent.click(screen.getByRole("button", { name: "Search" }));
    const rows = await screen.findAllByTestId("search-row");
    await userEvent.click(rows[0]);
    expect(onPivot).toHaveBeenCalled();
    expect(typeof onPivot.mock.calls[0][0]).toBe("string");
  });

  it("scopes results to a chosen dataset", async () => {
    renderWithApi(
      <Search caseName="mac-victim" datasets={DATASETS} onPivot={() => {}} />,
    );
    await userEvent.selectOptions(
      screen.getByLabelText("dataset filter"),
      "macos.tcc",
    );
    await userEvent.type(screen.getByLabelText("query"), "com");
    await userEvent.click(screen.getByRole("button", { name: "Search" }));
    const results = await screen.findByLabelText("search results");
    const badges = within(results).getAllByText("tcc");
    expect(badges.length).toBeGreaterThan(0);
  });
});
