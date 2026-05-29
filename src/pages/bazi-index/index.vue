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
            </view>
          </view>


          <!-- ══ 八字AI系统（共用免费排盘表单）══ -->
          <view class="tool-tab-content" id="baziTabAiContent" v-show="activeTab === 'ai'">
            <view class="wz-form">
              <view class="wz-form-row">
                <view class="wz-form-item wz-flex-3">
                  <text class="wz-form-label">档案</text>
                  <view class="archive-selector" @tap.stop="toggleArchiveDropdown">
                    <text class="archive-trigger" :class="{ active: archiveOpen }">
                      {{ selectedRecords.length > 0 ? '已选 ' + selectedRecords.length + ' 人' : '点击选择八字记录' }}
                    </text>
                    <text class="archive-arrow">{{ archiveOpen ? '▲' : '▼' }}</text>
                  </view>
                </view>
                <view class="wz-form-item wz-flex-1">
                  <text class="wz-form-label">筛选</text>
                  <view class="archive-selector" @tap.stop="toggleFilterDropdown">
                    <text class="archive-trigger" :class="{ active: filterOpen }">{{ archiveFilter }}</text>
                    <text class="archive-arrow">{{ filterOpen ? '▲' : '▼' }}</text>
                  </view>
                  <view class="filter-dropdown" v-show="filterOpen" @tap.stop>
                    <view class="filter-dropdown-item" :class="{ active: archiveFilter === f }" v-for="f in archiveFilters" :key="f" @tap="archiveFilter = f; filterOpen = false; loadArchiveRecords()">{{ f }}</view>
                  </view>
                </view>
              </view>
              <!-- 档案下拉面板 -->
              <view class="archive-dropdown" v-show="archiveOpen">
                <view class="archive-search"><input class="archive-search-input" v-model="archiveSearch" placeholder="搜索姓名..." @input="filterArchiveList" /></view>
                <view class="archive-list">
                  <view v-for="r in filteredArchive" :key="r.id" class="archive-item" @tap="toggleArchiveRecord(r)">
                    <view class="archive-checkbox" :class="{ checked: archiveRecordIds.includes(r.id) }">{{ archiveRecordIds.includes(r.id) ? '✓' : '' }}</view>
                    <view class="archive-info">
                      <text class="archive-name">{{ r.name || '未命名' }}</text>
                      <text class="archive-gender">{{ r.gender === '男' ? '♂' : '♀' }}</text>
                      <text class="archive-pillars">{{ r.pillars || '' }}</text>
                      <text class="archive-birth">{{ r.birth_time || '' }}</text>
                    </view>
                  </view>
                  <view v-if="filteredArchive.length === 0" class="archive-empty">暂无记录</view>
                </view>
                <view class="archive-actions">
                  <text class="archive-clear-btn" @tap="clearArchiveSelection">清空</text>
                  <text class="archive-confirm-btn" @tap="confirmArchiveSelection">确定 ({{ selectedRecords.length }})</text>
                </view>
              </view>

              <!-- 已选档案显示 -->
              <view class="archive-selected" v-if="selectedRecords.length > 0">
                <view v-for="r in selectedRecords" :key="r.id" class="archive-selected-tag">
                  <text>{{ r.name || '未命名' }} {{ r.gender === '男' ? '♂' : '♀' }}</text>
                  <text class="archive-selected-pillars">{{ r.pillars || '' }}</text>
                  <text class="archive-selected-remove" @tap="removeArchiveRecord(r.id)">✕</text>
                </view>
              </view>

              <view class="wz-divider"></view>

              <!-- 专业排盘结果显示 -->
              <view class="wz-form-group" id="baziPanDisplayAi">
                <text class="wz-form-label">八字排盘数据</text>
                <view class="pan-data-box" id="baziPanDisplayBox" style="min-height:80px;padding:12px;background:var(--card-bg);border:1.5px solid var(--card-border);border-radius:10px;margin-top:8px;font-size:0.85rem;line-height:1.7;">
                  <text v-if="selectedRecords.length === 0 && !panDataAvailable" style="color:var(--text-3);">请从上方档案选择八字记录，或在「八字排盘免费版」排盘后使用此功能。</text>
                  <text v-else-if="selectedRecords.length > 0" style="white-space:pre-wrap;">{{ archivePanSummary }}</text>
                  <text v-else>{{ panSummary }}</text>
                </view>
              </view>

              <view class="wz-divider"></view>
            </view>

            <view class="form-group"><text class="form-label">你的问题</text><view id="baiQuestion-wrap" class="dom-input-wrap"></view></view>
            <view class="submit-btn" data-bz-action="aiAsk">🔮 AI 深度解读</view>
            <view class="qai-stream-box" id="baiStreamBox" style="display:none;">
              <view class="chat-container" id="baiChatContainer"></view>
            </view>
            <view class="chat-input-bar" id="baiChatInputBar" style="display:none;">
              <input class="chat-input" id="baiChatInput" placeholder="继续追问..." />
              <view class="chat-send-btn" style="margin-right:6px;" data-bz-action="aiNewQuestion">新问题</view>
              <view class="chat-send-btn" data-bz-action="aiFollowUp">发送</view>
            </view>
          </view>

          <!-- ══ 排盘记录 ══ -->
          <view class="tool-tab-content" v-show="activeTab === 'records'">
            <view class="record-page">
              <!-- 1. 顶部Tab切换 -->
              <view class="record-tabs">
                <view id="baziRecordPaipan" class="record-tab" :class="{ active: recordTab === 'paipan' }" @tap="switchRecordTab('paipan')">排盘案例</view>
                <view id="baziRecordHepan" class="record-tab" :class="{ active: recordTab === 'hepan' }" @tap="switchRecordTab('hepan')">合盘案例</view>
              </view>

              <!-- 2. 工具栏 -->
              <view class="record-toolbar">
                <view class="record-search">
                  <view id="recordSearch-wrap" class="dom-input-wrap"></view>
                  <view class="search-btn" @tap="onRecordSearch">搜索</view>
                </view>
                <view class="record-actions">
                  <view class="action-btn" :class="{ disabled: !batchMode || selectedIds.length === 0 }" @tap="batchMode ? (moveGroupModal = true) : null">📁 移动分组</view>
                  <view class="action-btn" :class="{ active: showStarSection }" @tap="showStarSection = !showStarSection">⭐ 星标</view>
                  <view id="baziBatchToggle" class="action-btn" :class="{ active: batchMode }" @tap="toggleBatchDelete">{{ batchMode ? '退出批量' : '批量' }}</view>
                  <view class="action-btn action-btn-ai" @tap="sendRecordsBatchToAi">🔮 发AI</view>
                </view>
              </view>

              <view class="record-filter-row">
                <text class="record-filter-label">筛选</text>
                <view class="record-filter-tag" :class="{ active: catFilter === '全部' }" @tap="catFilter = '全部'">全部</view>
                <view class="record-filter-tag" :class="{ active: catFilter === '客户' }" @tap="catFilter = '客户'">客户</view>
                <view class="record-filter-tag" :class="{ active: catFilter === '名人' }" @tap="catFilter = '名人'">名人</view>
                <view class="record-filter-tag" :class="{ active: catFilter === '亲友' }" @tap="catFilter = '亲友'">亲友</view>
              </view>

              <!-- 5. 星标八字区（可折叠） -->
              <view class="star-section" v-if="starredRecords.length > 0 && showStarSection">
                <view class="star-title" @tap="showStarSection = !showStarSection">⭐ 星标八字 <text class="star-toggle">{{ showStarSection ? '▾' : '▸' }}</text></view>
                <view class="star-cards" v-show="showStarSection">
                  <view class="bz-card" :class="{ starred: true, pinned: r.pinned }" v-for="r in starredRecords" :key="'star-'+r.id" @tap="viewRecord(r)" @contextmenu.prevent="showRecordMenu($event, r)">
                    <view class="card-avatar">{{ getZodiacEmoji(r) }}</view>
                    <view class="card-userinfo">
                      <view class="card-name">{{ r.name || '未命名' }}<text class="card-sex">{{ r.gender }}</text><text class="card-star-badge" v-if="r.starred">★</text><text class="card-pin-badge" v-if="r.pinned">📌</text></view>
                      <view class="card-date">{{ r.dateStr }}</view>
                    </view>
                    <view class="card-gz" v-if="r.ganArr && r.ganArr.length">
                      <view class="gz-col" v-for="(g, i) in r.ganArr" :key="'sg'+i">
                        <text class="gz-circle" :style="{ backgroundColor: wxColor(g) }">{{ g }}</text>
                        <text class="gz-circle gz-zhi" :style="{ backgroundColor: wxColor(r.zhiArr[i]) }">{{ r.zhiArr[i] }}</text>
                      </view>
                    </view>
                    <view class="card-gz card-gz-empty" v-else>
                      <text class="gz-circle gz-placeholder">?</text>
                    </view>
                    <view class="card-ops" :data-ops-id="'ops-'+r.id" @tap.stop="showRecordMenu($event, r)">
                      <text class="ops-dots">⋮</text>
                    </view>
                  </view>
                </view>
              </view>

              <!-- 6. 批量操作栏 -->
              <view class="batch-bar" v-if="batchMode">
                <label class="batch-select-all" @tap="toggleSelectAll">
                  <text>{{ selectAll ? '☑' : '☐' }} 全选</text>
                </label>
                <text class="batch-count">已选 {{ selectedIds.length }} 项</text>
                <view class="batch-move-btn" @tap="moveGroupModal = true">📁 移动分组</view>
                <view class="batch-ai-btn" @tap="sendRecordsBatchToAi">🔮 发送AI</view>
                <view class="batch-confirm-btn" @tap="confirmBatchDelete">删除</view>
                <view class="batch-cancel-btn" @tap="cancelBatchDelete">取消</view>
              </view>

              <!-- 7. 案例列表 -->
              <view class="case-cards" v-if="filteredRecords.length > 0">
                <view class="bz-card" :class="{ pinned: r.pinned }" v-for="(r, idx) in filteredRecords" :key="r.id" @tap="batchMode ? toggleSelectId(r.id) : viewRecord(r)" @contextmenu.prevent="showRecordMenu($event, r)">
                  <view class="batch-checkbox" v-if="batchMode">
                    <view class="checkbox-view" :class="{ checked: selectedIds.includes(r.id) }"></view>
                  </view>
                  <view class="card-avatar">{{ getZodiacEmoji(r) }}</view>
                  <view class="card-userinfo">
                    <view class="card-name">{{ r.name || '未命名' }}<text class="card-sex">{{ r.gender }}</text><text class="card-star-badge" v-if="r.starred">★</text><text class="card-pin-badge" v-if="r.pinned">📌</text></view>
                    <view class="card-date">{{ r.dateStr }}</view>
                  </view>
                  <view class="card-gz" v-if="r.ganArr && r.ganArr.length">
                    <view class="gz-col" v-for="(g, i) in r.ganArr" :key="'g'+i">
                      <text class="gz-circle" :style="{ backgroundColor: wxColor(g) }">{{ g }}</text>
                      <text class="gz-circle gz-zhi" :style="{ backgroundColor: wxColor(r.zhiArr[i]) }">{{ r.zhiArr[i] }}</text>
                    </view>
                  </view>
                  <view class="card-gz card-gz-empty" v-else>
                    <text class="gz-circle gz-placeholder">?</text>
                  </view>
                  <view class="card-ops" :data-ops-id="'ops-'+r.id" @tap.stop="showRecordMenu($event, r)">
                    <text class="ops-dots">⋮</text>
                  </view>
                </view>
              </view>

              <!-- 8. 空状态 -->
              <view class="record-empty" v-if="filteredRecords.length === 0">
                <text class="empty-icon">📋</text>
                <view class="empty-text">暂无排盘记录</view>
                <view class="empty-hint">排一盘试试吧，记录会自动保存在这里</view>
                <view class="btn btn-accent btn-sm" @tap="activeTab = 'free'">去排盘</view>
              </view>
            </view>



            <!-- 移动分组弹窗 -->
            <view class="modal-overlay" :class="{ open: moveGroupModal }" @tap="moveGroupModal = false">
              <view class="modal-box" @tap.stop>
                <view class="modal-title">移动到分组</view>
                <view class="move-group-list">
                  <view class="move-group-item" @tap="batchMoveToGroup('全部')">📁 全部</view>
                  <view class="move-group-item" @tap="batchMoveToGroup('客户')">👤 客户</view>
                  <view class="move-group-item" @tap="batchMoveToGroup('名人')">🌟 名人</view>
                  <view class="move-group-item" @tap="batchMoveToGroup('亲友')">❤️ 亲友</view>
                </view>
                <view class="modal-btns">
                  <view class="btn btn-ghost" @tap="moveGroupModal = false">取消</view>
                </view>
              </view>
            </view>
          </view>
        </view>
      </section>
    </view>

    <view class="menu-overlay" v-if="recordContextMenu.show" @tap="hideRecordMenu()"></view>
    <view class="record-ctx-menu" v-if="recordContextMenu.show" :style="{ left: recordContextMenu.x + 'px', top: recordContextMenu.y + 'px' }" @tap.stop>
      <view class="ctx-menu-item" @tap="editRecord(recordContextMenu.record)">✏️ 编辑</view>
      <view class="ctx-menu-item" @tap="togglePin(recordContextMenu.record); hideRecordMenu()">{{ recordContextMenu.record && recordContextMenu.record.pinned ? '📌 取消置顶' : '📌 置顶' }}</view>
      <view class="ctx-menu-item" @tap="sendToAiFromMenu(recordContextMenu.record)">🔮 发AI解读</view>
      <view class="ctx-menu-divider"></view>
      <view class="ctx-menu-item ctx-danger" @tap="deleteRecordFromMenu(recordContextMenu.record)">🗑️ 删除</view>
    </view>

  </view>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'

