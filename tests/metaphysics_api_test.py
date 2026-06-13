import importlib
import json
import os
import sys
import time

import pytest
from types import SimpleNamespace
from pathlib import Path
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
        module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
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
        {"year": 2024, "month": 2, "day": 4, "hour": 16, "minute": 30, "panType": 2},
    )
    assert qimen["fourPillars"] == {"year": "甲辰", "month": "丙寅", "day": "戊戌", "hour": "庚申"}
    assert qimen["ju"] == "阳遁八局上元"
    assert qimen["solarTerm"] == "立春"
    assert qimen["zhiFu"] == "值符天辅落坎一宫(北)"
    assert qimen["zhiShi"] == "值使杜门落坎一宫(北)"
    assert len(qimen["palaces"]) == 9
    assert isinstance(qimen["specialPatterns"], list)
    assert all("patterns" in palace for palace in qimen["palaces"])
    pattern_names = {pattern["name"] for pattern in qimen["specialPatterns"]}
    assert {"落空亡", "门迫", "三奇得使"}.issubset(pattern_names)

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


def test_qimen_chaibu_sample_before_mangzhong_uses_previous_month_pillar(client):
    qimen = _post_json(
        client,
        "/api/qimen/paipan",
        {"year": 2026, "month": 6, "day": 5, "hour": 12, "minute": 2, "panType": 2},
    )

    assert qimen["fourPillars"] == {"year": "丙午", "month": "癸巳", "day": "庚戌", "hour": "壬午"}
    assert qimen["ju"] == "阳遁五局上元"
    assert qimen["solarTerm"] == "小满"
    assert qimen["xunShou"] == "己"
    assert qimen["xunKong"] == {"day": "寅卯", "hour": "申酉"}
    assert qimen["zhiFu"] == "值符天心落离九宫(南)"
    assert qimen["zhiShi"] == "值使开门落坤二宫(西南)"
    assert qimen["maXing"] == {"驛馬": "申"}
    palaces = {p["gong"]: p for p in qimen["palaces"]}
    assert palaces[2]["menFull"] == "开门"
    assert palaces[2]["yinGan"] == "壬"
    assert palaces[8]["menFull"] == "杜门"
    assert palaces[8]["yinGan"] == "己"
    pattern_names = {pattern["name"] for pattern in qimen["specialPatterns"]}
    assert {"青龙返首", "螣蛇夭矫", "三奇入墓", "六仪击刑"}.issubset(pattern_names)


def test_qimen_middle_palace_earth_stem_ji_gong_uses_kun_not_gen(client):
    qimen = _post_json(
        client,
        "/api/qimen/paipan",
        {"year": 2026, "month": 6, "day": 7, "hour": 18, "minute": 19, "panType": 2},
    )

    palaces = {p["gong"]: p for p in qimen["palaces"]}
    assert palaces[5]["diGan"] == "乙"
    assert palaces[5]["jiGong"] == 2
    assert palaces[8]["bagua"] == "艮"
    assert palaces[8]["diGan"] == "庚"
    assert palaces[2]["bagua"] == "坤"
    assert palaces[2]["diGan"] == ["癸", "乙"]


def test_qimen_before_mangzhong_exact_time_stays_xiaoman(client):
    qimen = _post_json(
        client,
        "/api/qimen/paipan",
        {"year": 2026, "month": 6, "day": 5, "hour": 16, "minute": 17, "panType": 2},
    )

    assert qimen["fourPillars"] == {"year": "丙午", "month": "癸巳", "day": "庚戌", "hour": "甲申"}
    assert qimen["solarTerm"] == "小满"
    assert qimen["ju"] == "阳遁五局上元"
    assert qimen["zhiFu"] == "值符天柱落兑七宫(西)"
    assert qimen["zhiShi"] == "值使惊门落兑七宫(西)"
    assert qimen["maXing"] == {"驛馬": "寅"}


