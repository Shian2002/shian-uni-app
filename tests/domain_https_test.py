from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_domain_https_config_tracks_h5_api_dns_https_and_records():
    config = read_text("configs/release/domain-https.json")

    for expected in [
        "h5-production",
        "api-production",
        "requiresHttpsBeforeStoreSubmit",
        "requiresIcpBeforeChinaStores",
        "requiresAppRecordBeforeChinaStores",
        "dnsStatus",
        "httpsStatus",
        "tlsCertificateStatus",
        "icpStatus",
        "appRecordStatus",
        "appRecordNotRequiredReason",
        "ownerAlias",
        "release-owner",
        "https://shianjieyouwu.com",
        "营销页末尾 ICP 备案展示源码或线上截图",
    ]:
        assert expected in config
    assert "http://119.29.128.18" not in config


def test_domain_https_checker_blocks_ip_http_and_secret_materials():
    source = read_text("scripts/domain_https_check.mjs")

    for expected in [
        "DOMAIN_HTTPS_STRICT",
        "configs/release/domain-https.json",
        "domain-https",
        "targetBaseUrl 不是 HTTPS",
        "currentCandidateUrl 不是 HTTPS",
        "currentCandidateUrl 仍使用 IP、本地地址或 http",
        "legal-urls 仍不是正式 HTTPS 域名",
        "DNS 密钥、证书私钥、密码或 token",
        "LEGAL_URL_CHECK_ONLINE=1",
        "appRecordNotRequiredReason",
    ]:
        assert expected in source


def test_domain_https_is_wired_into_release_flow():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    release_package = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    docs = read_text("docs/release/README.md")

    assert '"domain:https": "node scripts/domain_https_check.mjs"' in package_json
    assert "npm run domain:https" in ci
    assert "domain:https" in release_check
    assert "domain:https" in finalize
    assert "domainHttps" in readiness
    assert "domainHttps" in release_package
    assert "latestDomainHttps" in summary
    assert "domain:https" in docs
