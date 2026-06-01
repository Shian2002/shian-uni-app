import re
from pathlib import Path


BAZI_RESULT_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "bazi-result" / "index.vue"


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
