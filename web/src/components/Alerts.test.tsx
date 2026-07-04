// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { Alerts } from "./Alerts";
import { renderWithApi } from "../test/renderWithApi";

describe("Alerts", () => {
  it("renders alerts high-severity first", async () => {
    renderWithApi(<Alerts caseName="mac-victim" />);
    const list = await screen.findByLabelText("alerts");
    const levels = within(list)
      .getAllByText(/^(high|medium|low)$/)
      .map((el) => el.textContent);
    const rank: Record<string, number> = { high: 0, medium: 1, low: 2 };
    expect(levels.map((l) => rank[l!])).toEqual(
      [...levels.map((l) => rank[l!])].sort((a, b) => a - b),
    );
  });

  it("pivots to evidence with the alert's dataset and doc id", async () => {
    const onPivot = vi.fn();
    renderWithApi(<Alerts caseName="mac-victim" onPivot={onPivot} />);
    const card = await screen.findByText(
      "macOS persistence program in suspicious path",
    );
    await userEvent.click(card);
    expect(onPivot).toHaveBeenCalledWith("macos.persistence", "p3");
  });

  it("shows an all-clear state for a benign case", async () => {
    renderWithApi(<Alerts caseName="mac-clean" />);
    expect(
      await screen.findByText(/no detections fired/i),
    ).toBeInTheDocument();
  });
});
