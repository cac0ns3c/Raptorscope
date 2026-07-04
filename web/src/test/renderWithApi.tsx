// SPDX-License-Identifier: GPL-3.0-or-later
import { render } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";

import type { ApiClient } from "../api/client";
import { ApiProvider } from "../context/ApiContext";
import { makeFakeClient } from "./fakeClient";

export function renderWithApi(
  ui: ReactElement,
  client: ApiClient = makeFakeClient(),
) {
  // Use the `wrapper` option so `rerender` keeps the provider in place.
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <ApiProvider client={client}>{children}</ApiProvider>
  );
  return render(ui, { wrapper: Wrapper });
}
