// SPDX-License-Identifier: GPL-3.0-or-later
import { expect, test } from "@playwright/test";

// Selectors mirror the aria-labels/roles used across the components, so these
// stay in lockstep with the unit tests:
//   CasePicker  — text "mac-victim"; hunt input aria "hunt indicator across hosts",
//                 button "Hunt", result region aria "hunt result".
//   App tabs    — <nav aria-label="views"> of buttons whose accessible name is the
//                 tab id ("overview" | "artifacts" | "timeline" | "alerts" | "search").
//   Overview    — section aria "overview" with "<N> documents total".
//   Alerts      — section aria "alerts".  Timeline — list aria "timeline".
//   Search      — input aria "query", button "Search", table aria "search results",
//                 rows data-testid "search-row".
//
// The backend runs the bundled sample offline (no ES, no auth, AI disabled), so
// AI tabs/features are intentionally absent and not asserted here.

test.describe("Raptorscope SPA smoke", () => {
  test("case picker lists the sample host and hunts an IOC across the fleet", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByText("mac-victim")).toBeVisible();

    // Fleet hunt for a C2 IP present in the sample.
    await page
      .getByLabel("hunt indicator across hosts")
      .fill("45.9.148.99");
    await page.getByRole("button", { name: "Hunt" }).click();

    const hunt = page.getByLabel("hunt result");
    await expect(hunt).toBeVisible();
    await expect(hunt).toContainText("mac-victim");
  });

  test("selecting a case navigates the core tabs", async ({ page }) => {
    await page.goto("/");
    await page.getByText("mac-victim").click();

    // Overview is the default tab.
    const overview = page.getByLabel("overview");
    await expect(overview).toBeVisible();
    await expect(overview).toContainText("documents total");

    // Alerts — high-severity detections.
    await page.getByRole("button", { name: "alerts", exact: true }).click();
    await expect(page.getByLabel("alerts")).toBeVisible();

    // Timeline.
    await page.getByRole("button", { name: "timeline", exact: true }).click();
    await expect(page.getByLabel("timeline")).toBeVisible();
  });

  test("search returns results for a known indicator", async ({ page }) => {
    await page.goto("/");
    await page.getByText("mac-victim").click();

    await page.getByRole("button", { name: "search", exact: true }).click();
    await page.getByLabel("query", { exact: true }).fill("helper");
    // exact/case-sensitive so this matches the form's "Search" button, not the
    // lowercase "search" tab button.
    await page.getByRole("button", { name: "Search", exact: true }).click();

    await expect(page.getByLabel("search results")).toBeVisible();
    await expect(page.getByTestId("search-row").first()).toBeVisible();
  });
});
