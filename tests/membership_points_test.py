import importlib
import os
import sys
from types import SimpleNamespace

import pytest
from werkzeug.security import generate_password_hash


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


def test_migrate_db_promotes_legacy_first_user_when_no_admin_exists(app_module, user_factory):
    user = user_factory("legacy-owner", is_admin=False)
    assert user.id == 1

    app_module.migrate_db()

    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.User, user.id)
        assert refreshed.is_admin is True
