// SPDX-License-Identifier: GPL-3.0-or-later
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Copilot } from "./Copilot";
import { renderWithApi } from "../test/renderWithApi";

describe("Copilot", () => {
  it("asks a question and renders the verdict + citations", async () => {
    renderWithApi(<Copilot caseName="mac-victim" />);
    await userEvent.type(
      screen.getByLabelText("copilot question"),
      "Is this host compromised?",
    );
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));
    // citations from the agentic tool loop prove the verdict rendered
    expect(await screen.findByText("get_overview")).toBeInTheDocument();
    expect(screen.getByText("search_case")).toBeInTheDocument();
    expect(document.querySelector(".copilot-result")?.textContent).toMatch(/Verdict/i);
  });
});