def test_qimen_special_patterns_include_global_and_exportable_palace_data(client):
    qimen = _post_json(
        client,
        "/api/qimen/paipan",
        {"year": 2026, "month": 6, "day": 5, "hour": 15, "minute": 0, "panType": 2},
    )

    patterns = qimen["specialPatterns"]
    by_name = {pattern["name"]: pattern for pattern in patterns}
    assert {"伏吟", "天显时格", "天网四张", "天乙伏宫"}.issubset(by_name)
    assert by_name["伏吟"]["category"] == "global"
    assert by_name["天显时格"]["category"] == "global"
    assert by_name["天网四张"]["level"] == "大凶"
    assert by_name["天网四张"]["palace"] == 1

    palaces = {p["gong"]: p for p in qimen["palaces"]}
    palace_one_patterns = {p["name"] for p in palaces[1]["patterns"]}
    assert "天网四张" in palace_one_patterns


def test_qimen_chaibu_next_hour_keeps_rebu_wei_hour_alignment(client):
    qimen = _post_json(
        client,
        "/api/qimen/paipan",
        {"year": 2026, "month": 6, "day": 5, "hour": 14, "minute": 25, "panType": 2},
    )

    assert qimen["fourPillars"] == {"year": "丙午", "month": "癸巳", "day": "庚戌", "hour": "癸未"}
    assert qimen["ju"] == "阳遁五局上元"
    assert qimen["solarTerm"] == "小满"
    assert qimen["zhiFu"] == "值符天心落坎一宫(北)"
    assert qimen["zhiShi"] == "值使开门落乾六宫(西北)"
    assert qimen["maXing"] == {"驛馬": "巳"}
    palaces = {p["gong"]: p for p in qimen["palaces"]}
    assert palaces[6]["menFull"] == "开门"
    assert palaces[6]["yinGan"] == "癸"
    assert palaces[1]["shenFull"] == "值符"
    assert palaces[1]["xingFull"] == "天心"


def test_qimen_ask_default_pan_type_matches_free_paipan():
    source = (Path(__file__).resolve().parents[1] / "backend" / "qimen_ask_routes.py").read_text(encoding="utf-8")

    assert "pan_type = 2" in source
    assert "只保留新拆补法" in source


def test_qimen_ask_prompt_includes_special_patterns():
    from qimen_ask_routes import _build_qimen_ask_prompt

    prompt = _build_qimen_ask_prompt("这件事能不能推进", {
        "solarDate": "2026年6月5日 15时00分",
        "ju": "阳遁五局上元",
        "solarTerm": "小满",
        "fourPillars": {"year": "丙午", "month": "癸巳", "day": "庚戌", "hour": "甲申"},
        "zhiFu": "值符天心落兑七宫(西)",
        "zhiShi": "值使开门落坤二宫(西南)",
        "specialPatterns": [
            {"name": "伏吟", "level": "凶", "summary": "事情停滞", "evidence": ["值符落原宫"]},
            {"name": "天网四张", "level": "大凶", "palaceName": "坎一宫(北)", "summary": "受困难脱"},
        ],
        "palaces": [
            {"gong": 1, "men": "休", "xing": "蓬", "shen": "阴", "tianGan": "癸", "diGan": "癸",
             "patterns": [{"name": "天网四张"}]},
        ],
    })

    assert "**特殊格局**" in prompt
    assert "伏吟（凶）" in prompt
    assert "天网四张（大凶）" in prompt
    assert "格局=天网四张" in prompt
    assert "请先说明特殊格局对全局的影响" in prompt


def test_comprehensive_qimen_defaults_to_chaibu():
    source = (Path(__file__).resolve().parents[1] / "backend" / "comprehensive_routes.py").read_text(encoding="utf-8")

    assert "qimen_paipan(now.year, now.month, now.day, now.hour, now.minute, 2)" in source


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
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        spend_log = app_module.PointLog.query.filter_by(user_id=member.id, action="meihua_reading").one()
        record = app_module.Record.query.filter_by(user_id=member.id, app_type="meihua").one()
        assert membership.points == 15
        assert spend_log.points == -5
        assert spend_log.description == "梅花易数 AI 解读"
        assert record.question == "这件事能成吗"
        assert record.result_html == "梅花解读正文"


