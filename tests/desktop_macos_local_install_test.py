from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_macos_local_install_is_wired_into_release_flow():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    try_now = read_text("scripts/current_try_now_packet.mjs")
    release_package = read_text("scripts/release_package.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    docs = read_text("docs/release/README.md")

    assert '"desktop:install-macos-local": "node scripts/desktop_macos_local_install.mjs"' in package_json
    assert '"desktop:macos-lifecycle": "node scripts/desktop_macos_lifecycle_check.mjs"' in package_json
    assert "desktop:install-macos-local" in release_check
    assert "desktop:macos-lifecycle" in release_check
    assert "desktopMacosLocalInstall" in release_package
    assert "desktopMacosLifecycle" in release_package
    assert "desktopMacosLocalInstall" in readiness
    assert "desktopMacosLifecycle" in readiness
    assert "desktopMacosLocalInstall" in try_now
    assert "desktopMacosLifecycle" in try_now
    assert "artifacts/desktop-macos-local-install" in try_now
    assert "artifacts/desktop-macos-lifecycle" in try_now
    assert "desktop:install-macos-local" in docs
    assert "desktop:macos-lifecycle" in docs


def test_macos_local_install_preserves_native_app_requirements():
    source = read_text("scripts/desktop_macos_local_install.mjs")

    for expected in [
        "/Applications/时安解忧屋.app",
        "desktop/release/mac-arm64/时安解忧屋.app",
        "ditto",
        "CFBundleName",
        "CFBundleExecutable",
        "CFBundleIconFile",
        "icon.icns",
        "codesign",
        "未签名测试包",
        "Launchpad",
        "Finder",
    ]:
        assert expected in source


def test_macos_lifecycle_check_verifies_single_instance_runtime():
    source = read_text("scripts/desktop_macos_lifecycle_check.mjs")

    for expected in [
        "/Applications/时安解忧屋.app",
        "open",
        "pgrep",
        "mainProcessRows",
        "重复打开后主进程数量应为 1",
        "单实例锁",
        "保留 App 打开",
    ]:
        assert expected in source
