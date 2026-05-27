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

              <view class="wz-form-group" id="baziDateSectionAi">
                <text class="wz-form-label">出生时间</text>
                <view class="wz-datetime-row">
                  <view class="wz-dt-col"><select id="baziYearAi" class="wz-datetime-select"></select></view>
                  <view class="wz-dt-col"><select id="baziMonthAi" class="wz-datetime-select"></select></view>
                  <view class="wz-dt-col"><select id="baziDayAi" class="wz-datetime-select"></select></view>
                  <view class="wz-dt-col wz-dt-hour"><select id="baziHourAi" class="wz-datetime-select"></select></view>
                  <view class="wz-dt-col wz-dt-minute"><select id="baziMinuteAi" class="wz-datetime-select"></select></view>
                </view>
                <view class="wz-instant-row">
                  <view class="wz-instant-btn" @tap="wzInstantPaipan">⚡ 即时起局</view>
                  <view class="wz-instant-preview" v-if="instantPreview">{{ instantPreview }}</view>
                </view>
              </view>

              <view class="wz-form-group" id="baziSiziSectionAi" style="display:none;">
                <text class="wz-form-label">直接输入四柱干支</text>
                <view class="wz-sizi-grid">
                  <view class="wz-sizi-row-item"><text class="wz-sizi-label">年柱</text><view id="siziYear-wrap-ai" class="dom-input-wrap"></view></view>
                  <view class="wz-sizi-row-item"><text class="wz-sizi-label">月柱</text><view id="siziMonth-wrap-ai" class="dom-input-wrap"></view></view>
                  <view class="wz-sizi-row-item"><text class="wz-sizi-label">日柱</text><view id="siziDay-wrap-ai" class="dom-input-wrap"></view></view>
                  <view class="wz-sizi-row-item"><text class="wz-sizi-label">时柱</text><view id="siziHour-wrap-ai" class="dom-input-wrap"></view></view>
                </view>
                <text class="wz-form-hint">输入天干+地支各一字，如：甲子、丙寅、戊午、庚申</text>
              </view>

              <view class="wz-divider"></view>

              <view class="wz-form-group">
                <text class="wz-form-label">出生地址</text>
                <view class="wz-addr-selects">
                  <select id="baziProvinceAi" class="wz-addr-select"><option value="">-- 省 --</option></select>
                  <select id="baziCityAi" class="wz-addr-select"><option value="">-- 市 --</option></select>
                  <select id="baziDistrictAi" class="wz-addr-select"><option value="">-- 区 --</option></select>
                </view>
                <input type="hidden" id="baziBirthAddrAi" value="" style="display:none;">
                <input type="hidden" id="baziBirthLngAi" value="0" style="display:none;">
                <input type="hidden" id="baziBirthLatAi" value="0" style="display:none;">
                <view class="wz-addr-info" id="baziAddrInfoAi" style="display:none;">
                  <text class="wz-addr-solar" id="baziAddrSolarAi">真太阳时：--</text>
                  <text class="wz-addr-lng" id="baziAddrLngAi">经度：-- 纬度：--</text>
                </view>
              </view>

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
            </view>

            <view class="wz-divider" style="margin:24px 0 20px;"></view>
            <view class="form-group"><text class="form-label">分析类型</text>
              <view class="analysis-type-row">
                <view class="analysis-type-btn" :class="{ active: baiAnalysisTypeIdx === 0 }" data-bz-action="aiType" data-bz-type-idx="0">📜 命局总览</view>
                <view class="analysis-type-btn" :class="{ active: baiAnalysisTypeIdx === 1 }" data-bz-action="aiType" data-bz-type-idx="1">💰 财运事业</view>
                <view class="analysis-type-btn" :class="{ active: baiAnalysisTypeIdx === 2 }" data-bz-action="aiType" data-bz-type-idx="2">❤️ 婚姻感情</view>
                <view class="analysis-type-btn" :class="{ active: baiAnalysisTypeIdx === 3 }" data-bz-action="aiType" data-bz-type-idx="3">📈 大运流年</view>
                <view class="analysis-type-btn" :class="{ active: baiAnalysisTypeIdx === 4 }" data-bz-action="aiType" data-bz-type-idx="4">🏥 健康六亲</view>
              </view>
            </view>
            <view class="form-group"><text class="form-label">你的问题（选填）</text><view id="baiQuestion-wrap" class="dom-input-wrap"></view></view>
            <view class="submit-btn" data-bz-action="aiAsk">🔮 AI 深度解读</view>
            <view class="qai-stream-box" id="baiStreamBox" style="display:none;">
              <view class="chat-container" id="baiChatContainer"></view>
            </view>
            <view class="chat-input-bar" id="baiChatInputBar" style="display:none;">
              <input class="chat-input" id="baiChatInput" placeholder="继续追问..." />
              <view class="chat-send-btn" data-bz-action="aiFollowUp">发送</view>
            </view>
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
const shichenLabels = ['不确定', '子时 (23-1)', '丑时 (1-3)', '寅时 (3-5)', '卯时 (5-7)', '辰时 (7-9)', '巳时 (9-11)', '午时 (11-13)', '未时 (13-15)', '申时 (15-17)', '酉时 (17-19)', '戌时 (19-21)', '亥时 (21-23)']
window._baiChatHistory = []

