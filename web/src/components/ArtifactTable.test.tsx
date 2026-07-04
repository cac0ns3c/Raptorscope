// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ArtifactTable } from "./ArtifactTable";
import { renderWithApi } from "../test/renderWithApi";

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
});
