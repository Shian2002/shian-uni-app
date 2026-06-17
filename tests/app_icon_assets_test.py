from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_app_icon_release_surface_is_wired():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    package = read_text("scripts/release_package.mjs")
    mobile = read_text("scripts/mobile_build_request_packet.mjs")
    handoff = read_text("scripts/platform_build_handoff.mjs")
    docs = read_text("docs/release/mobile-build-evidence.md")

    assert '"release:app-icons": "node scripts/app_icon_asset_check.mjs"' in package_json
    assert "npm run release:app-icons" in ci
    assert "release:app-icons" in release_check
    assert "release:app-icons" in finalize
    assert "App 图标资产" in summary
    assert "assets.app-icons" in readiness
    assert "appIconsHardBlock" in package
    assert "src/static/app-icons/app-icon-1024.png" in mobile
    assert "src/static/app-icons/app-icon-1024.png" in handoff
    assert "androidDebugAab" in mobile
    assert "Android App Bundle 结构预检 AAB" in mobile
    assert "androidDebugAab" in handoff
    assert "当前 macOS DMG" in handoff
    assert "当前 Windows NSIS" in handoff
    assert "src/static/app-icons/app-icon-1024.png" in docs


def test_required_icon_files_exist():
    expected = [
        "src/static/images/logo.png",
        "src/static/app-icons/app-icon-1024.png",
        "src/static/app-icons/app-icon-512.png",
        "src/static/app-icons/app-icon-192.png",
        "src/static/app-icons/app-icon-180.png",
        "src/static/app-icons/app-icon-120.png",
        "desktop/assets/icon.icns",
        "desktop/assets/icon.ico",
        "desktop/assets/icon.png",
    ]

    for path in expected:
        full_path = ROOT / path
        assert full_path.exists(), path
        assert full_path.stat().st_size > 0, path
