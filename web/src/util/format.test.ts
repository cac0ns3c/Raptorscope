// SPDX-License-Identifier: GPL-3.0-or-later
import { describe, expect, it } from "vitest";

import { fmtNum, fmtTime } from "./format";

describe("fmtNum", () => {
  it("adds thousands separators", () => {
    expect(fmtNum(28431)).toBe((28431).toLocaleString());
  });
});

describe("fmtTime", () => {
  it("drops sub-second precision and the T/Z", () => {
    expect(fmtTime("2026-07-07T07:46:10.037835264Z")).toBe("2026-07-07 07:46:10");
    expect(fmtTime("2026-03-05T16:17:06Z")).toBe("2026-03-05 16:17:06");
  });
  it("is monotonic (preserves chronological ordering as a string sort)", () => {
    const a = fmtTime("2026-07-07T07:46:09.900Z");
    const b = fmtTime("2026-07-07T07:46:10.100Z");
    expect(a < b).toBe(true);
  });
  it("returns empty for null/empty and passes through non-timestamps", () => {
    expect(fmtTime(null)).toBe("");
    expect(fmtTime("")).toBe("");
    expect(fmtTime("not-a-time")).toBe("not-a-time");
  });
});
