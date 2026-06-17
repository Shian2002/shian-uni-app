from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_mobile_api_evidence_script_checks_built_app_runtime():
    source = read_text("scripts/mobile_api_evidence_check.mjs")

    for expected in [
        "artifacts', 'mobile-api-evidence'",
        "dist', 'build', 'app'",
        "https://shianjieyouwu.com",
        "withCredentials",
        "EventSource",
        "XMLHttpRequest",
        "/api/csrf-token",
        "sourceFreshnessInputs",
        "newestSource",
        "dist/build/app 早于移动端关键源码",
        "__uniappview.html",
        "app-service.js",
        "npm run build:app",
        "latest-manifest.json",
        "LATEST.md",
    ]:
        assert expected in source


def test_mobile_api_evidence_is_wired_into_scripts_and_preflight():
    package_json = read_text("package.json")
    preflight = read_text("scripts/mobile_release_preflight.mjs")
    release_check = read_text("scripts/release_check.mjs")

    assert '"mobile:api-evidence": "node scripts/mobile_api_evidence_check.mjs"' in package_json
    assert "mobile:api-evidence" in release_check
    for expected in [
        "dist/build/app runtime",
        "https://shianjieyouwu.com",
        "EventSource",
        "XMLHttpRequest",
        "withCredentials",
    ]:
        assert expected in preflight


def test_mobile_api_evidence_is_wired_into_release_orchestration():
    release_package = read_text("scripts/release_package.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    finalize = read_text("scripts/release_finalize.mjs")

    for expected in [
        "mobileApiEvidence",
        "artifacts/mobile-api-evidence",
        "移动端 API 后端请求证据",
    ]:
        assert expected in release_package

    for expected in [
        "mobileApiEvidence",
        "mobile:api-evidence",
        "platform.app-resources",
        "缺少通过的移动端 API 后端请求证据",
    ]:
        assert expected in readiness

    for expected in [
        "latestMobileApiEvidence",
        "mobile:api-evidence",
        "移动端 API 后端请求证据",
    ]:
        assert expected in summary

    for expected in [
        "mobile:api-evidence",
        "mobileApiEvidence",
        "Mobile API Evidence",
    ]:
        assert expected in finalize
