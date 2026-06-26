import re
import json
from pathlib import Path


INDEX_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "index" / "index.vue"
APP_VUE = Path(__file__).resolve().parents[1] / "src" / "App.vue"
TOP_NAV_VUE = Path(__file__).resolve().parents[1] / "src" / "components" / "TopNav.vue"
QIMEN_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "qimen" / "index.vue"
PROFILE_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "profile" / "index.vue"
VITE_CONFIG = Path(__file__).resolve().parents[1] / "vite.config.js"
PACKAGE_JSON = Path(__file__).resolve().parents[1] / "package.json"
SRC_MANIFEST = Path(__file__).resolve().parents[1] / "src" / "manifest.json"
PUBLIC_MANIFEST = Path(__file__).resolve().parents[1] / "public" / "manifest.json"
INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"
ONLINE_LOGIN_DEV_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "dev_h5_online_login.mjs"
ONLINE_LOGIN_SMOKE_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "local_online_login_smoke.mjs"
AUDIT_ACCOUNT_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_account_preflight.mjs"
AUDIT_ACCOUNT_SEED_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seed_audit_account_assets.py"
LOGIN_EVIDENCE_DOC = Path(__file__).resolve().parents[1] / "docs" / "release" / "login-agent-entry-evidence.md"


def _source():
    return INDEX_VUE.read_text(encoding="utf-8")


def test_android_browser_brand_identity_uses_shian_name():
    src_manifest = json.loads(SRC_MANIFEST.read_text(encoding="utf-8"))
    public_manifest = json.loads(PUBLIC_MANIFEST.read_text(encoding="utf-8"))
    index_html = INDEX_HTML.read_text(encoding="utf-8")
    top_nav = TOP_NAV_VUE.read_text(encoding="utf-8")
    app_vue = APP_VUE.read_text(encoding="utf-8")

    assert src_manifest["name"] == "时安解忧屋"
    assert public_manifest["name"] == "时安解忧屋"
    assert public_manifest["short_name"] == "时安解忧屋"
    assert '<meta name="application-name" content="时安解忧屋" />' in index_html
    assert '<meta name="apple-mobile-web-app-title" content="时安解忧屋" />' in index_html
    assert "青囊八字" not in index_html
    assert "'/pages/qimen/index': '时安解忧屋｜奇门遁甲'" in top_nav
    assert "'/pages/bazi-index/index': '时安解忧屋｜八字排盘'" in top_nav
    assert "function _syncDocumentTitle(hash)" in app_vue
    assert "'/pages/qimen/index': '时安解忧屋｜奇门遁甲'" in app_vue
    assert "document.title = _titleForHash(hash)" in app_vue


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


def test_home_ai_composer_is_forced_to_viewport_bottom_by_global_shell_styles():
    app_source = Path(__file__).resolve().parents[1].joinpath("src", "App.vue").read_text(encoding="utf-8")

    fixed_blocks = re.findall(
        r"body(?:\.desktop-native-shell)?\.home-fixed-page(?:\:not\(\:has\(\.home-ai-console\.has-chat\)\))? \.home-ai-main\{(?P<body>.*?)\n\}",
        app_source,
        re.S,
    )
    assert fixed_blocks, "缺少首页 AI 输入框的全局底部兜底样式"
    assert any("position:fixed!important" in block for block in fixed_blocks)
    assert any("top:auto!important" in block for block in fixed_blocks)
    assert any("left:50%!important" in block for block in fixed_blocks)
    assert any("right:auto!important" in block for block in fixed_blocks)
    assert any("transform:translateX(-50%)!important" in block for block in fixed_blocks)
    assert "html.home-fixed-page body .home-ai-main" in app_source
    assert "body.desktop-native-shell.home-fixed-page .home-ai-main" in app_source
    assert "bottom:max(12px,calc(env(safe-area-inset-bottom) + 10px))!important" in app_source
    for block in fixed_blocks:
        assert "top:50%!important" not in block
        assert "translate(-50%,-50%)!important" not in block


