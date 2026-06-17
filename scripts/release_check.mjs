import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'

const root = process.cwd()
const issues = []
const warnings = []

function readJson(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) {
    issues.push(`缺少文件: ${path}`)
    return null
  }
  try {
    return JSON.parse(readFileSync(fullPath, 'utf8'))
  } catch (error) {
    issues.push(`${path} 不是合法 JSON: ${error.message}`)
    return null
  }
}

function requireFile(path) {
  if (!existsSync(join(root, path))) {
    issues.push(`缺少文件: ${path}`)
  }
}

function requireText(path, snippets) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) {
    issues.push(`缺少文件: ${path}`)
    return
  }
  const text = readFileSync(fullPath, 'utf8')
  for (const snippet of snippets) {
    if (!text.includes(snippet)) {
      issues.push(`${path} 缺少关键内容: ${snippet}`)
    }
  }
}

function checkTrackedSecrets() {
  let tracked = ''
  try {
    tracked = execFileSync('git', ['ls-files'], { cwd: root, encoding: 'utf8' })
  } catch (error) {
    warnings.push(`无法读取 git 跟踪文件列表: ${error.message}`)
    return
  }

  const forbidden = [
    /\.keystore$/i,
    /\.jks$/i,
    /\.p12$/i,
    /\.mobileprovision$/i,
    /\.pem$/i,
    /\.key$/i,
    /\.env$/i,
    /tianji\.db(?:-wal|-shm)?$/i
  ]

  for (const file of tracked.split('\n').filter(Boolean)) {
    if (forbidden.some((pattern) => pattern.test(file))) {
      issues.push(`敏感或本地发行文件不应被 Git 跟踪: ${file}`)
    }
  }
}

function checkReleaseConfig(path, requiredKeys) {
  const data = readJson(path)
  if (!data) return
  for (const key of requiredKeys) {
    if (data[key] === undefined || data[key] === '') {
      issues.push(`${path} 缺少必填字段: ${key}`)
    }
  }
}

const manifest = readJson('src/manifest.json')
if (manifest) {
  if (!manifest.appid) {
    issues.push('src/manifest.json appid 不能为空；请配置 DCloud AppID 或占位发行 ID')
  }
  if (!manifest['app-plus']) {
    issues.push('src/manifest.json 缺少 app-plus 发行配置')
  }
  if (manifest.h5?.router?.mode !== 'hash') {
    issues.push(`src/manifest.json h5.router.mode 应为 hash，实际: ${manifest.h5?.router?.mode}`)
  }
}

const packageJson = readJson('package.json')
if (packageJson) {
  for (const script of ['lint', 'typecheck', 'test', 'build:h5', 'build:h5:appstore', 'build:h5:google-play', 'build:app', 'deploy:h5', 'rollback:h5', 'mobile:preflight', 'mobile:build-env', 'mobile:toolchain-plan', 'mobile:build-requests', 'mobile:api-evidence', 'mobile:app-resource-packet', 'mobile:hbuilderx-resources', 'mobile:hbuilderx-cloud-pack', 'mobile:hbuilderx-harmony-pack', 'mobile:ios-local-build-attempt', 'qa:staging', 'qa:online', 'qa:login:local-online', 'qa:agent:entry', 'qa:agent:entry-online-login', 'qa:audit-account', 'qa:audit-account:seed', 'release:check', 'release:readiness', 'release:user-actions', 'release:try-now', 'platform:backend-matrix', 'release:final-package-plan', 'release:final-preflight', 'release:package-completeness', 'release:package-cleanup-plan', 'artifacts:prune', 'artifacts:prune:apply', 'release:current-index', 'release:current-downloads', 'release:progress', 'release:quota-status', 'release:low-impact-status', 'release:all-platform-status', 'release:external-handoff', 'release:manifest', 'release:intake', 'release:artifact-metadata', 'release:payment-boundary', 'release:channel-builds', 'release:app-icons', 'release:package', 'release:summary', 'release:finalize', 'release:finalize:plan', 'product:launch-audit', 'real-user:packet', 'real-user:roster', 'real-user:dispatch', 'real-user:check', 'store:screenshots', 'store:materials', 'store:legal-urls', 'store:privacy', 'store:submission-status', 'store:evidence-status', 'store:account-access', 'store:app-record', 'domain:https', 'h5:legal-deploy-status', 'store:packet', 'platform:handoff', 'qa:user:all', 'desktop:pack', 'desktop:build:mac:arm64', 'desktop:build:win:x64', 'desktop:build:win:x64:safe', 'desktop:build:win:arm64', 'desktop:smoke', 'desktop:online-login-smoke', 'desktop:signing-preflight', 'desktop:release-status', 'desktop:bundle', 'desktop:release-inbox-sync', 'desktop:verify-macos', 'desktop:install-macos-local', 'desktop:macos-lifecycle', 'desktop:macos-user-packet', 'desktop:windows-user-packet', 'android:shell:debug-apk', 'android:device-smoke']) {
    if (!packageJson.scripts?.[script]) {
      issues.push(`package.json 缺少脚本: ${script}`)
    }
  }
}

