// SPDX-License-Identifier: GPL-3.0-or-later
import { kibanaDiscoverUrl } from "./kibana";

describe("kibanaDiscoverUrl", () => {
  it("builds a Discover deep link scoped to the case host", () => {
    const url = kibanaDiscoverUrl("http://localhost:5601", "mac-victim");
    expect(url).toContain("http://localhost:5601/app/discover");
    expect(url).toContain("language:kuery");
    expect(url).toContain(encodeURIComponent('host.name:"mac-victim"'));
  });
});
