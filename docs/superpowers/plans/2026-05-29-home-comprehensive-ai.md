# 首页综合 AI 问答 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在首页增加一个类似 Codex 桌面端的综合输入框，支持选择已保存排盘档案、切换大模型、复选术数模型、消耗积分提示、流式生成回答，并把内容保存到“对话历史 > 综合”中支持继续追问。

**Architecture:** 前端首页负责组合输入体验和流式对话 UI；后端新增综合 AI 聚合接口，先调用现有精准排盘能力生成结构化盘面，再把选中的术数盘面、用户问题、历史追问和模型配置组装为统一提示词发送给免费模型。历史存储新增 `ComprehensiveConversation`，保持与八字、奇门、塔罗等现有 conversation API 同构，便于对话历史页面接入“综合”标签。

**Tech Stack:** uni-app + Vue 3 + H5、Flask、SQLAlchemy、SQLite/MySQL 兼容迁移、现有 `deepseek_service.get_reading_stream`、现有 `Membership/PointLog` 积分系统。

---

## 关键约束

- 首页当前本地文件 `src/pages/index/index.vue` 与线上表现不完全一致，执行前必须先确认哪些未提交改动要保留。
- 不重写各术数排盘算法，只从现有后端排盘函数/API 获取参数与盘面结果。
- 第一版只接入当前可用免费模型；模型切换 UI 先按配置驱动，后续可扩展收费模型。
- 综合 AI 的积分消耗必须在前端展示，在后端二次校验扣除，不能只靠前端。
- 追问必须复用原会话的排盘上下文，不能每次追问都丢失盘面。

## 文件结构

- Modify: `backend/models.py`
  - 新增 `ComprehensiveConversation`，字段与现有各术数 conversation 保持一致，额外存储 `profile_data`、`models_json`、`paipan_json`、`model_id`、`points_cost`。
- Modify: `backend/app.py`
  - 增加数据库迁移字段/表检查。
  - 增加模型配置接口、综合会话 CRUD、综合流式问答接口。
  - 增加排盘上下文构建函数，调用现有排盘逻辑。
- Create: `backend/comprehensive_ai.py`
  - 封装模型列表、积分规则、术数选择校验、综合提示词构建、SSE 事件格式。
- Modify: `src/pages/index/index.vue`
  - 首页首屏新增 Codex 风格输入框、档案选择、模型选择、术数复选、积分提示、流式结果和追问入口。
- Modify: `src/package-user/history/index.vue`
  - 对话历史增加“综合”标签，加载综合会话列表，点击后进入首页并恢复会话。
- Modify: `database/schema.sql`
  - 补充 `comprehensive_conversation` 表结构，便于新库初始化。
- Optional Create: `src/utils/comprehensive-chat.js`
  - 如果首页文件继续膨胀，把 SSE、历史保存、恢复会话逻辑抽到独立工具文件。

## 数据模型

### `ComprehensiveConversation`

