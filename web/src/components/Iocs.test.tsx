// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Iocs } from "./Iocs";
import { renderWithApi } from "../test/renderWithApi";

describe("Iocs", () => {
  it("extracts IOCs and hunts one across the fleet", async () => {
    renderWithApi(<Iocs caseName="mac-victim" />);
    await userEvent.click(screen.getByRole("button", { name: /Extract IOCs/ }));
    const list = await screen.findByLabelText("iocs");
    expect(within(list).getByText("45.9.148.99")).toBeInTheDocument();
    // hunt the IOC across the fleet inline
    await userEvent.click(within(list).getAllByRole("button", { name: "Hunt fleet" })[0]);
    expect(await within(list).findByText(/on \d+ host/)).toBeInTheDocument();
  });
});