def test_liuyao_ask_stream_sends_paipan_and_records_point_spend(app_module, user_factory, monkeypatch):
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

    with app_module.app.app_context():
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        spend_log = app_module.PointLog.query.filter_by(user_id=member.id, action="liuyao_reading").one()
        record = app_module.Record.query.filter_by(user_id=member.id, app_type="liuyao").one()
        assert membership.points == 15
        assert spend_log.points == -5
        assert spend_log.description == "六爻 AI 解读"
        assert record.question == "合作能成吗"
        assert record.result_html == "六爻解读正文"


@pytest.mark.parametrize(
    ("path", "payload", "action", "app_type"),
    [
        (
            "/api/meihua/ask/stream",
            {"question": "积分不足还能解吗", "method": "number", "num1": 7, "num2": 12},
            "meihua_reading",
            "meihua",
        ),
        (
            "/api/liuyao/ask/stream",
            {
                "question": "积分不足还能解吗",
                "mode": "manual",
                "tosses": [[2, 2, 2], [2, 2, 3], [2, 3, 3], [3, 3, 3], [2, 3, 2], [3, 2, 3]],
            },
            "liuyao_reading",
            "liuyao",
        ),
    ],
)
def test_metaphysics_ask_stream_rejects_insufficient_points_without_side_effects(
    app_module, user_factory, monkeypatch, path, payload, action, app_type
):
    member = user_factory(f"{app_type}-poor-user")
    with app_module.app.app_context():
        app_module.add_points(member.id, "admin_add", 4, "不足 5 分")

    monkeypatch.setattr(app_module, "deepseek_available", lambda: True)
    monkeypatch.setattr(app_module, "get_reading_stream", lambda messages: iter([("不应调用", None)]))

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post(path, json=payload)

    assert response.status_code == 200
    payloads = _sse_payloads(response)
    assert payloads == [{"message": "积分不足（需要 5 积分）"}]

    with app_module.app.app_context():
        membership = app_module.Membership.query.filter_by(user_id=member.id).one()
        spend_logs = app_module.PointLog.query.filter_by(user_id=member.id, action=action).all()
        records = app_module.Record.query.filter_by(user_id=member.id, app_type=app_type).all()
        assert membership.points == 4
        assert spend_logs == []
        assert records == []


def test_qimen_ask_stream_uses_split_route_and_creates_record(app_module, user_factory, monkeypatch):
    member = user_factory("qimen-stream-user")
    monkeypatch.setattr(app_module, "deepseek_available", lambda: True)
    monkeypatch.setattr(app_module, "get_reading_stream", lambda messages: iter([("奇门解读正文", None)]))

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/qimen/ask/stream", json={
        "question": "合作能成吗",
        "year": 2024,
        "month": 2,
        "day": 4,
        "hour": 16,
        "minute": 30,
        "panType": 2,
    })

    assert response.status_code == 200
    payloads = _sse_payloads(response)
    assert {"content": "奇门解读正文"} in payloads
    assert any(item.get("length") == len("奇门解读正文") for item in payloads)

    with app_module.app.app_context():
        record = app_module.Record.query.filter_by(user_id=member.id, app_type="qimen").one()
        assert record.question == "合作能成吗"
        assert record.result_html == "奇门解读正文"


def test_qimen_ask_background_status_from_split_route(app_module, monkeypatch):
    def fake_reading(prompt, question, is_deep=False, system_prompt=None):
        return {"content": "后台奇门解读", "reasoning": "后台推理"}

    monkeypatch.setattr("deepseek_service.get_qimen_reading", fake_reading)

    client = app_module.app.test_client()
    response = client.post("/api/qimen/ask", json={
        "question": "什么时候推进",
        "year": 2024,
        "month": 2,
        "day": 4,
        "hour": 16,
        "minute": 30,
        "panType": 2,
    })

    assert response.status_code == 200
    run_id = response.get_json()["run_id"]
    for _ in range(20):
        status = client.get(f"/api/qimen/ask/status?run_id={run_id}")
        body = status.get_json()
        if body.get("phase") == "done":
            break
        time.sleep(0.05)
    else:
        raise AssertionError(f"奇门后台任务未完成: {body}")

    assert body["result"] == "后台奇门解读"
    assert body["reasoning"] == "后台推理"


