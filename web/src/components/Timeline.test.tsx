// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

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
    // persistence rows carry an mtime provenance badge
    expect(within(list).getAllByText("mtime").length).toBeGreaterThan(0);
  });

  it("shows an empty state for a case with no events", async () => {
    const client = {
      ...(await import("../test/fakeClient")).makeFakeClient(),
      getTimeline: async () => [],
    };
    renderWithApi(<Timeline caseName="mac-victim" />, client);
    expect(await screen.findByText(/no events/i)).toBeInTheDocument();
  });

  it("shows an error with Retry that re-fetches and recovers", async () => {
    const real = (await import("../test/fakeClient")).makeFakeClient();
    let calls = 0;
    const client = {
      ...real,
      getTimeline: async (...args: Parameters<typeof real.getTimeline>) => {
        calls += 1;
        if (calls === 1) throw new Error("boom");
        return real.getTimeline(...args);
      },
    };
    renderWithApi(<Timeline caseName="mac-victim" />, client);
    // first load fails -> error state with an actionable Retry
    const retry = await screen.findByRole("button", { name: /retry/i });
    await userEvent.click(retry);
    // second load succeeds -> timeline renders
    expect(await screen.findByLabelText("timeline")).toBeInTheDocument();
  });
});

describe("Timeline filters", () => {
  it("filters rows by dataset chip", async () => {
    renderWithApi(<Timeline caseName="mac-victim" />);
    const list = await screen.findByLabelText("timeline");
    const before = list.querySelectorAll(".timeline-row").length;
    const chip = screen
      .getAllByRole("button")
      .find((b) => /^persistence \d+/i.test(b.textContent || ""));
    expect(chip).toBeTruthy();
    await userEvent.click(chip!);
    const after = document
      .querySelector('[aria-label="timeline"]')!
      .querySelectorAll(".timeline-row").length;
    expect(after).toBeGreaterThan(0);
    expect(after).toBeLessThanOrEqual(before);
    // all remaining rows are persistence
    for (const r of document.querySelectorAll(".timeline-row"))
      expect(r.getAttribute("data-dataset")).toBe("macos.persistence");
  });
});
