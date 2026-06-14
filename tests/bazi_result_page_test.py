import re
import json
import subprocess
from pathlib import Path


BAZI_RESULT_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "bazi-result" / "index.vue"
BAZI_INDEX_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "bazi-index" / "index.vue"
BAZI_PRO_VUE = Path(__file__).resolve().parents[1] / "src" / "package-tools" / "bazi-pro" / "index.vue"
BAZI_RESULT_JS = Path(__file__).resolve().parents[1] / "src" / "static" / "js" / "bazi_result.js"
HEPAN_VUE = Path(__file__).resolve().parents[1] / "src" / "package-tools" / "hepan" / "index.vue"
HEPAN_JS = Path(__file__).resolve().parents[1] / "src" / "static" / "js" / "hepan.js"
INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"


def _source():
    return BAZI_RESULT_VUE.read_text(encoding="utf-8")


def _function_body(source, name):
    match = re.search(rf"function {name}\([^)]*\) \{{(?P<body>.*?)\n\}}", source, re.S)
    assert match, f"缺少 {name} 函数"
    return match.group("body")


def _function_source(source, name):
    start = source.find(f"function {name}(")
    assert start >= 0, f"缺少 {name} 函数"
    brace_start = source.find("{", start)
    assert brace_start >= 0
    depth = 0
    for idx in range(brace_start, len(source)):
        char = source[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:idx + 1]
    raise AssertionError(f"{name} 函数括号不完整")


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


def test_bazi_birth_date_selects_keep_natural_order():
    source = BAZI_INDEX_VUE.read_text(encoding="utf-8")

    assert "rotateBaziOptionsAroundAnchor" not in source
    assert "for (var i = 1; i <= 12; i++)" in source
    assert "monthOpts.push({ value: i, label: i + '月' })" in source
    assert "for (var i = 1; i <= maxDay; i++)" in source
    assert "dayOpts.push({ value: i, label: i + '日' })" in source


def test_bazi_mobile_free_paipan_action_stays_visible_before_advanced_options():
    source = BAZI_INDEX_VUE.read_text(encoding="utf-8")

    assert '<text class="tool-tab-main">八字排盘</text><text class="tab-badge free">免费</text>' in source
    assert ".tool-tab-main { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }" in source
    assert ".tab-badge { flex: 0 0 auto;" in source
    assert "⚡ 即时起局" not in source
    assert "⚡ 当前时间" in source

    action_idx = source.find('<view class="wz-action-block">')
    advanced_idx = source.find('<view class="wz-form-group wz-advanced-box">')
    assert action_idx >= 0
    assert advanced_idx >= 0
    assert action_idx < advanced_idx, "手机端主排盘按钮应在高级选项前，避免首屏找不到免费排盘"


def test_bazi_result_refresh_reads_last_params_fallback():
    source = _source()

    assert "function readBaziParamsFromStorage()" in source
    assert "var keys = ['xc_bazi_params', 'xc_bazi_last_params']" in source
    assert "localStorage.getItem(keys[i])" in source
    assert "sessionStorage.setItem('xc_bazi_params', stored)" in source
    assert "params = readBaziParamsFromStorage()" in source
    assert "刷新后没有找到本次排盘参数" in source


def test_bazi_professional_summary_displays_jiaoyun_text():
    source = _source()

    assert '<view class="pro-qiyun-extra" v-if="jiaoyunSummary">{{ jiaoyunSummary }}</view>' in source
    assert "const jiaoyunSummary = computed(() => {" in source
    assert "if (pro && pro.jiaoyun_text) return pro.jiaoyun_text" in source
    assert "if (qyd && qyd.jiao_yun_text) return qyd.jiao_yun_text" in source


def test_bazi_professional_request_prefers_effective_solar_time():
    source = _source()

    birth_solar_idx = source.find("if (d.birth_solar) {")
    birth_params_idx = source.find("} else if (d.birth_params) {")

    assert birth_solar_idx >= 0
    assert birth_params_idx > birth_solar_idx
    assert "var jy = ''" in source
    assert "var jyParts = (d.birth_input || '').match" in source
    assert "if (jy) url += '&jy=' + encodeURIComponent(jy)" in source
    assert "var url = '/api/bazi/shian-pro?y=' + y + '&m=' + m + '&d=' + dd + '&h=' + h + '&mi=' + mi + '&s=' + s" in source


