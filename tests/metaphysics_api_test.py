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


def _sse_payloads(response):
    text = response.get_data(as_text=True)
    payloads = []
    for part in text.split("\n\n"):
        line = next((item for item in part.splitlines() if item.startswith("data: ")), "")
        if line:
            payloads.append(json.loads(line[6:]))
    return payloads


def test_bazi_and_ziwei_share_fixed_sample_four_pillars(client):
    ziwei_info = client.get("/api/ziwei/info")
    assert ziwei_info.status_code == 200
    ziwei_info_data = ziwei_info.get_json()["data"]
    assert ziwei_info_data["name"] == "紫微斗数"
    assert len(ziwei_info_data["shichen"]) == 12

    ziwei_shichen = client.get("/api/ziwei/shichen")
    assert ziwei_shichen.status_code == 200
    assert ziwei_shichen.get_json()["data"]["shichen"][0]["name"] == "子时"

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

    meihua_same_gua = _post_json(client, "/api/meihua/paipan", {"method": "number", "num1": 3, "num2": 3})
    assert meihua_same_gua["success"] is True
    assert meihua_same_gua["benGua"]["name"] == "离为火"
    assert "离离卦" not in json.dumps(meihua_same_gua, ensure_ascii=False)

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


def test_meihua_ask_stream_uses_split_route_and_creates_record(app_module, user_factory, monkeypatch):
    member = user_factory("meihua-stream-user")
    with app_module.app.app_context():
        app_module.add_points(member.id, "admin_add", 20, "测试积分")

    monkeypatch.setattr(app_module, "deepseek_available", lambda: True)
    monkeypatch.setattr(app_module, "get_reading_stream", lambda messages: iter([("梅花解读正文", None)]))

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/meihua/ask/stream", json={
        "question": "这件事能成吗",
        "method": "number",
        "num1": 7,
        "num2": 12,
    })

    assert response.status_code == 200
    payloads = _sse_payloads(response)
    assert {"content": "梅花解读正文"} in payloads
    assert any(item.get("length") == len("梅花解读正文") for item in payloads)

    with app_module.app.app_context():
        record = app_module.Record.query.filter_by(user_id=member.id, app_type="meihua").one()
        assert record.question == "这件事能成吗"
        assert record.result_html == "梅花解读正文"


def test_liuyao_ask_stream_sends_paipan_from_split_route(app_module, user_factory, monkeypatch):
    member = user_factory("liuyao-stream-user")
    with app_module.app.app_context():
        app_module.add_points(member.id, "admin_add", 20, "测试积分")

    monkeypatch.setattr(app_module, "deepseek_available", lambda: True)
    monkeypatch.setattr(app_module, "get_reading_stream", lambda messages: iter([("六爻解读正文", None)]))

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/liuyao/ask/stream", json={
        "question": "合作能成吗",
        "mode": "manual",
        "tosses": [[2, 2, 2], [2, 2, 3], [2, 3, 3], [3, 3, 3], [2, 3, 2], [3, 2, 3]],
    })

    assert response.status_code == 200
    payloads = _sse_payloads(response)
    assert any(item.get("本卦") == "泽水困" and item.get("变卦") == "水泽节" for item in payloads)
    assert {"content": "六爻解读正文"} in payloads


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


