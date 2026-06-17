from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_desktop_release_status_config_tracks_unsigned_evidence_gap():
    config = read_text("configs/release/desktop-release-status.json")

    for expected in [
        "macos",
        "windows",
        "codeSigningStatus",
        "notarizationStatus",
        "installEvidencePaths",
        "unsigned",
        "not-started",
        "shian-v1.0.0-macos-arm64.dmg",
        "shian-v1.0.0-windows-x64-nsis.exe",
        "latest:desktop-smoke",
    ]:
        assert expected in config


def test_desktop_release_status_checker_blocks_secrets_and_requires_install_evidence():
    source = read_text("scripts/desktop_release_status_check.mjs")

    for expected in [
        "DESKTOP_RELEASE_STATUS_STRICT",
        "configs/release/desktop-release-status.json",
        "desktop-release-status",
        "codeSigningStatus",
        "notarizationStatus",
        "installEvidencePaths",
        "readySigningStatuses",
        "readyNotarizationStatuses",
        "latestPassingDesktopSmoke",
        "latestUserPacketEvidence",
        "configuredSmokeReportPath",
        "autoInstallEvidencePaths",
        "userTestPassed",
        "userTestReady",
        "macos 桌面 smoke 缺少浅色顶栏和底部对话框布局指标",
        "private[-_]?key",
        "证书",
        "非 strict 模式只生成报告",
        "不代表正式公开发布完成",
    ]:
        assert expected in source


def test_desktop_release_status_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")

    assert '"desktop:release-status": "node scripts/desktop_release_status_check.mjs"' in package_json
    assert "npm run desktop:release-status" in ci
    assert "desktop:release-status" in release_check
    assert "desktop:release-status" in finalize
    assert "desktopReleaseStatus" in readiness
    assert "desktopReleaseStatus" in release_package
    assert "latestDesktopReleaseStatus" in summary
    assert "desktop:release-status" in docs


def test_macos_dmg_verify_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    verifier = read_text("scripts/desktop_macos_install_verify.mjs")
    desktop_docs = read_text("docs/release/desktop-build-evidence.md")
    shell_docs = read_text("desktop/README.md")

    assert '"desktop:verify-macos": "node scripts/desktop_macos_install_verify.mjs"' in package_json
    assert "npm run desktop:verify-macos" in ci
    assert "desktop:verify-macos" in release_check
    assert "desktop:verify-macos" in finalize
    assert "desktopMacosInstall" in readiness
    assert "desktopMacosInstall" in release_package
    assert "desktopReleaseStatusHardBlock" in release_package
    assert "userTestPassed" in release_package
    assert "latestDesktopMacosInstall" in summary
    assert "desktop:verify-macos" in desktop_docs
    assert "desktop:verify-macos" in shell_docs
    assert "app.asar" in verifier
    assert "不是空壳 App" in verifier
    assert "lstatSync" in readiness
    assert "isSymbolicLink" in readiness


def test_macos_app_asar_refresh_is_wired_before_desktop_bundle():
    package_json = read_text("package.json")
    finalize = read_text("scripts/release_finalize.mjs")
    refresh_script = read_text("scripts/desktop_macos_refresh_app_asar.mjs")

    assert '"desktop:refresh-macos-app-asar": "node scripts/desktop_macos_refresh_app_asar.mjs"' in package_json
    assert "desktop:refresh-macos-app-asar" in finalize
    assert finalize.index("desktop:refresh-macos-app-asar") < finalize.index("desktop:make-macos-dmg")
    assert finalize.index("desktop:make-macos-dmg") < finalize.index("desktop:bundle")
    assert "desktop:build:win:x64:safe:skip-h5" in finalize
    assert finalize.index("desktop:build:win:x64:safe:skip-h5") < finalize.index("desktop:bundle")
    assert "desktop/node_modules/@electron/asar/bin/asar.js" in refresh_script
    assert "dist/build/h5" in refresh_script
    assert "desktop-asar-backups" in refresh_script
    assert "ElectronAsarIntegrity" in refresh_script
    assert "PlistBuddy" in refresh_script
    assert ":ElectronAsarIntegrity:Resources/app.asar:hash" in refresh_script
    assert "刷新后还需要执行 `npm run desktop:make-macos-dmg`" in refresh_script


def test_release_finalize_rebuilds_app_before_mobile_api_evidence():
    finalize = read_text("scripts/release_finalize.mjs")

    assert "['build:app', ['run', 'build:app']]" in finalize
    assert finalize.index("release:channel-builds") < finalize.index("build:app")
    assert finalize.index("build:app") < finalize.index("mobile:api-evidence")


def test_release_finalize_extends_windows_rebuild_timeout():
    finalize = read_text("scripts/release_finalize.mjs")

    assert "const windowsRebuildEnv" in finalize
    assert "DESKTOP_WINDOWS_REBUILD_TIMEOUT_MS" in finalize
    assert "'900000'" in finalize
    assert "DESKTOP_WINDOWS_REBUILD_SKIP_H5" in finalize
    assert "env: { ...process.env, ...extraEnv }" in finalize
    assert "desktop:build:win:x64:safe:skip-h5', ['run', 'desktop:build:win:x64:safe', '--', '--skip-h5'], windowsRebuildEnv" in finalize
    assert "desktop:build:win:x64:safe:skip-h5:final', ['run', 'desktop:build:win:x64:safe', '--', '--skip-h5'], windowsRebuildEnv" in finalize
