<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="admin-wrap">
      <section class="admin-head">
        <view>
          <view class="section-tag">后台管理</view>
          <view class="admin-title">运营控制台</view>
          <view class="admin-desc">用户 · 社区 · 举报 · 充值 · 审计</view>
        </view>
        <view class="admin-head-actions">
          <button class="admin-icon-btn" @click="refreshAll" title="刷新">↻</button>
          <button class="admin-primary" @click="activeTab = 'recharge'">处理充值</button>
        </view>
      </section>

      <section class="auth-state" v-if="authLoading">正在校验管理员权限...</section>
      <section class="auth-state denied" v-else-if="!isAdmin">
        <view class="denied-title">需要管理员权限</view>
        <view class="denied-copy">请使用管理员账号登录后访问后台。</view>
        <button class="admin-primary" @click="openLogin">登录</button>
      </section>

      <template v-else>
        <section class="metric-grid">
          <view class="metric-tile">
            <text class="metric-label">用户</text>
            <text class="metric-value">{{ summary.users }}</text>
          </view>
          <view class="metric-tile">
            <text class="metric-label">帖子</text>
            <text class="metric-value">{{ summary.posts }}</text>
          </view>
          <view class="metric-tile warn">
            <text class="metric-label">待审举报</text>
            <text class="metric-value">{{ summary.pending_reports }}</text>
          </view>
          <view class="metric-tile">
            <text class="metric-label">待确认充值</text>
            <text class="metric-value">{{ summary.pending_recharge_orders }}</text>
          </view>
        </section>

        <section class="admin-tabs">
          <button :class="{ active: activeTab === 'reports' }" @click="switchTab('reports')">举报审核</button>
          <button :class="{ active: activeTab === 'posts' }" @click="switchTab('posts')">帖子管理</button>
          <button :class="{ active: activeTab === 'users' }" @click="switchTab('users')">用户积分</button>
          <button :class="{ active: activeTab === 'recharge' }" @click="switchTab('recharge')">充值订单</button>
          <button :class="{ active: activeTab === 'audit' }" @click="switchTab('audit')">操作审计</button>
        </section>

        <section class="admin-panel" v-if="activeTab === 'reports'">
          <view class="panel-head">
            <view>
              <view class="panel-title">举报审核</view>
              <view class="panel-sub">处理用户提交的帖子或评论举报</view>
            </view>
            <select v-model="reportStatus" @change="loadReports" class="admin-select">
              <option value="pending">待处理</option>
              <option value="resolved">已处理</option>
              <option value="dismissed">已驳回</option>
            </select>
          </view>
          <view class="table-list">
            <view class="table-row table-head">
              <text>举报人</text><text>目标</text><text>原因</text><text>时间</text><text>操作</text>
            </view>
            <view class="table-row" v-for="r in reports" :key="r.id">
              <text>{{ r.reporterName }}</text>
              <text>{{ r.targetType }}#{{ r.targetId }}</text>
              <text>{{ reasonLabel(r.reason) }}</text>
              <text>{{ formatTime(r.createdAt) }}</text>
              <view class="row-actions">
                <button class="mini-btn danger" @click="resolveReport(r.id, 'resolve')" v-if="r.status === 'pending'">处理</button>
                <button class="mini-btn" @click="resolveReport(r.id, 'dismiss')" v-if="r.status === 'pending'">驳回</button>
                <text v-else>{{ statusLabel(r.status) }}</text>
              </view>
            </view>
            <view class="empty-line" v-if="!reports.length">暂无举报</view>
          </view>
        </section>

        <section class="admin-panel" v-if="activeTab === 'posts'">
          <view class="panel-head">
            <view>
              <view class="panel-title">帖子管理</view>
              <view class="panel-sub">包含隐藏帖，可直接置顶、加精、隐藏或恢复</view>
            </view>
            <view class="filter-line">
              <input class="admin-input" v-model="postQuery" placeholder="搜索标题/内容/标签" @confirm="loadPosts" />
              <select v-model="postStatus" @change="loadPosts" class="admin-select">
                <option value="all">全部</option>
                <option value="visible">可见</option>
                <option value="hidden">隐藏</option>
              </select>
              <button class="mini-btn" @click="loadPosts">查询</button>
            </view>
          </view>
          <view class="table-list">
            <view class="table-row post-row table-head">
              <text>ID</text><text>标题</text><text>作者</text><text>状态</text><text>互动</text><text>操作</text>
            </view>
            <view class="table-row post-row" v-for="p in posts" :key="p.id">
              <text>#{{ p.id }}</text>
              <text class="title-cell">{{ p.title }}</text>
              <text>{{ p.username }}</text>
              <text>{{ p.isHidden ? '隐藏' : '可见' }} · {{ p.isPinned ? '置顶' : '普通' }} · {{ p.isFeatured ? '精华' : '未加精' }}</text>
              <text>{{ p.likesCount }} 赞 / {{ p.commentsCount }} 评</text>
              <view class="row-actions">
                <button class="mini-btn" @click="togglePostPin(p)">{{ p.isPinned ? '取消置顶' : '置顶' }}</button>
                <button class="mini-btn" @click="togglePostFeature(p)">{{ p.isFeatured ? '取消加精' : '加精' }}</button>
                <button class="mini-btn danger" @click="togglePostHidden(p)">{{ p.isHidden ? '恢复' : '隐藏' }}</button>
              </view>
            </view>
            <view class="empty-line" v-if="!posts.length">暂无帖子</view>
          </view>
        </section>

        <section class="admin-panel" v-if="activeTab === 'users'">
          <view class="panel-head">
            <view>
              <view class="panel-title">用户积分</view>
              <view class="panel-sub">搜索用户并手动加积分</view>
            </view>
            <view class="filter-line">
              <input class="admin-input" v-model="userQuery" placeholder="用户名/邮箱/手机号" @confirm="loadUsers" />
              <button class="mini-btn" @click="loadUsers">查询</button>
            </view>
          </view>
          <view class="manual-box">
            <input class="admin-input compact" v-model="manualUserId" placeholder="用户ID" />
            <input class="admin-input compact" v-model="manualPoints" placeholder="加积分" />
            <input class="admin-input" v-model="manualRemark" placeholder="备注" />
            <button class="admin-primary" @click="addManualPoints">确认加分</button>
          </view>
          <view class="table-list">
            <view class="table-row user-row table-head">
              <text>ID</text><text>用户名</text><text>积分</text><text>等级</text><text>权限</text><text>注册时间</text>
            </view>
            <view class="table-row user-row" v-for="u in users" :key="u.id">
              <text>#{{ u.id }}</text>
              <text>{{ u.username }}</text>
              <text>{{ u.points }}</text>
              <text>{{ u.level }}</text>
              <text>{{ u.is_admin ? '管理员' : '用户' }}</text>
              <text>{{ formatTime(u.created_at) }}</text>
            </view>
            <view class="empty-line" v-if="!users.length">暂无用户</view>
          </view>
        </section>

        <section class="admin-panel" v-if="activeTab === 'recharge'">
          <view class="panel-head">
            <view>
              <view class="panel-title">充值订单</view>
              <view class="panel-sub">确认手动转账订单到账</view>
            </view>
            <select v-model="rechargeStatus" @change="loadRechargeOrders" class="admin-select">
              <option value="pending">待确认</option>
              <option value="paid">已到账</option>
              <option value="all">全部</option>
            </select>
          </view>
          <view class="manual-box">
            <input class="admin-input compact" v-model="manualOrderId" placeholder="订单ID" />
            <button class="admin-primary" @click="confirmOrderByInput">确认订单到账</button>
          </view>
          <view class="table-list">
            <view class="table-row order-row table-head">
              <text>订单</text><text>用户</text><text>套餐</text><text>金额</text><text>状态</text><text>操作</text>
            </view>
            <view class="table-row order-row" v-for="o in rechargeOrders" :key="o.id">
              <text>#{{ o.id }}</text>
              <text>{{ o.username }} (#{{ o.user_id }})</text>
              <text>{{ o.package_name }} · {{ o.points_amount }} 分</text>
              <text>¥{{ o.price }}</text>
              <text>{{ orderStatusLabel(o.status) }}</text>
              <view class="row-actions">
                <button class="mini-btn danger" v-if="o.status === 'pending'" @click="confirmOrder(o.id)">确认到账</button>
              </view>
            </view>
            <view class="empty-line" v-if="!rechargeOrders.length">暂无订单</view>
          </view>
        </section>

        <section class="admin-panel" v-if="activeTab === 'audit'">
          <view class="panel-head">
            <view>
              <view class="panel-title">操作审计</view>
              <view class="panel-sub">记录管理员处理举报、管理帖子、加积分和确认充值的动作</view>
            </view>
            <button class="mini-btn" @click="loadAuditLogs">刷新</button>
          </view>
          <view class="table-list">
            <view class="table-row audit-row table-head">
              <text>时间</text><text>管理员</text><text>动作</text><text>目标</text><text>详情</text><text>IP</text>
            </view>
            <view class="table-row audit-row" v-for="log in auditLogs" :key="log.id">
              <text>{{ formatTime(log.created_at) }}</text>
              <text>{{ log.admin_name }} (#{{ log.admin_id }})</text>
              <text>{{ auditActionLabel(log.action) }}</text>
              <text>{{ log.target_type }}#{{ log.target_id || '-' }}</text>
              <text class="title-cell">{{ auditDetail(log.detail) }}</text>
              <text>{{ log.ip_address || '--' }}</text>
            </view>
            <view class="empty-line" v-if="!auditLogs.length">暂无审计记录</view>
          </view>
        </section>
      </template>
    </view>
  </view>
</template>

<script setup>
import { inject, onMounted, ref } from 'vue'
import TopNav from '../../components/TopNav.vue'

const theme = inject('theme', ref('light'))
const toggleTheme = inject('toggleTheme', function() {})
const isLoggedIn = ref(false)
const isAdmin = ref(false)
const authLoading = ref(true)
const activeTab = ref('reports')
const summary = ref({ users: 0, posts: 0, hidden_posts: 0, pending_reports: 0, pending_recharge_orders: 0 })

const reports = ref([])
const reportStatus = ref('pending')
const posts = ref([])
const postStatus = ref('all')
const postQuery = ref('')
const users = ref([])
const userQuery = ref('')
const rechargeOrders = ref([])
const rechargeStatus = ref('pending')
const auditLogs = ref([])

const manualUserId = ref('')
const manualPoints = ref('')
const manualRemark = ref('后台手动加积分')
const manualOrderId = ref('')

const reportReasons = {
  spam: '广告垃圾',
  abuse: '辱骂攻击',
  misinformation: '虚假误导',
  illegal: '违法违规',
  other: '其他'
}

function request(url, options) {
  return uni.request(Object.assign({ url: url, method: 'GET' }, options || {})).then(function(res) {
    return res.data || {}
  })
}

function formatTime(value) {
  if (!value) return '--'
  return String(value).replace('T', ' ').slice(0, 16)
}

function reasonLabel(reason) {
  return reportReasons[reason] || reason || '--'
}

function statusLabel(status) {
  return { pending: '待处理', resolved: '已处理', dismissed: '已驳回' }[status] || status
}

function orderStatusLabel(status) {
  return { pending: '待确认', paid: '已到账', cancelled: '已取消' }[status] || status
}

function auditActionLabel(action) {
  return {
    report_resolve: '处理举报',
    report_dismiss: '驳回举报',
    post_pin: '置顶变更',
    post_feature: '加精变更',
    post_hide: '隐藏变更',
    points_add: '手动加分',
    recharge_confirm: '确认充值'
  }[action] || action
}

function auditDetail(detail) {
  if (!detail) return '--'
  const parts = []
  if (detail.title) parts.push(detail.title)
  if (detail.reason) parts.push(reasonLabel(detail.reason))
  if (detail.points) parts.push('余额 ' + detail.points)
  if (detail.added) parts.push('+' + detail.added + ' 分')
  if (detail.remark) parts.push(detail.remark)
  if (typeof detail.hidden === 'boolean') parts.push(detail.hidden ? '隐藏' : '恢复')
  if (typeof detail.pinned === 'boolean') parts.push(detail.pinned ? '置顶' : '取消置顶')
  if (typeof detail.featured === 'boolean') parts.push(detail.featured ? '加精' : '取消加精')
  return parts.join(' · ') || JSON.stringify(detail)
}

function toast(title, icon) {
  uni.showToast({ title: title, icon: icon || 'none' })
}

function openLogin() {
  if (window._openLoginModal) window._openLoginModal()
}

async function checkAdmin() {
  authLoading.value = true
  try {
    const me = await request('/api/me')
    isLoggedIn.value = !!(me && !me.guest)
    isAdmin.value = !!(me && me.is_admin)
  } finally {
    authLoading.value = false
  }
}

async function loadSummary() {
  const data = await request('/api/admin/summary')
  if (!data.error) summary.value = data
}

async function loadReports() {
  const data = await request('/api/admin/reports?status=' + encodeURIComponent(reportStatus.value))
  reports.value = data.reports || []
}

async function resolveReport(id, action) {
  const data = await request('/api/admin/reports/' + id + '/resolve', {
    method: 'POST',
    data: { action: action }
  })
  if (data.ok) {
    toast(action === 'resolve' ? '已处理' : '已驳回', 'success')
    await refreshAll()
  } else {
    toast(data.error || '操作失败')
  }
}

async function loadPosts() {
  const params = '?status=' + encodeURIComponent(postStatus.value) + '&q=' + encodeURIComponent(postQuery.value || '')
  const data = await request('/api/admin/posts' + params)
  posts.value = data.posts || []
}

async function togglePostPin(post) {
  const data = await request('/api/admin/posts/' + post.id + '/pin', { method: 'POST', data: { pinned: !post.isPinned } })
  if (data.ok) { toast('已更新', 'success'); await loadPosts(); await loadSummary() } else toast(data.error || '操作失败')
}

async function togglePostFeature(post) {
  const data = await request('/api/admin/posts/' + post.id + '/feature', { method: 'POST', data: { featured: !post.isFeatured } })
  if (data.ok) { toast('已更新', 'success'); await loadPosts(); await loadSummary() } else toast(data.error || '操作失败')
}

async function togglePostHidden(post) {
  const data = await request('/api/admin/posts/' + post.id + '/hide', { method: 'POST', data: { hidden: !post.isHidden } })
  if (data.ok) { toast(post.isHidden ? '已恢复' : '已隐藏', 'success'); await loadPosts(); await loadSummary() } else toast(data.error || '操作失败')
}

async function loadUsers() {
  const data = await request('/api/admin/users?q=' + encodeURIComponent(userQuery.value || ''))
  users.value = data.users || []
}

async function addManualPoints() {
  const uid = parseInt(manualUserId.value, 10)
  const points = parseInt(manualPoints.value, 10)
  if (!uid || !points) { toast('请填写用户ID和积分'); return }
  const data = await request('/api/admin/confirm-recharge', {
    method: 'POST',
    data: { action: 'add', user_id: uid, points: points, remark: manualRemark.value || '后台手动加积分' }
  })
  if (data.ok) {
    toast('已加积分', 'success')
    manualPoints.value = ''
    await loadUsers()
    await loadSummary()
  } else {
    toast(data.error || '操作失败')
  }
}

async function loadRechargeOrders() {
  const data = await request('/api/admin/recharge/orders?status=' + encodeURIComponent(rechargeStatus.value))
  rechargeOrders.value = data.orders || []
}

async function loadAuditLogs() {
  const data = await request('/api/admin/audit-logs')
  auditLogs.value = data.logs || []
}

async function confirmOrder(id) {
  const data = await request('/api/admin/confirm-recharge', { method: 'POST', data: { order_id: id } })
  if (data.ok) {
    toast('已确认到账', 'success')
    await loadRechargeOrders()
    await loadSummary()
  } else {
    toast(data.error || '操作失败')
  }
}

function confirmOrderByInput() {
  const id = parseInt(manualOrderId.value, 10)
  if (!id) { toast('请输入订单ID'); return }
  confirmOrder(id)
}

async function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'reports') await loadReports()
  if (tab === 'posts') await loadPosts()
  if (tab === 'users') await loadUsers()
  if (tab === 'recharge') await loadRechargeOrders()
  if (tab === 'audit') await loadAuditLogs()
}

