<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :isLoggedIn="isLoggedIn" @toggle-theme="toggleTheme" />

    <!-- 积分中心 -->
    <view class="page">
      <!-- 顶部返回 -->
      <view class="page-header">
        <view class="back-btn" style="visibility:hidden;">‹ 返回</view>
        <text class="page-title">积分中心</text>
        <view class="back-btn-placeholder"></view>
      </view>

      <!-- 积分余额卡片 -->
      <view class="points-card">
        <view class="points-balance">
          <text class="points-number" id="pointsNumber">--</text>
          <text class="points-unit">积分</text>
        </view>
        <view class="points-level" id="pointsLevel"></view>
        <view class="signin-btn" id="signinBtn" @click="doSignin">
          <text id="signinText">每日签到</text>
          <text class="signin-reward">+10分</text>
        </view>
      </view>

      <!-- 充值套餐 -->
      <view class="section">
        <view class="section-title">充值套餐</view>
        <view class="pkg-scroll" id="pkgScroll">
          <view class="pkg-card" v-for="pkg in packages" :key="pkg.id" @click="selectPackage(pkg)">
            <text class="pkg-points">{{ pkg.points }}</text>
            <text class="pkg-label">积分</text>
            <view class="pkg-price">¥{{ pkg.price }}</view>
            <view class="pkg-name">{{ pkg.name }}</view>
          </view>
        </view>
      </view>

      <!-- 积分明细 -->
      <view class="section">
        <view class="section-title">积分明细</view>
        <view class="dp-tabs">
          <view class="dp-tab active" id="dpTabAll" onclick="window._switchDpTab('all')">全部</view>
          <view class="dp-tab" id="dpTabPlus" onclick="window._switchDpTab('plus')">获取</view>
          <view class="dp-tab" id="dpTabMinus" onclick="window._switchDpTab('minus')">消耗</view>
        </view>
        <view id="pointsLogList">
          <view class="log-empty" id="logEmpty">暂无记录</view>
        </view>
        <view class="dp-pager" id="dpPager"></view>
      </view>
    </view>

    <!-- 充值弹窗 -->
    <view class="modal-overlay" id="rechargeModal" @click="closeRechargeModal">
      <view class="modal-box recharge-modal" @click.stop>
        <view class="modal-title">选择支付方式</view>
        <view class="recharge-summary">
          <text class="recharge-pkg-name" id="rechargePkgName"></text>
          <text class="recharge-amount" id="rechargeAmount"></text>
        </view>
        <view class="pay-methods">
          <view class="pay-method" @click="payByTransfer">
            <text class="pay-icon">💳</text>
            <view class="pay-info">
              <text class="pay-name">微信/支付宝转账</text>
              <text class="pay-desc">联系客服手动充值，到账后自动加积分</text>
            </view>
          </view>
          <view class="pay-hint">注：微信支付正在接入中，当前暂支持手动转账充值</view>
        </view>
        <view class="modal-btns">
          <view class="btn btn-outline" @click="closeRechargeModal">取消</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { ref, inject, onMounted } from 'vue'
import TopNav from '../../components/TopNav.vue'

