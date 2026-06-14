<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :isLoggedIn="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- ==================== 头部信息栏 ==================== -->
      <view class="header-container">
        <view class="header-avatar">{{ baziData.shengxiao || '' }}</view>
        <view class="header-username" style="font-size:25px;">{{ baziData.name || '' }}</view>
        <view class="header-calendar columnFlex">
          <view class="header-calendar-text">
            <text>阴历：{{ baziData.lunar_date || '' }} </text>
            <text class="mainColor">（{{ baziData.gender_label || '' }}）</text>
          </view>
          <view class="header-calendar-text">阳历：{{ baziData.solar_date || '' }}</view>
        </view>
        <view class="header-tms">胎命身</view>
        <view class="header-edit">✎</view>
      </view>

      <!-- ==================== 专业细盘主内容 ==================== -->
      <view class="pro-pan-content">
        <!-- ====== 左侧排盘表 ====== -->
        <view class="pro-pan-content-left">
          <view class="pro-pan-content-table">
            <!-- 标题行 -->
            <view class="pro-pan-row">
              <view class="pro-pan-row-item label-cell">日期</view>
              <view v-for="(label, i) in colLabels" :key="'h'+i" class="pro-pan-row-item paipanTitleColor" :class="{ shadowBoder: i < 6 }">{{ label }}</view>
            </view>
            <!-- 数据行 -->
            <view v-for="row in panRows" :key="row.key" class="pro-pan-row" :class="row.cls">
              <view class="pro-pan-row-item label-cell">{{ row.label }}</view>
              <template v-for="(col, i) in colKeys" :key="row.key+i">
                <view class="pro-pan-row-item" :class="{ shadowBoder: i < 6, columnFlex: row.key === 'cg' || row.key === 'ss' }">
                  <!-- 天干 -->
                  <template v-if="row.key === 'tg'">
                    <text :class="wxClass(getSizhuCol(col).tg)">{{ getSizhuCol(col).tg || '' }}</text>
                  </template>
                  <!-- 地支 -->
                  <template v-else-if="row.key === 'dz'">
                    <text :class="wxClass(getSizhuCol(col).dz)">{{ getSizhuCol(col).dz || '' }}</text>
                  </template>
                  <!-- 主星 -->
                  <template v-else-if="row.key === 'ss'">
                    <text>{{ getSizhuCol(col).ss || '' }}</text>
                  </template>
                  <!-- 藏干 -->
                  <template v-else-if="row.key === 'cg'">
                    <view class="canggan-wrap">
                      <view v-for="(cgItem, ci) in (getSizhuCol(col).canggan || [])" :key="ci" class="canggan-item">
                        <text :class="wxClass(cgItem.gz)">{{ cgItem.gz }}</text>
                        <text class="canggan-shishen">{{ cgItem.ss }}</text>
                      </view>
                    </view>
                  </template>
                  <!-- 星运 -->
                  <template v-else-if="row.key === 'xy'">
                    <text>{{ getSizhuCol(col).xingyun || '' }}</text>
                  </template>
                  <!-- 自坐 -->
                  <template v-else-if="row.key === 'zz'">
                    <text>{{ getSizhuCol(col).zizuo || '' }}</text>
                  </template>
                  <!-- 空亡 -->
                  <template v-else-if="row.key === 'kw'">
                    <text>{{ getSizhuCol(col).kongwang || '' }}</text>
                  </template>
                  <!-- 纳音 -->
                  <template v-else-if="row.key === 'ny'">
                    <text>{{ getSizhuCol(col).nayin || '' }}</text>
                  </template>
                </view>
              </template>
            </view>
            <!-- 神煞分割线 -->
            <view class="shensha_division"></view>
            <!-- 神煞行 -->
            <view class="pro-pan-row ss-row">
              <view class="pro-pan-row-item label-cell">神煞</view>
              <template v-for="(col, i) in colKeys" :key="'ss'+i">
                <view class="pro-pan-row-item columnFlex" :class="{ shadowBoder: i < 6 }">
                  <text v-for="(ssItem, si) in (getSizhuCol(col).shensha || [])" :key="si" class="shensha-tag">{{ ssItem }}</text>
                </view>
              </template>
            </view>
          </view>
        </view>

        <!-- ====== 右侧面板 ====== -->
        <view class="pro-pan-content-right">
          <view class="pro-pan-content-bg">
            <!-- 起运信息 -->
            <view class="pro-pan-qiyun">
              <text>起运： {{ baziData.qiyun_info || '' }} &nbsp;&nbsp; 交运： {{ baziData.jiaoyun_text || '' }}</text>
              <text v-if="baziData.jiaoyun_info" class="pro-pan-qiyun-extra">{{ baziData.jiaoyun_info || '' }}</text>
            </view>
            <!-- 大运 -->
            <view class="pro-pan-yun">
              <view class="pro-pan-yun-item yun-index">大运</view>
              <view class="pro-pan-yun-items">
                <view v-for="(item, idx) in (baziData.dayun_list || [])" :key="'dy'+idx" class="pro-pan-yun-item" :class="{ 'current-dayun': item.current }">
                  <text v-if="item.year" class="pro-pan-yun-item-small">{{ item.year }}</text>
                  <text v-if="item.age" class="pro-pan-yun-item-small" style="margin-top:4px;">{{ item.age }}</text>
                  <view v-if="item.tg" class="pro-pan-yun-item-label">
                    <text class="pro-pan-yun-item-text" :class="wxClass(item.tg)">{{ item.tg }}</text>
                    <text v-if="item.tgSs" class="pro-pan-yun-item-shishen">{{ item.tgSs }}</text>
                  </view>
                  <view v-if="item.dz" class="pro-pan-yun-item-label">
                    <text class="pro-pan-yun-item-text" :class="wxClass(item.dz)">{{ item.dz }}</text>
                    <text v-if="item.dzSs" class="pro-pan-yun-item-shishen">{{ item.dzSs }}</text>
                  </view>
                </view>
              </view>
            </view>
            <!-- 流年 -->
            <view class="pro-pan-yun">
              <view class="pro-pan-yun-item yun-index">流年</view>
              <view class="pro-pan-yun-items">
                <view v-for="(item, idx) in (baziData.liunian_list || [])" :key="'ln'+idx" class="pro-pan-yun-item" :class="{ 'current-dayun': item.current }">
                  <text v-if="item.year" class="pro-pan-yun-item-small">{{ item.year }}</text>
                  <view v-if="item.tg" class="pro-pan-yun-item-label">
                    <text class="pro-pan-yun-item-text" :class="wxClass(item.tg)">{{ item.tg }}</text>
                    <text v-if="item.tgSs" class="pro-pan-yun-item-shishen">{{ item.tgSs }}</text>
                  </view>
                  <view v-if="item.dz" class="pro-pan-yun-item-label">
                    <text class="pro-pan-yun-item-text" :class="wxClass(item.dz)">{{ item.dz }}</text>
                    <text v-if="item.dzSs" class="pro-pan-yun-item-shishen">{{ item.dzSs }}</text>
                  </view>
                </view>
              </view>
            </view>
            <!-- 小运 -->
            <view class="pro-pan-yun">
              <view class="pro-pan-yun-item yun-index">小运</view>
              <view class="pro-pan-yun-items">
                <view v-for="(item, idx) in (baziData.xiaoyun_list || [])" :key="'xy'+idx" class="pro-pan-yun-item" :class="{ 'current-dayun': item.current }">
                  <text v-if="item.year" class="pro-pan-yun-item-small">{{ item.year }}</text>
                  <text v-if="item.age" class="pro-pan-yun-item-small" style="margin-top:4px;">{{ item.age }}</text>
                  <view v-if="item.tg" class="pro-pan-yun-item-label">
                    <text class="pro-pan-yun-item-text" :class="wxClass(item.tg)">{{ item.tg }}</text>
                    <text v-if="item.tgSs" class="pro-pan-yun-item-shishen">{{ item.tgSs }}</text>
                  </view>
                  <view v-if="item.dz" class="pro-pan-yun-item-label">
                    <text class="pro-pan-yun-item-text" :class="wxClass(item.dz)">{{ item.dz }}</text>
                    <text v-if="item.dzSs" class="pro-pan-yun-item-shishen">{{ item.dzSs }}</text>
                  </view>
                </view>
              </view>
            </view>
            <!-- 流月 -->
            <view class="pro-pan-yun">
              <view class="pro-pan-yun-item yun-index">流月</view>
              <view class="pro-pan-yun-items">
                <view v-for="(item, idx) in (baziData.liuyue_list || [])" :key="'ly'+idx" class="pro-pan-yun-item" :class="{ 'current-dayun': item.current }">
                  <text v-if="item.jieqi || item.date" class="pro-pan-yun-item-small">{{ item.jieqi || '' }} {{ item.date || '' }}</text>
                  <view v-if="item.tg" class="pro-pan-yun-item-label">
                    <text class="pro-pan-yun-item-text" :class="wxClass(item.tg)">{{ item.tg }}</text>
                    <text v-if="item.tgSs" class="pro-pan-yun-item-shishen">{{ item.tgSs }}</text>
                  </view>
                  <view v-if="item.dz" class="pro-pan-yun-item-label">
                    <text class="pro-pan-yun-item-text" :class="wxClass(item.dz)">{{ item.dz }}</text>
                    <text v-if="item.dzSs" class="pro-pan-yun-item-shishen">{{ item.dzSs }}</text>
                  </view>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- ==================== 干支留意 ==================== -->
      <view class="sizhu-gztip">
        <view>天干留意：&nbsp; <text class="mainColor">{{ formatRelationList(baziData.tg_guanxi) }}</text></view>
        <view>地支留意：&nbsp; <text class="mainColor">{{ formatRelationList(baziData.dz_guanxi) }}</text></view>
      </view>

      <!-- ==================== 智能四柱图示 ==================== -->
      <view class="wzbz-box">
        <view class="wzbz_header">
          <view class="wzbz_header_title">智能四柱图示</view>
          <view class="wzbz_header_list">
            <view class="wzbz-header-btn" id="bzProTabLiutong" @tap="switchBzProTab('liutong')">干支流通</view>
            <view class="wzbz-header-btn" id="bzProTabGongwei" @tap="switchBzProTab('gongwei')">宫位</view>
            <view class="wzbz-header-btn" id="bzProTabLiuqin" @tap="switchBzProTab('liuqin')">六亲</view>
          </view>
        </view>
        <view class="wzbz_content">
          <rich-text v-if="baziData.wzbz_chart" :nodes="baziData.wzbz_chart"></rich-text>
          <view v-else style="padding:20px;color:#999;">（智能四柱图示区域 - 需配合排盘引擎渲染）</view>
        </view>
      </view>
    </view>




  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import TopNav from '@/components/TopNav.vue'

