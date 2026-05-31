#!/usr/bin/env python3
"""玄学接口固定样例烟测脚本。

默认使用 Flask test client 在本地进程内调用接口，不写生产数据库。
"""

import argparse
import importlib
import json
import os
import sys
import tempfile
from urllib import parse, request


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")


CASES = [
    {
        "name": "bazi_paipan",
        "method": "POST",
        "path": "/api/bazi/paipan",
        "json": {
            "name": "样例",
            "gender": "男",
            "calType": "公历",
            "birthTime": "199001271030",
            "birthAddr": "北京",
            "birthLng": 116.4074,
            "useSolarTime": True,
            "_replay": True,
        },
    },
    {
        "name": "ziwei_pan",
        "method": "POST",
        "path": "/api/ziwei/pan",
        "json": {
            "year": 1990,
            "month": 1,
            "day": 27,
            "hour": 10,
            "minute": 30,
            "gender": "男",
            "date_type": "solar",
            "longitude": 116.4074,
        },
    },
    {
        "name": "qimen_paipan",
        "method": "POST",
        "path": "/api/qimen/paipan",
        "json": {"year": 2024, "month": 2, "day": 4, "hour": 16, "minute": 30, "panType": 1},
    },
    {
        "name": "meihua_paipan",
        "method": "POST",
        "path": "/api/meihua/paipan",
        "json": {"method": "number", "num1": 7, "num2": 12},
    },
    {
        "name": "liuyao_paipan",
        "method": "POST",
        "path": "/api/liuyao/paipan",
        "json": {
            "mode": "manual",
            "question": "测试",
            "tosses": [[2, 2, 2], [2, 2, 3], [2, 3, 3], [3, 3, 3], [2, 3, 2], [3, 2, 3]],
        },
    },
    {"name": "tarot_verify", "method": "GET", "path": "/api/tarot/verify"},
    {"name": "tarot_spreads", "method": "GET", "path": "/api/tarot/spreads"},
    {"name": "huangli_day", "method": "GET", "path": "/api/huangli", "query": {"date": "2024-02-10"}},
    {"name": "huangli_month", "method": "GET", "path": "/api/huangli/month", "query": {"year": 2024, "month": 2}},
    {
        "name": "solar_to_lunar",
        "method": "POST",
        "path": "/api/bazi/solar-to-lunar",
        "json": {"year": 2024, "month": 2, "day": 10},
    },
    {
        "name": "lunar_to_solar",
        "method": "POST",
        "path": "/api/bazi/lunar-to-solar",
        "json": {"year": 2024, "month": 1, "day": 1, "isLeap": False},
    },
    {
        "name": "liu_yue",
        "method": "POST",
        "path": "/api/bazi/liu-yue",
        "json": {"year": 2024, "dayGan": "甲"},
    },
    {
        "name": "liu_ri",
        "method": "POST",
        "path": "/api/bazi/liu-ri",
        "json": {"year": 2024, "month": 2, "dayGan": "甲"},
    },
    {
        "name": "liu_shi",
        "method": "POST",
        "path": "/api/bazi/liu-shi",
        "json": {"dayGan": "甲", "dayZhuGan": "甲"},
    },
    {
        "name": "zeji",
        "method": "POST",
        "path": "/api/zeji",
        "json": {"zejiType": "搬家", "startDate": "2024-02-10", "endDate": "2024-02-12", "addr": "北京"},
    },
]


def _case_path(case):
    query = case.get("query")
    if not query:
        return case["path"]
    return f'{case["path"]}?{parse.urlencode(query)}'


def _call_local(case):
    global _LOCAL_CLIENT
    if "_LOCAL_CLIENT" not in globals():
        db_path = os.path.join(tempfile.mkdtemp(prefix="xuan-cet-smoke-"), "tianji-smoke.db")
        os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path}")
        os.environ.setdefault("TIANJI_SECRET_KEY", "smoke-secret-key")
        sys.path.insert(0, BACKEND_DIR)
        app_module = importlib.import_module("app")
        app_module.app.config.update(TESTING=True)
        with app_module.app.app_context():
            app_module.db.drop_all()
            app_module.db.create_all()
        _LOCAL_CLIENT = app_module.app.test_client()

    path = _case_path(case)
    if case["method"] == "POST":
        response = _LOCAL_CLIENT.post(path, json=case.get("json") or {})
    else:
        response = _LOCAL_CLIENT.get(path)
    return response.status_code, response.get_json()


def _call_http(base_url, case):
    url = base_url.rstrip("/") + _case_path(case)
    payload = None
    headers = {}
    if case["method"] == "POST":
        payload = json.dumps(case.get("json") or {}, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=payload, headers=headers, method=case["method"])
    with request.urlopen(req, timeout=12) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _pick_summary(name, data):
    if name == "bazi_paipan":
        pillars = data["four_pillars"]
        return {
            "pillars": [pillars[k]["gan_zhi"] for k in ("year", "month", "day", "hour")],
            "birth_solar": data.get("birth_solar"),
            "birth_lunar": data.get("birth_lunar"),
        }
    if name == "ziwei_pan":
        basic = data["data"]["basic_info"]
        return {
            "chinese_date": basic.get("chinese_date"),
            "solar_date": basic.get("solar_date"),
            "lunar_date": basic.get("lunar_date"),
            "palace_count": len(data["data"].get("twelve_palaces") or []),
        }
    if name == "qimen_paipan":
        return {
            "four_pillars": data.get("fourPillars"),
            "ju": data.get("ju"),
            "solar_term": data.get("solarTerm"),
            "palace_count": len(data.get("palaces") or []),
        }
    if name == "meihua_paipan":
        return {
            "ben_gua": data["benGua"]["name"],
            "hu_gua": data["huGua"]["name"],
            "bian_gua": data["bianGua"]["name"],
            "dong_yao": data["dongYao"],
        }
    if name == "liuyao_paipan":
        return {
            "ben_gua": data["本卦"],
            "bian_gua": data["变卦"],
            "shi": data["世爻"],
            "ying": data["应爻"],
            "moving": [idx + 1 for idx, yao in enumerate(data["六爻"]) if yao.get("is_moving")],
        }
    if name == "tarot_spreads":
        return {"count": len(data["data"]), "keys": [item["key"] for item in data["data"]]}
    if name == "huangli_month":
        return {"days": len(data["days"]), "first": data["days"][0]["solarDate"], "last": data["days"][-1]["solarDate"]}
    if name in ("liu_yue", "liu_ri", "liu_shi"):
        key = {"liu_yue": "liu_yue", "liu_ri": "liu_ri", "liu_shi": "liu_shi"}[name]
        return {"count": len(data[key]), "first": data[key][0]["gan_zhi"]}
    if name == "zeji":
        return {"success": data["success"], "best": data["bestDays"][0]["date"], "best_score": data["bestDays"][0]["score"]}
    return data


def main():
    parser = argparse.ArgumentParser(description="运行玄学接口固定样例烟测")
    parser.add_argument("--base-url", help="可选：对线上或本地 HTTP 服务运行，例如 http://119.29.128.18")
    parser.add_argument("--full", action="store_true", help="输出完整响应，而不是摘要")
    args = parser.parse_args()

    results = {}
    for case in CASES:
        status, data = _call_http(args.base_url, case) if args.base_url else _call_local(case)
        if status >= 400:
            raise SystemExit(f'{case["name"]} 请求失败: HTTP {status} {data}')
        results[case["name"]] = data if args.full else _pick_summary(case["name"], data)

    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
