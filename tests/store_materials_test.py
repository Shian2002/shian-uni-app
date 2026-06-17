from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_store_materials_script_covers_store_compliance_gates():
    source = read_text("scripts/store_materials_check.mjs")

    for expected in [
        "STORE_MATERIALS_STRICT",
        "configs/release/legal-urls.json",
        "Data safety",
        "App Privacy",
        "store:evidence-status",
        "store:app-record",
        "账号注销",
        "线上同款登录",
        "隐私政策 URL",
        "用户协议 URL",
        "artifacts",
        "store-materials",
        "current-release-scope.json",
        "deferredPlatforms",
        "activePlatforms",
        "当前批次",
        "延期平台只保留配置",
    ]:
        assert expected in source


def test_legal_materials_have_store_review_urls_and_pages():
    config = read_text("configs/release/legal-urls.json")
    pages = read_text("src/pages.json")
    legal_page = read_text("src/pages/legal/index.vue")
    privacy_doc = read_text("docs/legal/privacy-policy.md")
    terms_doc = read_text("docs/legal/user-agreement.md")

    assert "privacyPolicyUrl" in config
    assert "userAgreementUrl" in config
    assert "pages/legal/index" in pages
    assert "隐私政策" in legal_page
    assert "用户协议" in legal_page
    assert "账号注销" in legal_page
    assert "数据删除" in privacy_doc
    assert "不构成医疗、法律、金融" in terms_doc


def test_legal_url_check_is_static_by_default_and_online_opt_in():
    source = read_text("scripts/legal_url_check.mjs")

    for expected in [
        "LEGAL_URL_CHECK_ONLINE",
        "LEGAL_URL_CHECK_STRICT",
        "configs/release/legal-urls.json",
        "privacyPolicyUrl",
        "userAgreementUrl",
        "legal-url-checks",
        "local-static",
        "html-and-assets",
        "fetchSameOriginAssets",
    ]:
        assert expected in source


def test_privacy_disclosure_template_and_checker_cover_app_store_and_google_play():
    config = read_text("configs/release/privacy-disclosures.json")
    source = read_text("scripts/privacy_disclosure_check.mjs")

    for expected in [
        "appleAppPrivacy",
        "googlePlayDataSafety",
        "dataDeletionAvailable",
        "humanReviewStatus",
        "thirdPartySharing",
        "App Privacy",
        "Data safety",
    ]:
        assert expected in config

    for expected in [
        "PRIVACY_DISCLOSURE_STRICT",
        "configs/release/privacy-disclosures.json",
        "requiredAppleTypes",
        "requiredGoogleCategories",
        "privacy-disclosures",
        "localPassed",
        "finalPassed",
    ]:
        assert expected in source


def test_store_materials_is_wired_into_release_gates():
    package_json = read_text("package.json")
    ci = read_text(".github/workflows/ci.yml")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")

    assert '"store:materials": "node scripts/store_materials_check.mjs"' in package_json
    assert '"store:legal-urls": "node scripts/legal_url_check.mjs"' in package_json
    assert '"store:privacy": "node scripts/privacy_disclosure_check.mjs"' in package_json
    assert '"store:evidence-status": "node scripts/store_evidence_status_check.mjs"' in package_json
    assert '"store:app-record": "node scripts/app_record_status_check.mjs"' in package_json
    assert "npm run store:materials" in ci
    assert "npm run store:evidence-status" in ci
    assert "npm run store:app-record" in ci
    assert "store:materials" in finalize
    assert "store:evidence-status" in finalize
    assert "store:app-record" in finalize
    assert "store-materials" in readiness
