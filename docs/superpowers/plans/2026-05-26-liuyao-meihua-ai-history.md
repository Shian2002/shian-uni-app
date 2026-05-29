# 六爻 & 梅花易数 AI 解读对话历史保存 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 六爻和梅花易数的 AI 解读完成时自动保存对话历史，并在侧边栏中按类型分组显示，附带正确的北京时间

**Architecture:** 参照塔罗牌已实现的 `TarotConversation` 表 + CRUD API + 前端保存 + 侧边栏集成模式，为六爻和梅花各建独立 Conversation 表，在前端 `onDone` 回调中调用保存，侧边栏合并渲染时补充两个工具的请求

**Tech Stack:** Flask + SQLAlchemy + uni-app + Vue 3

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `server-backup/backend/models.py` | SQLAlchemy 模型定义 | 新增 `LiuyaoConversation`、`MeihuaConversation` |
| `server-backup/backend/app.py` | Flask API 路由 | 新增 8 个 API 路由，修改 import |
| `src/pages/liuyao/index.vue` | 六爻页面 | 新增 `_saveLyConversation`、`_updateLyConversation` |
| `src/pages/meihua/index.vue` | 梅花页面 | 新增 `_saveMhConversation`、`_updateMhConversation` |
| `src/components/TopNav.vue` | 侧边栏组件 | 新增2个请求+合并+查看函数+时区修复 |

---

## 实施顺序

1. 后端模型 + API 路由
2. 前端六爻保存逻辑
3. 前端梅花保存逻辑
4. 前端侧边栏集成 + 时区修复 + 查看弹窗
5. 构建 + 部署

---

### Task 1: 后端模型 — 新增 LiuyaoConversation 和 MeihuaConversation

**Files:**
- Modify: `server-backup/backend/models.py`（追加在 TarotConversation 之后）

- [ ] **Step 1: 在 models.py 中新增六爻对话模型**

打开 `server-backup/backend/models.py`，在 `TarotConversation` 类之后追加：

```python
class LiuyaoConversation(db.Model):
    """六爻对话历史"""
    __tablename__ = 'liuyao_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(100))
    scene_type = db.Column(db.String(40))
    liuyao_data = db.Column(db.Text)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MeihuaConversation(db.Model):
    """梅花易数对话历史"""
    __tablename__ = 'meihua_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(100))
    method = db.Column(db.String(20))
    meihua_data = db.Column(db.Text)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 保存 models.py**

确认文件保存成功，无语法错误。

---

### Task 2: 后端 API — 六爻和梅花的对话 CRUD 路由

**Files:**
- Modify: `server-backup/backend/app.py`

- [ ] **Step 1: 补充 import**

找到 import 行（约 L139），在 `TarotConversation` 后面加上 `LiuyaoConversation, MeihuaConversation`：

```python
from models import User, Record, UserProfile, FollowUp, Collection
from models import Post, Comment, Master, PostLike, Membership, PointLog, PaidContent, Purchase, TarotConversation
from models import LiuyaoConversation, MeihuaConversation
from models import BaziRecord
```

- [ ] **Step 2: 新增六爻对话 API（追加在塔罗对话 API 之后）**

打开 `server-backup/backend/app.py`，在 `api_tarot_conversation_delete` 函数之后（约 L3406）、`# 紫微斗数` 注释之前，插入以下代码：

