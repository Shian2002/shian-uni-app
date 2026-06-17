from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_hbuilderx_harmony_pack_attempt_is_safe_and_wired():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    docs = read_text("docs/release/mobile-build-evidence.md")
    source = read_text("scripts/hbuilderx_harmony_pack_attempt.mjs")

    assert '"mobile:hbuilderx-harmony-pack": "node scripts/hbuilderx_harmony_pack_attempt.mjs"' in package_json
    assert "mobile:hbuilderx-harmony-pack" in release_check
    assert "mobile:hbuilderx-harmony-pack" in finalize
    assert "mobile:hbuilderx-harmony-pack" in docs

    for expected in [
        "HBUILDERX_HARMONY_PACK_EXECUTE",
        "artifacts', 'hbuilderx-harmony-pack-attempts'",
        "pack",
        "app-harmony",
        "attempt.json",
        "output.redacted.log",
        "redact",
        "<redacted-email>",
        "harmony-toolchain-missing",
        "harmony-package-name-required",
        "harmony-signing-required",
        "DevEco Studio/hdc/hvigor",
        "HBuilderX CLI 不存在",
        "证书、签名口令、p12、keystore、华为后台凭据不进入 GitHub",
    ]:
        assert expected in source


def test_hbuilderx_harmony_pack_attempt_does_not_hardcode_secret_values():
    source = read_text("scripts/hbuilderx_harmony_pack_attempt.mjs")

    for forbidden in [
        "certpassword: '",
        "storepassword: '",
        "privateKey: '",
        "HUAWEI_PASSWORD",
        "HARMONY_CERT_PASSWORD || '",
    ]:
        assert forbidden not in source
