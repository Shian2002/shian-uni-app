import importlib
import os
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
