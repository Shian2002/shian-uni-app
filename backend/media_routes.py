"""搜索与媒体上传 API。"""

import os
import secrets
import time

from flask import jsonify, request
from flask_login import current_user, login_required

from extensions import csrf


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    """判断上传文件扩展名是否允许。"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _delete_old_avatar(upload_dir, avatar_url):
    if not avatar_url:
        return
    old_path = os.path.join(upload_dir, avatar_url.split('/')[-1])
    if os.path.exists(old_path):
        try:
            os.remove(old_path)
        except OSError:
            pass


def register_media_routes(app, db, deps):
    """注册搜索、图片上传和头像上传端点。"""

    Record = deps['Record']
    logger = deps.get('logger')

    @app.route('/api/search')
    @login_required
    def api_search():
        """搜索用户的排盘记录。"""
        q = (request.args.get('q') or '').strip()
        app_type = request.args.get('type', '')
        if not q:
            return jsonify({'results': [], 'total': 0})

        query = Record.query.filter_by(user_id=current_user.id)
        if app_type:
            query = query.filter_by(app_type=app_type)
        query = query.filter(Record.question.contains(q))
        records = query.order_by(Record.created_at.desc()).limit(20).all()

        return jsonify({
            'results': [{
                'id': r.id,
                'appType': r.app_type or 'qimen',
                'question': r.question,
                'hasResult': bool(r.result_html),
                'createdAt': r.created_at.isoformat() if r.created_at else None,
            } for r in records],
            'total': len(records),
        })

    @app.route('/api/upload', methods=['POST'])
    @login_required
    def api_upload():
        """图片上传：支持 jpg/png/gif/webp，最大 5MB。"""
        if 'file' not in request.files:
            return jsonify({'error': '未选择文件'}), 400
        f = request.files['file']
        if not f.filename:
            return jsonify({'error': '未选择文件'}), 400
        if not allowed_file(f.filename):
            return jsonify({'error': '不支持的文件格式，仅支持 jpg/png/gif/webp'}), 400

        ext = f.filename.rsplit('.', 1)[1].lower()
        fname = f"{int(time.time())}_{secrets.token_hex(6)}.{ext}"
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        fpath = os.path.join(upload_dir, fname)
        f.save(fpath)

        url = f"/static/uploads/{fname}"
        return jsonify({'url': url, 'filename': fname}), 201

    @app.route('/api/avatar', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_avatar():
        """用户头像上传。"""
        if logger:
            logger.info(
                f"[avatar] upload request from user={current_user.id}, "
                f"files={list(request.files.keys())}, content_type={request.content_type}"
            )
        if 'file' not in request.files:
            if logger:
                logger.warning(f"[avatar] no 'file' in request.files, keys={list(request.files.keys())}")
            return jsonify({'error': '未选择文件'}), 400
        f = request.files['file']
        if not f.filename:
            if logger:
                logger.warning("[avatar] empty filename")
            return jsonify({'error': '未选择文件'}), 400
        if not allowed_file(f.filename):
            if logger:
                logger.warning(f"[avatar] not allowed file: {f.filename}")
            return jsonify({'error': '不支持的文件格式，仅支持 jpg/png/gif/webp'}), 400

        try:
            from PIL import Image
            img = Image.open(f.stream)
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            w, h = img.size
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img = img.resize((200, 200), Image.LANCZOS)
            fname = f"avatar_{current_user.id}_{int(time.time())}.png"
            upload_dir = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            fpath = os.path.join(upload_dir, fname)
            if img.mode == 'RGBA':
                img.save(fpath, 'PNG')
            else:
                img.convert('RGB').save(fpath, 'PNG')

            url = f"/static/uploads/{fname}"
            _delete_old_avatar(upload_dir, current_user.avatar)
            current_user.avatar = url
            db.session.commit()
            return jsonify({'url': url}), 200
        except ImportError:
            ext = f.filename.rsplit('.', 1)[1].lower()
            fname = f"avatar_{current_user.id}_{int(time.time())}.{ext}"
            upload_dir = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            fpath = os.path.join(upload_dir, fname)
            f.save(fpath)
            url = f"/static/uploads/{fname}"
            _delete_old_avatar(upload_dir, current_user.avatar)
            current_user.avatar = url
            db.session.commit()
            return jsonify({'url': url}), 200
        except Exception as e:
            if logger:
                logger.error(f"[avatar] 上传失败: {e}")
            return jsonify({'error': '头像上传失败，请重试'}), 500