requireText('.gitignore', ['*.keystore', '*.p12', '*.mobileprovision', 'desktop/release/'])
requireText('.github/workflows/ci.yml', ['npm run release:user-actions', 'npm run release:payment-boundary', 'npm run store:materials', 'npm run store:submission-status', 'npm run store:evidence-status', 'npm run store:account-access', 'npm run domain:https', 'npm run desktop:release-status', 'npm run desktop:bundle', 'npm run desktop:verify-macos', 'npm run desktop:macos-user-packet', 'npm run desktop:windows-user-packet', 'npm run release:app-icons', 'npm run release:channel-builds', 'npm run mobile:api-evidence', 'npm run mobile:app-resource-packet', 'npm run release:artifact-metadata', 'npm run real-user:roster', 'MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight'])
requireText('docs/release/README.md', ['Shian2002/shian-uni-app', 'Shian2002/shian-uni-app-staging', 'GitHub Releases', 'release:readiness', 'release:user-actions', 'release:try-now', 'platform:backend-matrix', 'release:final-package-plan', 'release:final-preflight', 'artifacts:prune', 'release:current-index', 'release:current-downloads', 'release:progress', 'release:quota-status', 'release:low-impact-status', 'release:all-platform-status', 'release:external-handoff', 'user-action-handoff.md', 'release:intake', 'release:artifact-metadata', 'mobile:build-env', 'mobile:toolchain-plan', 'mobile:build-requests', 'mobile:api-evidence', 'mobile:app-resource-packet', 'mobile:hbuilderx-resources', 'mobile:hbuilderx-cloud-pack', 'mobile:hbuilderx-harmony-pack', 'mobile:ios-local-build-attempt', 'release:channel-builds', 'release:app-icons', 'release:finalize', 'release:finalize:plan', 'product:launch-audit', 'real-user:roster', 'store:screenshots', 'store:materials', 'store:legal-urls', 'store:submission-status', 'store:evidence-status', 'store:account-access', 'domain:https', 'h5:legal-deploy-status', 'desktop:release-status', 'desktop:bundle', 'desktop:release-inbox-sync', 'desktop:verify-macos', 'desktop:install-macos-local', 'desktop:macos-lifecycle', 'desktop:macos-user-packet', 'desktop:windows-user-packet', 'missingHardBlocks'])
requireText('docs/release/store-checklists.md', ['Apple App Store', 'Google Play', '鸿蒙', '国内安卓市场', 'store:screenshots', 'store:materials', 'store:submission-status'])
requireText('docs/release/github-maintenance.md', ['platform:android', 'platform:ios', 'store:yingyongbao', 'release:payment-boundary', 'release:channel-builds', 'release:user-actions', 'userRequired/approvalRequired', 'missingHardBlocks'])
requireText('docs/release/current-gap-plan.md', ['线上登录', 'qa:login:local-online', '真实用户测试', '时安agent', 'release:readiness', 'release:user-actions', '人工事项清零状态', 'product:launch-audit'])
requireText('docs/release/user-action-handoff.md', ['release:user-actions', '需要你确认后我才能做', '最后必须你做', 'CONFIRM_H5_DEPLOY=shianjieyouwu.com', '不在 GitHub 保存', 'userRequired', 'approvalRequired'])
requireText('docs/release/app-store-privacy-notes.md', ['账号注销', 'POST /api/account/delete', 'Apple IAP', 'VITE_RELEASE_CHANNEL=appstore', 'VITE_RELEASE_CHANNEL=google-play', '审核账号', 'configs/release/legal-urls.json'])
requireText('docs/release/product-gtm-benchmark.md', ['Tianfu Agent', '积分', '营销链路'])
requireText('docs/release/product-strategy-skill-report.md', ['product-strategy', 'monetization-strategy', 'marketing-ideas', '产品策略画布', '正式报告 SKU', '审核账号资产不足', '真实用户测试未回收'])
requireText('docs/release/product-content-acceptance.md', ['内容板块矩阵', 'GTM 实验矩阵', '截图验收清单', '时安agent', '正式报告 SKU'])
requireText('docs/release/platform-acceptance-matrix.md', ['真实登录接口', '时安 agent', 'POST /api/account/delete', 'GitHub Releases', 'release:readiness', 'store:screenshots'])
requireText('docs/release/store-screenshot-storyboard.md', ['store:screenshots', '时安agent', '账号注销', '问事 -> 登录/注册 -> Agent 工作台'])
requireText('docs/release/screenshot-visual-review.md', ['artifacts/store-screenshots/', '登录弹窗遮挡', '人工判断', '真机重拍'])
requireText('docs/release/login-agent-entry-evidence.md', ['时安agent', '登录/注册', '#/?app=1', 'Tianfu', 'qa:login:local-online'])
requireText('docs/release/desktop-build-evidence.md', ['macOS arm64', 'DMG', 'b9475eeef1a98bdaf918c4517d53fecba9f97fd2ccae5fed5c64a43f7df40dc8', 'Apple Developer ID', 'Windows', 'desktop:build:win:x64:safe', 'desktop:bundle', 'desktop:verify-macos', 'desktop:macos-user-packet', 'desktop:windows-user-packet'])
requireText('docs/release/mobile-build-evidence.md', ['Android', 'iOS', '鸿蒙', 'build:app', 'mobile:preflight', 'mobile:build-env', 'mobile:build-requests', 'mobile:api-evidence', 'mobile:hbuilderx-resources', 'mobile:hbuilderx-cloud-pack', 'mobile:hbuilderx-harmony-pack', 'mobile:ios-local-build-attempt', 'release:app-icons', 'src/static/app-icons/app-icon-1024.png'])
requireText('docs/release/platform-build-handoff.md', ['platform:handoff', 'android.md', 'ios.md', 'harmony.md', 'windows.md', '证书'])
requireText('docs/release/artifact-intake.md', ['release:intake', 'artifacts/release-inbox', 'checksums.sha256', 'Android APK/AAB', 'Windows EXE/MSI'])
requireText('docs/release/real-user-acceptance.md', ['real-user:packet', 'real-user:dispatch', 'real-user:check', 'artifacts/real-user-packets', 'result.example.json', 'results/tester-1.json', '至少需要 2 个测试人', '占位内容', '测试包只是材料模板'])
requireText('docs/release/legal-url-verification.md', ['store:legal-urls', 'LEGAL_URL_CHECK_ONLINE', 'configs/release/legal-urls.json', 'status', 'ready'])
requireText('docs/release/h5-legal-page-deploy-handoff.md', ['h5:legal-deploy-status', 'pages-legal-index', 'https://shianjieyouwu.com/', 'LEGAL_URL_CHECK_ONLINE=1'])
requireText('deploy-h5-to-server.sh', ['CONFIRM_H5_DEPLOY=shianjieyouwu.com', 'DRY_RUN=1', 'npm run h5:legal-deploy-status -- --strict', 'LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict'])
requireText('rollback-h5-on-server.sh', ['CONFIRM_H5_ROLLBACK=shianjieyouwu.com', 'ROLLBACK_ARCHIVE', 'h5-deploy-*.tar.gz', 'scripts/production_monitor.sh'])
requireText('docs/release/privacy-disclosure.md', ['store:privacy', 'App Privacy', 'Data safety', 'privacy-disclosures.json', 'humanReviewStatus'])
requireText('configs/release/privacy-disclosures.json', ['appleAppPrivacy', 'googlePlayDataSafety', 'dataDeletionAvailable', 'humanReviewStatus'])
requireText('configs/release/store-submissions.json', ['yingyongbao', 'google-play', 'appstore', 'harmony', 'github-desktop', 'not-submitted'])
requireText('configs/release/desktop-release-status.json', ['macos', 'windows', 'codeSigningStatus', 'notarizationStatus', 'installEvidencePaths'])
requireText('configs/release/store-evidence-requirements.json', ['yingyongbao', 'google-play', 'appstore', 'harmony', 'github-desktop', 'store-evidence-inbox'])
requireText('configs/release/artifact-metadata-requirements.json', ['android', 'ios', 'harmony', 'macos', 'windows', 'build-metadata.json'])
requireText('configs/release/real-user-roster.json', ['h5', 'android', 'ios', 'harmony', 'macos', 'windows', 'minimumTestersPerPlatform'])
requireText('configs/release/store-account-access.json', ['dcloud', 'apple-developer', 'google-play', 'huawei-appgallery', 'github-releases'])
requireText('configs/release/app-record.json', ['android-cn', 'harmony-cn', 'notRequiredReason', 'packageOrBundleId'])
requireText('configs/release/domain-https.json', ['h5-production', 'api-production', 'dnsStatus', 'httpsStatus', 'tlsCertificateStatus'])
requireText('src/pages/profile/index.vue', ['注销账号与删除数据', '输入：注销账号', '/api/account/delete'])
requireText('src/utils/releasePolicy.js', ['appstore', 'google-play', 'isExternalRechargeEnabled'])
requireText('src/pages/points/index.vue', ['externalRechargeEnabled', '当前审核渠道暂不开放充值', 'paymentBoundaryNotice'])
requireText('src/package-user/points/index.vue', ['externalRechargeEnabled', '当前审核渠道暂不开放充值', 'paymentBoundaryNotice'])
requireText('src/pages/legal/index.vue', ['隐私政策', '用户协议', '账号注销', '不构成医疗、法律、金融'])
requireText('backend/auth_routes.py', ["@app.route('/api/account/delete'", '注销账号', 'check_password_hash'])
requireFile('docs/release/review-log.md')
requireFile('docs/release/real-user-acceptance.md')
requireFile('.github/ISSUE_TEMPLATE/platform-bug.yml')
requireFile('.github/ISSUE_TEMPLATE/store-review.yml')
requireFile('.github/pull_request_template.md')
requireFile('.github/release-template.md')
requireFile('.github/labels.yml')
requireFile('desktop/package.json')
requireFile('desktop/package-lock.json')
requireFile('desktop/main.js')
requireFile('desktop/preload.js')
requireFile('desktop/README.md')
requireFile('scripts/release_candidate_summary.mjs')
requireFile('scripts/product_launch_audit.mjs')
requireFile('scripts/real_user_packet.mjs')
requireFile('scripts/real_user_roster_check.mjs')
requireFile('scripts/real_user_dispatch.mjs')
requireFile('scripts/real_user_acceptance_check.mjs')
requireFile('scripts/release_readiness_audit.mjs')
requireFile('scripts/release_user_action_handoff.mjs')
requireFile('scripts/platform_backend_matrix.mjs')
requireFile('scripts/final_package_refresh_plan.mjs')
requireFile('scripts/final_package_execution_preflight.mjs')
requireFile('scripts/final_package_completeness_check.mjs')
requireFile('scripts/package_binary_cleanup_plan.mjs')
requireFile('scripts/release_finalize.mjs')
requireFile('scripts/release_artifact_intake.mjs')
requireFile('scripts/release_artifact_metadata_check.mjs')
requireFile('scripts/mobile_build_env_check.mjs')
requireFile('scripts/mobile_toolchain_prepare_plan.mjs')
requireFile('scripts/mobile_build_request_packet.mjs')
requireFile('scripts/mobile_app_resource_packet.mjs')
requireFile('scripts/mobile_api_evidence_check.mjs')
requireFile('scripts/ios_local_build_attempt.mjs')
requireFile('scripts/payment_boundary_check.mjs')
requireFile('scripts/release_channel_builds.mjs')
requireFile('scripts/store_materials_check.mjs')
requireFile('scripts/legal_url_check.mjs')
requireFile('scripts/privacy_disclosure_check.mjs')
requireFile('scripts/store_submission_status_check.mjs')
requireFile('scripts/store_evidence_status_check.mjs')
requireFile('scripts/store_account_access_check.mjs')
requireFile('scripts/domain_https_check.mjs')
requireFile('scripts/desktop_release_status_check.mjs')
requireFile('scripts/app_icon_asset_check.mjs')
requireFile('scripts/desktop_macos_install_verify.mjs')
requireFile('scripts/desktop_macos_user_packet.mjs')
requireFile('scripts/desktop_windows_user_packet.mjs')
requireFile('scripts/store_screenshot_capture.mjs')
requireFile('scripts/dev_h5_online_login.mjs')
requireFile('scripts/local_online_login_smoke.mjs')
requireFile('scripts/agent_entry_acceptance.mjs')
requireFile('scripts/audit_account_preflight.mjs')
requireFile('scripts/seed_audit_account_assets.py')
requireFile('scripts/platform_build_handoff.mjs')
requireFile('src/utils/releasePolicy.js')
requireFile('docs/legal/privacy-policy.md')
requireFile('docs/legal/user-agreement.md')
requireFile('configs/release/app-icons.json')
requireFile('src/static/app-icons/app-icon-1024.png')

