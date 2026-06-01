import os


def test_admin_user_points_list_exposes_next_page_controls():
    page_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src", "pages", "admin", "index.vue")
    )
    source = open(page_path, encoding="utf-8").read()

    assert "userPage" in source
    assert "loadMoreUsers" in source
    assert "hasMoreUsers" in source
    assert "加载更多用户" in source
    assert "page=' + userPage.value" in source
