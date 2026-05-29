# 六爻 & 梅花易数 AI 解读对话历史保存设计

## 背景

六爻和梅花易数页面已具备完整的 SSE 流式 AI 解读功能（打字机效果、追问、Markdown 卡片渲染、积分消耗），但缺少对话历史保存到服务端和侧边栏历史记录显示的能力。塔罗牌的对话历史保存机制可以作为模板复用。

## 目标

1. 六爻 AI 解读完成后，对话（用户问题 + AI 回答）自动保存到服务端
2. 梅花易数 AI 解读完成后，对话自动保存到服务端
3. 侧边栏显示六爻和梅花的对话历史，按类型分组
4. 点击侧边栏条目可查看完整对话内容（弹窗）
5. 侧边栏时间显示正确（北京时间 UTC+8）
6. 追问后的新内容实时更新到服务端

## 数据流

```
用户点击"一键起卦·深度解读"
  → SSE 流式解读 (/api/liuyao/ask/stream 或 /api/meihua/ask/stream)
  → onDone 回调
  → _saveXxxConversation(question)  →  POST /api/{tool}/conversations
  → 写入 LiuyaoConversation / MeihuaConversation 表
  → window.__sidebarCache = null
  → 用户打开侧边栏 → 重新拉取最新对话列表
  → 侧边栏按类型分组显示
  → 点击条目 → 弹窗显示完整对话
```

## 数据库模型

### LiuyaoConversation

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 主键 |
| user_id | Integer, FK → user.id | 用户 ID，索引 |
| title | String(100) | 用户问题截取前50字 |
| scene_type | String(40) | 问事类型 (s_project/s_loveback 等) |
| liuyao_data | Text | 排盘结果 JSON |
| messages_json | Text | 对话轮次 JSON |
| created_at | DateTime | 创建时间 (UTC) |
| updated_at | DateTime | 更新时间 (UTC) |

### MeihuaConversation

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 主键 |
| user_id | Integer, FK → user.id | 用户 ID，索引 |
| title | String(100) | 用户问题截取前50字 |
| method | String(20) | 起卦方式 (time/number/word) |
| meihua_data | Text | 排盘结果 JSON |
| messages_json | Text | 对话轮次 JSON |
| created_at | DateTime | 创建时间 (UTC) |
| updated_at | DateTime | 更新时间 (UTC) |

## API 路由

每个工具独立一套 RESTful API（参照 `/api/tarot/conversations`）：

| 路由 | 方法 | 功能 | 认证 |
|------|------|------|------|
| `/api/liuyao/conversations` | GET | 获取当前用户的六爻对话列表 | @login_required |
| `/api/liuyao/conversations` | POST | 创建/更新六爻对话 | @login_required |
| `/api/liuyao/conversations/<id>` | GET | 获取单条六爻对话详情 | @login_required |
| `/api/liuyao/conversations/<id>` | DELETE | 删除六爻对话 | @login_required |
| `/api/meihua/conversations` | GET | 获取当前用户的梅花对话列表 | @login_required |
| `/api/meihua/conversations` | POST | 创建/更新梅花对话 | @login_required |
| `/api/meihua/conversations/<id>` | GET | 获取单条梅花对话详情 | @login_required |
| `/api/meihua/conversations/<id>` | DELETE | 删除梅花对话 | @login_required |

### POST /api/{tool}/conversations

请求体：
```json
{
  "id": null,           // 新建时为 null，更新时传已有 id
  "title": "问题摘要",
  "scene_type": "s_project",  // 仅六爻
  "method": "time",           // 仅梅花
  "question": "用户问题",
  "messages": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

返回：
```json
{ "id": 123, "ok": true }
```

### GET /api/{tool}/conversations

返回列表（按 updated_at 降序）：
```json
[
  { "id": 123, "title": "...", "created_at": "...", "updated_at": "..." },
  ...
]
```

### GET /api/{tool}/conversations/<id>

返回详情：
```json
{
  "id": 123,
  "title": "...",
  "created_at": "...",
  "updated_at": "...",
  "messages": [ ... ]
}
```

## 前端改动

### liuyao/index.vue

在 `liuyaoAskPaipan()` 的 `onDone` 回调末尾调用 `_saveLyConversation(question)`。

新增函数：
- `_saveLyConversation(question)` — POST /api/liuyao/conversations，成功后清除 `window.__sidebarCache = null`
- `_updateLyConversation()` — POST /api/liuyao/conversations 更新消息，成功后清除缓存

在 `lySendFollowUp()` 的 `onDone` 回调末尾调用 `_updateLyConversation()`。

### meihua/index.vue

同上，函数名改为 `_saveMhConversation` / `_updateMhConversation`，API 路径改为 `/api/meihua/conversations`。

### TopNav.vue

1. `toggleSidebar()` 中新增两个异步请求（六爻对话 + 梅花对话），与现有数据合并
2. `_renderMerged()` 中将六爻和梅花条目格式化为标准格式（含 `_lyConvId` / `_mhConvId` 标记）
3. 新增 `window._showLyConvDetail(cid)` 和 `window._showMhConvDetail(cid)` 查看函数
4. 侧边栏分组渲染时，六爻条目 onclick → `_showLyConvDetail`，梅花 → `_showMhConvDetail`
5. **修复时区**：`_renderSidebarGroups` 中所有时间使用 UTC+8 转换

## 时区修复

后端 `datetime.utcnow()` 存储 UTC 时间。侧边栏显示时在前端转为北京时间：

```javascript
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
```

## 改动文件清单

| 文件 | 改动内容 |
|------|----------|
| server-backup/backend/models.py | 新增 LiuyaoConversation、MeihuaConversation 模型 |
| server-backup/backend/app.py | 新增 8 个 API 路由 |
| src/pages/liuyao/index.vue | 新增 `_saveLyConversation`、`_updateLyConversation` |
| src/pages/meihua/index.vue | 新增 `_saveMhConversation`、`_updateMhConversation` |
| src/components/TopNav.vue | 新增请求、合并、查看函数、时区修复 |

## 实施顺序

1. 后端：模型 + API 路由
2. 前端：六爻保存逻辑
3. 前端：梅花保存逻辑
4. 前端：侧边栏集成 + 时区修复 + 查看弹窗
5. 构建 + 部署 + 测试
