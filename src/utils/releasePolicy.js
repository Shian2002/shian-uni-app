const restrictedRechargeChannels = new Set([
  'appstore',
  'app-store',
  'ios',
  'testflight',
  'google-play',
  'googleplay',
])

export function getReleaseChannel() {
  let channel = ''
  try {
    channel = import.meta.env.VITE_RELEASE_CHANNEL || import.meta.env.VITE_APP_RELEASE_CHANNEL || ''
  } catch (_) {}
  try {
    if (!channel && typeof window !== 'undefined') channel = window.__SHIAN_RELEASE_CHANNEL || ''
  } catch (_) {}
  return String(channel || '').trim().toLowerCase()
}

export function isExternalRechargeEnabled() {
  return !restrictedRechargeChannels.has(getReleaseChannel())
}

export function getPaymentBoundaryNotice() {
  return '当前审核渠道暂不展示第三方数字内容充值入口；积分消耗、签到、历史记录和账号功能仍可正常验证。'
}