// ── 主题 ──
const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
function toggleTheme() { theme.value = theme.value === 'dark' ? 'light' : 'dark'; uni.setStorageSync('xc_theme', theme.value) }

// ── 登录状态 ──
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

// ── 智能四柱图示Tab ──
const wzbzTab = ref('liutong')
function switchBzProTab(tab) {
  wzbzTab.value = tab
  var ids = ['bzProTabLiutong','bzProTabGongwei','bzProTabLiuqin']
  var tabs = ['liutong','gongwei','liuqin']
  for (var i = 0; i < ids.length; i++) {
    var el = document.getElementById(ids[i])
    if (el) { tab === tabs[i] ? el.classList.add('active') : el.classList.remove('active') }
  }
}

// ========== 五行映射（与Flask原版零改动） ==========
const WX = {
  '甲': 'wood', '乙': 'wood', '寅': 'wood', '卯': 'wood',
  '丙': 'fire', '丁': 'fire', '巳': 'fire', '午': 'fire',
  '戊': 'soil', '己': 'soil', '辰': 'soil', '丑': 'soil', '未': 'soil', '戌': 'soil',
  '庚': 'gold', '辛': 'gold', '申': 'gold', '酉': 'gold',
  '壬': 'water', '癸': 'water', '亥': 'water', '子': 'water'
}