async function refreshAll() {
  if (!isAdmin.value) return
  await loadSummary()
  await switchTab(activeTab.value)
}

onMounted(async function() {
  try { isLoggedIn.value = !!(uni.getStorageSync('xc_token') || localStorage.getItem('xc_token')) } catch(_) {}
  await checkAdmin()
  await refreshAll()
})
</script>

<style scoped>
.page-root {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text-1);
  position: relative;
}

.bg-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(135deg, rgba(178,149,93,0.08), transparent 34%),
    radial-gradient(circle at 86% 12%, rgba(34, 89, 83, 0.10), transparent 28%);
}

.admin-wrap {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 96px 0 56px;
  position: relative;
  z-index: 1;
}

.admin-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.section-tag {
  color: var(--accent);
  font-size: 0.78rem;
  letter-spacing: 0;
  margin-bottom: 6px;
}

.admin-title {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1.1;
}

.admin-desc, .panel-sub {
  color: var(--text-3);
  font-size: 0.9rem;
  margin-top: 8px;
}

.admin-head-actions, .filter-line, .manual-box, .row-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.admin-primary, .admin-icon-btn, .mini-btn, .admin-tabs button {
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  color: var(--text-2);
  border-radius: 8px;
  min-height: 36px;
  padding: 0 14px;
  font-size: 0.85rem;
  cursor: pointer;
}

