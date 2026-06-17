from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_package_hard_blocks_include_compliance_and_store_status():
    source = read_text("scripts/release_package.mjs")

    for expected in [
        "latestJsonReport",
        "latestEntryTime",
        "mtimeMs",
        "reportHardBlock",
        "legalUrlHardBlock",
        "realUserHardBlock",
        "platformBackendMatrixHardBlock",
        "BACKEND_READY",
        "agentStreamSmokeHardBlock",
        "真实 Agent stream 后端 smoke",
        "finalPackageCompletenessHardBlock",
        "最终安装包不完整",
        "artifactMetadataHardBlock",
        "ISSUES=",
        "finalPackageCompleteness",
        "userActionsHardBlock",
        "人工事项交接包未清零",
        "法律 URL HTTPS/线上验证未通过",
        "App Privacy / Data safety 隐私披露",
        "商店材料完整性检查",
        "商店提交状态台账",
        "商店后台证据收件台账",
        "开发者账号与后台访问台账",
        "域名 HTTPS 与备案台账",
        "H5 法律页线上部署状态",
        "发行产物元数据台账",
        "桌面端发布状态",
        "全端后端能力矩阵",
        "platformBackendMatrix",
        "Desktop Downloads",
        "Desktop Windows Rebuild",
        "desktopDownloadsHardBlock",
        "桌面下载交付包",
        "Windows x64 安全重建/新鲜度校验",
        "当前批次真实用户回收未通过",
        "真实用户测试名册",
        "current-release-scope.json",
        "deferredPlatforms",
    ]:
        assert expected in source


def test_release_package_uses_report_time_for_latest_artifact_dirs():
    for path in [
        "scripts/release_package.mjs",
        "scripts/release_candidate_summary.mjs",
        "scripts/release_readiness_audit.mjs",
        "scripts/release_finalize.mjs",
    ]:
        source = read_text(path)
        assert "latestEntryTime" in source
        assert "report.json" in source
        assert "summary.json" in source
        assert "mtimeMs" in source


def test_desktop_download_bundle_is_prioritized_for_release_assets():
    source = read_text("scripts/release_package.mjs")
    summary = read_text("scripts/release_candidate_summary.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")

    assert "artifacts/desktop-downloads/" in source
    assert "'artifacts/current-downloads'" in source
    assert "latestDesktopBinaryRoots" in source
    assert "isRedundantUserPacketBinary" in source
    assert "desktop-macos-user-packets" in source
    assert "artifacts/desktop-macos-user-packets" in source
    assert "artifacts/desktop-windows-user-packets" in source
    assert "desktopDownloadsHardBlock" in source
    assert "Desktop Downloads" in source
    assert "latestDesktopDownloads" in summary
    assert "latestDesktopWindowsRebuild" in summary
    assert "desktop:build:win:x64:safe -- --verify-current" in summary
    assert "desktop:bundle" in summary
    assert "desktopDownloads" in readiness
    assert "desktopWindowsRebuild" in readiness
    assert "缺少桌面下载交付包" in readiness
    assert "缺少通过的 Windows x64 安全重建/新鲜度校验报告" in readiness


def test_release_readiness_uses_latest_desktop_binary_roots():
    readiness = read_text("scripts/release_readiness_audit.mjs")

    assert "latestDesktopBinaryRoots" in readiness
    assert "uniqueByHash" in readiness
    assert "artifactPriority" in readiness
    assert "isRedundantUserPacketBinary" in readiness
    assert "filesByExt(latestDesktopBinaryRoots, ['.exe', '.msi'])" in readiness
    assert "filesByExt(latestDesktopBinaryRoots, ['.dmg', '.zip'])" in readiness
    assert "filesByExt(['desktop/release', 'artifacts'], ['.exe', '.msi'])" not in readiness
    assert "filesByExt(['desktop/release', 'artifacts'], ['.dmg', '.zip'])" not in readiness


def test_current_batch_defers_ios_harmony_and_tracks_agent_stream():
    summary = read_text("scripts/release_candidate_summary.mjs")
    readiness = read_text("scripts/release_readiness_audit.mjs")

    for expected in [
        "current-release-scope.json",
        "deferredPlatforms",
        "本批次暂停",
        "qa:agent:stream-smoke",
        "latestAgentStreamSmoke",
        "真实 Agent stream 后端 smoke",
    ]:
        assert expected in summary

    for expected in [
        "releaseScope",
        "deferredPlatforms.has('ios')",
        "deferredPlatforms.has('harmony')",
        "configs/release/current-release-scope.json 已将 iOS 延期到后续批次",
        "configs/release/current-release-scope.json 已将鸿蒙延期到后续批次",
        "flow.agent-stream",
        "qa:agent:stream-smoke",
        "agentStreamSmoke",
    ]:
        assert expected in readiness


def test_release_package_notes_expose_hard_blocks_and_compliance_evidence():
    source = read_text("scripts/release_package.mjs")

    for expected in [
        "Legal URL Check",
        "User Action Handoff",
        "Privacy Disclosure",
        "Store Materials",
        "Store Submission Status",
        "Store Evidence Status",
        "Store Account Access",
        "Domain HTTPS",
        "H5 Legal Deploy Status",
        "Artifact Metadata",
        "Desktop Release Status",
        "Platform Backend Matrix",
        "Agent Stream Smoke",
        "Final Package Completeness",
        "Desktop Windows Rebuild",
        "Real User Roster",
        "userActions",
        "tryNowPacket",
        "missingHardBlocks",
        "当前只能作为 GitHub Release 草稿/内部测试证据包",
    ]:
        assert expected in source
