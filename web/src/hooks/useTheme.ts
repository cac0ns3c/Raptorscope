// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState } from "react";

type Theme = "dark" | "light";

function initial(): Theme {
  try {
    return window.localStorage.getItem("rs_theme") === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(initial);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      window.localStorage.setItem("rs_theme", theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  return {
    theme,
    toggle: () => setTheme((t) => (t === "dark" ? "light" : "dark")),
  };
}
