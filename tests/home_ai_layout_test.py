import re
from pathlib import Path


INDEX_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "index" / "index.vue"
TOP_NAV_VUE = Path(__file__).resolve().parents[1] / "src" / "components" / "TopNav.vue"
QIMEN_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "qimen" / "index.vue"


def _source():
    return INDEX_VUE.read_text(encoding="utf-8")


def test_home_ai_reading_mode_claims_hero_space_without_locking_page_scroll():
    source = _source()

    assert ".hero-home.chat-active.reading-active .hero-brand" in source
    assert ".hero-home.chat-active.reading-active .home-ai-console.has-chat" in source
    assert "min-height: calc(100dvh - 60px - var(--home-ai-dock-space));" in source
    assert "setHomeFixedPage(true)" not in source
    scroll_fn = re.search(
        r"function scrollComprehensiveChatToBottom\(behavior, force\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert scroll_fn, "缺少综合 AI 聊天滚动函数"
    assert "scrollingElement" in source
    assert "window.scrollTo" not in scroll_fn.group("body")
    assert "scrollIntoView" not in scroll_fn.group("body")


def test_home_ai_input_is_compressed_and_chat_has_mobile_bottom_buffer():
    source = _source()

    assert "--home-ai-dock-space" in source
    assert "--home-ai-chat-bottom-buffer" in source
    assert "max-height: 64px" in source
    assert "max-height: 58px" in source
    assert re.search(
        r"\.home-ai-console\.has-chat \.home-ai-chat \{[^}]*padding-bottom: var\(--home-ai-chat-bottom-buffer\)",
        source,
        re.S,
    )
    assert re.search(
        r"\.home-ai-console\.has-chat \.home-ai-chat \{[^}]*scroll-padding-bottom: var\(--home-ai-chat-bottom-buffer\)",
        source,
        re.S,
    )


def test_home_ai_auto_follow_only_when_near_bottom():
    source = _source()

    assert "const HOME_AI_NEAR_BOTTOM_PX = 140" in source
    near_bottom = re.search(
        r"function isComprehensiveChatNearBottom\(\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert near_bottom, "缺少综合 AI 聊天接近底部判断"
    assert "HOME_AI_NEAR_BOTTOM_PX" in near_bottom.group("body")
    scroll_fn = re.search(
        r"function scrollComprehensiveChatToBottom\(behavior, force\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert scroll_fn, "缺少综合 AI 聊天滚动函数"
    assert "if (!force && !shouldAutoFollowChat.value) return" in scroll_fn.group("body")


def test_top_nav_distinguishes_agent_query_from_plain_home():
    source = TOP_NAV_VUE.read_text(encoding="utf-8")
    index_source = _source()

    assert 'data-href="#/?app=1"' in source
    assert "function getCurrentRouteWithQuery()" in source
    assert "fullRoute === fullTarget" in source
    assert "window.__xcHomeMode === 'app'" in source
    assert "xc-home-mode-changed" in source
    assert "window.__xcHomeMode = active ? 'marketing' : 'app'" in index_source
    assert "if (href === '#/') target = '/pages/index/index'" not in source


def test_top_nav_switches_back_to_home_before_rendering_agent_from_non_tab_pages():
    source = TOP_NAV_VUE.read_text(encoding="utf-8")

    assert "var routeBeforeNav = getCurrentRoute()" in source
    assert "var routeBeforeIsTab = TAB_PATHS.indexOf(routeBeforeNav) > -1 || routeBeforeNav === '/pages/index/index'" in source
    assert "var shouldSwitchForAgentHome = wantsAppHome && !routeBeforeIsTab" in source
    assert "if (wantsAppHome && !shouldSwitchForAgentHome)" in source
    assert "if (shouldSwitchForAgentHome)" in source
    assert "uni.switchTab({" in source
    assert "url: '/pages/index/index'" in source
    assert "setTimeout(renderAgentHome, 260)" in source
    assert re.search(
        r"if \(shouldSwitchForAgentHome\) \{(?P<body>.*?)\n\s*\}\s*catch\(_\) \{\}\n\s*renderAgentHome\(\)",
        source,
        re.S,
    ), "非 tab 页进入时安agent必须先 switchTab 并 return，避免先改 URL 导致页面栈卡死"


def test_top_nav_primary_buttons_are_not_double_handled_by_global_delegate():
    source = TOP_NAV_VUE.read_text(encoding="utf-8")

    assert "function goAsync(hash, event)" in source
    assert "setTimeout(function() { go(hash) }, 0)" in source
    assert "window.__topNavGoAsync = function(event, hash) { return goAsync(hash, event) }" in source
    assert '@click="goAsync(\'#/?app=1\', $event)"' in source
    assert "return window.__topNavGoAsync(event, '#/pages/qimen/index?tab=free')" in source
    assert "return window.__topNavGoAsync(event, '#/pages/bazi-index/index?tab=free')" in source
    assert "if (el.classList && el.classList.contains('nav-btn')) return" in source
    delegate = re.search(
        r"document\.addEventListener\('click', function\(e\) \{(?P<body>.*?)\n\s*\}, true\)",
        source,
        re.S,
    )
    assert delegate, "缺少顶部导航全局点击代理"
    assert delegate.group("body").find("contains('nav-btn')) return") < delegate.group("body").find("if (el.dataset && el.dataset.href)")


def test_top_nav_waits_for_switch_tab_before_rendering_from_non_tab_pages():
    source = TOP_NAV_VUE.read_text(encoding="utf-8")

    assert "if (!routeBeforeIsTab) {" in source
    assert "setTimeout(finishTargetTab, 30)" in source
    assert "setTimeout(finishTargetTab, 180)" in source
    non_tab_branch = re.search(
        r"if \(!routeBeforeIsTab\) \{(?P<body>.*?)\n\s*\}\n\s*uni\.switchTab",
        source,
        re.S,
    )
    assert non_tab_branch, "非 tab 页切 tab 必须单独分支，避免提前兜底渲染导致空白卡死"
    assert "return" in non_tab_branch.group("body")
    assert "setTimeout(renderTargetTab, 60)" not in non_tab_branch.group("body")


def test_home_ai_summary_tab_is_available_during_streaming():
    source = _source()

    assert ':show-summary="msg.role === \'assistant\' && (!!msg.content || !!msg._streaming)"' in source
    assert "msg.content || msg._streaming" in source
    assert "setActiveArtifact(aiIndex, '__summary__')" in source


def test_profile_sheet_scrolls_full_quick_create_form_on_mobile():
    source = _source()

    assert '<view class="profile-sheet-scroll">' in source
    assert re.search(r"\.profile-sheet-panel \{[^}]*overflow: hidden", source, re.S)
    assert re.search(r"\.profile-sheet-scroll \{[^}]*overflow-y: auto", source, re.S)
    assert re.search(r"\.profile-sheet-scroll \{[^}]*-webkit-overflow-scrolling: touch", source, re.S)
    assert source.find('class="profile-quick-create"') < source.find('class="profile-options"')
    assert ".profile-options { overflow: visible;" in source
    assert not re.search(r"^\s*\.sheet-actions \{[^}]*position: sticky", source, re.M | re.S)
    assert "请补全出生信息后再解读" in source
    assert "请补全出生时间后再解读" not in source
    assert "请填写出生地" not in source
    assert "birthPlacePrecision: birthAddr ? 'known' : 'unknown'" in source
    assert re.search(r"\.quick-save \{[^}]*box-sizing: border-box", source, re.S)


def test_question_based_tools_do_not_force_birth_profile_completion():
    source = _source()

    assert "{ id: 'qimen', name: '奇门遁甲', cost: 3, needs_profile: false }" in source
    assert "const needsExactTime = selectedToolModels.value.some(id => id === 'bazi' || id === 'ziwei')" in source
    assert "奇门、六爻、梅花或塔罗先看具体问题" in source


def test_quick_birth_select_options_keep_natural_order():
    source = _source()

    assert "rotateOptionsAroundAnchor" not in source
    assert "for (let y = current; y >= current - 120; y--) years.push(y)" in source
    assert "const quickMonthOptions = computed(() => Array.from({ length: 12 }, (_, i) => i + 1))" in source
    assert "return Array.from({ length: maxDay }, (_, i) => i + 1)" in source
    assert 'class="quick-datetime-row quick-datetime-all"' in source
    assert "quick-datetime-date" not in source
    assert "quick-datetime-time" not in source
    assert re.search(r"\.quick-datetime-all \{[^}]*grid-template-columns: minmax\(68px, 1\.2fr\) repeat\(4, minmax\(48px, 0\.9fr\)\)", source, re.S)
    assert '@change="onQuickBirthPartChange(\'birthYear\', $event)"' in source
    assert '@change="onQuickBirthPartChange(\'birthMonth\', $event)"' in source
    assert '@change="onQuickBirthPartChange(\'birthDay\', $event)"' in source
    assert '@change="onQuickBirthPartChange(\'birthHour\', $event)"' in source
    assert '@change="onQuickBirthPartChange(\'birthMinute\', $event)"' in source
    assert '<option value="">时</option>' in source
    assert '<option value="">分</option>' in source
    assert "birthHour: ''" in source
    assert "birthMinute: ''" in source
    assert "quickProfileForm.birthHour = ''" in source
    assert "quickProfileForm.birthMinute = ''" in source
    assert "quickNow" not in source
    assert "const missingTime = quickProfileForm.birthHour === '' || quickProfileForm.birthMinute === ''" in source
    assert "birthTimePrecision: quickProfileForm.timeUnknown || quickProfileForm.birthHour === '' || quickProfileForm.birthMinute === '' ? 'date_unknown_time' : 'datetime'" in source
    assert "function quickSelectValue(e)" in source
    assert "function onQuickDistrictChange(e)" in source


def test_qimen_free_json_copy_is_member_only_and_uses_backend_pan_type_values():
    source = QIMEN_VUE.read_text(encoding="utf-8")

    assert 'v-if="qfResult && qfJsonCopyAllowed"' in source
    assert "function copyQimenJson()" in source
    assert "JSON.stringify(qfRawResult.value, null, 2)" in source
    assert "const qimenPanTypeValues = [2]" in source
    assert "['拆补法', '置闰法']" not in source
