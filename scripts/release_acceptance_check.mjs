import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

const root = process.cwd()
const issues = []

function requireText(path, snippets) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) {
    issues.push(`缺少文件: ${path}`)
    return
  }
  const text = readFileSync(fullPath, 'utf8')
  for (const snippet of snippets) {
    if (!text.includes(snippet)) {
      issues.push(`${path} 缺少验收关键内容: ${snippet}`)
    }
  }
}

requireText('docs/release/platform-acceptance-matrix.md', [
  '真实登录接口',
  '时安 agent',
  '旧登录弹窗',
  '积分会员页',
  'Android',
  'iOS',
  '鸿蒙',
  'macOS',
  'Windows',
  'Tianfu Agent',
  '报告资产',
  'GitHub Releases',
  'release:readiness',
  'release:user-actions',
  'userRequired',
  'approvalRequired',
  'store:screenshots'
])

requireText('docs/release/product-gtm-benchmark.md', [
  'Tianfu Agent',
  '工作台',
  '免费额度',
  '积分包',
  '正式报告 SKU',
  '营销链路',
  '内容板块优化'
])

requireText('docs/release/store-screenshot-storyboard.md', [
  '首页主入口',
  '旧登录弹窗',
  '时安 agent 工作台',
  '积分会员与消耗说明',
  '个人中心与账号注销',
  'store:screenshots'
])

requireText('docs/release/current-gap-plan.md', [
  '线上登录',
  'qa:login:local-online',
  'mobile:build-requests',
  'POST /api/account/delete',
  'Android APK/AAB',
  'iOS TestFlight',
  '鸿蒙包',
  'macOS/Windows',
  '真实用户测试',
  'release:readiness'
])

requireText('docs/release/real-user-acceptance.md', [
  '截图位置',
  'real-user:packet',
  'real-user:check',
  'Android',
  'iOS',
  '鸿蒙',
  'macOS',
  'Windows',
  '账号注销'
])

requireText('docs/release/login-agent-entry-evidence.md', [
  '时安agent',
  '登录/注册',
  '#/?app=1',
  'qa:login:local-online',
  'Start Chat'
])

requireText('src/pages/profile/index.vue', [
  '注销账号与删除数据',
  '输入：注销账号',
  '/api/account/delete',
  'xc-auth-changed'
])

requireText('backend/auth_routes.py', [
  "@app.route('/api/account/delete'",
  '注销账号',
  'check_password_hash'
])

requireText('scripts/real_user_packet.mjs', [
  'Android',
  'iOS',
  '鸿蒙',
  'macOS',
  'Windows',
  'screenshots',
  'result.json'
])

requireText('scripts/real_user_dispatch.mjs', [
  'REAL_USER_DISPATCH_STRICT',
  'artifacts/real-user-dispatch',
  'ready-to-dispatch',
  '真实用户发测分发索引',
  'storeMaterials',
  'privacyDisclosure',
  'legalUrlCheck'
])

requireText('scripts/real_user_acceptance_check.mjs', [
  'REAL_USER_ACCEPTANCE_STRICT',
  '01-home.png',
  '08-delete-account.png',
  'canSubmitToStore',
  'artifacts/real-user-results'
])

requireText('scripts/release_readiness_audit.mjs', [
  'RELEASE_READINESS_STRICT',
  'release-readiness',
  'login-smoke',
  'Android APK/AAB',
  'iOS TestFlight',
  '鸿蒙',
  'Windows'
])

requireText('scripts/mobile_build_request_packet.mjs', [
  'artifacts',
  'mobile-build-requests',
  '线上登录 smoke',
  'Android APK/AAB',
  'iOS TestFlight',
  '鸿蒙/AppGallery',
  'artifacts/release-inbox'
])

requireText('scripts/local_online_login_smoke.mjs', [
  '/api/login',
  '/api/me',
  '线上登录未返回 session cookie',
  'artifacts'
])

requireText('scripts/store_screenshot_capture.mjs', [
  'STORE_SCREENSHOT_BASE_URL',
  '01-home',
  '02-login-modal',
  '03-agent-workbench',
  '06-profile-delete',
  '输入：注销账号',
  'summary.json'
])

requireText('scripts/store_materials_check.mjs', [
  'STORE_MATERIALS_STRICT',
  'configs/release/legal-urls.json',
  'artifacts/legal-url-checks',
  'Data safety',
  'App Privacy',
  '账号注销',
  '线上同款登录',
  'artifacts',
  'store-materials'
])

requireText('scripts/legal_url_check.mjs', [
  'LEGAL_URL_CHECK_ONLINE',
  'LEGAL_URL_CHECK_STRICT',
  'configs/release/legal-urls.json',
  'privacyPolicyUrl',
  'userAgreementUrl',
  'artifacts',
  'legal-url-checks'
])

requireText('scripts/privacy_disclosure_check.mjs', [
  'PRIVACY_DISCLOSURE_STRICT',
  'configs/release/privacy-disclosures.json',
  'appleAppPrivacy',
  'googlePlayDataSafety',
  'dataDeletionAvailable',
  'artifacts',
  'privacy-disclosures'
])

requireText('configs/release/privacy-disclosures.json', [
  'App Privacy',
  'Data safety',
  'dataDeletionAvailable',
  'humanReviewStatus',
  'thirdPartySharing'
])

requireText('src/pages/legal/index.vue', [
  '隐私政策',
  '用户协议',
  '账号注销',
  '不构成医疗、法律、金融',
  '积分与付费'
])

requireText('configs/release/legal-urls.json', [
  'privacyPolicyUrl',
  'userAgreementUrl',
  'requiresHttpsDomainBeforeStoreSubmit'
])

requireText('docs/release/desktop-build-evidence.md', [
  '时安解忧屋-1.0.0-arm64.app.zip',
  '41139db26d5ff5fd92f0269fce5c8a77cb795eaae7b239c80f84d95cd2f45a23',
  '未签名',
  'desktop-agent-app.png',
  'GitHub Releases',
  'Windows'
])

requireText('docs/release/mobile-build-evidence.md', [
  'dist/build/app',
  'Android',
  'iOS',
  '鸿蒙',
  'APK',
  'TestFlight',
  '真实用户测试'
])

requireText('scripts/user_acceptance_full.mjs', [
  '/api/login',
  '/api/register',
  'Gitee 验证登录',
  '时安agent',
  '积分会员-消耗说明',
  '去问时安 agent'
])

if (issues.length > 0) {
  console.error('发行验收矩阵检查失败:')
  for (const issue of issues) {
    console.error(`- ${issue}`)
  }
  process.exit(1)
}

console.log('发行验收矩阵检查通过')