```python
# ─── 六爻对话历史 API ───

@app.route('/api/liuyao/conversations', methods=['GET'])
@login_required
def api_liuyao_conversations():
    """获取当前用户的六爻对话列表"""
    convs = LiuyaoConversation.query.filter_by(user_id=current_user.id)\
        .order_by(LiuyaoConversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id, 'title': c.title,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    } for c in convs])


@app.route('/api/liuyao/conversations', methods=['POST'])
@login_required
def api_liuyao_conversations_create():
    """创建/更新六爻对话"""
    data = request.get_json(silent=True) or {}
    conv_id = data.get('id')
    messages = data.get('messages') or []
    if conv_id:
        conv = LiuyaoConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
        if conv:
            conv.messages_json = json.dumps(messages)
            conv.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'id': conv.id, 'ok': True})
    conv = LiuyaoConversation(
        user_id=current_user.id,
        title=(data.get('title') or '')[：100],
        scene_type=(data.get('scene_type') or '')[:40],
        liuyao_data=json.dumps(data.get('liuyao_data') or {}),
        messages_json=json.dumps(messages),
    )
    db.session.add(conv)
    db.session.commit()
    return jsonify({'id': conv.id, 'ok': True})


@app.route('/api/liuyao/conversations/<int:cid>', methods=['GET'])
@login_required
def api_liuyao_conversation_detail(cid):
    """获取单条六爻对话详情"""
    conv = LiuyaoConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify({
        'id': conv.id, 'title': conv.title,
        'messages': json.loads(conv.messages_json) if conv.messages_json else [],
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
    })


@app.route('/api/liuyao/conversations/<int:cid>', methods=['DELETE'])
@login_required
def api_liuyao_conversation_delete(cid):
    """删除六爻对话"""
    conv = LiuyaoConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'ok': True})


# ─── 梅花易数对话历史 API ───

@app.route('/api/meihua/conversations', methods=['GET'])
@login_required
def api_meihua_conversations():
    """获取当前用户的梅花对话列表"""
    convs = MeihuaConversation.query.filter_by(user_id=current_user.id)\
        .order_by(MeihuaConversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id, 'title': c.title,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    } for c in convs])


@app.route('/api/meihua/conversations', methods=['POST'])
@login_required
def api_meihua_conversations_create():
    """创建/更新梅花对话"""
    data = request.get_json(silent=True) or {}
    conv_id = data.get('id')
    messages = data.get('messages') or []
    if conv_id:
        conv = MeihuaConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
        if conv:
            conv.messages_json = json.dumps(messages)
            conv.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'id': conv.id, 'ok': True})
    conv = MeihuaConversation(
        user_id=current_user.id,
        title=(data.get('title') or '')[:100],
        method=(data.get('method') or '')[:20],
        meihua_data=json.dumps(data.get('meihua_data') or {}),
        messages_json=json.dumps(messages),
    )
    db.session.add(conv)
    db.session.commit()
    return jsonify({'id': conv.id, 'ok': True})


@app.route('/api/meihua/conversations/<int:cid>', methods=['GET'])
@login_required
def api_meihua_conversation_detail(cid):
    """获取单条梅花对话详情"""
    conv = MeihuaConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify({
        'id': conv.id, 'title': conv.title,
        'messages': json.loads(conv.messages_json) if conv.messages_json else [],
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
    })


@app.route('/api/meihua/conversations/<int:cid>', methods=['DELETE'])
@login_required
def api_meihua_conversation_delete(cid):
    """删除梅花对话"""
    conv = MeihuaConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'ok': True})
```

注意：第7行有中文冒号 `：100` 为笔误，实际应写 `[:100]`。请确认编辑器自动修正，或手动修正。

- [ ] **Step 3: 验证**

检查 `app.py` 末尾无语法错误：

```bash
cd server-backup/backend && python3 -c "import py_compile; py_compile.compile('app.py', doraise=True)" && echo "OK"
```

---

### Task 3: 前端 liuyao/index.vue — 对话保存逻辑

**Files:**
- Modify: `src/pages/liuyao/index.vue`

- [ ] **Step 1: 在 `liuyaoAskPaipan` 的 `onDone` 末尾调用保存**

找到 `liuyaoAskPaipan()` 函数中 `onDone` 回调（约 L546-558），在设置 `window._lyChatHistory` 之后、`laiResult.value` 之前，追加 `_saveLyConversation(question)` 调用：

```javascript
    onDone: function(fullText) {
      window._lyChatHistory = [
        { role: 'user', content: question },
        { role: 'assistant', content: fullText }
      ]
      _saveLyConversation(question)  // 新增
      laiResult.value = fullText
      var bar = document.getElementById('lyChatInputBar')
      if (bar) bar.style.display = 'flex'
    },
```

- [ ] **Step 2: 在 `lySendFollowUp` 的 `onDone` 末尾调用更新**

