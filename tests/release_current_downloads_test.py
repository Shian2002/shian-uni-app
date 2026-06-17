import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_current_downloads_creates_stable_aliases_without_extra_churn():
    package_json = json.loads(read_text("package.json"))
    source = read_text("scripts/release_current_downloads.mjs")
    release_check = read_text("scripts/release_check.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")
    docs = read_text("docs/release/README.md")

    assert package_json["scripts"]["release:current-downloads"] == "node scripts/release_current_downloads.mjs"
    assert "release:current-downloads" in release_check
    assert "release:current-downloads" in readiness
    assert "release:current-downloads" in docs
    assert "artifacts/current-downloads/" in docs
    for expected in [
        "artifacts', 'current-downloads'",
        "artifacts/current-index-latest.json",
        "shian-current-macos-arm64.dmg",
        "shian-current-macos-arm64.app.zip",
        "shian-current-windows-x64.exe",
        "shian-current-android-debug.apk",
        "shian-current-android-debug.aab",
        "shian-current-app-icon-1024.png",
        "samePath",
        "mode = 'existing'",
        "固定下载文件缺失",
        "linkSync(source, target)",
        "copyFileSync(source, target)",
        "checksums.sha256",
        "当前稳定下载入口",
        "证据摘要",
        "时安 agent",
        "移动端后端请求能力",
        "当前索引问题",
        "propagatedIndexIssues",
        "issue !== '当前稳定下载入口未通过或缺失'",
        "freshness: currentIndex?.freshness || null",
        "Windows 新鲜度",
    ]:
        assert expected in source


def test_release_finalize_refreshes_current_downloads_after_packaging():
    source = read_text("scripts/release_finalize.mjs")
    package_json = json.loads(read_text("package.json"))
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")

    assert package_json["scripts"]["release:finalize:plan"] == "node scripts/release_finalize.mjs --plan-only"
    assert "release:finalize:plan" in release_check
    assert "release:finalize:plan" in docs

    for expected in [
        "const planOnly = process.argv.includes('--plan-only')",
        "const requiredFinalizeConfirm = `final-package-refresh:${version}`",
        "CONFIRM_FINAL_PACKAGE_REFRESH",
        "executionBlocked",
        "confirmation-required",
        "function planStep",
        "(planOnly || executionBlocked) ? planStep",
        "没有执行构建、打包、部署、上传或商店提交命令",
        "['platform:backend-matrix:pre', ['run', 'platform:backend-matrix']]",
        "['release:final-package-plan:pre', ['run', 'release:final-package-plan']]",
        "['platform:backend-matrix', ['run', 'platform:backend-matrix']]",
        "['release:final-package-plan', ['run', 'release:final-package-plan']]",
        "['release:try-now', ['run', 'release:try-now']]",
        "['release:external-handoff', ['run', 'release:external-handoff']]",
        "['release:current-index', ['run', 'release:current-index']]",
        "['release:current-downloads', ['run', 'release:current-downloads']]",
        "['platform:backend-matrix:final', ['run', 'platform:backend-matrix']]",
        "['release:final-package-plan:final', ['run', 'release:final-package-plan']]",
        "['release:try-now:final', ['run', 'release:try-now']]",
        "['release:external-handoff:final', ['run', 'release:external-handoff']]",
        "['release:current-index:final', ['run', 'release:current-index']]",
        "['release:current-downloads:final', ['run', 'release:current-downloads']]",
        "tryNow: latestDir('artifacts/try-now')",
        "platformBackendMatrix: latestDir('artifacts/platform-backend-matrix')",
        "finalPackagePlan: latestDir('artifacts/final-package-plan')",
        "externalHandoff: latestDir('artifacts/external-handoff')",
        "currentIndex: latestDir('artifacts/current-index')",
        "currentDownloadsManifest",
    ]:
        assert expected in source

    assert source.index("['platform:backend-matrix:pre',") < source.index("['release:channel-builds',")
    assert source.index("['release:final-package-plan:pre',") < source.index("['release:channel-builds',")
    assert source.index("['release:user-actions',") < source.index("['platform:backend-matrix',")
    assert source.index("['platform:backend-matrix',") < source.index("['release:final-package-plan',")
    assert source.index("['release:final-package-plan',") < source.index("['release:try-now',")
    assert source.index("['release:try-now',") < source.index("['release:package',")
    assert source.index("['release:package',") < source.index("['release:external-handoff',")
    assert source.index("['release:external-handoff',") < source.index("['release:current-index',")
    assert source.index("['release:current-index',") < source.index("['release:current-downloads',")

    assert source.index("['release:user-actions:final',") < source.index("['platform:backend-matrix:final',")
    assert source.index("['platform:backend-matrix:final',") < source.index("['release:final-package-plan:final',")
    assert source.index("['release:final-package-plan:final',") < source.index("['release:try-now:final',")
    assert source.index("['release:try-now:final',") < source.index("['release:package:final',")
    assert source.index("['release:package:final',") < source.index("['release:external-handoff:final',")
    assert source.index("['release:external-handoff:final',") < source.index("['release:current-index:final',")
    assert source.index("['release:current-index:final',") < source.index("['release:current-downloads:final',")
