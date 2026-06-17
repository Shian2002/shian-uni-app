from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_all_platform_status_is_wired_into_release_surface():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")

    assert '"release:all-platform-status": "node scripts/release_all_platform_status.mjs"' in package_json
    assert "release:all-platform-status" in release_check
    assert "release:all-platform-status" in docs
    assert "全端后端矩阵" in docs


def test_all_platform_status_reads_existing_reports_without_heavy_work():
    source = read_text("scripts/release_all_platform_status.mjs")

    for expected in [
        "artifacts', 'all-platform-status'",
        "ALL_PLATFORM_STATUS_STRICT",
        "artifacts/low-impact-status",
        "artifacts/final-package-completeness",
        "artifacts/platform-backend-matrix",
        "artifacts/final-package-plan",
        "artifacts/current-downloads/manifest.json",
        "artifacts/mobile-build-requests",
        "全端安装包与后端状态总览",
        "低影响状态快照",
        "最终包完整性",
        "后端请求证据",
        "真机证据",
        "移动端已知本机阻塞",
        "旧安装包清理先用 npm run release:package-cleanup-plan -- --keep=2 做 dry-run",
        "最终包全部更新后再刷新 current-downloads",
        "HBuilderX 插件已补齐后，继续用 mobile:build-env/mobile:hbuilderx-resources",
        "iOS TestFlight/IPA 已延期到后续批次",
        "鸿蒙 HAP/AppGallery 已延期到后续批次",
        "current-release-scope.json",
        "scopedSummary",
        "deferredPlatforms",
        "延期平台本轮不作为阻塞",
        "不作为安装包缺口",
        "低影响可先跑",
        "重负载或外部环境补齐后再做",
    ]:
        assert expected in source

    assert "低影响状态未通过：当前存在重负载进程、磁盘或下载入口风险。" not in source

    for forbidden in [
        "child_process",
        "execFileSync",
        "spawnSync",
        "rmSync",
        "unlinkSync",
        "npm run build:app'",
        "npm run mobile:hbuilderx-resources'",
        "npx playwright install",
        "brew install xcodes",
    ]:
        assert forbidden not in source