```python
class ComprehensiveConversation(db.Model):
    """首页综合 AI 对话历史"""
    __tablename__ = 'comprehensive_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(100))
    profile_data = db.Column(db.Text)      # 选择的客户/用户档案快照
    models_json = db.Column(db.Text)       # 选中的术数模型列表，如 ["bazi", "ziwei"]
    paipan_json = db.Column(db.Text)       # 后端生成的各术数盘面上下文
    model_id = db.Column(db.String(50))    # 当前大模型 id
    points_cost = db.Column(db.Integer, default=0)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 模型配置第一版

```python
COMPREHENSIVE_LLM_MODELS = [
    {
        "id": "free",
        "name": "免费模型",
        "provider": "deepseek",
        "strength": "基础",
        "cost_base": 0,
        "cost_per_tool": 0,
        "followup_cost": 0,
        "enabled": True,
    }
]
```

### 术数模型第一版

```python
COMPREHENSIVE_TOOL_MODELS = [
    {"id": "bazi", "name": "八字", "cost": 1},
    {"id": "ziwei", "name": "紫微斗数", "cost": 1},
    {"id": "qimen", "name": "奇门遁甲", "cost": 1},
    {"id": "liuyao", "name": "六爻", "cost": 1},
    {"id": "meihua", "name": "梅花易数", "cost": 1},
]
```

## 后端 API 设计

### 获取模型与积分规则

`GET /api/comprehensive/options`

Response:

```json
{
  "llm_models": [{"id":"free","name":"免费模型","strength":"基础","cost_base":2,"cost_per_tool":1,"followup_cost":1,"enabled":true}],
  "tool_models": [{"id":"bazi","name":"八字","cost":1}],
  "points": 18
}
```

### 综合 AI 流式问答

`POST /api/comprehensive/ask/stream`

Request:

```json
{
  "question": "我今年事业和感情需要注意什么？",
  "profile_id": 12,
  "profile": null,
  "llm_model": "free",
  "tool_models": ["bazi", "ziwei"],
  "history": [],
  "conversation_id": null
}
```

SSE events:

```json
{"stage":"profile","message":"正在读取命盘档案..."}
{"stage":"paipan","message":"正在生成八字盘..."}
{"stage":"paipan","message":"正在生成紫微斗数盘..."}
{"stage":"generating","message":"正在生成综合解读..."}
{"content":"第一段回答..."}
{"done":true,"conversation_id":33,"points_left":15}
```

### 综合对话 CRUD

- `GET /api/comprehensive/conversations`
- `POST /api/comprehensive/conversations`
- `GET /api/comprehensive/conversations/<id>`
- `DELETE /api/comprehensive/conversations/<id>`

返回结构与现有 `/api/bazi/conversations`、`/api/ziwei/conversations` 保持一致，额外返回 `profile_data`、`models`、`paipan`、`model_id`。

## 实施任务

### Task 1: 保护现有工作区并确认首页基线

**Files:**
- Read: `src/pages/index/index.vue`
- Read: `git status --short`
- Read: `git diff -- src/pages/index/index.vue`

- [ ] **Step 1: 查看未提交改动**

Run:

```bash
git status --short
git diff -- src/pages/index/index.vue
```

Expected:

```text
看到首页是否已有用户未提交改动，并记录哪些内容不能覆盖。
```

- [ ] **Step 2: 确认首页应以哪个版本为准**

检查线上首页和本地首页差异：

```bash
npm run build:h5
```

Expected:

```text
构建通过；如果本地首页明显缺少线上功能，先暂停询问是否以线上恢复版为基线。
```

### Task 2: 新增综合对话数据表

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/app.py`
- Modify: `database/schema.sql`

- [ ] **Step 1: 在 `backend/models.py` 添加模型**

Add after `ZiweiConversation`:

```python
class ComprehensiveConversation(db.Model):
    """首页综合 AI 对话历史"""
    __tablename__ = 'comprehensive_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(100))
    profile_data = db.Column(db.Text)
    models_json = db.Column(db.Text)
    paipan_json = db.Column(db.Text)
    model_id = db.Column(db.String(50))
    points_cost = db.Column(db.Integer, default=0)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 更新 `backend/app.py` imports**

Change:

```python
from models import Post, Comment, Master, PostLike, Membership, PointLog, PaidContent, Purchase, TarotConversation, LiuyaoConversation, MeihuaConversation, QimenConversation, BaziConversation, ZiweiConversation
```

To:

```python
from models import Post, Comment, Master, PostLike, Membership, PointLog, PaidContent, Purchase, TarotConversation, LiuyaoConversation, MeihuaConversation, QimenConversation, BaziConversation, ZiweiConversation, ComprehensiveConversation
```

- [ ] **Step 3: 补充 schema**

Add to `database/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS comprehensive_conversation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  title VARCHAR(100),
  profile_data TEXT,
  models_json TEXT,
  paipan_json TEXT,
  model_id VARCHAR(50),
  points_cost INTEGER DEFAULT 0,
  messages_json TEXT,
  created_at DATETIME,
  updated_at DATETIME,
  FOREIGN KEY(user_id) REFERENCES user(id)
);
CREATE INDEX IF NOT EXISTS idx_comprehensive_conversation_user_id ON comprehensive_conversation(user_id);
```

- [ ] **Step 4: 验证模型导入**

Run:

```bash
python -m py_compile backend/models.py backend/app.py
```

Expected:

```text
无语法错误。
```

### Task 3: 新增综合 AI 服务模块

**Files:**
- Create: `backend/comprehensive_ai.py`

- [ ] **Step 1: 创建配置与校验函数**

```python
import json

