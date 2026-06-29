import importlib
import io
import json
import os
import sys
import base64
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from werkzeug.security import check_password_hash, generate_password_hash


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    db_path = tmp_path / "test-tianji.db"
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("TIANJI_SECRET_KEY", "test-secret-key")
    sys.path.insert(0, backend_dir)
    try:
        module = importlib.import_module("app")
        module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        with module.app.app_context():
            module.db.drop_all()
            module.db.create_all()
        yield module
    finally:
        if sys.path and sys.path[0] == backend_dir:
            sys.path.pop(0)


@pytest.fixture()
def user_factory(app_module):
    def create_user(username="member", is_admin=False):
        with app_module.app.app_context():
            user = app_module.User(
                username=username,
                password_hash=generate_password_hash("secret123", method="pbkdf2:sha256"),
                has_password=True,
                is_admin=is_admin,
            )
            app_module.db.session.add(user)
            app_module.db.session.commit()
            return SimpleNamespace(id=user.id, username=user.username, is_admin=user.is_admin)

    return create_user


def test_visible_avatar_url_filters_missing_local_upload(app_module, tmp_path):
    with app_module.app.app_context():
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        app_module.app.config["UPLOAD_FOLDER"] = str(upload_dir)
        avatar_utils = importlib.import_module("avatar_utils")

        assert avatar_utils.visible_avatar_url("/static/uploads/missing.png") == ""
        assert avatar_utils.visible_avatar_url("https://example.com/avatar.png") == "https://example.com/avatar.png"

        existing = upload_dir / "avatar_1.png"
        existing.write_bytes(PNG_1X1)
        assert avatar_utils.visible_avatar_url("/static/uploads/avatar_1.png") == "/static/uploads/avatar_1.png"


def test_unbind_oauth_requires_another_login_method(app_module):
    with app_module.app.app_context():
        user = app_module.User(
            username="oauth-only",
            password_hash="",
            has_password=False,
            oauth_gitee="gitee-only-id",
        )
        app_module.db.session.add(user)
        app_module.db.session.commit()
        user_id = user.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True

    response = client.post("/api/unbind/oauth", json={"provider": "gitee"})

    assert response.status_code == 400
    assert "请先设置密码或绑定邮箱" in response.get_json()["error"]
    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.User, user_id)
        assert refreshed.oauth_gitee == "gitee-only-id"


def test_unbind_oauth_clears_provider_when_password_exists(app_module, user_factory):
    user = user_factory("oauth-with-password")
    with app_module.app.app_context():
        db_user = app_module.db.session.get(app_module.User, user.id)
        db_user.oauth_gitee = "gitee-bound-id"
        app_module.db.session.commit()

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True

    response = client.post("/api/unbind/oauth", json={"provider": "gitee"})

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.User, user.id)
        assert refreshed.oauth_gitee is None


def test_delete_account_requires_password_and_anonymizes_personal_data(app_module, user_factory):
    user = user_factory("delete-owner")
    other = user_factory("delete-other")
    models = importlib.import_module("models")
    with app_module.app.app_context():
        db_user = app_module.db.session.get(app_module.User, user.id)
        db_user.email = "delete-owner@example.com"
        db_user.phone = "13900000000"
        db_user.oauth_gitee = "gitee-delete-id"
        db_user.avatar = "/static/uploads/delete-owner.png"
        record = models.Record(user_id=user.id, app_type="qimen", question="注销测试", result_html="ok")
        post = models.Post(user_id=user.id, title="注销帖子", content="注销帖子内容")
        app_module.db.session.add_all([
            db_user,
            models.UserProfile(user_id=user.id, name="注销命盘", birth_time="1990-01-01 08:00"),
            record,
            models.BaziRecord(user_id=user.id, name="注销八字", birth_time="1990-01-01 08:00"),
            models.Membership(user_id=user.id, points=88, ai_single_credits=2, ai_combo_credits=1),
            models.PointLog(user_id=user.id, action="admin_add", points=88, description="人工加积分"),
            models.AiRun(kind="comprehensive", user_id=user.id, request_json='{"q":"隐私"}', response_json='{"a":"answer"}'),
            post,
        ])
        app_module.db.session.flush()
        app_module.db.session.add_all([
            models.FollowUp(user_id=user.id, record_id=record.id, note="跟进记录"),
            models.Collection(user_id=user.id, target_type="record", target_id=record.id),
            models.Comment(user_id=user.id, post_id=post.id, content="注销评论"),
            models.Comment(user_id=other.id, post_id=post.id, content="别人评论"),
            models.PostLike(user_id=other.id, post_id=post.id),
            models.Notification(user_id=other.id, from_user_id=user.id, type="like", post_id=post.id, content="点赞"),
            models.Report(user_id=other.id, target_type="post", target_id=post.id, reason="测试"),
        ])
        app_module.db.session.commit()

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True

    wrong_password = client.post("/api/account/delete", json={"confirm": "注销账号", "password": "wrong"})
    assert wrong_password.status_code == 403
    with app_module.app.app_context():
        assert models.UserProfile.query.filter_by(user_id=user.id).count() == 1
        assert app_module.db.session.get(app_module.User, user.id).username == "delete-owner"

    response = client.post("/api/account/delete", json={"confirm": "注销账号", "password": "secret123"})
    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert client.get("/api/me").get_json() == {"guest": True}

    old_login = client.post("/api/login", json={"username": "delete-owner", "password": "secret123"})
    assert old_login.status_code == 401

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.User, user.id)
        assert refreshed.username.startswith(f"deleted_user_{user.id}_")
        assert refreshed.email is None
        assert refreshed.phone is None
        assert refreshed.oauth_gitee is None
        assert refreshed.avatar == ""
        assert refreshed.has_password is True
        assert not check_password_hash(refreshed.password_hash, "secret123")
        assert models.UserProfile.query.filter_by(user_id=user.id).count() == 0
        assert models.Record.query.filter_by(user_id=user.id).count() == 0
        assert models.BaziRecord.query.filter_by(user_id=user.id).count() == 0
        assert models.FollowUp.query.filter_by(user_id=user.id).count() == 0
        assert models.Collection.query.filter_by(user_id=user.id).count() == 0
        assert models.Membership.query.filter_by(user_id=user.id).count() == 0
        assert models.Post.query.filter_by(user_id=user.id).count() == 0
        assert models.Comment.query.filter_by(user_id=user.id).count() == 0
        assert models.PointLog.query.filter_by(user_id=user.id).one().description == "[account deleted]"
        assert models.AiRun.query.filter_by(user_id=user.id).one().request_json == ""


