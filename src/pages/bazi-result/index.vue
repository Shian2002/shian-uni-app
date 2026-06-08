<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :isLoggedIn="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- 结果展示区 -->
      <view class="result-container">
        <view id="resultArea">
          <!-- 加载状态 -->
          <view v-if="loading" class="loading-state">
            <view class="loading-spinner"></view>
            <view style="font-size:0.9375rem;">排盘计算中...</view>
          </view>
          <!-- 错误状态 -->
          <view v-else-if="errorMsg" class="error-state">
            <view class="error-icon">❌</view>
            <view class="error-msg">{{ errorMsg }}</view>
            <view class="btn-retry" @tap="goHome">返回首页</view>
          </view>
          <!-- 结果内容 -->
          <view v-else-if="baziData">
            <view class="agent-handoff-bar">
              <view>
                <text class="agent-handoff-title">用时安agent解读此盘</text>
                <text class="agent-handoff-sub">带入完整八字盘面、出生参数和当前设置</text>
              </view>
              <view class="agent-handoff-btn" @tap="sendBaziToAgent">去解读</view>
            </view>
            <!-- Tab布局 -->
            <view class="tab-layout">
              <!-- 侧边栏 -->
              <view class="tab-sidebar">
                <view id="baziTabInfo" class="tab-btn" :class="{ active: activeTab === 'info' }" @tap="switchTab('info')">基本信息</view>
                <view id="baziTabBasic" class="tab-btn" :class="{ active: activeTab === 'basic' }" @tap="switchTab('basic')">基本排盘</view>
                <view id="baziTabWzpro" class="tab-btn" :class="{ active: activeTab === 'wzpro' }" @tap="switchTab('wzpro')">专业排盘</view>
                <view id="baziTabNotes" class="tab-btn" :class="{ active: activeTab === 'notes' }" @tap="switchTab('notes')">📝 笔记</view>
                <view id="baziTabSettings" class="tab-btn" :class="{ active: activeTab === 'settings' }" @tap="switchTab('settings')">⚙ 设置</view>
                <view class="tab-btn tab-return-btn" @tap="goBaziHome">↩ 返回排盘</view>
              </view>
              <!-- 内容区 -->
              <view class="tab-content-area">
                <!-- Tab1: 基本信息 -->
                <view id="baziPanelInfo" class="tab-panel" :class="{ active: activeTab === 'info' }">
                  <view v-if="baziData">
                    <!-- 基本信息卡片 -->
                    <view class="info-card" style="margin-bottom:14px;">
                      <view class="card-title">📋 基本信息</view>
                      <view class="basic-info-grid">
                        <view class="basic-info-item" :class="{ 'full-width': item.fullWidth }" v-for="item in infoItems" :key="item.label">
                          <text class="label">{{ item.label }}：</text>
                          <text class="value">{{ item.value }}</text>
                        </view>
                      </view>
                      <view v-if="baziData.true_solar_time && baziData.true_solar_time !== baziData.birth_input" style="font-size:0.78rem;color:var(--text-3);margin-top:8px;padding-top:8px;border-top:1px solid var(--card-border);">
                        🕐 真太阳时：{{ baziData.true_solar_time }}
                      </view>
                    </view>

                    <!-- 今日干支 -->
                    <view class="info-card" v-if="baziData.today_paipan && baziData.today_paipan.date" style="margin-bottom:14px;">
                      <view class="card-title">📅 今日干支 <text style="font-weight:400;font-size:0.74rem;color:var(--text-3);">{{ baziData.today_paipan.date }}</text></view>
                      <view style="display:flex;gap:12px;justify-content:center;padding:6px 0;">
                        <view style="text-align:center;" v-if="baziData.today_paipan.year">
                          <view style="font-size:0.68rem;color:var(--text-3);margin-bottom:2px;">年</view>
                          <view style="font-size:1.1rem;font-weight:700;color:var(--text-1);">{{ baziData.today_paipan.year.gan_zhi || '' }}</view>
                        </view>
                        <view style="text-align:center;" v-if="baziData.today_paipan.month">
                          <view style="font-size:0.68rem;color:var(--text-3);margin-bottom:2px;">月</view>
                          <view style="font-size:1.1rem;font-weight:700;color:var(--text-1);">{{ baziData.today_paipan.month.gan_zhi || '' }}</view>
                        </view>
                        <view style="text-align:center;" v-if="baziData.today_paipan.day">
                          <view style="font-size:0.68rem;color:var(--text-3);margin-bottom:2px;">日</view>
                          <view style="font-size:1.1rem;font-weight:700;color:var(--text-1);">{{ baziData.today_paipan.day.gan_zhi || '' }}</view>
                        </view>
                        <view style="text-align:center;" v-if="baziData.today_paipan.hour">
                          <view style="font-size:0.68rem;color:var(--text-3);margin-bottom:2px;">时</view>
                          <view style="font-size:1.1rem;font-weight:700;color:var(--text-1);">{{ baziData.today_paipan.hour.gan_zhi || '' }}</view>
                        </view>
                      </view>
                    </view>

                    <!-- 起运+节气 -->
                    <view class="info-card" v-if="baziData.qi_yun_detail || baziData.jie_qi_range" style="margin-bottom:14px;">
                      <view v-if="baziData.qi_yun_detail && baziData.qi_yun_detail.text">
                        <view class="card-title">🕐 起运信息</view>
                        <view class="card-content">
                          <view>{{ baziData.qi_yun_detail.text }}</view>
                          <view v-if="baziData.qi_yun_detail.jiao_yun_text" style="margin-top:4px;font-size:0.74rem;color:var(--text-3);">{{ baziData.qi_yun_detail.jiao_yun_text }}</view>
                        </view>
                      </view>
                      <view v-if="baziData.jie_qi_range && baziData.jie_qi_range.prev_name" style="margin-top:10px;padding-top:10px;border-top:1px solid var(--card-border);">
                        <view class="card-title">🌿 节气</view>
                        <view class="card-content">
                          <view v-if="baziData.jie_qi_range.prev_name">前：{{ baziData.jie_qi_range.prev_name }} {{ baziData.jie_qi_range.prev_time || '' }}</view>
                          <view v-if="baziData.jie_qi_range.next_name">后：{{ baziData.jie_qi_range.next_name }} {{ baziData.jie_qi_range.next_time || '' }}</view>
                          <view v-if="baziData.jie_qi_range.after_text" style="margin-top:4px;color:var(--text-3);font-size:0.72rem;">{{ baziData.jie_qi_range.after_text }}</view>
                        </view>
                      </view>
                    </view>

                    <!-- 性格简析 -->
                    <view class="info-card" v-if="baziData.personality && baziData.personality.summary" style="margin-bottom:14px;">
                      <view class="card-title">🎭 性格简析</view>
                      <view style="font-size:0.84rem;color:var(--text-2);line-height:1.7;margin-bottom:8px;">{{ baziData.personality.summary }}</view>
                      <view v-if="baziData.personality.traits && baziData.personality.traits.length" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">
                        <text v-for="(t, ti) in baziData.personality.traits" :key="ti" style="font-size:0.72rem;padding:3px 10px;border-radius:20px;background:var(--tag-bg);color:var(--accent);border:1px solid var(--accent-glow);">{{ t }}</text>
                      </view>
                      <view v-if="baziData.personality.negative" style="font-size:0.74rem;color:var(--danger);">⚠️ 需注意：{{ baziData.personality.negative }}</view>
                    </view>

                    <!-- 命理提示 -->
                    <view class="info-card" v-if="baziData.personality && baziData.personality.advice" style="margin-bottom:14px;">
                      <view class="card-title">📜 命理提示</view>
                      <view style="font-size:0.82rem;color:var(--text-2);line-height:1.7;margin-bottom:8px;">{{ baziData.personality.advice }}</view>
                      <view v-if="baziData.personality.career" style="font-size:0.78rem;color:var(--info);margin-bottom:4px;">💼 事业：{{ baziData.personality.career }}</view>
                      <view v-if="baziData.personality.wealth" style="font-size:0.78rem;color:var(--success);margin-bottom:4px;">💰 财运：{{ baziData.personality.wealth }}</view>
                      <view v-if="baziData.personality.relationship" style="font-size:0.78rem;color:var(--danger);">💕 感情：{{ baziData.personality.relationship }}</view>
                    </view>

                    <!-- 胎元宫息 -->
                    <view class="info-card" v-if="baziData.tai_ming_shen" style="margin-bottom:14px;">
                      <view class="card-title">🔮 胎元宫息</view>
                      <view class="card-content">
                        <view class="mingli-row" v-if="baziData.tai_ming_shen.tai_yuan">
                          <text class="ml-label">胎元</text>
                          <text class="ml-value">{{ baziData.tai_ming_shen.tai_yuan.gan_zhi || '' }}</text>
                          <text class="ml-sub">{{ baziData.tai_ming_shen.tai_yuan.nayin || '' }}</text>
                        </view>
                        <view class="mingli-row" v-if="baziData.tai_ming_shen.ming_gong">
                          <text class="ml-label">命宫</text>
                          <text class="ml-value">{{ baziData.tai_ming_shen.ming_gong.gan_zhi || '' }}</text>
                          <text class="ml-sub">{{ baziData.tai_ming_shen.ming_gong.nayin || '' }}</text>
                        </view>
                        <view class="mingli-row" v-if="baziData.tai_ming_shen.shen_gong">
                          <text class="ml-label">身宫</text>
                          <text class="ml-value">{{ baziData.tai_ming_shen.shen_gong.gan_zhi || '' }}</text>
                          <text class="ml-sub">{{ baziData.tai_ming_shen.shen_gong.nayin || '' }}</text>
                        </view>
                        <view class="mingli-row" v-if="baziData.tai_xi && baziData.tai_xi.gan_zhi">
                          <text class="ml-label">胎息</text>
                          <text class="ml-value">{{ baziData.tai_xi.gan_zhi }}</text>
                          <text class="ml-sub">{{ baziData.tai_xi.nayin || '' }}</text>
                        </view>
                      </view>
                    </view>

                    <!-- 命理信息 -->
                    <view class="info-card" v-if="baziData.ming_gua || baziData.xing_su" style="margin-bottom:14px;">
                      <view class="card-title">🧭 命理信息</view>
                      <view class="card-content">
                        <view class="mingli-row" v-if="baziData.ming_gua && baziData.ming_gua.gua_name">
                          <text class="ml-label">命卦</text>
                          <text class="ml-value">{{ baziData.ming_gua.gua_name }}</text>
                          <text class="ml-sub">{{ baziData.ming_gua.group || '' }}</text>
                        </view>
                        <view class="mingli-row" v-if="baziData.xing_su">
                          <text class="ml-label">星宿</text>
                          <text class="ml-value">{{ baziData.xing_su }}</text>
                        </view>
                      </view>
                    </view>

                    <!-- 称骨 -->
                    <view class="info-card" v-if="chengGu" style="margin-bottom:14px;">
                      <view class="card-title">⚖️ 袁天罡称骨</view>
                      <view class="card-content">
                        <view style="display:flex;align-items:baseline;gap:8px;margin-bottom:2px;">
                          <text style="font-size:1.2rem;font-weight:700;color:var(--accent);">{{ chengGu.weight || '' }}</text>
                          <text style="font-size:0.72rem;color:var(--text-3);">满分7两2钱</text>
                        </view>
                        <view class="chenggu-bar-track" v-if="chengGu.weight_gram">
                          <view class="chenggu-bar-fill" :style="{ width: Math.min(100, Math.round((chengGu.weight_gram / 7.2) * 100)) + '%' }"></view>
                        </view>
                        <text class="chenggu-poem" style="margin-top:8px;display:block;">{{ chengGu.poem || '' }}</text>
                      </view>
                    </view>
                  </view>
                </view>

                <!-- Tab2: 基本排盘 -->
                <view id="baziPanelBasic" class="tab-panel" :class="{ active: activeTab === 'basic' }">
                  <view class="basic-layout">
                    <view class="basic-left">
                      <!-- 四柱表格 -->
                      <view class="pillar-table-wrap">
                        <view class="pillar-row header-row">
                          <view class="pillar-cell label-cell"></view>
                          <view class="pillar-cell" v-for="(pillar, key) in fourPillars" :key="key">
                            <text class="pillar-header">{{ pillarLabels[key] }}</text>
                          </view>
                        </view>
                        <view class="pillar-row">
                          <view class="pillar-cell label-cell">主星</view>
                          <view class="pillar-cell zhuxing-cell" v-for="(pillar, key) in fourPillars" :key="'zx'+key">
                            <text :class="ssTagClass(shiShen[key])" class="ss-full-text">{{ key === 'day' ? dayMasterLabel : fixShiShenName(shiShen[key]) }}</text>
                          </view>
                        </view>
                        <view class="pillar-row">
                          <view class="pillar-cell label-cell">天干</view>
                          <view class="pillar-cell gan-cell" v-for="(pillar, key) in fourPillars" :key="'gan'+key">
                            <rich-text :nodes="wxSpanBZ(pillar.gan)"></rich-text>
                          </view>
                        </view>
                        <view class="pillar-row">
                          <view class="pillar-cell label-cell">地支</view>
                          <view class="pillar-cell zhi-cell" v-for="(pillar, key) in fourPillars" :key="'zhi'+key">
                            <rich-text :nodes="wxSpanBZ(pillar.zhi)"></rich-text>
                          </view>
                        </view>
                        <view class="pillar-row">
                          <view class="pillar-cell label-cell">副星</view>
                          <view class="pillar-cell fuxing-cell" v-for="(pillar, key) in fourPillars" :key="'fx'+key">
                            <text v-for="(cgSs, ci) in (cangGanShiShen[key] || [])" :key="ci" :class="ssTagClass(cgSs)" class="ss-full-text ss-vertical">{{ fixShiShenName(cgSs) }}</text>
                          </view>
                        </view>
                        <view class="pillar-row">
                          <view class="pillar-cell label-cell">藏干</view>
                          <view class="pillar-cell cang-gan-cell" v-for="(pillar, key) in fourPillars" :key="'cg'+key">
                            <text v-for="(cg, ci) in (cangGan[key] || [])" :key="ci" class="cg-wx-text">
                              <rich-text :nodes="wxSpanStr(cg + (GAN_WUXING[cg] || ''))"></rich-text>
                            </text>
                          </view>
                        </view>
                        <view class="pillar-row">
                          <view class="pillar-cell label-cell">星运</view>
                          <view class="pillar-cell xingyun-cell" v-for="(pillar, key) in fourPillars" :key="'xy'+key">
                            <text>{{ xingYun[key] || '' }}</text>
                          </view>
                        </view>
                        <view class="pillar-row">
                          <view class="pillar-cell label-cell">自坐</view>
                          <view class="pillar-cell zizuo-cell" v-for="(pillar, key) in fourPillars" :key="'zz'+key">
                            <text>{{ ziZuo[key] || '' }}</text>
                          </view>
                        </view>
                        <view class="pillar-row">
                          <view class="pillar-cell label-cell">空亡</view>
                          <view class="pillar-cell kongwang-cell" v-for="(pillar, key) in fourPillars" :key="'kw'+key">
                            <text>{{ kongWangPerPillar[key] || '' }}</text>
                          </view>
                        </view>
                        <view class="pillar-row">
                          <view class="pillar-cell label-cell">纳音</view>
                          <view class="pillar-cell nayin-cell" v-for="(pillar, key) in fourPillars" :key="'ny'+key">
                            <text>{{ naYin[key] || '' }}</text>
                          </view>
                        </view>
                        <view class="pillar-row" v-if="shenShaPerPillar && Object.keys(shenShaPerPillar).length">
                          <view class="pillar-cell label-cell">神煞</view>
                          <view class="pillar-cell shensha-cell" v-for="(pillar, key) in fourPillars" :key="'ss2'+key">
                            <text class="ss-tag" v-for="(ss, si) in (shenShaPerPillar[key] || [])" :key="si">{{ ss }}</text>
                          </view>
                        </view>
                      </view>
                    </view>
                    <view class="basic-right">
                      <view class="info-card">
                        <view class="card-title">五行统计</view>
                        <view class="card-content">
                          <view class="wx-bar" v-for="(wx, name) in wuXingStats" :key="name">
                            <text class="wx-name" :style="{ color: wxColorMap[name] }">{{ name }}</text>
                            <view class="wx-track"><view class="wx-fill" :style="{ width: wx.count * 20 + '%', background: wxColorMap[name] }"></view></view>
                            <text class="wx-count">{{ wx.count }}</text>
                          </view>
                          <view v-if="baziData.lack_wuxing && baziData.lack_wuxing.length" style="margin-top:6px;font-size:0.78rem;color:var(--danger);">
                            缺<text v-for="(lx, lxi) in baziData.lack_wuxing" :key="lxi" :style="{ color: wxColorMap[lx], fontWeight: '700' }">{{ lx }}</text>
                          </view>
                          <view v-else style="margin-top:6px;font-size:0.78rem;color:var(--success);">五行俱全</view>
                          <view v-if="wangXiangXiu.length" style="margin-top:6px;display:flex;flex-wrap:wrap;gap:4px;">
                            <text v-for="(w, wi) in wangXiangXiu" :key="wi" class="wxxs-tag" :class="w.includes('旺')?'wx-wang':w.includes('相')?'wx-xiang':w.includes('休')?'wx-xiu':w.includes('囚')?'wx-qiu':'wx-si'">{{ w }}</text>
                          </view>
                        </view>
                      </view>
                      <view class="info-card" v-if="wangShuai || (baziData.geju && baziData.geju.geju)">
                        <view class="card-title">旺衰 · 格局</view>
                        <view class="card-content" style="display:flex;gap:8px;flex-wrap:wrap;">
                          <text v-if="wangShuai" style="font-size:0.84rem;font-weight:600;padding:2px 10px;border-radius:10px;background:rgba(7,233,48,0.1);color:#07e930;border:1px solid rgba(7,233,48,0.3);">{{ wangShuai }}</text>
                          <text v-if="baziData.geju && baziData.geju.geju" style="font-size:0.84rem;font-weight:600;padding:2px 10px;border-radius:10px;background:rgba(46,131,246,0.1);color:#2e83f6;border:1px solid rgba(46,131,246,0.3);">{{ baziData.geju.geju }}</text>
                        </view>
                      </view>
                      <view class="info-card" v-if="allGuanxiTags.length">
                        <view class="card-title">冲合关系</view>
                        <view class="card-content" style="display:flex;flex-wrap:wrap;gap:4px;">
                          <text v-for="(tag, ti) in allGuanxiTags" :key="ti" style="font-size:0.72rem;padding:2px 8px;border-radius:10px;border:1px solid;" :style="{ borderColor: tag.color, color: tag.color }">{{ tag.label }}</text>
                        </view>
                      </view>
                      <view class="info-card" v-if="chengGu">
                        <view class="card-title">称骨算命</view>
                        <view class="card-content">
                          <text class="chenggu-weight">{{ chengGu.weight || '' }}</text>
                          <text class="chenggu-poem">{{ chengGu.poem || '' }}</text>
                        </view>
                      </view>
                      <view class="info-card" v-if="baziData.kong_wang && baziData.kong_wang.length">
                        <view class="card-title">空亡</view>
                        <view class="card-content">{{ baziData.kong_wang.join ? baziData.kong_wang.join('、') : baziData.kong_wang }}</view>
                      </view>
                    </view>
                  </view>
                </view>

                <!-- Tab3: 专业排盘（问真风格1:1复刻） -->
                <view id="baziPanelWzpro" class="tab-panel" :class="{ active: activeTab === 'wzpro' }">
                  <view v-if="baziData" class="wzpro-wrap">
                    <!-- Top bar -->
                    <view class="wz-top-bar">
                      <view class="wz-case-info">
                        <text style="font-size:1.4rem;">{{ shengxiaoEmoji }}</text>
                        <view style="display:flex;flex-direction:column;gap:2px;">
                          <text style="font-weight:700;color:var(--text-1);">{{ baziData.name || '命主' }} <text style="color:var(--accent);font-size:0.78rem;">{{ baziData.gender || '' }}</text></text>
                          <text style="font-size:0.68rem;color:var(--text-3);">阴历：{{ baziData.birth_lunar || '' }}</text>
                          <text style="font-size:0.68rem;color:var(--text-3);">阳历：{{ baziData.birth_solar || '' }}</text>
                        </view>
                      </view>
                      <view class="wz-top-actions">
                        <view class="tms-toggle" :class="{active: showTMS}" @tap="showTMS = !showTMS">
                          <view class="toggle-dot"></view> 胎命身
                        </view>
                        <view class="tms-toggle layout-toggle" :class="{active: colOrder === 'sz-first'}" @click.stop="toggleColOrder" title="切换列顺序">
                          <text class="layout-icon">⇄</text> {{ colOrder === 'sz-first' ? '大运前' : '四柱前' }}
                        </view>
                      </view>
                    </view>

                    <!-- 胎命身横排 -->
                    <view class="wz-tms-bar" v-if="showTMS">
                      <view class="wz-tms-item" v-for="tms in tmsItems" :key="tms.key">
                        <view class="wz-tms-label">{{ tms.label }}</view>
                        <view class="wz-tms-value"><rich-text :nodes="tms.html"></rich-text></view>
                        <view class="wz-tms-sub" v-if="tms.nayin">{{ tms.nayin }}</view>
                      </view>
                      </view>
                    <!-- 起运摘要栏 -->
                    <view class="wz-summary-bar" v-if="qiyunSummary">
                      <view class="wz-qiyun-text">{{ qiyunSummary }}</view>
                      <view class="wz-qiyun-extra" v-if="wzProData && wzProData.jiaoyun_info">{{ wzProData.jiaoyun_info }}</view>
                    </view>

                    <!-- Main layout -->
                    <view class="wz-pan-layout">
                      <view class="wz-pan-left">
                        <view class="wz-pan-table-inner">
                          <view class="wz-row header-row" :key="'hdr-'+yunRefreshKey">
                            <view class="wz-row-item label-cell">日期</view>
                            <view class="wz-row-item" v-for="(h, i) in colLabels" :key="'hdr-'+yunRefreshKey+'-'+i">{{ h }}</view>
                          </view>
                          <view class="wz-row" :class="row.cls" v-for="row in proPanRows" :key="'row-'+yunRefreshKey+'-'+row.key">
                            <view class="wz-row-item label-cell">{{ row.label }}</view>
                            <view class="wz-row-item" :class="{'wz-pro-sep': (row.key === 'zhuxing' || row.key === 'tg' || row.key === 'dz') && i === proSepIdx}" v-for="(col, i) in colData" :key="'cd-'+yunRefreshKey+'-'+i">
                              <template v-if="row.key === 'tg'">
                                <rich-text :nodes="wxSpanBZ(col.tg || '')"></rich-text>
                              </template>
                              <template v-else-if="row.key === 'dz'">
                                <rich-text :nodes="wxSpanBZ(col.dz || '')"></rich-text>
                              </template>
                              <template v-else-if="row.key === 'ss'">
                                <text>{{ col.ss || '' }}</text>
                              </template>
                              <template v-else-if="row.key === 'zhuxing'">
                                <text class="mainColor">{{ col.zhuxing || '' }}</text>
                              </template>
                              <template v-else-if="row.key === 'cg'">
                                <view class="wz-cg-list wz-cg-wrap">
                                  <view class="wz-cg-item" v-for="(cg, cgi) in (col.canggan || [])" :key="cgi">
                                    <rich-text :nodes="wxSpanBZ(cg.gz || cg)"></rich-text>
                                    <text class="wz-cg-ss" v-if="cg.ss">{{ fixShiShenName(cg.ss) }}</text>
                                  </view>
                                </view>
                              </template>
                              <template v-else-if="row.key === 'xy'">
                                <text>{{ col.xingyun || '' }}</text>
                              </template>
                              <template v-else-if="row.key === 'zz'">
                                <text>{{ col.zizuo || '' }}</text>
                              </template>
                              <template v-else-if="row.key === 'dishi'">
                                <text>{{ col.dishi || '' }}</text>
                              </template>
                              <template v-else-if="row.key === 'kw'">
                                <text>{{ col.kongwang || '' }}</text>
                              </template>
                              <template v-else-if="row.key === 'ny'">
                                <text>{{ col.nayin || '' }}</text>
                              </template>
                              <template v-else-if="row.key === 'shensha'">
                                <view class="wz-ss-list">
                                  <text class="wz-ss-tag" v-for="(ss, ssi) in (col.shensha || [])" :key="ssi">{{ ss }}</text>
                                </view>
                              </template>
                            </view>
                          </view>
                          <view class="wz-ss-division"></view>
                          <view class="wz-row ss-row" :key="'ss-'+yunRefreshKey">
                            <view class="wz-row-item label-cell">神煞</view>
                            <view class="wz-row-item" v-for="(col, i) in colData" :key="'ss-cd-'+yunRefreshKey+'-'+i">
                              <text class="wz-ss-tag" :class="ssTagClass(s)" v-for="(s, si) in (col.shensha || [])" :key="si">{{ s }}</text>
                              <text v-if="!(col.shensha && col.shensha.length)">-</text>
                            </view>
                          </view>
                        </view>
                      </view>

                      <view class="wz-pan-right">
                        <view class="wz-yun-section">
                          <view class="wz-yun-switch-tabs">
                            <view class="wz-yun-tab" :class="{ active: activeYunType === 'dayun' }" @click="switchYunType('dayun')">大运</view>
                            <view class="wz-yun-tab" :class="{ active: activeYunType === 'xiaoyun' }" @click="switchYunType('xiaoyun')">小运</view>
                          </view>
                          <view class="wz-yun-items-wrap">
                            <view class="wz-yun-items" id="wz-yun-main"></view>
                          </view>
                        </view>

                        <view class="wz-yun-section" v-if="filteredLiuNian.length">
                          <view class="wz-yun-title">流年 <text class="wz-today-btn" @click="jumpToToday">今</text></view>
                          <view class="wz-yun-items-wrap">
                            <view class="wz-yun-items" id="wz-yun-liunian"></view>
                          </view>
                        </view>

                        <view class="wz-yun-section" v-if="proLiuYue.length">
                          <view class="wz-yun-title">流月</view>
                          <view class="wz-yun-items-wrap">
                            <view class="wz-yun-items" id="wz-yun-liuyue"></view>
                          </view>
                        </view>
                      </view>
                    </view>

                    <!-- 干支留意 -->
                    <view class="wz-guanxi-box" v-if="proGuanxi || proWuxingWangduSorted.length">
                      <view class="wz-guanxi-box-title"><text class="wz-guanxi-box-icon">⚡</text> 干支留意</view>
                      <view class="wz-guanxi-box-body" style="flex-direction:column;gap:6px;">
                        <view class="wz-guanxi-item" style="width:100%;" v-if="proGuanxi && proGuanxi.tg">
                          <text class="wz-guanxi-label">天干</text>
                          <text class="wz-guanxi-text">{{ proGuanxi.tg }}</text>
                        </view>
                        <view class="wz-guanxi-item" style="width:100%;" v-if="proGuanxi && proGuanxi.dz">
                          <text class="wz-guanxi-label">地支</text>
                          <text class="wz-guanxi-text">{{ proGuanxi.dz }}</text>
                        </view>
                        <view class="wz-guanxi-wx-row" style="width:100%;" v-if="proWuxingWangduSorted.length">
                          <text class="wz-guanxi-label">五行</text>
                          <view class="wz-guanxi-wx-items">
                            <text class="wz-guanxi-wx-tag" v-for="wx in proWuxingWangduSorted" :key="wx.name" :style="{borderColor: wx.color, color: wx.color}">{{ wx.name }}<text style="font-weight:700;">{{ wx.wang }}</text></text>
                          </view>
                        </view>
                      </view>
                    </view>

                    <!-- 参考用神 + 格局 + 称骨 -->
                    <view class="wz-pro-bottom-info" v-if="baziData.tiaohou || baziData.geju || baziData.cheng_gu" style="margin-top:12px;">
                      <view class="wz-pro-bottom-card" v-if="baziData.tiaohou && (baziData.tiaohou.yong_shen || baziData.tiaohou.tiao_hou)">
                        <view class="wz-pro-bottom-card-title">⚡ 参考用神</view>
                        <view style="display:flex;flex-wrap:wrap;gap:6px;">
                          <text v-if="baziData.tiaohou.yong_shen" class="info-tag">用 {{ baziData.tiaohou.yong_shen }}</text>
                          <text v-if="baziData.tiaohou.tiao_hou" class="info-tag">候 {{ baziData.tiaohou.tiao_hou }}</text>
                          <text v-if="baziData.tiaohou.xi_shen" class="info-tag">喜 {{ baziData.tiaohou.xi_shen }}</text>
                          <text v-if="baziData.tiaohou.ji_shen" class="info-tag">忌 {{ baziData.tiaohou.ji_shen }}</text>
                        </view>
                      </view>
                      <view class="wz-pro-bottom-card" v-if="baziData.geju && baziData.geju.desc">
                        <view class="wz-pro-bottom-card-title">🏛 格局</view>
                        <text style="font-size:0.78rem;color:var(--text-2);line-height:1.6;">{{ baziData.geju.desc }}</text>
                      </view>
                      <view class="wz-pro-bottom-card" v-if="baziData.cheng_gu && baziData.cheng_gu.weight">
                        <view class="wz-pro-bottom-card-title">⚖ 袁天罡称骨</view>
                        <text style="font-size:0.84rem;font-weight:700;color:var(--accent);">{{ baziData.cheng_gu.weight }}</text>
                        <text v-if="baziData.cheng_gu.poem" style="font-size:0.72rem;color:var(--text-3);display:block;margin-top:4px;">{{ baziData.cheng_gu.poem }}</text>
                      </view>
                    </view>

                    <!-- 旺衰详情 -->
                    <view class="wz-section-card" v-if="baziData.wang_shuai_detail && baziData.wang_shuai_detail.detail" style="margin-top:10px;">
                      <text class="wz-section-title">📊 旺衰分析</text>
                      <view class="wz-section-body">
                        <view style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
                          <text class="wxxs-tag" :class="baziData.wang_shuai_detail.de_sheng ? 'wx-wang' : 'wx-qiu'">得生{{ baziData.wang_shuai_detail.de_sheng ? '✓' : '✗' }}</text>
                          <text class="wxxs-tag" :class="baziData.wang_shuai_detail.de_zhu ? 'wx-wang' : 'wx-qiu'">得助{{ baziData.wang_shuai_detail.de_zhu ? '✓' : '✗' }}</text>
                          <text class="wxxs-tag" :class="baziData.wang_shuai_detail.de_ling ? 'wx-wang' : 'wx-qiu'">得令{{ baziData.wang_shuai_detail.de_ling ? '✓' : '✗' }}</text>
                          <text class="wxxs-tag" :class="baziData.wang_shuai_detail.de_di ? 'wx-wang' : 'wx-qiu'">得地{{ baziData.wang_shuai_detail.de_di ? '✓' : '✗' }}</text>
                        </view>
                        <view v-for="(v, k) in baziData.wang_shuai_detail.detail" :key="k" style="margin-bottom:3px;">
                          <text style="font-size:0.72rem;color:var(--text-3);">{{ {'di':'得地','ling':'得令','sheng':'得生','zhu':'得助'}[k] || k }}：</text>
                          <text style="font-size:0.72rem;" :style="{color: v.status ? '#4a8c5c' : 'var(--text-3)'}">{{ v.text }}</text>
                        </view>
                        <text style="font-size:0.72rem;color:var(--accent);display:block;margin-top:4px;">综合：{{ baziData.wang_shuai_detail.strength || '' }}（{{ baziData.wang_shuai_detail.score || 0 }}分）</text>
                      </view>
                    </view>

                    <!-- 性格分析 -->
                    <view class="wz-section-card" v-if="baziData.personality" style="margin-top:10px;">
                      <text class="wz-section-title">🎭 性格分析</text>
                      <view class="wz-section-body">
                        <text class="wz-section-text">{{ baziData.personality.summary || '' }}</text>
                        <view class="wz-trait-tags" v-if="baziData.personality.traits && baziData.personality.traits.length">
                          <text class="wz-trait-tag" v-for="(t, ti) in baziData.personality.traits" :key="ti">{{ t }}</text>
                        </view>
                        <view class="wz-personality-grid">
                          <view class="wz-p-item" v-if="baziData.personality.career">
                            <text class="wz-p-label">💼 事业</text>
                            <text class="wz-p-text">{{ baziData.personality.career }}</text>
                          </view>
                          <view class="wz-p-item" v-if="baziData.personality.wealth">
                            <text class="wz-p-label">💰 财运</text>
                            <text class="wz-p-text">{{ baziData.personality.wealth }}</text>
                          </view>
                          <view class="wz-p-item" v-if="baziData.personality.relationship">
                            <text class="wz-p-label">💕 感情</text>
                            <text class="wz-p-text">{{ baziData.personality.relationship }}</text>
                          </view>
                          <view class="wz-p-item" v-if="baziData.personality.advice">
                            <text class="wz-p-label">💡 建议</text>
                            <text class="wz-p-text">{{ baziData.personality.advice }}</text>
                          </view>
                        </view>
                      </view>
                    </view>

                    <!-- 古籍参考 -->
                    <view class="wz-section-card" v-if="baziData.guji_refs && baziData.guji_refs.length" style="margin-top:10px;">
                      <text class="wz-section-title">📚 古籍参考</text>
                      <view class="wz-section-body">
                        <view class="wz-guji-item" v-for="(ref, ri) in baziData.guji_refs" :key="ri">
                          <view class="wz-guji-header">
                            <text class="wz-guji-title">{{ ref.title }}</text>
                            <text class="wz-guji-match">{{ ref.source }}</text>
                          </view>
                          <text class="wz-guji-text">{{ ref.text }}</text>
                        </view>
                      </view>
                    </view>

                  </view>
                </view>
                <view id="baziPanelNotes" class="tab-panel" :class="{ active: activeTab === 'notes' }">
                  <view style="max-width:680px;">
                    <view class="info-card" style="margin-bottom:14px;">
                      <view class="card-title">📝 添加笔记</view>
                      <view class="card-content">
                        <view style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
                          <view v-for="t in noteTags" :key="t.key"
                            class="note-tag-btn" :class="{ active: selectedNoteTag === t.key }"
                            @tap="selectedNoteTag = t.key"
                            :style="selectedNoteTag === t.key ? { background: t.color + '33', borderColor: t.color, color: t.color } : {}">
                            {{ t.icon }} {{ t.label }}
                          </view>
                        </view>
                        <textarea v-model="noteInput" rows="3" placeholder="记录断事心得…"
                          style="width:100%;padding:10px 14px;border-radius:10px;border:1px solid var(--card-border);background:var(--section-alt);color:var(--text-1);font-size:0.84rem;font-family:var(--font-sans);resize:vertical;outline:none;"></textarea>
                        <view style="margin-top:10px;display:flex;justify-content:flex-end;">
                          <view class="btn btn-accent" @tap="addNote" style="padding:8px 20px;border-radius:10px;font-size:0.84rem;">添加笔记</view>
                        </view>
                      </view>
                    </view>
                    <view class="info-card">
                      <view class="card-title">📋 笔记列表{{ notes.length > 0 ? ` (${notes.length}条)` : '' }}</view>
                      <view v-if="notes.length === 0" style="text-align:center;padding:30px 0;color:var(--text-3);font-size:0.84rem;">暂无笔记，添加第一条断事心得吧 ✨</view>
                      <view v-else class="card-content" style="display:flex;flex-direction:column;gap:10px;">
                        <view v-for="note in sortedNotes" :key="note.id" class="note-item">
                          <view class="note-header">
                            <text class="note-tag" :style="{ background: getTagInfo(note.tag).color + '22', color: getTagInfo(note.tag).color }">{{ getTagInfo(note.tag).icon }} {{ getTagInfo(note.tag).label }}</text>
                            <text class="note-time">{{ formatNoteDate(note.created) }}</text>
                          </view>
                          <view class="note-text">{{ note.text }}</view>
                          <view class="note-actions">
                            <view class="note-action-btn" @tap="editNote(note.id)">✏️ 编辑</view>
                            <view class="note-action-btn" @tap="deleteNote(note.id)">🗑 删除</view>
                          </view>
                        </view>
                      </view>
                    </view>
                  </view>
                </view>

                <!-- Tab5: 设置 -->
                <view id="baziPanelSettings" class="tab-panel" :class="{ active: activeTab === 'settings' }">
                  <view style="max-width:680px;">
                    <view class="info-card">
                      <view class="card-title">⚙ 排盘设置</view>
                      <view class="card-content">
                        <view class="mingli-row">
                          <text class="ml-label">夜子时</text>
                          <text class="ml-value">{{ settings.nightZiMode || '夜子时不换日' }}</text>
                        </view>
                        <view class="mingli-row">
                          <text class="ml-label">真太阳时</text>
                          <text class="ml-value">{{ settings.useSolarTime ? '开启' : '关闭' }}</text>
                        </view>
                      </view>
                    </view>
                  </view>
                </view>
              </view>
            </view>
            <!-- 底部声明 -->
            <view class="disclaimer">⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议</view>
          </view>
        </view>
      </view>
    </view>

    <!-- 图片导出用隐藏 canvas -->
    <canvas canvas-id="exportCanvas" id="exportCanvas" style="position:fixed;left:-9999px;top:-9999px;width:750px;height:1200px;"></canvas>

    <!-- 分享面板 -->
    <view class="modal-overlay" id="sharePanelModal">
      <view class="modal-box">
        <view class="modal-title">分享/导出</view>
        <view style="display:flex;flex-direction:column;gap:10px;">
          <view class="btn btn-accent" @tap="shareAsImage">📷 保存为图片</view>
          <view class="btn btn-outline" @tap="shareAsText">📋 复制文本</view>
        </view>
        <view class="modal-btns"><view class="btn btn-outline" @tap="closeSharePanel">关闭</view></view>
      </view>
    </view>


  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
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

