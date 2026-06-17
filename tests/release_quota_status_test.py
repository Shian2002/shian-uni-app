from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_quota_status_is_wired_and_documented():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")

    assert '"release:quota-status": "node scripts/release_quota_status.mjs"' in package_json
    assert "release:quota-status" in release_check
    assert "release:quota-status" in docs


def test_quota_status_reads_existing_evidence_without_rebuilding():
    source = read_text("scripts/release_quota_status.mjs")

    for expected in [
        "低成本状态包",
        "不构建、不打包、不启动 App",
        "artifacts/try-now/latest-manifest.json",
        "artifacts/desktop-macos-local-install",
        "artifacts/desktop-macos-lifecycle",
        "remainingHardBlocks",
        "function remainingHardBlocks",
        "release package manifest 尚未可读",
        "missingHardBlocks 字段",
        "quotaSafeNextCommands",
        "avoidUntilNeeded",
        "CODEX_WEEKLY_QUOTA_PERCENT",
        "weeklyQuotaPercent",
        "Codex Pro 周额度",
        "quotaLevel",
        "suggestedMode",
        "evidence-only",
        "low/evidence-only",
        "trim() === ''",
    ]:
        assert expected in source

    for forbidden in [
        "child_process",
        "execFileSync",
        "spawn",
    ]:
        assert forbidden not in source