def test_bazi_result_has_wenzhen_style_smart_pillar_chart_tabs():
    source = _source()

    assert "智能四柱图示" in source
    assert "activeGzTab = ref('ganshi')" in source
    for label in ["干支", "流通", "宫位", "六亲"]:
        assert f">{label}</view>" in source
    assert "pro-smart-diagram" in source
    assert "smartRelationRows.top" in source
    assert "smartRelationRows.bottom" in source
    assert "pro-smart-line-end-left" in source
    assert "pro-smart-line-end-right" in source
    assert "leftChar" in source
    assert "rightChar" in source
    assert "offsetPx" in source
    assert "--line-shift" in source
    assert "{{ formatRelationList(proGuanxi.tg) }}" in source
    assert "{{ formatRelationList(proGuanxi.dz) }}" in source
    assert "td.level + td.type + ' ' + relationLabel(raw)" in source
    assert "arr.map(item => relationLabel(item.desc ||" in source
    assert "d.level + d.type + ' ' + relationLabel(raw)" in source
    assert "return `${relationPairText}冲`" in source
    assert "return `${hePairText}合化${m[1]}`" in source
    assert "return `${relationPairText}破`" in source
    assert "return `${relationPairText}自刑`" in source
    assert ".pro-smart-line-row { position: relative; min-height: 25px;" in source
    assert ".pro-smart-lines-bottom { margin-top: 10px; gap: 8px; }" in source
    assert "offsetPx: 0" in source
    assert "tier * 3" not in source
    assert "return `${pairText}拱合${juMap[m[1]] || m[1]}`" in source
    assert "return `${pairText}拱会${found ? found.ju : ''}`" in source
    assert "palaceAxisItems" in source
    assert "kinshipDiagramItems" in source
    assert "pro-palace-map" in source
    assert "pro-kinship-map" in source
    assert "activeGanzhiSetting = ref('relations')" not in source
    assert "ganzhiSettingTabs" not in source
    for label in ["地支藏干", "人元司令", "神煞设置", "命宫身宫", "格局取法", "虚实岁"]:
        assert f"label: '{label}'" not in source
    assert "问真结构" not in source
    assert "pro-gz-setting-panel" not in source
    assert "pro-gz-relation-tag" not in source
    assert "pro-palace-pillar" not in source
    assert "pro-kinship-card" not in source
    assert "求亲" not in source


def test_bazi_relation_labels_put_ganzhi_before_relation_name():
    source = _source()
    relation_label_source = _function_source(source, "relationLabel")
    format_relation_list_source = _function_source(source, "formatRelationList")
    cases = {
        "壬丙相冲": "壬丙冲",
        "辛丙合化水": "丙辛合化水",
        "丙辛合化水": "丙辛合化水",
        "午卯相破": "午卯破",
        "丑辰破": "辰丑破",
        "午午相刑": "午午自刑",
        "辰卯相害": "辰卯害",
        "戌酉害": "酉戌害",
        "甲戊相克": "甲戊克",
        "子丑相合": "子丑合",
        "寅 午 戌 三合火局": "寅午戌三合火局",
        "寅 卯 三会木局(缺辰)": "寅卯拱会木局",
        "寅丑暗合": "寅丑暗合",
        "寅 巳 申 无恩之刑": "寅巳申三刑",
    }
    script = (
        relation_label_source
        + "\n"
        + format_relation_list_source
        + "\nconst cases = "
        + json.dumps(cases, ensure_ascii=False)
        + ";\n"
        + "const out = Object.fromEntries(Object.keys(cases).map(k => [k, relationLabel(k)]));\n"
        + "const listOut = formatRelationList('壬丙相克,丙辛合化水,壬丙相冲,午午相刑,午卯相破');\n"
        + "console.log(JSON.stringify({out, listOut}));\n"
    )
    result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
    payload = json.loads(result.stdout)
    assert payload["out"] == cases
    assert payload["listOut"] == "壬丙克、丙辛合化水、壬丙冲、午午自刑、午卯破"


def test_package_bazi_pro_formats_ganzhi_attention_like_wenzhen_labels():
    source = BAZI_PRO_VUE.read_text(encoding="utf-8")

    assert "{{ formatRelationList(baziData.tg_guanxi) }}" in source
    assert "{{ formatRelationList(baziData.dz_guanxi) }}" in source
    assert "function relationLabel(desc)" in source
    assert "function formatRelationList(source)" in source
    assert "return `${relationPairText}冲`" in source
    assert "return `${relationPairText}破`" in source
    assert "return `${relationPairText}自刑`" in source


def test_static_bazi_result_formats_legacy_relation_renderers():
    source = BAZI_RESULT_JS.read_text(encoding="utf-8")

    assert "function relationLabelBZ(desc)" in source
    assert "function formatRelationListBZ(source)" in source
    assert "${formatRelationListBZ(tgRel)}" in source
    assert "${formatRelationListBZ(dzRel)}" in source
    assert "干${relationLabelBZ(r)}" in source
    assert "支${relationLabelBZ(r)}" in source
    assert "${relationLabelBZ(item.desc || '')}" in source
    assert "${label}${r.type} ${relationLabelBZ(r.desc || '')}" in source
    assert "${relationLabelBZ(r.desc)}</span>" in source
    assert ">${tgRel}<" not in source
    assert ">${dzRel}<" not in source
    assert ">${item.desc}<" not in source
    assert ">${r.desc}<" not in source


def test_hepan_relation_tags_use_forward_ganzhi_relation_labels():
    for path in [HEPAN_VUE, HEPAN_JS]:
        source = path.read_text(encoding="utf-8")
        assert "function relationLabelHepan(desc)" in source
        assert "${relationLabelHepan(r.desc)}</span>" in source
        assert "return `${pairText}拱合${juMap[m[1]] || m[1]}`" in source
        assert "return `${pairText}半合${m[1]}局`" in source
        assert "return `${allText}三刑`" in source
        assert "relationPairText" in source
        assert "${r.desc}</span>" not in source


def test_boot_fallback_prevents_blank_screen_when_app_fails_to_mount():
    source = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="xc-boot-fallback"' in source
    assert "function markBootFailed()" in source
    assert "window.addEventListener('error'" in source
    assert "window.addEventListener('unhandledrejection'" in source
    assert "页面加载异常" in source
