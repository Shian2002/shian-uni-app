from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_desktop_download_bundle_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    docs = read_text("docs/release/README.md")

    assert '"desktop:bundle": "node scripts/desktop_download_bundle.mjs"' in package_json
    assert "npm run desktop:bundle" in ci
    assert "desktop:bundle" in release_check
    assert "desktop:bundle" in finalize
    assert "desktopDownloads" in finalize
    assert "desktop:bundle" in docs


def test_desktop_download_bundle_generates_safe_public_assets():
    source = read_text("scripts/desktop_download_bundle.mjs")

    for expected in [
        "artifacts', 'desktop-downloads'",
        "shian-${version}-macos-arm64.dmg",
        "shian-${version}-macos-arm64.app.zip",
        "shian-${version}-windows-x64-nsis.exe",
        "checksums.sha256",
        "manifest.json",
        "src/static/images/logo.png",
        "登录仍复用线上 H5/后端现有登录逻辑",
        "未签名、未公证测试包",
        "Windows 代码签名",
        "assertSafeFileName",
        "refreshMacAppZip",
        "ditto",
        "--keepParent",
        "latestH5Build",
        "latestDesktopMain",
        "sourceMtime",
        "早于最新 H5 或桌面壳源码",
        "npm run desktop:build:win:x64",
        "npm run desktop:build:mac:arm64",
        "阻塞问题",
    ]:
        assert expected in source