def test_ziwei_ask_stream_uses_split_route(app_module, monkeypatch):
    import ziwei_ask_routes

    class FakeOpenAI:
        def __init__(self, api_key=None, base_url=None):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self.create)
            )

        def create(self, **kwargs):
            assert kwargs["stream"] is True
            return iter([
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="紫微"))]),
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="解读正文"))]),
            ])

    monkeypatch.setenv("SILICONFLOW_API_KEY", "test-key")
    monkeypatch.setattr(ziwei_ask_routes, "OpenAI", FakeOpenAI)

    client = app_module.app.test_client()
    response = client.post("/api/ziwei/ask/stream", json={
        "question": "我的事业如何",
        "year": 1990,
        "month": 1,
        "day": 27,
        "hour": 10,
        "minute": 30,
        "gender": "男",
        "date_type": "solar",
        "analysis_type": "career",
    })

    assert response.status_code == 200
    payloads = _sse_payloads(response)
    assert {"type": "delta", "content": "紫微解读正文"} in payloads
    assert {"type": "done"} in payloads


def test_ziwei_ask_stream_requires_run_id_for_get(client):
    response = client.get("/api/ziwei/ask/stream")
    assert response.status_code == 400
    assert response.get_json()["error"] == "无效的 run_id"


def test_bazi_ask_stream_uses_split_route_and_updates_record(app_module, user_factory, monkeypatch):
    import bazi_ask_routes

    class FakeOpenAI:
        def __init__(self, api_key=None, base_url=None):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self.create)
            )

        def create(self, **kwargs):
            assert kwargs["stream"] is True
            assert "八字" in kwargs["messages"][0]["content"]
            return iter([
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="八字"))]),
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="解读正文"))]),
            ])

    member = user_factory("bazi-stream-user")
    monkeypatch.setenv("SILICONFLOW_API_KEY", "test-key")
    monkeypatch.setattr(bazi_ask_routes, "OpenAI", FakeOpenAI)

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(member.id)
        sess["_fresh"] = True

    response = client.post("/api/bazi/ask/stream", json={
        "question": "事业如何",
        "pan_data": {
            "success": True,
            "name": "样例",
            "gender": "男",
            "birth_solar": "1990-01-27 10:02",
            "four_pillars": {
                "year": {"gan_zhi": "己巳"},
                "month": {"gan_zhi": "丁丑"},
                "day": {"gan_zhi": "壬辰", "gan": "壬", "wu_xing": "水"},
                "hour": {"gan_zhi": "乙巳"},
            },
            "shi_shen": {},
            "da_yun": [{"start_age": 1, "end_age": 10, "gan_zhi": "戊辰"}],
            "liu_nian": [{"year": 2026, "gan_zhi": "丙午"}],
        },
    })

    assert response.status_code == 200
    payloads = _sse_payloads(response)
    assert {"type": "delta", "content": "八字解读正文"} in payloads
    assert {"type": "done"} in payloads

    with app_module.app.app_context():
        record = app_module.Record.query.filter_by(user_id=member.id, app_type="bazi").one()
        assert record.question == "事业如何"
        assert record.result_html == "八字解读正文"


def test_bazi_ask_stream_requires_input(client):
    response = client.post("/api/bazi/ask/stream", json={"question": "事业如何"})
    assert response.status_code == 400
    assert response.get_json()["error"] == "请提供出生时间或选择档案"


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
        assert data["estimated_cost"] >= 0

        advanced_response = client.post("/api/comprehensive/recommend-tools", json={"question": question, "llm_model": "advanced"})
        assert advanced_response.status_code == 200
        assert advanced_response.get_json()["estimated_cost"] > 0