def test_add_points_can_participate_in_existing_transaction(app_module, user_factory):
    user = user_factory()

    with app_module.app.app_context():
        new_points = app_module.add_points(
            user.id,
            "admin_add",
            25,
            "事务内加积分",
            dedupe_key="manual:test:25",
            commit=False,
        )
        assert new_points == 25
        app_module.db.session.rollback()

        membership = app_module.Membership.query.filter_by(user_id=user.id).first()
        logs = app_module.PointLog.query.filter_by(user_id=user.id).all()
        assert membership is None
        assert logs == []


def test_daily_sign_in_is_idempotent_by_user_and_date(app_module, user_factory):
    user = user_factory()

    with app_module.app.app_context():
        first = app_module.create_daily_sign_in_once(user.id)
        second = app_module.create_daily_sign_in_once(user.id)

        assert first["ok"] is True
        assert first["added"] == app_module.POINT_RULES["sign_in"]
        assert second["ok"] is False
        assert second["error"] == "今天已签到"

        membership = app_module.Membership.query.filter_by(user_id=user.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=user.id, action="sign_in").all()
        assert membership.points == app_module.POINT_RULES["sign_in"]
        assert len(logs) == 1


def test_membership_endpoint_tolerates_concurrent_first_load(app_module, user_factory):
    user = user_factory("race-member")

    def load_membership():
        client = app_module.app.test_client()
        login = client.post("/api/login", json={"username": "race-member", "password": "secret123"})
        assert login.status_code == 200
        return client.get("/api/membership")

    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(lambda _: load_membership(), range(6)))

    assert [response.status_code for response in responses] == [200] * 6
    with app_module.app.app_context():
        memberships = app_module.Membership.query.filter_by(user_id=user.id).all()
        assert len(memberships) == 1


def test_use_points_does_not_write_log_when_balance_is_insufficient(app_module, user_factory):
    user = user_factory()

    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 5, "初始积分")

        result = app_module.use_points(user.id, "tool_use", 10, "余额不足扣分")

        membership = app_module.Membership.query.filter_by(user_id=user.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=user.id, action="tool_use").all()
        assert result["ok"] is False
        assert result["error"] == "积分不足"
        assert membership.points == 5
        assert logs == []


def test_app_uses_central_points_service(app_module):
    assert app_module.add_points.__module__ == "points_service"
    assert app_module.use_points.__module__ == "points_service"
    assert app_module.create_daily_sign_in_once.__module__ == "points_service"
    assert app_module.spend_ai_quota_once.__module__ == "points_service"
    assert app_module.refund_ai_quota_once.__module__ == "points_service"


def test_spend_ai_quota_once_uses_daily_light_before_points(app_module, user_factory):
    user = user_factory()

    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 5, "初始积分")

        result = app_module.spend_ai_quota_once(user.id, ["bazi"], 2)

        membership = app_module.Membership.query.filter_by(user_id=user.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=user.id, action="daily_ai_light").all()
        assert result["ok"] is True
        assert result["used_credit"] == "daily_light"
        assert result["used"] == 0
        assert membership.points == 5
        assert membership.daily_ai_light_used_at
        assert len(logs) == 1


def test_spend_ai_quota_once_allows_free_model_without_point_log(app_module, user_factory):
    user = user_factory()

    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 5, "初始积分")

        result = app_module.spend_ai_quota_once(user.id, ["qimen"], 0)

        membership = app_module.Membership.query.filter_by(user_id=user.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=user.id, action="comprehensive_ai").all()
        assert result["ok"] is True
        assert result["used_credit"] == "free_model"
        assert result["used"] == 0
        assert membership.points == 5
        assert logs == []


def test_spend_ai_quota_once_deducts_combo_credit_atomically(app_module, user_factory):
    user = user_factory()

    with app_module.app.app_context():
        membership = app_module.get_or_create_membership(user.id)
        membership.ai_combo_credits = 1
        app_module.db.session.commit()

        result = app_module.spend_ai_quota_once(user.id, ["bazi", "ziwei"], 8)

        membership = app_module.Membership.query.filter_by(user_id=user.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=user.id, action="ai_combo_credit_use").all()
        assert result["ok"] is True
        assert result["used_credit"] == "ai_combo_credits"
        assert result["used"] == 1
        assert membership.ai_combo_credits == 0
        assert len(logs) == 1


def test_spend_ai_quota_once_falls_back_to_points(app_module, user_factory):
    user = user_factory()

    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 12, "初始积分")
        membership = app_module.get_or_create_membership(user.id)
        membership.daily_ai_light_used_at = app_module.datetime.utcnow().strftime("%Y-%m-%d")
        app_module.db.session.commit()

        result = app_module.spend_ai_quota_once(user.id, ["bazi"], 7)

        membership = app_module.Membership.query.filter_by(user_id=user.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=user.id, action="comprehensive_ai").all()
        assert result["ok"] is True
        assert result["used_credit"] == "points"
        assert result["used"] == 7
        assert membership.points == 5
        assert len(logs) == 1


def test_refund_ai_quota_once_returns_points_after_upstream_failure(app_module, user_factory):
    user = user_factory()

    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 12, "初始积分")
        membership = app_module.get_or_create_membership(user.id)
        membership.daily_ai_light_used_at = app_module.datetime.utcnow().strftime("%Y-%m-%d")
        app_module.db.session.commit()
        spend = app_module.spend_ai_quota_once(user.id, ["bazi"], 7)

        refund = app_module.refund_ai_quota_once(user.id, spend, "测试退回")

        membership = app_module.Membership.query.filter_by(user_id=user.id).one()
        refund_log = app_module.PointLog.query.filter_by(user_id=user.id, action="comprehensive_ai_refund").one()
        assert refund["ok"] is True
        assert refund["refunded"] == 7
        assert membership.points == 12
        assert refund_log.points == 7


