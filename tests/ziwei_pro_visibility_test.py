from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ZIWEI_PAGE = ROOT / "src" / "pages" / "ziwei" / "index.vue"
HOME_PAGE = ROOT / "src" / "pages" / "index" / "index.vue"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_ziwei_page_hides_standalone_horoscope_pro_entry():
    source = _source(ZIWEI_PAGE)

    assert "activeTab === 'horoscope'" not in source
    assert "推运<text" not in source
    assert 'class="tab-badge">PRO' not in source
    assert '@click="ziweiHoroscope"' not in source


def test_ziwei_regular_pan_keeps_flow_capabilities():
    source = _source(ZIWEI_PAGE)

    assert "zwPanResult.value = renderZiweiPan(panData)" in source
    assert "refreshZiweiFlow()" in source
    assert "url: '/api/ziwei/horoscope'" in source
    assert "html += zwTimeline('大限', palaces, periods)" in source
    assert "html += zwYearTimeline(palaces, d)" in source
    assert "html += zwMonthTimeline()" in source
    assert "flowBadges.push(zwFlowPeriodBadge(decadal, '大限', 'decadal'))" in source
    assert "flowBadges.push(zwFlowPeriodBadge(yearly, '流年', 'year'))" in source
    assert "flowBadges.push(zwFlowPeriodBadge(monthly, '流月', 'month'))" in source


def test_home_tool_picker_does_not_offer_ziwei_horoscope_pro():
    source = _source(HOME_PAGE)

    assert "紫微推运 Pro" not in source
    assert "紫微推运" not in source
    assert "紫微斗数" in source