var _baiCurrentConvId = null

function _saveBaziConversation(question, birthData) {
  var title = (question || '八字AI解读').substring(0, 50)
  uni.request({
    url: '/api/bazi/conversations', method: 'POST',
    data: {
      title: title,
      messages: window._baiChatHistory || [],
      birth_data: birthData || {}
    },
    success: function(res) {
      if (res.data && res.data.id) _baiCurrentConvId = res.data.id
      window.__sidebarCache = null
    },
    fail: function(err) { console.error('[bazi] 保存对话失败:', err) }
  })
}

function _updateBaziConversation() {
  if (!_baiCurrentConvId) return
  uni.request({
    url: '/api/bazi/conversations', method: 'POST',
    data: { id: _baiCurrentConvId, messages: window._baiChatHistory || [] },
    success: function() { window.__sidebarCache = null },
    fail: function(err) { console.error('[bazi] 更新对话失败:', err) }
  })
}

function _checkBaziRestore() {
  var d = window.__xc_restoreData
  if (!d || d.type !== 'bazi') return
  window.__xc_restoreData = null
  switchBaziTab('ai')
  var messages = d.messages || []
  if (!messages.length) return
  window._baiChatHistory = messages.slice()
  _baiCurrentConvId = d.id || null
  var streamBox = document.getElementById('baiStreamBox')
  if (streamBox) streamBox.style.display = 'block'
  var chatContainer = document.getElementById('baiChatContainer')
  if (!chatContainer) return
  chatContainer.innerHTML = ''
  messages.forEach(function(m) {
    var cls = m.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'
    var content = (m.content || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
    var bubble = document.createElement('div')
    bubble.className = cls
    if (m.role === 'assistant') {
      bubble.innerHTML = '<div class="chat-bubble-content">' + content + '</div>'
    } else {
      bubble.innerHTML = '<div class="chat-bubble-text">' + content + '</div>'
    }
    chatContainer.appendChild(bubble)
  })
  chatContainer.scrollTop = chatContainer.scrollHeight
  var inputBar = document.getElementById('baiChatInputBar')
  if (inputBar) inputBar.style.display = 'flex'
}

window._xc_restoreBazi = function() {
  nextTick(function() { _checkBaziRestore() })
}

async function baiAiAsk() {
  window._baiAiAsk = baiAiAsk
  if (baiAiLoading.value) return

  // 从AI Tab表单读取（带Ai后缀的ID）
  var yEl = document.getElementById('baziYearAi'); var mEl = document.getElementById('baziMonthAi')
  var dEl = document.getElementById('baziDayAi'); var hEl = document.getElementById('baziHourAi')
  var miEl = document.getElementById('baziMinuteAi')
  if (!yEl || !mEl || !dEl) { uni.showToast({ title: '请选择出生日期', icon: 'none' }); return }

  var now = new Date()
  var defYear = now.getFullYear(), defMonth = now.getMonth() + 1, defDay = now.getDate()
  var defHour = now.getHours(), defMin = now.getMinutes()

  var yVal = yEl.value || String(defYear)
  var mVal = mEl.value || String(defMonth)
  var dVal = dEl.value || String(defDay)
  var hVal = hEl && hEl.value ? String(hEl.value).padStart(2, '0') : String(defHour).padStart(2, '0')
  var miVal = miEl && miEl.value ? String(miEl.value).padStart(2, '0') : String(defMin).padStart(2, '0')

  var d = yVal + String(mVal).padStart(2, '0') + String(dVal).padStart(2, '0')
  var h = hVal; var mi = miVal
  var gender = baziGender.value
  var calType = baziCalType.value
  var question = ((document.getElementById('baiQuestion') || {}).value || '').trim()
  var birthAddr = (document.getElementById('baziBirthAddrAi') || {}).value || ''
  var birthLng = parseFloat((document.getElementById('baziBirthLngAi') || {}).value) || 0
  var birthLat = parseFloat((document.getElementById('baziBirthLatAi') || {}).value) || 0

  // 清理 — 先设 loading
  baiAiLoading.value = true
  baziAiResult.value = ''; window._baiChatHistory = []
  var streamBox = document.getElementById('baiStreamBox')
  if (streamBox) streamBox.style.display = 'block'
  var chatContainer = document.getElementById('baiChatContainer')
  if (chatContainer) chatContainer.innerHTML = ''
  var inputBar = document.getElementById('baiChatInputBar')
  if (inputBar) inputBar.style.display = 'none'

  var bubbleId = 'baiBubble_' + Date.now()
  var bubbleHTML = '<div class="chat-bubble-ai" id="' + bubbleId + '">' +
    '<div class="ai-stage">🔗 正在连接 DeepSeek AI 引擎...</div>' +
    '<div class="ai-progress-bar"><div class="ai-progress-fill" style="width:20%"></div></div>' +
    '<div class="chat-bubble-content"></div></div>'
  if (chatContainer) chatContainer.innerHTML = bubbleHTML

  _baiDoStreamSSE({
    bubbleId: bubbleId, url: '/api/bazi/ask/stream',
    body: { birth: d + h + mi, gender: gender, cal_type: calType, question: question, analysis_type: baiAnalysisTypes[baiAnalysisTypeIdx], birth_addr: birthAddr, birth_lng: birthLng, birth_lat: birthLat },
    question: question,
    onDone: function(fullText) {
      window._baiChatHistory = [{ role: 'user', content: question }, { role: 'assistant', content: fullText }]
      baziAiResult.value = fullText
      var bar = document.getElementById('baiChatInputBar'); if (bar) bar.style.display = 'flex'
      _baiCurrentConvId = null
      _saveBaziConversation(question, {
        birth: d + h + mi, gender: gender, cal_type: calType,
        birth_addr: birthAddr, birth_lng: birthLng, birth_lat: birthLat,
        analysis_type: baiAnalysisTypes[baiAnalysisTypeIdx]
      })
    },
    onError: function() { baiAiLoading.value = false }
  })
}

function _baiDoStreamSSE(opts) {
  var bubble = document.getElementById(opts.bubbleId); if (!bubble) { console.error('[bazi] bubble not found'); return }
  var stageEl = bubble.querySelector('.ai-stage'); var barEl = bubble.querySelector('.ai-progress-fill')
  var contentEl = bubble.querySelector('.chat-bubble-content')
  var fullText = '', charQueue = '', typeTimer = null, doneReceived = false
  function startTypewriter() {
    if (typeTimer) return
    typeTimer = setInterval(function() {
      if (charQueue.length === 0 && doneReceived) {
        clearInterval(typeTimer); typeTimer = null
        baiAiLoading.value = false
        if (stageEl) stageEl.style.display = 'none'
        var barWrap = bubble.querySelector('.ai-progress-bar'); if (barWrap) barWrap.style.display = 'none'
        if (contentEl) contentEl.innerHTML = _baiRenderCards(fullText)
        if (opts.onDone) opts.onDone(fullText); return
      }
      if (charQueue.length === 0) return
      var take = charQueue.length > 3 ? 2 : 1
      fullText += charQueue.substring(0, take); charQueue = charQueue.substring(take)
      if (contentEl) contentEl.innerHTML = _stripMarkdown(fullText).replace(/\n/g, '<br>')
    }, 35)
  }
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  var xhr = new XMLHttpRequest()
  xhr.open('POST', opts.url, false)
  xhr.setRequestHeader('Content-Type', 'application/json')
  if (token) xhr.setRequestHeader('Authorization', 'Bearer ' + token)
  xhr.send(JSON.stringify(opts.body))
  if (xhr.status >= 200 && xhr.status < 300 && xhr.responseText) {
    var text = xhr.responseText
    var lines = text.split('\n')
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i]
      if (line.indexOf('data:') !== 0) continue
      try {
        var data = JSON.parse(line.replace('data:', '').trim())
        if (data.type === 'chunk' || data.type === 'delta') {
          if (!typeTimer) startTypewriter()
          charQueue += data.content
        } else if (data.type === 'done') {
          doneReceived = true
        } else if (data.type === 'error') {
          if (stageEl) stageEl.innerHTML = '⚠️ ' + data.message; if (opts.onError) opts.onError()
        }
      } catch(_) {}
    }
  } else {
    if (stageEl) stageEl.innerHTML = '⚠️ 服务器错误 ' + xhr.status
    if (opts.onError) opts.onError()
  }
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

