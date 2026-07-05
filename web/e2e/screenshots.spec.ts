// SPDX-License-Identifier: GPL-3.0-or-later
// Captures showcase screenshots of the core SPA views during the e2e run. Output
// lands in web/screenshots/ and is uploaded as a CI artifact. The offline backend
// has no AI key, so AI views (triage/copilot) are captured from the live app, not
// here. Selectors mirror smoke.spec.ts (already CI-verified).
import { test } from "@playwright/test";

const DIR = "screenshots";
test.use({ viewport: { width: 1440, height: 900 } });

async function selectCase(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.getByText("mac-victim").first().waitFor();
  await page.getByText("mac-victim").first().click();
}

test.describe("showcase screenshots", () => {
  test("case picker + fleet hunt", async ({ page }) => {
    await page.goto("/");
    await page.getByText("mac-victim").first().waitFor();
    await page.screenshot({ path: `${DIR}/01-case-picker.png`, fullPage: true });

    await page.getByLabel("hunt indicator across hosts").fill("45.9.148.99");
    await page.getByRole("button", { name: "Hunt" }).click();
    await page.getByLabel("hunt result").waitFor();
    await page.screenshot({ path: `${DIR}/02-fleet-hunt.png`, fullPage: true });
  });

  test("overview", async ({ page }) => {
    await selectCase(page);
    await page.getByLabel("overview").waitFor();
    await page.screenshot({ path: `${DIR}/03-overview.png`, fullPage: true });
  });

  test("alerts", async ({ page }) => {
    await selectCase(page);
    await page.getByRole("button", { name: "alerts", exact: true }).click();
    await page.getByLabel("alerts").waitFor();
    await page.screenshot({ path: `${DIR}/04-alerts.png`, fullPage: true });
  });

  test("timeline", async ({ page }) => {
    await selectCase(page);
    await page.getByRole("button", { name: "timeline", exact: true }).click();
    await page.getByLabel("timeline").waitFor();
    await page.screenshot({ path: `${DIR}/05-timeline.png`, fullPage: true });
  });

  test("search", async ({ page }) => {
    await selectCase(page);
    await page.getByRole("button", { name: "search", exact: true }).click();
    await page.getByLabel("query", { exact: true }).fill("helper");
    await page.getByRole("button", { name: "Search", exact: true }).click();
    await page.getByLabel("search results").waitFor();
    await page.screenshot({ path: `${DIR}/06-search.png`, fullPage: true });
  });
});