def test_comprehensive_guide_api_asks_then_recommends(app_module, user_factory):
    user = user_factory("guide-user")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    first = client.post("/api/comprehensive/guide", json={"question": "我想问这段感情还有没有机会复合"})
    assert first.status_code == 200
    first_data = first.get_json()
    assert first_data["status"] == "ask"
    assert first_data["skill"] == "关系应事判断"
    assert "assistant_message" in first_data
    assert "能否复合" in first_data["options"]

    second = client.post("/api/comprehensive/guide", json={
        "question": "我想问这段感情还有没有机会复合",
        "messages": [
            {"role": "assistant", "content": first_data["assistant_message"]},
            {"role": "user", "content": "我更想知道对方态度和能否复合"},
        ],
    })
    assert second.status_code == 200
    second_data = second.get_json()
    assert second_data["status"] == "ask"

    third = client.post("/api/comprehensive/guide", json={
        "question": "我想问这段感情还有没有机会复合",
        "messages": [
            {"role": "assistant", "content": first_data["assistant_message"]},
            {"role": "user", "content": "我更想知道对方态度和能否复合"},
            {"role": "assistant", "content": second_data["assistant_message"]},
            {"role": "user", "content": "我想看短期转机和行动建议"},
        ],
    })
    assert third.status_code == 200
    second_data = third.get_json()
    assert second_data["status"] == "recommend"
    assert second_data["tool_models"] == ["liuyao", "meihua", "tarot"]
    assert "对方态度" in second_data["final_question"]
    assert second_data["estimated_cost"] >= 0


def test_comprehensive_guide_boss_question_requires_rounds_and_profile_tools(app_module, user_factory):
    user = user_factory("guide-boss-user")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    first = client.post("/api/comprehensive/guide", json={"question": "我适合当老板吗"})
    assert first.status_code == 200
    first_data = first.get_json()
    assert first_data["status"] == "ask"
    assert first_data["skill"] == "事业主导力判断"
    assert "老板命" in first_data["assistant_message"]

    second = client.post("/api/comprehensive/guide", json={
        "question": "我适合当老板吗",
        "messages": [{"role": "user", "content": "想看自己有没有老板命"}],
    }).get_json()
    assert second["status"] == "ask"
    assert "阶段" in second["assistant_message"]

    third = client.post("/api/comprehensive/guide", json={
        "question": "我适合当老板吗",
        "messages": [
            {"role": "user", "content": "想看自己有没有老板命"},
            {"role": "user", "content": "还在想法阶段"},
            {"role": "user", "content": "担心赚钱能力和抗压风险"},
        ],
    }).get_json()
    assert third["status"] == "recommend"
    assert third["tool_models"] == ["bazi", "qimen"]
    assert "老板" in third["final_question"]


def test_comprehensive_reading_mode_cost_delta(app_module, user_factory):
    user = user_factory("reading-mode-cost-user")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    concise = client.post("/api/comprehensive/recommend-tools", json={
        "question": "最近整体怎么样",
        "llm_model": "advanced",
        "reading_mode": "concise",
    }).get_json()["estimated_cost"]
    standard = client.post("/api/comprehensive/recommend-tools", json={
        "question": "最近整体怎么样",
        "llm_model": "advanced",
        "reading_mode": "standard",
    }).get_json()["estimated_cost"]
    deep = client.post("/api/comprehensive/recommend-tools", json={
        "question": "最近整体怎么样",
        "llm_model": "advanced",
        "reading_mode": "deep",
    }).get_json()["estimated_cost"]

    assert concise == standard - 1
    assert deep == standard + 2


def test_comprehensive_options_hide_provider_details(app_module, user_factory):
    user = user_factory("model-options-user")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    response = client.get("/api/comprehensive/options")

    assert response.status_code == 200
    models = response.get_json()["llm_models"]
    reading_modes = response.get_json()["reading_modes"]
    assert [m["name"] for m in models] == ["Shian Insight Engine"]
    assert all("GLM" not in m["name"] for m in models)
    assert [m["name"] for m in reading_modes] == ["简约", "标准", "深度"]
    assert [m["cost_base"] for m in models] == [2]
    assert [m["display_cost"] for m in reading_modes] == [1, 2, 4]
    assert all("provider" not in m for m in models)
    assert all("strength" not in m for m in models)


