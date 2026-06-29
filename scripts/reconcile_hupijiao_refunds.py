#!/usr/bin/env python3
"""对账虎皮椒已退款订单，并回退本站积分或 AI 次数。"""

import argparse
import json
import sys
from pathlib import Path


def _bootstrap_path():
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent,
        script_dir.parent / 'backend',
    ]
    for candidate in candidates:
        if (candidate / 'app.py').exists():
            sys.path.insert(0, str(candidate))
            return
    sys.path.insert(0, str(script_dir.parent))


_bootstrap_path()

from app import app, db, refund_recharge_order_once  # noqa: E402
from recharge_routes import reconcile_hupijiao_refunds  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description='同步虎皮椒退款状态并回退积分')
    parser.add_argument('--lookback-days', type=int, default=14, help='扫描最近多少天的 paid 订单')
    parser.add_argument('--limit', type=int, default=50, help='每次最多扫描多少笔订单')
    parser.add_argument('--order-id', type=int, default=None, help='只扫描指定订单')
    parser.add_argument('--dry-run', action='store_true', help='只查询不回退')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    args = parser.parse_args()

    with app.app_context():
        result = reconcile_hupijiao_refunds(
            db,
            refund_recharge_order_once,
            lookback_days=args.lookback_days,
            limit=args.limit,
            order_id=args.order_id,
            dry_run=args.dry_run,
        )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"checked={result.get('checked', 0)} refunded={len(result.get('refunded', []))} failed={len(result.get('failed', []))}")
        for item in result.get('refunded', []):
            print(f"refunded order={item['order_id']} user={item['user_id']} amount={item['refunded']} type={item['credit_type']}")
        for item in result.get('failed', []):
            print(f"failed order={item.get('order_id')} error={item.get('error')}")
    return 0 if result.get('ok') and not result.get('failed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
