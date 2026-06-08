<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :isLoggedIn="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page points-page">
      <view class="points-hero">
        <view>
          <view class="eyebrow">账户中心</view>
          <text class="page-title">积分中心</text>
        </view>
        <view class="hero-actions">
          <view class="back-btn" style="visibility:hidden;">‹ 返回</view>
        </view>
      </view>

      <view class="points-layout">
        <view class="account-panel">
          <view class="account-card points-card">
            <view class="account-card-head">
              <view>
                <text class="account-label">可用积分</text>
                <view class="points-balance">
                  <text class="points-number" id="pointsNumber">--</text>
                  <text class="points-unit">分</text>
                </view>
              </view>
              <view class="points-level" id="pointsLevel"></view>
            </view>
            <view class="account-divider"></view>
            <view class="account-actions">
              <view class="signin-btn" id="signinBtn" @click="doSignin">
                <text id="signinText">每日签到</text>
                <text class="signin-reward">+10</text>
              </view>
              <view class="account-note">充值后请在账本核对到账记录</view>
            </view>
          </view>

          <view class="account-guide">
            <view class="guide-item">
              <text class="guide-k">用途</text>
              <text class="guide-v">AI 解读、深度合参、工具增值</text>
            </view>
            <view class="guide-item">
              <text class="guide-k">到账</text>
              <text class="guide-v">支付成功后自动到账</text>
            </view>
          </view>
        </view>

        <view class="commerce-panel">
          <view class="section shop-section">
            <view class="section-head">
              <view>
                <view class="section-title">积分充值</view>
                <view class="section-subtitle">适合自由选择不同术数解读</view>
              </view>
            </view>
            <view class="pkg-grid" id="pkgScroll">
              <view class="pkg-card" v-for="(pkg, index) in pointPackages" :key="pkg.id" :class="{ recommended: index === 2 }" @click="selectPackage(pkg)">
                <view class="pkg-badge" v-if="index === 2">推荐</view>
                <text class="pkg-name">{{ pkg.name }}</text>
                <view class="pkg-points-row">
                  <text class="pkg-points">{{ pkg.points }}</text>
                  <text class="pkg-label">积分</text>
                </view>
                <view class="pkg-price">¥{{ pkg.price }}</view>
              </view>
            </view>
          </view>

          <view class="section shop-section" v-if="aiPackages.length">
            <view class="section-head">
              <view>
                <view class="section-title">AI 次数套餐</view>
                <view class="section-subtitle">用于首页统一解读和多盘合参</view>
              </view>
            </view>
            <view class="pkg-grid ai-pkg-grid">
              <view class="pkg-card ai-pkg-card" v-for="(pkg, index) in aiPackages" :key="pkg.id" :class="{ recommended: index === 0 }" @click="selectPackage(pkg)">
                <view class="pkg-badge" v-if="index === 0">常用</view>
                <text class="pkg-name">{{ pkg.name }}</text>
                <view class="pkg-points-row">
                  <text class="pkg-points">{{ pkg.ai_single_credits || pkg.ai_combo_credits }}</text>
                  <text class="pkg-label">{{ pkg.ai_combo_credits ? '合参次数' : '单术数次数' }}</text>
                </view>
                <view class="pkg-price">¥{{ pkg.price }}</view>
                <view class="pkg-desc">{{ pkg.description }}</view>
              </view>
            </view>
          </view>

          <view class="section ledger-section">
            <view class="section-head ledger-head">
              <view>
                <view class="section-title">积分账本</view>
                <view class="section-subtitle">充值、签到和消耗记录</view>
              </view>
              <view class="dp-tabs">
                <view class="dp-tab active" id="dpTabAll" onclick="window._switchDpTab('all')">全部</view>
                <view class="dp-tab" id="dpTabPlus" onclick="window._switchDpTab('plus')">获取</view>
                <view class="dp-tab" id="dpTabMinus" onclick="window._switchDpTab('minus')">消耗</view>
              </view>
            </view>
            <view id="pointsLogList">
              <view class="log-empty" id="logEmpty">暂无记录</view>
            </view>
            <view class="dp-pager" id="dpPager"></view>
          </view>
        </view>
      </view>
    </view>

    <!-- 充值弹窗 -->
    <view class="modal-overlay" id="rechargeModal" @click="closeRechargeModal">
      <view class="modal-box recharge-modal pay-sheet" @click.stop>
        <view class="modal-head">
          <view>
            <view class="modal-title">创建账单</view>
            <view class="modal-subtitle">扫码后自动到账</view>
          </view>
          <view class="modal-close" @click="closeRechargeModal">×</view>
        </view>
        <view class="recharge-summary">
          <text class="recharge-pkg-name" id="rechargePkgName"></text>
          <text class="recharge-amount" id="rechargeAmount"></text>
        </view>
        <view class="hupijiao-panel">
          <view class="qr-panel">
            <img class="hupijiao-qr" v-if="paymentQrUrl" :src="paymentQrUrl" alt="支付二维码" />
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { ref, inject, onMounted, onBeforeUnmount } from 'vue'
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

    var packages = ref([
      { id: 'test-cent', name: '测试包',  points: 1,    price: 0.01, package_type: 'points' },
      { id: 'starter',  name: '体验包',  points: 60,   price: 9.9, package_type: 'points' },
      { id: 'standard', name: '标准包',  points: 240,  price: 29.9, package_type: 'points' },
      { id: 'premium',  name: '畅享包',  points: 650,  price: 68, package_type: 'points' },
      { id: 'vip',      name: '尊享包',  points: 2200, price: 198, package_type: 'points' },
    ])
    var pointPackages = ref([])
    var aiPackages = ref([])

    var dpFilter = 'all'
    var dpLogs = []
    var dpPage = 1
    var dpPerPage = 5
    var currentPackage = null
    var currentOrderId = ref(null)
    var paymentPayUrl = ref('')
    var paymentQrUrl = ref('')
    var paymentState = ref('idle')
    var paymentStateLabel = ref('等待创建')
    var paymentStatusText = ref('选择套餐后会自动创建账单。')
    var paymentChecking = ref(false)
    var paymentPollTimer = null
    var paymentPollCount = 0
    var ledgerRefreshTimer = null
    var pendingQrOrderId = null

    function resetPointsSessionState() {
      isLoggedIn.value = false
      dpLogs = []
      dpPage = 1
      dpFilter = 'all'
      currentPackage = null
      currentOrderId.value = null
      paymentPayUrl.value = ''
      paymentQrUrl.value = ''
      paymentState.value = 'idle'
      paymentStateLabel.value = '等待创建'
      paymentStatusText.value = '选择套餐后会自动创建账单。'
      paymentChecking.value = false
      stopPaymentPolling()
      stopLedgerRefresh()
      try {
        var pointsEl = document.getElementById('pointsNumber')
        var levelEl = document.getElementById('pointsLevel')
        var logEl = document.getElementById('pointsLogList')
        var pagerEl = document.getElementById('dpPager')
        var signBtn = document.getElementById('signinBtn')
        var signText = document.getElementById('signinText')
        var modal = document.getElementById('rechargeModal')
        if (pointsEl) pointsEl.textContent = '--'
        if (levelEl) levelEl.textContent = ''
        if (logEl) logEl.innerHTML = '<view class="log-empty">登录后查看积分账本</view>'
        if (pagerEl) pagerEl.innerHTML = ''
        if (signBtn) signBtn.classList.remove('signed')
        if (signText) signText.textContent = '每日签到'
        if (modal) modal.classList.remove('open')
        document.querySelectorAll('.dp-tab').forEach(function(el) { el.classList.remove('active') })
        var allTab = document.getElementById('dpTabAll')
        if (allTab) allTab.classList.add('active')
      } catch(_) {}
    }

    function handleAuthChanged(e) {
      var detail = e && e.detail ? e.detail : {}
      if (detail.type === 'logout' || detail.loggedIn === false) {
        resetPointsSessionState()
        return
      }
      if (detail.type === 'login' || detail.loggedIn === true) {
        isLoggedIn.value = true
        loadPoints()
        loadLogs()
        startLedgerRefresh()
      }
    }

    function formatLogTime(value) {
      if (!value) return ''
      var raw = String(value)
      var date = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(raw) ? raw : raw + 'Z')
      if (Number.isNaN(date.getTime())) return raw.substring(0, 16).replace('T', ' ')
      try {
        var parts = new Intl.DateTimeFormat('zh-CN', {
          timeZone: 'Asia/Shanghai',
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        }).formatToParts(date).reduce(function(acc, p) {
          acc[p.type] = p.value
          return acc
        }, {})
        return parts.year + '-' + parts.month + '-' + parts.day + ' ' + parts.hour + ':' + parts.minute
      } catch(_) {
        var local = new Date(date.getTime() + 8 * 60 * 60 * 1000)
        return local.toISOString().substring(0, 16).replace('T', ' ')
      }
    }

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
        var date = formatLogTime(log.createdAt)
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
      if (!isLoggedIn.value) {
        resetPointsSessionState()
        return
      }
      uni.request({
        url: '/api/points/log?page=1&per_page=50', method: 'GET',
        success: function(res) {
          var d = res.data
          dpLogs = (d && d.logs) || []
          renderDpLogs()
        }
      })
    }

    function startLedgerRefresh() {
      stopLedgerRefresh()
      if (!isLoggedIn.value) return
      ledgerRefreshTimer = setInterval(function() {
        if (!isLoggedIn.value) {
          stopLedgerRefresh()
          return
        }
        loadPoints()
        loadLogs()
      }, 10000)
    }

    function stopLedgerRefresh() {
      if (ledgerRefreshTimer) {
        clearInterval(ledgerRefreshTimer)
        ledgerRefreshTimer = null
      }
    }

    function loadMoreLogs() {} // no longer used

    function goBack() {
      uni.switchTab({ url: '/pages/index/index' })
    }

    function loadPoints() {
      if (!isLoggedIn.value) {
        resetPointsSessionState()
        return
      }
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

    function splitPackages(list) {
      var arr = Array.isArray(list) ? list : []
      pointPackages.value = arr.filter(function(p) { return (p.package_type || 'points') === 'points' })
      aiPackages.value = arr.filter(function(p) { return p.package_type === 'ai' })
      if (!pointPackages.value.length) pointPackages.value = packages.value.filter(function(p) { return (p.package_type || 'points') === 'points' })
    }

    function loadPackages() {
      uni.request({
        url: '/api/recharge/packages',
        method: 'GET',
        success: function(res) {
          var list = (res.data && res.data.packages) || []
          if (Array.isArray(list) && list.length) {
            packages.value = list
            splitPackages(list)
          }
        },
        fail: function() {
          splitPackages(packages.value)
        }
      })
    }

    function doSignin() {
      if (!isLoggedIn.value) {
        try { if (window._openLoginModal) window._openLoginModal() } catch(_) {}
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
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
      if (paymentChecking.value) return
      if (!isLoggedIn.value) {
        try { if (window._openLoginModal) window._openLoginModal() } catch(_) {}
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
      currentPackage = pkg
      currentOrderId.value = null
      paymentPayUrl.value = ''
      paymentQrUrl.value = ''
      paymentState.value = 'creating'
      paymentStateLabel.value = '创建中'
      paymentStatusText.value = '正在创建账单，请稍候。'
      var modal = document.getElementById('rechargeModal')
      if (!modal) return
      var nameEl = document.getElementById('rechargePkgName')
      if (nameEl) nameEl.textContent = pkg.name + '：' + pkg.points + ' 积分'
      if (nameEl && pkg.package_type === 'ai') {
        var count = pkg.ai_single_credits || pkg.ai_combo_credits || 0
        nameEl.textContent = pkg.name + '：' + count + (pkg.ai_combo_credits ? ' 次合参' : ' 次单术数')
      }
      var amtEl = document.getElementById('rechargeAmount')
      if (amtEl) amtEl.textContent = '需支付 ¥' + pkg.price
      modal.dataset.pkgId = pkg.id
      startHupijiaoPayment()
    }

    function closeRechargeModal() {
      var modal = document.getElementById('rechargeModal')
      if (modal) modal.classList.remove('open')
      paymentChecking.value = false
      try { uni.hideLoading() } catch(_) {}
      stopPaymentPolling()
    }

    function openPaymentUrl(url) {
      if (!url) return
      try {
        if (typeof window !== 'undefined') {
          window.open(url, '_blank', 'noopener,noreferrer')
          return
        }
      } catch(_) {}
      try { uni.navigateTo({ url: url }) } catch(_) {}
    }

    function stopPaymentPolling() {
      if (paymentPollTimer) {
        clearInterval(paymentPollTimer)
        paymentPollTimer = null
      }
    }

    function refreshPaymentStatus(silent) {
      if (!currentOrderId.value) {
        loadPoints()
        loadLogs()
        return
      }
      uni.request({
        url: '/api/recharge/orders?page=1&per_page=20',
        method: 'GET',
        success: function(res) {
          var list = (res.data && res.data.orders) || []
          var matched = list.find(function(o) { return String(o.id) === String(currentOrderId.value) })
          if (matched && matched.status === 'paid') {
            stopPaymentPolling()
            paymentState.value = 'paid'
            paymentStateLabel.value = '支付成功'
            paymentStatusText.value = '支付已到账，积分中心正在刷新。'
            uni.showToast({ title: '支付已到账', icon: 'success' })
            loadPoints()
            loadLogs()
            setTimeout(closeRechargeModal, 1200)
            return
          }
          if (matched && matched.status && matched.status !== 'pending') {
            stopPaymentPolling()
            paymentState.value = 'failed'
            paymentStateLabel.value = '支付失败'
            paymentStatusText.value = '这笔账单未完成，请关闭后重新选择套餐。'
            return
          }
          paymentState.value = 'pending'
          paymentStateLabel.value = '等待支付'
          paymentStatusText.value = '请扫码完成支付，系统正在自动核对到账状态。'
          loadLogs()
        },
        fail: function() {
          if (!silent) uni.showToast({ title: '刷新失败', icon: 'none' })
        }
      })
    }

    function startPaymentPolling() {
      stopPaymentPolling()
      paymentPollCount = 0
      paymentPollTimer = setInterval(function() {
        paymentPollCount += 1
        if (paymentPollCount > 60) {
          stopPaymentPolling()
          paymentState.value = 'failed'
          paymentStateLabel.value = '未到账'
          paymentStatusText.value = '长时间未核对到账，请关闭后在账本确认，或重新选择套餐。'
          return
        }
        refreshPaymentStatus(true)
      }, 3000)
    }

    function openRechargeModalWithQr(qrUrl, orderId) {
      if (!qrUrl) {
        try { uni.hideLoading() } catch(_) {}
        uni.showToast({ title: '二维码生成失败，请重试', icon: 'none' })
        return
      }
      pendingQrOrderId = orderId
      var img = new Image()
      img.onload = function() {
        if (String(pendingQrOrderId) !== String(orderId) || String(currentOrderId.value) !== String(orderId)) return
        paymentQrUrl.value = qrUrl
        var modal = document.getElementById('rechargeModal')
        if (modal) modal.classList.add('open')
        try { uni.hideLoading() } catch(_) {}
        startPaymentPolling()
      }
      img.onerror = function() {
        if (String(pendingQrOrderId) !== String(orderId)) return
        try { uni.hideLoading() } catch(_) {}
        uni.showToast({ title: '二维码加载失败，请重试', icon: 'none' })
      }
      img.src = qrUrl
    }

    function startHupijiaoPayment() {
      if (paymentChecking.value) return
      if (paymentPayUrl.value) {
        openPaymentUrl(paymentPayUrl.value)
        return
      }
      if (!isLoggedIn.value) {
        try { if (window._openLoginModal) window._openLoginModal() } catch(_) {}
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
      if (!currentPackage) {
        uni.showToast({ title: '请选择充值套餐', icon: 'none' })
        return
      }
      var modal = document.getElementById('rechargeModal')
      var pkgId = modal ? modal.dataset.pkgId : ''
      if (!pkgId) {
        uni.showToast({ title: '请选择充值套餐', icon: 'none' })
        return
      }
      paymentChecking.value = true
      try { uni.showLoading({ title: '创建账单中', mask: false }) } catch(_) {}
      uni.request({
        url: '/api/recharge/create-order',
        method: 'POST',
        data: { package_id: pkgId, pay_method: 'hupijiao' },
        success: function(res) {
          var d = res.data || {}
          if (!d.ok || !d.order_id) {
            paymentState.value = 'failed'
            paymentStateLabel.value = '创建失败'
            paymentStatusText.value = d.error || '账单创建失败，请关闭后重试。'
            try { uni.hideLoading() } catch(_) {}
            uni.showToast({ title: d.error || '创建订单失败', icon: 'none' })
            return
          }
          currentOrderId.value = d.order_id
          paymentPayUrl.value = d.pay_url || ''
          paymentQrUrl.value = ''
          paymentState.value = 'pending'
          paymentStateLabel.value = '等待支付'
          paymentStatusText.value = '请扫码完成支付，支付成功后会自动回到积分中心并刷新账本。'
          openRechargeModalWithQr(d.qrcode_url || '', d.order_id)
        },
        fail: function() {
          paymentState.value = 'failed'
          paymentStateLabel.value = '创建失败'
          paymentStatusText.value = '账单创建失败，请关闭后重试。'
          try { uni.hideLoading() } catch(_) {}
          uni.showToast({ title: '创建订单失败', icon: 'none' })
        },
        complete: function() {
          paymentChecking.value = false
        }
      })
    }

    onMounted(function() {
      splitPackages(packages.value)
      loadPackages()
      if (isLoggedIn.value) {
        loadPoints()
        loadLogs()
        startLedgerRefresh()
      } else {
        resetPointsSessionState()
      }
      try { window.addEventListener('xc-auth-changed', handleAuthChanged) } catch(_) {}
      try { window.addEventListener('xc-session-expired', resetPointsSessionState) } catch(_) {}
    })

    onBeforeUnmount(function() {
      try { window.removeEventListener('xc-auth-changed', handleAuthChanged) } catch(_) {}
      try { window.removeEventListener('xc-session-expired', resetPointsSessionState) } catch(_) {}
      stopPaymentPolling()
      stopLedgerRefresh()
    })

    return {
      theme,
      isLoggedIn,
      toggleTheme,
      packages,
      pointPackages,
      aiPackages,
      paymentPayUrl,
      paymentQrUrl,
      paymentState,
      paymentStateLabel,
      paymentStatusText,
      paymentChecking,
      goBack,
      doSignin,
      loadMoreLogs,
      selectPackage,
      closeRechargeModal,
      startHupijiaoPayment,
      refreshPaymentStatus,
    }
  }
}
</script>

<style>
.page-root { min-height: 100vh; background: var(--bg); }
.page.points-page {
  width: min(1080px, calc(100vw - 32px));
  max-width: 1080px;
  margin: 0 auto;
  padding: 18px 0 56px;
}

@media (min-width: 769px) {
  .topnav { padding-left: 16px; padding-right: 16px; }
  .nav-btn { padding-left: 8px; padding-right: 8px; font-size: 0.9rem; }
  .topnav-sidebar-btn { margin-right: 0; }
}

.points-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  margin: 8px 0 18px;
}
.eyebrow {
  margin-bottom: 6px;
  font-size: 0.72rem;
  color: var(--text-3);
  letter-spacing: 0.12em;
}
.page-title {
  display: block;
  font-size: clamp(1.45rem, 3vw, 2.1rem);
  font-weight: 800;
  color: var(--text-1);
  font-family: var(--font-serif);
  letter-spacing: 0;
}
.back-btn {
  font-size: 0.86rem;
  color: var(--accent);
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 10px;
}
.back-btn:hover { background: var(--accent-glow); }

.points-layout {
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}
.account-panel {
  position: sticky;
  top: 86px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.points-page .account-card,
.points-page .account-guide,
.points-page .section {
  background: color-mix(in srgb, var(--card-bg) 94%, #f6eddb 6%);
  border: 1px solid rgba(178,149,93,0.22);
  box-shadow: 0 16px 42px rgba(80, 62, 34, 0.08);
  box-sizing: border-box;
}
.account-card {
  position: relative;
  overflow: hidden;
  border-radius: 18px;
  padding: 22px;
}
.account-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(135deg, rgba(178,149,93,0.18), transparent 44%),
    repeating-linear-gradient(0deg, transparent 0, transparent 33px, rgba(178,149,93,0.06) 34px);
  pointer-events: none;
}
.account-card-head,
.account-actions {
  position: relative;
  z-index: 1;
}
.account-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}
.account-label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-3);
  font-size: 0.78rem;
}
.points-balance {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.points-number {
  font-size: clamp(2.4rem, 6vw, 3.6rem);
  line-height: 0.95;
  font-weight: 850;
  color: var(--text-1);
  letter-spacing: 0;
}
.points-unit {
  color: var(--accent);
  font-size: 0.92rem;
  font-weight: 700;
}
.points-level {
  min-height: 22px;
  padding: 5px 9px;
  border-radius: 999px;
  background: rgba(178,149,93,0.13);
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
}
.account-divider {
  position: relative;
  z-index: 1;
  height: 1px;
  margin: 22px 0 16px;
  background: linear-gradient(90deg, rgba(178,149,93,0), rgba(178,149,93,0.38), rgba(178,149,93,0));
}
.account-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.signin-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  border-radius: 12px;
  border: 1px solid var(--accent);
  background: var(--accent);
  color: #fff;
  font-size: 0.9rem;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.18s, box-shadow 0.18s, opacity 0.18s;
}
.signin-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(135,101,42,0.2);
}
.signin-btn.signed {
  opacity: 0.62;
  cursor: default;
  background: rgba(178,149,93,0.2);
  color: var(--accent);
}
.signin-btn.signed:hover {
  transform: none;
  box-shadow: none;
}
.signin-reward {
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(255,255,255,0.22);
  font-size: 0.74rem;
}
.account-note {
  color: var(--text-3);
  font-size: 0.75rem;
  line-height: 1.5;
  text-align: center;
}
.account-guide {
  border-radius: 16px;
  padding: 14px 16px;
}
.guide-item {
  display: grid;
  grid-template-columns: 46px 1fr;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(178,149,93,0.14);
}
.guide-item:last-child { border-bottom: 0; }
.guide-k {
  color: var(--accent);
  font-size: 0.76rem;
  font-weight: 800;
}
.guide-v {
  color: var(--text-2);
  font-size: 0.78rem;
  line-height: 1.45;
}

