from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_store_submission_status_config_tracks_all_release_channels():
    config = read_text("configs/release/store-submissions.json")

    for expected in [
        "yingyongbao",
        "huawei",
        "xiaomi",
        "oppo",
        "vivo",
        "google-play",
        "appstore",
        "harmony",
        "github-desktop",
        "not-submitted",
    ]:
        assert expected in config


def test_store_submission_status_checker_blocks_secrets_and_tracks_review_evidence():
    source = read_text("scripts/store_submission_status_check.mjs")

    for expected in [
        "STORE_SUBMISSION_STATUS_STRICT",
        "configs/release/store-submissions.json",
        "artifacts",
        "store-submission-status",
        "submissionId",
        "artifactSha256",
        "reviewScreenshotPaths",
        "not-submitted",
        "approved",
        "keystore",
        "mobileprovision",
        "验证码",
        "current-release-scope.json",
        "deferredPlatforms",
        "activePlatforms",
        "deferred",
        "延期平台本轮不作为阻塞",
    ]:
        assert expected in source


def test_store_submission_status_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")

    assert '"store:submission-status": "node scripts/store_submission_status_check.mjs"' in package_json
    assert "npm run store:submission-status" in ci
    assert "store:submission-status" in release_check
    assert "store:submission-status" in finalize
    assert "storeSubmissionStatus" in readiness
    assert "storeSubmissionStatus" in release_package
    assert "latestStoreSubmissionStatus" in summary
    assert "store:submission-status" in docs