def test_qimen_tool_messages_include_birth_year_and_full_pan(app_module):
    from comprehensive_ai import build_tool_analysis_messages

    profile = {
        "name": "楚桉",
        "gender": "女",
        "cal_type": "农历",
        "birth_time": "200611042319",
        "birth_addr": "广西省 贵港 平南县",
        "profile_type": "self",
        "source": "bazi_record",
        "meta": {
            "birthLng": 110.393,
            "birthLat": 23.5399,
            "useSolarTime": True,
            "isDst": True,
            "nightZiMode": "夜子时换日",
            "birth_solar": "2006-12-23 21:41",
            "birth_lunar": "丙戌年冬月初四 亥时",
            "pillars": "丙戌庚子丙戌己亥",
            "four_pillars": {
                "year": {"gan_zhi": "丙戌", "gan": "丙", "zhi": "戌"},
                "month": {"gan_zhi": "庚子", "gan": "庚", "zhi": "子"},
                "day": {"gan_zhi": "丙戌", "gan": "丙", "zhi": "戌"},
                "hour": {"gan_zhi": "己亥", "gan": "己", "zhi": "亥"},
            },
        },
    }
    qimen = {
        "solarDate": "2026年6月8日 02时49分",
        "fourPillars": {"year": "丙午", "month": "甲午", "day": "癸丑", "hour": "癸丑"},
        "ju": "阳遁六局上元",
        "xunKong": {"day": "寅卯", "hour": "寅卯"},
        "zhiFu": "值符天蓬落坤二宫(西南)",
        "zhiShi": "值使休门落坎一宫(北)",
        "palaces": [
            {
                "name": "坤二宫(西南)",
                "gong": 2,
                "menFull": "死门",
                "xingFull": "天蓬",
                "shenFull": "值符",
                "tianGan": "壬",
                "diGan": ["癸", "乙"],
            }
        ],
    }

    content = build_tool_analysis_messages(
        "今天下午的ai课程能逃课吗，会不会点名什么的",
        profile,
        "qimen",
        qimen,
    )[-1]["content"]

    assert "用户出生命盘上下文" in content
    assert '"birth_year": "2006"' in content
    assert '"birth_year_pillar": "丙戌"' in content
    assert '"birth_year_gan": "丙"' in content
    assert '"birth_year_zhi": "戌"' in content
    assert '"use_true_solar_time": true' in content
    assert '"is_dst": true' in content
    assert '"birth_lng": 110.393' in content
    assert "当前术数盘面完整数据" in content
    assert "坤二宫(西南)" in content
    assert '"diGan": [' in content


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
    assert synced["gender"] == "女"
    assert synced["meta"]["gender"] == "女"
    assert synced["meta"]["four_pillars"]["_gender"] == "女"


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


def test_delete_backfilled_bazi_profile_removes_source_record(app_module, user_factory):
    user = user_factory("profile-delete-backfill-user")
    with app_module.app.app_context():
        record = app_module.BaziRecord(
            user_id=user.id,
            name="待删除八字记录",
            gender="女",
            cal_type="公历",
            birth_time="199608251647",
            birth_addr="广州",
            pillars="丙子丙申甲午壬申",
            record_type="paipan",
            params_json=json.dumps({"birthLng": 113.2644, "useSolarTime": True}, ensure_ascii=False),
        )
        app_module.db.session.add(record)
        app_module.db.session.commit()
        record_id = record.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    profiles_response = client.get("/api/profiles?sort=last_used")
    assert profiles_response.status_code == 200
    synced = next(p for p in profiles_response.get_json()["profiles"] if p["sourceRecordId"] == record_id)

    delete_response = client.delete(f"/api/profiles/{synced['id']}")
    assert delete_response.status_code == 200
    assert delete_response.get_json()["deletedSourceRecord"] is True

    refreshed = client.get("/api/profiles?sort=last_used")
    assert refreshed.status_code == 200
    assert all(p["sourceRecordId"] != record_id for p in refreshed.get_json()["profiles"])
    with app_module.app.app_context():
        assert app_module.db.session.get(app_module.BaziRecord, record_id) is None


