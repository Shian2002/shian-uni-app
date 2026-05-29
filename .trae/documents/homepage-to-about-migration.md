# 首页板块移植 & 首页瘦身计划

## 概述
将首页的"核心特色"、"快速场景"、"新手常见问题"三个板块移植到关于我们页面，同时删除首页的"信任背书"板块，最后优化首页的间距。

## 当前状态分析

### 首页 (index/index.vue) 当前板块顺序
1. **Hero** (含品牌logo、产品卡片网格) — 第27-134行
2. **核心特色** — 第136-150行，CSS第600-606行，数据第304-311行
3. **快速场景** — 第152-167行，CSS第608-613行，数据第314-321行，函数第327-335行
4. **信任背书** — 第169-200行，CSS第615-632行，数据第338-342行 + 第344-380行
5. **新手常见问题(FAQ)** — 第202-219行，CSS第634-647行，数据第397-401行，函数第388-396行
6. **页脚** — 第221-254行

### 关于我们页面 (about/index.vue) 当前板块顺序
1. **Hero** — 第10-14行
2. **信任背书** — 第16-71行（含排盘内核权威说明 + 真实案例卡片）
3. **新手入门** — 第73-120行

## 修改计划

### 一、关于我们页面 (about/index.vue) — 新增3个板块

移植后的板块顺序：**Hero → 信任背书 → 核心特色 → 快速场景 → 新手常见问题 → 新手入门**

#### 1.1 HTML模板新增（在信任背书 `</view>` 和新手入门之间插入）

**核心特色 section** — 从首页第137-150行复制，保持 `feature-grid` 3列布局

**快速场景 section** — 从首页第153-167行复制，外层包裹 `.section-alt`

**新手常见问题(FAQ) section** — 从首页第203-219行复制，保持折叠面板交互

#### 1.2 CSS新增
从首页复制以下CSS到关于我们页面：
- `.feature-scroll-wrap`, `.feature-grid`, `.feature-card`, `.feature-icon`, `.feature-card-title`, `.feature-card-desc`（第600-606行）
- `.scenario-scroll-wrap`, `.scenario-grid`, `.scenario-card`, `.scenario-emoji`, `.scenario-card-title`（第608-613行）
- `.faq-panel`, `.faq-panel-header`, `.faq-panel-title`, `.faq-panel-arrow`, `.faq-panel-body`, `.faq-item`, `.faq-q`, `.faq-a`（第634-647行）

#### 1.3 数据和函数新增
- `features` 数组（6项）— 静态数据
- `scenarios` 数组（6项）— 静态数据
- `faqs` 数组（3项）— 响应式数据
- `goScenario(key)` 函数 — 跳转到奇门页面
- `toggleFaqPanel()` 函数 — FAQ面板折叠
- `toggleFaq(e)` 函数 — 单个FAQ折叠

#### 1.4 响应式适配
在关于我们页面的 `@media (max-width: 768px)` 中新增：
- `.feature-grid { grid-template-columns: repeat(2, 1fr); }`
- `.scenario-grid { grid-template-columns: repeat(3, 1fr); }`

### 二、首页 (index/index.vue) — 删除板块 + 间距优化

#### 2.1 删除HTML（4个section全部删除）
- 核心特色：第136-150行
- 快速场景：第152-167行
- 信任背书：第169-200行
- FAQ：第202-219行

删除后首页只剩：**Hero → 页脚**

#### 2.2 删除对应CSS
- 核心特色CSS：第600-606行
- 场景CSS：第608-613行
- 信任背书CSS：第615-632行
- FAQ CSS：第634-647行

#### 2.3 删除对应JS数据和函数
- `features` 数组（第304-311行）
- `scenarios` 数组（第314-321行）
- `goScenario()` 函数（第327-335行）
- `authorities` 数组（第338-342行）
- `caseFilter`, `filteredCases`, `switchCaseFilter()`（第344-380行）
- `toggleFaqPanel()`, `toggleFaq()`（第382-396行）
- `faqs` 数组（第397-401行）

#### 2.4 间距优化
- `.hero-home` 的 `padding` 从 `48px 32px 60px` 调整为 `48px 32px 32px`（减少底部内边距）
- `.site-footer` 的 `padding` 从 `48px 32px 24px` 调整为 `24px 32px 24px`（减少顶部内边距）
- `.scroll-hint` 位置相应调整

### 三、验证步骤
1. `npm run build:h5` 构建成功
2. 首页：只显示 Hero + 页脚，间距紧凑
3. 关于我们：Hero → 信任背书 → 核心特色 → 快速场景 → FAQ → 新手入门，排版正常
4. 所有交互正常：FAQ折叠展开、场景卡片点击跳转、案例滑动
