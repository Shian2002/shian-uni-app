from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_mobile_build_env_checks_real_tool_readiness_not_just_paths():
    source = read_text("scripts/mobile_build_env_check.mjs")

    for expected in [
        "diskInfo",
        "availableGiB",
        "sw_vers",
        "xcodeSelect",
        "xcodebuildVersion",
        "xcrun', ['simctl'",
        "Xcodes.app",
        "xcodesCli",
        "mas",
        "recommendedXcode",
        "Xcode 16.2",
        "https://developer.apple.com/support/xcode/",
        "externalStorage",
        "/Volumes/时安500G",
        "File System Personality:   ExFAT",
        "完整 Xcode",
        "Command Line Tools",
        "HBuilderX CLI",
        "hbuilderxUser",
        "runRedacted",
        "<redacted-email>",
        "defaultAndroidSdkRoot",
        "detectedAndroidHome",
        "detectedJavaHome",
        "platform-tools",
        "cmdline-tools",
        "JAVA_HOME",
        "sdkPackages",
        "warnings",
        "当前已安装 Android 基础工具链仍可构建 debug APK",
        "hbuilderxPlugins",
        "appSafePack",
        "launcherTools",
        "amazonCorretto",
        "建议至少 45 GiB",
    ]:
        assert expected in source

    assert "env.disk.availableGiB >= 12" not in source
    assert "建议至少 12 GiB" not in source


def test_mobile_build_env_docs_track_hbuilderx_and_space_boundary():
    docs = read_text("docs/release/mobile-build-evidence.md")

    for expected in [
        "mobile:hbuilderx-resources",
        "HBuilderX CLI",
        "App Resource",
        "此功能需要先登录",
        "完整 Xcode",
        "剩余空间",
        "Xcode 16.2",
        "/Volumes/时安500G",
    ]:
        assert expected in docs
