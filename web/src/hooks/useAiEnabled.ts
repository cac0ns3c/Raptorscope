// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState } from "react";

import { useApi } from "../context/ApiContext";

/** True when the backend has AI features configured (ANTHROPIC_API_KEY set). */
export function useAiEnabled(): boolean {
  const api = useApi();
  const [enabled, setEnabled] = useState(false);
  useEffect(() => {
    let live = true;
    api
      .aiStatus()
      .then((s) => live && setEnabled(!!s.enabled))
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [api]);
  return enabled;
}
