from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_mobile_native_runtime_prefixes_relative_api_to_online_backend():
    source = read_text("src/main.js")

    for expected in [
        "const productionApiOrigin = 'https://shianjieyouwu.com'",
        "function normalizeApiUrl",
        "function isNativeAppRuntime",
        "shouldUseProductionApiOrigin",
        "if (isNativeAppRuntime()) return true",
        "uniPlatform.indexOf('app') === 0",
        "args.url = normalizeApiUrl(args.url)",
        "args.withCredentials = true",
        "fetch(normalizeApiUrl('/api/csrf-token'), { credentials: 'include' })",
        "options.credentials = options.credentials || 'include'",
    ]:
        assert expected in source


def test_stream_and_legacy_requests_share_mobile_api_origin():
    source = read_text("src/main.js")

    for expected in [
        "window.EventSource",
        "function ShianEventSource",
        "new OriginalEventSource(normalizedUrl, config)",
        "window.XMLHttpRequest",
        "function ShianXMLHttpRequest",
        "args[1] = normalizeApiUrl(url)",
    ]:
        assert expected in source


def test_h5_and_desktop_keep_relative_api_proxy_boundary():
    source = read_text("src/main.js")
    desktop = read_text("desktop/main.js")

    assert "return shouldUseProductionApiOrigin() ? productionApiOrigin + url : url" in source
    assert "pathname === '/api' || pathname.startsWith('/api/')" in desktop
    assert "https://shianjieyouwu.com" in desktop
