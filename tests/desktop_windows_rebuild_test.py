from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_windows_safe_rebuild_script_is_wired():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    desktop_docs = read_text("docs/release/desktop-build-evidence.md")

    assert '"desktop:build:win:x64:safe": "node scripts/desktop_windows_rebuild.mjs"' in package_json
    assert "desktop:build:win:x64:safe" in release_check
    assert "desktop:build:win:x64:safe:verify" in finalize
    assert "https://npmmirror.com/mirrors/electron/" in finalize
    assert "desktopWindowsRebuild" in finalize
    assert "desktop:build:win:x64:safe" in desktop_docs
    assert "--verify-current" in desktop_docs


def test_windows_safe_rebuild_records_timeout_env_and_freshness():
    source = read_text("scripts/desktop_windows_rebuild.mjs")

    for expected in [
        "artifacts', 'desktop-windows-rebuild'",
        "DESKTOP_WINDOWS_REBUILD_TIMEOUT_MS",
        "DESKTOP_WINDOWS_REBUILD_VERIFY_CURRENT",
        "CSC_IDENTITY_AUTO_DISCOVERY",
        "ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES",
        "ELECTRON_MIRROR",
        "USE_HARD_LINKS",
        "dist:win:x64",
        "build:h5",
        "Windows 安装器早于最新 H5 构建产物",
        "Windows unpacked exe 早于最新 H5 构建产物",
        "report.json",
        "build.log",
        "README.md",
        "释放至少 8-12GiB 空间",
        "Windows 10/11 机器或 CI runner",
    ]:
        assert expected in source
