// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, within } from "@testing-library/react";

import { Timeline } from "./Timeline";
import { renderWithApi } from "../test/renderWithApi";

describe("Timeline", () => {
  it("renders events newest-first with dataset badges", async () => {
    renderWithApi(<Timeline caseName="mac-victim" />);
    const list = await screen.findByLabelText("timeline");
    const times = within(list)
      .getAllByTestId("tl-ts")
      .map((t) => t.textContent ?? "");
    // API returns newest-first; the component preserves that order
    expect(times).toEqual([...times].sort().reverse());
    // dataset badges are present
    expect(within(list).getAllByText(/persistence|process|tcc|quarantine|inventory/).length)
      .toBeGreaterThan(0);
  });

  it("shows an empty state for a case with no events", async () => {
    const client = {
      ...(await import("../test/fakeClient")).makeFakeClient(),
      getTimeline: async () => [],
    };
    renderWithApi(<Timeline caseName="mac-victim" />, client);
    expect(await screen.findByText("No events.")).toBeInTheDocument();
  });
});
