from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_hbuilderx_cloud_pack_attempt_is_safe_and_wired():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/mobile-build-evidence.md")
    source = read_text("scripts/hbuilderx_cloud_pack_attempt.mjs")

    assert '"mobile:hbuilderx-cloud-pack": "node scripts/hbuilderx_cloud_pack_attempt.mjs"' in package_json
    assert "mobile:hbuilderx-cloud-pack" in release_check
    assert "mobile:hbuilderx-cloud-pack" in docs

    for expected in [
        "HBUILDERX_CLOUD_PACK_EXECUTE",
        "artifacts', 'hbuilderx-cloud-pack-attempts'",
        "attempt.json",
        "output.redacted.log",
        "redactedArgs",
        "certpassword",
        "storepassword",
        "<redacted>",
        "--android.androidpacktype",
        "|| '3'",
        "--android.packagename",
        "--ios.bundle",
        "dcloud-phone-verification",
        "android-public-cert-disabled",
        "dcloud-sdk-version-lag",
        "cloud-certificate-required",
        "ios-profile-required",
        "ios-cert-required",
        "ios-signing-material-required",
        "HBuilderX CLI 不存在",
        "DCloud 账号或应用所有者账号需要重新验证手机号",
        "iOS 云打包需要 provisioning profile 文件",
        "证书、签名口令、p12、mobileprovision、keystore 不进入 GitHub",
    ]:
        assert expected in source


def test_hbuilderx_cloud_pack_attempt_does_not_hardcode_secret_values():
    source = read_text("scripts/hbuilderx_cloud_pack_attempt.mjs")

    for forbidden in [
        "HBUILDERX_IOS_CERT_PASSWORD || '",
        "HBUILDERX_ANDROID_CERT_PASSWORD || '",
        "HBUILDERX_ANDROID_STORE_PASSWORD || '",
        "certpassword: '",
        "storepassword: '",
        "privateKey: '",
    ]:
        assert forbidden not in source