def test_recharge_confirmation_only_pays_pending_order_once(app_module, user_factory):
    member = user_factory("buyer")

    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()

        first = app_module.confirm_recharge_order_once(order.id)
        second = app_module.confirm_recharge_order_once(order.id)

        assert first["ok"] is True
        assert first["user_id"] == member.id
        assert first["added"] == 60
        assert second["ok"] is False
        assert second["status"] == "paid"

        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=member.id, action="recharge").all()
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order.id)
        assert membership.points == 60
        assert len(logs) == 1
        assert refreshed.status == "paid"


def test_recharge_test_package_creates_one_cent_one_point_order(app_module, user_factory):
    member = user_factory("cent-buyer")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/create-order", json={
        "package_id": "test-cent",
        "pay_method": "hupijiao",
    })

    assert response.status_code == 503
    assert response.get_json()["error"] == "虎皮椒支付暂未配置"


def test_recharge_packages_include_points_and_ai_credit_packages(app_module):
    client = app_module.app.test_client()

    response = client.get("/api/recharge/packages")

    assert response.status_code == 200
    packages = response.get_json()["packages"]
    assert any(p["id"] == "test-cent" and p["points"] == 1 and p["package_type"] == "points" for p in packages)
    assert any(p["id"] == "ai-starter" and p["ai_single_credits"] == 10 for p in packages)
    assert any(p["id"] == "ai-combo" and p["ai_combo_credits"] == 20 for p in packages)


def test_paid_content_purchase_deducts_buyer_and_rewards_master(app_module, user_factory):
    buyer = user_factory("paid-buyer")
    author = user_factory("paid-author")

    with app_module.app.app_context():
        app_module.add_points(buyer.id, "admin_add", 100, "初始积分")
        master = app_module.Master(user_id=author.id, display_name="作者")
        app_module.db.session.add(master)
        app_module.db.session.flush()
        content = app_module.PaidContent(
            title="合婚报告",
            content_type="report",
            preview="预览",
            full_content="完整报告内容",
            price=30,
            master_id=master.id,
            category="bazi",
        )
        app_module.db.session.add(content)
        app_module.db.session.commit()
        content_id = content.id

    client = app_module.app.test_client()
    detail_before = client.get(f"/api/paid-contents/{content_id}")
    assert detail_before.status_code == 200
    assert detail_before.get_json()["purchased"] is False
    assert "fullContent" not in detail_before.get_json()

    with client.session_transaction() as sess:
        sess["_user_id"] = str(buyer.id)
        sess["_fresh"] = True

    purchase = client.post(f"/api/paid-contents/{content_id}/purchase")
    assert purchase.status_code == 200
    assert purchase.get_json()["pointsCost"] == 30

    detail_after = client.get(f"/api/paid-contents/{content_id}")
    assert detail_after.status_code == 200
    assert detail_after.get_json()["purchased"] is True
    assert detail_after.get_json()["fullContent"] == "完整报告内容"

    duplicate = client.post(f"/api/paid-contents/{content_id}/purchase")
    assert duplicate.status_code == 409

    with app_module.app.app_context():
        buyer_membership = app_module.Membership.query.filter_by(user_id=buyer.id).one()
        author_membership = app_module.Membership.query.filter_by(user_id=author.id).one()
        purchase_record = app_module.Purchase.query.filter_by(user_id=buyer.id, content_id=content_id).one()
        assert buyer_membership.points == 70
        assert author_membership.points == 21
        assert purchase_record.points_cost == 30


def test_master_can_create_paid_content_and_list_uses_preview_only(app_module, user_factory):
    ordinary = user_factory("ordinary-user")
    author = user_factory("master-user")

    with app_module.app.app_context():
        master = app_module.Master(user_id=author.id, display_name="专栏作者")
        app_module.db.session.add(master)
        app_module.db.session.commit()

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(ordinary.id)
        sess["_fresh"] = True

    denied = client.post("/api/paid-contents", json={
        "title": "普通用户内容",
        "fullContent": "不应创建",
        "price": 10,
    })
    assert denied.status_code == 403

    with client.session_transaction() as sess:
        sess["_user_id"] = str(author.id)
        sess["_fresh"] = True

    created = client.post("/api/paid-contents", json={
        "title": "择吉专栏",
        "contentType": "article",
        "preview": "只看摘要",
        "fullContent": "完整专栏正文",
        "price": 12,
        "category": "zeji",
    })
    assert created.status_code == 201
    content_id = created.get_json()["id"]

    listed = client.get("/api/paid-contents?category=zeji")
    assert listed.status_code == 200
    body = listed.get_json()
    assert body["total"] == 1
    assert body["contents"][0]["id"] == content_id
    assert body["contents"][0]["preview"] == "只看摘要"
    assert "fullContent" not in body["contents"][0]


def test_tool_run_meihua_creates_record_with_template_reading(app_module, user_factory):
    member = user_factory("tool-run-user")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/tool-run", json={
        "appType": "meihua",
        "name": "测事",
        "method": "number",
        "num1": 7,
        "num2": 12,
        "question": "这件事能成吗",
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert "梅花易数解读" in body["result"]
    assert "山雷颐" in body["result"]

    with app_module.app.app_context():
        record = app_module.db.session.get(app_module.Record, body["record_id"])
        assert record.user_id == member.id
        assert record.app_type == "meihua"
        assert "本卦:山雷颐" in record.question
        assert "梅花易数解读" in record.result_html


def test_tool_run_rejects_unknown_tool_type(app_module, user_factory):
    member = user_factory("bad-tool-user")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/tool-run", json={"appType": "unknown"})

    assert response.status_code == 400
    assert "不支持的工具类型" in response.get_json()["error"]


