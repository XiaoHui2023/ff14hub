from __future__ import annotations

import subprocess
import sys


def ensure_playwright_chromium() -> None:
    """若已装 Playwright 但缺 Chromium 内核，则自动执行 install chromium。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except Exception:
        print("Installing Playwright Chromium (~180MB)...", flush=True)
        subprocess.check_call(
            [sys.executable, "-m", "playwright", "install", "chromium"],
        )


def main() -> None:
    ensure_playwright_chromium()


if __name__ == "__main__":
    main()
