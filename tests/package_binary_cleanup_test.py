import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_package_binary_cleanup_plan_is_wired_and_protected():
    package_json = json.loads(read_text("package.json"))
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")
    source = read_text("scripts/package_binary_cleanup_plan.mjs")

    assert package_json["scripts"]["release:package-cleanup-plan"] == "node scripts/package_binary_cleanup_plan.mjs"
    assert "release:package-cleanup-plan" in release_check
    assert "scripts/package_binary_cleanup_plan.mjs" in release_check
    assert "npm run release:package-cleanup-plan -- --keep=2" in docs
    assert "只读生成旧安装包/中间包清理候选" in docs
    assert "CONFIRM_PACKAGE_BINARY_CLEANUP" in source
    assert "artifacts/low-impact-status" in source
    assert "lowImpactStatus" in source
    assert "videoSafe" in source
    assert "删除仍需显式确认变量" in source
    assert "blockedReasons.length === 0" in source
    assert "delete-old-packages:" in source
    assert "artifacts/current-downloads/" in source
    assert "artifacts/release-inbox/" in source
    assert "artifacts/current-index-latest.json" in source
    assert "artifacts/try-now/latest-manifest.json" in source
    assert "dynamicProtectedPaths" in source
    assert "artifacts/ip-evidence/" in source
    assert "artifacts/soft-copyright-application/" in source
    assert "rmSync(join(root, file.path), { force: true })" in source


def test_package_binary_cleanup_plan_covers_binary_extensions_and_finalize_queue():
    source = read_text("scripts/package_binary_cleanup_plan.mjs")
    finalize = read_text("scripts/release_finalize.mjs")
    plan = read_text("scripts/final_package_refresh_plan.mjs")
    prune = read_text("scripts/prune_old_artifacts.mjs")

    for expected in [".apk", ".aab", ".ipa", ".hap", ".dmg", ".zip", ".exe", ".msi"]:
        assert expected in source
    assert "package-binary-cleanup" in prune
    assert "package-cleanup-dry-run" in plan
    assert "release:package-cleanup-plan:pre" in finalize
    assert "release:package-cleanup-plan:final" in finalize
    assert finalize.index("release:package-cleanup-plan:pre") < finalize.index("release:channel-builds")
    assert finalize.index("release:package-cleanup-plan:final") < finalize.index("release:try-now:final")
