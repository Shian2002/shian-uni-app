<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- Hero -->
      <view class="tarot-hero">
        <view class="tarot-stars">
          <view class="tarot-star" v-for="(star, i) in stars" :key="i"
            :style="{ left: star.left + '%', top: star.top + '%', animationDelay: star.delay + 's', animationDuration: star.duration + 's' }">
          </view>
        </view>
        <view class="tarot-hero-icon">🃏</view>
        <view class="tarot-hero-title">塔罗牌占卜</view>
        <view class="tarot-hero-desc">韦特塔罗正统体系，78张完整牌库，多牌阵选择<text class="hero-br"></text>直觉引导，探索内心深处的答案</view>
      </view>

      <!-- 牌阵选择 -->
      <view class="tarot-section" id="spreadSection">
        <view class="tarot-section-title">✦ 选择牌阵</view>
        <view class="spread-grid">
          <view class="spread-card" v-for="s in spreads" :key="s.key"
            :data-key="s.key" @tap="selectSpread(s.key)">
            <view class="spread-card-head">
              <text class="spread-card-name">{{ s.name }}</text>
              <text class="spread-card-count">{{ s.card_count }}张</text>
            </view>
            <text class="spread-card-desc">{{ s.description }}</text>
          </view>
        </view>

        <!-- 设置 -->
        <view class="tarot-settings">
          <view class="tarot-setting-item">
            <text class="tarot-setting-label">正逆位开关</text>
            <label class="tarot-toggle-label">
              <view class="tarot-toggle" id="tarotToggle" @tap="toggleReversed">
                <view class="tarot-toggle-knob"></view>
              </view>
              <text class="tarot-toggle-status">{{ enableReversed ? '已开启' : '已关闭' }}</text>
            </label>
          </view>
          <view id="tarotQuestion-wrap" class="dom-input-wrap"></view>
        </view>

        <!-- 抽牌按钮 -->
        <view class="tarot-btn-row">
          <view class="tarot-draw-btn" @tap="startDraw">✦ 开始抽牌 ✦</view>
          <view class="btn btn-ghost" @tap="tarotReset">🔄 清空</view>
        </view>
      </view>

      <!-- 抽牌动画 -->
      <view class="tarot-drawing-area" id="drawingArea">
        <view class="tarot-drawing-text">✦ 正在洗牌抽牌 ✦</view>
        <view class="tarot-card-stack">
          <view class="stack-card"><view class="stack-card-inner"><text class="stack-card-symbol">✦</text></view></view>
          <view class="stack-card"><view class="stack-card-inner"><text class="stack-card-symbol">☽</text></view></view>
          <view class="stack-card"><view class="stack-card-inner"><text class="stack-card-symbol">⚝</text></view></view>
        </view>
      </view>

      <!-- 抽牌结果（DOM直操作渲染，绕开Vue 3.4.21 render effect bug） -->
      <view class="tarot-result-area" id="resultArea">
        <view class="tarot-result-header">
          <view class="tarot-result-title" id="resultSpreadName"></view>
          <view class="draw-time" id="resultDrawTime"></view>
        </view>

        <!-- 牌面展示（由JS innerHTML渲染） -->
        <view class="tarot-cards-display" id="cardsDisplay"></view>

        <!-- 确认区域 -->
        <view class="tarot-confirm-area" id="confirmArea">
          <view class="confirm-text">
            <text>请核对以上抽牌结果，确认无误后进入解读环节</text>
            <text class="confirm-hint">⚠️ 抽牌结果由密码级真随机生成，确认后不可更改</text>
          </view>
          <view class="tarot-confirm-btns">
            <view class="tarot-btn tarot-btn-primary" @tap="confirmAndRead">✦ 保留牌面，回首页深度解读</view>
            <view class="tarot-btn tarot-btn-outline" @tap="redrawCards">🔄 重新抽牌</view>
          </view>
        </view>

        <!-- 解读区域已统一到首页综合 AI，这里只保留抽牌和牌面确认 -->
        <view v-if="false" class="tarot-reading-area" id="readingArea">
          <view class="tarot-reading-section">
            <view class="reading-title">✦ 核心总断</view>
            <view class="reading-body" id="readingOverview"></view>
          </view>
          <!-- 对话历史（首轮解读 + 追问） -->
          <view class="tarot-reading-section" id="chatSection">
            <view class="reading-title">✦ AI 解读</view>
            <view class="chat-container" id="chatContainer"></view>
            <!-- 追问输入栏 -->
            <view class="chat-input-bar" id="chatInputBar" style="display:none;">
              <input class="chat-input" id="chatInput" placeholder="继续追问..." />
              <view class="chat-send-btn" id="chatSendBtn" onclick="window.sendFollowUp()">发送</view>
            </view>
          </view>
          <!-- 本地解读占位（AI 不可用时） -->
          <view class="tarot-reading-section" id="fallbackCardsSection" style="display:none;">
            <view class="reading-title">✦ 分牌位解读</view>
            <view class="reading-body" id="readingCards"></view>
          </view>
          <view class="tarot-disclaimer">
            ⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议
          </view>
        </view>

        <!-- 重新抽牌 -->
        <view class="tarot-redraw-area" id="redrawArea" style="display:none;">
          <view class="tarot-btn tarot-btn-outline" @tap="redrawCards">🔄 重新占卜</view>
        </view>
      </view>
    </view>



  </view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'

// ═══ 主题 ═══
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

// ═══ 导航 ═══
const mobileMenuOpen = ref(false)
const submenuOpen = reactive({ qimen: false, bazi: false, more: false })
function openMobileMenu() { mobileMenuOpen.value = true }
function closeMobileMenu() { mobileMenuOpen.value = false }
function toggleSubmenu(key) { submenuOpen[key] = !submenuOpen[key] }

// ═══ 登录状态 ═══
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

// ═══ 全局状态 ═══
let currentSpread = ref('three')
let enableReversed = ref(true)
const questionInput = ref('')

// DOM直操作用的纯JS变量（绕开Vue 3.4.21 render effect bug）
let _drawResult = null
let _cardsConfirmed = false
let _isDrawing = false

const TAROT_IMAGE_BASE_URL = '/static/tarot/rws/'
const MINOR_SUIT_PREFIX = { '权杖': 'w', '圣杯': 'c', '宝剑': 's', '星币': 'p' }
const MINOR_NUMBER_IMAGE_INDEX = {
  Ace: 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
  '8': 8, '9': 9, '10': 10, Page: 11, Knight: 12, Queen: 13, King: 14
}

// ═══ 星星动画 ═══
const stars = reactive([])
function generateStars() {
  stars.length = 0
  for (let i = 0; i < 20; i++) {
    stars.push({
      left: Math.random() * 100,
      top: Math.random() * 100,
      delay: Math.random() * 3,
      duration: 2 + Math.random() * 3
    })
  }
}

// ═══ 牌阵数据 ═══
const spreads = ref([
  { key: 'three', name: '无牌阵三张', card_count: 3, description: '最经典的入门牌阵，简洁有力' },
  { key: 'time_flow', name: '时间流牌阵', card_count: 5, description: '以时间为轴线的线性牌阵' },
  { key: 'hexagram', name: '六芒星牌阵', card_count: 7, description: '六芒星结构的深度牌阵' },
  { key: 'celtic_cross', name: '凯尔特十字', card_count: 10, description: '最经典的全局面牌阵' },
  { key: 'relationship', name: '关系牌阵', card_count: 5, description: '分析两人关系的专属牌阵' },
  { key: 'single', name: '单牌占卜', card_count: 1, description: '最简洁的占卜方式' },
])

// ═══ 加载牌阵（API优先，fallback本地） ═══
async function loadSpreads() {
  try {
    const res = await uni.request({
      url: '/api/tarot/spreads',
      method: 'GET',
      header: { 'Content-Type': 'application/json' }
    })
    const data = res.data
    if (data && data.code === 0 && data.data && data.data.length > 0) {
      spreads.value = data.data
    }
  } catch (e) {
    // fallback本地数据（已初始化）
  }
}

function selectSpread(key) {
  currentSpread.value = key
  // DOM直操作更新active（绕开Vue 3.4.21 render effect bug）
  document.querySelectorAll('.spread-card').forEach(function(el) {
    el.classList.toggle('active', el.getAttribute('data-key') === key)
  })
}

// ═══ 正逆位开关 ═══
function toggleReversed() {
  enableReversed.value = !enableReversed.value
  var toggle = document.getElementById('tarotToggle')
  if (toggle) { enableReversed.value ? toggle.classList.add('on') : toggle.classList.remove('on') }
}

