import re
from pathlib import Path


LIUYAO_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "liuyao" / "index.vue"


def _source():
    return LIUYAO_VUE.read_text(encoding="utf-8")


def test_liuyao_result_uses_symmetric_double_column_layout():
    source = _source()

    assert "--ly-side-width" in source
    assert "--ly-center-gap" in source
    assert "grid-template-columns: var(--ly-side-width) var(--ly-center-gap) var(--ly-side-width)" in source
    assert ".ly-ben-bian-top" in source
    assert ".ly-paired-row" in source
    assert "grid-template-columns: 1fr auto 1fr" not in source
    assert ".ly-row-bian-side { padding-left:" not in source


def test_liuyao_bian_rows_keep_yao_position_information():
    source = _source()

    bian_info = re.search(
        r"html \+= '<div class=\"ly-paired-bian-info\">'(?P<body>.*?)html \+= '</div>'",
        source,
        re.S,
    )
    assert bian_info, "缺少变卦信息区渲染"
    assert "${bian.name}" in bian_info.group("body")


def test_liuyao_markers_remain_inline_with_each_paired_row():
    source = _source()

    assert "position: absolute" not in re.search(
        r"/\* ═══ 六爻纳甲排盘结果样式 ═══ \*/(?P<body>.*?)/\* AI进度条/结果/开关 \*/",
        source,
        re.S,
    ).group("body")
    assert ".ly-yao-tags-left { display: flex; align-items: center;" in source
    assert ".ly-row-bian-side .ly-yao-tags-left { width:" not in source