COMPREHENSIVE_LLM_MODELS = [
    {"id": "free", "name": "免费模型", "provider": "deepseek", "strength": "基础", "cost_base": 2, "cost_per_tool": 1, "followup_cost": 1, "enabled": True}
]

COMPREHENSIVE_TOOL_MODELS = [
    {"id": "bazi", "name": "八字", "cost": 1},
    {"id": "ziwei", "name": "紫微斗数", "cost": 1},
    {"id": "qimen", "name": "奇门遁甲", "cost": 1},
    {"id": "liuyao", "name": "六爻", "cost": 1},
    {"id": "meihua", "name": "梅花易数", "cost": 1},
]

def get_llm_model(model_id):
    for model in COMPREHENSIVE_LLM_MODELS:
        if model["id"] == model_id and model.get("enabled"):
            return model
    return COMPREHENSIVE_LLM_MODELS[0]

def normalize_tool_models(tool_models):
    allowed = {item["id"] for item in COMPREHENSIVE_TOOL_MODELS}
    result = []
    for item in tool_models or []:
        if item in allowed and item not in result:
            result.append(item)
    return result

def calculate_cost(model_id, tool_models, is_followup=False):
    model = get_llm_model(model_id)
    if is_followup:
        return int(model.get("followup_cost", 1))
    return int(model.get("cost_base", 2)) + len(normalize_tool_models(tool_models)) * int(model.get("cost_per_tool", 1))
```

- [ ] **Step 2: 添加提示词构建函数**

```python
def build_comprehensive_messages(question, profile, tool_models, paipan_context, history=None):
    system = """你是时安解忧屋的综合命理答疑助手。
你必须基于后端已经生成的排盘数据进行分析，不要自行编造出生信息、干支、宫位、星曜或卦象。
回答要求：
1. 先给出直接结论；
2. 分术数说明依据；
3. 汇总不同术数之间一致和冲突的地方；
4. 给出可执行建议；
5. 明确提示内容仅为民俗文化参考，不构成现实决策承诺。
"""
    context = {
        "profile": profile or {},
        "selected_tools": tool_models,
        "paipan_context": paipan_context or {},
    }
    messages = [{"role": "system", "content": system}]
    for item in history or []:
        if item.get("role") in ("user", "assistant"):
            messages.append({"role": item["role"], "content": str(item.get("content", ""))[:6000]})
    messages.append({
        "role": "user",
        "content": "用户问题：%s\n\n后端排盘上下文：\n%s" % (question, json.dumps(context, ensure_ascii=False, indent=2))
    })
    return messages
```

### Task 4: 后端综合接口

**Files:**
- Modify: `backend/app.py`

- [ ] **Step 1: 增加 imports**

```python
from comprehensive_ai import (
    COMPREHENSIVE_LLM_MODELS,
    COMPREHENSIVE_TOOL_MODELS,
    calculate_cost,
    normalize_tool_models,
    build_comprehensive_messages,
)
```

- [ ] **Step 2: 增加 options API**

```python
@app.route('/api/comprehensive/options')
@login_required
def api_comprehensive_options():
    membership = get_or_create_membership(current_user.id)
    return jsonify({
        'llm_models': COMPREHENSIVE_LLM_MODELS,
        'tool_models': COMPREHENSIVE_TOOL_MODELS,
        'points': membership.points,
    })
