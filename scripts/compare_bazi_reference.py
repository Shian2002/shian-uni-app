#!/usr/bin/env python3
"""八字参考样本对照工具。

用法：
  python3 scripts/compare_bazi_reference.py --write-template artifacts/bazi-reference/template.csv
  python3 scripts/compare_bazi_reference.py artifacts/bazi-reference/cases.csv --report artifacts/bazi-reference/report.md

CSV 中 reference_* 字段填写你合法取得并认可的参考排盘结果；空字段会跳过比较。
脚本只调用时安本地算法，不访问任何第三方接口。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from bazi_engine import paipan  # noqa: E402


TEMPLATE_COLUMNS = [
    "case_id",
    "name",
    "gender",
    "birth_time",
    "cal_type",
    "use_solar_time",
    "birth_addr",
    "longitude",
    "reference_year_pillar",
    "reference_month_pillar",
    "reference_day_pillar",
    "reference_hour_pillar",
    "reference_dayun",
    "reference_qi_yun_age",
    "reference_qi_yun_text",
    "reference_tai_yuan",
    "reference_ming_gong",
    "reference_shen_gong",
    "note",
]


TEMPLATE_ROWS = [
    {
        "case_id": "sample-19900127-male",
        "name": "样例1990",
        "gender": "男",
        "birth_time": "199001271030",
        "cal_type": "公历",
        "use_solar_time": "false",
        "birth_addr": "北京",
        "longitude": "",
        "reference_year_pillar": "",
        "reference_month_pillar": "",
        "reference_day_pillar": "",
        "reference_hour_pillar": "",
        "reference_dayun": "",
        "reference_qi_yun_age": "",
        "reference_qi_yun_text": "",
        "reference_tai_yuan": "",
        "reference_ming_gong": "",
        "reference_shen_gong": "",
        "note": "把你认可的参考结果填入 reference_* 字段后再跑对照。",
    }
]


@dataclass
class FieldResult:
    case_id: str
    field: str
    expected: str
    actual: str
    matched: bool


def normalize_bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "是"}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(normalize_text(item) for item in value if normalize_text(item))
    return str(value).strip()


def normalize_sequence(value: Any) -> str:
    text = normalize_text(value)
    return " ".join(text.replace(",", " ").replace("，", " ").split())


def pillar(result: dict[str, Any], key: str) -> str:
    data = (result.get("four_pillars") or {}).get(key) or {}
    return normalize_text(data.get("gan_zhi") or (normalize_text(data.get("gan")) + normalize_text(data.get("zhi"))))


def dayun_sequence(result: dict[str, Any], limit: int = 12) -> str:
    items = []
    for item in (result.get("da_yun") or [])[:limit]:
        gz = normalize_text(item.get("gan_zhi") or (normalize_text(item.get("gan")) + normalize_text(item.get("zhi"))))
        if gz:
            items.append(gz)
    return " ".join(items)


def tms_value(result: dict[str, Any], key: str) -> str:
    data = (result.get("tai_ming_shen") or {}).get(key) or {}
    return normalize_text(data.get("gan_zhi"))


def local_snapshot(row: dict[str, str]) -> dict[str, str]:
    longitude_raw = normalize_text(row.get("longitude"))
    longitude = float(longitude_raw) if longitude_raw else None
    result = paipan(
        name=normalize_text(row.get("name")) or normalize_text(row.get("case_id")) or "样例",
        gender=normalize_text(row.get("gender")) or "男",
        birth_time=normalize_text(row.get("birth_time")),
        birth_addr=normalize_text(row.get("birth_addr")) or "",
        cal_type=normalize_text(row.get("cal_type")) or "公历",
        use_solar_time=normalize_bool(row.get("use_solar_time"), False),
        longitude=longitude,
    )
    if not result.get("success"):
        raise RuntimeError(result.get("error") or "本地排盘失败")

    qi_yun_detail = result.get("qi_yun_detail") or {}
    return {
        "year_pillar": pillar(result, "year"),
        "month_pillar": pillar(result, "month"),
        "day_pillar": pillar(result, "day"),
        "hour_pillar": pillar(result, "hour"),
        "dayun": dayun_sequence(result),
        "qi_yun_age": normalize_text(result.get("qi_yun_age")),
        "qi_yun_text": normalize_text(qi_yun_detail.get("text")),
        "tai_yuan": tms_value(result, "tai_yuan"),
        "ming_gong": tms_value(result, "ming_gong"),
        "shen_gong": tms_value(result, "shen_gong"),
        "_raw": json.dumps(result, ensure_ascii=False, sort_keys=True),
    }


def compare_row(row: dict[str, str]) -> tuple[list[FieldResult], dict[str, str]]:
    case_id = normalize_text(row.get("case_id")) or normalize_text(row.get("birth_time")) or "unknown"
    actual = local_snapshot(row)
    checks = [
        ("year_pillar", "reference_year_pillar", actual["year_pillar"], normalize_text),
        ("month_pillar", "reference_month_pillar", actual["month_pillar"], normalize_text),
        ("day_pillar", "reference_day_pillar", actual["day_pillar"], normalize_text),
        ("hour_pillar", "reference_hour_pillar", actual["hour_pillar"], normalize_text),
        ("dayun", "reference_dayun", actual["dayun"], normalize_sequence),
        ("qi_yun_age", "reference_qi_yun_age", actual["qi_yun_age"], normalize_text),
        ("qi_yun_text", "reference_qi_yun_text", actual["qi_yun_text"], normalize_text),
        ("tai_yuan", "reference_tai_yuan", actual["tai_yuan"], normalize_text),
        ("ming_gong", "reference_ming_gong", actual["ming_gong"], normalize_text),
        ("shen_gong", "reference_shen_gong", actual["shen_gong"], normalize_text),
    ]
    results: list[FieldResult] = []
    for field, reference_field, actual_value, normalizer in checks:
        expected_raw = row.get(reference_field, "")
        if normalize_text(expected_raw) == "":
            continue
        expected = normalizer(expected_raw)
        actual_normalized = normalizer(actual_value)
        results.append(
            FieldResult(
                case_id=case_id,
                field=field,
                expected=expected,
                actual=actual_normalized,
                matched=expected == actual_normalized,
            )
        )
    return results, actual


def write_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=TEMPLATE_COLUMNS)
        writer.writeheader()
        writer.writerows(TEMPLATE_ROWS)


def load_cases(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fp:
        return list(csv.DictReader(fp))


def render_report(results: list[FieldResult], snapshots: dict[str, dict[str, str]]) -> str:
    total = len(results)
    matched = sum(1 for item in results if item.matched)
    mismatched = total - matched
    lines = [
        "# 八字参考样本对照报告",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"- 比较字段数：{total}",
        f"- 一致字段数：{matched}",
        f"- 差异字段数：{mismatched}",
        "",
    ]
    if total == 0:
        lines.extend([
            "未发现可比较字段。请在 CSV 的 `reference_*` 字段中填写参考结果后重跑。",
            "",
        ])
    else:
        lines.extend([
            "| 样例 | 字段 | 结果 | 参考值 | 本地值 |",
            "| --- | --- | --- | --- | --- |",
        ])
        for item in results:
            status = "一致" if item.matched else "差异"
            lines.append(f"| {item.case_id} | {item.field} | {status} | {item.expected} | {item.actual} |")
        lines.append("")

    lines.extend(["## 本地排盘快照", ""])
    for case_id, snapshot in snapshots.items():
        lines.append(f"### {case_id}")
        for key in [
            "year_pillar",
            "month_pillar",
            "day_pillar",
            "hour_pillar",
            "dayun",
            "qi_yun_age",
            "qi_yun_text",
            "tai_yuan",
            "ming_gong",
            "shen_gong",
        ]:
            lines.append(f"- {key}: {snapshot.get(key, '')}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="对比时安本地八字排盘与人工参考样本")
    parser.add_argument("cases", nargs="?", help="参考样本 CSV 路径")
    parser.add_argument("--write-template", help="写出 CSV 模板后退出")
    parser.add_argument("--report", help="Markdown 报告输出路径")
    args = parser.parse_args()

    if args.write_template:
        write_template(Path(args.write_template))
        print(f"已写出模板: {args.write_template}")
        return 0

    if not args.cases:
        parser.error("请提供参考样本 CSV，或使用 --write-template 生成模板")

    cases_path = Path(args.cases)
    rows = load_cases(cases_path)
    all_results: list[FieldResult] = []
    snapshots: dict[str, dict[str, str]] = {}
    for row in rows:
        case_id = normalize_text(row.get("case_id")) or normalize_text(row.get("birth_time")) or "unknown"
        results, snapshot = compare_row(row)
        all_results.extend(results)
        snapshots[case_id] = snapshot

    report = render_report(all_results, snapshots)
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        print(f"已写出报告: {report_path}")
    else:
        print(report)

    return 1 if any(not item.matched for item in all_results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