export default {
  components: { TopNav },
  setup() {
    var theme = inject('theme', ref('light'))
    // 直接检查 localStorage 中的登录状态，不依赖 Vue inject
    // 因为 uni-app 子包页面可能无法继承父级的 provide
    var isLoggedIn = ref(false)
    try { isLoggedIn.value = !!(uni.getStorageSync('xc_token') || localStorage.getItem('xc_token')) } catch(_) {}
    var toggleTheme = inject('toggleTheme', function() {})

    var packages = [
      { id: 'starter',  name: '体验包',  points: 50,   price: 9.9 },
      { id: 'standard', name: '标准包',  points: 200,  price: 29.9 },
      { id: 'premium',  name: '畅享包',  points: 500,  price: 68 },
      { id: 'vip',      name: '尊享包',  points: 2000, price: 198 },
    ]

    var dpFilter = 'all'
    var dpLogs = []
    var dpPage = 1
    var dpPerPage = 5

    function renderDpLogs() {
      var filtered = dpLogs
      if (dpFilter === 'plus') filtered = dpLogs.filter(function(l) { return l.points >= 0 })
      else if (dpFilter === 'minus') filtered = dpLogs.filter(function(l) { return l.points < 0 })
      var totalPages = Math.ceil(filtered.length / dpPerPage) || 1
      if (dpPage > totalPages) dpPage = totalPages
      var start = (dpPage - 1) * dpPerPage
      var pageItems = filtered.slice(start, start + dpPerPage)

      var el = document.getElementById('pointsLogList')
      if (!el) return
      if (!pageItems.length) {
        el.innerHTML = '<view class="log-empty">暂无记录</view>'
        document.getElementById('dpPager').innerHTML = ''
        return
      }
      var h = '<view class="dp-list">'
      pageItems.forEach(function(log) {
        var date = log.createdAt ? log.createdAt.substring(0, 16).replace('T', ' ') : ''
        var sign = log.points >= 0 ? '+' : ''
        var cls = log.points >= 0 ? 'dp-plus' : 'dp-minus'
        h += '<view class="dp-item">'
          + '<view class="dp-left">'
          + '<text class="dp-desc">' + (log.description || log.action) + '</text>'
          + '<text class="dp-date">' + date + '</text>'
          + '</view>'
          + '<text class="dp-points ' + cls + '">' + sign + log.points + '</text>'
          + '</view>'
      })
      h += '</view>'
      el.innerHTML = h

      var pagerHtml = ''
      if (totalPages > 1) {
        if (dpPage > 1) pagerHtml += '<view class="dp-page-btn" onclick="window._dpGo(' + (dpPage - 1) + ')">‹</view>'
        for (var i = 1; i <= totalPages; i++) {
          pagerHtml += '<view class="dp-page-num' + (i === dpPage ? ' dp-page-cur' : '') + '" onclick="window._dpGo(' + i + ')">' + i + '</view>'
        }
        if (dpPage < totalPages) pagerHtml += '<view class="dp-page-btn" onclick="window._dpGo(' + (dpPage + 1) + ')">›</view>'
      }
      document.getElementById('dpPager').innerHTML = pagerHtml
    }

    window._dpGo = function(p) { dpPage = p; renderDpLogs() }

    window._switchDpTab = function(t) {
      dpFilter = t; dpPage = 1
      document.querySelectorAll('.dp-tab').forEach(function(el) { el.classList.remove('active') })
      var tabMap = { all: 'dpTabAll', plus: 'dpTabPlus', minus: 'dpTabMinus' }
      var target = document.getElementById(tabMap[t])
      if (target) target.classList.add('active')
      renderDpLogs()
    }

    function loadLogs() {
      if (!isLoggedIn.value) return
      uni.request({
        url: '/api/points/log?page=1&per_page=50', method: 'GET',
        success: function(res) {
          var d = res.data
          dpLogs = (d && d.logs) || []
          renderDpLogs()
        }
      })
    }

    function loadMoreLogs() {} // no longer used

    function goBack() {
      uni.switchTab({ url: '/pages/index/index' })
    }

    function loadPoints() {
      if (!isLoggedIn.value) return
      uni.request({
        url: '/api/membership', method: 'GET',
        success: function(res) {
          var d = res.data
          if (!d || typeof d.points !== 'number') return
          var el = document.getElementById('pointsNumber')
          if (el) el.textContent = d.points
          var lv = document.getElementById('pointsLevel')
          if (lv) {
            var labels = { free: '普通用户', basic: '白银会员', premium: '黄金会员', vip: '钻石会员' }
            lv.textContent = labels[d.level] || d.level
          }
          var btn = document.getElementById('signinBtn')
          if (d.signed_in_today && btn) {
            btn.classList.add('signed')
            var txt = document.getElementById('signinText')
            if (txt) txt.textContent = '已签到'
          }
        }
      })
    }

    function doSignin() {
      var btn = document.getElementById('signinBtn')
      if (btn && btn.classList.contains('signed')) return
      uni.request({
        url: '/api/membership/sign-in', method: 'POST',
        success: function(res) {
          var d = res.data
          if (d && d.ok) {
            var el = document.getElementById('pointsNumber')
            if (el) el.textContent = d.points
            if (btn) btn.classList.add('signed')
            var txt = document.getElementById('signinText')
            if (txt) txt.textContent = '已签到'
            uni.showToast({ title: '签到成功 +' + d.added, icon: 'success' })
            try { window.dispatchEvent(new CustomEvent('xc-points-updated', { detail: { points: d.points } })) } catch(_) {}
            loadLogs()
          } else if (d && d.error) {
            uni.showToast({ title: d.error, icon: 'none' })
          }
        },
        fail: function() {
          uni.showToast({ title: '签到失败', icon: 'none' })
        }
      })
    }

    function selectPackage(pkg) {
      var modal = document.getElementById('rechargeModal')
      if (!modal) return
      modal.classList.add('open')
      var nameEl = document.getElementById('rechargePkgName')
      if (nameEl) nameEl.textContent = pkg.name + '：' + pkg.points + ' 积分'
      var amtEl = document.getElementById('rechargeAmount')
      if (amtEl) amtEl.textContent = '需支付 ¥' + pkg.price
      modal.dataset.pkgId = pkg.id
    }

    function closeRechargeModal() {
      var modal = document.getElementById('rechargeModal')
      if (modal) modal.classList.remove('open')
    }

    function payByTransfer() {
      closeRechargeModal()
      uni.showModal({
        title: '手动充值',
        content: '请联系客服微信：xxx，备注您的用户名，付款后将为您手动到账。',
        showCancel: false,
        confirmText: '知道了'
      })
      // 创建订单记录
      var modal = document.getElementById('rechargeModal')
      var pkgId = modal ? modal.dataset.pkgId : ''
      if (pkgId) {
        uni.request({
          url: '/api/recharge/create-order', method: 'POST',
          data: { package_id: pkgId, pay_method: 'transfer' }
        })
      }
    }

    onMounted(function() {
      loadPoints()
      loadLogs()
    })

    return { theme, isLoggedIn, toggleTheme, packages, goBack, doSignin, loadMoreLogs, selectPackage, closeRechargeModal, payByTransfer }
  }
}
</script>

