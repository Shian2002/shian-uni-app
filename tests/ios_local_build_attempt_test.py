from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ios_local_build_attempt_is_safe_and_wired():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    docs = read_text("docs/release/mobile-build-evidence.md")
    source = read_text("scripts/ios_local_build_attempt.mjs")

    assert '"mobile:ios-local-build-attempt": "node scripts/ios_local_build_attempt.mjs"' in package_json
    assert "mobile:ios-local-build-attempt" in release_check
    assert "mobile:ios-local-build-attempt" in finalize
    assert "mobile:ios-local-build-attempt" in docs

    for expected in [
        "IOS_LOCAL_BUILD_EXECUTE",
        "artifacts', 'ios-local-build-attempts'",
        "xcode-select",
        "xcodebuild",
        "simctl",
        "security",
        "find-identity",
        "Provisioning Profiles",
        "/Volumes/XcodeAPFS",
        "xcodeApfsReady",
        "internal-disk-cache-low",
        "完整 Xcode 16.2",
        "attempt.json",
        "commands.redacted.log",
        "redact",
        "<redacted-email>",
        "xcode-full-missing",
        "simctl-missing",
        "ios-provisioning-profile-missing",
        "ios-code-signing-identity-missing",
        "disk-space-low",
        "p12、mobileprovision、签名口令只在本机钥匙串或安全交接中处理，不进入 GitHub",
    ]:
        assert expected in source


def test_ios_local_build_attempt_does_not_store_secret_materials():
    source = read_text("scripts/ios_local_build_attempt.mjs")

    for forbidden in [
        ".p12')",
        "readFileSync(profile",
        "certpassword: '",
        "APPLE_PASSWORD",
        "FASTLANE_SESSION",
        "notarytool store-credentials",
    ]:
        assert forbidden not in source
