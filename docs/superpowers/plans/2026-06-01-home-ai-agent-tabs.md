# 首页 AI 解读区 Agent 状态与术数切换 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 首页综合 AI 解读区从长页面堆叠改成“时安 agent 状态 + 术数切换 + 当前术数内容 + 最终综合结论”的紧凑交互，并修正 agent logo 在生成完成后的状态。

**Architecture:** 继续在 `src/pages/index/index.vue` 的首页综合 AI 渲染层改造，不改后端数据结构和旧历史数据库。旧历史、新生成流式消息都通过同一套 `visibleArtifactList`、`activeArtifactKey`、`msg.content` 渲染，因此所有改动必须走前端 normalize/展示层兼容。

**Tech Stack:** UniApp Vue 3、现有 Flask SSE 综合 AI 接口、pytest 源码断言测试、`npm run build:h5`。

---

## Files

- Modify: `src/pages/index/index.vue`
  - 删除助手消息顶部重复的“时安 agent / 综合解答”静态头。
  - 保留并改造生成中状态块：logo + `时安 agent` + 当前阶段文案。
  - 生成中 logo 旋转；生成完成后 logo 停止，显示正常 logo。
  - 把术数卡片从全部纵向展开改成切换式导航，只展示当前术数。
  - 增加最终“综合结论”入口/区域。
- Modify: `tests/comprehensive_render_perf_test.py`
  - 覆盖 agent 头不重复、生成中旋转、完成后停止、术数切换、旧历史兼容。

---

### Task 1: 修正 Agent 头部重复与 logo 状态

**Files:**
- Modify: `src/pages/index/index.vue`
- Test: `tests/comprehensive_render_perf_test.py`

- [ ] **Step 1: 写失败测试**

在 `tests/comprehensive_render_perf_test.py` 增加：

```python
def test_home_ai_agent_header_only_lives_in_status_block():
    source = _source()

    assert "home-ai-agent-head" in source
    assert "home-ai-agent-head static" not in source
    assert "home-ai-agent-logo spinning" in source
    assert "home-ai-agent-logo idle" in source
    assert "msg.stage || msg.content || visibleArtifactList(msg).length" in source
    assert "综合解答</text>" not in source
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m pytest -q tests/comprehensive_render_perf_test.py::test_home_ai_agent_header_only_lives_in_status_block
```

Expected: FAIL，因为当前模板里还有静态“综合解答”。

- [ ] **Step 3: 修改助手消息模板**

在 `src/pages/index/index.vue` 的 `home-ai-message` 内：

```vue
<text class="home-ai-role" v-if="msg.role === 'user'">你</text>
<view
  class="home-ai-agent-head"
  v-else-if="msg.stage || msg.content || visibleArtifactList(msg).length"
>
  <img
    class="home-ai-agent-logo"
    :class="msg.stage ? 'spinning' : 'idle'"
    src="/static/images/logo.webp?v=2"
    alt="时安解忧屋"
  />
  <view class="home-ai-agent-texts">
    <text class="home-ai-agent-name">时安 agent</text>
    <text class="home-ai-agent-sub">{{ msg.stage || '已完成解读' }}</text>
  </view>
</view>
```

删除原来的静态：

```vue
<text class="home-ai-agent-sub">综合解答</text>
```

- [ ] **Step 4: 修改 logo CSS**

在 `src/pages/index/index.vue` 样式区调整：

```css
.home-ai-agent-logo { width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0; object-fit: cover; box-shadow: 0 0 0 1px rgba(178,149,93,.18), 0 6px 16px rgba(0,0,0,.12); }
.home-ai-agent-logo.spinning { animation: stage-spin 3.2s linear infinite; }
.home-ai-agent-logo.idle { animation: none; }
.home-ai-stage-wrap { display: none; }
```

这里保留一个统一 agent 头，避免同时出现两个 logo。

- [ ] **Step 5: 验证并提交**

Run:

