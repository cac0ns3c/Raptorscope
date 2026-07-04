// SPDX-License-Identifier: GPL-3.0-or-later
import { render } from "@testing-library/react";
import type { ReactElement } from "react";

import type { ApiClient } from "../api/client";
import { ApiProvider } from "../context/ApiContext";
import { makeFakeClient } from "./fakeClient";

export function renderWithApi(
  ui: ReactElement,
  client: ApiClient = makeFakeClient(),
) {
  return render(<ApiProvider client={client}>{ui}</ApiProvider>);
}