// ── 全局变量 ──
var _cityData = null

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
  
  // 同时更新 AI Tab 的 select
  var yElAi = document.getElementById('baziYearAi'); if (yElAi) yElAi.value = year
  var mElAi = document.getElementById('baziMonthAi'); if (mElAi) mElAi.value = month
  var dElAi = document.getElementById('baziDayAi'); if (dElAi) dElAi.value = day
  var hElAi = document.getElementById('baziHourAi'); if (hElAi) hElAi.value = hour
  var miElAi = document.getElementById('baziMinuteAi'); if (miElAi) miElAi.value = minute

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
    // 保存排盘结果，供时安八字系统AI解读使用
    if (res.data) window.__lastBaziPanData = res.data
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
const baiDate = ref(''); const baiHourIdx = ref(12); const baiMinuteIdx = ref(0); const baiSecondIdx = ref(0); const baiAddr = ref('')
const baiAnalysisTypeIdx = ref(0)
const baiAnalysisTypes = ['general', 'career', 'marriage', 'decadal', 'family']
const baiAdvanced = ref(false)
const baiAiLoading = ref(false); const baziAiResult = ref('')
const panDataAvailable = computed(function() { return !!(window.__lastBaziPanData && window.__lastBaziPanData.success) })
const panSummary = computed(function() {
  var d = window.__lastBaziPanData
  if (!d || !d.success) return ''
  var fp = d.four_pillars || {}
  var yz = fp.year ? (fp.year.gan||'') + (fp.year.zhi||'') : ''
  var mz = fp.month ? (fp.month.gan||'') + (fp.month.zhi||'') : ''
  var dz = fp.day ? (fp.day.gan||'') + (fp.day.zhi||'') : ''
  var hz = fp.hour ? (fp.hour.gan||'') + (fp.hour.zhi||'') : ''
  var dayGan = fp.day ? (fp.day.gan||'') : ''
  var wx = d.wu_xing || ''
  var lack = d.lack_wuxing ? d.lack_wuxing.join(',') : '无'
  return '出生: ' + (d.birth_solar||'') + '  性别: ' + (d.gender||'') + '\n四柱: ' + yz + ' ' + mz + ' ' + dz + ' ' + hz + '\n日主: ' + dayGan + '  五行: ' + wx + '  所缺: ' + lack
})
// 档案（八字记录选择）
const archiveOpen = ref(false)
const archiveFilter = ref('全部')
const archiveFilters = ['全部', '客户', '名人', '亲友']
const filterOpen = ref(false)
const archiveSearch = ref('')
const archiveRecords = ref([])
const filteredArchive = ref([])
const archiveRecordIds = ref([])
const selectedRecords = ref([])
const archivePanSummary = computed(function() {
  var lines = []
  for (var i = 0; i < selectedRecords.value.length; i++) {
    var r = selectedRecords.value[i]
    lines.push('【命主' + (i+1) + '】' + (r.name||'未命名') + ' ' + (r.gender === '男' ? '♂' : '♀') + '\n  出生: ' + (r.birth_time||'') + '  四柱: ' + (r.pillars||''))
  }
  return lines.join('\n')
})
const shichenLabels = ['不确定', '子时 (23-1)', '丑时 (1-3)', '寅时 (3-5)', '卯时 (5-7)', '辰时 (7-9)', '巳时 (9-11)', '午时 (11-13)', '未时 (13-15)', '申时 (15-17)', '酉时 (17-19)', '戌时 (19-21)', '亥时 (21-23)']
window._baiChatHistory = []

var _baiCurrentConvId = null

// ── 档案（八字记录多选）──
function loadArchiveRecords() {
  var cat = archiveFilter.value
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  if (!token) { uni.showToast({ title: '请先登录', icon: 'none' }); return }
  uni.request({
    url: '/api/bazi/history', method: 'GET',
    header: token ? { 'Authorization': 'Bearer ' + token } : {},
    success: function(res) {
      var list = []
      if (res.statusCode === 401) { uni.showToast({ title: '请先登录', icon: 'none' }); return }
      if (res.data && Array.isArray(res.data)) list = res.data
      else if (res.data && res.data.success && Array.isArray(res.data.history)) list = res.data.history
      if (cat !== '全部') list = list.filter(function(r) { return r.category === cat })
      archiveRecords.value = list
      filterArchiveList()
    },
    fail: function() { uni.showToast({ title: '加载档案失败', icon: 'none' }) }
  })
}
function filterArchiveList() {
  var q = (archiveSearch.value || '').toLowerCase()
  var list = archiveRecords.value.filter(function(r) { return !q || (r.name || '').toLowerCase().includes(q) })
  filteredArchive.value = list
}
function _bzApplyFrost(el) {
  if (!el || window.innerWidth > 768) return
  var parent = el.parentElement
  if (parent && parent !== document.body) {
    el._bz_origParent = parent
    el._bz_origNext = el.nextElementSibling
    document.body.appendChild(el)
  }
  el.style.setProperty('position', 'fixed', 'important')
  el.style.setProperty('background', 'rgba(255,255,255,0.65)', 'important')
  el.style.setProperty('border-color', 'rgba(255,255,255,0.3)', 'important')
  el.style.setProperty('border-radius', '20px', 'important')
  el.style.setProperty('box-shadow', '0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.4)', 'important')
  el.style.setProperty('-webkit-backdrop-filter', 'blur(20px) saturate(180%)', 'important')
  el.style.setProperty('backdrop-filter', 'blur(20px) saturate(180%)', 'important')
  el.style.setProperty('z-index', '9999', 'important')
  el.style.setProperty('padding', '6px 0', 'important')
  el.style.setProperty('color', '#333', 'important')
  el.style.setProperty('visibility', 'visible', 'important')
  el.style.setProperty('opacity', '1', 'important')
  el.style.setProperty('pointer-events', 'auto', 'important')

  var trigger = null
  if (el._bz_origParent) {
    trigger = el._bz_origParent.querySelector('.archive-selector')
  }
  if (trigger) {
    var rect = trigger.getBoundingClientRect()
    el.style.setProperty('top', (rect.bottom + 8) + 'px', 'important')
    el.style.setProperty('left', rect.left + 'px', 'important')
    el.style.setProperty('right', 'auto', 'important')
    el.style.setProperty('transform', 'translateZ(0)', 'important')
  } else {
    el.style.setProperty('top', '120px', 'important')
    el.style.setProperty('left', '50%', 'important')
    el.style.setProperty('right', 'auto', 'important')
    el.style.setProperty('transform', 'translateX(-50%) translateZ(0)', 'important')
  }
}
function _bzRestoreMenu(el) {
  if (!el) return
  el.style.removeProperty('position')
  el.style.removeProperty('top')
  el.style.removeProperty('left')
  el.style.removeProperty('right')
  el.style.removeProperty('transform')
  el.style.removeProperty('background')
  el.style.removeProperty('border-color')
  el.style.removeProperty('border-radius')
  el.style.removeProperty('box-shadow')
  el.style.removeProperty('-webkit-backdrop-filter')
  el.style.removeProperty('backdrop-filter')
  el.style.removeProperty('z-index')
  el.style.removeProperty('padding')
  el.style.removeProperty('color')
  el.style.removeProperty('visibility')
  el.style.removeProperty('opacity')
  el.style.removeProperty('pointer-events')
  if (el._bz_origParent) {
    var origParent = el._bz_origParent
    var origNext = el._bz_origNext
    if (origNext && origNext.parentElement === origParent) {
      origParent.insertBefore(el, origNext)
    } else {
      origParent.appendChild(el)
    }
    el._bz_origParent = null
    el._bz_origNext = null
  }
}
function toggleArchiveDropdown() {
  if (archiveOpen.value) {
    archiveOpen.value = false
    var dd = document.querySelector('.archive-dropdown')
    if (dd && dd._bz_origParent) _bzRestoreMenu(dd)
    return
  }
  archiveOpen.value = true
  filterOpen.value = false
  var fd = document.querySelector('.filter-dropdown')
  if (fd && fd._bz_origParent) _bzRestoreMenu(fd)
  if (archiveRecords.value.length === 0) loadArchiveRecords()
  nextTick(function() {
    var dd = document.querySelector('.archive-dropdown')
    if (dd) _bzApplyFrost(dd)
  })
}
function toggleFilterDropdown() {
  if (filterOpen.value) {
    filterOpen.value = false
    var dd = document.querySelector('.filter-dropdown')
    if (dd && dd._bz_origParent) _bzRestoreMenu(dd)
    return
  }
  filterOpen.value = true
  archiveOpen.value = false
  var ad = document.querySelector('.archive-dropdown')
  if (ad && ad._bz_origParent) _bzRestoreMenu(ad)
  nextTick(function() {
    var dd = document.querySelector('.filter-dropdown')
    if (dd) _bzApplyFrost(dd)
  })
}
function toggleArchiveRecord(r) {
  var idx = archiveRecordIds.value.indexOf(r.id)
  if (idx >= 0) archiveRecordIds.value.splice(idx, 1)
  else archiveRecordIds.value.push(r.id)
}
function removeArchiveRecord(id) {
  var idx = archiveRecordIds.value.indexOf(id)
  if (idx >= 0) archiveRecordIds.value.splice(idx, 1)
  selectedRecords.value = selectedRecords.value.filter(function(r) { return r.id !== id })
}
function clearArchiveSelection() {
  archiveRecordIds.value = []
  selectedRecords.value = []
}
function confirmArchiveSelection() {
  var ids = archiveRecordIds.value
  var list = archiveRecords.value.filter(function(r) { return ids.indexOf(r.id) >= 0 })
  selectedRecords.value = list
  archiveOpen.value = false
  // 清除旧排盘缓存以免混淆
  delete window.__lastBaziPanData
}