```bash
python3 -m pytest -q tests/comprehensive_render_perf_test.py::test_home_ai_agent_header_only_lives_in_status_block
```

Expected: PASS.

Commit:

```bash
git add src/pages/index/index.vue tests/comprehensive_render_perf_test.py
git commit -m "fix: simplify home ai agent status header"
```

---

### Task 2: 增加术数切换状态，只显示当前内容

**Files:**
- Modify: `src/pages/index/index.vue`
- Test: `tests/comprehensive_render_perf_test.py`

- [ ] **Step 1: 写失败测试**

增加：

```python
def test_home_ai_artifacts_use_switcher_not_full_stack():
    source = _source()

    assert "activeArtifactKeyByMessage" in source
    assert "setActiveArtifact(idx, artifact.key)" in source
    assert "currentArtifactForMessage(msg, idx)" in source
    assert "home-artifact-switcher" in source
    assert "v-for=\"artifact in visibleArtifactList(msg)\"" in source
    assert "v-if=\"currentArtifactForMessage(msg, idx)\"" in source
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m pytest -q tests/comprehensive_render_perf_test.py::test_home_ai_artifacts_use_switcher_not_full_stack
```

Expected: FAIL.

- [ ] **Step 3: 增加响应式状态和工具函数**

在 `<script setup>` 里增加：

```js
const activeArtifactKeyByMessage = reactive({})

function ensureActiveArtifact(messageIndex, artifacts) {
  const list = artifacts || []
  const current = activeArtifactKeyByMessage[messageIndex]
  if (!list.length) return ''
  if (current && list.some(function(item) { return item.key === current })) return current
  activeArtifactKeyByMessage[messageIndex] = list[0].key
  return list[0].key
}

function setActiveArtifact(messageIndex, key) {
  activeArtifactKeyByMessage[messageIndex] = key
}

function currentArtifactForMessage(msg, messageIndex) {
  const list = visibleArtifactList(msg)
  const key = ensureActiveArtifact(messageIndex, list)
  return list.find(function(item) { return item.key === key }) || null
}
```

- [ ] **Step 4: 改造模板**

把现有 `.home-tool-cards` 内多个卡片堆叠替换成：

```vue
<view class="home-tool-cards" v-if="visibleArtifactList(msg).length">
  <view class="home-artifact-switcher">
    <view
      class="home-artifact-tab"
      v-for="artifact in visibleArtifactList(msg)"
      :key="artifact.key"
      :class="{ active: currentArtifactForMessage(msg, idx)?.key === artifact.key }"
      @tap="setActiveArtifact(idx, artifact.key)"
    >
      <text class="home-artifact-tab-title">{{ artifact.title }}</text>
      <text class="home-artifact-tab-sub">{{ artifactSummary(artifact) }}</text>
    </view>
    <view
      class="home-artifact-tab conclusion"
      :class="{ active: activeArtifactKeyByMessage[idx] === '__summary__' }"
      v-if="msg.content"
      @tap="setActiveArtifact(idx, '__summary__')"
    >
      <text class="home-artifact-tab-title">综合结论</text>
      <text class="home-artifact-tab-sub">最终合参建议</text>
    </view>
  </view>

  <view class="home-tool-card" v-if="currentArtifactForMessage(msg, idx) && activeArtifactKeyByMessage[idx] !== '__summary__'">
    <view class="home-tool-card-head">
      <view>
        <text class="home-tool-card-title">{{ currentArtifactForMessage(msg, idx).title }}</text>
        <text class="home-tool-card-sub">{{ artifactSummary(currentArtifactForMessage(msg, idx)) }}</text>
      </view>
    </view>
    <view class="home-tool-card-body">
      <view class="home-artifact-render" v-html="renderArtifactHtml(currentArtifactForMessage(msg, idx))"></view>
      <view class="home-artifact-analysis" v-if="currentArtifactForMessage(msg, idx).analysis">
        <view class="home-artifact-analysis-head">
          <img class="home-ai-agent-logo small idle" src="/static/images/logo.webp?v=2" alt="时安解忧屋" />
          <view class="home-ai-agent-texts">
            <text class="home-ai-agent-name">时安 agent</text>
            <text class="home-artifact-analysis-title">{{ currentArtifactForMessage(msg, idx).title }}解析</text>
          </view>
        </view>
        <text>{{ currentArtifactForMessage(msg, idx).analysis }}</text>
      </view>
    </view>
  </view>
</view>
```

