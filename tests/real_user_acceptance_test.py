from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_real_user_packet_generates_two_tester_result_templates():
    source = read_text("scripts/real_user_packet.mjs")

    for expected in [
        "REAL_USER_MIN_TESTERS",
        "minimumTestersPerPlatform",
        "results/tester-1.json",
        "results/tester-2.json",
        "至少",
        "result.example.json",
        "screenshots/",
        "当前可发测产物",
        "当前 release evidence",
        "releaseEvidence",
        "最新 try-now",
        "Android 构建证据",
        "Android 真机证据",
        "桌面 UI smoke",
        "桌面线上登录/积分/agent smoke",
        "App Bundle 结构预检 AAB",
        "macOS DMG",
        "Windows NSIS",
        "current-release-scope.json",
        "activePlatforms",
        "deferredPlatforms",
        "当前批次",
        "延期平台",
    ]:
        assert expected in source


def test_real_user_acceptance_requires_minimum_two_testers_and_screenshots():
    source = read_text("scripts/real_user_acceptance_check.mjs")

    for expected in [
        "REAL_USER_MIN_TESTERS",
        "minimumTestersPerPlatform",
        "resultFilesForPlatform",
        "results/*.json",
        "通过测试人不足",
        "01-home.png",
        "08-delete-account.png",
        "realSmsEmailPaymentTriggered",
        "current-release-scope.json",
        "activePlatforms",
        "deferredPlatforms",
        "当前批次平台",
    ]:
        assert expected in source


def test_real_user_acceptance_docs_explain_multi_tester_requirement():
    docs = read_text("docs/release/real-user-acceptance.md")

    for expected in [
        "每个平台至少需要 2 个测试人",
        "results/tester-1.json",
        "results/tester-2.json",
        "正式候选以 `results/*.json`",
        "少于 2 个测试人通过",
    ]:
        assert expected in docs
