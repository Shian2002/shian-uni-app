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
        "pay_method": "alipay_qr",
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    assert body["points_amount"] == 1
    assert body["price"] == 0.01

    with app_module.app.app_context():
        order = app_module.RechargeOrder.query.filter_by(user_id=member.id).one()
        assert order.package_id == "test-cent"
        assert order.package_name == "测试包"
        assert order.points == 1
        assert order.amount == 0.01
        assert order.status == "pending"


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


def test_alipay_recharge_verification_records_proof_without_auto_confirm(app_module, user_factory):
    member = user_factory("alipay-buyer")

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
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/verify-payment", json={
        "order_id": order_id,
        "paid_amount": 9.9,
        "payment_reference": "2026053113580001",
    })
    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    assert body["status"] == "pending"

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).first()
        logs = app_module.PointLog.query.filter_by(user_id=member.id, action="recharge").all()
        assert refreshed.status == "pending"
        assert refreshed.pay_method == "alipay_qr"
        assert refreshed.payment_reference == "2026053113580001"
        assert membership is None
        assert logs == []


def test_alipay_recharge_verification_can_auto_confirm_when_enabled(app_module, user_factory, monkeypatch):
    monkeypatch.setenv("ALIPAY_QR_AUTO_CONFIRM", "1")
    member = user_factory("auto-alipay-buyer")

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
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/verify-payment", json={
        "order_id": order_id,
        "paid_amount": 9.9,
        "payment_reference": "2026053113580001",
    })
    duplicate = client.post("/api/recharge/verify-payment", json={
        "order_id": order_id,
        "paid_amount": 9.9,
        "payment_reference": "2026053113580001",
    })

    assert response.status_code == 200
    assert response.get_json()["added"] == 60
    assert duplicate.status_code == 400

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        logs = app_module.PointLog.query.filter_by(user_id=member.id, action="recharge").all()
        assert refreshed.status == "paid"
        assert membership.points == 60
        assert len(logs) == 1


def test_small_recharge_screenshot_auto_confirms_when_amount_and_receiver_match(app_module, user_factory):
    member = user_factory("small-auto-buyer")

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
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/verify-payment", json={
        "order_id": order_id,
        "payment_proof_text": "支付宝支付成功 收款方 时安解忧屋 支付金额 ¥9.90",
        "payment_proof_hash": "proof-small-unique",
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "paid"
    assert body["auto_confirmed"] is True
    assert body["added"] == 60

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        assert refreshed.status == "paid"
        assert refreshed.payment_reference == "proof-small-unique"
        assert membership.points == 60


def test_small_recharge_ignores_alipay_reward_numbers_when_matching_amount(app_module, user_factory):
    member = user_factory("small-noisy-alipay-buyer")

    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="test-cent",
            package_name="测试包",
            points=1,
            amount=0.01,
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    noisy_proof_text = "\n".join([
        "23:12:20 58.3KB/s 5G 66",
        "支付成功",
        "¥0.01",
        "时安解忧屋 ¥0.01",
        "支付宝积分+2 账单贴纸+1",
        "最高领20元红包",
        "完成",
    ])
    response = client.post("/api/recharge/verify-payment", json={
        "order_id": order_id,
        "payment_proof_text": noisy_proof_text,
        "payment_proof_hash": "proof-small-noisy-unique",
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "paid"
    assert body["auto_confirmed"] is True
    assert body["added"] == 1

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        assert refreshed.status == "paid"
        assert membership.points == 1


def test_spaced_ocr_receiver_text_still_matches(app_module):
    assert app_module._payment_text_matches_receiver("支 付 成 功\n时 安 解 忧 屋 ¥0.01") is True


def test_large_recharge_screenshot_waits_for_manual_confirmation(app_module, user_factory):
    member = user_factory("large-manual-buyer")

    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="premium",
            package_name="畅享包",
            points=650,
            amount=68,
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/verify-payment", json={
        "order_id": order_id,
        "payment_proof_text": "支付宝支付成功 收款方 时安解忧屋 支付金额 ¥68.00",
        "payment_proof_hash": "proof-large-unique",
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "pending"
    assert body["auto_confirmed"] is False
    assert "10:00 - 24:00" in body["message"]

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).first()
        assert refreshed.status == "pending"
        assert refreshed.payment_reference == "proof-large-unique"
        assert membership is None


def test_recharge_screenshot_proof_cannot_be_reused(app_module, user_factory):
    member = user_factory("duplicate-proof-buyer")

    with app_module.app.app_context():
        first_order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            status="paid",
            payment_reference="duplicate-proof-hash",
        )
        second_order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="starter",
            package_name="体验包",
            points=60,
            amount=9.9,
            status="pending",
        )
        app_module.db.session.add_all([first_order, second_order])
        app_module.db.session.commit()
        order_id = second_order.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/verify-payment", json={
        "order_id": order_id,
        "payment_proof_text": "支付宝支付成功 收款方 时安解忧屋 支付金额 ¥9.90",
        "payment_proof_hash": "duplicate-proof-hash",
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "付款截图已提交过"


def test_recharge_screenshot_rejects_disguised_image_file(app_module, user_factory):
    member = user_factory("fake-proof-buyer")

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
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post(
        "/api/recharge/verify-payment",
        data={
            "order_id": str(order_id),
            "paid_amount": "9.9",
            "file": (io.BytesIO(b"not a real image"), "proof.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "图片内容无法识别"


def test_alipay_recharge_verification_rejects_mismatched_amount(app_module, user_factory):
    member = user_factory("mismatch-buyer")

    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="standard",
            package_name="标准包",
            points=240,
            amount=29.9,
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/verify-payment", json={
        "order_id": order_id,
        "paid_amount": 9.9,
        "payment_reference": "wrong-amount",
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "付款金额与订单金额不一致"

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).first()
        assert refreshed.status == "pending"
        assert membership is None


def test_recharge_screenshot_rejects_explicit_mismatched_amount(app_module, user_factory):
    member = user_factory("proof-mismatch-buyer")

    with app_module.app.app_context():
        order = app_module.RechargeOrder(
            user_id=member.id,
            package_id="test-cent",
            package_name="测试包",
            points=1,
            amount=0.01,
            status="pending",
        )
        app_module.db.session.add(order)
        app_module.db.session.commit()
        order_id = order.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/verify-payment", json={
        "order_id": order_id,
        "payment_proof_text": "支付宝支付成功 收款方 时安解忧屋 支付金额 ¥0.02",
        "payment_proof_hash": "proof-explicit-mismatch",
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "付款金额与订单金额不一致"

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.RechargeOrder, order_id)
        membership = app_module.Membership.query.filter_by(user_id=member.id).first()
        assert refreshed.status == "pending"
        assert membership is None


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
