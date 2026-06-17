from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_desktop_release_inbox_sync_is_wired_into_release_flow():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")

    assert '"desktop:release-inbox-sync": "node scripts/desktop_release_inbox_sync.mjs"' in package_json
    assert "desktop:release-inbox-sync" in release_check
    assert "desktop:release-inbox-sync" in docs


def test_desktop_release_inbox_sync_records_current_desktop_evidence():
    source = read_text("scripts/desktop_release_inbox_sync.mjs")

    for expected in [
        "artifacts/release-inbox",
        "desktop/release/时安解忧屋-1.0.0-arm64.dmg",
        "desktop/release/时安解忧屋 Setup 1.0.0.exe",
        "latestReportDirWith",
        "artifacts/desktop-smoke",
        "artifacts/desktop-online-login-smoke",
        "layout?.agent?.homeAiMain",
        "layout?.agent?.topnav",
        "artifactSha256",
        "not-in-metadata-use-secure-channel",
        "pending-real-user-evidence",
        "writeWindowsUninstallEvidence",
        "uninstall-evidence.md",
        "正式发布前仍需要在真实 Windows 设备补充安装、启动、登录、积分、时安 agent、窗口缩放和卸载截图",
    ]:
        assert expected in source
    assert "if (uninstallEvidence.length) metadata.uninstallEvidence = uninstallEvidence" in source
    assert "metadata.uninstallEvidence = [" not in source
