from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_h5_only_deploy_script_requires_explicit_confirmation_and_dry_run():
    script = read_text("deploy-h5-to-server.sh")

    for expected in [
        "CONFIRM_H5_DEPLOY=shianjieyouwu.com",
        "DRY_RUN=1",
        "INCLUDE_RECHARGE_ASSETS=1",
        "dist/build/h5/index.html",
        "dist/build/h5/assets",
        "dist/build/h5/static",
        "--exclude '/static/uploads/'",
        "--exclude '/static/alipay-recharge.jpg'",
        "npm run h5:legal-deploy-status -- --strict",
        "LEGAL_URL_CHECK_SCOPE=website LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict",
        "STORE_SUBMISSION_CHECK=1",
        "bash scripts/production_monitor.sh",
    ]:
        assert expected in script

    assert "backend/" not in script
    assert "systemctl restart" not in script


def test_h5_only_deploy_is_wired_into_release_checks_and_docs():
    package_json = read_text("package.json")
    preflight = read_text("scripts/preflight_release.sh")
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/h5-legal-page-deploy-handoff.md")

    assert '"deploy:h5": "bash deploy-h5-to-server.sh"' in package_json
    assert '"rollback:h5": "bash rollback-h5-on-server.sh"' in package_json
    assert "deploy-h5-to-server.sh" in preflight
    assert "rollback-h5-on-server.sh" in preflight
    assert "deploy:h5" in release_check
    assert "rollback:h5" in release_check
    assert "CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5" in docs
    assert "CONFIRM_H5_ROLLBACK=shianjieyouwu.com npm run rollback:h5" in docs


def test_h5_rollback_script_requires_explicit_confirmation_and_uses_latest_backup():
    script = read_text("rollback-h5-on-server.sh")

    for expected in [
        "CONFIRM_H5_ROLLBACK=shianjieyouwu.com",
        "ROLLBACK_ARCHIVE",
        "h5-deploy-*.tar.gz",
        "rm -rf '$H5_DIR/assets'",
        "tar -C '$H5_DIR' -xzf '$ROLLBACK_ARCHIVE'",
        "bash scripts/production_monitor.sh",
        "https://shianjieyouwu.com",
    ]:
        assert expected in script

    assert "backend/" not in script
    assert "systemctl restart" not in script
