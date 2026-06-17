from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_real_user_dispatch_script_tracks_all_platforms_and_evidence():
    source = read_text("scripts/real_user_dispatch.mjs")

    for expected in [
        "REAL_USER_DISPATCH_STRICT",
        "artifacts/real-user-dispatch",
        "ready-to-dispatch",
        "android",
        "ios",
        "harmony",
        "macos",
        "windows",
        "storeMaterials",
        "privacyDisclosure",
        "legalUrlCheck",
        "current-release-scope.json",
        "activePlatforms",
        "deferredPlatforms",
        "当前批次可发测",
        "延期平台本轮不作为阻塞",
    ]:
        assert expected in source


def test_real_user_dispatch_is_wired_into_release_flow():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    docs = read_text("docs/release/real-user-acceptance.md")

    assert '"real-user:dispatch": "node scripts/real_user_dispatch.mjs"' in package_json
    assert "real-user:dispatch" in release_check
    assert "real-user:dispatch" in finalize
    assert "realUserDispatch" in readiness
    assert "artifacts/real-user-dispatch" in docs
