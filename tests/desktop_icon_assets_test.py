import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_desktop_builder_uses_project_logo_icons():
    package_json = json.loads(read_text("desktop/package.json"))
    build = package_json["build"]

    assert "assets/**/*" in build["files"]
    assert build["mac"]["icon"] == "assets/icon.icns"
    assert build["win"]["icon"] == "assets/icon.ico"

    for icon_path in [
        "desktop/assets/icon.png",
        "desktop/assets/icon.icns",
        "desktop/assets/icon.ico",
    ]:
        path = ROOT / icon_path
        assert path.exists(), f"{icon_path} missing"
        assert path.stat().st_size > 1024, f"{icon_path} is unexpectedly small"


def test_desktop_window_has_runtime_icon_without_touching_login_logic():
    main_js = read_text("desktop/main.js")
    docs = read_text("docs/release/desktop-build-evidence.md")

    assert "assets', 'icon.png'" in main_js
    assert "icon: fs.existsSync(desktopIcon) ? desktopIcon : undefined" in main_js
    assert "当前登录仍复用线上 H5/后端现有登录逻辑" in docs