.commerce-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.points-page .section {
  width: auto;
  max-width: none;
  margin: 0;
  border-radius: 18px;
  padding: 18px;
}
.points-page .section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
}
.points-page .section-title {
  font-size: 1rem;
  font-weight: 800;
  color: var(--text-1);
}
.points-page .section-subtitle {
  margin-top: 4px;
  color: var(--text-3);
  font-size: 0.76rem;
}
.points-page .pkg-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}
.points-page .ai-pkg-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.points-page .pkg-card {
  position: relative;
  width: auto;
  min-height: 132px;
  padding: 15px 13px;
  box-sizing: border-box;
  border: 1px solid rgba(178,149,93,0.18);
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.45), transparent),
    color-mix(in srgb, var(--card-bg) 92%, #fff5dd 8%);
  cursor: pointer;
  transition: transform 0.16s, box-shadow 0.16s, border-color 0.16s;
}
.points-page .pkg-card:hover {
  transform: translateY(-2px);
  border-color: rgba(178,149,93,0.52);
  box-shadow: 0 12px 26px rgba(80,62,34,0.12);
}
.points-page .pkg-card.recommended {
  border-color: var(--accent);
  background:
    linear-gradient(135deg, rgba(178,149,93,0.18), rgba(178,149,93,0.03) 42%),
    var(--card-bg);
}
.pkg-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 3px 7px;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
  font-size: 0.64rem;
  font-weight: 800;
}
.pkg-name {
  display: block;
  min-height: 22px;
  padding-right: 36px;
  color: var(--text-2);
  font-size: 0.78rem;
  font-weight: 800;
}
.pkg-points-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-top: 16px;
}
.pkg-points {
  color: var(--text-1);
  font-size: 1.55rem;
  line-height: 1;
  font-weight: 850;
}
.pkg-label {
  color: var(--text-3);
  font-size: 0.68rem;
  line-height: 1.25;
}
.pkg-price {
  margin-top: 14px;
  color: var(--accent);
  font-size: 1rem;
  font-weight: 850;
}
.pkg-desc {
  margin-top: 8px;
  color: var(--text-3);
  font-size: 0.68rem;
  line-height: 1.4;
}

