import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_platform_backend_matrix_is_wired_and_non_packaging():
    package_json = json.loads(read_text("package.json"))
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")

    assert package_json["scripts"]["platform:backend-matrix"] == "node scripts/platform_backend_matrix.mjs"
    assert "platform:backend-matrix" in release_check
    assert "scripts/platform_backend_matrix.mjs" in release_check
    assert "npm run platform:backend-matrix" in docs
    assert "默认不打包、不部署" in docs


def test_platform_backend_matrix_covers_all_platforms_and_backend_modes():
    source = read_text("scripts/platform_backend_matrix.mjs")

    for expected in [
        "artifacts', 'platform-backend-matrix'",
        "PLATFORM_BACKEND_MATRIX_STRICT",
        "latestDir('artifacts/desktop-windows-rebuild', 'report.json')",
        "latestDir('artifacts/agent-stream-smoke', 'report.json')",
        "windowsPackageFreshness",
        "Windows 安装器不是最新 H5 构建后的产物",
        "packageReady: Boolean(files.windowsExe) && freshness.windows.fresh",
        "real-electron-online-smoke",
        "shared-electron-online-smoke",
        "agentStreamReady",
        "共享 Agent stream 真实后端证据缺失或未通过",
        "runtime-config-plus-shared-contract",
        "runtime-config-only",
        "shared-online-contract",
        "shian-current-macos-arm64.dmg",
        "shian-current-windows-x64.exe",
        "shian-current-android-debug.apk",
        "shian-current-android-debug.aab",
        "iOS IPA/TestFlight 构建产物缺失",
        "鸿蒙 HAP/AppGallery 构建产物缺失",
        "fileInfo(item?.path || '')",
        "metadataReady(row)",
        "metadataValue(row, field)",
        "metadataEvidenceReady(row, field)",
        "row?.metadata?.[field]",
        "row?.readiness === 'ready'",
        "backendContract",
        "agentStream",
        "comprehensive-recommend-tools",
        "comprehensive-conversations",
        "bazi-paipan",
        "bazi-shian-pro",
        "ziwei-pan",
        "qimen-paipan",
        "meihua-paipan",
        "liuyao-paipan",
        "zeji",
        "records",
        "collections",
        "coreFunctions",
        "最后必须人工处理",
        "CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh",
    ]:
        assert expected in source


def test_release_current_index_includes_platform_backend_matrix_and_real_files():
    source = read_text("scripts/release_current_index.mjs")

    for expected in [
        "latestDir('artifacts/platform-backend-matrix', 'report.json')",
        "platformBackendMatrixGenerated",
        "全端后端能力矩阵",
        "全端后端矩阵",
        "fileInfoFromManifest(currentDownloads, 'shian-current-windows-x64.exe')",
        "latestDir('artifacts/desktop-windows-rebuild', 'report.json')",
        "windowsInstallerFresh",
        "Windows 新鲜度",
        "(currentDownloads.files || []).every((file) => Boolean(fileInfo(file.path)))",
    ]:
        assert expected in source