const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })
function closeSharePanel() { sharePanelOpen.value = false; try { document.getElementById('sharePanelModal')?.classList.remove('open') } catch(_) {} }

// ═══ 五行颜色映射（问真八字官方配色） ═══
const WX_COLOR_BZ = {
  '金':'#ef9104','木':'#07e930','水':'#2e83f6','火':'#d30505','土':'#8b6d03',
  '庚':'#ef9104','辛':'#d4860a','甲':'#07e930','乙':'#1dcc36',
  '壬':'#2e83f6','癸':'#4a96f0','丙':'#d30505','丁':'#e02a2a',
  '戊':'#8b6d03','己':'#a07d10','申':'#ef9104','酉':'#d4860a',
  '寅':'#07e930','卯':'#1dcc36','子':'#2e83f6','亥':'#4a96f0',
  '巳':'#d30505','午':'#e02a2a','辰':'#8b6d03','丑':'#a07d10','未':'#a07d10','戌':'#8b6d03'
}
try { window.WX_COLOR_BZ = WX_COLOR_BZ } catch(e) {}

const wxColorMap = { '金':'#ef9104','木':'#07e930','水':'#2e83f6','火':'#d30505','土':'#8b6d03' }

const GAN_WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}

const REN_YUAN_SI_LING = {
  '子': '癸', '丑': '己', '寅': '甲', '卯': '乙', '辰': '戊', '巳': '丙',
  '午': '丁', '未': '己', '申': '庚', '酉': '辛', '戌': '戊', '亥': '壬'
}

function fixShiShenName(ss) {
  if (!ss) return ''
  if (ss === '偏官') return '七杀'
  if (ss === '日主') return '比肩'
  return ss
}

function wxSpanBZ(ch) {
  if (!ch) return ''
  const color = WX_COLOR_BZ[ch]
  return color ? `<span style="color:${color}">${ch}</span>` : ch
}

function wxSpanStr(s) {
  if (!s) return ''
  var r = ''
  for (var i = 0; i < s.length; i++) { r += wxSpanBZ(s[i]) }
  return r
}

function abbreviateShiShen(ss) {
  if (!ss) return ''
  const m = { '比肩':'比','劫财':'劫','食神':'食','伤官':'伤','正财':'财','偏财':'才','正官':'官','偏官':'杀','七杀':'杀','正印':'印','偏印':'枭','日主':'日主' }
  return m[ss] || ss.charAt(0)
}

function getShiShenLocal(dayMaster, gan) {
  if (!dayMaster || !gan || dayMaster === gan) return '比肩'
  const SS_TABLE = [
    ['比肩','劫财','食神','伤官','偏财','正财','七杀','正官','偏印','正印'],
    ['劫财','比肩','伤官','食神','正财','偏财','正官','七杀','正印','偏印'],
    ['偏印','正印','比肩','劫财','食神','伤官','偏财','正财','七杀','正官'],
    ['正印','偏印','劫财','比肩','伤官','食神','正财','偏财','正官','七杀'],
    ['七杀','正官','偏印','正印','比肩','劫财','食神','伤官','偏财','正财'],
    ['正官','七杀','正印','偏印','劫财','比肩','伤官','食神','正财','偏财'],
    ['偏财','正财','七杀','正官','偏印','正印','比肩','劫财','食神','伤官'],
    ['正财','偏财','正官','七杀','正印','偏印','劫财','比肩','伤官','食神'],
    ['食神','伤官','偏财','正财','七杀','正官','偏印','正印','比肩','劫财'],
    ['伤官','食神','正财','偏财','正官','七杀','正印','偏印','劫财','比肩'],
  ]
  const TG = '甲乙丙丁戊己庚辛壬癸'
  const row = TG.indexOf(dayMaster)
  const col = TG.indexOf(gan)
  if (row < 0 || col < 0) return ''
  const ss = SS_TABLE[row][col]
  return ss === '偏官' ? '七杀' : ss
}

function computeKongWang(gan, zhi) {
  const TG = '甲乙丙丁戊己庚辛壬癸'
  const DZ = '子丑寅卯辰巳午未申酉戌亥'
  const tgIdx = TG.indexOf(gan)
  const dzIdx = DZ.indexOf(zhi)
  if (tgIdx < 0 || dzIdx < 0) return ''
  const gzNum = ((tgIdx * 6 - dzIdx * 5) % 60 + 60) % 60
  const xunStart = gzNum - (gzNum % 10)
  const kong1 = DZ[(xunStart % 12 + 10) % 12]
  const kong2 = DZ[(xunStart % 12 + 11) % 12]
  return kong1 + kong2
}

