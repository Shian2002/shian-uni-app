from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_mobile_build_request_packet_covers_android_ios_harmony():
    source = read_text("scripts/mobile_build_request_packet.mjs")

    for expected in [
        "MOBILE_BUILD_REQUEST_VERSION",
        "artifacts",
        "mobile-build-requests",
        "Android APK/AAB",
        "androidDebugAab",
        "Android App Bundle 结构预检 AAB",
        "iOS TestFlight",
        "鸿蒙/AppGallery",
        "artifacts/release-inbox",
        "build-metadata.json",
        "release:artifact-metadata",
        "线上登录 smoke",
        "时安 agent 入口验收",
        "HBuilderX App Resource 检查",
        "mobile:hbuilderx-resources",
        "mobileToolchainPlan",
        "mobile:toolchain-plan",
        "移动端工具链准备计划",
        "/Volumes/XcodeAPFS",
        "Apple 下载认证",
        "Xcode 16.2",
        "FASTLANE_SESSION",
        "release:low-impact-status",
        "低影响状态",
        "knownLocalBlockers",
        "App 打包插件已恢复",
        "HBuilderX 云打包尝试",
        "HBuilderX 鸿蒙本地打包尝试",
        "iOS 本地构建尝试",
        "hbuilderxHarmonyPackAttempt",
        "iosLocalBuildAttempt",
        "artifacts/ios-local-build-attempts",
        "artifacts/hbuilderx-harmony-pack-attempts",
        "hbuilderxCloudPackAttempt",
        "hbuilderxCloudPackAttempts",
        "hbuilderxCloudPackAttempt: evidence.hbuilderxCloudPackAttempts?.[request.id]",
        "latestReportDirForPlatform",
        ".endsWith(`-${platform}`)",
        "mobile:hbuilderx-cloud-pack",
        "mobile:hbuilderx-harmony-pack",
        "mobile:ios-local-build-attempt",
        "HBuilderX CLI pack 云打包入口已确认",
        "Apple 签名身份",
        "provisioning profile",
        "pack app-harmony",
        "DCloud 服务端检查",
        "手机号重新验证",
        "云端 SDK 版本差异",
        "HBuilderX 插件安装尝试",
        "hbuilderxPluginInstall",
        "launcher",
        "app-safe-pack",
        "amazon-corretto",
        "内置盘低空间",
        "完整 Xcode",
        "DevEco/hdc/hvigor",
        "keystore",
        "mobileprovision",
    ]:
        assert expected in source


def test_mobile_build_request_packet_is_wired_into_release_flow():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    ci = read_text(".github/workflows/ci.yml")
    docs = read_text("docs/release/README.md")

    assert '"mobile:build-requests": "node scripts/mobile_build_request_packet.mjs"' in package_json
    assert '"mobile:hbuilderx-cloud-pack": "node scripts/hbuilderx_cloud_pack_attempt.mjs"' in package_json
    assert '"mobile:hbuilderx-harmony-pack": "node scripts/hbuilderx_harmony_pack_attempt.mjs"' in package_json
    assert '"mobile:ios-local-build-attempt": "node scripts/ios_local_build_attempt.mjs"' in package_json
    assert "mobile:build-requests" in release_check
    assert "mobile:hbuilderx-cloud-pack" in release_check
    assert "mobile:hbuilderx-harmony-pack" in release_check
    assert "mobile:ios-local-build-attempt" in release_check
    assert "mobile:build-requests" in finalize
    assert "mobile:hbuilderx-harmony-pack" in finalize
    assert "mobile:ios-local-build-attempt" in finalize
    assert "mobileBuildRequests" in readiness
    assert "mobileBuildRequests" in release_package
    assert "latestMobileBuildRequests" in summary
    assert "npm run mobile:build-requests" in ci
    assert "mobile:build-requests" in docs
    assert "mobile:hbuilderx-cloud-pack" in docs
    assert "mobile:hbuilderx-harmony-pack" in docs
    assert "mobile:ios-local-build-attempt" in docs