def test_records_are_user_scoped_and_detail_parses_qimen_json(app_module, user_factory):
    owner = user_factory("record-owner")
    other = user_factory("record-other")

    with app_module.app.app_context():
        owner_record = app_module.Record(
            user_id=owner.id,
            app_type="qimen",
            question="自己的奇门记录",
            result_html="<p>已解读</p>",
            qimen_json=json.dumps({"ju": "阳遁九局"}, ensure_ascii=False),
        )
        other_record = app_module.Record(
            user_id=other.id,
            app_type="qimen",
            question="别人的奇门记录",
            result_html="<p>不可见</p>",
        )
        app_module.db.session.add_all([owner_record, other_record])
        app_module.db.session.commit()
        owner_record_id = owner_record.id
        other_record_id = other_record.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(owner.id)
        sess["_fresh"] = True

    listed = client.get("/api/records")
    assert listed.status_code == 200
    listed_body = listed.get_json()
    assert listed_body["total"] == 1
    assert listed_body["records"][0]["id"] == owner_record_id
    assert listed_body["records"][0]["has_result"] is True

    detail = client.get(f"/api/records/{owner_record_id}")
    assert detail.status_code == 200
    detail_body = detail.get_json()
    assert detail_body["question"] == "自己的奇门记录"
    assert detail_body["qimen"] == {"ju": "阳遁九局"}

    denied = client.get(f"/api/records/{other_record_id}")
    assert denied.status_code == 403


def test_followups_and_collections_are_user_scoped(app_module, user_factory):
    owner = user_factory("content-owner")
    other = user_factory("content-other")

    with app_module.app.app_context():
        owner_record = app_module.Record(
            user_id=owner.id,
            app_type="meihua",
            question="自己的梅花记录",
            result_html="",
        )
        other_record = app_module.Record(
            user_id=other.id,
            app_type="meihua",
            question="别人的梅花记录",
            result_html="",
        )
        app_module.db.session.add_all([owner_record, other_record])
        app_module.db.session.commit()
        owner_record_id = owner_record.id
        other_record_id = other_record.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(owner.id)
        sess["_fresh"] = True

    denied_followup = client.post("/api/followups", json={
        "recordId": other_record_id,
        "note": "不应允许",
    })
    assert denied_followup.status_code == 403

    created_followup = client.post("/api/followups", json={
        "recordId": owner_record_id,
        "note": "一个月后回看",
        "feedback": "待验证",
    })
    assert created_followup.status_code == 201
    followup_id = created_followup.get_json()["id"]

    followups = client.get(f"/api/followups?record_id={owner_record_id}")
    assert followups.status_code == 200
    assert followups.get_json()["followups"][0]["note"] == "一个月后回看"

    updated_followup = client.put(f"/api/followups/{followup_id}", json={
        "feedback": "已验证",
    })
    assert updated_followup.status_code == 200

    created_collection = client.post("/api/collections", json={
        "targetType": "record",
        "targetId": owner_record_id,
    })
    assert created_collection.status_code == 201
    collection_id = created_collection.get_json()["id"]

    duplicate_collection = client.post("/api/collections", json={
        "targetType": "record",
        "targetId": owner_record_id,
    })
    assert duplicate_collection.status_code == 409

    collections = client.get("/api/collections?type=record")
    assert collections.status_code == 200
    assert collections.get_json()["collections"][0]["targetId"] == owner_record_id

    deleted_collection = client.delete(f"/api/collections/{collection_id}")
    assert deleted_collection.status_code == 200

    deleted_followup = client.delete(f"/api/followups/{followup_id}")
    assert deleted_followup.status_code == 200


