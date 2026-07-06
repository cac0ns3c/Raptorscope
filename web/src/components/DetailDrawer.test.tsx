// SPDX-License-Identifier: GPL-3.0-or-later
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { DetailDrawer } from "./DetailDrawer";
import type { Doc } from "../api/types";

const doc = {
  _id: "d1",
  event: { dataset: "macos.tcc" },
  file: { path: "/Users/Shared/.helper/agent" },
} as unknown as Doc;

describe("DetailDrawer", () => {
  it("copies a field value to the clipboard via its copy button", async () => {
    const writeText = vi.fn();
    Object.assign(navigator, { clipboard: { writeText } });
    render(<DetailDrawer doc={doc} onClose={() => {}} />);
    await userEvent.click(
      screen.getByRole("button", { name: /copy file\.path/i }),
    );
    expect(writeText).toHaveBeenCalledWith("/Users/Shared/.helper/agent");
  });

  it("closes on Escape (modal keyboard support)", async () => {
    Object.assign(navigator, { clipboard: { writeText: vi.fn() } });
    const onClose = vi.fn();
    render(<DetailDrawer doc={doc} onClose={onClose} />);
    await userEvent.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();
  });
});
