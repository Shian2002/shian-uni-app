from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_android_device_smoke_script_installs_launches_screenshots_and_records_evidence():
    package_json = read_text("package.json")
    source = read_text("scripts/android_device_smoke.mjs")

    assert '"android:device-smoke": "node scripts/android_device_smoke.mjs"' in package_json

    for expected in [
        "adb(['devices'])",
        "adb([...serialArgs, 'install', '-r', apkPath]",
        "adb([...serialArgs, 'shell', 'am', 'start', '-n', activityName])",
        "screencap",
        "adb([...serialArgs, 'pull', remoteScreenshot, localScreenshot])",
        "deviceTestEvidence",
        "metadataUpdated",
        "no-device",
        "--strict",
        "com.shian.xuanctai/.MainActivity",
        "artifacts', 'android-device-smoke'",
        "android-device-agent.png",
    ]:
        assert expected in source


def test_android_device_smoke_docs_explain_no_fake_evidence_boundary():
    source = read_text("scripts/android_device_smoke.mjs")

    assert "默认无设备不失败" in source
    assert "登录、积分、时安 agent、账号注销仍需人工" in source
    assert "未检测到 adb device 状态的安卓设备" in source