def test_email_code_login_uses_shared_verification_store(app_module, user_factory):
    member = user_factory("email-code-user")
    email_addr = "email-code@example.com"

    with app_module.app.app_context():
        user = app_module.db.session.get(app_module.User, member.id)
        user.email = email_addr
        app_module.db.session.commit()

    import auth_channel_routes
    auth_channel_routes._store_code(f"email_{email_addr}", "123456")

    client = app_module.app.test_client()
    response = client.post("/api/email/login", json={
        "email": email_addr,
        "code": "123456",
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body["username"] == "email-code-user"


def test_sms_code_login_uses_shared_verification_store(app_module, user_factory):
    member = user_factory("sms-code-user")
    phone = "13900002222"

    with app_module.app.app_context():
        user = app_module.db.session.get(app_module.User, member.id)
        user.phone = phone
        app_module.db.session.commit()

    import auth_channel_routes
    auth_channel_routes._store_code(f"sms_{phone}", "222333")

    client = app_module.app.test_client()
    response = client.post("/api/sms/login", json={
        "phone": phone,
        "code": "222333",
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body["username"] == "sms-code-user"


def test_password_reset_by_bound_email_updates_password(app_module, user_factory):
    member = user_factory("reset-email-user")
    email_addr = "reset-email@example.com"

    with app_module.app.app_context():
        user = app_module.db.session.get(app_module.User, member.id)
        user.email = email_addr
        app_module.db.session.commit()

    import auth_channel_routes
    auth_channel_routes._store_code(f"email_{email_addr}", "654321")

    client = app_module.app.test_client()
    reset_response = client.post("/api/password/reset", json={
        "method": "email",
        "target": email_addr,
        "code": "654321",
        "new_password": "newpass123",
    })
    assert reset_response.status_code == 200
    assert reset_response.get_json()["ok"] is True

    login_response = client.post("/api/login", json={
        "username": email_addr,
        "password": "newpass123",
    })
    assert login_response.status_code == 200
    assert login_response.get_json()["username"] == "reset-email-user"


def test_password_reset_rejects_unbound_phone_after_valid_code(app_module):
    import auth_channel_routes
    auth_channel_routes._store_code("sms_13900001111", "123123")

    client = app_module.app.test_client()
    response = client.post("/api/password/reset", json={
        "method": "phone",
        "target": "13900001111",
        "code": "123123",
        "new_password": "newpass123",
    })

    assert response.status_code == 400
    assert "未绑定" in response.get_json()["error"]


def test_unconfigured_oauth_url_returns_actionable_error(app_module):
    import auth_channel_routes
    auth_channel_routes.QQ_APP_ID = ""
    client = app_module.app.test_client()

    response = client.get("/api/oauth/qq/url")

    assert response.status_code == 200
    body = response.get_json()
    assert body["url"] == ""
    assert "暂未配置" in body["error"]


def test_ai_credit_package_confirmation_adds_ai_quota_not_points(app_module, user_factory):
    member = user_factory("ai-credit-buyer")

    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="ai-starter",
            package_name="入门 AI 包",
            points=0,
            amount=9.9,
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

        result = app_module.confirm_recharge_order_once(order_id)

        assert result["ok"] is True
        assert result["added"] == 10
        assert result["credit_type"] == "ai_single_credits"
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        assert membership.points == 0
        assert membership.ai_single_credits == 10


def test_admin_recharge_requires_is_admin_flag(app_module, user_factory):
    fake_admin = user_factory("admin", is_admin=False)
    real_admin = user_factory("ops-admin", is_admin=True)
    member = user_factory("buyer")

    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(fake_admin.id)
        sess["_fresh"] = True

    denied = client.post("/api/admin/confirm-recharge", json={"order_id": order_id})
    assert denied.status_code == 403

    with app_module.app.app_context():
        order = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).first()
        assert order.status == "pending"
        assert membership is None

    with client.session_transaction() as sess:
        sess["_user_id"] = str(real_admin.id)
        sess["_fresh"] = True

    allowed = client.post("/api/admin/confirm-recharge", json={"order_id": order_id})
    assert allowed.status_code == 200
    assert allowed.get_json()["added"] == 60

    with app_module.app.app_context():
        audit = app_module.AdminAuditLog.query.filter_by(action="recharge_confirm").one()
        assert audit.admin_id == real_admin.id


def test_admin_can_refund_paid_recharge_once(app_module, user_factory):
    admin = user_factory("refund-admin", is_admin=True)
    member = user_factory("refund-member")
    with app_module.app.app_context():
        app_module.db.session.add(app_module.Membership(user_id=member.id, points=61))
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            amount_cents=990,
            pay_method="hupijiao",
            status="paid",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin.id)
        sess["_fresh"] = True

    refunded = client.post("/api/admin/confirm-recharge", json={"action": "refund", "order_id": order_id})
    duplicate = client.post("/api/admin/confirm-recharge", json={"action": "refund", "order_id": order_id})

    assert refunded.status_code == 200
    assert refunded.get_json()["refunded"] == 60
    assert duplicate.status_code == 400
    assert duplicate.get_json()["status"] == "refunded"
    with app_module.app.app_context():
        order = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        audit = app_module.AdminAuditLog.query.filter_by(action="recharge_refund").one()
        assert order.status == "refunded"
        assert membership.points == 1
        assert audit.admin_id == admin.id


def test_admin_can_add_points_by_username_and_users_endpoint_is_guarded(app_module, user_factory):
    member = user_factory("manual-user")
    fake_admin = user_factory("fake-admin", is_admin=False)
    real_admin = user_factory("real-admin", is_admin=True)
    client = app_module.app.test_client()

    with client.session_transaction() as sess:
        sess["_user_id"] = str(fake_admin.id)
        sess["_fresh"] = True

    denied = client.get("/api/admin/users")
    assert denied.status_code == 403

    denied_add = client.post("/api/admin/confirm-recharge", json={
        "action": "add",
        "user_identifier": member.username,
        "points": 100,
    })
    assert denied_add.status_code == 403

    with client.session_transaction() as sess:
        sess["_user_id"] = str(real_admin.id)
        sess["_fresh"] = True

    listed = client.get("/api/admin/users?q=manual-user")
    assert listed.status_code == 200
    listed_body = listed.get_json()
    assert listed_body["total"] == 1
    assert listed_body["users"][0]["username"] == "manual-user"
    assert listed_body["users"][0]["points"] == 0

    added = client.post("/api/admin/confirm-recharge", json={
        "action": "add",
        "user_identifier": member.username,
        "points": 100,
        "remark": "按用户名加分",
    })
    assert added.status_code == 200
    added_body = added.get_json()
    assert added_body["ok"] is True
    assert added_body["username"] == "manual-user"
    assert added_body["points"] == 100

    with app_module.app.app_context():
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        audit = app_module.AdminAuditLog.query.filter_by(action="points_add").one()
        assert membership.points == 100
        assert audit.admin_id == real_admin.id
        assert audit.target_id == member.id


def _enable_hupijiao(monkeypatch):
    monkeypatch.setenv("HUPIJIAO_ENABLED", "1")
    monkeypatch.setenv("HUPIJIAO_APPID", "test-appid")
    monkeypatch.setenv("HUPIJIAO_APPSECRET", "test-secret")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://example.com")


def _signed_hupijiao_notify(app_module, **overrides):
    payload = {
        "trade_order_id": "XC1",
        "total_fee": "9.90",
        "transaction_id": "txn-001",
        "open_order_id": "open-001",
        "order_title": "体验包",
        "status": "OD",
        "appid": "test-appid",
        "time": "1710000000",
        "nonce_str": "nonce001",
    }
    payload.update({k: str(v) for k, v in overrides.items()})
    payload["hash"] = app_module._hupijiao_sign(payload, "test-secret")
    return payload


def test_hupijiao_signature_skips_empty_values_and_hash(app_module):
    payload = {
        "appid": "test-appid",
        "hash": "ignored",
        "nonce_str": "abc",
        "optional": "",
        "time": "1710000000",
        "trade_order_id": "XC1",
    }

    assert app_module._hupijiao_sign(payload, "secret") == app_module.hashlib.md5(
        b"appid=test-appid&nonce_str=abc&time=1710000000&trade_order_id=XC1secret"
    ).hexdigest()


def test_hupijiao_create_order_requires_configuration(app_module, user_factory):
    member = user_factory("missing-hupijiao-config")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/create-order", json={
        "package_id": "starter",
        "pay_method": "hupijiao",
    })

    assert response.status_code == 503
    body = response.get_json()
    assert body["error"] == "虎皮椒支付暂未配置"
    assert "HUPIJIAO_APPSECRET" in body["missing"]
    assert "test-secret" not in json.dumps(body)


