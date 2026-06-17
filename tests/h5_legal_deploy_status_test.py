from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_h5_legal_deploy_status_checker_tracks_local_dist_and_online_assets():
    source = read_text("scripts/h5_legal_deploy_status_check.mjs")

    for expected in [
        "H5_LEGAL_DEPLOY_STRICT",
        "configs/release/legal-urls.json",
        "configs/release/domain-https.json",
        "pages-legal-index",
        "fetchSameOriginAssets",
        "deployedLegalPage",
        "deployedIcpFooter",
        "粤ICP备",
        "LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict",
        "不得把 `configs/release/legal-urls.json` 的 `status` 改为 `ready`",
    ]:
        assert expected in source


def test_h5_legal_deploy_status_is_documented_and_wired():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    ci = read_text(".github/workflows/ci.yml")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/h5-legal-page-deploy-handoff.md")

    assert '"h5:legal-deploy-status": "node scripts/h5_legal_deploy_status_check.mjs"' in package_json
    assert "h5:legal-deploy-status" in release_check
    assert "npm run h5:legal-deploy-status" in ci
    assert "h5:legal-deploy-status" in finalize
    assert "h5:legal-deploy-status" in readiness
    assert "compliance.h5-legal-deploy" in readiness
    assert "H5 法律页线上部署" in readiness
    assert "h5LegalDeployStatusReport" in readiness
    assert "h5LegalDeployStatus" in release_package
    assert "latestH5LegalDeployStatus" in summary
    assert "npm run h5:legal-deploy-status" in docs