function computeShenShaLocal(gan, zhi, dayGan, yearZhi, dayZhi) {
  const result = []
  const TYGR = {'甲':['丑','未'],'乙':['子','申'],'丙':['亥','酉'],'丁':['亥','酉'],'戊':['丑','未'],'己':['子','申'],'庚':['丑','未'],'辛':['午','寅'],'壬':['卯','巳'],'癸':['卯','巳']}
  if (TYGR[dayGan] && TYGR[dayGan].includes(zhi)) result.push('天乙')
  const YIMA = {'申':'寅','子':'寅','辰':'寅','寅':'申','午':'申','戌':'申','巳':'亥','酉':'亥','丑':'亥','亥':'巳','卯':'巳','未':'巳'}
  if (YIMA[yearZhi] === zhi || YIMA[dayZhi] === zhi) result.push('驿马')
  const TH = {'申':'酉','子':'酉','辰':'酉','寅':'卯','午':'卯','戌':'卯','巳':'午','酉':'午','丑':'午','亥':'子','卯':'子','未':'子'}
  if (TH[yearZhi] === zhi || TH[dayZhi] === zhi) result.push('桃花')
  const HUAGAI = {'申':'辰','子':'辰','辰':'辰','寅':'戌','午':'戌','戌':'戌','巳':'丑','酉':'丑','丑':'丑','亥':'未','卯':'未','未':'未'}
  if (HUAGAI[yearZhi] === zhi || HUAGAI[dayZhi] === zhi) result.push('华盖')
  const WENCHANG = {'甲':'巳','乙':'午','丙':'申','丁':'酉','戊':'申','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}
  if (WENCHANG[dayGan] === zhi) result.push('文昌')
  const LU = {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}
  if (LU[dayGan] === zhi) result.push('禄')
  const YR = {'甲':'卯','乙':'辰','丙':'午','丁':'未','戊':'午','己':'未','庚':'酉','辛':'戌','壬':'子','癸':'丑'}
  if (YR[dayGan] === zhi) result.push('羊刃')
  const JIESHA = {'申':'巳','子':'巳','辰':'巳','寅':'亥','午':'亥','戌':'亥','巳':'寅','酉':'寅','丑':'寅','亥':'申','卯':'申','未':'申'}
  if (JIESHA[dayZhi] === zhi || JIESHA[yearZhi] === zhi) result.push('劫煞')
  const WANGSHEN = {'申':'亥','子':'亥','辰':'亥','寅':'巳','午':'巳','戌':'巳','巳':'申','酉':'申','丑':'申','亥':'寅','卯':'寅','未':'寅'}
  if (WANGSHEN[dayZhi] === zhi || WANGSHEN[yearZhi] === zhi) result.push('亡神')
  return result
}

function getQiYunMonth(d) {
  if (d && d.qi_yun_detail) {
    var qd = d.qi_yun_detail
    if (qd.qiyun_month) return qd.qiyun_month
    if (qd.month) return qd.month
    var monthMatch = (qd.text || '').match(/(\d+)月/)
    if (monthMatch) return parseInt(monthMatch[1])
  }
  if (d && d.wzProData && d.wzProData.qi_yun_detail) {
    var qd2 = d.wzProData.qi_yun_detail
    if (qd2.month) return qd2.month
  }
  return null
}

function getQiYunMaxLiuYue(d) {
  var month = getQiYunMonth(d)
  if (!month) return 12
  month = parseInt(month)
  if (!month || month < 1 || month > 12) return 12
  return month
}

function getQiYunYear(d) {
  if (d && d.qi_yun_detail) {
    var qd = d.qi_yun_detail
    if (qd.qiyun_year) return qd.qiyun_year
    if (qd.year) return qd.year
  }
  if (d && d.wzProData && d.wzProData.qi_yun_detail) {
    var qd2 = d.wzProData.qi_yun_detail
    if (qd2.year) return qd2.year
  }
  return null
}

// ═══ 生肖emoji映射 ═══
const SHENGXIAO_EMOJI = { '鼠':'🐭','牛':'🐮','虎':'🐯','兔':'🐰','龙':'🐲','蛇':'🐍','马':'🐴','羊':'🐑','猴':'🐵','鸡':'🐔','狗':'🐶','猪':'🐷' }

// ═══ 笔记标签 ═══
const noteTags = [
  { key: 'career', label: '事业', color: '#2e83f6', icon: '💼' },
  { key: 'wealth', label: '财运', color: '#ef9104', icon: '💰' },
  { key: 'marriage', label: '婚姻', color: '#d30505', icon: '💕' },
  { key: 'health', label: '健康', color: '#07e930', icon: '🏥' },
  { key: 'study', label: '学业', color: '#8A2BE2', icon: '📚' },
  { key: 'other', label: '其他', color: '#888', icon: '📌' },
]

// ═══ 核心状态 ═══
const loading = ref(true)
const errorMsg = ref('')
const baziData = ref(null)
const navInfo = ref('')
const showTMS = ref(false)
const sharePanelOpen = ref(false)
const wzProData = ref(null)
const wzProLoading = ref(false)
const baziSourceParams = ref(null)
const agentHandoffStorageKey = 'xc_agent_handoff_v1'

// Tab
const activeTab = ref(uni.getStorageSync('xc_bazi_activeTab') || 'wzpro')
function switchTab(tab) {
  activeTab.value = tab
  uni.setStorageSync('xc_bazi_activeTab', tab)
  rememberBaziResultRoute()
  if (tab === 'wzpro') {
    loadWzProData()
  }
  // DOM直操作：绕过Vue 3.4.21 render effect bug
  var tabs = ['info','basic','wzpro','notes','settings']
  var btnIds = ['baziTabInfo','baziTabBasic','baziTabWzpro','baziTabNotes','baziTabSettings']
  var panelIds = ['baziPanelInfo','baziPanelBasic','baziPanelWzpro','baziPanelNotes','baziPanelSettings']
  for (var i = 0; i < tabs.length; i++) {
    var btn = document.getElementById(btnIds[i])
    if (btn) { tab === tabs[i] ? btn.classList.add('active') : btn.classList.remove('active') }
    var panel = document.getElementById(panelIds[i])
    if (panel) { panel.style.display = tab === tabs[i] ? 'block' : 'none' }
  }
}

function rememberBaziResultRoute() {
  // 只保存在当前 H5 会话的 window 上，刷新页面后自然失效。
  // 用于从其他术数页点回“八字排盘”时恢复刚才看的结果页。
  // #ifdef H5
  try {
    var hash = window.location.hash || ''
    var idx = hash.indexOf('/pages/bazi-result/index')
    if (idx >= 0) {
      window.__xc_lastBaziResultRoute = hash.substring(idx)
    }
  } catch(_) {}
  // #endif
}

function readBaziParamsFromStorage() {
  // #ifdef H5
  var keys = ['xc_bazi_params', 'xc_bazi_last_params']
  for (var i = 0; i < keys.length; i++) {
    try {
      var stored = keys[i] === 'xc_bazi_params'
        ? sessionStorage.getItem(keys[i])
        : localStorage.getItem(keys[i])
      if (stored) {
        var parsed = JSON.parse(stored)
        if (parsed && (parsed.birthTime || parsed.birthDate || parsed.siziPillars || parsed.id)) {
          if (keys[i] !== 'xc_bazi_params') {
            try { sessionStorage.setItem('xc_bazi_params', stored) } catch (_) {}
          }
          return parsed
        }
      }
    } catch (_) {}
  }
  // #endif
  return null
}

function rememberLastBaziParams(params) {
  // #ifdef H5
  try {
    if (!params || params._replay) return
    var raw = JSON.stringify(params)
    sessionStorage.setItem('xc_bazi_params', raw)
    localStorage.setItem('xc_bazi_last_params', raw)
  } catch (_) {}
  // #endif
}

function sendBaziToAgent() {
  if (!baziData.value) return uni.showToast({ title: '请先完成排盘', icon: 'none' })
  const params = baziSourceParams.value || readBaziParamsFromStorage() || {}
  const handoff = {
    source: 'bazi_free',
    tool_models: ['bazi'],
    question: '请结合这个八字命盘，围绕我的问题进行解读。',
    paipan: {
      bazi: {
        form: {
          name: params.name || baziData.value.name || '',
          gender: params.gender || baziData.value.gender || '',
          calType: params.calType || '公历',
          birthTime: params.birthTime || '',
          birthDate: params.birthDate || '',
          birthHour: params.birthHour || '',
          birthMinute: params.birthMinute || '',
          birthAddr: params.birthAddr || '',
          birthLng: params.birthLng || 0,
          birthLat: params.birthLat || 0,
          nightZiMode: params.nightZiMode || settings.nightZiMode,
          useSolarTime: params.useSolarTime !== false,
          isLeapMonth: !!params.isLeapMonth,
        },
        pan: baziData.value,
      }
    }
  }
  try {
    uni.setStorageSync(agentHandoffStorageKey, JSON.stringify(handoff))
  } catch (_) {}
  // #ifdef H5
  try {
    window.location.hash = '#/?app=1'
    return
  } catch (_) {}
  // #endif
  uni.reLaunch({ url: '/pages/index/index?app=1' })
}

async function loadWzProData() {
  if (wzProData.value) return
  var d = baziData.value
  if (!d) return

  wzProLoading.value = true
  try {
    var y = '', m = '', dd = '', h = '0', mi = 0, s = 1

    if (d.birth_params) {
      y = d.birth_params.y || ''
      m = d.birth_params.m || ''
      dd = d.birth_params.d || ''
      h = d.birth_params.h || '0'
      mi = d.birth_params.mi || 0
      s = d.birth_params.s || 1
    } else if (d.birth_solar) {
      var parts = d.birth_solar.match(/(\d{4})-(\d{2})-(\d{2})\s*(\d{2}):(\d{2})/)
      if (parts) {
        y = parts[1]; m = parseInt(parts[2]); dd = parseInt(parts[3])
        h = parseInt(parts[4]); mi = parseInt(parts[5])
      }
      s = d.gender === '女' ? 2 : 1
    }

    if (!y || !m || !dd) {
      wzProLoading.value = false
      return
    }

    var url = '/api/bazi/wz-pro?y=' + y + '&m=' + m + '&d=' + dd + '&h=' + h + '&mi=' + mi + '&s=' + s
    var r = await uni.request({ url: url, method: 'GET' })
    if (r.data && r.data.success) {
      wzProData.value = r.data
    }
  } catch (e) {
    console.log('[专业排盘] 加载wz-pro数据失败', e)
  } finally {
    wzProLoading.value = false
  }
}

// 笔记
const selectedNoteTag = ref('career')
const noteInput = ref('')
const notes = ref([])

// 设置
const settings = reactive({ nightZiMode: '夜子时不换日', useSolarTime: true })

// ═══ 计算属性 ═══
const PILLAR_ORDER = ['year', 'month', 'day', 'hour']

const fourPillars = computed(() => {
  const fp = (baziData.value && baziData.value.four_pillars) || {}
  const ordered = {}
  PILLAR_ORDER.forEach(k => { if (fp[k]) ordered[k] = fp[k] })
  return ordered
})

const pillarLabels = { year: '年柱', month: '月柱', day: '日柱', hour: '时柱' }

const cangGan = computed(() => baziData.value?.cang_gan || {})
// API返回{year_gan, month_gan, day_gan, hour_gan}，需要映射为{year, month, day, hour}
const shiShen = computed(() => {
  const ss = baziData.value?.shi_shen || {}
  const fp = baziData.value?.four_pillars || {}
  const dm = baziData.value?.day_master || ''
  const calc = (key) => {
    if (key === 'day') return ss.day_gan || '日主'
    const gan = fp[key]?.gan
    return dm && gan ? getShiShenLocal(dm, gan) : (ss[`${key}_gan`] || '')
  }
  return { year: calc('year'), month: calc('month'), day: calc('day'), hour: calc('hour') }
})
const naYin = computed(() => {
  const fp = baziData.value?.four_pillars || {}
  return {
    year: fp.year?.nayin || '',
    month: fp.month?.nayin || '',
    day: fp.day?.nayin || '',
    hour: fp.hour?.nayin || '',
  }
})
const shenShaPerPillar = computed(() => baziData.value?.shen_sha_per_pillar || {})
const cangGanShiShen = computed(() => baziData.value?.cang_gan_shi_shen || {})
const xingYun = computed(() => baziData.value?.xing_yun || {})
const ziZuo = computed(() => baziData.value?.zi_zuo || {})
const kongWangPerPillar = computed(() => baziData.value?.kong_wang_per_pillar || {})
const cangGanWithWx = computed(() => baziData.value?.cang_gan_with_wx || {})
const dayMasterLabel = computed(() => baziData.value?.day_master_label || (baziData.value?.gender === '女' ? '元女' : '元男'))
const wangShuai = computed(() => {
  const ws = baziData.value.ri_zhu_wangshuai || baziData.value.wang_shuai || ''
  return ws
})
const chengGu = computed(() => baziData.value?.cheng_gu || null)

const strengthColorMap = { '身旺': '#4a8c5c', '偏旺': '#3CB371', '中和': '#ef9104', '偏弱': '#CD853F', '身弱': '#d30505' }

const wangShuaiDims = computed(() => {
  const d = baziData.value?.wang_shuai_detail
  if (!d || !d.detail) return []
  const dims = [
    { key: 'ling', label: '得令/失令', icon: '👑', keyName: '令' },
    { key: 'di', label: '得地/失地', icon: '🏰', keyName: '地' },
    { key: 'sheng', label: '得生/失生', icon: '💧', keyName: '生' },
    { key: 'zhu', label: '得助/失助', icon: '🤝', keyName: '助' },
  ]
  return dims.map(dim => {
    const dd = d.detail[dim.key] || {}
    return { ...dim, status: dd.status, text: dd.text || '' }
  })
})

// wu_xing: API返回{金:0, 木:2, lack:["金"],...}扁平数字，转换为{count, wang}对象
const wuXingStats = computed(() => {
  const wx = baziData.value?.wu_xing || {}
  const names = ['金', '木', '水', '火', '土']
  const result = {}
  names.forEach(n => {
    const val = wx[n]
    result[n] = typeof val === 'number' ? { count: val, wang: '' } : (val || { count: 0, wang: '' })
  })
  return result
})

const infoItems = computed(() => {
  if (!baziData.value) return []
  const d = baziData.value
  const fp = d.four_pillars || {}
  const items = [
    { label: '姓名', value: d.name || '未命名' },
    { label: '性别', value: d.gender || '' },
    { label: '出生时间', value: d.birth_input || d.birth_solar || '', fullWidth: true },
    { label: '四柱', value: `${fp.year?.gan_zhi || ''} ${fp.month?.gan_zhi || ''} ${fp.day?.gan_zhi || ''} ${fp.hour?.gan_zhi || ''}`, fullWidth: true },
    { label: '生肖', value: (SHENGXIAO_EMOJI[d.sheng_xiao] || '') + ' ' + (d.sheng_xiao || '') },
    { label: '日主', value: d.day_master_label || (d.gender === '女' ? '元女' : '元男') },
    { label: '纳音', value: `${fp.year?.nayin || ''}` },
    { label: '旺衰', value: d.wang_shuai || '' },
    { label: '星座', value: d.xing_zuo || '' },
    { label: '起运年龄', value: d.qi_yun_age ? `${d.qi_yun_age}岁` : '' },
    { label: '大运方向', value: d.da_yun_direction || '' },
  ]
  return items.filter(i => i.value)
})

// 专业排盘HTML（由后端渲染）— 已弃用，改用前端渲染
// const wzproHtml = computed(() => baziData.value?.wzpro_html || baziData.value?.pro_html || '')

// ═══ 专业排盘数据 ═══
const selDaYunIdx = ref(-1)
const selLiuNianIdx = ref(-1)
const colOrder = ref((uni && uni.getStorageSync && uni.getStorageSync('xc_bazi_colOrder')) || 'dy-first')
const activeYunType = ref('dayun')
const yunRefreshKey = ref(0)
const savedSel = { dayun: { dy: -1, ln: -1, ly: -1, lmlist: [] }, xiaoyun: { dy: -1, ln: -1, ly: -1, lmlist: [] } }

const currentYunPhase = computed(() => {
  if (activeYunType.value === 'xiaoyun') return 'xiaoyun'
  return 'dayun'
})
const currentYunPhaseLabel = computed(() => {
  return currentYunPhase.value === 'xiaoyun' ? '小运' : '大运'
})

function switchYunType(type) {
  switchYunPhase(type)
}

const shengxiaoEmoji = computed(() => {
  const sx = baziData.value.sheng_xiao || ''
  const map = { '鼠': '🐭', '牛': '🐮', '虎': '🐯', '兔': '🐰', '龙': '🐲', '蛇': '🐍', '马': '🐴', '羊': '🐑', '猴': '🐵', '鸡': '🐔', '狗': '🐶', '猪': '🐷' }
  return map[sx] || ''
})

const tmsItems = computed(() => {
  const d = baziData.value
  if (!d) return []
  const items = []
  const tms = d.tai_ming_shen || {}
  if (tms.tai_yuan) items.push({ key: 'ty', label: '胎元', html: wxSpanBZ(tms.tai_yuan.gan || '') + wxSpanBZ(tms.tai_yuan.zhi || ''), nayin: tms.tai_yuan.nayin || '' })
  if (tms.ming_gong) items.push({ key: 'mg', label: '命宫', html: wxSpanBZ(tms.ming_gong.gan || '') + wxSpanBZ(tms.ming_gong.zhi || ''), nayin: tms.ming_gong.nayin || '' })
  if (tms.shen_gong) items.push({ key: 'sg', label: '身宫', html: wxSpanBZ(tms.shen_gong.gan || '') + wxSpanBZ(tms.shen_gong.zhi || ''), nayin: tms.shen_gong.nayin || '' })
  return items
})

const wxSummaryItems = computed(() => {
  const wx = baziData.value.wu_xing || {}
  const wxMap = { '金': { color: '#ef9104', cls: 'metal' }, '木': { color: '#07e930', cls: 'wood' }, '水': { color: '#2e83f6', cls: 'water' }, '火': { color: '#d30505', cls: 'fire' }, '土': { color: '#8b6d03', cls: 'earth' } }
  return Object.keys(wxMap).map(name => ({
    name,
    count: wx[name] || 0,
    color: wxMap[name].color,
    cls: wxMap[name].cls
  }))
})

const colLabels = computed(() => {
  const szLabels = ['年柱', '月柱', '日柱', '时柱']
  const tmsLabels = showTMS.value ? ['胎元', '命宫', '身宫'] : []
  const dyLabel = currentYunPhaseLabel.value
  const labels = [dyLabel, '流年', '流月', ...szLabels, ...tmsLabels]
  if (colOrder.value === 'sz-first') {
    return [...szLabels, ...tmsLabels, dyLabel, '流年', '流月']
  }
  return labels
})

const colData = computed(() => {
  const d = baziData.value
  if (!d || !d.four_pillars) return []
  const fp = d.four_pillars
  const cg = d.cang_gan || {}
  const cgSs = d.cang_gan_shi_shen || {}
  const cgWx = d.cang_gan_with_wx || {}
  const ss = d.shi_shen || {}
  const ssp = d.shen_sha_per_pillar || {}
  const ds = d.di_shi || {}
  const xy = d.xing_yun || {}
  const zz = d.zi_zuo || {}
  const kw = d.kong_wang_per_pillar || {}

  function pillarCol(key) {
    const p = fp[key] || {}
    const cgList = (cg[key] || []).map(function(g, i) {
      return { gz: g, ss: (cgSs[key] || [])[i] || '', wx: (cgWx[key] || [])[i] || '' }
    })
    return {
      tg: p.gan || '',
      dz: p.zhi || '',
      zhuxing: fixShiShenName(ss[key + '_gan']),
      canggan: cgList,
      nayin: p.nayin || '',
      kongwang: kw[key] || '',
      shensha: ssp[key] || [],
      xingyun: xy[key] || '',
      zizuo: zz[key] || '',
      dishi: ds[key] || ''
    }
  }

  const szData = [pillarCol('year'), pillarCol('month'), pillarCol('day'), pillarCol('hour')]

  const dayMaster = d.four_pillars?.day?.gan || ''

  const dyIdx = selDaYunIdx.value
  let dyData = { tg: '', dz: '', zhuxing: '', canggan: [], nayin: '', kongwang: '', shensha: [], xingyun: '', zizuo: '', dishi: '' }
  if (currentYunPhase.value === 'dayun') {
    const selDy = activeYunList.value.find(i => i._active)
    if (selDy) {
      const cgList = (selDy.cang_gan || []).map(function(g, i) {
        return { gz: g, ss: (selDy.cang_gan_shi_shen || [])[i] || '' }
      })
      const dySs = selDy.shi_shen_gan || (selDy.gan ? getShiShenLocal(dayMaster, selDy.gan) : '')
      dyData = { tg: selDy.gan || '', dz: selDy.zhi || '', zhuxing: fixShiShenName(dySs), canggan: cgList, nayin: selDy.nayin || '', kongwang: selDy.kong_wang || '', shensha: selDy.shen_sha || [], xingyun: selDy.xing_yun || selDy.chang_sheng || '', zizuo: selDy.zi_zuo || '', dishi: '' }
    }
  } else {
    const selXy = activeYunList.value.find(i => i._active)
    if (selXy) {
      const xyGan = selXy.gan || ''
      const xyZhi = selXy.zhi || ''
      const xySs = xyGan ? getShiShenLocal(dayMaster, xyGan) : ''
      const CANG_GAN_LOCAL = {'子':['癸'],'丑':['己','癸','辛'],'寅':['甲','丙','戊'],'卯':['乙'],'辰':['戊','乙','癸'],'巳':['丙','庚','戊'],'午':['丁','己'],'未':['己','丁','乙'],'申':['庚','壬','戊'],'酉':['辛'],'戌':['戊','辛','丁'],'亥':['壬','甲']}
      const cgList = (CANG_GAN_LOCAL[xyZhi] || []).map(function(g) { return { gz: g, ss: fixShiShenName(getShiShenLocal(dayMaster, g)) } })
      const NAYIN_TABLE = {
        '甲子':'海中金','乙丑':'海中金','丙寅':'炉中火','丁卯':'炉中火','戊辰':'大林木','己巳':'大林木',
        '庚午':'路旁土','辛未':'路旁土','壬申':'剑锋金','癸酉':'剑锋金','甲戌':'山头火','乙亥':'山头火',
        '丙子':'涧下水','丁丑':'涧下水','戊寅':'城头土','己卯':'城头土','庚辰':'白蜡金','辛巳':'白蜡金',
        '壬午':'杨柳木','癸未':'杨柳木','甲申':'泉中水','乙酉':'泉中水','丙戌':'屋上土','丁亥':'屋上土',
        '戊子':'霹雳火','己丑':'霹雳火','庚寅':'松柏木','辛卯':'松柏木','壬辰':'长流水','癸巳':'长流水',
        '甲午':'砂石金','乙未':'砂石金','丙申':'山下火','丁酉':'山下火','戊戌':'平地木','己亥':'平地木',
        '庚子':'壁上土','辛丑':'壁上土','壬寅':'金箔金','癸卯':'金箔金','甲辰':'覆灯火','乙巳':'覆灯火',
        '丙午':'天河水','丁未':'天河水','戊申':'大驿土','己酉':'大驿土','庚戌':'钗钏金','辛亥':'钗钏金',
        '壬子':'桑柘木','癸丑':'桑柘木','甲寅':'大溪水','乙卯':'大溪水','丙辰':'沙中土','丁巳':'沙中土',
        '戊午':'天上火','己未':'天上火','庚申':'石榴木','辛酉':'石榴木','壬戌':'大海水','癸亥':'大海水',
      }
      const CHANG_SHENG_TABLE = {
        '甲': {'寅':'长生','卯':'沐浴','辰':'冠带','巳':'临官','午':'帝旺','未':'衰','申':'病','酉':'死','戌':'墓','亥':'绝','子':'胎','丑':'养'},
        '乙': {'亥':'长生','子':'沐浴','丑':'冠带','寅':'临官','卯':'帝旺','辰':'衰','巳':'病','午':'死','未':'墓','申':'绝','酉':'胎','戌':'养'},
        '丙': {'寅':'长生','卯':'沐浴','辰':'冠带','巳':'临官','午':'帝旺','未':'衰','申':'病','酉':'死','戌':'墓','亥':'绝','子':'胎','丑':'养'},
        '丁': {'酉':'长生','申':'沐浴','未':'冠带','午':'临官','巳':'帝旺','辰':'衰','卯':'病','寅':'死','丑':'墓','子':'绝','亥':'胎','戌':'养'},
        '戊': {'寅':'长生','卯':'沐浴','辰':'冠带','巳':'临官','午':'帝旺','未':'衰','申':'病','酉':'死','戌':'墓','亥':'绝','子':'胎','丑':'养'},
        '己': {'酉':'长生','申':'沐浴','未':'冠带','午':'临官','巳':'帝旺','辰':'衰','卯':'病','寅':'死','丑':'墓','子':'绝','亥':'胎','戌':'养'},
        '庚': {'巳':'长生','午':'沐浴','未':'冠带','申':'临官','酉':'帝旺','戌':'衰','亥':'病','子':'死','丑':'墓','寅':'绝','卯':'胎','辰':'养'},
        '辛': {'子':'长生','亥':'沐浴','戌':'冠带','酉':'临官','申':'帝旺','未':'衰','午':'病','巳':'死','辰':'墓','卯':'绝','寅':'胎','丑':'养'},
        '壬': {'申':'长生','酉':'沐浴','戌':'冠带','亥':'临官','子':'帝旺','丑':'衰','寅':'病','卯':'死','辰':'墓','巳':'绝','午':'胎','未':'养'},
        '癸': {'卯':'长生','寅':'沐浴','丑':'冠带','子':'临官','亥':'帝旺','戌':'衰','酉':'病','申':'死','未':'墓','午':'绝','巳':'胎','辰':'养'},
      }
      const yearZhi = d.four_pillars?.year?.zhi || ''
      const dayZhi = d.four_pillars?.day?.zhi || ''
      const ganZhi = xyGan + xyZhi
      const nayin = NAYIN_TABLE[ganZhi] || ''
      const xingYun = (CHANG_SHENG_TABLE[xyGan] && CHANG_SHENG_TABLE[xyGan][dayZhi]) || ''
      const ziZuo = (CHANG_SHENG_TABLE[xyGan] && CHANG_SHENG_TABLE[xyGan][xyZhi]) || ''
      const kongWang = computeKongWang(xyGan, xyZhi)
      const shenSha = computeShenShaLocal(xyGan, xyZhi, dayMaster, yearZhi, dayZhi)
      dyData = { tg: xyGan, dz: xyZhi, zhuxing: fixShiShenName(xySs), canggan: cgList, nayin, kongwang: kongWang, shensha: shenSha, xingyun: xingYun, zizuo: ziZuo, dishi: '' }
    }
  }

  const lnIdx = selLiuNianIdx.value
  let lnData = { tg: '', dz: '', zhuxing: '', canggan: [], nayin: '', kongwang: '', shensha: [], xingyun: '', zizuo: '', dishi: '' }
  const fLnList = filteredLiuNian.value
  if (lnIdx >= 0 && lnIdx < fLnList.length) {
    const ln = fLnList[lnIdx]
    const cgList = (ln.cang_gan || []).map(function(g, i) {
      return { gz: g, ss: (ln.cang_gan_shi_shen || [])[i] || '' }
    })
    const lnSs = ln.shi_shen_gan || (ln.gan ? getShiShenLocal(dayMaster, ln.gan) : '')
    lnData = { tg: ln.gan || '', dz: ln.zhi || '', zhuxing: fixShiShenName(lnSs), canggan: cgList, nayin: ln.nayin || '', kongwang: ln.kong_wang || '', shensha: ln.shen_sha || [], xingyun: ln.chang_sheng || ln.xing_yun || '', zizuo: ln.zi_zuo || '', dishi: '' }
  }

  const lmIdx = selLiuYueIdx.value
  let lmData = { tg: '', dz: '', zhuxing: '', canggan: [], nayin: '', kongwang: '', shensha: [], xingyun: '', zizuo: '', dishi: '' }
  const lmList = proLiuYue.value || []
  if (lmIdx >= 0 && lmIdx < lmList.length) {
    const lm = lmList[lmIdx]
    const cgList = (lm.cang_gan || []).map(function(g, i) {
      return { gz: g, ss: (lm.cang_gan_shi_shen || [])[i] || '' }
    })
    const lmSs = lm.tgSs || (lm.gan ? getShiShenLocal(dayMaster, lm.gan) : '')
    lmData = { tg: lm.gan || '', dz: lm.zhi || '', zhuxing: fixShiShenName(lmSs), canggan: cgList, nayin: lm.nayin || '', kongwang: lm.kong_wang || '', shensha: lm.shen_sha || [], xingyun: lm.chang_sheng || '', zizuo: lm.zi_zuo || '', dishi: '' }
  }

  const tmsCols = []
  if (showTMS.value) {
    const tms = d.tai_ming_shen || {}
    const wzTms = wzProData.value || {}
    const tmsDefs = [
      { key: 'tai_yuan', label: '胎元', wzKey: 'taiyuan' },
      { key: 'ming_gong', label: '命宫', wzKey: 'minggong' },
      { key: 'shen_gong', label: '身宫', wzKey: 'shenggong' },
    ]
    tmsDefs.forEach(function(def) {
      const tmsData = tms[def.key] || {}
      const wzGz = wzTms[def.wzKey] || ''
      let tg = tmsData.gan || (wzGz ? wzGz[0] : '')
      let dz = tmsData.zhi || (wzGz && wzGz.length > 1 ? wzGz[1] : '')
      const dayMaster = d.four_pillars.day.gan || ''
      const CANG_GAN_LOCAL = {'子':['癸'],'丑':['己','癸','辛'],'寅':['甲','丙','戊'],'卯':['乙'],'辰':['戊','乙','癸'],'巳':['丙','庚','戊'],'午':['丁','己'],'未':['己','丁','乙'],'申':['庚','壬','戊'],'酉':['辛'],'戌':['戊','辛','丁'],'亥':['壬','甲']}
      const cgList = (CANG_GAN_LOCAL[dz] || []).map(function(g) { return { gz: g, ss: getShiShenLocal(dayMaster, g) } })
      let nayin = tmsData.nayin || ''
      tmsCols.push({
        tg: tg, dz: dz, zhuxing: '', canggan: cgList, nayin: nayin,
        kongwang: '', shensha: [], xingyun: '', zizuo: '', dishi: ''
      })
    })
  }

  const cols = [dyData, lnData, lmData, ...szData, ...tmsCols]
  if (colOrder.value === 'sz-first') {
    return [...szData, ...tmsCols, dyData, lnData, lmData]
  }
  return cols
})

const proSepIdx = computed(() => {
  const d = baziData.value
  if (!d) return -1
  const tmsCount = showTMS.value ? 3 : 0
  if (colOrder.value === 'sz-first') {
    return 4 + tmsCount
  }
  return 3
})

const activeYunList = computed(() => {
  const d = baziData.value
  if (!d) return []
  const phase = currentYunPhase.value
  let list = []
  if (phase === 'xiaoyun') {
    const qiAge = d.qi_yun_age || 7
    const xyList = d.xiao_yun || []
    const birthYear = d.four_pillars?.year?.year || parseInt((d.birth_solar || d.birth_input || '2000').substring(0, 4)) || 2000
    const dayMaster = d.four_pillars?.day?.gan || ''
    list = xyList.filter(xy => xy.age <= qiAge + 1).map((item, idx) => {
      const gan = item.gan || ''
      const ssFull = gan ? getShiShenLocal(dayMaster, gan) : ''
      return {
        ...item,
        _realIdx: idx,
        _active: idx === selDaYunIdx.value,
        start_year: birthYear + (item.age || idx + 1) - 1,
        end_year: birthYear + (item.age || idx + 1) - 1,
        start_age: item.age || idx + 1,
        end_age: item.age || idx + 1,
        ss_full: fixShiShenName(ssFull),
      }
    })
  } else {
    const dayMaster = d.four_pillars?.day?.gan || ''
    list = (d.da_yun || []).filter(item => item.gan || item.zhi).slice(0, 10).map((item, idx) => {
      const gan = item.gan || ''
      const ssFull = gan ? getShiShenLocal(dayMaster, gan) : ''
      return {
        ...item,
        _realIdx: idx,
        _active: idx === selDaYunIdx.value,
        ss_full: fixShiShenName(ssFull),
      }
    })
  }
  return list
})

const filteredLiuNian = computed(() => {
  const d = baziData.value
  if (!d) return []
  const lnList = d.liu_nian || []
  let filtered = lnList
  const phase = currentYunPhase.value
  if (phase === 'xiaoyun') {
    const birthYear = d.four_pillars?.year?.year || parseInt((d.birth_solar || d.birth_input || '2000').substring(0, 4)) || 2000
    const qiAge = d.qi_yun_age || 7
    const xyList = d.xiao_yun || []
    const preQiXy = xyList.filter(xy => xy.age <= qiAge + 1)
    if (preQiXy.length > 0) {
      const firstYear = birthYear
      const lastYear = birthYear + preQiXy[preQiXy.length - 1].age - 1
      filtered = lnList.filter(l => {
        const ly = typeof l.year === 'string' ? parseInt(l.year) : l.year
        return ly >= firstYear && ly <= lastYear
      })
    }
  } else {
    const selItem = activeYunList.value.find(i => i._active)
    if (selItem) {
      const startYear = selItem.start_year || selItem.year
      const endYear = selItem.end_year || (startYear ? startYear + 9 : null)
      if (startYear && endYear) {
        filtered = lnList.filter(l => {
          const ly = typeof l.year === 'string' ? parseInt(l.year) : l.year
          return ly >= startYear && ly <= endYear
        })
      }
    }
  }
  return filtered.map((item, idx) => {
    const dayMaster = d.four_pillars?.day?.gan || ''
    const gan = item.gan || ''
    const ssFull = gan ? getShiShenLocal(dayMaster, gan) : ''
    return { ...item, _realIdx: idx, _active: idx === selLiuNianIdx.value, ss_full: fixShiShenName(ssFull) }
  })
})

const proPanRows = [
  { label: '主星', key: 'zhuxing', cls: '' },
  { label: '天干', key: 'tg', cls: 'wz-tg-row' },
  { label: '地支', key: 'dz', cls: 'wz-dz-row' },
  { label: '藏干', key: 'cg', cls: 'wz-cg-row' },
  { label: '星运', key: 'xy', cls: '' },
  { label: '自坐', key: 'zz', cls: '' },
  { label: '空亡', key: 'kw', cls: '' },
  { label: '纳音', key: 'ny', cls: '' },
]

const proDaYun = computed(() => {
  const dayMaster = baziData.value?.four_pillars?.day?.gan || ''
  if (wzProData.value && wzProData.value.dayun_list) {
    return wzProData.value.dayun_list.map((dy, i) => {
      const gan = dy.tg || dy.gan || ''
      const ssFull = gan ? getShiShenLocal(dayMaster, gan) : ''
      return {
        ...dy,
        gan,
        zhi: dy.dz || dy.zhi || '',
        gan_shishen_abbrev: dy.tgSs || dy.gan_shishen_abbrev || '',
        ss_full: fixShiShenName(ssFull),
        zhi_shishen_abbrev: dy.dzSs || dy.zhi_shishen_abbrev || '',
        _active: i === selDaYunIdx.value,
      }
    })
  }
  const d = baziData.value
  if (!d) return []
  return (d.da_yun || []).map((dy, i) => {
    const gan = dy.gan || ''
    const ssFull = gan ? getShiShenLocal(dayMaster, gan) : ''
    return {
      ...dy,
      ss_full: fixShiShenName(ssFull),
      _active: i === selDaYunIdx.value,
    }
  })
})

const proDaYunLabel = computed(() => {
  const d = baziData.value
  if (!d) return '大运'
  const dyList = d.da_yun || []
  const selDy = dyList[selDaYunIdx.value] || {}
  return selDy?.is_pre_qiyun ? '小运' : '大运'
})

const proLiuNian = computed(() => {
  const dayMaster = baziData.value?.four_pillars?.day?.gan || ''
  if (wzProData.value && wzProData.value.liunian_list) {
    return wzProData.value.liunian_list.map((ln, i) => {
      const gan = ln.tg || ln.gan || ''
      const ssFull = gan ? getShiShenLocal(dayMaster, gan) : ''
      return {
        ...ln,
        gan,
        zhi: ln.dz || ln.zhi || '',
        gan_shishen_abbrev: ln.tgSs || ln.gan_shishen_abbrev || '',
        ss_full: fixShiShenName(ssFull),
        zhi_shishen_abbrev: ln.dzSs || ln.zhi_shishen_abbrev || '',
        _active: i === selLiuNianIdx.value,
      }
    })
  }
  const d = baziData.value
  if (!d) return []
  return (d.liu_nian || []).map((ln, i) => {
    const gan = ln.gan_zhi?.[0] || ln.gan || ''
    const ssFull = gan ? getShiShenLocal(dayMaster, gan) : ''
    return {
      ...ln,
      gan,
      zhi: ln.gan_zhi?.[1] || ln.zhi || '',
      ss_full: fixShiShenName(ssFull),
      _active: i === selLiuNianIdx.value,
    }
  })
})

const proXiaoYun = computed(() => {
  if (wzProData.value && wzProData.value.xiaoyun_list) {
    return wzProData.value.xiaoyun_list.map((xy, i) => ({
      ...xy,
      gan: xy.tg || xy.gan || '',
      zhi: xy.dz || xy.zhi || '',
      _active: i === selLiuNianIdx.value,
    }))
  }
  const d = baziData.value
  if (!d) return []
  return (d.xiao_yun || []).map((xy, i) => ({
    ...xy,
    _active: i === selLiuNianIdx.value,
  }))
})

const proLiuYue = ref([])

const wuXingBar = computed(() => {
  const wx = baziData.value?.wu_xing || {}
  const wxw = baziData.value?.wang_xiang_xiu || []
  const names = ['金', '木', '水', '火', '土']
  return names.map((n, i) => ({
    name: n,
    count: typeof wx[n] === 'number' ? wx[n] : (wx[n]?.count || 0),
    wang: wxw[i] || wx[n]?.wang || '',
  }))
})

const proWuxingWangdu = computed(() => {
  if (wzProData.value && wzProData.value.wuxing_wangdu) {
    var wd = wzProData.value.wuxing_wangdu
    return [
      { name: '水', wang: wd.water || '' },
      { name: '木', wang: wd.wood || '' },
      { name: '金', wang: wd.gold || '' },
      { name: '土', wang: wd.soil || '' },
      { name: '火', wang: wd.fire || '' },
    ]
  }
  return null
})

const proGuanxi = computed(() => {
  if (wzProData.value && (wzProData.value.tg_guanxi || wzProData.value.dz_guanxi)) {
    return {
      tg: wzProData.value.tg_guanxi || '',
      dz: wzProData.value.dz_guanxi || '',
    }
  }
  const rel = baziData.value?.ganzhi_relations
  if (rel) {
    const tgParts = []
    const dzParts = []
    if (rel.gan_he && rel.gan_he.length) tgParts.push(...rel.gan_he.map(i => i.desc || '').filter(Boolean))
    if (rel.gan_chong && rel.gan_chong.length) tgParts.push(...rel.gan_chong.map(i => i.desc || '').filter(Boolean))
    if (rel.zhi_liu_he && rel.zhi_liu_he.length) dzParts.push(...rel.zhi_liu_he.map(i => i.desc || '').filter(Boolean))
    if (rel.zhi_san_he && rel.zhi_san_he.length) dzParts.push(...rel.zhi_san_he.map(i => i.desc || '').filter(Boolean))
    if (rel.zhi_liu_chong && rel.zhi_liu_chong.length) dzParts.push(...rel.zhi_liu_chong.map(i => i.desc || '').filter(Boolean))
    if (rel.zhi_liu_hai && rel.zhi_liu_hai.length) dzParts.push(...rel.zhi_liu_hai.map(i => i.desc || '').filter(Boolean))
    if (rel.zhi_san_xing && rel.zhi_san_xing.length) dzParts.push(...rel.zhi_san_xing.map(i => i.desc || '').filter(Boolean))
    if (rel.zhi_ban_he && rel.zhi_ban_he.length) dzParts.push(...rel.zhi_ban_he.map(i => i.desc || '').filter(Boolean))
    if (rel.zhi_san_hui && rel.zhi_san_hui.length) dzParts.push(...rel.zhi_san_hui.map(i => i.desc || '').filter(Boolean))
    if (rel.zhi_liu_po && rel.zhi_liu_po.length) dzParts.push(...rel.zhi_liu_po.map(i => i.desc || '').filter(Boolean))
    if (rel.zhi_an_he && rel.zhi_an_he.length) dzParts.push(...rel.zhi_an_he.map(i => i.desc || '').filter(Boolean))
    const tg = tgParts.join('、')
    const dz = dzParts.join('、')
    if (tg || dz) return { tg, dz }
  }
  return null
})

const allGuanxiTags = computed(() => {
  var rel = baziData.value?.ganzhi_relations
  if (!rel) return []
  var tags = []
  var tagDefs = [
    { key: 'gan_he', type: '合', color: '#07e930', level: '干' },
    { key: 'gan_chong', type: '冲', color: '#d30505', level: '干' },
    { key: 'zhi_liu_he', type: '合', color: '#07e930', level: '支' },
    { key: 'zhi_san_he', type: '三合', color: '#2e83f6', level: '支' },
    { key: 'zhi_ban_he', type: '半合', color: '#5bc0de', level: '支' },
    { key: 'zhi_an_he', type: '暗合', color: '#8e6fbf', level: '支' },
    { key: 'zhi_san_hui', type: '三会', color: '#e67e22', level: '支' },
    { key: 'zhi_liu_chong', type: '冲', color: '#d30505', level: '支' },
    { key: 'zhi_liu_hai', type: '害', color: '#ef9104', level: '支' },
    { key: 'zhi_liu_po', type: '破', color: '#888', level: '支' },
    { key: 'zhi_san_xing', type: '刑', color: '#d30505', level: '支' },
  ]
  tagDefs.forEach(function(td) {
    var arr = rel[td.key]
    if (arr && arr.length) {
      arr.forEach(function(item) {
        tags.push({ label: td.level + td.type + ' ' + (item.desc || ''), color: td.color })
      })
    }
  })
  return tags
})

// 干支关系文本化（API返回结构化数据，转为可读文本）
const ganzhiRelationTexts = computed(() => {
  const rel = baziData.value?.ganzhi_relations
  if (!rel) return []
  const lines = []
  const relMap = [
    { key: 'gan_he', label: '天干合', cls: 'mainColor' },
    { key: 'gan_chong', label: '天干冲', cls: 'wz-text-danger' },
    { key: 'zhi_san_he', label: '地支三合', cls: 'mainColor' },
    { key: 'zhi_liu_he', label: '地支六合', cls: 'mainColor' },
    { key: 'zhi_ban_he', label: '地支半合', cls: 'mainColor' },
    { key: 'zhi_an_he', label: '地支暗合', cls: 'mainColor' },
    { key: 'zhi_liu_chong', label: '地支六冲', cls: 'wz-text-danger' },
    { key: 'zhi_liu_hai', label: '地支六害', cls: 'wz-text-danger' },
    { key: 'zhi_liu_po', label: '地支相破', cls: 'wz-text-warn' },
    { key: 'zhi_san_xing', label: '地支三刑', cls: 'wz-text-warn' },
    { key: 'zhi_san_hui', label: '地支三会', cls: 'mainColor' },
  ]
  relMap.forEach(r => {
    const arr = rel[r.key]
    if (arr && arr.length) {
      const text = arr.map(item => item.desc || `${item.gan1 || item.zhi1 || ''}${item.gan2 || item.zhi2 || ''}`).join('、')
      lines.push({ label: r.label, text, cls: r.cls })
    }
  })
  return lines
})

const wzRelationTags = computed(() => {
  const tags = []
  const rel = baziData.value?.ganzhi_relations
  if (!rel) return tags
  const defs = [
    { key: 'gan_he', type: '合', color: '#07e930', level: '干' },
    { key: 'gan_chong', type: '冲', color: '#d30505', level: '干' },
    { key: 'zhi_liu_he', type: '合', color: '#07e930', level: '支' },
    { key: 'zhi_san_he', type: '三合', color: '#2e83f6', level: '支' },
    { key: 'zhi_ban_he', type: '半合', color: '#5bc0de', level: '支' },
    { key: 'zhi_an_he', type: '暗合', color: '#8e6fbf', level: '支' },
    { key: 'zhi_san_hui', type: '三会', color: '#e67e22', level: '支' },
    { key: 'zhi_liu_chong', type: '冲', color: '#d30505', level: '支' },
    { key: 'zhi_liu_hai', type: '害', color: '#ef9104', level: '支' },
    { key: 'zhi_liu_po', type: '破', color: '#888', level: '支' },
    { key: 'zhi_san_xing', type: '刑', color: '#d30505', level: '支' },
  ]
  defs.forEach(d => {
    const arr = rel[d.key]
    if (arr && arr.length) {
      arr.forEach(item => {
        tags.push({ label: d.level + (item.desc || ''), color: d.color })
      })
    }
  })
  return tags
})

const proWuxingWangduSorted = computed(() => {
  const wx = baziData.value?.wu_xing || {}
  const wxw = baziData.value?.wang_xiang_xiu || []
  const wxColors = {
    '水': { color: '#2e83f6', bg: 'rgba(46,131,246,0.1)' },
    '木': { color: '#07e930', bg: 'rgba(7,233,48,0.1)' },
    '金': { color: '#ef9104', bg: 'rgba(239,145,4,0.1)' },
    '土': { color: '#8b6d03', bg: 'rgba(139,109,3,0.1)' },
    '火': { color: '#d30505', bg: 'rgba(211,5,5,0.1)' },
  }
  const wsRank = { '旺': 0, '相': 1, '休': 2, '囚': 3, '死': 4 }
  const names = ['金', '木', '水', '火', '土']
  const items = names.map((n, i) => ({
    name: n,
    count: typeof wx[n] === 'number' ? wx[n] : (wx[n]?.count || 0),
    wang: wxw[i] || '',
    color: wxColors[n].color,
    bg: wxColors[n].bg,
  }))
  items.sort((a, b) => (wsRank[a.wang] ?? 4) - (wsRank[b.wang] ?? 4))
  return items.filter(i => i.wang)
})

const qiyunSummary = computed(() => {
  const d = baziData.value
  if (!d) return ''
  const qyd = d.qi_yun_detail
  if (qyd && qyd.text) return qyd.text
  if (wzProData.value && wzProData.value.qiyun_info) return wzProData.value.qiyun_info
  const qiAge = d.qi_yun_age || wzProData.value?.qi_yun_age
  if (qiAge) return `${qiAge}岁起运`
  return ''
})

// 缺失五行
const lackWuXing = computed(() => {
  const items = wxSummaryItems.value
  return items.filter(w => w.count === 0).map(w => w.name)
})

// 性格分析
const personality = computed(() => baziData.value?.personality || null)

// 命卦
const mingGua = computed(() => baziData.value?.ming_gua || null)

// 古籍引用
const gujiRefs = computed(() => baziData.value?.guji_refs || [])

// 旺相休
const wangXiangXiu = computed(() => baziData.value?.wang_xiang_xiu || [])

// 节气
const jieQiRange = computed(() => baziData.value?.jie_qi_range || null)

function buildCangGan(cgList, ssList) {
  if (!cgList || !cgList.length) return []
  if (typeof cgList[0] === 'string') {
    return cgList.map((g, i) => ({ gz: g, ss: ssList?.[i] || '' }))
  }
  return cgList
}

function getDaYunDetail() {
  const d = baziData.value
  if (!d) return {}
  const dyList = d.da_yun || []
  const idx = selDaYunIdx.value
  if (idx < 0 || idx >= dyList.length) return {}
  const dy = dyList[idx]
  return {
    tg: dy.gan, dz: dy.zhi,
    ss: dy.gan_shishen_abbrev || '',
    canggan: buildCangGan(dy.cang_gan, dy.cang_gan_shi_shen),
    xingyun: dy.xing_yun || dy.chang_sheng || '',
    zizuo: dy.zi_zuo || '',
    kongwang: dy.kong_wang || '',
    nayin: dy.nayin || '',
    shensha: dy.shen_sha || [],
  }
}

function getLiuNianDetail() {
  const d = baziData.value
  if (!d) return {}
  const lnList = d.liu_nian || []
  const idx = selLiuNianIdx.value
  if (idx < 0 || idx >= lnList.length) return {}
  const ln = lnList[idx]
  return {
    tg: ln.gan_zhi?.[0] || ln.gan,
    dz: ln.gan_zhi?.[1] || ln.zhi,
    ss: ln.gan_shishen_abbrev || ln.shi_shen || '',
    canggan: buildCangGan(ln.cang_gan, ln.cang_gan_shi_shen),
    xingyun: ln.xing_yun || ln.chang_sheng || '',
    zizuo: ln.zi_zuo || '',
    kongwang: ln.kong_wang || '',
    nayin: ln.nayin || '',
    shensha: ln.shen_sha || [],
  }
}

function getXiaoYunDetail() {
  const d = baziData.value
  if (!d) return {}
  const xyList = d.xiao_yun || []
  const idx = selLiuNianIdx.value
  if (idx < 0 || idx >= xyList.length) return {}
  const xy = xyList[idx]
  return {
    tg: xy.gan, dz: xy.zhi,
    canggan: buildCangGan(null, null),
  }
}

function getLiuYueDetail() {
  const d = baziData.value
  if (!d) return {}
  const lmList = d.liu_yue || []
  const idx = selLiuYueIdx.value
  if (idx < 0 || idx >= lmList.length) return {}
  const lm = lmList[idx]
  return {
    tg: lm.gan_zhi?.[0] || lm.gan,
    dz: lm.gan_zhi?.[1] || lm.zhi,
    nayin: lm.nayin || '',
    shensha: lm.shen_sha || [],
  }
}

const selLiuYueIdx = ref(0)

function selectDaYun(idx) {
  selDaYunIdx.value = idx
  // 切换大运时重置流年到当前
  const d = baziData.value
  const lnList = d?.liu_nian || []
  selLiuNianIdx.value = -1
  for (let i = 0; i < lnList.length; i++) {
    if (lnList[i].current) { selLiuNianIdx.value = i; break }
  }
  if (selLiuNianIdx.value < 0 && lnList.length) selLiuNianIdx.value = 0
}

function selectLiuNian(idx) {
  selLiuNianIdx.value = idx
  // 同步小运
  selLiuYueIdx.value = 0
}

function toggleColOrder() {
  colOrder.value = colOrder.value === 'dy-first' ? 'sz-first' : 'dy-first'
  uni.setStorageSync('xc_bazi_colOrder', colOrder.value)
  yunRefreshKey.value++
}

function switchYunPhase(phase) {
  savedSel[activeYunType.value] = { dy: selDaYunIdx.value, ln: selLiuNianIdx.value, ly: selLiuYueIdx.value, lmlist: proLiuYue.value.slice() }
  activeYunType.value = phase
  yunRefreshKey.value++
  var saved = savedSel[phase]
  if (saved.dy >= 0) {
    selDaYunIdx.value = saved.dy
    selLiuNianIdx.value = saved.ln
    selLiuYueIdx.value = saved.ly
    proLiuYue.value = saved.lmlist
  } else {
    selDaYunIdx.value = -1
    const list = phase === 'xiaoyun'
      ? (baziData.value.xiao_yun || []).filter(xy => xy.age <= (baziData.value.qi_yun_age || 7) + 1)
      : (baziData.value.da_yun || []).filter(dy => dy.gan || dy.zhi)
    for (let i = 0; i < list.length; i++) {
      if (list[i].current) { selDaYunIdx.value = i; break }
    }
    if (selDaYunIdx.value < 0 && list.length > 0) selDaYunIdx.value = 0
    selLiuNianIdx.value = -1
    const lnList = filteredLiuNian.value
    for (let i = 0; i < lnList.length; i++) {
      if (lnList[i].current) { selLiuNianIdx.value = i; break }
    }
    if (selLiuNianIdx.value < 0 && lnList.length) selLiuNianIdx.value = 0
    updateLiuYue()
  }
  updateYunActiveDOM()
  scrollActiveIntoView()
}

function getScopedAttr() {
  if (typeof document === 'undefined') return ''
  var el = document.getElementById('wz-yun-main')
  if (!el) return ''
  var attrs = el.attributes
  for (var i = 0; i < attrs.length; i++) {
    if (attrs[i].name.indexOf('data-v-') === 0) return attrs[i].name
  }
  return ''
}

function ce(tag, cls, scopedAttr, text) {
  var el = document.createElement(tag)
  if (cls) el.className = cls
  if (scopedAttr) el.setAttribute(scopedAttr, '')
  if (text !== undefined && text !== null && text !== false) el.textContent = text
  return el
}

function renderYunItemsDOM() {
  if (typeof document === 'undefined') return
  nextTick(() => {
    var sa = getScopedAttr()

    var mainEl = document.getElementById('wz-yun-main')
    if (mainEl) {
      mainEl.setAttribute('data-yun-type', activeYunType.value)
      mainEl.innerHTML = ''
      var list = activeYunList.value
      list.forEach(function(item, idx) {
        var cls = 'wz-yun-item'
        if (idx === selDaYunIdx.value) cls += ' wz-active'
        else if (item.current) cls += ' wz-current'
        var row = ce('div', cls, sa)
        row.setAttribute('data-idx', idx)
        if (item.start_year) row.appendChild(ce('span', 'wz-yun-item-year', sa, item.start_year))
        if (item.start_age && item.end_age && item.start_age !== item.end_age) row.appendChild(ce('span', 'wz-yun-item-age', sa, item.start_age + '-' + item.end_age))
        else if (item.start_age) row.appendChild(ce('span', 'wz-yun-item-age', sa, item.start_age + '岁'))
        else if (item.age) row.appendChild(ce('span', 'wz-yun-item-age', sa, item.age + '岁'))
        if (item.gan) {
          var gw = ce('div', null, sa)
          var gSpan = document.createElement('span')
          gSpan.className = 'wz-yun-item-gz'
          var gColor = WX_COLOR_BZ && WX_COLOR_BZ[item.gan] || ''
          if (gColor) gSpan.style.color = gColor
          gSpan.textContent = item.gan
          if (sa) gSpan.setAttribute(sa, '')
          gw.appendChild(gSpan)
          row.appendChild(gw)
        }
        if (item.zhi) {
          var zw = ce('div', null, sa)
          var zSpan = document.createElement('span')
          zSpan.className = 'wz-yun-item-gz'
          var zColor = WX_COLOR_BZ && WX_COLOR_BZ[item.zhi] || ''
          if (zColor) zSpan.style.color = zColor
          zSpan.textContent = item.zhi
          if (sa) zSpan.setAttribute(sa, '')
          zw.appendChild(zSpan)
          row.appendChild(zw)
        }
        var ss = item.ss_full || item.gan_shishen_abbrev
        if (ss) row.appendChild(ce('span', 'wz-yun-item-ss', sa, ss))
        mainEl.appendChild(row)
      })
    }

    var lnEl = document.getElementById('wz-yun-liunian')
    if (lnEl) {
      lnEl.innerHTML = ''
      var lnList = filteredLiuNian.value
      lnList.forEach(function(item, idx) {
        var cls = 'wz-yun-item'
        if (idx === selLiuNianIdx.value) cls += ' wz-active'
        else if (item.current) cls += ' wz-current'
        var row = ce('div', cls, sa)
        row.setAttribute('data-idx', idx)
        row.setAttribute('data-type', 'liunian')
        row.appendChild(ce('span', 'wz-yun-item-year', sa, item.year))
        if (item.age) row.appendChild(ce('span', 'wz-yun-item-age', sa, item.age))
        if (item.gan) {
          var gwl = ce('div', null, sa)
          var gsL = document.createElement('span')
          gsL.className = 'wz-yun-item-gz'
          var gcL = WX_COLOR_BZ && WX_COLOR_BZ[item.gan] || ''
          if (gcL) gsL.style.color = gcL
          gsL.textContent = item.gan
          if (sa) gsL.setAttribute(sa, '')
          gwl.appendChild(gsL)
          row.appendChild(gwl)
        }
        if (item.zhi) {
          var zwl = ce('div', null, sa)
          var zsL = document.createElement('span')
          zsL.className = 'wz-yun-item-gz'
          var zcL = WX_COLOR_BZ && WX_COLOR_BZ[item.zhi] || ''
          if (zcL) zsL.style.color = zcL
          zsL.textContent = item.zhi
          if (sa) zsL.setAttribute(sa, '')
          zwl.appendChild(zsL)
          row.appendChild(zwl)
        }
        lnEl.appendChild(row)
      })
    }

    var lyEl = document.getElementById('wz-yun-liuyue')
    if (lyEl) {
      lyEl.innerHTML = ''
      var lyList = proLiuYue.value
      lyList.forEach(function(item, idx) {
        var cls = 'wz-yun-item'
        if (idx === selLiuYueIdx.value) cls += ' wz-active'
        else if (item.current) cls += ' wz-current'
        var row = ce('div', cls, sa)
        row.setAttribute('data-idx', idx)
        row.setAttribute('data-type', 'liuyue')
        if (item.jieqi) row.appendChild(ce('span', 'wz-yun-item-month', sa, item.jieqi))
        if (item.date) row.appendChild(ce('span', 'wz-yun-item-date', sa, item.date))
        if (item.gan) {
          var gwly = ce('div', null, sa)
          var gsLy = document.createElement('span')
          gsLy.className = 'wz-yun-item-gz'
          var gcLy = WX_COLOR_BZ && WX_COLOR_BZ[item.gan] || ''
          if (gcLy) gsLy.style.color = gcLy
          gsLy.textContent = item.gan
          if (sa) gsLy.setAttribute(sa, '')
          gwly.appendChild(gsLy)
          row.appendChild(gwly)
        }
        if (item.zhi) {
          var zwly = ce('div', null, sa)
          var zsLy = document.createElement('span')
          zsLy.className = 'wz-yun-item-gz'
          var zcLy = WX_COLOR_BZ && WX_COLOR_BZ[item.zhi] || ''
          if (zcLy) zsLy.style.color = zcLy
          zsLy.textContent = item.zhi
          if (sa) zsLy.setAttribute(sa, '')
          zwly.appendChild(zsLy)
          row.appendChild(zwly)
        }
        if (item.tgSs) row.appendChild(ce('span', 'wz-yun-item-ss', sa, item.tgSs))
        lyEl.appendChild(row)
      })
    }

    setupDragScroll(document.getElementById('wz-yun-main'))
    setupDragScroll(document.getElementById('wz-yun-liunian'))
    setupDragScroll(document.getElementById('wz-yun-liuyue'))
    updateYunActiveDOM()
    scrollActiveIntoView()
  })
}

function setupDragScroll(el) {
  if (!el || el._dragScrolled) return
  el._dragScrolled = true
  var isDown = false
  var isDragging = false
  var touchMode = ''
  var startX = 0
  var startY = 0
  var scrollLeft = 0
  el.addEventListener('mousedown', function(e) {
    isDown = true
    isDragging = false
    startX = e.clientX
    scrollLeft = el.scrollLeft
  })
  el.addEventListener('mousemove', function(e) {
    if (!isDown) return
    var dx = e.clientX - startX
    if (!isDragging) {
      if (Math.abs(dx) <= 5) return
      isDragging = true
      el.style.cursor = 'grabbing'
      el.style.userSelect = 'none'
    }
    e.preventDefault()
    el.scrollLeft = scrollLeft - dx
  })
  document.addEventListener('mouseup', function upHandler() {
    if (!isDown) return
    isDown = false
    if (isDragging) {
      el.style.cursor = ''
      el.style.userSelect = ''
      el.setAttribute('data-drag-moved', '1')
      setTimeout(function() { el.removeAttribute('data-drag-moved') }, 100)
    }
  })
  el.addEventListener('touchstart', function(e) {
    if (!e.touches || !e.touches[0]) return
    touchMode = ''
    startX = e.touches[0].clientX
    startY = e.touches[0].clientY
    scrollLeft = el.scrollLeft
  }, { passive: true })
  el.addEventListener('touchmove', function(e) {
    if (!e.touches || !e.touches[0]) return
    var dx = e.touches[0].clientX - startX
    var dy = e.touches[0].clientY - startY
    if (!touchMode) {
      if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return
      touchMode = Math.abs(dx) > Math.abs(dy) * 1.15 ? 'x' : 'y'
    }
    if (touchMode === 'x') {
      e.preventDefault()
      e.stopPropagation()
      el.scrollLeft = scrollLeft - dx
    }
  }, { passive: false })
  el.addEventListener('touchend', function() {
    touchMode = ''
  }, { passive: true })
}

function updateYunActiveDOM() {
  if (typeof document === 'undefined') return
  var containers = [
    { el: document.getElementById('wz-yun-main'), idx: selDaYunIdx.value },
    { el: document.getElementById('wz-yun-liunian'), idx: selLiuNianIdx.value },
    { el: document.getElementById('wz-yun-liuyue'), idx: selLiuYueIdx.value },
  ]
  containers.forEach(function(c) {
    if (!c.el) return
    var items = c.el.querySelectorAll('.wz-yun-item')
    items.forEach(function(item, i) {
      item.classList.toggle('wz-active', i === c.idx)
    })
  })
}

function scrollActiveIntoView() {
  if (typeof document === 'undefined') return
  var targets = [
    { el: document.getElementById('wz-yun-main'), idx: selDaYunIdx.value },
    { el: document.getElementById('wz-yun-liunian'), idx: selLiuNianIdx.value },
    { el: document.getElementById('wz-yun-liuyue'), idx: selLiuYueIdx.value },
  ]
  targets.forEach(function(t) {
    if (!t.el || t.idx < 0) return
    var items = t.el.querySelectorAll('.wz-yun-item')
    if (items && items[t.idx]) {
      items[t.idx].scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
    }
  })
}

document.addEventListener('click', function(e) {
  var el = e.target
  while (el && el !== document.body) {
    var idx = el.getAttribute && el.getAttribute('data-idx')
    if (idx !== null && idx !== undefined) {
      var container = el.closest && el.closest('.wz-yun-items')
      if (container && container.getAttribute('data-drag-moved') === '1') return
      idx = parseInt(idx)
      var type = el.getAttribute('data-type') || activeYunType.value
      if (type === 'liunian') {
        selectYun('liunian', filteredLiuNian.value[idx]._realIdx)
      } else if (type === 'liuyue') {
        selectYun('liuyue', idx)
      } else {
        selectYun(type, activeYunList.value[idx]._realIdx)
      }
      return
    }
    el = el.parentElement
  }
})

watch(activeYunType, (val) => {
  nextTick(() => {
    document.querySelectorAll('.wz-yun-tab').forEach(t => {
      const isDayun = t.textContent.trim() === '大运'
      t.classList.toggle('active', isDayun ? val === 'dayun' : val === 'xiaoyun')
    })
    renderYunItemsDOM()
  })
})

function selectYun(type, idx) {
  yunRefreshKey.value++
  if (type === 'liunian') {
    selLiuNianIdx.value = idx
    if (currentYunPhase.value === 'xiaoyun') {
      selDaYunIdx.value = idx
    }
    updateLiuYue()
  } else if (type === 'liuyue') {
    selLiuYueIdx.value = idx
  } else {
    selDaYunIdx.value = idx
    if (currentYunPhase.value === 'xiaoyun') {
      selLiuNianIdx.value = idx
    } else {
      selLiuNianIdx.value = -1
      const nowYear = new Date().getFullYear()
      const lnList = filteredLiuNian.value
      for (let i = 0; i < lnList.length; i++) {
        const ly = typeof lnList[i].year === 'string' ? parseInt(lnList[i].year) : lnList[i].year
        if (ly === nowYear || lnList[i].current) { selLiuNianIdx.value = i; break }
      }
      if (selLiuNianIdx.value < 0 && lnList.length) selLiuNianIdx.value = 0
    }
    updateLiuYue()
  }
  updateYunActiveDOM()
  savedSel[activeYunType.value] = { dy: selDaYunIdx.value, ln: selLiuNianIdx.value, ly: selLiuYueIdx.value }
}

function updateLiuYue() {
  const lnList = filteredLiuNian.value
  const lnIdx = selLiuNianIdx.value
  if (lnIdx >= 0 && lnIdx < lnList.length) {
    const year = lnList[lnIdx].year
    if (year) {
      const ly = typeof year === 'string' ? parseInt(year) : year
      let lmList = computeLiuYueList(ly)
      const d = baziData.value
      const birthYear = d?.four_pillars?.year?.year || parseInt((d?.birth_solar || d?.birth_input || '2000').substring(0, 4)) || 2000
      const qiAge = d?.qi_yun_age || 7
      const qiyunYr = getQiYunYear(d)
      const qiyunMo = getQiYunMonth(d)

      if (currentYunPhase.value === 'xiaoyun') {
        const xyList = d?.xiao_yun || []
        const preQiXy = xyList.filter(xy => xy.age <= qiAge + 1)
        if (preQiXy.length > 0) {
          const lastXyYear = birthYear + preQiXy[preQiXy.length - 1].age - 1
          if (ly === lastXyYear && qiyunMo && qiyunMo > 1 && qiyunMo <= 12) {
            lmList = lmList.slice(0, qiyunMo)
          }
        }
      } else {
        if (qiyunYr && ly === qiyunYr && qiyunMo && qiyunMo > 1 && qiyunMo <= 12) {
          lmList = lmList.slice(qiyunMo - 1)
        }
      }
      proLiuYue.value = lmList
      const nowMonth = new Date().getMonth() + 1
      const nowYear = new Date().getFullYear()
      selLiuYueIdx.value = 0
      if (ly === nowYear) {
        for (let i = 0; i < proLiuYue.value.length; i++) {
          if (proLiuYue.value[i].month_num === nowMonth || proLiuYue.value[i].current) { selLiuYueIdx.value = i; break }
        }
      }
    }
  }
}

function computeLiuYueList(year) {
  const TG = '甲乙丙丁戊己庚辛壬癸'
  const lnList = baziData.value?.liu_nian || []
  const selectedLn = lnList.find(l => {
    const ly = typeof l.year === 'string' ? parseInt(l.year) : l.year
    return ly === year
  })
  const yearGan = selectedLn ? (selectedLn.gan || '') : ''
  const yearGanIdx = yearGan ? TG.indexOf(yearGan) : -1
  const monthGanStart = yearGanIdx >= 0 ? [2, 4, 6, 8, 0][yearGanIdx % 5] : 0
  const monthZhis = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
  const jieNames = ['立春', '惊蛰', '清明', '立夏', '芒种', '小暑', '立秋', '白露', '寒露', '立冬', '大雪', '小寒']
  const monthNames = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月']
  const dayMaster = baziData.value?.four_pillars?.day?.gan || ''
  const dayZhi = baziData.value?.four_pillars?.day?.zhi || ''
  const CANG_GAN = { '子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'], '卯': ['乙'], '辰': ['戊', '乙', '癸'], '巳': ['丙', '庚', '戊'], '午': ['丁', '己'], '未': ['己', '丁', '乙'], '申': ['庚', '壬', '戊'], '酉': ['辛'], '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲'] }
  const NAYIN_TABLE = {
    '甲子':'海中金','乙丑':'海中金','丙寅':'炉中火','丁卯':'炉中火','戊辰':'大林木','己巳':'大林木',
    '庚午':'路旁土','辛未':'路旁土','壬申':'剑锋金','癸酉':'剑锋金','甲戌':'山头火','乙亥':'山头火',
    '丙子':'涧下水','丁丑':'涧下水','戊寅':'城头土','己卯':'城头土','庚辰':'白蜡金','辛巳':'白蜡金',
    '壬午':'杨柳木','癸未':'杨柳木','甲申':'泉中水','乙酉':'泉中水','丙戌':'屋上土','丁亥':'屋上土',
    '戊子':'霹雳火','己丑':'霹雳火','庚寅':'松柏木','辛卯':'松柏木','壬辰':'长流水','癸巳':'长流水',
    '甲午':'砂石金','乙未':'砂石金','丙申':'山下火','丁酉':'山下火','戊戌':'平地木','己亥':'平地木',
    '庚子':'壁上土','辛丑':'壁上土','壬寅':'金箔金','癸卯':'金箔金','甲辰':'覆灯火','乙巳':'覆灯火',
    '丙午':'天河水','丁未':'天河水','戊申':'大驿土','己酉':'大驿土','庚戌':'钗钏金','辛亥':'钗钏金',
    '壬子':'桑柘木','癸丑':'桑柘木','甲寅':'大溪水','乙卯':'大溪水','丙辰':'沙中土','丁巳':'沙中土',
    '戊午':'天上火','己未':'天上火','庚申':'石榴木','辛酉':'石榴木','壬戌':'大海水','癸亥':'大海水',
  }
  const CHANG_SHENG_TABLE = {
    '甲': {'寅':'长生','卯':'沐浴','辰':'冠带','巳':'临官','午':'帝旺','未':'衰','申':'病','酉':'死','戌':'墓','亥':'绝','子':'胎','丑':'养'},
    '乙': {'亥':'长生','子':'沐浴','丑':'冠带','寅':'临官','卯':'帝旺','辰':'衰','巳':'病','午':'死','未':'墓','申':'绝','酉':'胎','戌':'养'},
    '丙': {'寅':'长生','卯':'沐浴','辰':'冠带','巳':'临官','午':'帝旺','未':'衰','申':'病','酉':'死','戌':'墓','亥':'绝','子':'胎','丑':'养'},
    '丁': {'酉':'长生','申':'沐浴','未':'冠带','午':'临官','巳':'帝旺','辰':'衰','卯':'病','寅':'死','丑':'墓','子':'绝','亥':'胎','戌':'养'},
    '戊': {'寅':'长生','卯':'沐浴','辰':'冠带','巳':'临官','午':'帝旺','未':'衰','申':'病','酉':'死','戌':'墓','亥':'绝','子':'胎','丑':'养'},
    '己': {'酉':'长生','申':'沐浴','未':'冠带','午':'临官','巳':'帝旺','辰':'衰','卯':'病','寅':'死','丑':'墓','子':'绝','亥':'胎','戌':'养'},
    '庚': {'巳':'长生','午':'沐浴','未':'冠带','申':'临官','酉':'帝旺','戌':'衰','亥':'病','子':'死','丑':'墓','寅':'绝','卯':'胎','辰':'养'},
    '辛': {'子':'长生','亥':'沐浴','戌':'冠带','酉':'临官','申':'帝旺','未':'衰','午':'病','巳':'死','辰':'墓','卯':'绝','寅':'胎','丑':'养'},
    '壬': {'申':'长生','酉':'沐浴','戌':'冠带','亥':'临官','子':'帝旺','丑':'衰','寅':'病','卯':'死','辰':'墓','巳':'绝','午':'胎','未':'养'},
    '癸': {'卯':'长生','寅':'沐浴','丑':'冠带','子':'临官','亥':'帝旺','戌':'衰','酉':'病','申':'死','未':'墓','午':'绝','巳':'胎','辰':'养'},
  }
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() + 1
  const currentDay = now.getDate()
  let currentLiuyueIdx = -1
  if (year === currentYear) {
    const jieMonthDays = [[2, 4], [3, 5], [4, 5], [5, 5], [6, 5], [7, 7], [8, 7], [9, 7], [10, 8], [11, 7], [12, 7], [1, 5]]
    if (currentMonth === 1 && currentDay >= 5) {
      currentLiuyueIdx = 11
    } else {
      for (let j = 0; j < jieMonthDays.length - 1; j++) {
        const [jm, jd] = jieMonthDays[j]
        if (currentMonth > jm || (currentMonth === jm && currentDay >= jd)) currentLiuyueIdx = j
      }
      if (currentLiuyueIdx < 0) currentLiuyueIdx = 11
    }
  }
  const list = []
  for (let i = 0; i < 12; i++) {
    const mGanIdx = (monthGanStart + i) % 10
    const mGan = TG[mGanIdx]
    const mZhi = monthZhis[i]
    const mSs = getShiShenLocal(dayMaster, mGan)
    const mGanZhi = mGan + mZhi
    const jieDates = ['2/4', '3/5', '4/5', '5/5', '6/5', '7/7', '8/7', '9/7', '10/8', '11/7', '12/7', '1/5']
    const cgList = CANG_GAN[mZhi] || []
    const cgSsList = cgList.map(g => getShiShenLocal(dayMaster, g))
    const nayin = NAYIN_TABLE[mGanZhi] || ''
    const changSheng = (CHANG_SHENG_TABLE[mGan] && CHANG_SHENG_TABLE[mGan][dayZhi]) || ''
    const ziZuo = (CHANG_SHENG_TABLE[mGan] && CHANG_SHENG_TABLE[mGan][mZhi]) || ''
    const yearZhi = baziData.value?.four_pillars?.year?.zhi || ''
    const kongWang = computeKongWang(mGan, mZhi)
    const shenSha = computeShenShaLocal(mGan, mZhi, dayMaster, yearZhi, dayZhi)
    list.push({
      jieqi: jieNames[i],
      date: jieDates[i],
      month_name: monthNames[i],
      month_num: i + 1,
      gan: mGan,
      zhi: mZhi,
      gan_zhi: mGanZhi,
      tgSs: mSs,
      cang_gan: cgList,
      cang_gan_shi_shen: cgSsList,
      nayin: nayin,
      chang_sheng: changSheng,
      zi_zuo: ziZuo,
      kong_wang: kongWang,
      shen_sha: shenSha,
      current: i === currentLiuyueIdx,
    })
  }
  return list
}

