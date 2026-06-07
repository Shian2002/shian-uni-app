from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ZIWEI_PAGE = ROOT / "src" / "pages" / "ziwei" / "index.vue"
HOME_PAGE = ROOT / "src" / "pages" / "index" / "index.vue"
TOP_NAV = ROOT / "src" / "components" / "TopNav.vue"
PAGES_JSON = ROOT / "src" / "pages.json"
USER_MANAGEMENT_PAGE = ROOT / "src" / "pages" / "user-management" / "index.vue"


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


def test_ziwei_pan_can_save_user_profile():
    source = _source(ZIWEI_PAGE)

    assert "保存档案" in source
    assert "source: 'ziwei_pan'" in source
    assert "saveZiweiPanProfile(panData)" in source


def test_user_management_page_is_registered_and_linked():
    nav = _source(TOP_NAV)
    pages = _source(PAGES_JSON)

    assert "pages/user-management/index" in pages
    assert '"pagePath": "pages/user-management/index"' in pages
    assert "档案列表" in nav
    assert "#/pages/user-management/index" in nav
    assert "'/pages/user-management/index'" in nav
    assert "'pages/user-management/index'" in nav
    assert "'/pages/user-management/index': '档案列表'" in nav
    assert '"navigationBarTitleText": "档案列表"' in pages


def test_user_management_content_sits_above_background_layer():
    source = _source(USER_MANAGEMENT_PAGE)

    assert ".user-page-wrap" in source
    assert "z-index: 1;" in source
    assert "档案列表" in source
    assert "档案信息" in source


def test_user_management_search_input_is_focusable_and_controlled():
    source = _source(USER_MANAGEMENT_PAGE)

    assert 'ref="searchInputRef"' in source
    assert ':value="searchText"' in source
    assert '@input="onSearchInput"' in source
    assert '@confirm="onSearchInput"' in source
    assert '@tap.stop="focusSearch"' in source
    assert "function onSearchInput(e)" in source
    assert "function focusSearch()" in source
    assert ".search-input :deep(.uni-input-input)" in source
    assert "pointer-events: none;" in source


def test_top_nav_closes_login_modal_before_navigation():
    nav = _source(TOP_NAV)

    assert "closeBlockingOverlaysBeforeNav()" in nav
    assert "document.querySelectorAll('#topnavLoginModal')" in nav


def test_user_management_uses_compact_two_column_cards():
    source = _source(USER_MANAGEMENT_PAGE)

    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in source
    assert "compactBirthLine(profile)" in source
    assert "shortAddr(profile)" in source
    assert ">八字</view>" in source
    assert ">紫微</view>" in source
    assert ">agent</view>" in source
