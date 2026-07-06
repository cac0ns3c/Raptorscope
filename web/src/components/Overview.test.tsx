// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, vi } from "vitest";

import { Overview } from "./Overview";
import { renderWithApi } from "../test/renderWithApi";

beforeEach(() => window.localStorage.clear());

describe("Overview", () => {
  it("shows dataset tiles and the persistence-type breakdown", async () => {
    renderWithApi(<Overview caseName="mac-victim" />);
    // a dataset tile
    const overview = await screen.findByLabelText("overview");
    expect(within(overview).getByText("persistence")).toBeInTheDocument();

    const ptypes = screen.getByLabelText("persistence types");
    for (const t of ["launch_agent", "login_item", "cron", "config_profile", "btm"]) {
      expect(within(ptypes).getByText(t)).toBeInTheDocument();
    }
  });

  it("drills into a dataset when a tile is clicked", async () => {
    const onOpenDataset = vi.fn();
    renderWithApi(<Overview caseName="mac-victim" onOpenDataset={onOpenDataset} />);
    await userEvent.click(
      await screen.findByRole("button", { name: /view 12 persistence artifacts/i }),
    );
    expect(onOpenDataset).toHaveBeenCalledWith("macos.persistence");
  });

  it("drills into processes from the unsigned-process counter", async () => {
    const onOpenDataset = vi.fn();
    renderWithApi(<Overview caseName="mac-victim" onOpenDataset={onOpenDataset} />);
    await userEvent.click(
      await screen.findByRole("button", { name: /view 1 unsigned processes/i }),
    );
    expect(onOpenDataset).toHaveBeenCalledWith("macos.process");
  });

  it("shows unsigned counters and the document total", async () => {
    renderWithApi(<Overview caseName="mac-victim" />);
    expect(await screen.findByText(/22 documents total/)).toBeInTheDocument();
    expect(screen.getByText("Unsigned processes")).toBeInTheDocument();
    expect(screen.getByText("Unsigned applications")).toBeInTheDocument();
  });

  it("generates an AI case summary on demand", async () => {
    renderWithApi(<Overview caseName="mac-victim" />);
    await userEvent.click(
      await screen.findByRole("button", { name: /Summarize case/ }),
    );
    expect(await screen.findByText(/Bottom line/)).toBeInTheDocument();
  });

  it("persists the summary across remounts until re-run", async () => {
    const { unmount } = renderWithApi(<Overview caseName="mac-victim" />);
    await userEvent.click(
      await screen.findByRole("button", { name: /Summarize case/ }),
    );
    await screen.findByText(/Bottom line/);
    unmount();
    // fresh mount restores the summary from storage without another API call
    renderWithApi(<Overview caseName="mac-victim" />);
    expect(await screen.findByText(/Bottom line/)).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: /Re-summarize/ }),
    ).toBeInTheDocument();
  });
});
