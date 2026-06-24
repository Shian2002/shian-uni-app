<template>
  <view class="page-root" :class="{ 'marketing-active': marketingMode, 'marketing-android-active': marketingAndroid }" :data-theme="theme">
    <view v-if="marketingMode" class="marketing-landing">
      <view class="marketing-auth-host">
        <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />
      </view>
      <view class="marketing-nav">
        <view class="marketing-brand">
          <view class="marketing-logo-wrap">
            <img class="marketing-logo" src="/static/images/logo.webp?v=3" alt="时安解忧屋" />
          </view>
          <text>时安解忧屋</text>
        </view>
        <view class="marketing-nav-links">
          <text class="marketing-nav-link marketing-agent-link" data-enter-app="1" @tap="enterMarketingApp" @click="enterMarketingApp">时安agent</text>
          <button class="marketing-enter" data-enter-app="1" @tap="enterMarketingApp" @click="enterMarketingApp">{{ isLoggedIn ? '进入应用' : '登录/注册' }}</button>
        </view>
      </view>

      <view
        id="marketingHero"
        class="marketing-hero"
        :class="{ 'is-visible': isMarketingSectionVisible('hero') }"
      >
        <view class="marketing-ambient" aria-hidden="true">
          <view class="marketing-mist marketing-mist-a"></view>
          <view class="marketing-mist marketing-mist-b"></view>
          <view class="marketing-mist marketing-mist-c"></view>
          <view class="marketing-orbits">
            <view class="marketing-orbit"></view>
            <view class="marketing-orbit"></view>
            <view class="marketing-orbit"></view>
            <view class="marketing-orbit"></view>
          </view>
          <view class="marketing-particle marketing-particle-1"></view>
          <view class="marketing-particle marketing-particle-2"></view>
          <view class="marketing-particle marketing-particle-3"></view>
          <view class="marketing-particle marketing-particle-4"></view>
          <view class="marketing-particle marketing-particle-5"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-6"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-7"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-8"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-9"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-10"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-11"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-12"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-13"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-14"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-15"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-16"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-17"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-18"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-19"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-20"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-21"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-22"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-23"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-24"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-25"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-26"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-27"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-28"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-29"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-30"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-31"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-32"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-33"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-34"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-35"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-36"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-37"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-38"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-39"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-40"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-41"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-42"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-43"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-44"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-45"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-46"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-47"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-48"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-49"></view>
          <view class="marketing-particle marketing-particle-soft marketing-particle-50"></view>
          <view class="marketing-bottom-blur"></view>
        </view>

        <view class="marketing-copy">
          <view class="marketing-main">
            <text class="marketing-kicker">The Oriental Insight Agent</text>
            <view class="marketing-title">
              <text>BaZi · QiMen</text>
              <text>Multi-model</text>
              <text>All in Shian</text>
            </view>
            <view class="marketing-title-cn">
              <text>八字 · 奇门 · 多模型</text>
              <text>共同推演</text>
            </view>
          </view>
          <view class="marketing-side">
            <text class="marketing-side-title">Chart. Reason. Decide.</text>
            <text class="marketing-side-desc">把复杂命盘转成可读结论。先看局势，再看路径，最后给出可执行的时机建议。</text>
            <view class="marketing-cta-row">
              <button class="marketing-primary" data-enter-app="1" @tap="enterMarketingApp" @click="enterMarketingApp">开始解读</button>
              <button class="marketing-secondary" @tap="scrollMarketingCritical">详细了解</button>
            </view>
          </view>
        </view>
        <text class="marketing-scroll-hint">向下探索</text>
      </view>

      <view
        class="marketing-critical"
        id="marketingCritical"
        :class="{ 'is-visible': marketingCriticalVisible || isMarketingSectionVisible('critical') }"
      >
        <text class="marketing-section-label">Critical Moment</text>
        <text class="marketing-critical-title">在关键时刻，看清你真正面对的局</text>
        <view class="marketing-cards">
          <view class="marketing-card">
            <view class="marketing-card-visual marketing-card-visual-a" aria-hidden="true">
              <svg viewBox="0 0 220 104" class="marketing-mini-svg">
                <path class="marketing-path marketing-path-soft" d="M18 72 C56 32, 88 92, 128 52 S184 24, 204 44" />
                <path class="marketing-path marketing-path-main" d="M18 72 C56 32, 88 92, 128 52 S184 24, 204 44" />
                <circle class="marketing-node n1" cx="18" cy="72" r="5" />
                <circle class="marketing-node n2" cx="128" cy="52" r="6" />
                <circle class="marketing-node n3" cx="204" cy="44" r="5" />
              </svg>
            </view>
            <text class="marketing-card-kicker">趋势路径</text>
            <text class="marketing-card-title">事业抉择</text>
            <text class="marketing-card-desc">识别趋势、资源和阻力，判断是继续推进，还是换一条更稳的路径。</text>
            <text class="marketing-card-tags">趋势识别 · 资源判断 · 推进窗口</text>
          </view>
          <view class="marketing-card">
            <view class="marketing-card-visual marketing-card-visual-b" aria-hidden="true">
              <svg viewBox="0 0 220 104" class="marketing-mini-svg">
                <circle class="marketing-ring r1" cx="88" cy="52" r="34" />
                <circle class="marketing-ring r2" cx="132" cy="52" r="34" />
                <path class="marketing-path marketing-path-main" d="M58 52 C86 20, 134 20, 162 52 C134 84, 86 84, 58 52" />
                <circle class="marketing-node n2" cx="110" cy="52" r="6" />
              </svg>
            </view>
            <text class="marketing-card-kicker">能量结构</text>
            <text class="marketing-card-title">关系洞察</text>
            <text class="marketing-card-desc">不只给关系贴标签，而是拆解双方能量、沟通结构与阶段性变化。</text>
            <text class="marketing-card-tags">关系阶段 · 沟通结构 · 能量互补</text>
          </view>
          <view class="marketing-card">
            <view class="marketing-card-visual marketing-card-visual-c" aria-hidden="true">
              <svg viewBox="0 0 220 104" class="marketing-mini-svg">
                <circle class="marketing-time-ring" cx="110" cy="52" r="38" />
                <circle class="marketing-time-ring marketing-time-ring-inner" cx="110" cy="52" r="18" />
                <path class="marketing-time-marks" d="M110 12V22 M110 82V92 M70 52H80 M140 52H150 M82 24L89 31 M138 24L131 31 M82 80L89 73 M138 80L131 73" />
                <g class="marketing-time-rotor">
                  <path class="marketing-time-hand marketing-time-hand-soft" d="M110 52 L89 21" />
                  <path class="marketing-time-hand marketing-time-hand-main" d="M110 52 L131 21" />
                  <path class="marketing-time-window" d="M89 21 A38 38 0 0 1 131 21" />
                  <circle class="marketing-time-dot marketing-time-dot-soft" cx="89" cy="21" r="3.8" />
                  <circle class="marketing-time-dot" cx="131" cy="21" r="4.2" />
                </g>
              </svg>
            </view>
            <text class="marketing-card-kicker">行动时机</text>
            <text class="marketing-card-title">择时行动</text>
            <text class="marketing-card-desc">把“什么时候做”变成清晰的行动窗口，减少犹豫和反复。</text>
            <text class="marketing-card-tags">吉时判断 · 风险避让 · 执行建议</text>
          </view>
          <view class="marketing-console">
            <text class="marketing-console-title">Shian Console</text>
            <view class="marketing-console-line"></view>
            <view class="marketing-console-line"></view>
            <view class="marketing-console-line"></view>
            <view class="marketing-console-line"></view>
          </view>
        </view>
      </view>

      <!-- 第3页：产品推理 -->
      <view
        class="marketing-tools"
        id="marketingProduct"
        :class="{ 'is-visible': isMarketingSectionVisible('product') }"
      >
        <view class="marketing-product-copy">
          <text class="marketing-section-watermark">Product</text>
          <view class="marketing-product-title">
            <text class="marketing-product-title-line">像老师傅一样思考</text>
            <text class="marketing-product-title-line">像工程系统一样输出</text>
          </view>
          <text class="marketing-product-sub">多模型驱动的 AI 分析系统</text>
          <text class="marketing-product-lead">复刻老师傅级推演逻辑，结合现实处境与时间节律，根据你人生路上的每一次经历与选择，找到那个独一无二的你。多个专业模型各司其职，追求每一步推理的严谨透明。</text>
        </view>
        <view class="marketing-engine">
          <view class="marketing-engine-browser">
            <text></text>
            <text></text>
            <text></text>
          </view>
          <view class="marketing-engine-ui">
            <view class="marketing-engine-sidebar">
              <text class="marketing-engine-brand">+ Shian Agent</text>
              <text class="marketing-engine-item is-active">命盘分析</text>
              <text class="marketing-engine-item">合参结论</text>
              <text class="marketing-engine-item">追问历史</text>
            </view>
            <view class="marketing-engine-chat">
              <text class="marketing-engine-bubble">我适合什么时候行动？</text>
              <view class="marketing-engine-steps" aria-hidden="true">
                <text>读取资料</text>
                <text>排盘核对</text>
                <text>合参推理</text>
              </view>
              <view class="marketing-engine-report">
                <text class="marketing-engine-report-title">综合分析</text>
                <text class="marketing-engine-report-line"></text>
                <text class="marketing-engine-report-line"></text>
                <text class="marketing-engine-report-line short"></text>
              </view>
            </view>
            <view class="marketing-engine-chart">
              <view class="marketing-engine-chart-core"></view>
              <view class="marketing-engine-chart-grid"></view>
              <text class="marketing-engine-chart-line l1"></text>
              <text class="marketing-engine-chart-line l2"></text>
              <text class="marketing-engine-chart-line l3"></text>
            </view>
          </view>
        </view>
      </view>

      <!-- 第4页：术数体系 -->
      <view
        class="marketing-core"
        id="marketingSystems"
        :class="{ 'is-visible': isMarketingSectionVisible('systems') }"
      >
        <view class="marketing-system-head">
          <text class="marketing-critical-title">三大术数体系，验证每一步推演</text>
          <text class="marketing-section-sub">八字 · 奇门 · 紫微，多模型合参，覆盖核心推演环节。</text>
          <view class="marketing-product-stats">
            <view class="marketing-stat">
              <text class="marketing-stat-number">3</text>
              <text class="marketing-stat-label">主推演体系</text>
            </view>
            <view class="marketing-stat">
              <text class="marketing-stat-number">6+</text>
              <text class="marketing-stat-label">辅助模型</text>
            </view>
          </view>
        </view>
        <view class="marketing-system-body">
          <view class="marketing-system-item marketing-system-item-bazi">
            <view class="marketing-system-visual">
              <img class="marketing-system-svg" src="/static/images/marketing-five-elements.svg?v=4" alt="八字五行旋转图" />
            </view>
            <view class="marketing-system-copy">
              <text class="marketing-system-title">八字命理 <text>Bazi</text></text>
              <text class="marketing-system-desc">以出生时刻的干支结构为基础，观察格局、喜忌、大运与流年，判断长期趋势与阶段变化。</text>
            </view>
          </view>
          <view class="marketing-system-item marketing-system-item-ziwei">
            <view class="marketing-system-visual">
              <img class="marketing-system-svg" src="/static/images/marketing-ziwei-layers.svg?v=4" alt="河图洛书旋转图" />
            </view>
            <view class="marketing-system-copy">
              <text class="marketing-system-title">紫微斗数 <text>Ziwei</text></text>
              <text class="marketing-system-desc">用宫位、星曜与四化串联人生主题，补足关系、事业、财帛与关键阶段的细节刻画。</text>
            </view>
          </view>
          <view class="marketing-system-item marketing-system-item-qimen">
            <view class="marketing-system-visual">
              <svg class="marketing-system-svg" viewBox="0 0 220 220" aria-hidden="true">
                <g class="marketing-spin-slow">
                  <circle cx="110" cy="110" r="92" fill="none" stroke="#747169" stroke-width="1.2" stroke-dasharray="3 7"/>
                  <g stroke="#5f5c55" stroke-width="4.2" stroke-linecap="round">
                    <g transform="rotate(0 110 110) translate(110 36)">
                      <path d="M-12 -9H12 M-12 0H12 M-12 9H12"/>
                    </g>
                    <g transform="rotate(45 110 110) translate(110 36)">
                      <path d="M-12 -9H-4 M4 -9H12 M-12 0H12 M-12 9H12"/>
                    </g>
                    <g transform="rotate(90 110 110) translate(110 36)">
                      <path d="M-12 -9H12 M-12 0H-4 M4 0H12 M-12 9H12"/>
                    </g>
                    <g transform="rotate(135 110 110) translate(110 36)">
                      <path d="M-12 -9H-4 M4 -9H12 M-12 0H-4 M4 0H12 M-12 9H12"/>
                    </g>
                    <g transform="rotate(180 110 110) translate(110 36)">
                      <path d="M-12 -9H12 M-12 0H12 M-12 9H-4 M4 9H12"/>
                    </g>
                    <g transform="rotate(225 110 110) translate(110 36)">
                      <path d="M-12 -9H-4 M4 -9H12 M-12 0H12 M-12 9H-4 M4 9H12"/>
                    </g>
                    <g transform="rotate(270 110 110) translate(110 36)">
                      <path d="M-12 -9H-4 M4 -9H12 M-12 0H-4 M4 0H12 M-12 9H12"/>
                    </g>
                    <g transform="rotate(315 110 110) translate(110 36)">
                      <path d="M-12 -9H-4 M4 -9H12 M-12 0H-4 M4 0H12 M-12 9H-4 M4 9H12"/>
                    </g>
                  </g>
                </g>
                <g class="marketing-spin-reverse">
                  <circle cx="110" cy="110" r="17.5" fill="#918d82" stroke="#5f5c55" stroke-width="1"/>
                  <path d="M110 92.5a17.5 17.5 0 0 1 0 35c8.2-4.2 8.2-13.2 0-17.5s-8.2-13.2 0-17.5z" fill="#f8f3e7"/>
                  <circle cx="103.5" cy="110" r="3.6" fill="#f8f3e7"/>
                  <circle cx="117" cy="110" r="3.6" fill="#918d82"/>
                </g>
              </svg>
            </view>
            <view class="marketing-system-copy">
              <text class="marketing-system-title">奇门遁甲 <text>Qimen</text></text>
              <text class="marketing-system-desc">把时间、方位、门星神与局势放进同一个盘面，适合分析时机、行动路径和外部阻力。</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 第5页：底部CTA+Footer -->
      <view
        class="marketing-final"
        id="marketingFinal"
        :class="{ 'is-visible': isMarketingSectionVisible('final') }"
      >
        <view class="marketing-faq">
          <text class="marketing-section-watermark">Q&A</text>
          <text class="marketing-final-title">常见问题</text>
          <text class="marketing-final-desc">关于时安解忧屋的使用方式、推演逻辑与数据安全</text>
          <view class="marketing-faq-list">
            <view
              v-for="(item, index) in marketingFaqs"
              :key="item.question"
              class="marketing-faq-row"
              :class="{ 'is-open': marketingActiveFaq === index }"
              @tap="toggleMarketingFaq(index)"
            >
              <view class="marketing-faq-question">
                <text>{{ item.question }}</text>
                <text class="marketing-faq-icon">⌄</text>
              </view>
              <text class="marketing-faq-answer">{{ item.answer }}</text>
            </view>
          </view>
        </view>
        <view class="marketing-final-content">
          <text class="marketing-final-title">准备好探索你的命盘了吗？</text>
          <text class="marketing-final-desc">开始一次真正有深度的命理对话</text>
          <button class="marketing-primary" data-enter-app="1" @tap="enterMarketingApp" @click="enterMarketingApp">进入应用</button>
        </view>
        <view class="marketing-footer">
          <text class="marketing-footer-text">© 2026 时安解忧屋 · 保留所有权利</text>
          <text class="marketing-footer-icp" @tap="openMiitBeian">粤ICP备2026072162号-1</text>
        </view>
      </view>
    </view>

    <view v-else class="tool-home-shell">
    <!-- 视频背景层（H5 only） -->
    <!-- #ifdef H5 -->
    <view v-if="videoEnabled" class="video-bg" :class="{ 'video-fallback': videoFallback, 'video-visible': videoVisible }" id="videoBg">
      <video
        class="video-bg-video"
        id="heroVideo"
        autoplay
        muted
        loop
        playsinline
        @error="onVideoError"
        @loadeddata="onVideoReady"
      >
        <source src="https://assets.mixkit.co/videos/preview/mixkit-abstract-technology-white-lines-2826-large.mp4" type="video/mp4" />
      </video>
      <view class="video-bg-overlay"></view>
    </view>
    <!-- #endif -->
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn"
      @toggle-theme="toggleTheme" ref="topNavRef" />

    <view class="page-wrap">

      <!-- ═══ 首屏 Hero ═══ -->
      <section class="hero-home" :class="{ 'chat-active': comprehensiveMessages.length, 'reading-active': comprehensiveLoading }">
        <view class="hero-home-content">
          <!-- LOGO 和品牌 -->
            <view class="hero-brand">
              <view class="hero-brand-icon-wrap"><img class="hero-brand-icon" src="/static/images/logo.webp?v=3" alt="时安解忧屋" /></view>
              <view class="hero-brand-name">时安解忧屋</view>
              <view class="hero-brand-divider"></view>
            <view class="hero-brand-slogan">一念起，便可问</view>
            <view class="hero-brand-sub">心有所感，自有其路。我会先帮你理清所问，再为你择法解读。</view>
            <view class="home-question-templates" v-if="showHomeQuestionTemplates">
              <view
                v-for="item in homeQuestionTemplates"
                :key="item.key"
                class="home-question-template"
                :data-template-key="item.key"
                @tap="selectHomeQuestionTemplate(item)"
                @click="selectHomeQuestionTemplate(item)"
              >
                <text class="home-question-template-label">{{ item.label }}</text>
                <text class="home-question-template-text">{{ item.short }}</text>
              </view>
            </view>
          </view>

          <view class="home-ai-console" :class="{ 'has-chat': comprehensiveMessages.length }">
            <view class="home-ai-chat" v-if="comprehensiveMessages.length" @scroll="onHomeChatScroll">
              <view class="home-ai-chat-head">
                <view class="home-ai-chat-head-main">
                  <text class="home-ai-chat-title">综合解读</text>
                  <text class="home-ai-chat-sub">{{ homeAiContextSummary }}</text>
                </view>
                <view class="home-ai-new-chat" @tap="startNewComprehensiveConversation">新对话</view>
              </view>
              <view
                v-for="(msg, idx) in comprehensiveMessages"
                :key="idx"
                class="home-ai-message"
                :class="msg.role === 'user' ? 'user' : 'assistant'"
              >
                <text class="home-ai-role" v-if="msg.role === 'user'">你</text>
                <view
                  class="home-ai-agent-head"
                  v-else-if="msg.stage || msg.content || msg.guideLoading || visibleArtifactList(msg).length"
                >
                  <img
                    class="home-ai-agent-logo"
                    :class="(msg.stage || msg.guideLoading) ? 'spinning' : 'idle'"
                    src="/static/images/logo.webp?v=3"
                    alt="时安解忧屋"
                  />
                  <view class="home-ai-agent-texts">
                    <text class="home-ai-agent-name">时安 agent</text>
                    <text class="home-ai-agent-sub">{{ msg.stage || msg.guideLoadingText || '已完成解读' }}</text>
                    <text class="home-ai-stage-note" v-if="msg.stage || msg.guideLoading">{{ msg.guideLoading ? '正在理解你的来意，并为你择法' : '正在按所选命盘和术数生成，可继续停留在当前页' }}</text>
                  </view>
                </view>
                <view class="home-ai-context-chip" v-if="msg.role === 'assistant' && msg.contextSummary">
                  <text>{{ msg.contextNotice || '当前使用' }}</text>
                  <text>{{ msg.contextSummary }}</text>
                </view>
                <view class="home-ai-step-row" v-if="msg.stage && !msg.content">
                  <text>读取资料</text>
                  <text>排盘核对</text>
                  <text>模型解读</text>
                  <text>组织回答</text>
                </view>
                <view class="home-ai-progress-track" v-if="msg.stage">
                  <view class="home-ai-progress-bar"></view>
                </view>
                <view class="home-tool-cards" v-if="visibleArtifactList(msg).length">
                  <HomeArtifactTabs
                    :artifacts="artifactTabsForMessage(msg)"
                    :active-key="activeArtifactKeyForMessage(msg, idx)"
                    :summary-active="isSummaryActive(msg, idx)"
                    :show-summary="msg.role === 'assistant' && (!!msg.content || !!msg._streaming)"
                    @select="setActiveArtifact(idx, $event)"
                  />
                  <view class="home-tool-card" v-if="currentArtifactForMessage(msg, idx) && !isSummaryActive(msg, idx)">
                    <view class="home-tool-card-head">
                      <view>
                        <text class="home-tool-card-title">{{ currentArtifactForMessage(msg, idx).title }}</text>
                        <text class="home-tool-card-sub">{{ artifactSummary(currentArtifactForMessage(msg, idx)) }}</text>
                        <text class="home-tool-card-feed" v-if="artifactFeedSummary(currentArtifactForMessage(msg, idx))">{{ artifactFeedSummary(currentArtifactForMessage(msg, idx)) }}</text>
                      </view>
                    </view>
                    <view class="home-tool-card-body">
                      <view class="home-artifact-render" v-html="renderArtifactHtml(currentArtifactForMessage(msg, idx))"></view>
                      <view class="home-artifact-analysis" v-if="currentArtifactForMessage(msg, idx).analysis">
                        <view class="home-artifact-analysis-title">{{ currentArtifactForMessage(msg, idx).title }}解析</view>
                        <text>{{ currentArtifactForMessage(msg, idx).analysis }}</text>
                      </view>
                    </view>
                  </view>
                </view>
                <text class="home-ai-content" v-if="msg.role === 'user' && msg.content">{{ msg.content }}</text>
                <view class="home-ai-summary-panel" v-if="msg.role === 'assistant' && (msg.content || msg._streaming) && (!visibleArtifactList(msg).length || isSummaryActive(msg, idx))">
                  <view class="home-artifact-analysis-title">{{ msg.isGuide ? '问事引导' : '综合结论' }}</view>
                  <view class="home-guide-thinking" v-if="msg.guideLoading">
                    <text>{{ msg.guideLoadingText || '正在理清所问' }}</text>
                    <view class="home-guide-dots">
                      <text></text>
                      <text></text>
                      <text></text>
                    </view>
                  </view>
                  <view
                    v-else
                    class="home-ai-content home-ai-stream-text"
                    :data-home-ai-stream-key="'summary-' + idx"
                  >{{ msg.content }}</view>
                  <view class="home-guide-options" v-if="msg.guideOptions && msg.guideOptions.length">
                    <view
                      v-for="option in msg.guideOptions"
                      :key="option"
                      class="home-guide-option"
                      @tap="submitQuestionGuideAnswer(option)"
                    >{{ option }}</view>
                  </view>
                  <view class="home-guide-recommend" v-if="msg.guideRecommendation">
                    <view class="home-guide-recommend-title">建议选择：{{ toolSummaryForIds(msg.guideRecommendation.tool_models) }}</view>
                    <view class="home-guide-recommend-meta" v-if="toolsNeedProfile(msg.guideRecommendation.tool_models)">需要先填写出生信息后排盘</view>
                    <view class="home-guide-loading" v-if="msg.guideApplying">
                      <view class="home-guide-spinner"></view>
                      <text>正在择法...</text>
                    </view>
                    <view
                      v-else-if="!msg.guideRecommendation.applied"
                      class="home-guide-primary"
                      @tap="applyGuideRecommendationFromMessage(msg.guideRecommendation, msg)"
                    >一键选择术数</view>
                    <view
                      v-else
                      class="home-guide-primary"
                      @tap="startGuidedRecommendationReading(msg.guideRecommendation)"
                    >{{ guideRecommendationReady(msg.guideRecommendation) ? '开始解读' : '填写出生信息' }}</view>
                  </view>
                </view>
              </view>
            </view>

            <HomeAiComposer
              v-model="comprehensiveQuestion"
              :placeholder="comprehensivePlaceholder"
              :loading="comprehensiveLoading"
              :selected-profile-name="selectedProfileName"
              :auto-select-tools="autoSelectTools"
              :selected-tool-summary="selectedToolSummary"
              :tool-models="toolModels"
              :selected-tool-models="selectedToolModels"
              :reading-mode-names="readingModeNames"
              :reading-mode-labels="readingModeLabels"
              :reading-mode-idx="readingModeIdx"
              :selected-reading-mode="selectedReadingMode"
              :llm-model-names="llmModelNames"
              :llm-model-idx="llmModelIdx"
              :selected-llm-model="selectedLlmModel"
              :estimated-cost="estimatedCost"
              :current-points="currentPoints"
              :hide-llm-picker="true"
              @open-profile="openProfilePicker"
              @tool-auto-toggle="toggleAutoSelectTools"
              @tool-model-toggle="toggleToolModel"
              @reading-mode-change="onReadingModeChange"
              @llm-model-change="onLlmModelChange"
              @send="startComprehensiveAsk"
              @keydown="onComprehensiveInputKeydown"
            />
            <view class="home-guidance-note" v-if="showGuidanceHint">
              <text>问事前会先帮你理清所问，并为你推荐适合的解读方式。</text>
              <text class="home-guidance-note-action" @tap="disableQuestionGuidance">以后直接解读</text>
            </view>
          </view>
        </view>

      </section>

    </view><!-- page-wrap -->

    <view class="profile-sheet" v-if="profileSheetOpen">
      <view class="profile-sheet-mask" @tap="cancelProfileSelection"></view>
      <view class="profile-sheet-panel">
        <view class="profile-sheet-head">
          <text class="profile-sheet-title">选择命盘</text>
          <text class="profile-sheet-close" @tap="cancelProfileSelection">×</text>
        </view>
        <view class="profile-sheet-scroll">
          <view class="profile-tabs">
            <view v-for="tab in profileTabs" :key="tab" :class="{ active: profileTab === tab }" @tap="profileTab = tab">{{ tab }}</view>
          </view>
          <view class="profile-quick-create">
            <view class="profile-quick-toggle" @tap="toggleQuickProfileForm">
              <text>{{ profileQuickFormOpen ? '收起新增命盘' : '+ 新增命盘' }}</text>
              <text class="profile-quick-hint">不知道具体时分也可以先保存</text>
            </view>
            <view class="profile-quick-form" v-if="profileQuickFormOpen">
              <view class="quick-grid">
                <label class="quick-field">
                  <text>姓名</text>
                  <input v-model="quickProfileForm.name" placeholder="请输入名称" />
                </label>
                <label class="quick-field">
                  <text>关系</text>
                  <picker :range="profileTypeQuickLabels" :value="quickProfileTypeIndex" @change="onQuickProfileTypeChange">
                    <view class="quick-picker">{{ profileTypeLabel(quickProfileForm.profileType) }}</view>
                  </picker>
                </label>
                <label class="quick-field">
                  <text>性别</text>
                  <picker :range="genderOptions" :value="quickGenderIndex" @change="onQuickGenderChange">
                    <view class="quick-picker">{{ quickProfileForm.gender }}</view>
                  </picker>
                </label>
                <label class="quick-field">
                  <text>历法</text>
                  <picker :range="calTypeOptions" :value="quickCalTypeIndex" @change="onQuickCalTypeChange">
                    <view class="quick-picker">{{ quickProfileForm.calType }}</view>
                  </picker>
                </label>
                <view class="quick-field quick-field-wide">
                  <text>出生时间</text>
                  <view class="quick-datetime-row quick-datetime-all">
                    <select v-model="quickProfileForm.birthYear" class="quick-native-select" @change="onQuickBirthPartChange('birthYear', $event)">
                      <option value="">年</option>
                      <option v-for="year in quickYearOptions" :key="'qy-' + year" :value="year">{{ year }}年</option>
                    </select>
                    <select v-model="quickProfileForm.birthMonth" class="quick-native-select" @change="onQuickBirthPartChange('birthMonth', $event)">
                      <option value="">月</option>
                      <option v-for="month in quickMonthOptions" :key="'qm-' + month" :value="month">{{ String(month).padStart(2, '0') }}月</option>
                    </select>
                    <select v-model="quickProfileForm.birthDay" class="quick-native-select" @change="onQuickBirthPartChange('birthDay', $event)">
                      <option value="">日</option>
                      <option v-for="day in quickDayOptions" :key="'qd-' + day" :value="day">{{ String(day).padStart(2, '0') }}日</option>
                    </select>
                    <select v-model="quickProfileForm.birthHour" class="quick-native-select" :disabled="quickProfileForm.timeUnknown" @change="onQuickBirthPartChange('birthHour', $event)">
                      <option value="">时</option>
                      <option v-for="hour in quickHourOptions" :key="'qh-' + hour" :value="hour">{{ String(hour).padStart(2, '0') }}时</option>
                    </select>
                    <select v-model="quickProfileForm.birthMinute" class="quick-native-select" :disabled="quickProfileForm.timeUnknown" @change="onQuickBirthPartChange('birthMinute', $event)">
                      <option value="">分</option>
                      <option v-for="minute in quickMinuteOptions" :key="'qmi-' + minute" :value="minute">{{ String(minute).padStart(2, '0') }}分</option>
                    </select>
                  </view>
                </view>
                <view class="quick-field quick-field-wide">
                  <text>出生地</text>
                  <view class="quick-addr-selects">
                    <select v-model="quickProfileForm.birthProvince" class="quick-native-select" @change="onQuickProvinceChange">
                      <option value="">省</option>
                      <option v-for="province in quickProvinceOptions" :key="'qp-' + province" :value="province">{{ province }}</option>
                    </select>
                    <select v-model="quickProfileForm.birthCity" class="quick-native-select" @change="onQuickCityChange">
                      <option value="">市</option>
                      <option v-for="city in quickCityOptions" :key="'qc-' + city" :value="city">{{ city }}</option>
                    </select>
                    <select v-model="quickProfileForm.birthDistrict" class="quick-native-select" @change="onQuickDistrictChange">
                      <option value="">区</option>
                      <option v-for="district in quickDistrictOptions" :key="'qd-' + district.name" :value="district.name">{{ district.name }}</option>
                    </select>
                  </view>
                  <view class="quick-addr-info" v-if="quickProfileForm.birthAddr">
                    <text>{{ quickProfileForm.birthAddr }}</text>
                    <text v-if="quickProfileForm.birthLng">经度 {{ quickProfileForm.birthLng }} · 纬度 {{ quickProfileForm.birthLat }}</text>
                  </view>
                </view>
              </view>
              <view class="quick-row">
                <view class="quick-check" :class="{ active: quickProfileForm.timeUnknown }" @tap="quickProfileForm.timeUnknown = !quickProfileForm.timeUnknown">
                  <text class="quick-check-dot">{{ quickProfileForm.timeUnknown ? '✓' : '' }}</text>
                  <text>不清楚具体时分</text>
                </view>
                <view class="quick-save" @tap="createQuickProfile">保存并选中</view>
              </view>
              <view class="quick-note">八字和紫微需要较准确的出生时间；信息不全时，时安agent会优先建议用奇门或先补充资料。</view>
            </view>
          </view>
          <view class="profile-options">
            <view v-if="profileGroups[profileTab].length === 0" class="profile-empty">
              <text>暂无命盘档案</text>
              <text class="profile-empty-sub">可先新增一个常用命盘，再用于八字、紫微和时安agent。</text>
            </view>
            <view
              class="profile-option"
              v-for="p in profileGroups[profileTab]"
              :key="p.id"
              :class="{ active: isProfileDraftSelected(p) }"
              @tap="toggleProfileSelection(p)"
            >
              <view>
                <text class="profile-option-name">{{ p.name || '未命名' }}</text>
                <text class="profile-option-meta">{{ p.gender }} · {{ formatBirthTime(p.birthTime || p.birth_time) }}</text>
              </view>
              <view class="profile-option-side">
                <text class="profile-option-type">{{ profileTypeLabel(p.profileType || p.profile_type) }}</text>
                <text class="profile-option-check">{{ isProfileDraftSelected(p) ? '✓' : '' }}</text>
              </view>
            </view>
          </view>
        </view>
        <view class="sheet-actions">
          <view class="sheet-btn sheet-btn-secondary" @tap="cancelProfileSelection">取消</view>
          <view class="sheet-btn sheet-btn-primary" @tap="confirmProfileSelection">确认</view>
        </view>
      </view>
    </view>

    <view class="send-confirm-sheet" v-if="sendConfirmOpen">
      <view class="send-confirm-mask" @tap="resolveSendConfirm(false)"></view>
      <view class="send-confirm-panel">
        <view class="send-confirm-title">发送前确认</view>
        <view class="send-confirm-desc">请确认本次解读使用的命盘和参数。</view>
        <view class="send-confirm-list">
          <view><text>命盘</text><text>{{ selectedProfileName || '未选择' }}</text></view>
          <view><text>术数</text><text>{{ selectedToolSummary }}</text></view>
          <view><text>Engine</text><text>SHIAN-1.1</text></view>
          <view><text>模式</text><text>{{ selectedReadingMode.name || '标准' }} · {{ estimatedCost }}积分</text></view>
        </view>
        <view class="send-confirm-check" :class="{ active: sendConfirmDontRemind }" @tap="sendConfirmDontRemind = !sendConfirmDontRemind">
          <text class="quick-check-dot">{{ sendConfirmDontRemind ? '✓' : '' }}</text>
          <text>下次不再提醒</text>
        </view>
        <view class="sheet-actions">
          <view class="sheet-btn sheet-btn-secondary" @tap="resolveSendConfirm(false)">再看看</view>
          <view class="sheet-btn sheet-btn-primary" @tap="resolveSendConfirm(true)">开始解读</view>
        </view>
      </view>
    </view>

    <view class="question-guide-sheet" v-if="questionGuideOpen">
      <view class="send-confirm-mask" @tap="closeQuestionGuide"></view>
      <view class="question-guide-panel">
        <view class="question-guide-kicker">问事引导</view>
        <view class="send-confirm-title">{{ questionGuideSkill || '先理清所问' }}</view>
        <view class="send-confirm-desc">时安会先理解你的问题，再像调用 skill 一样为你择法。</view>
        <view class="question-guide-origin">
          <text>起问</text>
          <text>{{ questionGuideDraft.question }}</text>
        </view>
        <view class="question-guide-chat">
          <view
            v-for="(message, idx) in questionGuideMessages"
            :key="'qg-' + idx"
            class="question-guide-message"
            :class="'question-guide-message-' + message.role"
          >
            <text>{{ message.content }}</text>
          </view>
          <view class="question-guide-message question-guide-message-assistant" v-if="questionGuideLoading">
            <text>正在理解你的问题...</text>
          </view>
        </view>
        <view class="question-guide-chips">
          <view
            v-for="option in questionGuideOptions"
            :key="option"
            class="question-guide-chip"
            @tap="submitQuestionGuideAnswer(option)"
          >{{ option }}</view>
        </view>
        <textarea
          class="question-guide-input"
          v-model="questionGuideInput"
          auto-height
          maxlength="180"
          placeholder="也可以直接补充一句，比如：我更想知道对方现在怎么想。"
        />
        <view class="question-guide-progress">
          <text>AI 理解后会自动择法并勾选</text>
          <text>SHIAN-1.1</text>
        </view>
        <view class="sheet-actions">
          <view class="sheet-btn sheet-btn-secondary" @tap="closeQuestionGuide">取消</view>
          <view class="sheet-btn sheet-btn-primary" @tap="submitQuestionGuideAnswer()">{{ questionGuideLoading ? '理解中...' : '发送给时安' }}</view>
        </view>
      </view>
    </view>

    <view class="question-guide-sheet" v-if="toolRecommendOpen">
      <view class="send-confirm-mask" @tap="resolveToolRecommendation(false)"></view>
      <view class="question-guide-panel">
        <view class="question-guide-kicker">已为你择定解读方式</view>
        <view class="send-confirm-title">已自动勾选 {{ selectedToolSummary }}</view>
        <view class="send-confirm-desc">{{ toolRecommendReason || '根据你的问题，建议先从最贴近当下的一种解读开始。' }}</view>
        <view class="question-guide-origin">
          <text>整理后所问</text>
          <text>{{ questionGuideDraft.finalQuestion || questionGuideDraft.question }}</text>
        </view>
        <view class="send-confirm-list">
          <view><text>解读方式</text><text>{{ selectedToolSummary }}</text></view>
          <view><text>解读深度</text><text>{{ selectedReadingMode.name || '标准' }} · {{ estimatedCost }}积分</text></view>
          <view><text>Engine</text><text>SHIAN-1.1</text></view>
        </view>
        <view class="send-confirm-check" :class="{ active: keepQuestionGuidance }" @tap="keepQuestionGuidance = !keepQuestionGuidance">
          <text class="quick-check-dot">{{ keepQuestionGuidance ? '✓' : '' }}</text>
          <text>以后继续开启问事引导</text>
        </view>
        <view class="sheet-actions">
          <view class="sheet-btn sheet-btn-secondary" @tap="resolveToolRecommendation(false)">再看看</view>
          <view class="sheet-btn sheet-btn-primary" @tap="resolveToolRecommendation(true)">开始解读</view>
        </view>
      </view>
    </view>

    </view><!-- tool-home-shell -->
  </view>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { onLoad, onShow, onHide } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'
import HomeAiComposer from './components/HomeAiComposer.vue'
import HomeArtifactTabs from './components/HomeArtifactTabs.vue'
import { createHomeAiDraftStorage } from './useHomeAiDraft.js'
import {
  HOME_AI_STREAM_DEFAULTS,
  shouldSyncStreamContent,
  smoothTextSpeed,
  takeSmoothTextChunk,
} from './useHomeAiStream.js'
import {
  htmlEscape,
  pillarText,
  readStorageJson,
  sanitizeArtifactAnalysisChunk,
  sanitizeArtifactAnalysisText,
  writeStorageJson,
} from './homeAiUtils.js'

// ── 主题 ──
function hasUserSelectedTheme() {
  try {
    const v = uni.getStorageSync('xc_theme_user_selected')
    if (v === '1' || v === true) return true
  } catch(_) {}
  // #ifdef H5
  try {
    return localStorage.getItem('xc_theme_user_selected') === '1'
  } catch(_) {}
  // #endif
  return false
}
function readInitialTheme() {
  if (!hasUserSelectedTheme()) return 'light'
  let saved = ''
  try { saved = uni.getStorageSync('xc_theme') || '' } catch(_) {}
  // #ifdef H5
  if (!saved) {
    try { saved = localStorage.getItem('xc_theme') || '' } catch(_) {}
  }
  // #endif
  return saved === 'dark' ? 'dark' : 'light'
}
const theme = ref(readInitialTheme())
const topNavRef = ref(null)
const marketingMode = ref(true)
const marketingAndroid = ref(false)
const marketingCriticalVisible = ref(false)
const marketingVisibleSections = reactive({
  hero: true,
  critical: false,
  product: false,
  systems: false,
  final: false,
})
const marketingFaqs = [
  {
    question: '如何正确看待命理分析的结果？',
    answer: '它更适合作为趋势和决策参考，不是替你决定人生。时安会把局势、变量和行动窗口拆清楚，最后选择仍然回到你自己。',
  },
  {
    question: '和免费的模板占卜有什么区别？',
    answer: '免费模板通常只按生日或关键词拼接固定文案。时安会结合命盘结构、提问场景和多术数交叉验证，尽量让结论有推理路径可追溯。',
  },
  {
    question: '不懂术语，也能看懂报告吗？',
    answer: '可以。报告会优先给出白话结论、关键原因和行动建议，专业术语只作为辅助说明，避免让你被概念本身卡住。',
  },
  {
    question: '我的出生日期等隐私安全吗？',
    answer: '命盘资料只用于排盘和解读流程。页面会尽量减少无关暴露；后续如进入应用，会按账号权限和隐私策略处理历史记录。',
  },
]
const marketingActiveFaq = ref(null)
let marketingObserver = null
let marketingScrollRestoration = ''
let marketingTopResetTimer = null
let marketingEnterLastTouch = 0

function resetMarketingVisibleSections() {
  marketingVisibleSections.hero = true
  marketingVisibleSections.critical = false
  marketingVisibleSections.product = false
  marketingVisibleSections.systems = false
  marketingVisibleSections.final = false
}

function isMarketingSectionVisible(key) {
  return !!marketingVisibleSections[key]
}

function setMarketingSectionVisible(key) {
  if (key && Object.prototype.hasOwnProperty.call(marketingVisibleSections, key)) {
    marketingVisibleSections[key] = true
  }
}

function toggleMarketingFaq(index) {
  marketingActiveFaq.value = marketingActiveFaq.value === index ? null : index
}

function shouldOpenToolHome(query) {
  if (query && (query.app === '1' || query.app === 'true')) return true
  // #ifdef H5
  try {
    const href = window.location.href || ''
    const hash = window.location.hash || ''
    const search = window.location.search || ''
    return /(?:[?&])app=(?:1|true)(?:&|$)/.test(href) ||
      /(?:[?&])app=(?:1|true)(?:&|$)/.test(hash) ||
      /(?:[?&])app=(?:1|true)(?:&|$)/.test(search)
  } catch(_) {}
  // #endif
  return false
}

function shouldForceToolRoute() {
  // #ifdef H5
  try {
    const hash = window.location.hash || ''
    return /^#\/(?:pages|package-)\//.test(hash) &&
      !/^#\/pages\/index\/index(?:\?|$)/.test(hash)
  } catch(_) {}
  // #endif
  return false
}

function refreshMarketingMode(query) {
  if (shouldForceToolRoute()) {
    marketingMode.value = false
    disconnectMarketingObserver()
    restoreMarketingScrollRestoration()
    syncMarketingPageClass()
    return
  }
  const wantsToolHome = shouldOpenToolHome(query)
  if (wantsToolHome && !isLoggedIn.value) {
    marketingMode.value = true
    // #ifdef H5
    try {
      if (window.location.hash !== '#/') window.history.replaceState({ marketing: 'home' }, '', '#/')
    } catch(_) {}
    // #endif
  } else {
    marketingMode.value = !wantsToolHome
  }
  if (marketingMode.value) {
    marketingCriticalVisible.value = false
    resetMarketingVisibleSections()
    resetMarketingScrollTop()
    nextTick(setupMarketingObserver)
  } else {
    disconnectMarketingObserver()
    restoreMarketingScrollRestoration()
  }
  syncMarketingPageClass()
}

function showMarketingHome() {
  marketingMode.value = true
  marketingCriticalVisible.value = false
  resetMarketingVisibleSections()
  syncMarketingPageClass()
  nextTick(setupMarketingObserver)
  // #ifdef H5
  try {
    if (window.location.hash !== '#/') window.history.replaceState({ marketing: 'home' }, '', '#/')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch(_) {}
  // #endif
}

function syncMarketingPageClass() {
  // #ifdef H5
  try {
    const active = !!marketingMode.value
    window.__xcHomeMode = active ? 'marketing' : 'app'
    const nav = window.navigator || {}
    const ua = nav.userAgent || ''
    const isAndroid = /Android/i.test(ua)
    const isWindows = /Windows NT/i.test(ua)
    marketingAndroid.value = active && isAndroid
    document.documentElement.classList.toggle('marketing-page', active)
    document.body.classList.toggle('marketing-page', active)
    document.documentElement.classList.toggle('marketing-android', marketingAndroid.value)
    document.body.classList.toggle('marketing-android', marketingAndroid.value)
    document.documentElement.classList.toggle('marketing-wheel-scroll', active && isWindows)
    document.body.classList.toggle('marketing-wheel-scroll', active && isWindows)
    syncMarketingDomIsolation(active)
    if (active) {
      document.documentElement.classList.remove('home-fixed-page')
      document.body.classList.remove('home-fixed-page')
    } else {
      document.documentElement.classList.add('home-fixed-page')
      document.body.classList.add('home-fixed-page')
    }
    window.dispatchEvent(new CustomEvent('xc-home-mode-changed', { detail: { mode: window.__xcHomeMode } }))
  } catch(_) {}
  // #endif
}

function resetMarketingScrollTop() {
  // #ifdef H5
  try {
    if (marketingTopResetTimer) clearTimeout(marketingTopResetTimer)
    if ('scrollRestoration' in window.history) {
      if (!marketingScrollRestoration) marketingScrollRestoration = window.history.scrollRestoration || 'auto'
      window.history.scrollRestoration = 'manual'
    }
    const reset = function() {
      try {
        const root = document.querySelector('.page-root.marketing-active')
        const landing = document.querySelector('.marketing-landing')
        const wrap = root && root.closest ? root.closest('uni-page-wrapper') : null
        if (landing) landing.scrollTop = 0
        if (root) root.scrollTop = 0
        if (wrap) wrap.scrollTop = 0
        window.scrollTo(0, 0)
      } catch(_) {}
    }
    reset()
    marketingTopResetTimer = setTimeout(reset, 120)
  } catch(_) {}
  // #endif
}

function restoreMarketingScrollRestoration() {
  // #ifdef H5
  try {
    if (marketingTopResetTimer) {
      clearTimeout(marketingTopResetTimer)
      marketingTopResetTimer = null
    }
    if (marketingScrollRestoration && 'scrollRestoration' in window.history) {
      window.history.scrollRestoration = marketingScrollRestoration
      marketingScrollRestoration = ''
    }
  } catch(_) {}
  // #endif
}

function enterMarketingApp() {
  if (!isLoggedIn.value) {
    showMarketingHome()
    openMarketingLogin()
    return
  }
  marketingMode.value = false
  syncMarketingPageClass()
  disconnectMarketingObserver()
  // #ifdef H5
  try {
    const targetHash = '#/?app=1'
    if (window.location.hash !== targetHash) window.history.pushState({ app: 'home' }, '', targetHash)
    window.scrollTo(0, 0)
  } catch(_) {}
  scheduleHomeVideoLoad()
  // #endif
}

function openMarketingLogin() {
  // #ifdef H5
  nextTick(function() {
    setTimeout(function() {
      try {
        if (window._openLoginModal) {
          window._openLoginModal()
        } else {
          uni.showToast({ title: '请先登录或注册', icon: 'none' })
        }
      } catch(_) {}
    }, 160)
  })
  // #endif
}

function onMarketingEnterNative(e) {
  // #ifdef H5
  try {
    const target = e && e.target
    const trigger = target && target.closest ? target.closest('[data-enter-app="1"]') : null
    if (!trigger || !marketingMode.value) return
    if (e.type === 'click' && Date.now() - marketingEnterLastTouch < 500) {
      e.preventDefault()
      e.stopPropagation()
      if (e.stopImmediatePropagation) e.stopImmediatePropagation()
      return
    }
    if (e.type === 'touchstart') marketingEnterLastTouch = Date.now()
    e.preventDefault()
    e.stopPropagation()
    if (e.stopImmediatePropagation) e.stopImmediatePropagation()
    enterMarketingApp()
  } catch(_) {}
  // #endif
}

function onMarketingRouteChange() {
  refreshMarketingMode()
}

function scrollMarketingCritical() {
  // #ifdef H5
  try {
    const target = document.getElementById('marketingCritical')
    if (!target) return
    const scrollEl =
      document.querySelector('.marketing-landing') ||
      document.querySelector('.page-root.marketing-active') ||
      document.querySelector('.page-root')
    if (scrollEl && scrollEl.scrollHeight > scrollEl.clientHeight) {
      scrollEl.scrollTo({ top: target.offsetTop, behavior: 'smooth' })
    } else {
      window.scrollTo({ top: target.offsetTop, behavior: 'smooth' })
    }
  } catch(_) {}
  // #endif
}

function scrollMarketingProduct() {
  // #ifdef H5
  try {
    const target = document.getElementById('marketingProduct')
    if (!target) return
    const scrollEl =
      document.querySelector('.marketing-landing') ||
      document.querySelector('.page-root.marketing-active') ||
      document.querySelector('.page-root')
    if (scrollEl && scrollEl.scrollHeight > scrollEl.clientHeight) {
      scrollEl.scrollTo({ top: target.offsetTop, behavior: 'smooth' })
    } else {
      window.scrollTo({ top: target.offsetTop, behavior: 'smooth' })
    }
  } catch(_) {}
  // #endif
}

function goMarketingTool(url) {
  marketingMode.value = false
  syncMarketingPageClass()
  disconnectMarketingObserver()
  const renderTarget = function() {
    try {
      if (window.__xcRenderTabPath) window.__xcRenderTabPath(url)
    } catch(_) {}
  }
  // #ifdef H5
  try {
    if (window.history && window.history.pushState) {
      window.history.pushState({ tool: url }, '', '#' + url)
    } else {
      window.location.hash = '#' + url
    }
  } catch(_) {}
  // #endif
  try {
    uni.switchTab({ url, success: renderTarget, fail: renderTarget })
    setTimeout(renderTarget, 80)
  } catch(_) {
    try { uni.navigateTo({ url }) } catch(_) {}
    renderTarget()
  }
}

function scrollMarketingHero() {
  // #ifdef H5
  try {
    const scrollEl =
      document.querySelector('.marketing-landing') ||
      document.querySelector('.page-root.marketing-active') ||
      document.querySelector('.page-root')
    if (scrollEl && scrollEl.scrollHeight > scrollEl.clientHeight) {
      scrollEl.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  } catch(_) {}
  // #endif
}

function disconnectMarketingObserver() {
  // #ifdef H5
  if (marketingObserver) {
    marketingObserver.disconnect()
    marketingObserver = null
  }
  // #endif
}

function syncMarketingDomIsolation(active) {
  // #ifdef H5
  try {
    const pages = document.querySelectorAll('uni-page')
    pages.forEach(function(page) {
      const isMarketingPage = !!(page.querySelector && page.querySelector('.marketing-landing'))
      if (active && !isMarketingPage) {
        page.setAttribute('aria-hidden', 'true')
        page.setAttribute('data-marketing-hidden', 'true')
        try { page.inert = true } catch(_) {}
      } else if (page.getAttribute && page.getAttribute('data-marketing-hidden') === 'true') {
        page.removeAttribute('aria-hidden')
        page.removeAttribute('data-marketing-hidden')
        try { page.inert = false } catch(_) {}
      }
    })
  } catch(_) {}
  // #endif
}

function setupMarketingObserver() {
  // #ifdef H5
  disconnectMarketingObserver()
  if (!marketingMode.value) return
  try {
    syncMarketingDomIsolation(true)
    const targets = [
      { key: 'hero', el: document.getElementById('marketingHero') },
      { key: 'critical', el: document.getElementById('marketingCritical') },
      { key: 'product', el: document.getElementById('marketingProduct') },
      { key: 'systems', el: document.getElementById('marketingSystems') },
      { key: 'final', el: document.getElementById('marketingFinal') },
    ].filter(function(item) { return !!item.el })
    if (!targets.length || typeof IntersectionObserver === 'undefined') {
      marketingCriticalVisible.value = true
      targets.forEach(function(item) { setMarketingSectionVisible(item.key) })
      return
    }
    marketingObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const key = entry.target && entry.target.getAttribute ? entry.target.getAttribute('data-marketing-section') : ''
          setMarketingSectionVisible(key)
          if (key === 'critical') marketingCriticalVisible.value = true
        }
      })
    }, {
      root: document.querySelector('.marketing-landing') || null,
      threshold: 0.24,
    })
    targets.forEach(function(item) {
      item.el.setAttribute('data-marketing-section', item.key)
      marketingObserver.observe(item.el)
    })
  } catch(_) {
    marketingCriticalVisible.value = true
    resetMarketingVisibleSections()
    marketingVisibleSections.critical = true
    marketingVisibleSections.product = true
    marketingVisibleSections.systems = true
    marketingVisibleSections.final = true
  }
  // #endif
}
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  uni.setStorageSync('xc_theme', theme.value)
  uni.setStorageSync('xc_theme_user_selected', '1')
  try {
    localStorage.setItem('xc_theme', theme.value)
    localStorage.setItem('xc_theme_user_selected', '1')
    document.documentElement.setAttribute('data-theme', theme.value); document.body.setAttribute('data-theme', theme.value); const root = document.querySelector('.page-root')
    if (root) root.setAttribute('data-theme', theme.value)
    const icon = document.getElementById('themeToggleIcon')
    if (icon) icon.textContent = theme.value === 'dark' ? '🌙' : '☀️'
  } catch(_) {}
}

// ── 视频背景（H5 only）──
const videoFallback = ref(false)
const videoVisible = ref(false)
const videoEnabled = ref(false)
let homeVideoFallbackTimer = null
let homeVideoRevealTimer = null
function setHomeFixedPage(enabled) {
  // #ifdef H5
  try {
    document.documentElement.classList.toggle('home-fixed-page', !!enabled)
    document.body.classList.toggle('home-fixed-page', !!enabled)
  } catch(_) {}
  // #endif
}
function onVideoError() {
  videoFallback.value = true
  videoVisible.value = true
}
function onVideoReady() {
  videoVisible.value = true
}

function scheduleHomeVideoLoad() {
  // 首屏视频是装饰资源，延后挂载，避免首页跳转时抢占网络和主线程。
  const enable = function() {
    videoEnabled.value = true
    homeVideoFallbackTimer = setTimeout(() => {
      const v = document.getElementById('heroVideo')
      if (v && v.readyState < 2) {
        videoFallback.value = true
        videoVisible.value = true
        v.style.display = 'none'
      }
    }, 3000)
    homeVideoRevealTimer = setTimeout(() => {
      if (!videoVisible.value) videoVisible.value = true
    }, 1000)
  }
  try {
    if (window.requestIdleCallback) window.requestIdleCallback(enable, { timeout: 1800 })
    else setTimeout(enable, 1200)
  } catch(_) {
    setTimeout(enable, 1200)
  }
}

// ── 移动端菜单 ──
const mobileMenuOpen = ref(false)
const submenuOpen = reactive({ qimen: false, bazi: false, more: false })
function openMobileMenu() { mobileMenuOpen.value = true }
function closeMobileMenu() { mobileMenuOpen.value = false }
function toggleSubmenu(key) { submenuOpen[key] = !submenuOpen[key] }

// ── 登录状态 ──
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
function resetHomeAuthState() {
  clearHomeAgentSelectionStorage()
  currentPoints.value = 0
  profiles.value = []
  selectedProfiles.value = []
  startNewComprehensiveConversation()
  clearHomeAgentSelectionStorage()
  showMarketingHome()
}
window.addEventListener('xc-session-expired', function() {
  isLoggedIn.value = false
  resetHomeAuthState()
})
window.addEventListener('xc-show-marketing-home', function() {
  showMarketingHome()
})
window.addEventListener('xc-show-agent-home', function() {
  enterMarketingApp()
})
window.addEventListener('xc-auth-changed', function(e) {
  const loggedIn = !!(e && e.detail && e.detail.loggedIn)
  isLoggedIn.value = loggedIn
  if (loggedIn) {
    loadComprehensiveOptions()
    loadProfiles()
    if (marketingMode.value) {
      nextTick(function() {
        enterMarketingApp()
      })
    }
  } else {
    resetHomeAuthState()
  }
})

// ── 首页综合 AI ──
const comprehensiveQuestion = ref('')
const comprehensiveLoading = ref(false)
const profiles = ref([])
const selectedProfiles = ref([])
const draftSelectedProfiles = ref([])
const profileSelectionConfirmed = ref(false)
const profileSheetOpen = ref(false)
const profileTab = ref('全部')
const profileTabs = ['全部', '客户', '用户']
const readingModeStorageKey = 'xc_home_reading_mode_v1'
const artifactCollapseStorageKey = 'xc_home_artifact_collapse_v1'
const comprehensiveDraftStorageKey = 'xc_home_comprehensive_draft_v1'
const selectedProfilesStorageKey = 'xc_home_selected_profiles_v1'
const selectedToolsStorageKey = 'xc_home_selected_tools_v1'
const sendConfirmSkipStorageKey = 'xc_home_send_confirm_skip_v1'
const questionGuidanceEnabledStorageKey = 'xc_home_question_guidance_enabled_v1'
const agentHandoffStorageKey = 'xc_agent_handoff_v1'
const homeQuestionTemplates = [
  { key: 'career', label: '事业', short: '跳槽时机', question: '我最近适合跳槽或换方向吗？请结合事业趋势、阻力和适合行动的时间窗口来判断。' },
  { key: 'relationship', label: '感情', short: '关系走向', question: '我和对方接下来的关系走向如何？请看双方状态、沟通阻力和是否适合继续推进。' },
  { key: 'partnership', label: '合作', short: '项目取舍', question: '这个合作或项目现在适合推进吗？请帮我看机会、风险和需要避开的关键点。' },
  { key: 'annual', label: '年运', short: '年度重点', question: '我接下来一年最需要注意什么？请从事业、财运、关系和关键月份给出重点提醒。' },
]
const profileTypeQuickLabels = ['自己', '家人', '朋友', '伴侣', '客户', '名人', '收藏', '其他']
const profileTypeQuickValues = ['self', 'family', 'friend', 'partner', 'customer', 'celebrity', 'collect', 'other']
const genderOptions = ['男', '女']
const calTypeOptions = ['公历', '农历']
const profileQuickFormOpen = ref(false)
const quickDefaultBirth = { year: 2000, month: 6, day: 15 }
const quickProfileForm = reactive({
  name: '',
  profileType: 'self',
  gender: '男',
  calType: '公历',
  birthYear: '',
  birthMonth: '',
  birthDay: '',
  birthHour: '',
  birthMinute: '',
  birthProvince: '',
  birthCity: '',
  birthDistrict: '',
  birthAddr: '',
  birthLng: 0,
  birthLat: 0,
  timeUnknown: false,
})
const quickCityData = ref([])
const sendConfirmOpen = ref(false)
const sendConfirmDontRemind = ref(false)
let pendingSendConfirmResolve = null
const questionGuidanceEnabled = ref(readStorageJson(currentUserScopedStorageKey(questionGuidanceEnabledStorageKey), true) !== false)
const questionGuideOpen = ref(false)
const toolRecommendOpen = ref(false)
const toolRecommendReason = ref('')
const keepQuestionGuidance = ref(true)
const questionGuideInput = ref('')
const questionGuideLoading = ref(false)
const questionGuideSkill = ref('')
const questionGuideOptions = ref([])
const questionGuideMessages = ref([])
const questionGuideInChat = ref(false)
const pendingGuideRecommendation = ref(null)
const questionGuideDraft = reactive({
  question: '',
  finalQuestion: '',
})
let pendingToolRecommendResolve = null
let questionGuideLoadingMessageIndex = -1
const readingModes = ref([
  { id: 'concise', name: '简约', cost_delta: -1, display_cost: 1 },
  { id: 'standard', name: '标准', cost_delta: 0, display_cost: 2 },
  { id: 'deep', name: '深度', cost_delta: 2, display_cost: 4 },
])
const llmModels = ref([{ id: 'basic', name: 'SHIAN-1.1', cost_base: 2, cost_multiplier: 0, followup_cost: 2 }])
const toolModels = ref([
  { id: 'qimen', name: '奇门遁甲', cost: 3, needs_profile: false },
  { id: 'bazi', name: '八字', cost: 2, needs_profile: true },
  { id: 'liuyao', name: '六爻', cost: 2, needs_profile: false },
  { id: 'meihua', name: '梅花易数', cost: 2, needs_profile: false },
  { id: 'ziwei', name: '紫微斗数', cost: 3, needs_profile: true },
  { id: 'tarot', name: '塔罗牌', cost: 2, needs_profile: false },
  { id: 'zeji', name: '择吉工具', cost: 2, needs_profile: false },
])
const llmModelIdx = ref(0)
const selectedToolModels = ref([])
const autoSelectTools = ref(false)
const currentPoints = ref(0)
const aiSingleCredits = ref(0)
const aiComboCredits = ref(0)
const dailyLightAvailable = ref(false)
const comprehensiveMessages = ref([])
const currentComprehensiveConvId = ref(null)
const currentPaipanContext = ref({})
const currentArtifacts = ref({})
const readingMode = ref(readStorageJson(readingModeStorageKey, 'standard'))
const shouldAutoFollowChat = ref(true)
let pendingComprehensiveId = ''
let lastComprehensiveScrollTop = 0
let comprehensiveProgressTimer = null
let comprehensiveTypeTimer = null
let comprehensiveScrollTimer = null
let comprehensiveRenderFrame = null
let comprehensiveTypeFrame = null
let comprehensivePendingAssistantUpdate = null
let comprehensiveArtifactAnalysisTimers = {}
let comprehensiveTypeStates = {}
let artifactHtmlCache = new WeakMap()
const COMPREHENSIVE_TYPE_FRAME_MS = HOME_AI_STREAM_DEFAULTS.frameMs
const COMPREHENSIVE_TYPE_MAX_FRAME_CHARS = HOME_AI_STREAM_DEFAULTS.maxFrameChars
const COMPREHENSIVE_REACTIVE_SYNC_MS = HOME_AI_STREAM_DEFAULTS.reactiveSyncMs
const COMPREHENSIVE_ARTIFACT_STREAM_OPTIONS = {
  baseCps: 76,
  maxCps: 96,
  maxFrameChars: 2,
}
const COMPREHENSIVE_HEAVY_ARTIFACT_STREAM_OPTIONS = {
  baseCps: 96,
  maxCps: 132,
  maxFrameChars: 6,
}
const COMPREHENSIVE_HEAVY_ARTIFACT_KEYS = ['bazi.basic', 'bazi.yun', 'ziwei.pan']
const HOME_AI_NEAR_BOTTOM_PX = 140
const COMPREHENSIVE_DRAFT_SAVE_MS = 320
const COMPREHENSIVE_DRAFT_MAX_AGE_MS = 24 * 60 * 60 * 1000

const selectedLlmModel = computed(() => llmModels.value[llmModelIdx.value] || llmModels.value[0] || {})
const llmModelNames = computed(() => llmModels.value.map(m => m.name || 'SHIAN-1.1'))
const selectedReadingMode = computed(() => readingModes.value.find(m => m.id === readingMode.value) || readingModes.value[1] || {})
const readingModeNames = computed(() => readingModes.value.map(m => m.name))
const readingModeLabels = computed(() => readingModes.value.map(m => {
  const cost = Number(m.display_cost || 0)
  return cost > 0 ? `${m.name}（${cost}积分）` : m.name
}))
const readingModeIdx = computed(() => Math.max(0, readingModes.value.findIndex(m => m.id === selectedReadingMode.value.id)))
const comprehensivePlaceholder = computed(() => comprehensiveMessages.value.length ? '请继续输入你想问的问题' : '此刻最牵动你的，是哪一件事？')
const showHomeQuestionTemplates = computed(() => {
  return !comprehensiveMessages.value.length && !comprehensiveLoading.value
})
const showGuidanceHint = computed(() => {
  return questionGuidanceEnabled.value && !comprehensiveMessages.value.length && !comprehensiveLoading.value
})
const homeAiContextSummary = computed(() => {
  const profileText = selectedProfileName.value || '未选择命盘'
  const toolText = selectedToolSummary.value === '选择术数' ? '未选择术数' : selectedToolSummary.value
  const costText = estimatedCost.value + '积分'
  return profileText + ' · ' + toolText + ' · SHIAN-1.1 · ' + costText
})
const estimatedCost = computed(() => {
  if (comprehensiveMessages.value.length > 0) return Math.max(0, (selectedLlmModel.value.followup_cost || 0) + modeCostDelta())
  const selected = selectedToolModels.value || []
  if (selected.length > 1 && aiComboCredits.value > 0) return 0
  if (selected.length === 1 && aiSingleCredits.value > 0) return 0
  const profileCount = Math.max(1, selectedProfiles.value.length)
  const toolsCost = selected.reduce((sum, id) => {
    const tool = toolModels.value.find(t => t.id === id)
    return sum + (tool ? Number(tool.cost || 0) : 0)
  }, 0)
  const cost = Math.round((selectedLlmModel.value.cost_base || 0) + toolsCost * profileCount * (selectedLlmModel.value.cost_multiplier || 1) + modeCostDelta())
  if (dailyLightAvailable.value && cost <= 2) return 0
  return cost
})
const selectedToolSummary = computed(() => {
  const names = toolModels.value.filter(t => selectedToolModels.value.includes(t.id)).map(t => t.name)
  if (!names.length) return '选择术数'
  if (names.length <= 2) return names.join(' + ')
  return names.slice(0, 2).join(' + ') + ' 等' + names.length + '项'
})
const selectedProfileName = computed(() => {
  const list = selectedProfiles.value || []
  if (!list.length) return ''
  if (list.length === 1) return list[0].name || '未命名'
  return (list[0].name || '未命名') + ' 等' + list.length + '盘'
})
const selectedProfileMeta = computed(() => {
  const p = selectedProfiles.value[0]
  if (!p) return ''
  return (p.gender || '') + ' · ' + formatBirthTime(p.birthTime || p.birth_time)
})

function comprehensiveContextSnapshot() {
  const profileIds = (selectedProfiles.value || []).map(function(p) {
    return String(p.id || p.birthTime || p.birth_time || p.name || '')
  })
  const toolIds = (selectedToolModels.value || []).slice()
  const modelId = selectedLlmModel.value.id || 'basic'
  const modeId = selectedReadingMode.value.id || 'standard'
  const profileText = selectedProfileName.value || '未选择命盘'
  const toolText = selectedToolSummary.value === '选择术数' ? '未选择术数' : selectedToolSummary.value
  const modelText = 'SHIAN-1.1'
  const modeText = selectedReadingMode.value.name || '标准'
  return {
    profileIds,
    toolIds,
    modelId,
    modeId,
    summary: profileText + ' · ' + toolText + ' · ' + modelText + ' · ' + modeText,
  }
}

function lastAssistantContextSnapshot() {
  for (let i = comprehensiveMessages.value.length - 1; i >= 0; i--) {
    const msg = comprehensiveMessages.value[i]
    if (msg && msg.role === 'assistant' && msg.contextSnapshot) return msg.contextSnapshot
  }
  return null
}

function sameComprehensiveContext(a, b) {
  if (!a || !b) return false
  return a.modelId === b.modelId
    && a.modeId === b.modeId
    && JSON.stringify(a.profileIds || []) === JSON.stringify(b.profileIds || [])
    && JSON.stringify(a.toolIds || []) === JSON.stringify(b.toolIds || [])
}
const quickProfileTypeIndex = computed(() => Math.max(0, profileTypeQuickValues.indexOf(quickProfileForm.profileType)))
const quickGenderIndex = computed(() => Math.max(0, genderOptions.indexOf(quickProfileForm.gender)))
const quickCalTypeIndex = computed(() => Math.max(0, calTypeOptions.indexOf(quickProfileForm.calType)))
const quickYearOptions = computed(() => {
  const current = new Date().getFullYear()
  const years = []
  for (let y = current; y >= current - 120; y--) years.push(y)
  return years
})
const quickMonthOptions = computed(() => Array.from({ length: 12 }, (_, i) => i + 1))
const quickDayOptions = computed(() => {
  const year = Number(quickProfileForm.birthYear || quickDefaultBirth.year)
  const month = Number(quickProfileForm.birthMonth || quickDefaultBirth.month)
  const maxDay = new Date(year, month, 0).getDate()
  return Array.from({ length: maxDay }, (_, i) => i + 1)
})
const quickHourOptions = computed(() => Array.from({ length: 24 }, (_, i) => i))
const quickMinuteOptions = computed(() => Array.from({ length: 60 }, (_, i) => i))
const quickProvinceOptions = computed(() => (quickCityData.value || []).map(item => item && item[0]).filter(name => name && name !== '未知地区'))
const quickSelectedProvince = computed(() => (quickCityData.value || []).find(item => item && item[0] === quickProfileForm.birthProvince))
const quickCityOptions = computed(() => {
  const province = quickSelectedProvince.value
  return province && Array.isArray(province[1]) ? province[1].map(city => city && city[0]).filter(Boolean) : []
})
const quickSelectedCity = computed(() => {
  const province = quickSelectedProvince.value
  const cities = province && Array.isArray(province[1]) ? province[1] : []
  return cities.find(city => city && city[0] === quickProfileForm.birthCity)
})
const quickDistrictOptions = computed(() => {
  const city = quickSelectedCity.value
  const districts = city && Array.isArray(city[1]) ? city[1] : []
  return districts.map(item => ({ name: item && item[0], lat: item && item[1], lng: item && item[2] })).filter(item => item.name)
})
const profileGroups = computed(() => {
  const list = profiles.value || []
  return {
    '全部': list,
    '客户': list.filter(p => (p.profileType || p.profile_type) === 'customer'),
    '用户': list.filter(p => (p.profileType || p.profile_type || 'self') !== 'customer'),
  }
})

function goToPage(url) {
  if (!url) return
  if (url.indexOf('/pages/') === 0) {
    uni.switchTab({
      url,
      fail: function() { uni.navigateTo({ url }) }
    })
  } else {
    uni.navigateTo({ url })
  }
}

function openMiitBeian() {
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
}

function profileTypeLabel(type) {
  if (type === 'self') return '自己'
  if (type === 'family') return '家人'
  if (type === 'friend') return '朋友'
  if (type === 'partner') return '伴侣'
  if (type === 'customer') return '客户'
  if (type === 'celebrity') return '名人'
  if (type === 'collect') return '收藏'
  if (type === 'other') return '其他'
  if (type === 'bazi_record') return '八字记录'
  return '用户'
}

function formatBirthTime(v) {
  const s = String(v || '')
  if (s.length >= 12) return s.slice(0,4) + '-' + s.slice(4,6) + '-' + s.slice(6,8) + ' ' + s.slice(8,10) + ':' + s.slice(10,12)
  if (s.length >= 8) return s.slice(0,4) + '-' + s.slice(4,6) + '-' + s.slice(6,8)
  return '未填写出生时间'
}

function openProfilePicker() {
  if (!isLoggedIn.value) {
    uni.showToast({ title: '请先登录后选择命盘', icon: 'none' })
    setTimeout(function() {
      try { if (window._openLoginModal) window._openLoginModal() } catch(_) {}
    }, 180)
    return
  }
  draftSelectedProfiles.value = selectedProfiles.value.slice()
  profileSheetOpen.value = true
  loadProfiles()
}

function profileKey(p) {
  return (p.source || 'profile') + ':' + String(p.recordId || p.id || '')
}

function currentUserScopedStorageKey(base) {
  let userKey = 'guest'
  try {
    const raw = uni.getStorageSync('xc_user')
    const user = typeof raw === 'string' ? JSON.parse(raw) : raw
    userKey = String((user && (user.id || user.username || user.phone)) || 'guest')
  } catch (_) {}
  return base + ':' + userKey
}

function clearHomeAgentSelectionStorage() {
  ;[selectedProfilesStorageKey, selectedToolsStorageKey, sendConfirmSkipStorageKey].forEach(function(base) {
    try { uni.removeStorageSync(currentUserScopedStorageKey(base)) } catch (_) {}
  })
}

function saveSelectedProfiles() {
  if (!isLoggedIn.value) return
  try { uni.removeStorageSync(currentUserScopedStorageKey(selectedProfilesStorageKey)) } catch (_) {}
}

function saveSelectedToolModels() {
  try { uni.removeStorageSync(currentUserScopedStorageKey(selectedToolsStorageKey)) } catch (_) {}
}

function resetSelectedToolModels() {
  selectedToolModels.value = []
  autoSelectTools.value = false
  saveSelectedToolModels()
}

function restoreSavedAgentSelection(profileList) {
  if (!isLoggedIn.value) return
  try { uni.removeStorageSync(currentUserScopedStorageKey(selectedProfilesStorageKey)) } catch (_) {}
  saveSelectedToolModels()
}

function isProfileSelected(p) {
  const key = profileKey(p)
  return selectedProfiles.value.some(item => profileKey(item) === key)
}

function isProfileDraftSelected(p) {
  const key = profileKey(p)
  return draftSelectedProfiles.value.some(item => profileKey(item) === key)
}

function toggleProfileSelection(p) {
  const list = draftSelectedProfiles.value.slice()
  const key = profileKey(p)
  const idx = list.findIndex(item => profileKey(item) === key)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(p)
  draftSelectedProfiles.value = list
}

function confirmProfileSelection() {
  selectedProfiles.value = draftSelectedProfiles.value.slice()
  profileSelectionConfirmed.value = true
  saveSelectedProfiles()
  if (selectedProfilesNeedBirthCompletion()) {
    uni.showToast({ title: '请补全出生信息后再解读', icon: 'none' })
    profileQuickFormOpen.value = true
    loadQuickCityData()
  } else {
    profileSheetOpen.value = false
    uni.showToast({ title: '命盘已选，可开始解读', icon: 'none' })
  }
}

function cancelProfileSelection() {
  draftSelectedProfiles.value = selectedProfiles.value.slice()
  profileSheetOpen.value = false
}

function onLlmModelChange(e) {
  llmModelIdx.value = Number(e.detail.value || 0)
}

function onReadingModeChange(e) {
  const idx = Number(e.detail.value || 0)
  readingMode.value = (readingModes.value[idx] && readingModes.value[idx].id) || 'standard'
  writeStorageJson(readingModeStorageKey, readingMode.value)
}

function modeCostDelta() {
  const mode = selectedReadingMode.value || readingModes.value[1] || {}
  return Number(mode.cost_delta || 0)
}

function toggleToolModel(id) {
  autoSelectTools.value = false
  const list = selectedToolModels.value.slice()
  const idx = list.indexOf(id)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(id)
  selectedToolModels.value = list
  saveSelectedToolModels()
}

function toggleAutoSelectTools() {
  autoSelectTools.value = !autoSelectTools.value
  if (autoSelectTools.value) selectedToolModels.value = []
  saveSelectedToolModels()
}

async function loadComprehensiveOptions() {
  if (!isLoggedIn.value) return
  try {
    const res = await uni.request({ url: '/api/comprehensive/options' })
    const data = res.data || {}
    if (Array.isArray(data.llm_models) && data.llm_models.length) llmModels.value = data.llm_models
    if (Array.isArray(data.reading_modes) && data.reading_modes.length) readingModes.value = data.reading_modes
    if (Array.isArray(data.tool_models) && data.tool_models.length) toolModels.value = data.tool_models
    if (typeof data.points === 'number') currentPoints.value = data.points
    if (typeof data.ai_single_credits === 'number') aiSingleCredits.value = data.ai_single_credits
    if (typeof data.ai_combo_credits === 'number') aiComboCredits.value = data.ai_combo_credits
    dailyLightAvailable.value = !!data.daily_light_available
  } catch (_) {}
}

async function loadProfiles() {
  if (!isLoggedIn.value) return
  try {
    const res = await uni.request({ url: '/api/profiles?sort=last_used' })
    const profileData = res.data || {}
    const profileList = (profileData.profiles || []).map(function(p) {
      return Object.assign({ source: 'profile' }, p)
    })
    profiles.value = profileList
    const appliedPending = applyPendingAgentProfile(profileList)
    if (!appliedPending) restoreSavedAgentSelection(profileList)
    applyPendingAgentHandoff(profileList)
  } catch (_) {
    profiles.value = []
  }
}

function applyPendingAgentHandoff(profileList) {
  let handoff = null
  try {
    const raw = uni.getStorageSync(agentHandoffStorageKey)
    handoff = typeof raw === 'string' ? JSON.parse(raw) : raw
    if (!handoff || typeof handoff !== 'object') return false
    uni.removeStorageSync(agentHandoffStorageKey)
  } catch (_) {
    try { uni.removeStorageSync(agentHandoffStorageKey) } catch (__) {}
    return false
  }

  const tools = Array.isArray(handoff.tool_models) ? handoff.tool_models.filter(Boolean) : []
  if (tools.length) {
    autoSelectTools.value = false
    selectedToolModels.value = tools
    saveSelectedToolModels()
  }

  const list = profileList || profiles.value || []
  const profileId = handoff.profile_id || (handoff.profile && handoff.profile.id)
  let selected = profileId ? list.find(p => String(p.id) === String(profileId)) : null
  if (!selected && handoff.profile && (handoff.profile.name || handoff.profile.birthTime || handoff.profile.birth_time)) {
    selected = Object.assign({ source: 'profile' }, handoff.profile)
  }
  if (selected) {
    selectedProfiles.value = [Object.assign({ source: selected.source || 'profile' }, selected)]
    profileSelectionConfirmed.value = true
    saveSelectedProfiles()
  }

  if (handoff.paipan && typeof handoff.paipan === 'object') {
    currentPaipanContext.value = Object.assign({}, currentPaipanContext.value || {}, handoff.paipan)
  }
  if (handoff.artifacts && typeof handoff.artifacts === 'object') {
    currentArtifacts.value = Object.assign({}, currentArtifacts.value || {}, handoff.artifacts)
  }
  if (handoff.question && !comprehensiveQuestion.value.trim()) {
    comprehensiveQuestion.value = String(handoff.question)
    questionGuideDraft.question = String(handoff.question)
    questionGuideDraft.finalQuestion = String(handoff.question)
  }
  saveComprehensiveDraftNow()
  uni.showToast({ title: '已带入盘面，可直接解读', icon: 'none' })
  return true
}

function applyPendingAgentProfile(profileList) {
  try {
    const pendingId = uni.getStorageSync('xc_agent_profile_autoselect')
    if (!pendingId) return false
    const list = profileList || profiles.value || []
    let selected = list.find(p => String(p.id) === String(pendingId))
    if (!selected) {
      const raw = uni.getStorageSync('xc_selected_profile')
      selected = raw ? JSON.parse(raw) : null
    }
    if (selected && selected.name) {
      selectedProfiles.value = [Object.assign({ source: 'profile' }, selected)]
      profileSelectionConfirmed.value = true
      saveSelectedProfiles()
    }
    uni.removeStorageSync('xc_agent_profile_autoselect')
    return !!(selected && selected.name)
  } catch (_) {
    return false
  }
}

function toggleQuickProfileForm() {
  profileQuickFormOpen.value = !profileQuickFormOpen.value
  if (profileQuickFormOpen.value) loadQuickCityData()
}

function onQuickProfileTypeChange(e) {
  const idx = Number(e.detail.value || 0)
  quickProfileForm.profileType = profileTypeQuickValues[idx] || 'self'
}

function onQuickGenderChange(e) {
  const idx = Number(e.detail.value || 0)
  quickProfileForm.gender = genderOptions[idx] || '男'
}

function onQuickCalTypeChange(e) {
  const idx = Number(e.detail.value || 0)
  quickProfileForm.calType = calTypeOptions[idx] || '公历'
}

function resetQuickProfileForm() {
  quickProfileForm.name = ''
  quickProfileForm.profileType = 'self'
  quickProfileForm.gender = '男'
  quickProfileForm.calType = '公历'
  quickProfileForm.birthYear = ''
  quickProfileForm.birthMonth = ''
  quickProfileForm.birthDay = ''
  quickProfileForm.birthHour = ''
  quickProfileForm.birthMinute = ''
  quickProfileForm.birthProvince = ''
  quickProfileForm.birthCity = ''
  quickProfileForm.birthDistrict = ''
  quickProfileForm.birthAddr = ''
  quickProfileForm.birthLng = 0
  quickProfileForm.birthLat = 0
  quickProfileForm.timeUnknown = false
}

function quickBirthTime() {
  const y = String(quickProfileForm.birthYear || '').padStart(4, '0')
  const m = String(quickProfileForm.birthMonth || '').padStart(2, '0')
  const d = String(quickProfileForm.birthDay || '').padStart(2, '0')
  const missingTime = quickProfileForm.birthHour === '' || quickProfileForm.birthMinute === ''
  const h = quickProfileForm.timeUnknown || missingTime ? '12' : String(quickProfileForm.birthHour).padStart(2, '0')
  const minute = quickProfileForm.timeUnknown || missingTime ? '00' : String(quickProfileForm.birthMinute).padStart(2, '0')
  return y + m + d + h + minute
}

function normalizeQuickBirthDay() {
  const day = Number(quickProfileForm.birthDay || 0)
  const maxDay = quickDayOptions.value.length
  if (day > maxDay) quickProfileForm.birthDay = maxDay
}

function quickSelectValue(e) {
  if (e && e.target) return e.target.value
  if (e && e.detail && e.detail.value !== undefined) return e.detail.value
  return ''
}

function onQuickBirthPartChange(part, e) {
  const raw = quickSelectValue(e)
  quickProfileForm[part] = raw === '' ? '' : Number(raw)
  if (part === 'birthYear' || part === 'birthMonth') normalizeQuickBirthDay()
}

function loadQuickCityData() {
  if (quickCityData.value.length) return
  // #ifdef H5
  fetch('/static/js/city_data.json')
    .then(function(res) { return res.json() })
    .then(function(data) { quickCityData.value = Array.isArray(data) ? data : [] })
    .catch(function() { quickCityData.value = [] })
  // #endif
}

function onQuickProvinceChange(e) {
  quickProfileForm.birthProvince = quickSelectValue(e)
  quickProfileForm.birthCity = ''
  quickProfileForm.birthDistrict = ''
  syncQuickBirthAddr()
}

function onQuickCityChange(e) {
  quickProfileForm.birthCity = quickSelectValue(e)
  quickProfileForm.birthDistrict = ''
  syncQuickBirthAddr()
}

function onQuickDistrictChange(e) {
  quickProfileForm.birthDistrict = quickSelectValue(e)
  syncQuickBirthAddr()
}

function syncQuickBirthAddr() {
  const parts = [quickProfileForm.birthProvince, quickProfileForm.birthCity, quickProfileForm.birthDistrict].filter(Boolean)
  quickProfileForm.birthAddr = parts.join(' ')
  let district = null
  if (quickProfileForm.birthDistrict) {
    district = quickDistrictOptions.value.find(item => item.name === quickProfileForm.birthDistrict)
  }
  if (!district && quickDistrictOptions.value.length) district = quickDistrictOptions.value[0]
  quickProfileForm.birthLat = district && district.lat ? Number(district.lat) : 0
  quickProfileForm.birthLng = district && district.lng ? Number(district.lng) : 0
}

async function createQuickProfile() {
  const name = quickProfileForm.name.trim()
  if (!quickProfileForm.birthYear || !quickProfileForm.birthMonth || !quickProfileForm.birthDay) {
    return uni.showToast({ title: '请填写出生日期', icon: 'none' })
  }
  const birthDate = String(quickProfileForm.birthYear || '').padStart(4, '0')
    + String(quickProfileForm.birthMonth || '').padStart(2, '0')
    + String(quickProfileForm.birthDay || '').padStart(2, '0')
  if (!name) return uni.showToast({ title: '请填写姓名', icon: 'none' })
  if (!birthDate || birthDate.length !== 8) return uni.showToast({ title: '请填写出生日期', icon: 'none' })
  const birthAddr = quickProfileForm.birthAddr.trim()
  try {
    const payload = {
      name,
      gender: quickProfileForm.gender,
      calType: quickProfileForm.calType,
      birthTime: quickBirthTime(),
      birthAddr,
      birthLng: quickProfileForm.birthLng || 0,
      birthLat: quickProfileForm.birthLat || 0,
      profileType: quickProfileForm.profileType,
      isDefault: quickProfileForm.profileType === 'self' && !(profiles.value || []).some(p => p.isDefault),
      source: 'manual',
      meta: {
        source: 'manual',
        createdFrom: 'home_agent_profile_picker',
        birthTimePrecision: quickProfileForm.timeUnknown || quickProfileForm.birthHour === '' || quickProfileForm.birthMinute === '' ? 'date_unknown_time' : 'datetime',
        birthPlacePrecision: birthAddr ? 'known' : 'unknown',
        birthLng: quickProfileForm.birthLng || 0,
        birthLat: quickProfileForm.birthLat || 0,
      },
    }
    const res = await uni.request({ url: '/api/profiles', method: 'POST', data: payload })
    const created = res.data || {}
    if (created.error) throw new Error(created.error)
    await loadProfiles()
    const selected = (profiles.value || []).find(p => String(p.id) === String(created.id)) || Object.assign({ source: 'profile' }, created)
    selectedProfiles.value = [selected]
    draftSelectedProfiles.value = [selected]
    profileSelectionConfirmed.value = true
    saveSelectedProfiles()
    profileQuickFormOpen.value = false
    resetQuickProfileForm()
    uni.showToast({ title: '已添加命盘', icon: 'none' })
  } catch (_) {
    uni.showToast({ title: '添加失败，请稍后重试', icon: 'none' })
  }
}

function comprehensiveProfilePayload(p) {
  return {
    name: p.name || '未命名',
    gender: p.gender || '男',
    cal_type: p.cal_type || p.calType || '公历',
    birth_time: p.birth_time || p.birthTime || '',
    birth_addr: p.birth_addr || p.birthAddr || '',
    profile_type: p.profile_type || p.profileType || 'self',
    source: p.source || 'profile',
    record_id: p.recordId || null,
    meta: p.meta || {},
  }
}

function getToolName(id) {
  const tool = toolModels.value.find(t => t.id === id)
  return tool ? tool.name : id
}

function normalizeHomeArtifactForDisplay(artifact, key, previous, options) {
  const opts = options || {}
  const savedCollapsed = getSavedArtifactCollapsed(key)
  const rawAnalysis = (artifact.analysis || '') || (previous.analysis || '')
  return Object.assign({}, artifact, {
    key: artifact.key || key,
    title: artifact.title || artifactTitle(key, artifact.tool),
    collapsed: previous.collapsed !== undefined ? !!previous.collapsed : (savedCollapsed !== undefined ? savedCollapsed : !!artifact.collapsed),
    visible: previous.visible !== undefined ? !!previous.visible : (opts.defaultVisible !== undefined ? !!opts.defaultVisible : artifact.visible !== false),
    analysis: sanitizeArtifactAnalysisText(rawAnalysis),
  })
}

function artifactListFromMap(map, options) {
  const order = ['qimen.pan', 'bazi.basic', 'bazi.yun', 'liuyao.pan', 'meihua.pan', 'ziwei.pan', 'tarot.cards', 'zeji.days']
  const source = map || {}
  const opts = options || {}
  const existing = opts.existing || []
  const existingMap = {}
  existing.forEach(function(item) {
    if (item && item.key) existingMap[item.key] = item
  })
  return Object.keys(source)
    .sort(function(a, b) {
      const ai = order.indexOf(a)
      const bi = order.indexOf(b)
      return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi)
    })
    .map(function(key) {
      const artifact = source[key] || {}
      const previous = existingMap[key] || {}
      return normalizeHomeArtifactForDisplay(artifact, key, previous, opts)
    })
}

function getArtifactCollapseStore() {
  const stored = readStorageJson(artifactCollapseStorageKey, {})
  return stored && typeof stored === 'object' && !Array.isArray(stored) ? stored : {}
}

function artifactCollapseStoreKey(artifactKey, conversationId) {
  return (conversationId ? ('conv:' + conversationId) : 'global') + ':' + artifactKey
}

function getSavedArtifactCollapsed(artifactKey) {
  const store = getArtifactCollapseStore()
  const convId = currentComprehensiveConvId.value
  const convKey = artifactCollapseStoreKey(artifactKey, convId)
  if (Object.prototype.hasOwnProperty.call(store, convKey)) return !!store[convKey]
  const globalKey = artifactCollapseStoreKey(artifactKey, null)
  if (Object.prototype.hasOwnProperty.call(store, globalKey)) return !!store[globalKey]
  return undefined
}

function saveArtifactCollapsed(artifactKey, collapsed, conversationId) {
  if (!artifactKey) return
  const store = getArtifactCollapseStore()
  store[artifactCollapseStoreKey(artifactKey, null)] = !!collapsed
  const convId = conversationId || currentComprehensiveConvId.value
  if (convId) store[artifactCollapseStoreKey(artifactKey, convId)] = !!collapsed
  uni.setStorageSync(artifactCollapseStorageKey, store)
}

function syncArtifactCollapseStateToConversation(conversationId) {
  if (!conversationId) return
  comprehensiveMessages.value.forEach(function(msg) {
    ;(msg.artifacts || []).forEach(function(artifact) {
      if (artifact && artifact.key) saveArtifactCollapsed(artifact.key, !!artifact.collapsed, conversationId)
    })
  })
}

function visibleArtifactList(msg) {
  return ((msg && msg.artifacts) || []).filter(function(artifact) {
    return artifact && artifact.visible !== false
  })
}

function artifactTabsForMessage(msg) {
  return visibleArtifactList(msg).map(function(artifact) {
    return Object.assign({}, artifact, { summary: artifactSummary(artifact) })
  })
}

const activeArtifactKeyByMessage = reactive({})

function ensureActiveArtifact(messageIndex, artifacts) {
  const list = artifacts || []
  const current = activeArtifactKeyByMessage[messageIndex]
  if (!list.length) return ''
  if (current === '__summary__') return current
  if (current && list.some(function(item) { return item.key === current })) return current
  activeArtifactKeyByMessage[messageIndex] = list[0].key
  return list[0].key
}

function activeArtifactKeyForMessage(msg, messageIndex) {
  const list = visibleArtifactList(msg)
  if (msg && msg.role === 'assistant' && (msg.content || msg._streaming) && !activeArtifactKeyByMessage[messageIndex]) return '__summary__'
  return activeArtifactKeyByMessage[messageIndex] || (list[0] && list[0].key) || ''
}

function setActiveArtifact(messageIndex, key) {
  if (!key) return
  activeArtifactKeyByMessage[messageIndex] = key
  scheduleComprehensiveDraftSave()
}

function isSummaryActive(msg, messageIndex) {
  const list = visibleArtifactList(msg)
  return !!msg && msg.role === 'assistant' && (!!msg.content || !!msg._streaming) && activeArtifactKeyForMessage(msg, messageIndex) === '__summary__' && list.length > 0
}

function currentArtifactForMessage(msg, messageIndex) {
  const list = visibleArtifactList(msg)
  const key = activeArtifactKeyForMessage(msg, messageIndex)
  return list.find(function(item) { return item.key === key }) || list[0] || null
}

function revealArtifact(aiIndex, artifactKey) {
  const current = comprehensiveMessages.value[aiIndex]
  if (!current || !artifactKey) return
  const savedCollapsed = getSavedArtifactCollapsed(artifactKey)
  const artifacts = (current.artifacts || []).map(function(artifact) {
    if (artifact.key !== artifactKey) return artifact
    return Object.assign({}, artifact, {
      visible: true,
      collapsed: savedCollapsed !== undefined ? savedCollapsed : false,
    })
  })
  setActiveArtifact(aiIndex, artifactKey)
  updateComprehensiveAssistant(aiIndex, { artifacts }, { shouldFollow: shouldAutoFollowChat.value && isComprehensiveChatNearBottom() })
}

function artifactAnalysisQueueKey(aiIndex, artifactKey) {
  return String(aiIndex) + ':' + String(artifactKey)
}

function cleanArtifactAnalysisChunk(text) {
  return sanitizeArtifactAnalysisChunk(text)
}

function artifactStreamOptions(artifactKey) {
  return COMPREHENSIVE_HEAVY_ARTIFACT_KEYS.includes(artifactKey)
    ? COMPREHENSIVE_HEAVY_ARTIFACT_STREAM_OPTIONS
    : COMPREHENSIVE_ARTIFACT_STREAM_OPTIONS
}

function cancelArtifactAnalysisFrame(state) {
  if (!state) return
  // #ifdef H5
  if (state.frame) cancelAnimationFrame(state.frame)
  state.frame = null
  // #endif
  // #ifndef H5
  if (state.timer) clearTimeout(state.timer)
  state.timer = null
  // #endif
}

function scheduleArtifactAnalysisFrame(state) {
  if (!state || state.frame || state.timer) return
  // #ifdef H5
  state.frame = requestAnimationFrame(function(now) {
    state.frame = null
    pumpArtifactAnalysis(state.aiIndex, state.artifactKey, now)
  })
  // #endif
  // #ifndef H5
  state.timer = setTimeout(function() {
    state.timer = null
    pumpArtifactAnalysis(state.aiIndex, state.artifactKey, Date.now())
  }, COMPREHENSIVE_TYPE_FRAME_MS)
  // #endif
}

function appendArtifactAnalysisChunk(aiIndex, artifactKey, chunk) {
  const shouldFollow = shouldAutoFollowChat.value && isComprehensiveChatNearBottom()
  const current = comprehensiveMessages.value[aiIndex]
  if (!current || !artifactKey || !chunk) return
  const cleanedChunk = cleanArtifactAnalysisChunk(chunk)
  if (!cleanedChunk) return
  const artifacts = (current.artifacts || []).map(function(artifact) {
    if (artifact.key !== artifactKey) return artifact
    return Object.assign({}, artifact, {
      visible: true,
      analysis: (artifact.analysis || '') + cleanedChunk,
    })
  })
  updateComprehensiveAssistant(aiIndex, { artifacts }, { shouldFollow })
}

function pumpArtifactAnalysis(aiIndex, artifactKey, now) {
  const queueKey = artifactAnalysisQueueKey(aiIndex, artifactKey)
  const state = comprehensiveArtifactAnalysisTimers[queueKey]
  const current = comprehensiveMessages.value[aiIndex]
  if (!state || !current || !artifactKey) {
    if (state) delete comprehensiveArtifactAnalysisTimers[queueKey]
    return
  }
  if (!state.queue.length) {
    delete comprehensiveArtifactAnalysisTimers[queueKey]
    return
  }
  const lastAt = state.lastTypeAt || now
  const elapsed = Math.max(COMPREHENSIVE_TYPE_FRAME_MS, Math.min(48, now - lastAt))
  state.lastTypeAt = now
  const streamOptions = artifactStreamOptions(artifactKey)
  state.charBudget = (state.charBudget || 0) + (elapsed / 1000) * smoothTextSpeed(state.queue.length, streamOptions)
  const nextChunk = takeSmoothTextChunk(state.queue, Math.floor(state.charBudget), streamOptions.maxFrameChars)
  if (nextChunk.chunk) {
    state.charBudget = Math.max(0, (state.charBudget || 0) - nextChunk.count)
    state.queue = nextChunk.rest
    appendArtifactAnalysisChunk(aiIndex, artifactKey, nextChunk.chunk)
  }
  if (state.queue.length) scheduleArtifactAnalysisFrame(state)
  else delete comprehensiveArtifactAnalysisTimers[queueKey]
}

function flushArtifactAnalysis(aiIndex, artifactKey) {
  const shouldFollow = shouldAutoFollowChat.value && isComprehensiveChatNearBottom()
  const current = comprehensiveMessages.value[aiIndex]
  const queueKey = artifactAnalysisQueueKey(aiIndex, artifactKey)
  const state = comprehensiveArtifactAnalysisTimers[queueKey]
  if (!state) return
  cancelArtifactAnalysisFrame(state)
  delete comprehensiveArtifactAnalysisTimers[queueKey]
  if (!current || !artifactKey || !state.queue) return
  const artifacts = (current.artifacts || []).map(function(artifact) {
    if (artifact.key !== artifactKey) return artifact
    return Object.assign({}, artifact, {
      visible: true,
      analysis: sanitizeArtifactAnalysisText(stripComprehensiveMarkdown((artifact.analysis || '') + state.queue))
    })
  })
  updateComprehensiveAssistant(aiIndex, { artifacts }, { shouldFollow })
}

function flushPendingArtifactAnalyses() {
  Object.keys(comprehensiveArtifactAnalysisTimers).forEach(function(key) {
    const state = comprehensiveArtifactAnalysisTimers[key]
    if (state) flushArtifactAnalysis(state.aiIndex, state.artifactKey)
  })
}

function stopPendingArtifactAnalysisTimers() {
  Object.keys(comprehensiveArtifactAnalysisTimers).forEach(function(key) {
    const state = comprehensiveArtifactAnalysisTimers[key]
    cancelArtifactAnalysisFrame(state)
  })
  comprehensiveArtifactAnalysisTimers = {}
}

function appendArtifactAnalysis(aiIndex, artifactKey, content) {
  const current = comprehensiveMessages.value[aiIndex]
  if (!current || !artifactKey || !content) return
  const queueKey = artifactAnalysisQueueKey(aiIndex, artifactKey)
  const state = comprehensiveArtifactAnalysisTimers[queueKey] || {
    aiIndex,
    artifactKey,
    queue: '',
    frame: null,
    timer: null,
    charBudget: 0,
    lastTypeAt: 0,
  }
  state.queue += content
  comprehensiveArtifactAnalysisTimers[queueKey] = state
  scheduleArtifactAnalysisFrame(state)
}

function artifactTitle(key, tool) {
  const map = {
    'bazi.basic': '八字基本排盘',
    'bazi.yun': '大运流年流月',
    'qimen.pan': '奇门遁甲完整盘',
    'liuyao.pan': '六爻卦象',
    'meihua.pan': '梅花易数卦象',
    'ziwei.pan': '紫微斗数三合盘',
    'tarot.cards': '塔罗牌面',
    'zeji.days': '择吉结果',
  }
  return map[key] || getToolName(tool || key)
}

function artifactSummary(artifact) {
  const data = artifact && artifact.data ? artifact.data : {}
  if (artifact.key === 'bazi.basic') {
    const fp = data.four_pillars || {}
    return [pillarText(fp.year), pillarText(fp.month), pillarText(fp.day), pillarText(fp.hour)].filter(Boolean).join(' ')
  }
  if (artifact.key === 'bazi.yun') return '按问题追加推运依据，不重复基础盘'
  if (artifact.key === 'qimen.pan') return [data.ju, data.solar_date].filter(Boolean).join(' · ') || '完整九宫盘'
  if (artifact.key === 'liuyao.pan') return [data.ben_gua, data.bian_gua].filter(Boolean).join(' → ') || '六亲六神世应'
  if (artifact.key === 'meihua.pan') return '本卦 · 互卦 · 变卦 · 体用'
  if (artifact.key === 'ziwei.pan') return ((data.twelve_palaces || data.palaces || []).length || 12) + ' 宫'
  if (artifact.key === 'tarot.cards') return (data.spread && data.spread.name) || data.spread_name || '抽牌翻牌结果'
  if (artifact.key === 'zeji.days') return (data.best_days || []).length + ' 个候选日'
  return artifact.title || ''
}

function compactValue(value) {
  if (value === undefined || value === null || value === '') return ''
  if (Array.isArray(value)) return value.length ? value.join('/') : ''
  if (typeof value === 'object') return ''
  return String(value)
}

function compactParts(parts) {
  return parts.map(function(item) {
    const value = compactValue(item.value)
    return value ? item.label + ' ' + value : ''
  }).filter(Boolean).join(' · ')
}

function artifactFeedSummary(artifact) {
  const data = artifact && artifact.data ? artifact.data : {}
  const key = artifact && artifact.key
  if (!key) return ''
  if (key === 'bazi.basic' || key === 'bazi.yun') {
    const fp = data.four_pillars || {}
    return '合参资料：' + compactParts([
      { label: '出生', value: data.birth_input || data.birth_solar || data.birthTime },
      { label: '真太阳时', value: data.true_solar_time },
      { label: '四柱', value: [pillarText(fp.year), pillarText(fp.month), pillarText(fp.day), pillarText(fp.hour)].filter(Boolean) },
      { label: '起运', value: data.qi_yun_detail && data.qi_yun_detail.text },
    ])
  }
  if (key === 'qimen.pan') {
    const fp = data.fourPillars || data.four_pillars || {}
    return '合参资料：' + compactParts([
      { label: '起局', value: data.paipanTime || data.paipan_time || data.solar_date || data.time },
      { label: '局数', value: data.ju || data.ju_name },
      { label: '四柱', value: [fp.year, fp.month, fp.day, fp.hour].filter(Boolean) },
      { label: '问题', value: data.question },
    ])
  }
  if (key === 'ziwei.pan') {
    const form = data.form || data.birth || {}
    return '合参资料：' + compactParts([
      { label: '出生', value: [form.year, form.month, form.day].filter(Boolean).join('-') || data.solar_date || data.birth_date },
      { label: '时分', value: [form.hour, form.minute].filter(v => v !== undefined && v !== '').join(':') },
      { label: '性别', value: form.gender || data.gender },
      { label: '宫数', value: ((data.twelve_palaces || data.palaces || []).length || '') },
    ])
  }
  if (key === 'liuyao.pan') {
    return '合参资料：' + compactParts([
      { label: '起卦', value: data.timestamp || data.time || data.created_at },
      { label: '方式', value: data.method || data.qigua_method },
      { label: '本卦', value: data.ben_gua },
      { label: '变卦', value: data.bian_gua },
    ])
  }
  if (key === 'meihua.pan') {
    return '合参资料：' + compactParts([
      { label: '起卦', value: data.timestamp || data.time },
      { label: '本卦', value: data.ben_gua || data.main_gua },
      { label: '互卦', value: data.hu_gua },
      { label: '变卦', value: data.bian_gua || data.changed_gua },
    ])
  }
  if (key === 'tarot.cards') {
    const cards = (data.cards || []).map(function(card) { return card.name || card.title || card.card }).filter(Boolean)
    return '合参资料：' + compactParts([
      { label: '牌阵', value: (data.spread && data.spread.name) || data.spread_name },
      { label: '牌面', value: cards.slice(0, 5) },
    ])
  }
  if (key === 'zeji.days') {
    return '合参资料：' + compactParts([
      { label: '事项', value: data.zeji_type || data.type },
      { label: '日期', value: data.start_date && data.end_date ? data.start_date + ' 至 ' + data.end_date : data.date },
      { label: '候选', value: (data.best_days || []).length ? (data.best_days || []).length + '天' : '' },
    ])
  }
  return ''
}

function renderKV(label, value) {
  return '<div class="artifact-kv"><span>' + htmlEscape(label) + '</span><strong>' + htmlEscape(value || '-') + '</strong></div>'
}

function extractAnalysisHighlights(text) {
  const source = String(text || '')
  const years = new Set(source.match(/(?:19|20|21)\d{2}/g) || [])
  const months = new Set()
  ;(source.match(/(?:正|一|二|三|四|五|六|七|八|九|十|十一|十二|\d{1,2})月/g) || []).forEach(function(m) {
    const raw = m.replace('月', '')
    const cn = { '正': '1', '一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6', '七': '7', '八': '8', '九': '9', '十': '10', '十一': '11', '十二': '12' }
    months.add(String(Number(cn[raw] || raw)))
  })
  return { raw: source, years, months }
}

function verticalGzHtml(gz) {
  const text = String(gz || '').trim()
  if (!text) return '<b>-</b>'
  return text.split('').map(function(ch) {
    const wx = ganWuxing(ch) || zhiWuxing(ch)
    return '<b class="wx-text-' + wxClass(wx) + '">' + htmlEscape(ch) + '</b>'
  }).join('')
}

function homeYunGz(item) {
  if (!item) return ''
  if (typeof item === 'string') return item
  return item.gan_zhi || item.gz || item.name || item.stem_branch || [item.gan, item.zhi].filter(Boolean).join('')
}

function homeYunLabel(item) {
  if (!item) return ''
  if (item.month_name) return item.month_name
  if (item.month_num) return item.month_num + '月'
  if (item.month) return item.month
  if (item.start_age && item.end_age) return item.start_age + '-' + item.end_age + '岁'
  return item.age_range || item.range || item.start_age || item.age || item.year || ''
}

function homeYunSub(item) {
  if (!item) return ''
  return item.gan_shishen_abbrev || item.shi_shen_gan || item.shi_shen || item.ss_full || item.tgSs || item.nayin || ''
}

function homeYunYear(item) {
  if (!item) return ''
  return item.start_year || item.year || item.jieqi || ''
}

function parseHomeYear(value) {
  const n = parseInt(value, 10)
  return Number.isFinite(n) ? n : 0
}

function homeYunInDayun(item, dy) {
  if (!dy) return true
  const year = parseHomeYear(item && item.year)
  if (!year) return true
  const startYear = parseHomeYear(dy.start_year || dy.year)
  const endYear = parseHomeYear(dy.end_year || (startYear ? startYear + 9 : 0))
  if (!startYear || !endYear) return true
  return year >= startYear && year <= endYear
}

function homeShiShen(dayMaster, gan) {
  if (!dayMaster || !gan) return ''
  const TG = '甲乙丙丁戊己庚辛壬癸'
  const idxD = TG.indexOf(dayMaster)
  const idxG = TG.indexOf(gan)
  if (idxD < 0 || idxG < 0) return ''
  const diff = (idxG - idxD + 10) % 10
  return ['比肩', '劫财', '食神', '伤官', '偏财', '正财', '七杀', '正官', '偏印', '正印'][diff] || ''
}

function computeHomeLiuYueList(year, liunianList, data) {
  const TG = '甲乙丙丁戊己庚辛壬癸'
  const ly = parseHomeYear(year)
  const selectedLn = (liunianList || []).find(function(item) {
    return parseHomeYear(item && item.year) === ly
  }) || {}
  const yearGan = selectedLn.gan || String(homeYunGz(selectedLn)).slice(0, 1)
  const yearGanIdx = yearGan ? TG.indexOf(yearGan) : -1
  const monthGanStart = yearGanIdx >= 0 ? [2, 4, 6, 8, 0][yearGanIdx % 5] : 0
  const monthZhis = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
  const jieNames = ['立春', '惊蛰', '清明', '立夏', '芒种', '小暑', '立秋', '白露', '寒露', '立冬', '大雪', '小寒']
  const monthNames = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月']
  const dayMaster = data?.four_pillars?.day?.gan || data?.day_master || ''
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() + 1
  const currentDay = now.getDate()
  let currentLiuyueIdx = -1
  if (ly === currentYear) {
    const jieMonthDays = [[2, 4], [3, 5], [4, 5], [5, 5], [6, 5], [7, 7], [8, 7], [9, 7], [10, 8], [11, 7], [12, 7], [1, 5]]
    if (currentMonth === 1 && currentDay >= 5) {
      currentLiuyueIdx = 11
    } else {
      for (let j = 0; j < jieMonthDays.length - 1; j++) {
        const jm = jieMonthDays[j][0]
        const jd = jieMonthDays[j][1]
        if (currentMonth > jm || (currentMonth === jm && currentDay >= jd)) currentLiuyueIdx = j
      }
      if (currentLiuyueIdx < 0) currentLiuyueIdx = 11
    }
  }
  return monthZhis.map(function(zhi, idx) {
    const gan = TG[(monthGanStart + idx) % 10]
    return {
      year: ly,
      jieqi: jieNames[idx],
      month_name: monthNames[idx],
      month_num: idx + 1,
      gan,
      zhi,
      gan_zhi: gan + zhi,
      tgSs: homeShiShen(dayMaster, gan),
      current: idx === currentLiuyueIdx,
    }
  })
}

function renderHomeYunItem(item, kind, index, options) {
  const opts = options || {}
  const label = homeYunLabel(item)
  const value = homeYunGz(item)
  const sub = homeYunSub(item)
  const year = homeYunYear(item)
  const yearNum = kind === 'dayun' ? (item.start_year || item.year || '') : (item.year || '')
  const monthNum = item.month_num || ''
  const classes = [
    'bz-yun-item',
    opts.active ? 'is-active' : '',
    opts.highlight ? 'is-analysis-highlight' : '',
    item && item.current ? 'is-current' : '',
  ].filter(Boolean).join(' ')
  const hiddenStyle = opts.hidden ? ' style="display:none"' : ''
  return '<div class="' + classes + '" role="button" tabindex="0" data-yun-kind="' + htmlEscape(kind) + '" data-yun-index="' + htmlEscape(index) + '" data-year="' + htmlEscape(yearNum) + '" data-start-year="' + htmlEscape(item.start_year || '') + '" data-end-year="' + htmlEscape(item.end_year || '') + '" data-gan="' + htmlEscape(item.gan || String(value).slice(0, 1) || '') + '" data-zhi="' + htmlEscape(item.zhi || String(value).slice(1, 2) || '') + '" data-month-num="' + htmlEscape(monthNum) + '"' + hiddenStyle + '>' +
    '<span class="bz-yun-year">' + htmlEscape(year) + '</span>' +
    '<span class="bz-yun-age">' + htmlEscape(label) + '</span>' +
    '<strong class="bz-yun-gz bz-yun-gz-vertical">' + verticalGzHtml(value) + '</strong>' +
    '<em>' + htmlEscape(sub) + '</em>' +
    '</div>'
}

function renderBaziBasicArtifact(data) {
  const fp = data.four_pillars || {}
  const rows = [
    ['年柱', fp.year],
    ['月柱', fp.month],
    ['日柱', fp.day],
    ['时柱', fp.hour],
  ].map(function(row) {
    const pillar = row[1] || {}
    const gan = pillar.gan || String(pillarText(pillar) || '').slice(0, 1)
    const zhi = pillar.zhi || String(pillarText(pillar) || '').slice(1, 2)
    return '<div class="bz-artifact-pillar"><span class="bz-artifact-label">' + htmlEscape(row[0]) + '</span><div class="bz-artifact-gz bz-artifact-gz-vertical"><b class="wx-color-' + wxClass(ganWuxing(gan)) + '">' + htmlEscape(gan || '-') + '</b><b class="wx-color-' + wxClass(zhiWuxing(zhi)) + '">' + htmlEscape(zhi || '-') + '</b></div><span class="bz-artifact-sub">' + htmlEscape(pillar.nayin || '') + '</span></div>'
  }).join('')
  const wuxing = data.wu_xing || data.wuxing_stats || {}
  const strength = data.strength || data.wang_shuai || data.day_master_strength || (data.wang_shuai_detail && (data.wang_shuai_detail.strength || data.wang_shuai_detail.level)) || '-'
  const geju = (data.geju && (data.geju.geju || data.geju.name)) || data.geju_name || '-'
  const birthAddr = data.birth_addr || data.birth_place || (data.location && (data.location.addr || data.location.name)) || '未填写'
  const wuxingHtml = ['金', '木', '水', '火', '土'].map(function(k) {
    return '<span class="bz-wuxing-chip wx-color-' + wxClass(k) + '">' + k + ' ' + htmlEscape(wuxing[k] === undefined ? '-' : wuxing[k]) + '</span>'
  }).join('')
  return '<div class="bz-artifact-panel">' +
    '<div class="bz-artifact-head"><div><b>八字基本排盘</b><span>' + htmlEscape([data.name, data.gender, data.birth_solar || data.birth_time].filter(Boolean).join(' · ')) + '</span></div><em>' + htmlEscape(data.birth_lunar || '') + '</em></div>' +
    '<div class="bz-artifact-pillars">' + rows + '</div>' +
    '<div class="bz-artifact-meta">' +
    '<span>日主 <b>' + htmlEscape(data.day_master || (fp.day && fp.day.gan) || '-') + '</b></span>' +
    '<span>强弱 <b>' + htmlEscape(strength) + '</b></span>' +
    '<span>格局 <b>' + htmlEscape(geju) + '</b></span>' +
    '<span>出生地 <b>' + htmlEscape(birthAddr) + '</b></span>' +
    '</div><div class="bz-wuxing-row">' + wuxingHtml + '</div>' +
    '</div>'
}

function renderBaziYunArtifact(data, analysisText) {
  const dayun = data.da_yun || data.dayun || data.luck_pillars || []
  const liunian = data.liu_nian || data.liunians || []
  const highlights = extractAnalysisHighlights(analysisText)
  const itemHighlighted = function(item) {
    const year = String(item.start_year || item.year || '')
    const month = String(item.month_num || '').replace(/[^\d]/g, '')
    const label = String(homeYunLabel(item) || '')
    return (year && highlights.years.has(year)) || (month && highlights.months.has(month)) || (!!label && highlights.raw.indexOf(label) >= 0)
  }
  const nowYear = new Date().getFullYear()
  let activeDayunIdx = Math.max(0, dayun.findIndex(function(item) {
    return item.current || homeYunInDayun({ year: nowYear }, item)
  }))
  if (!dayun.length) activeDayunIdx = -1
  const activeDayun = activeDayunIdx >= 0 ? dayun[activeDayunIdx] : null
  const visibleLiunian = (Array.isArray(liunian) ? liunian : []).filter(function(item) {
    return homeYunInDayun(item, activeDayun)
  })
  let activeLiuNianIdx = liunian.findIndex(function(item) {
    return visibleLiunian.indexOf(item) >= 0 && (item.current || parseHomeYear(item.year) === nowYear)
  })
  if (activeLiuNianIdx < 0 && visibleLiunian.length) activeLiuNianIdx = liunian.indexOf(visibleLiunian[0])
  const activeYear = activeLiuNianIdx >= 0 ? parseHomeYear(liunian[activeLiuNianIdx].year) : nowYear
  const liuyue = computeHomeLiuYueList(activeYear, liunian, data)
  const activeLiuYueIdx = Math.max(0, liuyue.findIndex(function(item) { return item.current }))
  const renderRow = function(title, list, kind, activeIdx, filterDayun) {
    const sourceList = Array.isArray(list) ? list : []
    const items = sourceList.map(function(item, idx) {
      return renderHomeYunItem(item, kind, idx, {
        active: idx === activeIdx,
        hidden: kind === 'liunian' && !homeYunInDayun(item, filterDayun),
        highlight: itemHighlighted(item),
      })
    }).join('')
    return '<div class="bz-yun-section"><div class="bz-yun-title">' + htmlEscape(title) + '</div><div class="bz-yun-scroll">' + (items || '<span class="artifact-empty">暂无数据</span>') + '</div></div>'
  }
  return '<div class="bz-yun-panel" data-day-master="' + htmlEscape(data?.four_pillars?.day?.gan || data?.day_master || '') + '">' +
    renderRow('大运', dayun, 'dayun', activeDayunIdx) +
    renderRow('流年', liunian, 'liunian', activeLiuNianIdx, activeDayun) +
    renderRow('流月', liuyue, 'liuyue', activeLiuYueIdx) +
    '</div>'
}

function createHomeYunDomItem(item, kind, index, active) {
  const node = document.createElement('div')
  node.className = 'bz-yun-item' + (active ? ' is-active' : '') + (item.current ? ' is-current' : '')
  node.setAttribute('role', 'button')
  node.setAttribute('tabindex', '0')
  node.setAttribute('data-yun-kind', kind)
  node.setAttribute('data-yun-index', String(index))
  node.setAttribute('data-year', String(kind === 'liuyue' ? (item.year || '') : (item.year || item.start_year || '')))
  node.setAttribute('data-start-year', String(item.start_year || ''))
  node.setAttribute('data-end-year', String(item.end_year || ''))
  node.setAttribute('data-gan', String(item.gan || '').slice(0, 1))
  node.setAttribute('data-zhi', String(item.zhi || '').slice(0, 1))
  node.setAttribute('data-month-num', String(item.month_num || ''))

  const yearEl = document.createElement('span')
  yearEl.className = 'bz-yun-year'
  yearEl.textContent = homeYunYear(item)
  node.appendChild(yearEl)

  const ageEl = document.createElement('span')
  ageEl.className = 'bz-yun-age'
  ageEl.textContent = homeYunLabel(item)
  node.appendChild(ageEl)

  const gzEl = document.createElement('strong')
  gzEl.className = 'bz-yun-gz bz-yun-gz-vertical'
  String(homeYunGz(item) || '').split('').forEach(function(ch) {
    const b = document.createElement('b')
    const wx = ganWuxing(ch) || zhiWuxing(ch)
    b.className = 'wx-text-' + wxClass(wx)
    b.textContent = ch
    gzEl.appendChild(b)
  })
  if (!gzEl.childNodes.length) {
    const b = document.createElement('b')
    b.textContent = '-'
    gzEl.appendChild(b)
  }
  node.appendChild(gzEl)

  const subEl = document.createElement('em')
  subEl.textContent = homeYunSub(item)
  node.appendChild(subEl)
  return node
}

function findHomeBaziYunItem(event) {
  let el = event && event.target
  while (el && el !== document.body) {
    if (el.getAttribute && el.getAttribute('data-yun-kind') && el.classList && el.classList.contains('bz-yun-item')) return el
    el = el.parentElement
  }
  return null
}

function setHomeYunActive(item) {
  const row = item && item.parentElement
  if (!row) return
  row.querySelectorAll('.bz-yun-item').forEach(function(node) {
    node.classList.toggle('is-active', node === item)
  })
}

function getHomeVisibleLiuNianItems(panel) {
  return Array.from(panel.querySelectorAll('.bz-yun-item[data-yun-kind="liunian"]')).filter(function(item) {
    return item.style.display !== 'none'
  })
}

function updateHomeLiuYueRow(panel, liunianItem) {
  if (!panel || !liunianItem) return
  const year = parseHomeYear(liunianItem.getAttribute('data-year'))
  if (!year) return
  const dayMaster = panel.getAttribute('data-day-master') || ''
  const lnGan = liunianItem.getAttribute('data-gan') || ''
  const liuyueList = computeHomeLiuYueList(year, [{ year, gan: lnGan }], { day_master: dayMaster })
  const liuyueItems = panel.querySelectorAll('.bz-yun-item[data-yun-kind="liuyue"]')
  const liuyueRow = liuyueItems.length ? liuyueItems[0].parentElement : null
  if (!liuyueRow) return
  liuyueRow.innerHTML = ''
  const activeIdx = Math.max(0, liuyueList.findIndex(function(item) { return item.current }))
  liuyueList.forEach(function(item, idx) {
    liuyueRow.appendChild(createHomeYunDomItem(item, 'liuyue', idx, idx === activeIdx))
  })
}

function onHomeBaziYunClick(event) {
  // #ifdef H5
  const item = findHomeBaziYunItem(event)
  if (!item) return
  const panel = item.closest && item.closest('.bz-yun-panel')
  if (!panel) return
  const kind = item.getAttribute('data-yun-kind')
  if (kind === 'dayun') {
    setHomeYunActive(item)
    const startYear = parseHomeYear(item.getAttribute('data-start-year') || item.getAttribute('data-year'))
    const endYear = parseHomeYear(item.getAttribute('data-end-year') || (startYear ? startYear + 9 : 0))
    const liunianItems = Array.from(panel.querySelectorAll('.bz-yun-item[data-yun-kind="liunian"]'))
    liunianItems.forEach(function(lnItem) {
      const year = parseHomeYear(lnItem.getAttribute('data-year'))
      const visible = !year || !startYear || !endYear || (year >= startYear && year <= endYear)
      lnItem.style.display = visible ? '' : 'none'
      if (!visible) lnItem.classList.remove('is-active')
    })
    const visibleLiunianItems = getHomeVisibleLiuNianItems(panel)
    if (visibleLiunianItems.length) {
      const nowYear = new Date().getFullYear()
      const nextLiuNian = visibleLiunianItems.find(function(lnItem) {
        return parseHomeYear(lnItem.getAttribute('data-year')) === nowYear || lnItem.classList.contains('is-current')
      }) || visibleLiunianItems[0]
      setHomeYunActive(nextLiuNian)
      updateHomeLiuYueRow(panel, nextLiuNian)
      nextLiuNian.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
    }
    return
  }
  if (kind === 'liunian') {
    if (item.style.display === 'none') return
    setHomeYunActive(item)
    updateHomeLiuYueRow(panel, item)
    return
  }
  if (kind === 'liuyue') {
    setHomeYunActive(item)
  }
  // #endif
}

function ganWuxing(gan) {
  return ({ '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水' })[gan] || ''
}

function zhiWuxing(zhi) {
  return ({ '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水' })[zhi] || ''
}

function pickValue(obj, keys, fallback) {
  for (let i = 0; i < keys.length; i++) {
    if (obj && obj[keys[i]] !== undefined && obj[keys[i]] !== null && obj[keys[i]] !== '') return obj[keys[i]]
  }
  return fallback === undefined ? '' : fallback
}

function wxClass(wx) {
  const map = { '金': 'jin', '木': 'mu', '水': 'shui', '火': 'huo', '土': 'tu' }
  return map[wx] || ''
}

function wsClass(ws) {
  const map = { '旺': 'wang', '相': 'xiang', '休': 'xiu', '囚': 'qiu', '死': 'si' }
  return map[ws] || 'xiu'
}

function relClass(rel) {
  if (rel === '被生' || rel === '比和') return 'ji'
  if (rel === '被克') return 'xiong'
  return 'zhong'
}

function normalizeMeihuaData(data) {
  const tiYong = data.tiYong || data.ti_yong || {}
  return {
    methodLabel: pickValue(data, ['methodLabel', 'method_label'], '时间起卦'),
    paipanTime: pickValue(data, ['paipanTime', 'paipan_time', 'time'], ''),
    ganzhi: data.ganzhi || '',
    dongYao: pickValue(data, ['dongYao', 'dong_yao'], ''),
    benGua: data.benGua || data.ben_gua || {},
    huGua: data.huGua || data.hu_gua || {},
    bianGua: data.bianGua || data.bian_gua || {},
    benGuaYao: data.benGuaYao || data.ben_gua_yao || null,
    huGuaYao: data.huGuaYao || data.hu_gua_yao || null,
    bianGuaYao: data.bianGuaYao || data.bian_gua_yao || null,
    tiYong: {
      tiPosition: pickValue(tiYong, ['tiPosition', 'ti_position'], ''),
      tiGua: pickValue(tiYong, ['tiGua', 'ti_gua'], ''),
      tiTrigram: pickValue(tiYong, ['tiTrigram', 'ti_trigram'], ''),
      tiWuxing: pickValue(tiYong, ['tiWuxing', 'ti_wuxing'], ''),
      tiWangshuai: pickValue(tiYong, ['tiWangshuai', 'ti_wangshuai'], ''),
      yongPosition: pickValue(tiYong, ['yongPosition', 'yong_position'], ''),
      yongGua: pickValue(tiYong, ['yongGua', 'yong_gua'], ''),
      yongTrigram: pickValue(tiYong, ['yongTrigram', 'yong_trigram'], ''),
      yongWuxing: pickValue(tiYong, ['yongWuxing', 'yong_wuxing'], ''),
      yongWangshuai: pickValue(tiYong, ['yongWangshuai', 'yong_wangshuai'], ''),
      tiYongRel: pickValue(tiYong, ['tiYongRel', 'ti_yong_rel', 'relation'], ''),
      tiYongJiXiong: pickValue(tiYong, ['tiYongJiXiong', 'ti_yong_ji_xiong', 'jixiong'], ''),
      tiHuRel: pickValue(tiYong, ['tiHuRel', 'ti_hu_rel'], ''),
      huWuxing: pickValue(tiYong, ['huWuxing', 'hu_wuxing'], ''),
      tiBianRel: pickValue(tiYong, ['tiBianRel', 'ti_bian_rel'], ''),
      bianWuxing: pickValue(tiYong, ['bianWuxing', 'bian_wuxing'], ''),
      verdict: tiYong.verdict || '',
    }
  }
}

function renderMeihuaGuaCard(label, gua, cardClass, dongYao, yaoList) {
  if (!gua) return ''
  const upper = gua.upper || {}
  const lower = gua.lower || {}
  let html = '<div class="gua-card ' + htmlEscape(cardClass) + '">'
  html += '<div class="gua-card-label">' + htmlEscape(label) + '</div>'
  html += '<div class="gua-card-name">' + htmlEscape(gua.name || '') + '</div>'
  if (Array.isArray(yaoList) && yaoList.length === 6) {
    html += '<div class="gua-yao-wrap">'
    for (let i = 5; i >= 0; i--) {
      const isYang = Number(yaoList[i]) === 1
      const isDong = (i + 1) === Number(dongYao)
      html += '<div class="gua-yao ' + (isYang ? 'yang' : 'yin') + (isDong ? ' dong-yao' : '') + '">'
      html += isYang ? '<div class="gua-yao-line"></div>' : '<div class="gua-yao-line"></div><div class="gua-yao-line"></div>'
      html += '</div>'
    }
    html += '</div>'
  } else {
    html += '<div class="gua-trigram">' + htmlEscape((upper.trigram || '') + (lower.trigram || '')) + '</div>'
  }
  html += '<div class="gua-sub-info">'
  html += '<span>上卦 ' + htmlEscape([upper.name, upper.nature, upper.wuxing].filter(Boolean).join('·')) + '</span>'
  html += '<span>下卦 ' + htmlEscape([lower.name, lower.nature, lower.wuxing].filter(Boolean).join('·')) + '</span>'
  html += '</div></div>'
  return html
}

function renderMeihuaArtifact(data) {
  const d = normalizeMeihuaData(data)
  let html = '<div class="mh-result-wrap">'
  html += '<div class="mh-summary">'
  html += '<span><b>起卦方式：</b>' + htmlEscape(d.methodLabel) + '</span>'
  html += '<span><b>排盘时间：</b>' + htmlEscape(d.paipanTime) + '</span>'
  if (d.ganzhi) html += '<span><b>干支：</b>' + htmlEscape(d.ganzhi) + '</span>'
  html += '</div>'
  html += '<div class="gua-display">'
  html += renderMeihuaGuaCard('本卦', d.benGua, 'ben-gua', d.dongYao, d.benGuaYao)
  html += renderMeihuaGuaCard('互卦', d.huGua, 'hu-gua', 0, d.huGuaYao)
  html += renderMeihuaGuaCard('变卦', d.bianGua, 'bian-gua', 0, d.bianGuaYao)
  html += '</div>'
  if (d.tiYong && (d.tiYong.tiGua || d.tiYong.yongGua || d.tiYong.verdict)) {
    html += '<div class="ti-yong-section">'
    html += '<div class="ti-yong-title">🌸 体用分析</div>'
    html += '<div class="ti-yong-grid">'
    html += '<div class="ti-yong-box ti"><div class="ti-yong-label">体卦（' + htmlEscape(d.tiYong.tiPosition) + '）</div><div class="ti-yong-gua">' + htmlEscape(d.tiYong.tiGua) + '</div><div class="ti-yong-wx">' + htmlEscape(d.tiYong.tiTrigram) + ' <span class="wx-tag ' + wxClass(d.tiYong.tiWuxing) + '">' + htmlEscape(d.tiYong.tiWuxing) + '</span> <span class="ws-tag ' + wsClass(d.tiYong.tiWangshuai) + '">' + htmlEscape(d.tiYong.tiWangshuai) + '</span></div></div>'
    html += '<div class="ti-yong-rel ' + relClass(d.tiYong.tiYongRel) + '">体' + htmlEscape(d.tiYong.tiWuxing) + ' ' + htmlEscape(d.tiYong.tiYongRel) + ' 用' + htmlEscape(d.tiYong.yongWuxing) + '</div>'
    html += '<div class="ti-yong-box yong"><div class="ti-yong-label">用卦（' + htmlEscape(d.tiYong.yongPosition) + '）</div><div class="ti-yong-gua">' + htmlEscape(d.tiYong.yongGua) + '</div><div class="ti-yong-wx">' + htmlEscape(d.tiYong.yongTrigram) + ' <span class="wx-tag ' + wxClass(d.tiYong.yongWuxing) + '">' + htmlEscape(d.tiYong.yongWuxing) + '</span> <span class="ws-tag ' + wsClass(d.tiYong.yongWangshuai) + '">' + htmlEscape(d.tiYong.yongWangshuai) + '</span></div></div>'
    html += '</div><table class="mh-analysis-table"><tr><th>分析项</th><th>关系</th><th>吉凶</th></tr>'
    if (d.tiYong.tiYongJiXiong) html += '<tr><td>体用关系</td><td>体' + htmlEscape(d.tiYong.tiWuxing) + ' ' + htmlEscape(d.tiYong.tiYongRel) + ' 用' + htmlEscape(d.tiYong.yongWuxing) + '</td><td>' + htmlEscape(d.tiYong.tiYongJiXiong) + '</td></tr>'
    if (d.tiYong.tiHuRel) html += '<tr><td>互卦与体</td><td>体' + htmlEscape(d.tiYong.tiWuxing) + ' ' + htmlEscape(d.tiYong.tiHuRel) + ' 互' + htmlEscape(d.tiYong.huWuxing) + '</td><td>-</td></tr>'
    if (d.tiYong.tiBianRel) html += '<tr><td>变卦与体</td><td>体' + htmlEscape(d.tiYong.tiWuxing) + ' ' + htmlEscape(d.tiYong.tiBianRel) + ' 变' + htmlEscape(d.tiYong.bianWuxing) + '</td><td>-</td></tr>'
    html += '</table>'
    if (d.tiYong.verdict) html += '<div class="mh-verdict">' + htmlEscape(d.tiYong.verdict) + '</div>'
    html += '</div>'
  }
  html += '</div>'
  return html
}

function normalizeQimenData(data) {
  return {
    fourPillars: data.fourPillars || data.four_pillars || {},
    palaces: data.palaces || data.gong_pan || [],
    solarDate: pickValue(data, ['solarDate', 'solar_date'], ''),
    panType: pickValue(data, ['panType', 'pan_type'], ''),
    xunKong: data.xunKong || data.xun_kong || data.xunkong || {},
    solarTerm: pickValue(data, ['solarTerm', 'solar_term'], ''),
    ju: data.ju || '',
    xunShou: pickValue(data, ['xunShou', 'xun_shou'], ''),
    zhiFu: pickValue(data, ['zhiFu', 'zhi_fu'], ''),
    zhiShi: pickValue(data, ['zhiShi', 'zhi_shi'], ''),
    zhiFuStar: pickValue(data, ['zhiFuStar', 'zhi_fu_star'], ''),
    zhiShiMen: pickValue(data, ['zhiShiMen', 'zhi_shi_men'], ''),
    zhiFuGong: pickValue(data, ['zhiFuGong', 'zhi_fu_gong'], ''),
    zhiShiGong: pickValue(data, ['zhiShiGong', 'zhi_shi_gong'], ''),
    dayGan: pickValue(data, ['dayGan', 'day_gan'], ''),
    hourGan: pickValue(data, ['hourGan', 'hour_gan'], ''),
    tianYi: pickValue(data, ['tianYi', 'tian_yi'], ''),
    maXing: data.maXing || data.ma_xing || {},
  }
}

function coloredGzInline(value) {
  const text = String(value || '').trim()
  if (!text) return '-'
  return text.split('').map(function(ch) {
    const wx = ganWuxing(ch) || zhiWuxing(ch)
    return '<span class="wx-text-' + wxClass(wx) + '">' + htmlEscape(ch) + '</span>'
  }).join('<span class="qm-gz-gap"></span>')
}

function qimenArrayValue(value) {
  if (Array.isArray(value)) return value.filter(Boolean).join('')
  return value || ''
}

function qimenDizhiGong(zhi) {
  const map = {
    '子': 1,
    '丑': 8,
    '寅': 8,
    '卯': 3,
    '辰': 4,
    '巳': 4,
    '午': 9,
    '未': 2,
    '申': 2,
    '酉': 7,
    '戌': 6,
    '亥': 6,
  }
  return map[String(zhi || '').trim()] || 0
}

function qimenMaGongFromData(maXing) {
  const mx = maXing || {}
  const yima = mx['驛馬'] || mx['驿马'] || mx.yima || mx.yiMa || ''
  return qimenDizhiGong(yima)
}

function renderQimenArtifact(data) {
  const d = normalizeQimenData(data)
  const palaces = d.palaces || []
  const fp = d.fourPillars || {}
  const luoOrder = [4, 9, 2, 3, 5, 7, 8, 1, 6]
  const baguaSimple = { '坎': '坎', '坤': '坤', '震': '震', '巽': '巽', '中': '中', '乾': '乾', '兌': '兑', '兑': '兑', '艮': '艮', '離': '离', '离': '离' }
  const xk = d.xunKong || {}
  const mx = d.maXing || {}
  const fallbackMaGong = qimenMaGongFromData(mx)
  const maList = []
  if (mx['驛馬'] || mx['驿马']) maList.push('驿马->' + (mx['驛馬'] || mx['驿马']))
  if (mx['丁馬'] || mx['丁马']) maList.push('丁马->' + (mx['丁馬'] || mx['丁马']))
  if (mx['天馬'] || mx['天马']) maList.push('天马->' + (mx['天馬'] || mx['天马']))
  let html = '<div class="qm-result-wrap qm-free-layout">'
  html += '<div class="qm-free-summary"><div class="qm-free-title">奇门遁甲排盘</div>'
  html += '<div class="qm-free-line"><span><b>盘式：</b>转盘奇门 · ' + htmlEscape(d.panType || '拆补法') + '</span>'
  if (d.solarDate) html += '<span><b>时间：</b>' + htmlEscape(d.solarDate) + '</span>'
  html += '</div><div class="qm-free-pillars">'
  ;[['年柱', fp.year], ['月柱', fp.month], ['日柱', fp.day], ['时柱', fp.hour]].forEach(function(item) {
    if (item[1]) html += '<span><b>' + htmlEscape(item[0]) + '</b><strong>' + coloredGzInline(item[1]) + '</strong></span>'
  })
  html += '</div>'
  if (xk.day || xk.hour) {
    html += '<div class="qm-free-line"><span><b>旬空：</b>'
    if (xk.day) html += '日空' + htmlEscape(xk.day)
    if (xk.day && xk.hour) html += ' '
    if (xk.hour) html += '时空' + htmlEscape(xk.hour)
    html += '</span></div>'
  }
  html += '<div class="qm-free-line">'
  if (d.solarTerm) html += '<span><b>节气：</b>' + htmlEscape(d.solarTerm) + '</span>'
  if (d.ju) html += '<span><b>局数：</b>' + htmlEscape(d.ju) + '</span>'
  if (d.xunShou) html += '<span><b>旬首：</b>' + htmlEscape(d.xunShou) + '</span>'
  html += '</div><div class="qm-free-line">'
  if (d.zhiFu) html += '<span><b>值符：</b>' + htmlEscape(d.zhiFu) + '</span>'
  if (d.zhiShi) html += '<span><b>值使：</b>' + htmlEscape(d.zhiShi) + '</span>'
  if (d.tianYi) html += '<span><b>天乙：</b>' + htmlEscape(d.tianYi) + '</span>'
  if (maList.length) html += '<span><b>马星：</b>' + htmlEscape(maList.join(' ')) + '</span>'
  html += '</div></div><div class="qm-scale-shell"><div class="qm-nine-grid qm-nine-grid-free">'
  luoOrder.forEach(function(gongNum) {
    const p = palaces[gongNum - 1] || palaces.find(function(x) { return Number(x.gong || x.gong_num || x.number) === gongNum }) || {}
    if (gongNum === 5) {
      const xunMap = { '戊': '甲子', '己': '甲戌', '庚': '甲申', '辛': '甲午', '壬': '甲辰', '癸': '甲寅' }
      const dateStr = String(d.solarDate || '').split(' ')[0]
      html += '<div class="qm-palace center"><div class="qm-center-date">' + htmlEscape(dateStr || '奇门遁甲') + '</div>'
      html += '<div class="qm-center-xun">' + (xunMap[d.xunShou] ? coloredGzInline(xunMap[d.xunShou]) + '旬' : '') + (xk.hour ? ' ' + coloredGzInline(xk.hour) + '空' : '') + '</div>'
      html += '<div class="qm-center-pillars">' + [fp.year, fp.month, fp.day, fp.hour].filter(Boolean).map(coloredGzInline).join(' ') + '</div>'
      html += '<div class="qm-center-title">' + htmlEscape([d.solarTerm, d.ju].filter(Boolean).join(' ')) + '</div>'
      if (d.zhiFu) html += '<div class="qm-center-meta">' + htmlEscape(d.zhiFu) + '</div>'
      if (d.zhiShi) html += '<div class="qm-center-meta">' + htmlEscape(d.zhiShi) + '</div>'
      html += '</div>'
      return
    }
    const shen = pickValue(p, ['shenFull', 'shen_full', 'shen', 'god'], '')
    const xing = qimenArrayValue(p.xingFull || p.xing_full || p.xing || p.star)
    const men = pickValue(p, ['menFull', 'men_full', 'men', 'door'], '')
    const yinGan = pickValue(p, ['yinGan', 'yin_gan'], '')
    const tianGan = qimenArrayValue(p.tianGan || p.tian_gan || p.tianPan || p.tian_pan)
    const diGan = qimenArrayValue(p.diGan || p.di_gan || p.diPan || p.di_pan)
    const bagua = baguaSimple[p.bagua] || p.bagua || ''
    const isMa = !!(p.isMa || p.is_ma || (fallbackMaGong && fallbackMaGong === gongNum))
    html += '<div class="qm-palace">'
    html += '<div class="qm-palace-line"><span class="qm-shen">' + htmlEscape(shen) + (p.isKong ? '<em>○</em>' : '') + '</span><span class="qm-gan">' + (isMa ? '<i class="qm-horse">🐎</i>' : '') + coloredGzInline(tianGan) + '</span></div>'
    html += '<div class="qm-palace-line"><span class="qm-xing' + (xing === d.zhiFuStar ? ' highlight' : '') + '">' + htmlEscape(xing) + '</span><span class="qm-gan di">' + coloredGzInline(diGan) + '</span></div>'
    html += '<div class="qm-palace-line"><span class="qm-men' + (men === d.zhiShiMen ? ' highlight' : '') + (p.isMenPo ? ' menpo' : '') + '">' + htmlEscape(men) + '</span><span class="qm-yingan">' + htmlEscape(yinGan) + '</span></div>'
    html += '<div class="qm-gong-label">' + htmlEscape(gongNum + '·' + bagua) + '</div>'
    html += '</div>'
  })
  html += '</div></div><div class="qm-legend"><span><b class="green">值使</b></span><span><b class="red">门迫</b></span><span><b class="purple">击刑</b></span><span><b class="brown">入墓</b></span><span>○ 空亡</span><span><i class="qm-horse">🐎</i>马星</span></div></div>'
  return html
}

function renderYaoGraphic(isYang) {
  return isYang ? '<div class="ly-yang-bar"></div>' : '<div class="ly-yin-bars"><div class="ly-yin-seg"></div><div class="ly-yin-seg"></div></div>'
}

function liuyaoTrigramBadge(data, natureKey, trigramKey, guaName, fallbackIndex) {
  const nature = data[natureKey] || ''
  const trigram = data[trigramKey] || ''
  if (nature || trigram) return [nature, trigram].filter(Boolean).join(' ')
  const name = String(guaName || '')
  const trigramChar = name.length >= 2 ? name.charAt(fallbackIndex) : ''
  return trigramChar ? trigramChar + '卦' : ''
}

function renderLiuyaoArtifact(data) {
  const details = data.details || data.lines || []
  const bianDetails = data.bian_details || data.changed_details || []
  const benName = data['本卦'] || data.ben_gua || ''
  const bianName = data['变卦'] || data.bian_gua || ''
  const hasBian = !!bianName || bianDetails.length
  const movingCount = details.filter(function(x) { return x && x.is_moving }).length
  const benUpperBadge = liuyaoTrigramBadge(data, 'upper_nature', 'upper_trigram', benName, 0)
  const benLowerBadge = liuyaoTrigramBadge(data, 'lower_nature', 'lower_trigram', benName, 1)
  const bianUpperBadge = liuyaoTrigramBadge(data, 'bian_upper_nature', 'bian_upper_trigram', bianName, 0)
  const bianLowerBadge = liuyaoTrigramBadge(data, 'bian_lower_nature', 'bian_lower_trigram', bianName, 1)
  let html = '<div class="ly-result-wrap"><div class="ly-ben-bian-box">'
  html += '<div class="ly-ben-bian-top"><div class="ly-ben-bian-name-block"><div class="ly-ben-bian-label">本 卦</div><div class="ly-ben-bian-name-text">' + htmlEscape(benName) + '</div><div class="ly-ben-bian-trigrams"><span class="ly-trigram-badge">' + htmlEscape(benUpperBadge) + '</span><span class="ly-trigram-badge">' + htmlEscape(benLowerBadge) + '</span></div></div>'
  if (hasBian) html += '<div class="ly-ben-bian-top-arrow">→</div><div class="ly-ben-bian-name-block"><div class="ly-ben-bian-label">变 卦</div><div class="ly-ben-bian-name-text">' + htmlEscape(bianName) + '</div><div class="ly-ben-bian-trigrams"><span class="ly-trigram-badge">' + htmlEscape(bianUpperBadge) + '</span><span class="ly-trigram-badge">' + htmlEscape(bianLowerBadge) + '</span></div></div>'
  html += '</div><div class="ly-ben-bian-body">'
  for (let i = details.length - 1; i >= 0; i--) {
    const ben = details[i] || {}
    const bian = bianDetails[i] || null
    html += '<div class="ly-paired-row ' + (ben.is_moving ? 'moving' : '') + (bian ? ' has-bian' : ' has-ben-only') + '">'
    html += '<div class="ly-row-ben-side"><div class="ly-visual-side"><div class="ly-yao-tags-left">'
    if (ben.is_shi) html += '<span class="ly-tag ly-tag-shi">世</span>'
    if (ben.is_ying) html += '<span class="ly-tag ly-tag-ying">应</span>'
    if (ben.is_moving) html += '<span class="ly-tag ly-tag-moving">动</span>'
    html += '</div><div class="ly-paired-ben">' + renderYaoGraphic(!!ben.is_yang) + '</div><div class="ly-paired-info">'
    html += '<span class="ly-yao-pos">' + htmlEscape(ben.name || '') + '</span><span class="ly-tag ly-tag-liuqin">' + htmlEscape(ben.liuqin || ben.liu_qin || '') + '</span><span class="ly-tag ly-tag-liushen">' + htmlEscape(ben.liushen || ben.liu_shen || '') + '</span><span class="ly-tag ly-tag-naja">' + htmlEscape(ben.naja || ben.na_jia || '') + '</span></div></div></div>'
    if (bian) {
      html += '<div class="ly-row-divider"></div><div class="ly-row-bian-side"><div class="ly-visual-side"><div class="ly-yao-tags-left">' + (bian.yao_type === '变' ? '<span class="ly-tag ly-tag-bian">变</span>' : '') + '</div><div class="ly-paired-bian">' + renderYaoGraphic(!!bian.is_yang) + '</div><div class="ly-paired-bian-info"><span class="ly-yao-pos">' + htmlEscape(bian.name || ben.name || '') + '</span><span class="ly-tag ly-tag-liuqin">' + htmlEscape(bian.liuqin || bian.liu_qin || '') + '</span><span class="ly-tag ly-tag-liushen">' + htmlEscape(bian.liushen || bian.liu_shen || '') + '</span><span class="ly-tag ly-tag-naja">' + htmlEscape(bian.naja || bian.na_jia || '') + '</span></div></div></div>'
    }
    html += '</div>'
  }
  html += '</div><div class="ly-ben-bian-footer">'
  html += '<span class="ly-ben-bian-meta">宫：' + htmlEscape(data.palace_name || '') + '宫（' + htmlEscape(data.palace_element || '') + '）</span>'
  html += '<span class="ly-ben-bian-meta">日辰：' + htmlEscape(data.day_ganzhi || data.ri_chen || '') + '</span>'
  html += '<span class="ly-ben-bian-meta">月建：' + htmlEscape(data.month_ganzhi || data.yue_jian || '') + '</span>'
  html += '<span class="ly-ben-bian-meta">' + (movingCount ? ('动爻：' + movingCount + '个') : '静卦（无动爻）') + '</span>'
  html += '</div></div>'
  html += '<div class="ly-detail-table-wrap"><table class="ly-detail-table"><tr><th>爻位</th><th>阴阳</th><th>六亲</th><th>六神</th><th>纳甲</th><th>地支五行</th><th>世应</th><th>动</th></tr>'
  for (let i = details.length - 1; i >= 0; i--) {
    const x = details[i] || {}
    html += '<tr class="' + (x.is_moving ? 'moving-row' : '') + '"><td>' + htmlEscape(x.name || '') + '</td><td>' + (x.is_yang ? '⚊ 阳' : '⚋ 阴') + '</td><td>' + htmlEscape(x.liuqin || x.liu_qin || '') + '</td><td>' + htmlEscape(x.liushen || x.liu_shen || '') + '</td><td>' + htmlEscape(x.naja || x.na_jia || '') + '</td><td>' + htmlEscape(x.dizhi_element || '') + '</td><td>' + htmlEscape(x.is_shi ? '世' : x.is_ying ? '应' : '') + '</td><td>' + (x.is_moving ? '⚡ 动' : '') + '</td></tr>'
  }
  html += '</table></div>'
  html += '<div class="ly-paipan-meta"><span>🕐 ' + htmlEscape(data.timestamp || '') + '</span><span>📖 ' + htmlEscape(data.method || '自动摇卦') + '</span>' + (data.question ? '<span>❓ ' + htmlEscape(data.question) + '</span>' : '') + '</div></div>'
  return html
}

function ziweiDecadalStart(palace) {
  const range = palace && palace.decadal && palace.decadal.range
  const start = Array.isArray(range) ? Number(range[0]) : NaN
  return Number.isFinite(start) ? start : 9999
}

function renderZiweiArtifact(data, analysisText) {
  const palaces = (data.twelve_palaces || data.palaces || []).slice(0, 12)
  const order = [4, 3, 5, 6, 2, 'center', 7, 1, 8, 0, 11, 10, 9]
  const starName = function(s) { return typeof s === 'string' ? s : ((s && s.name) || '') }
  const highlights = extractAnalysisHighlights(analysisText)
  const highlightEnabled = readingMode.value === 'deep'
  const wrapHit = function(text) {
    const t = String(text || '')
    if (!highlightEnabled || !t) return htmlEscape(t)
    return highlights.raw.indexOf(t) >= 0 ? '<span class="analysis-hit-star">' + htmlEscape(t) + '</span>' : htmlEscape(t)
  }
  const palaceCell = function(p, idx) {
    if (!p) return '<div class="zw-artifact-palace empty"></div>'
    const major = (p.major_stars || p.stars || []).slice(0, 5).map(starName).filter(Boolean)
    const minor = (p.minor_stars || []).slice(0, 8).map(starName).filter(Boolean)
    const adj = (p.adjective_stars || []).slice(0, 6).map(starName).filter(Boolean)
    const palaceName = p.name || p.palace_name || ''
    const dec = p.decadal || {}
    const decText = dec.range ? ('大限 ' + dec.range[0] + '-' + dec.range[1] + '岁 ' + ((dec.heavenly_stem || '') + (dec.earthly_branch || ''))) : (p.da_xian || '')
    const support = [p.changsheng12, p.boshi12, p.jiangqian12, p.suiqian12].filter(Boolean).join(' · ')
    const ages = (p.ages || []).slice(0, 8).join(',')
    const matched = highlightEnabled && ([palaceName].concat(major, minor, adj).some(function(x) { return x && highlights.raw.indexOf(String(x)) >= 0 }) || (ages && String(ages).split(',').some(function(y) { return highlights.years.has(String(y)) })))
    return '<div class="zw-artifact-palace palace-' + idx + (matched ? ' is-analysis-highlight' : '') + '"><div class="zw-artifact-top"><b>' + htmlEscape(palaceName) + '</b><span>' + htmlEscape(p.ganzhi || p.gan_zhi || ((p.heavenly_stem || '') + (p.earthly_branch || ''))) + '</span></div>' +
      '<div class="zw-artifact-stars major">' + major.map(function(s) { return '<span>' + wrapHit(s) + '</span>' }).join('') + '</div>' +
      '<div class="zw-artifact-stars minor">' + minor.map(function(s) { return '<span>' + wrapHit(s) + '</span>' }).join('') + '</div>' +
      '<div class="zw-artifact-stars adj">' + adj.map(function(s) { return '<span>' + wrapHit(s) + '</span>' }).join('') + '</div>' +
      (support ? '<div class="zw-artifact-support">' + htmlEscape(support) + '</div>' : '') +
      '<div class="zw-artifact-foot"><span>' + htmlEscape(decText) + '</span><strong>' + htmlEscape((p.is_body_palace || p.body_palace) ? '身宫' : '') + '</strong></div>' +
      (ages ? '<div class="zw-artifact-ages">流年:' + htmlEscape(ages) + '</div>' : '') +
      '</div>'
  }
  const cells = order.map(function(idx) {
    if (idx === 'center') {
      const bi = data.basic_info || {}
      const cp = data.core_palace || {}
      const meta = data.display_meta || {}
      return '<div class="zw-artifact-center"><span class="zw-center-kicker">三合盘</span><b>紫微斗数命盘</b><span>' + htmlEscape([(meta.gender_yinyang || data.gender), bi.five_elements_class || data.wuxingju || data.five_element_class].filter(Boolean).join(' · ')) + '</span><em>北京时间 ' + htmlEscape(meta.beijing_time || bi.solar_date || data.birth_time || '') + '</em><em>真太阳时 ' + htmlEscape(meta.true_solar_time || '') + '</em><em>农历 ' + htmlEscape(bi.lunar_date || data.lunar_date || '') + '</em><em>节气四柱 ' + htmlEscape(bi.chinese_date || '') + '</em><em>' + htmlEscape([cp.soul_star && ('命主 ' + cp.soul_star), cp.body_star && ('身主 ' + cp.body_star)].filter(Boolean).join('  ')) + '</em></div>'
    }
    return palaceCell(palaces[idx], idx)
  }).join('')
  const timeline = palaces.filter(function(p) { return p && p.decadal && p.decadal.range }).sort(function(a, b) {
    return ziweiDecadalStart(a) - ziweiDecadalStart(b)
  }).map(function(p) {
    const r = p.decadal.range || []
    const label = r[0] + '-' + r[1]
    const matched = highlightEnabled && (highlights.raw.indexOf(label) >= 0 || highlights.raw.indexOf(String(p.name || '')) >= 0)
    return '<span class="zw-flow-item' + (matched ? ' is-analysis-highlight' : '') + '"><b>' + htmlEscape(label) + '</b><em>' + htmlEscape((p.decadal.heavenly_stem || '') + (p.decadal.earthly_branch || '')) + '</em><i>' + htmlEscape(p.name || '') + '</i></span>'
  }).join('')
  return '<div class="zw-artifact-wrap"><div class="zw-orientation">正南方</div><div class="zw-artifact-grid">' + cells + '</div><div class="zw-orientation">正北方</div><div class="zw-flow-row"><div class="zw-flow-title">大限</div><div class="zw-flow-scroll">' + timeline + '</div></div></div>'
}

const HOME_TAROT_IMAGE_BASE_URL = '/static/tarot/rws/'
const HOME_TAROT_MAJOR_NAMES = ['愚者', '魔术师', '女祭司', '皇后', '皇帝', '教皇', '恋人', '战车', '力量', '隐士', '命运之轮', '正义', '倒吊人', '死神', '节制', '恶魔', '塔', '星星', '月亮', '太阳', '审判', '世界']
const HOME_TAROT_MINOR_PREFIX = { '权杖': 'w', '圣杯': 'c', '宝剑': 's', '星币': 'p' }
const HOME_TAROT_MINOR_INDEX = { 'Ace': 1, 'A': 1, '一': 1, '1': 1, '二': 2, '2': 2, '三': 3, '3': 3, '四': 4, '4': 4, '五': 5, '5': 5, '六': 6, '6': 6, '七': 7, '7': 7, '八': 8, '8': 8, '九': 9, '9': 9, '十': 10, '10': 10, '侍卫': 11, 'Page': 11, '骑士': 12, 'Knight': 12, '王后': 13, 'Queen': 13, '国王': 14, 'King': 14 }

function inferHomeTarotImageKey(card) {
  const c = card || {}
  if (c.image_key) return c.image_key
  if (c.type === 'major' && typeof c.id === 'number') return 'm' + String(c.id).padStart(2, '0') + '.jpg'
  const name = String(c.name || '')
  const majorIdx = HOME_TAROT_MAJOR_NAMES.indexOf(name)
  if (majorIdx >= 0) return 'm' + String(majorIdx).padStart(2, '0') + '.jpg'
  const suit = c.suit || Object.keys(HOME_TAROT_MINOR_PREFIX).find(function(item) { return name.indexOf(item) === 0 })
  const prefix = HOME_TAROT_MINOR_PREFIX[suit]
  const numberText = c.number || (suit ? name.replace(suit, '') : '')
  const idx = HOME_TAROT_MINOR_INDEX[numberText]
  if (prefix && idx) return prefix + String(idx).padStart(2, '0') + '.jpg'
  return ''
}

function getHomeTarotImage(card) {
  if (card && card.image_url) return card.image_url
  const key = inferHomeTarotImageKey(card)
  return key ? HOME_TAROT_IMAGE_BASE_URL + key : ''
}

function renderTarotArtifact(data) {
  const cards = (data.cards || []).map(function(c, i) {
    const orientationClass = c.is_reversed ? 'reversed' : 'upright'
    const keyword = c.is_reversed && c.keyword_reversed ? c.keyword_reversed : (c.keyword || '')
    const imageUrl = getHomeTarotImage(c)
    const imageKey = inferHomeTarotImageKey(c)
    const imageClass = 'tarot-card-img' + (c.is_reversed ? ' tarot-card-img-reversed' : '')
    const cardNum = c.type === 'major' ? (typeof c.id === 'number' ? c.id : '') : (c.number || '')
    return '<div class="tarot-card-slot" style="animation: tarotCardAppear 0.5s ' + (i * 0.12) + 's both">' +
      '<div class="tarot-card-flipper flipped">' +
        '<div class="tarot-card-back"><div class="tarot-card-back-pattern"></div><span class="tarot-card-back-symbol">✦</span></div>' +
        '<div class="tarot-card-front">' +
          '<div class="tarot-card-art-wrap"><img class="' + imageClass + '" src="' + htmlEscape(imageUrl) + '" alt="' + htmlEscape([c.name, c.name_en, c.orientation].filter(Boolean).join(' / ')) + '" loading="lazy" data-image-key="' + htmlEscape(imageKey) + '" onerror="this.closest && this.closest(\'.tarot-card-front\').classList.add(\'image-failed\')"><div class="tarot-card-fallback"><div class="tarot-card-num">' + htmlEscape(cardNum) + '</div><div class="tarot-card-name">' + htmlEscape(c.name || '') + '</div><div class="tarot-card-name-en">' + htmlEscape(c.name_en || '') + '</div><div class="tarot-card-keyword">' + htmlEscape(keyword) + '</div></div></div>' +
          '<div class="tarot-card-name tarot-card-name-below">' + htmlEscape(c.name || '') + '</div>' +
          '<div class="tarot-card-name-en">' + htmlEscape(c.name_en || '') + '</div>' +
          '<div class="tarot-card-orientation ' + orientationClass + '">' + htmlEscape(c.orientation || '') + '</div>' +
          '<div class="tarot-card-keyword tarot-card-keyword-below">' + htmlEscape(keyword) + '</div>' +
        '</div>' +
      '</div>' +
      '<div class="tarot-card-position"><div class="tarot-card-position-name">' + htmlEscape(c.position_name || c.position || '') + '</div><div class="tarot-card-position-meaning">' + htmlEscape(c.position_meaning || '') + '</div>' + (c.is_reversed ? '<div class="tarot-card-reversed-hint">逆位</div>' : '') + '</div>' +
    '</div>'
  }).join('')
  const count = (data.cards || []).length
  return '<div class="tarot-artifact-wrap"><div class="tarot-drawing-text">✦ 塔罗抽牌结果 ✦</div><div class="tarot-cards-display" data-count="' + htmlEscape(count) + '">' + cards + '</div></div>'
}

function renderZejiArtifact(data) {
  const days = (data.best_days || data.days || []).slice(0, 8).map(function(d) {
    return '<div class="artifact-line"><span>' + htmlEscape(d.date || '') + '</span><strong>' + htmlEscape((d.score || '') + ' ' + (d.jian_chu || d.zhi_shen || '')) + '</strong></div>'
  }).join('')
  return '<div class="artifact-panel"><div class="artifact-line-list">' + days + '</div></div>'
}

function cachedArtifactHtml(artifact, cacheKey, render) {
  const data = artifact && artifact.data
  if (!data || typeof data !== 'object') return render()
  const current = artifactHtmlCache.get(data) || {}
  if (current[cacheKey]) return current[cacheKey]
  const html = render()
  artifactHtmlCache.set(data, Object.assign({}, current, { [cacheKey]: html }))
  return html
}

function renderArtifactHtml(artifact) {
  const data = artifact && artifact.data ? artifact.data : {}
  if (artifact.key === 'bazi.basic') return cachedArtifactHtml(artifact, 'bazi.basic', function() { return renderBaziBasicArtifact(data) })
  if (artifact.key === 'bazi.yun') return cachedArtifactHtml(artifact, 'bazi.yun', function() { return renderBaziYunArtifact(data, '') })
  if (artifact.key === 'qimen.pan') return cachedArtifactHtml(artifact, 'qimen.pan', function() { return renderQimenArtifact(data) })
  if (artifact.key === 'liuyao.pan') return cachedArtifactHtml(artifact, 'liuyao.pan', function() { return renderLiuyaoArtifact(data) })
  if (artifact.key === 'meihua.pan') return cachedArtifactHtml(artifact, 'meihua.pan', function() { return renderMeihuaArtifact(data) })
  if (artifact.key === 'ziwei.pan') return cachedArtifactHtml(artifact, 'ziwei.pan', function() { return renderZiweiArtifact(data, '') })
  if (artifact.key === 'tarot.cards') return cachedArtifactHtml(artifact, 'tarot.cards', function() { return renderTarotArtifact(data) })
  if (artifact.key === 'zeji.days') return cachedArtifactHtml(artifact, 'zeji.days', function() { return renderZejiArtifact(data) })
  return '<div class="artifact-panel"><pre>' + htmlEscape(JSON.stringify(data, null, 2)) + '</pre></div>'
}

function toggleArtifact(messageIndex, artifactKey) {
  const msg = comprehensiveMessages.value[messageIndex]
  if (!msg || !msg.artifacts) return
  let nextCollapsed = false
  comprehensiveMessages.value[messageIndex] = Object.assign({}, msg, {
    artifacts: msg.artifacts.map(function(artifact) {
      if (artifact.key !== artifactKey) return artifact
      nextCollapsed = !artifact.collapsed
      return Object.assign({}, artifact, { collapsed: nextCollapsed })
    })
  })
  saveArtifactCollapsed(artifactKey, nextCollapsed)
}

function normalizeMessageHistory() {
  return comprehensiveMessages.value
    .filter(m => m && (m.role === 'user' || m.role === 'assistant') && m.content)
    .map(m => ({ role: m.role, content: m.content }))
}

function comprehensiveDraftPayload() {
  syncActiveComprehensiveStreamText()
  return {
    updatedAt: Date.now(),
    conversationId: currentComprehensiveConvId.value || null,
    messages: comprehensiveMessages.value || [],
    paipan: currentPaipanContext.value || {},
    artifacts: currentArtifacts.value || {},
    selectedProfiles: [],
    selectedToolModels: [],
    autoSelectTools: false,
    llmModelId: selectedLlmModel.value.id || 'basic',
    readingMode: readingMode.value,
    activeArtifacts: Object.assign({}, activeArtifactKeyByMessage),
    loading: !!comprehensiveLoading.value,
  }
}

function applyComprehensiveDraft(draft) {
    currentComprehensiveConvId.value = draft.conversationId || null
    currentPaipanContext.value = draft.paipan || {}
    currentArtifacts.value = draft.artifacts || {}
    selectedProfiles.value = []
    draftSelectedProfiles.value = []
    profileSelectionConfirmed.value = false
    selectedToolModels.value = []
    autoSelectTools.value = false
    if (draft.readingMode) readingMode.value = draft.readingMode
    const mid = draft.llmModelId || 'basic'
    const mi = llmModels.value.findIndex(m => m.id === mid)
    if (mi >= 0) llmModelIdx.value = mi
    comprehensiveMessages.value = draft.messages.map(function(msg) {
      if (!msg || msg.role !== 'assistant') return msg
      if (msg.stage && draft.loading) {
        return Object.assign({}, msg, {
          stage: '',
          content: msg.content || '上次解读在刷新时中断，已恢复已生成内容；可以继续追问或重新发送。',
        })
      }
      return Object.assign({}, msg, { stage: '' })
    })
    Object.keys(activeArtifactKeyByMessage).forEach(function(key) { delete activeArtifactKeyByMessage[key] })
    Object.assign(activeArtifactKeyByMessage, draft.activeArtifacts || {})
    comprehensiveMessages.value.forEach(function(message, index) {
      ensureActiveArtifact(index, visibleArtifactList(message))
      if (message && message.role === 'assistant' && message.content && visibleArtifactList(message).length && !activeArtifactKeyByMessage[index]) {
        setActiveArtifact(index, '__summary__')
      }
    })
    comprehensiveLoading.value = false
    shouldAutoFollowChat.value = true
    scrollComprehensiveChatToBottom('auto', true)
    return true
}

const comprehensiveDraftStorage = createHomeAiDraftStorage({
  storageKey: comprehensiveDraftStorageKey,
  saveDelayMs: COMPREHENSIVE_DRAFT_SAVE_MS,
  maxAgeMs: COMPREHENSIVE_DRAFT_MAX_AGE_MS,
  getPayload: comprehensiveDraftPayload,
  canRestore: function() {
    return !pendingComprehensiveId && !comprehensiveMessages.value.length
  },
  applyDraft: applyComprehensiveDraft,
})

function saveComprehensiveDraftNow() {
  comprehensiveDraftStorage.saveNow()
}

function scheduleComprehensiveDraftSave() {
  // #ifdef H5
  comprehensiveDraftStorage.scheduleSave()
  // #endif
}

function clearComprehensiveDraft() {
  comprehensiveDraftStorage.clearDraft()
}

function restoreComprehensiveDraft() {
  // #ifdef H5
  return comprehensiveDraftStorage.restoreDraft()
  // #endif
  return false
}

function stopComprehensiveProgressTimer() {
  if (comprehensiveProgressTimer) {
    clearInterval(comprehensiveProgressTimer)
    comprehensiveProgressTimer = null
  }
}

function stopComprehensiveTypeTimer() {
  if (comprehensiveTypeTimer) {
    clearInterval(comprehensiveTypeTimer)
    comprehensiveTypeTimer = null
  }
  // #ifdef H5
  if (comprehensiveTypeFrame) {
    cancelAnimationFrame(comprehensiveTypeFrame)
    comprehensiveTypeFrame = null
  }
  // #endif
}

function syncActiveComprehensiveStreamText() {
  Object.keys(comprehensiveTypeStates).forEach(function(key) {
    const aiIndex = Number(key)
    const state = comprehensiveTypeStates[key]
    const msg = comprehensiveMessages.value[aiIndex]
    if (!state || !msg) return
    const displayText = stripComprehensiveMarkdown(state.displayed || '')
    if (displayText && msg.content !== displayText) msg.content = displayText
  })
}

function saveComprehensiveDraftForUnload() {
  syncActiveComprehensiveStreamText()
  saveComprehensiveDraftNow()
}

function onHomeVisibilityChange() {
  // #ifdef H5
  if (document.visibilityState === 'hidden') saveComprehensiveDraftForUnload()
  // #endif
}

function stripComprehensiveMarkdown(text) {
  return sanitizeArtifactAnalysisText(text)
}

function comprehensiveSummaryOnly(text) {
  const raw = String(text || '')
  const markers = ['【综合合参总结】', '综合合参总结：', '综合合参总结']
  for (let i = 0; i < markers.length; i += 1) {
    const idx = raw.lastIndexOf(markers[i])
    if (idx >= 0) return raw.slice(idx + markers[i].length).trim()
  }
  return raw.trim()
}

function scheduleComprehensiveAssistantUpdate(aiIndex, patch, options) {
  const opts = options || {}
  const shouldFollow = Object.prototype.hasOwnProperty.call(opts, 'shouldFollow')
    ? !!opts.shouldFollow
    : shouldAutoFollowChat.value && isComprehensiveChatNearBottom()
  if (comprehensivePendingAssistantUpdate && comprehensivePendingAssistantUpdate.aiIndex !== aiIndex) {
    flushComprehensiveAssistantUpdate()
  }
  const previous = comprehensivePendingAssistantUpdate || { aiIndex, patch: {}, shouldFollow: false }
  comprehensivePendingAssistantUpdate = {
    aiIndex,
    patch: Object.assign({}, previous.patch, patch),
    shouldFollow: previous.shouldFollow || shouldFollow,
  }
  // #ifdef H5
  if (!comprehensiveRenderFrame) {
    comprehensiveRenderFrame = requestAnimationFrame(function() {
      comprehensiveRenderFrame = null
      flushComprehensiveAssistantUpdate()
    })
  }
  // #endif
  // #ifndef H5
  flushComprehensiveAssistantUpdate()
  // #endif
}

function flushComprehensiveAssistantUpdate() {
  // #ifdef H5
  if (comprehensiveRenderFrame) {
    cancelAnimationFrame(comprehensiveRenderFrame)
    comprehensiveRenderFrame = null
  }
  // #endif
  if (!comprehensivePendingAssistantUpdate) return
  const pending = comprehensivePendingAssistantUpdate
  comprehensivePendingAssistantUpdate = null
  updateComprehensiveAssistant(pending.aiIndex, pending.patch, {
    shouldFollow: pending.shouldFollow,
  })
}

function stopComprehensiveAssistantUpdateQueue() {
  // #ifdef H5
  if (comprehensiveRenderFrame) cancelAnimationFrame(comprehensiveRenderFrame)
  comprehensiveRenderFrame = null
  // #endif
  comprehensivePendingAssistantUpdate = null
}

function flushComprehensiveTypewriter(aiIndex, state) {
  if (!state || !state.queue) return
  state.displayed += state.queue
  state.queue = ''
  paintComprehensiveStreamText(aiIndex, stripComprehensiveMarkdown(state.displayed))
  scheduleComprehensiveAssistantUpdate(aiIndex, {
    stage: '',
    content: stripComprehensiveMarkdown(state.displayed),
    _streaming: false,
  })
  flushComprehensiveAssistantUpdate()
}

function finishComprehensiveAnswer(aiIndex, state) {
  flushPendingArtifactAnalyses()
  if (state) {
    state.done = true
    startComprehensiveTypewriter(aiIndex, state)
  }
  scheduleComprehensiveAssistantUpdate(aiIndex, { stage: '' })
  setActiveArtifact(aiIndex, '__summary__')
  stopComprehensiveProgressTimer()
  scheduleComprehensiveDraftSave()
  try { window.__sidebarCache = null } catch(_) {}
}

function getComprehensiveStreamTextElement(aiIndex) {
  // #ifdef H5
  try {
    return document.querySelector('[data-home-ai-stream-key="summary-' + aiIndex + '"]')
  } catch (_) {
    return null
  }
  // #endif
  return null
}

function paintComprehensiveStreamText(aiIndex, text) {
  // #ifdef H5
  const target = getComprehensiveStreamTextElement(aiIndex)
  if (target) target.textContent = text || ''
  // #endif
}

function repaintComprehensiveStreamText(aiIndex) {
  // #ifdef H5
  const state = comprehensiveTypeStates[String(aiIndex)]
  if (!state || !state.displayed) return
  requestAnimationFrame(function() {
    paintComprehensiveStreamText(aiIndex, stripComprehensiveMarkdown(state.displayed))
  })
  // #endif
}

function startComprehensiveTypewriter(aiIndex, state) {
  comprehensiveTypeStates[String(aiIndex)] = state
  if (comprehensiveTypeFrame || comprehensiveTypeTimer) return
  const tick = function(now) {
    comprehensiveTypeFrame = null
    const current = comprehensiveMessages.value[aiIndex]
    if (!current) {
      stopComprehensiveTypeTimer()
      return
    }
    if (!state.started) {
      state.started = true
      state.lastReactiveSyncAt = now
      updateComprehensiveAssistant(aiIndex, { stage: '', _streaming: true }, {
        shouldFollow: shouldAutoFollowChat.value && isComprehensiveChatNearBottom()
      })
      comprehensiveTypeFrame = requestAnimationFrame(tick)
      return
    }
    if (!state.queue.length) {
      if (state.done) {
        scheduleComprehensiveAssistantUpdate(aiIndex, {
          stage: '',
          content: stripComprehensiveMarkdown(state.displayed),
          _streaming: false,
        })
        stopComprehensiveTypeTimer()
        delete comprehensiveTypeStates[String(aiIndex)]
      }
      else comprehensiveTypeFrame = requestAnimationFrame(tick)
      return
    }
    const lastAt = state.lastTypeAt || now
    const elapsed = Math.max(COMPREHENSIVE_TYPE_FRAME_MS, Math.min(48, now - lastAt))
    state.lastTypeAt = now
    state.charBudget = (state.charBudget || 0) + (elapsed / 1000) * smoothTextSpeed(state.queue.length)
    const nextChunk = takeSmoothTextChunk(state.queue, Math.floor(state.charBudget), COMPREHENSIVE_TYPE_MAX_FRAME_CHARS)
    if (!nextChunk.chunk) {
      comprehensiveTypeFrame = requestAnimationFrame(tick)
      return
    }
    state.charBudget = Math.max(0, (state.charBudget || 0) - nextChunk.count)
    state.displayed += nextChunk.chunk
    state.queue = nextChunk.rest
    const displayText = stripComprehensiveMarkdown(state.displayed)
    paintComprehensiveStreamText(aiIndex, displayText)
    if (shouldSyncStreamContent(now, state.lastReactiveSyncAt || 0, COMPREHENSIVE_REACTIVE_SYNC_MS, state.done && !state.queue.length)) {
      state.lastReactiveSyncAt = now
      scheduleComprehensiveAssistantUpdate(aiIndex, {
        stage: '',
        content: displayText,
        _streaming: !state.done || !!state.queue.length,
      })
    }
    comprehensiveTypeFrame = requestAnimationFrame(tick)
  }
  comprehensiveTypeFrame = requestAnimationFrame(tick)
}

function updateComprehensiveAssistant(aiIndex, patch, options) {
  const current = comprehensiveMessages.value[aiIndex]
  if (!current) return null
  const opts = options || {}
  const shouldFollow = Object.prototype.hasOwnProperty.call(opts, 'shouldFollow')
    ? !!opts.shouldFollow
    : shouldAutoFollowChat.value && isComprehensiveChatNearBottom()
  Object.keys(patch || {}).forEach(function(key) {
    current[key] = patch[key]
  })
  if (patch.artifacts) {
    ensureActiveArtifact(aiIndex, visibleArtifactList(current))
  }
  if ((current.content || current._streaming) && !activeArtifactKeyByMessage[aiIndex]) {
    setActiveArtifact(aiIndex, '__summary__')
  }
  scheduleComprehensiveDraftSave()
  if (comprehensiveMessages.value.length && (patch.content || patch.stage || patch.artifacts || patch._streaming) && shouldFollow) {
    scrollComprehensiveChatToBottom('auto')
  }
  if (current._streaming && comprehensiveTypeStates[String(aiIndex)] && !Object.prototype.hasOwnProperty.call(patch || {}, 'content')) {
    repaintComprehensiveStreamText(aiIndex)
  }
  return current
}

function startComprehensiveProgressTimer(aiIndex) {
  stopComprehensiveProgressTimer()
  const startedAt = Date.now()
  let localIndex = 0
  const localStages = [
    '正在连接综合解读服务',
    '正在读取命盘与排盘记录',
    '正在核对所选命盘和术数',
    '正在生成所选术数盘面',
    '正在整理盘面重点',
    '正在组织综合解读思路',
    '模型正在生成回答，请保持当前页面',
  ]
  updateComprehensiveAssistant(aiIndex, { _lastServerStageAt: startedAt })
  comprehensiveProgressTimer = setInterval(function() {
    const current = comprehensiveMessages.value[aiIndex]
    if (!comprehensiveLoading.value || !current || current.content) {
      stopComprehensiveProgressTimer()
      return
    }
    const elapsed = Math.max(1, Math.floor((Date.now() - startedAt) / 1000))
    const idleMs = Date.now() - (current._lastServerStageAt || startedAt)
    if (idleMs >= 2600) {
      scheduleComprehensiveAssistantUpdate(aiIndex, {
        stage: localStages[Math.min(localIndex, localStages.length - 1)] + ' · 已等待 ' + elapsed + ' 秒'
      })
      localIndex += 1
    } else if (current.stage && elapsed >= 4 && current.stage.indexOf('已等待') < 0) {
      scheduleComprehensiveAssistantUpdate(aiIndex, {
        stage: current.stage.replace(/ · \d+ 秒$/, '') + ' · ' + elapsed + ' 秒'
      })
    }
  }, 1200)
}

function disableQuestionGuidance() {
  questionGuidanceEnabled.value = false
  writeStorageJson(currentUserScopedStorageKey(questionGuidanceEnabledStorageKey), false)
  uni.showToast({ title: '已关闭问事引导，可在设置中开启', icon: 'none' })
}

function resetQuestionGuide(question) {
  questionGuideDraft.question = question
  questionGuideDraft.finalQuestion = ''
  questionGuideInput.value = ''
  questionGuideSkill.value = ''
  questionGuideOptions.value = []
  questionGuideMessages.value = []
  questionGuideInChat.value = false
  pendingGuideRecommendation.value = null
  questionGuideLoadingMessageIndex = -1
}

function closeQuestionGuide() {
  questionGuideOpen.value = false
  questionGuideInput.value = ''
  questionGuideLoading.value = false
}

function showQuestionGuideLoadingMessage(text) {
  const message = {
    role: 'assistant',
    content: '',
    stage: '',
    _streaming: true,
    isGuide: true,
    guideLoading: true,
    guideLoadingText: text || '正在理清所问',
  }
  comprehensiveMessages.value.push(message)
  questionGuideLoadingMessageIndex = comprehensiveMessages.value.length - 1
  shouldAutoFollowChat.value = true
  scrollComprehensiveChatToBottom('smooth', true)
}

function resolveQuestionGuideLoadingMessage(patch) {
  const idx = questionGuideLoadingMessageIndex
  questionGuideLoadingMessageIndex = -1
  const next = Object.assign({
    role: 'assistant',
    content: '',
    stage: '',
    _streaming: false,
    isGuide: true,
    guideLoading: false,
    guideLoadingText: '',
  }, patch || {})
  if (idx >= 0 && comprehensiveMessages.value[idx] && comprehensiveMessages.value[idx].guideLoading) {
    comprehensiveMessages.value.splice(idx, 1, Object.assign({}, comprehensiveMessages.value[idx], next))
  } else {
    comprehensiveMessages.value.push(next)
  }
  shouldAutoFollowChat.value = true
  scrollComprehensiveChatToBottom('smooth', true)
}

async function openQuestionGuide(question) {
  resetQuestionGuide(question)
  questionGuideInChat.value = true
  comprehensiveMessages.value.push({ role: 'user', content: question, isGuide: true })
  comprehensiveQuestion.value = ''
  shouldAutoFollowChat.value = true
  scrollComprehensiveChatToBottom('smooth', true)
  await requestQuestionGuidance()
}

async function submitQuestionGuideAnswer(answer) {
  if (questionGuideLoading.value) return
  const content = String(answer || comprehensiveQuestion.value || questionGuideInput.value || '').trim()
  if (!content) return uni.showToast({ title: '先补充一句，或点一个方向', icon: 'none' })
  questionGuideMessages.value.push({ role: 'user', content })
  comprehensiveMessages.value.push({ role: 'user', content, isGuide: true })
  comprehensiveQuestion.value = ''
  questionGuideInput.value = ''
  shouldAutoFollowChat.value = true
  scrollComprehensiveChatToBottom('smooth', true)
  await requestQuestionGuidance()
}

async function requestQuestionGuidance() {
  questionGuideLoading.value = true
  questionGuideOptions.value = []
  showQuestionGuideLoadingMessage('正在理清所问')
  try {
    const response = await uni.request({
      url: '/api/comprehensive/guide',
      method: 'POST',
      data: {
        question: questionGuideDraft.question,
        messages: questionGuideMessages.value,
        llm_model: selectedLlmModel.value.id || 'basic',
        reading_mode: selectedReadingMode.value.id || 'standard',
        profile_count: Math.max(1, selectedProfiles.value.length),
      }
    })
    const d = response.data || {}
    if (response.statusCode && response.statusCode >= 400) {
      throw new Error(d.error || 'AI 引导服务暂不可用')
    }
    if (d.status === 'error') {
      throw new Error(d.error || 'AI 引导服务暂不可用')
    }
    questionGuideSkill.value = d.skill || questionGuideSkill.value || '先理清所问'
    if (d.status === 'recommend') {
      await applyGuidedRecommendation(d)
      return
    }
    const assistantMessage = d.assistant_message || '我再确认一个关键点，再为你择法。'
    questionGuideMessages.value.push({ role: 'assistant', content: assistantMessage })
    questionGuideOptions.value = Array.isArray(d.options) ? d.options : []
    resolveQuestionGuideLoadingMessage({
      content: assistantMessage,
      stage: '',
      guideOptions: questionGuideOptions.value.slice(),
    })
  } catch (_) {
    resolveQuestionGuideLoadingMessage({
      content: '时安问事引导暂时不可用，请稍后再试。',
      stage: '',
    })
  } finally {
    questionGuideLoading.value = false
  }
}

async function applyGuidedRecommendation(data) {
  const finalQuestion = data.final_question || questionGuideDraft.question
  questionGuideDraft.finalQuestion = finalQuestion
  comprehensiveQuestion.value = ''
  const recommendation = {
    final_question: finalQuestion,
    tool_models: Array.isArray(data.tool_models) ? data.tool_models : [],
    reason: data.reason || '',
  }
  pendingGuideRecommendation.value = recommendation
  questionGuideInChat.value = false
  questionGuideLoading.value = false
  toolRecommendReason.value = recommendation.reason
  resolveQuestionGuideLoadingMessage({
    content: recommendation.reason || '我已根据你的回答整理好所问，并推荐了适合的术数。',
    stage: '',
    guideRecommendation: recommendation,
  })
}

function toolSummaryForIds(ids) {
  const names = toolModels.value.filter(t => (ids || []).includes(t.id)).map(t => t.name)
  if (!names.length) return '暂未选择'
  if (names.length <= 2) return names.join(' + ')
  return names.slice(0, 2).join(' + ') + ' 等' + names.length + '项'
}

function toolsNeedProfile(ids) {
  const selected = ids || selectedToolModels.value || []
  return toolModels.value.some(t => selected.includes(t.id) && t.needs_profile)
}

function selectedToolsNeedProfile() {
  return toolsNeedProfile(selectedToolModels.value)
}

function profileBirthDigits(profile) {
  return String((profile && (profile.birthTime || profile.birth_time)) || '').replace(/\D/g, '')
}

function isPlaceholderProfileName(name) {
  const text = String(name || '').trim()
  return !text || text === '未命名' || text === '默认'
}

function profileNeedsBirthCompletion(profile) {
  if (!profile) return true
  const meta = profile.meta || {}
  if (profileHasUnknownBirthTime(profile)) return true
  if (profileBirthDigits(profile).length < 12) return true
  if (meta && meta.requiresBirthConfirmation) return true
  return false
}

function selectedProfilesNeedBirthCompletion() {
  if (!selectedToolsNeedProfile()) return false
  return !profileSelectionConfirmed.value || !selectedProfiles.value.length || selectedProfiles.value.some(profileNeedsBirthCompletion)
}

function openBirthProfileCompletion() {
  draftSelectedProfiles.value = selectedProfiles.value.slice()
  profileQuickFormOpen.value = true
  loadQuickCityData()
  openProfilePicker()
}

function ensureSelectedProfilesReadyForTools(message) {
  if (!selectedProfilesNeedBirthCompletion()) return true
  uni.showToast({ title: message || '请先填写出生信息', icon: 'none' })
  openBirthProfileCompletion()
  return false
}

function guideRecommendationReady(recommendation) {
  const tools = recommendation && Array.isArray(recommendation.tool_models) ? recommendation.tool_models : []
  if (!toolsNeedProfile(tools)) return true
  return !!profileSelectionConfirmed.value && !!selectedProfiles.value.length && !selectedProfiles.value.some(profileNeedsBirthCompletion)
}

async function applyGuideRecommendationFromMessage(recommendation, message) {
  const tools = recommendation && Array.isArray(recommendation.tool_models) ? recommendation.tool_models : []
  if (!tools.length) return uni.showToast({ title: '暂无可选择的术数', icon: 'none' })
  if (message) message.guideApplying = true
  await new Promise(function(resolve) { setTimeout(resolve, 420) })
  selectedToolModels.value = tools
  autoSelectTools.value = false
  saveSelectedToolModels()
  if (recommendation.final_question) {
    questionGuideDraft.finalQuestion = recommendation.final_question
  }
  comprehensiveQuestion.value = ''
  writeStorageJson(currentUserScopedStorageKey(questionGuidanceEnabledStorageKey), !!questionGuidanceEnabled.value)
  if (recommendation) recommendation.applied = true
  if (message) message.guideApplying = false
  if (toolsNeedProfile(tools) && !ensureSelectedProfilesReadyForTools('已勾选术数，请先填写出生信息')) {
    return
  }
  uni.showToast({ title: '已一键选择术数，点击开始解读', icon: 'none' })
}

function startGuidedRecommendationReading(recommendation) {
  const tools = recommendation && Array.isArray(recommendation.tool_models) ? recommendation.tool_models : []
  if (tools.length) {
    selectedToolModels.value = tools
    autoSelectTools.value = false
    saveSelectedToolModels()
  }
  if (!ensureSelectedProfilesReadyForTools('所选术数需要出生信息，请先填写命盘')) return
  const finalQuestion = (recommendation && recommendation.final_question) || questionGuideDraft.finalQuestion || questionGuideDraft.question
  comprehensiveQuestion.value = ''
  startComprehensiveAsk(finalQuestion)
}

function confirmToolRecommendation() {
  toolRecommendOpen.value = true
  return new Promise(function(resolve) {
    pendingToolRecommendResolve = resolve
  })
}

function resolveToolRecommendation(ok) {
  toolRecommendOpen.value = false
  if (pendingToolRecommendResolve) {
    pendingToolRecommendResolve(!!ok)
    pendingToolRecommendResolve = null
  }
}

function selectHomeQuestionTemplate(item) {
  if (!item || comprehensiveLoading.value) return
  comprehensiveQuestion.value = item.question || ''
  try {
    const input = document.querySelector('.home-ai-input')
    if (input && typeof input.focus === 'function') input.focus()
  } catch (_) {}
}

async function startComprehensiveAsk(forcedQuestion) {
  if (comprehensiveLoading.value) return
  if (!isLoggedIn.value) return uni.showToast({ title: '请先登录', icon: 'none' })
  const question = (typeof forcedQuestion === 'string' ? forcedQuestion : comprehensiveQuestion.value).trim()
  if (!question) return uni.showToast({ title: '请输入问题', icon: 'none' })
  if (questionGuideInChat.value) {
    submitQuestionGuideAnswer(question)
    return
  }
  if (questionGuidanceEnabled.value && !comprehensiveMessages.value.length && questionGuideDraft.finalQuestion !== question) {
    openQuestionGuide(question)
    return
  }
  if (!ensureSelectedProfilesReadyForTools('所选术数需要出生信息，请先填写命盘')) return
  if (!autoSelectTools.value && !selectedToolModels.value.length) return uni.showToast({ title: '请至少选择一个术数模型', icon: 'none' })
  if (autoSelectTools.value && !comprehensiveMessages.value.length) {
    try {
      const rec = await uni.request({
        url: '/api/comprehensive/recommend-tools',
        method: 'POST',
        data: { question, llm_model: selectedLlmModel.value.id || 'basic', reading_mode: selectedReadingMode.value.id || 'standard', profile_count: Math.max(1, selectedProfiles.value.length) }
      })
      const d = rec.data || {}
      if (Array.isArray(d.tool_models) && d.tool_models.length) selectedToolModels.value = d.tool_models
    } catch (_) {}
  }
  if (!ensureSelectedProfilesReadyForTools('推荐术数需要出生信息，请先填写命盘')) return
  const precisionOk = await confirmBirthPrecisionForTools()
  if (!precisionOk) return
  if (currentPoints.value < estimatedCost.value) return uni.showToast({ title: '积分不足', icon: 'none' })
  const confirmed = await confirmComprehensiveSend()
  if (!confirmed) return

  const history = normalizeMessageHistory()
  const contextSnapshot = comprehensiveContextSnapshot()
  const previousContext = lastAssistantContextSnapshot()
  const contextNotice = previousContext
    ? (sameComprehensiveContext(previousContext, contextSnapshot) ? '当前使用' : '已切换为')
    : '本次使用'
  comprehensiveLoading.value = true
  comprehensiveMessages.value.push({ role: 'user', content: question })
  comprehensiveQuestion.value = ''
  const aiIndex = comprehensiveMessages.value.length
  comprehensiveMessages.value.push({
    role: 'assistant',
    content: '',
    stage: '正在连接综合解读服务',
    contextSummary: contextSnapshot.summary,
    contextNotice,
    contextSnapshot,
  })
  scheduleComprehensiveDraftSave()
  startComprehensiveProgressTimer(aiIndex)
  shouldAutoFollowChat.value = true
  scrollComprehensiveChatToBottom('smooth', true)
  const typeState = { queue: '', displayed: '', done: false }

  try {
    const requestBody = {
      question,
      profile_id: selectedProfiles.value.length === 1 && selectedProfiles.value[0].source === 'profile' ? selectedProfiles.value[0].id : undefined,
      profile: selectedProfiles.value.length === 1 ? comprehensiveProfilePayload(selectedProfiles.value[0]) : undefined,
      profiles: selectedProfiles.value.map(comprehensiveProfilePayload),
      profile_confirmed: !!profileSelectionConfirmed.value,
      llm_model: selectedLlmModel.value.id || 'basic',
      tool_models: selectedToolModels.value,
      auto_select_tools: autoSelectTools.value && !history.length,
      history,
      paipan: { paipan: currentPaipanContext.value, artifacts: currentArtifacts.value },
      reading_mode: readingMode.value,
      artifact_policy: 'auto',
      existing_artifact_keys: Object.keys(currentArtifacts.value || {}),
      conversation_id: currentComprehensiveConvId.value,
    }
    const resp = await fetch('/api/comprehensive/ask/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })
    if (!resp.ok || !resp.body) throw new Error('连接失败')
    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      parts.forEach(part => {
        const line = part.split('\n').find(l => l.indexOf('data: ') === 0)
        if (!line) return
        const data = JSON.parse(line.slice(6))
        if (data.error) {
          flushComprehensiveAssistantUpdate()
          updateComprehensiveAssistant(aiIndex, { stage: '', content: data.error })
          stopComprehensiveProgressTimer()
          stopComprehensiveTypeTimer()
        }
        if (data.message) {
          scheduleComprehensiveAssistantUpdate(aiIndex, { stage: data.message, _lastServerStageAt: Date.now() })
        }
        if (data.stage === 'tool_analysis_start' && data.tool_key) {
          revealArtifact(aiIndex, data.tool_key)
        }
        if (data.summary_start) {
          setActiveArtifact(aiIndex, '__summary__')
          scheduleComprehensiveAssistantUpdate(aiIndex, { stage: data.message || '正在生成综合结论' })
        }
        if (data.content) {
          if (data.tool_key) {
            appendArtifactAnalysis(aiIndex, data.tool_key, data.content)
          } else {
            typeState.queue += data.content
            startComprehensiveTypewriter(aiIndex, typeState)
          }
          stopComprehensiveProgressTimer()
        }
        if (data.conversation_id) {
          currentComprehensiveConvId.value = data.conversation_id
          syncArtifactCollapseStateToConversation(data.conversation_id)
          scheduleComprehensiveDraftSave()
        }
        if (Array.isArray(data.tool_models) && data.tool_models.length) selectedToolModels.value = data.tool_models
        if (data.paipan) {
          currentPaipanContext.value = data.paipan
        }
        if (data.artifacts) {
          currentArtifacts.value = data.artifacts || {}
          const existingArtifacts = (comprehensiveMessages.value[aiIndex] && comprehensiveMessages.value[aiIndex].artifacts) || []
          updateComprehensiveAssistant(aiIndex, {
            artifacts: artifactListFromMap(currentArtifacts.value, {
              existing: existingArtifacts,
              defaultVisible: false,
            })
          })
        }
        if (typeof data.points_left === 'number') currentPoints.value = data.points_left
        if (typeof data.ai_single_credits === 'number') aiSingleCredits.value = data.ai_single_credits
        if (typeof data.ai_combo_credits === 'number') aiComboCredits.value = data.ai_combo_credits
        if (data.used_credit === 'daily_light') dailyLightAvailable.value = false
        if (data.done) {
          finishComprehensiveAnswer(aiIndex, typeState)
        }
      })
    }
    finishComprehensiveAnswer(aiIndex, typeState)
    if (!typeState.queue.length) stopComprehensiveTypeTimer()
  } catch (e) {
    stopPendingArtifactAnalysisTimers()
    stopComprehensiveTypeTimer()
    flushComprehensiveAssistantUpdate()
    updateComprehensiveAssistant(aiIndex, { stage: '', content: '生成失败，请稍后重试' })
  } finally {
    flushPendingArtifactAnalyses()
    flushComprehensiveAssistantUpdate()
    comprehensiveLoading.value = false
    stopComprehensiveProgressTimer()
    saveComprehensiveDraftNow()
  }
}

function profileHasUnknownBirthTime(profile) {
  const meta = (profile && profile.meta) || {}
  return meta.birthTimePrecision === 'date_unknown_time' || meta.birthTimePrecision === 'month_only' || meta.birthTimePrecision === 'year_month'
}

function confirmBirthPrecisionForTools() {
  const needsExactTime = selectedToolModels.value.some(id => id === 'bazi' || id === 'ziwei')
  if (!needsExactTime || !selectedProfiles.value.some(profileHasUnknownBirthTime)) return Promise.resolve(true)
  return new Promise(function(resolve) {
    uni.showModal({
      title: '出生时间不完整',
      content: '当前命盘标记为不清楚具体时分。八字和紫微对出生时间较敏感，建议补充准确时间；若暂时不知道，可以改用奇门、六爻、梅花或塔罗先看具体问题。',
      confirmText: '继续',
      cancelText: '返回调整',
      success: function(res) { resolve(!!res.confirm) },
      fail: function() { resolve(false) },
    })
  })
}

function confirmComprehensiveSend() {
  if (readStorageJson(currentUserScopedStorageKey(sendConfirmSkipStorageKey), false)) return Promise.resolve(true)
  return new Promise(function(resolve) {
    pendingSendConfirmResolve = resolve
    sendConfirmDontRemind.value = false
    sendConfirmOpen.value = true
  })
}

function resolveSendConfirm(confirmed) {
  if (confirmed && sendConfirmDontRemind.value) {
    writeStorageJson(currentUserScopedStorageKey(sendConfirmSkipStorageKey), true)
  }
  sendConfirmOpen.value = false
  const resolve = pendingSendConfirmResolve
  pendingSendConfirmResolve = null
  if (resolve) resolve(!!confirmed)
}

function onComprehensiveInputKeydown(e) {
  if (!e || e.isComposing) return
  if (e.key !== 'Enter') return
  if (e.shiftKey || e.altKey || e.ctrlKey || e.metaKey) return
  e.preventDefault()
  startComprehensiveAsk()
}

async function restoreComprehensiveConversation(id) {
  if (!id || !isLoggedIn.value) return
  try {
    const res = await uni.request({ url: '/api/comprehensive/conversations/' + id })
    const data = res.data || {}
    if (!data.id) return
    currentComprehensiveConvId.value = data.id
    currentPaipanContext.value = data.paipan || {}
    currentArtifacts.value = data.artifacts || {}
    selectedToolModels.value = data.models && data.models.length ? data.models : ['bazi']
    const restoredArtifacts = artifactListFromMap(currentArtifacts.value)
    let attached = false
    comprehensiveMessages.value = (data.messages || []).map(function(m) {
      if (m && m.role === 'assistant' && m.content) {
        const next = Object.assign({}, m, { content: stripComprehensiveMarkdown(comprehensiveSummaryOnly(m.content)) })
        if (!attached && restoredArtifacts.length) {
          next.artifacts = restoredArtifacts
          attached = true
        }
        return next
      }
      return m
    })
    comprehensiveMessages.value.forEach(function(message, index) {
      ensureActiveArtifact(index, visibleArtifactList(message))
      if (message && message.role === 'assistant' && message.content) setActiveArtifact(index, '__summary__')
    })
    const mid = data.model_id || 'basic'
    const mi = llmModels.value.findIndex(m => m.id === mid)
    if (mi >= 0) llmModelIdx.value = mi
    const p = data.profile_data || {}
    selectedProfiles.value = (p.id || p.name || p.birth_time) ? [{
      id: p.id,
      name: p.name,
      gender: p.gender,
      birthTime: p.birth_time,
      calType: p.cal_type,
      birthAddr: p.birth_addr,
      profileType: p.profile_type,
      source: p.source || 'profile',
    }] : []
    shouldAutoFollowChat.value = true
    saveComprehensiveDraftNow()
    scrollComprehensiveChatToBottom('smooth', true)
  } catch (_) {}
}

function isComprehensiveChatNearBottom() {
  // #ifdef H5
  try {
    const el = getComprehensiveScrollTarget()
    if (!el) return true
    return el.scrollHeight - el.scrollTop - el.clientHeight < HOME_AI_NEAR_BOTTOM_PX
  } catch(_) {
    return true
  }
  // #endif
  return true
}

function updateComprehensiveAutoFollowFromScroll() {
  // #ifdef H5
  try {
    const el = getComprehensiveScrollTarget()
    if (!el) return
    const top = Number(el.scrollTop || 0)
    const scrollingUp = top + 2 < lastComprehensiveScrollTop
    lastComprehensiveScrollTop = top
    if (scrollingUp) {
      shouldAutoFollowChat.value = false
      return
    }
    if (isComprehensiveChatNearBottom()) shouldAutoFollowChat.value = true
  } catch (_) {}
  // #endif
}

function onHomeChatScroll() {
  updateComprehensiveAutoFollowFromScroll()
}

function onHomePageScroll() {
  if (!comprehensiveMessages.value.length) return
  updateComprehensiveAutoFollowFromScroll()
}

function getComprehensiveScrollTarget() {
  // #ifdef H5
  const pageTarget = document.scrollingElement || document.documentElement || document.body
  const chat = document.querySelector('.home-ai-chat')
  if (!chat) return pageTarget
  const style = window.getComputedStyle ? window.getComputedStyle(chat) : null
  const canScrollChat = chat.scrollHeight - chat.clientHeight > 8 && style && style.overflowY !== 'visible'
  return canScrollChat ? chat : pageTarget
  // #endif
  return null
}

function scrollComprehensiveChatToBottom(behavior, force) {
  if (!force && !shouldAutoFollowChat.value) return
  // #ifdef H5
  if (comprehensiveScrollTimer) cancelAnimationFrame(comprehensiveScrollTimer)
  comprehensiveScrollTimer = requestAnimationFrame(function() {
    comprehensiveScrollTimer = null
    try {
      const el = getComprehensiveScrollTarget()
      if (el) {
        el.scrollTo({ top: el.scrollHeight, behavior: behavior || 'auto' })
        lastComprehensiveScrollTop = Number(el.scrollHeight || 0)
      }
    } catch(_) {}
  })
  // #endif
}

function restoreComprehensiveFromSidebar(id) {
  const restoreId = id || pendingComprehensiveId
  if (!restoreId) return
  pendingComprehensiveId = ''
  restoreComprehensiveConversation(restoreId)
}

function startNewComprehensiveConversation() {
  stopComprehensiveProgressTimer()
  stopComprehensiveTypeTimer()
  stopPendingArtifactAnalysisTimers()
  stopComprehensiveAssistantUpdateQueue()
  comprehensiveQuestion.value = ''
  comprehensiveMessages.value = []
  resetQuestionGuide('')
  draftSelectedProfiles.value = selectedProfiles.value.slice()
  currentComprehensiveConvId.value = null
  currentPaipanContext.value = {}
  currentArtifacts.value = {}
  comprehensiveTypeStates = {}
  artifactHtmlCache = new WeakMap()
  resetSelectedToolModels()
  Object.keys(activeArtifactKeyByMessage).forEach(function(key) { delete activeArtifactKeyByMessage[key] })
  shouldAutoFollowChat.value = true
  pendingComprehensiveId = ''
  try { sessionStorage.removeItem('xc_comprehensive_resume_id') } catch(_) {}
  clearComprehensiveDraft()
  restoreSavedAgentSelection(profiles.value || [])
  resetSelectedToolModels()
  scrollComprehensiveChatToBottom('auto', true)
}

function onHomeKeydown(e) {
  if (!e || e.isComposing) return
  if (profileSheetOpen.value) {
    if (e.key === 'Escape') {
      e.preventDefault()
      cancelProfileSelection()
    } else if (e.key === 'Enter') {
      e.preventDefault()
      confirmProfileSelection()
    }
    return
  }
}

// ── 页脚 ──
function showFooterInfo(type) {
  const infoMap = {
    contact: '联系方式：请通过站内反馈或邮件联系',
    terms: '用户协议：使用本站即表示同意遵守相关条款',
    privacy: '隐私政策：所有数据本地处理，不上传服务器',
    disclaimer: '免责声明：本站内容仅为民俗文化参考',
    copyright: '版权信息：© 2026 时安解忧屋 版权所有',
  }
  uni.showModal({ title: '提示', content: infoMap[type] || '', showCancel: false })
}

function clearAllData() {
  uni.showModal({
    title: '确认清空',
    content: '确认清空所有本地数据？此操作不可撤销。',
    success: (res) => {
      if (res.confirm) {
        var _savedTheme = uni.getStorageSync('xc_theme')
        var _savedThemeChoice = uni.getStorageSync('xc_theme_user_selected')
        uni.clearStorageSync()
        if (_savedTheme) uni.setStorageSync('xc_theme', _savedTheme)
        if (_savedThemeChoice) uni.setStorageSync('xc_theme_user_selected', _savedThemeChoice)
        uni.showToast({ title: '已清空', icon: 'success' })
      }
    }
  })
}

// ── Tab 切换回来时同步主题 ──
onLoad((query) => {
  refreshMarketingMode(query)
  pendingComprehensiveId = query && query.comprehensive_id ? String(query.comprehensive_id) : ''
})

onShow(() => {
  refreshMarketingMode()
  setHomeFixedPage(!marketingMode.value)
  var t = readInitialTheme()
  if (t !== theme.value) {
    theme.value = t
    try {
      document.documentElement.setAttribute('data-theme', t)
      document.body.setAttribute('data-theme', t)
    } catch(_) {}
  }
  // #ifdef H5
  try {
    const resumeId = sessionStorage.getItem('xc_comprehensive_resume_id')
    if (resumeId) {
      sessionStorage.removeItem('xc_comprehensive_resume_id')
      pendingComprehensiveId = resumeId
    }
  } catch(_) {}
  // #endif
  loadComprehensiveOptions()
  loadProfiles().then(function() {
    if (pendingComprehensiveId) {
      const id = pendingComprehensiveId
      pendingComprehensiveId = ''
      restoreComprehensiveConversation(id)
    } else {
      restoreComprehensiveDraft()
    }
  })
})

onHide(() => {
  saveComprehensiveDraftNow()
  setHomeFixedPage(false)
})

// ── 视频加载超时处理（H5 only）──
onMounted(() => {
  refreshMarketingMode()
  resetSelectedToolModels()
  loadComprehensiveOptions()
  loadProfiles()
  // #ifdef H5
  setHomeFixedPage(!marketingMode.value)
  window._xc_restoreComprehensive = restoreComprehensiveFromSidebar
  window._xc_newComprehensive = startNewComprehensiveConversation
  window.addEventListener('keydown', onHomeKeydown)
  window.addEventListener('scroll', onHomePageScroll, { passive: true })
  window.addEventListener('popstate', onMarketingRouteChange)
  window.addEventListener('hashchange', onMarketingRouteChange)
  window.addEventListener('beforeunload', saveComprehensiveDraftForUnload)
  document.addEventListener('click', onMarketingEnterNative, true)
  document.addEventListener('touchstart', onMarketingEnterNative, { passive: false, capture: true })
  document.addEventListener('visibilitychange', onHomeVisibilityChange)
  document.addEventListener('click', onHomeBaziYunClick)
  if (!marketingMode.value) scheduleHomeVideoLoad()
  // #endif
})

onBeforeUnmount(() => {
  disconnectMarketingObserver()
  restoreMarketingScrollRestoration()
  saveComprehensiveDraftForUnload()
  stopComprehensiveProgressTimer()
  stopComprehensiveTypeTimer()
  stopPendingArtifactAnalysisTimers()
  stopComprehensiveAssistantUpdateQueue()
  // #ifdef H5
  if (comprehensiveScrollTimer) cancelAnimationFrame(comprehensiveScrollTimer)
  if (window._xc_restoreComprehensive === restoreComprehensiveFromSidebar) window._xc_restoreComprehensive = null
  if (window._xc_newComprehensive === startNewComprehensiveConversation) window._xc_newComprehensive = null
  window.removeEventListener('keydown', onHomeKeydown)
  window.removeEventListener('scroll', onHomePageScroll)
  window.removeEventListener('popstate', onMarketingRouteChange)
  window.removeEventListener('hashchange', onMarketingRouteChange)
  window.removeEventListener('beforeunload', saveComprehensiveDraftForUnload)
  document.removeEventListener('click', onMarketingEnterNative, true)
  document.removeEventListener('touchstart', onMarketingEnterNative, true)
  document.removeEventListener('visibilitychange', onHomeVisibilityChange)
  document.removeEventListener('click', onHomeBaziYunClick)
  if (homeVideoFallbackTimer) clearTimeout(homeVideoFallbackTimer)
  if (homeVideoRevealTimer) clearTimeout(homeVideoRevealTimer)
  setHomeFixedPage(false)
  // #endif
})
</script>

<style scoped>
/* ═══ 变量体系 ═══ */
:root {
  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --radius-md: 14px; --radius-lg: 20px;
  --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif;
  --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif;
  --max-w: 1280px;
}
[data-theme="dark"] {
  --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824;
  --accent-h: 38; --accent-s: 60%; --accent-l: 60%;
  --accent: hsl(var(--accent-h), var(--accent-s), var(--accent-l));
  --accent-2: hsl(var(--accent-h), var(--accent-s), 48%);
  --accent-glow: hsla(var(--accent-h), var(--accent-s), var(--accent-l), 0.10);
  --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12);
  --card-border-hover: rgba(255,255,255,0.18);
  --card-shadow: 0 16px 48px rgba(0,0,0,0.35);
  --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20);
  --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95);
  --text-3: rgba(170,160,145,0.88); --text-4: rgba(160,150,135,0.78);
  --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88);
  --info: rgba(120,170,230,0.88);
  --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45);
  --tag-bg: rgba(255,255,255,0.08); --tag-text: rgba(195,185,165,0.85);
}
[data-theme="light"] {
  --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0;
  --accent-h: 38; --accent-s: 72%; --accent-l: 30%;
  --accent: hsl(var(--accent-h), var(--accent-s), var(--accent-l));
  --accent-2: hsl(var(--accent-h), var(--accent-s), 22%);
  --accent-glow: hsla(var(--accent-h), var(--accent-s), var(--accent-l), 0.065);
  --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045);
  --card-border-hover: rgba(0,0,0,0.08);
  --card-shadow: 0 8px 28px rgba(60,40,15,0.055);
  --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065);
  --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90);
  --text-3: rgba(100,88,68,0.78); --text-4: rgba(90,78,58,0.68);
  --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88);
  --info: rgba(30,90,200,0.88);
  --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45);
  --tag-bg: rgba(0,0,0,0.05); --tag-text: rgba(70,58,40,0.80);
}

:global(html.home-fixed-page),
:global(body.home-fixed-page) {
  height: 100dvh !important;
  min-height: 100dvh !important;
  max-height: 100dvh !important;
  overflow: hidden !important;
  overscroll-behavior: none !important;
}
:global(uni-page[data-marketing-hidden="true"]) {
  display: none !important;
}
:global(body.marketing-page .tarot-sidebar),
:global(body.marketing-page #tarotSidebarGlobal) {
  display: none !important;
}
:global(body.home-fixed-page uni-page-body),
:global(body.home-fixed-page uni-page-wrapper),
:global(body.home-fixed-page .uni-page-body) {
  height: 100dvh !important;
  min-height: 100dvh !important;
  max-height: 100dvh !important;
  overflow: hidden !important;
}
:global(html.home-fixed-page:not(:has(.home-ai-console.has-chat))),
:global(body.home-fixed-page:not(:has(.home-ai-console.has-chat))) {
  height: 100dvh;
  min-height: 100dvh;
  overflow-y: hidden !important;
  overscroll-behavior: none;
}
:global(body.home-fixed-page:not(:has(.home-ai-console.has-chat)) uni-page-body),
:global(body.home-fixed-page:not(:has(.home-ai-console.has-chat)) uni-page-wrapper),
:global(body.home-fixed-page:not(:has(.home-ai-console.has-chat)) .uni-page-body) {
  height: 100dvh;
  min-height: 100dvh;
  max-height: 100dvh;
  overflow-y: hidden !important;
}
:global(html.home-fixed-page:has(.marketing-active)),
:global(body.home-fixed-page:has(.marketing-active)) {
  height: auto;
  min-height: 100%;
  overflow-y: auto !important;
  overscroll-behavior: auto;
}
:global(body.home-fixed-page:has(.marketing-active) uni-page-body),
:global(body.home-fixed-page:has(.marketing-active) uni-page-wrapper),
:global(body.home-fixed-page:has(.marketing-active) .uni-page-body) {
  height: auto;
  min-height: 100dvh;
  max-height: none;
  overflow-y: auto !important;
}
:global(html.marketing-page),
:global(body.marketing-page) {
  height: 100% !important;
  min-height: 100% !important;
  overflow-x: hidden !important;
  overflow-y: hidden !important;
  overscroll-behavior-y: auto !important;
  touch-action: auto !important;
}
:global(body.marketing-page uni-page-body),
:global(body.marketing-page uni-page-wrapper),
:global(body.marketing-page .uni-page-body) {
  height: 100dvh !important;
  min-height: 100dvh !important;
  max-height: 100dvh !important;
  overflow-y: hidden !important;
  touch-action: auto !important;
}

.page-root { --home-ai-dock-space: 116px; --home-ai-chat-bottom-buffer: 126px; min-height: 100dvh; overflow-x: hidden; overflow-y: auto; width: 100% !important; max-width: 100vw !important; box-sizing: border-box; }
.page-root.marketing-active {
  background:
    radial-gradient(circle at 18% 78%, rgba(255,255,255,.58), transparent 28rem),
    radial-gradient(circle at 82% 52%, rgba(197,122,36,.13), transparent 24rem),
    linear-gradient(180deg, #eee9df 0%, #ded6ca 54%, #f8f4ec 100%);
  height: 100dvh !important;
  max-height: 100dvh !important;
  overflow-x: hidden !important;
  overflow-y: hidden !important;
  overscroll-behavior-y: auto;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: auto;
  touch-action: auto;
}
:global(body.home-fixed-page) .page-root {
  height: 100dvh;
  min-height: 100dvh;
  max-height: 100dvh;
  overflow: hidden !important;
}
:global(body.marketing-page) .page-root.marketing-active {
  padding-top: 0 !important;
  height: 100dvh !important;
  min-height: 100dvh !important;
  max-height: 100dvh !important;
  overflow-x: hidden !important;
  overflow-y: hidden !important;
  overscroll-behavior-y: auto !important;
  -webkit-overflow-scrolling: touch;
  touch-action: auto !important;
}
.tool-home-shell { min-height: 100dvh; }

.marketing-landing {
  --marketing-ink: #171512;
  --marketing-ink-soft: rgba(23, 21, 18, .58);
  --marketing-paper: #f2eee5;
  --marketing-copper: #c57a24;
  --marketing-jade: #315f55;
  position: relative;
  height: 100dvh;
  min-height: 100dvh;
  max-height: 100dvh;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior-y: auto;
  scroll-snap-type: y mandatory;
  scroll-behavior: auto;
  -webkit-overflow-scrolling: touch;
  touch-action: auto;
  color: var(--marketing-ink);
  font-family: ui-serif, "Songti SC", "STSong", "Times New Roman", serif;
  box-sizing: border-box;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.marketing-landing::-webkit-scrollbar {
  width: 0;
  height: 0;
  display: none;
}
@media (hover: hover) and (pointer: fine) {
  :global(body.marketing-wheel-scroll .marketing-landing) {
    scroll-snap-type: none;
  }
  :global(body.marketing-wheel-scroll .marketing-hero),
  :global(body.marketing-wheel-scroll .marketing-critical),
  :global(body.marketing-wheel-scroll .marketing-tools),
  :global(body.marketing-wheel-scroll .marketing-core),
  :global(body.marketing-wheel-scroll .marketing-final) {
    scroll-snap-align: none;
  }
}
.marketing-auth-host {
  position: fixed;
  inset: 0;
  z-index: 80;
  pointer-events: none;
}
.marketing-auth-host :deep(.topnav) { display: none; }
.marketing-auth-host :deep(.modal-overlay) {
  pointer-events: auto;
  align-items: flex-end !important;
  justify-content: center !important;
  padding: 18px !important;
  padding-bottom: max(18px, calc(env(safe-area-inset-bottom) + 14px)) !important;
  box-sizing: border-box !important;
}
.marketing-auth-host :deep(.modal-overlay.open) {
  display: flex !important;
}
.marketing-auth-host :deep(.modal-box) {
  margin-top: auto !important;
  margin-bottom: 0 !important;
}
.marketing-nav {
  position: fixed;
  inset: 0 0 auto;
  z-index: 30;
  height: 78px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 50px;
  background: linear-gradient(180deg, rgba(242,238,229,.96) 0%, rgba(242,238,229,.82) 62%, rgba(242,238,229,0) 100%);
  backdrop-filter: blur(10px);
  animation: marketingNavIn .42s ease-out both;
}
.marketing-brand {
  display: flex;
  gap: 14px;
  align-items: center;
  flex: 0 0 auto;
  min-width: 210px;
  font-weight: 700;
  font-size: 17px;
  letter-spacing: .02em;
}
.marketing-logo-wrap {
  position: relative;
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: rgba(255,255,255,.5);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.7), 0 8px 24px rgba(49,95,85,.12);
}
.marketing-logo-wrap::before {
  content: "";
  position: absolute;
  inset: -6px;
  border-radius: inherit;
  border: 1px solid rgba(49,95,85,.18);
  border-top-color: rgba(197,122,36,.52);
  border-right-color: rgba(197,122,36,.24);
  transform-origin: center;
  animation: marketingSlowSpin 14s linear infinite;
}
.marketing-logo {
  width: 28px;
  height: 28px;
  object-fit: contain;
  transform-origin: center;
  animation: marketingSlowSpin 24s linear infinite reverse;
}
.marketing-nav-links {
  display: flex;
  gap: 36px;
  align-items: center;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 14px;
  font-weight: 650;
  color: rgba(23,21,18,.72);
}
.marketing-nav-link {
  cursor: pointer;
  white-space: nowrap;
  transition: color .18s ease, transform .18s ease;
}
.marketing-nav-link:hover {
  color: var(--marketing-copper);
  transform: translateY(-1px);
}
.marketing-agent-link {
  color: var(--marketing-ink);
  font-weight: 800;
}
.marketing-enter,
.marketing-primary,
.marketing-secondary {
  margin: 0;
  border: 0;
  border-radius: 999px;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-weight: 700;
  line-height: 1;
  transition: transform .18s ease, box-shadow .18s ease, background .18s ease;
}
.marketing-enter::after,
.marketing-primary::after,
.marketing-secondary::after { border: 0; }
.marketing-enter {
  min-height: 40px;
  min-width: 104px;
  padding: 0 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--marketing-ink);
  background: rgba(255,255,255,.66);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.7);
  font-size: 14px;
  line-height: 1;
}
.marketing-hero {
  position: relative;
  scroll-snap-align: start;
  scroll-snap-stop: normal;
  height: 100dvh;
  min-height: 100dvh;
  overflow: hidden;
  padding: 0 56px 80px clamp(196px, 15vw, 230px);
  display: flex;
  align-items: flex-end;
  box-sizing: border-box;
}
.marketing-ambient {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.marketing-ambient::before,
.marketing-ambient::after {
  content: "";
  position: absolute;
  pointer-events: none;
  border: 1px solid rgba(49,44,34,.12);
  border-radius: 50%;
  box-shadow: 0 0 32px rgba(197,122,36,.04);
}
.marketing-ambient::before {
  left: -18%;
  top: 18%;
  width: 78%;
  height: 40%;
  transform: rotate(-12deg);
}
.marketing-ambient::after {
  right: -14%;
  top: 12%;
  width: 74%;
  height: 52%;
  transform: rotate(22deg);
}
.marketing-mist {
  position: absolute;
  border-radius: 999px;
  filter: blur(2px);
  opacity: .54;
  animation: marketingMistDrift 18s ease-in-out infinite;
}
.marketing-mist-a {
  left: -14rem;
  bottom: 8rem;
  width: 48rem;
  height: 28rem;
  background: radial-gradient(circle, rgba(255,255,255,.7), rgba(255,255,255,0) 68%);
}
.marketing-mist-b {
  right: -8rem;
  top: 17rem;
  width: 38rem;
  height: 28rem;
  background: radial-gradient(circle, rgba(197,122,36,.15), rgba(197,122,36,0) 68%);
  animation-delay: -6s;
}
.marketing-mist-c {
  right: 5rem;
  top: 10rem;
  width: 20rem;
  height: 18rem;
  background: radial-gradient(circle, rgba(49,95,85,.14), rgba(49,95,85,0) 68%);
  animation-delay: -11s;
}
.marketing-orbits {
  position: absolute;
  left: 26%;
  top: -4%;
  width: 76rem;
  height: 48rem;
  opacity: .56;
  animation: marketingOrbitFloat 22s ease-in-out infinite;
}
.marketing-orbits::before,
.marketing-orbits::after {
  content: "";
  position: absolute;
  left: 50%;
  top: 50%;
  pointer-events: none;
  border: 1px solid rgba(49,44,34,.14);
  border-radius: 50%;
  transform: translate(-50%, -50%) rotate(var(--marketing-r));
  box-shadow: 0 0 30px rgba(197,122,36,.04);
}
.marketing-orbits::before {
  width: 88rem;
  height: 28rem;
  --marketing-r: 14deg;
}
.marketing-orbits::after {
  width: 96rem;
  height: 20rem;
  --marketing-r: -8deg;
}
.marketing-orbit {
  position: absolute;
  left: 50%;
  top: 50%;
  border: 1px solid rgba(49,44,34,.28);
  border-radius: 50%;
  box-shadow: 0 0 24px rgba(197,122,36,.055);
  transform: translate(-50%, -50%) rotate(var(--marketing-r));
  animation: marketingOrbitRotate var(--marketing-d) linear infinite;
}
.marketing-orbit:nth-child(1) { width: 24rem; height: 8rem; --marketing-r: -12deg; --marketing-d: 42s; }
.marketing-orbit:nth-child(2) { width: 38rem; height: 12.5rem; --marketing-r: 8deg; --marketing-d: 58s; }
.marketing-orbit:nth-child(3) { width: 54rem; height: 18rem; --marketing-r: 23deg; --marketing-d: 72s; }
.marketing-orbit:nth-child(4) { width: 70rem; height: 23rem; --marketing-r: -27deg; --marketing-d: 88s; }
.marketing-particle {
  position: absolute;
  width: 5.5px;
  height: 5.5px;
  border-radius: 50%;
  background: rgba(210,139,47,.92);
  box-shadow: 0 0 16px rgba(197,122,36,.34);
  animation: marketingParticleRise 6s ease-in-out infinite;
}
.marketing-particle-soft {
  width: 3.6px;
  height: 3.6px;
  background: rgba(197,122,36,.74);
  box-shadow: 0 0 13px rgba(197,122,36,.28);
  animation-duration: 9s;
}
.marketing-particle-1 { left: 18%; top: 28%; animation-delay: -.7s; }
.marketing-particle-2 { left: 42%; top: 20%; animation-delay: -2.1s; }
.marketing-particle-3 { left: 74%; top: 34%; animation-delay: -1.4s; }
.marketing-particle-4 { left: 86%; top: 62%; animation-delay: -3.2s; }
.marketing-particle-5 { left: 34%; top: 70%; animation-delay: -4s; }
.marketing-particle-6 { left: 11%; top: 58%; animation-delay: -5.4s; }
.marketing-particle-7 { left: 26%; top: 40%; animation-delay: -1.8s; }
.marketing-particle-8 { left: 51%; top: 52%; animation-delay: -6.2s; }
.marketing-particle-9 { left: 59%; top: 24%; animation-delay: -3.7s; }
.marketing-particle-10 { left: 67%; top: 66%; animation-delay: -7.1s; }
.marketing-particle-11 { left: 78%; top: 18%; animation-delay: -4.9s; }
.marketing-particle-12 { left: 91%; top: 46%; animation-delay: -2.6s; }
.marketing-particle-13 { left: 44%; top: 78%; animation-delay: -8.3s; }
.marketing-particle-14 { left: 82%; top: 74%; animation-delay: -6.8s; }
.marketing-particle-15 { left: 7%; top: 36%; animation-delay: -3.4s; }
.marketing-particle-16 { left: 21%; top: 76%; animation-delay: -7.8s; }
.marketing-particle-17 { left: 39%; top: 31%; animation-delay: -5.9s; }
.marketing-particle-18 { left: 53%; top: 14%; animation-delay: -9.1s; }
.marketing-particle-19 { left: 63%; top: 42%; animation-delay: -1.2s; }
.marketing-particle-20 { left: 72%; top: 82%; animation-delay: -8.7s; }
.marketing-particle-21 { left: 88%; top: 26%; animation-delay: -4.2s; }
.marketing-particle-22 { left: 96%; top: 68%; animation-delay: -6.4s; }
.marketing-particle-23 { left: 4%; top: 22%; animation-delay: -8.9s; }
.marketing-particle-24 { left: 9%; top: 84%; animation-delay: -2.9s; }
.marketing-particle-25 { left: 15%; top: 48%; animation-delay: -6.9s; }
.marketing-particle-26 { left: 24%; top: 16%; animation-delay: -10.4s; }
.marketing-particle-27 { left: 29%; top: 63%; animation-delay: -4.6s; }
.marketing-particle-28 { left: 36%; top: 88%; animation-delay: -9.7s; }
.marketing-particle-29 { left: 46%; top: 38%; animation-delay: -3.1s; }
.marketing-particle-30 { left: 49%; top: 86%; animation-delay: -7.3s; }
.marketing-particle-31 { left: 55%; top: 69%; animation-delay: -1.9s; }
.marketing-particle-32 { left: 58%; top: 9%; animation-delay: -11.2s; }
.marketing-particle-33 { left: 64%; top: 57%; animation-delay: -5.2s; }
.marketing-particle-34 { left: 69%; top: 29%; animation-delay: -8.1s; }
.marketing-particle-35 { left: 73%; top: 12%; animation-delay: -2.4s; }
.marketing-particle-36 { left: 77%; top: 49%; animation-delay: -10.9s; }
.marketing-particle-37 { left: 81%; top: 86%; animation-delay: -6.1s; }
.marketing-particle-38 { left: 85%; top: 39%; animation-delay: -12.1s; }
.marketing-particle-39 { left: 90%; top: 11%; animation-delay: -7.6s; }
.marketing-particle-40 { left: 94%; top: 33%; animation-delay: -4.4s; }
.marketing-particle-41 { left: 98%; top: 52%; animation-delay: -9.4s; }
.marketing-particle-42 { left: 2%; top: 63%; animation-delay: -5.8s; }
.marketing-particle-43 { left: 12%; top: 11%; animation-delay: -12.6s; }
.marketing-particle-44 { left: 19%; top: 90%; animation-delay: -3.9s; }
.marketing-particle-45 { left: 31%; top: 24%; animation-delay: -8.5s; }
.marketing-particle-46 { left: 41%; top: 58%; animation-delay: -11.7s; }
.marketing-particle-47 { left: 52%; top: 33%; animation-delay: -4.8s; }
.marketing-particle-48 { left: 61%; top: 78%; animation-delay: -10.1s; }
.marketing-particle-49 { left: 70%; top: 93%; animation-delay: -6.7s; }
.marketing-particle-50 { left: 93%; top: 79%; animation-delay: -13.2s; }
.marketing-bottom-blur {
  position: absolute;
  inset: auto 0 0;
  height: 270px;
  background: linear-gradient(180deg, rgba(242,238,229,0), rgba(242,238,229,.92) 72%);
  backdrop-filter: blur(7px);
}
.marketing-copy {
  position: relative;
  z-index: 2;
  width: min(100%, 1360px);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  gap: 60px;
  align-items: end;
  padding-bottom: 22px;
  transform: translateY(-38px);
}
.marketing-main {
  max-width: 820px;
  transform: translateY(-154px);
}
.marketing-side {
  transform: translateY(82px);
}
.marketing-kicker,
.marketing-title,
.marketing-title-cn,
.marketing-side-title,
.marketing-side-desc,
.marketing-cta-row {
  display: block;
  animation: marketingHeroRise .9s cubic-bezier(.2,.8,.2,1) both;
}
.marketing-kicker {
  margin: 0 0 18px;
  font: 650 22px/1.1 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  letter-spacing: .01em;
  animation-delay: .12s;
}
.marketing-title {
  margin: 0;
  font: 800 clamp(52px, 6.2vw, 82px)/1.08 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  letter-spacing: 0;
  opacity: .58;
  animation-delay: .28s;
}
.marketing-title-cn {
  margin: 18px 0 0;
  font-size: clamp(34px, 3.6vw, 48px);
  line-height: 1.18;
  font-weight: 700;
  color: rgba(23,21,18,.54);
  animation-delay: .44s;
}
.marketing-title text,
.marketing-title-cn text { display: block; }
.marketing-side-title {
  margin: 0 0 22px;
  font: 750 28px/1.15 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  animation-delay: .62s;
}
.marketing-side-desc {
  margin: 0;
  color: rgba(23,21,18,.62);
  font-size: 18px;
  line-height: 1.65;
  animation-delay: .74s;
}
.marketing-cta-row {
  display: flex;
  gap: 18px;
  margin-top: 44px;
  align-items: center;
  animation-delay: .9s;
}
.marketing-primary,
.marketing-secondary {
  height: 56px;
  min-width: 132px;
  max-width: 280px;
  width: auto;
  padding: 0 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  line-height: 1;
  box-sizing: border-box;
  text-align: center;
}
.marketing-primary {
  color: white;
  background: var(--marketing-copper);
  box-shadow: 0 16px 40px rgba(197,122,36,.22);
}
.marketing-secondary {
  color: var(--marketing-ink);
  background: rgba(255,255,255,.48);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.78);
}
.marketing-primary:hover,
.marketing-secondary:hover,
.marketing-enter:hover { transform: translateY(-2px); }

@media (max-width: 1280px) and (min-width: 761px) {
  .marketing-copy {
    grid-template-columns: 658px minmax(240px, 1fr);
    gap: 40px;
  }
  .marketing-kicker { font-size: 22px; }
  .marketing-title { font-size: 82px; }
  .marketing-title-cn { font-size: 48px; }
  .marketing-side-title { font-size: 25px; }
  .marketing-side-desc { font-size: 17px; }
}

@media (max-height: 820px) and (min-width: 761px) {
  .marketing-main { transform: translateY(-92px); }
  .marketing-title { font-size: 82px; }
  .marketing-title-cn { font-size: 48px; }
  .marketing-kicker { margin-bottom: 18px; font-size: 22px; }
}

@media (min-width: 761px) {
  .marketing-copy {
    width: 100%;
    min-width: 0;
    max-width: 1248px;
    grid-template-columns: 658px minmax(260px, 1fr);
    gap: clamp(86px, 8vw, 128px);
  }
  .marketing-main {
    width: 658px;
    max-width: 658px;
  }
  .marketing-kicker {
    margin-bottom: 18px;
    font-size: 22px;
  }
  .marketing-title {
    font-size: 82px;
  }
  .marketing-title-cn {
    margin-top: 18px;
    font-size: 48px;
  }
  .marketing-side {
    width: min(100%, 410px);
    justify-self: end;
  }
  .marketing-side-title {
    font-size: 28px;
  }
  .marketing-side-desc {
    font-size: 18px;
  }
  .marketing-cta-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
    gap: 18px;
  }
  .marketing-cta-row .marketing-primary,
  .marketing-cta-row .marketing-secondary {
    width: 100%;
    min-width: 0;
    max-width: none;
    padding: 0 20px;
  }
}

@media (max-width: 1280px) and (min-width: 761px) {
  .marketing-hero {
    padding-right: 50px;
    padding-left: clamp(178px, 13.6vw, 204px);
  }
  .marketing-copy {
    max-width: none;
    grid-template-columns: 658px minmax(240px, 1fr);
    gap: 40px;
  }
  .marketing-main {
    width: 658px;
    max-width: 658px;
    transform: translateY(-92px);
  }
  .marketing-title {
    font-size: 82px;
  }
  .marketing-title-cn {
    font-size: 48px;
  }
  .marketing-side {
    width: min(100%, 330px);
  }
  .marketing-side {
    transform: translateY(42px);
  }
  .marketing-cta-row {
    gap: 12px;
  }
  .marketing-cta-row .marketing-primary,
  .marketing-cta-row .marketing-secondary {
    padding: 0 12px;
  }
  .marketing-tools {
    grid-template-columns: minmax(340px, .68fr) minmax(500px, .9fr);
    gap: 48px;
    padding-left: 56px;
    padding-right: 56px;
  }
  .marketing-engine {
    padding: 28px;
  }
  .marketing-engine-ui {
    grid-template-columns: 112px minmax(150px, 1fr) 150px;
    gap: 14px;
  }
  .marketing-engine-chart-grid {
    background-size: 34px 34px;
  }
  .marketing-core {
    padding: 90px 56px 52px;
  }
  .marketing-system-body {
    gap: 18px;
    margin-top: 22px;
  }
  .marketing-system-item {
    min-height: 304px;
    padding: 20px 20px 22px;
  }
  .marketing-system-visual {
    width: 150px;
    margin-bottom: 14px;
  }
  .marketing-system-desc {
    font-size: 15px;
    line-height: 1.55;
  }
}

@media (max-width: 1120px) and (min-width: 761px) {
  .marketing-hero {
    padding-right: 50px;
    padding-left: 166px;
  }
  .marketing-copy {
    position: relative;
    grid-template-columns: 658px minmax(0, 1fr);
    gap: 0;
  }
  .marketing-main {
    width: 658px;
    max-width: 658px;
  }
  .marketing-side {
    position: absolute;
    right: 0;
    bottom: -96px;
    width: clamp(220px, calc(100vw - 742px), 320px);
    transform: none;
  }
}

@media (max-height: 780px) and (min-width: 761px) {
  .marketing-hero {
    padding-bottom: 30px;
  }
  .marketing-copy {
    transform: translateY(-30px);
  }
  .marketing-main {
    transform: translateY(-148px);
  }
  .marketing-side {
    transform: translateY(-72px);
  }
  .marketing-side-title {
    margin-bottom: 14px;
    font-size: 24px;
    line-height: 1.12;
  }
  .marketing-side-desc {
    font-size: 16px;
    line-height: 1.48;
  }
  .marketing-cta-row {
    margin-top: 18px;
  }
  .marketing-cta-row .marketing-primary,
  .marketing-cta-row .marketing-secondary {
    height: 50px;
  }
  .marketing-scroll-hint {
    bottom: 20px;
  }
}

@media (max-height: 780px) and (max-width: 1120px) and (min-width: 761px) {
  .marketing-side {
    bottom: 58px;
    transform: none;
  }
}

@media (max-height: 700px) and (min-width: 761px) {
  .marketing-hero {
    padding-bottom: 22px;
  }
  .marketing-main {
    transform: translateY(-132px);
  }
  .marketing-side {
    transform: translateY(-78px);
  }
  .marketing-side-title {
    margin-bottom: 10px;
    font-size: 22px;
  }
  .marketing-side-desc {
    font-size: 15px;
    line-height: 1.42;
  }
  .marketing-cta-row {
    margin-top: 18px;
  }
  .marketing-cta-row .marketing-primary,
  .marketing-cta-row .marketing-secondary {
    height: 48px;
  }
}

@media (max-height: 700px) and (max-width: 1120px) and (min-width: 761px) {
  .marketing-side {
    bottom: 52px;
    transform: none;
  }
}

@media (min-width: 761px) and (max-width: 1120px) {
  .marketing-hero {
    padding-left: 166px;
  }
  .marketing-copy {
    position: static;
    transform: none;
  }
  .marketing-main {
    width: 658px;
    max-width: 658px;
    transform: translateY(-154px);
  }
  .marketing-kicker {
    margin-bottom: 18px;
    font-size: 22px;
    line-height: 1.1;
  }
  .marketing-title {
    font-size: 82px;
    line-height: 1.08;
  }
  .marketing-title-cn {
    margin-top: 18px;
    font-size: 48px;
    line-height: 1.18;
  }
  .marketing-side {
    right: 50px;
    bottom: 34px;
    width: clamp(360px, 38vw, 410px);
    transform: none;
  }
  .marketing-side-title {
    margin-bottom: 10px;
    font-size: 28px;
    line-height: 1.15;
  }
  .marketing-side-desc {
    font-size: 18px;
    line-height: 1.65;
  }
  .marketing-cta-row {
    gap: 18px;
    margin-top: 10px;
  }
  .marketing-cta-row .marketing-primary,
  .marketing-cta-row .marketing-secondary {
    height: 56px;
    min-width: 0;
    padding: 0 20px;
    font-size: 15px;
  }
}

@media (min-width: 761px) and (max-width: 1120px) and (max-height: 720px) {
  .marketing-main {
    transform: translateY(-154px);
  }
  .marketing-side {
    bottom: 34px;
  }
}

.marketing-scroll-hint {
  position: absolute;
  left: 50%;
  bottom: 44px;
  transform: translateX(-50%);
  color: rgba(23,21,18,.38);
  font-size: 13px;
  animation: marketingHintPulse 1.8s ease-in-out infinite;
}
.marketing-critical {
  position: relative;
  scroll-snap-align: start;
  scroll-snap-stop: normal;
  height: 100dvh;
  min-height: 100dvh;
  overflow: hidden;
  padding: 108px 56px 70px;
  background:
    radial-gradient(circle at 82% 20%, rgba(197,122,36,.12), transparent 25rem),
    radial-gradient(circle at 18% 82%, rgba(49,95,85,.08), transparent 22rem),
    linear-gradient(180deg, #f2eee5, #faf7ef);
  box-sizing: border-box;
}
.marketing-critical::before {
  content: "";
  position: absolute;
  inset: auto auto -26%;
  left: -18%;
  width: 52%;
  height: 74%;
  pointer-events: none;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(20,17,14,.055), rgba(20,17,14,.02) 52%, transparent 72%);
  opacity: .72;
  transform: rotate(-12deg);
}
.marketing-critical::after {
  display: none;
}
.marketing-section-head {
  position: relative;
  z-index: 1;
  text-align: center;
  min-height: 286px;
}
.marketing-section-watermark {
  position: absolute;
  left: 50%;
  top: -34px;
  transform: translateX(-50%);
  z-index: -1;
  color: rgba(23,21,18,.035);
  font: 850 clamp(72px, 8vw, 126px)/1 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  white-space: nowrap;
  pointer-events: none;
}
.marketing-section-label {
  display: block;
  width: fit-content;
  margin: 0 auto 16px;
  padding: 10px 16px;
  border: 1px solid rgba(23,21,18,.1);
  border-radius: 999px;
  color: rgba(197,122,36,.9);
  background: rgba(255,255,255,.34);
  font: 760 14px/1 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.marketing-section-sub {
  display: block;
  margin-top: 18px;
  color: rgba(23,21,18,.52);
  font-size: 20px;
  line-height: 1.6;
}
.marketing-critical-title {
  display: block;
  margin: 0 auto;
  max-width: 1120px;
  font: 800 clamp(42px, 4.1vw, 60px)/1.14 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.18;
  letter-spacing: 0;
  text-align: center;
}
.marketing-cards {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) 300px;
  gap: 20px;
  align-items: stretch;
  width: min(100%, 1260px);
  margin: 42px auto 0;
  border: 0;
}
.marketing-card,
.marketing-console {
  opacity: 0;
  transform: translateY(28px);
  transition: opacity .7s ease, transform .7s cubic-bezier(.2,.8,.2,1);
}
.marketing-critical.is-visible .marketing-card,
.marketing-critical.is-visible .marketing-console {
  opacity: 1;
  transform: translateY(0);
}
.marketing-card {
  position: relative;
  min-height: 328px;
  padding: 28px 26px 26px;
  border: 1px solid rgba(23,21,18,.08);
  border-radius: 18px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.7), rgba(255,255,255,.34)),
    radial-gradient(circle at 82% 0%, rgba(197,122,36,.1), transparent 12rem);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8), 0 20px 64px rgba(36,30,22,.06);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  overflow: hidden;
  transition: opacity .7s ease, transform .7s cubic-bezier(.2,.8,.2,1), box-shadow .24s ease, background .24s ease;
}
.marketing-card::before {
  content: "";
  position: absolute;
  left: 26px;
  right: 26px;
  top: 18px;
  height: 1px;
  background: linear-gradient(90deg, rgba(197,122,36,.64), rgba(197,122,36,0));
}
.marketing-card:hover {
  transform: translateY(-4px);
  background:
    linear-gradient(180deg, rgba(255,255,255,.78), rgba(255,255,255,.42)),
    radial-gradient(circle at 82% 0%, rgba(197,122,36,.14), transparent 12rem);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.86), 0 28px 72px rgba(36,30,22,.1);
}
.marketing-card + .marketing-card {
  border-left: 0;
}
.marketing-card:nth-child(2) { transition-delay: .12s; }
.marketing-card:nth-child(3) { transition-delay: .24s; }
.marketing-card-kicker {
  display: block;
  margin: 4px 0 14px;
  color: rgba(197,122,36,.86);
  font: 760 13px/1.2 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  letter-spacing: .04em;
}
.marketing-card-title {
  display: block;
  margin: 0 0 20px;
  max-width: 360px;
  font-size: clamp(27px, 2.25vw, 36px);
  line-height: 1.24;
  font-weight: 700;
}
.marketing-card-desc {
  display: block;
  color: rgba(23,21,18,.64);
  line-height: 1.72;
  font-size: 15px;
}
.marketing-card-tags {
  display: block;
  margin-top: auto;
  padding-top: 30px;
  color: rgba(23,21,18,.46);
  font: 650 13px/1.4 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.marketing-card-visual {
  position: relative;
  left: auto;
  right: auto;
  top: auto;
  height: 118px;
  margin: 6px 0 16px;
  pointer-events: none;
}
.marketing-mini-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.marketing-path,
.marketing-ring,
.marketing-window,
.marketing-sweep,
.marketing-time-ring,
.marketing-time-marks,
.marketing-time-hand,
.marketing-time-window {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.marketing-path-soft {
  stroke: rgba(23,21,18,.12);
  stroke-width: 2;
}
.marketing-path-main {
  stroke: rgba(197,122,36,.72);
  stroke-width: 2.4;
  stroke-dasharray: 260;
  stroke-dashoffset: 260;
}
.marketing-ring {
  stroke: rgba(49,95,85,.22);
  stroke-width: 2;
  transform-box: fill-box;
  transform-origin: center;
}
.marketing-window {
  stroke: rgba(23,21,18,.16);
  stroke-width: 2;
  fill: rgba(197,122,36,.055);
}
.marketing-sweep {
  stroke: rgba(197,122,36,.66);
  stroke-width: 3;
  stroke-dasharray: 74;
  stroke-dashoffset: 74;
}
.marketing-time-ring {
  stroke: rgba(23,21,18,.14);
  stroke-width: 2;
}
.marketing-time-ring-inner {
  stroke: rgba(49,95,85,.2);
}
.marketing-time-marks {
  stroke: rgba(23,21,18,.18);
  stroke-width: 2.2;
}
.marketing-time-rotor {
  transform-box: view-box;
  transform-origin: 110px 52px;
}
.marketing-time-hand {
  stroke-width: 3.1;
}
.marketing-time-hand-main {
  stroke: rgba(197,122,36,.74);
}
.marketing-time-hand-soft {
  stroke: rgba(103,118,108,.66);
}
.marketing-time-window {
  stroke: rgba(197,122,36,.76);
  stroke-width: 3.4;
}
.marketing-time-dot {
  fill: rgba(197,122,36,.62);
  opacity: .82;
  filter: drop-shadow(0 0 5px rgba(197,122,36,.24));
}
.marketing-time-dot-soft {
  fill: rgba(197,122,36,.42);
  opacity: .58;
}
.marketing-node {
  fill: rgba(197,122,36,.78);
  opacity: .32;
  transform-box: fill-box;
  transform-origin: center;
}
.marketing-critical.is-visible .marketing-path-main {
  animation: marketingDrawPath 1.4s cubic-bezier(.2,.8,.2,1) .16s both;
}
.marketing-critical.is-visible .marketing-sweep {
  animation: marketingDrawPath .9s cubic-bezier(.2,.8,.2,1) .54s both;
}
.marketing-critical.is-visible .marketing-time-rotor {
  animation: marketingClockRotate 7.2s linear .25s infinite;
}
.marketing-critical.is-visible .marketing-ring.r1 {
  animation: marketingPulseRing 3.2s ease-in-out .18s infinite;
}
.marketing-critical.is-visible .marketing-ring.r2 {
  animation: marketingPulseRing 3.2s ease-in-out .62s infinite;
}
.marketing-critical.is-visible .marketing-node {
  animation: marketingNodeGlow 2.4s ease-in-out infinite;
}
.marketing-critical.is-visible .marketing-node.n2 { animation-delay: .26s; }
.marketing-critical.is-visible .marketing-node.n3 { animation-delay: .52s; }
.marketing-visual-line {
  position: absolute;
  left: 24%;
  right: 12%;
  top: 44px;
  height: 1px;
  background: rgba(23,21,18,.12);
}
.marketing-visual-line::before,
.marketing-visual-line::after,
.marketing-visual-dot {
  content: "";
  position: absolute;
  top: -7px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: rgba(23,21,18,.18);
}
.marketing-visual-line::before { left: 10%; }
.marketing-visual-line::after { right: 0; background: rgba(197,122,36,.72); }
.marketing-visual-dot { left: 66%; top: 37px; }
.marketing-card-visual-b {
  display: flex;
  justify-content: center;
  align-items: center;
}
.marketing-visual-ring {
  width: 74px;
  height: 74px;
  border: 2px solid rgba(197,122,36,.28);
  border-radius: 50%;
}
.marketing-visual-ring + .marketing-visual-ring {
  margin-left: -18px;
  border-color: rgba(108,70,140,.18);
}
.marketing-visual-alert {
  position: absolute;
  left: 46%;
  top: 18px;
  width: 54px;
  height: 54px;
  clip-path: polygon(50% 0, 100% 92%, 0 92%);
  border: 0;
  background: rgba(214,88,72,.18);
}
.marketing-visual-alert::after {
  content: "!";
  position: absolute;
  inset: 12px 0 0;
  text-align: center;
  color: rgba(214,88,72,.72);
  font: 800 34px/1 ui-sans-serif, system-ui, sans-serif;
}
.marketing-visual-planet {
  position: absolute;
  right: 8%;
  top: 28px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(197,122,36,.62);
}
.marketing-console {
  position: relative;
  min-height: 328px;
  padding: 28px;
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 18px;
  background:
    radial-gradient(circle at 72% 18%, rgba(197,122,36,.2), transparent 10rem),
    linear-gradient(180deg, rgba(31,27,23,.92), rgba(17,15,13,.96));
  color: white;
  overflow: hidden;
  box-sizing: border-box;
  transition-delay: .36s;
}
.marketing-console::after {
  content: "";
  position: absolute;
  inset: auto 24px 24px;
  height: 78px;
  border: 1px solid rgba(197,122,36,.18);
  border-radius: 999px;
  transform: rotate(-12deg);
}
.marketing-console-title,
.marketing-console-line {
  display: block;
}
.marketing-console-title {
  color: rgba(255,255,255,.88);
  font: 700 15px/1.2 ui-sans-serif, system-ui, sans-serif;
}
.marketing-console-line {
  height: 28px;
  margin-top: 16px;
  border-radius: 999px;
  background: rgba(255,255,255,.13);
}
.marketing-console-line:first-of-type {
  background: var(--marketing-copper);
}

/* 第3页：产品推理 */
.marketing-tools {
  position: relative;
  scroll-snap-align: start;
  scroll-snap-stop: normal;
  height: 100dvh;
  min-height: 100dvh;
  overflow: hidden;
  padding: 108px 72px 86px;
  background:
    radial-gradient(circle at 14% 70%, rgba(197,122,36,.1), transparent 22rem),
    radial-gradient(circle at 82% 22%, rgba(49,95,85,.12), transparent 24rem),
    linear-gradient(180deg, #faf7ef, #f2eee5);
  box-sizing: border-box;
  display: grid;
  grid-template-columns: minmax(360px, .66fr) minmax(560px, .98fr);
  gap: 76px;
  align-items: center;
}
.marketing-tools::before {
  content: "";
  position: absolute;
  left: -10%;
  top: 10%;
  width: 44%;
  height: 64%;
  border: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(20,17,14,.045), transparent 68%);
  transform: rotate(-18deg);
  pointer-events: none;
}
.marketing-product-copy,
.marketing-engine {
  position: relative;
  z-index: 1;
}
.marketing-tools .marketing-product-copy,
.marketing-tools .marketing-engine {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity .7s ease, transform .7s cubic-bezier(.2,.8,.2,1);
}
.marketing-tools.is-visible .marketing-product-copy,
.marketing-tools.is-visible .marketing-engine {
  opacity: 1;
  transform: translateY(0);
}
.marketing-tools.is-visible .marketing-engine {
  transition-delay: .12s;
}
.marketing-product-title {
  display: block;
  margin: 18px 0 18px;
  max-width: 620px;
  font-size: clamp(38px, 3.45vw, 52px);
  line-height: 1.18;
  font-weight: 780;
  letter-spacing: 0;
}
.marketing-product-title-line {
  display: block;
  white-space: nowrap;
}
.marketing-product-title-line + .marketing-product-title-line {
  margin-top: 6px;
}
.marketing-product-sub {
  display: block;
  margin-bottom: 56px;
  color: rgba(197,122,36,.78);
  font: 600 24px/1.3 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.marketing-product-lead {
  display: block;
  max-width: 560px;
  color: rgba(23,21,18,.62);
  font-size: 18px;
  line-height: 1.9;
}
.marketing-product-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0;
  max-width: 560px;
  margin-top: 54px;
  border-top: 1px solid rgba(23,21,18,.12);
  border-bottom: 1px solid rgba(23,21,18,.12);
}
.marketing-stat {
  padding: 20px 22px;
}
.marketing-stat + .marketing-stat {
  border-left: 1px solid rgba(23,21,18,.12);
}
.marketing-stat-number {
  display: block;
  font: 780 34px/1 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.marketing-stat-label {
  display: block;
  margin-top: 10px;
  color: rgba(23,21,18,.5);
  font-size: 14px;
}
.marketing-engine {
  position: relative;
  min-height: 504px;
  border-radius: 24px;
  padding: 30px;
  border: 1px solid rgba(255,255,255,.12);
  background:
    radial-gradient(circle at 78% 18%, rgba(197,122,36,.25), transparent 14rem),
    radial-gradient(circle at 14% 88%, rgba(49,95,85,.18), transparent 16rem),
    linear-gradient(180deg, rgba(32,29,26,.88), rgba(15,13,12,.96) 72%);
  color: white;
  box-shadow: 0 42px 100px rgba(20,17,14,.28);
  box-sizing: border-box;
  overflow: hidden;
}
.marketing-engine::before {
  content: "";
  position: absolute;
  inset: 24px;
  border: 1px solid rgba(197,122,36,.12);
  border-radius: 18px;
  pointer-events: none;
}
.marketing-engine-browser {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}
.marketing-engine-browser text {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255,255,255,.18);
}
.marketing-engine-ui {
  display: grid;
  grid-template-columns: 132px minmax(0, 1fr) 220px;
  gap: 18px;
  min-height: 408px;
}
.marketing-engine-sidebar,
.marketing-engine-chat,
.marketing-engine-chart {
  border-radius: 14px;
  background: rgba(255,255,255,.065);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.08);
}
.marketing-engine-sidebar {
  padding: 18px 14px;
}
.marketing-engine-brand,
.marketing-engine-item,
.marketing-engine-bubble,
.marketing-engine-report-title,
.marketing-engine-report-line {
  display: block;
}
.marketing-engine-brand {
  margin-bottom: 24px;
  color: rgba(255,255,255,.78);
  font: 700 12px/1.2 ui-sans-serif, system-ui, sans-serif;
}
.marketing-engine-item {
  margin-top: 10px;
  padding: 9px 10px;
  border-radius: 8px;
  color: rgba(255,255,255,.52);
  font: 600 12px/1 ui-sans-serif, system-ui, sans-serif;
}
.marketing-engine-item.is-active {
  background: rgba(197,122,36,.72);
  color: white;
}
.marketing-engine-chat {
  padding: 28px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.075), rgba(255,255,255,.045)),
    rgba(255,255,255,.05);
}
.marketing-engine-bubble {
  width: max-content;
  max-width: 80%;
  margin-left: auto;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255,255,255,.09);
  color: rgba(255,255,255,.78);
  font: 600 12px/1.2 ui-sans-serif, system-ui, sans-serif;
}
.marketing-engine-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 24px;
}
.marketing-engine-steps text {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  border-radius: 999px;
  color: rgba(255,255,255,.52);
  background: rgba(255,255,255,.055);
  font: 700 11px/1 ui-sans-serif, system-ui, sans-serif;
}
.marketing-tools.is-visible .marketing-engine-steps text {
  animation: marketingStepGlow 3.6s ease-in-out infinite;
}
.marketing-tools.is-visible .marketing-engine-steps text:nth-child(2) { animation-delay: .42s; }
.marketing-tools.is-visible .marketing-engine-steps text:nth-child(3) { animation-delay: .84s; }
.marketing-engine-report {
  position: relative;
  overflow: hidden;
  margin-top: 38px;
  padding: 22px;
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.06), rgba(0,0,0,.2)),
    rgba(0,0,0,.2);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.08);
}
.marketing-engine-report::after {
  content: "";
  position: absolute;
  inset: 0 auto 0 -48%;
  width: 42%;
  background: linear-gradient(90deg, transparent, rgba(197,122,36,.18), transparent);
  transform: skewX(-18deg);
  opacity: 0;
}
.marketing-tools.is-visible .marketing-engine-report::after {
  animation: marketingReportSweep 3.8s ease-in-out .6s infinite;
}
.marketing-engine-report-title {
  margin-bottom: 18px;
  font: 700 15px/1.2 ui-sans-serif, system-ui, sans-serif;
}
.marketing-engine-report-line {
  height: 10px;
  margin-top: 12px;
  border-radius: 999px;
  background: rgba(255,255,255,.12);
}
.marketing-engine-report-line.short { width: 62%; }
.marketing-engine-chart {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 50%, rgba(197,122,36,.13), transparent 9rem),
    rgba(255,255,255,.055);
}
.marketing-engine-chart-core {
  position: absolute;
  left: 50%;
  top: 50%;
  z-index: 1;
  width: 82px;
  height: 82px;
  border-radius: 50%;
  border: 1px solid rgba(197,122,36,.52);
  background: radial-gradient(circle, rgba(197,122,36,.22), rgba(197,122,36,.04) 62%, transparent 64%);
  transform: translate(-50%, -50%);
  box-shadow: 0 0 36px rgba(197,122,36,.16);
}
.marketing-tools.is-visible .marketing-engine-chart-core {
  animation: marketingChartPulse 2.8s ease-in-out infinite;
}
.marketing-engine-chart-grid {
  position: absolute;
  inset: 20px;
  background:
    linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px);
  background-size: 42px 42px;
}
.marketing-engine-chart-line {
  position: absolute;
  display: block;
  left: 24px;
  right: 24px;
  top: 48%;
  height: 1px;
  background: rgba(255,255,255,.28);
  transform: rotate(36deg);
}
.marketing-engine-chart-line.l2 { transform: rotate(-48deg); top: 42%; }
.marketing-engine-chart-line.l3 { transform: rotate(90deg); top: 50%; }
.marketing-tools.is-visible .marketing-engine-chart-line {
  animation: marketingChartLine 4s ease-in-out infinite;
}
.marketing-tools.is-visible .marketing-engine-chart-line.l2 { animation-delay: .4s; }
.marketing-tools.is-visible .marketing-engine-chart-line.l3 { animation-delay: .8s; }

/* 第4页：术数体系 */
.marketing-core {
  position: relative;
  scroll-snap-align: start;
  scroll-snap-stop: normal;
  height: 100dvh;
  min-height: 100dvh;
  overflow: hidden;
  padding: 96px 72px 104px;
  background:
    radial-gradient(circle at 86% 30%, rgba(197,122,36,.08), transparent 26rem),
    linear-gradient(180deg, #f2eee5, #faf7ef);
  box-sizing: border-box;
  text-align: center;
}
.marketing-core::before {
  content: "";
  position: absolute;
  right: -15%;
  top: 6%;
  width: 44%;
  height: 92%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(20,17,14,.045), transparent 68%);
  pointer-events: none;
}
.marketing-system-head {
  position: relative;
  z-index: 1;
  max-width: 980px;
  margin: 0 auto;
  text-align: center;
}
.marketing-system-head .marketing-critical-title {
  max-width: none;
  font-size: clamp(38px, 4vw, 58px);
}
.marketing-system-head .marketing-section-sub {
  margin-top: 12px;
}
.marketing-system-head .marketing-product-stats {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 22px auto 0;
  max-width: 360px;
}
.marketing-system-body {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
  align-items: stretch;
  max-width: 1160px;
  margin: 34px auto 0;
}
.marketing-system-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 332px;
  padding: 28px 26px 30px;
  border: 1px solid rgba(23,21,18,.1);
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.44), rgba(255,255,255,.16)),
    radial-gradient(circle at 50% 16%, rgba(197,122,36,.08), transparent 13rem);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.58), 0 18px 58px rgba(36,30,22,.045);
  box-sizing: border-box;
  opacity: 0;
  transform: translateY(28px);
  transition: opacity .68s ease, transform .68s cubic-bezier(.2,.8,.2,1), box-shadow .24s ease, background .24s ease;
}
.marketing-core.is-visible .marketing-system-item {
  opacity: 1;
  transform: translateY(0);
}
.marketing-core.is-visible .marketing-system-item:nth-child(2) { transition-delay: .12s; }
.marketing-core.is-visible .marketing-system-item:nth-child(3) { transition-delay: .24s; }
.marketing-system-item:hover {
  transform: translateY(-5px);
  background:
    linear-gradient(180deg, rgba(255,255,255,.58), rgba(255,255,255,.2)),
    radial-gradient(circle at 50% 16%, rgba(197,122,36,.12), transparent 13rem);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.66), 0 24px 64px rgba(36,30,22,.08);
}
.marketing-system-item-bazi,
.marketing-system-item-ziwei,
.marketing-system-item-qimen {
  grid-area: auto;
}
.marketing-system-item-qimen {
}
.marketing-system-visual {
  width: 178px;
  max-width: 100%;
  aspect-ratio: 1;
  margin: 0 auto 20px;
  color: rgba(44,41,36,.22);
  filter: drop-shadow(0 18px 30px rgba(90,68,38,.07));
}
.marketing-system-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.marketing-spin-slow,
.marketing-spin-reverse {
  transform-box: fill-box;
  transform-origin: center;
}
.marketing-spin-slow {
  animation: marketingSystemSpin 44s linear infinite;
}
.marketing-spin-reverse {
  animation: marketingSystemSpinReverse 58s linear infinite;
}
.marketing-system-item-ziwei .marketing-spin-slow {
  animation-duration: 52s;
}
.marketing-system-item-qimen .marketing-spin-slow {
  animation-duration: 64s;
}
.marketing-system-item-qimen .marketing-spin-reverse {
  animation-duration: 46s;
}
@keyframes marketingSystemSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes marketingSystemSpinReverse {
  from { transform: rotate(0deg); }
  to { transform: rotate(-360deg); }
}
@keyframes marketingDrawPath {
  from { stroke-dashoffset: 260; opacity: .18; }
  to { stroke-dashoffset: 0; opacity: 1; }
}
@keyframes marketingPulseRing {
  0%, 100% { opacity: .38; transform: scale(.94); }
  50% { opacity: .78; transform: scale(1.05); }
}
@keyframes marketingNodeGlow {
  0%, 100% { opacity: .34; transform: scale(.9); }
  50% { opacity: 1; transform: scale(1.18); }
}
@keyframes marketingClockRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes marketingStepGlow {
  0%, 100% { color: rgba(255,255,255,.46); background: rgba(255,255,255,.055); }
  38% { color: rgba(255,255,255,.96); background: rgba(197,122,36,.56); }
  68% { color: rgba(255,255,255,.62); background: rgba(255,255,255,.075); }
}
@keyframes marketingReportSweep {
  0% { left: -48%; opacity: 0; }
  18% { opacity: 1; }
  52% { left: 110%; opacity: 0; }
  100% { left: 110%; opacity: 0; }
}
@keyframes marketingChartPulse {
  0%, 100% { transform: translate(-50%, -50%) scale(.92); opacity: .62; }
  50% { transform: translate(-50%, -50%) scale(1.08); opacity: 1; }
}
@keyframes marketingChartLine {
  0%, 100% { opacity: .24; }
  50% { opacity: .72; }
}
.marketing-system-copy {
  max-width: 280px;
  margin: 0 auto;
  text-align: center;
}
.marketing-system-title {
  display: block;
  margin-bottom: 14px;
  color: rgba(197,122,36,.78);
  font-size: 21px;
  font-weight: 760;
}
.marketing-system-title text {
  margin-left: 14px;
  color: rgba(23,21,18,.38);
  font-style: italic;
  font-weight: 520;
}
.marketing-system-desc {
  display: block;
  color: rgba(23,21,18,.56);
  font-size: 16px;
  line-height: 1.72;
}

/* 第5页：FAQ+Footer */
.marketing-final {
  position: relative;
  scroll-snap-align: start;
  scroll-snap-stop: normal;
  height: 100dvh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: clamp(20px, 3.4vh, 38px);
  padding: 104px 72px 44px;
  background:
    radial-gradient(circle at 86% 45%, rgba(23,21,18,.06), transparent 26rem),
    linear-gradient(180deg, #faf7ef, #f2eee5);
  color: var(--marketing-ink);
  box-sizing: border-box;
}
.marketing-final::before {
  content: "";
  position: absolute;
  right: -14%;
  top: 12%;
  width: 44%;
  height: 84%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(20,17,14,.05), transparent 68%);
  pointer-events: none;
}
.marketing-faq {
  position: relative;
  z-index: 1;
  width: min(100%, 980px);
  max-width: 980px;
  margin: 0 auto;
}
.marketing-final-content {
  position: relative;
  z-index: 1;
  text-align: center;
  width: min(100%, 980px);
  max-width: 980px;
  margin: 0 auto;
  padding: 26px 34px 28px;
  border: 1px solid rgba(23,21,18,.08);
  border-radius: 22px;
  background:
    radial-gradient(circle at 82% 18%, rgba(197,122,36,.12), transparent 11rem),
    rgba(255,255,255,.46);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.72), 0 28px 76px rgba(36,30,22,.07);
  box-sizing: border-box;
}
.marketing-final-content .marketing-final-title {
  font-size: clamp(34px, 3.1vw, 46px);
  white-space: nowrap;
}
.marketing-final-title {
  display: block;
  font-size: clamp(34px, 3.4vw, 50px);
  font-weight: 800;
  margin-bottom: 18px;
  line-height: 1.08;
}
.marketing-final-desc {
  display: block;
  font-size: 18px;
  color: rgba(23,21,18,.48);
  margin-bottom: 30px;
  line-height: 1.6;
}
.marketing-faq .marketing-final-title,
.marketing-faq .marketing-final-desc {
  text-align: center;
}
.marketing-faq-list {
  margin-top: 38px;
  border: 1px solid rgba(23,21,18,.08);
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255,255,255,.38);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.7);
}
.marketing-faq-row {
  display: block;
  min-height: 66px;
  border-top: 1px solid rgba(23,21,18,.08);
  padding: 0 22px;
  color: rgba(23,21,18,.78);
  font-size: 19px;
  font-weight: 700;
  cursor: pointer;
  opacity: 0;
  transform: translateY(18px);
  transition: opacity .56s ease, transform .56s cubic-bezier(.2,.8,.2,1), background .2s ease;
}
.marketing-faq-row:first-child {
  border-top: 0;
}
.marketing-final.is-visible .marketing-faq-row {
  opacity: 1;
  transform: translateY(0);
}
.marketing-final.is-visible .marketing-faq-row:nth-child(2) { transition-delay: .08s; }
.marketing-final.is-visible .marketing-faq-row:nth-child(3) { transition-delay: .16s; }
.marketing-final.is-visible .marketing-faq-row:nth-child(4) { transition-delay: .24s; }
.marketing-faq-row:hover {
  background: rgba(255,255,255,.24);
}
.marketing-faq-row:last-child {
  border-bottom: 0;
}
.marketing-faq-question {
  min-height: 68px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
}
.marketing-faq-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  color: rgba(23,21,18,.42);
  transition: transform .22s ease, color .22s ease;
}
.marketing-faq-row.is-open .marketing-faq-icon {
  color: rgba(197,122,36,.78);
  transform: rotate(180deg);
}
.marketing-faq-answer {
  display: block;
  max-height: 0;
  overflow: hidden;
  color: rgba(23,21,18,.56);
  font-size: 16px;
  font-weight: 520;
  line-height: 1.66;
  opacity: 0;
  transition: max-height .28s ease, opacity .22s ease, padding .22s ease;
}
.marketing-faq-row.is-open .marketing-faq-answer {
  max-height: 96px;
  padding: 0 46px 20px 0;
  opacity: 1;
}
.marketing-footer {
  grid-column: 1 / -1;
  position: relative;
  z-index: 1;
  width: min(100%, 1120px);
  margin: 0 auto;
  padding: 0;
}
.marketing-footer-text {
  display: block;
  padding-top: 18px;
  border-top: 1px solid rgba(23,21,18,.1);
  font-size: 14px;
  color: rgba(23,21,18,.38);
  text-align: center;
}
.marketing-footer-icp {
  display: block;
  margin-top: 8px;
  font-size: 12px;
  color: rgba(23,21,18,.48);
  text-align: center;
  cursor: pointer;
}

@media (max-width: 1280px) and (min-width: 761px) {
  .marketing-critical {
    padding-left: 48px;
    padding-right: 48px;
  }
  .marketing-cards {
    grid-template-columns: repeat(3, minmax(0, 1fr)) 260px;
    gap: 16px;
    margin-top: 28px;
  }
  .marketing-card {
    min-height: 300px;
    padding: 24px 20px 22px;
  }
  .marketing-card-visual {
    height: 96px;
  }
  .marketing-card-title {
    font-size: 28px;
  }
  .marketing-console {
    min-height: 300px;
    padding: 24px;
  }
  .marketing-tools {
    grid-template-columns: minmax(340px, .68fr) minmax(500px, .9fr);
    gap: 48px;
    padding-left: 56px;
    padding-right: 56px;
  }
  .marketing-engine {
    padding: 28px;
  }
  .marketing-engine-ui {
    grid-template-columns: 112px minmax(150px, 1fr) 150px;
    gap: 14px;
  }
  .marketing-engine-chart-grid {
    background-size: 34px 34px;
  }
  .marketing-core {
    padding: 78px 56px 76px;
  }
  .marketing-system-body {
    gap: 18px;
    margin-top: 22px;
  }
  .marketing-system-item {
    min-height: 304px;
    padding: 20px 20px 22px;
  }
  .marketing-system-visual {
    width: 150px;
    margin-bottom: 14px;
  }
  .marketing-system-desc {
    font-size: 15px;
    line-height: 1.55;
  }
  .marketing-final {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    gap: 22px;
    padding-left: 56px;
    padding-right: 56px;
  }
  .marketing-final-content {
    max-width: 920px;
    padding: 28px;
    text-align: center;
  }
  .marketing-final-content .marketing-final-title {
    font-size: 38px;
  }
}

@media (max-height: 760px) and (min-width: 761px) {
  .marketing-core {
    padding: 92px 56px 28px;
  }
  .marketing-system-head .marketing-critical-title {
    font-size: clamp(34px, 3.4vw, 48px);
    line-height: 1.08;
  }
  .marketing-system-head .marketing-section-sub {
    margin-top: 8px;
    font-size: 17px;
    line-height: 1.35;
  }
  .marketing-system-head .marketing-product-stats {
    margin-top: 14px;
    max-width: 330px;
  }
  .marketing-system-head .marketing-stat {
    padding: 14px 18px;
  }
  .marketing-system-head .marketing-stat-number {
    font-size: 30px;
  }
  .marketing-system-head .marketing-stat-label {
    margin-top: 7px;
    font-size: 12px;
  }
  .marketing-system-body {
    gap: 18px;
    max-width: 1120px;
    margin-top: 18px;
  }
  .marketing-system-item {
    min-height: 248px;
    padding: 14px 20px 16px;
  }
  .marketing-system-visual {
    width: 112px;
    margin-bottom: 8px;
  }
  .marketing-system-title {
    margin-bottom: 8px;
    font-size: 19px;
  }
  .marketing-system-desc {
    font-size: 14px;
    line-height: 1.45;
  }
}

@media (max-height: 690px) and (min-width: 761px) {
  .marketing-core {
    padding-top: 86px;
    padding-bottom: 22px;
  }
  .marketing-system-head .marketing-critical-title {
    font-size: clamp(30px, 3vw, 42px);
  }
  .marketing-system-head .marketing-section-sub {
    font-size: 15px;
  }
  .marketing-system-head .marketing-product-stats {
    margin-top: 10px;
  }
  .marketing-system-head .marketing-stat {
    padding: 10px 16px;
  }
  .marketing-system-body {
    margin-top: 14px;
  }
  .marketing-system-item {
    min-height: 214px;
    padding: 12px 18px 14px;
  }
  .marketing-system-visual {
    width: 94px;
    margin-bottom: 6px;
  }
  .marketing-system-desc {
    display: -webkit-box;
    overflow: hidden;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
  }
}

@keyframes marketingNavIn {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes marketingSlowSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes marketingMistDrift {
  0%, 100% { transform: translate3d(0,0,0) scale(1); }
  50% { transform: translate3d(-28px,18px,0) scale(1.04); }
}
@keyframes marketingOrbitFloat {
  0%, 100% { transform: translate3d(0,0,0); }
  50% { transform: translate3d(-34px,14px,0); }
}
@keyframes marketingOrbitRotate {
  from { transform: translate(-50%, -50%) rotate(var(--marketing-r)); }
  to { transform: translate(-50%, -50%) rotate(calc(var(--marketing-r) + 360deg)); }
}
@keyframes marketingParticleRise {
  0%, 100% { opacity: .16; transform: translateY(0) scale(.85); }
  45% { opacity: .72; transform: translateY(-24px) scale(1); }
}
@keyframes marketingHeroRise {
  from { opacity: 0; transform: translateY(28px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes marketingHintPulse {
  0%, 100% { opacity: .26; transform: translate(-50%, 0); }
  50% { opacity: .56; transform: translate(-50%, 8px); }
}
@media (prefers-reduced-motion: reduce) {
  .marketing-landing *,
  .marketing-landing *::before,
  .marketing-landing *::after {
    animation-duration: .001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .001ms !important;
  }
}
@media (min-width: 761px) {
  .marketing-final-content .marketing-final-title {
    white-space: nowrap;
  }
}
@media (max-height: 820px) and (min-width: 761px) {
  .marketing-final {
    gap: 18px;
    padding-top: 82px;
    padding-bottom: 34px;
  }
  .marketing-faq-list {
    margin-top: 26px;
  }
  .marketing-faq-row {
    min-height: 50px;
  }
  .marketing-faq .marketing-final-title {
    font-size: 44px;
    margin-bottom: 10px;
  }
  .marketing-faq .marketing-final-desc {
    margin-bottom: 0;
  }
  .marketing-final-content .marketing-final-title {
    font-size: 42px;
    margin-bottom: 10px;
  }
  .marketing-final-content .marketing-final-desc {
    margin-bottom: 16px;
  }
  .marketing-final-content .marketing-primary {
    height: 50px;
  }
}
@media (max-width: 760px) {
  .marketing-landing {
    scroll-padding-top: max(72px, calc(env(safe-area-inset-top) + 62px));
  }
  .marketing-nav {
    position: fixed;
    top: env(safe-area-inset-top);
    left: 0;
    right: 0;
    z-index: 120;
    height: 76px;
    padding: 14px 16px 10px;
    box-sizing: border-box;
    overflow: visible;
    background: linear-gradient(180deg, rgba(242,238,229,.96), rgba(242,238,229,.68) 72%, rgba(242,238,229,0));
    animation: none;
  }
  .marketing-brand {
    min-width: 0;
    gap: 8px;
    font-size: 16px;
  }
  .marketing-logo-wrap { width: 40px; height: 40px; }
  .marketing-logo { width: 30px; height: 30px; }
  .marketing-nav-links { gap: 8px; }
  .marketing-nav-links text { display: none; }
  .marketing-nav-links .marketing-agent-link {
    display: inline-flex;
    align-items: center;
    min-height: 42px;
    padding: 0 10px;
    border-radius: 999px;
    background: rgba(255,255,255,.44);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,.58);
    font: 800 13px/1 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    white-space: nowrap;
  }
  .marketing-enter {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 94px;
    min-height: 42px;
    padding: 10px 12px;
    font-size: 13px;
    line-height: 1;
    white-space: nowrap;
  }
  .marketing-hero {
    padding: max(118px, calc(env(safe-area-inset-top) + 104px)) 24px max(30px, calc(env(safe-area-inset-bottom) + 24px));
    height: 100dvh;
    min-height: 100dvh;
    align-items: flex-start;
  }
  .marketing-ambient::before,
  .marketing-ambient::after {
    content: "";
    position: absolute;
    pointer-events: none;
    border: 1px solid rgba(49,44,34,.16);
    border-radius: 50%;
    box-shadow: 0 0 28px rgba(197,122,36,.045);
  }
  .marketing-ambient::before {
    left: -42%;
    top: 19%;
    width: 168%;
    height: 48%;
    transform: rotate(-14deg);
  }
  .marketing-ambient::after {
    right: -48%;
    top: 31%;
    width: 158%;
    height: 54%;
    transform: rotate(24deg);
  }
  .marketing-orbits {
    left: -26%;
    top: 4%;
    width: 58rem;
    height: 44rem;
    opacity: .36;
  }
  .marketing-bottom-blur {
    display: none;
  }
  .marketing-copy {
    grid-template-columns: 1fr;
    gap: 18px;
    padding-bottom: 0;
    transform: none;
  }
  .marketing-main {
    transform: none;
  }
  .marketing-kicker { margin-bottom: 14px; font-size: 16px; }
  .marketing-title { font-size: clamp(42px, 12.4vw, 46px); line-height: 1.04; }
  .marketing-title-cn { margin-top: 14px; font-size: 29px; line-height: 1.14; }
  .marketing-side { margin-top: 52px; transform: none; }
  .marketing-side-title { margin-bottom: 12px; font-size: 22px; }
  .marketing-side-desc { font-size: 15px; line-height: 1.52; }
  .marketing-cta-row { gap: 10px; flex-wrap: nowrap; margin-top: 34px; }
  .marketing-primary,
  .marketing-secondary {
    height: 50px;
    min-width: 100px;
    max-width: 200px;
    width: auto;
    flex: none;
    padding: 0 18px;
    font-size: 14px;
  }
  .marketing-critical {
    height: auto;
    min-height: 100dvh;
    overflow: visible;
    padding: max(70px, calc(env(safe-area-inset-top) + 58px)) 22px max(86px, calc(env(safe-area-inset-bottom) + 78px));
    display: flex;
    flex-direction: column;
  }
  .marketing-critical::before { opacity: .28; }
  .marketing-critical::after,
  .marketing-card::before,
  .marketing-console::after {
    display: none;
  }
  .marketing-section-sub { margin-top: 10px; font-size: 13px; line-height: 1.45; }
  .marketing-section-label {
    margin-bottom: 14px;
    padding: 8px 14px;
    font-size: 14px;
  }
  .marketing-critical-title {
    margin: 2px auto 14px;
    max-width: 330px;
    font-size: 25px;
    line-height: 1.18;
  }
  .marketing-cards {
    grid-template-columns: 1fr;
    gap: 0;
    min-height: 0;
    flex: 1 1 auto;
    align-content: start;
    margin: 12px auto 0;
    border-top: 1px solid rgba(23,21,18,.12);
    border-bottom: 1px solid rgba(23,21,18,.12);
  }
  .marketing-card {
    min-height: 0;
    padding: 12px 34px 13px 0;
    border: 0;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 70px;
    column-gap: 14px;
    align-items: center;
    overflow: visible;
  }
  .marketing-card + .marketing-card {
    border-left: 0;
    border-top: 1px solid rgba(23,21,18,.1);
  }
  .marketing-console {
    min-height: 70px;
    margin-top: 8px;
    padding: 12px 14px;
    border-radius: 16px;
  }
  .marketing-console-title { font-size: 11px; }
  .marketing-console-line {
    height: 7px;
    margin-top: 7px;
  }
  .marketing-card-kicker {
    grid-column: 1;
    margin: 0 0 7px;
    font-size: 10px;
  }
  .marketing-card-visual {
    grid-column: 2;
    grid-row: 1 / span 4;
    height: 48px;
    margin: 0;
    opacity: .42;
  }
  .marketing-card-title {
    grid-column: 1;
    margin-bottom: 8px;
    max-width: none;
    font-size: 18px;
    line-height: 1.18;
  }
  .marketing-card-desc {
    grid-column: 1 / -1;
    font-size: 12px;
    line-height: 1.36;
  }
  .marketing-card-tags {
    grid-column: 1 / -1;
    margin-top: 6px;
    padding-top: 0;
    font-size: 11px;
  }

  /* 第3页：产品推理 移动端 */
  .marketing-tools {
    height: auto;
    min-height: 100dvh;
    overflow: visible;
    padding: max(70px, calc(env(safe-area-inset-top) + 58px)) 22px max(86px, calc(env(safe-area-inset-bottom) + 78px));
    grid-template-columns: 1fr;
    gap: 14px;
    align-items: start;
  }
  .marketing-tools::before {
    left: -80%;
    top: 24%;
    width: 150%;
    height: 36%;
  }
  .marketing-product-title {
    margin: 8px 0 10px;
    max-width: 100%;
    font-size: 25px;
    line-height: 1.12;
    overflow-wrap: break-word;
  }
  .marketing-product-title-line {
    white-space: normal;
  }
  .marketing-product-title-line + .marketing-product-title-line {
    margin-top: 4px;
  }
  .marketing-product-sub {
    margin-bottom: 12px;
    font-size: 15px;
  }
  .marketing-product-lead {
    max-width: 100%;
    font-size: 12px;
    line-height: 1.48;
  }
  .marketing-product-stats {
    margin-top: 16px;
  }
  .marketing-stat {
    padding: 12px 10px;
  }
  .marketing-stat-number {
    font-size: 24px;
  }
  .marketing-stat-label {
    margin-top: 6px;
    font-size: 11px;
  }
  .marketing-engine {
    min-height: 0;
    padding: 12px;
    border-radius: 10px;
    box-shadow: 0 20px 52px rgba(20,17,14,.18);
  }
  .marketing-engine-browser {
    margin-bottom: 9px;
  }
  .marketing-engine-ui {
    grid-template-columns: 82px minmax(0, 1fr);
    gap: 8px;
    min-height: 204px;
  }
  .marketing-engine-sidebar,
  .marketing-engine-chat {
    border-radius: 10px;
  }
  .marketing-engine-sidebar {
    padding: 11px 8px;
  }
  .marketing-engine-brand {
    margin-bottom: 12px;
    font-size: 9px;
  }
  .marketing-engine-item {
    margin-top: 7px;
    padding: 7px;
    font-size: 9px;
  }
  .marketing-engine-chat {
    padding: 12px;
  }
  .marketing-engine-bubble {
    max-width: 92%;
    padding: 7px 9px;
    font-size: 9px;
  }
  .marketing-engine-steps {
    gap: 5px;
    margin-top: 14px;
  }
  .marketing-engine-steps text {
    min-height: 24px;
    font-size: 9px;
  }
  .marketing-engine-report {
    margin-top: 16px;
    padding: 12px;
    border-radius: 10px;
  }
  .marketing-engine-report-title {
    margin-bottom: 12px;
    font-size: 12px;
  }
  .marketing-engine-report-line {
    height: 8px;
    margin-top: 9px;
  }
  .marketing-engine-chart {
    display: none;
  }
  .marketing-engine-top {
    padding-bottom: 12px;
  }
  .marketing-engine-title {
    font-size: 14px;
  }
  .marketing-engine-status {
    min-height: 24px;
    padding: 0 10px;
    font-size: 10px;
  }
  .marketing-engine-step {
    grid-template-columns: 34px minmax(0, 1fr);
    gap: 10px;
    padding: 12px 0;
  }
  .marketing-engine-index {
    font-size: 15px;
  }
  .marketing-engine-name {
    margin-bottom: 4px;
    font-size: 15px;
  }
  .marketing-engine-desc {
    font-size: 11px;
    line-height: 1.45;
  }

  /* 第4页：核心3点 移动端 */
  .marketing-core {
    height: auto;
    min-height: 100dvh;
    overflow: visible;
    padding: max(70px, calc(env(safe-area-inset-top) + 58px)) 22px max(86px, calc(env(safe-area-inset-bottom) + 78px));
    display: flex;
    flex-direction: column;
  }
  .marketing-system-head {
    max-width: 100%;
  }
  .marketing-system-head .marketing-critical-title {
    font-size: 24px;
    line-height: 1.18;
  }
  .marketing-system-head .marketing-product-stats {
    margin-top: 14px;
    max-width: 260px;
  }
  .marketing-system-body {
    grid-template-columns: 1fr;
    grid-template-areas:
      "bazi"
      "ziwei"
      "qimen";
    gap: 14px;
    margin-top: 18px;
  }
  .marketing-system-item-bazi { grid-area: bazi; }
  .marketing-system-item-ziwei { grid-area: ziwei; }
  .marketing-system-item-qimen { grid-area: qimen; }
  .marketing-system-item,
  .marketing-system-item-qimen {
    grid-template-columns: 98px minmax(0, 1fr);
    gap: 14px;
    min-height: 88px;
    margin-top: 0;
    padding: 0;
    border: 0;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
    display: grid;
    text-align: left;
  }
  .marketing-system-visual {
    width: 86px;
    min-width: 86px;
    margin: 0;
  }
  .marketing-system-copy {
    max-width: none;
    margin: 0;
    text-align: left;
  }
  .marketing-system-title {
    margin-bottom: 8px;
    font-size: 16px;
  }
  .marketing-system-desc {
    display: -webkit-box;
    overflow: hidden;
    font-size: 12px;
    line-height: 1.42;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
  }

  /* 第5页：底部CTA+Footer 移动端 */
  .marketing-final {
    height: 100dvh;
    min-height: 100dvh;
    overflow: clip;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    gap: 14px;
    padding: max(78px, calc(env(safe-area-inset-top) + 66px)) 22px max(20px, calc(env(safe-area-inset-bottom) + 16px));
    background:
      radial-gradient(circle at 50% 78%, rgba(197,122,36,.08), transparent 15rem),
      radial-gradient(circle at 86% 38%, rgba(23,21,18,.045), transparent 16rem),
      linear-gradient(180deg, #faf7ef, #f2eee5);
  }
  .marketing-faq {
    width: 100%;
    max-width: none;
  }
  .marketing-faq .marketing-final-title,
  .marketing-faq .marketing-final-desc {
    text-align: center;
  }
  .marketing-faq-list {
    margin-top: 18px;
    border-radius: 12px;
  }
  .marketing-faq-row {
    min-height: 46px;
    padding: 0 14px;
    font-size: 13px;
  }
  .marketing-faq-question {
    min-height: 46px;
    gap: 14px;
  }
  .marketing-faq-answer {
    font-size: 12px;
    line-height: 1.48;
  }
  .marketing-faq-row.is-open .marketing-faq-answer {
    max-height: 74px;
    padding: 0 30px 10px 0;
  }
  .marketing-final-title {
    font-size: 30px;
    margin-bottom: 10px;
  }
  .marketing-final-content .marketing-final-title {
    max-width: 100%;
    font-size: 25px;
    line-height: 1.18;
    white-space: normal;
    overflow-wrap: break-word;
  }
  .marketing-final-content {
    width: 100%;
    max-width: none;
    padding: 22px 18px 24px;
    border: 1px solid rgba(23,21,18,.08);
    border-radius: 18px;
    background:
      radial-gradient(circle at 82% 18%, rgba(197,122,36,.12), transparent 9rem),
      rgba(255,255,255,.46);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.7), 0 22px 56px rgba(36,30,22,.07);
    text-align: center;
  }
  .marketing-final-desc {
    font-size: 14px;
    margin-bottom: 22px;
  }
  .marketing-final-content .marketing-primary {
    height: 48px;
    min-width: 112px;
  }
  .marketing-footer {
    width: 100%;
    margin-top: 0;
  }
  .marketing-footer-text {
    font-size: 13px;
  }

  .page-root.marketing-android-active .marketing-nav {
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    background: linear-gradient(180deg, rgba(242,238,229,.98), rgba(242,238,229,.72) 72%, rgba(242,238,229,0));
    transform: translateZ(0);
  }
  .page-root.marketing-android-active .marketing-mist {
    filter: none;
    opacity: .28;
    animation: none;
  }
  .page-root.marketing-android-active .marketing-bottom-blur {
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
  }
  .page-root.marketing-android-active .marketing-orbits {
    opacity: .34;
    animation: none;
    transform: translateZ(0);
  }
  .page-root.marketing-android-active .marketing-orbit {
    animation-duration: 120s;
    will-change: transform;
  }
  .page-root.marketing-android-active .marketing-particle {
    animation: none;
    opacity: .42;
    box-shadow: none;
    will-change: auto;
  }
  .page-root.marketing-android-active .marketing-particle-26,
  .page-root.marketing-android-active .marketing-particle-27,
  .page-root.marketing-android-active .marketing-particle-28,
  .page-root.marketing-android-active .marketing-particle-29,
  .page-root.marketing-android-active .marketing-particle-30,
  .page-root.marketing-android-active .marketing-particle-31,
  .page-root.marketing-android-active .marketing-particle-32,
  .page-root.marketing-android-active .marketing-particle-33,
  .page-root.marketing-android-active .marketing-particle-34,
  .page-root.marketing-android-active .marketing-particle-35,
  .page-root.marketing-android-active .marketing-particle-36,
  .page-root.marketing-android-active .marketing-particle-37,
  .page-root.marketing-android-active .marketing-particle-38,
  .page-root.marketing-android-active .marketing-particle-39,
  .page-root.marketing-android-active .marketing-particle-40,
  .page-root.marketing-android-active .marketing-particle-41,
  .page-root.marketing-android-active .marketing-particle-42,
  .page-root.marketing-android-active .marketing-particle-43,
  .page-root.marketing-android-active .marketing-particle-44,
  .page-root.marketing-android-active .marketing-particle-45,
  .page-root.marketing-android-active .marketing-particle-46,
  .page-root.marketing-android-active .marketing-particle-47,
  .page-root.marketing-android-active .marketing-particle-48,
  .page-root.marketing-android-active .marketing-particle-49,
  .page-root.marketing-android-active .marketing-particle-50 {
    display: none;
  }
  .page-root.marketing-android-active .marketing-kicker,
  .page-root.marketing-android-active .marketing-title,
  .page-root.marketing-android-active .marketing-title-cn,
  .page-root.marketing-android-active .marketing-side-title,
  .page-root.marketing-android-active .marketing-side-desc,
  .page-root.marketing-android-active .marketing-cta-row {
    animation: none;
  }
  .page-root.marketing-android-active .marketing-title {
    opacity: 1;
  }
}
@media (max-width: 760px) and (max-height: 700px) {
  .marketing-hero {
    padding-top: max(108px, calc(env(safe-area-inset-top) + 94px));
    padding-bottom: max(22px, calc(env(safe-area-inset-bottom) + 18px));
  }
  .marketing-copy { gap: 12px; }
  .marketing-kicker { margin-bottom: 10px; font-size: 15px; }
  .marketing-title { font-size: clamp(39px, 11.4vw, 44px); }
  .marketing-title-cn { margin-top: 10px; font-size: 27px; }
  .marketing-side { margin-top: 40px; transform: none; }
  .marketing-side-title { margin-bottom: 8px; font-size: 21px; }
  .marketing-side-desc { font-size: 14px; line-height: 1.45; }
  .marketing-cta-row { margin-top: 28px; }
  .marketing-primary,
  .marketing-secondary { height: 48px; }
  .marketing-critical {
    padding-top: max(78px, calc(env(safe-area-inset-top) + 66px));
    padding-bottom: max(86px, calc(env(safe-area-inset-bottom) + 78px));
  }
  .marketing-critical-title { margin-bottom: 12px; font-size: 23px; }
  .marketing-cards { gap: 0; margin-top: 12px; }
  .marketing-card { padding: 9px 26px 9px 0; }
  .marketing-card-visual { height: 42px; }
  .marketing-card-title { font-size: 16px; }
  .marketing-card-desc { font-size: 11px; line-height: 1.34; }
  .marketing-console { min-height: 68px; padding: 11px 14px; }
  .marketing-console-line { height: 7px; margin-top: 7px; }
  .marketing-tools,
  .marketing-core {
    padding-top: max(70px, calc(env(safe-area-inset-top) + 58px));
    padding-bottom: max(86px, calc(env(safe-area-inset-bottom) + 78px));
  }
  .marketing-product-title { font-size: 23px; }
  .marketing-product-lead { font-size: 11px; line-height: 1.44; }
  .marketing-engine-ui { min-height: 184px; }
  .marketing-system-head .marketing-critical-title { font-size: 22px; }
  .marketing-system-body { gap: 12px; margin-top: 14px; }
  .marketing-system-item,
  .marketing-system-item-qimen {
    grid-template-columns: 76px minmax(0, 1fr);
    min-height: 80px;
  }
  .marketing-system-visual {
    width: 76px;
    min-width: 76px;
  }
  .marketing-system-title { font-size: 15px; margin-bottom: 6px; }
  .marketing-system-desc { font-size: 11px; line-height: 1.36; }
  .marketing-final {
    min-height: 100dvh;
    height: auto;
    overflow: visible;
    gap: 12px;
    padding-top: max(78px, calc(env(safe-area-inset-top) + 66px));
  }
  .marketing-final-title { font-size: 28px; }
  .marketing-faq-list { margin-top: 14px; }
  .marketing-faq-row { min-height: 42px; font-size: 12px; }
  .marketing-faq-question { min-height: 42px; }
  .marketing-final-content { padding: 18px 16px 20px; }
  .marketing-final-content .marketing-final-title { font-size: 22px; }
  .marketing-final-desc { margin-bottom: 18px; font-size: 13px; }
}
.bg-layer { position: fixed; inset: 0; z-index: 0; transition: background 0.8s var(--ease); pointer-events: none; overflow: hidden; }
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
.page-wrap { position: relative; z-index: 1; width: 100%; min-height: calc(100dvh - 60px); max-width: 100vw; overflow: visible; box-sizing: border-box; }
:global(body.home-fixed-page) .page-wrap {
  height: calc(100dvh - 60px);
  min-height: calc(100dvh - 60px);
  max-height: calc(100dvh - 60px);
  overflow: hidden;
}

@media (min-width: 769px) {
  :deep(.topnav) { padding-left: 16px; padding-right: 16px; }
  :deep(.nav-btn) { padding-left: 8px; padding-right: 8px; font-size: 0.9rem; }
  :deep(.topnav-sidebar-btn) { margin-right: 0; }
}

/* ═══ 视频背景 ═══ */
.video-bg { position: fixed; inset: 0; z-index: -1; overflow: hidden; opacity: 0; visibility: hidden; transition: opacity 0.4s ease, visibility 0.4s ease; }
.video-bg.video-visible { opacity: 1; visibility: visible; }
.video-bg-video { width: 100%; height: 100%; object-fit: cover; opacity: 0.15; filter: blur(2px) saturate(0.5); }
[data-theme="light"] .video-bg-video { opacity: 0.08; }
.video-bg-overlay { position: absolute; inset: 0; background: linear-gradient(180deg, transparent 0%, var(--bg-grad-1) 85%); }
[data-theme="dark"] .video-bg-overlay { background: linear-gradient(180deg, rgba(22,26,42,0.3) 0%, rgba(22,26,42,0.9) 85%); }
[data-theme="light"] .video-bg-overlay { background: linear-gradient(180deg, rgba(247,242,234,0.3) 0%, rgba(247,242,234,0.9) 85%); }
.video-fallback { background: linear-gradient(135deg, var(--bg-grad-1), var(--bg-grad-2), var(--bg-grad-3), var(--bg-grad-2)); background-size: 400% 400%; animation: gradientShift 12s ease infinite; }
@keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
.video-fallback .video-bg-overlay { background: linear-gradient(180deg, transparent 0%, var(--bg-grad-1) 85%) !important; }

/* ═══ 通用区块 ═══ */
.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.section-alt { background: var(--section-alt); }
.section-alt .section { background: none; }
.section-tag { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.6875rem; letter-spacing: 2px; color: var(--accent); background: var(--accent-glow); margin-bottom: 12px; }
.section-title { font-family: var(--font-serif); font-size: 1.75rem; font-weight: 400; letter-spacing: 3px; color: var(--text-1); margin-bottom: 8px; }
.section-desc { color: var(--text-3); font-size: 0.875rem; margin-bottom: 40px; max-width: 600px; }

/* ═══ Hero ═══ */
.hero-home { min-height: calc(100dvh - 60px); display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; padding: 36px 32px 154px; overflow: visible; box-sizing: border-box; }
:global(body.home-fixed-page) .hero-home {
  height: calc(100dvh - 60px);
  min-height: calc(100dvh - 60px);
  max-height: calc(100dvh - 60px);
  overflow: hidden;
}
.hero-home-content { max-width: var(--max-w); width: 100%; min-height: 0; margin: 0 auto; text-align: center; display: flex; flex-direction: column; justify-content: center; }
.hero-brand { margin-bottom: 24px; flex: 0 0 auto; }
.hero-home.chat-active { padding: 14px 32px 176px; justify-content: flex-start; }
.hero-home.chat-active .hero-home-content { justify-content: flex-start; }
.hero-home.chat-active .hero-brand { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 12px; }
.hero-home.chat-active.reading-active { padding: 0 32px var(--home-ai-dock-space); }
.hero-home.chat-active.reading-active .hero-brand { display: none; }
.hero-home.chat-active.reading-active .home-ai-console.has-chat { flex: 0 0 auto; min-height: calc(100dvh - 60px - var(--home-ai-dock-space)); }
.hero-brand-icon-wrap { position: relative; display: flex; align-items: center; justify-content: center; width: 120px; height: 120px; margin: 0 auto 16px; animation: float 6s ease-in-out infinite; }
.hero-brand-icon-wrap::before { content: ''; position: absolute; left: 50%; top: 50%; width: 100%; height: 100%; transform: translate(-50%, -50%); border-radius: 50%; background: var(--hero-logo-backdrop); box-shadow: var(--hero-logo-backdrop-shadow); z-index: 0; }
.hero-brand-icon { width: 100px; height: 100px; object-fit: cover; object-position: center center; position: relative; z-index: 1; display: block; transform: none; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
.hero-brand-name { font-family: var(--font-serif); font-size: 2.2rem; font-weight: 400; letter-spacing: 8px; color: var(--text-1); margin-bottom: 12px; background: linear-gradient(135deg, var(--text-1), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; text-indent: 12px; }
.hero-brand-divider { width: 50px; height: 2px; background: var(--accent); margin: 12px auto; border-radius: 1px; box-shadow: 0 0 12px var(--accent-glow); }
.hero-brand-slogan { font-family: var(--font-serif); font-size: 0.95rem; letter-spacing: 4px; color: var(--accent); margin-bottom: 6px; }
.hero-brand-sub { font-size: 0.78rem; color: var(--text-3); letter-spacing: 1px; }
.home-question-templates { width: min(760px, calc(100vw - 44px)); margin: 18px auto 0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; pointer-events: auto; }
.home-question-template { min-width: 0; min-height: 58px; padding: 10px 12px; border-radius: 14px; border: 1px solid rgba(178,149,93,0.16); background: rgba(255,255,255,0.045); color: var(--text-2); display: flex; flex-direction: column; align-items: flex-start; justify-content: center; gap: 4px; cursor: pointer; box-sizing: border-box; box-shadow: inset 0 1px 0 rgba(255,255,255,0.06); transition: border-color .18s ease, background .18s ease, transform .18s ease, box-shadow .18s ease; }
[data-theme="light"] .home-question-template { background: rgba(255,253,248,0.72); box-shadow: 0 8px 24px rgba(60,40,15,0.06), inset 0 1px 0 rgba(255,255,255,0.82); }
.home-question-template:hover { transform: translateY(-1px); border-color: rgba(178,149,93,0.34); background: rgba(178,149,93,0.10); box-shadow: 0 10px 28px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,0.08); }
.home-question-template-label { color: var(--accent); font-size: 0.72rem; font-weight: 800; line-height: 1.2; letter-spacing: 0; }
.home-question-template-text { width: 100%; color: var(--text-2); font-size: 0.78rem; line-height: 1.25; letter-spacing: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hero-home.chat-active .hero-brand-icon-wrap { width: 58px; height: 58px; margin: 0; animation: none; }
.hero-home.chat-active .hero-brand-icon { width: 48px; height: 48px; transform: none; }
.hero-home.chat-active .hero-brand-name { font-size: 1.28rem; letter-spacing: 5px; margin: 0; text-indent: 5px; }
.hero-home.chat-active .hero-brand-divider { display: none; }
.hero-home.chat-active .hero-brand-slogan { display: none; }
.hero-home.chat-active .hero-brand-sub { display: none; }
.hero-home.chat-active .home-question-templates { display: none; }

.home-scan-panel { width: min(920px, 100%); margin: 0 auto 18px; display: grid; grid-template-columns: 1fr; gap: 10px; flex: 0 0 auto; }
.home-scan-status { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.home-scan-status-item { min-width: 0; padding: 10px 12px; border: 1px solid rgba(178,149,93,0.14); border-radius: 12px; background: rgba(255,255,255,0.045); backdrop-filter: blur(12px); box-sizing: border-box; text-align: left; }
[data-theme="light"] .home-scan-status-item { background: rgba(255,253,248,0.56); }
.home-scan-label { display: block; font-size: 0.64rem; line-height: 1.2; color: var(--text-3); margin-bottom: 5px; }
.home-scan-value { display: block; min-width: 0; color: var(--text-1); font-size: 0.82rem; line-height: 1.25; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-scan-actions { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.home-scan-action { min-width: 0; display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 9px; row-gap: 2px; align-items: center; padding: 10px 12px; border: 1px solid rgba(178,149,93,0.16); border-radius: 14px; background: rgba(34,31,25,0.30); color: var(--text-1); cursor: pointer; box-sizing: border-box; transition: transform .18s ease, border-color .18s ease, background .18s ease; text-align: left; }
[data-theme="light"] .home-scan-action { background: rgba(255,253,248,0.62); }
.home-scan-action:hover { transform: translateY(-1px); border-color: rgba(178,149,93,0.46); background: var(--accent-glow); }
.home-scan-action-mark { grid-row: 1 / span 2; width: 28px; height: 28px; border-radius: 9px; display: flex; align-items: center; justify-content: center; background: var(--accent-glow); color: var(--accent); font-family: var(--font-serif); font-size: 0.82rem; }
.home-scan-action-main { display: block; min-width: 0; color: var(--text-1); font-size: 0.82rem; line-height: 1.2; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-scan-action-sub { display: block; min-width: 0; color: var(--text-3); font-size: 0.66rem; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ═══ 首页综合 AI 输入框 ═══ */
.home-ai-console { max-width: 920px; margin: 0 auto; padding-bottom: 0; text-align: left; display: flex; flex-direction: column; gap: 12px; width: 100%; min-height: 0; overflow: visible; box-sizing: border-box; }
.home-ai-console.has-chat { width: min(1180px, calc(100vw - 48px)); max-width: none; flex: 1 1 auto; min-height: 0; margin: 0 auto; padding: 0; box-sizing: border-box; overflow: visible; }
.home-ai-main { position: fixed; left: 50%; bottom: 14px; z-index: 260; transform: translateX(-50%); width: min(960px, calc(100vw - 36px)); box-sizing: border-box; display: flex; flex-direction: column; gap: 7px; padding: 10px 12px; border: 1px solid rgba(178,149,93,0.18); border-radius: 18px; background: rgba(34, 31, 25, 0.50); backdrop-filter: blur(30px) saturate(145%); box-shadow: 0 16px 48px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.08); overflow-x: visible; transition: border-color .2s ease, box-shadow .2s ease, background .2s ease; }
:global(body.home-fixed-page:not(:has(.home-ai-console.has-chat))) .home-ai-main {
  bottom: max(18px, calc(env(safe-area-inset-bottom) + 14px));
  max-height: min(128px, calc(100dvh - 120px));
  overflow: hidden;
}
.home-ai-main:focus-within { border-color: rgba(178,149,93,0.50); box-shadow: 0 18px 52px rgba(0,0,0,0.24), 0 0 0 3px rgba(178,149,93,0.10), inset 0 1px 0 rgba(255,255,255,0.12); }
[data-theme="light"] .home-ai-main { background: rgba(255,253,248,0.80); box-shadow: 0 12px 34px rgba(60,40,15,0.10), inset 0 1px 0 rgba(255,255,255,0.75); }
[data-theme="light"] .home-ai-main:focus-within { box-shadow: 0 14px 42px rgba(60,40,15,0.13), 0 0 0 3px rgba(150,103,20,0.10), inset 0 1px 0 rgba(255,255,255,0.82); }
.home-ai-input { width: 100%; min-height: 42px; max-height: 64px; padding: 5px 4px 0; color: var(--text-1); font-size: 0.9rem; line-height: 1.38; background: transparent !important; background-color: transparent !important; border: none; outline: none; box-sizing: border-box; appearance: none; -webkit-appearance: none; color-scheme: dark; }
[data-theme="light"] .home-ai-input { color-scheme: light; }
.home-ai-input::placeholder { color: rgba(120,108,86,0.68); }
.home-ai-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-height: 40px; flex-wrap: nowrap !important; overflow-x: visible; box-sizing: border-box; width: 100%; }
.home-ai-toolbar-left { display: flex; align-items: center; gap: 6px; flex-shrink: 1; min-width: 0; }
.home-ai-toolbar-right { display: flex; align-items: center; gap: 6px; margin-left: auto; flex-shrink: 1; min-width: 0; overflow-x: visible; box-sizing: border-box; }
.profile-picker, .tool-picker, .reading-mode-picker, .llm-picker, .home-ai-send { min-height: 36px; border-radius: 999px; border: 1px solid rgba(178,149,93,0.18); background: rgba(255,255,255,0.065); color: var(--text-1); display: flex; align-items: center; justify-content: center; cursor: pointer; box-sizing: border-box; flex-shrink: 0; transition: border-color .18s ease, background .18s ease, transform .18s ease; }
[data-theme="light"] .profile-picker, [data-theme="light"] .tool-picker, [data-theme="light"] .reading-mode-picker, [data-theme="light"] .llm-picker { background: rgba(255,251,242,0.76); }
.profile-picker:hover, .tool-picker:hover, .reading-mode-picker:hover, .llm-picker:hover { border-color: rgba(178,149,93,0.45); background: var(--accent-glow); }
.profile-picker, .tool-picker { justify-content: flex-start; gap: 6px; padding: 0 10px; max-width: 168px; min-width: 86px; flex-shrink: 1; }
.profile-plus, .tool-picker-icon { width: 20px; height: 20px; border-radius: 50%; background: var(--accent-glow); color: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; flex-shrink: 0; }
.profile-name, .tool-picker text:last-child { display: block; font-size: 0.75rem; color: var(--text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.profile-meta { display: block; margin-top: 2px; font-size: 0.66rem; color: var(--text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.llm-picker { min-width: 96px; max-width: 128px; padding: 0 10px; align-items: center; justify-content: flex-start; gap: 7px; color: var(--text-2); white-space: nowrap; flex-shrink: 1; overflow: hidden; }
.reading-mode-picker { min-width: 82px; max-width: 96px; padding: 0 10px; align-items: center; justify-content: flex-start; gap: 6px; color: var(--text-2); white-space: nowrap; flex-shrink: 0; overflow: hidden; text-align: left; }
.reading-mode-label { display: block; min-width: 0; overflow: hidden; text-overflow: ellipsis; font-size: 0.72rem; color: var(--text-1); line-height: 1; text-align: left; }
.reading-mode-name { display: block; width: 100%; overflow: hidden; text-overflow: ellipsis; font-size: 0.72rem; color: var(--text-1); line-height: 1.2; text-align: center; }
.llm-name { display: block; min-width: 0; overflow: hidden; text-overflow: ellipsis; font-size: 0.72rem; color: var(--text-1); line-height: 1; }
.llm-points { display: flex; align-items: center; height: 18px; padding: 0 6px; border-radius: 999px; background: var(--accent-glow); color: var(--accent); font-size: 0.58rem; line-height: 1; flex-shrink: 0; }
.home-ai-send { width: 36px; height: 36px; min-height: 36px; background: var(--accent); border-color: var(--accent); color: #fff; font-size: 1.1rem; font-weight: 700; line-height: 1; flex-shrink: 0; box-shadow: 0 8px 22px rgba(120,80,12,0.22); }
[data-theme="light"] .home-ai-send { background: var(--accent); border-color: var(--accent); color: #fff; }
.home-ai-send:hover { transform: translateY(-1px); }
.home-ai-send.disabled { opacity: 0.55; pointer-events: none; }
.home-ai-chat { border: 1px solid rgba(178,149,93,0.16); border-radius: 18px; background: rgba(255,255,255,0.045); backdrop-filter: blur(18px); padding: 16px; max-height: none; overflow: visible; overscroll-behavior: auto; box-shadow: inset 0 1px 0 rgba(255,255,255,0.06); }
[data-theme="light"] .home-ai-chat { background: rgba(255,253,248,0.66); }
.home-ai-console.has-chat .home-ai-chat { flex: 1 1 auto; min-height: 0; max-height: calc(100dvh - 60px - var(--home-ai-dock-space) - 14px); box-sizing: border-box; overflow-y: auto; overflow-x: hidden; -webkit-overflow-scrolling: touch; overscroll-behavior: contain; touch-action: pan-y; padding-bottom: var(--home-ai-chat-bottom-buffer); scroll-padding-bottom: var(--home-ai-chat-bottom-buffer); }
.home-ai-console.has-chat .home-ai-input { min-height: 38px; max-height: 58px; }
.home-ai-chat-head { position: relative; z-index: 1; display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 12px; margin: 0 0 12px; border: 1px solid rgba(178,149,93,0.16); border-radius: 14px; background: rgba(34,31,25,0.62); backdrop-filter: blur(18px) saturate(145%); box-shadow: 0 10px 28px rgba(0,0,0,0.12); }
[data-theme="light"] .home-ai-chat-head { background: rgba(255,251,242,0.86); box-shadow: 0 10px 28px rgba(80,55,18,0.08); }
.home-ai-chat-head-main { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.home-ai-chat-title { color: var(--text-1); font-size: 0.88rem; font-weight: 700; letter-spacing: 1px; }
.home-ai-chat-sub { color: var(--text-3); font-size: 0.72rem; line-height: 1.35; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: min(680px, 62vw); }
.home-ai-new-chat { flex-shrink: 0; height: 30px; padding: 0 12px; border-radius: 999px; display: flex; align-items: center; justify-content: center; color: var(--accent); border: 1px solid rgba(178,149,93,0.22); background: var(--accent-glow); font-size: 0.74rem; cursor: pointer; box-sizing: border-box; }
.home-ai-new-chat:hover { border-color: rgba(178,149,93,0.48); }
.home-ai-message { padding: 14px 16px; border-radius: 14px; margin-bottom: 12px; border: 1px solid rgba(178,149,93,0.14); contain: layout; overflow-anchor: none; }
.home-ai-message.user { margin-left: 72px; background: rgba(178,149,93,0.13); border-color: rgba(178,149,93,0.26); }
.home-ai-message.assistant { margin-right: 72px; background: rgba(255,255,255,0.045); }
.home-ai-role { display: block; font-size: 0.68rem; color: var(--text-3); margin-bottom: 6px; }
.home-ai-agent-head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.home-ai-agent-logo { width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0; object-fit: cover; box-shadow: 0 0 0 1px rgba(178,149,93,.18), 0 6px 16px rgba(0,0,0,.12); }
.home-ai-agent-logo.spinning { animation: stage-spin 3.2s linear infinite; }
.home-ai-agent-logo.idle { animation: none; }
.home-ai-agent-logo.small { width: 22px; height: 22px; }
.home-ai-agent-texts { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.home-ai-agent-name { color: var(--text-1); font-size: .78rem; font-weight: 800; letter-spacing: .5px; line-height: 1.15; }
.home-ai-agent-sub { color: var(--text-3); font-size: .66rem; line-height: 1.2; }
.home-ai-stage { display: inline; font-size: 0.82rem; color: var(--accent); }
.home-ai-stage-wrap { display: none; }
.home-ai-stage-logo { width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0; animation: stage-spin 1.8s linear infinite; }
.home-ai-stage-texts { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.home-ai-stage-note { color: var(--text-3); font-size: 0.68rem; line-height: 1.35; }
.home-ai-context-chip { display: flex; align-items: center; gap: 8px; margin: -2px 0 10px 34px; padding: 7px 10px; border-radius: 999px; border: 1px solid rgba(178,149,93,0.16); background: rgba(178,149,93,0.075); color: var(--text-3); font-size: 0.68rem; line-height: 1.35; }
.home-ai-context-chip text:first-child { flex: 0 0 auto; color: var(--accent); font-weight: 700; }
.home-ai-context-chip text:last-child { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.home-ai-step-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; margin: 10px 0 8px; }
.home-ai-step-row text { min-width: 0; padding: 5px 6px; border-radius: 999px; color: var(--text-3); background: rgba(178,149,93,0.08); border: 1px solid rgba(178,149,93,0.10); text-align: center; font-size: 0.64rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; box-sizing: border-box; }
.home-ai-step-row text:nth-child(1) { color: var(--accent); border-color: rgba(178,149,93,0.26); }
@keyframes stage-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.home-ai-progress-track { height: 3px; margin-top: 8px; border-radius: 999px; overflow: hidden; background: rgba(178,149,93,0.12); }
.home-ai-progress-bar { width: 38%; height: 100%; border-radius: inherit; background: linear-gradient(90deg, transparent, var(--accent), transparent); animation: progress-sweep 1.35s ease-in-out infinite; }
@keyframes progress-sweep { 0% { transform: translateX(-110%); } 100% { transform: translateX(280%); } }
.home-ai-content { display: block; white-space: pre-wrap; font-size: 0.9rem; color: var(--text-2); line-height: 1.86; letter-spacing: 0; word-break: break-word; }
.home-tool-cards { display: grid; gap: 10px; margin: 10px 0 12px; }
.home-tool-card { min-height: 92px; border: 1px solid rgba(178,149,93,0.18); border-radius: 12px; background: rgba(178,149,93,0.055); overflow: hidden; contain: layout; }
.home-artifact-switcher { display: grid; grid-template-columns: repeat(auto-fit, minmax(112px, 1fr)); gap: 8px; overflow: visible; padding: 2px 0 10px; margin-bottom: 10px; contain: layout; }
.home-artifact-switcher::-webkit-scrollbar { display: none; }
.home-artifact-tab { min-width: 0; padding: 8px 9px; border-radius: 12px; border: 1px solid rgba(178,149,93,.14); background: rgba(255,255,255,.04); cursor: pointer; box-sizing: border-box; }
.home-artifact-tab.active { border-color: rgba(178,149,93,.48); background: rgba(178,149,93,.12); box-shadow: inset 0 1px 0 rgba(255,255,255,.08); }
.home-artifact-tab.conclusion { border-color: rgba(120,150,110,.24); }
.home-artifact-tab-title { display: block; color: var(--text-1); font-size: .76rem; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-artifact-tab-sub { display: block; margin-top: 3px; color: var(--text-3); font-size: .62rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-tool-card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 12px; cursor: default; }
.home-tool-card-title { display: block; color: var(--text-1); font-size: 0.84rem; font-weight: 700; }
.home-tool-card-sub { display: block; margin-top: 3px; color: var(--text-3); font-size: 0.68rem; line-height: 1.35; }
.home-tool-card-feed { display: block; margin-top: 5px; color: var(--text-3); font-size: 0.64rem; line-height: 1.45; word-break: break-word; }
.home-tool-card-toggle { display: none; }
.home-tool-card-body { min-width: 0; padding: 0 12px 12px; display: grid; gap: 12px; overflow: visible; }
.home-artifact-render { width: 100%; min-height: 0; overflow-x: visible; overflow-y: visible; border-radius: 12px; contain: layout; }
.home-artifact-analysis { margin-top: 12px; padding: 12px 14px; border-radius: 12px; border: 1px solid rgba(178,149,93,.16); background: rgba(178,149,93,.055); color: var(--text-2); line-height: 1.8; white-space: pre-wrap; font-size: .84rem; }
.home-artifact-analysis-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.home-artifact-analysis-title { color: var(--accent); font-weight: 800; font-size: .72rem; letter-spacing: .5px; line-height: 1.2; }
.home-ai-summary-panel { margin-top: 10px; padding: 14px 16px; border-radius: 14px; border: 1px solid rgba(178,149,93,.16); background: rgba(255,255,255,.045); contain: layout; }
.home-artifact-render :deep(.artifact-panel) { display: grid; gap: 10px; color: var(--text-2); font-size: 0.74rem; }
.home-artifact-render :deep(.artifact-grid) { display: grid; gap: 8px; }
.home-artifact-render :deep(.artifact-grid-4) { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.home-artifact-render :deep(.artifact-grid-3) { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.home-artifact-render :deep(.bazi-pillar),
.home-artifact-render :deep(.artifact-gua),
.home-artifact-render :deep(.artifact-tarot-card),
.home-artifact-render :deep(.artifact-kv),
.home-artifact-render :deep(.artifact-chip),
.home-artifact-render :deep(.artifact-line),
.home-artifact-render :deep(.artifact-palace),
.home-artifact-render :deep(.artifact-ziwei-palace) { min-width: 0; padding: 8px 9px; border: 1px solid rgba(178,149,93,0.13); border-radius: 10px; background: rgba(255,255,255,0.045); box-sizing: border-box; }
.home-artifact-render :deep(.bazi-pillar span),
.home-artifact-render :deep(.artifact-gua span),
.home-artifact-render :deep(.artifact-tarot-card span),
.home-artifact-render :deep(.artifact-kv span),
.home-artifact-render :deep(.artifact-chip span),
.home-artifact-render :deep(.artifact-line span),
.home-artifact-render :deep(.artifact-palace span),
.home-artifact-render :deep(.artifact-ziwei-palace span) { display: block; color: var(--text-3); font-size: 0.62rem; line-height: 1.25; overflow-wrap: anywhere; }
.home-artifact-render :deep(.bazi-pillar strong),
.home-artifact-render :deep(.artifact-gua strong),
.home-artifact-render :deep(.artifact-tarot-card strong),
.home-artifact-render :deep(.artifact-kv strong),
.home-artifact-render :deep(.artifact-chip strong),
.home-artifact-render :deep(.artifact-line strong),
.home-artifact-render :deep(.artifact-palace b),
.home-artifact-render :deep(.artifact-ziwei-palace b) { display: block; color: var(--text-1); font-size: 0.82rem; line-height: 1.35; margin-top: 3px; overflow-wrap: anywhere; }
.home-artifact-render :deep(.artifact-kv-grid) { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.home-artifact-render :deep(.artifact-palace-grid) { display: grid; grid-template-columns: repeat(3, minmax(92px, 1fr)); border: 1px solid rgba(178,149,93,0.14); border-radius: 12px; overflow: hidden; }
.home-artifact-render :deep(.artifact-palace) { border-radius: 0; min-height: 68px; border-width: 0 1px 1px 0; }
.home-artifact-render :deep(.artifact-ziwei-grid) { display: grid; grid-template-columns: repeat(4, minmax(98px, 1fr)); gap: 6px; }
.home-artifact-render :deep(.artifact-ziwei-palace) { min-height: 82px; display: flex; flex-direction: column; gap: 3px; }
.home-artifact-render :deep(.artifact-chip-row) { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 2px; }
.home-artifact-render :deep(.artifact-chip) { min-width: 78px; flex: 0 0 auto; }
.home-artifact-render :deep(.artifact-row-title) { color: var(--accent); font-weight: 700; font-size: 0.72rem; margin-bottom: 6px; }
.home-artifact-render :deep(.artifact-line-list) { display: grid; gap: 6px; }
.home-artifact-render :deep(.artifact-line) { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.home-artifact-render :deep(.artifact-tarot-card em) { display: block; margin-top: 3px; color: var(--accent); font-style: normal; font-size: 0.62rem; }
.home-artifact-render :deep(.artifact-empty) { color: var(--text-3); font-size: 0.68rem; }

.home-artifact-render :deep(.bz-artifact-panel) { width: 100%; padding: 16px; border: 1px solid rgba(178,149,93,.16); border-radius: 14px; background: rgba(255,253,248,.05); box-sizing: border-box; }
.home-artifact-render :deep(.bz-artifact-head) { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid rgba(178,149,93,.14); }
.home-artifact-render :deep(.bz-artifact-head b) { display: block; color: var(--text-1); font-family: var(--font-serif); font-size: 1rem; letter-spacing: 2px; }
.home-artifact-render :deep(.bz-artifact-head span),
.home-artifact-render :deep(.bz-artifact-head em) { display: block; margin-top: 4px; color: var(--text-3); font-size: .72rem; font-style: normal; }
.home-artifact-render :deep(.bz-artifact-pillars) { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.home-artifact-render :deep(.bz-artifact-pillar) { min-width: 0; padding: 12px 10px; border: 1px solid rgba(178,149,93,.14); border-radius: 12px; text-align: center; background: rgba(255,255,255,.045); }
.home-artifact-render :deep(.bz-artifact-label) { display: block; color: var(--text-3); font-size: .68rem; margin-bottom: 8px; }
.home-artifact-render :deep(.bz-artifact-gz) { display: flex; align-items: center; justify-content: center; gap: 8px; }
.home-artifact-render :deep(.bz-artifact-gz-vertical) { flex-direction: column; gap: 6px; }
.home-artifact-render :deep(.bz-artifact-gz b) { width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; color: #fff; font-size: 1rem; font-weight: 800; box-shadow: 0 6px 16px rgba(0,0,0,.12); }
.home-artifact-render :deep(.bz-artifact-sub) { display: block; min-height: 16px; margin-top: 7px; color: var(--text-3); font-size: .66rem; }
.home-artifact-render :deep(.bz-artifact-meta) { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }
.home-artifact-render :deep(.bz-artifact-meta span) { padding: 8px 10px; border-radius: 10px; background: rgba(178,149,93,.06); color: var(--text-3); font-size: .68rem; }
.home-artifact-render :deep(.bz-artifact-meta b) { color: var(--text-1); font-size: .78rem; margin-left: 4px; }
.home-artifact-render :deep(.bz-wuxing-row) { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 10px; margin-top: 12px; }
.home-artifact-render :deep(.bz-wuxing-chip) { padding: 4px 9px; border-radius: 999px; color: #fff; font-size: .68rem; font-weight: 700; }
.home-artifact-render :deep(.wx-color-jin) { background: #B8860B; }
.home-artifact-render :deep(.wx-color-mu) { background: #2E8B57; }
.home-artifact-render :deep(.wx-color-shui) { background: #2878B5; }
.home-artifact-render :deep(.wx-color-huo) { background: #C44D3A; }
.home-artifact-render :deep(.wx-color-tu) { background: #8A6A2A; }
.home-artifact-render :deep(.wx-text-jin) { color: #B8860B; }
.home-artifact-render :deep(.wx-text-mu) { color: #2E8B57; }
.home-artifact-render :deep(.wx-text-shui) { color: #2878B5; }
.home-artifact-render :deep(.wx-text-huo) { color: #C44D3A; }
.home-artifact-render :deep(.wx-text-tu) { color: #8A6A2A; }
.home-artifact-render :deep(.bz-yun-panel) { display: grid; gap: 10px; }
.home-artifact-render :deep(.bz-yun-section) { border: 1px solid var(--card-border); border-radius: 12px; overflow: hidden; background: rgba(255,255,255,.035); }
.home-artifact-render :deep(.bz-yun-title) { padding: 8px 12px; color: var(--accent); font-size: .74rem; font-weight: 800; background: var(--accent-glow); border-bottom: 1px solid var(--card-border); }
.home-artifact-render :deep(.bz-yun-scroll) { display: flex; flex-wrap: nowrap; overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
.home-artifact-render :deep(.bz-yun-scroll::-webkit-scrollbar) { display: none; }
.home-artifact-render :deep(.bz-yun-item) { flex: 0 0 auto; min-width: 58px; min-height: 72px; padding: 8px 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; border-right: 1px solid rgba(178,149,93,.10); box-sizing: border-box; cursor: pointer; transition: background .18s ease, box-shadow .18s ease; }
.home-artifact-render :deep(.bz-yun-item.is-current) { background: rgba(178,149,93,.08); }
.home-artifact-render :deep(.bz-yun-item.is-active) { background: var(--dayun-active); box-shadow: inset 0 0 0 1px rgba(178,149,93,.35); }
.home-artifact-render :deep(.bz-yun-year) { color: var(--text-3); font-size: .62rem; }
.home-artifact-render :deep(.bz-yun-age) { color: var(--text-3); font-size: .54rem; }
.home-artifact-render :deep(.bz-yun-gz) { display: flex; gap: 2px; font-family: var(--font-serif); font-size: .88rem; line-height: 1.1; }
.home-artifact-render :deep(.bz-yun-gz-vertical) { flex-direction: column; gap: 0; font-size: .92rem; line-height: 1; }
.home-artifact-render :deep(.bz-yun-gz b) { font-weight: 800; }
.home-artifact-render :deep(.bz-yun-item em) { color: var(--text-3); font-size: .52rem; font-style: normal; }
.home-artifact-render :deep(.is-analysis-highlight) { position: relative; z-index: 1; border-color: rgba(201,151,54,.58) !important; background: rgba(255,232,176,.22) !important; box-shadow: 0 0 0 1px rgba(201,151,54,.22), 0 0 20px rgba(201,151,54,.18); animation: artifactPulse 1.8s ease-in-out infinite; }
.home-artifact-render :deep(.analysis-hit-star) { display: inline-flex; align-items: center; justify-content: center; padding: 0 3px; border-radius: 4px; color: #B84D4D; background: rgba(255,232,176,.42); animation: artifactPulse 1.8s ease-in-out infinite; }
@keyframes artifactPulse { 0%, 100% { filter: brightness(1); } 50% { filter: brightness(1.12); } }

/* 首页 artifact 直接承载单项页盘面结构，避免重新画一套黑字简化卡片 */
.home-artifact-render :deep(.mh-result-wrap),
.home-artifact-render :deep(.qm-result-wrap),
.home-artifact-render :deep(.ly-result-wrap) { width: 100%; color: var(--text-2); box-sizing: border-box; }
.home-artifact-render :deep(.ly-result-wrap) { max-width: 760px; margin: 0 auto; overflow: hidden; }
.home-artifact-render :deep(.mh-summary),
.home-artifact-render :deep(.qm-summary) { display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 0.8125rem; color: var(--text-2); padding: 12px 16px; background: rgba(255,255,255,0.035); border-radius: 10px; border: 1px solid var(--card-border); margin-bottom: 16px; }
.home-artifact-render :deep(.mh-summary b),
.home-artifact-render :deep(.qm-summary b) { color: var(--text-1); }
.home-artifact-render :deep(.qm-summary-rich) { display: grid; gap: 10px; }
.home-artifact-render :deep(.qm-summary-line) { display: flex; flex-wrap: wrap; gap: 8px 16px; }
.home-artifact-render :deep(.qm-pillar-row) { display: grid; grid-template-columns: repeat(4, minmax(52px, 1fr)); gap: 8px; width: 100%; }
.home-artifact-render :deep(.qm-pillar-stack) { min-height: 72px; border: 1px solid rgba(178,149,93,.16); border-radius: 10px; background: rgba(255,253,248,.08); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; }
.home-artifact-render :deep(.qm-pillar-stack span) { color: var(--text-3); font-size: .62rem; }
.home-artifact-render :deep(.qm-pillar-stack strong) { display: flex; flex-direction: column; align-items: center; font-family: var(--font-serif); line-height: 1; font-size: .95rem; }
.home-artifact-render :deep(.gua-display) { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin: 20px 0; }
.home-artifact-render :deep(.gua-card) { background: rgba(255,255,255,0.035); border: 1px solid var(--card-border); border-radius: 14px; padding: 18px 14px 14px; text-align: center; position: relative; transition: all .25s ease; box-sizing: border-box; }
.home-artifact-render :deep(.gua-card-name) { font-family: var(--font-serif); font-size: 1.25rem; font-weight: 700; color: var(--text-1); letter-spacing: 3px; margin-bottom: 12px; }
.home-artifact-render :deep(.gua-card-label) { font-size: .72rem; color: var(--text-3); letter-spacing: 2px; margin-bottom: 8px; }
.home-artifact-render :deep(.gua-card.ben-gua .gua-card-name) { color: var(--accent); }
.home-artifact-render :deep(.gua-card.hu-gua .gua-card-name) { color: #7C93C3; }
.home-artifact-render :deep(.gua-card.bian-gua .gua-card-name) { color: #E8A87C; }
.home-artifact-render :deep(.gua-yao-wrap) { display: flex; flex-direction: column; align-items: center; gap: 6px; margin: 0 auto; width: 120px; max-width: 120px; }
.home-artifact-render :deep(.gua-yao) { display: flex; justify-content: center; align-items: center; gap: 6px; height: 8px; width: 100%; position: relative; }
.home-artifact-render :deep(.gua-yao-line) { height: 6px; border-radius: 2px; background: var(--text-1); }
.home-artifact-render :deep(.gua-yao.yang .gua-yao-line) { width: 80%; }
.home-artifact-render :deep(.gua-yao.yin .gua-yao-line) { width: calc((80% - 6px) / 2); }
.home-artifact-render :deep(.gua-yao.dong-yao .gua-yao-line) { background: var(--accent); box-shadow: 0 0 8px rgba(178,149,93,.35); }
.home-artifact-render :deep(.gua-yao.dong-yao::after) { content: '○'; position: absolute; right: -14px; font-size: .625rem; color: var(--accent); font-weight: 700; }
.home-artifact-render :deep(.gua-trigram) { font-size: 2.2rem; line-height: 1; margin-bottom: 4px; opacity: .82; }
.home-artifact-render :deep(.gua-sub-info) { margin-top: 12px; font-size: .72rem; color: var(--text-3); line-height: 1.8; }
.home-artifact-render :deep(.gua-sub-info span) { display: inline-block; padding: 2px 8px; border-radius: 4px; margin: 2px; background: rgba(255,255,255,.05); }
.home-artifact-render :deep(.ti-yong-section) { background: rgba(255,255,255,.035); border: 1px solid var(--card-border); border-radius: 14px; padding: 18px; margin: 18px 0; }
.home-artifact-render :deep(.ti-yong-title) { font-family: var(--font-serif); font-size: 1rem; font-weight: 700; color: var(--text-1); letter-spacing: 2px; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--card-border); }
.home-artifact-render :deep(.ti-yong-grid) { display: grid; grid-template-columns: 1fr auto 1fr; gap: 16px; align-items: center; margin-bottom: 16px; }
.home-artifact-render :deep(.ti-yong-box) { text-align: center; padding: 16px 12px; border-radius: 12px; border: 1px solid var(--card-border); }
.home-artifact-render :deep(.ti-yong-box.ti) { background: rgba(110,195,135,.07); border-color: rgba(110,195,135,.20); }
.home-artifact-render :deep(.ti-yong-box.yong) { background: rgba(124,147,195,.07); border-color: rgba(124,147,195,.20); }
.home-artifact-render :deep(.ti-yong-label) { font-size: .72rem; color: var(--text-3); margin-bottom: 4px; letter-spacing: 1px; }
.home-artifact-render :deep(.ti-yong-gua) { font-family: var(--font-serif); font-size: 1.85rem; font-weight: 800; color: var(--text-1); line-height: 1.15; }
.home-artifact-render :deep(.ti-yong-wx) { font-size: .8rem; color: var(--text-2); margin-top: 4px; }
.home-artifact-render :deep(.ti-yong-rel) { text-align: center; padding: 8px 16px; font-size: .84rem; font-weight: 700; border-radius: 8px; letter-spacing: 1px; white-space: nowrap; }
.home-artifact-render :deep(.ti-yong-rel.ji) { background: rgba(110,195,135,.12); color: var(--success); }
.home-artifact-render :deep(.ti-yong-rel.xiong) { background: rgba(215,125,110,.12); color: var(--danger); }
.home-artifact-render :deep(.ti-yong-rel.zhong) { background: rgba(255,255,255,.05); color: var(--text-2); }
.home-artifact-render :deep(.mh-analysis-table) { width: 100%; border-collapse: collapse; font-size: .78rem; }
.home-artifact-render :deep(.mh-analysis-table th) { text-align: left; padding: 10px 12px; color: var(--text-3); font-weight: 500; border-bottom: 1px solid var(--card-border); white-space: nowrap; }
.home-artifact-render :deep(.mh-analysis-table td) { padding: 10px 12px; color: var(--text-2); border-bottom: 1px solid var(--card-border); }
.home-artifact-render :deep(.mh-verdict) { margin-top: 16px; padding: 16px 20px; border-radius: 12px; border-left: 3px solid var(--accent); background: rgba(178,149,93,.055); font-size: .9rem; color: var(--text-2); line-height: 1.8; }
.home-artifact-render :deep(.wx-tag),
.home-artifact-render :deep(.ws-tag) { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: .72rem; font-weight: 600; }
.home-artifact-render :deep(.wx-tag.jin) { background: rgba(255,215,0,.12); color: #D4A017; }
.home-artifact-render :deep(.wx-tag.mu) { background: rgba(110,195,135,.12); color: #6EC387; }
.home-artifact-render :deep(.wx-tag.shui) { background: rgba(70,130,180,.12); color: #4682B4; }
.home-artifact-render :deep(.wx-tag.huo) { background: rgba(215,125,110,.12); color: #D77D6E; }
.home-artifact-render :deep(.wx-tag.tu) { background: rgba(160,140,100,.12); color: #A08C64; }
.home-artifact-render :deep(.ws-tag.wang) { background: rgba(110,195,135,.12); color: #6EC387; }
.home-artifact-render :deep(.ws-tag.xiang) { background: rgba(70,130,180,.12); color: #4682B4; }
.home-artifact-render :deep(.ws-tag.xiu) { background: rgba(255,255,255,.06); color: var(--text-3); }
.home-artifact-render :deep(.ws-tag.qiu) { background: rgba(215,125,110,.10); color: #D77D6E; }
.home-artifact-render :deep(.ws-tag.si) { background: rgba(160,140,100,.10); color: #A08C64; }

.home-artifact-render :deep(.qm-free-layout) { --qm-grid-size: clamp(286px, 78vw, 560px); padding: 18px; border: 1px solid var(--card-border); border-radius: 14px; background: var(--card-bg); box-sizing: border-box; container-type: inline-size; }
.home-artifact-render :deep(.qm-free-summary) { margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--card-border); }
.home-artifact-render :deep(.qm-free-title) { margin-bottom: 10px; color: var(--accent); font-size: 1.05rem; font-weight: 800; letter-spacing: 2px; }
.home-artifact-render :deep(.qm-free-line),
.home-artifact-render :deep(.qm-free-pillars) { display: flex; flex-wrap: wrap; gap: 7px 16px; margin-bottom: 7px; color: var(--text-2); font-size: .82rem; line-height: 1.7; }
.home-artifact-render :deep(.qm-free-line b),
.home-artifact-render :deep(.qm-free-pillars b) { color: var(--text-1); }
.home-artifact-render :deep(.qm-free-pillars span) { display: inline-flex; align-items: baseline; gap: 6px; }
.home-artifact-render :deep(.qm-free-pillars strong) { display: inline-flex; align-items: baseline; gap: 0; font-family: var(--font-serif); font-size: .92rem; letter-spacing: 0; }
.home-artifact-render :deep(.qm-gz-gap) { display: inline-block; width: .38em; }
.home-artifact-render :deep(.qm-scale-shell) { width: 100%; display: flex; justify-content: center; }
.home-artifact-render :deep(.qm-nine-grid) { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 2px; width: min(100%, var(--qm-grid-size)); margin: 0 auto; border: 2px solid #b8b0a0; border-radius: 12px; overflow: hidden; background: #d5cfc2; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.home-artifact-render :deep(.qm-palace) { aspect-ratio: 1; min-height: 0; padding: clamp(4px, 1.45cqw, 8px); background: #fff; color: #222; position: relative; display: flex; flex-direction: column; justify-content: space-between; gap: 2px; box-sizing: border-box; line-height: 1.25; }
.home-artifact-render :deep(.qm-palace.center) { justify-content: center; align-items: center; text-align: center; background: #f0ede5; font-size: .55rem; color: #222; }
.home-artifact-render :deep(.qm-center-date) { font-size: .58rem; font-weight: 800; color: #222; }
.home-artifact-render :deep(.qm-center-xun),
.home-artifact-render :deep(.qm-center-pillars),
.home-artifact-render :deep(.qm-center-meta) { color: #6f6250; font-size: .52rem; line-height: 1.25; }
.home-artifact-render :deep(.qm-center-title) { color: #8a6319; font-weight: 800; font-size: .56rem; line-height: 1.25; }
.home-artifact-render :deep(.qm-palace-line) { display: flex; align-items: center; justify-content: space-between; gap: clamp(2px, .9cqw, 5px); min-height: clamp(14px, 4.2cqw, 22px); font-size: clamp(.54rem, 1.9cqw, .82rem); white-space: nowrap; }
.home-artifact-render :deep(.qm-shen),
.home-artifact-render :deep(.qm-xing),
.home-artifact-render :deep(.qm-men) { font-weight: 600; color: #222; }
.home-artifact-render :deep(.qm-shen em) { margin-left: 2px; color: #444; font-style: normal; font-weight: 800; }
.home-artifact-render :deep(.qm-xing.highlight),
.home-artifact-render :deep(.qm-men.highlight) { color: #27AE60; font-weight: 800; }
.home-artifact-render :deep(.qm-men.menpo) { color: #E74C3C; font-weight: 800; }
.home-artifact-render :deep(.qm-gan),
.home-artifact-render :deep(.qm-yingan) { display: inline-flex; align-items: baseline; color: #555; gap: 0; }
.home-artifact-render :deep(.qm-gan i) { margin-left: 2px; color: #D4A017; font-size: .55rem; font-style: normal; }
.home-artifact-render :deep(.qm-horse) { color: #D4A017; font-style: normal; font-size: .72rem; line-height: 1; display: inline-flex; align-items: center; margin-right: 2px; }
.home-artifact-render :deep(.qm-gan .qm-horse) { margin-left: 0; margin-right: 2px; font-size: .62rem; }
.home-artifact-render :deep(.qm-gong-label) { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #d0d0d0; font-size: .45rem; pointer-events: none; }
.home-artifact-render :deep(.qm-legend) { display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 4px 10px; margin-top: 10px; color: var(--text-3); font-size: .65rem; }
.home-artifact-render :deep(.qm-legend b) { font-weight: 800; }
.home-artifact-render :deep(.qm-legend .green) { color: #27AE60; }
.home-artifact-render :deep(.qm-legend .red) { color: #E74C3C; }
.home-artifact-render :deep(.qm-legend .purple) { color: #9B59B6; }
.home-artifact-render :deep(.qm-legend .brown) { color: #8B4513; }

.home-artifact-render :deep(.ly-ben-bian-box) { max-width: 100%; overflow: hidden; border: 1px solid var(--card-border); border-radius: 14px; background: rgba(255,255,255,.035); padding: 16px; box-sizing: border-box; }
.home-artifact-render :deep(.ly-ben-bian-top) { display: grid; grid-template-columns: minmax(0, 1fr) 24px minmax(0, 1fr); gap: 10px; align-items: center; margin-bottom: 14px; }
.home-artifact-render :deep(.ly-ben-bian-name-block) { min-width: 0; min-height: 98px; text-align: center; border: 1px solid rgba(178,149,93,.16); border-radius: 12px; padding: 10px; background: rgba(255,255,255,.035); display: flex; flex-direction: column; align-items: center; justify-content: center; box-sizing: border-box; }
.home-artifact-render :deep(.ly-ben-bian-label) { font-size: .66rem; color: var(--text-3); letter-spacing: 2px; }
.home-artifact-render :deep(.ly-ben-bian-name-text) { max-width: 100%; margin-top: 4px; font-family: var(--font-serif); font-size: clamp(.92rem, 3.8vw, 1.1rem); font-weight: 800; color: var(--accent); letter-spacing: 1px; overflow-wrap: anywhere; }
.home-artifact-render :deep(.ly-ben-bian-trigrams) { width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
.home-artifact-render :deep(.ly-ben-bian-top-arrow) { color: var(--accent); font-size: 1.2rem; font-weight: 800; }
.home-artifact-render :deep(.ly-ben-bian-body) { --ly-side-width: 250px; --ly-marker-width: 38px; --ly-yao-width: 74px; --ly-yao-bar: 64px; display: grid; gap: 7px; max-width: 100%; }
.home-artifact-render :deep(.ly-paired-row) { display: grid; grid-template-columns: minmax(0, 1fr) 1px minmax(0, 1fr); gap: 8px; align-items: center; justify-items: stretch; width: 100%; max-width: 100%; padding: 8px; border-radius: 10px; background: rgba(255,255,255,.035); border: 1px solid rgba(178,149,93,.10); box-sizing: border-box; }
.home-artifact-render :deep(.ly-paired-row.has-ben-only) { grid-template-columns: minmax(0, 1fr); }
.home-artifact-render :deep(.ly-paired-row.moving) { background: rgba(215,125,110,.08); border-color: rgba(215,125,110,.22); }
.home-artifact-render :deep(.ly-row-ben-side),
.home-artifact-render :deep(.ly-row-bian-side) { position: relative; min-width: 0; width: 100%; display: flex; justify-content: center; box-sizing: border-box; }
.home-artifact-render :deep(.ly-row-ben-side) { grid-column: 1; }
.home-artifact-render :deep(.ly-row-bian-side) { grid-column: 3; }
.home-artifact-render :deep(.ly-visual-side) { position: relative; display: grid; grid-template-columns: var(--ly-marker-width) var(--ly-yao-width) minmax(0, 1fr); gap: 8px; align-items: center; width: min(var(--ly-side-width), 100%); max-width: 100%; min-width: 0; }
.home-artifact-render :deep(.ly-row-divider) { grid-column: 2; display: block; width: 1px; align-self: stretch; background: rgba(178,149,93,.18); }
.home-artifact-render :deep(.ly-yao-tags-left) { min-width: 0; display: flex; gap: 4px; justify-content: flex-start; flex-wrap: wrap; }
.home-artifact-render :deep(.ly-tag) { display: inline-flex; align-items: center; justify-content: center; min-height: 20px; padding: 1px 6px; border-radius: 6px; font-size: .65rem; line-height: 1; background: rgba(178,149,93,.10); color: var(--text-2); white-space: nowrap; }
.home-artifact-render :deep(.ly-tag-shi) { color: #fff; background: #8a6319; }
.home-artifact-render :deep(.ly-tag-ying) { color: #fff; background: #7C93C3; }
.home-artifact-render :deep(.ly-tag-moving) { color: #fff; background: #D77D6E; }
.home-artifact-render :deep(.ly-tag-bian) { color: #fff; background: #27AE60; }
.home-artifact-render :deep(.ly-tag-liuqin) { color: #8a6319; }
.home-artifact-render :deep(.ly-tag-liushen) { color: #2980B9; }
.home-artifact-render :deep(.ly-tag-naja) { color: #6d5a38; }
.home-artifact-render :deep(.ly-paired-ben),
.home-artifact-render :deep(.ly-paired-bian) { width: var(--ly-yao-width); display: flex; align-items: center; justify-content: center; }
.home-artifact-render :deep(.ly-yang-bar) { width: var(--ly-yao-bar); height: 7px; border-radius: 3px; background: var(--text-1); }
.home-artifact-render :deep(.ly-yin-bars) { width: var(--ly-yao-bar); display: flex; gap: 12px; justify-content: center; }
.home-artifact-render :deep(.ly-yin-seg) { width: 26px; height: 7px; border-radius: 3px; background: var(--text-1); }
.home-artifact-render :deep(.ly-paired-info),
.home-artifact-render :deep(.ly-paired-bian-info) { display: flex; gap: 5px; flex-wrap: wrap; align-items: center; min-width: 0; }
.home-artifact-render :deep(.ly-yao-pos) { color: var(--text-1); font-weight: 700; font-size: .72rem; }
.home-artifact-render :deep(.ly-meta-row) { margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--card-border); color: var(--text-3); font-size: .72rem; }
.home-artifact-render :deep(.ly-ben-bian-footer) { display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap; padding-top: 10px; margin-top: 10px; border-top: 1px solid var(--card-border); color: var(--text-3); font-size: .72rem; }
.home-artifact-render :deep(.ly-detail-table-wrap) { overflow-x: auto; margin-top: 12px; }
.home-artifact-render :deep(.ly-detail-table) { width: 100%; border-collapse: collapse; font-size: .72rem; }
.home-artifact-render :deep(.ly-detail-table th) { padding: 8px 6px; color: var(--text-3); font-weight: 600; border-bottom: 1px solid var(--card-border); white-space: nowrap; }
.home-artifact-render :deep(.ly-detail-table td) { padding: 8px 6px; color: var(--text-2); border-bottom: 1px solid rgba(178,149,93,.10); text-align: center; white-space: nowrap; }
.home-artifact-render :deep(.ly-detail-table .moving-row td) { color: var(--danger); }
.home-artifact-render :deep(.ly-paipan-meta) { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 12px; margin-top: 12px; padding: 12px; border-radius: 10px; background: rgba(255,255,255,.035); color: var(--text-3); font-size: .72rem; }

.home-artifact-render :deep(.zw-artifact-wrap) { width: 100%; overflow-x: auto; }
.home-artifact-render :deep(.zw-artifact-grid) { min-width: 620px; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); grid-template-rows: repeat(4, minmax(132px, auto)); gap: 1px; background: rgba(183,144,76,.28); border: 1px solid rgba(183,144,76,.30); border-radius: 10px; overflow: hidden; position: relative; }
.home-artifact-render :deep(.zw-artifact-palace) { min-height: 116px; padding: 8px; background: rgba(255,253,248,.96); color: #222; display: flex; flex-direction: column; gap: 5px; box-sizing: border-box; }
.home-artifact-render :deep(.zw-artifact-palace:nth-child(odd)) { background: rgba(255,249,242,.96); }
.home-artifact-render :deep(.zw-artifact-top) { display: flex; align-items: center; justify-content: space-between; color: #8a6319; font-size: .68rem; }
.home-artifact-render :deep(.zw-artifact-top b) { color: #B84D4D; font-size: .76rem; }
.home-artifact-render :deep(.zw-artifact-stars) { display: flex; flex-wrap: wrap; gap: 3px 6px; align-content: flex-start; }
.home-artifact-render :deep(.zw-artifact-stars.major span) { color: #b66b2d; font-size: .82rem; font-weight: 800; }
.home-artifact-render :deep(.zw-artifact-stars.minor span) { color: #2b89c9; font-size: .72rem; font-weight: 700; }
.home-artifact-render :deep(.zw-artifact-stars.adj span) { color: #6f6250; font-size: .64rem; font-weight: 500; }
.home-artifact-render :deep(.zw-artifact-support),
.home-artifact-render :deep(.zw-artifact-ages) { color: #7c7163; font-size: .58rem; line-height: 1.35; }
.home-artifact-render :deep(.zw-artifact-foot) { margin-top: auto; display: flex; align-items: flex-end; justify-content: space-between; gap: 6px; color: #6f6250; font-size: .62rem; }
.home-artifact-render :deep(.zw-artifact-foot strong) { color: #B84D4D; font-size: .68rem; }
.home-artifact-render :deep(.zw-artifact-center) { grid-column: 2 / 4; grid-row: 2 / 4; background: rgba(255,255,255,.96); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; text-align: center; color: #4a3922; padding: 16px; box-sizing: border-box; }
.home-artifact-render :deep(.zw-artifact-center b) { font-family: var(--font-serif); color: #8a6319; font-size: 1.05rem; letter-spacing: 2px; }
.home-artifact-render :deep(.zw-artifact-center span),
.home-artifact-render :deep(.zw-artifact-center em) { color: #6f6250; font-size: .72rem; font-style: normal; }
.home-artifact-render :deep(.zw-orientation) { min-width: 620px; text-align: center; color: var(--text-3); font-size: .72rem; margin: 4px 0; }
.home-artifact-render :deep(.zw-flow-row) { min-width: 620px; display: grid; grid-template-columns: 54px minmax(0, 1fr); gap: 8px; margin-top: 8px; }
.home-artifact-render :deep(.zw-flow-title) { display: flex; align-items: center; justify-content: center; border-radius: 8px; background: var(--accent-glow); color: var(--accent); font-size: .7rem; font-weight: 800; }
.home-artifact-render :deep(.zw-flow-scroll) { display: flex; overflow-x: auto; scrollbar-width: none; }
.home-artifact-render :deep(.zw-flow-scroll::-webkit-scrollbar) { display: none; }
.home-artifact-render :deep(.zw-flow-item) { flex: 0 0 62px; min-height: 54px; padding: 6px 4px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; border-right: 1px solid rgba(178,149,93,.10); background: rgba(255,255,255,.035); }
.home-artifact-render :deep(.zw-flow-item b) { color: var(--text-1); font-size: .66rem; }
.home-artifact-render :deep(.zw-flow-item em),
.home-artifact-render :deep(.zw-flow-item i) { color: var(--text-3); font-size: .54rem; font-style: normal; }

.home-artifact-render :deep(.tarot-artifact-wrap) { width: 100%; padding: 14px 0 4px; }
.home-artifact-render :deep(.tarot-drawing-text) { text-align: center; color: var(--accent); font-family: var(--font-serif); font-size: 1rem; font-weight: 800; letter-spacing: 2px; margin-bottom: 16px; }
.home-artifact-render :deep(.tarot-cards-display) { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 0 auto 12px; justify-items: center; }
.home-artifact-render :deep(.tarot-cards-display[data-count="1"]) { grid-template-columns: 1fr; max-width: 200px; }
.home-artifact-render :deep(.tarot-cards-display[data-count="3"]) { grid-template-columns: repeat(3, 1fr); max-width: 560px; }
.home-artifact-render :deep(.tarot-cards-display[data-count="5"]) { grid-template-columns: repeat(3, 1fr); max-width: 560px; }
.home-artifact-render :deep(.tarot-cards-display[data-count="6"]) { grid-template-columns: repeat(3, 1fr); max-width: 560px; }
.home-artifact-render :deep(.tarot-cards-display[data-count="7"]) { grid-template-columns: repeat(4, 1fr); max-width: 720px; }
.home-artifact-render :deep(.tarot-cards-display[data-count="10"]) { grid-template-columns: repeat(5, 1fr); max-width: 880px; }
.home-artifact-render :deep(.tarot-card-slot) { width: 100%; max-width: 148px; perspective: 600px; }
.home-artifact-render :deep(.tarot-card-flipper) { position: relative; width: 100%; height: 238px; transform-style: preserve-3d; transform: rotateY(180deg); }
.home-artifact-render :deep(.tarot-card-front),
.home-artifact-render :deep(.tarot-card-back) { position: absolute; inset: 0; border-radius: 12px; backface-visibility: hidden; overflow: hidden; box-sizing: border-box; }
.home-artifact-render :deep(.tarot-card-back) { background: linear-gradient(135deg, rgba(31,29,24,.95), rgba(65,48,22,.92)); border: 2px solid var(--accent); display: flex; align-items: center; justify-content: center; }
.home-artifact-render :deep(.tarot-card-back-pattern) { position: absolute; inset: 8px; border: 1px solid rgba(201,162,60,.25); border-radius: 8px; }
.home-artifact-render :deep(.tarot-card-back-symbol) { font-size: 3rem; color: var(--accent); opacity: .65; }
.home-artifact-render :deep(.tarot-card-front) { transform: rotateY(180deg); background: rgba(255,253,248,.96); border: 2px solid var(--accent); display: flex; flex-direction: column; align-items: center; padding: 8px; color: #2e2a24; }
.home-artifact-render :deep(.tarot-card-art-wrap) { position: relative; width: 100%; min-height: 0; border-radius: 8px; overflow: hidden; background: rgba(90,65,35,.08); border: 1px solid rgba(126,91,38,.24); flex: 1 1 auto; }
.home-artifact-render :deep(.tarot-card-img) { display: block; width: 100%; height: 100%; object-fit: cover; transform-origin: center; }
.home-artifact-render :deep(.tarot-card-img-reversed) { transform: rotate(180deg); }
.home-artifact-render :deep(.tarot-card-fallback) { position: absolute; inset: 0; display: none; flex-direction: column; align-items: center; justify-content: center; gap: 6px; padding: 14px 10px; text-align: center; background: linear-gradient(180deg, #fbf4e4, #ead9b9); }
.home-artifact-render :deep(.tarot-card-front.image-failed .tarot-card-img) { display: none; }
.home-artifact-render :deep(.tarot-card-front.image-failed .tarot-card-fallback) { display: flex; }
.home-artifact-render :deep(.tarot-card-num) { font-size: .68rem; color: #8d806d; margin-bottom: 4px; }
.home-artifact-render :deep(.tarot-card-name) { font-weight: 800; font-size: .9rem; color: #2e2a24; text-align: center; margin-bottom: 2px; letter-spacing: 1px; }
.home-artifact-render :deep(.tarot-card-name-below) { margin-top: 6px; }
.home-artifact-render :deep(.tarot-card-name-en) { font-size: .58rem; color: #8d806d; text-align: center; margin-bottom: 6px; }
.home-artifact-render :deep(.tarot-card-orientation) { font-size: .72rem; padding: 2px 8px; border-radius: 8px; margin-bottom: 6px; font-weight: 700; }
.home-artifact-render :deep(.tarot-card-orientation.upright) { color: #5b8c5a; background: rgba(91,140,90,.12); border: 1px solid rgba(91,140,90,.3); }
.home-artifact-render :deep(.tarot-card-orientation.reversed) { color: #c0392b; background: rgba(192,57,43,.12); border: 1px solid rgba(192,57,43,.3); }
.home-artifact-render :deep(.tarot-card-keyword) { font-size: .66rem; color: #6f6250; text-align: center; line-height: 1.45; }
.home-artifact-render :deep(.tarot-card-position) { text-align: center; margin-top: 10px; }
.home-artifact-render :deep(.tarot-card-position-name) { font-weight: 800; font-size: .8rem; color: var(--accent); letter-spacing: 1px; }
.home-artifact-render :deep(.tarot-card-position-meaning) { font-size: .66rem; color: var(--text-4); margin-top: 2px; }
.home-artifact-render :deep(.tarot-card-reversed-hint) { font-size: .62rem; color: #c0392b; margin-top: 2px; }
.mini-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1px solid rgba(178,149,93,0.14); border-radius: 10px; overflow: hidden; }
.mini-palace { min-height: 64px; padding: 7px; border-right: 1px solid rgba(178,149,93,0.12); border-bottom: 1px solid rgba(178,149,93,0.12); display: flex; flex-direction: column; gap: 2px; color: var(--text-3); font-size: 0.62rem; box-sizing: border-box; }
.mini-palace:nth-child(3n) { border-right: none; }
.mini-palace:nth-last-child(-n+3) { border-bottom: none; }
.mini-palace-name { color: var(--accent); font-size: 0.68rem; font-weight: 700; }
.mini-list { display: grid; gap: 6px; }
.mini-line { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 7px 9px; border-radius: 9px; background: rgba(255,255,255,0.045); color: var(--text-2); font-size: 0.68rem; }
.mini-gua-row, .mini-tarot-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.mini-gua, .mini-tarot { min-width: 0; padding: 9px; border-radius: 10px; background: rgba(255,255,255,0.045); border: 1px solid rgba(178,149,93,0.12); }
.mini-gua-label, .mini-tarot-pos { display: block; color: var(--text-3); font-size: 0.62rem; margin-bottom: 4px; }
.mini-gua-name, .mini-tarot-name { display: block; color: var(--text-1); font-size: 0.76rem; font-weight: 700; line-height: 1.35; }

.profile-sheet { position: fixed; inset: 0; z-index: 400; }
.profile-sheet-mask { position: absolute; inset: 0; background: rgba(20,16,10,0.50); backdrop-filter: blur(10px); touch-action: none; }
.profile-sheet-panel { position: absolute; left: 50%; bottom: 24px; transform: translateX(-50%); width: min(640px, calc(100vw - 28px)); max-height: 72vh; overflow: hidden; border-radius: 20px; border: 1px solid rgba(178,149,93,0.20); background: rgba(31, 29, 24, 0.92); box-shadow: 0 24px 80px rgba(0,0,0,0.34), inset 0 1px 0 rgba(255,255,255,0.08); padding: 20px; box-sizing: border-box; backdrop-filter: blur(30px) saturate(145%); display: flex; flex-direction: column; }
[data-theme="light"] .profile-sheet-panel { background: rgba(255,253,248,0.96); box-shadow: 0 24px 80px rgba(60,40,15,0.14), inset 0 1px 0 rgba(255,255,255,0.85); }
.profile-sheet-panel::before { content: ''; display: block; width: 42px; height: 4px; border-radius: 999px; background: rgba(178,149,93,0.30); margin: 0 auto 14px; }
.profile-sheet-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.profile-sheet-title { color: var(--text-1); font-size: 1rem; font-family: var(--font-serif); letter-spacing: 2px; }
.profile-sheet-close { width: 30px; height: 30px; border-radius: 50%; color: var(--text-3); font-size: 1.25rem; cursor: pointer; display: flex; align-items: center; justify-content: center; border: 1px solid transparent; }
.profile-sheet-close:hover { color: var(--accent); border-color: rgba(178,149,93,0.24); background: var(--accent-glow); }
.profile-sheet-scroll { flex: 1 1 auto; min-height: 0; overflow-y: auto; overflow-x: hidden; padding-right: 2px; -webkit-overflow-scrolling: touch; overscroll-behavior: contain; touch-action: pan-y; }
.profile-tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.profile-tabs view { flex: 1; text-align: center; padding: 8px 10px; border-radius: 10px; border: 1px solid var(--card-border); color: var(--text-3); font-size: 0.8rem; cursor: pointer; }
.profile-tabs view.active { background: var(--accent-glow); border-color: var(--accent); color: var(--accent); }
.profile-options { overflow: visible; min-height: 0; }
.profile-option { display: flex; justify-content: space-between; gap: 16px; padding: 12px; border-radius: 14px; border: 1px solid rgba(178,149,93,0.13); background: rgba(255,255,255,0.035); margin-bottom: 8px; cursor: pointer; transition: border-color .18s ease, background .18s ease; }
.profile-option-name { display: block; color: var(--text-1); font-size: 0.88rem; }
.profile-option-meta { display: block; margin-top: 4px; color: var(--text-3); font-size: 0.72rem; }
.profile-option.active { border-color: rgba(178,149,93,0.62); background: var(--accent-glow); }
.profile-option-side { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.profile-option-type { color: var(--accent); font-size: 0.72rem; white-space: nowrap; }
.profile-option-check { width: 22px; height: 22px; border-radius: 50%; border: 1px solid var(--card-border); color: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 700; }
.profile-empty { padding: 22px; text-align: center; color: var(--text-3); font-size: 0.84rem; display: grid; gap: 6px; }
.profile-empty-sub { font-size: 0.72rem; color: var(--text-4); }
.profile-quick-create { margin-bottom: 10px; border-bottom: 1px solid rgba(178,149,93,0.12); padding-bottom: 10px; flex-shrink: 0; }
.profile-quick-toggle { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 38px; border-radius: 12px; padding: 0 12px; background: rgba(178,149,93,0.10); color: var(--accent); font-size: 0.82rem; cursor: pointer; }
.profile-quick-hint { color: var(--text-4); font-size: 0.7rem; }
.profile-quick-form { margin-top: 10px; padding: 12px; border-radius: 14px; border: 1px solid rgba(178,149,93,0.16); background: rgba(255,255,255,0.04); }
.quick-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.quick-field { min-width: 0; display: grid; gap: 5px; color: var(--text-3); font-size: 0.72rem; }
.quick-field-wide { grid-column: 1 / -1; }
.quick-field.disabled { opacity: 0.62; }
.quick-field input, .quick-picker, .quick-native-select { width: 100%; height: 36px; border-radius: 10px; border: 1px solid rgba(178,149,93,0.16); background: var(--input-bg); color: var(--text-1); padding: 0 10px; box-sizing: border-box; display: flex; align-items: center; font-size: 0.8rem; outline: none; }
.quick-native-select { cursor: pointer; text-align: center; appearance: none; -webkit-appearance: none; -moz-appearance: none; background-image: linear-gradient(45deg, transparent 50%, var(--text-4) 50%), linear-gradient(135deg, var(--text-4) 50%, transparent 50%); background-position: calc(100% - 13px) 15px, calc(100% - 8px) 15px; background-size: 5px 5px, 5px 5px; background-repeat: no-repeat; padding-right: 20px; }
.quick-native-select:focus { border-color: rgba(178,149,93,0.46); }
.quick-native-select:disabled { opacity: 0.54; cursor: not-allowed; }
.quick-datetime-row, .quick-addr-selects { display: grid; gap: 8px; }
.quick-datetime-all { grid-template-columns: minmax(68px, 1.2fr) repeat(4, minmax(48px, 0.9fr)); }
.quick-addr-selects { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.quick-addr-info { display: grid; gap: 3px; margin-top: 7px; color: var(--text-4); font-size: 0.66rem; line-height: 1.35; }
.quick-addr-info text:first-child { color: var(--text-3); }
.quick-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 10px; }
.quick-check, .send-confirm-check { display: inline-flex; align-items: center; gap: 8px; color: var(--text-3); font-size: 0.76rem; cursor: pointer; }
.quick-check-dot { width: 18px; height: 18px; border-radius: 50%; border: 1px solid rgba(178,149,93,0.32); display: inline-flex; align-items: center; justify-content: center; color: var(--accent); font-size: 0.68rem; }
.quick-check.active .quick-check-dot, .send-confirm-check.active .quick-check-dot { background: var(--accent); border-color: var(--accent); color: #fff; }
.quick-save { flex-shrink: 0; max-width: 100%; height: 34px; padding: 0 14px; border-radius: 999px; background: var(--accent); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.78rem; cursor: pointer; box-sizing: border-box; }
.quick-note { margin-top: 8px; color: var(--text-4); font-size: 0.68rem; line-height: 1.55; }
.sheet-actions { display: flex; justify-content: flex-end; gap: 10px; padding-top: 12px; margin-top: 12px; border-top: 1px solid rgba(178,149,93,0.14); flex-shrink: 0; }
.sheet-btn { min-width: 88px; height: 38px; border-radius: 999px; display: flex; align-items: center; justify-content: center; font-size: 0.82rem; cursor: pointer; border: 1px solid rgba(178,149,93,0.18); box-sizing: border-box; transition: transform .18s ease, border-color .18s ease; }
.sheet-btn:hover { transform: translateY(-1px); border-color: rgba(178,149,93,0.45); }
.sheet-btn-secondary { color: var(--text-2); background: var(--input-bg); }
.sheet-btn-primary { color: #fff; background: var(--accent); border-color: var(--accent); }
.send-confirm-sheet { position: fixed; inset: 0; z-index: 430; }
.send-confirm-mask { position: absolute; inset: 0; background: rgba(20,16,10,0.52); backdrop-filter: blur(10px); }
.send-confirm-panel { position: absolute; left: 50%; bottom: 24px; transform: translateX(-50%); width: min(460px, calc(100vw - 28px)); border-radius: 18px; border: 1px solid rgba(178,149,93,0.22); background: rgba(31,29,24,0.94); box-shadow: 0 24px 80px rgba(0,0,0,0.34); padding: 18px; box-sizing: border-box; }
[data-theme="light"] .send-confirm-panel { background: rgba(255,253,248,0.98); box-shadow: 0 24px 80px rgba(60,40,15,0.14); }
.send-confirm-title { color: var(--text-1); font-family: var(--font-serif); font-size: 1rem; letter-spacing: 2px; }
.send-confirm-desc { margin-top: 5px; color: var(--text-3); font-size: 0.76rem; }
.send-confirm-list { display: grid; gap: 8px; margin: 14px 0; }
.send-confirm-list view { display: flex; justify-content: space-between; gap: 12px; padding: 9px 10px; border-radius: 10px; border: 1px solid rgba(178,149,93,0.12); background: rgba(255,255,255,0.035); color: var(--text-2); font-size: 0.78rem; }
.send-confirm-list text:first-child { color: var(--text-4); flex-shrink: 0; }
.send-confirm-list text:last-child { text-align: right; color: var(--text-1); }
.home-guidance-note { width: min(920px, calc(100vw - 40px)); margin: 0 auto; display: flex; align-items: center; justify-content: center; gap: 10px; color: var(--text-3); font-size: 0.72rem; text-align: center; pointer-events: auto; }
.home-guidance-note-action { color: var(--accent); cursor: pointer; white-space: nowrap; }
.question-guide-sheet { position: fixed; inset: 0; z-index: 435; }
.question-guide-panel { position: absolute; left: 50%; bottom: 24px; transform: translateX(-50%); width: min(500px, calc(100vw - 28px)); border-radius: 20px; border: 1px solid rgba(178,149,93,0.22); background: rgba(31,29,24,0.95); box-shadow: 0 24px 80px rgba(0,0,0,0.36); padding: 18px; box-sizing: border-box; backdrop-filter: blur(28px) saturate(145%); }
[data-theme="light"] .question-guide-panel { background: rgba(255,253,248,0.98); box-shadow: 0 24px 80px rgba(60,40,15,0.14); }
.question-guide-kicker { display: inline-flex; align-items: center; height: 24px; padding: 0 9px; margin-bottom: 8px; border-radius: 999px; background: var(--accent-glow); color: var(--accent); font-size: 0.68rem; font-weight: 700; letter-spacing: 1px; }
.question-guide-origin { display: grid; gap: 5px; margin: 12px 0; padding: 10px 12px; border-radius: 12px; border: 1px solid rgba(178,149,93,0.14); background: rgba(255,255,255,0.035); }
.question-guide-origin text:first-child { color: var(--text-4); font-size: 0.68rem; }
.question-guide-origin text:last-child { color: var(--text-1); font-size: 0.8rem; line-height: 1.5; }
.question-guide-chat { display: grid; gap: 8px; margin: 12px 0; max-height: 190px; overflow-y: auto; }
.question-guide-message { max-width: 88%; padding: 10px 12px; border-radius: 14px; font-size: 0.8rem; line-height: 1.55; box-sizing: border-box; }
.question-guide-message-assistant { justify-self: start; border: 1px solid rgba(178,149,93,0.16); background: rgba(255,255,255,0.045); color: var(--text-1); border-bottom-left-radius: 6px; }
.question-guide-message-user { justify-self: end; background: var(--accent-glow); color: var(--accent); border: 1px solid rgba(178,149,93,0.22); border-bottom-right-radius: 6px; }
[data-theme="light"] .question-guide-message-assistant { background: rgba(255,251,242,0.8); }
.question-guide-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.question-guide-chip { min-height: 32px; padding: 0 11px; border-radius: 999px; border: 1px solid rgba(178,149,93,0.18); background: rgba(255,255,255,0.04); color: var(--text-2); display: inline-flex; align-items: center; justify-content: center; font-size: 0.76rem; cursor: pointer; box-sizing: border-box; }
.question-guide-chip.active { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); box-shadow: inset 0 0 0 1px rgba(178,149,93,0.12); }
.question-guide-input { width: 100%; min-height: 44px; max-height: 88px; padding: 10px 12px; border-radius: 12px; border: 1px solid rgba(178,149,93,0.16); background: rgba(255,255,255,0.04); color: var(--text-1); font-size: 0.8rem; line-height: 1.45; box-sizing: border-box; outline: none; }
[data-theme="light"] .question-guide-input { background: rgba(255,251,242,0.78); }
.question-guide-progress { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 10px 0 2px; color: var(--text-4); font-size: 0.68rem; }
.home-guide-options { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.home-guide-option { min-height: 32px; padding: 0 12px; border-radius: 999px; border: 1px solid rgba(178,149,93,0.22); background: rgba(255,255,255,0.045); color: var(--text-2); display: inline-flex; align-items: center; justify-content: center; font-size: 0.76rem; cursor: pointer; box-sizing: border-box; }
.home-guide-option:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); }
.home-guide-recommend { display: grid; gap: 8px; margin-top: 12px; padding: 12px; border-radius: 12px; border: 1px solid rgba(178,149,93,0.16); background: rgba(255,255,255,0.04); }
.home-guide-recommend-title { color: var(--text-1); font-size: 0.82rem; font-weight: 700; }
.home-guide-recommend-meta { color: var(--text-4); font-size: 0.72rem; }
.home-guide-primary { min-height: 36px; padding: 0 14px; border-radius: 999px; background: var(--accent); color: #1f1d18; display: inline-flex; align-items: center; justify-content: center; justify-self: start; font-size: 0.78rem; font-weight: 800; cursor: pointer; }
.home-guide-loading { min-height: 36px; padding: 0 14px; border-radius: 999px; border: 1px solid rgba(178,149,93,0.22); background: rgba(178,149,93,0.10); color: var(--accent); display: inline-flex; align-items: center; justify-content: center; justify-self: start; gap: 8px; font-size: 0.78rem; font-weight: 800; }
.home-guide-thinking { min-height: 42px; display: inline-flex; align-items: center; gap: 9px; padding: 10px 12px; margin-top: 4px; border-radius: 14px; border: 1px solid rgba(178,149,93,0.16); background: linear-gradient(135deg, rgba(178,149,93,0.10), rgba(255,255,255,0.035)); color: var(--text-2); font-size: 0.82rem; line-height: 1.4; box-sizing: border-box; }
.home-guide-spinner { width: 14px; height: 14px; border-radius: 50%; border: 2px solid rgba(178,149,93,0.24); border-top-color: var(--accent); animation: guideSpin .8s linear infinite; box-sizing: border-box; }
.home-guide-dots { display: inline-flex; gap: 4px; align-items: center; padding-left: 1px; }
.home-guide-dots text { width: 4px; height: 4px; border-radius: 50%; background: var(--accent); opacity: .35; animation: guideDotPulse 1.1s ease-in-out infinite; }
.home-guide-dots text:nth-child(2) { animation-delay: .16s; }
.home-guide-dots text:nth-child(3) { animation-delay: .32s; }
@keyframes guideSpin { to { transform: rotate(360deg); } }
@keyframes guideDotPulse { 0%, 80%, 100% { opacity: .28; transform: translateY(0); } 40% { opacity: .95; transform: translateY(-2px); } }
/* ═══ 页脚 ═══ */
.site-footer { background: var(--nav-bg); border-top: 1px solid var(--card-border); padding: 24px 32px 24px; margin-top: 0; }
.footer-disclaimer { max-width: var(--max-w); margin: 0 auto 32px; padding: 14px 20px; border-radius: 10px; background: rgba(215,125,110,0.08); border: 1px solid rgba(215,125,110,0.15); font-size: 0.75rem; color: var(--danger); line-height: 1.6; text-align: center; }
.footer-grid { max-width: var(--max-w); margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 40px; }
.footer-col-title { font-size: 0.8125rem; color: var(--text-2); margin-bottom: 12px; letter-spacing: 1px; }
.footer-col navigator, .footer-col .footer-link { display: block; font-size: 0.75rem; color: var(--text-3); text-decoration: none; padding: 6px 0; }
.footer-icp { font-size: 0.6875rem; color: var(--text-3); margin-top: 8px; }
.footer-bottom { max-width: var(--max-w); margin: 24px auto 0; padding-top: 16px; border-top: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center; }
.footer-bottom-text { font-size: 0.6875rem; color: var(--text-3); }
.btn-clear-data { font-size: 0.6875rem; padding: 4px 10px; border-radius: 6px; background: transparent; border: 1px solid var(--danger); color: var(--danger); cursor: pointer; }

/* ═══ 弹窗 ═══ */
.modal-overlay { display: none; position: fixed; inset: 0; z-index: 300; background: rgba(0,0,0,0.55); backdrop-filter: blur(8px); align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; width: 360px; backdrop-filter: blur(40px); box-shadow: var(--card-shadow); }
.modal-title { font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px; text-align: center; margin-bottom: 24px; color: var(--text-1); }
.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: var(--danger); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }
:global(body #topnavLoginModal) {
  align-items: flex-end !important;
  justify-content: center !important;
  padding: 18px !important;
  padding-bottom: max(18px, calc(env(safe-area-inset-bottom) + 14px)) !important;
  box-sizing: border-box !important;
}
:global(body #topnavLoginModal.open),
:global(body #topnavLoginModal.modal-overlay.open) {
  display: flex !important;
}
:global(body #topnavLoginModal .modal-box) {
  margin-top: auto !important;
  margin-bottom: 0 !important;
  border-radius: 22px 22px 16px 16px !important;
}

/* ═══ 响应式 ═══ */
@media (max-width: 1024px) {
  .footer-grid { grid-template-columns: 1fr; gap: 24px; }
}
@media (min-width: 769px) and (max-height: 720px) {
  .page-root { --home-ai-dock-space: 104px; --home-ai-chat-bottom-buffer: 116px; }
  .hero-home { padding: 20px 32px 132px; }
  .hero-brand { margin-bottom: 16px; }
  .hero-brand-icon-wrap { width: 96px; height: 96px; margin-bottom: 10px; }
  .hero-brand-icon { width: 80px; height: 80px; transform: translateY(3px); }
  .hero-brand-name { font-size: 1.82rem; letter-spacing: 6px; margin-bottom: 8px; text-indent: 6px; }
  .hero-brand-divider { margin: 8px auto; }
  .hero-brand-slogan { font-size: 0.82rem; letter-spacing: 3px; }
  .hero-brand-sub { display: none; }
  .home-question-templates { margin-top: 12px; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
  .home-question-template { min-height: 48px; padding: 8px 10px; border-radius: 12px; }
  .home-question-template-label { font-size: 0.66rem; }
  .home-question-template-text { font-size: 0.72rem; }
  .home-scan-panel { margin-bottom: 12px; }
  .home-scan-status-item, .home-scan-action { padding-top: 8px; padding-bottom: 8px; }
  .home-scan-action-sub { display: none; }
  .home-ai-input { min-height: 40px; max-height: 60px; }
  .home-ai-main { bottom: 12px; }
  .hero-home.chat-active { padding: 10px 32px 158px; }
  .hero-home.chat-active.reading-active { padding: 0 32px var(--home-ai-dock-space); }
  .hero-home.chat-active .hero-brand { margin-bottom: 10px; }
  .hero-home.chat-active .hero-brand-icon-wrap { width: 50px; height: 50px; }
  .hero-home.chat-active .hero-brand-icon { width: 42px; height: 42px; transform: translateY(2px); }
  .hero-home.chat-active .hero-brand-name { font-size: 1.14rem; letter-spacing: 4px; text-indent: 4px; }
}
@media (min-width: 769px) and (max-height: 620px) {
  .page-root { --home-ai-dock-space: 96px; --home-ai-chat-bottom-buffer: 106px; }
  .hero-home { padding: 14px 32px 120px; }
  .hero-brand { margin-bottom: 10px; }
  .hero-brand-icon-wrap { width: 78px; height: 78px; margin-bottom: 8px; }
  .hero-brand-icon { width: 64px; height: 64px; transform: translateY(2px); }
  .hero-brand-name { font-size: 1.45rem; letter-spacing: 4px; margin-bottom: 6px; text-indent: 4px; }
  .hero-brand-divider, .hero-brand-slogan, .hero-brand-sub { display: none; }
  .home-question-templates { width: min(620px, calc(100vw - 36px)); margin-top: 10px; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
  .home-question-template { min-height: 46px; padding: 8px 10px; border-radius: 12px; }
  .home-scan-panel { margin-bottom: 8px; gap: 8px; }
  .home-scan-status { display: none; }
  .home-scan-actions { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .home-scan-action { grid-template-columns: 22px minmax(0, 1fr); padding: 7px 8px; border-radius: 12px; }
  .home-scan-action-mark { width: 22px; height: 22px; border-radius: 7px; font-size: 0.7rem; }
  .home-scan-action-main { font-size: 0.72rem; }
  .home-scan-action-sub { display: none; }
  .home-ai-input { min-height: 38px; max-height: 56px; font-size: 0.88rem; }
  .home-ai-main { padding: 8px 10px; gap: 5px; bottom: 8px; }
  .home-ai-toolbar { min-height: 34px; }
  .profile-picker, .tool-picker, .reading-mode-picker, .llm-picker, .home-ai-send { min-height: 32px; }
  .home-ai-send { width: 32px; height: 32px; }
  .hero-home.chat-active { padding: 8px 32px 156px; }
  .hero-home.chat-active.reading-active { padding: 0 32px var(--home-ai-dock-space); }
  .hero-home.chat-active .hero-brand { margin-bottom: 8px; }
  .hero-home.chat-active .hero-brand-icon-wrap { width: 42px; height: 42px; }
  .hero-home.chat-active .hero-brand-icon { width: 34px; height: 34px; transform: translateY(1px); }
  .hero-home.chat-active .hero-brand-name { font-size: 1rem; letter-spacing: 3px; text-indent: 3px; }
}
@media (max-width: 768px) {
  .page-root { --home-ai-dock-space: 124px; --home-ai-chat-bottom-buffer: 136px; }
  .hero-home { min-height: calc(100dvh - 60px); padding: 34px 16px 126px; }
  .hero-home.chat-active { min-height: calc(100dvh - 60px); padding: 10px 16px 162px; }
  .hero-home.chat-active.reading-active { padding: 0 16px var(--home-ai-dock-space); }
  .hero-brand { margin-bottom: 38px; }
  .hero-home.chat-active .hero-brand { gap: 8px; margin-bottom: 10px; }
  .hero-home.chat-active .hero-brand-icon-wrap { width: 48px; height: 48px; margin: 0; }
  .hero-home.chat-active .hero-brand-icon { width: 40px; height: 40px; transform: translateY(2px); }
  .hero-home.chat-active .hero-brand-name { font-size: 1.05rem; letter-spacing: 3px; margin: 0; text-indent: 3px; }
  .hero-home.chat-active .hero-brand-divider { display: none; }
  .hero-home.chat-active .hero-brand-slogan { font-size: 0.68rem; letter-spacing: 2px; }
  .hero-brand-name { font-size: 2rem; letter-spacing: 6px; }
  .hero-brand-slogan { font-size: 0.875rem; letter-spacing: 3px; }
  .home-question-templates { grid-template-columns: repeat(2, minmax(0, 1fr)); width: calc(100vw - 34px); gap: 8px; margin-top: 14px; }
  .home-question-template { min-height: 50px; padding: 8px 10px; }
  .home-question-template-label { font-size: 0.66rem; }
  .home-question-template-text { font-size: 0.72rem; }
  .home-scan-panel { width: 100%; margin-bottom: 12px; gap: 8px; }
  .home-scan-status { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
  .home-scan-status-item { padding: 8px 10px; border-radius: 10px; }
  .home-scan-label { font-size: 0.58rem; margin-bottom: 3px; }
  .home-scan-value { font-size: 0.72rem; }
  .home-scan-actions { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
  .home-scan-action { padding: 8px 9px; border-radius: 12px; }
  .home-scan-action-sub { display: none; }
  .home-ai-console { margin-top: 0; padding-bottom: 0; }
  .home-ai-console.has-chat { width: calc(100vw - 32px); padding: 0; margin-top: 0; }
  .home-ai-console.has-chat .home-ai-chat { flex: 1 1 auto; min-height: 0; max-height: calc(100dvh - 60px - var(--home-ai-dock-space) - 10px); padding-bottom: var(--home-ai-chat-bottom-buffer); overflow-y: auto; overflow-x: hidden; -webkit-overflow-scrolling: touch; overscroll-behavior: contain; touch-action: pan-y; scroll-padding-bottom: var(--home-ai-chat-bottom-buffer); }
  .home-ai-main { bottom: 8px; width: calc(100vw - 18px); border-radius: 16px; }
  .home-ai-main { padding: 9px 10px; gap: 6px; }
  .home-ai-input { min-height: 40px; max-height: 58px; font-size: 0.88rem; }
  .home-ai-console.has-chat .home-ai-input { min-height: 36px; max-height: 54px; }
  .home-ai-toolbar { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.08fr) 72px 72px 30px; align-items: center; gap: 4px; flex-wrap: nowrap !important; overflow: visible; box-sizing: border-box; }
  .home-ai-toolbar-left, .home-ai-toolbar-right { display: contents; }
  .profile-picker, .tool-picker, .reading-mode-picker, .llm-picker { width: 100%; min-width: 0; max-width: none; height: 30px; min-height: 30px; padding: 0 7px; flex-direction: row; align-items: center; justify-content: flex-start; gap: 4px; overflow: hidden; }
  .profile-plus, .tool-picker-icon { width: 18px; height: 18px; font-size: 0.72rem; }
  .profile-name, .tool-picker text:last-child { font-size: 0.66rem; }
  .reading-mode-label, .llm-name { display: block; font-size: 0.64rem; line-height: 1; }
  .reading-mode-points, .llm-points { display: flex; align-items: center; height: 16px; padding: 0 4px; border-radius: 999px; background: var(--accent-glow); color: var(--accent); font-size: 0.5rem; line-height: 1; flex-shrink: 0; }
  .reading-mode-caret, .llm-caret { display: none; }
  .home-ai-send { width: 30px; min-width: 30px; height: 30px; min-height: 30px; font-size: 0.95rem; justify-self: end; }
  .home-ai-message.user, .home-ai-message.assistant { margin-left: 0; margin-right: 0; }
  .home-ai-chat-head { align-items: flex-start; padding: 9px 10px; gap: 8px; }
  .home-ai-chat-sub { max-width: calc(100vw - 148px); font-size: 0.66rem; }
  .home-ai-new-chat { height: 28px; padding: 0 10px; font-size: 0.68rem; }
  .home-ai-context-chip { margin-left: 0; border-radius: 12px; align-items: flex-start; }
  .home-ai-context-chip text:last-child { white-space: normal; }
  .home-ai-step-row { gap: 4px; }
  .home-ai-step-row text { padding: 4px 3px; font-size: 0.56rem; }
  .home-tool-card-head { padding: 9px 10px; }
  .home-artifact-render :deep(.artifact-grid-4),
  .home-artifact-render :deep(.artifact-grid-3),
  .home-artifact-render :deep(.artifact-kv-grid) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .home-artifact-render :deep(.artifact-ziwei-grid) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .home-artifact-render :deep(.bz-artifact-pillars),
  .home-artifact-render :deep(.bz-artifact-meta) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .home-artifact-render :deep(.bz-artifact-head) { flex-direction: column; }
  .home-artifact-render :deep(.zw-artifact-wrap) { overflow-x: auto; overscroll-behavior-x: contain; }
  .home-artifact-render :deep(.zw-artifact-grid) { min-width: 0; width: 100%; grid-template-columns: repeat(4, minmax(68px, 1fr)); grid-template-rows: repeat(4, minmax(94px, auto)); }
  .home-artifact-render :deep(.zw-orientation),
  .home-artifact-render :deep(.zw-flow-row) { min-width: 0; width: 100%; }
  .home-artifact-render :deep(.zw-artifact-center) { padding: 10px 6px; gap: 4px; }
  .home-artifact-render :deep(.zw-artifact-center b) { font-size: .82rem; letter-spacing: 1px; }
  .home-artifact-render :deep(.zw-artifact-center span),
  .home-artifact-render :deep(.zw-artifact-center em) { font-size: .52rem; line-height: 1.25; }
  .home-artifact-render :deep(.gua-display) { grid-template-columns: 1fr; gap: 12px; }
  .home-artifact-render :deep(.ti-yong-grid) { grid-template-columns: 1fr; gap: 8px; }
  .home-artifact-render :deep(.ti-yong-rel) { white-space: normal; }
  .home-artifact-render :deep(.qm-free-layout) { padding: 12px; overflow: hidden; }
  .home-artifact-render :deep(.qm-free-line),
  .home-artifact-render :deep(.qm-free-pillars) { gap: 6px 10px; font-size: .72rem; }
  .home-artifact-render :deep(.qm-free-pillars span) { gap: 5px; }
  .home-artifact-render :deep(.qm-free-layout) { --qm-grid-size: 100%; }
  .home-artifact-render :deep(.qm-nine-grid) { width: min(100%, var(--qm-grid-size)); grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .home-artifact-render :deep(.qm-palace) { padding: 5px; }
  .home-artifact-render :deep(.qm-star-row) { font-size: .76rem; }
  .home-artifact-render :deep(.ly-ben-bian-box) { padding: 12px; }
  .home-artifact-render :deep(.ly-ben-bian-top) { grid-template-columns: minmax(0, 1fr) 20px minmax(0, 1fr); gap: 6px; }
  .home-artifact-render :deep(.ly-ben-bian-name-block) { padding: 9px 6px; }
  .home-artifact-render :deep(.ly-ben-bian-body) { --ly-side-width: 180px; --ly-marker-width: 28px; --ly-yao-width: 52px; --ly-yao-bar: 46px; }
  .home-artifact-render :deep(.ly-visual-side) { gap: 5px; }
  .home-artifact-render :deep(.ly-tag) { min-height: 18px; padding: 1px 4px; border-radius: 5px; font-size: .58rem; }
  .home-artifact-render :deep(.ly-yang-bar),
  .home-artifact-render :deep(.ly-yin-bars) { width: var(--ly-yao-bar); }
  .home-artifact-render :deep(.ly-yin-seg) { width: 18px; }
  .home-artifact-render :deep(.tarot-card-slot) { max-width: 122px; }
  .home-artifact-render :deep(.tarot-card-flipper) { height: 198px; }
  .home-artifact-render :deep(.tarot-cards-display[data-count="6"]) { grid-template-columns: repeat(3, 1fr); max-width: 420px; }
  .home-artifact-render :deep(.tarot-cards-display[data-count="7"]) { grid-template-columns: repeat(4, 1fr); max-width: 560px; }
  .home-artifact-render :deep(.tarot-cards-display[data-count="10"]) { grid-template-columns: repeat(5, 1fr); max-width: 680px; }
  .home-artifact-render { overflow-x: visible; overflow-y: visible; }
  .mini-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .mini-palace:nth-child(3n) { border-right: 1px solid rgba(178,149,93,0.12); }
  .mini-palace:nth-child(2n) { border-right: none; }
  .mini-palace:nth-last-child(-n+3) { border-bottom: 1px solid rgba(178,149,93,0.12); }
  .mini-gua-row, .mini-tarot-row { grid-template-columns: 1fr; }
  .section { padding: 48px 16px; }
  .section-title { font-size: 1.35rem; }
  .section-desc { font-size: 0.8125rem; }
}
@media (max-width: 480px) {
  .page-root { --home-ai-dock-space: 120px; --home-ai-chat-bottom-buffer: 132px; }
  .hero-home { padding: 54px 16px 120px; }
  .hero-home.chat-active { min-height: calc(100dvh - 60px); padding: 10px 16px 156px; }
  .hero-home.chat-active.reading-active { padding: 0 16px var(--home-ai-dock-space); }
  .hero-brand-icon-wrap { width: 120px; height: 120px; }
  .hero-brand-icon { width: 90px; height: 90px; transform: translateY(3px); }
  .hero-brand-name { font-size: 1.6rem; letter-spacing: 4px; }
  .hero-brand-slogan { font-size: 0.75rem; letter-spacing: 3px; }
  .hero-brand-sub { font-size: 0.75rem; }
  .home-scan-panel { display: none; }
  .hero-home.chat-active .hero-brand-slogan { display: none; }
  .home-ai-console.has-chat { width: calc(100vw - 32px); padding-top: 0; }
  .home-ai-console.has-chat .home-ai-chat { flex: 1 1 auto; min-height: 0; max-height: calc(100dvh - 60px - var(--home-ai-dock-space) - 8px); padding: 10px 10px var(--home-ai-chat-bottom-buffer); overflow-y: auto; overflow-x: hidden; -webkit-overflow-scrolling: touch; overscroll-behavior: contain; touch-action: pan-y; scroll-padding-bottom: var(--home-ai-chat-bottom-buffer); }
  .home-ai-main { padding: 7px 9px; gap: 4px; border-radius: 15px; }
  .home-ai-input { min-height: 34px; max-height: 50px; font-size: 0.84rem; padding: 3px 4px 0; }
  .home-ai-toolbar { grid-template-columns: minmax(0, 1fr) minmax(0, 1.05fr) 72px 72px 28px; gap: 3px; overflow: visible; box-sizing: border-box; }
  .profile-picker, .tool-picker, .reading-mode-picker, .llm-picker { height: 28px; min-height: 28px; padding: 0 5px; gap: 3px; }
  .profile-plus, .tool-picker-icon { width: 16px; height: 16px; font-size: 0.66rem; }
  .profile-name, .tool-picker text:last-child { font-size: 0.6rem; }
  .reading-mode-label, .llm-name { font-size: 0.58rem; }
  .reading-mode-points, .llm-points { height: 15px; padding: 0 3px; font-size: 0.46rem; }
  .home-ai-send { width: 28px; min-width: 28px; height: 28px; min-height: 28px; font-size: 0.9rem; }
  .home-ai-chat-head { margin: 0 0 10px; border-radius: 12px; }
  .home-ai-chat-title { font-size: 0.8rem; }
  .home-ai-chat-sub { max-width: calc(100vw - 136px); font-size: 0.6rem; }
  .home-ai-stage-note { font-size: 0.6rem; }
  .home-ai-step-row text { font-size: 0.5rem; }
  .home-artifact-switcher { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
  .home-artifact-tab { min-width: 0; max-width: none; padding: 7px 8px; }
  .home-artifact-tab-title { font-size: .7rem; }
  .home-artifact-tab-sub { font-size: .56rem; }
  .home-ai-summary-panel { padding: 12px; }
  .profile-sheet-panel { bottom: max(10px, env(safe-area-inset-bottom)); max-height: calc(100dvh - 22px); padding: 16px; border-radius: 18px; }
  .profile-sheet-head { flex-shrink: 0; margin-bottom: 10px; }
  .profile-tabs { flex-shrink: 0; }
  .profile-options { max-height: none; }
  .quick-grid { grid-template-columns: 1fr; gap: 9px; }
  .quick-datetime-all { grid-template-columns: minmax(60px, 1.16fr) repeat(4, minmax(44px, 0.92fr)); gap: 5px; }
  .quick-addr-selects { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
  .quick-native-select { padding-left: 6px; padding-right: 16px; font-size: 0.72rem; background-position: calc(100% - 10px) 15px, calc(100% - 6px) 15px; }
  .quick-row { align-items: stretch; flex-direction: column; }
  .quick-save { width: 100%; }
  .home-tool-card-title { font-size: 0.78rem; }
  .home-tool-card-sub { font-size: 0.62rem; }
  .home-artifact-render :deep(.artifact-grid-4),
  .home-artifact-render :deep(.artifact-grid-3),
  .home-artifact-render :deep(.artifact-kv-grid),
  .home-artifact-render :deep(.artifact-ziwei-grid) { grid-template-columns: 1fr; }
  .home-artifact-render :deep(.bz-artifact-panel) { padding: 12px; }
  .home-artifact-render :deep(.bz-artifact-pillars),
  .home-artifact-render :deep(.bz-artifact-meta) { grid-template-columns: 1fr 1fr; gap: 7px; }
  .home-artifact-render :deep(.bz-artifact-gz b) { width: 30px; height: 30px; font-size: .9rem; }
  .home-artifact-render :deep(.zw-artifact-wrap) { overflow-x: auto; overscroll-behavior-x: contain; }
  .home-artifact-render :deep(.zw-artifact-grid) { min-width: 0; width: 100%; grid-template-columns: repeat(4, minmax(58px, 1fr)); grid-template-rows: repeat(4, minmax(88px, auto)); }
  .home-artifact-render :deep(.zw-artifact-palace) { min-height: 100px; padding: 6px; }
  .home-artifact-render :deep(.zw-artifact-top) { font-size: .54rem; }
  .home-artifact-render :deep(.zw-artifact-top b) { font-size: .62rem; }
  .home-artifact-render :deep(.zw-artifact-stars.major span) { font-size: .66rem; }
  .home-artifact-render :deep(.zw-artifact-stars.minor span) { font-size: .58rem; }
  .home-artifact-render :deep(.zw-artifact-stars.adj span),
  .home-artifact-render :deep(.zw-artifact-support),
  .home-artifact-render :deep(.zw-artifact-ages) { font-size: .48rem; }
  .home-artifact-render :deep(.zw-artifact-foot) { font-size: .5rem; }
  .home-artifact-render :deep(.zw-artifact-center) { padding: 8px 5px; gap: 3px; }
  .home-artifact-render :deep(.zw-artifact-center b) { font-size: .68rem; letter-spacing: 0; }
  .home-artifact-render :deep(.zw-artifact-center span),
  .home-artifact-render :deep(.zw-artifact-center em) { font-size: .45rem; line-height: 1.22; }
  .home-artifact-render :deep(.zw-orientation),
  .home-artifact-render :deep(.zw-flow-row) { min-width: 0; width: 100%; }
  .home-artifact-render :deep(.qm-free-layout) { padding: 10px; overflow: hidden; }
  .home-artifact-render :deep(.qm-free-title) { font-size: .9rem; }
  .home-artifact-render :deep(.qm-free-line),
  .home-artifact-render :deep(.qm-free-pillars) { gap: 5px 8px; font-size: .66rem; }
  .home-artifact-render :deep(.qm-free-pillars span) { gap: 4px; }
  .home-artifact-render :deep(.qm-free-pillars strong) { font-size: .8rem; }
  .home-artifact-render :deep(.qm-free-layout) { --qm-grid-size: 100%; }
  .home-artifact-render :deep(.qm-nine-grid) { width: min(100%, var(--qm-grid-size)); grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .home-artifact-render :deep(.qm-palace) { padding: 4px; }
  .home-artifact-render :deep(.qm-palace-head) { font-size: .56rem; }
  .home-artifact-render :deep(.qm-palace-head b) { font-size: .66rem; }
  .home-artifact-render :deep(.qm-star-row) { font-size: .68rem; gap: 2px; }
  .home-artifact-render :deep(.qm-info-row) { font-size: .58rem; }
  .home-artifact-render :deep(.qm-palace-line) { min-height: 14px; font-size: .54rem; gap: 2px; }
  .home-artifact-render :deep(.qm-center-date) { font-size: .5rem; }
  .home-artifact-render :deep(.qm-center-xun),
  .home-artifact-render :deep(.qm-center-pillars),
  .home-artifact-render :deep(.qm-center-meta) { font-size: .44rem; }
  .home-artifact-render :deep(.qm-center-title) { font-size: .46rem; }
  .home-artifact-render :deep(.ly-ben-bian-box) { padding: 9px; }
  .home-artifact-render :deep(.ly-ben-bian-top) { grid-template-columns: minmax(0, 1fr) 18px minmax(0, 1fr); gap: 4px; margin-bottom: 8px; }
  .home-artifact-render :deep(.ly-ben-bian-name-block) { min-height: 74px; padding: 6px 5px; }
  .home-artifact-render :deep(.ly-ben-bian-name-text) { font-size: .92rem; letter-spacing: 0; }
  .home-artifact-render :deep(.ly-ben-bian-label) { font-size: .58rem; letter-spacing: 1px; }
  .home-artifact-render :deep(.ly-trigram-badge) { padding: 3px 5px; font-size: .56rem; }
  .home-artifact-render :deep(.ly-ben-bian-top-arrow) { transform: none; text-align: center; }
  .home-artifact-render :deep(.ly-ben-bian-body) { gap: 3px; }
  .home-artifact-render :deep(.ly-paired-row),
  .home-artifact-render :deep(.ly-paired-row.has-bian) { grid-template-columns: minmax(0, 1fr) 1px minmax(0, 1fr); gap: 2px; padding: 3px 2px; border-radius: 8px; }
  .home-artifact-render :deep(.ly-row-divider) { width: 1px; height: auto; }
  .home-artifact-render :deep(.ly-ben-bian-body) { --ly-side-width: 138px; --ly-marker-width: 20px; --ly-yao-width: 42px; --ly-yao-bar: 36px; }
  .home-artifact-render :deep(.ly-visual-side) { gap: 3px; }
  .home-artifact-render :deep(.ly-yao-tags-left) { gap: 2px; }
  .home-artifact-render :deep(.ly-tag) { min-height: 13px; padding: 0 2px; border-radius: 3px; font-size: .43rem; line-height: 1.05; }
  .home-artifact-render :deep(.ly-yao-pos) { width: 1em; font-size: .5rem; line-height: 1.05; text-align: center; white-space: normal; }
  .home-artifact-render :deep(.ly-paired-info),
  .home-artifact-render :deep(.ly-paired-bian-info) { display: grid; grid-template-columns: auto 1fr; justify-items: center; align-content: center; column-gap: 3px; row-gap: 1px; }
  .home-artifact-render :deep(.ly-paired-info .ly-yao-pos),
  .home-artifact-render :deep(.ly-paired-bian-info .ly-yao-pos) { grid-column: 1; grid-row: 1 / 4; align-self: center; }
  .home-artifact-render :deep(.ly-paired-info .ly-tag),
  .home-artifact-render :deep(.ly-paired-bian-info .ly-tag) { grid-column: 2; min-height: auto; padding: 0; border-radius: 0; background: transparent; font-size: .5rem; line-height: 1.05; }
  .home-artifact-render :deep(.ly-yang-bar),
  .home-artifact-render :deep(.ly-yin-bars) { width: var(--ly-yao-bar); }
  .home-artifact-render :deep(.ly-yin-seg) { width: 14px; }
  .home-artifact-render :deep(.tarot-cards-display),
  .home-artifact-render :deep(.tarot-cards-display[data-count="3"]),
  .home-artifact-render :deep(.tarot-cards-display[data-count="5"]),
  .home-artifact-render :deep(.tarot-cards-display[data-count="6"]) { grid-template-columns: repeat(2, 1fr); max-width: 260px; gap: 12px; }
  .home-artifact-render :deep(.tarot-cards-display[data-count="7"]),
  .home-artifact-render :deep(.tarot-cards-display[data-count="10"]) { grid-template-columns: repeat(3, 1fr); max-width: 390px; gap: 10px; }
  .home-artifact-render :deep(.tarot-card-slot) { max-width: 112px; }
  .home-artifact-render :deep(.tarot-card-flipper) { height: 184px; }
  .home-artifact-render :deep(.tarot-card-name) { font-size: .78rem; }
  .mini-line { align-items: flex-start; flex-direction: column; gap: 3px; }
  .section { padding: 32px 16px; }
  .section-title { font-size: 1.15rem; }
  .section-desc { font-size: 0.75rem; }
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .footer-col:nth-child(3) { grid-column: 1 / -1; }
  .site-footer { padding: 32px 16px 24px; margin-top: 0; }
  .footer-bottom { flex-direction: column; gap: 8px; text-align: center; }
}

@media (max-width: 520px) {
  .home-guidance-note { width: calc(100vw - 24px); flex-direction: column; gap: 4px; font-size: 0.68rem; }
  .question-guide-panel { bottom: max(10px, env(safe-area-inset-bottom)); max-height: calc(100dvh - 22px); overflow-y: auto; padding: 16px; }
  .question-guide-progress { align-items: flex-start; flex-direction: column; gap: 3px; }
  .question-guide-chip { min-height: 30px; font-size: 0.72rem; }
}
</style>