function baiSendFollowUp() {
  window._baiSendFollowUp = baiSendFollowUp
  var input = document.querySelector('#baiChatInput input') || document.getElementById('baiChatInput'); if (!input) return
  var question = input.value.trim(); if (!question) return; input.value = ''
  var chatContainer = document.getElementById('baiChatContainer'); if (!chatContainer) return
  var userBubble = document.createElement('view'); userBubble.className = 'chat-bubble-user'; userBubble.textContent = question
  chatContainer.appendChild(userBubble)
  var bubbleId = 'baiFollow_' + Date.now()
  var aiBubble = document.createElement('view'); aiBubble.className = 'chat-bubble-ai'; aiBubble.id = bubbleId
  aiBubble.innerHTML = '<div class="ai-stage"><img class="ai-stage-logo" src="/static/images/logo.webp?v=2">正在生成回复...</div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:60%"></div></div><div class="chat-bubble-content"></div>'
  chatContainer.appendChild(aiBubble); chatContainer.scrollIntoView({ behavior: 'smooth', block: 'end' })
  var history = window._baiChatHistory || []; history.push({ role: 'user', content: question })
  _baiDoStreamSSE({
    bubbleId: bubbleId, url: '/api/bazi/ask/stream', body: { question: question, history: history },
    question: question,
    onDone: function(fullText) {
      history.push({ role: 'assistant', content: fullText }); window._baiChatHistory = history
      if (_baiCurrentConvId) { _updateBaziConversation() } else { _saveBaziConversation(question, {}) }
    },
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
  // DOM click 绑定（事件代理，uni-view 的 @tap/@click 不生效）
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
        if (sendBtn) { baiSendFollowUp(); return }
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

  document.getElementById('recordSearch')
  const searchVal = searchEl ? searchEl.value : recordSearch.value
  if (catFilter.value !== '全部') list = list.filter(r => r.category === catFilter.value)
  if (searchVal) { const q = searchVal.toLowerCase(); list = list.filter(r => (r.name || '').toLowerCase().includes(q)) }
  return list
})

function onRecordSearch() {
  const el = 
  // DOM click 绑定（事件代理，uni-view 的 @tap/@click 不生效）
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
        if (sendBtn) { baiSendFollowUp(); return }
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

function loadRecords() {
  uni.request({
    url: '/api/bazi/history',
    method: 'GET',
    success: function(res) {
      if (res.data && Array.isArray(res.data)) {
        records.value = res.data
      } else if (res.data && res.data.success && Array.isArray(res.data.records)) {
        records.value = res.data.records
      }
    },
    fail: function(err) { console.error('[bazi] 加载排盘记录失败:', err) }
  })
}

function deleteRecord(id) {
  if (!id) return
  uni.request({
    url: '/api/bazi/history/delete',
    method: 'POST',
    data: { id: id },
    success: function() {
      records.value = records.value.filter(function(r) { return r.id !== id })
    },
    fail: function(err) { console.error('[bazi] 删除记录失败:', err) }
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
  // AI Tab激活时：初始化select选项（免费Tab先初始化，AI Tab需要同步）
  if (tab === 'ai') {
    nextTick(function() { _initAiTabSelects() })
  }
}

// AI Tab：同步免费Tab的select选项到AI Tab
function _initAiTabSelects() {
  var freeTabIds = ['baziYear', 'baziMonth', 'baziDay', 'baziHour', 'baziMinute']
  var aiTabIds = ['baziYearAi', 'baziMonthAi', 'baziDayAi', 'baziHourAi', 'baziMinuteAi']
  for (var i = 0; i < freeTabIds.length; i++) {
    var freeEl = document.getElementById(freeTabIds[i])
    var aiEl = document.getElementById(aiTabIds[i])
    if (freeEl && aiEl) {
      aiEl.innerHTML = freeEl.innerHTML
      aiEl.value = freeEl.value
    }
  }
  var freeAddrIds = ['baziProvince', 'baziCity', 'baziDistrict']
  var aiAddrIds = ['baziProvinceAi', 'baziCityAi', 'baziDistrictAi']
  for (var j = 0; j < freeAddrIds.length; j++) {
    var freeAddrEl = document.getElementById(freeAddrIds[j])
    var aiAddrEl = document.getElementById(aiAddrIds[j])
    if (freeAddrEl && aiAddrEl) {
      aiAddrEl.innerHTML = freeAddrEl.innerHTML
      aiAddrEl.value = freeAddrEl.value
    }
  }
  _initAiTabAddrListeners()
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
          if (action === 'aiAsk' && window._baiAiAsk) window._baiAiAsk()
          else if (action === 'aiFollowUp' && window._baiSendFollowUp) window._baiSendFollowUp()
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
    
    // 也初始化 AI Tab 的地址选择器
    _initAiTabSelects()
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
