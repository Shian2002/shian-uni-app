<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :isLoggedIn="isLoggedIn" @toggle-theme="toggleTheme" />

    <!-- 积分中心 -->
    <view class="page">
      <!-- 顶部返回 -->
      <view class="page-header">
        <view class="back-btn" @click="goBack">‹ 返回</view>
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
        <view class="section-head">
          <view class="section-title">充值套餐</view>
          <view class="section-hint">横向滑动查看更多</view>
        </view>
        <view class="pkg-scroll-wrap">
          <view class="pkg-scroll" id="pkgScroll">
            <view class="pkg-card" v-for="pkg in packages" :key="pkg.id" @click="selectPackage(pkg)">
              <text class="pkg-points">{{ pkg.points }}</text>
              <text class="pkg-label">积分</text>
              <view class="pkg-price">¥{{ pkg.price }}</view>
              <view class="pkg-name">{{ pkg.name }}</view>
            </view>
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
        <view class="alipay-panel">
          <image class="alipay-qr" src="/static/alipay-recharge.jpg" mode="widthFix" />
          <view class="pay-hint">请用支付宝扫码付款，付款金额必须与当前套餐一致。</view>
          <input
            class="payment-input"
            v-model="paymentReference"
            type="text"
            placeholder="填写支付宝订单号/付款备注"
            maxlength="80"
          />
          <view class="btn btn-primary verify-pay-btn" :class="{ disabled: paymentChecking }" @click="verifyAlipayPayment">
            {{ paymentChecking ? '识别中...' : '已付款，自动识别到账' }}
          </view>
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
      { id: 'starter',  name: '体验包',  points: 60,   price: 9.9 },
      { id: 'standard', name: '标准包',  points: 240,  price: 29.9 },
      { id: 'premium',  name: '畅享包',  points: 650,  price: 68 },
      { id: 'vip',      name: '尊享包',  points: 2200, price: 198 },
    ]

    var dpFilter = 'all'
    var dpLogs = []
    var dpPage = 1
    var dpPerPage = 5
    var currentPackage = null
    var currentOrderId = ref(null)
    var paymentReference = ref('')
    var paymentChecking = ref(false)

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
        var pages = []
        if (totalPages <= 5) {
          // 5页以内全部显示
          for (var i = 1; i <= totalPages; i++) pages.push(i)
        } else {
          // 超过5页，滑动窗口
          if (dpPage <= 3) {
            // 前3页显示 1-5
            for (var i = 1; i <= 5; i++) pages.push(i)
          } else if (dpPage >= totalPages - 2) {
            // 后3页显示最后5页
            for (var i = totalPages - 4; i <= totalPages; i++) pages.push(i)
          } else {
            // 中间，当前页居中显示
            for (var i = dpPage - 2; i <= dpPage + 2; i++) pages.push(i)
          }
        }
        pages.forEach(function(p) {
          pagerHtml += '<view class="dp-page-num' + (p === dpPage ? ' dp-page-cur' : '') + '" onclick="window._dpGo(' + p + ')">' + p + '</view>'
        })
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
      currentPackage = pkg
      currentOrderId.value = null
      paymentReference.value = ''
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
      paymentChecking.value = false
    }

    function ensureRechargeOrder(done) {
      if (currentOrderId.value) {
        done(currentOrderId.value)
        return
      }
      var modal = document.getElementById('rechargeModal')
      var pkgId = modal ? modal.dataset.pkgId : ''
      if (!pkgId) {
        uni.showToast({ title: '请选择充值套餐', icon: 'none' })
        return
      }
      uni.request({
        url: '/api/recharge/create-order',
        method: 'POST',
        data: { package_id: pkgId, pay_method: 'alipay_qr' },
        success: function(res) {
          var d = res.data || {}
          if (!d.ok || !d.order_id) {
            uni.showToast({ title: d.error || '创建订单失败', icon: 'none' })
            return
          }
          currentOrderId.value = d.order_id
          done(d.order_id)
        },
        fail: function() {
          uni.showToast({ title: '创建订单失败', icon: 'none' })
        }
      })
    }

    function verifyAlipayPayment() {
      if (paymentChecking.value) return
      if (!currentPackage) {
        uni.showToast({ title: '请选择充值套餐', icon: 'none' })
        return
      }
      var reference = (paymentReference.value || '').trim()
      if (reference.length < 4) {
        uni.showToast({ title: '请填写支付宝订单号或付款备注', icon: 'none' })
        return
      }
      paymentChecking.value = true
      ensureRechargeOrder(function(orderId) {
        uni.request({
          url: '/api/recharge/verify-payment',
          method: 'POST',
          data: {
            order_id: orderId,
            paid_amount: currentPackage.price,
            payment_reference: reference,
            payment_proof: '用户在积分中心提交支付宝扫码付款凭证'
          },
          success: function(res) {
            var d = res.data || {}
            if (!d.ok) {
              uni.showToast({ title: d.error || '识别失败', icon: 'none' })
              return
            }
            closeRechargeModal()
            if (d.status === 'pending') {
              uni.showToast({ title: d.message || '已提交，待确认到账', icon: 'none' })
              loadLogs()
              return
            }
            uni.showToast({ title: '充值到账 +' + d.added, icon: 'success' })
            if (typeof d.points === 'number') {
              var el = document.getElementById('pointsNumber')
              if (el) el.textContent = d.points
              try { window.dispatchEvent(new CustomEvent('xc-points-updated', { detail: { points: d.points } })) } catch(_) {}
            }
            loadLogs()
          },
          fail: function() {
            uni.showToast({ title: '识别失败', icon: 'none' })
          },
          complete: function() {
            paymentChecking.value = false
          }
        })
      })
    }

    onMounted(function() {
      loadPoints()
      loadLogs()
    })

    return {
      theme,
      isLoggedIn,
      toggleTheme,
      packages,
      paymentReference,
      paymentChecking,
      goBack,
      doSignin,
      loadMoreLogs,
      selectPackage,
      closeRechargeModal,
      verifyAlipayPayment,
    }
  }
}
</script>

