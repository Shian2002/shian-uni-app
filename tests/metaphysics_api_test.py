import importlib
import json
import os
import sys

import pytest
from types import SimpleNamespace
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
def client(app_module):
    return app_module.app.test_client()


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


def _post_json(client, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code == 200
    return response.get_json()


def test_bazi_and_ziwei_share_fixed_sample_four_pillars(client):
    bazi = _post_json(
        client,
        "/api/bazi/paipan",
        {
            "name": "样例",
            "gender": "男",
            "calType": "公历",
            "birthTime": "199001271030",
            "birthAddr": "北京",
            "birthLng": 116.4074,
            "useSolarTime": True,
            "_replay": True,
        },
    )

    pillars = bazi["four_pillars"]
    bazi_pillar_text = " ".join(pillars[key]["gan_zhi"] for key in ("year", "month", "day", "hour"))
    assert bazi["success"] is True
    assert bazi_pillar_text == "己巳 丁丑 壬辰 乙巳"
    assert bazi["birth_solar"] == "1990-01-27 10:02"
    assert bazi["birth_lunar"] == "己巳年正月初一 巳时"
    assert bazi["pillar_source"] in ("本地计算", "问真八字")

    ziwei = _post_json(
        client,
        "/api/ziwei/pan",
        {
            "year": 1990,
            "month": 1,
            "day": 27,
            "hour": 10,
            "minute": 30,
            "gender": "男",
            "date_type": "solar",
            "longitude": 116.4074,
        },
    )

    ziwei_data = ziwei["data"]
    assert ziwei["code"] == 0
    assert ziwei_data["basic_info"]["chinese_date"] == bazi_pillar_text
    assert ziwei_data["basic_info"]["lunar_date"] == "一九九〇年正月初一"
    assert ziwei_data["basic_info"]["shichen"] == "巳时"
    assert ziwei_data["core_palace"]["soul_star"] == "文曲"
    assert len(ziwei_data["twelve_palaces"]) == 12
    assert ziwei_data["display_meta"]["chart_method"] == "三合盘"
    assert ziwei_data["display_meta"]["true_solar_enabled"] is True
    assert ziwei_data["display_meta"]["true_solar_time"].startswith("1990-01-27 10:")
    assert ziwei_data["twelve_palaces"][0]["ganzhi"]
    assert len(ziwei_data["decadal_overview"]) == 12

    ziwei_flow = _post_json(
        client,
        "/api/ziwei/horoscope",
        {
            "year": 1990,
            "month": 1,
            "day": 27,
            "hour": 10,
            "minute": 30,
            "gender": "男",
            "date_type": "solar",
            "longitude": 116.4074,
            "target_date": "2028-04-25",
        },
    )
    flow_data = ziwei_flow["data"]
    assert ziwei_flow["code"] == 0
    assert flow_data["display_meta"]["true_solar_enabled"] is True
    assert flow_data["horoscope"]["monthly"]["name"] == "流月"
    assert flow_data["horoscope"]["monthly"]["ganzhi"]
    assert isinstance(flow_data["horoscope"]["monthly"]["index"], int)


def test_qimen_meihua_and_liuyao_fixed_samples(client):
    qimen = _post_json(
        client,
        "/api/qimen/paipan",
        {"year": 2024, "month": 2, "day": 4, "hour": 16, "minute": 30, "panType": 1},
    )
    assert qimen["fourPillars"] == {"year": "甲辰", "month": "丙寅", "day": "戊戌", "hour": "庚申"}
    assert qimen["ju"] == "阳遁五局中元"
    assert qimen["solarTerm"] == "立春"
    assert qimen["zhiFu"] == "值符天蓬落兑七宫(西)"
    assert qimen["zhiShi"] == "值使休门落兑七宫(西)"
    assert len(qimen["palaces"]) == 9

    meihua = _post_json(client, "/api/meihua/paipan", {"method": "number", "num1": 7, "num2": 12})
    assert meihua["success"] is True
    assert meihua["benGua"]["name"] == "山雷颐"
    assert meihua["huGua"]["name"] == "坤为地"
    assert meihua["bianGua"]["name"] == "山地剥"
    assert meihua["dongYao"] == 1

    liuyao = _post_json(
        client,
        "/api/liuyao/paipan",
        {
            "mode": "manual",
            "question": "测试",
            "tosses": [[2, 2, 2], [2, 2, 3], [2, 3, 3], [3, 3, 3], [2, 3, 2], [3, 2, 3]],
        },
    )
    assert liuyao["本卦"] == "泽水困"
    assert liuyao["变卦"] == "水泽节"
    assert liuyao["世爻"] == 1
    assert liuyao["应爻"] == 4
    assert [idx + 1 for idx, yao in enumerate(liuyao["六爻"]) if yao["is_moving"]] == [1, 4]


def test_tarot_huangli_zeji_and_calendar_fixed_samples(client):
    tarot_verify = client.get("/api/tarot/verify")
    assert tarot_verify.status_code == 200
    assert tarot_verify.get_json() == {"major": 22, "minor": 56, "total": 78, "valid": True}

    tarot_spreads = client.get("/api/tarot/spreads")
    assert tarot_spreads.status_code == 200
    spreads = tarot_spreads.get_json()["data"]
    assert [item["key"] for item in spreads] == [
        "single",
        "three",
        "time_flow",
        "hexagram",
        "celtic_cross",
        "relationship",
    ]

    huangli = client.get("/api/huangli?date=2024-02-10")
    assert huangli.status_code == 200
    huangli_data = huangli.get_json()
    assert huangli_data["lunarDate"] == "2024年1月1日"
    assert huangli_data["ganZhiYear"] == "甲辰年"
    assert huangli_data["ganZhiMonth"] == "丙寅"
    assert huangli_data["ganZhiDay"] == "甲辰"
    assert huangli_data["source"] == "local"

    huangli_month = client.get("/api/huangli/month?year=2024&month=2")
    assert huangli_month.status_code == 200
    month_days = huangli_month.get_json()["days"]
    assert len(month_days) == 29
    assert month_days[9]["solarDate"] == "2024-02-10"
    assert month_days[9]["lunarDayName"] == "初一"

    solar_to_lunar = _post_json(client, "/api/bazi/solar-to-lunar", {"year": 2024, "month": 2, "day": 10})
    assert solar_to_lunar == {"success": True, "year": 2024, "month": 1, "day": 1, "isLeap": False}

    lunar_to_solar = _post_json(
        client,
        "/api/bazi/lunar-to-solar",
        {"year": 2024, "month": 1, "day": 1, "isLeap": False},
    )
    assert lunar_to_solar == {"success": True, "year": 2024, "month": 2, "day": 10}

    liu_yue = _post_json(client, "/api/bazi/liu-yue", {"year": 2024, "dayGan": "甲"})
    assert len(liu_yue["liu_yue"]) == 12
    assert liu_yue["liu_yue"][0]["gan_zhi"] == "丙寅"

    liu_ri = _post_json(client, "/api/bazi/liu-ri", {"year": 2024, "month": 2, "dayGan": "甲"})
    assert len(liu_ri["liu_ri"]) == 29
    assert liu_ri["liu_ri"][9]["gan_zhi"] == "甲辰"

    liu_shi = _post_json(client, "/api/bazi/liu-shi", {"dayGan": "甲", "dayZhuGan": "甲"})
    assert len(liu_shi["liu_shi"]) == 12
    assert liu_shi["liu_shi"][0]["gan_zhi"] == "甲子"

    zeji = _post_json(
        client,
        "/api/zeji",
        {"zejiType": "搬家", "startDate": "2024-02-10", "endDate": "2024-02-12", "addr": "北京"},
    )
    assert zeji["success"] is True
    assert [item["date"] for item in zeji["bestDays"]] == ["2024-02-12", "2024-02-10", "2024-02-11"]
    assert "民俗文化参考" in zeji["result"]


def test_comprehensive_recommend_tools_rules(app_module, user_factory):
    user = user_factory("recommend-user")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    samples = [
        ("我要不要跳槽", ["bazi", "qimen"]),
        ("这个合作靠谱吗", ["qimen", "liuyao"]),
        ("他还会不会回来", ["liuyao", "meihua", "tarot"]),
        ("什么时候结婚", ["bazi", "ziwei"]),
        ("哪天开业好", ["zeji"]),
        ("最近整体怎么样", ["bazi", "qimen"]),
    ]
    for question, expected in samples:
        response = client.post("/api/comprehensive/recommend-tools", json={"question": question})
        assert response.status_code == 200
        data = response.get_json()
        assert data["tool_models"] == expected
        assert data["estimated_cost"] > 0


def test_bazi_paipan_syncs_logged_in_profile_with_extended_meta(app_module, user_factory):
    user = user_factory("profile-sync-user")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    response = client.post(
        "/api/bazi/paipan",
        json={
            "name": "档案样例",
            "gender": "女",
            "calType": "公历",
            "birthTime": "199001271030",
            "birthAddr": "北京",
            "birthLng": 116.4074,
            "birthLat": 39.9042,
            "useSolarTime": True,
            "nightZiMode": "夜子时不换日",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    profiles_response = client.get("/api/profiles?sort=last_used")
    assert profiles_response.status_code == 200
    profiles = profiles_response.get_json()["profiles"]
    synced = next(p for p in profiles if p["name"] == "档案样例")
    assert synced["source"] == "bazi_record"
    assert synced["meta"]["birthLng"] == 116.4074
    assert synced["meta"]["birthLat"] == 39.9042
    assert synced["meta"]["useSolarTime"] is True
    assert "four_pillars" in synced["meta"]


def test_profiles_list_backfills_existing_bazi_records(app_module, user_factory):
    user = user_factory("profile-backfill-user")
    with app_module.app.app_context():
        record = app_module.BaziRecord(
            user_id=user.id,
            name="旧八字记录",
            gender="男",
            cal_type="公历",
            birth_time="199001271030",
            birth_addr="北京",
            pillars="己巳丁丑壬辰乙巳",
            record_type="paipan",
            params_json=json.dumps({"birthLng": 116.4074, "useSolarTime": True}, ensure_ascii=False),
        )
        app_module.db.session.add(record)
        app_module.db.session.commit()
        record_id = record.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    response = client.get("/api/profiles?sort=last_used")
    assert response.status_code == 200
    profiles = response.get_json()["profiles"]
    synced = next(p for p in profiles if p["name"] == "旧八字记录")
    assert synced["source"] == "bazi_record"
    assert synced["sourceRecordId"] == record_id
    assert synced["meta"]["birthLng"] == 116.4074
