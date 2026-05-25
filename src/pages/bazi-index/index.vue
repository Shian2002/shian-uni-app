<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- 页面头部 -->
      <section class="tool-hero">
        <view class="tool-hero-content">
          <view class="section-tag">八字排盘</view>
          <view class="tool-hero-title">八字排盘 · 看透先天格局与人生大运</view>
          <view class="tool-hero-desc">定格局 · 看喜忌 · 断大运 · 解姻缘 · 知财运</view>
        </view>
      </section>

      <!-- 工具面板 -->
      <section class="section">
        <view class="tool-container">
          <!-- 无痕模式 -->
          <view class="incognito-bar">
            <view class="incognito-toggle" @tap="toggleIncognito">
              <view class="incognito-check" :class="{ checked: incognito }"></view>
              <text>{{ incognito ? '🔒 无痕模式' : '🔓 有痕模式' }}</text>
            </view>
            <text class="incognito-desc">本地计算 · 不上传数据 · 退出自动清空</text>
          </view>

          <!-- Tab 切换 -->
          <view class="tool-tabs">
            <view id="baziTabFree" class="tool-tab" :class="{ active: activeTab === 'free' }" @tap="switchBaziTab('free')">
              八字排盘<text class="tab-badge free">免费</text>
            </view>
            <view id="baziTabAi" class="tool-tab" :class="{ active: activeTab === 'ai' }" @tap="switchBaziTab('ai')">
              时安八字系统<text class="tab-badge">PRO</text>
            </view>
            <view id="baziTabRecords" class="tool-tab" :class="{ active: activeTab === 'records' }" @tap="switchBaziTab('records')">
              排盘记录
            </view>
          </view>

          <!-- ══ 八字排盘（免费） ══ -->
          <view class="tool-tab-content" v-show="activeTab === 'free'">
            <view class="wz-form">
              <!-- 姓名 + 分类 -->
              <view class="wz-form-row">
                <view class="wz-form-item wz-flex-3">
                  <text class="wz-form-label">姓名</text>
                  <view id="baziName-wrap" class="dom-input-wrap"></view>
                </view>
                <view class="wz-form-item wz-flex-1">
                  <text class="wz-form-label">分类</text>
                  <picker :range="['全部', '客户', '名人']" :value="baziCatIdx" @change="baziCatIdx = $event.detail.value">
                    <view class="wz-form-input picker-display">{{ ['全部', '客户', '名人'][baziCatIdx] }}</view>
                  </picker>
                </view>
              </view>

              <!-- 性别 + 历法 -->
              <view class="wz-form-row">
                <view class="wz-form-item">
                  <text class="wz-form-label">性别</text>
                  <view class="wz-segment-box">
                    <view id="baziGenderMale" class="wz-segment-btn" :class="{ active: baziGender === '男' }" @tap="selectBaziGender('男')">
                      <text class="wz-segment-icon">♂</text><text>男</text>
                    </view>
                    <view id="baziGenderFemale" class="wz-segment-btn" :class="{ active: baziGender === '女' }" @tap="selectBaziGender('女')">
                      <text class="wz-segment-icon">♀</text><text>女</text>
                    </view>
                  </view>
                </view>
                <view class="wz-form-item wz-flex-2">
                  <text class="wz-form-label">历法</text>
                  <view class="wz-segment-box">
                    <view id="baziCalGongLi" class="wz-segment-btn" :class="{ active: baziCalType === '公历' }" @tap="selectBaziCalType('公历')">公历</view>
                    <view id="baziCalNongLi" class="wz-segment-btn" :class="{ active: baziCalType === '农历' }" @tap="selectBaziCalType('农历')">农历</view>
                    <view id="baziCalSiZhu" class="wz-segment-btn" :class="{ active: baziCalType === '四柱' }" @tap="selectBaziCalType('四柱')">四柱</view>
                  </view>
                </view>
              </view>

              <view class="wz-divider"></view>

              <!-- 出生时间（公历/农历模式）（:class/v-show已移除，由DOM操作控制） -->
              <view class="wz-form-group" id="baziDateSection">
                <text class="wz-form-label">出生时间</text>
                <view class="wz-datetime-row">
                  <view class="wz-dt-col">
                    <select id="baziYear" class="wz-datetime-select"></select>
                  </view>
                  <view class="wz-dt-col">
                    <select id="baziMonth" class="wz-datetime-select"></select>
                  </view>
                  <view class="wz-dt-col">
                    <select id="baziDay" class="wz-datetime-select"></select>
                  </view>
                  <view class="wz-dt-col wz-dt-hour">
                    <select id="baziHour" class="wz-datetime-select"></select>
                  </view>
                  <view class="wz-dt-col wz-dt-minute">
                    <select id="baziMinute" class="wz-datetime-select"></select>
                  </view>
                </view>
                <view class="wz-instant-row">
                  <view class="wz-instant-btn" @tap="wzInstantPaipan">⚡ 即时起局</view>
                  <view class="wz-instant-preview" v-if="instantPreview">{{ instantPreview }}</view>
                </view>
              </view>

              <!-- 四柱输入（四柱模式）（v-show已移除，由DOM操作控制） -->
              <view class="wz-form-group" id="baziSiziSection" style="display:none;">
                <text class="wz-form-label">直接输入四柱干支</text>
                <view class="wz-sizi-grid">
                  <view class="wz-sizi-row-item">
                    <text class="wz-sizi-label">年柱</text>
                    <view id="siziYear-wrap" class="dom-input-wrap"></view>
                  </view>
                  <view class="wz-sizi-row-item">
                    <text class="wz-sizi-label">月柱</text>
                    <view id="siziMonth-wrap" class="dom-input-wrap"></view>
                  </view>
                  <view class="wz-sizi-row-item">
                    <text class="wz-sizi-label">日柱</text>
                    <view id="siziDay-wrap" class="dom-input-wrap"></view>
                  </view>
                  <view class="wz-sizi-row-item">
                    <text class="wz-sizi-label">时柱</text>
                    <view id="siziHour-wrap" class="dom-input-wrap"></view>
                  </view>
                </view>
                <text class="wz-form-hint">输入天干+地支各一字，如：甲子、丙寅、戊午、庚申</text>
              </view>

              <view class="wz-divider"></view>

              <!-- 出生地址 -->
              <view class="wz-form-group">
                <text class="wz-form-label">出生地址</text>
                <view class="wz-addr-selects">
                  <select id="baziProvince" class="wz-addr-select"><option value="">-- 省 --</option></select>
                  <select id="baziCity" class="wz-addr-select"><option value="">-- 市 --</option></select>
                  <select id="baziDistrict" class="wz-addr-select"><option value="">-- 区 --</option></select>
                </view>
                <input type="hidden" id="baziBirthAddr" value="" style="display:none;">
                <input type="hidden" id="baziBirthLng" value="0" style="display:none;">
                <input type="hidden" id="baziBirthLat" value="0" style="display:none;">
                <view class="wz-addr-info" id="baziAddrInfo" style="display:none;">
                  <text class="wz-addr-solar" id="baziAddrSolar">真太阳时：--</text>
                  <text class="wz-addr-lng" id="baziAddrLng">经度：-- 纬度：--</text>
                </view>
              </view>

              <!-- 高级选项 -->
              <view class="wz-form-group wz-advanced-box">
                <view class="wz-switch-grid">
                  <view class="wz-switch-row">
                    <text class="wz-switch-label">真太阳时</text>
                    <view id="baziSwitchSolar" class="wz-switch" :class="{ active: useSolarTime }" @tap="toggleBaziSolar">
                      <view class="wz-switch-slider"></view>
                    </view>
                    <text class="wz-switch-hint">{{ useSolarTime ? '开' : '关' }}</text>
                  </view>
                  <view class="wz-switch-row">
                    <text class="wz-switch-label">夏令时</text>
                    <view id="baziSwitchDst" class="wz-switch" :class="{ active: isDst }" @tap="toggleBaziDst">
                      <view class="wz-switch-slider"></view>
                    </view>
                    <text class="wz-switch-hint">{{ isDst ? '开' : '关' }}</text>
                  </view>
                  <view class="wz-switch-row">
                    <text class="wz-switch-label">子时换日</text>
                    <view id="baziSwitchZi" class="wz-switch" :class="{ active: nightZi }" @tap="toggleBaziZi">
                      <view class="wz-switch-slider"></view>
                    </view>
                    <text class="wz-switch-hint">{{ nightZi ? '早子时' : '夜子时' }}</text>
                  </view>
                  <view class="wz-switch-row">
                    <text class="wz-switch-label">保存案例</text>
                    <view id="baziSwitchSave" class="wz-switch" :class="{ active: saveCase }" @tap="toggleBaziSave">
                      <view class="wz-switch-slider"></view>
                    </view>
                    <text class="wz-switch-hint">{{ saveCase ? '保存' : '不保存' }}</text>
                  </view>
                </view>
                <text class="wz-form-hint">夏令时：1986-1991年中国实行夏令时，时钟拨快1小时 | 子时换日：23:00后日柱是否换到次日（默认不换日）</text>
              </view>

              <view class="wz-submit-btn" @tap="baziFreePaipan">📜 免费排盘</view>
              <text class="wz-form-hint" style="text-align:center;display:block;">基础命盘结果，不含AI解读。如需深度解读请使用时安八字系统。</text>
              <view class="privacy-note">✅ 本地计算 · 不上传数据 · 秒出结果</view>
            </view>
          </view>


          <!-- ══ 八字AI系统 ══ -->
          <view class="tool-tab-content" id="baziTabAiContent" v-show="activeTab === 'ai'">
            <view class="form-group">
              <text class="form-label">姓名</text>
              <view id="baiName-wrap" class="dom-input-wrap"></view>
            </view>
            <view class="form-row">
              <view class="form-group">
                <text class="form-label">性别</text>
                <select id="baiGender" class="form-select-picker"></select>
              </view>
              <view class="form-group">
                <text class="form-label">历法</text>
                <select id="baiCal" class="form-select-picker"></select>
              </view>
            </view>
            <view class="form-group">
              <text class="form-label">出生日期</text>
              <view class="qf-datetime-row" style="gap:6px;">
                <view class="qf-dt-col">
                  <select id="bai-year" class="qf-datetime-select"></select>
                </view>
                <view class="qf-dt-col">
                  <select id="bai-month" class="qf-datetime-select"></select>
                </view>
                <view class="qf-dt-col">
                  <select id="bai-day" class="qf-datetime-select"></select>
                </view>
              </view>
            </view>
            <view class="form-group">
              <text class="form-label">出生时辰</text>
              <select id="baiHour" class="form-select-picker"></select>
            </view>
            <view class="advanced-fields" :class="{ show: baiAdvanced }">
              <view class="form-group">
                <text class="form-label">出生地（时区校正）</text>
                <view id="baiAddr-wrap" class="dom-input-wrap"></view>
              </view>
            </view>
            <view class="advanced-toggle" @tap="baiAdvanced = !baiAdvanced">{{ baiAdvanced ? '▼ 收起高级选项' : '▶ 高级选项' }}</view>
            <view class="form-group"><text class="form-label">分析类型</text>
              <view class="analysis-type-row">
                <view class="analysis-type-btn" :class="{ active: baiAnalysisTypeIdx === 0 }" id="baiAiTypeBtn0">📜 命局总览</view>
                <view class="analysis-type-btn" :class="{ active: baiAnalysisTypeIdx === 1 }" id="baiAiTypeBtn1">💰 财运事业</view>
                <view class="analysis-type-btn" :class="{ active: baiAnalysisTypeIdx === 2 }" id="baiAiTypeBtn2">❤️ 婚姻感情</view>
                <view class="analysis-type-btn" :class="{ active: baiAnalysisTypeIdx === 3 }" id="baiAiTypeBtn3">📈 大运流年</view>
                <view class="analysis-type-btn" :class="{ active: baiAnalysisTypeIdx === 4 }" id="baiAiTypeBtn4">🏥 健康六亲</view>
              </view>
            </view>
            <view class="form-group"><text class="form-label">你的问题（选填）</text><view id="baiQuestion-wrap" class="dom-input-wrap"></view></view>
            <view class="submit-btn" id="baiAiAskBtn">🔮 AI 深度解读</view>
            <!-- 流式解读区域 -->
            <view class="qai-stream-box" v-if="baiAiLoading || baziAiResult">
              <view class="chat-container" id="baiChatContainer"></view>
            </view>
            <view class="chat-input-bar" id="baiChatInputBar" style="display:none;">
              <input class="chat-input" id="baiChatInput" placeholder="继续追问..." />
              <view class="chat-send-btn" id="baiFollowUpBtn">发送</view>
            </view>
            <view class="privacy-note incognito-status">✅ 无痕模式已开启 · 本地计算 · 不上传数据 · 退出自动清空</view>
          </view>

          <!-- ══ 记录案例 ══ -->
          <view class="tool-tab-content" v-show="activeTab === 'records'">
            <view class="record-page">
              <!-- 1. 顶部Tab切换 -->
              <view class="record-tabs">
                <view id="baziRecordPaipan" class="record-tab" :class="{ active: recordTab === 'paipan' }" @tap="switchRecordTab('paipan')">排盘案例</view>
                <view id="baziRecordHepan" class="record-tab" :class="{ active: recordTab === 'hepan' }" @tap="switchRecordTab('hepan')">合盘案例</view>
              </view>

              <!-- 2. 搜索栏 + 功能按钮 -->
              <view class="record-toolbar">
                <view class="record-search">
                  <view id="recordSearch-wrap" class="dom-input-wrap"></view>
                  <view class="search-btn" @tap="onRecordSearch">搜索</view>
                </view>
                <view class="record-actions">
                  <view id="baziBatchToggle" class="action-btn" :class="{ active: batchMode }" @tap="toggleBatchDelete">批量删除</view>
                  <view class="action-btn" @tap="showFilter = !showFilter">筛选</view>
                </view>
              </view>

              <!-- 3. 分类标签 -->
              <view class="record-categories">
                <text class="cat-label">案例分类:</text>
                <view class="cat-tags">
                  <view id="baziCatAll" class="cat-tag" :class="{ active: catFilter === '全部' }" @tap="selectCatFilter('全部')">全部</view>
                  <view id="baziCatClient" class="cat-tag" :class="{ active: catFilter === '客户' }" @tap="selectCatFilter('客户')">客户</view>
                  <view id="baziCatFamous" class="cat-tag" :class="{ active: catFilter === '名人' }" @tap="selectCatFilter('名人')">名人</view>
                  <view id="baziCatFamily" class="cat-tag" :class="{ active: catFilter === '亲友' }" @tap="selectCatFilter('亲友')">亲友</view>
                </view>
              </view>

              <!-- 4. 星标八字区 -->
              <view class="star-section" v-if="starredRecords.length > 0">
                <view class="star-title">⭐ 星标八字</view>
                <view class="star-cards">
                  <view class="bz-card starred" v-for="r in starredRecords" :key="r.id" @tap="viewRecord(r)">
                    <text class="sx-icon">{{ r.gender === '男' ? '♂' : '♀' }}</text>
                    <view class="card-userinfo">
                      <view class="card-name">{{ r.name || '未命名' }}</view>
                      <view class="card-date">{{ r.dateStr }}</view>
                    </view>
                  </view>
                </view>
              </view>

              <!-- 5. 批量操作栏 -->
              <view class="batch-bar" v-if="batchMode">
                <label class="batch-select-all" @tap="toggleSelectAll">
                  <text>{{ selectAll ? '☑' : '☐' }} 全选</text>
                </label>
                <text class="batch-count">已选 {{ selectedIds.length }} 项</text>
                <view class="batch-confirm-btn" @tap="confirmBatchDelete">确认删除</view>
                <view class="batch-cancel-btn" @tap="cancelBatchDelete">取消</view>
              </view>

              <!-- 6. 案例列表 -->
              <view class="case-cards" v-if="filteredRecords.length > 0">
                <view class="bz-card" v-for="r in filteredRecords" :key="r.id" @tap="viewRecord(r)">
                  <view class="batch-checkbox" v-if="batchMode">
                    <view class="checkbox-view" :class="{ checked: selectedIds.includes(r.id) }" @tap.stop="toggleSelectId(r.id)"></view>
                  </view>
                  <text class="sx-icon">{{ r.gender === '男' ? '♂' : '♀' }}</text>
                  <view class="card-userinfo">
                    <view class="card-name">{{ r.name || '未命名' }}<text class="card-sex">{{ r.gender }}</text></view>
                    <view class="card-date">{{ r.dateStr }}</view>
                  </view>
                  <view class="card-gz">
                    <view class="card-gan">
                      <text class="gz-label" v-for="(g, i) in r.ganArr" :key="'g'+i">{{ g }}</text>
                    </view>
                    <view class="card-zhi">
                      <text class="gz-label" v-for="(z, i) in r.zhiArr" :key="'z'+i">{{ z }}</text>
                    </view>
                  </view>
                  <view class="card-star" :class="{ starred: r.starred }" @tap.stop="toggleStar(r)">★</view>
                </view>
              </view>

              <!-- 7. 空状态 -->
              <view class="record-empty" v-if="filteredRecords.length === 0">
                <text class="empty-icon">📋</text>
                <view class="empty-text">暂无排盘记录</view>
                <view class="empty-hint">排一盘试试吧，记录会自动保存在这里</view>
                <view class="btn btn-accent btn-sm" @tap="activeTab = 'free'">去排盘</view>
              </view>
            </view>
          </view>
        </view>
      </section>
    </view>

    <!-- 页脚 -->
    <view class="site-footer">
      <view class="footer-disclaimer">⚠️ 本站所有内容仅为民俗文化与传统命理科普参考，不构成任何决策建议，严禁利用本站内容从事封建迷信及违法违规活动，本站不对任何用户基于本站内容做出的决策承担任何责任</view>
      <view class="footer-grid">
        <view class="footer-col">
          <view class="footer-col-title">平台信息</view>
          <navigator url="/package-info/about/index">关于我们</navigator>
        </view>
        <view class="footer-col">
          <view class="footer-col-title">快捷导航</view>
          <navigator url="/pages/qimen/index" open-type="switchTab">奇门遁甲</navigator>
          <navigator url="/pages/bazi-index/index" open-type="switchTab">八字排盘</navigator>
          <navigator url="/pages/calendar/index" open-type="switchTab">专属日历</navigator>
          <navigator url="/pages/community/index" open-type="switchTab">社区</navigator>
        </view>
        <view class="footer-col">
          <view class="footer-col-title">备案与版权</view>
          <view class="footer-icp">ICP备案号：京ICP备2026050601号-1</view>
          <view class="footer-icp">© 2026 时安解忧屋 版权所有</view>
        </view>
      </view>
      <view class="footer-bottom">
        <text class="footer-bottom-text">时安解忧屋 · 看得懂用得上的民俗命理参考平台</text>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'