function _escTarotText(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function getCardImage(card) {
  if (card.image_url) return card.image_url
  if (card.image_key) return TAROT_IMAGE_BASE_URL + card.image_key
  if (card.type === 'major' && typeof card.id === 'number') return TAROT_IMAGE_BASE_URL + 'm' + String(card.id).padStart(2, '0') + '.jpg'
  var prefix = MINOR_SUIT_PREFIX[card.suit]
  var index = MINOR_NUMBER_IMAGE_INDEX[card.number]
  if (prefix && index) return TAROT_IMAGE_BASE_URL + prefix + String(index).padStart(2, '0') + '.jpg'
  return ''
}

function getCardImageKey(card) {
  if (card.image_key) return card.image_key
  var image = getCardImage(card)
  return image ? image.split('/').pop() : ''
}

function getCardAlt(card) {
  var name = card.name || ''
  var en = card.name_en ? ' / ' + card.name_en : ''
  return name + en + ' ' + (card.orientation || '')
}

function showTarotCardFallback(img) {
  var front = img && img.closest ? img.closest('.tarot-card-front') : null
  if (!front) return
  front.classList.add('image-failed')
}

// ═══ 翻牌（DOM直操作） ═══
function flipCard(index, event) {
  if (event) event.preventDefault()
  const flipper = document.getElementById('cardFlipper' + index)
  if (flipper && !flipper.classList.contains('flipped')) {
    flipper.classList.add('flipped')
  }
}

// ═══ 抽牌（DOM直操作，绕开Vue 3.4.21 render effect bug） ═══
async function startDraw() {
  if (_isDrawing) return
  _isDrawing = true

  // 隐藏牌阵选择区，显示抽牌动画
  const spreadSection = document.getElementById('spreadSection')
  const drawingArea = document.getElementById('drawingArea')
  if (spreadSection) spreadSection.style.display = 'none'
  if (drawingArea) drawingArea.classList.add('show')

  try {
    const res = await uni.request({
      url: '/api/tarot/draw',
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      data: {
        spread_name: currentSpread.value,
        enable_reversed: enableReversed.value,
      }
    })
    const data = res.data
    if (!data) {
      uni.showToast({ title: '服务器未响应', icon: 'none' })
      _resetUIDOM()
      return
    }
    if (data.code !== undefined && data.code !== 0) {
      uni.showToast({ title: data.msg || '抽牌失败，请重试', icon: 'none' })
      _resetUIDOM()
      return
    }
    _drawResult = data.data || data
    _cardsConfirmed = false

    // 延迟显示结果（动画效果）
    setTimeout(() => {
      if (drawingArea) drawingArea.classList.remove('show')
      _showResultDOM()
    }, 1800)

  } catch (e) {
    uni.showToast({ title: '网络错误，请重试', icon: 'none' })
    _resetUIDOM()
  }
}

// ═══ DOM直操作：渲染抽牌结果（try-catch包裹，避免渲染异常时静默失败） ═══
function _showResultDOM() {
  try {
    if (!_drawResult) return
    _unscopeStyles()
    _isDrawing = false

    const area = document.getElementById('resultArea')
    if (area) area.classList.add('show')

    // 牌阵名称和时间
    const nameEl = document.getElementById('resultSpreadName')
    const timeEl = document.getElementById('resultDrawTime')
    if (nameEl && _drawResult.spread) nameEl.textContent = _drawResult.spread.name + ' · 塔罗牌占卜'
    if (timeEl && _drawResult.draw_time) timeEl.textContent = '抽牌时间: ' + _drawResult.draw_time

    // 渲染卡牌
    const display = document.getElementById('cardsDisplay')
    if (display && _drawResult.cards && _drawResult.cards.length) {
      display.setAttribute('data-count', String(_drawResult.cards.length))
      display.innerHTML = _drawResult.cards.map(function(card, i) {
      const orientationClass = card.is_reversed ? 'reversed' : 'upright'
      const keyword = card.is_reversed && card.keyword_reversed
        ? card.keyword_reversed
        : card.keyword
      const imageUrl = getCardImage(card)
      const imageKey = getCardImageKey(card)
      const imageClass = 'tarot-card-img' + (card.is_reversed ? ' tarot-card-img-reversed' : '')
      const cardNum = card.type === 'major' ? card.id : (card.number || '')
      const cardName = _escTarotText(card.name)
      const cardNameEn = _escTarotText(card.name_en)
      const cardAlt = _escTarotText(getCardAlt(card))
      const cardKeyword = _escTarotText(keyword)

      return '<div class="tarot-card-slot" style="animation: tarotCardAppear 0.5s ' + (i * 0.15) + 's both">' +
        '<div class="tarot-card-flipper" id="cardFlipper' + i + '" onclick="event.preventDefault();window.__tarotFlip(' + i + ', event)">' +
          '<div class="tarot-card-back">' +
            '<div class="tarot-card-back-pattern"></div>' +
            '<span class="tarot-card-back-symbol">✦</span>' +
          '</div>' +
          '<div class="tarot-card-front">' +
            '<div class="tarot-card-art-wrap">' +
              '<img class="' + imageClass + '" src="' + _escTarotText(imageUrl) + '" alt="' + cardAlt + '" loading="lazy" data-image-key="' + _escTarotText(imageKey) + '" onerror="window.__tarotImageFallback(this)">' +
              '<div class="tarot-card-fallback">' +
                '<div class="tarot-card-num">' + _escTarotText(cardNum) + '</div>' +
                '<div class="tarot-card-name">' + cardName + '</div>' +
                '<div class="tarot-card-name-en">' + cardNameEn + '</div>' +
                '<div class="tarot-card-keyword">' + cardKeyword + '</div>' +
              '</div>' +
            '</div>' +
            '<div class="tarot-card-name tarot-card-name-below">' + cardName + '</div>' +
            '<div class="tarot-card-name-en">' + cardNameEn + '</div>' +
            '<div class="tarot-card-orientation ' + orientationClass + '">' + card.orientation + '</div>' +
            '<div class="tarot-card-keyword tarot-card-keyword-below">' + cardKeyword + '</div>' +
          '</div>' +
        '</div>' +
        '<div class="tarot-card-position">' +
          '<div class="tarot-card-position-name">' + _escTarotText(card.position_name) + '</div>' +
          '<div class="tarot-card-position-meaning">' + _escTarotText(card.position_meaning) + '</div>' +
          (card.is_reversed ? '<div class="tarot-card-reversed-hint">逆位</div>' : '') +
        '</div>' +
      '</div>'
    }).join('')
  }

  // 注册全局翻牌函数
  window.__tarotFlip = flipCard
  window.__tarotImageFallback = showTarotCardFallback

  // 自动翻牌
  _drawResult.cards.forEach(function(_, i) {
    setTimeout(function() { flipCard(i, null) }, 600 + i * 400)
  })

  // 显示确认区，隐藏解读区和重抽区
  const confirmArea = document.getElementById('confirmArea')
  const readingArea = document.getElementById('readingArea')
  const redrawArea = document.getElementById('redrawArea')
  if (confirmArea) confirmArea.style.display = 'block'
  if (readingArea) readingArea.classList.remove('show')
  if (redrawArea) redrawArea.style.display = 'none'

  // 避免强制滚动（不上滑页面）
  if (area) area.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  } catch(e) {
    console.error('_showResultDOM error:', e)
    _isDrawing = false
    uni.showToast({ title: '渲染结果异常，请重新抽牌', icon: 'none' })
  }
}

// ═══ 确认并解读（DOM直操作） ═══
// ═══ 大阿卡纳解读（AI 不可用时的降级方案） ═══
var MAJOR_READINGS = {
  0: { upright: '新的旅程即将开始，拥抱未知，相信直觉。此刻需要放下包袱，以赤子之心迎接变化。', reversed: '可能过于鲁莽或不愿面对新的开始。审视自己是否在逃避改变。' },
  1: { upright: '你拥有将想法变为现实的全部资源和能力。现在是采取行动的时刻，专注你的意志力。', reversed: '才能未能充分发挥，或试图操控局面。需要诚实面对自己的动机。' },
  2: { upright: '倾听内在的声音，答案就在你的潜意识中。静下来，让直觉引导你。', reversed: '忽视了内在智慧，过度依赖外在信息。需要重新连接你的直觉。' },
  3: { upright: '丰盛与滋养的能量环绕着你。创造力旺盛，适合培育新事物。', reversed: '可能过度依赖他人或忽视自我照顾。需要在给予和接受间找平衡。' },
  4: { upright: '结构、秩序和纪律是此刻的关键。稳健的领导力将带来成果。', reversed: '过度控制或权威僵化。适度放权，保持灵活。' },
  5: { upright: '传统智慧和精神指引可以提供方向。寻求导师或值得信赖的建议。', reversed: '质疑传统或教条束缚。找到属于自己的信念体系。' },
  6: { upright: '面临重要的选择，需要倾听内心。和谐的关系是力量的源泉。', reversed: '关系失衡或难以抉择。审视内心真正的渴望。' },
  7: { upright: '凭借决心和毅力，胜利就在前方。掌控方向，勇往直前。', reversed: '失去方向感或内心冲突导致停滞。重新明确目标。' },
  8: { upright: '内在力量远超想象。温柔而坚定的态度比强硬更有效。', reversed: '自我怀疑或缺乏信心。回顾过去克服困难的经验。' },
  9: { upright: '独处和内省能带来深刻的领悟。暂时退一步，是为了更清晰地前进。', reversed: '过度孤立或逃避现实。在独处和社交间找平衡。' },
  10: { upright: '命运的齿轮正在转动，变化即将来临。顺应周期，抓住机遇。', reversed: '抗拒变化或感觉命运无常。接受起伏是人生常态。' },
  11: { upright: '公正和平衡是此刻的主题。因果循环，种什么因得什么果。', reversed: '不公正的对待或逃避责任。正视问题，做出公正的判断。' },
  12: { upright: '换一个角度看问题，会有新的发现。暂时的等待是为了更好的出发。', reversed: '无意义的牺牲或固执己见。学会放手不合理的坚持。' },
  13: { upright: '一个阶段正在结束，新的篇章即将开启。结束不是终点，而是转化的起点。', reversed: '抗拒必然的变化或恐惧未知。接受结束是重生的前提。' },
  14: { upright: '平衡与适度是关键。融合不同元素，找到中庸之道。', reversed: '过度极端或缺乏耐心。回归内心的平静。' },
  15: { upright: '觉察那些束缚你的模式和执念。认清阴影，才能走向自由。', reversed: '开始摆脱束缚或面对深层恐惧。这是解放的开始。' },
  16: { upright: '突发的变化将打破现状。虽然剧烈，但这是必要的觉醒。', reversed: '延缓的冲击或抗拒不可避免的变革。做好准备。' },
  17: { upright: '希望和灵感正在流入你的生命。相信未来，保持信心。', reversed: '暂时失去方向或信心动摇。这不是终点，黎明前总是最黑暗。' },
  18: { upright: '事情并非表面看起来的那样。注意直觉中的警告信号，辨别幻象与真实。', reversed: '迷雾开始散去，真相逐渐显现。走出恐惧的阴影。' },
  19: { upright: '光明、喜悦和成功正在到来。积极乐观，享受生活的馈赠。', reversed: '成功可能延迟或过度乐观。保持理性乐观。' },
  20: { upright: '深刻的觉醒和审视。过去的经历将带来全新的理解。', reversed: '无法释怀过去或拒绝反思。勇敢面对内心。' },
  21: { upright: '圆满和完成。一切努力都将得到回报，进入新的层次。', reversed: '差最后一步就能完成。坚持到底，不要放弃。' },
}
function getCardReading(card) {
  if (card.type === 'major' && MAJOR_READINGS[card.id]) {
    return card.is_reversed ? MAJOR_READINGS[card.id].reversed : MAJOR_READINGS[card.id].upright
  }
  if (card.type === 'minor') {
    if (card.is_reversed) {
      return card.name + '逆位，' + card.element + '元素能量受阻。' + (card.keyword || '').replace(/[（].+[）]/g, '') + '的主题受到干扰，建议审视这个领域是否存在逃避或执念。'
    } else {
      return card.name + '正位，' + card.element + '元素能量顺畅。' + (card.keyword || '').replace(/[（].+[）]/g, '') + '的主题正在积极展现。建议善用这股能量。'
    }
  }
  return '静心感受这张牌传递的信息。'
}
function getTrendAnalysis(cards, spread) {
  var rRatio = cards.filter(function(c) { return c.is_reversed }).length / cards.length
  var lastCard = cards[cards.length - 1]
  var t = ''
  if (rRatio < 0.3) t += '整体牌面以正位为主，事态发展较为顺畅，阻力较小。'
  else if (rRatio > 0.6) t += '逆位牌占比较高，事态可能面临较多波折和内在阻碍，需要更多耐心。'
  else t += '正逆位交替出现，事态发展有起有伏，需要灵活应对。'
  if (lastCard) {
    t += ' 最终位置（' + lastCard.position_name + '）出现' + lastCard.name + (lastCard.is_reversed ? '逆位' : '正位') + '，'
    t += lastCard.is_reversed ? '提示最终结果可能需要更多时间和努力才能达成。' : '暗示最终结果偏向积极。'
  }
  return t
}
function getAdvice(cards) {
  var suits = {}; cards.forEach(function(c) { if (c.suit) suits[c.suit] = true })
  var rCount = cards.filter(function(c) { return c.is_reversed }).length
  var a = '综合牌面信息，'
  if (suits['宝剑']) a += '需要理性分析和清晰思考；'
  if (suits['圣杯']) a += '关注情感需求和人际关系；'
  if (suits['权杖']) a += '保持行动力和创造力；'
  if (suits['星币']) a += '注重实际成果和物质基础；'
  if (rCount > cards.length / 2) a += '建议先调整内在状态再行动。'
  return a
}
function getShortTermAction(cards) {
  var mid = cards[Math.floor(cards.length / 2)]
  if (mid) return '关注「' + mid.position_name + '」位置的' + mid.name + '，' + (mid.is_reversed ? '先解决内在阻滞' : '顺势而为') + '。'
  return '保持觉察，顺应牌面指引行动。'
}
function getCaution(cards) {
  var rCards = cards.filter(function(c) { return c.is_reversed })
  if (rCards.length > 0) {
    return '逆位牌提示：' + rCards.map(function(c) { return c.position_name + '方面可能存在阻滞' }).join('；') + '。避免冲动和过度执着。'
  }
  return '虽然牌面积极，仍需保持谦逊和警觉。'
}
function getMindsetAdvice(cards) {
  var majorCount = cards.filter(function(c) { return c.type === 'major' }).length
  if (majorCount >= 2) return '大阿卡纳频繁出现，说明当前是人生的重要转折期。保持开放心态，拥抱变化。'
  return '保持平常心，相信自己的判断力。每一步都是成长。'
}

// ═══ DOM直操作：确认并开始解读 ═══
function confirmAndRead() {
  if (!_drawResult) return
  _cardsConfirmed = true

  var confirmArea = document.getElementById('confirmArea')
  if (confirmArea) confirmArea.style.display = 'none'

  try { uni.showToast({ title: '深度 AI 解读请回首页选择塔罗牌', icon: 'none' }) } catch(_) {}

  var redrawArea = document.getElementById('redrawArea')
  if (redrawArea) redrawArea.style.display = 'block'
}

// ═══ AI 流式解读 ═══
function _startAIReading() {
  if (!_drawResult) return
  var cards = _drawResult.cards
  var spread = _drawResult.spread
  var question = (document.getElementById('tarotQuestion') && document.getElementById('tarotQuestion').value || questionInput.value || '').trim()

  // 先渲染概览（本地计算，立即显示）
  _renderOverview(cards, spread, question)

  // 创建 AI 解读气泡，放入对话容器
  var chatContainer = document.getElementById('chatContainer')
  if (!chatContainer) return
  chatContainer.innerHTML = ''  // 新占卜清空旧对话

  var bubbleHTML = '<div class="chat-bubble-ai" id="aiBubble">' +
    '<div class="ai-stage" id="aiStage">🔗 正在连接 DeepSeek AI 引擎...</div>' +
    '<div class="ai-progress-bar"><div class="ai-progress-fill" id="aiProgressBar"></div></div>' +
    '<div class="chat-bubble-content" id="aiStreamContent"></div>' +
    '</div>'
  chatContainer.innerHTML = bubbleHTML

  // 发起 SSE 请求
  var token = ''
  try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  if (!token) {
    _fallbackLocalReading(cards, spread)
    return
  }

  _doStreamSSE({
    cards: cards, question: question, spread_name: spread.name,
    bubbleId: 'aiBubble',
    onDone: function(fullText) {
      _finalizeAIReading(fullText)
      // 保存首轮对话到历史
      window._chatHistory = [
        { role: 'user', content: question },
        { role: 'assistant', content: fullText }
      ]
      // 保存到服务端
      _saveConversation(question)
      // 显示追问栏
      var bar = document.getElementById('chatInputBar')
      if (bar) bar.style.display = 'flex'
    },
    onError: function() {
      _fallbackLocalReading(cards, spread)
    }
  })
}

// ═══ 追问 ═══
function sendFollowUp() {
  try {
    var input = document.querySelector('#chatInput input') || document.getElementById('chatInput')
    if (!input) { console.warn('[tarot] chatInput not found'); return }
    var question = input.value.trim()
    if (!question) return
    input.value = ''

    var chatContainer = document.getElementById('chatContainer')
    if (!chatContainer) return

    var userBubble = document.createElement('view')
    userBubble.className = 'chat-bubble-user'
    userBubble.textContent = question
    chatContainer.appendChild(userBubble)

    var aiBubble = document.createElement('view')
    aiBubble.className = 'chat-bubble-ai'
    aiBubble.id = 'aiFollowBubble_' + Date.now()
    aiBubble.innerHTML = '<div class="ai-stage"><img class="ai-stage-logo" src="/static/images/logo.webp?v=2">正在生成回复...</div>' +
      '<div class="ai-progress-bar"><div class="ai-progress-fill" style="width:60%"></div></div>' +
      '<div class="chat-bubble-content"></div>'
    chatContainer.appendChild(aiBubble)
    chatContainer.scrollIntoView({ behavior: 'smooth', block: 'end' })

    var history = window._chatHistory || []
    history.push({ role: 'user', content: question })

    // 发送时立即保存
    if (_currentConvId) {
      window._chatHistory = history
      _updateConversation()
    } else {
      window._chatHistory = history
      _saveConversation(question)
    }

    _doStreamSSE({
      history: history, question: question,
      bubbleId: aiBubble.id,
      onDone: function(fullText) {
        history.push({ role: 'assistant', content: fullText })
        window._chatHistory = history
        if (_currentConvId) { _updateConversation() } else { _saveConversation(question) }
      },
      onError: function() {
        var eb = document.getElementById(aiBubble.id)
        if (eb) { var es = eb.querySelector('.ai-stage'); if (es) es.innerHTML = '⚠️ 追问失败，请重试' }
      }
    })
  } catch (err) { console.error('[tarot] sendFollowUp error:', err) }
}
window.sendFollowUp = sendFollowUp

// ═══ 通用 SSE 流式 ═══
function _doStreamSSE(opts) {
  var bubble = document.getElementById(opts.bubbleId)
  if (!bubble) return
  var stageEl = bubble.querySelector('.ai-stage')
  var barEl = bubble.querySelector('.ai-progress-fill')
  var contentEl = bubble.querySelector('.chat-bubble-content')

  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  var xhr = new XMLHttpRequest()
  xhr.open('POST', '/api/tarot/reading/stream', true)
  xhr.setRequestHeader('Content-Type', 'application/json')
  if (token) xhr.setRequestHeader('Authorization', 'Bearer ' + token)

  var lastIndex = 0
  var fullText = ''
  var charQueue = ''
  var typeTimer = null
  var doneReceived = false

  function startTypewriter() {
    if (typeTimer) return
    typeTimer = setInterval(function() {
      if (charQueue.length === 0 && doneReceived) {
        clearInterval(typeTimer); typeTimer = null
        if (stageEl) stageEl.style.display = 'none'
        if (barEl && barEl.parentElement) barEl.parentElement.style.display = 'none'
        if (opts.onDone) opts.onDone(fullText)
        return
      }
      if (charQueue.length === 0) return
      var take = charQueue.length > 3 ? 2 : 1
      fullText += charQueue.substring(0, take)
      charQueue = charQueue.substring(take)
      if (contentEl) contentEl.innerHTML = _stripMarkdown(fullText).replace(/\n/g, '<br>')
    }, 35)
  }

  xhr.onprogress = function() {
    var newText = xhr.responseText.substring(lastIndex)
    lastIndex = xhr.responseText.length
    var lines = newText.split('\n')
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i]
      if (line.indexOf('event:') === 0) { var eventType = line.replace('event:', '').trim(); continue }
      if (line.indexOf('data:') !== 0) continue
      try {
        var data = JSON.parse(line.replace('data:', '').trim())
        if (eventType === 'progress') {
          if (data.stage === 'connecting' && stageEl) stageEl.innerHTML = '🔗 正在连接...'
          else if (data.stage === 'analyzing' && stageEl) stageEl.innerHTML = '🧠 正在分析...'
          else if (data.stage === 'generating' && stageEl) { stageEl.innerHTML = '<img class="ai-stage-logo" src="/static/images/logo.webp?v=2">正在生成...'; startTypewriter() }
          if (barEl) barEl.style.width = '60%'
        } else if (eventType === 'chunk') {
          charQueue += data.content
        } else if (eventType === 'done') {
          doneReceived = true
        } else if (eventType === 'error') {
          if (stageEl) stageEl.innerHTML = '⚠️ ' + data.message
          if (opts.onError) opts.onError()
        }
        eventType = ''
      } catch(_) {}
    }
  }
  xhr.onerror = function() { if (opts.onError) opts.onError() }

  var body = { question: opts.question || '' }
  if (opts.cards) {
    body.cards = opts.cards.map(function(c) { return {
      name: c.name, name_en: c.name_en, position_name: c.position_name,
      position_meaning: c.position_meaning, is_reversed: c.is_reversed,
      type: c.type, element: c.element, keyword: c.keyword, keyword_reversed: c.keyword_reversed
    }})
    body.spread_name = opts.spread_name || ''
  }
  if (opts.history) body.history = opts.history
  xhr.send(JSON.stringify(body))
}

