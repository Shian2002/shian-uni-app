"""社区、通知、举报与大师体系 API。"""

import os
import secrets
import time

from flask import jsonify, request
from flask_login import current_user, login_required

from models import (
    Comment,
    CommentLike,
    Master,
    Notification,
    Post,
    PostLike,
    Report,
    User,
)


VALID_CATEGORIES = {'share', 'discuss', 'ask', 'experience'}
REPORT_REASONS = {'spam', 'abuse', 'misinformation', 'illegal', 'other'}


def register_community_routes(app, db, services):
    """注册社区相关路由。"""
    allowed_file = services['allowed_file']

    def _create_notification(user_id, ntype, from_user_id=None, post_id=None, comment_id=None, content=None):
        n = Notification(user_id=user_id, type=ntype, from_user_id=from_user_id,
                         post_id=post_id, comment_id=comment_id, content=content)
        db.session.add(n)

    @app.route('/api/posts', methods=['GET'])
    def api_posts_list():
        """社区帖子列表 — 支持 category/tags/page/sort 参数。"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        category = request.args.get('category', '')
        tag = request.args.get('tag', '').strip()
        sort = request.args.get('sort', 'latest').strip()

        query = Post.query.filter_by(is_hidden=False)
        if category and category in VALID_CATEGORIES:
            query = query.filter_by(category=category)
        if tag:
            query = query.filter(Post.tags.contains(tag))

        if sort == 'hot':
            query = query.order_by(Post.is_pinned.desc(), Post.likes_count.desc(), Post.comments_count.desc(), Post.created_at.desc())
        elif sort == 'featured':
            query = query.filter_by(is_featured=True).order_by(Post.is_pinned.desc(), Post.created_at.desc())
        else:
            query = query.order_by(Post.is_pinned.desc(), Post.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        posts = []
        for p in pagination.items:
            author = db.session.get(User, p.user_id)
            posts.append({
                'id': p.id,
                'userId': p.user_id,
                'username': author.username if author else '匿名',
                'title': p.title,
                'contentPreview': (p.content[:80] + '...') if p.content and len(p.content) > 80 else (p.content or ''),
                'category': p.category,
                'tags': p.tags.split(',') if p.tags else [],
                'imageUrl': p.image_url or None,
                'likesCount': p.likes_count,
                'commentsCount': p.comments_count,
                'isFeatured': p.is_featured,
                'isPinned': p.is_pinned,
                'createdAt': p.created_at.isoformat() if p.created_at else None,
            })

        return jsonify({
            'posts': posts,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'disclaimer': '本社区内容为民俗文化探讨，不构成命运预测承诺',
        })

    @app.route('/api/posts', methods=['POST'])
    @login_required
    def api_posts_create():
        """创建帖子 — 支持 JSON 和 multipart/form-data（含图片上传）。"""
        image_url = None

        if request.content_type and 'multipart/form-data' in request.content_type:
            title = (request.form.get('title') or '').strip()
            content = (request.form.get('content') or '').strip()
            category = request.form.get('category', 'share')
            tags = request.form.get('tags', '')

            if 'image' in request.files:
                f = request.files['image']
                if f and f.filename and allowed_file(f.filename):
                    ext = f.filename.rsplit('.', 1)[1].lower()
                    fname = f"{int(time.time())}_{secrets.token_hex(6)}.{ext}"
                    upload_dir = app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_dir, exist_ok=True)
                    fpath = os.path.join(upload_dir, fname)
                    f.save(fpath)
                    image_url = f"/static/uploads/{fname}"
        else:
            data = request.get_json(silent=True) or {}
            title = (data.get('title') or '').strip()
            content = (data.get('content') or '').strip()
            category = data.get('category', 'share')
            tags = data.get('tags', '')
            image_url = data.get('imageUrl')

        if not title or len(title) > 200:
            return jsonify({'error': '标题需1-200个字符'}), 400
        if not content:
            return jsonify({'error': '内容不能为空'}), 400
        if category not in VALID_CATEGORIES:
            return jsonify({'error': f'无效分类，可选: {", ".join(VALID_CATEGORIES)}'}), 400

        if isinstance(tags, list):
            tag_str = ','.join(t.strip() for t in tags if t.strip())
        else:
            tag_str = ','.join(t.strip() for t in str(tags).split(',') if t.strip())

        post = Post(
            user_id=current_user.id, title=title, content=content,
            category=category, tags=tag_str, image_url=image_url,
        )
        db.session.add(post)
        db.session.commit()
        return jsonify({'id': post.id, 'disclaimer': '本帖内容为民俗文化探讨，不构成命运预测承诺'}), 201

    @app.route('/api/posts/<int:pid>')
    def api_posts_detail(pid):
        """帖子详情（含评论）。"""
        post = db.session.get(Post, pid)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404
        if post.is_hidden and not (current_user.is_authenticated and current_user.is_admin):
            return jsonify({'error': '帖子已被隐藏'}), 404

        author = db.session.get(User, post.user_id)
        comments = Comment.query.filter_by(post_id=pid, parent_id=None)\
            .order_by(Comment.created_at.asc()).all()

        def format_comment(c):
            author_c = db.session.get(User, c.user_id)
            replies = Comment.query.filter_by(parent_id=c.id)\
                .order_by(Comment.created_at.asc()).all()
            c_liked = False
            if current_user.is_authenticated:
                c_liked = CommentLike.query.filter_by(user_id=current_user.id, comment_id=c.id).first() is not None
            return {
                'id': c.id,
                'userId': c.user_id,
                'username': author_c.username if author_c else '匿名',
                'content': c.content,
                'parentId': c.parent_id,
                'likesCount': c.likes_count,
                'liked': c_liked,
                'replies': [format_comment(r) for r in replies],
                'createdAt': c.created_at.isoformat() if c.created_at else None,
            }

        liked = False
        if current_user.is_authenticated:
            liked = PostLike.query.filter_by(user_id=current_user.id, post_id=pid).first() is not None

        return jsonify({
            'id': post.id,
            'userId': post.user_id,
            'username': author.username if author else '匿名',
            'title': post.title,
            'content': post.content,
            'category': post.category,
            'tags': post.tags.split(',') if post.tags else [],
            'imageUrl': post.image_url or None,
            'likesCount': post.likes_count,
            'commentsCount': post.comments_count,
            'isFeatured': post.is_featured,
            'isPinned': post.is_pinned,
            'isHidden': post.is_hidden,
            'liked': liked,
            'comments': [format_comment(c) for c in comments],
            'createdAt': post.created_at.isoformat() if post.created_at else None,
            'disclaimer': '本帖内容为民俗文化探讨，不构成命运预测承诺',
        })

    @app.route('/api/posts/<int:pid>', methods=['DELETE'])
    @login_required
    def api_posts_delete(pid):
        """删除帖子（仅作者）。"""
        post = db.session.get(Post, pid)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404
        if post.user_id != current_user.id:
            return jsonify({'error': '仅作者可删除'}), 403

        Comment.query.filter_by(post_id=pid).delete()
        PostLike.query.filter_by(post_id=pid).delete()
        db.session.delete(post)
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/posts/<int:pid>/like', methods=['POST'])
    @login_required
    def api_posts_like(pid):
        """点赞/取消点赞。"""
        post = db.session.get(Post, pid)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        existing = PostLike.query.filter_by(user_id=current_user.id, post_id=pid).first()
        if existing:
            db.session.delete(existing)
            post.likes_count = max(0, (post.likes_count or 0) - 1)
            db.session.commit()
            return jsonify({'liked': False, 'likesCount': post.likes_count})

        like = PostLike(user_id=current_user.id, post_id=pid)
        db.session.add(like)
        post.likes_count = (post.likes_count or 0) + 1
        if post.user_id != current_user.id:
            _create_notification(post.user_id, 'like', from_user_id=current_user.id,
                                 post_id=pid, content=f'{current_user.username} 赞了你的帖子')
        db.session.commit()
        return jsonify({'liked': True, 'likesCount': post.likes_count})

    @app.route('/api/posts/<int:pid>/comments', methods=['POST'])
    @login_required
    def api_posts_comment(pid):
        """添加评论。"""
        post = db.session.get(Post, pid)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        data = request.get_json(silent=True) or {}
        content = (data.get('content') or '').strip()
        parent_id = data.get('parentId')

        if not content:
            return jsonify({'error': '评论内容不能为空'}), 400

        if parent_id:
            parent = db.session.get(Comment, parent_id)
            if not parent or parent.post_id != pid:
                return jsonify({'error': '回复的评论不存在'}), 400

        comment = Comment(
            user_id=current_user.id, post_id=pid,
            content=content, parent_id=parent_id,
        )
        db.session.add(comment)
        post.comments_count = (post.comments_count or 0) + 1
        if post.user_id != current_user.id:
            _create_notification(post.user_id, 'comment', from_user_id=current_user.id,
                                 post_id=pid, comment_id=comment.id,
                                 content=f'{current_user.username} 评论了你的帖子')
        if parent_id:
            parent_c = db.session.get(Comment, parent_id)
            if parent_c and parent_c.user_id != current_user.id:
                _create_notification(parent_c.user_id, 'reply', from_user_id=current_user.id,
                                     post_id=pid, comment_id=comment.id,
                                     content=f'{current_user.username} 回复了你的评论')
        db.session.commit()
        return jsonify({'id': comment.id, 'disclaimer': '本评论内容为民俗文化探讨，不构成命运预测承诺'}), 201

    @app.route('/api/comments/<int:cid>', methods=['DELETE'])
    @login_required
    def api_comments_delete(cid):
        """删除评论（仅作者）。"""
        comment = db.session.get(Comment, cid)
        if not comment:
            return jsonify({'error': '评论不存在'}), 404
        if comment.user_id != current_user.id:
            return jsonify({'error': '仅作者可删除'}), 403

        post = db.session.get(Post, comment.post_id)
        if post:
            post.comments_count = max(0, (post.comments_count or 0) - 1)
        Comment.query.filter_by(parent_id=cid).delete()
        CommentLike.query.filter_by(comment_id=cid).delete()
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/posts/<int:pid>', methods=['PUT'])
    @login_required
    def api_posts_update(pid):
        """编辑帖子（仅作者）。"""
        post = db.session.get(Post, pid)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404
        if post.user_id != current_user.id:
            return jsonify({'error': '仅作者可编辑'}), 403

        data = request.get_json(silent=True) or {}
        title = (data.get('title') or '').strip()
        content = (data.get('content') or '').strip()
        category = data.get('category', post.category)
        tags = data.get('tags', None)

        if title:
            if len(title) > 200:
                return jsonify({'error': '标题需1-200个字符'}), 400
            post.title = title
        if content:
            post.content = content
        if category and category in VALID_CATEGORIES:
            post.category = category
        if tags is not None:
            if isinstance(tags, list):
                tag_str = ','.join(t.strip() for t in tags if t.strip())
            else:
                tag_str = ','.join(t.strip() for t in str(tags).split(',') if t.strip())
            post.tags = tag_str

        db.session.commit()
        return jsonify({'ok': True, 'id': post.id})

    @app.route('/api/users/<int:uid>/posts')
    def api_user_posts(uid):
        """获取用户的帖子列表。"""
        user = db.session.get(User, uid)
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)

        pagination = Post.query.filter_by(user_id=uid)\
            .order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        posts = []
        for p in pagination.items:
            posts.append({
                'id': p.id,
                'userId': p.user_id,
                'username': user.username,
                'title': p.title,
                'contentPreview': (p.content[:80] + '...') if p.content and len(p.content) > 80 else (p.content or ''),
                'category': p.category,
                'tags': p.tags.split(',') if p.tags else [],
                'imageUrl': p.image_url or None,
                'likesCount': p.likes_count,
                'commentsCount': p.comments_count,
                'isFeatured': p.is_featured,
                'createdAt': p.created_at.isoformat() if p.created_at else None,
            })

        return jsonify({
            'user': {'id': user.id, 'username': user.username},
            'posts': posts,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
        })

    @app.route('/api/comments/<int:cid>/like', methods=['POST'])
    @login_required
    def api_comments_like(cid):
        """评论点赞/取消点赞。"""
        comment = db.session.get(Comment, cid)
        if not comment:
            return jsonify({'error': '评论不存在'}), 404

        existing = CommentLike.query.filter_by(user_id=current_user.id, comment_id=cid).first()
        if existing:
            db.session.delete(existing)
            comment.likes_count = max(0, (comment.likes_count or 0) - 1)
            db.session.commit()
            return jsonify({'liked': False, 'likesCount': comment.likes_count})

        like = CommentLike(user_id=current_user.id, comment_id=cid)
        db.session.add(like)
        comment.likes_count = (comment.likes_count or 0) + 1
        db.session.commit()
        return jsonify({'liked': True, 'likesCount': comment.likes_count})

    @app.route('/api/notifications')
    @login_required
    def api_notifications_list():
        """获取当前用户的通知列表。"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 30, type=int), 50)
        pagination = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        items = []
        for n in pagination.items:
            from_user = db.session.get(User, n.from_user_id) if n.from_user_id else None
            items.append({
                'id': n.id,
                'type': n.type,
                'fromUserId': n.from_user_id,
                'fromUsername': from_user.username if from_user else None,
                'postId': n.post_id,
                'commentId': n.comment_id,
                'content': n.content,
                'isRead': n.is_read,
                'createdAt': n.created_at.isoformat() if n.created_at else None,
            })

        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

        return jsonify({
            'notifications': items,
            'unreadCount': unread_count,
            'total': pagination.total,
            'page': page,
            'has_next': pagination.has_next,
        })

    @app.route('/api/notifications/read', methods=['POST'])
    @login_required
    def api_notifications_read():
        """标记所有通知为已读。"""
        Notification.query.filter_by(user_id=current_user.id, is_read=False)\
            .update({'is_read': True})
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/notifications/<int:nid>/read', methods=['POST'])
    @login_required
    def api_notification_read_one(nid):
        """标记单条通知为已读。"""
        n = db.session.get(Notification, nid)
        if not n or n.user_id != current_user.id:
            return jsonify({'error': '通知不存在'}), 404
        n.is_read = True
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/reports', methods=['POST'])
    @login_required
    def api_reports_create():
        """创建举报。"""
        data = request.get_json(silent=True) or {}
        target_type = (data.get('targetType') or '').strip()
        target_id = data.get('targetId')
        reason = (data.get('reason') or '').strip()

        if target_type not in ('post', 'comment'):
            return jsonify({'error': '无效的举报目标类型'}), 400
        if not target_id:
            return jsonify({'error': '缺少目标ID'}), 400
        if reason not in REPORT_REASONS:
            return jsonify({'error': '无效的举报原因'}), 400

        existing = Report.query.filter_by(user_id=current_user.id, target_type=target_type,
                                          target_id=target_id, status='pending').first()
        if existing:
            return jsonify({'error': '你已经举报过该内容，请等待审核'}), 400

        report = Report(user_id=current_user.id, target_type=target_type,
                        target_id=target_id, reason=reason)
        db.session.add(report)
        db.session.commit()
        return jsonify({'ok': True, 'id': report.id}), 201

    @app.route('/api/posts/<int:pid>/share', methods=['POST'])
    @login_required
    def api_posts_share(pid):
        """记录分享行为。"""
        post = db.session.get(Post, pid)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        share_url = f"{request.host_url}community?post={pid}"
        return jsonify({
            'ok': True,
            'shareUrl': share_url,
            'title': post.title,
            'description': (post.content[:100] + '...') if post.content and len(post.content) > 100 else (post.content or ''),
        })

    @app.route('/api/masters', methods=['GET'])
    def api_masters_list():
        """大师列表 — 支持 specialty 参数过滤。"""
        specialty = request.args.get('specialty', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)

        query = Master.query
        if specialty:
            query = query.filter(Master.specialties.contains(specialty))

        pagination = query.order_by(Master.rating.desc(), Master.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        masters = []
        for m in pagination.items:
            user = db.session.get(User, m.user_id)
            masters.append({
                'id': m.id,
                'userId': m.user_id,
                'username': user.username if user else '匿名',
                'displayName': m.display_name,
                'avatar': m.avatar,
                'title': m.title,
                'specialties': m.specialties.split(',') if m.specialties else [],
                'verified': m.verified,
                'rating': m.rating,
                'reviewCount': m.review_count,
                'createdAt': m.created_at.isoformat() if m.created_at else None,
            })

        return jsonify({
            'masters': masters,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'disclaimer': '大师信息仅供民俗文化交流参考，不构成命运预测承诺',
        })

    @app.route('/api/masters/apply', methods=['POST'])
    @login_required
    def api_masters_apply():
        """申请成为大师。"""
        existing = Master.query.filter_by(user_id=current_user.id).first()
        if existing:
            return jsonify({'error': '您已提交申请或已是大师'}), 409

        data = request.get_json(silent=True) or {}
        display_name = (data.get('displayName') or '').strip()
        title = (data.get('title') or '').strip()
        specialties = data.get('specialties', '')
        bio = (data.get('bio') or '').strip()

        if not display_name or len(display_name) > 50:
            return jsonify({'error': '展示名需1-50个字符'}), 400
        if not title:
            return jsonify({'error': '请填写头衔'}), 400

        if isinstance(specialties, list):
            spec_str = ','.join(s.strip() for s in specialties if s.strip())
        else:
            spec_str = ','.join(s.strip() for s in str(specialties).split(',') if s.strip())

        master = Master(
            user_id=current_user.id, display_name=display_name,
            title=title, specialties=spec_str, bio=bio,
            verified=False,
        )
        db.session.add(master)
        db.session.commit()
        return jsonify({'id': master.id, 'verified': False, 'disclaimer': '大师认证仅供民俗文化交流参考，不构成命运预测承诺'}), 201

    @app.route('/api/masters/<int:mid>')
    def api_masters_detail(mid):
        """大师详情。"""
        master = db.session.get(Master, mid)
        if not master:
            return jsonify({'error': '大师不存在'}), 404

        user = db.session.get(User, master.user_id)
        return jsonify({
            'id': master.id,
            'userId': master.user_id,
            'username': user.username if user else '匿名',
            'displayName': master.display_name,
            'avatar': master.avatar,
            'title': master.title,
            'specialties': master.specialties.split(',') if master.specialties else [],
            'bio': master.bio,
            'verified': master.verified,
            'rating': master.rating,
            'reviewCount': master.review_count,
            'createdAt': master.created_at.isoformat() if master.created_at else None,
            'disclaimer': '大师信息仅供民俗文化交流参考，不构成命运预测承诺',
        })
