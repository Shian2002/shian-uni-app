<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <main class="legal-wrap">
      <section class="legal-hero">
        <view class="section-tag">合规说明</view>
        <h1 class="legal-title">{{ currentDoc.title }}</h1>
        <p class="legal-subtitle">{{ currentDoc.subtitle }}</p>
        <p class="legal-updated">生效日期：2026-06-15 · 版本：v1.0.0</p>
        <view class="legal-tabs">
          <button class="legal-tab" :class="{ active: docType === 'privacy' }" @tap="switchDoc('privacy')">隐私政策</button>
          <button class="legal-tab" :class="{ active: docType === 'terms' }" @tap="switchDoc('terms')">用户协议</button>
        </view>
      </section>

      <section class="legal-content">
        <article v-if="docType === 'privacy'">
          <h2>一、我们处理哪些信息</h2>
          <p>为了提供账号登录、命盘档案、排盘解读、积分记录、历史报告和客服处理能力，应用会在用户主动使用相关功能时处理必要信息。</p>
          <ul>
            <li>账号信息：用户名、手机号、邮箱、第三方登录标识、登录状态。</li>
            <li>命盘信息：出生日期、时间、地点、性别、命盘档案名称。</li>
            <li>内容信息：用户输入的问题、AI 解读记录、排盘历史、收藏或报告保存记录。</li>
            <li>交易信息：积分、订单、充值记录、售后核验所需的必要流水。</li>
            <li>设备与日志：用于登录安全、异常排查、性能分析的最小化技术日志。</li>
          </ul>

          <h2>二、使用目的</h2>
          <p>上述信息仅用于提供传统文化排盘、问事引导、AI 综合解读、历史记录、账号安全、积分核算、客服售后和合规审计。不用于医疗、法律、金融、征信或自动化重大决策。</p>

          <h2>三、权限与第三方服务</h2>
          <p>应用不会在首次启动时提前申请通讯录、定位、相册、麦克风等敏感权限。只有用户主动使用相关能力时才触发权限，并说明用途。登录、短信、邮件、支付、AI 生成等能力可能由第三方服务提供，实际清单以上架包和商店后台披露为准。</p>

          <h2>四、账号注销与数据删除</h2>
          <p>用户可以在个人中心进入“账号注销 -> 注销账号与删除数据”。注销前需要输入“注销账号”，有密码账号还需要验证当前密码。注销后会清理命盘、历史、对话、收藏、社区内容等个人数据，并匿名化账号身份字段。订单、充值和必要审计记录会按合规要求保留。</p>

          <h2>五、用户权利</h2>
          <p>用户可以查看、更正、删除命盘档案和历史记录，也可以申请账号注销、数据删除或客服核验。审核账号、证书、密钥和后台截图不会写入公开仓库。</p>

          <h2>六、联系我们</h2>
          <p>如需处理隐私、账号、订单或内容问题，请通过应用内客服入口或发行材料中登记的客服邮箱联系，并提供账号、时间、页面和截图便于核验。</p>
        </article>

        <article v-else>
          <h2>一、服务定位</h2>
          <p>时安解忧屋提供传统文化工具、八字/奇门/紫微等排盘、问事引导、AI 综合解读、历史记录和报告保存。所有内容仅供娱乐、参考和自我记录，不构成医疗、法律、金融、心理咨询、投资、人事或婚恋等专业建议。</p>

          <h2>二、账号使用</h2>
          <p>用户应妥善保管账号和验证码，不得冒用他人身份、批量注册、攻击服务、绕过积分规则或利用平台内容从事违法违规、诈骗、恐吓、诱导交易、封建迷信牟利等行为。</p>

          <h2>三、内容边界</h2>
          <p>排盘、择吉、日历、案例、AI 解读和报告均基于传统文化模型、算法规则和 AI 生成。结果可能存在不完整、不准确或不适用于个体情况的情形，用户应结合现实证据和专业人士意见独立判断。</p>

          <h2>四、积分与付费</h2>
          <p>积分用于部分 AI 解读、报告生成或高级功能消耗。不同商店渠道会遵守对应平台支付政策。App Store / Google Play 审核包在未接入平台官方支付前，会隐藏不合规的第三方数字内容充值入口。</p>

          <h2>五、知识产权</h2>
          <p>应用页面设计、交互、排盘展示、原创文案、解读模板、报告结构和相关素材受法律保护。未经许可，不得批量抓取、复制、镜像、反向工程或用于商业再分发。</p>

          <h2>六、账号注销</h2>
          <p>用户可以在个人中心发起注销。注销会清理命盘、历史、对话和个人资料；订单、充值和必要审计记录会按法律法规、财务和争议处理需要保留。</p>
        </article>
      </section>
    </main>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'

const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
const docType = ref('privacy')

const docs = {
  privacy: {
    title: '隐私政策',
    subtitle: '说明时安解忧屋如何处理账号、命盘、问题、积分、订单和日志信息。',
  },
  terms: {
    title: '用户协议',
    subtitle: '说明服务定位、内容边界、账号使用、积分付费和知识产权规则。',
  },
}

const currentDoc = computed(() => docs[docType.value] || docs.privacy)

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  uni.setStorageSync('xc_theme', theme.value)
}

function switchDoc(type) {
  docType.value = docs[type] ? type : 'privacy'
  // #ifdef H5
  try {
    const url = new URL(window.location.href)
    url.hash = `/pages/legal/index?type=${docType.value}`
    window.history.replaceState(null, '', url.toString())
  } catch (_) {}
  // #endif
}

onLoad((query) => {
  if (query?.type === 'terms') docType.value = 'terms'
  else docType.value = 'privacy'
})
</script>

<style scoped>
.page-root {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-1);
}

.legal-wrap {
  width: min(920px, calc(100% - 32px));
  margin: 0 auto;
  padding: 104px 0 64px;
}

.legal-hero {
  padding-bottom: 24px;
  border-bottom: 1px solid var(--card-border);
}

.section-tag {
  display: inline-block;
  color: var(--accent);
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 12px;
}

.legal-title {
  margin: 0;
  font-size: 34px;
  line-height: 1.2;
  letter-spacing: 0;
}

.legal-subtitle,
.legal-updated {
  margin: 12px 0 0;
  color: var(--text-2);
  line-height: 1.7;
}

.legal-tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 20px;
}

.legal-tab {
  min-height: 38px;
  padding: 0 16px;
  border-radius: 8px;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  color: var(--text-1);
  font-size: 14px;
}

.legal-tab.active {
  border-color: var(--accent);
  color: var(--accent);
}

.legal-content {
  padding-top: 28px;
}

.legal-content article {
  display: grid;
  gap: 16px;
}

.legal-content h2 {
  margin: 16px 0 0;
  font-size: 20px;
  letter-spacing: 0;
}

.legal-content p,
.legal-content li {
  color: var(--text-2);
  line-height: 1.85;
  font-size: 15px;
}

.legal-content p {
  margin: 0;
}

.legal-content ul {
  margin: 0;
  padding-left: 22px;
}

@media (max-width: 640px) {
  .legal-wrap {
    width: min(100% - 24px, 920px);
    padding-top: 88px;
  }

  .legal-title {
    font-size: 28px;
  }

  .legal-tab {
    flex: 1 1 130px;
  }
}
</style>