// ── 主题 ──
const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  uni.setStorageSync('xc_theme', theme.value)
  try {
    document.documentElement.setAttribute('data-theme', theme.value); document.body.setAttribute('data-theme', theme.value); const root = document.querySelector('.page-root')
    if (root) root.setAttribute('data-theme', theme.value)
    const icon = document.getElementById('themeToggleIcon')
    if (icon) icon.textContent = theme.value === 'dark' ? '🌙' : '☀️'
  } catch(_) {}
}

// ── 菜单 ──
const mobileMenuOpen = ref(false)
const submenuOpen = ref({ qimen: false, bazi: false, more: false })
function openMobileMenu() { mobileMenuOpen.value = true }
function closeMobileMenu() { mobileMenuOpen.value = false }
function toggleSubmenu(key) { submenuOpen.value[key] = !submenuOpen.value[key] }

const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

// ── 无痕模式 ──
const incognito = ref(true)

// ── Tab切换 ──
const activeTab = ref('free')

// ── 八字免费排盘表单 ──
const baziName = ref('')
const baziCatIdx = ref(0)
const baziGender = ref('男')
const baziCalType = ref('公历')
const baziDate = ref('')
const baziHourIdx = ref(12)
const baziMinuteIdx = ref(0)
const instantPreview = ref('')

// 时辰选项
const hourLabels = Array.from({ length: 24 }, (_, i) => String(i))
const minuteLabels = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'))

// 四柱输入
const siziYear = ref(''); const siziMonth = ref(''); const siziDay = ref(''); const siziHour = ref('')

// 地址：已改用原生select + DOM操作（绕过uni-picker H5 bug）

// 高级选项
const useSolarTime = ref(true)
const isDst = ref(false)
const nightZi = ref(false)
const saveCase = ref(false)

async function wzInstantPaipan() {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const day = now.getDate()
  const hour = now.getHours()
  const minute = now.getMinutes()

  baziDate.value = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`
  baziHourIdx.value = hour
  baziMinuteIdx.value = minute

  var yEl = document.getElementById('baziYear'); if (yEl) yEl.value = year
  var mEl = document.getElementById('baziMonth'); if (mEl) mEl.value = month

  if (baziCalType.value === '农历') {
    await new Promise(function(resolve) {
      fetch('/api/bazi/solar-to-lunar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({year: year, month: month, day: day})
      }).then(function(r) { return r.json() }).then(function(data) {
        if (data.success) {
          wzUpdateLunarMonthDayWithDate(data.year, data.month, data.day, data.isLeap, resolve)
        } else {
          wzUpdateLunarMonthDay()
          resolve()
        }
      }).catch(function() {
        wzUpdateLunarMonthDay()
        resolve()
      })
    })
  } else {
    refillBaziDaySelect()
    var dEl = document.getElementById('baziDay'); if (dEl) dEl.value = day
  }

  var hEl = document.getElementById('baziHour'); if (hEl) hEl.value = hour
  var miEl = document.getElementById('baziMinute'); if (miEl) miEl.value = minute

  updateBaziDate()

  var timeStr = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')} ${String(hour).padStart(2,'0')}:${String(minute).padStart(2,'0')}`

  try {
    var birthTime = `${year}${String(month).padStart(2,'0')}${String(day).padStart(2,'0')}${String(hour).padStart(2,'0')}${String(minute).padStart(2,'0')}`
    var r = await fetch('/api/bazi/paipan', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        name: '', gender: baziGender.value || '男', calType: baziCalType.value === '农历' ? '农历' : '公历',
        birthTime: birthTime, birthAddr: '',
        isDst: isDst.value, nightZiMode: nightZi.value ? '夜子时换日' : '夜子时不换日',
        useSolarTime: useSolarTime.value, isLeapMonth: false
      })
    })
    var data = await r.json()
    if (data.success && data.four_pillars) {
      var p = data.four_pillars
      var yz = (p.year && p.year.gan ? p.year.gan : '') + (p.year && p.year.zhi ? p.year.zhi : '')
      var mz = (p.month && p.month.gan ? p.month.gan : '') + (p.month && p.month.zhi ? p.month.zhi : '')
      var dz = (p.day && p.day.gan ? p.day.gan : '') + (p.day && p.day.zhi ? p.day.zhi : '')
      var hz = p.hour ? ((p.hour.gan || '') + (p.hour.zhi || '')) : ''
      var lunarStr = data.lunar_str || ''
      instantPreview.value = `${yz} ${mz} ${dz} ${hz}\n${lunarStr ? '农历：' + lunarStr + '  ' : ''}公历：${timeStr}`
    } else {
      instantPreview.value = `公历：${timeStr}`
    }
  } catch(e) {
    instantPreview.value = `公历：${timeStr}`
  }
}