function jumpToToday() {
  yunRefreshKey.value++
  const nowYear = new Date().getFullYear()
  const d = baziData.value
  if (!d) return
  const birthYear = d.four_pillars?.year?.year || parseInt((d.birth_solar || d.birth_input || '2000').substring(0, 4)) || 2000
  const currentAge = nowYear - birthYear + 1
  const qiAge = d.qi_yun_age || 7
  if (currentAge <= qiAge) {
    activeYunType.value = 'xiaoyun'
    const xyList = (d.xiao_yun || []).filter(xy => xy.age <= qiAge + 1)
    for (let i = 0; i < xyList.length; i++) {
      if (xyList[i].age === currentAge) { selDaYunIdx.value = i; break }
    }
    if (selDaYunIdx.value < 0 && xyList.length > 0) selDaYunIdx.value = 0
  } else {
    activeYunType.value = 'dayun'
    const dyList = (d.da_yun || []).filter(item => item.gan || item.zhi).slice(0, 10)
    for (let j = 0; j < dyList.length; j++) {
      const startYear = dyList[j].start_year
      const endYear = dyList[j].end_year
      if (startYear && endYear && nowYear >= startYear && nowYear <= endYear) {
        selDaYunIdx.value = j
        break
      }
    }
    if (selDaYunIdx.value < 0 && dyList.length > 0) selDaYunIdx.value = 0
  }
  selLiuNianIdx.value = -1
  const fLnList = filteredLiuNian.value
  for (let i = 0; i < fLnList.length; i++) {
    const ly = typeof fLnList[i].year === 'string' ? parseInt(fLnList[i].year) : fLnList[i].year
    if (ly === nowYear) { selLiuNianIdx.value = i; break }
  }
  if (selLiuNianIdx.value < 0 && fLnList.length) selLiuNianIdx.value = 0
  var _initLyYear = nowYear
  for (var _li = 0; _li < fLnList.length; _li++) {
    if (fLnList[_li]._active) {
      _initLyYear = typeof fLnList[_li].year === 'string' ? parseInt(fLnList[_li].year) : fLnList[_li].year
      break
    }
  }
  var lmResult = computeLiuYueList(_initLyYear)
  if (currentYunPhase.value === 'xiaoyun') {
    var _qiAge = d.qi_yun_age || 7
    var _xyList = (d.xiao_yun || []).filter(xy => xy.age <= _qiAge)
    if (_xyList.length > 0) {
      var _lastXyYear = birthYear + _xyList[_xyList.length - 1].age - 1
      if (_initLyYear === _lastXyYear) {
        var _maxMonth = getQiYunMaxLiuYue(d)
        if (_maxMonth > 0 && _maxMonth < 12) {
          lmResult = lmResult.slice(0, _maxMonth)
        }
      }
    }
  }
  proLiuYue.value = lmResult
  selLiuYueIdx.value = 0
  var nowMonth = new Date().getMonth() + 1
  var lmList = proLiuYue.value
  for (var _mi = 0; _mi < lmList.length; _mi++) {
    if (lmList[_mi].month_num === nowMonth || lmList[_mi].current) { selLiuYueIdx.value = _mi; break }
  }
  renderYunItemsDOM()
}