function _finalizeAIReading(text) {
  text = _stripMarkdown(text)
  var bubble = document.getElementById('aiBubble')
  if (!bubble) return
  var bar = bubble.querySelector('.ai-progress-bar')
  var stage = bubble.querySelector('.ai-stage')
  if (bar) bar.style.display = 'none'
  if (stage) stage.style.display = 'none'
  var sections = text.split(/\n(?=#{2,3} )/)
  var html = ''
  sections.forEach(function(sec) {
    var m = sec.match(/^(#{2,3})\s+(.+)/)
    var title = m ? m[2] : ''
    var body = m ? sec.substring(m[0].length).trim() : sec
    body = body.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')
    if (!body) body = '&nbsp;'
    if (title) html += '<div class="tarot-reading-card-item"><div class="tarot-reading-card-title">' + title + '</div><div class="tarot-reading-card-body"><p>' + body + '</p></div></div>'
    else html += '<div class="tarot-reading-card-item"><div class="tarot-reading-card-body"><p>' + body + '</p></div></div>'
  })
  var contentEl = bubble.querySelector('.chat-bubble-content')
  if (contentEl) contentEl.innerHTML = html
}

function _stripMarkdown(s) {
  if (!s) return ''
  return s.replace(/^#{1,6}\s*/gm, '').replace(/\*\*/g, '').replace(/^[-*]\s+/gm, '')
}

// ═══ 本地规则引擎解读（AI 不可用时的降级） ═══
function _fallbackLocalReading(cards, spread) {
  // 显示 fallback 区
  var fb = document.getElementById('fallbackCardsSection')
  if (fb) fb.style.display = ''

  // 逐张解读
  var cardsHtml = ''
  cards.forEach(function(card) {
    var icon = getCardIcon(card)
    var orientation = card.is_reversed ? '逆位' : '正位'
    var keyword = card.is_reversed && card.keyword_reversed ? card.keyword_reversed : card.keyword
    cardsHtml += '<div class="tarot-reading-card-item">' +
      '<div class="tarot-reading-card-title">' + icon + ' 【' + card.position_name + '】' + card.name + '（' + orientation + '）</div>' +
      '<div class="tarot-reading-card-body">' +
        '<strong>位置含义：</strong>' + card.position_meaning + '<br>' +
        '<strong>核心关键词：</strong>' + keyword + '<br>' +
        '<strong>解读：</strong>' + getCardReading(card) +
      '</div>' +
    '</div>'
  })
  // 合并趋势分析和行动建议到解读区
  cardsHtml += '<div class="tarot-reading-card-item" style="border-left-color:var(--accent);">' +
    '<div class="tarot-reading-card-title">📈 事态发展趋势</div>' +
    '<div class="tarot-reading-card-body"><p>' + getTrendAnalysis(cards, spread) + '</p></div>' +
    '</div>' +
    '<div class="tarot-reading-card-item" style="border-left-color:#f59e0b;">' +
    '<div class="tarot-reading-card-title">💡 行动建议与风险提示</div>' +
    '<div class="tarot-reading-card-body"><p>' + getAdvice(cards) + '</p><ul>' +
    '<li><strong>短期行动：</strong>' + getShortTermAction(cards) + '</li>' +
    '<li><strong>注意事项：</strong>' + getCaution(cards) + '</li>' +
    '<li><strong>心态调整：</strong>' + getMindsetAdvice(cards) + '</li>' +
    '</ul></div></div>'
  var cardsEl = document.getElementById('readingCards')
  if (cardsEl) cardsEl.innerHTML = cardsHtml
}

// ═══ 渲染概览（总断 — 本地计算） ═══
function _renderOverview(cards, spread, question) {
  var majorCards = cards.filter(function(c) { return c.type === 'major' })
  var reversedCards = cards.filter(function(c) { return c.is_reversed })
  var uprightCards = cards.filter(function(c) { return !c.is_reversed })
  var hasFool = cards.some(function(c) { return c.id === 0 })
  var hasTower = cards.some(function(c) { return c.id === 16 })
  var hasStar = cards.some(function(c) { return c.id === 17 })
  var hasSun = cards.some(function(c) { return c.id === 19 })
  var hasWorld = cards.some(function(c) { return c.id === 21 })

  var overview = ''
  if (question) overview += '<p>问事主题：<strong style="color:var(--accent)">' + question + '</strong></p>'
  overview += '<p>本次采用<strong>' + spread.name + '</strong>牌阵，共抽取<strong>' + cards.length + '</strong>张牌。'
  if (majorCards.length > 0) {
    overview += '其中大阿卡纳<strong>' + majorCards.length + '</strong>张（' + majorCards.map(function(c) { return c.name }).join('、') + '），'
  }
  overview += '正位<strong>' + uprightCards.length + '</strong>张，逆位<strong>' + reversedCards.length + '</strong>张。</p>'
  if (hasSun || hasStar || hasWorld) overview += '<p>牌面中出现星星/太阳/世界等积极牌面，整体运势偏向光明与希望，事态有望朝好的方向发展。</p>'
  if (hasTower) overview += '<p>⚠️ 牌面中出现塔牌，暗示可能有突变或意外事件，需要做好心理准备和应对预案。</p>'
  if (reversedCards.length >= cards.length * 0.6) overview += '<p>逆位牌占比较高，提示当前可能面临较多阻滞或内在冲突，需要更多耐心与自省。</p>'
  if (hasFool) overview += '<p>愚者的出现暗示新的开始或冒险的契机，保持开放心态，拥抱未知。</p>'

  var overviewEl = document.getElementById('readingOverview')
  if (overviewEl) overviewEl.innerHTML = overview
}

// ═══ 对话历史侧边栏（全局，由 TopNav 控制打开/关闭） ═══
var _currentConvId = null

function _saveConversation(question) {
  var title = (question || '塔罗占卜').substring(0, 50)
  uni.request({
    url: '/api/tarot/conversations', method: 'POST',
    data: {
      title: title, spread_name: _drawResult ? _drawResult.spread.name : '',
      cards: _drawResult ? _drawResult.cards : [],
      messages: window._chatHistory || []
    },
    success: function(res) {
      if (res.data && res.data.id) _currentConvId = res.data.id
      window.__sidebarCache = null
    },
    fail: function(err) {
      console.error('[tarot] 保存对话失败:', err)
    }
  })
}

function _updateConversation() {
  if (!_currentConvId) return
  uni.request({
    url: '/api/tarot/conversations', method: 'POST',
    data: { id: _currentConvId, messages: window._chatHistory || [] },
    success: function() { window.__sidebarCache = null },
    fail: function(err) { console.error('[tarot] 更新对话失败:', err) }
  })
}

window._loadConvDetail = function(cid) {
  uni.request({
    url: '/api/tarot/conversations/' + cid, method: 'GET',
    success: function(res) {
      var d = res.data
      if (!d || d.error) return
      _currentConvId = d.id
      // 渲染牌面概览
      if (d.cards && d.cards.length) {
        _renderOverview(d.cards, {name: d.spread_name}, d.title)
      }
      // 渲染对话
      var chatContainer = document.getElementById('chatContainer')
      if (!chatContainer) return
      chatContainer.innerHTML = ''
      var msgs = d.messages || []
      msgs.forEach(function(m) {
        var cls = m.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'
        var bubble = document.createElement('view')
        bubble.className = cls
        bubble.textContent = m.content
        chatContainer.appendChild(bubble)
      })
      window._chatHistory = msgs
      // 显示追问栏
      var bar = document.getElementById('chatInputBar')
      if (bar) bar.style.display = 'flex'
      // 显示解读区
      var readingArea = document.getElementById('readingArea')
      if (readingArea) { readingArea.classList.add('show'); readingArea.scrollIntoView({behavior:'smooth', block:'start'}) }
      document.getElementById('tarotSidebarGlobal').classList.remove('open')
      document.getElementById('sidebarOverlayGlobal').classList.remove('show')
    }
  })
}

// ═══ 重新抽牌（DOM直操作） ═══
function redrawCards() {
  _drawResult = null
  _cardsConfirmed = false
  _isDrawing = false
  window._chatHistory = null
  _resetUIDOM()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function tarotReset() {
  currentSpread.value = 'three'
  enableReversed.value = true
  questionInput.value = ''
  var qInp = document.getElementById('tarotQuestion')
  if (qInp) qInp.value = ''
  _drawResult = null
  _cardsConfirmed = false
  _isDrawing = false
  _resetUIDOM()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function _resetUIDOM() {
  _isDrawing = false
  const spreadSection = document.getElementById('spreadSection')
  const drawingArea = document.getElementById('drawingArea')
  const resultArea = document.getElementById('resultArea')
  if (spreadSection) spreadSection.style.display = ''
  if (drawingArea) drawingArea.classList.remove('show')
  if (resultArea) resultArea.classList.remove('show')
}

function scrollToResult() {
  if (_drawResult) {
    const target = _cardsConfirmed
      ? document.getElementById('readingArea')
      : document.getElementById('resultArea')
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ═══ 注入全局样式（合并所有stylesheet，绕开uni-app强制scope） ═══
function _unscopeStyles() {
  let css = ''
  for (let i = 0; i < document.styleSheets.length; i++) {
    try {
      const sheet = document.styleSheets[i]
      if (!sheet.cssRules) continue
      for (let j = 0; j < sheet.cssRules.length; j++) {
        let t = sheet.cssRules[j].cssText
        t = t.replace(/\[data-v-[^\]]*\]/g, '')
        t = t.replace(/-[a-f0-9]{7,}\b/g, '')
        css += t
      }
    } catch(e) {}
  }
  if (!css) return
  const old = document.getElementById('tarot-unscoped')
  if (old) old.remove()
  const style = document.createElement('style')
  style.id = 'tarot-unscoped'
  style.textContent = css
  document.head.appendChild(style)
}

onShow(() => {
  try { _checkTarotRestore() } catch(_) {}
  var t = uni.getStorageSync('xc_theme')
  if (t && t !== theme.value) {
    theme.value = t
    try {
      document.documentElement.setAttribute('data-theme', t)
      document.body.setAttribute('data-theme', t)
    } catch(_) {}
  }
})

// ═══ 初始化 ═══
onMounted(() => {
  // 初始化正逆位开关DOM状态
  var toggle = document.getElementById('tarotToggle')
  if (toggle) toggle.classList.add('on')
  // 初始化牌阵选择active状态
  document.querySelectorAll('.spread-card').forEach(function(el) {
    el.classList.toggle('active', el.getAttribute('data-key') === currentSpread.value)
  })
  // 创建原生问题输入框（绕过v-model render effect bug）
  var qWrap = document.getElementById('tarotQuestion-wrap')
  if (qWrap) {
    var inp = document.createElement('input')
    inp.type = 'text'
    inp.id = 'tarotQuestion'
    inp.placeholder = '输入你的问题或占卜主题（选填）'
    inp.maxLength = 100
    inp.className = 'tarot-question-input'
    inp.style.cssText = 'width:100%;padding:10px 14px;border:1px solid var(--card-border);border-radius:10px;background:var(--input-bg);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;'
    qWrap.appendChild(inp)
  }
  _unscopeStyles()
  generateStars()
  loadSpreads()
  // 监听对话恢复事件
  uni.$on('xc-restore', _checkTarotRestore)
  _checkTarotRestore()
})

function _checkTarotRestore() {
  var d = window.__xc_restoreData
  if (!d || d.type !== 'tarot') return
  var chatContainer = document.getElementById('chatContainer')
  var inputBar = document.getElementById('chatInputBar')
  var resultArea = document.getElementById('resultArea')
  var readingArea = document.getElementById('readingArea')
  var redrawArea = document.getElementById('redrawArea')
  if (!chatContainer) return
  window.__xc_restoreData = null
  if (resultArea) resultArea.classList.add('show')
  if (readingArea) readingArea.classList.add('show')
  if (redrawArea) redrawArea.style.display = 'block'
  chatContainer.innerHTML = ''
  if (d.rawHtml) {
    // 旧记录：先去除 markdown 格式，再渲染
    if (d.question) {
      var ub2 = document.createElement('view')
      ub2.className = 'chat-bubble-user'
      ub2.textContent = d.question
      chatContainer.appendChild(ub2)
    }
    // 先去除 HTML 标签，再去除 markdown 格式，最后转成 HTML
    var cleanHtml = _stripMarkdown(d.rawHtml.replace(/<[^>]+>/g, '')).replace(/\n/g, '<br>')
    var ab2 = document.createElement('view')
    ab2.className = 'chat-bubble-ai'
    ab2.innerHTML = '<div class="chat-bubble-content">' + cleanHtml + '</div>'
    chatContainer.appendChild(ab2)
    window._chatHistory = [
      { role: 'user', content: d.question || '' },
      { role: 'assistant', content: cleanHtml.replace(/<[^>]+>/g, '').substring(0, 200) + '...' }
    ]
    _currentConvId = null
  } else {
    var messages = d.messages || []
    window._chatHistory = messages.slice()
    _currentConvId = d.id || null
    messages.forEach(function(m) {
      if (m.role === 'user') {
        var ub = document.createElement('view')
        ub.className = 'chat-bubble-user'
        ub.textContent = m.content
        chatContainer.appendChild(ub)
      } else if (m.role === 'assistant') {
        var ab = document.createElement('view')
        ab.className = 'chat-bubble-ai'
        ab.innerHTML = '<div class="chat-bubble-content">' + _stripMarkdown(m.content).replace(/\n/g, '<br>') + '</div>'
        chatContainer.appendChild(ab)
      }
    })
  }
  if (inputBar) inputBar.style.display = 'flex'
  setTimeout(function() {
    var title = document.getElementById('chatSection')
    if (title) title.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, 100)
}
</script>

<style>
/* ═══ CSS变量体系 ═══ */
:root {
  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --radius-md: 14px;
  --radius-lg: 20px;
  --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif;
  --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif;
  --max-w: 1280px;
}

[data-theme="dark"] {
  --bg-grad-1: #161a2a;
  --bg-grad-2: #1a1e30;
  --bg-grad-3: #141824;
  --accent-h: 38; --accent-s: 60%; --accent-l: 60%;
  --accent: hsl(var(--accent-h), var(--accent-s), var(--accent-l));
  --accent-2: hsl(var(--accent-h), var(--accent-s), 48%);
  --accent-glow: hsla(var(--accent-h), var(--accent-s), var(--accent-l), 0.10);
  --card-bg: rgba(48, 53, 76, 0.85);
  --card-border: rgba(255,255,255,0.12);
  --card-border-hover: rgba(255,255,255,0.18);
  --card-shadow: 0 16px 48px rgba(0,0,0,0.35);
  --input-bg: rgba(58, 64, 90, 0.88);
  --input-border: rgba(255,255,255,0.20);
  --text-1: rgba(240,236,228,0.97);
  --text-2: rgba(195,185,165,0.95);
  --text-3: rgba(170,160,145,0.88);
  --text-4: rgba(160,150,135,0.78);
  --danger: rgba(215,125,110,0.88);
  --success: rgba(110,195,135,0.88);
  --info: rgba(120,170,230,0.88);
  --nav-bg: rgba(22, 26, 42, 0.92);
  --section-alt: rgba(30,34,55,0.45);
  --tag-bg: rgba(255,255,255,0.08);
  --tag-text: rgba(195,185,165,0.85);
  --bg-1: #1a1e30;
  --bg-2: rgba(40, 45, 68, 0.80);
  --border: rgba(255,255,255,0.10);
}

[data-theme="light"] {
  --bg-grad-1: #f7f2ea;
  --bg-grad-2: #f0ebe1;
  --bg-grad-3: #f9f5f0;
  --accent-h: 38; --accent-s: 72%; --accent-l: 30%;
  --accent: hsl(var(--accent-h), var(--accent-s), var(--accent-l));
  --accent-2: hsl(var(--accent-h), var(--accent-s), 22%);
  --accent-glow: hsla(var(--accent-h), var(--accent-s), var(--accent-l), 0.065);
  --card-bg: rgba(255,253,248,0.68);
  --card-border: rgba(0,0,0,0.045);
  --card-border-hover: rgba(0,0,0,0.08);
  --card-shadow: 0 8px 28px rgba(60,40,15,0.055);
  --input-bg: rgba(252,248,240,0.75);
  --input-border: rgba(0,0,0,0.065);
  --text-1: rgba(20,16,10,0.96);
  --text-2: rgba(70,58,40,0.90);
  --text-3: rgba(100,88,68,0.78);
  --text-4: rgba(90,78,58,0.68);
  --danger: rgba(170,65,50,0.88);
  --success: rgba(30,130,60,0.88);
  --info: rgba(30,90,200,0.88);
  --nav-bg: rgba(247,242,234,0.95);
  --section-alt: rgba(240,235,225,0.45);
  --tag-bg: rgba(0,0,0,0.05);
  --tag-text: rgba(70,58,40,0.80);
  --bg-1: #f9f5f0;
  --bg-2: rgba(245,240,230,0.80);
  --border: rgba(0,0,0,0.06);
}

.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer {
  background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%),
    radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%),
    linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3));
}
[data-theme="light"] .bg-layer {
  background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%),
    radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%),
    linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3));
}
.page-wrap { position: relative; z-index: 1; }

/* ═══ 塔罗牌专用样式 ═══ */

/* ── Hero区域 ── */
.tarot-hero {
  text-align: center;
  padding: 60px 20px 40px;
  position: relative;
}
.tarot-hero-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  animation: tarotFloat 4s ease-in-out infinite;
  filter: drop-shadow(0 0 20px rgba(201, 162, 60, 0.4));
}
@keyframes tarotFloat {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-8px) rotate(2deg); }
  75% { transform: translateY(4px) rotate(-2deg); }
}
.tarot-hero-title {
  font-family: var(--font-serif);
  font-size: 2.2rem;
  color: var(--text-1);
  letter-spacing: 4px;
  margin-bottom: 8px;
}
.tarot-hero-desc {
  color: var(--text-3);
  font-size: 0.9375rem;
  line-height: 1.8;
  max-width: 480px;
  margin: 0 auto;
}
.hero-br { display: block; height: 0; }

