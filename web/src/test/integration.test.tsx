// SPDX-License-Identifier: GPL-3.0-or-later
// End-to-end (fake client): case select -> overview -> alerts -> pivot to evidence.
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "../App";
import { renderWithApi } from "./renderWithApi";

describe("triage flow", () => {
  it("selects a case, reads overview, then pivots from an alert to its evidence", async () => {
    renderWithApi(<App />);

    // 1. select the dirty case
    await userEvent.click(await screen.findByText("mac-victim"));

    // 2. overview is the default tab
    expect(await screen.findByText(/22 documents total/)).toBeInTheDocument();

    // 3. open the Alerts tab
    await userEvent.click(screen.getByRole("button", { name: "alerts" }));
    const alerts = await screen.findByLabelText("alerts");

    // 4. pivot from the persistence alert
    await userEvent.click(
      within(alerts).getByText("macOS persistence program in suspicious path"),
    );

    // 5. we land on the Artifacts tab, persistence dataset, evidence row highlighted
    const table = await screen.findByLabelText("artifacts macos.persistence");
    const highlighted = table.querySelector("tr.highlight");
    expect(highlighted).not.toBeNull();
    expect(highlighted!).toHaveTextContent("com.system.helper");
  });

  it("switches dataset chips within the Artifacts tab", async () => {
    renderWithApi(<App />);
    await userEvent.click(await screen.findByText("mac-victim"));
    await userEvent.click(screen.getByRole("button", { name: "artifacts" }));

    // default dataset is the first one; switch to processes
    await userEvent.click(
      screen.getByRole("button", { name: "process" }),
    );
    expect(
      await screen.findByLabelText("artifacts macos.process"),
    ).toBeInTheDocument();
  });
});
