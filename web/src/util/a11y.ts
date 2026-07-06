// SPDX-License-Identifier: GPL-3.0-or-later
import type { KeyboardEvent } from "react";

/**
 * Props that make a non-button element (e.g. a table row) behave like a button:
 * click, Enter, and Space all activate it, and it joins the tab order. Space is
 * preventDefault'd so it doesn't scroll the page.
 */
export function rowActivation(onActivate: () => void) {
  return {
    role: "button" as const,
    tabIndex: 0,
    onClick: onActivate,
    onKeyDown: (e: KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onActivate();
      }
    },
  };
}
