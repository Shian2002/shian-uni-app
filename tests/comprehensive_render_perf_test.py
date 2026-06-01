import re
from pathlib import Path


INDEX_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "index" / "index.vue"


def _source():
    return INDEX_VUE.read_text(encoding="utf-8")


def test_comprehensive_stream_rendering_is_batched():
    source = _source()

    assert "const COMPREHENSIVE_TYPE_FRAME_MS = 80" in source
    assert "const COMPREHENSIVE_ARTIFACT_FLUSH_MS = 120" in source
    assert "function flushPendingArtifactAnalyses()" in source
    assert "flushPendingArtifactAnalyses()" in source

    typewriter = re.search(
        r"function startComprehensiveTypewriter\(aiIndex, state\) \{(?P<body>.*?)\n\}",
        source,
        re.S,
    )
    assert typewriter, "缺少综合问答打字机函数"
    assert "state.queue.length > 120 ? 24" in typewriter.group("body")
    assert ", COMPREHENSIVE_TYPE_FRAME_MS)" in typewriter.group("body")


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
    assert "clearTimeout(comprehensiveScrollTimer)" in body
    assert "comprehensiveScrollTimer = setTimeout" in body


def test_home_artifacts_are_normalized_for_old_history_display():
    source = _source()

    assert "function normalizeHomeArtifactForDisplay" in source
    assert "normalizeHomeArtifactForDisplay(artifact" in source
    assert "sanitizeArtifactAnalysisText" in source
    assert "'zhi_liu_chong': '地支六冲'" in source
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
    assert "animation: stage-spin 3.2s linear infinite" in source
    assert "{{ artifact.title }}解析" in source


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
