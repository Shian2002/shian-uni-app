"""用户头像 URL 过滤。"""

import os
from urllib.parse import urlparse

from flask import current_app, has_app_context


def visible_avatar_url(avatar_url):
    """返回前端可安全展示的头像 URL，本地上传文件缺失时返回空字符串。"""
    value = (avatar_url or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        return value
    if not parsed.path.startswith("/static/uploads/"):
        return value
    if not has_app_context():
        return ""
    upload_dir = current_app.config.get("UPLOAD_FOLDER") or ""
    if not upload_dir:
        return ""
    relative = parsed.path[len("/static/uploads/") :]
    if not relative or relative.startswith("/") or ".." in relative.split("/"):
        return ""
    path = os.path.join(upload_dir, *relative.split("/"))
    return value if os.path.isfile(path) else ""
