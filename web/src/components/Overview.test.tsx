// SPDX-License-Identifier: GPL-3.0-or-later
import { screen, within } from "@testing-library/react";

import { Overview } from "./Overview";
import { renderWithApi } from "../test/renderWithApi";

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

  it("shows unsigned counters and the document total", async () => {
    renderWithApi(<Overview caseName="mac-victim" />);
    expect(await screen.findByText(/22 documents total/)).toBeInTheDocument();
    expect(screen.getByText("processes")).toBeInTheDocument();
    expect(screen.getByText("applications")).toBeInTheDocument();
  });
});