<style>
.page-root { min-height: 100vh; background: var(--bg); }
.page { max-width: 640px; margin: 0 auto; padding: 10px 16px 40px; }

/* 页头 */
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 0 16px;
}
.back-btn {
  font-size: 0.88rem; color: var(--accent); cursor: pointer;
  padding: 6px 10px; border-radius: 8px;
}
.back-btn:hover { background: var(--accent-glow); }
.page-title { font-size: 1.05rem; font-weight: 700; color: var(--text-1); font-family: var(--font-serif); }
.back-btn-placeholder { width: 60px; }

/* 积分卡片 */
.points-card {
  background: linear-gradient(135deg, #c9a84c, #b2955d, #8d7140);
  border-radius: 18px; padding: 32px 24px 28px; text-align: center;
  margin-bottom: 24px; color: #fff;
  box-shadow: 0 8px 32px rgba(178,149,93,0.3), inset 0 1px 0 rgba(255,255,255,0.15);
  position: relative; overflow: hidden;
}
.points-card::before {
  content: ''; position: absolute; top: -50%; right: -50%;
  width: 100%; height: 100%;
  background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
  pointer-events: none;
}
.points-balance { display: flex; align-items: baseline; justify-content: center; gap: 6px; margin-bottom: 4px; position: relative; z-index: 1; }
.points-number { font-size: 3rem; font-weight: 800; letter-spacing: -1px; text-shadow: 0 2px 8px rgba(0,0,0,0.15); }
.points-unit { font-size: 1rem; opacity: 0.85; }
.points-level { font-size: 0.82rem; opacity: 0.75; margin-bottom: 18px; position: relative; z-index: 1; }
.signin-btn {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,0.18); backdrop-filter: blur(4px);
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 24px; padding: 10px 28px; cursor: pointer;
  font-size: 0.88rem; transition: all 0.25s;
  position: relative; z-index: 1;
}
.signin-btn:hover { background: rgba(255,255,255,0.3); transform: translateY(-1px); }
.signin-btn:active { transform: translateY(0); }
.signin-btn.signed { opacity: 0.5; cursor: default; background: rgba(255,255,255,0.1); }
.signin-btn.signed:hover { background: rgba(255,255,255,0.1); transform: none; }
.signin-reward { font-size: 0.75rem; opacity: 0.8; }

