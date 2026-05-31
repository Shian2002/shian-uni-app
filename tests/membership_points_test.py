import importlib
import os
import sys
from types import SimpleNamespace

import pytest
from werkzeug.security import check_password_hash, generate_password_hash


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    db_path = tmp_path / "test-tianji.db"
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("TIANJI_SECRET_KEY", "test-secret-key")
    sys.path.insert(0, backend_dir)
    try:
        module = importlib.import_module("app")
        module.app.config.update(TESTING=True)
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
        assert audit.target_type == "recharge_order"
        assert audit.target_id == order_id


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
