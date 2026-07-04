// SPDX-License-Identifier: GPL-3.0-or-later
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { useTheme } from "./useTheme";

function Probe() {
  const { theme, toggle } = useTheme();
  return (
    <button onClick={toggle}>
      {theme}
    </button>
  );
}

describe("useTheme", () => {
  it("toggles the document theme between dark and light", async () => {
    render(<Probe />);
    const btn = screen.getByRole("button");
    expect(btn).toHaveTextContent("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    await userEvent.click(btn);
    expect(btn).toHaveTextContent("light");
    expect(document.documentElement.dataset.theme).toBe("light");
  });
});