def test_hupijiao_create_order_returns_payment_urls(app_module, user_factory, monkeypatch):
    import recharge_routes
    _enable_hupijiao(monkeypatch)
    member = user_factory("hupijiao-buyer")

    captured = {}
    def fake_post(url, payload, timeout=10):
        captured["url"] = url
        captured["payload"] = payload
        return {"errcode": 0, "url": "https://pay.example/order", "url_qrcode": "https://pay.example/qr.png"}

    monkeypatch.setattr(recharge_routes, "_post_hupijiao_order", fake_post)
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/create-order", json={
        "package_id": "test-cent",
        "pay_method": "hupijiao",
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    assert body["pay_url"] == "https://pay.example/order"
    assert body["qrcode_url"] == "https://pay.example/qr.png"
    assert body["trade_order_id"].startswith("XC")
    assert captured["payload"]["notify_url"] == "https://example.com/api/recharge/hupijiao/notify"
    assert captured["payload"]["type"] == "WAP"
    assert captured["payload"]["wap_url"] == "https://example.com"
    assert captured["payload"]["wap_name"] == "时安解忧屋"
    assert captured["payload"]["hash"] == app_module._hupijiao_sign(captured["payload"], "test-secret")

    with app_module.app.app_context():
        order = app_module.RechargeOrder.query.filter_by(user_id=member.id).one()
        assert order.pay_method == "hupijiao"
        assert order.status == "pending"
        assert order.amount_cents == 1


def test_hupijiao_create_order_rate_limits_recent_pending_order(app_module, user_factory, monkeypatch):
    import recharge_routes
    _enable_hupijiao(monkeypatch)
    member = user_factory("hupijiao-fast-buyer")

    def fake_post(url, payload, timeout=10):
        return {"errcode": 0, "url": "https://pay.example/order", "url_qrcode": "https://pay.example/qr.png"}

    monkeypatch.setattr(recharge_routes, "_post_hupijiao_order", fake_post)
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    first = client.post("/api/recharge/create-order", json={
        "package_id": "test-cent",
        "pay_method": "hupijiao",
    })
    second = client.post("/api/recharge/create-order", json={
        "package_id": "test-cent",
        "pay_method": "hupijiao",
    })

    assert first.status_code == 200
    assert second.status_code == 429
    assert "下单过快" in second.get_json()["error"]


def test_alipay_recharge_verification_is_disabled(app_module, user_factory):
    member = user_factory("legacy-disabled-buyer")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/verify-payment", json={"order_id": 1})

    assert response.status_code == 410
    assert "已停用" in response.get_json()["error"]


def test_hupijiao_notify_rejects_bad_signature(app_module, user_factory, monkeypatch):
    _enable_hupijiao(monkeypatch)
    member = user_factory("bad-sign-buyer")
    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            pay_method="hupijiao",
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    payload = _signed_hupijiao_notify(app_module, trade_order_id=f"XC{order_id}")
    payload["hash"] = "bad"
    response = app_module.app.test_client().post("/api/recharge/hupijiao/notify", data=payload)

    assert response.status_code == 400
    assert response.text == "failed"
    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        assert refreshed.status == "pending"


def test_hupijiao_notify_rejects_mismatched_amount(app_module, user_factory, monkeypatch):
    _enable_hupijiao(monkeypatch)
    member = user_factory("bad-amount-buyer")
    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="standard",
            package_name="标准包",
            points=240,
            amount=29.9,
            pay_method="hupijiao",
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    payload = _signed_hupijiao_notify(app_module, trade_order_id=f"XC{order_id}", total_fee="9.90")
    response = app_module.app.test_client().post("/api/recharge/hupijiao/notify", data=payload)

    assert response.status_code == 400
    assert response.text == "failed"
    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).first()
        assert refreshed.status == "pending"
        assert membership is None


def test_hupijiao_notify_pays_points_once_and_accepts_duplicate(app_module, user_factory, monkeypatch):
    _enable_hupijiao(monkeypatch)
    member = user_factory("hupijiao-paid-buyer")
    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            pay_method="hupijiao",
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    payload = _signed_hupijiao_notify(app_module, trade_order_id=f"XC{order_id}", total_fee="9.90")
    client = app_module.app.test_client()
    first = client.post("/api/recharge/hupijiao/notify", data=payload)
    second = client.post("/api/recharge/hupijiao/notify", data=payload)

    assert first.status_code == 200
    assert first.text == "success"
    assert second.status_code == 200
    assert second.text == "success"
    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=member.id, action="recharge").all()
        assert refreshed.status == "paid"
        assert refreshed.payment_reference == "txn-001"
        assert membership.points == 60
        assert len(logs) == 1


def test_hupijiao_refund_callback_reverses_points_once(app_module, user_factory, monkeypatch):
    _enable_hupijiao(monkeypatch)
    member = user_factory("hupijiao-refund-buyer")
    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            amount_cents=990,
            pay_method="hupijiao",
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    client = app_module.app.test_client()
    paid_payload = _signed_hupijiao_notify(app_module, trade_order_id=f"XC{order_id}", total_fee="9.90")
    refund_payload = _signed_hupijiao_notify(app_module, trade_order_id=f"XC{order_id}", total_fee="9.90", status="CD")

    paid = client.post("/api/recharge/hupijiao/notify", data=paid_payload)
    first_refund = client.post("/api/recharge/hupijiao/notify", data=refund_payload)
    duplicate_refund = client.post("/api/recharge/hupijiao/notify", data=refund_payload)

    assert paid.status_code == 200
    assert first_refund.status_code == 200
    assert duplicate_refund.status_code == 200
    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=member.id).order_by(app_module.PointLog.id.asc()).all()
        assert refreshed.status == "refunded"
        assert refreshed.refund_reference == "txn-001"
        assert refreshed.refunded_at is not None
        assert membership.points == 0
        assert [log.action for log in logs] == ["recharge", "recharge_refund"]
        assert [log.points for log in logs] == [60, -60]