checkReleaseConfig('configs/release/android-channels.json', ['appName', 'packageName', 'versionName', 'versionCode', 'channels'])
checkReleaseConfig('configs/release/ios-appstore.json', ['appName', 'bundleId', 'versionName', 'buildNumber', 'paymentPolicy'])
checkReleaseConfig('configs/release/harmony-appgallery.json', ['appName', 'bundleName', 'versionName', 'versionCode'])
checkReleaseConfig('configs/release/desktop.json', ['appName', 'appId', 'versionName', 'platforms'])
checkReleaseConfig('configs/release/desktop-release-status.json', ['appName', 'versionName', 'status', 'platforms'])
checkReleaseConfig('configs/release/app-icons.json', ['appName', 'versionName', 'status', 'sourceLogo', 'storeIcon', 'requiredIcons'])
checkReleaseConfig('configs/release/pricing-template.json', ['appName', 'currency', 'plans', 'usageEstimate'])
checkReleaseConfig('configs/release/legal-urls.json', ['appName', 'privacyPolicyUrl', 'userAgreementUrl', 'requiresHttpsDomainBeforeStoreSubmit'])
checkReleaseConfig('configs/release/privacy-disclosures.json', ['appName', 'status', 'humanReviewStatus', 'appleAppPrivacy', 'googlePlayDataSafety'])
checkReleaseConfig('configs/release/store-evidence-requirements.json', ['appName', 'versionName', 'status', 'inboxRoot', 'stores'])
checkReleaseConfig('configs/release/artifact-metadata-requirements.json', ['appName', 'versionName', 'status', 'metadataRoot', 'platforms'])
checkReleaseConfig('configs/release/real-user-roster.json', ['appName', 'versionName', 'status', 'minimumTestersPerPlatform', 'platforms'])
checkReleaseConfig('configs/release/store-account-access.json', ['appName', 'versionName', 'status', 'accounts'])
checkReleaseConfig('configs/release/domain-https.json', ['appName', 'versionName', 'status', 'domains'])
checkTrackedSecrets()

for (const warning of warnings) {
  console.warn(`警告: ${warning}`)
}

if (issues.length > 0) {
  console.error('发行检查失败:')
  for (const issue of issues) {
    console.error(`- ${issue}`)
  }
  process.exit(1)
}

console.log('发行检查通过')
