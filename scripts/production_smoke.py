#!/usr/bin/env python3
"""线上发布后烟测。"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar


class SmokeClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.cookies = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))

    def request(self, method, path, data=None):
        body = None
        headers = {}
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return resp.status, raw
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", errors="replace")

    def get_json(self, path):
        status, raw = self.request("GET", path)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw[:300]}
        return status, payload

    def login(self, username, password):
        return self.request("POST", "/api/login", {"username": username, "password": password})


def require(condition, message, failures):
    if condition:
        print(f"[OK] {message}")
    else:
        print(f"[FAIL] {message}")
        failures.append(message)


def main():
    parser = argparse.ArgumentParser(description="检查线上健康、前端资源、登录和后台权限")
    parser.add_argument("--base-url", default=os.environ.get("SMOKE_BASE_URL", "https://shianjieyouwu.com"))
    parser.add_argument("--normal-user", default=os.environ.get("SMOKE_NORMAL_USER"))
    parser.add_argument("--normal-password", default=os.environ.get("SMOKE_NORMAL_PASSWORD"))
    parser.add_argument("--admin-user", default=os.environ.get("SMOKE_ADMIN_USER"))
    parser.add_argument("--admin-password", default=os.environ.get("SMOKE_ADMIN_PASSWORD"))
    parser.add_argument("--skip-auth", action="store_true")
    args = parser.parse_args()

    failures = []
    client = SmokeClient(args.base_url)

    health_status, health = client.get_json("/api/health")
    require(health_status == 200 and health.get("success") and health.get("status") == "running", "健康检查 200 且服务运行", failures)

    index_status, index_html = client.request("GET", "/")
    require(index_status == 200 and "assets/index-" in index_html, "首页 HTML 指向当前构建资源", failures)

    if not args.skip_auth:
        if not all([args.normal_user, args.normal_password, args.admin_user, args.admin_password]):
            print("[FAIL] 认证烟测需要通过环境变量或参数显式提供普通用户和管理员账号")
            print("      可设置 SMOKE_NORMAL_USER/SMOKE_NORMAL_PASSWORD/SMOKE_ADMIN_USER/SMOKE_ADMIN_PASSWORD")
            return 1

        normal = SmokeClient(args.base_url)
        normal_login_status, _ = normal.login(args.normal_user, args.normal_password)
        normal_admin_status, _ = normal.request("GET", "/api/admin/summary")
        require(normal_login_status == 200, "普通用户可登录", failures)
        require(normal_admin_status == 403, "普通用户不能访问后台", failures)

        admin = SmokeClient(args.base_url)
        admin_login_status, _ = admin.login(args.admin_user, args.admin_password)
        admin_summary_status, summary_raw = admin.request("GET", "/api/admin/summary")
        admin_users_status, users_raw = admin.request("GET", "/api/admin/users")
        require(admin_login_status == 200, "管理员可登录", failures)
        require(admin_summary_status == 200, "管理员可访问后台概要", failures)
        require(admin_users_status == 200, "管理员可访问用户列表", failures)

        try:
            users = json.loads(users_raw)
            require(bool(users.get("users")), "后台用户列表返回用户数据", failures)
        except json.JSONDecodeError:
            failures.append("后台用户列表不是 JSON")
            print("[FAIL] 后台用户列表不是 JSON")

    if failures:
        print("\n烟测失败:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("\n烟测通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