def test_hupijiao_refund_rejects_mismatched_amount(app_module, user_factory, monkeypatch):
    _enable_hupijiao(monkeypatch)
    member = user_factory("hupijiao-bad-refund")
    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            amount_cents=990,
            pay_method="hupijiao",
            status="paid",
        )
        app_module.db.session.add(app_module.Membership(user_id=member.id, points=60))
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    payload = _signed_hupijiao_notify(app_module, trade_order_id=f"XC{order_id}", total_fee="0.01", status="CD")
    response = app_module.app.test_client().post("/api/recharge/hupijiao/notify", data=payload)

    assert response.status_code == 400
    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        assert refreshed.status == "paid"
        assert membership.points == 60


def test_hupijiao_refund_fails_when_points_already_spent(app_module, user_factory, monkeypatch):
    _enable_hupijiao(monkeypatch)
    member = user_factory("hupijiao-refund-insufficient")
    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            amount_cents=990,
            pay_method="hupijiao",
            status="paid",
        )
        app_module.db.session.add(app_module.Membership(user_id=member.id, points=10))
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    payload = _signed_hupijiao_notify(app_module, trade_order_id=f"XC{order_id}", total_fee="9.90", status="CD")
    response = app_module.app.test_client().post("/api/recharge/hupijiao/notify", data=payload)

    assert response.status_code == 400
    assert response.text == "failed"
    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=member.id, action="recharge_refund").all()
        assert refreshed.status == "paid"
        assert membership.points == 10
        assert logs == []


def test_hupijiao_reconcile_refunds_paid_order_from_query(app_module, user_factory, monkeypatch):
    import recharge_routes
    _enable_hupijiao(monkeypatch)
    member = user_factory("hupijiao-query-refund")
    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            amount_cents=990,
            pay_method="hupijiao",
            status="paid",
            payment_reference="txn-query-001",
        )
        app_module.db.session.add(app_module.Membership(user_id=member.id, points=60))
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

        def fake_query(config, remote_order):
            assert config["query_url"].endswith("/payment/query.html")
            assert remote_order.id == order_id
            return {
                "ok": True,
                "status": "CD",
                "reference": "txn-query-001",
                "data": {
                    "trade_order_id": f"XC{order_id}",
                    "transaction_id": "txn-query-001",
                    "open_order_id": "open-query-001",
                    "status": "CD",
                },
            }

        result = recharge_routes.reconcile_hupijiao_refunds(
            app_module.db,
            app_module.refund_recharge_order_once,
            query_order_func=fake_query,
            order_id=order_id,
        )

        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        refund_log = app_module.PointLog.query.filter_by(user_id=member.id, action="recharge_refund").one()
        assert result["ok"] is True
        assert result["checked"] == 1
        assert result["refunded"][0]["order_id"] == order_id
        assert refreshed.status == "refunded"
        assert refreshed.refund_reference == "txn-query-001"
        assert refreshed.refunded_at is not None
        assert json.loads(refreshed.refund_proof)["source"] == "query_reconcile"
        assert membership.points == 0
        assert refund_log.points == -60
        assert refund_log.dedupe_key == f"refund_order:{order_id}"


def test_hupijiao_reconcile_rejects_mismatched_payment_reference(app_module, user_factory, monkeypatch):
    import recharge_routes
    _enable_hupijiao(monkeypatch)
    member = user_factory("hupijiao-query-mismatch")
    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            amount_cents=990,
            pay_method="hupijiao",
            status="paid",
            payment_reference="txn-local",
        )
        app_module.db.session.add(app_module.Membership(user_id=member.id, points=60))
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

        def fake_query(config, remote_order):
            return {
                "ok": True,
                "status": "CD",
                "reference": "txn-other",
                "data": {"status": "CD", "transaction_id": "txn-other"},
            }

        result = recharge_routes.reconcile_hupijiao_refunds(
            app_module.db,
            app_module.refund_recharge_order_once,
            query_order_func=fake_query,
            order_id=order_id,
        )

        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=member.id, action="recharge_refund").all()
        assert result["failed"][0]["error"] == "支付流水号不匹配"
        assert refreshed.status == "paid"
        assert membership.points == 60
        assert logs == []


def test_hupijiao_notify_adds_ai_quota_not_points(app_module, user_factory, monkeypatch):
    _enable_hupijiao(monkeypatch)
    member = user_factory("hupijiao-ai-buyer")
    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="ai-starter",
            package_name="入门 AI 包",
            points=0,
            amount=9.9,
            pay_method="hupijiao",
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    payload = _signed_hupijiao_notify(app_module, trade_order_id=f"XC{order_id}", total_fee="9.90")
    response = app_module.app.test_client().post("/api/recharge/hupijiao/notify", data=payload)

    assert response.status_code == 200
    with app_module.app.app_context():
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=member.id, action="ai_credit_recharge").all()
        assert membership.points == 0
        assert membership.ai_single_credits == 10
        assert len(logs) == 1


def test_migrate_db_promotes_legacy_first_user_when_no_admin_exists(app_module, user_factory):
    user = user_factory("legacy-owner", is_admin=False)
    assert user.id == 1

    app_module.migrate_db()

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.User, user.id)
        assert refreshed.is_admin is True


