<template>
  <view class="page-root" :data-theme="theme">
    <!-- 背景 -->
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- Hero -->
      <view class="about-hero">
        <text class="section-tag">关于我们</text>
        <text class="about-hero-title">时安解忧屋 · 双术数融合命理参考平台</text>
        <text class="about-hero-desc">以八字定先天根基与人生大势，以奇门断当下事件与具体决策，双体系结合更全面</text>
      </view>

      <!-- 信任背书 -->
      <view class="section">
        <text class="section-tag">信任背书</text>
        <text class="section-title">专业排盘体系 权威有据可依</text>
        <text class="section-desc">透明公开排盘规则与算法依据，真实应验案例可查可验证</text>
        <view class="trust-grid">
          <view class="trust-authority">
            <text class="trust-title">📋 排盘内核权威说明</text>
            <view class="auth-item">
              <text class="auth-item-title">奇门遁甲排盘规则</text>
              <text class="auth-item-desc">采用时家奇门拆补法起局，支持置闰法、茅山法切换。用神取日干/时干双参体系，值符值使自动推演，九星八门三奇六仪完整排布。</text>
            </view>
            <view class="auth-item">
              <text class="auth-item-title">八字排盘命理体系</text>
              <text class="auth-item-desc">基于子平术命理体系，支持真太阳时校正。四柱推排、十神分析、大运流年自动计算，五行旺衰量化评分。</text>
            </view>
            <view class="auth-item">
              <text class="auth-item-title">算法依据与数据源</text>
              <text class="auth-item-desc">历法数据对接天文历表，节气精确到分钟级。所有推算逻辑开源可审查，确保排盘结果准确可靠。</text>
            </view>
          </view>
          <view class="case-scroll-wrap">
            <view class="case-tabs">
              <view class="case-tab" id="caseTabAll" @tap="filterCases('all')">全部</view>
              <view class="case-tab" id="caseTabClassic" @tap="filterCases('classic')">经典案例</view>
              <view class="case-tab" id="caseTabReal" @tap="filterCases('real')">实战案例</view>
              <view class="case-tab" id="caseTabCommunity" @tap="filterCases('community')">社区案例</view>
            </view>
            <scroll-view scroll-x class="case-list">
              <view class="case-card" v-for="(c, i) in filteredCases" :key="i">
                <view class="case-badge" :id="'caseBadge' + i">{{ c.sourceLabel }}</view>
                <text class="case-type">{{ c.type }}</text>
                <text class="case-title">{{ c.title }}</text>
                <text class="case-desc">{{ c.desc }}</text>
                <text class="case-verified">{{ c.verified }}</text>
                <text class="case-disclaimer">仅为民俗参考，不代表绝对结果</text>
              </view>
            </scroll-view>
          </view>
        </view>
      </view>

      <!-- 新手入门 -->
      <view class="section-alt">
        <view class="section">
          <text class="section-tag">新手入门</text>
          <text class="section-title">八字+奇门 双术数融合</text>
          <text class="section-desc">以八字定先天根基与人生大势，以奇门断当下事件与具体决策，双体系结合更全面</text>
          <view class="edu-grid">
            <view class="edu-card">
              <text class="edu-icon">📜</text>
              <text class="edu-card-title">八字命理：看透先天格局与人生大运</text>
              <view class="edu-list">
                <text class="edu-li">· 定格局：判断命局基本格局类型</text>
                <text class="edu-li">· 看喜忌：分析五行喜用与忌神</text>
                <text class="edu-li">· 断大运：十年运势走向参考</text>
                <text class="edu-li">· 解姻缘：感情婚姻趋势参考</text>
                <text class="edu-li">· 知财运：财运方位与时机参考</text>
              </view>
              <view class="edu-btns">
                <navigator url="/pages/bazi-index/index" open-type="switchTab" class="btn btn-accent btn-sm">一键排盘</navigator>
              </view>
            </view>
            <view class="edu-card center">
              <text class="edu-icon">☯️</text>
              <text class="edu-card-title">八字+奇门 双体系融合</text>
              <view class="edu-list">
                <text class="edu-li">· 以八字定先天根基与人生大势</text>
                <text class="edu-li">· 以奇门断当下事件与具体决策</text>
                <text class="edu-li">· 双体系结合，给你更全面的人生决策参考</text>
                <text class="edu-li">· 同一平台双体系切换，无需多方求证</text>
              </view>
            </view>
            <view class="edu-card">
              <text class="edu-icon">🔮</text>
              <text class="edu-card-title">奇门遁甲：预判当下事件与吉凶走向</text>
              <view class="edu-list">
                <text class="edu-li">· 一事一断：单事件精准预判参考</text>
                <text class="edu-li">· 吉凶预判：事件发展趋势判断</text>
                <text class="edu-li">· 决策参考：多方案对比选优参考</text>
                <text class="edu-li">· 择时择方：吉时吉方选择参考</text>
                <text class="edu-li">· 趋吉避凶：风险规避方向参考</text>
              </view>
              <view class="edu-btns">
                <navigator url="/pages/qimen/index" open-type="switchTab" class="btn btn-accent btn-sm">一键起局</navigator>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 页脚 -->
    <view class="site-footer">
      <view class="footer-disclaimer">
        ⚠️ 本站所有内容仅为民俗文化与传统命理科普参考，不构成任何决策建议，严禁利用本站内容从事封建迷信及违法违规活动，本站不对任何用户基于本站内容做出的决策承担任何责任
      </view>
      <view class="footer-grid">
        <view class="footer-col">
          <text class="footer-col-title">平台信息</text>
          <text class="footer-link" @tap="showFooterInfo('about')">关于我们</text>
          <text class="footer-link" @tap="showFooterInfo('contact')">联系方式</text>
          <text class="footer-link" @tap="showFooterInfo('privacy')">隐私政策</text>
        </view>
        <view class="footer-col">
          <text class="footer-col-title">快捷导航</text>
          <navigator url="/pages/qimen/index" open-type="switchTab">奇门遁甲</navigator>
          <navigator url="/pages/bazi-index/index" open-type="switchTab">八字排盘</navigator>
          <navigator url="/pages/calendar/index" open-type="switchTab">专属日历</navigator>
          <navigator url="/pages/community/index" open-type="switchTab">社区</navigator>
        </view>
        <view class="footer-col">
          <text class="footer-col-title">备案与版权</text>
          <text class="footer-icp">ICP备案号：京ICP备2026050601号-1</text>
          <text class="footer-copyright">© 2026 时安解忧屋 版权所有</text>
        </view>
      </view>
      <view class="footer-bottom">
        <text>时安解忧屋 · 看得懂用得上的民俗命理参考平台</text>
      </view>
    </view>


  </view>
