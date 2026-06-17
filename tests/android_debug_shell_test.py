from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_android_debug_shell_matches_release_identity_and_online_entry():
    manifest = read_text("android-shell/app/src/main/AndroidManifest.xml")
    build_gradle = read_text("android-shell/app/build.gradle")
    main_activity = read_text("android-shell/app/src/main/java/com/shian/xuanctai/MainActivity.java")
    strings = read_text("android-shell/app/src/main/res/values/strings.xml")

    assert "applicationId 'com.shian.xuanctai'" in build_gradle
    assert "versionCode 100" in build_gradle
    assert "versionName '1.0.0'" in build_gradle
    assert "android.permission.INTERNET" in manifest
    assert "android:usesCleartextTraffic=\"false\"" in manifest
    assert "https://shianjieyouwu.com/#/?app=1" in main_activity
    assert "setJavaScriptEnabled(true)" in main_activity
    assert "setDomStorageEnabled(true)" in main_activity
    assert "MIXED_CONTENT_NEVER_ALLOW" in main_activity
    assert "时安解忧屋" in strings


def test_android_debug_shell_build_script_writes_release_inbox_metadata():
    package_json = read_text("package.json")
    source = read_text("scripts/android_debug_shell_build.mjs")

    assert '"android:shell:debug-apk": "node scripts/android_debug_shell_build.mjs"' in package_json
    for expected in [
        "artifacts', 'release-inbox', version, 'android'",
        "shian-${version}-android-debug-shell.apk",
        "shian-${version}-android-debug-shell.aab",
        "build-metadata.json",
        "debug-shell",
        "debug-signing-only",
        "internal-test-only",
        "secondaryArtifacts",
        "buildEvidence",
        "automatedEvidence",
        "mobileRuntimeEvidence",
        "sharedBackendContractEvidence",
        "deviceTestEvidence: []",
        "artifacts/mobile-api-evidence",
        "artifacts/desktop-online-login-smoke",
        "comprehensive-guide",
        "schemaReady === true",
        "if (report.passed)",
        "const buildSucceeded = steps.every((step) => step.ok)",
        "已跳过复制旧 APK/AAB 到 release inbox",
        "不替代 deviceTestEvidence 真机验收",
        "不替代 Android 真机安装、登录和功能回归",
        "https://shianjieyouwu.com/#/?app=1",
        "src/static/app-icons",
        "gradle-assemble-debug",
        "gradle-bundle-debug",
        ":app:assembleDebug",
        ":app:bundleDebug",
        "HBuilderX/DCloud 发行权限恢复前",
        "不是应用商店正式 APK/AAB",
        "Android App Bundle",
    ]:
        assert expected in source