def test_profiles_update_preserves_owner_and_serializes_meta(app_module, user_factory):
    user = user_factory("profile-edit-user")
    with app_module.app.app_context():
        profile = app_module.UserProfile(
            user_id=user.id,
            name="旧名",
            gender="男",
            cal_type="公历",
            birth_time="199001271030",
            birth_addr="北京",
            profile_type="self",
            source="manual",
        )
        app_module.db.session.add(profile)
        app_module.db.session.commit()
        profile_id = profile.id

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    response = client.put(f"/api/profiles/{profile_id}", json={
        "name": "新名",
        "gender": "女",
        "calType": "农历",
        "birthTime": "199102030405",
        "birthAddr": "上海",
        "profileType": "customer",
        "isDefault": True,
        "source": "manual",
        "meta": {"note": "测试", "gender": "男", "four_pillars": {"_gender": "男"}},
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "新名"
    assert data["profileType"] == "customer"
    assert data["isDefault"] is True
    assert data["meta"]["note"] == "测试"
    assert data["gender"] == "女"
    assert data["meta"]["gender"] == "女"
    assert data["meta"]["four_pillars"]["_gender"] == "女"


def test_profiles_create_ziwei_source_updates_same_birth_profile(app_module, user_factory):
    user = user_factory("ziwei-profile-user")
    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    payload = {
        "name": "紫微样例",
        "gender": "男",
        "calType": "公历",
        "birthTime": "199001271030",
        "birthAddr": "北京",
        "profileType": "self",
        "source": "ziwei_pan",
        "meta": {"longitude": 116.4074, "soul_star": "文曲"},
    }
    first = client.post("/api/profiles", json=payload)
    second = client.post("/api/profiles", json={**payload, "meta": {"longitude": 116.4, "body_star": "天同"}})

    assert first.status_code == 201
    assert second.status_code == 200
    profiles = client.get("/api/profiles?sort=last_used").get_json()["profiles"]
    ziwei_profiles = [p for p in profiles if p["source"] == "ziwei_pan" and p["name"] == "紫微样例"]
    assert len(ziwei_profiles) == 1
    assert ziwei_profiles[0]["meta"]["body_star"] == "天同"


def test_comprehensive_new_conversation_returns_full_bazi_artifact(app_module, user_factory, monkeypatch):
    user = user_factory("artifact-new-user")
    seen_model_ids = []

    def fake_stream(messages, model_id=None):
        seen_model_ids.append(model_id)
        return iter([("职业方向可以结合命局判断。", None)])

    monkeypatch.setattr(app_module, "get_reading_stream", fake_stream)
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
        "llm_model": "advanced",
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
    assert seen_model_ids
    assert set(seen_model_ids) == {"advanced"}


def test_comprehensive_uses_frontend_handoff_paipan_without_rebuilding(app_module, user_factory, monkeypatch):
    user = user_factory("handoff-paipan-user")

    def fake_stream(*args, **kwargs):
        return iter([("已按传入盘面解读。", None)])

    monkeypatch.setattr(app_module, "get_reading_stream", fake_stream)
    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 100, "测试积分")

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    handoff_qimen = {
        "handoff_sentinel": "frontend-qimen-pan",
        "paipanTime": "2026-06-08 10:30",
        "ju": "阳遁一局",
        "fourPillars": {"year": "丙午", "month": "甲午", "day": "癸丑", "hour": "丁巳"},
    }
    response = client.post("/api/comprehensive/ask/stream", json={
        "question": "请解读这个奇门盘",
        "profile": {
            "name": "奇门样例",
            "gender": "男",
            "calType": "公历",
            "birthTime": "199001271030",
            "birthAddr": "北京",
        },
        "tool_models": ["qimen"],
        "auto_select_tools": False,
        "paipan": {"paipan": {"qimen": handoff_qimen}, "artifacts": {}},
        "reading_mode": "standard",
    })

    assert response.status_code == 200
    paipan_done = next(p for p in _sse_payloads(response) if p.get("stage") == "paipan_done")
    assert paipan_done["paipan"]["qimen"]["handoff_sentinel"] == "frontend-qimen-pan"
    qimen_artifact = paipan_done["artifacts"]["qimen.pan"]
    assert qimen_artifact["data"]["handoff_sentinel"] == "frontend-qimen-pan"
    assert qimen_artifact["data"]["paipanTime"] == "2026-06-08 10:30"
    assert paipan_done["artifact_actions"]["added"] == ["qimen.pan"]


def test_comprehensive_stream_passes_reading_mode_to_model_provider(app_module, user_factory, monkeypatch):
    user = user_factory("artifact-reading-mode-user")
    seen = []

    def fake_stream(messages, model_id=None, reading_mode=None):
        seen.append((model_id, reading_mode))
        return iter([("深度解读正文。", None)])

    monkeypatch.setattr(app_module, "get_reading_stream", fake_stream)
    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 100, "测试积分")

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    response = client.post("/api/comprehensive/ask/stream", json={
        "question": "我适合什么工作",
        "reading_mode": "deep",
        "profile": {
            "name": "深度样例",
            "gender": "男",
            "calType": "公历",
            "birthTime": "199001271030",
            "birthAddr": "北京",
            "meta": {"birthLng": 116.4074, "useSolarTime": True},
        },
        "tool_models": ["bazi"],
        "llm_model": "expert",
    })

    assert response.status_code == 200
    _sse_payloads(response)
    assert seen
    assert set(seen) == {("expert", "deep")}


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


