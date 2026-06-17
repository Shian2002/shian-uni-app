from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_mobile_toolchain_plan_is_safe_and_wired():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    docs = read_text("docs/release/README.md")
    source = read_text("scripts/mobile_toolchain_prepare_plan.mjs")

    assert '"mobile:toolchain-plan": "node scripts/mobile_toolchain_prepare_plan.mjs"' in package_json
    assert "mobile:toolchain-plan" in release_check
    assert "mobile:toolchain-plan" in finalize
    assert "mobile:toolchain-plan" in docs

    for expected in [
        "artifacts', 'mobile-toolchain-plan'",
        "/Volumes/时安500G",
        "/Volumes/XcodeAPFS",
        "File System Personality:   ExFAT",
        "File System Personality:   APFS",
        "Xcode 16.2",
        "xcodes install 16.2 --directory /Volumes/XcodeAPFS",
        "apple-download-auth",
        "DevEco Studio/hdc/hvigor",
        "https://developer.huawei.com/consumer/cn/deveco-studio/",
        "https://developer.huawei.com/consumer/cn/download/",
        "HBuilderX -> 偏好设置 -> 运行配置 -> 鸿蒙开发者工具路径",
        "hbuilderxHarmonyPlugin",
        "generatedHarmonyResource",
        ".app-harmony",
        "硬盘 100GB",
        "避免误保存账号或 secret",
        "FASTLANE_SESSION",
        "不要把 Apple ID 密码",
        "不自动登录 Apple、DCloud、华为账号",
        "不保存 p12、mobileprovision、keystore",
        "artifacts/current-downloads",
        "artifacts/release-inbox",
    ]:
        assert expected in source


def test_mobile_toolchain_plan_does_not_perform_install_or_signing():
    source = read_text("scripts/mobile_toolchain_prepare_plan.mjs")

    for forbidden in [
        "execFileSync('xcodes', ['install'",
        "execFileSync('diskutil', ['eraseDisk'",
        "security import",
        "FASTLANE_SESSION=",
        "APPLE_PASSWORD",
        "HUAWEI_PASSWORD",
    ]:
        assert forbidden not in source
