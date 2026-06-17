from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_mobile_app_resource_packet_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")
    mobile_docs = read_text("docs/release/mobile-build-evidence.md")

    assert '"mobile:app-resource-packet": "node scripts/mobile_app_resource_packet.mjs"' in package_json
    assert "npm run mobile:app-resource-packet" in ci
    assert "mobile:app-resource-packet" in release_check
    assert "mobile:app-resource-packet" in finalize
    assert "mobileAppResourcePacket" in finalize
    assert "mobileAppResourcePacket" in readiness
    assert "mobileAppResourcePacket" in release_package
    assert "latestMobileAppResourcePacket" in summary
    assert "mobile:app-resource-packet" in docs
    assert "mobile:app-resource-packet" in mobile_docs


def test_mobile_app_resource_packet_documents_build_input_boundary():
    source = read_text("scripts/mobile_app_resource_packet.mjs")

    for expected in [
        "artifacts', 'mobile-app-resource-packets'",
        "dist/build/app",
        "__uniappview.html",
        "app-service.js",
        "app-resource",
        "src/static/app-icons",
        "app-icon-1024.png",
        "source-manifest.json",
        "android-channels.json",
        "ios-appstore.json",
        "harmony-appgallery.json",
        "Android APK/AAB",
        "iOS TestFlight/IPA",
        "鸿蒙 HAP/AppGallery",
        "keystore",
        "mobileprovision",
        "latest-manifest.json",
        "checksums.sha256",
        "manifest.json",
        "hbuilderxResources",
        "hbuilderx-mobile-resources",
        "HBuilderX App Resource 检查",
        "mobileApiEvidence",
        "mobile-api-evidence",
        "移动端 API 后端请求证据",
        "移动端 API 后端请求证据早于最新 App 构建",
        "dist/build/app 早于移动端关键源码",
        "sourceFreshnessInputs",
        "latestMobileApiEvidenceMtime",
        "newestSource",
        "sourceMtime",
        "npm run build:app",
        "npm run mobile:api-evidence",
    ]:
        assert expected in source
