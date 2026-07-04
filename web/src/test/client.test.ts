// SPDX-License-Identifier: GPL-3.0-or-later
import { afterEach, vi } from "vitest";

import { createHttpClient } from "../api/client";
import { makeFakeClient, DIRTY, CLEAN } from "./fakeClient";

afterEach(() => {
  vi.restoreAllMocks();
});

function mockFetch(body: unknown) {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => body,
  }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("createHttpClient", () => {
  it("builds the artifacts URL with query params", async () => {
    const f = mockFetch({ dataset: "macos.tcc", total: 0, items: [] });
    const client = createHttpClient("/api/");
    await client.getArtifacts("mac-victim", "macos.tcc", { limit: 5, offset: 10 });
    expect(f).toHaveBeenCalledWith(
      "/api/cases/mac-victim/artifacts/macos.tcc?limit=5&offset=10",
    );
  });

  it("throws on non-ok responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) })),
    );
    await expect(createHttpClient("/api").listCases()).rejects.toThrow(
      /request failed: 500/,
    );
  });
});

describe("fakeClient", () => {
  it("lists both seeded cases", async () => {
    const names = (await makeFakeClient().listCases()).map((c) => c.name);
    expect(names).toEqual([DIRTY, CLEAN]);
  });

  it("paginates artifacts", async () => {
    const client = makeFakeClient();
    const page = await client.getArtifacts(DIRTY, "macos.persistence", {
      limit: 5,
      offset: 5,
    });
    expect(page.total).toBe(12);
    expect(page.items).toHaveLength(5);
  });

  it("returns no alerts for the clean case", async () => {
    expect(await makeFakeClient().getAlerts(CLEAN)).toEqual([]);
  });
});
