from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_current_try_now_packet_collects_latest_cross_platform_artifacts():
    package_json = read_text("package.json")
    source = read_text("scripts/current_try_now_packet.mjs")
    release_check = read_text("scripts/release_check.mjs")
    release_package = read_text("scripts/release_package.mjs")

    assert '"release:try-now": "node scripts/current_try_now_packet.mjs"' in package_json
    assert "release:try-now" in release_check
    assert "tryNowPacket" in release_package
    assert "Try Now Packet" in release_package
    for expected in [
        "artifacts', 'try-now'",
        "desktop-macos-user-packets",
        "desktop-macos-updated-app",
        "desktop-windows-user-packets",
        "mobile-app-resource-packets",
        "mobile-api-evidence",
        "desktopDownloadsDir",
        "releasePackageReport",
        "latestReportDir('artifacts/release-packages', 'upload-manifest.json')",
        "Release package upload-manifest 缺失或未写完",
        "macDownloadsAppZip",
        "artifactByExt(downloadsManifest, '.app.zip')",
        "desktop-online-login-smoke",
        "h5-legal-deploy-status",
        "release-user-actions",
        "h5LegalDeployStatus",
        "userActions",
        "H5 法律页线上状态",
        "人工事项交接包",
        "CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh",
        "existsSync(join(root, item.reportPath))",
        "manifest.tryNow.macosUpdatedAppZip || manifest.evidence.macosUpdatedApp",
        "desktopLayout",
        "topnav",
        "homeAiMain",
        "macosDmg",
        "macosUpdatedAppZip",
        "macOS 当前已更新 App",
        "macOS 当前已更新 App 包",
        "windowsInstaller",
        "androidDebugApk",
        "androidDebugAab",
        "Android 调试安装包",
        "Android AAB",
        "release-inbox",
        ".apk",
        ".aab",
        "userMustDoLast",
        "Apple Developer ID 签名和 notarization",
        "Android APK/AAB、iOS TestFlight/IPA、鸿蒙 HAP/AppGallery 包",
        "明确批准后才能执行生产 H5 法律页部署",
        "H5 法律页部署后回填法律 URL 严格验证",
        "当前可试用包",
        "latest-manifest.json",
        "LATEST.md",
    ]:
        assert expected in source