function wxClass(gz) {
  const w = WX[gz]
  return w ? w + 'Color' : ''
}

function relationLabel(desc) {
  const raw = String(desc || '').trim()
  const rawCompact = raw.replace(/\s+/g, '')
  const charSource = rawCompact.replace(/缺[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]+/g, '')
  const pair = charSource.match(/[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]/g) || []
  const pairText = pair.slice(0, 2).join('')
  const allText = pair.join('')
  const hePairOrder = ['甲己', '乙庚', '丙辛', '丁壬', '戊癸']
  const relationPairOrder = ['辰丑', '酉戌', '辰卯', '午卯', '巳亥', '辰戌', '丑戌']
  const orderedPair = (orders) => pair.length >= 2 && pair[0] !== pair[1] ? (orders.find(item => item.includes(pair[0]) && item.includes(pair[1])) || pairText) : pairText
  const hePairText = orderedPair(hePairOrder)
  const relationPairText = orderedPair(relationPairOrder)
  const juMap = { 子: '水局', 午: '火局', 卯: '木局', 酉: '金局' }
  const huiSets = [
    { zhis: '寅卯辰', ju: '木局' },
    { zhis: '巳午未', ju: '火局' },
    { zhis: '申酉戌', ju: '金局' },
    { zhis: '亥子丑', ju: '水局' },
  ]
  let m = rawCompact.match(/合化([木火土金水])/)
  if (m && pairText) return `${hePairText}合化${m[1]}`
  if (/六合|相合/.test(rawCompact) && pairText) return `${relationPairText}合`
  if (rawCompact.includes('相克') && pairText) return `${pairText}克`
  if (rawCompact.includes('相冲') && pairText) return `${relationPairText}冲`
  if (rawCompact.includes('相害') && pairText) return `${relationPairText}害`
  if (rawCompact.includes('自刑') && pairText) return `${relationPairText}自刑`
  if (/无恩之刑|恃势之刑|无礼之刑/.test(rawCompact) && allText) return `${allText}三刑`
  if (rawCompact.includes('相刑') && pairText) return `${relationPairText}${pair[0] === pair[1] ? '自刑' : '刑'}`
  if (rawCompact.includes('相破') && pairText) return `${relationPairText}破`
  m = rawCompact.match(/拱合([子午卯酉])/)
  if (m && pairText) return `${pairText}拱合${juMap[m[1]] || m[1]}`
  if (rawCompact.includes('拱会') && pairText) {
    const found = huiSets.find(item => pair.slice(0, 2).every(zhi => item.zhis.includes(zhi)))
    return `${pairText}拱会${found ? found.ju : ''}`
  }
  m = rawCompact.match(/半合([木火金水])局/)
  if (m && pairText) return `${pairText}半合${m[1]}局`
  m = rawCompact.match(/三合([木火金水])局/)
  if (m && allText) return `${allText}三合${m[1]}局`
  m = rawCompact.match(/三会([木火金水])局/)
  if (m && rawCompact.includes('缺') && pairText) return `${pairText}拱会${m[1]}局`
  if (m && allText) return `${allText}三会${m[1]}局`
  if (rawCompact.includes('暗合') && pairText) return `${relationPairText}暗合`
  for (const suffix of ['冲', '害', '破', '合', '克']) {
    if (rawCompact.endsWith(suffix) && pairText) return `${relationPairText}${suffix}`
  }
  return rawCompact.replace(/相/g, '')
}

