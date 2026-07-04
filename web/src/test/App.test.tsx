// SPDX-License-Identifier: GPL-3.0-or-later
import { screen } from "@testing-library/react";

import { App } from "../App";
import { renderWithApi } from "./renderWithApi";

describe("App", () => {
  it("renders the Raptorscope heading and case picker", async () => {
    renderWithApi(<App />);
    expect(
      screen.getByRole("heading", { name: "Raptorscope" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("Select a case")).toBeInTheDocument();
  });
});