async function baziFreePaipan() {
  // 从原生DOM select读取值（绕过Vue 3.4.21 render effect bug）
  var yEl = document.getElementById('baziYear')
  var mEl = document.getElementById('baziMonth')
  var dEl = document.getElementById('baziDay')
  var hEl = document.getElementById('baziHour')
  var miEl = document.getElementById('baziMinute')
  if (yEl && mEl && dEl) {
    baziDate.value = yEl.value + '-' + String(mEl.value).padStart(2,'0') + '-' + String(dEl.value).padStart(2,'0')
  }
  if (hEl) baziHourIdx.value = parseInt(hEl.value)
  if (miEl) baziMinuteIdx.value = parseInt(miEl.value)
  if (!baziDate.value && baziCalType.value !== '四柱') { uni.showToast({ title: '请选择出生时间', icon: 'none' }); return }
  try {
    const nameVal = document.getElementById('baziName') ? document.getElementById('baziName').value : baziName.value
    const siziY = document.getElementById('siziYear') ? document.getElementById('siziYear').value : siziYear.value
    const siziM = document.getElementById('siziMonth') ? document.getElementById('siziMonth').value : siziMonth.value
    const siziD = document.getElementById('siziDay') ? document.getElementById('siziDay').value : siziDay.value
    const siziH = document.getElementById('siziHour') ? document.getElementById('siziHour').value : siziHour.value
    const data = baziCalType.value === '四柱'
      ? { calType: '四柱', siziPillars: { year: siziY, month: siziM, day: siziD, hour: siziH }, gender: baziGender.value, name: nameVal }
      : (() => {
          const d = baziDate.value.replace(/-/g, '') // YYYYMMDD
          const h = String(baziHourIdx.value).padStart(2, '0')
          const m = String(baziMinuteIdx.value).padStart(2, '0')
          return {
            calType: baziCalType.value === '农历' ? '农历' : '公历',
            birthTime: d + h + m,  // YYYYMMDDHHmm — Flask 后端格式
            gender: baziGender.value,
            name: nameVal,
            birthAddr: (function() { var el = document.getElementById('baziBirthAddr'); return el ? el.value : '' })(),
            birthLng: (function() { var el = document.getElementById('baziBirthLng'); return el ? parseFloat(el.value) : 0 })(),
            birthLat: (function() { var el = document.getElementById('baziBirthLat'); return el ? parseFloat(el.value) : 0 })(),
            isDst: isDst.value,
            nightZiMode: nightZi.value ? '夜子时换日' : '夜子时不换日',
            useSolarTime: useSolarTime.value,
            isLeapMonth: (function() {
              if (baziCalType.value !== '农历') return false
              var mEl = document.getElementById('baziMonth')
              if (!mEl) return false
              var selOpt = mEl.options[mEl.selectedIndex]
              return selOpt ? selOpt.getAttribute('data-is-leap') === 'true' : false
            })(),
          }
        })()
    const res = await uni.request({ url: '/api/bazi/paipan', method: 'POST', data })
    if (res.data && res.data.redirect) {
      // #ifdef H5
      sessionStorage.setItem('xc_bazi_params', JSON.stringify(data))
      // #endif
      uni.navigateTo({ url: `/pages/bazi-result/index?id=${res.data.id}` })
    }
    else if (res.data && res.data.success) {
      // #ifdef H5
      sessionStorage.setItem('xc_bazi_params', JSON.stringify(data))
      // #endif
      // 无 redirect 时直接跳转结果页（带参数）
      uni.navigateTo({ url: `/pages/bazi-result/index` })
    }
    else if (res.data && res.data.error) { uni.showToast({ title: res.data.error, icon: 'none' }) }
  } catch (e) { uni.showToast({ title: '排盘失败', icon: 'none' }) }
}

// ── 八字AI系统 ──
const baiName = ref(''); const baiGenderIdx = ref(0); const baiCalIdx = ref(0)
const baiDate = ref(''); const baiHourIdx = ref(0); const baiAddr = ref('')
const baiAnalysisTypeIdx = ref(0)
const baiAnalysisTypes = ['overview', 'career', 'love', 'decadal', 'health']
const baiAdvanced = ref(false)
const baiAiLoading = ref(false); const baziAiResult = ref('')
const shichenLabels = ['不确定', '子时 (23-1)', '丑时 (1-3)', '寅时 (3-5)', '卯时 (5-7)', '辰时 (7-9)', '巳时 (9-11)', '午时 (11-13)', '未时 (13-15)', '申时 (15-17)', '酉时 (17-19)', '戌时 (19-21)', '亥时 (21-23)']
window._baiChatHistory = []

async function baiAiAsk() {
  if (baiAiLoading.value) return
  if (!baiDate.value) { uni.showToast({ title: '请选择出生日期', icon: 'none' }); return }

  var d = baiDate.value.replace(/-/g, '')
  var h = String(baiHourIdx.value).padStart(2, '0')
  var gender = ['男', '女'][baiGenderIdx.value]
  var calType = ['公历', '农历'][baiCalIdx.value]
  var question = ((document.getElementById('baiQuestion') || {}).value || '').trim()

  // 清理
  baziAiResult.value = ''; window._baiChatHistory = []
  var chatContainer = document.getElementById('baiChatContainer')
  if (chatContainer) chatContainer.innerHTML = ''
  var inputBar = document.getElementById('baiChatInputBar')
  if (inputBar) inputBar.style.display = 'none'
  baiAiLoading.value = true

  var bubbleId = 'baiBubble_' + Date.now()
  var bubbleHTML = '<div class="chat-bubble-ai" id="' + bubbleId + '">' +
    '<div class="ai-stage">🔗 正在连接 DeepSeek AI 引擎...</div>' +
    '<div class="ai-progress-bar"><div class="ai-progress-fill" style="width:20%"></div></div>' +
    '<div class="chat-bubble-content"></div></div>'
  if (chatContainer) chatContainer.innerHTML = bubbleHTML

  _baiDoStreamSSE({
    bubbleId: bubbleId, url: '/api/bazi/ask/stream',
    body: { birth: d + h + '00', gender: gender, cal_type: calType, question: question, analysis_type: baiAnalysisTypes[baiAnalysisTypeIdx] },
    question: question,
    onDone: function(fullText) {
      window._baiChatHistory = [{ role: 'user', content: question }, { role: 'assistant', content: fullText }]
      baziAiResult.value = fullText
      var bar = document.getElementById('baiChatInputBar'); if (bar) bar.style.display = 'flex'
    },
    onError: function() { baiAiLoading.value = false }
  })
}

function _baiDoStreamSSE(opts) {
  var bubble = document.getElementById(opts.bubbleId); if (!bubble) return
  var stageEl = bubble.querySelector('.ai-stage'); var barEl = bubble.querySelector('.ai-progress-fill')
  var contentEl = bubble.querySelector('.chat-bubble-content')
  var xhr = new XMLHttpRequest(); xhr.open('POST', opts.url, true); xhr.setRequestHeader('Content-Type', 'application/json')
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  if (token) xhr.setRequestHeader('Authorization', 'Bearer ' + token)
  var lastIndex = 0, fullText = '', charQueue = '', typeTimer = null, doneReceived = false
  function startTypewriter() {
    if (typeTimer) return
    typeTimer = setInterval(function() {
      if (charQueue.length === 0 && doneReceived) {
        clearInterval(typeTimer); typeTimer = null
        if (stageEl) stageEl.style.display = 'none'
        var barWrap = bubble.querySelector('.ai-progress-bar'); if (barWrap) barWrap.style.display = 'none'
        if (contentEl) contentEl.innerHTML = _baiRenderCards(fullText)
        if (opts.onDone) opts.onDone(fullText); return
      }
      if (charQueue.length === 0) return
      var take = charQueue.length > 3 ? 2 : 1
      fullText += charQueue.substring(0, take); charQueue = charQueue.substring(take)
      if (contentEl) contentEl.innerHTML = fullText.replace(/\n/g, '<br>')
    }, 35)
  }
  xhr.onprogress = function() {
    var newText = xhr.responseText.substring(lastIndex); lastIndex = xhr.responseText.length
    var lines = newText.split('\n'), eventType = ''
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i]
      if (line.indexOf('event:') === 0) { eventType = line.replace('event:', '').trim(); continue }
      if (line.indexOf('data:') !== 0) continue
      try {
        var data = JSON.parse(line.replace('data:', '').trim())
        if (eventType === 'progress') {
          if (data.stage === 'connecting' && stageEl) stageEl.innerHTML = '🔗 正在连接...'
          else if (data.stage === 'analyzing' && stageEl) stageEl.innerHTML = '🧠 排盘分析中...'
          else if (data.stage === 'generating' && stageEl) { stageEl.innerHTML = '✍️ 正在生成解读...'; startTypewriter() }
          if (barEl) barEl.style.width = '60%'
        } else if (eventType === 'chunk') { charQueue += data.content }
        else if (eventType === 'done') { doneReceived = true; baiAiLoading.value = false }
        else if (eventType === 'error') { if (stageEl) stageEl.innerHTML = '⚠️ ' + data.message; if (opts.onError) opts.onError() }
        eventType = ''
      } catch(_) {}
    }
  }
  xhr.onerror = function() { if (stageEl) stageEl.innerHTML = '⚠️ 网络错误'; if (opts.onError) opts.onError() }
  xhr.send(JSON.stringify(opts.body))
}

