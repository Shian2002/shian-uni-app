import re
from pathlib import Path


INDEX_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "index" / "index.vue"
QIMEN_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "qimen" / "index.vue"
BAZI_INDEX_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "bazi-index" / "index.vue"
APP_VUE = Path(__file__).resolve().parents[1] / "src" / "App.vue"
HOME_AI_UTILS = Path(__file__).resolve().parents[1] / "src" / "pages" / "index" / "homeAiUtils.js"
HOME_AI_DRAFT = Path(__file__).resolve().parents[1] / "src" / "pages" / "index" / "useHomeAiDraft.js"
HOME_AI_STREAM = Path(__file__).resolve().parents[1] / "src" / "pages" / "index" / "useHomeAiStream.js"
HOME_ARTIFACT_TABS = Path(__file__).resolve().parents[1] / "src" / "pages" / "index" / "components" / "HomeArtifactTabs.vue"


def _source():
    return INDEX_VUE.read_text(encoding="utf-8")


def _qimen_source():
    return QIMEN_VUE.read_text(encoding="utf-8")


def _bazi_index_source():
    return BAZI_INDEX_VUE.read_text(encoding="utf-8")


def _app_source():
    return APP_VUE.read_text(encoding="utf-8")


def _home_ai_utils_source():
    return HOME_AI_UTILS.read_text(encoding="utf-8")


def _home_ai_draft_source():
    return HOME_AI_DRAFT.read_text(encoding="utf-8")


def _home_ai_stream_source():
    return HOME_AI_STREAM.read_text(encoding="utf-8")


def _home_artifact_tabs_source():
    return HOME_ARTIFACT_TABS.read_text(encoding="utf-8")