def test_marketing_login_modal_is_also_forced_to_bottom():
    source = _source()

    host_modal = re.search(
        r"\.marketing-auth-host :deep\(\.modal-overlay\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert host_modal, "营销页登录 host 缺少弹窗底部兜底样式"
    assert "align-items: flex-end !important" in host_modal.group("body")
    assert "justify-content: center !important" in host_modal.group("body")
    assert "padding-bottom: max(18px, calc(env(safe-area-inset-bottom) + 14px)) !important" in host_modal.group("body")
    assert ".marketing-auth-host :deep(.modal-overlay.open)" in source
    assert ".marketing-auth-host :deep(.modal-box)" in source
    assert "margin-top: auto !important" in source
    assert "margin-bottom: 0 !important" in source


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


def test_agent_entry_does_not_auto_open_login_over_bottom_agent_input():
    source = _source()
    top_nav_source = TOP_NAV_VUE.read_text(encoding="utf-8")

    assert "wantsToolHome && !isLoggedIn.value" in source
    assert "marketingMode.value = true" in source
    assert "wantsAppHome && !localLoggedIn.value" in top_nav_source
    assert "xc-show-marketing-home" in top_nav_source
    assert "function openMarketingLogin()" in source
    assert "marketingPendingEnterAfterLogin" not in source


def test_home_agent_defaults_to_light_until_user_selects_theme():
    source = _source()
    app_source = APP_VUE.read_text(encoding="utf-8")
    top_nav_source = TOP_NAV_VUE.read_text(encoding="utf-8")

    assert "xc_theme_user_selected" in app_source
    assert "saved = 'light'" in app_source
    assert "window.matchMedia && window.matchMedia('(prefers-color-scheme" not in app_source
    assert "function readInitialTheme()" in source
    assert "if (!hasUserSelectedTheme()) return 'light'" in source
    assert "const theme = ref(readInitialTheme())" in source
    assert "uni.setStorageSync('xc_theme_user_selected', '1')" in source
    assert "localStorage.setItem('xc_theme_user_selected', '1')" in top_nav_source
    assert "theme: { type: String, default: 'light' }" in top_nav_source


def test_marketing_home_keeps_shian_agent_entry_and_contextual_auth_cta():
    source = _source()

    assert 'class="marketing-nav-link marketing-agent-link"' in source
    assert 'data-enter-app="1"' in source
    assert ">时安agent</text>" in source
    assert "{{ isLoggedIn ? '进入应用' : '登录/注册' }}" in source
    assert "min-width: 104px;" in source
    assert ".marketing-nav-links .marketing-agent-link" in source
    assert ".marketing-login" not in source


def test_marketing_login_success_enters_app_without_second_click():
    source = _source()

    assert "window.addEventListener('xc-auth-changed', function(e)" in source
    assert "if (marketingMode.value)" in source
    assert "nextTick(function() {\n        enterMarketingApp()" in source
    assert "marketingPendingEnterAfterLogin" not in source


def test_home_agent_exposes_four_question_templates_without_auto_sending():
    source = _source()

    assert "const homeQuestionTemplates = [" in source
    for key, label, short in [
        ("career", "事业", "跳槽时机"),
        ("relationship", "感情", "关系走向"),
        ("partnership", "合作", "项目取舍"),
        ("annual", "年运", "年度重点"),
    ]:
        assert f"key: '{key}'" in source
        assert f"label: '{label}'" in source
        assert f"short: '{short}'" in source
    assert 'class="home-question-templates"' in source
    assert 'class="home-question-template"' in source
    assert "showHomeQuestionTemplates" in source
    assert "function selectHomeQuestionTemplate(item)" in source
    assert "comprehensiveQuestion.value = item.question || ''" in source
    assert "startComprehensiveAsk(item.question" not in source
    assert ".home-question-templates { grid-template-columns: repeat(2, minmax(0, 1fr));" in source


def test_top_nav_login_modal_keeps_legacy_login_choices():
    source = TOP_NAV_VUE.read_text(encoding="utf-8")

    assert 'id="topnavLoginModal"' in source
    assert 'data-tab="password"' in source
    assert "账号" in source
    assert 'data-tab="code"' in source
    assert "邮箱" in source
    assert "Gitee" in source


def test_top_nav_login_modal_is_forced_to_bottom_globally():
    app_source = APP_VUE.read_text(encoding="utf-8")
    home_source = INDEX_VUE.read_text(encoding="utf-8")

    assert "body #topnavLoginModal" in app_source
    assert "body #topnavLoginModal.modal-overlay" in app_source
    assert "body .modal-overlay#topnavLoginModal" in app_source
    assert "align-items:flex-end!important" in app_source
    assert "body #topnavLoginModal.modal-overlay.open" in app_source
    assert "body .modal-overlay#topnavLoginModal.open" in app_source
    assert "display:flex!important" in app_source
    assert "body #topnavLoginModal .modal-box" in app_source
    assert "body .modal-overlay#topnavLoginModal .modal-box" in app_source
    assert "margin-top:auto!important" in app_source
    assert "transform:none!important" in app_source
    assert ":global(body #topnavLoginModal)" in home_source
    assert "align-items: flex-end !important" in home_source
    assert ":global(body #topnavLoginModal.open)" in home_source
    assert ":global(body #topnavLoginModal .modal-box)" in home_source
    assert "margin-top: auto !important" in home_source


def test_top_nav_reuses_online_login_endpoints_for_local_app_shell():
    source = TOP_NAV_VUE.read_text(encoding="utf-8")

    assert "用户名/邮箱" in source
    assert "邮箱登录需要输入邮箱" in source
    assert "url = '/api/email/login'" in source
    assert "url: '/api/email/send'" in source
    assert "url: '/api/oauth/' + provider + '/url'" in source
    assert "用户名/邮箱/手机号" not in source
    assert "邮箱/手机号" not in source
    assert "验证码登录需要输入邮箱或手机号" not in source
    assert "url = '/api/sms/login'" not in source
    assert "url: idType === 'phone' ? '/api/sms/send' : '/api/email/send'" not in source


def test_local_h5_can_proxy_api_to_online_login_without_new_auth_stack():
    vite_source = VITE_CONFIG.read_text(encoding="utf-8")
    package_json = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    dev_script = ONLINE_LOGIN_DEV_SCRIPT.read_text(encoding="utf-8")
    smoke_script = ONLINE_LOGIN_SMOKE_SCRIPT.read_text(encoding="utf-8")
    audit_account_script = AUDIT_ACCOUNT_SCRIPT.read_text(encoding="utf-8")
    evidence_doc = LOGIN_EVIDENCE_DOC.read_text(encoding="utf-8")

    assert "process.env.VITE_API_PROXY_TARGET || 'http://localhost:5199'" in vite_source
    assert "target: apiProxyTarget" in vite_source
    assert package_json["scripts"]["dev:h5:online-login"] == "node scripts/dev_h5_online_login.mjs"
    assert package_json["scripts"]["qa:agent:local-online-login"] == (
        "QA_MODE=online QA_BASE_URL=${QA_BASE_URL:-http://localhost:5173} node scripts/user_acceptance_full.mjs"
    )
    assert package_json["scripts"]["qa:login:local-online"] == (
        "QA_BASE_URL=${QA_BASE_URL:-http://localhost:5173} node scripts/local_online_login_smoke.mjs"
    )
    assert package_json["scripts"]["qa:audit-account"] == (
        "QA_BASE_URL=${QA_BASE_URL:-http://localhost:5173} node scripts/audit_account_preflight.mjs"
    )
    assert package_json["scripts"]["qa:audit-account:seed"] == "python3 scripts/seed_audit_account_assets.py"
    assert "process.env.VITE_API_PROXY_TARGET || 'https://shianjieyouwu.com'" in dev_script
    assert "manifest.h5.devServer.proxy['/api'].target = target" in dev_script
    assert "restoreManifest" in dev_script
    assert "body: { username: qaUser, password: qaPassword }" in smoke_script
    assert "await request('/api/me', {}, login.cookie)" in smoke_script
    assert "线上登录未返回 session cookie" in smoke_script
    assert "/api/comprehensive/options" in audit_account_script
    assert "fullAgentReady" in audit_account_script
    assert "这条预检只读取账号资产，不发起 Agent stream，不扣积分。" in audit_account_script
    assert "npm run dev:h5:online-login" in evidence_doc
    assert "npm run qa:login:local-online" in evidence_doc
    assert "npm run qa:agent:local-online-login" in evidence_doc
    assert "不触发真实短信、邮件和支付" in evidence_doc


def test_audit_account_seed_script_is_staging_local_only_by_default():
    source = AUDIT_ACCOUNT_SEED_SCRIPT.read_text(encoding="utf-8")

    assert "默认 dry-run" in source
    assert "parser.add_argument(\"--apply\"" in source
    assert "def assert_safe_target" in source
    assert "拒绝在 production 环境预置审核账号资产" in source
    assert "/home/lighthouse/tianji/flask-source/backend/tianji.db" in source
    assert "audit_seed_points" in source
    assert "audit_seed_ai_single" in source
    assert "audit_seed_ai_combo" in source
    assert "point_log" in source
    assert "membership" in source


def test_profile_page_exposes_account_deletion_for_store_review():
    source = PROFILE_VUE.read_text(encoding="utf-8")

    assert "注销账号与删除数据" in source
    assert "输入：注销账号" in source
    assert "/api/account/delete" in source
    assert "uni.removeStorageSync('xc_token')" in source
    assert "xc-auth-changed" in source
    assert ".btn-danger" in source
    assert ".danger-group" in source


def test_profile_page_normalizes_cached_user_before_rendering_username():
    source = PROFILE_VUE.read_text(encoding="utf-8")

    assert "function normalizeUsername(value)" in source
    assert "username: normalizeUsername(uni.getStorageSync('xc_user'))" in source
    assert "const displayUsername = computed(() => normalizeUsername(userInfo.username))" in source
    assert "const profileInitial = computed(() => displayUsername.value.charAt(0).toUpperCase())" in source
    assert "{{ profileInitial }}" in source
    assert "{{ displayUsername }}" in source
    assert "(userInfo.username || '用').charAt(0)" not in source


def test_top_nav_switches_back_to_home_before_rendering_agent_from_non_tab_pages():
    source = TOP_NAV_VUE.read_text(encoding="utf-8")

    assert "var routeBeforeNav = getCurrentRoute()" in source
    assert "var routeBeforeIsTab = TAB_PATHS.indexOf(routeBeforeNav) > -1 || routeBeforeNav === '/pages/index/index'" in source
    assert "var routeBeforeIsHome = routeBeforeNav === '/' || routeBeforeNav === '/pages/index/index'" in source
    assert "var shouldSwitchForAgentHome = wantsAppHome && !routeBeforeIsHome" in source
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


def test_qimen_free_grid_marks_xingmu_and_centers_palace_rows():
    source = QIMEN_VUE.read_text(encoding="utf-8")

    assert "function qimenStemTone(g, jiSet, ruSet, defaultColor)" in source
    assert "if (hasJiXing && hasRuMu) return { color: C_XINGMU, weight: '700' }" in source
    assert "刑+墓" in source
    assert 'class="qm-palace-row qm-row-top"' in source
    assert 'class="qm-palace-row qm-row-middle"' in source
    assert 'class="qm-palace-row qm-row-bottom"' in source
    assert "justify-content: center;" in source
    assert ".qf-result :deep(.qm-palace-row)" in source
    assert '--qm-row-width-current: 92%;' in source
    assert '--qm-row-width-compact: 82%;' in source
    assert '--qm-row-width-tight: 60%;' in source
    assert '--qm-row-width-rollback: 68%;' in source
    assert '--qm-row-width: var(--qm-row-width-current);' in source
    assert '--qm-row-top: 24%;' in source
    assert '--qm-row-middle: 50%;' in source
    assert '--qm-row-bottom: 76%;' in source
    assert 'left: var(--qm-row-left);' in source
    assert 'width: var(--qm-row-width);' in source
    assert ".qf-result :deep(.qm-row-top) { top: var(--qm-row-top); }" in source
    assert ".qf-result :deep(.qm-row-bottom) { top: var(--qm-row-bottom); }" in source
    assert 'class="qm-gong-dot"' in source
    assert ".qf-result :deep(.qm-gong-dot)" in source
    assert "--qm-gong-label-font: clamp(0.62rem, calc(var(--qm-grid-size) / 46), 1.08rem);" in source
    assert "color: rgba(160, 160, 160, 0.22);" in source
    assert "width: 3.25em;" in source
    assert "qimenTailAlignClass(p.shenFull || '', 'qm-kong-anchor')" in source
    assert 'class="qm-kong-marker"' in source
    assert ".qf-result :deep(.qm-kong-marker)" in source
    assert "--qm-plate-font: 'Yuanti SC', 'STYuanti', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif;" in source
    assert "font-family: var(--qm-plate-font);" in source


def test_qimen_free_summary_uses_scannable_meta_groups():
    source = QIMEN_VUE.read_text(encoding="utf-8")

    assert 'class="qf-meta-panel"' in source
    assert 'class="qf-meta-head"' in source
    assert 'class="qf-meta-groups"' in source
    assert "pillarPair('年柱', fp.year)" in source
    assert 'class="qf-pillar-strip"' in source
    assert "metaPair('值符', data.zhiFu, true)" in source
    assert ".qf-result :deep(.qf-meta-groups)" in source
    assert ".qf-result :deep(.qf-pillar-strip)" in source
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in source