/* 区块标题 */
.section { margin-bottom: 24px; }
.section-title {
  font-size: 0.92rem; font-weight: 700; color: var(--text-1);
  margin-bottom: 12px; padding-left: 4px;
}

/* 充值套餐 */
.pkg-scroll {
  display: flex; gap: 10px;
  padding: 4px 0 8px;
}
.pkg-card {
  flex: 1 1 0; min-width: 0; background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: 14px; padding: 18px 10px; text-align: center;
  cursor: pointer; transition: transform 0.15s, box-shadow 0.15s;
}
.pkg-card:hover { transform: translateY(-3px); box-shadow: var(--card-shadow); }
.pkg-card:first-child { background: linear-gradient(135deg, var(--accent-glow), var(--card-bg)); border-color: var(--accent); }
.pkg-points { display: block; font-size: 1.6rem; font-weight: 800; color: var(--accent); }
.pkg-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 10px; }
.pkg-price { font-size: 1rem; font-weight: 700; color: var(--text-1); margin-bottom: 4px; }
.pkg-name { font-size: 0.72rem; color: var(--text-3); }

/* 积分明细 — 时光轴 */
.log-empty { text-align: center; padding: 40px 0; color: var(--text-3); font-size: 0.85rem; }
.load-more {
  text-align: center; padding: 16px; color: var(--accent); font-size: 0.82rem;
  cursor: pointer; margin-top: 8px;
}
.load-more:hover { opacity: 0.7; }

/* 弹窗遮罩 */
.modal-overlay {
  position: fixed; top: 0; right: 0; bottom: 0; left: 0;
  z-index: 999; background: rgba(0,0,0,.55);
  display: none; align-items: center; justify-content: center;
  backdrop-filter: blur(4px);
}
.modal-overlay.open { display: flex; }
.modal-box {
  background: var(--card-bg); border-radius: 18px;
  padding: 28px 32px; max-width: 400px; width: 90%;
  box-shadow: 0 12px 40px rgba(0,0,0,.2);
}
.modal-title { font-size: 1.05rem; font-weight: 700; color: var(--text-1); margin-bottom: 18px; text-align: center; }
.modal-btns { display: flex; gap: 10px; margin-top: 6px; }

/* 充值弹窗 */
.recharge-modal { max-width: 360px; }
.recharge-summary {
  background: var(--accent-glow); border-radius: 10px;
  padding: 14px 16px; margin-bottom: 16px; text-align: center;
}
.recharge-pkg-name { display: block; font-size: 0.88rem; color: var(--text-2); margin-bottom: 4px; }
.recharge-amount { display: block; font-size: 1.2rem; font-weight: 700; color: var(--accent); }
.pay-methods { margin-bottom: 14px; }
.pay-method {
  display: flex; align-items: center; gap: 12px;
  width: 100%;
  padding: 14px; border: 1px solid var(--card-border); border-radius: 12px;
  cursor: pointer; transition: border-color 0.15s;
}
.pay-method:hover { border-color: var(--accent); }
.pay-icon { font-size: 1.5rem; }
.pay-info { display: flex; flex-direction: column; gap: 2px; }
.pay-name { font-size: 0.85rem; font-weight: 600; color: var(--text-1); }
.pay-desc { font-size: 0.72rem; color: var(--text-3); }
.pay-hint { font-size: 0.7rem; color: var(--text-3); text-align: center; margin-top: 8px; padding: 0 10px; }

/* 响应式 */
@media (max-width: 480px) {
  .pkg-card { flex: 0 0 110px; min-width: unset; padding: 14px 12px; }
  .points-number { font-size: 2.2rem; }
}
</style>