function formatRelationList(source) {
  return String(source || '')
    .split(/[、,，]/)
    .map(s => s.trim())
    .filter(Boolean)
    .map(relationLabel)
    .join('、')
}

const CANG_GAN_LOCAL = {
  '子':['癸'],'丑':['己','癸','辛'],'寅':['甲','丙','戊'],'卯':['乙'],
  '辰':['戊','乙','癸'],'巳':['丙','庚','戊'],'午':['丁','己'],'未':['己','丁','乙'],
  '申':['庚','壬','戊'],'酉':['辛'],'戌':['戊','辛','丁'],'亥':['壬','甲']
}

const SS_TABLE = {
  '甲':{'甲':'比肩','乙':'劫财','丙':'食神','丁':'伤官','戊':'偏财','己':'正财','庚':'七杀','辛':'正官','壬':'偏印','癸':'正印'},
  '乙':{'甲':'劫财','乙':'比肩','丙':'伤官','丁':'食神','戊':'正财','己':'偏财','庚':'正官','辛':'七杀','壬':'正印','癸':'偏印'},
  '丙':{'甲':'偏印','乙':'正印','丙':'比肩','丁':'劫财','戊':'食神','己':'伤官','庚':'偏财','辛':'正财','壬':'七杀','癸':'正官'},
  '丁':{'甲':'正印','乙':'偏印','丙':'劫财','丁':'比肩','戊':'伤官','己':'食神','庚':'正财','辛':'偏财','壬':'正官','癸':'七杀'},
  '戊':{'甲':'七杀','乙':'正官','丙':'偏印','丁':'正印','戊':'比肩','己':'劫财','庚':'食神','辛':'伤官','壬':'偏财','癸':'正财'},
  '己':{'甲':'正官','乙':'七杀','丙':'正印','丁':'偏印','戊':'劫财','己':'比肩','庚':'伤官','辛':'食神','壬':'正财','癸':'偏财'},
  '庚':{'甲':'偏财','乙':'正财','丙':'食神','丁':'伤官','戊':'七杀','己':'正官','庚':'比肩','辛':'劫财','壬':'食神','癸':'伤官'},
  '辛':{'甲':'正财','乙':'偏财','丙':'伤官','丁':'食神','戊':'正官','己':'七杀','庚':'劫财','辛':'比肩','壬':'伤官','癸':'食神'},
  '壬':{'甲':'食神','乙':'伤官','丙':'偏财','丁':'正财','戊':'七杀','己':'正官','庚':'偏印','辛':'正印','壬':'比肩','癸':'劫财'},
  '癸':{'甲':'伤官','乙':'食神','丙':'正财','丁':'偏财','戊':'正官','己':'七杀','庚':'正印','辛':'偏印','壬':'劫财','癸':'比肩'},
}

