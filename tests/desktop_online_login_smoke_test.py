from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_desktop_shell_proxies_api_to_online_backend():
    source = read_text("desktop/main.js")

    for expected in [
        "SHIAN_DESKTOP_API_TARGET",
        "https://shianjieyouwu.com",
        "proxyApiRequest",
        "pathname === '/api' || pathname.startsWith('/api/')",
        "rewriteSetCookieHeaders",
        "desktop_api_proxy_failed",
    ]:
        assert expected in source


def test_desktop_online_login_smoke_exercises_real_backend_data():
    package_json = read_text("package.json")
    source = read_text("scripts/desktop_online_login_smoke.mjs")

    assert '"desktop:online-login-smoke": "node scripts/desktop_online_login_smoke.mjs"' in package_json
    for expected in [
        "/api/health",
        "/api/login",
        "/api/me",
        "/api/membership",
        "/api/points/log?page=1&per_page=5",
        "/api/comprehensive/options",
        "/api/comprehensive/recommend-tools",
        "/api/comprehensive/guide",
        "/api/comprehensive/conversations",
        "/api/ziwei/info",
        "/api/huangli?date=2024-02-10",
        "/api/bazi/paipan",
        "/api/bazi/shian-pro?y=1990&m=1&d=27&h=10&mi=30&s=1",
        "/api/ziwei/pan",
        "/api/qimen/paipan",
        "/api/meihua/paipan",
        "/api/liuyao/paipan",
        "/api/zeji",
        "/api/records",
        "/api/collections?type=record",
        "SHIAN_DESKTOP_API_TARGET",
        "SHIAN_DESKTOP_USER_DATA_DIR",
        "join(artifactDir, 'user-data')",
        "launchDesktopApp",
        "quitExistingMacosApp",
        "launchPreflight",
        "installedExecutable",
        "pgrep",
        "pending.json",
        "failure.json",
        "attempts: launchAttempts",
        "page.context().cookies",
        "桌面端登录后浏览器上下文没有写入 session cookie",
        "schemaReady",
        "membershipReady",
        "pointsReady",
        "comprehensiveOptionsReady",
        "recommendToolsReady",
        "guideReady",
        "conversationsReady",
        "runCoreBackendChecks",
        "baziPaipanReady",
        "qimenPaipanReady",
        "liuyaoPaipanReady",
        "collectionsReady",
        "nonEmptyArray(comprehensiveOptions.data.llm_models)",
        "nonEmptyArray(comprehensiveOptions.data.reading_modes)",
        "nonEmptyArray(comprehensiveOptions.data.tool_models)",
        "typeof recommendTools.data.estimated_cost === 'number'",
        "['ask', 'recommend'].includes(guideStatus)",
        "桌面端 /api/membership 数据结构异常",
        "桌面端 /api/comprehensive/options 数据结构异常",
    ]:
        assert expected in source
