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
