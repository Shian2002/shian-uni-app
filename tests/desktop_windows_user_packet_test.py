from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_windows_user_packet_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")
    desktop_docs = read_text("docs/release/desktop-build-evidence.md")

    assert '"desktop:windows-user-packet": "node scripts/desktop_windows_user_packet.mjs"' in package_json
    assert "npm run desktop:windows-user-packet" in ci
    assert "desktop:windows-user-packet" in release_check
    assert "desktop:windows-user-packet" in finalize
    assert "desktopWindowsUserPacket" in finalize
    assert "desktopWindowsUserPacket" in readiness
    assert "desktopWindowsUserPacket" in release_package
    assert "latestDesktopWindowsUserPacket" in summary
    assert "desktop:windows-user-packet" in docs
    assert "desktop:windows-user-packet" in desktop_docs


def test_windows_user_packet_documents_current_test_boundary():
    source = read_text("scripts/desktop_windows_user_packet.mjs")

    for expected in [
        "artifacts', 'desktop-windows-user-packets'",
        "shian-${version}-windows-x64-user-test-nsis.exe",
        "desktop/release/时安解忧屋 Setup 1.0.0.exe",
        "latestPassingDesktopSmoke",
        "smokeLayout",
        "桌面 smoke 缺少浅色顶栏和底部对话框布局指标",
        "未签名 NSIS 测试安装器",
        "Windows 10/11 真机",
        "开始菜单",
        "卸载流程截图",
        "src/static/images/logo.png",
        "登录复用线上 H5/后端现有登录逻辑",
        "preview.html",
        "LATEST.md",
        "latest-manifest.json",
        "checksums.sha256",
        "manifest.json",
        "latestH5Build",
        "latestDesktopMain",
        "sourceMtime",
        "if (!source) return null",
        "statSync(sourcePath).isFile()",
        "Windows 安装器早于最新 H5 或桌面壳源码",
        "缺少时安 agent 应用态截图",
        "release inbox 备份由 `npm run desktop:release-inbox-sync` 统一生成",
        "npm run desktop:build:win:x64",
    ]:
        assert expected in source

    assert "windows-x64-release-inbox-copy.exe" not in source
    assert "artifacts/desktop-smoke/2026-06-15T02-33-13-363Z" not in source
    assert "桌面截图不足" not in source
