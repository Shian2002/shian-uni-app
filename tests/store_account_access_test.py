from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_store_account_access_config_tracks_all_required_developer_accounts_without_secrets():
    config = read_text("configs/release/store-account-access.json")

    for expected in [
        "dcloud",
        "apple-developer",
        "google-play",
        "huawei-appgallery",
        "yingyongbao",
        "xiaomi",
        "oppo",
        "vivo",
        "github-releases",
        "noPasswords",
        "noVerificationCodes",
        "ownersUseAliasesOnly",
    ]:
        assert expected in config


def test_store_account_access_checker_blocks_sensitive_account_data_and_requires_ready_statuses():
    source = read_text("scripts/store_account_access_check.mjs")

    for expected in [
        "STORE_ACCOUNT_ACCESS_STRICT",
        "configs/release/store-account-access.json",
        "store-account-access",
        "accessStatus",
        "twoFactorStatus",
        "organizationStatus",
        "signingCapabilityStatus",
        "ownerAlias",
        "手机号、邮箱、密码、验证码、token",
        "current-release-scope.json",
        "deferredPlatforms",
        "activePlatforms",
        "deferred",
        "华为应用市场",
    ]:
        assert expected in source


def test_store_account_access_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")

    assert '"store:account-access": "node scripts/store_account_access_check.mjs"' in package_json
    assert "npm run store:account-access" in ci
    assert "store:account-access" in release_check
    assert "store:account-access" in finalize
    assert "storeAccountAccess" in readiness
    assert "storeAccountAccess" in release_package
    assert "latestStoreAccountAccess" in summary
    assert "store:account-access" in docs
