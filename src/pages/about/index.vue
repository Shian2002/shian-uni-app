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

      <!-- 产品导航 -->
      <section class="section">
        <view class="section-tag">产品导航</view>
        <view class="section-title">全方位命理参考工具</view>
        <view class="hero-cards">
          <view @tap="goToPage('/pages/qimen/index')" class="hero-card hero-card-primary">
            <view class="hero-card-glow"></view>
            <view class="hero-card-content">
              <view class="hero-card-icon">🔮</view>
              <view class="hero-card-title">奇门遁甲</view>
              <view class="hero-card-desc">一事一断 · 吉凶预判 · 择时择方</view>
              <view class="hero-card-features">
                <view class="hero-card-tag">时安奇门系统</view>
                <view class="hero-card-tag free">免费排盘</view>
              </view>
              <view class="hero-card-arrow">→</view>
            </view>
          </view>

          <view @tap="goToPage('/pages/bazi-index/index')" class="hero-card hero-card-primary">
            <view class="hero-card-glow"></view>
            <view class="hero-card-content">
              <view class="hero-card-icon">📜</view>
              <view class="hero-card-title">八字排盘</view>
              <view class="hero-card-desc">定格局 · 看喜忌 · 断大运 · 知财运</view>
              <view class="hero-card-features">
                <view class="hero-card-tag">时安八字系统</view>
                <view class="hero-card-tag free">免费排盘</view>
              </view>
              <view class="hero-card-arrow">→</view>
            </view>
          </view>

          <view class="hero-mini-scroll">
            <view @tap="goToPage('/pages/liuyao/index')" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">🧭</view>
                <view class="hero-card-title">六爻排盘</view>
              </view>
            </view>
            <view @tap="goToPage('/pages/meihua/index')" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">🌸</view>
                <view class="hero-card-title">梅花易数</view>
              </view>
            </view>
            <view @tap="goToPage('/pages/ziwei/index')" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">⭐</view>
                <view class="hero-card-title">紫微斗数</view>
              </view>
            </view>
            <view @tap="goToPage('/pages/tarot/index')" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">🃏</view>
                <view class="hero-card-title">塔罗牌</view>
              </view>
            </view>
            <view @tap="goToPage('/pages/zeji/index')" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">📅</view>
                <view class="hero-card-title">择吉工具</view>
              </view>
            </view>
            <view @tap="goToPage('/pages/calendar/index')" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">🗓️</view>
                <view class="hero-card-title">专属日历</view>
              </view>
            </view>
            <view v-if="showCommunityEntry" @tap="goToPage('/pages/community/index')" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">💬</view>
                <view class="hero-card-title">交流社区</view>
              </view>
            </view>
          </view>
        </view>
      </section>

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
              <text class="auth-item-desc">采用时家奇门拆补法起局。用神取日干/时干双参体系，值符值使自动推演，九星八门三奇六仪完整排布。</text>
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
              <view v-if="showCommunityEntry" class="case-tab" id="caseTabCommunity" @tap="filterCases('community')">社区案例</view>
            </view>
            <view class="case-list">
              <view class="case-card" v-for="(c, i) in filteredCases" :key="i">
                <view class="case-header">
                  <view class="case-avatar" :style="{ background: c.avatarColor }">{{ c.avatar }}</view>
                  <view class="case-user-info">
                    <text class="case-nickname">{{ c.nickname }}</text>
                    <text class="case-date">{{ c.date }}</text>
                  </view>
                  <view class="case-badge" :id="'caseBadge' + i">{{ c.sourceLabel }}</view>
                </view>
                <view class="case-type">{{ c.type }}</view>
                <view class="case-q">
                  <text class="case-q-label">问</text>
                  <text class="case-q-text">{{ c.question }}</text>
                </view>
                <view class="case-a">
                  <text class="case-a-label">答</text>
                  <text class="case-a-text">{{ c.answer }}</text>
                </view>
                <view class="case-result">
                  <text class="case-verified">{{ c.verified }}</text>
                  <text class="case-feedback">{{ c.feedback }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 核心特色 -->
      <section class="section">
        <view class="section-tag">核心特色</view>
        <view class="section-title">双术数融合 · 更全面的命理参考</view>
        <view class="section-desc">以八字定先天根基与人生大势，以奇门断当下事件与具体决策</view>
        <view class="feature-scroll-wrap">
          <view class="feature-grid">
            <view class="feature-card" v-for="f in features" :key="f.title">
              <view class="feature-icon">{{ f.icon }}</view>
              <view class="feature-card-title">{{ f.title }}</view>
              <view class="feature-card-desc">{{ f.desc }}</view>
            </view>
          </view>
        </view>
      </section>

      <!-- 快速场景 -->
      <view class="section-alt">
        <section class="section">
          <view class="section-tag">快速场景</view>
          <view class="section-title">针对具体事件精准起局</view>
          <view class="section-desc">选择你的场景，一键获取专业解读参考</view>
          <view class="scenario-scroll-wrap">
            <view class="scenario-grid">
              <view class="scenario-card" v-for="s in scenarios" :key="s.key" @tap="goScenario(s.key)">
                <text class="scenario-emoji">{{ s.emoji }}</text>
                <view class="scenario-card-title">{{ s.title }}</view>
              </view>
            </view>
          </view>
        </section>
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

      <!-- 新手常见问题 -->
      <section class="section faq-section">
        <view class="faq-panel" id="faqPanel">
          <view class="faq-panel-header" id="faqPanelHeader" @tap="toggleFaqPanel">
            <view class="faq-panel-title">❓ 新手常见问题</view>
            <view class="faq-panel-arrow" id="faqPanelArrow">▲</view>
          </view>
          <view class="faq-panel-body" id="faqPanelBody">
            <view class="faq-item" v-for="(faq, idx) in faqs" :key="faq.q">
              <view class="faq-q" :id="'faqQ' + idx" @tap="toggleFaq(idx)">
                <text>{{ faq.q }}</text>
                <text class="arrow" :id="'faqArrow' + idx">▼</text>
              </view>
              <view class="faq-a" :id="'faqA' + idx">{{ faq.a }}</view>
            </view>
          </view>
        </view>
      </section>

      <!-- 页脚 -->
      <view class="site-footer">
        <view class="footer-disclaimer">
          ⚠️ 本站所有内容仅为民俗文化与传统命理科普参考，不构成任何决策建议，严禁利用本站内容从事封建迷信及违法违规活动，本站不对任何用户基于本站内容做出的决策承担任何责任
        </view>
        <view class="footer-grid">
          <view class="footer-col">
            <view class="footer-col-title">平台信息</view>
            <navigator url="/package-info/about/index">关于我们</navigator>
            <view class="footer-link" @tap="showFooterInfo('contact')">联系方式</view>
            <view class="footer-link" @tap="showFooterInfo('terms')">用户协议</view>
            <view class="footer-link" @tap="showFooterInfo('privacy')">隐私政策</view>
            <view class="footer-link" @tap="showFooterInfo('disclaimer')">完整免责声明</view>
          </view>
          <view class="footer-col">
            <view class="footer-col-title">快捷导航</view>
            <view class="footer-link" @tap="goToPage('/pages/qimen/index')">奇门遁甲</view>
            <view class="footer-link" @tap="goToPage('/pages/bazi-index/index')">八字排盘</view>
            <view class="footer-link" @tap="goToPage('/pages/calendar/index')">专属日历</view>
            <view v-if="showCommunityEntry" class="footer-link" @tap="goToPage('/pages/community/index')">社区</view>
            <navigator url="/package-info/about/index">关于我们</navigator>
          </view>
          <view class="footer-col">
            <view class="footer-col-title">备案与版权</view>
            <view class="footer-icp footer-icp-link" @tap="openMiitBeian">ICP备案号：粤ICP备2026072162号-1</view>
            <view class="footer-link" @tap="showFooterInfo('copyright')">版权信息</view>
            <view class="footer-icp">© 2026 时安解忧屋 版权所有</view>
          </view>
        </view>
        <view class="footer-bottom">
          <text class="footer-bottom-text">时安解忧屋 · 看得懂用得上的民俗命理参考平台</text>
          <view class="btn-clear-data" @tap="clearAllData">🗑️ 一键清空所有数据</view>
        </view>
      </view>

    </view>

  </view>
</template>

<script>
import TopNav from '@/components/TopNav.vue'

const SHOW_COMMUNITY_ENTRY = import.meta.env.DEV || import.meta.env.VITE_SHOW_COMMUNITY === '1'

export default {
  components: { TopNav },
  data() {
    return {
      theme: (typeof uni !== 'undefined' && uni.getStorageSync('xc_theme')) || 'dark',
      isLoggedIn: !!uni.getStorageSync('xc_token'),
      showCommunityEntry: SHOW_COMMUNITY_ENTRY,
      caseFilter: 'all',
      cases: [
        { source: 'classic', sourceLabel: '经典', avatar: '陈', avatarColor: 'linear-gradient(135deg,#b2955d,#d4a853)', nickname: '陈先生', date: '2025.03', type: '事业 · 奇门遁甲', question: '下周有一场重要面试，能否顺利通过？', answer: '排盘显示开门临宫，利东方方位，午时最为有利。建议调整面试时间至上午，着深色正装。', feedback: '调整时间后顺利拿到offer！', verified: '✅ 已应验' },
        { source: 'classic', sourceLabel: '经典', avatar: '林', avatarColor: 'linear-gradient(135deg,#e67e22,#f39c12)', nickname: '林女士', date: '2025.01', type: '感情 · 奇门遁甲', question: '和前任还有复合的可能吗？什么时候比较合适？', answer: '休门临宫，逢合期在秋分前后。双方暂需冷静，不宜急于联系，秋分后关系自然缓和。', feedback: '秋分后真的慢慢联系上了', verified: '✅ 已应验' },
        { source: 'real', sourceLabel: '实战', avatar: '王', avatarColor: 'linear-gradient(135deg,#27ae60,#2ecc71)', nickname: '王先生', date: '2025.04', type: '财运 · 八字命理', question: '最近有一笔投资机会，适合投入吗？', answer: '八字分析显示偏财星弱、正财为主，流年财星受制。建议稳健理财，不宜大额高风险投入。', feedback: '听劝没投，朋友投了亏了不少', verified: '✅ 已应验' },
        { source: 'real', sourceLabel: '实战', avatar: '赵', avatarColor: 'linear-gradient(135deg,#3498db,#2980b9)', nickname: '赵同学', date: '2025.02', type: '学业 · 奇门遁甲', question: '今年考研能否上岸？', answer: '景门旺相、文书星有利，考场方位利东南。用神得位，发挥正常则结果可期。', feedback: '成功上岸了！感谢', verified: '✅ 已应验' },
        ...(SHOW_COMMUNITY_ENTRY ? [
          { source: 'community', sourceLabel: '社区', avatar: '周', avatarColor: 'linear-gradient(135deg,#9b59b6,#8e44ad)', nickname: '周女士', date: '2025.05', type: '出行 · 奇门遁甲', question: '计划月底长途出行，安全吗？需要注意什么？', answer: '驿马星动但逢冲，原定日期不太理想。建议推迟一周，避开冲煞日，旅途会更加顺利。', feedback: '改期后一路顺风', verified: '✅ 已应验' },
          { source: 'community', sourceLabel: '社区', avatar: '李', avatarColor: 'linear-gradient(135deg,#e74c3c,#c0392b)', nickname: '李先生', date: '2025.03', type: '事业 · 八字命理', question: '现在跳槽时机合适吗？还是再等等？', answer: '正官逢冲流年，上半年不宜轻动。下半年印星得力，事业有贵人相助，届时机会更好。', feedback: '秋季确实拿到了更好的offer', verified: '✅ 已应验' }
        ] : [])
      ],
      features: [
        { icon: '🔮', title: '时安深度解读', desc: '小白极简版 + 专业深度版，专业术语点击即弹出大白话释义' },
        { icon: '⚡', title: '秒出排盘', desc: '本地精准排盘引擎，基于天文历表，节气精确到分钟级' },
        { icon: '🔄', title: '双体系互补', desc: '八字看"命里有没有"，奇门看"现在该怎么做"，双体系结合更全面' },
        { icon: '📜', title: '古籍加持', desc: '融合《渊海子平》《奇门旨归》等经典古籍，以古法为基，以今用为归' },
        { icon: '📱', title: '全端适配', desc: '桌面端、平板、手机全端适配，随时随地查排盘' },
        { icon: '🎯', title: '场景化问事', desc: '面试能否通过、项目能否回款、感情复合时机等快速场景一键起局' },
      ],
      scenarios: [
        { key: 's_interview', emoji: '💼', title: '面试能否通过' },
        { key: 's_project', emoji: '💰', title: '项目能否回款' },
        { key: 's_loveback', emoji: '💕', title: '感情复合时机' },
        { key: 's_house', emoji: '🏠', title: '买房租房吉凶' },
        { key: 's_travel', emoji: '✈️', title: '出行安全预判' },
        { key: 's_business', emoji: '🏪', title: '开业签约择吉' },
      ],
      faqs: [
        { q: '排盘时间怎么选？', a: '新手模式下默认使用当前时间，这也是最常用的起局方式。奇门遁甲讲究"当时当刻"，用问事时刻起局即可。', open: false },
        { q: '解读结果怎么看？', a: '建议新手先看"小白极简版"，只保留核心结论和行动建议。有基础后可切换"专业深度版"。', open: false },
        { q: '八字和奇门该用哪个？', a: '看整体运势用八字，看具体事件用奇门。两者结合使用效果更全面。', open: false },
      ]
    }
  },
  computed: {
    filteredCases() {
      const visibleCases = this.showCommunityEntry ? this.cases : this.cases.filter(c => c.source !== 'community')
      if (this.caseFilter === 'all') return visibleCases
      return visibleCases.filter(c => c.source === this.caseFilter)
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
      const infoMap = {
        contact: '联系方式：可通过站内反馈或邮件联系处理问题与建议。涉及账号、积分、订单、内容纠错时，请尽量提供登录手机号、发生时间、页面名称和截图，便于核验处理。',
        terms: '用户协议：使用本站即表示你理解并同意，本平台提供的是传统民俗文化、命理排盘与解读参考服务。你应自行判断内容适用性，不得利用本站内容从事违法违规、诈骗、恐吓、诱导交易或损害他人权益的行为。',
        privacy: '隐私政策：本站仅在提供排盘、保存命盘、内容互动、积分与订单服务时处理必要信息。出生信息、命盘档案、提问内容会用于生成解读和历史记录展示；你可以在用户管理中自行维护或删除相关资料。',
        disclaimer: '完整免责声明：本站所有排盘、解读、择吉、日历、案例内容均为传统民俗文化参考，不构成医疗、法律、投资、婚恋、人事或其他现实决策建议。重大事项请结合现实证据与专业人士意见独立判断。',
        copyright: '版权信息：© 2026 时安解忧屋 版权所有。本站页面设计、排盘展示、原创文案、解读模板与互动内容受相关法律保护；未经许可不得批量抓取、复制、镜像或用于商业再分发。',
      }
      uni.showModal({ title: '提示', content: infoMap[type] || '', showCancel: false })
    },
    openMiitBeian() {
      // #ifdef H5
      try {
        window.open('https://beian.miit.gov.cn/', '_blank', 'noopener,noreferrer')
        return
      } catch(_) {}
      // #endif
      uni.showModal({
        title: '备案信息',
        content: 'ICP备案号：粤ICP备2026072162号-1\n工信部备案官网：https://beian.miit.gov.cn/',
        showCancel: false
      })
    },
    clearAllData() {
      uni.showModal({
        title: '确认清空',
        content: '确认清空所有本地数据？此操作不可撤销。',
        success: (res) => {
          if (res.confirm) {
            var _savedTheme = uni.getStorageSync('xc_theme')
            uni.clearStorageSync()
            if (_savedTheme) uni.setStorageSync('xc_theme', _savedTheme)
            uni.showToast({ title: '已清空', icon: 'success' })
          }
        }
      })
    },
    goToPage(url) {
      uni.switchTab({ url: url })
    },
    goScenario(key) {
      try { sessionStorage.setItem('_nav_query', '?scenario=' + key) } catch(_) {}
      uni.switchTab({
        url: '/pages/qimen/index',
        success: function() {
          setTimeout(function() { try { uni.$emit('nav-query', '?scenario=' + key) } catch(_) {} }, 200)
        }
      })
    },
    toggleFaqPanel() {
      var panel = document.getElementById('faqPanel')
      if (panel) panel.classList.toggle('open')
      var body = document.getElementById('faqPanelBody')
      if (body) body.classList.toggle('open')
      var arrow = document.getElementById('faqPanelArrow')
      if (arrow) arrow.classList.toggle('rotated')
    },
    toggleFaq(idx) {
      var a = document.getElementById('faqA' + idx)
      var arrow = document.getElementById('faqArrow' + idx)
      if (a) a.classList.toggle('open')
      if (arrow) arrow.classList.toggle('rotated')
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

/* 产品导航卡片 */
.hero-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 20px; }
.hero-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 28px 24px; backdrop-filter: blur(20px); cursor: pointer; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); position: relative; overflow: hidden; }
.hero-card:hover { transform: translateY(-6px) scale(1.02); border-color: rgba(255, 255, 255, 0.18); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 40px var(--accent-glow); }
.hero-card-glow { position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle at center, var(--accent-glow) 0%, transparent 70%); opacity: 0; transition: opacity 0.4s; pointer-events: none; }
.hero-card:hover .hero-card-glow { opacity: 1; }
.hero-card-content { position: relative; z-index: 1; }
.hero-card-icon { font-size: 2.5rem; margin-bottom: 16px; }
.hero-card-title { font-family: var(--font-serif); font-size: 1.25rem; font-weight: 400; letter-spacing: 4px; color: var(--text-1); margin-bottom: 8px; }
.hero-card-desc { font-size: 0.8125rem; color: var(--text-3); letter-spacing: 1px; margin-bottom: 16px; line-height: 1.6; }
.hero-card-features { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.hero-card-tag { padding: 4px 12px; border-radius: 20px; font-size: 0.6875rem; background: var(--accent-glow); color: var(--accent); border: 1px solid rgba(255,255,255,0.06); letter-spacing: 1px; }
.hero-card-tag.free { background: rgba(110,195,135,0.1); color: var(--success); }
.hero-card-arrow { font-size: 1.25rem; color: var(--accent); opacity: 0; transform: translateX(-8px); transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.hero-card:hover .hero-card-arrow { opacity: 1; transform: translateX(0); }
.hero-card-primary { grid-column: span 2; background: rgba(255, 255, 255, 0.06); border-color: rgba(255, 255, 255, 0.12); text-align: center; }
.hero-card-primary:hover { border-color: var(--accent); }
.hero-card-primary .hero-card-icon { text-align: center; }
.hero-card-primary .hero-card-title { text-align: center; }
.hero-card-primary .hero-card-desc { text-align: center; }
.hero-card-primary .hero-card-features { justify-content: center; }
.hero-mini-scroll { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; grid-column: 1 / -1; position: relative; }
.hero-card-mini { background: rgba(255, 255, 255, 0.02); border-color: rgba(255, 255, 255, 0.05); padding: 18px 8px; border-radius: 14px; }
.hero-card-mini:hover { transform: translateY(-3px) scale(1.01); border-color: rgba(255, 255, 255, 0.12); box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
.hero-card-mini .hero-card-content { display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center; }
.hero-card-mini .hero-card-icon { font-size: 1.75rem; margin-bottom: 0; flex-shrink: 0; }
.hero-card-mini .hero-card-title { font-size: 0.8125rem; letter-spacing: 1px; margin-bottom: 0; }
.hero-card-mini .hero-card-arrow { display: none; }
.hero-card-mini .hero-card-desc { display: none; }
.hero-card-mini .hero-card-features { display: none; }

/* 通用区块 */
.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.section-alt { background: var(--section-alt); }
.section-tag { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.6875rem; letter-spacing: 2px; color: var(--accent); background: var(--accent-glow); margin-bottom: 12px; }
.section-title { font-family: var(--font-serif); font-size: 1.75rem; font-weight: 400; letter-spacing: 3px; color: var(--text-1); margin-bottom: 8px; display: block; }
.section-desc { color: var(--text-3); font-size: 0.875rem; margin-bottom: 40px; max-width: 600px; display: block; }

/* 信任背书 */
.trust-grid { display: grid; grid-template-columns: 280px 1fr; gap: 24px; align-items: stretch; }
.trust-authority { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 20px; backdrop-filter: blur(16px); height: 100%; box-sizing: border-box; }
.trust-title { font-family: var(--font-serif); font-size: 0.9rem; letter-spacing: 2px; margin-bottom: 12px; display: block; color: var(--text-1); }
.auth-item { margin-bottom: 10px; }
.auth-item-title { font-size: 0.75rem; color: var(--accent); margin-bottom: 3px; display: block; }
.auth-item-desc { font-size: 0.6875rem; color: var(--text-3); line-height: 1.5; display: block; }

/* 案例卡片 */
.case-scroll-wrap { position: relative; min-width: 0; height: 100%; display: flex; flex-direction: column; }
.case-scroll-wrap::after {
  content: ''; position: absolute; top: 0; right: 0; width: 60px; height: 100%;
  background: linear-gradient(to right, transparent, var(--bg));
  pointer-events: none; z-index: 3;
}
.case-tabs { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; position: relative; z-index: 2; flex-shrink: 0; }
.case-tab { padding: 5px 14px; border-radius: 20px; font-size: 0.75rem; border: 1px solid var(--card-border); color: var(--text-3); cursor: pointer; background: transparent; }
.case-tab.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }
.case-list { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; gap: 16px; overflow-x: auto; padding-bottom: 8px; -webkit-overflow-scrolling: touch; position: relative; z-index: 2; flex: 1; min-height: 0; }
.case-list::-webkit-scrollbar { height: 4px; }
.case-list::-webkit-scrollbar-thumb { background: var(--card-border); border-radius: 2px; }
.case-card { flex: 0 0 280px !important; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 16px; backdrop-filter: blur(16px); position: relative; }
.case-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.case-avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; color: #fff; flex-shrink: 0; font-weight: 500; }
.case-user-info { flex: 1; min-width: 0; }
.case-nickname { font-size: 0.8125rem; color: var(--text-1); display: block; font-weight: 500; }
.case-date { font-size: 0.625rem; color: var(--text-3); display: block; margin-top: 1px; }
.case-badge { font-size: 0.5625rem; padding: 2px 6px; border-radius: 4px; color: #fff; flex-shrink: 0; }
.case-badge.classic { background: var(--accent); }
.case-badge.real { background: #e67e22; }
.case-badge.community { background: #27ae60; }
.case-type { font-size: 0.6875rem; color: var(--accent); margin-bottom: 10px; letter-spacing: 1px; display: flex; align-items: center; }
.case-q, .case-a { display: flex; gap: 6px; margin-bottom: 8px; }
.case-q-label, .case-a-label { width: 18px; height: 18px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 0.625rem; font-weight: 600; flex-shrink: 0; margin-top: 1px; }
.case-q-label { background: rgba(178,149,93,0.15); color: var(--accent); }
.case-a-label { background: rgba(39,174,96,0.15); color: var(--success); }
.case-q-text, .case-a-text { font-size: 0.75rem; color: var(--text-2); line-height: 1.5; flex: 1; min-width: 0; white-space: normal; word-break: break-all; }
.case-a-text { color: var(--text-3); }
.case-result { display: flex; align-items: center; gap: 8px; margin-top: 4px; margin-bottom: 4px; }
.case-verified { font-size: 0.6875rem; color: var(--success); }
.case-feedback { font-size: 0.6875rem; color: var(--accent); font-style: italic; }

/* 核心特色 */
.feature-scroll-wrap { position: relative; }
.feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.feature-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 28px 24px; backdrop-filter: blur(20px); transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); text-align: center; }
.feature-icon { font-size: 2rem; margin-bottom: 12px; }
.feature-card-title { font-family: var(--font-serif); font-size: 0.9375rem; letter-spacing: 2px; margin-bottom: 8px; color: var(--text-1); }
.feature-card-desc { font-size: 0.8125rem; color: var(--text-3); line-height: 1.6; }

/* 场景快速入口 */
.scenario-scroll-wrap { position: relative; }
.scenario-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; }
.scenario-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 24px 16px; backdrop-filter: blur(16px); text-align: center; cursor: pointer; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.scenario-emoji { font-size: 2rem; display: block; margin-bottom: 8px; }
.scenario-card-title { font-size: 0.8125rem; color: var(--text-2); letter-spacing: 1px; }

/* FAQ */
.faq-section { padding-bottom: 0 !important; }
.faq-panel { max-width: var(--max-w); margin: 0 auto; border: 1px solid var(--card-border); border-radius: var(--radius-md); overflow: hidden; background: var(--card-bg); backdrop-filter: blur(12px); }
.faq-panel-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; cursor: pointer; }
.faq-panel-title { font-family: var(--font-serif); font-size: 0.9375rem; letter-spacing: 2px; color: var(--text-2); }
.faq-panel-arrow { font-size: 0.75rem; color: var(--text-3); transition: transform 0.3s var(--ease); }
.faq-panel-arrow.rotated { transform: rotate(180deg); }
.faq-panel-body { max-height: 0; overflow: hidden; transition: max-height 0.4s var(--ease); padding: 0 20px; }
.faq-panel-body.open { max-height: 600px; padding: 0 20px 16px; }
.faq-item { border: 1px solid var(--card-border); border-radius: 10px; margin-bottom: 8px; overflow: hidden; }
.faq-q { padding: 14px 20px; cursor: pointer; font-size: 0.875rem; color: var(--text-2); display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); }
.faq-q .arrow { transition: transform 0.2s; }
.faq-q .arrow.rotated { transform: rotate(180deg); }
.faq-a { padding: 0 20px; max-height: 0; overflow: hidden; transition: max-height 0.3s var(--ease); font-size: 0.8125rem; color: var(--text-3); line-height: 1.7; }
.faq-a.open { max-height: 200px; padding: 14px 20px; }

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

