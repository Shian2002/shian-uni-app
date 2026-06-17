import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_progress_board_is_wired_into_release_workflow():
    package_json = json.loads(read_text("package.json"))
    source = read_text("scripts/release_progress_board.mjs")
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")

    assert package_json["scripts"]["release:progress"] == "node scripts/release_progress_board.mjs"
    assert "release:progress" in release_check
    assert "release:progress" in docs

    for expected in [
        "当前发行进度表",
        "安装包优先",
        "后端请求",
        "真机证据",
        "最后需要你或外部后台处理",
        "release-progress-latest.json",
        "artifacts/RELEASE_PROGRESS.md",
        "current-release-scope.json",
        "deferredPlatforms",
        "current-downloads/manifest.json",
        "agent-stream-smoke",
        "missingHardBlocks",
        "finalPackagePlan",
        "externalHandoff",
        "releaseFinalizePlan",
        "lowImpactStatus",
        "最终刷新计划",
        "外部回传任务",
        "低影响状态",
        "所有回传到齐后 15-30 分钟",
    ]:
        assert expected in source


def test_release_progress_board_keeps_user_work_last():
    source = read_text("scripts/release_progress_board.mjs")

    assert source.index("packages.current") < source.index("backend.requests")
    assert source.index("backend.requests") < source.index("device.real-machine")
    assert source.index("device.real-machine") < source.index("handoff.external")
    assert source.index("handoff.external") < source.index("stores.compliance")
    assert source.index("stores.compliance") < source.index("final.refresh")
    assert "这些是最后处理项，不抢在安装包和功能验证前面。" in source
