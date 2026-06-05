import importlib
import os
import re
import sys


def _import_backend_module(name):
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
    sys.path.insert(0, backend_dir)
    try:
        return importlib.import_module(name)
    finally:
        if sys.path and sys.path[0] == backend_dir:
            sys.path.pop(0)


def test_tarot_deck_cards_have_stable_image_metadata():
    tarot_engine = _import_backend_module("tarot_engine")

    assert len(tarot_engine.FULL_DECK) == 78
    image_keys = [card.get("image_key") for card in tarot_engine.FULL_DECK]

    assert all(image_keys)
    assert len(set(image_keys)) == 78
    assert all(card.get("name_en") for card in tarot_engine.FULL_DECK)
    assert all(card.get("image_url", "").startswith("/static/tarot/rws/") for card in tarot_engine.FULL_DECK)

    draw = tarot_engine.draw_cards("celtic_cross", enable_reversed=True)
    for card in draw["data"]["cards"]:
        assert card["image_key"]
        assert card["image_url"].startswith("/static/tarot/rws/")
        assert card["name_en"]


def test_tarot_page_renders_real_card_images_with_fallback():
    page_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src", "pages", "tarot", "index.vue")
    )
    source = open(page_path, encoding="utf-8").read()

    assert "tarot-card-img" in source
    assert "getCardImage" in source
    assert "tarot-card-fallback" in source
    assert "MAJOR_ICONS" not in source
    assert "SUIT_ICONS" not in source


def test_tarot_page_card_images_and_text_are_not_cropped():
    page_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src", "pages", "tarot", "index.vue")
    )
    source = open(page_path, encoding="utf-8").read()
    name_block = re.search(r"\.tarot-card-name-below \{(?P<body>.*?)\n\}", source, re.S)
    english_block = re.search(r"\.tarot-card-name-en \{(?P<body>.*?)\n\}", source, re.S)
    mobile_block = re.search(r"@media \(max-width: 480px\) \{(?P<body>.*?)\n\}", source, re.S)

    assert "object-fit: contain;" in source
    assert "object-fit: cover;" not in source
    assert ".tarot-card-front, .tarot-card-back" in source
    assert "overflow: visible;" in source
    assert name_block and "white-space: nowrap;" not in name_block.group("body")
    assert english_block and "white-space: nowrap;" not in english_block.group("body")
    assert ".tarot-card-keyword-below" in source
    assert ".tarot-card-keyword-below { display: none; }" not in source
    assert mobile_block and ".tarot-card-keyword-below { display: none; }" not in mobile_block.group("body")


def test_tarot_result_card_text_has_reserved_space_below_images():
    page_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src", "pages", "tarot", "index.vue")
    )
    source = open(page_path, encoding="utf-8").read()
    art_block = re.search(r"\.tarot-card-art-wrap \{(?P<body>.*?)\n\}", source, re.S)
    position_block = re.search(r"\.tarot-card-position \{(?P<body>.*?)\n\}", source, re.S)
    keyword_block = re.search(r"\.tarot-card-keyword-below \{(?P<body>.*?)\n\}", source, re.S)

    assert ".tarot-card-front, .tarot-card-back" in source
    assert "box-sizing: border-box;" in source
    assert ".tarot-card-front" in source and "gap: 4px;" in source
    assert art_block and "aspect-ratio: 7 / 10.8;" in art_block.group("body")
    assert keyword_block and "min-height: 28px;" in keyword_block.group("body")
    assert position_block and "margin-top: 14px;" in position_block.group("body")
    assert position_block and "min-height: 74px;" in position_block.group("body")


def test_tarot_mobile_card_grid_does_not_overflow_viewport():
    page_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src", "pages", "tarot", "index.vue")
    )
    source = open(page_path, encoding="utf-8").read()
    mobile_block = re.search(r"@media \(max-width: 480px\) \{(?P<body>.*?)\n\}", source, re.S)

    assert mobile_block, "缺少塔罗移动端样式"
    body = mobile_block.group("body")
    assert '.tarot-cards-display[data-count="3"] { grid-template-columns: repeat(2, 1fr); max-width: 270px;' in body
    assert '.tarot-cards-display[data-count="5"] { grid-template-columns: repeat(2, 1fr); max-width: 270px;' in body
    assert '.tarot-cards-display[data-count="10"] { grid-template-columns: repeat(2, 1fr); max-width: 270px;' in body


def test_sidebar_history_touch_does_not_navigate_on_scroll_end():
    nav_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src", "components", "TopNav.vue")
    )
    source = open(nav_path, encoding="utf-8").read()

    assert "sidebar-touch-moving" in source
    assert "data-click-action" in source
    assert "data-delete-action" in source
    assert "ontouchend=\"event.preventDefault();event.stopPropagation();" not in source
    assert "function _handleSidebarTouchEnd" in source