const CS_TABLE = {'甲':'亥','乙':'午','丙':'寅','丁':'酉','戊':'寅','己':'酉','庚':'巳','辛':'子','壬':'申','癸':'卯'}
const CS_ORDER = ['长生','沐浴','冠带','临官','帝旺','衰','病','死','墓','绝','胎','养']
const DZ_ORDER = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
const YANG_GAN = ['甲','丙','戊','庚','壬']

function getShiShen(dayGan, targetGan) {
  return (SS_TABLE[dayGan] || {})[targetGan] || ''
}

function calcChangsheng(dayGan, zhi) {
  const start = CS_TABLE[dayGan]
  if (!start || !zhi) return ''
  const si = DZ_ORDER.indexOf(start), ti = DZ_ORDER.indexOf(zhi)
  if (si < 0 || ti < 0) return ''
  const isYang = YANG_GAN.includes(dayGan)
  const off = isYang ? (ti - si + 12) % 12 : (si - ti + 12) % 12
  return CS_ORDER[off] || ''
}

function calcKongwang(gan, zhi) {
  const TG = '甲乙丙丁戊己庚辛壬癸'
  const gi = TG.indexOf(gan), zi = DZ_ORDER.indexOf(zhi)
  if (gi < 0 || zi < 0) return ''
  let idx = -1
  for (let k = 0; k < 60; k++) {
    if (k % 10 === gi && k % 12 === zi) { idx = k; break }
  }
  if (idx < 0) return ''
  const xunEnd = idx - (idx % 10) + 9
  const lastZi = xunEnd % 12
  return DZ_ORDER[(lastZi + 1) % 12] + DZ_ORDER[(lastZi + 2) % 12]
}

function supplementSizhu(szData, dayMaster) {
  if (!szData || !dayMaster) return szData
  const keys = Object.keys(szData)
  keys.forEach(k => {
    const p = szData[k]
    if (!p || !p.tg || !p.dz) return
    const needCompute = !p.xingyun || !p.zizuo || !p.kongwang || !(p.shensha && p.shensha.length)
    if (needCompute) {
      if (!p.ss) p.ss = getShiShen(dayMaster, p.tg)
      if (!p.canggan || !p.canggan.length) {
        p.canggan = (CANG_GAN_LOCAL[p.dz] || []).map(g => ({ gz: g, ss: getShiShen(dayMaster, g) }))
      }
      if (!p.xingyun) p.xingyun = calcChangsheng(dayMaster, p.dz)
      if (!p.zizuo) p.zizuo = calcChangsheng(p.tg, p.dz)
      if (!p.kongwang) p.kongwang = calcKongwang(p.tg, p.dz)
      if ((!p.shensha || !p.shensha.length)) p.shensha = []
    }
  })
  return szData
}

// ========== 排盘表格配置 ==========
const colKeys = ['liunian', 'xiaoyun', 'dayun', 'year', 'month', 'day', 'hour']
const colLabels = ['流年', '小运', '大运', '年柱', '月柱', '日柱', '时柱']
const panRows = [
  { label: '主星', key: 'ss', cls: '' },
  { label: '天干', key: 'tg', cls: 'tg-row' },
  { label: '地支', key: 'dz', cls: 'dz-row' },
  { label: '藏干', key: 'cg', cls: 'cg-row greyBg' },
  { label: '星运', key: 'xy', cls: '' },
  { label: '自坐', key: 'zz', cls: '' },
  { label: '空亡', key: 'kw', cls: '' },
  { label: '纳音', key: 'ny', cls: '' }
]

function getSizhuCol(colKey) {
  return baziData.sizhu[colKey] || {}
}

