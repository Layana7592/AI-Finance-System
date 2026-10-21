"""Chromium end-to-end run against Django/PostgreSQL + Vite, with real API calls.

This run uses a smaller synthetic dataset for speed. The 50,000-row research
benchmark is verified separately by report-evidence.yml.
"""
import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(os.getenv("DEMO_EVIDENCE_DIR", "evidence/browser"))
OUT.mkdir(parents=True, exist_ok=True)
URL = os.getenv("DEMO_FRONTEND_URL", "http://127.0.0.1:5173")
USERNAME = "demo_presenter"
PASSWORD = os.environ["DEMO_PRESENTER_PASSWORD"]


def screenshot(page, name):
    page.screenshot(path=str(OUT / name), full_page=True, animations="disabled")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=1)
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
    page.get_by_role("heading", name="AI Finance System").wait_for(timeout=30_000)
    screenshot(page, "01-login.png")
    page.get_by_label("Username").fill(USERNAME)
    page.get_by_label("Password").fill(PASSWORD)
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.get_by_role("heading", name="One transaction. Eight verified steps.").wait_for(timeout=30_000)
    screenshot(page, "02-authenticated.png")

    start = time.monotonic()
    page.get_by_role("button", name="Start timed demonstration").click()
    page.get_by_text("Demo complete", exact=False).wait_for(timeout=900_000)
    elapsed = round(time.monotonic() - start, 2)
    screenshot(page, "03-complete-steps.png")
    page.get_by_text("Verified transaction evidence", exact=True).wait_for()
    page.get_by_text("Behavioural risk score:", exact=False).wait_for()
    page.locator(".demo-evidence").get_by_text("Alert #", exact=False).wait_for()
    page.get_by_text("Audit event #", exact=False).wait_for()
    page.get_by_text("Saved forecast records: 12", exact=False).wait_for()
    page.locator("details").get_by_text("Show management report").click()
    screenshot(page, "04-report-evidence.png")

    page.get_by_role("button", name="Analytics dashboard").click()
    page.locator(".dashboard .hero h1, .error-screen").first.wait_for(timeout=90_000)
    if page.locator(".error-screen").count() > 0:
        raise AssertionError("Analytics dashboard failed: " + page.locator(".error-screen").inner_text())
    page.get_by_role("heading", name="Banking analytics dashboard").wait_for(timeout=10_000)
    screenshot(page, "05-real-dashboard.png")
    page.get_by_role("button", name="Sign out").click()
    page.get_by_role("heading", name="AI Finance System").wait_for(timeout=30_000)
    screenshot(page, "06-logout.png")
    (OUT / "demo-result.json").write_text(json.dumps({
        "success": True,
        "elapsed_seconds": elapsed,
        "verified_steps": 8,
        "dashboard_rendered": True,
        "report_fallback_or_gemini_verified": True,
        "browser": "Chromium",
        "data_type": "synthetic",
        "dataset_note": "Smaller browser-smoke dataset; separate 50k scientific benchmark",
    }, indent=2))
    print("E2E browser demonstration passed, eight backend steps, elapsed", elapsed, "seconds.")
    browser.close()
