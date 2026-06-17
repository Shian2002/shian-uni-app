from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_macos_window_uses_native_hidden_titlebar():
    source = read_text("desktop/main.js")

    for expected in [
        "titleBarStyle",
        "hiddenInset",
        "titleBarOverlay",
        "color: '#f1e7d7'",
        "symbolColor: '#5a4424'",
        "height: 36",
        "trafficLightPosition",
        "{ x: 14, y: 9 }",
        "process.platform === 'darwin'",
        "backgroundColor: '#f1e7d7'",
        "SHIAN_DESKTOP_USER_DATA_DIR",
        "app.setPath('userData'",
    ]:
        assert expected in source


def test_desktop_shell_opens_agent_workspace_by_default():
    source = read_text("desktop/main.js")

    for expected in [
        "function getDesktopAppStartUrl(startUrl)",
        "url.hash = '/?app=1'",
        "win.loadURL(getDesktopAppStartUrl(startUrl))",
    ]:
        assert expected in source


def test_desktop_main_has_native_app_lifecycle_menu_and_single_instance():
    source = read_text("desktop/main.js")

    for expected in [
        "Menu",
        "requestSingleInstanceLock",
        "second-instance",
        "mainWindow",
        "createAppMenu",
        "Menu.setApplicationMenu",
        "关于时安解忧屋",
        "退出时安解忧屋",
        "app.setName('时安解忧屋')",
        "role: 'quit'",
        "role: 'minimize'",
        "role: 'zoom'",
    ]:
        assert expected in source


def test_desktop_shell_has_compact_native_workspace_layout():
    source = read_text("src/App.vue")

    for expected in [
        "desktop-native-shell",
        "window.shianDesktop",
        "var isDesktopShell = false",
        "saved = 'light'",
        "-webkit-app-region:drag",
        "-webkit-app-region:no-drag",
        "padding-left:72px",
        "height:36px",
        "padding-top:36px",
        "calc(100dvh - 36px)",
        "--desktop-chrome-bg:#f1e7d7",
        "--desktop-chrome-bg-2:#eadcc7",
        "linear-gradient(180deg",
        "background:var(--desktop-chrome-bg)!important",
        "transform:none",
        "bottom:12px",
    ]:
        assert expected in source
    desktop_shell_block = source.split("html.desktop-native-shell,", 1)[1].split("/* 工具页默认输入态", 1)[0]
    assert "#f7f2ea" not in desktop_shell_block


def test_desktop_smoke_asserts_native_topbar_and_bottom_agent_input():
    source = read_text("scripts/desktop_smoke.mjs")

    for expected in [
        "desktopLayoutMetrics",
        "loginModalMetrics",
        "assertDesktopNativeLayout",
        "assertLoginModalDocked",
        "assertAgentInputDocked",
        "htmlTheme",
        "bodyTheme",
        "桌面 App html 主题不是浅色",
        "桌面 App body 主题不是浅色",
        "桌面顶部栏仍接近纯白",
        "桌面顶部栏不是主题暖米色",
        "桌面登录弹窗未底部对齐",
        "桌面登录弹窗未贴近底部",
        "桌面登录弹窗不是浅色主题",
        "时安agent 对话框未贴近底部",
        "时安agent 对话框跑到中间",
        "homeAiMain.top >= Math.round(metrics.viewport.height * 0.65)",
        "SHIAN_DESKTOP_USER_DATA_DIR",
        "join(artifactDir, 'user-data')",
        "Unauthorized",
    ]:
        assert expected in source