// ========== 八字数据（响应式） ==========
const baziData = reactive({
  name: '',
  shengxiao: '',
  lunar_date: '',
  gender_label: '',
  solar_date: '',
  qiyun_info: '',
  jiaoyun_text: '',
  jiaoyun_info: '',
  tg_guanxi: '',
  dz_guanxi: '',
  sizhu: {
    liunian: {}, xiaoyun: {}, dayun: {},
    year: {}, month: {}, day: {}, hour: {}
  },
  dayun_list: [],
  liunian_list: [],
  xiaoyun_list: [],
  liuyue_list: [],
  wuxing_wangdu: { water: '', wood: '', gold: '', soil: '', fire: '' },
  wzbz_chart: ''
})

// ========== 数据注入函数（与Flask injectBaziData 零改动逻辑） ==========
function injectBaziData(data) {
  // 头部
  baziData.name = data.name || ''
  baziData.shengxiao = data.shengxiao || ''
  baziData.lunar_date = data.lunar_date || ''
  baziData.gender_label = data.gender_label || ''
  baziData.solar_date = data.solar_date || ''
  // 起运信息
  baziData.qiyun_info = data.qiyun_info || ''
  baziData.jiaoyun_text = data.jiaoyun_text || (data.qi_yun_detail && data.qi_yun_detail.jiao_yun_text) || ''
  baziData.jiaoyun_info = data.jiaoyun_info || ''
  // 干支留意
  baziData.tg_guanxi = data.tg_guanxi || ''
  baziData.dz_guanxi = data.dz_guanxi || ''
  // 四柱 - 补充缺失数据
  const dayMaster = data.day_master || ''
  if (data.sizhu) {
    const supplemented = supplementSizhu({...data.sizhu}, dayMaster)
    Object.keys(supplemented).forEach(key => {
      baziData.sizhu[key] = supplemented[key] || {}
    })
  }
  // 大运/流年/小运/流月
  baziData.dayun_list = data.dayun_list || []
  baziData.liunian_list = data.liunian_list || []
  baziData.xiaoyun_list = data.xiaoyun_list || []
  baziData.liuyue_list = data.liuyue_list || []
  // 五行旺度
  baziData.wuxing_wangdu = data.wuxing_wangdu || { water: '', wood: '', gold: '', soil: '', fire: '' }
  // 智能四柱图示
  baziData.wzbz_chart = data.wzbz_chart || ''
}

// ========== 初始化 ==========
onMounted(() => {
  // #ifdef H5
  // 检查URL参数获取数据
  const params = new URLSearchParams(location.search)
  const dataParam = params.get('data')
  if (dataParam) {
    try { injectBaziData(JSON.parse(decodeURIComponent(dataParam))) } catch (e) {}
  }
  // #endif

  // 尝试从页面路由参数或storage获取数据
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  if (currentPage && currentPage.options) {
    const opts = currentPage.options
    if (opts.id) {
      // 从API加载排盘数据
      loadBaziData(opts.id)
    }
  }

  // 如果没有数据，使用示例数据预览
  const stored = uni.getStorageSync('bazi_pro_data')
  if (stored) {
    try { injectBaziData(JSON.parse(stored)) } catch (e) {}
  }
})

async function loadBaziData(id) {
  try {
    const res = await uni.request({ url: `/api/bazi/pro/${id}`, method: 'GET' })
    if (res.data && !res.data.error) {
      injectBaziData(res.data)
    }
  } catch (e) {
    console.log('[八字专业] 加载数据失败', e)
  }
}

// 暴露给外部调用
defineExpose({ injectBaziData })
</script>

<style scoped>
/* ========== 变量体系 ========== */
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --accent: hsl(38, 60%, 60%); --accent-2: hsl(38, 60%, 48%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-border-hover: rgba(255,255,255,0.18); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --accent: hsl(38, 72%, 30%); --accent-2: hsl(38, 72%, 22%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-border-hover: rgba(0,0,0,0.08); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }

.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }
.page-wrap { position: relative; z-index: 1; }