<style>
.page-root { min-height: 100vh; background: var(--bg); }
.page { max-width: 640px; margin: 0 auto; padding: 10px 16px 40px; }

@media (min-width: 769px) {
  .topnav { padding-left: 16px; padding-right: 16px; }
  .nav-btn { padding-left: 8px; padding-right: 8px; font-size: 0.9rem; }
  .topnav-sidebar-btn { margin-right: 0; }
}

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
.section-head {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; margin-bottom: 12px; padding-left: 4px;
}
.section-title {
  font-size: 0.92rem; font-weight: 700; color: var(--text-1);
}
.section-hint {
  display: none; flex-shrink: 0; align-items: center; gap: 4px;
  font-size: 0.72rem; color: var(--text-3);
}
.section-hint::after {
  content: '›'; display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; border-radius: 50%;
  color: var(--accent); background: var(--accent-glow);
}

/* 充值套餐 */
.pkg-scroll-wrap { position: relative; overflow: hidden; }
.pkg-scroll {
  display: flex; gap: 10px;
  padding: 4px 0 8px;
  max-width: 100%;
  box-sizing: border-box;
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
  padding: 24px 24px; max-width: 400px; width: 90%;
  box-shadow: 0 12px 40px rgba(0,0,0,.2);
}
.modal-title { font-size: 1.05rem; font-weight: 700; color: var(--text-1); margin-bottom: 18px; text-align: center; }
.modal-btns { display: flex; gap: 10px; margin-top: 6px; }
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 10px 16px; border-radius: 10px; font-size: 0.82rem;
  cursor: pointer; text-align: center; box-sizing: border-box;
}
.btn-outline { background: transparent; border: 1px solid var(--card-border); color: var(--text-2); }
.btn-primary { border: 1px solid var(--accent); background: var(--accent); color: #fff; font-weight: 700; }
.btn.disabled { opacity: 0.55; cursor: not-allowed; }

/* 充值弹窗 */
.recharge-modal { max-width: 360px; }
.recharge-summary {
  background: var(--accent-glow); border-radius: 10px;
  padding: 14px 16px; margin-bottom: 16px; text-align: center;
}
.recharge-pkg-name { display: block; font-size: 0.88rem; color: var(--text-2); margin-bottom: 4px; }
.recharge-amount { display: block; font-size: 1.2rem; font-weight: 700; color: var(--accent); }
.alipay-panel { display: flex; flex-direction: column; align-items: stretch; gap: 10px; margin-bottom: 14px; }
.alipay-qr {
  display: block; width: min(100%, 260px); max-height: 390px;
  margin: 0 auto; border-radius: 12px; border: 1px solid var(--card-border);
  background: #fff;
}
.payment-input {
  width: 100%; height: 42px; padding: 0 12px; box-sizing: border-box;
  border: 1px solid var(--card-border); border-radius: 10px;
  background: var(--bg); color: var(--text-1); font-size: 0.82rem;
}
.verify-pay-btn { width: 100%; }
.pay-hint { font-size: 0.72rem; line-height: 1.5; color: var(--text-3); text-align: center; padding: 0 4px; }

/* 响应式 */
@media (max-width: 480px) {
  .section-head { padding-left: 0; }
  .section-hint { display: inline-flex; }
  .pkg-scroll-wrap::after {
    content: ''; position: absolute; top: 0; right: 0; bottom: 0;
    width: 42px; pointer-events: none;
    background: linear-gradient(90deg, transparent, var(--bg));
  }
  .pkg-scroll {
    overflow-x: auto; overflow-y: hidden;
    padding: 4px 34px 10px 0;
    scroll-snap-type: x proximity;
    -webkit-overflow-scrolling: touch;
  }
  .pkg-scroll::-webkit-scrollbar { height: 0; }
  .pkg-card {
    flex: 0 0 124px; min-width: 124px; padding: 14px 12px;
    scroll-snap-align: start;
  }
  .points-number { font-size: 2.2rem; }
}
</style>