def test_comprehensive_new_conversation_returns_full_bazi_artifact(app_module, user_factory, monkeypatch):
    user = user_factory("artifact-new-user")
    monkeypatch.setattr(app_module, "get_reading_stream", lambda messages: iter([("职业方向可以结合命局判断。", None)]))
    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 100, "测试积分")

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    response = client.post("/api/comprehensive/ask/stream", json={
        "question": "我适合什么工作",
        "reading_mode": "standard",
        "profile": {
            "name": "职业样例",
            "gender": "男",
            "calType": "公历",
            "birthTime": "199001271030",
            "birthAddr": "北京",
            "meta": {"birthLng": 116.4074, "useSolarTime": True},
        },
        "auto_select_tools": True,
    })

    assert response.status_code == 200
    payloads = _sse_payloads(response)
    paipan_done = next(p for p in payloads if p.get("stage") == "paipan_done")
    assert "bazi.basic" in paipan_done["artifacts"]
    assert paipan_done["artifact_actions"]["added"] == ["bazi.basic"]
    assert paipan_done["artifact_actions"]["reused"] == []
    basic = paipan_done["artifacts"]["bazi.basic"]
    assert basic["display"] == "bazi_basic"
    assert basic["data"]["four_pillars"]["year"]["gan_zhi"] == "己巳"
    done = payloads[-1]
    assert "bazi.basic" in done["artifacts"]


def test_comprehensive_multi_profile_unwraps_artifacts_and_yun(app_module, user_factory, monkeypatch):
    user = user_factory("artifact-multi-user")
    monkeypatch.setattr(app_module, "get_reading_stream", lambda messages: iter([("今年运势要结合盘面看。", None)]))

    def fake_build_one_tool(tool, profile, question):
        if tool == "qimen":
            return tool, {"ju": "阳遁一局", "solar_date": "2026-06-01", "profile": profile["name"]}
        if tool == "bazi":
            return tool, {
                "birth_time": profile["birth_time"],
                "four_pillars": {
                    "year": {"gan_zhi": "己丑", "gan": "己", "zhi": "丑"},
                    "month": {"gan_zhi": "丙寅", "gan": "丙", "zhi": "寅"},
                    "day": {"gan_zhi": "乙巳", "gan": "乙", "zhi": "巳"},
                    "hour": {"gan_zhi": "庚辰", "gan": "庚", "zhi": "辰"},
                },
                "dayun": [{"start_year": 2024, "start_age": 16, "end_age": 25, "gan_zhi": "戊辰"}],
                "liu_nian": [{"year": 2026, "gan_zhi": "丙午"}],
            }
        return tool, {}

    monkeypatch.setattr(app_module, "_build_one_tool", fake_build_one_tool)
    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 100, "测试积分")

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    response = client.post("/api/comprehensive/ask/stream", json={
        "question": "我想知道我今年的运势怎么样",
        "reading_mode": "deep",
        "profiles": [
            {"name": "丑牛示例命盘", "gender": "女", "calType": "公历", "birthTime": "200903010800"},
            {"name": "卯兔示例命盘", "gender": "女", "calType": "公历", "birthTime": "201103010800"},
        ],
        "tool_models": ["qimen", "bazi"],
        "paipan": {"paipan": {}, "artifacts": {}},
    })

    assert response.status_code == 200
    paipan_done = next(p for p in _sse_payloads(response) if p.get("stage") == "paipan_done")
    assert paipan_done["artifact_actions"]["added"] == ["qimen.pan", "bazi.basic", "bazi.yun"]
    assert paipan_done["artifacts"]["qimen.pan"]["data"]["ju"] == "阳遁一局"
    assert paipan_done["artifacts"]["bazi.basic"]["data"]["birth_time"] == "200903010800"
    assert paipan_done["artifacts"]["bazi.yun"]["data"]["dayun"][0]["gan_zhi"] == "戊辰"


