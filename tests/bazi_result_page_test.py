import re
from pathlib import Path


BAZI_RESULT_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "bazi-result" / "index.vue"
BAZI_INDEX_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "bazi-index" / "index.vue"
INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"


def _source():
    return BAZI_RESULT_VUE.read_text(encoding="utf-8")


def _function_body(source, name):
    match = re.search(rf"function {name}\([^)]*\) \{{(?P<body>.*?)\n\}}", source, re.S)
    assert match, f"缺少 {name} 函数"
    return match.group("body")


def test_bazi_result_defines_qiyun_max_liuyue_before_use():
    source = _source()

    definition = source.find("function getQiYunMaxLiuYue")
    call_sites = [
        source.find("var _maxMonth = getQiYunMaxLiuYue(d)"),
        source.find("var _maxM = getQiYunMaxLiuYue(data)"),
    ]

    assert definition >= 0, "缺少 getQiYunMaxLiuYue 定义"
    assert all(site > definition for site in call_sites), "getQiYunMaxLiuYue 应先定义再调用，避免运行时未定义引用"
    assert "getQiYunMonth(d)" in _function_body(source, "getQiYunMaxLiuYue")


def test_bazi_error_state_has_explicit_home_navigation_handler():
    source = _source()

    assert '<view class="btn-retry" @tap="goHome">返回首页</view>' in source
    go_home = _function_body(source, "goHome")

    assert "uni.switchTab" in go_home
    assert "url: '/pages/index/index'" in go_home
    assert "location.hash = '#/pages/index/index'" in go_home
    assert "navigateBack" not in go_home


def test_bazi_return_paipan_goes_to_bazi_free_tab_not_marketing_home():
    source = _source()

    assert '<view class="tab-btn tab-return-btn" @tap="goBaziHome">↩ 返回排盘</view>' in source
    go_bazi_home = _function_body(source, "goBaziHome")

    assert "window.location.hash = '#/pages/bazi-index/index?tab=free'" in go_bazi_home
    assert "sessionStorage.setItem('_nav_query', 'tab=free')" in go_bazi_home
    assert "sessionStorage.removeItem('xc_bazi_params')" in go_bazi_home
    assert "location.hash = '#/pages/index/index'" not in go_bazi_home
    assert "url: '/pages/index/index'" not in go_bazi_home
    assert "setTimeout" not in go_bazi_home


def test_bazi_paipan_persists_last_params_for_refresh_recovery():
    source = BAZI_INDEX_VUE.read_text(encoding="utf-8")

    assert "function persistBaziResultParams(data)" in source
    assert "sessionStorage.setItem('xc_bazi_params', raw)" in source
    assert "localStorage.setItem('xc_bazi_last_params', raw)" in source
    assert source.count("persistBaziResultParams(data)") >= 3


def test_bazi_result_refresh_reads_last_params_fallback():
    source = _source()

    assert "function readBaziParamsFromStorage()" in source
    assert "var keys = ['xc_bazi_params', 'xc_bazi_last_params']" in source
    assert "localStorage.getItem(keys[i])" in source
    assert "sessionStorage.setItem('xc_bazi_params', stored)" in source
    assert "params = readBaziParamsFromStorage()" in source
    assert "刷新后没有找到本次排盘参数" in source


def test_boot_fallback_prevents_blank_screen_when_app_fails_to_mount():
    source = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="xc-boot-fallback"' in source
    assert "function markBootFailed()" in source
    assert "window.addEventListener('error'" in source
    assert "window.addEventListener('unhandledrejection'" in source
    assert "页面加载异常" in source
