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


def test_release_policy_enables_default_h5_and_restricts_store_channels():
    source = read("src/utils/releasePolicy.js")

    assert "externalRechargeChannels" in source
    assert "h5-recharge" in source
    assert "if (!channel) return true" in source
    assert "return externalRechargeChannels.has(channel)" in source
    assert "当前审核渠道暂不展示第三方数字内容充值入口" in source


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
        assert "startHupijiaoPayment" in source
        assert "paymentQrUrl" in source
        assert "pay_method: 'hupijiao'" in source
        assert "rechargeQrSrc" not in source
        assert "paymentProofPlaceholder" not in source
        assert "verifyPayButtonText" not in source


def test_points_pages_open_hupijiao_pay_url_on_mobile_and_keep_qr_fallback():
    for path in ["src/pages/points/index.vue", "src/package-user/points/index.vue"]:
        source = read(path)

        assert "function isMobilePaymentRuntime()" in source
        assert "function isWechatBrowser()" in source
        assert "paymentPayButtonText" in source
        assert "pkg-cta" in source
        assert "立即充值" in source
        assert "登录后充值" in source
        assert "打开微信支付页" in source
        assert "订单已创建，请点击下方按钮进入微信支付页。" in source
        assert "window.location.href = url" in source
        assert "function handleCreatedPaymentOrder(payUrl, qrUrl, orderId)" in source
        assert "if (isWechatBrowser() && payUrl)" in source
        assert "if (isMobilePaymentRuntime() && payUrl)" in source
        assert source.index("if (isWechatBrowser() && payUrl)") < source.index("if (isMobilePaymentRuntime() && payUrl)")
        assert "openRechargeModalWithQr(qrUrl, orderId)" in source
        assert "未拿到二维码，请点打开支付页继续支付。" in source
        assert "handleCreatedPaymentOrder(d.pay_url || '', d.qrcode_url || '', d.order_id)" in source
