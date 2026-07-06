// SPDX-License-Identifier: GPL-3.0-or-later
import { useCallback, useEffect, useState } from "react";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  /** Re-run the loader (e.g. from a "Retry" button after an error). */
  reload: () => void;
}

/** Run an async loader on mount / when `deps` change, tracking load state.
 *  Stale results are dropped when deps change or the component unmounts.
 *  `reload()` re-runs the loader with the current deps. */
export function useAsync<T>(
  loader: () => Promise<T>,
  deps: unknown[],
): AsyncState<T> {
  const [state, setState] = useState<
    Omit<AsyncState<T>, "reload">
  >({
    data: null,
    loading: true,
    error: null,
  });
  // Bumping this nonce re-runs the effect without changing the caller's deps.
  const [nonce, setNonce] = useState(0);
  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    let live = true;
    setState({ data: null, loading: true, error: null });
    loader()
      .then((data) => live && setState({ data, loading: false, error: null }))
      .catch(
        (e: unknown) =>
          live &&
          setState({ data: null, loading: false, error: String(e) }),
      );
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  return { ...state, reload };
}
