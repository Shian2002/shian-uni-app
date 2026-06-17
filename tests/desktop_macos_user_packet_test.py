from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_macos_user_packet_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")
    desktop_docs = read_text("docs/release/desktop-build-evidence.md")

    assert '"desktop:macos-user-packet": "node scripts/desktop_macos_user_packet.mjs"' in package_json
    assert "npm run desktop:macos-user-packet" in ci
    assert "desktop:macos-user-packet" in release_check
    assert "desktop:macos-user-packet" in finalize
    assert "desktopMacosUserPacket" in finalize
    assert "desktopMacosUserPacket" in readiness
    assert "desktopMacosUserPacket" in release_package
    assert "latestDesktopMacosUserPacket" in summary
    assert "desktop:macos-user-packet" in docs
    assert "desktop:macos-user-packet" in desktop_docs


def test_macos_user_packet_documents_current_personal_test_boundary():
    source = read_text("scripts/desktop_macos_user_packet.mjs")
    dmg_source = read_text("scripts/desktop_macos_dmg_from_app.mjs")
    package_json = read_text("package.json")

    assert '"desktop:make-macos-dmg": "node scripts/desktop_macos_dmg_from_app.mjs"' in package_json

    for expected in [
        "artifacts', 'desktop-macos-user-packets'",
        "shian-${version}-macos-arm64-user-test.dmg",
        "desktop/release/时安解忧屋-1.0.0-arm64.dmg",
        "latestPassingDesktopSmoke",
        "smokeLayout",
        "桌面 smoke 缺少浅色顶栏和底部对话框布局指标",
        "缺少时安 agent 应用态截图",
        "latestH5Build",
        "latestDesktopMain",
        "macOS 产物早于最新 H5 或桌面壳源码",
        "sourceMtime",
        "if (!source) return null",
        "statSync(sourcePath).isFile()",
        "desktop-macos-install",
        "未签名、未公证",
        "右键应用选择“打开”",
        "系统设置 -> 隐私与安全性",
        "src/static/images/logo.png",
        "登录复用线上 H5/后端现有登录逻辑",
        "preview.html",
        "open-macos-dmg.command",
        "LATEST.md",
        "latest-manifest.json",
        "open-latest-preview.command",
        "latestPacketDir",
        "chmodSync",
        "时安解忧屋 macOS 试用预览",
        "最新 macOS 个人试用包",
        "先看页面预览",
        "checksums.sha256",
        "manifest.json",
        "refreshMacAppZip",
        "ditto",
        "--keepParent",
    ]:
        assert expected in source

    for expected in [
        "hdiutil",
        "create",
        "-format",
        "UDZO",
        "desktop/release/mac-arm64/时安解忧屋.app",
        "desktop/release/时安解忧屋-${version}-arm64.dmg",
        "app.asar",
        "icon.icns",
        "Apple Developer ID 签名",
        "notarization",
        "desktop-dmg-backups",
        "无法创建 Applications 快捷方式",
    ]:
        assert expected in dmg_source

    assert "artifacts/desktop-smoke/2026-06-15T02-33-13-363Z" not in source
    assert "桌面截图不足" not in source