- [ ] **Step 5: 综合结论只在结论页显示**

把原来的：

```vue
<text class="home-ai-content" v-if="msg.content">{{ msg.content }}</text>
```

改成：

```vue
<view class="home-ai-summary-panel" v-if="msg.content && (!visibleArtifactList(msg).length || activeArtifactKeyByMessage[idx] === '__summary__')">
  <view class="home-artifact-analysis-head">
    <img class="home-ai-agent-logo small idle" src="/static/images/logo.webp?v=2" alt="时安解忧屋" />
    <view class="home-ai-agent-texts">
      <text class="home-ai-agent-name">时安 agent</text>
      <text class="home-artifact-analysis-title">综合结论</text>
    </view>
  </view>
  <text class="home-ai-content">{{ msg.content }}</text>
</view>
```

- [ ] **Step 6: 验证并提交**

Run:

```bash
python3 -m pytest -q tests/comprehensive_render_perf_test.py::test_home_ai_artifacts_use_switcher_not_full_stack
```

Expected: PASS.

Commit:

```bash
git add src/pages/index/index.vue tests/comprehensive_render_perf_test.py
git commit -m "feat: add home artifact switcher"
```

---

### Task 3: 调整切换式布局样式

**Files:**
- Modify: `src/pages/index/index.vue`
- Test: `tests/comprehensive_render_perf_test.py`

- [ ] **Step 1: 写失败测试**

增加：

```python
def test_home_ai_switcher_layout_is_compact():
    source = _source()

    assert ".home-artifact-switcher" in source
    assert "overflow-x: auto" in source
    assert ".home-artifact-tab.active" in source
    assert ".home-ai-summary-panel" in source
    assert ".home-tool-card.collapsed" not in source
```

- [ ] **Step 2: 添加样式**

在样式区增加：

```css
.home-artifact-switcher { display: flex; gap: 8px; overflow-x: auto; padding: 2px 0 10px; margin-bottom: 10px; scrollbar-width: none; }
.home-artifact-switcher::-webkit-scrollbar { display: none; }
.home-artifact-tab { flex: 0 0 auto; min-width: 138px; max-width: 190px; padding: 9px 11px; border-radius: 12px; border: 1px solid rgba(178,149,93,.14); background: rgba(255,255,255,.04); cursor: pointer; box-sizing: border-box; }
.home-artifact-tab.active { border-color: rgba(178,149,93,.48); background: rgba(178,149,93,.12); box-shadow: inset 0 1px 0 rgba(255,255,255,.08); }
.home-artifact-tab.conclusion { border-color: rgba(120,150,110,.24); }
.home-artifact-tab-title { display: block; color: var(--text-1); font-size: .76rem; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-artifact-tab-sub { display: block; margin-top: 3px; color: var(--text-3); font-size: .62rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-ai-summary-panel { margin-top: 10px; padding: 14px 16px; border-radius: 14px; border: 1px solid rgba(178,149,93,.16); background: rgba(255,255,255,.045); }
.home-tool-card-head { cursor: default; }
.home-tool-card-toggle { display: none; }
```

- [ ] **Step 3: 移动端样式**

在 `@media (max-width: 480px)` 内增加：

```css
.home-artifact-tab { min-width: 116px; max-width: 152px; padding: 8px 9px; }
.home-artifact-tab-title { font-size: .7rem; }
.home-artifact-tab-sub { font-size: .56rem; }
.home-ai-summary-panel { padding: 12px; }
```

