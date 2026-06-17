from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_app_record_config_tracks_mobile_records_and_not_required_reasons():
    config = read_text("configs/release/app-record.json")

    for expected in [
        "h5-domain",
        "android-cn",
        "harmony-cn",
        "ios-appstore",
        "google-play",
        "packageOrBundleId",
        "notRequiredReason",
        "requiresChinaAppRecordBeforeChinaStores",
        "com.shian.xuanctai",
    ]:
        assert expected in config


def test_app_record_checker_blocks_missing_evidence_and_secret_materials():
    source = read_text("scripts/app_record_status_check.mjs")

    for expected in [
        "APP_RECORD_STRICT",
        "configs/release/app-record.json",
        "app-record-status",
        "status=ready 但缺少 evidencePaths",
        "status=not-required 但缺少 notRequiredReason",
        "可能包含密码、token、证书或验证码",
        "H5 域名 ICP 与 HTTPS 继续由 `npm run domain:https` 追踪",
        "current-release-scope.json",
        "deferredPlatforms",
        "activePlatforms",
        "deferred",
        "鸿蒙延期时不作为本轮阻塞",
    ]:
        assert expected in source


def test_app_record_status_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")
    handoff = read_text("docs/release/app-record-handoff.md")

    assert '"store:app-record": "node scripts/app_record_status_check.mjs"' in package_json
    assert "npm run store:app-record" in ci
    assert "store:app-record" in release_check
    assert "store:app-record" in finalize
    assert "store:app-record" in readiness
    assert "compliance.app-record" in readiness
    assert "APP 备案与不适用说明" in readiness
    assert "appRecordStatus" in release_package
    assert "latestAppRecordStatus" in summary
    assert "store:app-record" in docs
    assert "app-record-handoff.md" in docs
    assert "https://shianjieyouwu.com/" in handoff
    assert "粤ICP备2026072162号-1" in handoff
    assert "artifacts/store-evidence-inbox/v1.0.0/harmony/app-record-screenshot/" in handoff