function ssTagClass(name) {
  if (!name) return ''
  if (name.indexOf('禄') > -1 || name.indexOf('贵') > -1 || name.indexOf('马') > -1) return 'ss-ji'
  if (name.indexOf('冲') > -1 || name.indexOf('刑') > -1 || name.indexOf('害') > -1 || name.indexOf('破') > -1) return 'ss-xiong'
  return ''
}

const sortedNotes = computed(() => {
  return [...notes.value].sort((a, b) => b.created - a.created)
})

// ═══ 方法 ═══
function goHome() {
  // #ifdef H5
  try {
    delete window.__xc_lastBaziResultRoute
    location.hash = '#/pages/index/index'
  } catch(_) {}
  // #endif
  uni.switchTab({
    url: '/pages/index/index',
    fail: function() {
      // #ifdef H5
      try { location.hash = '#/pages/index/index' } catch(_) {}
      // #endif
    }
  })
}

function goBack() {
  uni.navigateBack({ delta: 1 })
}

function goBaziHome() {
  // 用户主动回八字首页时，清掉本次会话的结果页记忆。
  // #ifdef H5
  try {
    delete window.__xc_lastBaziResultRoute
    sessionStorage.removeItem('xc_bazi_params')
    sessionStorage.setItem('_nav_query', 'tab=free')
    window.location.hash = '#/pages/bazi-index/index?tab=free'
    try {
      if (window.__xcRenderTabPath) window.__xcRenderTabPath('/pages/bazi-index/index')
    } catch(_) {}
    return
  } catch(_) {}
  // #endif
  uni.switchTab({
    url: '/pages/bazi-index/index',
    fail: function() {
      // #ifdef H5
      try { location.hash = '#/pages/bazi-index/index?tab=free' } catch(_) {}
      // #endif
    }
  })
}