.tarot-stars {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  overflow: hidden;
}
.tarot-star {
  position: absolute;
  width: 3px; height: 3px;
  background: var(--accent);
  border-radius: 50%;
  opacity: 0;
  animation: starTwinkle 3s ease-in-out infinite;
}
@keyframes starTwinkle {
  0%, 100% { opacity: 0; transform: scale(0.5); }
  50% { opacity: 0.8; transform: scale(1.2); }
}

/* ── 牌阵选择 ── */
.tarot-section {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 20px 40px;
}
.tarot-section-title {
  font-family: var(--font-serif);
  font-size: 1.3rem;
  color: var(--text-1);
  letter-spacing: 2px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.tarot-section-title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(to right, var(--border), transparent);
}
.spread-grid {
  display: grid !important;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.spread-card {
  background: var(--bg-2);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.25s ease;
  overflow: hidden;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.spread-card::before { display: none; }
.spread-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
  box-shadow: 0 2px 12px rgba(201, 162, 60, 0.12);
}
.spread-card.active {
  border-color: var(--accent);
  background: var(--accent-glow);
  box-shadow: 0 0 0 1px var(--accent);
}
.spread-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.spread-card-name {
  font-weight: 700;
  font-size: 0.875rem;
  color: var(--text-1);
}
.spread-card-count {
  font-size: 0.6875rem;
  color: var(--accent);
  background: var(--accent-glow);
  padding: 1px 8px;
  border-radius: 10px;
  border: 1px solid var(--accent);
  white-space: nowrap;
}
.spread-card-desc {
  font-size: 0.75rem;
  color: var(--text-3);
  line-height: 1.2;
  opacity: 0.7;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  white-space: normal;
}

/* ── 设置区域 ── */
.tarot-settings {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  margin: 24px 0;
  padding: 20px;
  background: var(--bg-2);
  border-radius: 12px;
  border: 1px solid var(--border);
}
.tarot-setting-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tarot-setting-label {
  font-size: 0.875rem;
  color: var(--text-2);
}
.tarot-toggle-status {
  font-size: 0.75rem;
  color: var(--text-4);
  margin-left: 2px;
}
.tarot-toggle-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}
.tarot-toggle {
  position: relative;
  width: 44px; height: 24px;
  background: var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.3s;
}
.tarot-toggle.on { background: var(--accent); }
.tarot-toggle-knob {
  position: absolute;
  top: 3px; left: 3px;
  width: 18px; height: 18px;
  background: white;
  border-radius: 50%;
  transition: transform 0.3s;
}
.tarot-toggle.on .tarot-toggle-knob { transform: translateX(20px); }
.tarot-question-input {
  flex: 1;
  min-width: 200px;
  padding: 10px 14px;
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-1);
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.3s;
}