找到 `lySendFollowUp()` 函数末尾的 `onDone`（约 L704-708），追加 `_updateLyConversation()`：

```javascript
    onDone: function(fullText) {
      history.push({ role: 'assistant', content: fullText })
      window._lyChatHistory = history
      _updateLyConversation()  // 新增
    },
```

- [ ] **Step 3: 在文件末尾（最后一个 `</script>` 之前）添加保存函数**

```javascript

// ═══ 六爻对话保存 ═══
var _lyCurrentConvId = null

function _saveLyConversation(question) {
  var title = (question || '六爻占卜').substring(0, 50)
  var typeSelect = document.getElementById('lai-type')
  var sceneType = typeSelect ? typeSelect.value : ''
  uni.request({
    url: '/api/liuyao/conversations', method: 'POST',
    data: {
      title: title, scene_type: sceneType,
      question: question,
      messages: window._lyChatHistory || []
    },
    success: function(res) {
      if (res.data && res.data.id) _lyCurrentConvId = res.data.id
      window.__sidebarCache = null
    },
    fail: function(err) { console.error('[liuyao] 保存对话失败:', err) }
  })
}

function _updateLyConversation() {
  if (!_lyCurrentConvId) return
  uni.request({
    url: '/api/liuyao/conversations', method: 'POST',
    data: { id: _lyCurrentConvId, messages: window._lyChatHistory || [] },
    success: function() { window.__sidebarCache = null },
    fail: function(err) { console.error('[liuyao] 更新对话失败:', err) }
  })
}
```

---

### Task 4: 前端 meihua/index.vue — 对话保存逻辑

**Files:**
- Modify: `src/pages/meihua/index.vue`

- [ ] **Step 1: 在 `meihuaAskPaipan` 的 `onDone` 末尾调用保存**

找到 `meihuaAskPaipan()` 中 `onDone`（约 L373-383），追加 `_saveMhConversation(question)`：

```javascript
    onDone: function(fullText) {
      window._mhChatHistory = [
        { role: 'user', content: question },
        { role: 'assistant', content: fullText }
      ]
      _saveMhConversation(question)  // 新增
      maiResult.value = fullText
      var bar = document.getElementById('mhChatInputBar')
      if (bar) bar.style.display = 'flex'
    },
```

- [ ] **Step 2: 在 `mhSendFollowUp` 的 `onDone` 末尾调用更新**

找到 `mhSendFollowUp()` 末尾的 `onDone`（约 L515），追加 `_updateMhConversation()`：

```javascript
    onDone: function(fullText) { history.push({ role: 'assistant', content: fullText }); window._mhChatHistory = history; _updateMhConversation() },
```

- [ ] **Step 3: 在文件末尾添加梅花保存函数**

```javascript

// ═══ 梅花对话保存 ═══
var _mhCurrentConvId = null

function _saveMhConversation(question) {
  var title = (question || '梅花易数').substring(0, 50)
  var methodSelect = document.getElementById('mai-method')
  var method = methodSelect ? document.querySelector('#mai-method .selected') ? document.querySelector('#mai-method .selected').getAttribute('data-value') : '' : ''
  uni.request({
    url: '/api/meihua/conversations', method: 'POST',
    data: {
      title: title, method: method,
      question: question,
      messages: window._mhChatHistory || []
    },
    success: function(res) {
      if (res.data && res.data.id) _mhCurrentConvId = res.data.id
      window.__sidebarCache = null
    },
    fail: function(err) { console.error('[meihua] 保存对话失败:', err) }
  })
}

function _updateMhConversation() {
  if (!_mhCurrentConvId) return
  uni.request({
    url: '/api/meihua/conversations', method: 'POST',
    data: { id: _mhCurrentConvId, messages: window._mhChatHistory || [] },
    success: function() { window.__sidebarCache = null },
    fail: function(err) { console.error('[meihua] 更新对话失败:', err) }
  })
}
```

---

### Task 5: 前端 TopNav.vue — 侧边栏集成 + 时区修复

**Files:**
- Modify: `src/components/TopNav.vue`

- [ ] **Step 1: 修复时区 — 修改 `_renderSidebarGroups` 中的时间格式化**