def test_comprehensive_stream_refunds_points_when_model_provider_fails(app_module, user_factory, monkeypatch):
    user = user_factory("artifact-refund-user")
    monkeypatch.setattr(app_module, "get_reading_stream", lambda messages, model_id=None: iter([(None, "AI 服务异常：余额不足")]))
    with app_module.app.app_context():
        app_module.add_points(user.id, "admin_add", 20, "测试积分")
        membership = app_module.get_or_create_membership(user.id)
        membership.daily_ai_light_used_at = app_module.datetime.utcnow().strftime("%Y-%m-%d")
        app_module.db.session.commit()

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
      sess["_user_id"] = str(user.id)
      sess["_fresh"] = True

    response = client.post("/api/comprehensive/ask/stream", json={
        "question": "我适合什么工作",
        "profile": {
            "name": "退回样例",
            "gender": "男",
            "calType": "公历",
            "birthTime": "199001271030",
            "birthAddr": "北京",
            "meta": {"birthLng": 116.4074, "useSolarTime": True},
        },
        "tool_models": ["bazi"],
        "llm_model": "advanced",
    })

    payloads = _sse_payloads(response)
    error_payload = next(p for p in payloads if p.get("error"))
    assert error_payload["refund"]["ok"] is True
    assert error_payload["refund"]["refunded"] == 4
    with app_module.app.app_context():
        membership = app_module.Membership.query.filter_by(user_id=user.id).one()
        refund_logs = app_module.PointLog.query.filter_by(user_id=user.id, action="comprehensive_ai_refund").all()
        assert membership.points == 20
        assert len(refund_logs) == 1


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
    assert "readingModeLabels" in source
    assert "reading-mode-picker" in composer_source
    assert "reading-mode-segment" not in composer_source
    assert "renderArtifactHtml" in source
    assert "buildResultCards(" not in source
    assert "shouldAutoFollowChat" in source
    assert "xc_home_artifact_collapse_v1" in source
    assert "saveArtifactCollapsed" in source
    assert "🐎" in source
    assert "qimenMaGongFromData" in source
