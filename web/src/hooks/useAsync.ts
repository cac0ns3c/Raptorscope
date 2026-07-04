// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState } from "react";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/** Run an async loader on mount / when `deps` change, tracking load state.
 *  Stale results are dropped when deps change or the component unmounts. */
export function useAsync<T>(
  loader: () => Promise<T>,
  deps: unknown[],
): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
  });

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
  }, deps);

  return state;
}
