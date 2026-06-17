import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_final_package_plan_is_wired_as_read_only_planning_step():
    package_json = json.loads(read_text("package.json"))
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")

    assert package_json["scripts"]["release:final-package-plan"] == "node scripts/final_package_refresh_plan.mjs"
    assert "release:final-package-plan" in release_check
    assert "scripts/final_package_refresh_plan.mjs" in release_check
    assert "npm run release:final-package-plan" in docs
    assert "不自动打包、不部署" in docs


def test_final_package_plan_keeps_package_rebuilds_last_and_explicit():
    source = read_text("scripts/final_package_refresh_plan.mjs")

    for expected in [
        "artifacts', 'final-package-plan'",
        "FINAL_PACKAGE_PLAN_STRICT",
        "readyToRunFinalPackageRefresh",
        "videoSafe",
        "lowImpactStatus",
        "artifacts/low-impact-status",
        "npm run release:low-impact-status",
        "记录低影响状态快照",
        "结果只作为风险提示，不阻塞 build-once 阶段",
        "低影响状态快照",
        "missingPackages",
        "Windows EXE",
        "current-release-scope.json",
        "activePlatforms",
        "deferredPlatforms",
        "packageRequired",
        "延期平台本轮不作为缺包阻塞",
        "npm run artifacts:prune -- --keep=2",
        "只生成可清理候选报告",
        "npm run release:package-cleanup-plan -- --keep=2",
        "打包前旧安装包清理预估",
        "npm run mobile:toolchain-plan",
        "刷新移动端工具链准备计划",
        "npm run build:app && npm run mobile:api-evidence",
        "npm run desktop:build:mac:arm64 && npm run desktop:refresh-macos-app-asar && npm run desktop:make-macos-dmg",
        "ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/ npm run desktop:build:win:x64:safe -- --skip-h5",
        "国内 Electron 镜像",
        "npm run android:shell:debug-apk",
        "packageRequired('ios')",
        "packageRequired('harmony')",
        "iOS/鸿蒙后续批次再补",
        "CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5",
        "npm run release:try-now && npm run release:package",
        "userMustDoLast",
        "deleteCandidates",
        "desktop/release",
        "desktopNodeModulesMB",
        "npmCacheMB",
        ".npm-cache",
        "artifacts/current-downloads",
    ]:
        assert expected in source


def test_final_package_plan_does_not_execute_build_commands():
    source = read_text("scripts/final_package_refresh_plan.mjs")

    assert "execFileSync" not in source
    assert "spawnSync" not in source
    assert "commandStep(" in source
    assert "writeFileSync(join(outDir, 'report.json')" in source