function toggleTMS() { showTMS.value = !showTMS.value }
function showSharePanel() { sharePanelOpen.value = true; try { document.getElementById('sharePanelModal')?.classList.add('open') } catch(_) {} }
function shareAsImage() {
  if (!baziData.value) return
  uni.showLoading({ title: '生成图片中...' })

  const ctx = uni.createCanvasContext('exportCanvas')
  const W = 750, H = 1200

  // 背景
  const isDark = theme.value === 'dark'
  ctx.setFillStyle(isDark ? '#1a1e30' : '#f7f2ea')
  ctx.fillRect(0, 0, W, H)

  // 标题
  ctx.setFillStyle(isDark ? '#b2955d' : '#8b6d03')
  ctx.setFontSize(36)
  ctx.setTextAlign('center')
  ctx.fillText('时安解忧屋 · 八字排盘', W / 2, 60)

  // 副标题
  const fp = baziData.value.four_pillars || {}
  const ganZhi = `${fp.year?.gan_zhi || ''} ${fp.month?.gan_zhi || ''} ${fp.day?.gan_zhi || ''} ${fp.hour?.gan_zhi || ''}`
  ctx.setFillStyle(isDark ? 'rgba(240,236,228,0.97)' : 'rgba(20,16,10,0.96)')
  ctx.setFontSize(28)
  ctx.fillText(ganZhi, W / 2, 110)

  // 分隔线
  ctx.setStrokeStyle(isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.045)')
  ctx.setLineWidth(1)
  ctx.beginPath()
  ctx.moveTo(40, 135)
  ctx.lineTo(W - 40, 135)
  ctx.stroke()

  // 四柱表格
  let y = 175
  const colW = (W - 80) / 4
  const labels = ['年柱', '月柱', '日柱', '时柱']
  const keys = ['year', 'month', 'day', 'hour']

  // 表头
  ctx.setFillStyle(isDark ? 'rgba(178,149,93,0.15)' : 'rgba(178,149,93,0.10)')
  ctx.fillRect(40, y - 25, W - 80, 40)
  ctx.setFillStyle('#b2955d')
  ctx.setFontSize(22)
  keys.forEach((k, i) => {
    ctx.setTextAlign('center')
    ctx.fillText(labels[i], 40 + colW * i + colW / 2, y)
  })
  y += 40

  // 天干
  ctx.setFontSize(38)
  ctx.setTextAlign('center')
  keys.forEach((k, i) => {
    const gan = fp[k]?.gan || ''
    const color = WX_COLOR_BZ[gan] || (isDark ? '#f0ece4' : '#14100a')
    ctx.setFillStyle(color)
    ctx.fillText(gan, 40 + colW * i + colW / 2, y + 30)
  })
  y += 55

  // 地支
  keys.forEach((k, i) => {
    const zhi = fp[k]?.zhi || ''
    const color = WX_COLOR_BZ[zhi] || (isDark ? '#f0ece4' : '#14100a')
    ctx.setFillStyle(color)
    ctx.fillText(zhi, 40 + colW * i + colW / 2, y + 30)
  })
  y += 55

  // 十神
  ctx.setFontSize(20)
  const ss = shiShen.value
  keys.forEach((k, i) => {
    ctx.setFillStyle(isDark ? 'rgba(170,160,145,0.88)' : 'rgba(100,88,68,0.78)')
    ctx.fillText(ss[k] || '', 40 + colW * i + colW / 2, y + 20)
  })
  y += 40

  // 纳音
  const ny = naYin.value
  ctx.setFontSize(18)
  keys.forEach((k, i) => {
    ctx.fillText(ny[k] || '', 40 + colW * i + colW / 2, y + 18)
  })
  y += 45

  // 分隔线
  ctx.setStrokeStyle(isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.045)')
  ctx.beginPath()
  ctx.moveTo(40, y)
  ctx.lineTo(W - 40, y)
  ctx.stroke()
  y += 30

  // 基本信息
  ctx.setTextAlign('left')
  ctx.setFontSize(22)
  const d = baziData.value
  const infoLines = [
    `姓名：${d.name || '未命名'}`,
    `性别：${d.gender || ''}  生肖：${d.sheng_xiao || ''}  星座：${d.xing_zuo || ''}`,
    `出生：${d.birth_input || d.birth_solar || ''}`,
    `日主：${d.day_master_label || (d.gender === '女' ? '元女' : '元男')}  旺衰：${d.wang_shuai || ''}`,
    `起运：${d.qi_yun_age ? d.qi_yun_age + '岁' : ''}  ${d.da_yun_direction || ''}`,
  ]
  infoLines.forEach(line => {
    ctx.setFillStyle(isDark ? 'rgba(195,185,165,0.95)' : 'rgba(70,58,40,0.90)')
    ctx.fillText(line, 60, y)
    y += 38
  })

  y += 15
  // 五行统计
  ctx.setStrokeStyle(isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.045)')
  ctx.beginPath()
  ctx.moveTo(40, y)
  ctx.lineTo(W - 40, y)
  ctx.stroke()
  y += 30

  ctx.setFillStyle('#b2955d')
  ctx.setFontSize(24)
  ctx.fillText('五行统计', 60, y)
  y += 35

  const wx = d.wu_xing || {}
  const wxNames = ['金', '木', '水', '火', '土']
  const wxColors = { '金':'#ef9104', '木':'#07e930', '水':'#2e83f6', '火':'#d30505', '土':'#8b6d03' }

  ctx.setFontSize(20)
  wxNames.forEach(name => {
    const count = typeof wx[name] === 'number' ? wx[name] : (wx[name]?.count || 0)
    ctx.setTextAlign('left')
    ctx.setFillStyle(wxColors[name])
    ctx.fillText(name, 60, y)

    // 进度条
    const barX = 110
    const barW = 400
    const barH = 14
    ctx.setFillStyle(isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)')
    ctx.fillRect(barX, y - 12, barW, barH)
    ctx.setFillStyle(wxColors[name])
    ctx.fillRect(barX, y - 12, Math.min(barW, count * barW / 8), barH)

    ctx.setFillStyle(isDark ? 'rgba(240,236,228,0.97)' : 'rgba(20,16,10,0.96)')
    ctx.setTextAlign('left')
    ctx.fillText(String(count), barX + barW + 15, y)
    y += 34
  })

  // 底部声明
  y = H - 50
  ctx.setFillStyle(isDark ? 'rgba(170,160,145,0.88)' : 'rgba(100,88,68,0.78)')
  ctx.setFontSize(16)
  ctx.setTextAlign('center')
  ctx.fillText('⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议', W / 2, y)
  y += 24
  ctx.fillText('时安解忧屋 · 看得懂用得上的民俗命理参考平台', W / 2, y)

  // 绘制并导出
  ctx.draw(false, () => {
    setTimeout(() => {
      uni.canvasToTempFilePath({
        canvasId: 'exportCanvas',
        quality: 1,
        success: (res) => {
          uni.hideLoading()
          // 保存到相册
          uni.saveImageToPhotosAlbum({
            filePath: res.tempFilePath,
            success: () => {
              uni.showToast({ title: '已保存到相册', icon: 'success' })
              closeSharePanel()
            },
            fail: (err) => {
              // 可能没有相册权限，尝试用预览方式
              if (err.errMsg && err.errMsg.includes('auth')) {
                uni.showModal({
                  title: '需要相册权限',
                  content: '请在设置中允许访问相册，或选择"预览图片"手动保存',
                  confirmText: '去设置',
                  success: (r) => {
                    if (r.confirm) uni.openSetting()
                  }
                })
              } else {
                // 降级：预览图片
                uni.previewImage({ urls: [res.tempFilePath] })
              }
            }
          })
        },
        fail: (err) => {
          uni.hideLoading()
          uni.showToast({ title: '图片生成失败', icon: 'none' })
        }
      })
    }, 300) // 等待 canvas 渲染完成
  })
}
function shareAsText() {
  if (!baziData.value) return
  const fp = baziData.value.four_pillars || {}
  const text = `八字排盘：${fp.year?.gan_zhi || ''} ${fp.month?.gan_zhi || ''} ${fp.day?.gan_zhi || ''} ${fp.hour?.gan_zhi || ''}`
  uni.setClipboardData({ data: text, success: () => uni.showToast({ title: '已复制', icon: 'success' }) })
}