function _baiRenderCards(text) {
  var sections = text.split(/\n(?=#{2,3} )/), html = ''
  sections.forEach(function(sec) {
    var m = sec.match(/^(#{2,3})\s+(.+)/); var title = m ? m[2] : ''
    var body = m ? sec.substring(m[0].length).trim() : sec
    body = body.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')
    if (!body) body = '&nbsp;'
    if (title) html += '<div class="qai-card-item"><div class="qai-card-title">' + title + '</div><div class="qai-card-body"><p>' + body + '</p></div></div>'
  })
  return html
}

function baiSendFollowUp() {
  var input = document.getElementById('baiChatInput'); if (!input) return
  var question = input.value.trim(); if (!question) return; input.value = ''
  var chatContainer = document.getElementById('baiChatContainer'); if (!chatContainer) return
  var userBubble = document.createElement('view'); userBubble.className = 'chat-bubble-user'; userBubble.textContent = question
  chatContainer.appendChild(userBubble)
  var bubbleId = 'baiFollow_' + Date.now()
  var aiBubble = document.createElement('view'); aiBubble.className = 'chat-bubble-ai'; aiBubble.id = bubbleId
  aiBubble.innerHTML = '<div class="ai-stage">✍️ 正在生成回复...</div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:60%"></div></div><div class="chat-bubble-content"></div>'
  chatContainer.appendChild(aiBubble); chatContainer.scrollIntoView({ behavior: 'smooth', block: 'end' })
  var history = window._baiChatHistory || []; history.push({ role: 'user', content: question })
  _baiDoStreamSSE({
    bubbleId: bubbleId, url: '/api/bazi/ask/stream', body: { question: question, history: history },
    question: question,
    onDone: function(fullText) { history.push({ role: 'assistant', content: fullText }); window._baiChatHistory = history },
    onError: function() {}
  })
}

// 保留旧函数兼容
function goPaipan() {
  if (!baiDate.value) { uni.showToast({ title: '请选择出生日期', icon: 'none' }); return }
  baiAiAsk()
}

// ── 记录案例 ──
const recordTab = ref('paipan')
const recordSearch = ref(''); const catFilter = ref('全部')
const batchMode = ref(false); const selectAll = ref(false)
const selectedIds = ref([]); const showFilter = ref(false)
const records = ref([])
const starredRecords = computed(() => records.value.filter(r => r.starred))
const filteredRecords = computed(() => {
  let list = records.value
  const searchEl = 
  // DOM click 绑定
  setTimeout(function() {
    var aiAskBtn = document.getElementById('baiAiAskBtn')
    if (aiAskBtn) aiAskBtn.addEventListener('click', function() { baiAiAsk() })
    var fwBtn = document.getElementById('baiFollowUpBtn')
    if (fwBtn) fwBtn.addEventListener('click', function() { baiSendFollowUp() })
    for (var i = 0; i < 5; i++) {
      (function(idx) {
        var btn = document.getElementById('baiAiTypeBtn' + idx)
        if (btn) btn.addEventListener('click', function() { baiAnalysisTypeIdx.value = idx })
      })(i)
    }
  }, 300)

  document.getElementById('recordSearch')
  const searchVal = searchEl ? searchEl.value : recordSearch.value
  if (catFilter.value !== '全部') list = list.filter(r => r.category === catFilter.value)
  if (searchVal) { const q = searchVal.toLowerCase(); list = list.filter(r => (r.name || '').toLowerCase().includes(q)) }
  return list
})

function onRecordSearch() {
  const el = 
  // DOM click 绑定
  setTimeout(function() {
    var aiAskBtn = document.getElementById('baiAiAskBtn')
    if (aiAskBtn) aiAskBtn.addEventListener('click', function() { baiAiAsk() })
    var fwBtn = document.getElementById('baiFollowUpBtn')
    if (fwBtn) fwBtn.addEventListener('click', function() { baiSendFollowUp() })
    for (var i = 0; i < 5; i++) {
      (function(idx) {
        var btn = document.getElementById('baiAiTypeBtn' + idx)
        if (btn) btn.addEventListener('click', function() { baiAnalysisTypeIdx.value = idx })
      })(i)
    }
  }, 300)

  document.getElementById('recordSearch')
  if (el) recordSearch.value = el.value
}
function toggleBatchDelete() {
  batchMode.value = !batchMode.value; selectedIds.value = []; selectAll.value = false
  const el = document.getElementById('baziBatchToggle')
  if (el) { batchMode.value ? el.classList.add('active') : el.classList.remove('active') }
}
function toggleSelectAll() { selectAll.value = !selectAll.value; selectedIds.value = selectAll.value ? filteredRecords.value.map(r => r.id) : [] }
function toggleSelectId(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx > -1) selectedIds.value.splice(idx, 1); else selectedIds.value.push(id)
}
function confirmBatchDelete() { records.value = records.value.filter(r => !selectedIds.value.includes(r.id)); batchMode.value = false; selectedIds.value = [] }
function cancelBatchDelete() { batchMode.value = false; selectedIds.value = [] }
function toggleStar(r) { r.starred = !r.starred }
function viewRecord(r) { uni.navigateTo({ url: `/pages/bazi-result/index?id=${r.id}` }) }

// ── 模式B: DOM classList 辅助函数 ──
function domSyncActive(ids, key) {
  ids.forEach(function(id) {
    const el = document.getElementById(id)
    if (!el) return
    const val = el.getAttribute('data-val') || id.replace(/^bazi/, '').toLowerCase()
    if (el.classList.contains('active') !== (val === key)) {
      el.classList.toggle('active', val === key)
    }
  })
}

// ── 模式B: Tab切换 ──
function switchBaziTab(tab) {
  activeTab.value = tab
  // DOM classList 切换（绕过Vue 3.4.21 render effect bug）
  var tabs = ['baziTabFree', 'baziTabAi', 'baziTabRecords']
  for (var i = 0; i < tabs.length; i++) {
    var el = document.getElementById(tabs[i])
    if (el) {
      if (tabs[i] === 'baziTab' + tab.charAt(0).toUpperCase() + tab.slice(1)) {
        el.classList.add('active')
      } else {
        el.classList.remove('active')
      }
    }
  }

}

// ── 模式B: 性别选择 ──
function selectBaziGender(val) {
  baziGender.value = val
  var maleEl = document.getElementById('baziGenderMale')
  var femaleEl = document.getElementById('baziGenderFemale')
  if (maleEl) { val === '男' ? maleEl.classList.add('active') : maleEl.classList.remove('active') }
  if (femaleEl) { val === '女' ? femaleEl.classList.add('active') : femaleEl.classList.remove('active') }
}

// ── 模式B: 历法选择 ──
var _calTypeChanging = false  // 防止异步竞态的锁
var _calTypeSeq = 0           // 请求序列号，丢弃过期响应
function selectBaziCalType(type) {
  // 如果正在转换中，忽略重复点击
  if (_calTypeChanging) return
  // 相同历法不重复处理
  if (baziCalType.value === type) return

  var prevType = baziCalType.value  // 用 baziCalType.value 作为真实来源

  // 立即更新 UI 状态
  baziCalType.value = type
  var ids = ['baziCalGongLi', 'baziCalNongLi', 'baziCalSiZhu']
  var vals = ['公历', '农历', '四柱']
  for (var i = 0; i < ids.length; i++) {
    var el = document.getElementById(ids[i])
    if (el) { type === vals[i] ? el.classList.add('active') : el.classList.remove('active') }
  }

  // DOM 控制日期/四柱区域显示（绕过v-show render effect bug）
  var dateSection = document.getElementById('baziDateSection')
  var siziSection = document.getElementById('baziSiziSection')
  if (type === '四柱') {
    if (dateSection) dateSection.style.display = 'none'
    if (siziSection) siziSection.style.display = 'block'
    return
  }
  if (dateSection) dateSection.style.display = 'block'
  if (siziSection) siziSection.style.display = 'none'

  // ── 读取当前日期 ──
  var yEl = document.getElementById('baziYear')
  var mEl = document.getElementById('baziMonth')
  var dEl = document.getElementById('baziDay')
  if (!yEl || !mEl || !dEl) return
  var curY = parseInt(yEl.value)
  var curM = parseInt(mEl.value)
  var curD = parseInt(dEl.value)

  if (type === '农历' && prevType === '公历') {
    // 公历 → 农历
    _calTypeChanging = true
    var seq = ++_calTypeSeq
    fetch('/api/bazi/solar-to-lunar', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({year: curY, month: curM, day: curD})
    }).then(function(r) { return r.json() }).then(function(data) {
      if (seq !== _calTypeSeq) return  // 过期响应，丢弃
      if (data.success) {
        wzUpdateLunarMonthDayWithDate(data.year, data.month, data.day, data.isLeap, function() {
          _calTypeChanging = false  // 内层fetch完成后才释放锁
        })
      } else {
        wzUpdateLunarMonthDay()
        _calTypeChanging = false
      }
    }).catch(function() {
      if (seq !== _calTypeSeq) return
      wzUpdateLunarMonthDay()
      _calTypeChanging = false
    })
  } else if (type === '公历' && prevType === '农历') {
    // 农历 → 公历：获取闰月信息
    var isLeap = false
    var selOpt = mEl.options[mEl.selectedIndex]
    if (selOpt && selOpt.getAttribute('data-is-leap') === 'true') isLeap = true
    _calTypeChanging = true
    var seq2 = ++_calTypeSeq
    fetch('/api/bazi/lunar-to-solar', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({year: curY, month: curM, day: curD, isLeap: isLeap})
    }).then(function(r) { return r.json() }).then(function(data) {
      if (seq2 !== _calTypeSeq) return  // 过期响应，丢弃
      if (data.success) {
        // 重建公历月份选项
        wzInitSolarMonthDayRaw()
        // 设置转换后的公历日期（value格式需匹配：年份纯数字，月份padStart2，日期纯数字）
        var yEl2 = document.getElementById('baziYear')
        var mEl2 = document.getElementById('baziMonth')
        var dEl2 = document.getElementById('baziDay')
        if (yEl2) yEl2.value = data.year
        if (mEl2) mEl2.value = String(data.month).padStart(2, '0')
        // 月份可能不同，重建日期选项
        refillBaziDaySelectForced()
        dEl2 = document.getElementById('baziDay')  // 重建后重新获取
        if (dEl2) dEl2.value = data.day
        updateBaziDate()
      } else {
        wzInitSolarMonthDay()
      }
      _calTypeChanging = false
    }).catch(function() {
      if (seq2 !== _calTypeSeq) return
      wzInitSolarMonthDay()
      _calTypeChanging = false
    })
  } else {
    // 其他情况（如从四柱切换回来）
    if (type === '农历') {
      wzUpdateLunarMonthDay()
    } else {
      wzInitSolarMonthDay()
    }
  }
}

// ── 农历月份日期适配 ──
var _lunarMonthsData = null
var _lunarDayNames = null

var _lunarDayNameMap = {1:'初一',2:'初二',3:'初三',4:'初四',5:'初五',
  6:'初六',7:'初七',8:'初八',9:'初九',10:'初十',
  11:'十一',12:'十二',13:'十三',14:'十四',15:'十五',
  16:'十六',17:'十七',18:'十八',19:'十九',20:'二十',
  21:'廿一',22:'廿二',23:'廿三',24:'廿四',25:'廿五',
  26:'廿六',27:'廿七',28:'廿八',29:'廿九',30:'三十'}

function wzUpdateLunarMonthDay() {
  var yEl = document.getElementById('baziYear')
  if (!yEl) return
  var year = parseInt(yEl.value)
  if (!year) return
  fetch('/api/bazi/lunar-month-data', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({year: year})
  }).then(function(r) { return r.json() }).then(function(data) {
    if (!data.success) { console.error('Lunar data error:', data.error); return }
    _lunarMonthsData = data.months
    _lunarDayNames = data.dayNames || _lunarDayNameMap
    // 重建月份选择器（农历名称）
    var monthSel = document.getElementById('baziMonth')
    if (!monthSel) return
    var prevMonth = monthSel.value
    monthSel.innerHTML = ''
    data.months.forEach(function(m) {
      var opt = document.createElement('option')
      opt.value = String(m.value).padStart(2, '0')
      opt.textContent = m.label
      if (m.isLeap) opt.setAttribute('data-is-leap', 'true')
      monthSel.appendChild(opt)
    })
    // 尝试恢复之前的月份选择
    if (prevMonth && monthSel.querySelector('option[value="' + prevMonth + '"]')) {
      monthSel.value = prevMonth
    }
    // 根据当前选中月份获取天数
    var selIdx = monthSel.selectedIndex
    var mInfo = (selIdx >= 0 && selIdx < data.months.length) ? data.months[selIdx] : data.months[0]
    if (mInfo) {
      wzUpdateLunarDays(mInfo.dayCount, _lunarDayNames)
    }
  }).catch(function(e) { console.error('Failed to fetch lunar data:', e) })
}