</template>

<script>
import TopNav from '@/components/TopNav.vue'

export default {
  components: { TopNav },
  data() {
    return {
      theme: (typeof uni !== 'undefined' && uni.getStorageSync('xc_theme')) || 'dark',
      isLoggedIn: !!uni.getStorageSync('xc_token'),
      caseFilter: 'all',
      cases: [
        { source: 'classic', sourceLabel: '经典', type: '事业 · 奇门遁甲', title: '求职面试能否通过', desc: '问事背景：用户面临重要面试，排盘解读结论为利东方方位、午时有利。后续果然在调整面试时间后顺利通过。', verified: '✅ 已应验' },
        { source: 'classic', sourceLabel: '经典', type: '感情 · 奇门遁甲', title: '感情复合时机判断', desc: '问事背景：用户询问与前任复合可能性，排盘显示休门临宫、逢合期在秋分后。用户反馈秋分后确实关系缓和。', verified: '✅ 已应验' },
        { source: 'real', sourceLabel: '实战', type: '财运 · 八字命理', title: '投资理财方向参考', desc: '问事背景：用户询问投资方向，八字分析显示偏财星弱、正财为主，建议稳健理财。用户采纳后避免了高风险损失。', verified: '✅ 已应验' },
        { source: 'real', sourceLabel: '实战', type: '学业 · 奇门遁甲', title: '考试发挥与结果预判', desc: '问事背景：用户询问考研结果，排盘显示景门旺相、文书有利。后续考试发挥顺利，成功上岸。', verified: '✅ 已应验' },
        { source: 'community', sourceLabel: '社区', type: '出行 · 奇门遁甲', title: '长途出行安全预判', desc: '问事背景：用户计划远行，排盘显示驿马星动但逢冲，建议调整出行日期。用户改期后旅途顺利。', verified: '✅ 已应验' },
        { source: 'community', sourceLabel: '社区', type: '事业 · 八字命理', title: '跳槽时机与方向选择', desc: '问事背景：社区用户分享，八字看正官逢冲流年，建议观望至下半年。实际秋季获得更好 offer。', verified: '✅ 已应验' }
      ]
    }
  },
  computed: {
    filteredCases() {
      if (this.caseFilter === 'all') return this.cases
      return this.cases.filter(c => c.source === this.caseFilter)
    }
  },
  onMounted() {
    // #ifdef H5
    this._updateCaseTabs('all')
    this.cases.forEach(function(c, i) {
      var badge = document.getElementById('caseBadge' + i)
      if (badge) badge.classList.add(c.source)
    })
    this._createNativeInputs()
    // #endif
  },
  methods: {
    _createNativeInputs() {
      var self = this
      var pairs = [
        ['aboutLoginUser-wrap', 'aboutLoginUser', 'text', '用户名'],
        ['aboutLoginPass-wrap', 'aboutLoginPass', 'password', '密码'],
        ['aboutRegUser-wrap', 'aboutRegUser', 'text', '用户名'],
        ['aboutRegPass-wrap', 'aboutRegPass', 'password', '密码'],
        ['aboutRegPass2-wrap', 'aboutRegPass2', 'password', '确认密码']
      ]
      var root = document.querySelector('.page-root') || document.documentElement
      var cardBg = getComputedStyle(root).getPropertyValue('--card-bg').trim() || 'rgba(48,53,76,0.85)'
      var cardBorder = getComputedStyle(root).getPropertyValue('--card-border').trim() || 'rgba(255,255,255,0.12)'
      var textColor = getComputedStyle(root).getPropertyValue('--text-1').trim() || 'rgba(240,236,228,0.97)'
      for (var i = 0; i < pairs.length; i++) {
        var wrap = document.getElementById(pairs[i][0])
        if (!wrap) continue
        var inp = document.createElement('input')
        inp.type = pairs[i][2]
        inp.id = pairs[i][1]
        inp.placeholder = pairs[i][3]
        inp.style.cssText = 'width:100%;padding:10px 14px;border-radius:12px;background:' + cardBg + ';border:1.5px solid ' + cardBorder + ';color:' + textColor + ';font-size:0.875rem;outline:none;box-sizing:border-box;'
        wrap.appendChild(inp)
      }
    },
    _updateCaseTabs(active) {
      var tabs = { all: 'caseTabAll', classic: 'caseTabClassic', real: 'caseTabReal', community: 'caseTabCommunity' }
      for (var k in tabs) {
        var el = document.getElementById(tabs[k])
        if (el) { k === active ? el.classList.add('active') : el.classList.remove('active') }
      }
    },
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
      try { uni.setStorageSync('xc_theme', this.theme) } catch (e) {}
      try {
        const root = document.querySelector('.page-root')
        if (root) root.setAttribute('data-theme', this.theme)
        const icon = document.getElementById('themeToggleIcon')
        if (icon) icon.textContent = this.theme === 'dark' ? '🌙' : '☀️'
      } catch(_) {}
    },
    filterCases(filter) {
      this.caseFilter = filter
      this._updateCaseTabs(filter)
    },
    showFooterInfo(type) {
      const titles = { about: '关于我们', contact: '联系方式', privacy: '隐私政策' }
      uni.showModal({ title: titles[type] || type, content: '详细信息请访问网站查看', showCancel: false })
    },

  }
}
</script>

