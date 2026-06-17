from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_external_handoff_is_wired_and_documented():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")
    quota = read_text("scripts/release_quota_status.mjs")

    assert '"release:external-handoff": "node scripts/release_external_handoff.mjs"' in package_json
    assert "release:external-handoff" in release_check
    assert "release:external-handoff" in docs
    assert "release:external-handoff" in quota


def test_external_handoff_creates_return_directories_without_building():
    source = read_text("scripts/release_external_handoff.mjs")

    for expected in [
        "外部硬阻塞回传清单",
        "当前可先试装",
        "Android 调试 APK",
        "Android 调试 APK/AAB 只用于先行真机回归",
        "只生成外部回传清单和目录",
        "releaseInboxBase",
        "${releaseInboxBase}/android/",
        "${releaseInboxBase}/ios/",
        "${releaseInboxBase}/harmony/",
        "artifacts/store-evidence-inbox/",
        "artifacts/real-user-results/",
        "不要放入证书、私钥、keystore",
        "Android APK/AAB 真包",
        "iOS TestFlight/IPA 构建记录",
        "鸿蒙 HAP/AppGallery 包",
        "build-metadata.template.json",
        "evidence-index.template.json",
        "tester-result.template.json",
        "secure-channel-not-in-git",
    ]:
        assert expected in source

    for forbidden in [
        "child_process",
        "execFileSync",
        "spawn",
        "desktop:build:mac",
        "desktop:build:win",
    ]:
        assert forbidden not in source
