from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_real_user_roster_tracks_two_slots_for_each_platform_without_private_contact_data():
    config = read_text("configs/release/real-user-roster.json")

    for expected in [
        "minimumTestersPerPlatform",
        "h5-tester-1",
        "android-tester-1",
        "ios-tester-1",
        "harmony-tester-1",
        "macos-tester-1",
        "windows-tester-1",
        "noPhoneNumbers",
        "noEmailAddresses",
        "reviewAccountDeliveredBySecureChannel",
    ]:
        assert expected in config


def test_real_user_roster_checker_blocks_private_contact_data_and_requires_passed_slots():
    source = read_text("scripts/real_user_roster_check.mjs")

    for expected in [
        "REAL_USER_ROSTER_STRICT",
        "configs/release/real-user-roster.json",
        "real-user-roster",
        "not-assigned",
        "passed",
        "通过测试人不足",
        "手机号、邮箱、密码、验证码或 token",
        "latestRealUserPacket",
        "current-release-scope.json",
        "activePlatforms",
        "deferredPlatforms",
        "deferred",
        "当前批次平台",
    ]:
        assert expected in source


def test_real_user_roster_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")

    assert '"real-user:roster": "node scripts/real_user_roster_check.mjs"' in package_json
    assert "npm run real-user:roster" in ci
    assert "real-user:roster" in release_check
    assert "real-user:roster" in finalize
    assert "realUserRoster" in readiness
    assert "realUserRoster" in release_package
    assert "latestRealUserRoster" in summary
    assert "real-user:roster" in docs
