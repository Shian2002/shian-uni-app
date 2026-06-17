import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_final_package_completeness_is_wired_and_read_only():
    package_json = json.loads(read_text("package.json"))
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")
    source = read_text("scripts/final_package_completeness_check.mjs")

    assert package_json["scripts"]["release:package-completeness"] == "node scripts/final_package_completeness_check.mjs"
    assert "release:package-completeness" in release_check
    assert "scripts/final_package_completeness_check.mjs" in release_check
    assert "npm run release:package-completeness" in docs
    assert "只读检查当前批次最终安装包类型是否齐备" in docs
    assert "execFileSync" not in source
    assert "spawnSync" not in source
    assert "rmSync" not in source


def test_final_package_completeness_covers_required_package_types():
    source = read_text("scripts/final_package_completeness_check.mjs")

    for expected in [
        "artifacts', 'final-package-completeness'",
        "FINAL_PACKAGE_COMPLETENESS_STRICT",
        "artifacts/current-downloads/manifest.json",
        "artifacts/release-inbox",
        "uploadCandidates",
        "Android APK",
        "Android AAB",
        "iOS TestFlight/IPA",
        "鸿蒙 HAP/AppGallery",
        "macOS DMG",
        "macOS App ZIP",
        "Windows EXE/MSI/NSIS",
        "platformPackageReady",
        "platformPackageIssue",
        "packageReady === true",
        "platformReady",
        "filesReady",
        "缺少或过期最终包",
        "stale",
        "全端后端能力矩阵未达到 backendReady=total",
        "readyToRunFinalPackageRefresh",
        "current-release-scope.json",
        "deferredPlatforms",
        "requiredForCurrentBatch",
        "当前批次最终安装包类型齐备",
        "deferred",
    ]:
        assert expected in source


def test_release_finalize_runs_package_completeness_after_downloads():
    source = read_text("scripts/release_finalize.mjs")

    assert "['release:package-completeness:before-handoff', ['run', 'release:package-completeness']]" in source
    assert "['release:package:with-completeness', ['run', 'release:package']]" in source
    assert "['release:package-completeness:after-downloads', ['run', 'release:package-completeness']]" in source
    assert "['release:package:after-downloads', ['run', 'release:package']]" in source
    assert "['release:package-completeness:before-handoff:final', ['run', 'release:package-completeness']]" in source
    assert "['release:package:with-completeness:final', ['run', 'release:package']]" in source
    assert "['release:package-completeness:final', ['run', 'release:package-completeness']]" in source
    assert "['release:package:after-downloads:final', ['run', 'release:package']]" in source
    assert "finalPackageCompleteness: latestDir('artifacts/final-package-completeness')" in source
    assert "Final Package Completeness" in source
    assert source.index("['release:package',") < source.index("['release:package-completeness:before-handoff',")
    assert source.index("['release:package-completeness:before-handoff',") < source.index("['release:package:with-completeness',")
    assert source.index("['release:package:with-completeness',") < source.index("['release:external-handoff',")
    assert source.index("['release:current-downloads',") < source.index("['release:package-completeness:after-downloads',")
    assert source.index("['release:package-completeness:after-downloads',") < source.index("['release:package:after-downloads',")
    assert source.index("['release:current-downloads:final',") < source.index("['release:package-completeness:final',")
    assert source.index("['release:package-completeness:final',") < source.index("['release:package:after-downloads:final',")