<style scoped>
/* 根容器 & 通用（同 tool-coming） */
.page-root { min-height: 100vh; position: relative; overflow-x: hidden; font-family: 'PingFang SC','Helvetica Neue',-apple-system,sans-serif; font-size: 0.9375rem; line-height: 1.75; color: var(--text-1); }
:root { --ease: cubic-bezier(0.4,0,0.2,1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC','Noto Serif SC','STSong',serif; --max-w: 1280px; }
/* ═══ TopNav 组件所需的 CSS 变量 ═══ */
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --bg-2: rgba(40,45,68,0.80); --accent: hsl(38, 60%, 60%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-border-hover: rgba(255,255,255,0.18); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --text-4: rgba(160,150,135,0.78); --border: rgba(255,255,255,0.12); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --bg-2: rgba(245,240,230,0.80); --accent: hsl(38, 72%, 30%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-border-hover: rgba(0,0,0,0.08); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --text-4: rgba(90,78,58,0.68); --border: rgba(0,0,0,0.045); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }
.bg-layer { position: fixed; top:0; left:0; right:0; bottom:0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%,rgba(45,50,90,0.30) 0%,transparent 72%),radial-gradient(ellipse 65% 50% at 88% 92%,rgba(65,42,18,0.16) 0%,transparent 68%),linear-gradient(162deg,#161a2a,#1a1e30 50%,#141824); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%,rgba(210,190,150,0.20) 0%,transparent 65%),radial-gradient(ellipse 55% 42% at 92% 85%,rgba(195,175,135,0.13) 0%,transparent 60%),linear-gradient(155deg,#f7f2ea,#f0ebe1 60%,#f9f5f0); }
.page-wrap { position: relative; z-index: 1; }

/* About Hero */
.about-hero { max-width: var(--max-w); margin: 0 auto; padding: 100px 24px 48px; text-align: center; }
.about-hero-title { font-family: var(--font-serif); font-size: 1.75rem; letter-spacing: 3px; color: var(--text-1); margin-bottom: 16px; display: block; }
.about-hero-desc { font-size: 0.9375rem; color: var(--text-2); line-height: 1.7; max-width: 640px; margin: 0 auto; display: block; }

/* 通用区块 */
.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.section-alt { background: var(--section-alt); }
.section-tag { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.6875rem; letter-spacing: 2px; color: var(--accent); background: var(--accent-glow); margin-bottom: 12px; }
.section-title { font-family: var(--font-serif); font-size: 1.75rem; font-weight: 400; letter-spacing: 3px; color: var(--text-1); margin-bottom: 8px; display: block; }
.section-desc { color: var(--text-3); font-size: 0.875rem; margin-bottom: 40px; max-width: 600px; display: block; }

/* 信任背书 */
.trust-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
.trust-authority { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; backdrop-filter: blur(16px); }
.trust-title { font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px; margin-bottom: 16px; display: block; color: var(--text-1); }
.auth-item { margin-bottom: 12px; }
.auth-item-title { font-size: 0.8125rem; color: var(--accent); margin-bottom: 4px; display: block; }
.auth-item-desc { font-size: 0.75rem; color: var(--text-3); line-height: 1.6; display: block; }

/* 案例卡片 */
.case-scroll-wrap { overflow: hidden; }
.case-tabs { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.case-tab { padding: 5px 14px; border-radius: 20px; font-size: 0.75rem; border: 1px solid var(--card-border); color: var(--text-3); cursor: pointer; background: transparent; }
.case-tab.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }
.case-list { display: flex; gap: 16px; overflow-x: auto; padding-bottom: 8px; white-space: nowrap; }
.case-card { flex: 0 0 300px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 20px; backdrop-filter: blur(16px); position: relative; }
.case-badge { position: absolute; top: 10px; right: 10px; font-size: 0.5625rem; padding: 2px 6px; border-radius: 4px; color: #fff; }
.case-badge.classic { background: var(--accent); }
.case-badge.real { background: #e67e22; }
.case-badge.community { background: #27ae60; }
.case-type { font-size: 0.6875rem; color: var(--accent); margin-bottom: 8px; letter-spacing: 1px; display: block; }
.case-title { font-size: 0.875rem; margin-bottom: 6px; display: block; color: var(--text-1); }
.case-desc { font-size: 0.75rem; color: var(--text-3); line-height: 1.5; margin-bottom: 8px; display: block; white-space: normal; }
.case-verified { font-size: 0.6875rem; color: var(--success); display: block; }
.case-disclaimer { font-size: 0.625rem; color: var(--text-3); margin-top: 8px; border-top: 1px dashed var(--card-border); padding-top: 8px; display: block; }

/* 教育板块 */
.edu-grid { display: grid; grid-template-columns: 1fr 1.2fr 1fr; gap: 24px; }
.edu-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px 24px; backdrop-filter: blur(16px); text-align: center; }
.edu-card.center { border-color: var(--accent); box-shadow: 0 0 40px var(--accent-glow); }
.edu-icon { font-size: 2.5rem; margin-bottom: 12px; display: block; }
.edu-card-title { font-family: var(--font-serif); font-size: 1rem; letter-spacing: 2px; margin-bottom: 12px; display: block; color: var(--text-1); }
.edu-list { text-align: left; margin-bottom: 20px; }
.edu-li { font-size: 0.8125rem; color: var(--text-2); padding: 4px 0; display: block; }
.edu-btns { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }

/* 按钮 */
.btn { padding: 7px 18px; border-radius: 10px; font-size: 0.8125rem; cursor: pointer; border: none; display: inline-block; text-align: center; }
.btn-outline { background: transparent; border: 1px solid var(--card-border); color: var(--text-2); }
.btn-accent { background: var(--accent); color: #fff; }
.btn-sm { padding: 5px 12px; font-size: 0.75rem; border-radius: 8px; }

/* 页脚 */
.site-footer { background: var(--nav-bg); border-top: 1px solid var(--card-border); padding: 48px 32px 24px; margin-top: 80px; }
.footer-disclaimer { max-width: var(--max-w); margin: 0 auto 32px; padding: 14px 20px; border-radius: 10px; background: rgba(215,125,110,0.08); border: 1px solid rgba(215,125,110,0.15); font-size: 0.75rem; color: var(--danger); line-height: 1.6; text-align: center; }
.footer-grid { max-width: var(--max-w); margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 40px; }
.footer-col-title { font-size: 0.8125rem; color: var(--text-2); margin-bottom: 12px; letter-spacing: 1px; display: block; font-weight: 600; }
.footer-col navigator, .footer-link { display: block; font-size: 0.75rem; color: var(--text-3); text-decoration: none; padding: 3px 0; cursor: pointer; }
.footer-icp { display: block; font-size: 0.75rem; color: var(--text-3); padding: 3px 0; }
.footer-copyright { display: block; font-size: 0.6875rem; color: var(--text-3); margin-top: 8px; }
.footer-bottom { max-width: var(--max-w); margin: 24px auto 0; padding-top: 16px; border-top: 1px solid var(--card-border); text-align: center; }
.footer-bottom text { font-size: 0.6875rem; color: var(--text-3); }

/* 响应式 */
@media (max-width: 768px) {
  .about-hero { padding: 80px 16px 32px; }
  .about-hero-title { font-size: 1.35rem; letter-spacing: 2px; }
  .about-hero-desc { font-size: 0.8125rem; }
  .section { padding: 48px 16px; }
  .trust-grid, .edu-grid { grid-template-columns: 1fr; }
  .footer-grid { grid-template-columns: 1fr; gap: 24px; }
}

/* 弹窗 */
.modal-overlay { display: none; position: fixed; inset: 0; z-index: 300; background: rgba(0,0,0,0.55); backdrop-filter: blur(8px); align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 20px; padding: 32px; width: 360px; backdrop-filter: blur(40px); box-shadow: var(--card-shadow); }
.modal-title { font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px; text-align: center; margin-bottom: 24px; color: var(--text-1); }
.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
input, textarea, select { border-radius: 10px; }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: var(--danger); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }
.btn { padding: 7px 18px; border-radius: 10px; font-size: 0.8125rem; cursor: pointer; border: none; display: inline-flex; align-items: center; justify-content: center; }
.btn-outline { background: transparent; border: 1px solid var(--card-border); color: var(--text-2); }
.btn-accent { background: var(--accent); color: #fff; }
</style>
