from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_hbuilderx_mobile_resources_script_is_wired():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    docs = read_text("docs/release/mobile-build-evidence.md")

    assert '"mobile:hbuilderx-resources": "node scripts/hbuilderx_mobile_resources.mjs"' in package_json
    assert "mobile:hbuilderx-resources" in release_check
    assert "mobile:hbuilderx-resources" in finalize
    assert "hbuilderxMobileResources" in readiness
    assert "mobile:hbuilderx-resources" in docs


def test_hbuilderx_mobile_resources_records_real_cli_boundaries():
    source = read_text("scripts/hbuilderx_mobile_resources.mjs")

    for expected in [
        "HBUILDERX_CLI",
        "/Applications/HBuilderX.app/Contents/MacOS/cli",
        "publish', 'app-android'",
        "publish', 'app-ios'",
        "publish', 'app-harmony'",
        "--type', 'appResource'",
        "需要先登录",
        "user-action",
        "environment-action",
        "Incompatible processor",
        "Qt build requires",
        "hostMachine",
        "cliFileInfo",
        "en_US.UTF-8",
        "App Resource 不是最终安装包",
        "release-inbox/v1.0.0/<platform>",
        "latest-manifest.json",
        "report.json",
        "latest-commands.sh",
        "cleanupResidualAppBuildProcesses",
        "uni.js build -p app",
        "residualBuildCleanup",
        "SIGTERM",
        "redact",
        "<redacted-email>",
        "keystore",
        "mobileprovision",
    ]:
        assert expected in source

    for forbidden in [
        "certpassword: '",
        "storepassword: '",
        "privateKey: '",
    ]:
        assert forbidden not in source
