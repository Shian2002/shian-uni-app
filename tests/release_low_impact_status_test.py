from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_low_impact_status_is_wired_into_release_surface():
    package_json = read_text("package.json")
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")

    assert '"release:low-impact-status": "node scripts/release_low_impact_status.mjs"' in package_json
    assert "release:low-impact-status" in release_check
    assert "release:low-impact-status" in docs
    assert "看视频" in docs


def test_low_impact_status_only_checks_existing_state():
    source = read_text("scripts/release_low_impact_status.mjs")

    for expected in [
        "低影响工作状态",
        "看视频期间使用",
        "不构建、不打包、不下载、不启动预览",
        "videoSafe",
        "heavyProcessRules",
        "hbuilderx-pack",
        "hbuilderx-plugin-install",
        "xcode-download",
        "uni-app-build",
        "desktop-build",
        "preview-server",
        "release:low-impact-status",
        "release:quota-status",
        "deferUntilVideoEnds",
        "artifacts/current-downloads/manifest.json",
        "artifacts/current-index-latest.json",
    ]:
        assert expected in source

    for forbidden in [
        "execFileSync('npm'",
        'execFileSync("npm"',
        "execFileSync('brew'",
        'execFileSync("brew"',
        "execFileSync('/Applications/HBuilderX.app/Contents/MacOS/cli'",
        'execFileSync("/Applications/HBuilderX.app/Contents/MacOS/cli"',
        "execFileSync('npx'",
        'execFileSync("npx"',
        "kill ",
        "app quit",
    ]:
        assert forbidden not in source