找到 `_renderSidebarGroups` 函数（约 L449），将时间格式化代码从：
```javascript
var time = r.created_at ? r.created_at.substring(0, 16).replace('T', ' ') : ''
```
改为：
```javascript
var time = ''
if (r.created_at) {
  var t = new Date(r.created_at)
  if (!isNaN(t.getTime())) {
    var offset = 8 * 60
    var local = new Date(t.getTime() + offset * 60 * 1000)
    var y = local.getUTCFullYear()
    var M = ('0' + (local.getUTCMonth() + 1)).slice(-2)
    var d = ('0' + local.getUTCDate()).slice(-2)
    var h = ('0' + local.getUTCHours()).slice(-2)
    var m = ('0' + local.getUTCMinutes()).slice(-2)
    time = y + '-' + M + '-' + d + ' ' + h + ':' + m
  }
}
```

- [ ] **Step 2: 在 `toggleSidebar` 中添加六爻和梅花的请求**

找到 `toggleSidebar()` 函数中现有的数据请求区域（约 L440-445，塔罗请求附近），在塔罗加载回调下方新增：

在 `var tarotLoaded = false` 下方新增：
```javascript
var lyConvLoaded = false, mhConvLoaded = false
var lyConvItems = [], mhConvItems = []
```

在塔罗请求的 `fail` 回调下方新增两个请求（注意 `_renderMerged` 是闭包，不需要修改其定义）：

```javascript
  uni.request({ url: '/api/liuyao/conversations', method: 'GET', success: function(res) {
    lyConvItems = res.data || []; if (!Array.isArray(lyConvItems)) lyConvItems = []
    lyConvLoaded = true; _renderMerged()
  }, fail: function() { lyConvLoaded = true; _renderMerged() }})
  uni.request({ url: '/api/meihua/conversations', method: 'GET', success: function(res) {
    mhConvItems = res.data || []; if (!Array.isArray(mhConvItems)) mhConvItems = []
    mhConvLoaded = true; _renderMerged()
  }, fail: function() { mhConvLoaded = true; _renderMerged() }})
```

- [ ] **Step 3: 修改 `_renderMerged` 合并六爻和梅花条目**

找到 `_renderMerged` 函数体内（约 L431-445），在 `tarotItems.forEach` 之后、`if (!allRecords.length)` 之前插入：

```javascript
    // 合并六爻条目
    lyConvItems.forEach(function(c) {
      allRecords.push({ id: 'ly_' + c.id, app_type: 'liuyao', question: c.title || '六爻占卜', created_at: c.updated_at || c.created_at, _lyConvId: c.id })
    })
    // 合并梅花条目
    mhConvItems.forEach(function(c) {
      allRecords.push({ id: 'mh_' + c.id, app_type: 'meihua', question: c.title || '梅花易数', created_at: c.updated_at || c.created_at, _mhConvId: c.id })
    })
```

然后修改 `_renderMerged` 中等待条件的栅栏（原来只检查 `recordsLoaded && tarotLoaded`），改为同时检查 `lyConvLoaded && mhConvLoaded`：

```javascript
    if (!recordsLoaded || !tarotLoaded || !lyConvLoaded || !mhConvLoaded) return
```

- [ ] **Step 4: 修改分组渲染条件，为六爻和梅花条目绑定点击事件**

找到 `_renderSidebarGroups` 函数中构建 `clickAction` 的部分（约 L462-466），在塔罗条件之后追加：

```javascript
      var clickAction = r._tarotConvId
        ? 'onclick="window._showTarotConv(' + r._tarotConvId + ')"'
        : r._lyConvId
        ? 'onclick="window._showLyConvDetail(' + r._lyConvId + ')"'
        : r._mhConvId
        ? 'onclick="window._showMhConvDetail(' + r._mhConvId + ')"'
        : 'onclick="window._showHistoryDetail(' + r.id + ')"'
```

- [ ] **Step 5: 新增六爻和梅花的查看函数**

在 `_showTarotConv` 函数之后（约 L494）、`_showHistoryDetail` 之前，插入：