- [ ] **Step 4: 验证并提交**

Run:

```bash
python3 -m pytest -q tests/comprehensive_render_perf_test.py::test_home_ai_switcher_layout_is_compact
```

Expected: PASS.

Commit:

```bash
git add src/pages/index/index.vue tests/comprehensive_render_perf_test.py
git commit -m "style: compact home ai artifact switcher"
```

---

### Task 4: 旧历史与生成中状态兼容

**Files:**
- Modify: `src/pages/index/index.vue`
- Test: `tests/comprehensive_render_perf_test.py`

- [ ] **Step 1: 写兼容测试**

增加：

```python
def test_home_ai_switcher_supports_old_history_and_streaming():
    source = _source()

    assert "normalizeHomeArtifactForDisplay" in source
    assert "ensureActiveArtifact(messageIndex, artifacts)" in source
    assert "if (!list.length) return ''" in source
    assert "msg.stage ? 'spinning' : 'idle'" in source
    assert "activeArtifactKeyByMessage[idx] === '__summary__'" in source
```

- [ ] **Step 2: 确保历史恢复后默认选第一个术数**

在 `loadComprehensiveHistoryDetail` 恢复消息后，补充：

```js
comprehensiveMessages.value.forEach(function(message, index) {
  ensureActiveArtifact(index, visibleArtifactList(message))
})
```

- [ ] **Step 3: 流式追加 artifact 时保持当前选择**

在 `updateComprehensiveAssistant` 或 artifact flush 后补充：

```js
ensureActiveArtifact(aiIndex, visibleArtifactList(comprehensiveMessages.value[aiIndex]))
```

如果用户已经点过某个术数，`ensureActiveArtifact` 不覆盖现有选择。

- [ ] **Step 4: 验证并提交**

Run:

```bash
python3 -m pytest -q tests/comprehensive_render_perf_test.py::test_home_ai_switcher_supports_old_history_and_streaming
```

Expected: PASS.

Commit:

```bash
git add src/pages/index/index.vue tests/comprehensive_render_perf_test.py
git commit -m "fix: keep home artifact switcher compatible with history"
```

---

### Task 5: 全量验证、部署、线上验活

**Files:**
- No code changes unless verification finds a bug.

- [ ] **Step 1: 跑全量测试**

Run:

```bash
python3 -m pytest -q
```

Expected: `48 passed` or higher.

- [ ] **Step 2: 构建 H5**

Run:

```bash
npm run build:h5
```

Expected: `DONE Build complete.`

- [ ] **Step 3: 推送 GitHub**

Run:

```bash
git status --short
git log --oneline -5
git push origin master
```

Expected: 本地提交全部推到 `origin/master`。

- [ ] **Step 4: 部署服务器**

Run:

```bash
bash deploy-to-server.sh
```

Expected: `后端 200 OK`，访问 `http://119.29.128.18`。

- [ ] **Step 5: 线上资源核验**

Run:

```bash
curl -fsS http://119.29.128.18/api/health
curl -fsS http://119.29.128.18/ | rg -o "assets/[^\"' ]+\\.(css|js)" | sort -u
```

再检查线上 CSS/JS 包包含：

```text
home-artifact-switcher
home-ai-agent-logo
home-ai-summary-panel
```

并不包含：

```text
综合解答</text>
ly-tag-gutter
```

- [ ] **Step 6: 浏览器验活**

在 `http://119.29.128.18/#/` 验证：

- 新生成时：只显示一个 `时安 agent` 头。
- “正在结合大运流年流月 / 正在解读八字 / 正在解读奇门”前面有旋转 logo。
- 生成完成后：logo 停止旋转，仍显示正常 logo。
- 点击“奇门遁甲盘”只显示奇门内容。
- 点击“八字基本排盘”切换到八字内容。
- 点击“综合结论”显示最终合参总结。
- 打开旧历史记录也使用同一套切换式展示。