.ledger-head {
  align-items: center;
}
.dp-tabs {
  display: inline-flex;
  gap: 4px;
  padding: 3px;
  border: 1px solid rgba(178,149,93,0.18);
  border-radius: 999px;
  background: rgba(178,149,93,0.06);
}
.dp-tab {
  min-width: 44px;
  padding: 7px 10px;
  border-radius: 999px;
  color: var(--text-3);
  font-size: 0.74rem;
  text-align: center;
  cursor: pointer;
}
.dp-tab.active {
  background: var(--card-bg);
  color: var(--accent);
  font-weight: 800;
  box-shadow: 0 4px 10px rgba(80,62,34,0.08);
}
.log-empty {
  padding: 38px 0;
  color: var(--text-3);
  font-size: 0.85rem;
  text-align: center;
  border: 1px dashed rgba(178,149,93,0.22);
  border-radius: 14px;
  background: rgba(178,149,93,0.04);
}
.dp-list {
  border: 1px solid rgba(178,149,93,0.14);
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255,255,255,0.18);
}
.dp-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  min-height: 54px;
  padding: 11px 14px;
  border-bottom: 1px solid rgba(178,149,93,0.12);
}
.dp-item:last-child { border-bottom: 0; }
.dp-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.dp-desc {
  color: var(--text-1);
  font-size: 0.82rem;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dp-date {
  color: var(--text-3);
  font-size: 0.7rem;
}
.dp-points {
  font-size: 0.96rem;
  font-weight: 850;
  white-space: nowrap;
}
.dp-plus { color: #2f8f67; }
.dp-minus { color: #b15c4f; }
.dp-pager {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 12px;
}
.dp-page-btn,
.dp-page-num {
  min-width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(178,149,93,0.2);
  border-radius: 9px;
  color: var(--text-2);
  font-size: 0.78rem;
  cursor: pointer;
}
.dp-page-cur {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  font-weight: 800;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(28,22,14,.55);
  backdrop-filter: blur(5px);
}
.modal-overlay.open { display: flex; }
.modal-box {
  position: relative;
  width: min(430px, 100%);
  max-height: calc(100dvh - 32px);
  padding: 20px;
  border: 1px solid rgba(178,149,93,0.22);
  border-radius: 20px;
  background:
    radial-gradient(circle at 18% 0%, rgba(178,149,93,0.14), transparent 38%),
    linear-gradient(180deg, color-mix(in srgb, var(--card-bg) 98%, #fff4d8 2%), var(--card-bg));
  box-shadow: 0 26px 70px rgba(26,20,12,.28);
  overflow: auto;
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.modal-title {
  color: var(--text-1);
  font-size: 1.08rem;
  font-weight: 850;
}
.modal-subtitle {
  margin-top: 4px;
  color: var(--text-3);
  font-size: 0.72rem;
}
.modal-close {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(178,149,93,0.2);
  border-radius: 999px;
  color: var(--text-3);
  font-size: 1.2rem;
  line-height: 1;
  cursor: pointer;
  background: rgba(178,149,93,0.06);
}
.modal-close:hover {
  color: var(--accent);
  border-color: rgba(178,149,93,0.42);
}
.recharge-summary {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: end;
  gap: 14px;
  padding: 14px 15px;
  margin-bottom: 16px;
  border: 1px solid rgba(178,149,93,0.18);
  border-radius: 16px;
  background:
    linear-gradient(135deg, rgba(178,149,93,0.12), rgba(178,149,93,0.03)),
    rgba(178,149,93,0.05);
}
.recharge-pkg-name {
  color: var(--text-2);
  font-size: 0.86rem;
  font-weight: 700;
}
.recharge-amount {
  color: var(--accent);
  font-size: 1.2rem;
  font-weight: 850;
  white-space: nowrap;
}
.hupijiao-panel {
  display: flex;
  justify-content: center;
  align-items: center;
}
.qr-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.hupijiao-qr {
  display: block;
  width: min(252px, 100%);
  aspect-ratio: 1;
  max-height: 252px;
  border: 1px solid rgba(178,149,93,0.2);
  border-radius: 18px;
  background: #fff;
}
.hupijiao-qr {
  object-fit: contain;
  padding: 8px;
  box-sizing: border-box;
  box-shadow: 0 12px 30px rgba(80,62,34,0.12);
}
.payment-state {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 4px 9px;
  margin-bottom: 8px;
  border-radius: 999px;
  color: var(--text-1);
  font-size: 0.76rem;
  font-weight: 850;
  background: rgba(178,149,93,0.12);
}
.state-paid { color: #2f8f67; background: rgba(47,143,103,0.12); }
.state-failed { color: #b15c4f; background: rgba(177,92,79,0.12); }
.state-pending,
.state-creating { color: var(--accent); background: rgba(178,149,93,0.14); }
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 0.84rem;
  cursor: pointer;
  text-align: center;
  box-sizing: border-box;
}
.btn-outline {
  background: transparent;
  border: 1px solid rgba(178,149,93,0.26);
  color: var(--text-2);
}
.btn-primary {
  border: 1px solid var(--accent);
  background: var(--accent);
  color: #fff;
  font-weight: 850;
}
.btn.disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 920px) {
  .points-layout {
    grid-template-columns: 1fr;
  }
  .account-panel {
    position: static;
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(220px, 0.8fr);
  }
  .pkg-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .points-page {
    width: min(100vw - 24px, 520px);
    padding-top: 12px;
  }
  .points-hero {
    margin-bottom: 14px;
  }
  .account-panel {
    display: flex;
  }
  .account-card {
    padding: 18px;
  }
  .account-card-head {
    flex-direction: column;
    align-items: flex-start;
  }
  .points-level {
    align-self: flex-start;
  }
  .points-page .section {
    padding: 14px;
    border-radius: 16px;
  }
  .points-page .section-head,
  .points-page .ledger-head {
    flex-direction: column;
    align-items: stretch;
  }
  .points-page .pkg-grid,
  .points-page .ai-pkg-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .points-page .pkg-card {
    min-height: 124px;
    padding: 13px 11px;
  }
  .points-page .pkg-name {
    padding-right: 34px;
  }
  .hupijiao-panel {
    grid-template-columns: 1fr;
  }
  .hupijiao-qr {
    width: min(100%, 220px);
    margin: 0 auto;
  }
  .recharge-summary,
  .modal-btns {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }
  .recharge-amount {
    justify-self: start;
  }
  .modal-btns {
    display: flex;
  }
}

@media (max-width: 390px) {
  .points-page .pkg-grid,
  .points-page .ai-pkg-grid {
    grid-template-columns: 1fr;
  }
}
</style>