function getTagInfo(key) { return noteTags.find(t => t.key === key) || noteTags[5] }
function formatNoteDate(ts) {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function _fourPillarsHash() {
  const fp = (baziData.value && baziData.value.four_pillars) || {}
  return `${fp.year?.gan_zhi||''}_${fp.month?.gan_zhi||''}_${fp.day?.gan_zhi||''}_${fp.hour?.gan_zhi||''}`
}

function _loadNotes() {
  try {
    const raw = uni.getStorageSync('xc_bazi_notes_' + _fourPillarsHash())
    return raw ? JSON.parse(raw) : []
  } catch (e) { return [] }
}

function _saveNotes() {
  uni.setStorageSync('xc_bazi_notes_' + _fourPillarsHash(), JSON.stringify(notes.value))
}

function addNote() {
  const text = noteInput.value.trim()
  if (!text) return
  notes.value.push({ id: Date.now().toString(), tag: selectedNoteTag.value, text, created: Date.now(), editing: false })
  noteInput.value = ''
  _saveNotes()
}

function editNote(id) {
  // 简化：删除后重新输入
  const note = notes.value.find(n => n.id === id)
  if (note) { noteInput.value = note.text; selectedNoteTag.value = note.tag; deleteNote(id) }
}

function deleteNote(id) {
  notes.value = notes.value.filter(n => n.id !== id)
  _saveNotes()
}

// ═══ 页面加载 ═══
onMounted(async () => {
  rememberBaziResultRoute()
  // 获取页面参数
  let params = null

  // #ifdef H5
  params = readBaziParamsFromStorage()
  // #endif

  if (!params) {
    // 从 URL 参数或 uni 路由参数获取
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    const urlParams = currentPage?.$page?.options || currentPage?.options || {}

    // #ifdef H5
    var _hashQs = ''
    var _hashMatch = location.hash.match(/\?([^#]*)$/)
    if (_hashMatch) _hashQs = _hashMatch[1]
    const urlP = new URLSearchParams(location.search || '')
    if (_hashQs) {
      new URLSearchParams(_hashQs).forEach(function(value, key) {
        urlP.set(key, value)
      })
    }
    const uy = urlP.get('y'), um = urlP.get('m'), ud = urlP.get('d')
    const uh = urlP.get('h'), umi = urlP.get('mi'), us = urlP.get('s')
    var uCal = urlP.get('cal')
    if (uy && um && ud) {
      params = {
        calType: uCal || '公历',
        gender: (us == 2) ? '女' : '男',
        birthTime: `${uy}${String(um).padStart(2,'0')}${String(ud).padStart(2,'0')}${String(uh||0).padStart(2,'0')}${String(umi||0).padStart(2,'0')}`,
        birthAddr: '', birthLng: 0, birthLat: 0,
        isDst: false, nightZiMode: '夜子时不换日',
        useSolarTime: true, isLeapMonth: false, _replay: true,
      }
    }
    // #endif

    if (!params && urlParams.id) {
      // 通过记录ID查看
      params = { id: urlParams.id }
    }
  }

  if (!params) {
    loading.value = false
    errorMsg.value = '刷新后没有找到本次排盘参数，请返回八字排盘重新排盘，或从用户管理/历史记录进入。'
    return
  }

  // 如果是记录ID模式，先获取记录
  if (params.id && !params.birthTime) {
    try {
      const r = await uni.request({ url: `/api/bazi/history/${params.id}` })
      if (r.data && r.data.success) {
        params = r.data.record?.params || params
      }
    } catch (e) {}
  }

  baziSourceParams.value = params

  // 构建排盘请求
  let birthTime = ''
  let siziPillars = null
  const calType = params.calType || '公历'

  if (calType === '四柱' && params.siziPillars) {
    siziPillars = params.siziPillars
  } else {
    if (params.birthTime) {
      birthTime = params.birthTime
    } else if (params.birthDate) {
      const [y, m, d] = params.birthDate.split('-')
      const hh = params.birthHour || '0'
      const mm = params.birthMinute || '00'
      birthTime = `${y}${m}${d}${String(hh).padStart(2,'0')}${String(mm).padStart(2,'0')}`
    }
  }

  try {
    const r = await uni.request({
      url: '/api/bazi/paipan',
      method: 'POST',
      data: {
        name: params.name || '',
        gender: params.gender || '男',
        calType,
        birthTime,
        birthAddr: params.birthAddr || '',
        birthLng: params.birthLng || 0,
        birthLat: params.birthLat || 0,
        isDst: params.isDst || false,
        nightZiMode: params.nightZiMode || '夜子时不换日',
        siziPillars,
        useSolarTime: params.useSolarTime !== false,
        isLeapMonth: params.isLeapMonth || false,
        _replay: !!params._replay
      }
    })
    const data = r.data
    if (data && data.success) {
      baziData.value = data
      baziSourceParams.value = params
      rememberLastBaziParams(params)
      // 更新导航信息
      const fp = data.four_pillars || {}
      const sx = data.sheng_xiao || ''
      navInfo.value = `${SHENGXIAO_EMOJI[sx] || ''} ${data.name || ''} ${data.birth_input || data.birth_solar || ''}`
      // 加载笔记
      notes.value = _loadNotes()
      // 更新设置
      if (params.nightZiMode) settings.nightZiMode = params.nightZiMode
      if (params.useSolarTime !== undefined) settings.useSolarTime = params.useSolarTime
      // 初始化专业排盘选中状态
      const dyList = data.da_yun || []
      selDaYunIdx.value = -1
      const nowYear = new Date().getFullYear()
      const birthYear = data.four_pillars?.year?.year || parseInt((data.birth_solar || data.birth_input || '2000').substring(0, 4)) || 2000
      const currentAge = nowYear - birthYear + 1
      const qiAge = data.qi_yun_age || 7
      if (currentAge <= qiAge) {
        activeYunType.value = 'xiaoyun'
        const xyList = (data.xiao_yun || []).filter(xy => xy.age <= qiAge)
        for (let i = 0; i < xyList.length; i++) {
          if (xyList[i].age === currentAge) { selDaYunIdx.value = i; break }
        }
        if (selDaYunIdx.value < 0 && xyList.length > 0) selDaYunIdx.value = 0
      } else {
        activeYunType.value = 'dayun'
        const filteredDyList = dyList.filter(dy => dy.gan || dy.zhi).slice(0, 10)
        for (let i = 0; i < filteredDyList.length; i++) {
          const sy = filteredDyList[i].start_year
          const ey = filteredDyList[i].end_year
          if (sy && ey && nowYear >= sy && nowYear <= ey) { selDaYunIdx.value = i; break }
        }
        if (selDaYunIdx.value < 0 && filteredDyList.length > 0) selDaYunIdx.value = 0
      }
      const lnList = data.liu_nian || []
      selLiuNianIdx.value = -1
      const fLnInit = filteredLiuNian.value
      for (let i = 0; i < fLnInit.length; i++) {
        const ly = typeof fLnInit[i].year === 'string' ? parseInt(fLnInit[i].year) : fLnInit[i].year
        if (ly === nowYear || fLnInit[i].current) { selLiuNianIdx.value = i; break }
      }
      if (selLiuNianIdx.value < 0 && fLnInit.length) selLiuNianIdx.value = 0
      var _initLyYear = nowYear
      var _initLnList = data.liu_nian || []
      for (var _li = 0; _li < _initLnList.length; _li++) {
        var _ly = typeof _initLnList[_li].year === 'string' ? parseInt(_initLnList[_li].year) : _initLnList[_li].year
        if (_ly === nowYear || _initLnList[_li].current) { _initLyYear = _ly; break }
      }
      var _initLmResult = computeLiuYueList(_initLyYear)
      if (currentYunPhase.value === 'xiaoyun') {
        var _qiAgeInit = data.qi_yun_age || 7
        var _xyListInit = (data.xiao_yun || []).filter(xy => xy.age <= _qiAgeInit)
        if (_xyListInit.length > 0) {
          var _lastXyYearInit = birthYear + _xyListInit[_xyListInit.length - 1].age - 1
          if (_initLyYear === _lastXyYearInit) {
            var _maxM = getQiYunMaxLiuYue(data)
            if (_maxM > 0 && _maxM < 12) {
              _initLmResult = _initLmResult.slice(0, _maxM)
            }
          }
        }
      }
      proLiuYue.value = _initLmResult
      selLiuYueIdx.value = 0
      var _initLmList = proLiuYue.value
      var nowMonth = new Date().getMonth() + 1
      for (var _mi = 0; _mi < _initLmList.length; _mi++) {
        if (_initLmList[_mi].month_num === nowMonth || _initLmList[_mi].current) { selLiuYueIdx.value = _mi; break }
      }
      if (selDaYunIdx.value < 0 && dyList.length > 1) selDaYunIdx.value = 1
      nextTick(() => {
        renderYunItemsDOM()
      })
      // 如果当前tab是专业排盘，立即加载wz-pro数据
      if (activeTab.value === 'wzpro') {
        loadWzProData()
      }
    } else {
      errorMsg.value = (data && data.error) || '排盘失败'
    }
  } catch (e) {
    errorMsg.value = '网络错误：' + (e.message || e.errMsg || '请稍后重试')
  } finally {
    loading.value = false
  }
})







</script>

<style scoped>

.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }
.page-wrap { position: relative; z-index: 1; }

/* 结果容器 */
.result-container { max-width: var(--max-w); margin: 0 auto; padding: 16px 16px 48px; }
.agent-handoff-bar { margin: 0 0 14px; padding: 12px 14px; border-radius: 12px; border: 1px solid rgba(178,149,93,0.30); background: linear-gradient(135deg, rgba(178,149,93,0.13), rgba(110,195,135,0.08)); display: flex; align-items: center; justify-content: space-between; gap: 14px; box-sizing: border-box; }
.agent-handoff-title { display: block; color: var(--text-1); font-size: 0.9rem; font-weight: 700; letter-spacing: 0.5px; }
.agent-handoff-sub { display: block; color: var(--text-3); font-size: 0.72rem; margin-top: 2px; line-height: 1.45; }
.agent-handoff-btn { flex: 0 0 auto; padding: 8px 18px; border-radius: 999px; color: #fff; background: linear-gradient(135deg, #9a6b2f, #c49a46); font-size: 0.82rem; font-weight: 700; cursor: pointer; box-shadow: 0 8px 18px rgba(154,107,47,0.20); }

/* 加载/错误状态 */
.loading-state { text-align: center; padding: 80px 20px; color: var(--text-3); }
.loading-spinner { display: inline-block; width: 40px; height: 40px; border: 3px solid var(--card-border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }
.error-state { text-align: center; padding: 60px 20px; color: var(--danger); }
.error-state .error-icon { font-size: 3rem; margin-bottom: 12px; }
.error-state .error-msg { font-size: 0.9375rem; margin-bottom: 20px; }
.btn-retry { display: inline-block; padding: 10px 28px; border-radius: 10px; font-size: 0.875rem; background: var(--accent); color: #fff; border: none; cursor: pointer; }

/* Tab布局 */
.tab-layout { display: flex; gap: 0; margin-top: 8px; }
.tab-sidebar { width: 100px; flex-shrink: 0; display: flex; flex-direction: column; gap: 2px; }
.tab-btn { display: flex; align-items: center; gap: 6px; padding: 14px 12px; border: none; cursor: pointer; font-size: 0.85rem; font-weight: 500; color: var(--text-3); background: var(--sidebar-bg); border-radius: var(--radius-md) 0 0 var(--radius-md); transition: all 0.25s var(--ease); text-align: left; border: 1px solid transparent; border-right: none; position: relative; }
.tab-btn.active { color: var(--accent); background: var(--card-bg); border-color: var(--card-border); border-right-color: var(--card-bg); font-weight: 700; z-index: 2; }
.tab-return-btn {
  margin-top: 10px;
  color: var(--text-2);
  background: rgba(255,255,255,0.18);
  border: 1px solid var(--card-border);
  border-right: 1px solid var(--card-border);
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  justify-content: center;
  -webkit-backdrop-filter: blur(14px) saturate(140%);
  backdrop-filter: blur(14px) saturate(140%);
}
.tab-return-btn:hover {
  color: var(--accent);
  background: var(--accent-glow);
  border-color: rgba(178,149,93,0.36);
}
.tab-content-area { flex: 1; min-width: 0; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 0 var(--radius-md) var(--radius-md) var(--radius-md); overflow: visible; }
.tab-panel { display: none; padding: 20px; animation: fadeIn 0.3s var(--ease); }
.tab-panel.active { display: block; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

/* 基本信息Tab */
.basic-info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.basic-info-item { display: flex; align-items: baseline; gap: 6px; font-size: 0.85rem; padding: 4px 0; }
.basic-info-item.full-width { grid-column: 1 / -1; }
.basic-info-item .label { color: var(--text-3); white-space: nowrap; }
.basic-info-item .value { color: var(--text-1); font-weight: 500; }

/* 基本排盘Tab */
.basic-layout { display: flex; gap: 16px; }
.basic-left { flex: 1; min-width: 0; }
.basic-right { width: 280px; flex-shrink: 0; display: flex; flex-direction: column; gap: 12px; }

/* 四柱表格 */
.pillar-table-wrap { width: 100%; background: var(--section-alt); border-radius: 10px; border: 1px solid var(--card-border); overflow: hidden; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.pillar-row { display: flex; border-bottom: 1px solid var(--card-border); }
.pillar-row:last-child { border-bottom: none; }
.pillar-row.header-row .pillar-cell { color: var(--accent); font-size: 0.85rem; font-weight: 700; background: rgba(178,149,93,0.06); }
.pillar-cell { flex: 1; padding: 8px 4px; text-align: center; vertical-align: middle; line-height: 1.5; border-right: 1px solid var(--card-border); }
.pillar-cell:last-child { border-right: none; }
.pillar-cell.label-cell { flex: 0 0 52px; max-width: 52px; color: var(--text-3); font-size: 0.76rem; font-weight: 500; background: rgba(178,149,93,0.06); white-space: nowrap; }
.pillar-header { font-size: 0.85rem; font-weight: 700; color: var(--accent); }
.pillar-cell.gan-cell { font-size: 1.45rem; font-weight: 700; color: var(--text-1); }
.pillar-cell.zhi-cell { font-size: 1.45rem; font-weight: 700; color: var(--text-1); }
.pillar-cell.cang-gan-cell { font-size: 0.82rem; color: var(--text-2); display: flex; flex-direction: column; align-items: center; gap: 2px; }
.cg-wx-text { display: flex; align-items: baseline; gap: 1px; }
.cg-wx-label { font-size: 0.6rem; color: var(--text-3); }
.pillar-cell.nayin-cell { font-size: 0.76rem; color: var(--text-3); }
.pillar-cell.shensha-cell { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; font-size: 0.7rem; color: var(--text-3); }
.ss-tag { display: inline-block; padding: 1px 5px; margin: 1px; border-radius: 6px; background: var(--tag-bg); border: 1px solid var(--card-border); font-size: 0.66rem; color: var(--tag-text); }
.ss-full-text { font-size: 0.72rem; font-weight: 600; display: block; line-height: 1.4; text-align: center; }
.ss-vertical { display: block; margin: 1px 0; }
.pillar-cell.zhuxing-cell { display: flex; align-items: center; justify-content: center; min-height: 1.8em; }
.pillar-cell.fuxing-cell { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px; min-height: 1.8em; }

/* 信息卡片 */
.info-card { background: var(--section-alt); border-radius: 10px; padding: 12px; border: 1px solid var(--card-border); }
.info-card .card-title { font-size: 0.8rem; font-weight: 700; color: var(--text-1); margin-bottom: 8px; font-family: var(--font-serif); }
.info-card .card-content { font-size: 0.78rem; color: var(--text-2); line-height: 1.6; }

/* 五行统计条 */
.wx-bar { display: flex; align-items: center; gap: 6px; margin: 3px 0; }
.wx-bar .wx-name { width: 20px; font-weight: 700; text-align: center; }
.wx-bar .wx-track { flex: 1; height: 6px; background: var(--card-border); border-radius: 3px; overflow: hidden; }
.wx-bar .wx-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
.wx-bar .wx-count { width: 18px; font-weight: 600; text-align: right; font-size: 0.76rem; }

/* 命理信息行 */
.mingli-row { display: flex; align-items: baseline; gap: 6px; padding: 5px 0; border-bottom: 1px solid var(--card-border); }
.mingli-row:last-child { border-bottom: none; }
.mingli-row .ml-label { font-size: 0.74rem; color: var(--text-3); width: 48px; flex-shrink: 0; text-align: right; font-weight: 600; }
.mingli-row .ml-value { font-size: 0.84rem; color: var(--text-1); font-weight: 600; }
.mingli-row .ml-sub { font-size: 0.72rem; color: var(--text-3); margin-left: 4px; }

/* 称骨 */
.chenggu-weight { font-weight: 700; color: var(--accent); font-size: 0.84rem; display: block; }
.chenggu-bar-track { width: 100%; height: 8px; background: var(--card-border); border-radius: 4px; overflow: hidden; margin: 6px 0 8px; }
.chenggu-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--accent-2), var(--accent)); transition: width 0.6s var(--ease); }
.chenggu-poem { font-size: 0.7rem; color: var(--text-3); line-height: 1.5; white-space: pre-wrap; }

/* 底部声明 */
.disclaimer { text-align: center; font-size: 0.78rem; color: var(--text-3); margin-top: 16px; padding: 12px; }

/* 笔记 */
.note-tag-btn { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 20px; border: 1px solid var(--card-border); background: var(--tag-bg); color: var(--text-2); font-size: 0.76rem; cursor: pointer; transition: 0.2s; }
.note-item { padding: 12px; border-radius: 10px; background: var(--section-alt); border: 1px solid var(--card-border); }
.note-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.note-tag { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 500; }
.note-time { font-size: 0.7rem; color: var(--text-3); }
.note-text { font-size: 0.84rem; color: var(--text-1); line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.note-actions { margin-top: 8px; display: flex; gap: 8px; justify-content: flex-end; }
.note-action-btn { padding: 2px 8px; border-radius: 6px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.72rem; cursor: pointer; }

/* 弹窗 */
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

/* ═══ 专业排盘（问真风格1:1复刻） ═══ */
.mainColor { color: var(--accent); font-weight: 500; }
.wzpro-wrap { font-size: 0.875rem; }

/* 顶部信息栏 */
.wz-top-bar { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-radius: 10px; margin-bottom: 10px; background: linear-gradient(135deg, rgba(178,149,93,0.08) 0%, rgba(178,149,93,0.03) 100%); border: 1px solid rgba(178,149,93,0.15); }
.wz-case-info { display: flex; align-items: center; gap: 10px; }
.wz-top-actions { display: flex; align-items: center; gap: 8px; }
.tms-toggle { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 14px; font-size: 0.72rem; cursor: pointer; border: 1px solid var(--card-border); color: var(--text-3); transition: all 0.2s; }
.tms-toggle:active { transform: scale(0.95); }
.tms-toggle.active { background: var(--accent-glow); border-color: var(--accent); color: var(--accent); }
.toggle-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--text-3); }
.tms-toggle.active .toggle-dot { background: var(--accent); }
.layout-toggle { font-size: 0.68rem; }
.layout-icon { font-size: 0.82rem; }

/* 胎命身横排 */
.wz-tms-bar { display: flex; align-items: center; gap: 16px; padding: 10px 16px; border-radius: 8px; margin-bottom: 10px; background: var(--section-alt); border: 1px solid var(--card-border); flex-wrap: wrap; }
.wz-tms-item { display: flex; align-items: center; gap: 6px; }
.wz-tms-label { font-size: 0.72rem; color: var(--text-3); font-weight: 500; white-space: nowrap; }
.wz-tms-value { font-size: 0.88rem; font-weight: 600; }
.wz-tms-sub { font-size: 0.62rem; color: var(--text-3); }

/* 起运摘要栏 */
.wz-summary-bar { display: flex; align-items: center; justify-content: space-between; padding: 8px 14px; border-radius: 8px; margin-bottom: 10px; background: var(--section-alt); border: 1px solid var(--card-border); flex-wrap: wrap; gap: 8px; }
.wz-qiyun-text { font-size: 0.78rem; color: var(--text-2); font-weight: 600; }
.wz-qiyun-extra { font-size: 0.68rem; color: var(--text-3); margin-top: 2px; }
.wz-wx-bar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.wz-wx-item { display: flex; align-items: center; gap: 3px; font-size: 0.78rem; font-weight: 600; }
.wx-dot { width: 8px; height: 8px; border-radius: 50%; }
.wx-jin { background: #f0c040; }
.wx-mu { background: #4caf50; }
.wx-shui { background: #2196f3; }
.wx-huo { background: #f44336; }
.wx-tu { background: #9c6b30; }
.wz-wx-lack { font-size: 0.72rem; color: var(--danger); font-weight: 600; }
.wz-geju-info { display: flex; align-items: center; gap: 6px; }
.wz-ws-tag { font-size: 0.72rem; padding: 2px 8px; border-radius: 10px; background: rgba(178,149,93,0.15); color: var(--accent); font-weight: 600; }
.wz-geju-tag { font-size: 0.72rem; padding: 2px 8px; border-radius: 10px; background: rgba(46,131,246,0.12); color: var(--info); font-weight: 600; }

/* 排盘主布局 */
.wz-pan-layout { display: flex; gap: 10px; margin-bottom: 10px; }
.wz-pan-left { flex: 1; min-width: 0; overflow: hidden; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); }
.wz-pan-table-inner { width: 100%; min-width: 0; }
.wz-pan-right { width: 380px; flex-shrink: 0; display: flex; flex-direction: column; gap: 10px; overflow-y: auto; border-left: 1px solid var(--card-border); padding-left: 10px; }

.wz-row { display: flex; align-items: stretch; min-height: 28px; border-bottom: 1px solid var(--card-border); width: 100%; }
.wz-row:last-child { border-bottom: none; }
.wz-row.header-row .wz-row-item { color: var(--accent); font-size: 0.72rem; font-weight: 700; background: var(--section-alt); }
.wz-row-item { flex: 1 1 0%; display: flex; align-items: center; justify-content: center; font-size: 0.82rem; padding: 3px 2px; position: relative; transition: background 0.15s; min-width: 0; overflow: hidden; }
.wz-row-item:last-child { border-right: none; }
.wz-row-item.wz-pro-sep { border-left: 2px solid var(--card-border); }
.wz-row-item.label-cell { flex: 0 0 48px; max-width: 48px; min-width: 48px; padding: 0 !important; box-sizing: border-box; color: var(--text-3); font-size: 0.72rem; font-weight: 600; background: var(--section-alt); border-right: 1px solid var(--card-border); }

.wz-row.wz-tg-row .wz-row-item:not(.label-cell) { font-size: 1.2rem; font-weight: 700; padding: 6px 0; }
.wz-row.wz-tg-row { border-bottom: none; }
.wz-row.wz-dz-row .wz-row-item:not(.label-cell) { font-size: 1.2rem; font-weight: 700; padding: 8px 0; }
.wz-row.wz-cg-row { background: var(--section-alt); }
.wz-row.wz-cg-row .wz-row-item { flex-direction: column; gap: 1px; font-size: 0.68rem; }
.wz-cg-wrap { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.wz-cg-item { display: flex; align-items: center; gap: 1px; line-height: 1.5; white-space: nowrap; }
.wz-cg-ss { font-size: 0.56rem; color: var(--text-3); }
.wz-cg-wx { font-size: 0.52rem; color: var(--text-3); opacity: 0.7; }
.wz-row.wz-fuxing-row { background: var(--section-alt); }
.wz-row.wz-fuxing-row .wz-row-item { flex-direction: column; gap: 2px; font-size: 0.56rem; }
.wz-row.wz-siling-row { background: var(--section-alt); }
.wz-siling-text { font-size: 0.68rem; color: var(--accent); font-weight: 600; }
.wz-canggan-item { display: flex; align-items: center; gap: 2px; line-height: 1.4; }
.wz-canggan-ss { font-size: 0.56rem; color: var(--text-3); }
.info-tag { font-size: 0.78rem; padding: 2px 8px; border-radius: 6px; background: var(--tag-bg); color: var(--text-2); border: 1px solid var(--card-border); }
/* 神煞分割行 */
.wz-ss-division { height: 8px; background: var(--section-alt); }
/* 天干留意/地支留意行 */
.wz-row.guanxi-row { background: var(--section-alt); }
.wz-row.guanxi-row .wz-row-item.label-cell { background: transparent; font-size: 0.66rem; color: var(--accent); font-weight: 600; align-items: flex-start; padding-top: 5px; }
.wz-guanxi-cell { flex: 1 !important; border-right: none !important; text-align: left !important; justify-content: flex-start !important; padding: 4px 8px !important; flex-wrap: wrap; gap: 2px 10px; }
.wz-guanxi-text { font-size: 0.68rem; line-height: 1.6; color: var(--text-2); }
/* 神煞行 */
.wz-row.ss-row .wz-row-item { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; font-size: 0.62rem; line-height: 1.5; padding: 4px 1px; }
.wz-ss-tag { display: inline-block; padding: 0 3px; margin: 0 1px; border-radius: 3px; background: var(--tag-bg); border: 1px solid var(--card-border); font-size: 0.52rem; color: var(--tag-text); line-height: 1.4; }
.wz-ss-tag.ji-shen { border-color: var(--card-border); background: var(--tag-bg); color: var(--text-1); }
.wz-ss-tag.xiong-sha { border-color: var(--card-border); background: var(--tag-bg); color: var(--text-1); }

/* 日主高亮 */
.wz-day-master-gan { position: relative; text-shadow: 0 0 8px var(--accent-glow); }

/* 右侧面板 - 大运/小运切换 */
.wz-yun-section { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); }
.wz-yun-title { padding: 8px 12px; font-size: 0.74rem; font-weight: 700; color: var(--accent); background: var(--accent-glow); border-bottom: 1px solid var(--card-border); display: flex; align-items: center; gap: 4px; }
.wz-today-btn { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 4px; background: var(--accent); color: #fff; font-size: 0.68rem; font-weight: 700; cursor: pointer; margin-left: auto; transition: all 0.2s; border: 1px solid var(--accent); line-height: 1; }
.wz-yun-switch-tabs { display: flex; border-bottom: 1px solid var(--card-border); background: var(--accent-glow); }
.wz-yun-tab { flex: 1; text-align: center; padding: 8px 12px; font-size: 0.74rem; font-weight: 700; cursor: pointer; color: var(--text-3); transition: all 0.2s; border-bottom: 2px solid transparent; }
.wz-yun-tab.active { color: var(--accent); border-bottom-color: var(--accent); background: var(--card-bg); }
.wz-yun-items-wrap { position: relative; padding: 0; }
.wz-yun-items { display: flex; flex-wrap: nowrap; gap: 0; overflow-x: auto; overflow-y: hidden; -webkit-overflow-scrolling: touch; position: relative; scrollbar-width: none; -ms-overflow-style: none; touch-action: pan-x; overscroll-behavior-x: contain; overscroll-behavior-y: none; }
.wz-yun-items::-webkit-scrollbar { display: none; }
.wz-yun-item { display: flex; flex-direction: column; align-items: center; padding: 8px 4px; min-width: 48px; flex: 0 0 auto; cursor: pointer; transition: background 0.15s; gap: 2px; min-height: 72px; justify-content: center; box-sizing: border-box; scroll-snap-align: start; }
.wz-yun-item:hover { background: var(--accent-glow); }
.wz-yun-item.wz-active { background: var(--dayun-active); }
.wz-yun-item.wz-current { background: var(--accent-glow); }
.wz-yun-item-year { font-size: 0.62rem; color: var(--text-3); }
.wz-yun-item-age { font-size: 0.52rem; color: var(--text-3); margin-top: 1px; }
.wz-yun-item-month { font-size: 0.62rem; color: var(--text-3); font-weight: 500; }
.wz-yun-item-date { font-size: 0.48rem; color: var(--text-3); }
.wz-yun-item-gz { font-size: 0.88rem; font-weight: 700; color: var(--text-1); font-family: var(--font-serif); }
.wz-yun-item.wz-active .wz-yun-item-gz { color: var(--accent); }
.wz-yun-item-ss { font-size: 0.52rem; color: var(--text-3); }
.wz-yun-item-age-label { font-size: 0.48rem; color: var(--text-3); margin-top: 1px; white-space: nowrap; }

/* 起运信息 */
.wz-qiyun-section { padding: 8px 10px; font-size: 0.72rem; color: var(--text-2); border-bottom: 1px solid var(--card-border); text-align: left; line-height: 1.6; }

/* 五行旺度条 */
.wz-wuxing-bar { background: transparent; border-radius: 6px; padding: 8px 12px; display: flex; align-items: center; justify-content: center; gap: 10px; font-size: 0.78rem; font-weight: 500; flex-wrap: wrap; }
.wz-wuxing-item { padding: 3px 10px; border-radius: 6px; font-weight: 500; display: inline-flex; align-items: center; gap: 2px; }
.wz-wuxing-item b { font-weight: 700; }

/* 干支留意盒子 */
.wz-guanxi-box { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); overflow: hidden; margin-bottom: 10px; }
.wz-guanxi-box-title { display: flex; align-items: center; gap: 6px; padding: 8px 12px; font-size: 0.78rem; font-weight: 700; color: var(--accent); background: var(--accent-glow); border-bottom: 1px solid var(--card-border); font-family: var(--font-serif); }
.wz-guanxi-box-icon { font-size: 0.88rem; }
.wz-guanxi-box-body { padding: 10px 12px; display: flex; flex-wrap: wrap; gap: 8px 20px; align-items: center; }
.wz-guanxi-item { display: flex; align-items: baseline; gap: 8px; }
.wz-guanxi-label { flex-shrink: 0; font-size: 0.72rem; font-weight: 700; color: var(--text-3); }
.wz-guanxi-text { font-size: 0.72rem; color: var(--text-2); }
.wz-guanxi-wx-row { display: flex; align-items: center; gap: 8px; }
.wz-guanxi-wx-items { display: flex; gap: 6px; }
.wz-guanxi-wx-tag { font-size: 0.72rem; color: var(--text-2); background: var(--tag-bg); border: 1px solid var(--card-border); border-radius: 5px; padding: 2px 7px; }
.wz-guanxi-wx-tag text { font-weight: 700; color: var(--accent); margin-left: 2px; }
.wz-guanxi-lack { font-size: 0.68rem; color: var(--danger); margin-left: 4px; }
.wz-guanxi-ws-tag { font-size: 0.72rem; font-weight: 700; padding: 2px 10px; border-radius: 5px; color: var(--info); background: rgba(46,131,246,0.12); border: 1px solid rgba(46,131,246,0.25); }
.wz-guanxi-geju-tag { font-size: 0.72rem; font-weight: 700; padding: 2px 10px; border-radius: 5px; color: var(--success); background: rgba(7,233,48,0.10); border: 1px solid rgba(7,233,48,0.22); }

/* 冲合关系 */
.wz-relation-section { margin-top: 10px; }
.wz-relation-title { font-size: 0.82rem; font-weight: 700; color: var(--accent); font-family: var(--font-serif); margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }
.wz-relation-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.wz-relation-tag { padding: 2px 8px; border-radius: 6px; font-size: 0.7rem; background: var(--section-alt); border: 1px solid; font-weight: 500; }

/* 旺相休囚死标签 */
.wxxs-tag { font-size: 0.72rem; padding: 3px 10px; border-radius: 14px; border: 1px solid var(--card-border); background: var(--tag-bg); color: var(--text-2); }
.wx-wang { border-color: #4a8c5c; color: #4a8c5c; background: rgba(74,140,92,0.08); }
.wx-xiang { border-color: #2e83f6; color: #2e83f6; background: rgba(46,131,246,0.08); }
.wx-xiu { border-color: #ef9104; color: #ef9104; background: rgba(239,145,4,0.08); }
.wx-qiu { border-color: #8b6d03; color: #8b6d03; background: rgba(139,109,3,0.08); }
.wx-si { border-color: #d30505; color: #d30505; background: rgba(211,5,5,0.08); }
.wz-pro-bottom-info { display: flex; flex-direction: column; gap: 8px; }
.wz-pro-bottom-card { background: var(--section-alt); border-radius: 10px; padding: 12px 16px; border: 1px solid var(--card-border); }
.wz-pro-bottom-card-title { font-size: 0.78rem; font-weight: 700; color: var(--text-1); margin-bottom: 8px; }

/* 格局/用神等 */
.wz-extra-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.wz-extra-card { background: var(--section-alt); border-radius: 10px; padding: 12px 16px; border: 1px solid var(--card-border); }
.wz-extra-title { font-size: 0.72rem; color: var(--text-3); font-weight: 600; display: block; margin-bottom: 4px; }
.wz-extra-val { font-size: 0.9rem; font-weight: 600; display: block; margin-bottom: 4px; }
.wz-extra-desc { font-size: 0.68rem; color: var(--text-3); line-height: 1.5; display: block; }

/* 性格分析/古籍等区块卡片 */
.wz-section-card { background: var(--section-alt); border-radius: 10px; padding: 14px 18px; border: 1px solid var(--card-border); margin-top: 10px; }
.wz-section-title { font-size: 0.85rem; font-weight: 700; color: var(--accent); display: block; margin-bottom: 10px; font-family: var(--font-serif); letter-spacing: 1px; }
.wz-section-body { font-size: 0.78rem; color: var(--text-2); line-height: 1.7; }
.wz-section-text { display: block; margin-bottom: 8px; }
.wz-trait-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.wz-trait-tag { padding: 3px 10px; border-radius: 14px; font-size: 0.72rem; background: var(--tag-bg); border: 1px solid var(--card-border); color: var(--accent); }
.wz-personality-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }
.wz-p-item { padding: 6px 10px; border-radius: 8px; background: rgba(178,149,93,0.06); }
.wz-p-label { font-size: 0.68rem; color: var(--accent); font-weight: 600; display: block; margin-bottom: 2px; }
.wz-p-text { font-size: 0.72rem; color: var(--text-2); line-height: 1.5; }
.wz-guji-item { padding: 10px 0; border-bottom: 1px solid var(--card-border); }
.wz-guji-item:last-child { border-bottom: none; }
.wz-guji-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }
.wz-guji-title { font-size: 0.78rem; font-weight: 600; }
.wz-guji-match { font-size: 0.62rem; color: var(--text-3); padding: 1px 6px; border-radius: 8px; background: var(--tag-bg); }
.wz-guji-text { font-size: 0.72rem; color: var(--text-3); line-height: 1.6; }

/* 响应式 */
@media (max-width: 768px) {
  .tab-layout { flex-direction: column; }
  .tab-sidebar { width: 100%; flex-direction: row; gap: 0; overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .tab-btn { border-radius: var(--radius-md) var(--radius-md) 0 0; padding: 10px 16px; white-space: nowrap; border-right: 1px solid var(--card-border); border-bottom: none; justify-content: center; }
  .tab-return-btn { margin-top: 0; margin-left: 8px; border-radius: var(--radius-md) var(--radius-md) 0 0; }
  .tab-btn.active { border-color: var(--card-border); border-bottom-color: var(--card-bg); }
  .tab-content-area { border-radius: 0 0 var(--radius-md) var(--radius-md); }
  .basic-layout { flex-direction: column; }
  .basic-right { width: 100%; }
  .pillar-cell { padding: 6px 2px; }
  .pillar-cell.gan-cell, .pillar-cell.zhi-cell { font-size: 1.2rem; }
  .pillar-cell.cang-gan-cell { font-size: 0.74rem; }
  .pillar-cell.nayin-cell { font-size: 0.68rem; }
  .pillar-cell.shensha-cell { font-size: 0.64rem; }
  .wz-pan-layout { flex-direction: column; }
  .wz-pan-right { width: 100%; border-left: none; padding-left: 0; border-top: 1px solid var(--card-border); padding-top: 10px; }
  .wz-extra-grid { grid-template-columns: 1fr; }
  .wz-row-item.label-cell { flex: 0 0 40px; max-width: 40px; min-width: 40px; font-size: 0.68rem; }
  .wz-row-item { min-width: 0; font-size: 0.68rem; }
  .wz-row.wz-tg-row .wz-row-item:not(.label-cell), .wz-row.wz-dz-row .wz-row-item:not(.label-cell) { font-size: 0.95rem; }
}
@media (max-width: 640px) {
  .result-container { padding: 8px 8px 36px; }
  .agent-handoff-bar { align-items: stretch; flex-direction: column; gap: 10px; }
  .agent-handoff-btn { text-align: center; }
  .tab-panel { padding: 12px; }
  .pillar-cell.gan-cell, .pillar-cell.zhi-cell { font-size: 1.05rem; }
  .pillar-cell.label-cell { flex: 0 0 40px; max-width: 40px; font-size: 0.68rem; }
  .wz-row-item { min-width: 44px; font-size: 0.68rem; }
  .wz-row-item.label-cell { flex: 0 0 40px; max-width: 40px; min-width: 40px; padding: 0 !important; }
  .wz-row.wz-tg-row .wz-row-item, .wz-row.wz-dz-row .wz-row-item { font-size: 0.95rem; }
  .wz-tms-bar { gap: 8px; }
  .wz-tms-item { gap: 3px; }
  .wz-top-bar { flex-wrap: wrap; gap: 8px; }
}
@media (max-width: 480px) {
  .pillar-cell.label-cell { flex: 0 0 36px; max-width: 36px; font-size: 0.6rem; }
  .wz-pan-table-inner { min-width: auto !important; }
  .wz-row-item { min-width: 0; font-size: 0.55rem; padding: 2px 1px; flex: 1; }
  .wz-row-item.label-cell { flex: 0 0 24px; max-width: 24px; min-width: 24px; font-size: 0.52rem; padding: 0 !important; }
  .wz-row.wz-tg-row .wz-row-item:not(.label-cell), .wz-row.wz-dz-row .wz-row-item:not(.label-cell) { font-size: 0.9rem; padding: 4px 0; }
  .wz-pro-sep { border-left-width: 1px !important; }
  .wz-row.ss-row .wz-row-item { gap: 1px; padding: 2px 0; }
  .wz-ss-tag { font-size: 0.45rem; padding: 0 2px; margin: 0; }
  .ss-tag { font-size: 0.5rem; padding: 0 3px; }
  .wz-yun-item { min-width: 0; flex: 1; padding: 4px 1px; font-size: 0.6rem; min-height: 52px; }
  .wz-cg-item { font-size: 0.55rem; }
}
.riZhu-strength { margin-top: 12px; padding: 12px; background: var(--section-alt); border-radius: 10px; border: 1px solid var(--card-border); }
.riZhu-strength .strength-label { font-size: 0.78rem; font-weight: 700; color: var(--text-1); margin-bottom: 8px; }
.strength-bar-track { width: 100%; height: 10px; border-radius: 5px; overflow: hidden; background: var(--card-border); position: relative; }
.strength-bar-fill { height: 100%; border-radius: 5px; transition: width 0.6s var(--ease); position: absolute; left: 0; top: 0; }
.strength-bar-fill.yin-bi { background: linear-gradient(90deg, #07e930, #4CAF50); }
.strength-legend { display: flex; justify-content: space-between; margin-top: 6px; font-size: 0.7rem; color: var(--text-3); }
.legend-item { display: flex; align-items: center; gap: 4px; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; }
</style>
