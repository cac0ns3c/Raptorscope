// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach } from "vitest";

import { ArtifactTable } from "./ArtifactTable";
import { renderWithApi } from "../test/renderWithApi";

beforeEach(() => window.localStorage.clear());

describe("ArtifactTable", () => {
  it("renders dataset-appropriate columns and rows", async () => {
    renderWithApi(
      <ArtifactTable caseName="mac-victim" dataset="macos.persistence" />,
    );
    expect(await screen.findByText("Label")).toBeInTheDocument();
    expect(screen.getByText("com.system.helper")).toBeInTheDocument();
    // 12 persistence rows fit under the default page size
    expect(screen.getAllByTestId("artifact-row")).toHaveLength(12);
  });

  it("refetches with the right columns when the dataset changes", async () => {
    const { rerender } = renderWithApi(
      <ArtifactTable caseName="mac-victim" dataset="macos.persistence" />,
    );
    await screen.findByText("Label");
    rerender(
      // ApiProvider is applied by renderWithApi's initial render; rerender keeps it
      <ArtifactTable caseName="mac-victim" dataset="macos.process" />,
    );
    // process columns appear, persistence-only column gone
    expect(await screen.findByText("PID")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.queryByText("Label")).not.toBeInTheDocument(),
    );
  });

  it("opens a detail drawer when a row is clicked", async () => {
    renderWithApi(
      <ArtifactTable caseName="mac-victim" dataset="macos.persistence" />,
    );
    const rows = await screen.findAllByTestId("artifact-row");
    await userEvent.click(rows[0]);
    expect(
      await screen.findByRole("dialog"),
    ).toBeInTheDocument();
  });

  it("sorts rows when a column header is clicked", async () => {
    renderWithApi(
      <ArtifactTable caseName="mac-victim" dataset="macos.persistence" />,
    );
    const header = await screen.findByText("Label");
    await userEvent.click(header);
    expect(header.closest("th")).toHaveAttribute("aria-sort", "ascending");
    await userEvent.click(header);
    expect(header.closest("th")).toHaveAttribute("aria-sort", "descending");
  });

  it("offers CSV and JSON export", async () => {
    renderWithApi(
      <ArtifactTable caseName="mac-victim" dataset="macos.persistence" />,
    );
    expect(await screen.findByRole("button", { name: "CSV" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "JSON" })).toBeInTheDocument();
  });

  it("paginates with Prev/Next", async () => {
    renderWithApi(
      <ArtifactTable
        caseName="mac-victim"
        dataset="macos.persistence"
        pageSize={5}
      />,
    );
    expect(await screen.findByText("1–5 of 12")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("6–10 of 12")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("11–12 of 12")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("hides and restores a column via the column picker", async () => {
    renderWithApi(
      <ArtifactTable caseName="mac-victim" dataset="macos.persistence" />,
    );
    expect(
      await screen.findByRole("columnheader", { name: /Label/ }),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Columns/ }));
    const menu = screen.getByRole("group", { name: "choose columns" });
    // the picker offers more than the curated columns — every field in the data
    expect(within(menu).getByText("event.dataset")).toBeInTheDocument();

    // uncheck the curated "Label" column (target its unique field path)
    const labelRow = within(menu)
      .getByText("raptorscope.persistence.label")
      .closest("label")!;
    await userEvent.click(within(labelRow).getByRole("checkbox"));
    await waitFor(() =>
      expect(
        screen.queryByRole("columnheader", { name: /Label/ }),
      ).not.toBeInTheDocument(),
    );

    // re-check it -> column comes back
    await userEvent.click(within(labelRow).getByRole("checkbox"));
    expect(
      await screen.findByRole("columnheader", { name: /Label/ }),
    ).toBeInTheDocument();
  });

  it("adds a non-default field as a column", async () => {
    renderWithApi(
      <ArtifactTable caseName="mac-victim" dataset="macos.persistence" />,
    );
    await screen.findByRole("columnheader", { name: /Label/ });
    await userEvent.click(screen.getByRole("button", { name: /Columns/ }));
    const menu = screen.getByRole("group", { name: "choose columns" });
    const fileRow = within(menu).getByText("file.name").closest("label")!;
    await userEvent.click(within(fileRow).getByRole("checkbox"));
    // a new "Name" column header appears (humanized from host.name)
    await waitFor(() =>
      expect(
        screen.getAllByRole("columnheader").some((h) => /Name/.test(h.textContent || "")),
      ).toBe(true),
    );
  });
});