def test_comprehensive_stream_rendering_is_batched():
    source = _source()
    stream_source = _home_ai_stream_source()

    assert "frameMs: 16" in stream_source
    assert "baseCps: 58" in stream_source
    assert "maxCps: 72" in stream_source
    assert "maxFrameChars: 1" in stream_source
    assert "reactiveSyncMs: 420" in stream_source
    assert "const COMPREHENSIVE_ARTIFACT_STREAM_OPTIONS" in source
    assert "const COMPREHENSIVE_HEAVY_ARTIFACT_STREAM_OPTIONS" in source
    assert "const COMPREHENSIVE_HEAVY_ARTIFACT_KEYS = ['bazi.basic', 'bazi.yun', 'ziwei.pan']" in source
    assert "let comprehensiveRenderFrame = null" in source
    assert "let comprehensiveTypeFrame = null" in source
    assert "let comprehensiveTypeStates = {}" in source
    assert "let artifactHtmlCache = new WeakMap()" in source
    assert "function scheduleComprehensiveAssistantUpdate" in source
    assert "function flushComprehensiveAssistantUpdate" in source
    assert "function flushPendingArtifactAnalyses()" in source
    assert "flushPendingArtifactAnalyses()" in source
    assert "function scheduleArtifactAnalysisFrame(state)" in source
    assert "function pumpArtifactAnalysis(aiIndex, artifactKey, now)" in source
    assert "function cachedArtifactHtml(artifact, cacheKey, render)" in source
    assert "cachedArtifactHtml(artifact, 'bazi.yun'" in source
    assert "cachedArtifactHtml(artifact, 'ziwei.pan'" in source

    typewriter = re.search(
        r"function startComprehensiveTypewriter\(aiIndex, state\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert typewriter, "缺少综合问答打字机函数"
    assert "requestAnimationFrame(tick)" in typewriter.group("body")
    assert "smoothTextSpeed(state.queue.length)" in typewriter.group("body")
    assert "state.charBudget" in typewriter.group("body")
    assert "takeSmoothTextChunk(state.queue" in typewriter.group("body")
    assert "scheduleComprehensiveAssistantUpdate" in typewriter.group("body")
    assert "paintComprehensiveStreamText(aiIndex, displayText)" in typewriter.group("body")
    assert "comprehensiveTypeStates[String(aiIndex)] = state" in source
    assert "repaintComprehensiveStreamText(aiIndex)" in source
    assert "setInterval" not in typewriter.group("body")
    assert "function takeSmoothTextChunk" in stream_source
    assert "function shouldSyncStreamContent" in stream_source
    assert "COMPREHENSIVE_TYPE_MAX_FRAME_CHARS" in source
    assert "home-ai-stream-text" in source

    update_fn = re.search(
        r"function updateComprehensiveAssistant\(aiIndex, patch, options\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert update_fn, "缺少综合问答消息更新函数"
    update_body = update_fn.group("body")
    assert "Object.keys(patch || {}).forEach" in update_body
    assert "current[key] = patch[key]" in update_body
    assert "comprehensiveMessages.value[aiIndex] = Object.assign" not in update_body

    assert "async function startComprehensiveAsk(forcedQuestion)" in source
    assert "scheduleComprehensiveAssistantUpdate(aiIndex, { stage: data.message" in source
    assert "if (data.summary_start)" in source
    assert "setActiveArtifact(aiIndex, '__summary__')" in source
    assert "正在生成综合结论" in source
    assert "flushComprehensiveAssistantUpdate()" in source
    assert "function finishComprehensiveAnswer" in source
    assert "finishComprehensiveAnswer(aiIndex, typeState)" in source
    assert "updateComprehensiveAssistant(aiIndex, { stage: data.message" not in source

    finish_fn = re.search(
        r"function finishComprehensiveAnswer\(aiIndex, state\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert finish_fn, "缺少综合问答收尾函数"
    assert "flushComprehensiveTypewriter" not in finish_fn.group("body")
    assert "startComprehensiveTypewriter(aiIndex, state)" in finish_fn.group("body")


def test_comprehensive_chat_scroll_is_coalesced():
    source = _source()

    assert "let comprehensiveScrollTimer = null" in source
    scroll_fn = re.search(
        r"function scrollComprehensiveChatToBottom\(behavior, force\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert scroll_fn, "缺少综合问答滚动函数"
    body = scroll_fn.group("body")
    assert "cancelAnimationFrame(comprehensiveScrollTimer)" in body
    assert "comprehensiveScrollTimer = requestAnimationFrame" in body
    assert "behavior: behavior || 'auto'" in body
    assert "getComprehensiveScrollTarget()" in body


def test_comprehensive_home_draft_survives_refresh_during_stream():
    source = _source()
    draft_source = _home_ai_draft_source()

    assert "const comprehensiveDraftStorageKey = 'xc_home_comprehensive_draft_v1'" in source
    assert "const COMPREHENSIVE_DRAFT_SAVE_MS = 320" in source
    assert "createHomeAiDraftStorage" in source
    assert "function saveComprehensiveDraftNow()" in source
    assert "function saveComprehensiveDraftForUnload()" in source
    assert "function syncActiveComprehensiveStreamText()" in source
    assert "function scheduleComprehensiveDraftSave()" in source
    assert "function restoreComprehensiveDraft()" in source
    assert "localStorage.setItem(storageKey" in draft_source
    assert "localStorage.getItem(storageKey)" in draft_source
    assert "scheduleComprehensiveDraftSave()" in source
    assert "saveComprehensiveDraftNow()" in source
    assert "restoreComprehensiveDraft()" in source
    assert "上次解读在刷新时中断，已恢复已生成内容" in source
    assert "syncActiveComprehensiveStreamText()" in source
    assert "window.addEventListener('beforeunload', saveComprehensiveDraftForUnload)" in source
    assert "document.addEventListener('visibilitychange', onHomeVisibilityChange)" in source

    update_fn = re.search(
        r"function updateComprehensiveAssistant\(aiIndex, patch, options\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert update_fn, "缺少综合问答消息更新函数"
    assert "scheduleComprehensiveDraftSave()" in update_fn.group("body")

    onshow = re.search(r"onShow\(\(\) => \{(?P<body>.*?)\n\}\)", source, re.S)
    assert onshow, "缺少首页 onShow 恢复逻辑"
    assert "restoreComprehensiveConversation(id)" in onshow.group("body")
    assert "restoreComprehensiveDraft()" in onshow.group("body")

    new_chat = re.search(
        r"function startNewComprehensiveConversation\(\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert new_chat, "缺少新对话清理逻辑"
    assert "clearComprehensiveDraft()" in new_chat.group("body")


def test_home_ai_locks_shell_and_scrolls_messages_internally():
    source = _source()

    assert "setHomeFixedPage(true)" not in source
    fixed_root = re.search(r":global\(html\.home-fixed-page\),\n:global\(body\.home-fixed-page\) \{(?P<body>[^}]*)\}", source)
    assert fixed_root, "缺少首页固定工作台外层样式"
    assert "overflow: hidden !important" in fixed_root.group("body")

    fixed_page = re.search(r":global\(body\.home-fixed-page\) \.page-root \{(?P<body>[^}]*)\}", source)
    assert fixed_page, "缺少首页固定工作台根容器样式"
    assert "overflow: hidden !important" in fixed_page.group("body")

    chat = re.search(r"\.home-ai-console\.has-chat \.home-ai-chat \{(?P<body>[^}]*)\}", source)
    assert chat, "缺少综合问答消息区样式"
    assert "overflow-y: auto" in chat.group("body")
    assert "overscroll-behavior: contain" in chat.group("body")


def test_home_artifacts_are_normalized_for_old_history_display():
    source = _source()
    utils_source = _home_ai_utils_source()

    assert "function normalizeHomeArtifactForDisplay" in source
    assert "normalizeHomeArtifactForDisplay(artifact" in source
    assert "sanitizeArtifactAnalysisText" in source
    assert "zhi_liu_chong: '地支六冲'" in utils_source
    assert "artifact.analysis || previous.analysis || ''" not in source


def test_home_tarot_artifact_uses_real_images_not_emoji_cards():
    source = _source()

    tarot_fn = re.search(
        r"function renderTarotArtifact\(data\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert tarot_fn, "缺少首页塔罗 artifact 渲染函数"
    body = tarot_fn.group("body")
    assert "tarot-card-img" in body
    assert "getHomeTarotImage" in body
    assert "tarot-card-fallback" in body
    assert "tarot-card-icon" not in body
    assert "🃏" not in body


def test_home_artifact_layout_has_no_inner_vertical_scroll_box():
    source = _source()

    assert ".home-tool-card-body { min-width: 0; padding:" in source
    assert ".home-tool-card-body { min-width: 0; min-height:" not in source
    artifact_rule = re.search(r"\.home-artifact-render \{(?P<body>[^}]*)\}", source)
    assert artifact_rule, "缺少首页 artifact 容器样式"
    body = artifact_rule.group("body")
    assert "max-height" not in body
    assert "overflow: auto" not in body
    assert "overflow-y: visible" in body


def test_home_ai_answers_show_rotating_shian_agent_header():
    source = _source()

    assert "home-ai-agent-head" in source
    assert "时安 agent" in source
    assert "home-artifact-analysis-head" in source
    assert "home-ai-agent-logo" in source
    assert "home-ai-agent-logo.spinning" in source
    assert "animation: stage-spin 3.2s linear infinite" in source
    assert "home-ai-agent-logo.idle" in source
    assert "animation: none" in source
    assert "综合解答</text>" not in source
    assert "currentArtifactForMessage(msg, idx).title }}解析" in source
    assert '<img class="home-ai-agent-logo small idle"' not in source


def test_home_ai_artifacts_use_switcher_not_full_stack():
    source = _source()
    tabs_source = _home_artifact_tabs_source()

    assert "activeArtifactKeyByMessage" in source
    assert '@select="setActiveArtifact(idx, $event)"' in source
    assert "currentArtifactForMessage(msg, idx)" in source
    assert "artifactTabsForMessage(msg)" in source
    assert "home-artifact-switcher" in source
    assert 'v-for="artifact in artifacts"' in tabs_source
    assert 'v-if="currentArtifactForMessage(msg, idx) && !isSummaryActive(msg, idx)"' in source
    assert "home-ai-summary-panel" in source
    assert "activeArtifactKeyByMessage[messageIndex] = key" in source
    assert "ensureActiveArtifact(index, visibleArtifactList(message))" in source
    assert "msg.role === 'assistant' && (msg.content || msg._streaming)" in source
    assert "setActiveArtifact(aiIndex, '__summary__')" in source
    assert "setActiveArtifact(index, '__summary__')" in source
    assert "msg.role === 'user' && msg.content" in source


def test_home_ai_switcher_layout_is_compact():
    source = _source() + "\n" + _home_artifact_tabs_source()
    switcher_rule = re.search(r"\.home-artifact-switcher \{(?P<body>[^}]*)\}", source)
    assert switcher_rule, "缺少术数切换栏样式"

    assert ".home-artifact-switcher" in source
    assert "grid-template-columns: repeat(auto-fit, minmax(112px, 1fr))" in source
    assert "overflow-x: auto" not in switcher_rule.group("body")
    assert "-webkit-overflow-scrolling: touch" not in switcher_rule.group("body")
    assert ".home-artifact-tab.active" in source
    assert ".home-ai-summary-panel" in source
    assert ".home-tool-card-toggle { display: none; }" in source
    assert "home-ai-stage-wrap { display: none; }" in source


def test_home_ziwei_timeline_is_sorted_by_decadal_age():
    source = _source()

    assert "function ziweiDecadalStart" in source
    timeline = re.search(r"const timeline = palaces(?P<body>.*?)\.map\(function\(p\)", source, re.S)
    assert timeline, "缺少紫微大限 timeline 生成"
    assert ".sort(function(a, b)" in timeline.group("body")
    assert "ziweiDecadalStart(a) - ziweiDecadalStart(b)" in timeline.group("body")


def test_home_liuyao_keeps_visual_center_on_mobile():
    source = _source()

    assert "ly-visual-side" in source
    assert "--ly-yao-width" in source
    assert "--ly-side-width" in source
    assert "--ly-marker-width" in source
    assert "justify-content: center" in source
    assert "grid-template-columns: var(--ly-marker-width) var(--ly-yao-width) minmax(0, 1fr)" in source
    assert "width: min(var(--ly-side-width), 100%)" in source
    assert "grid-template-columns: minmax(0, 1fr) 1px minmax(0, 1fr)" in source
    assert "ly-row-ben-side\"><div class=\"ly-yao-tags-left\"" not in source
    assert "position: absolute; left: calc(-1 * var(--ly-tag-gutter))" not in source
    assert "--ly-tag-gutter" not in source
    assert "htmlEscape(bian.name || ben.name || '')" in source
    assert ".home-artifact-render :deep(.ly-paired-row.has-bian) { grid-template-columns: 1fr; }" not in source
    assert ".home-artifact-render :deep(.ly-row-divider) { width: 100%; height: 1px; }" not in source


def test_home_qimen_grid_scales_with_available_width():
    source = _source()

    assert "qm-scale-shell" in source
    assert "--qm-grid-size" in source
    assert "width: min(100%, var(--qm-grid-size))" in source
    assert "font-size: clamp(" in source


def test_qimen_standalone_grid_scales_with_available_width():
    source = _qimen_source()

    assert "qm-scale-shell" in source
    assert "qm-palace-grid" in source
    assert "--qm-grid-size" in source
    assert "width: min(100%, var(--qm-grid-size))" in source
    assert "font-size: var(--qm-cell-font)" in source
    assert "max-width:300px" not in source
    assert "max-width: 300px" not in source
    assert "--qm-cell-font: clamp(0.66rem, calc(var(--qm-grid-size) / 40), 1.24rem)" in source
    assert "--qm-kong-font" in source
    assert "--qm-gong-label-font" in source
    assert "--qm-cell-pad: clamp(7px, calc(var(--qm-grid-size) / 54), 15px)" in source
    assert "padding: var(--qm-cell-pad)" in source
    assert "p.isMa?`<span class=\"qm-ma-marker\"" in source
    assert "p.isMa?`<span class=\"qm-ma-marker\"" in source.split("${tianHtml}")[0]
    assert "class=\"qm-heaven-stem\"" in source


def test_tool_tabs_stay_in_normal_scroll_flow():
    source = _app_source()

    assert "body:not(.home-fixed-page) .tool-tabs" in source
    assert "position:static!important" in source
    assert "top:auto!important" in source
    assert "z-index:auto!important" in source
    assert "body:not(.home-fixed-page) .tool-tabs{\n  position:sticky!important;" not in source
    assert "body:not(.home-fixed-page) .tool-tabs{top:56px" not in source


def test_bazi_record_cards_align_pillars_before_ops_and_use_soft_colors():
    source = _bazi_index_source()

    assert "grid-template-columns: 50px minmax(0, 1fr) 132px 44px" in source
    assert ".bz-card .card-gz { display: flex; gap: 8px; width: 132px;" in source
    assert ".bz-card .card-ops {\n  width: 44px;" in source
    assert "grid-template-columns: 42px minmax(0, 1fr) 112px 38px !important" in source
    assert "'甲':'#4f9d67'" in source
    assert "'乙':'#63ad74'" in source
    assert "#07e930" not in source
    assert "#1dcc36" not in source
    assert "#2ecc71" not in source