/* ── 抽牌按钮 ── */
.tarot-btn-row { display: flex; gap: 10px; justify-content: center; align-items: center; margin: 30px auto; }
.btn-ghost { background: transparent; border: 1px solid var(--card-border); color: var(--text-3); padding: 7px 18px; border-radius: 10px; font-size: 0.8125rem; }
.tarot-btn-row .tarot-draw-btn {
  margin: 0;
}
.tarot-draw-btn {
  display: block;
  width: 100%;
  max-width: 320px;
  margin: 30px auto;
  padding: 16px 32px;
  background: linear-gradient(135deg, hsl(38, 60%, 52%), hsl(38, 55%, 45%));
  color: white;
  border: none;
  border-radius: 14px;
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: 3px;
  cursor: pointer;
  transition: all 0.35s;
  position: relative;
  overflow: hidden;
  text-align: center;
}
.tarot-draw-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(201, 162, 60, 0.4);
}
.tarot-draw-btn:active { transform: translateY(0); }
.tarot-draw-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
.tarot-draw-btn .btn-ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.3);
  transform: scale(0);
  animation: ripple 0.6s linear;
}
@keyframes ripple {
  to { transform: scale(4); opacity: 0; }
}

/* ── 抽牌动画 ── */
.tarot-drawing-area {
  text-align: center;
  padding: 40px 20px;
  display: none;
}
.tarot-drawing-area.show { display: block; }
.tarot-drawing-text {
  font-family: var(--font-serif);
  font-size: 1.2rem;
  color: var(--accent);
  letter-spacing: 3px;
  margin-bottom: 24px;
}
.tarot-card-stack {
  display: inline-flex;
  position: relative;
  width: 120px;
  height: 180px;
}
.tarot-card-stack .stack-card {
  position: absolute;
  width: 120px;
  height: 180px;
  background: linear-gradient(135deg, var(--bg-2), var(--bg-1));
  border: 2px solid var(--accent);
  border-radius: 10px;
  animation: stackShuffle 1.2s ease-in-out infinite;
}
.tarot-card-stack .stack-card:nth-child(1) { animation-delay: 0s; }
.tarot-card-stack .stack-card:nth-child(2) { animation-delay: 0.15s; top: -2px; left: 2px; }
.tarot-card-stack .stack-card:nth-child(3) { animation-delay: 0.3s; top: -4px; left: 4px; }
.stack-card-inner {
  position: absolute;
  inset: 8px;
  border: 1px solid rgba(201,162,60,0.3);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stack-card-symbol {
  font-size: 2.5rem;
  opacity: 0.6;
}
@keyframes stackShuffle {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(3deg) translateX(4px); }
  75% { transform: rotate(-3deg) translateX(-4px); }
}