function _saveBaziConversation(question, birthData) {
  var title = (question || '八字AI解读').substring(0, 50)
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  fetch('/api/bazi/conversations', {
    method: 'POST',
    headers: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    body: JSON.stringify({
      title: title,
      messages: window._baiChatHistory || [],
      birth_data: birthData || {}
    })
  }).then(function(r) { return r.json() }).then(function(data) {
    if (data && data.id) _baiCurrentConvId = data.id
    window.__sidebarCache = null
    if (window._xc_refreshSidebar) window._xc_refreshSidebar()
  }).catch(function(err) { console.error('[bazi] 保存对话失败:', err) })
}

function _updateBaziConversation() {
  if (!_baiCurrentConvId) return
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  fetch('/api/bazi/conversations', {
    method: 'POST',
    headers: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    body: JSON.stringify({ id: _baiCurrentConvId, messages: window._baiChatHistory || [] })
  }).then(function() { window.__sidebarCache = null }).catch(function(err) { console.error('[bazi] 更新对话失败:', err) })
}

function _checkBaziRestore() {
  var d = window.__xc_restoreData
  if (!d || d.type !== 'bazi') return
  window.__xc_restoreData = null
  switchBaziTab('ai')
  function doRestore() {
    var aiPanel = document.getElementById('baziTabAiContent')
    if (!aiPanel || getComputedStyle(aiPanel).display === 'none') return false
    var streamBox = document.getElementById('baiStreamBox')
    if (streamBox) streamBox.style.display = ''
    var chatContainer = document.getElementById('baiChatContainer')
    var inputBar = document.getElementById('baiChatInputBar')
    if (!chatContainer) return false
    chatContainer.innerHTML = ''
    if (d.rawHtml) {
      if (d.question) {
        var ub = document.createElement('view')
        ub.className = 'chat-bubble-user'
        ub.textContent = d.question
        chatContainer.appendChild(ub)
      }
      var ab = document.createElement('view')
      ab.className = 'chat-bubble-ai'
      ab.innerHTML = '<div class="chat-bubble-content">' + _baiRenderCards(d.rawHtml) + '</div>'
      chatContainer.appendChild(ab)
      window._baiChatHistory = [
        { role: 'user', content: d.question || '' },
        { role: 'assistant', content: d.rawHtml.replace(/<[^>]+>/g, '').substring(0, 200) }
      ]
      _baiCurrentConvId = null
    } else {
      var messages = d.messages || []
      window._baiChatHistory = messages.slice()
      _baiCurrentConvId = d.id || null
      messages.forEach(function(m) {
        if (m.role === 'user') {
          var ub = document.createElement('view')
          ub.className = 'chat-bubble-user'
          ub.textContent = m.content
          chatContainer.appendChild(ub)
        } else if (m.role === 'assistant') {
          var ab = document.createElement('view')
          ab.className = 'chat-bubble-ai'
          ab.innerHTML = '<div class="chat-bubble-content">' + _baiRenderCards(m.content) + '</div>'
          chatContainer.appendChild(ab)
        }
      })
    }
    if (inputBar) inputBar.style.display = 'flex'
    var askBtn = document.querySelector('[data-bz-action="aiAsk"]'); if (askBtn) askBtn.style.display = 'none'
    setTimeout(function() {
      var el = document.getElementById('baiChatInputBar')
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 150)
    return true
  }
  if (!doRestore()) {
    setTimeout(doRestore, 200)
    setTimeout(doRestore, 500)
    setTimeout(doRestore, 1000)
  }
}

window._xc_restoreBazi = function() {
  nextTick(function() { _checkBaziRestore() })
}
setInterval(function() {
  var rd = window.__xc_restoreData
  if (rd && rd.type === 'bazi') _checkBaziRestore()
}, 500)
window._baiAiAsk = baiAiAsk

async function baiAiAsk() {
  if (baiAiLoading.value) return

  var question = ((document.getElementById('baiQuestion') || {}).value || '').trim()
  if (!question) { baiAiLoading.value = false; uni.showToast({ title: '请输入您想问的问题', icon: 'none' }); return }

  // 决定数据来源：优先用档案（多选），其次用免费排盘的缓存
  var useArchive = selectedRecords.value.length > 0
  var useSinglePan = !useArchive && window.__lastBaziPanData && window.__lastBaziPanData.success

  if (!useArchive && !useSinglePan) {
    baiAiLoading.value = false
    uni.showToast({ title: '请先在档案选择八字记录，或在八字排盘免费版排盘', icon: 'none' })
    return
  }

  var bodyData = { question: question, analysis_type: baiAnalysisTypes[baiAnalysisTypeIdx] }

  if (useArchive) {
    bodyData.record_ids = selectedRecords.value.map(function(r) { return r.id })
    var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
    if (token) bodyData.token = token
  } else {
    var panData = window.__lastBaziPanData
    var birthSolar = panData.birth_solar || ''
    bodyData.pan_data = panData
    bodyData.gender = panData.gender || '男'
    bodyData.birth = birthSolar.replace(/[- ]/g, '').substring(0, 12) || '199001011200'
    bodyData.cal_type = '公历'
  }

  // 清理 — 先设 loading
  baiAiLoading.value = true
  baziAiResult.value = ''; window._baiChatHistory = []
  var streamBox = document.getElementById('baiStreamBox')
  if (streamBox) streamBox.style.display = 'block'
  var chatContainer = document.getElementById('baiChatContainer')
  if (chatContainer) chatContainer.innerHTML = ''
  var inputBar = document.getElementById('baiChatInputBar')
  if (inputBar) { inputBar.style.display = 'none'; var ci = document.getElementById('baiChatInput'); if (ci) ci.value = '' }
  var askBtn = document.querySelector('[data-bz-action="aiAsk"]'); if (askBtn) askBtn.style.display = 'inline-flex'

  var bubbleId = 'baiBubble_' + Date.now()
  var bubbleHTML = '<div class="chat-bubble-ai" id="' + bubbleId + '">' +
    '<div class="ai-stage" id="baiStage"><img class="ai-stage-logo" id="baiStageLogo" src="/static/images/logo.webp?v=2"><span id="baiStageText">排盘准备中</span></div>' +
    '<div class="ai-progress-bar"><div class="ai-progress-fill" id="baiProgressFill" style="width:8%"></div></div>' +
    '<div class="chat-bubble-content"></div></div>'
  if (chatContainer) chatContainer.innerHTML = bubbleHTML

  var stages = ['加载命理数据库...', '计算四柱八字...', '分析五行生克...', '推演大运流年...', '调用AI引擎...', '生成深度解读...']
  var stageIdx = 0
  var progFill = document.getElementById('baiProgressFill')
  var stageText = document.getElementById('baiStageText')
  var progTimer = setInterval(function() {
    if (!progFill) return
    var w = parseFloat(progFill.style.width) || 8
    if (w < 70) progFill.style.width = Math.min(w + 2.5, 70) + '%'
  }, 300)
  var stageTimer = setInterval(function() {
    if (stageIdx < stages.length - 1) {
      stageIdx++
      if (stageText) stageText.textContent = stages[stageIdx]
    } else {
      clearInterval(stageTimer)
    }
  }, 2000)
  setTimeout(function() { stageIdx = Math.max(stageIdx, 2); if (stageText) stageText.textContent = stages[stageIdx] }, 6000)

  try {
    var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
    var resp = await fetch('/api/bazi/ask/stream', {
      method: 'POST',
      headers: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
      body: JSON.stringify(bodyData)
    })
    if (!resp.ok) { clearInterval(progTimer); clearInterval(stageTimer); baiAiLoading.value = false; uni.showToast({ title: '请求失败 ' + resp.status, icon: 'none' }); return }
    var text = await resp.text()
    if (!text) { clearInterval(progTimer); clearInterval(stageTimer); baiAiLoading.value = false; uni.showToast({ title: '响应为空', icon: 'none' }); return }
    var lines = text.split('\n')
    var charQueue = '', fullText = '', doneReceived = false
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i]
      if (line.indexOf('data:') !== 0) continue
      try {
        var data = JSON.parse(line.replace('data:', '').trim())
        if (data.type === 'chunk' || data.type === 'delta') { charQueue += data.content }
        else if (data.type === 'done') { doneReceived = true }
      } catch(_) {}
    }
    startBaziTypewriter(bubbleId, charQueue, function(finalText) {
      clearInterval(progTimer); clearInterval(stageTimer)
      if (progFill) progFill.style.width = '100%'
      if (stageText) stageText.textContent = '✅ 解读完成'
      window._baiChatHistory = [{ role: 'user', content: question }, { role: 'assistant', content: finalText }]
      baziAiResult.value = finalText
      var bar = document.getElementById('baiChatInputBar'); if (bar) bar.style.display = 'flex'
      var askBtn = document.querySelector('[data-bz-action="aiAsk"]'); if (askBtn) askBtn.style.display = 'none'
      _baiCurrentConvId = null
      _saveBaziConversation(question, { birth: '', gender: '', cal_type: '公历', analysis_type: baiAnalysisTypes[baiAnalysisTypeIdx] })
    }, doneReceived)
  } catch(e) {
    console.error('[bazi] fetch error:', e)
    baiAiLoading.value = false
    uni.showToast({ title: '网络异常', icon: 'none' })
  }
}

