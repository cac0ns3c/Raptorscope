// SPDX-License-Identifier: GPL-3.0-or-later
// Records a guided-tour video of the SPA; CI converts the webm to an optimized
// GIF (docs/img/walkthrough.gif) for the README. Only uses selectors already
// verified by smoke.spec.ts / screenshots.spec.ts in CI. Deliberate pauses make
// the resulting GIF watchable.
import { test } from "@playwright/test";

test.use({
  viewport: { width: 1280, height: 800 },
  video: { mode: "on", size: { width: 1280, height: 800 } },
});

const pause = (p: import("@playwright/test").Page, ms: number) =>
  p.waitForTimeout(ms);

test("guided walkthrough", async ({ page }) => {
  // 1. Case picker — the landing screen.
  await page.goto("/");
  await page.getByText("mac-victim").first().waitFor();
  await pause(page, 1200);

  // 2. Fleet-wide IOC hunt — correlate an indicator across hosts.
  await page.getByLabel("hunt indicator across hosts").click();
  await page.getByLabel("hunt indicator across hosts").fill("45.9.148.99");
  await pause(page, 600);
  await page.getByRole("button", { name: "Hunt" }).click();
  await page.getByLabel("hunt result").waitFor();
  await pause(page, 1900);

  // 3. Open the case → overview dashboard.
  await page.getByText("mac-victim").first().click();
  await page.getByLabel("overview").waitFor();
  await pause(page, 1900);

  // 4. Fired detections.
  await page.getByRole("button", { name: "alerts", exact: true }).click();
  await page.getByLabel("alerts").waitFor();
  await pause(page, 1900);

  // 5. Timeline.
  await page.getByRole("button", { name: "timeline", exact: true }).click();
  await page.getByLabel("timeline").waitFor();
  await pause(page, 1700);

  // 6. Search across the case.
  await page.getByRole("button", { name: "search", exact: true }).click();
  await page.getByLabel("query", { exact: true }).fill("helper");
  await pause(page, 500);
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await page.getByLabel("search results").waitFor();
  await pause(page, 1900);

  // 7. Close the loop back on the overview (best-effort — never fails the run).
  try {
    await page.getByRole("button", { name: "overview", exact: true }).click();
    await page.getByLabel("overview").waitFor({ timeout: 3000 });
    await pause(page, 1100);
  } catch {
    /* optional closing shot */
  }
});