// 公历→农历转换后，重建月份/日期并设置到转换后的日期
// onComplete: 完成后的回调（用于释放锁）
function wzUpdateLunarMonthDayWithDate(lunarYear, lunarMonth, lunarDay, isLeap, onComplete) {
  var yEl = document.getElementById('baziYear')
  if (!yEl) { if (onComplete) onComplete(); return }
  // 如果农历年份与当前年份不同，需要更新年份选择器
  if (lunarYear && parseInt(yEl.value) !== lunarYear) {
    yEl.value = lunarYear
  }
  var year = lunarYear || parseInt(yEl.value)
  if (!year) { if (onComplete) onComplete(); return }
  fetch('/api/bazi/lunar-month-data', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({year: year})
  }).then(function(r) { return r.json() }).then(function(data) {
    if (!data.success) { console.error('Lunar data error:', data.error); if (onComplete) onComplete(); return }
    _lunarMonthsData = data.months
    _lunarDayNames = data.dayNames || _lunarDayNameMap
    // 重建月份选择器（农历名称）
    var monthSel = document.getElementById('baziMonth')
    if (!monthSel) { if (onComplete) onComplete(); return }
    monthSel.innerHTML = ''
    var targetMonthIdx = 0  // 默认选中第一个月
    data.months.forEach(function(m, idx) {
      var opt = document.createElement('option')
      opt.value = String(m.value).padStart(2, '0')
      opt.textContent = m.label
      if (m.isLeap) opt.setAttribute('data-is-leap', 'true')
      monthSel.appendChild(opt)
      // 匹配转换后的月份（值相等 + 闰月标识一致）
      if (lunarMonth && m.value === lunarMonth && m.isLeap === !!isLeap) {
        targetMonthIdx = idx
      }
    })
    // 选中目标月份
    monthSel.selectedIndex = targetMonthIdx
    // 根据选中月份的天数重建日期，并设置转换后的日
    var targetMonthInfo = data.months[targetMonthIdx]
    if (targetMonthInfo) {
      wzUpdateLunarDays(targetMonthInfo.dayCount, _lunarDayNames)
      // 设置转换后的日
      var daySel = document.getElementById('baziDay')
      if (daySel && lunarDay) {
        var dayVal = String(lunarDay).padStart(2, '0')
        if (lunarDay <= targetMonthInfo.dayCount) {
          daySel.value = dayVal
        }
      }
      updateBaziDate()
    }
    if (onComplete) onComplete()
  }).catch(function(e) {
    console.error('Failed to fetch lunar data:', e)
    if (onComplete) onComplete()
  })
}

function wzUpdateLunarDays(dayCount, dayNames) {
  var daySel = document.getElementById('baziDay')
  if (!daySel) return
  var prevDay = daySel.value
  daySel.innerHTML = ''
  for (var d = 1; d <= dayCount; d++) {
    var opt = document.createElement('option')
    opt.value = String(d).padStart(2, '0')
    opt.textContent = (dayNames && dayNames[d]) ? dayNames[d] : d
    daySel.appendChild(opt)
  }
  if (parseInt(prevDay) <= dayCount) {
    daySel.value = prevDay
  }
  updateBaziDate()
}

function wzInitSolarMonthDay() {
  var monthSel = document.getElementById('baziMonth')
  if (!monthSel) return
  var curMonth = monthSel.value
  monthSel.innerHTML = ''
  for (var m = 1; m <= 12; m++) {
    var opt = document.createElement('option')
    opt.value = String(m).padStart(2, '0')
    opt.textContent = m + '月'
    monthSel.appendChild(opt)
  }
  if (curMonth) monthSel.value = curMonth
  refillBaziDaySelect()
}

// 不调用 refillBaziDaySelect 的版本（用于农历→公历时先建月份，再手动设日期）
function wzInitSolarMonthDayRaw() {
  var monthSel = document.getElementById('baziMonth')
  if (!monthSel) return
  monthSel.innerHTML = ''
  for (var m = 1; m <= 12; m++) {
    var opt = document.createElement('option')
    opt.value = String(m).padStart(2, '0')
    opt.textContent = m + '月'
    monthSel.appendChild(opt)
  }
}

// 强制版 refillBaziDaySelect（不受农历模式 return 限制）
function refillBaziDaySelectForced() {
  var yEl = document.getElementById('baziYear')
  var mEl = document.getElementById('baziMonth')
  var dEl = document.getElementById('baziDay')
  if (!yEl || !mEl || !dEl) return
  var y = parseInt(yEl.value)
  var m = parseInt(mEl.value)
  var maxDay = getDaysInMonth(y, m)
  var curDay = parseInt(dEl.value)
  dEl.innerHTML = ''
  for (var i = 1; i <= maxDay; i++) {
    var opt = document.createElement('option')
    opt.value = i
    opt.text = i + '日'
    if (i === curDay) opt.selected = true
    dEl.appendChild(opt)
  }
  if (curDay > maxDay) {
    dEl.value = String(maxDay)
  }
  updateBaziDate()
}

// ── 模式B: 开关切换 ──
function toggleBaziSolar() {
  useSolarTime.value = !useSolarTime.value
  var el = document.getElementById('baziSwitchSolar')
  if (el) el.classList.toggle('active', useSolarTime.value)
  // 关闭真太阳时 → 隐藏地址信息面板; 开启 → 如果已选地址则重新显示
  var infoEl = document.getElementById('baziAddrInfo')
  if (infoEl) {
    if (!useSolarTime.value) {
      infoEl.style.display = 'none'
    } else {
      // 开启时：如果已选了城市，重新显示
      var cityEl = document.getElementById('baziCity')
      if (cityEl && cityEl.value) {
        infoEl.style.display = 'flex'
      }
    }
  }
}
function toggleBaziDst() {
  isDst.value = !isDst.value
  var el = document.getElementById('baziSwitchDst')
  if (el) el.classList.toggle('active', isDst.value)
}
function toggleBaziZi() {
  nightZi.value = !nightZi.value
  var el = document.getElementById('baziSwitchZi')
  if (el) el.classList.toggle('active', nightZi.value)
}
function toggleBaziSave() {
  saveCase.value = !saveCase.value
  var el = document.getElementById('baziSwitchSave')
  if (el) el.classList.toggle('active', saveCase.value)
}

// ── 模式B: resultMode ──
function switchBaziResultMode(mode) {
  resultMode.value = mode
  var simpleEl = document.getElementById('baziResultSimple')
  var proEl = document.getElementById('baziResultPro')
  if (simpleEl) { mode === 'simple' ? simpleEl.classList.add('active') : simpleEl.classList.remove('active') }
  if (proEl) { mode === 'pro' ? proEl.classList.add('active') : proEl.classList.remove('active') }
}

// ── 模式B: recordTab ──
function switchRecordTab(tab) {
  recordTab.value = tab
  var paipanEl = document.getElementById('baziRecordPaipan')
  var hepanEl = document.getElementById('baziRecordHepan')
  if (paipanEl) { tab === 'paipan' ? paipanEl.classList.add('active') : paipanEl.classList.remove('active') }
  if (hepanEl) { tab === 'hepan' ? hepanEl.classList.add('active') : hepanEl.classList.remove('active') }
}

// ── 模式B: catFilter ──
function selectCatFilter(val) {
  catFilter.value = val
  var ids = ['baziCatAll', 'baziCatClient', 'baziCatFamous', 'baziCatFamily']
  var vals = ['全部', '客户', '名人', '亲友']
  for (var i = 0; i < ids.length; i++) {
    var el = document.getElementById(ids[i])
    if (el) { val === vals[i] ? el.classList.add('active') : el.classList.remove('active') }
  }
}

// ── 模式C: toggleIncognito ──
function toggleIncognito() {
  incognito.value = !incognito.value
  var el = document.querySelector('.incognito-check')
  if (el) { incognito.value ? el.classList.add('checked') : el.classList.remove('checked') }
}

// ── 模式C: 填充原生select（绕过Vue 3.4.21 picker bug） ──
function fillBaziSelect(id, options, selectedVal, onChange) {
  var el = document.getElementById(id)
  if (!el) return
  el.innerHTML = ''
  for (var i = 0; i < options.length; i++) {
    var opt = document.createElement('option')
    var item = options[i]
    if (typeof item === 'object' && item !== null) {
      opt.value = item.value !== undefined ? item.value : item.label
      opt.text = item.label
    } else {
      opt.value = item
      opt.text = item
    }
    if (String(opt.value) === String(selectedVal)) opt.selected = true
    el.appendChild(opt)
  }
  if (onChange) {
    el.addEventListener('change', function(e) { onChange(e.target.value, e) })
  }
}

// ── 模式C: 年月日联动 ──
function getDaysInMonth(year, month) {
  return new Date(year, month, 0).getDate()
}

function refillBaziDaySelect() {
  // 农历模式下由月份change事件单独处理
  if (baziCalType.value === '农历' && _lunarMonthsData) return
  var yEl = document.getElementById('baziYear')
  var mEl = document.getElementById('baziMonth')
  var dEl = document.getElementById('baziDay')
  if (!yEl || !mEl || !dEl) return
  var y = parseInt(yEl.value)
  var m = parseInt(mEl.value)
  var maxDay = getDaysInMonth(y, m)
  var curDay = parseInt(dEl.value)
  dEl.innerHTML = ''
  for (var i = 1; i <= maxDay; i++) {
    var opt = document.createElement('option')
    opt.value = i
    opt.text = i + '日'
    if (i === curDay) opt.selected = true
    dEl.appendChild(opt)
  }
  if (curDay > maxDay) {
    dEl.value = String(maxDay)
  }
  updateBaziDate()
}

// ── AI版日期联动 ──
function refillBaiDaySelect() {
  var yEl = document.getElementById('bai-year')
  var mEl = document.getElementById('bai-month')
  var dEl = document.getElementById('bai-day')
  if (!yEl || !mEl || !dEl) return
  var y = parseInt(yEl.value)
  var m = parseInt(mEl.value)
  var maxDay = getDaysInMonth(y, m)
  var curDay = parseInt(dEl.value)
  dEl.innerHTML = ''
  for (var i = 1; i <= maxDay; i++) {
    var opt = document.createElement('option')
    opt.value = i
    opt.text = i + '日'
    if (i === curDay) opt.selected = true
    dEl.appendChild(opt)
  }
  if (curDay > maxDay) {
    dEl.value = String(maxDay)
  }
  updateBaiDate()
}

function updateBaiDate() {
  var yEl = document.getElementById('bai-year')
  var mEl = document.getElementById('bai-month')
  var dEl = document.getElementById('bai-day')
  if (yEl && mEl && dEl) {
    baiDate.value = yEl.value + '-' + String(mEl.value).padStart(2, '0') + '-' + String(dEl.value).padStart(2, '0')
  }
}

function updateBaziDate() {
  var y = document.getElementById('baziYear') ? document.getElementById('baziYear').value : ''
  var m = document.getElementById('baziMonth') ? String(document.getElementById('baziMonth').value).padStart(2, '0') : ''
  var d = document.getElementById('baziDay') ? String(document.getElementById('baziDay').value).padStart(2, '0') : ''
  baziDate.value = y + '-' + m + '-' + d
}

// ── 模式A: 创建原生输入框 ──
function createNativeInput(wrapId, type, placeholder, maxlength) {
  var wrap = document.getElementById(wrapId + '-wrap')
  if (!wrap) return
  var input = document.createElement('input')
  input.type = type || 'text'
  input.id = wrapId
  input.placeholder = placeholder || ''
  if (maxlength) input.maxLength = maxlength
  input.className = 'native-input'
  // 样式设置
  input.style.cssText = 'width:100%;padding:9px 12px;border:1.5px solid var(--card-border);border-radius:10px;font-size:0.85rem;background:var(--card-bg);color:var(--text-1);outline:none;box-sizing:border-box;'
  // 对于记录搜索输入，添加 input 事件同步到 ref
  if (wrapId === 'recordSearch') {
    input.addEventListener('input', function(e) {
      recordSearch.value = e.target.value
    })
  }
  wrap.appendChild(input)
}