```

- [ ] **Step 3: 增加会话列表与详情 API**

```python
@app.route('/api/comprehensive/conversations', methods=['GET'])
@login_required
def api_comprehensive_conversations():
    convs = ComprehensiveConversation.query.filter_by(user_id=current_user.id).order_by(ComprehensiveConversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'model_id': c.model_id,
        'models': json.loads(c.models_json) if c.models_json else [],
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    } for c in convs])

@app.route('/api/comprehensive/conversations/<int:cid>', methods=['GET'])
@login_required
def api_comprehensive_conversation_detail(cid):
    conv = ComprehensiveConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify({
        'id': conv.id,
        'title': conv.title,
        'profile_data': json.loads(conv.profile_data) if conv.profile_data else {},
        'models': json.loads(conv.models_json) if conv.models_json else [],
        'paipan': json.loads(conv.paipan_json) if conv.paipan_json else {},
        'model_id': conv.model_id,
        'messages': json.loads(conv.messages_json) if conv.messages_json else [],
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
    })
```

- [ ] **Step 4: 增加流式问答 API**

第一版实现策略：先使用占位 `build_paipan_context()` 函数调用现有排盘能力；如果某个术数暂时缺少统一函数，先返回该术数的错误上下文，不阻断其他术数。

```python
@app.route('/api/comprehensive/ask/stream', methods=['POST'])
@login_required
def api_comprehensive_ask_stream():
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    history = data.get('history') or []
    tool_models = normalize_tool_models(data.get('tool_models') or [])
    model_id = data.get('llm_model') or 'free'
    is_followup = bool(history)
    cost = calculate_cost(model_id, tool_models, is_followup=is_followup)

    if not question:
        return Response('data: {"error":"请输入问题"}\n\n', mimetype='text/event-stream')
    if not tool_models and not is_followup:
        return Response('data: {"error":"请至少选择一个术数模型"}\n\n', mimetype='text/event-stream')

    membership = get_or_create_membership(current_user.id)
    if membership.points < cost:
        return Response(('data: %s\n\n' % json.dumps({'error': '积分不足', 'current': membership.points, 'required': cost}, ensure_ascii=False)), mimetype='text/event-stream')

    def generate():
        yield 'data: %s\n\n' % json.dumps({'stage': 'profile', 'message': '正在读取命盘档案...'}, ensure_ascii=False)
        profile = resolve_comprehensive_profile(data)
        yield 'data: %s\n\n' % json.dumps({'stage': 'paipan', 'message': '正在生成术数盘面...'}, ensure_ascii=False)
        paipan_context = build_comprehensive_paipan_context(profile, tool_models)
        add_points(current_user.id, 'comprehensive_ai', -cost, '综合 AI 解读' + ('追问' if is_followup else ''))
        messages = build_comprehensive_messages(question, profile, tool_models, paipan_context, history)
        full_text = ''
        yield 'data: %s\n\n' % json.dumps({'stage': 'generating', 'message': '正在生成综合解读...'}, ensure_ascii=False)
        for chunk, error in get_reading_stream(messages):
            if error:
                yield 'data: %s\n\n' % json.dumps({'error': error}, ensure_ascii=False)
                return
            if chunk:
                full_text += chunk
                yield 'data: %s\n\n' % json.dumps({'content': chunk}, ensure_ascii=False)
        conv = save_comprehensive_conversation(data, question, profile, tool_models, paipan_context, model_id, cost, history, full_text)
        left = get_or_create_membership(current_user.id).points
        yield 'data: %s\n\n' % json.dumps({'done': True, 'conversation_id': conv.id, 'points_left': left}, ensure_ascii=False)

    return Response(stream_with_context(generate()), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
```

### Task 5: 排盘上下文适配

**Files:**
- Modify: `backend/app.py`

- [ ] **Step 1: 解析用户选择的档案**

```python
def resolve_comprehensive_profile(data):
    profile_id = data.get('profile_id')
    if profile_id:
        prof = UserProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
        if not prof:
            raise ValueError('命盘档案不存在')
        return {
            'id': prof.id,
            'name': prof.name,
            'gender': prof.gender,
            'cal_type': prof.cal_type,
            'birth_time': prof.birth_time,
            'birth_addr': prof.birth_addr,
            'profile_type': prof.profile_type,
        }
    profile = data.get('profile') or {}
    return {
        'name': profile.get('name') or '未命名',
        'gender': profile.get('gender') or '男',
        'cal_type': profile.get('cal_type') or '公历',
        'birth_time': profile.get('birth_time') or '',
        'birth_addr': profile.get('birth_addr') or '',
        'profile_type': profile.get('profile_type') or 'self',
    }
```

- [ ] **Step 2: 生成综合排盘上下文**

```python
def build_comprehensive_paipan_context(profile, tool_models):
    context = {}
    for tool in tool_models:
        try:
            if tool == 'bazi':
                context['bazi'] = build_bazi_context_from_profile(profile)
            elif tool == 'ziwei':
                context['ziwei'] = build_ziwei_context_from_profile(profile)
            elif tool == 'qimen':
                context['qimen'] = build_qimen_context_from_profile(profile)
            elif tool == 'liuyao':
                context['liuyao'] = {'note': '六爻需要起卦参数，第一版仅在用户提供六爻上下文时使用'}
            elif tool == 'meihua':
                context['meihua'] = {'note': '梅花易数需要起卦参数，第一版仅在用户提供梅花上下文时使用'}
        except Exception as exc:
            context[tool] = {'error': str(exc)}
    return context
```

说明：八字、紫微可以直接由出生年月日时分生成。奇门用于“当下问事”更合理，第一版可用当前时间起局。六爻、梅花没有铜钱/数字/字数等起卦参数时，不应该强行按出生信息生成。

### Task 6: 首页输入框 UI

**Files:**
- Modify: `src/pages/index/index.vue`
- Optional Create: `src/utils/comprehensive-chat.js`

- [ ] **Step 1: 在 Hero 品牌下方添加综合输入区域**

```vue
<view class="home-ai-console">
  <view class="home-ai-main">
    <view class="profile-picker" @tap="openProfilePicker">
      <text class="profile-plus">＋</text>
      <text class="profile-name">{{ selectedProfileName || '选择命盘' }}</text>
    </view>
    <textarea
      class="home-ai-input"
      v-model="comprehensiveQuestion"
      auto-height
      maxlength="800"
      placeholder="输入你的问题，选择术数模型后开始综合解读..."
    />
    <picker :range="llmModelNames" :value="llmModelIdx" @change="onLlmModelChange">
      <view class="llm-picker">{{ selectedLlmModel.name }}</view>
    </picker>
    <view class="home-ai-send" :class="{ disabled: comprehensiveLoading }" @tap="startComprehensiveAsk">发送</view>
  </view>
  <view class="tool-model-row">
    <view
      class="tool-model-chip"
      v-for="tool in toolModels"
      :key="tool.id"
      :class="{ active: selectedToolModels.includes(tool.id) }"
      @tap="toggleToolModel(tool.id)"
    >{{ tool.name }}</view>
  </view>
  <view class="points-hint">预计消耗 {{ estimatedCost }} 积分 · 当前 {{ currentPoints }} 积分</view>
</view>
```

- [ ] **Step 2: 添加状态**

```js
const comprehensiveQuestion = ref('')
const comprehensiveLoading = ref(false)
const profiles = ref([])
const selectedProfile = ref(null)
const llmModels = ref([])
const toolModels = ref([])
const llmModelIdx = ref(0)
const selectedToolModels = ref(['bazi'])
const currentPoints = ref(0)
const comprehensiveMessages = ref([])
const currentComprehensiveConvId = ref(null)
```

- [ ] **Step 3: 添加积分估算**

```js
const selectedLlmModel = computed(() => llmModels.value[llmModelIdx.value] || { id: 'free', name: '免费模型', cost_base: 2, cost_per_tool: 1, followup_cost: 1 })
const llmModelNames = computed(() => llmModels.value.map(m => m.name + ' · ' + m.strength))
const estimatedCost = computed(() => {
  if (comprehensiveMessages.value.length > 0) return selectedLlmModel.value.followup_cost || 1
  return (selectedLlmModel.value.cost_base || 2) + selectedToolModels.value.length * (selectedLlmModel.value.cost_per_tool || 1)
})
const selectedProfileName = computed(() => selectedProfile.value ? selectedProfile.value.name : '')
```

### Task 7: 首页流式生成与提示词状态

**Files:**
- Modify: `src/pages/index/index.vue`

- [ ] **Step 1: 加载 options 和档案**

```js
async function loadComprehensiveOptions() {
  const res = await uni.request({ url: '/api/comprehensive/options' })
  const data = res.data || {}
  llmModels.value = data.llm_models || []
  toolModels.value = data.tool_models || []
  currentPoints.value = data.points || 0
}

async function loadProfiles() {
  const res = await uni.request({ url: '/api/profiles' })
  profiles.value = (res.data && res.data.profiles) || []
}
```

- [ ] **Step 2: 实现生成流程**

```js
async function startComprehensiveAsk() {
  if (comprehensiveLoading.value) return
  const question = comprehensiveQuestion.value.trim()
  if (!question) return uni.showToast({ title: '请输入问题', icon: 'none' })
  if (!selectedProfile.value) return uni.showToast({ title: '请先选择命盘', icon: 'none' })
  if (!selectedToolModels.value.length) return uni.showToast({ title: '请至少选择一个术数模型', icon: 'none' })
  if (currentPoints.value < estimatedCost.value) return uni.showToast({ title: '积分不足', icon: 'none' })

  comprehensiveLoading.value = true
  comprehensiveMessages.value.push({ role: 'user', content: question })
  comprehensiveMessages.value.push({ role: 'assistant', content: '', stage: '正在读取命盘档案...' })
  const aiMsg = comprehensiveMessages.value[comprehensiveMessages.value.length - 1]

  const resp = await fetch('/api/comprehensive/ask/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      profile_id: selectedProfile.value.id,
      llm_model: selectedLlmModel.value.id,
      tool_models: selectedToolModels.value,
      history: comprehensiveMessages.value.filter(m => !m.stage).slice(0, -1),
      conversation_id: currentComprehensiveConvId.value,
    })
  })
  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''
    parts.forEach(part => {
      const line = part.split('\n').find(l => l.startsWith('data: '))
      if (!line) return
      const data = JSON.parse(line.slice(6))
      if (data.message) aiMsg.stage = data.message
      if (data.content) {
        aiMsg.stage = ''
        aiMsg.content += data.content
      }
      if (data.conversation_id) currentComprehensiveConvId.value = data.conversation_id
      if (typeof data.points_left === 'number') currentPoints.value = data.points_left
    })
  }
  comprehensiveQuestion.value = ''
  comprehensiveLoading.value = false
}
```

### Task 8: 档案选择器

**Files:**
- Modify: `src/pages/index/index.vue`

- [ ] **Step 1: 分类展示档案**

分类规则：

```js
const profileGroups = computed(() => ({
  全部: profiles.value,
  客户: profiles.value.filter(p => p.profile_type === 'client'),
  用户: profiles.value.filter(p => p.profile_type !== 'client'),
}))
```

- [ ] **Step 2: 点击左侧加号弹出选择面板**

实现一个底部弹层：

```vue
<view class="profile-sheet" v-if="profileSheetOpen">
  <view class="profile-sheet-mask" @tap="profileSheetOpen = false"></view>
  <view class="profile-sheet-panel">
    <view class="profile-tabs">
      <view v-for="tab in ['全部','客户','用户']" :key="tab" :class="{ active: profileTab === tab }" @tap="profileTab = tab">{{ tab }}</view>
    </view>
    <view class="profile-option" v-for="p in profileGroups[profileTab]" :key="p.id" @tap="selectProfile(p)">
      <text>{{ p.name }}</text>
      <text>{{ p.gender }} · {{ formatBirthTime(p.birth_time) }}</text>
    </view>
  </view>
