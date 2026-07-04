// SPDX-License-Identifier: GPL-3.0-or-later
import { render, screen } from "@testing-library/react";

import { App } from "../App";

describe("App", () => {
  it("renders the Raptorscope heading", () => {
    render(<App />);
    expect(
      screen.getByRole("heading", { name: "Raptorscope" }),
    ).toBeInTheDocument();
  });
});
