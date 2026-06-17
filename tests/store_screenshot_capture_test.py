from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_store_screenshot_capture_can_use_system_browser_without_playwright_download():
    source = read_text("scripts/store_screenshot_capture.mjs")

    for expected in [
        "STORE_SCREENSHOT_BROWSER_CHANNEL",
        "STORE_SCREENSHOT_BROWSER_EXECUTABLE",
        "/Applications/Google Chrome.app",
        "/Applications/Microsoft Edge.app",
        "channel: systemBrowserChannel",
        "executablePath: systemBrowserExecutable",
    ]:
        assert expected in source


def test_store_screenshot_capture_uses_h5_storage_and_tab_router_for_logged_in_screens():
    source = read_text("scripts/store_screenshot_capture.mjs")

    for expected in [
        "const me = await api(page, '/api/me')",
        "localStorage.setItem('xc_token', 'session')",
        "localStorage.setItem('xc_user', JSON.stringify(userPayload))",
        "if (window.uni && typeof window.uni.setStorageSync === 'function')",
        "await waitForSession(page)",
        "window.__xcRenderTabPath(path, query)",
        "window.dispatchEvent(new CustomEvent('xc-auth-changed'",
    ]:
        assert expected in source