def test_admin_dashboard_endpoints_require_admin_and_return_operational_data(app_module, user_factory):
    from models import Report

    admin = user_factory("ops-admin", is_admin=True)
    member = user_factory("member")

    with app_module.app.app_context():
        app_module.add_points(member.id, "admin_add", 12, "初始积分")
        post = app_module.Post(
            user_id=member.id,
            title="需要审核的帖子",
            content="后台列表应能看到这条内容",
            category="share",
            is_hidden=True,
        )
        app_module.db.session.add(post)
        app_module.db.session.flush()
        report = Report(user_id=member.id, target_type="post", target_id=post.id, reason="spam")
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            status="pending",
        )
        app_module.db.session.add(report)
        app_module.db.session.add(order)
        app_module.db.session.commit()

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    denied = client.get("/api/admin/summary")
    assert denied.status_code == 403

    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin.id)
        sess["_fresh"] = True

    summary = client.get("/api/admin/summary")
    assert summary.status_code == 200
    assert summary.get_json()["pending_reports"] == 1

    users = client.get("/api/admin/users?q=member")
    assert users.status_code == 200
    assert users.get_json()["users"][0]["points"] == 12

    posts = client.get("/api/admin/posts?status=hidden")
    assert posts.status_code == 200
    assert posts.get_json()["posts"][0]["isHidden"] is True

    orders = client.get("/api/admin/recharge/orders?status=pending")
    assert orders.status_code == 200
    assert orders.get_json()["orders"][0]["points_amount"] == 60


def test_admin_actions_write_and_expose_audit_logs(app_module, user_factory):
    admin = user_factory("ops-admin", is_admin=True)
    member = user_factory("member")

    with app_module.app.app_context():
        post = app_module.Post(
            user_id=member.id,
            title="审计测试帖子",
            content="管理员改动需要记录",
            category="share",
        )
        app_module.db.session.add(post)
        app_module.db.session.commit()
        post_id = post.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin.id)
        sess["_fresh"] = True

    changed = client.post(f"/api/admin/posts/{post_id}/hide", json={"hidden": True})
    assert changed.status_code == 200

    logs = client.get("/api/admin/audit-logs")
    assert logs.status_code == 200
    data = logs.get_json()["logs"]
    assert data[0]["action"] == "post_hide"
    assert data[0]["admin_id"] == admin.id
    assert data[0]["target_id"] == post_id
    assert data[0]["detail"]["hidden"] is True


def test_admin_can_add_points_by_username_identifier(app_module, user_factory):
    admin = user_factory("ops-admin", is_admin=True)
    member = user_factory("19195566287")

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin.id)
        sess["_fresh"] = True

    resp = client.post(
        "/api/admin/confirm-recharge",
        json={
            "action": "add",
            "user_identifier": "19195566287",
            "points": 1000,
            "remark": "后台按用户名加积分",
        },
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["user_id"] == member.id
    assert body["points"] == 1000

    with app_module.app.app_context():
        log = app_module.PointLog.query.filter_by(user_id=member.id, action="admin_add").one()
        assert log.points == 1000
        assert "后台按用户名加积分" in log.description


def test_admin_change_password_requires_admin_current_password_and_audits(app_module, user_factory):
    admin = user_factory("ops-admin", is_admin=True)
    member = user_factory("member")

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    denied = client.post(
        "/api/admin/change-password",
        json={
            "old_password": "secret123",
            "new_password": "new-secret-12345",
            "confirm_password": "new-secret-12345",
        },
    )
    assert denied.status_code == 403

    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin.id)
        sess["_fresh"] = True

    wrong_old = client.post(
        "/api/admin/change-password",
        json={
            "old_password": "wrong",
            "new_password": "new-secret-12345",
            "confirm_password": "new-secret-12345",
        },
    )
    assert wrong_old.status_code == 403

    too_short = client.post(
        "/api/admin/change-password",
        json={
            "old_password": "secret123",
            "new_password": "short",
            "confirm_password": "short",
        },
    )
    assert too_short.status_code == 400

    changed = client.post(
        "/api/admin/change-password",
        json={
            "old_password": "secret123",
            "new_password": "new-secret-12345",
            "confirm_password": "new-secret-12345",
        },
    )
    assert changed.status_code == 200

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.User, admin.id)
        assert check_password_hash(refreshed.password_hash, "new-secret-12345")
        audit = app_module.AdminAuditLog.query.filter_by(action="admin_password_change").one()
        assert audit.admin_id == admin.id
        assert audit.target_type == "user"
        assert audit.target_id == admin.id
        assert "new-secret-12345" not in audit.detail


def test_zeji_api_returns_direct_analysis_for_public_page(app_module):
    client = app_module.app.test_client()

    response = client.post(
        "/api/zeji",
        json={
            "zejiType": "搬家",
            "startDate": "2024-02-10",
            "endDate": "2024-02-12",
            "addr": "北京",
            "name": "择吉分析",
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["zejiType"] == "搬家"
    assert data["startDate"] == "2024-02-10"
    assert data["endDate"] == "2024-02-12"
    assert "2024-02-10" in data["result"]
    assert "搬家" in data["result"]
    assert "民俗文化参考" in data["result"]


def test_search_returns_only_current_user_records(app_module, user_factory):
    owner = user_factory("search-owner")
    other = user_factory("search-other")

    with app_module.app.app_context():
        app_module.db.session.add_all([
            app_module.Record(user_id=owner.id, app_type="qimen", question="我要找工作", result_html="ok"),
            app_module.Record(user_id=other.id, app_type="qimen", question="我要找工作", result_html="hidden"),
        ])
        app_module.db.session.commit()

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(owner.id)

    response = client.get("/api/search?q=找工作&type=qimen")

    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 1
    assert data["results"][0]["question"] == "我要找工作"
    assert data["results"][0]["hasResult"] is True


def test_upload_saves_allowed_file_for_logged_in_user(app_module, user_factory, tmp_path):
    user = user_factory("upload-owner")
    upload_dir = tmp_path / "uploads"
    app_module.app.config["UPLOAD_FOLDER"] = str(upload_dir)
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

    response = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(PNG_1X1), "proof.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["url"].startswith("/static/uploads/")
    assert (upload_dir / data["filename"]).exists()


def test_upload_rejects_disguised_image_file(app_module, user_factory, tmp_path):
    user = user_factory("upload-fake")
    upload_dir = tmp_path / "uploads"
    app_module.app.config["UPLOAD_FOLDER"] = str(upload_dir)
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

    response = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(b"not a real image"), "proof.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "图片内容无法识别"
    assert not upload_dir.exists()
