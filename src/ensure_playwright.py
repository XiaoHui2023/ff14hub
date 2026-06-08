from __future__ import annotations

import sys


def ensure_playwright_chromium() -> int:
    """检查 Playwright Chromium 是否可用。

    Returns:
        可用为 0；缺 Chromium 时为 1（已打印安装命令）。
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return 0
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except Exception:
        print("错误：Playwright Chromium 未安装。请执行：", flush=True)
        print(f"  {sys.executable} -m playwright install chromium", flush=True)
        return 1
    return 0


def main() -> None:
    raise SystemExit(ensure_playwright_chromium())


if __name__ == "__main__":
    main()
