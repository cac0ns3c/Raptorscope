// SPDX-License-Identifier: GPL-3.0-or-later
import type { Doc } from "../api/types";
import { buildCsv, flatten } from "./tabular";

const doc: Doc = {
  _id: "1",
  event: { dataset: "macos.process" },
  process: { name: "helper", executable: "/private/tmp/x" },
};

describe("flatten", () => {
  it("produces sorted dotted paths and drops _id", () => {
    const flat = flatten(doc);
    const keys = flat.map(([k]) => k);
    expect(keys).toContain("event.dataset");
    expect(keys).toContain("process.executable");
    expect(keys).not.toContain("_id");
    expect(keys).toEqual([...keys].sort());
  });
});

describe("buildCsv", () => {
  it("writes a header row and escapes commas/quotes", () => {
    const csv = buildCsv(
      [{ _id: "1", file: { path: "a,b" } } as Doc],
      [{ header: "Path", path: "file.path" }],
    );
    const [head, row] = csv.split("\n");
    expect(head).toBe("Path");
    expect(row).toBe('"a,b"');
  });
});
