import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const root = process.env.DEMO_URL || "http://127.0.0.1:5173";
const password = process.env.DEMO_PRESENTER_PASSWORD;
if (!password) throw new Error("DEMO_PRESENTER_PASSWORD is required");
const evidenceDir = path.resolve(process.env.DEMO_EVIDENCE_DIR || "evidence/browser");
fs.mkdirSync(evidenceDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const log = { started: new Date().toISOString(), steps: [], url: root, pass: false };
try {
  await page.goto(root, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.getByRole("heading", { name: "AI Finance System" }).waitFor({ timeout: 30000 });
  await page.screenshot({ path: path.join(evidenceDir, "01-login.png"), fullPage: true });
  await page.getByLabel("Username").fill("demo_presenter");
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("heading", { name: "One transaction. Eight verified steps." }).waitFor({ timeout: 30000 });
  await page.screenshot({ path: path.join(evidenceDir, "02-presenter-ready.png"), fullPage: true });
  await page.getByRole("button", { name: "Start timed demonstration" }).click();
  // Both model evaluations run against the *real* 50k synthetic records.
  await page.getByRole("status").filter({ hasText: "Demo complete — 8/8" }).waitFor({ timeout: 1200000 });
  const stepRows = await page.locator(".demo-step").all();
  for (const row of stepRows) {
    const title = await row.locator("h2").innerText();
    const detail = await row.locator("p").innerText();
    const status = await row.locator("strong").innerText();
    if (!status.toLowerCase().startsWith("pass")) throw new Error("Failed step " + title + ": " + status);
    log.steps.push({ title, detail, status });
  }
  if (stepRows.length !== 8) throw new Error("Expected exactly eight verified steps");
  const runtime = await page.locator(".demo-timer strong").innerText();
  log.elapsed_time = runtime;
  await page.screenshot({ path: path.join(evidenceDir, "03-live-end-to-end-success.png"), fullPage: true });
  await page.getByRole("button", { name: "Analytics dashboard" }).click();
  await page.locator(".dashboard .hero h1, .error-screen").first().waitFor({ timeout: 90000 });
  if (await page.locator(".error-screen").count()) {
    throw new Error("Dashboard screen failed: " + (await page.locator(".error-screen").innerText()));
  }
  await page.getByRole("heading", { name: "Banking analytics dashboard" }).waitFor({ timeout: 10000 });
  await page.screenshot({ path: path.join(evidenceDir, "04-analytics-dashboard.png"), fullPage: true });
  await page.getByRole("button", { name: "Guided demo" }).click();
  await page.getByText("Verified transaction evidence").waitFor({ timeout: 30000 });
  await page.getByText("Show management report").click();
  await page.screenshot({ path: path.join(evidenceDir, "05-management-report.png"), fullPage: true });
  // Complete an independent human-facing transaction review in the UI.
  await page.getByRole("button", { name: "Operations", exact: true }).click();
  await page.getByRole("heading", { name: "Transactions and alert investigations" }).waitFor({ timeout: 60000 });
  const presenterAccountOption = page.locator("#ops-account option").filter({ hasText: "DEMO-ACCOUNT-2026" });
  await page.locator("#ops-account").waitFor({ timeout: 20000 });
  await presenterAccountOption.first().waitFor({ state: "attached", timeout: 20000 });
  const accountValue = await presenterAccountOption.getAttribute("value");
  if (!accountValue) throw new Error("Presenter account missing from operational selector");
  await page.locator("#ops-account").selectOption(accountValue);
  await page.getByRole("button", { name: "Create and verify transaction" }).click();
  await page.getByRole("status").filter({ hasText: "Created synthetic transaction #" }).waitFor({ timeout: 60000 });
  const originalAlert = page.locator(".ops-alert").filter({ hasText: "Open for investigation" }).first();
  await originalAlert.waitFor({ timeout: 20000 });
  await page.getByLabel("Investigation conclusion").fill(
    "Reviewed controlled synthetic alert: account and transaction verified; educational demonstration only."
  );
  await originalAlert.getByRole("button", { name: "Resolve with reason" }).click();
  await page.getByRole("status").filter({ hasText: "resolved and audit-logged" }).waitFor({ timeout: 20000 });
  if (!(await page.locator(".ops-audit-list").innerText()).includes("Reason: Reviewed controlled synthetic alert")) {
    throw new Error("Operational UI did not show the persisted alert resolution audit record.");
  }
  log.operational_review_verified = true;
  await page.screenshot({ path: path.join(evidenceDir, "06-operations-reviewed.png"), fullPage: true });

  // The separately posted synthetic ledger must reconcile without changing
  // existing ML benchmark transaction rows or legacy account balances.
  await page.getByRole("button", { name: "Synthetic ledger", exact: true }).click();
  await page.getByRole("heading", { name: "Double-entry ledger and reconciliation" }).waitFor({ timeout: 20000 });
  await page.getByLabel("Source account ID").fill(accountValue);
  await page.getByRole("button", { name: "Post and verify balanced entry" }).click();
  await page.getByRole("status").filter({ hasText: "two balanced lines" }).waitFor({ timeout: 20000 });
  await page.getByRole("status").filter({ hasText: "All postings and wallet balances reconcile." }).waitFor({ timeout: 20000 });
  log.synthetic_ledger_balanced = true;
  await page.screenshot({ path: path.join(evidenceDir, "07-balanced-synthetic-ledger.png"), fullPage: true });

  await page.getByRole("button", { name: "Analytics dashboard" }).click();
  await page.getByRole("heading", { name: "Exploratory Seasonal-Naive uncertainty" }).waitFor({ timeout: 90000 });
  // The heading renders before the async forecast uncertainty request completes.
  // Wait for actual table data rather than immediately reading an empty DOM.
  await page.getByText("Insufficient data").first().waitFor({ state: "visible", timeout: 60000 });
  if ((await page.getByText("Insufficient data").count()) === 0) {
    throw new Error("Uncertainty display did not disclose unavailable longer horizons.");
  }
  log.uncertainty_limitations_visible = true;
  await page.screenshot({ path: path.join(evidenceDir, "08-forecast-uncertainty.png"), fullPage: true });

  const presenterToken = await page.evaluate(() => sessionStorage.getItem("finance_api_token"));
  if (!presenterToken) throw new Error("Presenter token missing before logout");
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.getByRole("button", { name: "Sign in", exact: true }).waitFor({ timeout: 30000 });
  const denied = await page.request.get(root + "/api/me/", {
    headers: { Authorization: "Token " + presenterToken },
  });
  if (denied.status() !== 401) {
    throw new Error("SECURITY REGRESSION: signed-out server token still authorizes /api/me/ (HTTP " + denied.status() + ")");
  }
  log.server_token_revoked = true;
  await page.screenshot({ path: path.join(evidenceDir, "09-signed-out.png"), fullPage: true });
  log.pass = true;
  console.log("BROWSER DEMO PASS: 8/8 steps; " + runtime);
} catch (error) {
  log.error = String(error);
  await page.screenshot({ path: path.join(evidenceDir, "failure.png"), fullPage: true }).catch(() => {});
  throw error;
} finally {
  log.finished = new Date().toISOString();
  fs.writeFileSync(path.join(evidenceDir, "demo-log.json"), JSON.stringify(log, null, 2));
  await browser.close();
}
