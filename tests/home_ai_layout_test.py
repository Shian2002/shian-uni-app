import re
from pathlib import Path


INDEX_VUE = Path(__file__).resolve().parents[1] / "src" / "pages" / "index" / "index.vue"


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