/* ========== 问真八字原生色彩 ========== */
.mainColor { color: #b2955d }
.paipanTitleColor { color: #9e9e9e }
.fireColor { color: #d30505 }
.waterColor { color: #2e83f6 }
.woodColor { color: #07e930 }
.goldColor { color: #ef9104 }
.soilColor { color: #8b6d03 }
.greyBg { background: #f5f5f7 }
[data-theme="dark"] .paipanTitleColor { color: rgba(170,160,145,0.88) }
[data-theme="dark"] .greyBg { background: rgba(30,34,55,0.45) }
.columnFlex { display: flex; flex-direction: column; align-items: center; justify-content: center }

/* ========== 头部信息栏 ========== */
.header-container { background: linear-gradient(135deg, #f8f4ed 0%, #ede4d3 100%); border-radius: 10px; margin: 12px 16px; padding: 20px 24px; display: flex; align-items: center; gap: 16px; }
[data-theme="dark"] .header-container { background: linear-gradient(135deg, rgba(48,53,76,0.85) 0%, rgba(58,64,90,0.88) 100%); }
.header-avatar { width: 50px; height: 50px; border-radius: 50%; background: #e8dcc8; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
[data-theme="dark"] .header-avatar { background: rgba(178,149,91,0.2); }
.header-username { font-size: 25px; font-weight: 500; color: #101010; margin-right: 12px; white-space: nowrap; }
[data-theme="dark"] .header-username { color: var(--text-1); }
.header-calendar { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
.header-calendar-text { font-size: 13px; color: #666; text-align: left; }
[data-theme="dark"] .header-calendar-text { color: var(--text-3); }
.header-tms { margin-left: auto; display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 13px; color: #b2955d; }
.header-edit { cursor: pointer; margin-left: 8px; font-size: 13px; color: #999; }

/* ========== 专业细盘主布局 ========== */
.pro-pan-content { display: flex; flex-direction: row; gap: 12px; padding: 0 16px 12px; }
.pro-pan-content-left { flex: 1 1 0%; background: #fff; border-radius: 10px; padding: 10px 0; }
[data-theme="dark"] .pro-pan-content-left { background: var(--card-bg); }
.pro-pan-content-right { flex: 0 1 auto; width: 520px; background: #fff; border-radius: 10px; padding: 10px; }
[data-theme="dark"] .pro-pan-content-right { background: var(--card-bg); }

/* ========== 左侧排盘表格 ========== */
.pro-pan-content-table { display: flex; flex-direction: column; }
.pro-pan-row { display: flex; align-items: stretch; min-height: 27px; }
.pro-pan-row-item { flex: 1 1 0%; display: flex; align-items: center; justify-content: center; font-size: 15px; padding: 2px 0; position: relative; }
.pro-pan-row-item.shadowBoder { border-right: 1px solid #f0f0f0; }
[data-theme="dark"] .pro-pan-row-item.shadowBoder { border-right: 1px solid var(--card-border); }
.pro-pan-row-item.shadowBoder:last-child { border-right: none; }
.pro-pan-row-item.label-cell { color: #9e9e9e; font-size: 14px; flex: 0 0 88px; max-width: 88px; min-width: 88px; }
[data-theme="dark"] .pro-pan-row-item.label-cell { color: var(--text-3); }

/* 天干行 */
.pro-pan-row.tg-row .pro-pan-row-item { font-size: 22px; font-weight: 600; padding: 6px 0; }
/* 地支行 */
.pro-pan-row.dz-row .pro-pan-row-item { font-size: 22px; font-weight: 600; padding: 8px 0; }
/* 藏干行 */
.pro-pan-row.cg-row { background: #f5f5f7; padding: 4px 0; }
[data-theme="dark"] .pro-pan-row.cg-row { background: rgba(30,34,55,0.45); }
.pro-pan-row.cg-row .pro-pan-row-item { flex-direction: column; gap: 1px; font-size: 13px; }
.canggan-wrap { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.canggan-item { display: flex; align-items: center; gap: 2px; line-height: 1.5; white-space: nowrap; }
.canggan-shishen { font-size: 11px; color: #999; }
[data-theme="dark"] .canggan-shishen { color: var(--text-3); }

/* 神煞分割线 */
.shensha_division { height: 11px; background: #f8f8f8; }
[data-theme="dark"] .shensha_division { background: rgba(30,34,55,0.45); }
/* 神煞行 */
.pro-pan-row.ss-row .pro-pan-row-item { flex-direction: column; align-items: center; gap: 2px; font-size: 12px; line-height: 1.5; padding: 4px 2px; }
.shensha-tag { display: inline-block; font-size: 12px; color: #666; line-height: 1.6; }
[data-theme="dark"] .shensha-tag { color: var(--text-3); }

/* ========== 右侧面板 ========== */
.pro-pan-content-bg { display: flex; flex-direction: column; gap: 6px; }
.pro-pan-qiyun { font-size: 12px; color: #101010; text-align: left; padding: 8px 4px; line-height: 1.6; border-bottom: 1px solid #f0f0f0; }
[data-theme="dark"] .pro-pan-qiyun { color: var(--text-1); border-bottom-color: var(--card-border); }
.pro-pan-yun { display: flex; border-bottom: 1px solid #f5f5f7; }
[data-theme="dark"] .pro-pan-yun { border-bottom-color: var(--card-border); }
.pro-pan-yun:last-child { border-bottom: none; }
.pro-pan-yun-items { display: flex; overflow-x: auto; flex: 1; gap: 0; }
.pro-pan-yun-item { display: flex; flex-direction: column; align-items: center; padding: 4px 2px; font-size: 12px; min-width: 47px; cursor: pointer; flex-shrink: 0; }
.pro-pan-yun-item.yun-index { background: #f8f4ed; border-radius: 4px; min-width: 50px; font-weight: 500; color: #b2955d; font-size: 13px; flex-shrink: 0; }
[data-theme="dark"] .pro-pan-yun-item.yun-index { background: rgba(178,149,91,0.15); color: var(--accent); }
.pro-pan-yun-item-small { font-size: 10px; color: #999; display: block; }
[data-theme="dark"] .pro-pan-yun-item-small { color: var(--text-3); }
.pro-pan-yun-item-label { display: flex; flex-direction: column; align-items: center; gap: 0; margin-top: 2px; }
.pro-pan-yun-item-text { font-size: 14px; font-weight: 500; }
.pro-pan-yun-item-shishen { font-size: 10px; color: #999; }
[data-theme="dark"] .pro-pan-yun-item-shishen { color: var(--text-3); }

/* ========== 干支留意 ========== */
.sizhu-gztip { background: #fff; border-radius: 10px; margin: 0 16px 8px; padding: 14px 20px; text-align: left; font-size: 13px; color: #666; line-height: 1.8; }
[data-theme="dark"] .sizhu-gztip { background: var(--card-bg); color: var(--text-3); }
.sizhu-gztip .mainColor { font-weight: 500; }

/* ========== 智能四柱图示 ========== */
.wzbz-box { background: #fff; border-radius: 10px; margin: 0 16px 16px; overflow: hidden; }
[data-theme="dark"] .wzbz-box { background: var(--card-bg); }
.wzbz_header { display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; border-bottom: 1px solid #f0f0f0; }
[data-theme="dark"] .wzbz_header { border-bottom-color: var(--card-border); }
.wzbz_header_title { font-size: 15px; font-weight: 500; color: #333; }
[data-theme="dark"] .wzbz_header_title { color: var(--text-1); }
.wzbz_header_list { display: flex; gap: 16px; font-size: 13px; color: #b2955d; }
[data-theme="dark"] .wzbz_header_list { color: var(--accent); }
.wzbz_header_list .wzbz-header-btn { cursor: pointer; padding: 2px 8px; border-radius: 4px; }
.wzbz_header_list .wzbz-header-btn.active { background: #f8f4ed; font-weight: 500; }
[data-theme="dark"] .wzbz_header_list .wzbz-header-btn.active { background: var(--accent-glow); }
.wzbz_content { padding: 16px 20px; min-height: 400px; font-size: 13px; color: #666; line-height: 1.8; }
[data-theme="dark"] .wzbz_content { color: var(--text-3); }

/* 当前大运高亮 */
.pro-pan-yun-item.current-dayun { background: #f8f4ed; border-radius: 4px; }
[data-theme="dark"] .pro-pan-yun-item.current-dayun { background: rgba(178,149,91,0.15); }

/* ========== 弹窗 ========== */
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

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .pro-pan-content { flex-direction: column; }
  .pro-pan-content-right { width: 100%; }
  .header-container { flex-wrap: wrap; padding: 16px; }
  .header-username { font-size: 20px; }
  .pro-pan-row-item.label-cell { flex: 0 0 60px; max-width: 60px; min-width: 60px; font-size: 12px; }
  .pro-pan-row-item { font-size: 13px; }
  .pro-pan-row.tg-row .pro-pan-row-item { font-size: 17px; }
  .pro-pan-row.dz-row .pro-pan-row-item { font-size: 17px; }
  .wzbz-box { margin: 0 8px 12px; }
  .sizhu-gztip { margin: 0 8px 8px; }
  .header-container { margin: 8px 8px; }
  .pro-pan-content { padding: 0 8px 12px; }
}
</style>