/* ── 抽牌结果 ── */
.tarot-result-area {
  display: none;
  max-width: 960px;
  margin: 0 auto;
  padding: 0 20px 40px;
}
.tarot-result-area.show { display: block; }

.tarot-result-header {
  text-align: center;
  margin-bottom: 32px;
}
.tarot-result-title {
  font-family: var(--font-serif);
  font-size: 1.5rem;
  color: var(--text-1);
  letter-spacing: 3px;
}
.draw-time {
  font-size: 0.8125rem;
  color: var(--text-4);
  margin-top: 6px;
}

/* 牌面展示 */
.tarot-cards-display {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin-bottom: 32px;
  justify-items: center;
}
.tarot-cards-display[data-count="1"] { grid-template-columns: 1fr; max-width: 220px; margin-left: auto; margin-right: auto; }
.tarot-cards-display[data-count="3"] { grid-template-columns: repeat(3, 1fr); max-width: 680px; margin-left: auto; margin-right: auto; }
.tarot-cards-display[data-count="5"] { grid-template-columns: repeat(3, 1fr); max-width: 680px; margin-left: auto; margin-right: auto; }
.tarot-cards-display[data-count="6"] { grid-template-columns: repeat(3, 1fr); max-width: 680px; margin-left: auto; margin-right: auto; }
.tarot-cards-display[data-count="7"] { grid-template-columns: repeat(4, 1fr); max-width: 880px; margin-left: auto; margin-right: auto; }
.tarot-cards-display[data-count="10"] { grid-template-columns: repeat(5, 1fr); max-width: 1060px; margin-left: auto; margin-right: auto; }
.tarot-card-slot {
  width: 100%;
  max-width: 204px;
  perspective: 600px;
  overflow-anchor: none;
}
.tarot-card-flipper {
  position: relative;
  width: 100%;
  aspect-ratio: 7 / 13.8;
  height: auto;
  min-height: 360px;
  transition: transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  transform-style: preserve-3d;
  cursor: pointer;
  overflow-anchor: none;
}
.tarot-card-flipper.flipped { transform: rotateY(180deg); }
.tarot-card-front, .tarot-card-back {
  position: absolute;
  inset: 0;
  border-radius: 12px;
  backface-visibility: hidden;
  overflow: visible;
}
.tarot-card-back {
  background: linear-gradient(135deg, var(--bg-2), var(--bg-1));
  border: 2px solid var(--accent);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.tarot-card-back-symbol {
  font-size: 3rem;
  opacity: 0.6;
  margin-bottom: 12px;
}
.tarot-card-back-pattern {
  position: absolute;
  inset: 8px;
  border: 1px solid rgba(201,162,60,0.25);
  border-radius: 8px;
}
.tarot-card-front {
  transform: rotateY(180deg);
  background: #f8f2e4;
  border: 1px solid rgba(126, 91, 38, 0.42);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px;
  box-shadow: inset 0 0 0 4px rgba(255,255,255,0.56);
}
.tarot-card-num {
  font-size: 0.6875rem;
  color: var(--text-4);
  margin-bottom: 4px;
}
.tarot-card-art-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 7 / 12;
  min-height: 0;
  border-radius: 7px;
  overflow: visible;
  background: rgba(90,65,35,0.08);
  border: 1px solid rgba(126,91,38,0.24);
  flex: 0 0 auto;
}
.tarot-card-img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  transform-origin: center;
}
.tarot-card-img-reversed {
  transform: rotate(180deg) scale(0.985);
}
.tarot-card-fallback {
  position: absolute;
  inset: 0;
  display: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px 10px;
  text-align: center;
  background: linear-gradient(180deg, #fbf4e4, #ead9b9);
}
.tarot-card-front.image-failed .tarot-card-img {
  display: none;
}
.tarot-card-front.image-failed .tarot-card-fallback {
  display: flex;
}
.tarot-card-name {
  font-weight: 700;
  font-size: 0.875rem;
  color: #2c2418;
  text-align: center;
  margin: 5px 0 1px;
  letter-spacing: 0;
}
.tarot-card-name-below {
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.25;
}
.tarot-card-name-en {
  font-size: 0.6rem;
  color: rgba(44,36,24,0.64);
  text-align: center;
  margin-bottom: 4px;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.25;
}
.tarot-card-orientation {
  font-size: 0.75rem;
  padding: 1px 7px;
  border-radius: 8px;
  margin-bottom: 4px;
  font-weight: 600;
  flex: 0 0 auto;
}
.tarot-card-orientation.upright {
  color: #5b8c5a;
  background: rgba(91,140,90,0.12);
  border: 1px solid rgba(91,140,90,0.3);
}
.tarot-card-orientation.reversed {
  color: #c0392b;
  background: rgba(192,57,43,0.12);
  border: 1px solid rgba(192,57,43,0.3);
}
.tarot-card-keyword {
  font-size: 0.625rem;
  color: rgba(44,36,24,0.66);
  text-align: center;
  line-height: 1.35;
}
.tarot-card-keyword-below {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 30px;
  padding: 0 3px;
}
.tarot-card-position {
  text-align: center;
  margin-top: 10px;
}
.tarot-card-position-name {
  font-weight: 700;
  font-size: 0.875rem;
  color: var(--accent);
  letter-spacing: 1px;
}
.tarot-card-position-meaning {
  font-size: 0.6875rem;
  color: var(--text-4);
  margin-top: 2px;
}
.tarot-card-reversed-hint {
  font-size: 0.625rem;
  color: #c0392b;
  margin-top: 2px;
}

/* 确认按钮 — 默认隐藏，由JS DOM直操作控制显隐（绕开Vue render effect bug） */
.tarot-confirm-area {
  display: none;
  text-align: center;
  margin: 24px 0;
  padding: 20px;
  background: var(--bg-2);
  border-radius: 12px;
  border: 1px solid var(--border);
}
.confirm-text {
  font-size: 0.875rem;
  color: var(--text-3);
  margin-bottom: 16px;
  line-height: 1.7;
}
.confirm-hint {
  font-size: 0.75rem;
  color: var(--text-4);
}
.tarot-confirm-btns {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
.tarot-btn {
  padding: 10px 28px;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid transparent;
}
.tarot-btn-primary {
  background: linear-gradient(135deg, hsl(38, 60%, 52%), hsl(38, 55%, 45%));
  color: white;
  border-color: transparent;
}
.tarot-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(201,162,60,0.35);
}
.tarot-btn-outline {
  background: transparent;
  color: var(--accent);
  border-color: var(--accent);
}
.tarot-btn-outline:hover {
  background: var(--accent-glow);
}

/* 解读区域 */
.tarot-reading-area {
  display: none;
  margin-top: 24px;
}
.tarot-reading-area.show { display: block; }

.tarot-reading-section {
  background: var(--bg-2);
  border-radius: 14px;
  border: 1px solid var(--border);
  padding: 24px;
  margin-bottom: 16px;
}
.reading-title {
  font-family: var(--font-serif);
  font-size: 1.125rem;
  color: var(--accent);
  letter-spacing: 2px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.reading-body {
  font-size: 0.9375rem;
  color: var(--text-2);
  line-height: 1.9;
}
.reading-body p { margin-bottom: 8px; }
.reading-body ul { padding-left: 20px; }
.reading-body li { margin-bottom: 4px; }
.tarot-reading-card-item {
  padding: 12px 16px;
  background: var(--bg-1);
  border-radius: 10px;
  margin-bottom: 10px;
  border-left: 3px solid var(--accent);
}
.tarot-reading-card-title {
  font-weight: 700;
  color: var(--text-1);
  font-size: 0.9375rem;
  margin-bottom: 6px;
}
.tarot-reading-card-body {
  font-size: 0.875rem;
  color: var(--text-3);
  line-height: 1.8;
}
.tarot-disclaimer {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-4);
  padding: 20px;
  border-top: 1px solid var(--border);
  margin-top: 16px;
}

/* ── 重新抽牌 ── */
.tarot-redraw-area {
  text-align: center;
  margin-top: 20px;
}

/* ── 牌面图标映射 ── */
.suit-wands::before { content: '🔥'; }
.suit-cups::before { content: '💧'; }
.suit-swords::before { content: '🗡️'; }
.suit-pentacles::before { content: '🪙'; }

/* ═══ 弹窗 ═══ */
.modal-overlay {
  display: none; position: fixed; inset: 0; z-index: 300;
  background: rgba(0,0,0,0.55); backdrop-filter: blur(8px);
  align-items: center; justify-content: center;
}
.modal-overlay.open { display: flex; }
.modal-box {
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: var(--radius-lg); padding: 32px; width: 360px;
  backdrop-filter: blur(40px); box-shadow: var(--card-shadow);
}
.modal-title {
  font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px;
  text-align: center; margin-bottom: 24px; color: var(--text-1);
}
.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; }
.field-input {
  width: 100%; padding: 10px 14px; border-radius: 10px;
  background: var(--input-bg); border: 1px solid var(--input-border);
  color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box;
}
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error {
  color: var(--danger); font-size: 0.75rem; text-align: center;
  margin-top: 10px; min-height: 18px;
}

