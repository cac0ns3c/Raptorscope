// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, vi } from "vitest";

import { Alerts } from "./Alerts";
import { renderWithApi } from "../test/renderWithApi";

beforeEach(() => window.localStorage.clear());

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

  it("dismisses an alert and hides it until shown", async () => {
    renderWithApi(<Alerts caseName="mac-victim" />);
    await screen.findByLabelText("alerts");
    const before = screen.getAllByText(/^(high|medium|low)$/).length;
    await userEvent.click(screen.getAllByRole("button", { name: "Dismiss" })[0]);
    expect(screen.getAllByText(/^(high|medium|low)$/).length).toBe(before - 1);
    // re-show dismissed
    await userEvent.click(screen.getByRole("button", { name: /show 1 dismissed/i }));
    expect(screen.getAllByText(/^(high|medium|low)$/).length).toBe(before);
  });

  it("acknowledges an alert and tags it", async () => {
    renderWithApi(<Alerts caseName="mac-victim" />);
    await screen.findByLabelText("alerts");
    await userEvent.click(screen.getAllByRole("button", { name: "Ack" })[0]);
    expect(screen.getByText("acknowledged")).toBeInTheDocument();
    expect(screen.getByText(/1 acknowledged/)).toBeInTheDocument();
  });

  it("runs AI triage and shows the analysis", async () => {
    renderWithApi(<Alerts caseName="mac-victim" />);
    await screen.findByLabelText("alerts");
    const btns = await screen.findAllByRole("button", { name: "AI triage" });
    await userEvent.click(btns[0]);
    expect(await screen.findByText(/Assessment/)).toBeInTheDocument();
  });

  it("persists a triage analysis across remounts", async () => {
    const { unmount } = renderWithApi(<Alerts caseName="mac-victim" />);
    await screen.findByLabelText("alerts");
    const btns = await screen.findAllByRole("button", { name: "AI triage" });
    await userEvent.click(btns[0]);
    await screen.findByText(/Assessment/);
    unmount();
    // fresh mount restores the analysis from storage without re-running it
    renderWithApi(<Alerts caseName="mac-victim" />);
    expect(await screen.findByText(/Assessment/)).toBeInTheDocument();
  });

  it("exposes the pivot as a real button, not a card wrapping the controls", async () => {
    const onPivot = vi.fn();
    renderWithApi(<Alerts caseName="mac-victim" onPivot={onPivot} />);
    await screen.findByLabelText("alerts");
    // The title is a real button that pivots...
    const title = screen.getAllByRole("button", { name: /view evidence:/i })[0];
    await userEvent.click(title);
    expect(onPivot).toHaveBeenCalled();
    // ...and the action buttons are siblings, NOT descendants of it (valid ARIA:
    // a button must not contain other interactive elements).
    const ack = screen.getAllByRole("button", { name: "Ack" })[0];
    expect(title.contains(ack)).toBe(false);
  });

  it("keeps a triage note without pivoting", async () => {
    const onPivot = vi.fn();
    renderWithApi(<Alerts caseName="mac-victim" onPivot={onPivot} />);
    await screen.findByLabelText("alerts");
    await userEvent.click(screen.getAllByRole("button", { name: "Note" })[0]);
    const note = screen.getAllByLabelText(/^note for /)[0];
    await userEvent.type(note, "looks real");
    expect((note as HTMLInputElement).value).toBe("looks real");
    expect(onPivot).not.toHaveBeenCalled();
  });

  it("groups duplicate-rule alerts with a header and bulk-dismisses them", async () => {
    const real = (await import("../test/fakeClient")).makeFakeClient();
    const dupes = [
      { rule_id: "r-dup", title: "macOS repeated finding", level: "high", dataset: "macos.persistence", doc_id: "d1", evidence: {} },
      { rule_id: "r-dup", title: "macOS repeated finding", level: "high", dataset: "macos.persistence", doc_id: "d2", evidence: {} },
      { rule_id: "r-dup", title: "macOS repeated finding", level: "high", dataset: "macos.persistence", doc_id: "d3", evidence: {} },
    ];
    const client = { ...real, getAlerts: async () => dupes };
    renderWithApi(<Alerts caseName="mac-victim" />, client);
    await screen.findByLabelText("alerts");
    // group header with the count + bulk action
    const bulk = await screen.findByRole("button", { name: /dismiss all 3/i });
    expect(bulk).toBeInTheDocument();
    // 3 cards visible before
    expect(screen.getAllByText(/^high$/).length).toBe(3);
    await userEvent.click(bulk);
    // all three dismissed -> gone from the default view
    expect(screen.queryAllByText(/^high$/).length).toBe(0);
  });
});