</view>
```

### Task 9: 对话历史增加“综合”

**Files:**
- Modify: `src/package-user/history/index.vue`

- [ ] **Step 1: 标签增加综合**

现有“全部”后面增加：

```js
const historyTabs = ['全部', '综合', '八字', '奇门', '塔罗', '六爻', '梅花', '紫微']
```

- [ ] **Step 2: 加载综合会话**

```js
async function loadComprehensiveConversations() {
  const res = await uni.request({ url: '/api/comprehensive/conversations' })
  return (res.data || []).map(item => ({
    ...item,
    history_type: '综合',
    route: '/pages/index/index?comprehensive_id=' + item.id,
  }))
}
```

- [ ] **Step 3: 点击继续追问**

跳转：

```js
uni.navigateTo({ url: '/pages/index/index?comprehensive_id=' + item.id })
```

首页 `onLoad` 读取 `comprehensive_id`，调用 `/api/comprehensive/conversations/<id>` 恢复消息、档案、模型和术数选择。

### Task 10: 验证

**Files:**
- No code changes

- [ ] **Step 1: 后端语法检查**

Run:

```bash
python -m py_compile backend/app.py backend/models.py backend/comprehensive_ai.py
```

Expected:

```text
无输出或无错误。
```

- [ ] **Step 2: 前端构建**

Run:

```bash
npm run build:h5
```

Expected:

```text
DONE Build complete.
```

- [ ] **Step 3: 浏览器验证**

访问：

```text
http://localhost:3001/#/pages/index/index
```

验证：

```text
1. 首页输入框显示正常，移动端不溢出。
2. 左侧档案选择可切换“全部/客户/用户”。
3. 选择免费模型时显示积分消耗。
4. 可复选八字、紫微等术数。
5. 发送后依次显示“正在读取命盘档案...”“正在生成术数盘面...”“正在生成综合解读...”。
6. 回答完成后积分变化。
7. 对话历史出现“综合”标签。
8. 点击综合历史可恢复对话并继续追问。
```

## 分阶段上线建议

### 第一阶段：最小可用

- 首页输入框
- 档案选择
- 免费模型
- 八字 + 紫微综合
- 综合历史 + 追问

### 第二阶段：扩展术数

- 奇门按当前时间/用户问题起局
- 六爻支持从用户输入或已有六爻记录带入卦象
- 梅花支持数字/字数/时间起卦入口

### 第三阶段：模型计费

- 增加强模型选项
- 按模型强弱配置不同积分消耗
- 增加积分不足时的充值引导

## 风险与处理

- 风险：首页本地代码与线上首页不一致。
  - 处理：执行前先确认基线，不覆盖未提交改动。
- 风险：六爻、梅花不能只靠出生年月日生成有效盘。
  - 处理：第一版不强行生成，必须有起卦参数或已有记录。
- 风险：综合问答消耗 token 较大。
  - 处理：排盘上下文只传关键结构，不传完整 HTML。
- 风险：前端只提示积分但后端没校验会被绕过。
  - 处理：后端统一计算和扣积分，前端只做展示。