/* ═══ 响应式 ═══ */
@media (max-width: 768px) {
  .tarot-hero-title { font-size: 1.6rem; }
  .spread-grid { grid-template-columns: repeat(2, 1fr); gap: 6px; }
  .tarot-card-slot { max-width: 146px; }
  .tarot-card-flipper { min-height: 282px; }
  .tarot-cards-display { gap: 12px; }
  .tarot-cards-display[data-count="6"] { grid-template-columns: repeat(3, 1fr); max-width: 420px; }
  .tarot-cards-display[data-count="7"] { grid-template-columns: repeat(4, 1fr); max-width: 560px; }
  .tarot-cards-display[data-count="10"] { grid-template-columns: repeat(5, 1fr); max-width: 680px; }
  .tarot-settings { flex-direction: column; align-items: stretch; }
}
@media (max-width: 480px) {
  .tarot-card-slot { max-width: 126px; }
  .tarot-card-flipper { min-height: 258px; }
  .tarot-card-name { font-size: 0.75rem; }
  .tarot-card-name-en { font-size: 0.55rem; }
  .tarot-card-keyword { font-size: 0.56rem; line-height: 1.3; }
  .tarot-card-keyword-below { -webkit-line-clamp: 2; min-height: 28px; }
  .tarot-cards-display[data-count="6"] { grid-template-columns: repeat(2, 1fr); max-width: 240px; }
  .tarot-cards-display[data-count="7"] { grid-template-columns: repeat(3, 1fr); max-width: 360px; }
  .tarot-cards-display[data-count="10"] { grid-template-columns: repeat(4, 1fr); max-width: 480px; }
}

