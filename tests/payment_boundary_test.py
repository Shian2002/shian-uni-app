from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_policy_restricts_app_store_and_google_play_external_recharge():
    source = read("src/utils/releasePolicy.js")

    assert "appstore" in source
    assert "google-play" in source
    assert "isExternalRechargeEnabled" in source
    assert "getPaymentBoundaryNotice" in source


def test_points_pages_hide_external_recharge_for_restricted_channels():
    for path in ["src/pages/points/index.vue", "src/package-user/points/index.vue"]:
        source = read(path)

        assert "isExternalRechargeEnabled" in source
        assert 'v-if="externalRechargeEnabled"' in source
        assert 'v-if="externalRechargeEnabled && aiPackages.length"' in source
        assert 'v-if="!externalRechargeEnabled"' in source
        assert 'id="rechargeModal" v-if="externalRechargeEnabled"' in source
        assert "当前审核渠道暂不开放充值" in source
        assert "paymentBoundaryNotice" in source


def test_points_pages_keep_recharge_api_behind_policy_guard():
    for path in ["src/pages/points/index.vue", "src/package-user/points/index.vue"]:
        source = read(path)
        guard_index = source.index("if (!externalRechargeEnabled.value)")
        create_order_index = source.index("url: rechargeApiBase + '/create-order'")

        assert guard_index < create_order_index
        assert "rechargeQrSrc" in source
        assert "paymentProofPlaceholder" in source
        assert "verifyPayButtonText" in source