/* 响应式 */
@media (max-width: 768px) {
  .about-hero { padding: 80px 16px 32px; }
  .about-hero-title { font-size: 1.35rem; letter-spacing: 2px; }
  .about-hero-desc { font-size: 0.8125rem; }
  .section { padding: 48px 16px; }
  .hero-cards { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .hero-card-primary { grid-column: span 2; }
  .hero-mini-scroll { grid-template-columns: repeat(4, 1fr); }
  .trust-grid { grid-template-columns: 1fr; }
  .feature-grid { grid-template-columns: repeat(2, 1fr); }
  .scenario-grid { grid-template-columns: repeat(3, 1fr); }
  .edu-grid { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
}

/* 页脚 */
.site-footer { background: var(--nav-bg); border-top: 1px solid var(--card-border); padding: 24px 32px 24px; margin-top: 0; text-align: center; }
.footer-disclaimer { max-width: var(--max-w); margin: 0 auto 32px; padding: 14px 20px; border-radius: 10px; background: rgba(215,125,110,0.08); border: 1px solid rgba(215,125,110,0.15); font-size: 0.75rem; color: var(--danger); line-height: 1.6; text-align: center; }
.footer-grid { max-width: 860px; margin: 0 auto; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 32px; justify-items: center; text-align: center; }
.footer-col { width: 100%; min-width: 0; }
.footer-col-title { font-size: 0.8125rem; color: var(--text-2); margin-bottom: 12px; letter-spacing: 1px; }
.footer-col navigator, .footer-col .footer-link { display: block; width: 100%; font-size: 0.75rem; color: var(--text-3); text-decoration: none; padding: 3px 0; cursor: pointer; text-align: center; }
.footer-icp { font-size: 0.6875rem; color: var(--text-3); margin-top: 8px; }
.footer-icp-link { cursor: pointer; text-decoration: none; }
.footer-icp-link:hover { color: var(--accent); }
.footer-bottom { max-width: 860px; margin: 24px auto 0; padding-top: 16px; border-top: 1px solid var(--card-border); display: flex; justify-content: center; align-items: center; gap: 18px; flex-wrap: wrap; text-align: center; }
.footer-bottom-text { font-size: 0.6875rem; color: var(--text-3); }
.btn-clear-data { font-size: 0.6875rem; padding: 4px 10px; border-radius: 6px; background: transparent; border: 1px solid var(--danger); color: var(--danger); cursor: pointer; }

@media (max-width: 768px) {
  .site-footer { padding: 24px 16px; }
  .footer-grid { grid-template-columns: 1fr; gap: 24px; max-width: 420px; }
}

@media (max-width: 480px) {
  .footer-bottom { flex-direction: column; gap: 8px; }
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