def test_comprehensive_followup_reuses_existing_artifact_and_adds_yun_when_needed(app_module, user_factory, monkeypatch):
    user = user_factory("artifact-follow-user")
    monkeypatch.setattr(app_module, "get_reading_stream", lambda messages: iter([("继续分析。", None)]))
    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 100, "测试积分")

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    base_artifacts = {
        "bazi.basic": {
            "key": "bazi.basic",
            "tool": "bazi",
            "display": "bazi_basic",
            "title": "八字基本排盘",
            "data": {"four_pillars": {"year": {"gan_zhi": "己巳"}}},
        }
    }
    base_paipan = {"bazi": {"four_pillars": {"year": {"gan_zhi": "己巳"}}, "dayun": [{"gan": "甲", "zhi": "子"}]}}
    common = {
        "conversation_id": 123,
        "profile": {
            "name": "追问样例",
            "gender": "男",
            "calType": "公历",
            "birthTime": "199001271030",
            "birthAddr": "北京",
            "meta": {"birthLng": 116.4074, "useSolarTime": True},
        },
        "history": [{"role": "user", "content": "我适合什么工作"}, {"role": "assistant", "content": "先看八字基本盘。"}],
        "paipan": {"paipan": base_paipan, "artifacts": base_artifacts},
        "tool_models": ["bazi"],
        "reading_mode": "standard",
    }

    ordinary = client.post("/api/comprehensive/ask/stream", json={**common, "question": "那我适合做销售吗"})
    ordinary_done = next(p for p in _sse_payloads(ordinary) if p.get("stage") == "paipan_done")
    assert ordinary_done["artifact_actions"]["reused"] == ["bazi.basic"]
    assert ordinary_done["artifact_actions"]["added"] == []
    assert set(ordinary_done["artifacts"]) == {"bazi.basic"}

    timing = client.post("/api/comprehensive/ask/stream", json={**common, "question": "什么时候能发财"})
    timing_done = next(p for p in _sse_payloads(timing) if p.get("stage") == "paipan_done")
    assert "bazi.basic" in timing_done["artifact_actions"]["reused"]
    assert "bazi.yun" in timing_done["artifact_actions"]["added"]
    assert timing_done["artifacts"]["bazi.yun"]["display"] == "bazi_yun"


def test_comprehensive_history_detail_hides_single_tool_analysis(app_module, user_factory):
    user = user_factory("history-summary-user")
    with app_module.app.app_context():
        conv = app_module.ComprehensiveConversation(
            user_id=user.id,
            title="旧综合记录",
            profile_data=json.dumps({"name": "样例"}, ensure_ascii=False),
            models_json=json.dumps(["qimen", "bazi"], ensure_ascii=False),
            paipan_json=json.dumps({
                "paipan": {"qimen": {"ju": "阳遁一局"}},
                "artifacts": {"qimen.pan": {"key": "qimen.pan", "analysis": "奇门单盘分析"}},
            }, ensure_ascii=False),
            model_id="basic",
            points_cost=4,
            messages_json=json.dumps([
                {"role": "user", "content": "我今年怎么样"},
                {
                    "role": "assistant",
                    "content": "【奇门遁甲解析】\n单盘内容\n\n【八字解析】\n八字内容\n\n【综合合参总结】\n只显示综合总结",
                },
            ], ensure_ascii=False),
        )
        app_module.db.session.add(conv)
        app_module.db.session.commit()
        conv_id = conv.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    response = client.get(f"/api/comprehensive/conversations/{conv_id}")
    assert response.status_code == 200
    content = response.get_json()["messages"][-1]["content"]
    assert content == "只显示综合总结"
    assert "奇门遁甲解析" not in content
    assert "八字解析" not in content


def test_homepage_uses_artifact_renderer_and_reading_mode_control():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    index_path = os.path.join(repo_root, "src", "pages", "index", "index.vue")
    composer_path = os.path.join(repo_root, "src", "pages", "index", "components", "HomeAiComposer.vue")
    with open(index_path, encoding="utf-8") as fh:
        source = fh.read()
    with open(composer_path, encoding="utf-8") as fh:
        composer_source = fh.read()

    assert "readingMode" in source
    assert "解读模式" in composer_source
    assert "renderArtifactHtml" in source
    assert "buildResultCards(" not in source
    assert "shouldAutoFollowChat" in source
    assert "xc_home_artifact_collapse_v1" in source
    assert "saveArtifactCollapsed" in source
    assert "🐎" in source
    assert "qimenMaGongFromData" in source
