from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_desktop_signing_preflight_checks_real_signing_tools_without_secrets():
    package_json = read_text("package.json")
    source = read_text("scripts/desktop_signing_preflight.mjs")

    assert '"desktop:signing-preflight": "node scripts/desktop_signing_preflight.mjs"' in package_json

    for expected in [
        "security', ['find-identity', '-v', '-p', 'codesigning']",
        "Developer ID Application",
        "xcrun', ['notarytool', '--help']",
        "codesign', ['--verify', '--deep', '--strict'",
        "spctl', ['--assess', '--type', 'execute'",
        "signtool",
        "osslsigncode",
        "desktop-signing-preflight",
        "macSigningReady",
        "windowsSigningTool",
        "不会读取、保存或要求输入证书密码",
    ]:
        assert expected in source


def test_desktop_signing_preflight_redacts_sensitive_output():
    source = read_text("scripts/desktop_signing_preflight.mjs")

    for expected in [
        "redact",
        "<redacted-email>",
        "<redacted-sha1>",
        "password|passwd|token|secret|keychain-profile|apple-id|team-id",
    ]:
        assert expected in source