```javascript
// 六爻对话查看
window._showLyConvDetail = function(cid) {
  uni.request({ url: '/api/liuyao/conversations/' + cid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) return
    var overlay = document.getElementById('historyDetailOverlayGlobal')
    var title = document.getElementById('historyDetailTitle')
    var content = document.getElementById('historyDetailContent')
    if (overlay) overlay.classList.add('open')
    if (title) title.textContent = d.title || '六爻占卜'
    var msgs = d.messages || []
    var html = ''
    msgs.forEach(function(m) {
      var label = m.role === 'user' ? '🙋 我的问题' : '🔮 AI 解读'
      var cls = m.role === 'user' ? 'tarot-detail-user' : 'tarot-detail-ai'
      html += '<div class="' + cls + '"><div class="tarot-detail-label">' + label + '</div><div class="tarot-detail-body">' + _escHtml(m.content || '') + '</div></div>'
    })
    if (!html) html = '<div style="color:var(--text-3);text-align:center;padding:20px;">暂无解读内容</div>'
    if (content) content.innerHTML = html
    window._xc_toggleSidebar()
  }})
}

// 梅花对话查看
window._showMhConvDetail = function(cid) {
  uni.request({ url: '/api/meihua/conversations/' + cid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) return
    var overlay = document.getElementById('historyDetailOverlayGlobal')
    var title = document.getElementById('historyDetailTitle')
    var content = document.getElementById('historyDetailContent')
    if (overlay) overlay.classList.add('open')
    if (title) title.textContent = d.title || '梅花易数'
    var msgs = d.messages || []
    var html = ''
    msgs.forEach(function(m) {
      var label = m.role === 'user' ? '🙋 我的问题' : '🔮 AI 解读'
      var cls = m.role === 'user' ? 'tarot-detail-user' : 'tarot-detail-ai'
      html += '<div class="' + cls + '"><div class="tarot-detail-label">' + label + '</div><div class="tarot-detail-body">' + _escHtml(m.content || '') + '</div></div>'
    })
    if (!html) html = '<div style="color:var(--text-3);text-align:center;padding:20px;">暂无解读内容</div>'
    if (content) content.innerHTML = html
    window._xc_toggleSidebar()
  }})
}
```

---

### Task 6: 构建 + 部署 + 测试

**Files:**
- 无代码改动

- [ ] **Step 1: 重启后端**

登录服务器，重启后端使数据库新表和 API 生效：
```bash
ssh -i $HOME/.ssh/deploy_key lighthouse@119.29.128.18 "sudo fuser -k 5199/tcp 2>/dev/null; sleep 2; cd /opt/xuan-cet/backend && sudo -b nohup ./venv/bin/python app.py > /tmp/xuan-cet.log 2>&1"
```

验证后端启动成功：
```bash
ssh -i $HOME/.ssh/deploy_key lighthouse@119.29.128.18 "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5199/"
```
预期返回 `200`。

- [ ] **Step 2: 构建前端**

```bash
npm run build:h5
```
预期：`DONE Build complete.`

- [ ] **Step 3: 部署前端**

```bash
bash deploy-to-server.sh
```
预期：assets 文件上传到 `/var/www/xuan-cet/assets/`，返回 `后端 200 OK`。

- [ ] **Step 4: 验证 API 可用性**

```bash
# 测试六爻对话列表 API（需要 cookie）
curl -s -b "session=..." http://119.29.128.18/api/liuyao/conversations
# 预期返回 JSON 数组

# 测试梅花对话列表 API
curl -s -b "session=..." http://119.29.128.18/api/meihua/conversations
# 预期返回 JSON 数组
```

- [ ] **Step 5: 功能测试**

打开浏览器访问 http://119.29.128.18 ，登录后：

1. 进入六爻页面 → 选择"时安六爻系统"Tab → 输入问题 → 点击"一键起卦·深度解读"
2. 等待 AI 解读完成
3. 点击右上角 ☰ 打开侧边栏
4. 验证「🧭 六爻排盘」分组下出现刚刚的解读记录
5. 点击该记录 → 弹窗显示完整对话（🙋 我的问题 + 🔮 AI 解读）
6. 验证时间显示为北京时间
7. 进入梅花易数页面 → 重复以上步骤，验证「🌸 梅花易数」分组
