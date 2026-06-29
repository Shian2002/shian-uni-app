from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_JS = ROOT / "src" / "main.js"


def test_uni_frontend_installs_csrf_interceptors():
    source = MAIN_JS.read_text(encoding="utf-8")

    assert "installCsrfProtection()" in source
    assert "uni.addInterceptor('request'" in source
    assert "uni.addInterceptor('uploadFile'" in source
    assert "X-CSRFToken" in source


def test_frontend_fetch_is_patched_for_csrf_writes():
    source = MAIN_JS.read_text(encoding="utf-8")

    assert "window.fetch = function csrfFetch" in source
    assert "csrfWriteMethods" in source
    assert "/api/csrf-token" in source


def test_uni_request_wrapper_returns_promise_for_callback_free_calls():
    source = MAIN_JS.read_text(encoding="utf-8")

    assert "const shouldReturnPromise =" in source
    assert "typeof userSuccess !== 'function'" in source
    assert "typeof userFail !== 'function'" in source
    assert "typeof userComplete !== 'function'" in source
    assert "const compatPromise = shouldReturnPromise ? new Promise" in source
    assert "if (resolveCompatRequest) resolveCompatRequest(res)" in source
    assert "if (rejectCompatRequest) rejectCompatRequest(err)" in source
    assert "if (compatPromise) return compatPromise" in source
