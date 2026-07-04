// SPDX-License-Identifier: GPL-3.0-or-later
import { defineConfig, devices } from "@playwright/test";

const CI = !!process.env.CI;
const API_PORT = 8000;
const WEB_PORT = 4173;

// End-to-end: drives the built SPA (vite preview, which proxies /api) against a
// real backend running the bundled sample offline (no ES, no auth, AI disabled).
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: CI,
  retries: CI ? 2 : 0,
  reporter: CI ? "list" : "html",
  use: {
    baseURL: `http://127.0.0.1:${WEB_PORT}`,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      // Requires the raptorscope package on PATH (pip install -e .).
      command: `raptorscope serve --collection samples/mac-victim --port ${API_PORT}`,
      cwd: "..",
      url: `http://127.0.0.1:${API_PORT}/health`,
      reuseExistingServer: !CI,
      timeout: 60_000,
    },
    {
      // `npm run preview` serves web/dist and proxies /api to the API (vite.config).
      command: `npm run preview -- --host 127.0.0.1 --port ${WEB_PORT}`,
      url: `http://127.0.0.1:${WEB_PORT}`,
      reuseExistingServer: !CI,
      timeout: 60_000,
    },
  ],
});