// ── 初始化 ──
function applyNavQuery(q) {
  if (!q) return
  if (q.includes('tab=free') || q.includes('#free')) { activeTab.value = 'free'; nextTick(() => { switchBaziTab('free') }) }
  else if (q.includes('tab=ai') || q.includes('#ai')) { activeTab.value = 'ai'; nextTick(() => { switchBaziTab('ai') }) }
  else if (q.includes('tab=records') || q.includes('#records')) { activeTab.value = 'records'; nextTick(() => { switchBaziTab('records') }) }
}

onShow(() => {
  try {
    var q = sessionStorage.getItem('_nav_query')
    if (q) { sessionStorage.removeItem('_nav_query'); applyNavQuery(q) }
  } catch(_) {}
  var token = uni.getStorageSync('xc_token')
  var loggedIn = !!token
  if (isLoggedIn.value !== loggedIn) {
    isLoggedIn.value = loggedIn
  }
  var t = uni.getStorageSync('xc_theme')
  if (t && t !== theme.value) {
    theme.value = t
    try {
      document.documentElement.setAttribute('data-theme', t)
      document.body.setAttribute('data-theme', t)
    } catch(_) {}
  }
})

onMounted(() => {
  try {
    uni.$on('nav-query', function(q) { applyNavQuery(q) })
    var q = sessionStorage.getItem('_nav_query')
    if (q) { sessionStorage.removeItem('_nav_query'); applyNavQuery(q) }
  } catch(_) {}
  const now = new Date()
  baziDate.value = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`
  baziHourIdx.value = now.getHours()
  baziMinuteIdx.value = now.getMinutes()

  // ── 创建原生 DOM 输入框（模式A） ──
  // #ifdef H5
  createNativeInput('baziName', 'text', '选填', 30)
  createNativeInput('siziYear', 'text', '甲子', 2)
  createNativeInput('siziMonth', 'text', '丙寅', 2)
  createNativeInput('siziDay', 'text', '戊午', 2)
  createNativeInput('siziHour', 'text', '庚申', 2)
  createNativeInput('baiName', 'text', '选填')
  createNativeInput('baiAddr', 'text', '如：北京')
  createNativeInput('baiQuestion', 'text', '请输入您想问的问题', '200')
  createNativeInput('recordSearch', 'text', '请输入搜索的内容')
  // 记录搜索框特殊样式（在搜索栏圆角容器内，去掉边框/背景）
  var rsEl = 
  // DOM click 绑定
  setTimeout(function() {
    var aiAskBtn = document.getElementById('baiAiAskBtn')
    if (aiAskBtn) aiAskBtn.addEventListener('click', function() { baiAiAsk() })
    var fwBtn = document.getElementById('baiFollowUpBtn')
    if (fwBtn) fwBtn.addEventListener('click', function() { baiSendFollowUp() })
    for (var i = 0; i < 5; i++) {
      (function(idx) {
        var btn = document.getElementById('baiAiTypeBtn' + idx)
        if (btn) btn.addEventListener('click', function() { baiAnalysisTypeIdx.value = idx })
      })(i)
    }
  }, 300)

  document.getElementById('recordSearch')
  if (rsEl) {
    rsEl.style.cssText = 'width:100%;padding:8px 10px;border:none;background:none;outline:none;font-size:14px;color:var(--text-1);box-sizing:border-box;'
  }

  // ── 创建原生select日期选择（模式C：绕过Vue 3.4.21 picker bug） ──
  var curYear = now.getFullYear()
  // 年
  var yearOpts = []
  for (var y = curYear - 120; y <= curYear + 10; y++) {
    yearOpts.push({ value: y, label: y + '年' })
  }
  fillBaziSelect('baziYear', yearOpts, curYear, function() {
    if (baziCalType.value === '农历') { wzUpdateLunarMonthDay() } else { refillBaziDaySelect() }
  })
  // 月
  var monthOpts = []
  for (var i = 1; i <= 12; i++) {
    monthOpts.push({ value: i, label: i + '月' })
  }
  fillBaziSelect('baziMonth', monthOpts, now.getMonth() + 1, function() {
    if (baziCalType.value === '农历' && _lunarMonthsData) {
      // 农历模式：根据选中月份更新日期
      var mEl = document.getElementById('baziMonth')
      var selVal = mEl ? mEl.value : ''
      var mInfo = null
      if (_lunarMonthsData) {
        for (var idx = 0; idx < _lunarMonthsData.length; idx++) {
          if (String(_lunarMonthsData[idx].value).padStart(2, '0') === selVal) {
            var isLeap = false
            var selOpt = mEl.options[mEl.selectedIndex]
            if (selOpt && selOpt.getAttribute('data-is-leap') === 'true') isLeap = true
            if (_lunarMonthsData[idx].isLeap === isLeap) { mInfo = _lunarMonthsData[idx]; break }
          }
        }
      }
      if (mInfo) { wzUpdateLunarDays(mInfo.dayCount, _lunarDayNames) }
    } else {
      refillBaziDaySelect()
    }
  })
  // 日
  var maxDay = getDaysInMonth(curYear, now.getMonth() + 1)
  var dayOpts = []
  for (var i = 1; i <= maxDay; i++) {
    dayOpts.push({ value: i, label: i + '日' })
  }
  fillBaziSelect('baziDay', dayOpts, now.getDate(), function() { updateBaziDate() })
  // 时
  var hourOpts = []
  for (var i = 0; i < 24; i++) {
    hourOpts.push({ value: i, label: String(i).padStart(2, '0') + '时' })
  }
  fillBaziSelect('baziHour', hourOpts, now.getHours(), function(val) {
    baziHourIdx.value = parseInt(val)
  })
  // 分
  var minOpts = []
  for (var i = 0; i < 60; i++) {
    minOpts.push({ value: i, label: String(i).padStart(2, '0') + '分' })
  }
  fillBaziSelect('baziMinute', minOpts, now.getMinutes(), function(val) {
    baziMinuteIdx.value = parseInt(val)
  })
  // #endif

  // ── 填充AI版原生select ──
  // #ifdef H5
  // 性别
  fillBaziSelect('baiGender', [{ value: 0, label: '男' }, { value: 1, label: '女' }], 0, function(val) { baiGenderIdx.value = parseInt(val) })
  // 历法
  fillBaziSelect('baiCal', [{ value: 0, label: '公历' }, { value: 1, label: '农历' }], 0, function(val) { baiCalIdx.value = parseInt(val) })
  // AI版日期
  var baiYearOpts = []
  for (var y = curYear - 120; y <= curYear + 10; y++) {
    baiYearOpts.push({ value: y, label: y + '年' })
  }
  fillBaziSelect('bai-year', baiYearOpts, curYear, function() { refillBaiDaySelect() })
  var baiMonthOpts = []
  for (var i = 1; i <= 12; i++) {
    baiMonthOpts.push({ value: i, label: i + '月' })
  }
  fillBaziSelect('bai-month', baiMonthOpts, now.getMonth() + 1, function() { refillBaiDaySelect() })
  var baiMaxDay = getDaysInMonth(curYear, now.getMonth() + 1)
  var baiDayOpts = []
  for (var i = 1; i <= baiMaxDay; i++) {
    baiDayOpts.push({ value: i, label: i + '日' })
  }
  fillBaziSelect('bai-day', baiDayOpts, now.getDate(), function() { updateBaiDate() })
  // 时辰
  var baiHourOpts = []
  for (var i = 0; i < shichenLabels.length; i++) {
    baiHourOpts.push({ value: i, label: shichenLabels[i] })
  }
  fillBaziSelect('baiHour', baiHourOpts, baiHourIdx.value, function(val) { baiHourIdx.value = parseInt(val) })

  // ── 出生地址：加载城市数据并填充三级级联选择 ──
  var _cityData = null
  fetch('/static/js/city_data.json').then(function(r) { return r.json() }).then(function(data) {
    _cityData = data
    var provEl = document.getElementById('baziProvince')
    var cityEl = document.getElementById('baziCity')
    var distEl = document.getElementById('baziDistrict')
    if (!provEl) return
    provEl.innerHTML = '<option value="">-- 省 --</option>'
    for (var i = 0; i < data.length; i++) {
      if (data[i][0] === '未知地区') continue
      var opt = document.createElement('option')
      opt.value = data[i][0]
      opt.text = data[i][0]
      provEl.appendChild(opt)
    }
    provEl.addEventListener('change', function() {
      if (cityEl) cityEl.innerHTML = '<option value="">-- 市 --</option>'
      if (distEl) { distEl.innerHTML = '<option value="">-- 区 --</option>'; }
      var selProv = provEl.value
      for (var j = 0; j < data.length; j++) {
        if (data[j][0] === selProv && data[j][1]) {
          if (cityEl) {
            for (var k = 0; k < data[j][1].length; k++) {
              var co = document.createElement('option')
              co.value = data[j][1][k][0]
              co.text = data[j][1][k][0]
              co.setAttribute('data-city-idx', k)
              cityEl.appendChild(co)
            }
          }
          break
        }
      }
      _updateAddrInfo()
    })
    if (cityEl) {
      cityEl.addEventListener('change', function() {
        if (distEl) { distEl.innerHTML = '<option value="">-- 区 --</option>'; }
        // 根据选中的省份和城市，填充区级选项
        var selProv = provEl ? provEl.value : ''
        var selCity = cityEl.value
        var hasDistrict = false
        for (var j = 0; j < data.length; j++) {
          if (data[j][0] === selProv && data[j][1]) {
            for (var k = 0; k < data[j][1].length; k++) {
              if (data[j][1][k][0] === selCity && data[j][1][k][1] && data[j][1][k][1].length > 0) {
                hasDistrict = true
                if (distEl) {
                  for (var m = 0; m < data[j][1][k][1].length; m++) {
                    var dopt = document.createElement('option')
                    dopt.value = data[j][1][k][1][m][0]
                    dopt.text = data[j][1][k][1][m][0]
                    dopt.setAttribute('data-lat', data[j][1][k][1][m][1])
                    dopt.setAttribute('data-lng', data[j][1][k][1][m][2])
                    distEl.appendChild(dopt)
                  }
                }
                break
              }
            }
            break
          }
        }
        _updateAddrInfo()
      })
    }
    if (distEl) {
      distEl.innerHTML = '<option value="">-- 区 --</option>'
      distEl.addEventListener('change', function() { _updateAddrInfo() })
    }
  }).catch(function() {})

  function _updateAddrInfo() {
    var provEl = document.getElementById('baziProvince')
    var cityEl = document.getElementById('baziCity')
    var distEl = document.getElementById('baziDistrict')
    var addrEl = document.getElementById('baziBirthAddr')
    var lngEl = document.getElementById('baziBirthLng')
    var latEl = document.getElementById('baziBirthLat')
    var infoEl = document.getElementById('baziAddrInfo')
    var solarEl = document.getElementById('baziAddrSolar')
    var lngInfoEl = document.getElementById('baziAddrLng')
    var provVal = provEl ? provEl.value : ''
    var cityVal = cityEl ? cityEl.value : ''
    var distVal = distEl ? distEl.value : ''
    if (!cityVal) {
      if (infoEl) infoEl.style.display = 'none'
      return
    }
    // 优先从区级取 lat/lng，否则从市级取
    var lat = 0, lng = 0, addrText = provVal
    if (distVal) {
      var distOpt = distEl.options[distEl.selectedIndex]
      lat = distOpt ? parseFloat(distOpt.getAttribute('data-lat')) : 0
      lng = distOpt ? parseFloat(distOpt.getAttribute('data-lng')) : 0
      addrText = provVal + ' ' + cityVal + ' ' + distVal
    } else {
      // 没选区，尝试从 city_data 取城市的经纬度（用第一个区的坐标）
      var found = false
      if (_cityData) {
        for (var j = 0; j < _cityData.length; j++) {
          if (_cityData[j][0] === provVal && _cityData[j][1]) {
            for (var k = 0; k < _cityData[j][1].length; k++) {
              if (_cityData[j][1][k][0] === cityVal && _cityData[j][1][k][1] && _cityData[j][1][k][1].length > 0) {
                lat = _cityData[j][1][k][1][0][1]
                lng = _cityData[j][1][k][1][0][2]
                found = true
                break
              }
            }
          }
          if (found) break
        }
      }
      addrText = provVal + ' ' + cityVal
    }
    if (addrEl) addrEl.value = addrText
    if (lngEl) lngEl.value = lng
    if (latEl) latEl.value = lat
    if (infoEl) {
      infoEl.style.display = 'flex'
      if (solarEl) solarEl.textContent = '真太阳时：已根据经度校正'
      if (lngInfoEl) lngInfoEl.textContent = '经度：' + lng + ' 纬度：' + lat
    }
  }

  const hash = location.hash
  if (hash.includes('tab=free') || hash.includes('#free')) activeTab.value = 'free'
  else if (hash.includes('tab=ai') || hash.includes('#ai')) activeTab.value = 'ai'
  else if (hash.includes('tab=records') || hash.includes('#records')) activeTab.value = 'records'
  // 调用 switchBaziTab 同步DOM（绕过Vue 3.4.21 render effect bug）
  nextTick(() => { switchBaziTab(activeTab.value) })
  // #endif

})
</script>

<style scoped>
/* ═══ 变量体系 ═══ */
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --accent: hsl(38, 60%, 60%); --accent-2: hsl(38, 60%, 48%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-border-hover: rgba(255,255,255,0.18); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --accent: hsl(38, 72%, 30%); --accent-2: hsl(38, 72%, 22%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-border-hover: rgba(0,0,0,0.08); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }

.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }
.page-wrap { position: relative; z-index: 1; }

/* 工具页Hero */
.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.section-tag { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.6875rem; letter-spacing: 2px; color: var(--accent); background: var(--accent-glow); margin-bottom: 12px; }
.tool-hero { padding: 60px 32px 32px; text-align: center; position: relative; overflow: hidden; }
.tool-hero::before { content: ''; position: absolute; top: -50%; left: -20%; width: 140%; height: 200%; background: radial-gradient(ellipse at center, var(--accent-glow) 0%, transparent 70%); opacity: 0.5; pointer-events: none; }
.tool-hero-content { position: relative; z-index: 1; max-width: var(--max-w); margin: 0 auto; }
.tool-hero-title { font-family: var(--font-serif); font-size: 2rem; font-weight: 400; letter-spacing: 4px; color: var(--text-1); margin-bottom: 12px; }
.tool-hero-desc { font-size: 0.9375rem; color: var(--text-3); letter-spacing: 2px; }

/* 工具容器 */
.tool-container { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; backdrop-filter: blur(20px); box-shadow: var(--card-shadow); max-width: 720px; margin: 0 auto; }
.incognito-bar { display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; border-radius: 12px; background: rgba(110,195,135,0.06); border: 1px solid rgba(110,195,135,0.12); margin-bottom: 24px; }
.incognito-toggle { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: var(--success); cursor: pointer; }
.incognito-check { width: 18px; height: 18px; border: 2px solid var(--success); border-radius: 4px; position: relative; transition: all 0.2s; }
.incognito-check.checked { background: var(--success); }
.incognito-check.checked::after { content: '✓'; position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); color: #fff; font-size: 12px; font-weight: bold; }
.dom-input-wrap { width: 100%; }
.dom-input-wrap .native-input { width: 100%; padding: 9px 12px; border: 1.5px solid var(--card-border); border-radius: 10px; font-size: 0.85rem; background: var(--card-bg); color: var(--text-1); outline: none; box-sizing: border-box; }
.checkbox-view { width: 18px; height: 18px; border: 2px solid var(--accent); border-radius: 3px; position: relative; cursor: pointer; transition: all 0.15s; }
.checkbox-view.checked { background: var(--accent); }
.checkbox-view.checked::after { content: '✓'; position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); color: #fff; font-size: 12px; font-weight: bold; }
.incognito-desc { font-size: 0.6875rem; color: var(--success); opacity: 0.7; }
.tool-tabs { display: flex; gap: 4px; margin-bottom: 28px; border-bottom: 1px solid var(--card-border); }
.tool-tab { padding: 12px 20px; border-radius: 10px 10px 0 0; font-size: 0.875rem; cursor: pointer; border: 1px solid transparent; border-bottom: none; color: var(--text-3); background: transparent; }
.tool-tab.active { color: var(--accent); background: var(--accent-glow); border-color: var(--accent); font-weight: 600; }
.tab-badge { font-size: 0.5625rem; padding: 1px 5px; border-radius: 4px; background: var(--accent); color: #fff; margin-left: 4px; }
.tab-badge.free { background: var(--success); }
.tool-tab-content { display: block; }

/* ── 问真风格表单 ── */
.wz-form { padding: 4px 0; }
.wz-form-row { display: flex; gap: 12px; margin-bottom: 14px; }
.wz-form-item { flex: 1; }
.wz-flex-1 { flex: 0 0 90px; }
.wz-flex-2 { flex: 2; }
.wz-flex-3 { flex: 3; }
.wz-form-label { display: block; font-size: 0.78rem; font-weight: 600; color: var(--text-2); margin-bottom: 6px; letter-spacing: 1px; }
.wz-form-input { width: 100%; padding: 9px 12px; border: 1.5px solid var(--card-border); border-radius: 10px; font-size: 0.85rem; background: var(--card-bg); color: var(--text-1); outline: none; box-sizing: border-box; }
.picker-display { line-height: 1.4; cursor: pointer; }
.wz-segment-box { display: flex; gap: 6px; }
.wz-segment-btn { padding: 7px 14px; cursor: pointer; font-size: 0.85rem; font-weight: 500; color: var(--text-2); background: var(--card-bg); border: 1.5px solid var(--card-border); border-radius: 10px; transition: all 0.25s; display: flex; align-items: center; gap: 4px; }
.wz-segment-btn.active { color: #fff; background: var(--accent); border-color: var(--accent); }
.wz-segment-icon { font-size: 0.95rem; }
.wz-divider { border: none; border-top: 1px solid var(--card-border); margin: 14px 0; }
.wz-form-group { margin-bottom: 14px; }
.wz-form-hint { font-size: 0.72rem; color: var(--text-3); margin-top: 6px; line-height: 1.5; }

/* 日期时间行 */
.wz-datetime-row { display: flex; gap: 8px; align-items: center; justify-content: space-between; }
.wz-dt-col { flex: 1; min-width: 0; position: relative; }
.wz-dt-hour { flex: 0.8; }
.wz-dt-minute { flex: 0.7; }
.wz-datetime-select { width: 100%; padding: 9px 6px; border: 1.5px solid var(--card-border); border-radius: 8px; font-size: 0.85rem; font-weight: 500; background: var(--card-bg); color: var(--text-1); cursor: pointer; text-align: center; appearance: none; -webkit-appearance: none; -moz-appearance: none; outline: none; box-sizing: border-box; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath d='M5 7L1 3h8z' fill='%23999'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 4px center; padding-right: 16px; }
.wz-datetime-select:focus { border-color: var(--accent); }

/* 即时起局 */
.wz-instant-row { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
.wz-instant-btn { padding: 7px 16px; border-radius: 10px; background: var(--accent-glow); border: 1.5px solid var(--accent); color: var(--accent); font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.wz-instant-preview { font-size: 0.72rem; color: var(--success); }

/* 四柱输入 */
.wz-sizi-grid { display: flex; flex-direction: column; gap: 10px; }
.wz-sizi-row-item { display: flex; align-items: center; gap: 10px; }
.wz-sizi-label { flex-shrink: 0; width: 40px; font-size: 0.85rem; font-weight: 600; color: var(--text-2); text-align: right; }
.wz-sizi-row-item .dom-input-wrap { flex: 1; }
.wz-sizi-row-item .native-input { text-align: center; padding: 9px 4px; font-size: 0.95rem; letter-spacing: 2px; font-weight: 600; }

/* 地址选择 */
.wz-addr-selects { display: flex; gap: 8px; }
.wz-addr-select { flex: 1; padding: 9px 8px; border: 1.5px solid var(--card-border); border-radius: 10px; font-size: 0.85rem; background: var(--card-bg); color: var(--text-1); cursor: pointer; text-align: center; appearance: none; -webkit-appearance: none; -moz-appearance: none; outline: none; box-sizing: border-box; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath d='M5 7L1 3h8z' fill='%23999'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 4px center; padding-right: 16px; }
.wz-addr-info { margin-top: 8px; display: flex; gap: 16px; font-size: 0.72rem; color: var(--text-3); }
.wz-addr-solar { color: var(--success); }
.wz-addr-lng { color: var(--text-4); }

/* 开关 */
.wz-advanced-box { background: var(--section-alt); border-radius: 12px; padding: 14px 16px; border: 1px solid var(--card-border); }
.wz-switch-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.wz-switch-row { display: flex; align-items: center; gap: 8px; }
.wz-switch-label { font-size: 0.82rem; color: var(--text-2); min-width: 60px; }
.wz-switch { width: 40px; height: 22px; background: var(--card-border); border-radius: 11px; position: relative; cursor: pointer; transition: background 0.3s; }
.wz-switch.active { background: var(--accent); }
.wz-switch-slider { width: 18px; height: 18px; background: #fff; border-radius: 50%; position: absolute; top: 2px; left: 2px; transition: transform 0.3s; }
.wz-switch.active .wz-switch-slider { transform: translateX(18px); }
.wz-switch-hint { font-size: 0.72rem; color: var(--text-3); }

.wz-submit-btn { width: 100%; padding: 14px; border-radius: 30px; border: none; background: hsl(35, 38%, 52%); color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer; letter-spacing: 2px; margin-top: 14px; text-align: center; box-sizing: border-box; }

/* AI tab datetime selects (matches qimen pattern) */
.qf-datetime-row { display: flex; gap: 8px; align-items: center; justify-content: space-between; }
.qf-dt-col { flex: 1; min-width: 0; }
.qf-datetime-select { width: 100%; padding: 9px 6px; border: 1.5px solid var(--card-border); border-radius: 8px; font-size: 0.85rem; font-weight: 500; background: var(--card-bg); color: var(--text-1); cursor: pointer; text-align: center; appearance: none; -webkit-appearance: none; -moz-appearance: none; outline: none; box-sizing: border-box; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath d='M5 7L1 3h8z' fill='%23999'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 4px center; padding-right: 16px; }
.qf-datetime-select:focus { border-color: var(--accent); }

/* 通用表单 */
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 6px; letter-spacing: 1px; }
.form-input, .form-select-picker { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
select.form-select-picker { appearance: none; -webkit-appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M6 8L1 3h10z' fill='%23999'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; padding-right: 32px; cursor: pointer; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.advanced-fields { display: none; margin-top: 12px; padding-top: 12px; border-top: 1px dashed var(--card-border); }
.advanced-fields.show { display: block; }
.advanced-toggle { font-size: 0.75rem; color: var(--text-3); cursor: pointer; border: none; background: none; text-decoration: underline; margin-top: 8px; }
.submit-btn { width: 100%; padding: 14px; border-radius: 30px; border: none; background: hsl(35, 38%, 52%); color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer; letter-spacing: 2px; margin-top: 8px; text-align: center; }
.privacy-note { margin-top: 16px; padding: 10px 14px; border-radius: 10px; background: rgba(110,195,135,0.08); border: 1px solid rgba(110,195,135,0.15); font-size: 0.75rem; color: var(--success); text-align: center; }
.result-mode-switch { display: flex; gap: 8px; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--card-border); }
.result-mode-btn { flex: 1; padding: 8px; border-radius: 8px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.75rem; cursor: pointer; text-align: center; }
.result-mode-btn.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }

/* ── 记录案例（问真风格） ── */
.record-page { background: var(--card-bg); border-radius: 12px; overflow: visible; }
.record-tabs { display: flex; border-bottom: 1px solid var(--card-border); padding: 0 20px; }
.record-tab { padding: 16px 24px; font-size: 15px; color: var(--text-3); cursor: pointer; border-bottom: 2px solid transparent; }
.record-tab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
.record-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; gap: 12px; flex-wrap: wrap; }
.record-search { display: flex; align-items: center; background: var(--input-bg); border-radius: 20px; padding: 4px 4px 4px 14px; flex: 1; max-width: 400px; }
.record-search .dom-input-wrap { flex: 1; }
.record-search .dom-input-wrap .native-input { border: none; background: none; outline: none; padding: 8px 10px; font-size: 14px; flex: 1; color: var(--text-1); }
.search-btn { background: var(--accent); color: #fff; border: none; border-radius: 16px; padding: 8px 20px; font-size: 14px; cursor: pointer; }
.record-actions { display: flex; gap: 4px; }
.action-btn { padding: 8px 14px; font-size: 13px; color: var(--text-3); cursor: pointer; border-radius: 6px; }
.action-btn.active { background: var(--accent); color: #fff; }
.record-categories { display: flex; align-items: center; padding: 0 20px 12px; gap: 10px; }
.cat-label { font-size: 14px; color: var(--text-3); white-space: nowrap; }
.cat-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.cat-tag { padding: 6px 16px; font-size: 13px; color: var(--text-3); background: var(--input-bg); border-radius: 16px; cursor: pointer; }
.cat-tag.active { background: var(--accent); color: #fff; }
.star-section { padding: 0 20px 8px; }
.star-title { font-size: 15px; font-weight: 600; color: var(--text-1); padding: 12px 0 10px; border-top: 1px solid var(--card-border); }
.star-cards { display: flex; flex-wrap: wrap; gap: 12px; }
.batch-bar { display: flex; align-items: center; gap: 16px; padding: 10px 20px; background: var(--section-alt); border-top: 1px solid var(--card-border); border-bottom: 1px solid var(--card-border); }
.batch-select-all { font-size: 14px; color: var(--text-3); cursor: pointer; }
.batch-count { font-size: 14px; color: var(--accent); font-weight: 600; }
.batch-confirm-btn { margin-left: auto; background: #e74c3c; color: #fff; border: none; border-radius: 6px; padding: 6px 16px; font-size: 13px; cursor: pointer; }
.batch-cancel-btn { background: var(--input-bg); color: var(--text-3); border: 1px solid var(--card-border); border-radius: 6px; padding: 6px 16px; font-size: 13px; cursor: pointer; }
.case-cards { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px; padding: 12px 20px 20px; }
.bz-card { width: calc(50% - 6px); background: var(--accent-glow); border-radius: 10px; padding: 16px 18px; position: relative; cursor: pointer; }
.bz-card.starred { background: rgba(178,149,91,0.1); border: 1px solid rgba(178,149,91,0.25); }
.bz-card .sx-icon { position: absolute; top: 12px; left: 14px; width: 28px; height: 28px; font-size: 20px; line-height: 28px; text-align: center; }
.bz-card .card-userinfo { margin-left: 34px; margin-bottom: 10px; }
.bz-card .card-name { font-size: 15px; font-weight: 600; color: var(--text-1); display: flex; align-items: center; gap: 6px; }
.bz-card .card-sex { font-size: 11px; color: var(--text-3); background: var(--input-bg); padding: 1px 6px; border-radius: 4px; }
.bz-card .card-date { font-size: 13px; color: var(--text-3); margin-top: 3px; }
.bz-card .card-gz { display: flex; flex-direction: column; gap: 6px; margin-left: 34px; }
.bz-card .card-gan, .bz-card .card-zhi { display: flex; gap: 10px; }
.bz-card .gz-label { font-size: 14px; font-weight: 700; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; border-radius: 4px; color: var(--accent); }
.bz-card .card-star { position: absolute; right: 12px; top: 14px; font-size: 16px; cursor: pointer; opacity: 0.4; }
.bz-card .card-star.starred { opacity: 1; }
.bz-card .batch-checkbox { position: absolute; left: -4px; top: 14px; width: 18px; height: 18px; }
.record-empty { text-align: center; padding: 60px 20px; }
.empty-icon { font-size: 3rem; margin-bottom: 12px; }
.empty-text { font-size: 16px; color: var(--text-3); margin-bottom: 6px; }
.empty-hint { font-size: 13px; color: var(--text-3); margin-bottom: 16px; }

/* 页脚 */
.site-footer { background: var(--nav-bg); border-top: 1px solid var(--card-border); padding: 48px 32px 24px; margin-top: 80px; }
.footer-disclaimer { max-width: var(--max-w); margin: 0 auto 32px; padding: 14px 20px; border-radius: 10px; background: rgba(215,125,110,0.08); border: 1px solid rgba(215,125,110,0.15); font-size: 0.75rem; color: var(--danger); line-height: 1.6; text-align: center; }
.footer-grid { max-width: var(--max-w); margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 40px; }
.footer-col-title { font-size: 0.8125rem; color: var(--text-2); margin-bottom: 12px; }
.footer-col navigator { display: block; font-size: 0.75rem; color: var(--text-3); text-decoration: none; padding: 3px 0; }
.footer-icp { font-size: 0.6875rem; color: var(--text-3); margin-top: 8px; }
.footer-bottom { max-width: var(--max-w); margin: 24px auto 0; padding-top: 16px; border-top: 1px solid var(--card-border); display: flex; justify-content: space-between; }
.footer-bottom-text { font-size: 0.6875rem; color: var(--text-3); }

/* 弹窗 */
.modal-overlay { display: none; position: fixed; inset: 0; z-index: 300; background: rgba(0,0,0,0.55); backdrop-filter: blur(8px); align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; width: 360px; backdrop-filter: blur(40px); box-shadow: var(--card-shadow); }
.modal-title { font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px; text-align: center; margin-bottom: 24px; color: var(--text-1); }
.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: var(--danger); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }

/* 响应式 */
@media (max-width: 1024px) { .footer-grid { grid-template-columns: 1fr; gap: 24px; } }
@media (max-width: 768px) {
  .tool-hero { padding: 40px 16px 24px; }
  .tool-hero-title { font-size: 1.5rem; }
  .tool-container { padding: 20px 16px; }
  .section { padding: 48px 16px; }
  .wz-form-row { flex-wrap: wrap; }
  .wz-flex-1 { flex: 1 1 100%; }
  .wz-datetime-row { flex-wrap: wrap; }
  .wz-dt-col { flex: 1 1 calc(33% - 8px); min-width: 60px; }
  .wz-addr-selects { flex-wrap: wrap; }
  .wz-switch-grid { grid-template-columns: 1fr; }
  .bz-card { width: 100%; }
  .record-toolbar { flex-direction: column; align-items: stretch; }
  .record-search { max-width: none; }
  .wz-smart-btns { flex-direction: column; }
  .wz-smart-btns .wz-submit-btn { width: 100%; }
}
@media (max-width: 480px) {
  .tool-hero-title { font-size: 1.2rem; }
  .tool-hero-desc { font-size: 0.75rem; }
  .tool-container { padding: 16px 12px; }
  .wz-form-row { flex-direction: row; gap: 8px; }
  .wz-flex-1 { flex: 0 0 70px; }
  .wz-form-input, .dom-input-wrap .native-input { height: 42px; font-size: 0.8125rem; }
  .wz-segment-box { flex-wrap: nowrap; }
  .wz-segment-btn { height: 38px; padding: 6px 12px; white-space: nowrap; font-size: 0.78rem; }
  .wz-dt-col { flex: 1 1 calc(50% - 6px); min-width: 50px; }
  .wz-datetime-select { font-size: 0.78rem; padding: 7px 4px; }
  .wz-addr-selects { flex-direction: column; }
  .wz-switch-grid { grid-template-columns: 1fr 1fr; }
  .submit-btn { font-size: 0.875rem; padding: 12px 16px; }
  .tool-tab { display: inline-flex; align-items: center; padding: 8px 10px; font-size: 0.75rem; }
  .tab-badge { font-size: 0.5rem; padding: 1px 4px; }
  .record-tab { padding: 12px 16px; font-size: 0.8125rem; }
}

/* ═══ 流式解读 + 对话气泡 ═══ */
.qai-stream-box { margin-top: 20px; padding: 16px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 14px; }
.qai-card-item { background: var(--section-alt); border: 1px solid var(--card-border); border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; }
.qai-card-title { font-size: 0.9rem; font-weight: 700; color: var(--accent); margin-bottom: 6px; }
.qai-card-body { font-size: 0.82rem; color: var(--text-2); line-height: 1.7; }
.qai-card-body strong { color: var(--text-1); }
.chat-container { display: flex; flex-direction: column; gap: 12px; }
.chat-bubble-ai { align-self: flex-start; background: var(--section-alt); border: 1px solid var(--card-border); border-radius: 14px 14px 14px 4px; padding: 16px 20px; max-width: 92%; width: 100%; box-sizing: border-box; }
.chat-bubble-user { align-self: flex-end; background: var(--accent); color: #fff; border-radius: 14px 14px 4px 14px; padding: 10px 16px; max-width: 80%; font-size: 0.9rem; line-height: 1.5; }
.chat-bubble-content { font-size: 0.875rem; color: var(--text-2); line-height: 1.9; }
.ai-stage { font-size: 0.9rem; color: var(--text-1); margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
.ai-progress-bar { height: 4px; background: var(--card-border); border-radius: 2px; overflow: hidden; margin-bottom: 16px; }
.ai-progress-fill { height: 100%; width: 20%; background: linear-gradient(90deg, var(--accent), #8b5cf6); border-radius: 2px; animation: ai-progress-pulse 1.5s ease-in-out infinite; transition: width 0.3s ease; }
@keyframes ai-progress-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.chat-input-bar { display: flex; gap: 8px; margin-top: 16px; padding: 10px 14px; background: var(--section-alt); border-radius: 12px; border: 1px solid var(--card-border); }
.chat-input { flex: 1; padding: 8px 14px; border-radius: 8px; border: 1px solid var(--card-border); background: var(--input-bg); color: var(--text-1); font-size: 0.875rem; outline: none; }
.chat-send-btn { padding: 8px 20px; background: var(--accent); color: #fff; border-radius: 8px; font-size: 0.875rem; cursor: pointer; white-space: nowrap; }

.analysis-type-row { display: flex; flex-wrap: wrap; gap: 6px; }
.analysis-type-btn { padding: 6px 12px; border-radius: 8px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.75rem; cursor: pointer; text-align: center; white-space: nowrap; transition: all .15s; }
.analysis-type-btn.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }

</style>
