import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_final_package_preflight_is_wired_and_read_only():
    package_json = json.loads(read_text("package.json"))
    release_check = read_text("scripts/release_check.mjs")
    docs = read_text("docs/release/README.md")
    source = read_text("scripts/final_package_execution_preflight.mjs")

    assert package_json["scripts"]["release:final-preflight"] == "node scripts/final_package_execution_preflight.mjs"
    assert "release:final-preflight" in release_check
    assert "scripts/final_package_execution_preflight.mjs" in release_check
    assert "npm run release:final-preflight" in docs
    assert "默认不安装、不打包" in docs
    assert "execFileSync" not in source
    assert "spawnSync" not in source


def test_final_package_preflight_checks_final_package_inputs():
    source = read_text("scripts/final_package_execution_preflight.mjs")

    for expected in [
        "artifacts', 'final-package-preflight'",
        "FINAL_PACKAGE_PREFLIGHT_STRICT",
        "desktop/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron",
        "desktop/node_modules/@electron/asar/bin/asar.js",
        "macOS .app 最终构建产物",
        "dist/build/h5/index.html",
        "dist/build/app/__uniappview.html",
        "dist/build/app/app-service.js",
        "artifacts/current-downloads/shian-current-windows-x64.exe",
        "expectedConfirm",
        "readyForConfirmedFinalize",
        "hardMissing",
        "softMissing",
        "evidenceIssues",
        "CONFIRM_FINAL_PACKAGE_REFRESH",
    ]:
        assert expected in source


def test_release_finalize_runs_final_preflight_before_builds_and_indexes():
    source = read_text("scripts/release_finalize.mjs")

    for expected in [
        "const strictPreflightEnv = { FINAL_PACKAGE_PREFLIGHT_STRICT: '1' }",
        "['release:final-preflight:pre', ['run', 'release:final-preflight'], strictPreflightEnv]",
        "['artifacts:prune:dry-run:pre', ['run', 'artifacts:prune', '--', '--keep=2']]",
        "['desktop:build:mac:arm64', ['run', 'desktop:build:mac:arm64']]",
        "['release:final-preflight', ['run', 'release:final-preflight'], strictPreflightEnv]",
        "['desktop:build:mac:arm64:final', ['run', 'desktop:build:mac:arm64']]",
        "['release:final-preflight:final', ['run', 'release:final-preflight'], strictPreflightEnv]",
        "['artifacts:prune:dry-run:final', ['run', 'artifacts:prune', '--', '--keep=2']]",
        "finalPackagePreflight: latestDir('artifacts/final-package-preflight')",
        "Final Package Preflight",
    ]:
        assert expected in source

    assert source.index("['release:final-preflight:pre',") < source.index("['release:channel-builds',")
    assert source.index("['release:final-preflight:pre',") < source.index("['artifacts:prune:dry-run:pre',")
    assert source.index("['artifacts:prune:dry-run:pre',") < source.index("['release:channel-builds',")
    assert source.index("['desktop:build:mac:arm64',") < source.index("['desktop:refresh-macos-app-asar',")
    assert source.index("['release:final-package-plan',") < source.index("['release:final-preflight',")
    assert source.index("['release:final-preflight',") < source.index("['release:try-now',")
    assert source.index("['release:final-package-plan:final',") < source.index("['release:final-preflight:final',")
    assert source.index("['desktop:build:mac:arm64:final',") < source.index("['desktop:refresh-macos-app-asar:final',")
    assert source.index("['release:final-preflight:final',") < source.index("['artifacts:prune:dry-run:final',")
    assert source.index("['artifacts:prune:dry-run:final',") < source.index("['release:try-now:final',")
    assert source.index("['release:final-preflight:final',") < source.index("['release:try-now:final',")