function startBaziTypewriter(bubbleId, text, onDone, doneReceived) {
  var bubble = document.getElementById(bubbleId); if (!bubble) { console.error('[bazi] bubble not found'); return }
  var stageEl = bubble.querySelector('.ai-stage'); var contentEl = bubble.querySelector('.chat-bubble-content')
  var fullText = '', charQueue = text || '', pos = 0, timer = null
  function tick() {
    if (pos >= charQueue.length && doneReceived) {
      clearInterval(timer); timer = null
      baiAiLoading.value = false
      if (stageEl) stageEl.style.display = 'none'
      var barWrap = bubble.querySelector('.ai-progress-bar'); if (barWrap) barWrap.style.display = 'none'
      if (contentEl) contentEl.innerHTML = _baiRenderCards(fullText)
      if (onDone) onDone(fullText); return
    }
    if (pos >= charQueue.length) return
    var take = (charQueue.length - pos) > 3 ? 2 : 1
    fullText += charQueue.substring(pos, pos + take); pos += take
    if (contentEl) contentEl.innerHTML = _stripMarkdown(fullText).replace(/\n/g, '<br>')
  }
  if (charQueue.length > 0) timer = setInterval(tick, 35)
}

function _stripMarkdown(s) {
  if (!s) return ''
  return s.replace(/^#{1,6}\s*/gm, '').replace(/\*\*/g, '').replace(/^[-*]\s+/gm, '')
}

function _baiRenderCards(text) {
  text = _stripMarkdown(text)
  var sections = text.split(/\n(?=#{2,} |\d+\.\s+\*\*)/)
  var html = ''
  sections.forEach(function(sec) {
    var title = ''
    var body = sec
    var m = sec.match(/^(#{2,})\s+(.+)/)
    if (m) { title = m[2]; body = sec.substring(m[0].length).trim() }
    else {
      var m2 = sec.match(/^(\d+\.)\s+\*\*(.+?)\*\*[：:]\s*/)
      if (m2) { title = m2[2]; body = sec.substring(m2[0].length).trim() }
    }
    body = body.replace(/\*\*(.+?)\*\*/g, '$1').replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')
    if (!body) body = '&nbsp;'
    if (title) { html += '<div class="qai-card-item"><div class="qai-card-title">' + title + '</div><div class="qai-card-body"><p>' + body + '</p></div></div>' }
    else { html += '<div class="qai-card-item"><div class="qai-card-body"><p>' + body + '</p></div></div>' }
  })
  return html
}

async function baiSendFollowUp() {
  var input = document.querySelector('#baiChatInput input') || document.getElementById('baiChatInput'); if (!input) return
  var question = input.value.trim(); if (!question) return; input.value = ''
  var chatContainer = document.getElementById('baiChatContainer'); if (!chatContainer) return
  var userBubble = document.createElement('div'); userBubble.className = 'chat-bubble-user'; userBubble.textContent = question
  chatContainer.appendChild(userBubble)
  var bubbleId = 'baiFollow_' + Date.now()
  var aiBubble = document.createElement('div'); aiBubble.className = 'chat-bubble-ai'; aiBubble.id = bubbleId
  aiBubble.innerHTML = '<div class="ai-stage"><img class="ai-stage-logo" src="/static/images/logo.webp?v=2"><span>AI思考中...</span></div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:10%"></div></div><div class="chat-bubble-content"></div>'
  chatContainer.appendChild(aiBubble); chatContainer.scrollIntoView({ behavior: 'smooth', block: 'end' })
  var history = window._baiChatHistory || []; history.push({ role: 'user', content: question })
  var followProg = aiBubble.querySelector('.ai-progress-fill')
  var followTimer = setInterval(function() {
    if (!followProg) return
    var w = parseFloat(followProg.style.width) || 10
    if (w < 75) followProg.style.width = Math.min(w + 1.8, 75) + '%'
  }, 400)
  try {
    var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
    var bd = window._baziInitBirthData || {}
    var resp = await fetch('/api/bazi/ask/stream', {
      method: 'POST',
      headers: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
      body: JSON.stringify(Object.assign({ question: question, history: history }, bd))
    })
    if (!resp.ok) return
    var text = await resp.text()
    if (!text) return
    var lines = text.split('\n'), charQueue = '', doneReceived = false
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i]
      if (line.indexOf('data:') !== 0) continue
      try {
        var data = JSON.parse(line.replace('data:', '').trim())
        if (data.type === 'chunk' || data.type === 'delta') { charQueue += data.content }
        else if (data.type === 'done') { doneReceived = true }
      } catch(_) {}
    }
    startBaziTypewriter(bubbleId, charQueue, function(finalText) {
      clearInterval(followTimer)
      if (followProg) followProg.style.width = '100%'
      history.push({ role: 'assistant', content: finalText }); window._baiChatHistory = history
      if (_baiCurrentConvId) { _updateBaziConversation() } else { _saveBaziConversation(question, {}) }
    }, doneReceived)
  } catch(e) { console.error('[bazi] followup error:', e) }
}
window._baiSendFollowUp = baiSendFollowUp

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
const showStarSection = ref(true)
const filterDropdownOpen = ref(false)
const moveGroupModal = ref(false)
const records = ref([])
const starredRecords = computed(() => records.value.filter(r => r.starred))
const filteredRecords = computed(() => {
  let list = records.value
  const searchEl = document.getElementById('recordSearch')
  const searchVal = searchEl ? searchEl.value : recordSearch.value
  if (catFilter.value !== '全部') list = list.filter(r => r.category === catFilter.value)
  if (searchVal) { const q = searchVal.toLowerCase(); list = list.filter(r => (r.name || '').toLowerCase().includes(q)) }
  return list
})

function onRecordSearch() {
  const el = document.getElementById('recordSearch')
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
function confirmBatchDelete() {
  var ids = selectedIds.value.slice()
  if (ids.length === 0) { batchMode.value = false; return }
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  uni.request({
    url: '/api/bazi/history/batch-delete', method: 'POST',
    header: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    data: JSON.stringify({ ids: ids }),
    success: function(res) {
      if (res.data && res.data.success) {
        records.value = records.value.filter(function(r) { return ids.indexOf(r.id) < 0 })
        uni.showToast({ title: '已删除 ' + ids.length + ' 条', icon: 'none' })
      } else {
        uni.showToast({ title: '删除失败', icon: 'none' })
      }
    },
    fail: function() { uni.showToast({ title: '网络错误', icon: 'none' }) }
  })
  batchMode.value = false; selectedIds.value = []
}
function cancelBatchDelete() { batchMode.value = false; selectedIds.value = [] }
function toggleStar(r) {
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  uni.request({
    url: '/api/bazi/history/star', method: 'POST',
    header: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    data: JSON.stringify({ id: r.id }),
    success: function(res) {
      if (res.data && res.data.success) {
        r.starred = res.data.starred
      }
    },
    fail: function() { r.starred = !r.starred }
  })
}
function viewRecord(r) {
  try { sessionStorage.removeItem('xc_bazi_params') } catch(_) {}
  var bt = r.birth_time || ''
  var q = '?y=' + bt.substring(0,4)
  q += '&m=' + bt.substring(4,6)
  q += '&d=' + bt.substring(6,8)
  q += '&h=' + bt.substring(8,10)
  q += '&mi=' + bt.substring(10,12)
  q += '&s=' + (r.gender === '女' ? 2 : 1)
  if (r.cal_type && r.cal_type !== '公历') q += '&cal=' + encodeURIComponent(r.cal_type)
  uni.navigateTo({ url: '/pages/bazi-result/index' + q })
}

var WX_CARD = {
  '甲':'#07e930','乙':'#1dcc36','丙':'#d30505','丁':'#e02a2a','戊':'#8b6d03','己':'#a07d10',
  '庚':'#ef9104','辛':'#d4860a','壬':'#2e83f6','癸':'#4a96f0',
  '子':'#2e83f6','丑':'#a07d10','寅':'#07e930','卯':'#1dcc36','辰':'#a07d10','巳':'#d30505',
  '午':'#e02a2a','未':'#a07d10','申':'#ef9104','酉':'#d4860a','戌':'#8b6d03','亥':'#4a96f0'
}
var GAN_WX_NAME = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
var ZHI_WX_NAME = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
var ZODIAC_EMOJI = ['🐭','🐮','🐯','🐰','🐲','🐍','🐴','🐏','🐵','🐔','🐶','🐷']
function getZodiacEmoji(r) {
  if (r && r.birth_time) {
    var bt = String(r.birth_time)
    var m = bt.match(/(\d{4})(\d{2})(\d{2})/)
    if (m) {
      var year = parseInt(m[1])
      var month = parseInt(m[2])
      var day = parseInt(m[3])
      if (month < 2 || (month === 2 && day < 4)) year -= 1
      return ZODIAC_EMOJI[(year - 4) % 12]
    }
  }
  return r && r.gender === '女' ? '♀' : '♂'
}
function wxColor(ch) { return WX_CARD[ch] || 'var(--text-2)' }
function fmtTimeAgo(dateStr) {
  if (!dateStr) return ''
  var d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr.slice(0, 10)
  var now = new Date(), diff = Math.floor((now - d) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 2592000) return Math.floor(diff / 86400) + '天前'
  var m = d.getMonth() + 1, day = d.getDate()
  return (d.getFullYear() !== now.getFullYear() ? d.getFullYear() + '/' : '') + m + '/' + day
}
function fmtDateCN(str) {
  if (!str) return ''
  var s = String(str).replace(/[T\s].*$/, '').replace(/[-\/]/g, '')
  if (s.length > 8) s = s.slice(0, 8)
  if (/^\d{8}$/.test(s)) return s.slice(0,4) + '年' + s.slice(4,6) + '月' + s.slice(6,8) + '日'
  var d = new Date(str)
  if (!isNaN(d.getTime())) return d.getFullYear() + '年' + String(d.getMonth()+1).padStart(2,'0') + '月' + String(d.getDate()).padStart(2,'0') + '日'
  return str.slice(0, 10)
}
function _fmtRecord(r) {
  var p = (r.pillars || '')
  var ganArr = [], zhiArr = []
  for (var i = 0; i < p.length; i += 2) {
    if (i + 1 < p.length) { ganArr.push(p[i]); zhiArr.push(p[i + 1]) }
  }
  r.ganArr = ganArr; r.zhiArr = zhiArr
  r.dateStr = fmtDateCN(r.birth_time || r.created_at || '')
  r.dayGan = ganArr.length >= 3 ? ganArr[2] : ''
  r.dayGanWx = r.dayGan ? (GAN_WX_NAME[r.dayGan] || '') : ''
  r.typeLabel = r.record_type === 'hepan' ? '合盘' : '排盘'
  r.catLabel = r.category && r.category !== '全部' ? r.category : ''
  r.calLabel = r.cal_type || '公历'
  r.addrShort = r.birth_addr ? r.birth_addr.replace(/省|市|自治区|特别行政区/g, '').slice(0, 4) : ''
  r.createdAgo = fmtTimeAgo(r.created_at)
  return r
}

function loadRecords() {
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  uni.request({
    url: '/api/bazi/history', method: 'GET',
    header: token ? { 'Authorization': 'Bearer ' + token } : {},
    success: function(res) {
      var list = []
      if (res.data && Array.isArray(res.data)) list = res.data
      else if (res.data && res.data.success && Array.isArray(res.data.history)) list = res.data.history
      else if (res.data && res.data.success && Array.isArray(res.data.records)) list = res.data.records
      for (var i = 0; i < list.length; i++) _fmtRecord(list[i])
      records.value = list
    },
    fail: function(err) { console.error('[bazi] 加载排盘记录失败:', err) }
  })
}

function deleteRecord(id) {
  if (!id) return
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  uni.request({
    url: '/api/bazi/history/delete', method: 'POST',
    header: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    data: JSON.stringify({ id: id }),
    success: function() {
      records.value = records.value.filter(function(r) { return r.id !== id })
    },
    fail: function(err) { console.error('[bazi] 删除记录失败:', err) }
  })
}

function sendRecordToAi(r) {
  if (!selectedRecords.value) return
  var exists = selectedRecords.value.some(function(s) { return s.id === r.id })
  if (!exists) {
    selectedRecords.value.push(r)
    archiveRecordIds.value.push(r.id)
  }
  delete window.__lastBaziPanData
  activeTab.value = 'ai'
  uni.showToast({ title: '已加载到AI档案', icon: 'none' })
}

function sendRecordsBatchToAi() {
  var ids = selectedIds.value.slice()
  if (ids.length === 0) { uni.showToast({ title: '请先选择记录', icon: 'none' }); return }
  for (var i = 0; i < ids.length; i++) {
    var r = records.value.find(function(x) { return x.id === ids[i] })
    if (r) {
      var exists = selectedRecords.value.some(function(s) { return s.id === r.id })
      if (!exists) {
        selectedRecords.value.push(r)
        archiveRecordIds.value.push(r.id)
      }
    }
  }
  delete window.__lastBaziPanData
  batchMode.value = false; selectedIds.value = []
  activeTab.value = 'ai'
  uni.showToast({ title: '已加载 ' + ids.length + ' 条到AI档案', icon: 'none' })
}

var recordContextMenu = ref({ show: false, x: 0, y: 0, record: null, targetRect: null })

function showRecordMenu(e, r) {
  if (e && e.stopPropagation) e.stopPropagation()
  if (e && e.preventDefault) e.preventDefault()

  var menuWidth = 180
  var menuHeight = 200
  var x = 20
  var y = 20
  var vw = window.innerWidth || 375
  var vh = window.innerHeight || 667

  var targetElement = null

  if (e && e.currentTarget && e.currentTarget.getBoundingClientRect) {
    targetElement = e.currentTarget
  } else if (e && e.target) {
    var closest = e.target.closest ? e.target.closest('.card-ops') : null
    if (closest) targetElement = closest
  }

  if (!targetElement && r && r.id) {
    targetElement = document.querySelector('[data-ops-id="ops-' + r.id + '"]')
  }

  if (targetElement) {
    var rect = targetElement.getBoundingClientRect()
    x = rect.right - menuWidth
    y = rect.bottom + 6
    if (y + menuHeight > vh - 10 && rect.top > menuHeight + 10) {
      y = rect.top - menuHeight - 6
    }
  } else if (e) {
    var cx = 0, cy = 0
    if (e.touches && e.touches[0]) {
      cx = e.touches[0].clientX
      cy = e.touches[0].clientY
    } else if (typeof e.clientX === 'number') {
      cx = e.clientX
      cy = e.clientY
    }
    if (cx > 0 && cy > 0) {
      x = cx - menuWidth + 20
      y = cy + 10
    }
  }

  if (x < 10) x = 10
  if (x + menuWidth > vw - 10) x = vw - menuWidth - 10
  if (y < 10) y = 10
  if (y + menuHeight > vh - 10) y = vh - menuHeight - 10

  x = Math.round(x)
  y = Math.round(y)

  recordContextMenu.value = {
    show: true,
    x: x,
    y: y,
    record: r,
    targetRect: null,
    ready: true
  }
}

function showMoveGroupForRecord(r) {
  hideRecordMenu()
  selectedIds.value = [r.id]
  moveGroupModal.value = true
}
function hideRecordMenu() { recordContextMenu.value.show = false }

function moveRecordCategory(r, cat) {
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  uni.request({
    url: '/api/bazi/history/category', method: 'POST',
    header: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    data: JSON.stringify({ id: r.id, category: cat }),
    success: function(res) {
      if (res.data && res.data.success) {
        r.category = cat
        uni.showToast({ title: '已移至「' + cat + '」', icon: 'none' })
      }
    }
  })
  hideRecordMenu()
}

function renameRecordPrompt(r) {
  var newName = prompt('修改名称:', r.name || '')
  if (newName === null || newName.trim() === '') return
  newName = newName.trim()
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  uni.request({
    url: '/api/bazi/history/rename', method: 'POST',
    header: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    data: JSON.stringify({ id: r.id, name: newName }),
    success: function(res) {
      if (res.data && res.data.success) {
        r.name = newName
      } else {
        uni.showToast({ title: '重命名失败', icon: 'none' })
      }
    }
  })
  hideRecordMenu()
}

function editRecord(r) {
  hideRecordMenu()
  var newName = prompt('编辑名称:', r.name || '')
  if (newName === null || newName.trim() === '') return
  newName = newName.trim()
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  uni.request({
    url: '/api/bazi/history/rename', method: 'POST',
    header: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    data: JSON.stringify({ id: r.id, name: newName }),
    success: function(res) {
      if (res.data && res.data.success) {
        r.name = newName
        uni.showToast({ title: '修改成功', icon: 'success' })
      } else {
        uni.showToast({ title: '编辑失败', icon: 'none' })
      }
    }
  })
}

function togglePin(r) {
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  uni.request({
    url: '/api/bazi/history/pin', method: 'POST',
    header: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    data: JSON.stringify({ id: r.id }),
    success: function(res) {
      if (res.data && res.data.success) {
        // 更新本地状态并重新加载列表以正确排序
        loadRecords()
        uni.showToast({ title: res.data.pinned ? '已置顶' : '已取消置顶', icon: 'success' })
      }
    },
    fail: function(err) { console.error('[bazi] 置顶失败:', err) }
  })
}

function deleteRecordFromMenu(r) {
  uni.showModal({
    title: '确认删除',
    content: '确定删除「' + (r.name || '未命名') + '」的排盘记录？',
    success: function(res) {
      if (res.confirm) {
        deleteRecord(r.id)
      }
    }
  })
  hideRecordMenu()
}

function sendToAiFromMenu(r) {
  hideRecordMenu()
  sendRecordToAi(r)
}

function selectFilterAndClose(cat) {
  catFilter.value = cat
  filterDropdownOpen.value = false
}

function batchMoveToGroup(cat) {
  var ids = selectedIds.value.slice()
  if (ids.length === 0) { uni.showToast({ title: '请先选择记录', icon: 'none' }); return }
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  uni.request({
    url: '/api/bazi/history/category', method: 'POST',
    header: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    data: JSON.stringify({ ids: ids, category: cat }),
    success: function(res) {
      if (res.data && res.data.success) {
        for (var i = 0; i < ids.length; i++) {
          var r = records.value.find(function(x) { return x.id === ids[i] })
          if (r) r.category = cat
        }
        uni.showToast({ title: '已将 ' + ids.length + ' 条移至「' + cat + '」', icon: 'none' })
        moveGroupModal.value = false
      }
    }
  })
}

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

// AI Tab：同步免费Tab的select选项到AI Tab
function _initAiTabSelects() {
  // AI Tab 不再需要独立日期输入，保留空函数避免报错
}

// AI Tab：初始化地址选择器事件监听
function _initAiTabAddrListeners() {
  var provEl = document.getElementById('baziProvinceAi')
  var cityEl = document.getElementById('baziCityAi')
  var distEl = document.getElementById('baziDistrictAi')
  if (!provEl || !cityEl || !distEl) return
  if (provEl.dataset.bound) return
  provEl.dataset.bound = '1'
  cityEl.dataset.bound = '1'
  distEl.dataset.bound = '1'
  if (!_cityData) return
  provEl.addEventListener('change', function() {
    cityEl.innerHTML = '<option value="">-- 市 --</option>'
    distEl.innerHTML = '<option value="">-- 区 --</option>'
    var selProv = provEl.value
    for (var j = 0; j < _cityData.length; j++) {
      if (_cityData[j][0] === selProv && _cityData[j][1]) {
        for (var k = 0; k < _cityData[j][1].length; k++) {
          var co = document.createElement('option')
          co.value = _cityData[j][1][k][0]
          co.text = _cityData[j][1][k][0]
          co.setAttribute('data-city-idx', k)
          cityEl.appendChild(co)
        }
        break
      }
    }
    _updateAddrInfoAi()
  })
  cityEl.addEventListener('change', function() {
    distEl.innerHTML = '<option value="">-- 区 --</option>'
    var selProv = provEl.value, selCity = cityEl.value
    for (var j = 0; j < _cityData.length; j++) {
      if (_cityData[j][0] === selProv && _cityData[j][1]) {
        for (var k = 0; k < _cityData[j][1].length; k++) {
          if (_cityData[j][1][k][0] === selCity && _cityData[j][1][k][1] && _cityData[j][1][k][1].length > 0) {
            for (var m = 0; m < _cityData[j][1][k][1].length; m++) {
              var dopt = document.createElement('option')
              dopt.value = _cityData[j][1][k][1][m][0]
              dopt.text = _cityData[j][1][k][1][m][0]
              dopt.setAttribute('data-lat', _cityData[j][1][k][1][m][1])
              dopt.setAttribute('data-lng', _cityData[j][1][k][1][m][2])
              distEl.appendChild(dopt)
            }
            break
          }
        }
        break
      }
    }
    _updateAddrInfoAi()
  })
  distEl.addEventListener('change', function() { _updateAddrInfoAi() })
}

function _updateAddrInfoAi() {
  var provEl = document.getElementById('baziProvinceAi')
  var cityEl = document.getElementById('baziCityAi')
  var distEl = document.getElementById('baziDistrictAi')
  var addrEl = document.getElementById('baziBirthAddrAi')
  var lngEl = document.getElementById('baziBirthLngAi')
  var latEl = document.getElementById('baziBirthLatAi')
  var infoEl = document.getElementById('baziAddrInfoAi')
  var solarEl = document.getElementById('baziAddrSolarAi')
  var lngInfoEl = document.getElementById('baziAddrLngAi')
  var provVal = provEl ? provEl.value : ''
  var cityVal = cityEl ? cityEl.value : ''
  var distVal = distEl ? distEl.value : ''
  if (!cityVal) { if (infoEl) infoEl.style.display = 'none'; return }
  var lat = 0, lng = 0, addrText = provVal
  if (distVal) {
    var distOpt = distEl.options[distEl.selectedIndex]
    lat = distOpt ? parseFloat(distOpt.getAttribute('data-lat')) : 0
    lng = distOpt ? parseFloat(distOpt.getAttribute('data-lng')) : 0
    addrText = provVal + ' ' + cityVal + ' ' + distVal
  } else {
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
  var dateSectionAi = document.getElementById('baziDateSectionAi')
  var siziSectionAi = document.getElementById('baziSiziSectionAi')
  if (type === '四柱') {
    if (dateSection) dateSection.style.display = 'none'
    if (siziSection) siziSection.style.display = 'block'
    if (dateSectionAi) dateSectionAi.style.display = 'none'
    if (siziSectionAi) siziSectionAi.style.display = 'block'
    return
  }
  if (dateSection) dateSection.style.display = 'block'
  if (siziSection) siziSection.style.display = 'none'
  if (dateSectionAi) dateSectionAi.style.display = 'block'
  if (siziSectionAi) siziSectionAi.style.display = 'none'

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
    var monthSelAi = document.getElementById('baziMonthAi')
    if (monthSel) {
      var prevMonth = monthSel.value
      monthSel.innerHTML = ''
      data.months.forEach(function(m) {
        var opt = document.createElement('option')
        opt.value = String(m.value).padStart(2, '0')
        opt.textContent = m.label
        if (m.isLeap) opt.setAttribute('data-is-leap', 'true')
        monthSel.appendChild(opt)
      })
      if (prevMonth && monthSel.querySelector('option[value="' + prevMonth + '"]')) {
        monthSel.value = prevMonth
      }
    }
    // 同时更新 AI Tab
    if (monthSelAi) {
      var prevMonthAi = monthSelAi.value
      monthSelAi.innerHTML = ''
      data.months.forEach(function(m) {
        var opt = document.createElement('option')
        opt.value = String(m.value).padStart(2, '0')
        opt.textContent = m.label
        if (m.isLeap) opt.setAttribute('data-is-leap', 'true')
        monthSelAi.appendChild(opt)
      })
      if (prevMonthAi && monthSelAi.querySelector('option[value="' + prevMonthAi + '"]')) {
        monthSelAi.value = prevMonthAi
      }
    }
    // 根据当前选中月份获取天数
    var selIdx = monthSel ? monthSel.selectedIndex : 0
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
  var yElAi = document.getElementById('baziYearAi')
  if (!yEl) { if (onComplete) onComplete(); return }
  if (lunarYear && parseInt(yEl.value) !== lunarYear) {
    yEl.value = lunarYear
  }
  if (yElAi && lunarYear && parseInt(yElAi.value) !== lunarYear) {
    yElAi.value = lunarYear
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
    var monthSel = document.getElementById('baziMonth')
    var monthSelAi = document.getElementById('baziMonthAi')
    var targetMonthIdx = 0
    if (monthSel) {
      monthSel.innerHTML = ''
      data.months.forEach(function(m, idx) {
        var opt = document.createElement('option')
        opt.value = String(m.value).padStart(2, '0')
        opt.textContent = m.label
        if (m.isLeap) opt.setAttribute('data-is-leap', 'true')
        monthSel.appendChild(opt)
        if (lunarMonth && m.value === lunarMonth && m.isLeap === !!isLeap) {
          targetMonthIdx = idx
        }
      })
      monthSel.selectedIndex = targetMonthIdx
    }
    if (monthSelAi) {
      monthSelAi.innerHTML = ''
      data.months.forEach(function(m, idx) {
        var opt = document.createElement('option')
        opt.value = String(m.value).padStart(2, '0')
        opt.textContent = m.label
        if (m.isLeap) opt.setAttribute('data-is-leap', 'true')
        monthSelAi.appendChild(opt)
      })
      monthSelAi.selectedIndex = targetMonthIdx
    }
    var targetMonthInfo = data.months[targetMonthIdx]
    if (targetMonthInfo) {
      wzUpdateLunarDays(targetMonthInfo.dayCount, _lunarDayNames)
      var daySel = document.getElementById('baziDay')
      var daySelAi = document.getElementById('baziDayAi')
      if (daySel && lunarDay) {
        var dayVal = String(lunarDay).padStart(2, '0')
        if (lunarDay <= targetMonthInfo.dayCount) {
          daySel.value = dayVal
        }
      }
      if (daySelAi && lunarDay) {
        var dayVal = String(lunarDay).padStart(2, '0')
        if (lunarDay <= targetMonthInfo.dayCount) {
          daySelAi.value = dayVal
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
  var daySelAi = document.getElementById('baziDayAi')
  if (daySel) {
    var prevDay = daySel.value
    daySel.innerHTML = ''
    for (var d = 1; d <= dayCount; d++) {
      var opt = document.createElement('option')
      opt.value = String(d).padStart(2, '0')
      opt.textContent = (dayNames && dayNames[d]) ? dayNames[d] : d
      daySel.appendChild(opt)
    }
    if (prevDay && daySel.querySelector('option[value="' + prevDay + '"]')) {
      daySel.value = prevDay
    } else if (daySel.options.length > 0) {
      daySel.selectedIndex = 0
    }
  }
  if (daySelAi) {
    var prevDayAi = daySelAi.value
    daySelAi.innerHTML = ''
    for (var d = 1; d <= dayCount; d++) {
      var opt = document.createElement('option')
      opt.value = String(d).padStart(2, '0')
      opt.textContent = (dayNames && dayNames[d]) ? dayNames[d] : d
      daySelAi.appendChild(opt)
    }
    if (prevDayAi && daySelAi.querySelector('option[value="' + prevDayAi + '"]')) {
      daySelAi.value = prevDayAi
    } else if (daySelAi.options.length > 0) {
      daySelAi.selectedIndex = 0
    }
  }
  updateBaziDate()
}

function wzInitSolarMonthDay() {
  var monthSel = document.getElementById('baziMonth')
  var monthSelAi = document.getElementById('baziMonthAi')
  if (monthSel) {
    var curMonth = monthSel.value
    monthSel.innerHTML = ''
    for (var m = 1; m <= 12; m++) {
      var opt = document.createElement('option')
      opt.value = String(m).padStart(2, '0')
      opt.textContent = m + '月'
      monthSel.appendChild(opt)
    }
    if (curMonth) monthSel.value = curMonth
  }
  if (monthSelAi) {
    var curMonthAi = monthSelAi.value
    monthSelAi.innerHTML = ''
    for (var m = 1; m <= 12; m++) {
      var opt = document.createElement('option')
      opt.value = String(m).padStart(2, '0')
      opt.textContent = m + '月'
      monthSelAi.appendChild(opt)
    }
    if (curMonthAi) monthSelAi.value = curMonthAi
  }
  refillBaziDaySelect()
}

// 不调用 refillBaziDaySelect 的版本（用于农历→公历时先建月份，再手动设日期）
function wzInitSolarMonthDayRaw() {
  var monthSel = document.getElementById('baziMonth')
  var monthSelAi = document.getElementById('baziMonthAi')
  if (monthSel) {
    monthSel.innerHTML = ''
    for (var m = 1; m <= 12; m++) {
      var opt = document.createElement('option')
      opt.value = String(m).padStart(2, '0')
      opt.textContent = m + '月'
      monthSel.appendChild(opt)
    }
  }
  if (monthSelAi) {
    monthSelAi.innerHTML = ''
    for (var m = 1; m <= 12; m++) {
      var opt = document.createElement('option')
      opt.value = String(m).padStart(2, '0')
      opt.textContent = m + '月'
      monthSelAi.appendChild(opt)
    }
  }
}

// 强制版 refillBaziDaySelect（不受农历模式 return 限制）
function refillBaziDaySelectForced() {
  var yEl = document.getElementById('baziYear')
  var mEl = document.getElementById('baziMonth')
  var dEl = document.getElementById('baziDay')
  var yElAi = document.getElementById('baziYearAi')
  var mElAi = document.getElementById('baziMonthAi')
  var dElAi = document.getElementById('baziDayAi')
  if (yEl && mEl && dEl) {
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
  }
  if (yElAi && mElAi && dElAi) {
    var yAi = parseInt(yElAi.value)
    var mAi = parseInt(mElAi.value)
    var maxDayAi = getDaysInMonth(yAi, mAi)
    var curDayAi = parseInt(dElAi.value)
    dElAi.innerHTML = ''
    for (var i = 1; i <= maxDayAi; i++) {
      var opt = document.createElement('option')
      opt.value = i
      opt.text = i + '日'
      if (i === curDayAi) opt.selected = true
      dElAi.appendChild(opt)
    }
    if (curDayAi > maxDayAi) {
      dElAi.value = String(maxDayAi)
    }
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
  
  // 同时更新 AI Tab 的日 select
  var yElAi = document.getElementById('baziYearAi')
  var mElAi = document.getElementById('baziMonthAi')
  var dElAi = document.getElementById('baziDayAi')
  if (yElAi && mElAi && dElAi) {
    var yAi = parseInt(yElAi.value) || y
    var mAi = parseInt(mElAi.value) || m
    var maxDayAi = getDaysInMonth(yAi, mAi)
    var curDayAi = parseInt(dElAi.value) || curDay
    dElAi.innerHTML = ''
    for (var i = 1; i <= maxDayAi; i++) {
      var optAi = document.createElement('option')
      optAi.value = i
      optAi.text = i + '日'
      if (i === curDayAi) optAi.selected = true
      dElAi.appendChild(optAi)
    }
    if (curDayAi > maxDayAi) {
      dElAi.value = String(maxDayAi)
    }
  }
  
  updateBaziDate()
}

// ── 日期联动（免费/AI共用）──
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
  nextTick(function() { _checkBaziRestore() })
  loadRecords()
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
  document.querySelectorAll('.btn-row').forEach(function(btnRow) {
    btnRow.addEventListener('click', function(e) {
      var target = e.target; var depth = 8
      while (target && target !== this && depth > 0) {
        if (target.dataset && target.dataset.bzAction) {
          var action = target.dataset.bzAction
          if (action === 'aiAsk') baiAiAsk()
          else if (action === 'aiFollowUp') baiSendFollowUp()
          else if (action === 'aiNewQuestion') {
            baziAiResult.value = ''; window._baiChatHistory = []; _baiCurrentConvId = null
            archiveOpen.value = false; archiveRecordIds.value = []; selectedRecords.value = []
            var box = document.getElementById('baiStreamBox'); if (box) box.style.display = 'none'
            var ib = document.getElementById('baiChatInputBar'); if (ib) { ib.style.display = 'none'; var ci = document.getElementById('baiChatInput'); if (ci) ci.value = '' }
            var ab = document.querySelector('[data-bz-action="aiAsk"]'); if (ab) ab.style.display = 'inline-flex'
          }
          else if (action === 'aiType') {
            var idx = parseInt(target.dataset.bzTypeIdx)
            if (!isNaN(idx)) baiAnalysisTypeIdx.value = idx
          }
          return
        }
        target = target.parentElement; depth--
      }
    })
  })

  var rsEl = document.getElementById('recordSearch')

  document.getElementById('recordSearch')
  if (rsEl) {
    rsEl.style.cssText = 'width:100%;padding:8px 10px;border:none;background:none;outline:none;font-size:14px;color:var(--text-1);box-sizing:border-box;'
  }

  // 档案下拉：点击外部关闭
  document.addEventListener('click', function(e) {
    if (archiveOpen.value) {
      var sel = e.target.closest('.archive-selector, .archive-dropdown')
      if (!sel) archiveOpen.value = false
    }
    if (recordContextMenu.value.show) {
      var menu = e.target.closest('.record-ctx-menu')
      if (!menu) hideRecordMenu()
    }
  })

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
  
  // 立即填充 AI Tab 的日期时间 select
  fillBaziSelect('baziYearAi', yearOpts, curYear, function() {
    if (baziCalType.value === '农历') { wzUpdateLunarMonthDay() } else { refillBaziDaySelect() }
  })
  fillBaziSelect('baziMonthAi', monthOpts, now.getMonth() + 1, function() {
    if (baziCalType.value === '农历' && _lunarMonthsData) {
      var mEl = document.getElementById('baziMonthAi')
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
  var maxDay = getDaysInMonth(curYear, now.getMonth() + 1)
  var dayOpts = []
  for (var i = 1; i <= maxDay; i++) {
    dayOpts.push({ value: i, label: i + '日' })
  }
  fillBaziSelect('baziDayAi', dayOpts, now.getDate(), function() { updateBaziDate() })
  fillBaziSelect('baziHourAi', hourOpts, now.getHours(), function(val) {
    baziHourIdx.value = parseInt(val)
  })
  fillBaziSelect('baziMinuteAi', minOpts, now.getMinutes(), function(val) {
    baziMinuteIdx.value = parseInt(val)
  })

  // AI Tab 年/月 change → 刷新日 select
  ;['baziYearAi', 'baziMonthAi'].forEach(function(id) {
    var el = document.getElementById(id)
    if (el) el.addEventListener('change', function() { refillBaziDaySelect() })
  })

  // ── AI Tab DOM click 绑定（事件代理，uni-view 的 @tap/@click 不生效）──
  setTimeout(function() {
    var aiContent = document.getElementById('baziTabAiContent')
    if (aiContent) {
      aiContent.addEventListener('click', function(e) {
        var target = e.target
        var btn = target.closest ? target.closest('.submit-btn') : null
        if (!btn) { btn = target; while (btn && !btn.classList.contains('submit-btn')) btn = btn.parentElement }
        if (btn && btn.textContent.indexOf('AI 深度解读') !== -1) {
          baiAiAsk(); return
        }
        var sendBtn = target.closest ? target.closest('.chat-send-btn') : null
        if (!sendBtn) { sendBtn = target; while (sendBtn && !sendBtn.classList.contains('chat-send-btn')) sendBtn = sendBtn.parentElement }
        if (sendBtn) {
          if (sendBtn.getAttribute('data-bz-action') === 'aiNewQuestion') {
            baiAiAsk()
          } else {
            baiSendFollowUp()
          }
          return
        }
        var typeBtn = target.closest ? target.closest('.analysis-type-btn') : null
        if (!typeBtn) { typeBtn = target; while (typeBtn && !typeBtn.classList.contains('analysis-type-btn')) typeBtn = typeBtn.parentElement }
        if (typeBtn) {
          var texts = ['命局总览', '财运事业', '婚姻感情', '大运流年', '健康六亲']
          for (var i = 0; i < texts.length; i++) {
            if (typeBtn.textContent.indexOf(texts[i]) !== -1) { baiAnalysisTypeIdx.value = i; return }
          }
        }
      })
    }
  }, 300)

  // ── 出生地址：加载城市数据并填充三级级联选择 ──
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
.dom-input-wrap { width: 100%; }
.dom-input-wrap .native-input { width: 100%; padding: 9px 12px; border: 1.5px solid var(--card-border); border-radius: 10px; font-size: 0.85rem; background: var(--card-bg); color: var(--text-1); outline: none; box-sizing: border-box; }
.checkbox-view { width: 18px; height: 18px; border: 2px solid var(--accent); border-radius: 3px; position: relative; cursor: pointer; transition: all 0.15s; }
.checkbox-view.checked { background: var(--accent); }
.checkbox-view.checked::after { content: '✓'; position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); color: #fff; font-size: 12px; font-weight: bold; }
.tool-tabs { display: flex; gap: 4px; margin-bottom: 28px; border-bottom: 1px solid var(--card-border); }
.tool-tab { padding: 12px 20px; border-radius: 10px 10px 0 0; font-size: 0.875rem; cursor: pointer; border: 1px solid transparent; border-bottom: none; color: var(--text-3); background: transparent; }
.tool-tab.active { color: var(--accent); background: var(--accent-glow); border-color: var(--accent); font-weight: 600; }
.tab-badge { font-size: 0.5625rem; padding: 1px 5px; border-radius: 4px; background: var(--accent); color: #fff; margin-left: 4px; }
.tab-badge.free { background: var(--success); }
.tool-tab-content { display: block; }

/* ── 问真风格表单 ── */
.wz-form { padding: 4px 0; }
.wz-form-row { display: flex; gap: 12px; margin-bottom: 14px; }
.wz-form-item { flex: 1; position: relative; }
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
.result-mode-switch { display: flex; gap: 8px; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--card-border); }
.result-mode-btn { flex: 1; padding: 8px; border-radius: 8px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.75rem; cursor: pointer; text-align: center; }
.result-mode-btn.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }

/* ── 记录案例 ── */
.record-page { background: var(--card-bg); border-radius: 12px; overflow: visible; }
.record-tabs { display: flex; border-bottom: 1px solid var(--card-border); padding: 0 20px; }
.record-tab { padding: 16px 24px; font-size: 15px; color: var(--text-3); cursor: pointer; border-bottom: 2px solid transparent; }
.record-tab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
.record-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 12px 20px 4px; gap: 10px; flex-wrap: wrap; }
.record-filter-row { display: flex; align-items: center; gap: 6px; padding: 8px 20px 10px; flex-wrap: wrap; }
.record-filter-label { font-size: 13px; color: var(--text-3); margin-right: 2px; }
.record-filter-tag { padding: 4px 12px; border-radius: 6px; font-size: 12px; border: 1px solid var(--card-border); color: var(--text-3); cursor: pointer; transition: all 0.15s; }
.record-filter-tag.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); font-weight: 600; }
.record-search { display: flex; align-items: center; background: var(--input-bg); border-radius: 20px; padding: 4px 4px 4px 14px; flex: 1; max-width: 400px; }
.record-search .dom-input-wrap { flex: 1; }
.record-search .dom-input-wrap .native-input { border: none; background: none; outline: none; padding: 8px 10px; font-size: 14px; flex: 1; color: var(--text-1); }
.search-btn { background: var(--accent); color: #fff; border: none; border-radius: 16px; padding: 8px 20px; font-size: 14px; cursor: pointer; }
.record-actions { display: flex; gap: 4px; flex-wrap: wrap; }
.action-btn { padding: 6px 12px; font-size: 12px; color: var(--text-3); cursor: pointer; border-radius: 6px; white-space: nowrap; transition: all 0.2s; }
.action-btn:hover { background: var(--accent-glow); color: var(--accent); }
.action-btn.active { background: var(--accent); color: #fff; }
.action-btn.disabled { opacity: 0.35; pointer-events: none; }
.action-btn-ai { color: var(--accent); }
.filter-dropdown { padding: 0 20px; position: relative; }
.filter-dropdown-inner { display: flex; gap: 8px; padding: 10px 16px; background: var(--section-alt); border-radius: 10px; border: 1px solid var(--card-border); }
.filter-item { padding: 6px 20px; font-size: 13px; color: var(--text-3); border-radius: 16px; cursor: pointer; transition: all 0.2s; }
.filter-item:hover { background: var(--accent-glow); color: var(--accent); }
.filter-item.active { background: var(--accent); color: #fff; }
.active-filter-tag { display: flex; align-items: center; gap: 8px; padding: 6px 20px; }
.filter-tag-text { font-size: 12px; color: var(--accent); background: var(--accent-glow); padding: 4px 12px; border-radius: 12px; }
.filter-tag-close { font-size: 12px; color: var(--text-3); cursor: pointer; padding: 2px 6px; }
.filter-tag-close:hover { color: var(--danger); }
.star-section { padding: 0 20px 8px; }
.star-title { font-size: 15px; font-weight: 600; color: var(--text-1); padding: 12px 0 10px; border-top: 1px solid var(--card-border); cursor: pointer; display: flex; align-items: center; gap: 6px; }
.star-toggle { font-size: 12px; color: var(--text-3); }
.star-cards { display: grid !important; grid-template-columns: 1fr 1fr; gap: 10px; }
.batch-bar { display: flex; align-items: center; gap: 12px; padding: 10px 20px; background: var(--section-alt); border-top: 1px solid var(--card-border); border-bottom: 1px solid var(--card-border); flex-wrap: wrap; }
.batch-select-all { font-size: 14px; color: var(--text-3); cursor: pointer; }
.batch-count { font-size: 14px; color: var(--accent); font-weight: 600; }
.batch-move-btn { background: var(--section-alt); color: var(--text-2); border: 1px solid var(--card-border); border-radius: 6px; padding: 6px 14px; font-size: 13px; cursor: pointer; }
.batch-move-btn:hover { border-color: var(--accent); color: var(--accent); }
.batch-confirm-btn { background: #e74c3c; color: #fff; border: none; border-radius: 6px; padding: 6px 16px; font-size: 13px; cursor: pointer; }
.batch-cancel-btn { background: var(--input-bg); color: var(--text-3); border: 1px solid var(--card-border); border-radius: 6px; padding: 6px 16px; font-size: 13px; cursor: pointer; }
.case-cards { display: grid !important; grid-template-columns: 1fr 1fr; gap: 10px; padding: 14px 20px 20px; }
.bz-card { width: auto !important; display: flex; align-items: center; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; position: relative; cursor: pointer; height: 80px; transition: border-color 0.2s, background 0.2s; overflow: hidden; }
.bz-card:hover { border-color: var(--accent); background: var(--accent-glow); }
.bz-card.starred { border-color: rgba(241,196,15,0.4); background: rgba(241,196,15,0.04); }
.bz-card.pinned { border-color: rgba(46,204,113,0.6); background: rgba(46,204,113,0.06); box-shadow: 0 0 0 1px rgba(46,204,113,0.3), 0 4px 12px rgba(46,204,113,0.15); }
.bz-card.pinned::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #2ecc71 0%, #27ae60 100%);
  border-radius: 10px 0 0 10px;
}
.bz-card .card-pin-badge { color: #2ecc71; font-size: 12px; }
.bz-card .card-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  color: #333;
  margin-left: 12px;
  line-height: 1;
  padding: 0;
  box-sizing: border-box;
}
.bz-card .card-userinfo { flex: 0 1 auto; min-width: 0; max-width: 120px; padding: 0 8px; display: flex; flex-direction: column; justify-content: center; overflow: hidden; }
.bz-card .card-name { font-size: 14px; font-weight: 700; color: var(--text-1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 4px; }
.bz-card .card-sex { font-size: 10px; color: var(--text-3); background: var(--input-bg); padding: 0 5px; border-radius: 3px; flex-shrink: 0; }
.bz-card .card-star-badge { color: #f1c40f; font-size: 12px; }
.bz-card .card-date { font-size: 11px; color: var(--text-3); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bz-card .card-gz { display: flex; gap: 4px; flex: 1; justify-content: center; min-width: 0; align-items: center; padding: 6px 4px; }
.bz-card .gz-col { display: flex; flex-direction: column; align-items: center; gap: 3px; flex: 1; min-width: 0; }
.bz-card .gz-circle { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: #fff; flex-shrink: 0; }
.bz-card .gz-placeholder { background: var(--card-border); color: var(--text-3); }
.bz-card .card-ops {
  width: 50px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(255,255,255,0.05);
  border-left: 1px solid var(--card-border);
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
  z-index: 10;
}
.bz-card .card-ops:hover {
  background: rgba(255,255,255,0.12);
}
.bz-card .card-ops:active {
  background: rgba(255,255,255,0.18);
}
.bz-card .ops-dots {
  font-size: 24px;
  color: var(--text-3);
  font-weight: 700;
  line-height: 1;
  pointer-events: none;
}
.bz-card .batch-checkbox { position: absolute; left: -6px; top: 50%; transform: translateY(-50%); z-index: 2; }
.batch-ai-btn { background: var(--accent); color: #fff; border: none; border-radius: 6px; padding: 6px 14px; font-size: 13px; cursor: pointer; }

/* 移动分组弹窗 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 600; display: none; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card-bg); border-radius: 16px; padding: 24px; min-width: 280px; max-width: 360px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
.modal-title { font-size: 17px; font-weight: 700; color: var(--text-1); margin-bottom: 16px; text-align: center; }
.move-group-list { display: flex; flex-direction: column; gap: 8px; }
.move-group-item { padding: 12px 16px; font-size: 15px; color: var(--text-2); background: var(--section-alt); border-radius: 10px; cursor: pointer; text-align: center; transition: all 0.2s; border: 1px solid transparent; }
.move-group-item:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); }
.modal-btns { margin-top: 16px; text-align: center; }
.btn-ghost { background: transparent; color: var(--text-3); border: 1px solid var(--card-border); border-radius: 8px; padding: 8px 24px; font-size: 14px; cursor: pointer; }

.bz-card.selected { border-color: var(--accent) !important; background: var(--accent-glow) !important; box-shadow: 0 0 0 1px var(--accent); }
.record-empty { text-align: center; padding: 60px 20px; }
.empty-icon { font-size: 3rem; margin-bottom: 12px; display: block; opacity: 0.5; }
.empty-text { font-size: 16px; color: var(--text-2); margin-bottom: 6px; font-weight: 600; }
.empty-hint { font-size: 13px; color: var(--text-4); margin-bottom: 20px; line-height: 1.6; }

/* 右键菜单 */
.record-ctx-menu { position: fixed; z-index: 9999; background: rgba(235,235,240,0.96); border: 1px solid rgba(0,0,0,0.08); border-radius: 14px; padding: 6px 0; min-width: 180px; box-shadow: 0 8px 32px rgba(0,0,0,0.12); color: #333; }
@media (max-width: 768px) {
  .record-ctx-menu { background: rgba(255,255,255,0.65); border-color: rgba(255,255,255,0.3); border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.4); -webkit-backdrop-filter: blur(20px) saturate(180%); backdrop-filter: blur(20px) saturate(180%); -webkit-transform: translateZ(0); transform: translateZ(0); isolation: isolate; }
}
.ctx-menu-item { padding: 10px 18px; font-size: 14px; color: #333; cursor: pointer; display: flex; align-items: center; gap: 8px; white-space: nowrap; transition: all 0.15s; }
.ctx-menu-item:hover { background: rgba(0,0,0,0.06); color: #111; }
.ctx-menu-item.ctx-danger { color: #e74c3c; }
.ctx-menu-item.ctx-danger:hover { background: rgba(231,76,60,0.08); }
.ctx-menu-divider { height: 1px; background: rgba(0,0,0,0.08); margin: 4px 12px; }
.ctx-submenu { position: relative; }
.ctx-submenu-list { display: none; position: absolute; left: 100%; top: 0; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 6px 0; min-width: 100px; box-shadow: var(--card-shadow); z-index: 10000; }
.ctx-submenu:hover .ctx-submenu-list { display: block; }
.ctx-submenu-item { padding: 8px 16px; font-size: 13px; color: var(--text-2); cursor: pointer; }
.ctx-submenu-item:hover { background: var(--accent-glow); color: var(--accent); }
/* 点击外部关闭菜单的遮罩 */
.menu-overlay { position: fixed; inset: 0; z-index: 4999; }

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
  .record-toolbar { flex-direction: column; align-items: stretch; }
  .record-search { max-width: none; }
  .wz-smart-btns { flex-direction: column; }
  .wz-smart-btns .wz-submit-btn { width: 100%; }
  .case-cards, .star-cards { display: flex !important; flex-direction: column !important; gap: 10px !important; }
  .bz-card { height: auto !important; min-height: 90px !important; }
  .card-userinfo { max-width: 100% !important; }
  .gz-circle { width: 20px !important; height: 20px !important; font-size: 11px !important; }
  .record-filter-row { padding: 8px 16px 10px !important; }
  
  /* 手机端头像 fix */
  .bz-card .card-avatar {
    width: 38px !important;
    height: 38px !important;
    min-width: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    font-size: 18px !important;
    line-height: 1 !important;
    padding: 0 !important;
    margin-left: 12px !important;
    color: #fff !important;
    box-sizing: border-box !important;
    border-radius: 50% !important;
  }
  
  /* 手机版菜单样式 */
  .record-ctx-menu { min-width: 170px; }
  .ctx-submenu-list { position: static; display: none; background: rgba(0,0,0,0.2); margin-top: 4px; border-top: 1px solid var(--card-border); border-bottom: 1px solid var(--card-border); border-radius: 0; }
  .ctx-submenu:active .ctx-submenu-list, 
  .ctx-submenu:focus .ctx-submenu-list { display: block; }
  
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
.ai-stage-logo { width: 22px; height: 22px; border-radius: 50%; object-fit: cover; flex-shrink: 0; animation: ai-logo-spin 1.8s linear infinite; box-shadow: 0 0 6px rgba(0,0,0,0.06); }
@keyframes ai-logo-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.ai-progress-bar { height: 4px; background: var(--card-border); border-radius: 2px; overflow: hidden; margin-bottom: 16px; }
.ai-progress-fill { height: 100%; width: 20%; background: linear-gradient(90deg, var(--accent), #8b5cf6); border-radius: 2px; animation: ai-progress-pulse 1.5s ease-in-out infinite; transition: width 0.3s ease; }
@keyframes ai-progress-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.chat-input-bar { display: flex; gap: 8px; margin-top: 16px; padding: 10px 14px; background: var(--section-alt); border-radius: 12px; border: 1px solid var(--card-border); }
.chat-input { flex: 1; padding: 8px 14px; border-radius: 8px; border: 1px solid var(--card-border); background: var(--input-bg); color: var(--text-1); font-size: 0.875rem; outline: none; }
.chat-send-btn { padding: 8px 20px; background: var(--accent); color: #fff; border-radius: 8px; font-size: 0.875rem; cursor: pointer; white-space: nowrap; }

.analysis-type-row { display: flex; flex-wrap: wrap; gap: 6px; }
.analysis-type-btn { padding: 6px 12px; border-radius: 8px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.75rem; cursor: pointer; text-align: center; white-space: nowrap; transition: all .15s; }
.analysis-type-btn.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }

/* ── 档案多选 ── */
.archive-selector { display: flex; align-items: center; gap: 4px; padding: 9px 12px; border: 1.5px solid var(--card-border); border-radius: 10px; background: var(--card-bg); cursor: pointer; min-height: 38px; box-sizing: border-box; }
.archive-trigger { flex: 1; font-size: 0.85rem; color: var(--text-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.archive-trigger.active { color: var(--accent); }
.archive-arrow { font-size: 0.7rem; color: var(--text-3); }
.archive-dropdown { position: relative; z-index: 100; background: var(--card-bg); border: 1.5px solid var(--card-border); border-radius: 12px; margin-top: 4px; max-height: 320px; display: flex; flex-direction: column; box-shadow: var(--card-shadow); }
.archive-search { padding: 8px 10px; border-bottom: 1px solid var(--card-border); }
.archive-search-input { width: 100%; padding: 8px 10px; border: 1px solid var(--card-border); border-radius: 8px; font-size: 0.82rem; background: var(--input-bg); color: var(--text-1); outline: none; box-sizing: border-box; }
.archive-list { overflow-y: auto; flex: 1; max-height: 200px; }
.archive-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; cursor: pointer; border-bottom: 1px solid var(--card-border); }
.archive-item:active { background: var(--section-alt); }
.archive-checkbox { width: 20px; height: 20px; border-radius: 4px; border: 2px solid var(--card-border); flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; color: #fff; transition: all .15s; }
.archive-checkbox.checked { background: var(--accent); border-color: var(--accent); }
.archive-info { display: flex; flex-wrap: wrap; gap: 4px 8px; align-items: baseline; min-width: 0; }
.archive-name { font-size: 0.9rem; font-weight: 600; color: var(--text-1); }
.archive-gender { font-size: 0.75rem; color: var(--text-3); }
.archive-pillars { font-size: 0.82rem; color: var(--accent); font-weight: 500; letter-spacing: 1px; }
.archive-birth { font-size: 0.72rem; color: var(--text-3); }
.archive-empty { padding: 24px; text-align: center; color: var(--text-3); font-size: 0.85rem; }
.archive-actions { display: flex; justify-content: space-between; padding: 8px 12px; border-top: 1px solid var(--card-border); }
.archive-clear-btn { padding: 6px 14px; border-radius: 8px; font-size: 0.82rem; color: var(--danger); cursor: pointer; }
.archive-confirm-btn { padding: 6px 18px; border-radius: 8px; font-size: 0.82rem; background: var(--accent); color: #fff; cursor: pointer; }
.archive-filter-row { display: flex; gap: 4px; flex-wrap: wrap; }
.archive-filter-tag { padding: 4px 10px; border-radius: 6px; font-size: 0.72rem; border: 1px solid var(--card-border); color: var(--text-3); cursor: pointer; }
.archive-filter-tag.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }
.filter-dropdown { position: absolute; z-index: 100; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 4px 0; margin-top: 4px; min-width: 100px; box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
.filter-dropdown-item { padding: 8px 14px; font-size: 0.8rem; color: var(--text-2); cursor: pointer; white-space: nowrap; }
.filter-dropdown-item:hover { background: rgba(255,255,255,0.06); }
.filter-dropdown-item.active { color: var(--accent); font-weight: 600; }
.archive-selected { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.archive-selected-tag { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 8px; background: var(--accent-glow); border: 1px solid var(--accent); font-size: 0.78rem; color: var(--accent); }
.archive-selected-pillars { font-weight: 600; letter-spacing: 1px; }
.archive-selected-remove { margin-left: 4px; cursor: pointer; opacity: 0.6; font-size: 0.82rem; }
.archive-selected-remove:hover { opacity: 1; }

@media (max-width: 768px) {
  .archive-dropdown,
  .filter-dropdown {
    position: fixed !important;
    top: 120px !important;
    left: 50% !important;
    transform: translateX(-50%) translateZ(0) !important;
    background: rgba(255,255,255,0.65) !important;
    border-color: rgba(255,255,255,0.3) !important;
    border-radius: 20px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.4) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    isolation: isolate !important;
    padding: 6px 0 !important;
    color: #333 !important;
    border-width: 1px !important;
    z-index: 9999 !important;
  }
}
</style>
