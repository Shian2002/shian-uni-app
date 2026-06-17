from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_store_evidence_requirements_track_all_stores_and_backend_screenshots():
    config = read_text("configs/release/store-evidence-requirements.json")

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
        "data-safety-screenshot",
        "app-privacy-screenshot",
        "account-deletion-device-screenshot",
        "artifacts/store-evidence-inbox/v1.0.0",
    ]:
        assert expected in config


def test_store_evidence_status_checker_blocks_secret_evidence_and_generates_manifest():
    source = read_text("scripts/store_evidence_status_check.mjs")

    for expected in [
        "STORE_EVIDENCE_STATUS_STRICT",
        "configs/release/store-evidence-requirements.json",
        "store-evidence-status",
        "store-evidence-inbox",
        "submit-status-json",
        "data-safety-screenshot",
        "app-privacy-screenshot",
        "sha256",
        "mobileprovision",
        "验证码",
        "current-release-scope.json",
        "deferredPlatforms",
        "activePlatforms",
        "deferred",
        "延期平台本轮不作为阻塞",
    ]:
        assert expected in source


def test_store_evidence_status_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")
    handoff = read_text("docs/release/store-evidence-handoff.md")

    assert '"store:evidence-status": "node scripts/store_evidence_status_check.mjs"' in package_json
    assert "npm run store:evidence-status" in ci
    assert "store:evidence-status" in release_check
    assert "store:evidence-status" in finalize
    assert "storeEvidenceStatus" in readiness
    assert "storeEvidenceStatus" in release_package
    assert "latestStoreEvidenceStatus" in summary
    assert "store:evidence-status" in docs
    assert "store-evidence-handoff.md" in docs
    assert "artifacts/store-evidence-inbox/v1.0.0/google-play" in handoff
    assert "app-privacy-screenshot" in handoff