/* ═══ AI 进度区 ═══ */
.ai-reading-progress {
  margin: 12px 0;
}
.ai-stage {
  font-size: 0.9rem;
  color: var(--text-1);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.ai-progress-bar {
  height: 4px;
  background: var(--card-border);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 16px;
}
.ai-progress-fill {
  height: 100%;
  width: 20%;
  background: linear-gradient(90deg, var(--accent), #8b5cf6);
  border-radius: 2px;
  animation: ai-progress-pulse 1.5s ease-in-out infinite;
  transition: width 0.3s ease;
}
@keyframes ai-progress-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
.ai-stream-content {
  font-size: 0.875rem;
  color: var(--text-1);
}
/* AI 解读流式容器 — 与页面原生卡片风格统一 */
.ai-chat-bubble {
  min-height: 200px;
  padding: 0;
  line-height: 1.9;
  font-size: 0.9375rem;
  color: var(--text-2);
}

/* ═══ 对话气泡 ═══ */
.chat-container { display:flex; flex-direction:column; gap:12px; }
.chat-bubble-ai {
  align-self:flex-start;
  background:var(--bg-2);
  border:1px solid var(--border);
  border-radius:14px 14px 14px 4px;
  padding:16px 20px;
  max-width:92%;
  width:100%;
  box-sizing:border-box;
}
.chat-bubble-user {
  align-self:flex-end;
  background:var(--accent);
  color:#fff;
  border-radius:14px 14px 4px 14px;
  padding:10px 16px;
  max-width:80%;
  font-size:0.9rem;
  line-height:1.5;
}
.chat-bubble-content {
  font-size:0.875rem;
  color:var(--text-2);
  line-height:1.9;
}
.chat-input-bar {
  display:flex;
  gap:8px;
  margin-top:16px;
  padding:10px 14px;
  background:var(--bg-2);
  border-radius:12px;
  border:1px solid var(--border);
}
.chat-input {
  flex:1;
  padding:8px 14px;
  border-radius:8px;
  border:1px solid var(--border);
  background:var(--bg-1);
  color:var(--text-1);
  font-size:0.875rem;
  outline:none;
}
.chat-send-btn {
  padding:8px 20px;
  background:var(--accent);
  color:#fff;
  border-radius:8px;
  font-size:0.875rem;
  cursor:pointer;
  white-space:nowrap;
}

</style>