.admin-primary {
  background: var(--accent);
  color: #1c160d;
  border-color: var(--accent);
  font-weight: 650;
}

.admin-icon-btn {
  width: 36px;
  padding: 0;
  font-size: 1.05rem;
}

.mini-btn {
  min-height: 30px;
  padding: 0 10px;
  font-size: 0.78rem;
}

.mini-btn.danger {
  border-color: rgba(172, 78, 70, 0.45);
  color: #d27a70;
}

.auth-state, .admin-panel, .metric-tile {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  box-shadow: var(--card-shadow);
}

.auth-state {
  padding: 28px;
  color: var(--text-2);
}

.auth-state.denied {
  max-width: 520px;
}

.denied-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.denied-copy {
  color: var(--text-3);
  margin-bottom: 18px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.metric-tile {
  padding: 16px;
  min-height: 92px;
}

.metric-label {
  display: block;
  color: var(--text-3);
  font-size: 0.78rem;
}

.metric-value {
  display: block;
  font-size: 1.9rem;
  font-weight: 750;
  margin-top: 10px;
}

.metric-tile.warn .metric-value {
  color: #d9a441;
}

.admin-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  overflow-x: auto;
}

.admin-tabs button.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #1c160d;
  font-weight: 650;
}

.admin-panel {
  padding: 16px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.panel-title {
  font-size: 1.1rem;
  font-weight: 700;
}

.admin-input, .admin-select {
  min-height: 36px;
  border: 1px solid var(--input-border);
  background: var(--input-bg);
  color: var(--text-1);
  border-radius: 8px;
  padding: 0 12px;
  box-sizing: border-box;
  font-size: 0.85rem;
}

.admin-input {
  width: 220px;
}

.admin-input.compact {
  width: 104px;
}

.manual-box {
  margin-bottom: 14px;
  padding: 10px;
  border: 1px dashed var(--card-border);
  border-radius: 8px;
}

.table-list {
  width: 100%;
  overflow-x: auto;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1.2fr;
  gap: 12px;
  align-items: center;
  min-width: 780px;
  padding: 11px 8px;
  border-bottom: 1px solid var(--card-border);
  color: var(--text-2);
  font-size: 0.84rem;
}

.table-row.table-head {
  color: var(--text-3);
  font-size: 0.76rem;
  font-weight: 700;
}

.table-row.post-row {
  grid-template-columns: 0.5fr 1.7fr 0.8fr 1.2fr 0.8fr 1.7fr;
  min-width: 980px;
}

.table-row.user-row {
  grid-template-columns: 0.5fr 1.4fr 0.8fr 0.8fr 0.8fr 1.1fr;
  min-width: 800px;
}

.table-row.order-row {
  grid-template-columns: 0.5fr 1.4fr 1.4fr 0.8fr 0.8fr 1fr;
  min-width: 860px;
}

.table-row.audit-row {
  grid-template-columns: 1fr 1.1fr 0.9fr 0.8fr 1.7fr 0.9fr;
  min-width: 980px;
}

.title-cell {
  color: var(--text-1);
  font-weight: 650;
}

.empty-line {
  padding: 26px 8px;
  color: var(--text-3);
  text-align: center;
}

@media (max-width: 760px) {
  .admin-wrap {
    width: min(100% - 20px, 1180px);
    padding-top: 82px;
  }

  .admin-head, .panel-head {
    display: block;
  }

  .admin-head-actions, .filter-line {
    margin-top: 12px;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .admin-input {
    width: 100%;
  }

  .admin-input.compact {
    width: calc(50% - 4px);
  }
}
</style>
