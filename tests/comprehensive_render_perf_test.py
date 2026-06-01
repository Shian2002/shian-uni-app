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
