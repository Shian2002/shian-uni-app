import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_current_index_is_wired_and_covers_current_try_now_state():
    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    source = (ROOT / "scripts" / "release_current_index.mjs").read_text(encoding="utf-8")

    assert package_json["scripts"]["release:current-index"] == "node scripts/release_current_index.mjs"
    assert "latestDir('artifacts/try-now', 'manifest.json')" in source
    assert "latestDir('artifacts/release-packages', 'upload-manifest.json')" in source
    assert "latestDir('artifacts/external-handoff', 'manifest.json')" in source
    assert "latestDir('artifacts/release-user-actions', 'report.json')" in source
    assert "latestDir('artifacts/desktop-smoke', 'report.json')" in source
    assert "latestDir('artifacts/desktop-online-login-smoke', 'report.json')" in source
    assert "latestDir('artifacts/agent-stream-smoke', 'report.json')" in source
    assert "latestDir('artifacts/desktop-windows-rebuild', 'report.json')" in source
    assert "latestDir('artifacts/mobile-api-evidence', 'manifest.json')" in source
    assert "latestDir('artifacts/mobile-app-resource-packets', 'manifest.json')" in source
    assert "latestDir('artifacts/platform-backend-matrix', 'report.json')" in source
    assert "artifacts/current-downloads" in source
    assert "latestDir('artifacts/app-icons', 'report.json')" in source
    assert "latestDir('artifacts/artifact-prune', 'report.json')" in source
    assert "latestDir('artifacts/h5-legal-deploy-status', 'report.json')" in source
    assert "RELEASE_CURRENT_INDEX_STRICT" in source
    assert "if (strict && !index.passed) process.exit(1)" in source
    assert "macosDmg" in source
    assert "windowsInstaller" in source
    assert "androidDebugApk" in source
    assert "mobileAppResourcePacket?.storeIcon?.path" in source
    assert "mobileApiEvidencePassed" in source
    assert "currentDownloadsPassed" in source
    assert "稳定下载入口" in source
    assert "shian-current-macos-arm64.dmg" in source
    assert "shian-current-windows-x64.exe" in source
    assert "移动端 API 后端请求证据" in source
    assert "evidenceSummary" in source
    assert "证据摘要" in source
    assert "macOS 原生窗口" in source
    assert "积分/会员" in source
    assert "时安 agent" in source
    assert "Agent 流式真实后端" in source
    assert "agentStreamSmokePassed" in source
    assert "conversationId" in source
    assert "usedCredit" in source
    assert "coreBackendCoverage" in source
    assert "核心功能接口" in source
    assert "bazi-paipan" in source
    assert "ziwei-pan" in source
    assert "qimen-paipan" in source
    assert "meihua-paipan" in source
    assert "liuyao-paipan" in source
    assert "zeji" in source
    assert "records" in source
    assert "collections" in source
    assert "移动端后端请求能力" in source
    assert "全端后端能力矩阵" in source
    assert "全端后端矩阵" in source
    assert "platformBackendMatrixGenerated" in source
    assert "fileInfoFromManifest" in source
    assert "windowsPackageFreshness" in source
    assert "windowsInstallerFresh" in source
    assert "Windows 新鲜度" in source
    assert "Windows 安装器不是最新 H5 构建后的产物" in source
    assert "legalDeploy" in source
    assert "legalDeploySummary" in source
    assert "onlineLegalPage" in source
    assert "onlineIcpFooter" in source
    assert "report?.localLegalChunk?.path" in source
    assert "report?.online?.deployedLegalPage" in source
    assert "report?.online?.deployedIcpFooter" in source
    assert "H5 法律页" in source
    assert "需要你明确批准后才能做" in source
    assert "CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh" in source
    assert "checkByName" in source
    assert "comprehensive-recommend-tools" in source
    assert "userMustDoLast" in source
    assert "remainingHardBlocks" in source
    assert "CURRENT_RELEASE_INDEX.md" in source
