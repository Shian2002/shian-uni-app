// ═══ 工具函数（核心由 api-client.js 提供） ═══
// $, getCSRF, apiFetch, esc, sanitizeData, toggleTheme, openMobileMenu, closeMobileMenu 已在 api-client.js 中定义

// ═══ 返回 ═══
function goBack(){
    if(document.referrer && document.referrer.includes(window.location.host)){
        window.history.back();
    } else {
        window.location.href='/';
    }
}

// ═══ 五行颜色映射（时安八字配色 — 完全对齐时安八字专业盘） ═══
const WX_COLOR_BZ = {
    '金':'#ef9104','木':'#07e930','水':'#2e83f6','火':'#d30505','土':'#8b6d03',
    '庚':'#ef9104','辛':'#d4860a',
    '甲':'#07e930','乙':'#1dcc36',
    '壬':'#2e83f6','癸':'#4a96f0',
    '丙':'#d30505','丁':'#e02a2a',
    '戊':'#8b6d03','己':'#a07d10',
    '申':'#ef9104','酉':'#d4860a',
    '寅':'#07e930','卯':'#1dcc36',
    '子':'#2e83f6','亥':'#4a96f0',
    '巳':'#d30505','午':'#e02a2a',
    '辰':'#8b6d03','丑':'#a07d10','未':'#a07d10','戌':'#8b6d03'
};

// 五行名称映射（用于着色时判断）
const GAN_WUXING_DETAIL = {
    '甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'
};
const ZHI_WUXING_DETAIL = {
    '子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'
};

function wxSpanBZ(ch, options){
    const opts = options || {};
    const size = opts.size || '';  // 'lg' for larger font
    const sizeStyle = size === 'lg' ? 'font-size:1.2rem;' : '';
    let html = '';
    for (const c of ch) {
        const color = WX_COLOR_BZ[c];
        if (color) {
            html += `<span style="color:${color};${sizeStyle}">${c}</span>`;
        } else {
            html += `<span style="${sizeStyle}">${c}</span>`;
        }
    }
    return html;
}

function relationLabelBZ(desc) {
    const raw = String(desc || '').trim();
    const rawCompact = raw.replace(/\s+/g, '');
    const charSource = rawCompact.replace(/缺[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]+/g, '');
    const pair = charSource.match(/[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]/g) || [];
    const pairText = pair.slice(0, 2).join('');
    const allText = pair.join('');
    const hePairOrder = ['甲己', '乙庚', '丙辛', '丁壬', '戊癸'];
    const relationPairOrder = ['辰丑', '酉戌', '辰卯', '午卯', '巳亥', '辰戌', '丑戌'];
    const orderedPair = (orders) => pair.length >= 2 && pair[0] !== pair[1] ? (orders.find(item => item.includes(pair[0]) && item.includes(pair[1])) || pairText) : pairText;
    const hePairText = orderedPair(hePairOrder);
    const relationPairText = orderedPair(relationPairOrder);
    const juMap = { 子: '水局', 午: '火局', 卯: '木局', 酉: '金局' };
    const huiSets = [
        { zhis: '寅卯辰', ju: '木局' },
        { zhis: '巳午未', ju: '火局' },
        { zhis: '申酉戌', ju: '金局' },
        { zhis: '亥子丑', ju: '水局' },
    ];
    let m = rawCompact.match(/合化([木火土金水])/);
    if (m && pairText) return `${hePairText}合化${m[1]}`;
    if (/六合|相合/.test(rawCompact) && pairText) return `${relationPairText}合`;
    if (rawCompact.includes('相克') && pairText) return `${pairText}克`;
    if (rawCompact.includes('相冲') && pairText) return `${relationPairText}冲`;
    if (rawCompact.includes('相害') && pairText) return `${relationPairText}害`;
    if (rawCompact.includes('自刑') && pairText) return `${relationPairText}自刑`;
    if (/无恩之刑|恃势之刑|无礼之刑/.test(rawCompact) && allText) return `${allText}三刑`;
    if (rawCompact.includes('相刑') && pairText) return `${relationPairText}${pair[0] === pair[1] ? '自刑' : '刑'}`;
    if (rawCompact.includes('相破') && pairText) return `${relationPairText}破`;
    m = rawCompact.match(/拱合([子午卯酉])/);
    if (m && pairText) return `${pairText}拱合${juMap[m[1]] || m[1]}`;
    if (rawCompact.includes('拱会') && pairText) {
        const found = huiSets.find(item => pair.slice(0, 2).every(zhi => item.zhis.includes(zhi)));
        return `${pairText}拱会${found ? found.ju : ''}`;
    }
    m = rawCompact.match(/半合([木火金水])局/);
    if (m && pairText) return `${pairText}半合${m[1]}局`;
    m = rawCompact.match(/三合([木火金水])局/);
    if (m && allText) return `${allText}三合${m[1]}局`;
    m = rawCompact.match(/三会([木火金水])局/);
    if (m && rawCompact.includes('缺') && pairText) return `${pairText}拱会${m[1]}局`;
    if (m && allText) return `${allText}三会${m[1]}局`;
    if (rawCompact.includes('暗合') && pairText) return `${relationPairText}暗合`;
    for (const suffix of ['冲', '害', '破', '合', '克']) {
        if (rawCompact.endsWith(suffix) && pairText) return `${relationPairText}${suffix}`;
    }
    return rawCompact.replace(/相/g, '');
}

function formatRelationListBZ(source) {
    return String(source || '')
        .split(/[、,，]/)
        .map(s => s.trim())
        .filter(Boolean)
        .map(relationLabelBZ)
        .join('、');
}

// ═══ 月份/星期 ═══
const MONTH_CN = ['正月','二月','三月','四月','五月','六月','七月','八月','九月','十月','冬月','腊月'];

// ═══ 生肖emoji映射 ═══
const SHENGXIAO_EMOJI = {
    '鼠':'🐭','牛':'🐮','虎':'🐯','兔':'🐰','龙':'🐲','蛇':'🐍',
    '马':'🐴','羊':'🐑','猴':'🐵','鸡':'🐔','狗':'🐶','猪':'🐷'
};

// ═══ 天干五行映射（JS端）═══
const GAN_WUXING_JS = {
    '甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'
};

// ═══ 本地藏干表（小运单元格渲染用）═══
const CANG_GAN_LOCAL = {
    '子':['癸'],'丑':['己','癸','辛'],'寅':['甲','丙','戊'],'卯':['乙'],
    '辰':['戊','乙','癸'],'巳':['丙','庚','戊'],'午':['丁','己'],'未':['己','丁','乙'],
    '申':['庚','壬','戊'],'酉':['辛'],'戌':['戊','辛','丁'],'亥':['壬','甲']
};

// ═══ 本地十神表（小运单元格渲染用）═══
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
};

// ═══ 交互状态 ═══
let _baziActiveYear = null;
let _baziActiveMonth = null;
let _baziActiveDayGz = null;
let _activeTab = localStorage.getItem('xc_bazi_activeTab') || 'shiAnpro'; // 'info' | 'basic' | 'shiAnpro' | 'notes' | 'settings'
let _showTMS = false; // 胎命身
let _activeDayunIdx = -1; // 专业排盘选中的大运索引
let _activeLiunianIdx = -1; // 专业细盘选中的流年索引
let _dayunUserSelected = false; // 用户是否手动点击了大运
let _baziData = null; // 全局数据缓存

// 初始化：自动选中当前大运和当前流年（始终选中一个大运，不再"排一堆"）
function _initActiveDayun() {
    if (!_baziData) return;
    const dy = _baziData.da_yun || [];
    const ln = _baziData.liu_nian || [];
    if (dy.length === 0) return;
    const currentYear = new Date().getFullYear();

    // 找到当前年份所在的大运
    let dyIdx = dy.findIndex(d => currentYear >= d.start_year && currentYear <= d.end_year);
    // 如果当前年份不在任何大运中（如未起运或超出范围），找最近的大运
    if (dyIdx < 0) {
        // 找start_year最接近当前年份的大运
        let minDist = Infinity;
        dy.forEach((d, i) => {
            const dist = Math.abs(d.start_year - currentYear);
            if (dist < minDist) { minDist = dist; dyIdx = i; }
        });
    }

    _activeDayunIdx = dyIdx;
    _dayunUserSelected = false; // 初始化时非用户手动选择

    // 优先找当前年份的流年
    let lnIdx = ln.findIndex(l => l.year === currentYear);
    if (lnIdx < 0) {
        // 流年数据可能不覆盖当前年份，找大运范围内最近的年份
        const activeDy = dy[dyIdx];
        if (activeDy) {
            for (let y = activeDy.start_year; y <= activeDy.end_year; y++) {
                const idx = ln.findIndex(l => l.year === y);
                if (idx >= 0) { lnIdx = idx; break; }
            }
        }
    }
    _activeLiunianIdx = lnIdx >= 0 ? lnIdx : -1;

    // 自动滚动到大运区域的当前项
    setTimeout(() => {
        const activeDayunEl = document.querySelector('.col-dayun.dy-active');
        if (activeDayunEl) {
            activeDayunEl.scrollIntoView({behavior:'smooth', block:'nearest', inline:'center'});
        }
        const activeLnEl = document.querySelector('.col-liunian.ln-active');
        if (activeLnEl) {
            activeLnEl.scrollIntoView({behavior:'smooth', block:'nearest', inline:'center'});
        }
    }, 200);
}

// ═══ 页面加载 ═══
document.addEventListener('DOMContentLoaded', async function(){
    let params = null;
    const stored = sessionStorage.getItem('xc_bazi_params');
    if(stored){
        try { params = JSON.parse(stored); } catch(e) { params = null; }
    }

    // 如果 sessionStorage 无数据，尝试从 URL 参数构建
    if(!params){
        const urlP = new URLSearchParams(location.search);
        const uy = urlP.get('y'), um = urlP.get('m'), ud = urlP.get('d');
        const uh = urlP.get('h'), umi = urlP.get('mi'), us = urlP.get('s');
        if(uy && um && ud){
            params = {
                calType: '公历',
                gender: (us == 2) ? '女' : '男',
                birthTime: `${uy}${String(um).padStart(2,'0')}${String(ud).padStart(2,'0')}${String(uh||0).padStart(2,'0')}${String(umi||0).padStart(2,'0')}`,
                birthAddr: '',
                birthLng: 0,
                birthLat: 0,
                isDst: false,
                nightZiMode: '夜子时不换日',
                useSolarTime: true,
                isLeapMonth: false,
                _replay: true,
            };
        }
    }

    if(!params){
        showError('未找到排盘参数，请返回首页重新排盘');
        return;
    }

    const calType = params.calType || '公历';

    let birthTime = '';
    let siziPillars = null;

    if (calType === '四柱' && params.siziPillars) {
        // 四柱直接输入模式
        siziPillars = params.siziPillars;
    } else {
        // 公历/农历模式
        const birthDate = params.birthDate;
        if(!birthDate && !params.birthTime){ showError('缺少出生日期'); return; }
        if (params.birthTime) {
            birthTime = params.birthTime;
        } else {
            const [y, m, d] = birthDate.split('-');
            const hh = params.birthHour || '0';
            const mm = params.birthMinute || '00';
            birthTime = `${y}${m}${d}${String(hh).padStart(2,'0')}${String(mm).padStart(2,'0')}`;
        }
    }

    try {
        const r = await apiFetch('/api/bazi/paipan', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: params.name || '',
                gender: params.gender || '男',
                calType: calType,
                birthTime: birthTime,
                birthAddr: params.birthAddr || '',
                birthLng: params.birthLng || 0,
                birthLat: params.birthLat || 0,
                isDst: params.isDst || false,
                nightZiMode: params.nightZiMode || '夜子时不换日',
                siziPillars: siziPillars,
                useSolarTime: params.useSolarTime !== false,
                isLeapMonth: params.isLeapMonth || false,
                _replay: !!params._replay   // 回放标记：不重复保存记录
            })
        });
        const data = await r.json();
        if(data.success){
            _baziData = sanitizeData(data);
            // 自动选中当前大运和当前流年
            _initActiveDayun();
            renderBaziResult(data);
        } else {
            showError(data.error || '排盘失败');
        }
    } catch(e){
        showError('网络错误：' + e.message);
    }
});

function showError(msg){
    $('resultArea').innerHTML = `
        <div class="error-state">
            <div class="error-icon">❌</div>
            <div class="error-msg">${msg}</div>
            <button class="btn-retry" onclick="window.location.href='/'">返回首页</button>
        </div>`;
}

// ═══════════════════════════════════════════════════════════════
// 排盘结果渲染
// ═══════════════════════════════════════════════════════════════

function renderBaziResult(data) {
    const fp = data.four_pillars || {};
    const ss = data.shi_shen || {};
    const cg = data.cang_gan || {};
    const cgss = data.cang_gan_shi_shen || {};
    const wx = data.wu_xing || {};
    const kong = data.kong_wang || [];
    const ws = data.wang_shuai || '';
    const dy = data.da_yun || [];
    const ln = data.liu_nian || [];
    const dyDir = data.da_yun_direction || '顺';
    const qiAge = data.qi_yun_age || 0;

    // 新字段
    const dayMasterLabel = data.day_master_label || (data.gender === '女' ? '元女' : '元男');
    const cgWx = data.cang_gan_with_wx || {};
    const xingYun = data.xing_yun || {};
    const diShi = data.di_shi || {};
    const ziZuo = data.zi_zuo || {};
    const kongPerPillar = data.kong_wang_per_pillar || {};
    const ssPerPillar = data.shen_sha_per_pillar || {};
    const wangXiangXiu = data.wang_xiang_xiu || [];
    const shengXiao = data.sheng_xiao || '';
    const xingZuo = data.xing_zuo || '';
    const taiMingShen = data.tai_ming_shen || {};
    const qiYunDetail = data.qi_yun_detail || {};
    const jieQiRange = data.jie_qi_range || {};
    const xiaoYun = data.xiao_yun || [];

    // ═══ 构建页面 ═══
    let html = '';

    // Tab布局
    html += `<div class="tab-layout">`;
    // 侧边栏
    html += `<div class="tab-sidebar">`;
    html += `<button class="tab-btn${_activeTab==='info'?' active':''}" onclick="switchTab('info')">基本信息</button>`;
    html += `<button class="tab-btn${_activeTab==='basic'?' active':''}" onclick="switchTab('basic')">基本排盘</button>`;
    html += `<button class="tab-btn${_activeTab==='shiAnpro'?' active':''}" onclick="switchTab('shiAnpro')">专业排盘</button>`;
    html += `<button class="tab-btn${_activeTab==='notes'?' active':''}" onclick="switchTab('notes')">📝 笔记</button>`;
    html += `<button class="tab-btn${_activeTab==='settings'?' active':''}" onclick="switchTab('settings')">⚙ 设置</button>`;
    html += `</div>`;
    // 内容区
    html += `<div class="tab-content-area">`;

    // ─── Tab1: 基本信息 ───
    html += `<div class="tab-panel${_activeTab==='info'?' active':''}" id="panelInfo">`;
    html += renderInfoTab(data);
    html += `</div>`;

    // ─── Tab2: 基本排盘 ───
    html += `<div class="tab-panel${_activeTab==='basic'?' active':''}" id="panelBasic">`;
    html += renderBasicTab(data);
    html += `</div>`;

    // ─── Tab3: 专业排盘 ───
    html += `<div class="tab-panel${_activeTab==='shiAnpro'?' active':''}" id="panelWzpro">`;
    html += renderShianProTab(data);
    html += `</div>`;

    // ─── Tab5: 断事笔记 ───
    html += `<div class="tab-panel${_activeTab==='notes'?' active':''}" id="panelNotes">`;
    html += renderNotesTab(data);
    html += `</div>`;

    // ─── Tab5: 设置 ───
    html += `<div class="tab-panel${_activeTab==='settings'?' active':''}" id="panelSettings">`;
    html += renderSettingsTab();
    html += `</div>`;

    html += `</div>`; // tab-content-area
    html += `</div>`; // tab-layout

    // 底部声明
    html += `<div class="disclaimer">⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议</div>`;

    $('resultArea').innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════
// Tab切换
// ═══════════════════════════════════════════════════════════════

function switchTab(tab) {
    _activeTab = tab;
    localStorage.setItem('xc_bazi_activeTab', tab);
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    // 按顺序: info=0, basic=1, shiAnpro=2, notes=3, settings=4
    const idx = {info:0, basic:1, shiAnpro:2, notes:3, settings:4}[tab];
    document.querySelectorAll('.tab-btn')[idx].classList.add('active');
    if (tab === 'shiAnpro') {
        $('panelWzpro').classList.add('active');
    } else {
        $('panel' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('active');
    }
}

// ═══════════════════════════════════════════════════════════════
// Tab4: 断事笔记（纯 localStorage 存储）
// ═══════════════════════════════════════════════════════════════

const NOTE_TAGS = [
    {key: 'career', label: '事业', color: '#2e83f6', icon: '💼'},
    {key: 'wealth', label: '财运', color: '#ef9104', icon: '💰'},
    {key: 'marriage', label: '婚姻', color: '#d30505', icon: '💕'},
    {key: 'health', label: '健康', color: '#07e930', icon: '🏥'},
    {key: 'study', label: '学业', color: '#8A2BE2', icon: '📚'},
    {key: 'other', label: '其他', color: '#888', icon: '📌'},
];

function _fourPillarsHash(data) {
    // 基于四柱干支生成唯一hash
    const fp = (data && data.four_pillars) || {};
    const key = `${fp.year?.gan_zhi||''}_${fp.month?.gan_zhi||''}_${fp.day?.gan_zhi||''}_${fp.hour?.gan_zhi||''}`;
    return key;
}

function _getNotesStorageKey(data) {
    return 'xc_bazi_notes_' + _fourPillarsHash(data);
}

function _loadNotes(data) {
    try {
        const raw = localStorage.getItem(_getNotesStorageKey(data));
        return raw ? JSON.parse(raw) : [];
    } catch(e) { return []; }
}

function _saveNotes(data, notes) {
    localStorage.setItem(_getNotesStorageKey(data), JSON.stringify(notes));
}

function renderNotesTab(data) {
    const notes = _loadNotes(data);
    let html = '';

    html += `<div style="max-width:680px;">`;

    // ── 添加笔记区 ──
    html += `<div class="info-card" style="margin-bottom:14px;">`;
    html += `<div class="card-title">📝 添加笔记</div>`;
    html += `<div class="card-content">`;

    // 标签选择
    html += `<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">`;
    NOTE_TAGS.forEach(t => {
        html += `<button id="noteTagBtn_${t.key}" onclick="_selectNoteTag('${t.key}')" style="display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:20px;border:1px solid var(--card-border);background:var(--tag-bg);color:var(--text-2);font-size:0.76rem;cursor:pointer;transition:0.2s;">${t.icon} ${t.label}</button>`;
    });
    html += `</div>`;

    // 文本输入
    html += `<textarea id="noteInput" rows="3" placeholder="记录断事心得…" style="width:100%;padding:10px 14px;border-radius:10px;border:1px solid var(--card-border);background:var(--section-alt);color:var(--text-1);font-size:0.84rem;font-family:var(--font-sans);resize:vertical;outline:none;transition:border-color 0.2s;" onfocus="this.style.borderColor='var(--accent)'" onblur="this.style.borderColor='var(--card-border)'"></textarea>`;

    // 提交按钮
    html += `<div style="margin-top:10px;display:flex;justify-content:flex-end;">`;
    html += `<button onclick="_addNote()" style="padding:8px 20px;border-radius:10px;border:none;background:var(--accent);color:#fff;font-size:0.84rem;font-weight:600;cursor:pointer;transition:0.2s;opacity:0.92;" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.92'">添加笔记</button>`;
    html += `</div>`;

    html += `</div></div>`;

    // ── 笔记列表 ──
    html += `<div class="info-card" style="margin-bottom:14px;">`;
    html += `<div class="card-title">📋 笔记列表${notes.length > 0 ? ` <span style="font-size:0.74rem;color:var(--text-3);font-weight:400;">（${notes.length}条）</span>` : ''}</div>`;

    if (notes.length === 0) {
        html += `<div style="text-align:center;padding:30px 0;color:var(--text-3);font-size:0.84rem;">暂无笔记，添加第一条断事心得吧 ✨</div>`;
    } else {
        html += `<div class="card-content" style="display:flex;flex-direction:column;gap:10px;">`;
        // 按时间倒序
        const sorted = [...notes].sort((a, b) => b.created - a.created);
        sorted.forEach(note => {
            const tagInfo = NOTE_TAGS.find(t => t.key === note.tag) || NOTE_TAGS[5];
            const date = new Date(note.created);
            const dateStr = `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')} ${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;

            html += `<div style="padding:12px;border-radius:10px;background:var(--section-alt);border:1px solid var(--card-border);transition:0.2s;" onmouseover="this.style.borderColor='var(--card-border-hover)'" onmouseout="this.style.borderColor='var(--card-border)'">`;

            // 标签 + 时间
            html += `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">`;
            html += `<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:12px;background:${tagInfo.color}22;color:${tagInfo.color};font-size:0.72rem;font-weight:500;">${tagInfo.icon} ${tagInfo.label}</span>`;
            html += `<span style="font-size:0.7rem;color:var(--text-3);">${dateStr}</span>`;
            html += `</div>`;

            // 内容
            if (note.editing) {
                html += `<textarea id="noteEdit_${note.id}" rows="3" style="width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--accent);background:var(--card-bg);color:var(--text-1);font-size:0.82rem;font-family:var(--font-sans);resize:vertical;outline:none;">${_escHtml(note.text)}</textarea>`;
                html += `<div style="margin-top:6px;display:flex;gap:6px;justify-content:flex-end;">`;
                html += `<button onclick="_saveEditNote('${note.id}')" style="padding:4px 14px;border-radius:8px;border:none;background:var(--accent);color:#fff;font-size:0.76rem;cursor:pointer;">保存</button>`;
                html += `<button onclick="_cancelEditNote('${note.id}')" style="padding:4px 14px;border-radius:8px;border:1px solid var(--card-border);background:transparent;color:var(--text-2);font-size:0.76rem;cursor:pointer;">取消</button>`;
                html += `</div>`;
            } else {
                html += `<div style="font-size:0.84rem;color:var(--text-1);line-height:1.6;white-space:pre-wrap;word-break:break-word;">${_escHtml(note.text)}</div>`;
            }

            // 操作按钮
            if (!note.editing) {
                html += `<div style="margin-top:8px;display:flex;gap:8px;justify-content:flex-end;">`;
                html += `<button onclick="_editNote('${note.id}')" style="padding:2px 8px;border-radius:6px;border:1px solid var(--card-border);background:transparent;color:var(--text-3);font-size:0.72rem;cursor:pointer;transition:0.2s;" onmouseover="this.style.color='var(--accent)';this.style.borderColor='var(--accent)'" onmouseout="this.style.color='var(--text-3)';this.style.borderColor='var(--card-border)'">✏️ 编辑</button>`;
                html += `<button onclick="_deleteNote('${note.id}')" style="padding:2px 8px;border-radius:6px;border:1px solid var(--card-border);background:transparent;color:var(--text-3);font-size:0.72rem;cursor:pointer;transition:0.2s;" onmouseover="this.style.color='var(--danger)';this.style.borderColor='var(--danger)'" onmouseout="this.style.color='var(--text-3)';this.style.borderColor='var(--card-border)'">🗑 删除</button>`;
                html += `</div>`;
            }

            html += `</div>`;
        });
        html += `</div>`;
    }

    html += `</div>`;

    // ── 四柱信息 ──
    const fp = (data && data.four_pillars) || {};
    const fpStr = `${fp.year?.gan_zhi||''} ${fp.month?.gan_zhi||''} ${fp.day?.gan_zhi||''} ${fp.hour?.gan_zhi||''}`;
    if (fpStr.trim()) {
        html += `<div style="text-align:center;font-size:0.72rem;color:var(--text-3);margin-top:4px;">四柱：${fpStr}</div>`;
    }

    html += `</div>`;
    return html;
}

// 笔记选中标签
let _selectedNoteTag = 'career';

function _selectNoteTag(key) {
    _selectedNoteTag = key;
    // 更新按钮样式
    NOTE_TAGS.forEach(t => {
        const btn = document.getElementById('noteTagBtn_' + t.key);
        if (btn) {
            if (t.key === key) {
                btn.style.background = t.color + '33';
                btn.style.borderColor = t.color;
                btn.style.color = t.color;
            } else {
                btn.style.background = 'var(--tag-bg)';
                btn.style.borderColor = 'var(--card-border)';
                btn.style.color = 'var(--text-2)';
            }
        }
    });
}

function _addNote() {
    if (!_baziData) return;
    const input = document.getElementById('noteInput');
    const text = (input ? input.value : '').trim();
    if (!text) return;

    const notes = _loadNotes(_baziData);
    notes.push({
        id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
        text: text,
        created: Date.now(),
        tag: _selectedNoteTag,
    });
    _saveNotes(_baziData, notes);

    // 重新渲染
    $('panelNotes').innerHTML = renderNotesTab(_baziData);
    // 默认选中当前标签
    setTimeout(() => _selectNoteTag(_selectedNoteTag), 50);
}

function _editNote(id) {
    if (!_baziData) return;
    const notes = _loadNotes(_baziData);
    const note = notes.find(n => n.id === id);
    if (note) {
        note.editing = true;
        _saveNotes(_baziData, notes);
        $('panelNotes').innerHTML = renderNotesTab(_baziData);
        setTimeout(() => _selectNoteTag(_selectedNoteTag), 50);
    }
}

function _saveEditNote(id) {
    if (!_baziData) return;
    const notes = _loadNotes(_baziData);
    const note = notes.find(n => n.id === id);
    const textarea = document.getElementById('noteEdit_' + id);
    if (note && textarea) {
        note.text = textarea.value.trim();
        note.editing = false;
        if (!note.text) {
            // 空文本则删除
            const idx = notes.indexOf(note);
            if (idx >= 0) notes.splice(idx, 1);
        }
        _saveNotes(_baziData, notes);
        $('panelNotes').innerHTML = renderNotesTab(_baziData);
        setTimeout(() => _selectNoteTag(_selectedNoteTag), 50);
    }
}

function _cancelEditNote(id) {
    if (!_baziData) return;
    const notes = _loadNotes(_baziData);
    const note = notes.find(n => n.id === id);
    if (note) {
        note.editing = false;
        _saveNotes(_baziData, notes);
        $('panelNotes').innerHTML = renderNotesTab(_baziData);
        setTimeout(() => _selectNoteTag(_selectedNoteTag), 50);
    }
}

function _deleteNote(id) {
    if (!_baziData) return;
    const notes = _loadNotes(_baziData);
    const idx = notes.findIndex(n => n.id === id);
    if (idx >= 0) {
        notes.splice(idx, 1);
        _saveNotes(_baziData, notes);
        $('panelNotes').innerHTML = renderNotesTab(_baziData);
        setTimeout(() => _selectNoteTag(_selectedNoteTag), 50);
    }
}

function _escHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function _toggleGujiText(idx) {
    const textEl = document.getElementById('gujiText_' + idx);
    const fadeEl = document.getElementById('gujiFade_' + idx);
    const btnEl = document.getElementById('gujiBtn_' + idx);
    if (!textEl) return;
    if (textEl.style.maxHeight === 'none' || textEl.style.maxHeight === '') {
        textEl.style.maxHeight = '3.4em';
        if (fadeEl) fadeEl.style.display = '';
        if (btnEl) btnEl.textContent = '展开全文';
    } else {
        textEl.style.maxHeight = 'none';
        if (fadeEl) fadeEl.style.display = 'none';
        if (btnEl) btnEl.textContent = '收起';
    }
}

// ═══════════════════════════════════════════════════════════════
// Tab5: 设置
// ═══════════════════════════════════════════════════════════════

function getSettings() {
    const defaults = {
        show_shensha: true,
        show_canggan: true,
        show_xingyun: true,
        show_kongwang: true,
        show_nayin: true,
        wx_display: 'count', // count | energy | canggan
        theme: 'dark',
    };
    try {
        const saved = localStorage.getItem('xc_bazi_settings');
        if (saved) return {...defaults, ...JSON.parse(saved)};
    } catch(e) {}
    return defaults;
}

function saveSetting(key, value) {
    const s = getSettings();
    s[key] = value;
    localStorage.setItem('xc_bazi_settings', JSON.stringify(s));
}

function renderSettingsTab() {
    const s = getSettings();
    let html = '';

    html += `<div style="max-width:480px;">`;

    // ── 显示控制 ──
    html += `<div class="info-card" style="margin-bottom:14px;">`;
    html += `<div class="card-title">📊 显示控制</div>`;
    html += `<div class="card-content">`;

    const toggles = [
        {key: 'show_shensha', label: '神煞显示', desc: '在基本排盘中显示神煞行'},
        {key: 'show_canggan', label: '藏干显示', desc: '在基本排盘中显示藏干行'},
        {key: 'show_xingyun', label: '星运显示', desc: '在基本排盘中显示星运行'},
        {key: 'show_kongwang', label: '空亡显示', desc: '在基本排盘中显示空亡行'},
        {key: 'show_nayin', label: '纳音显示', desc: '在基本排盘中显示纳音行'},
    ];

    toggles.forEach(t => {
        const checked = s[t.key] !== false;
        html += `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--card-border);">`;
        html += `<div><div style="font-size:0.84rem;font-weight:600;color:var(--text-1);">${t.label}</div><div style="font-size:0.7rem;color:var(--text-3);">${t.desc}</div></div>`;
        html += `<label style="position:relative;display:inline-block;width:40px;height:22px;cursor:pointer;">`;
        html += `<input type="checkbox" ${checked?'checked':''} onchange="saveSetting('${t.key}',this.checked);onSettingsChanged();" style="opacity:0;width:0;height:0;">`;
        html += `<span style="position:absolute;inset:0;background:${checked?'var(--accent)':'var(--card-border)'};border-radius:11px;transition:0.3s;"></span>`;
        html += `<span style="position:absolute;left:${checked?'20px':'3px'};top:3px;width:16px;height:16px;background:#fff;border-radius:50%;transition:0.3s;"></span>`;
        html += `</label>`;
        html += `</div>`;
    });

    html += `</div></div>`;

    // ── 五行统计默认视图 ──
    html += `<div class="info-card" style="margin-bottom:14px;">`;
    html += `<div class="card-title">🔥 五行统计默认视图</div>`;
    html += `<div class="card-content">`;
    const wxViews = [
        {val:'count', label:'个数视图', desc:'按五行出现个数统计'},
        {val:'energy', label:'能量视图', desc:'按旺相休囚死加权统计'},
        {val:'canggan', label:'含藏干视图', desc:'含藏干五行分布统计'},
    ];
    wxViews.forEach(v => {
        const selected = s.wx_display === v.val;
        html += `<div style="display:flex;align-items:center;gap:10px;padding:8px 0;cursor:pointer;border-bottom:1px solid var(--card-border);" onclick="saveSetting('wx_display','${v.val}');onSettingsChanged();">`;
        html += `<span style="width:18px;height:18px;border-radius:50%;border:2px solid ${selected?'var(--accent)':'var(--card-border)'};display:flex;align-items:center;justify-content:center;">${selected?'<span style="width:10px;height:10px;border-radius:50%;background:var(--accent);"></span>':''}</span>`;
        html += `<div><div style="font-size:0.84rem;font-weight:600;color:${selected?'var(--accent)':'var(--text-1)'};">${v.label}</div><div style="font-size:0.7rem;color:var(--text-3);">${v.desc}</div></div>`;
        html += `</div>`;
    });
    html += `</div></div>`;

    // ── 关于 ──
    html += `<div class="info-card" style="margin-bottom:14px;">`;
    html += `<div class="card-title">ℹ️ 关于</div>`;
    html += `<div class="card-content">`;
    html += `<div style="font-size:0.84rem;color:var(--text-2);line-height:1.7;">`;
    html += `<div>时安解忧屋八字排盘 v7.0</div>`;
    html += `<div style="color:var(--text-3);font-size:0.74rem;margin-top:4px;">1:1 复刻时安八字专业盘排盘结果页功能，保持时安解忧屋视觉风格</div>`;
    html += `<div style="color:var(--text-3);font-size:0.74rem;margin-top:2px;">技术栈：Python Flask + 纯前端 JS/CSS</div>`;
    html += `</div></div></div>`;

    html += `</div>`;
    return html;
}

function onSettingsChanged() {
    // 重新渲染设置Tab
    if (_activeTab === 'settings') {
        $('panelSettings').innerHTML = renderSettingsTab();
    }
    // 重新渲染所有内容Tab（应用显示设置变化）
    if (_baziData) {
        $('panelInfo').innerHTML = renderInfoTab(_baziData);
        $('panelBasic').innerHTML = renderBasicTab(_baziData);
        // 笔记Tab无需设置关联，不重新渲染
    }
}

// ═══════════════════════════════════════════════════════════════
// Tab1: 基本信息
// ═══════════════════════════════════════════════════════════════

function renderInfoTab(data) {
    const fp = data.four_pillars || {};
    const ss = data.shi_shen || {};
    const wx = data.wu_xing || {};
    const kong = data.kong_wang || [];
    const ws = data.wang_shuai || '';
    const shengXiao = data.sheng_xiao || '';
    const xingZuo = data.xing_zuo || '';
    const taiMingShen = data.tai_ming_shen || {};
    const qiYunDetail = data.qi_yun_detail || {};
    const jieQiRange = data.jie_qi_range || {};
    const wangXiangXiu = data.wang_xiang_xiu || [];

    let html = '';

    // ═══ 基本信息卡片 ═══
    html += `<div class="info-card" style="margin-bottom:14px;">`;
    html += `<div class="card-title">📋 基本信息</div>`;
    html += `<div class="basic-info-grid">`;
    if (data.name) html += `<div class="basic-info-item"><span class="label">姓名：</span><span class="value">${data.name}</span></div>`;
    html += `<div class="basic-info-item"><span class="label">性别：</span><span class="value">${data.gender}</span></div>`;
    if (data.birth_input) html += `<div class="basic-info-item"><span class="label">阳历：</span><span class="value">${data.birth_input}</span></div>`;
    if (data.birth_lunar) html += `<div class="basic-info-item"><span class="label">阴历：</span><span class="value">${data.birth_lunar}</span></div>`;
    if (shengXiao) html += `<div class="basic-info-item"><span class="label">生肖：</span><span class="value">${SHENGXIAO_EMOJI[shengXiao]||''} ${shengXiao}</span></div>`;
    if (xingZuo) html += `<div class="basic-info-item"><span class="label">星座：</span><span class="value">${xingZuo}</span></div>`;
    if (ws) {
        // 使用综合旺衰判断（wang_shuai_detail.strength），避免与详细分析矛盾
        const wsDetail = data.wang_shuai_detail || {};
        const wsDisplay = wsDetail.strength || ws;
        html += `<div class="basic-info-item"><span class="label">日干旺衰：</span><span class="value">${wsDisplay}</span></div>`;
    }
    html += `</div>`;
    // 真太阳时
    if (data.true_solar_time && data.true_solar_time !== data.birth_input) {
        html += `<div style="font-size:0.78rem;color:var(--text-3);margin-top:8px;padding-top:8px;border-top:1px solid var(--card-border);">🕐 真太阳时：${data.true_solar_time}`;
        if (data.location && data.location.lng !== 120.0) {
            html += `（经度修正 ${data.location.tz_offset_min > 0 ? '+' : ''}${data.location.tz_offset_min}分钟）`;
        }
        html += `</div>`;
    }
    html += `</div>`;

    // ═══ 当天排盘 ═══
    const todayPp = data.today_paipan || {};
    if (todayPp.date) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">📅 今日干支 <span style="font-weight:400;font-size:0.74rem;color:var(--text-3);">${todayPp.date}</span></div>`;
        html += `<div style="display:flex;gap:12px;justify-content:center;padding:6px 0;">`;
        const todayPillars = [
            {label:'年', data: todayPp.year},
            {label:'月', data: todayPp.month},
            {label:'日', data: todayPp.day},
            {label:'时', data: todayPp.hour},
        ];
        todayPillars.forEach(tp => {
            if (tp.data) {
                html += `<div style="text-align:center;">`;
                html += `<div style="font-size:0.68rem;color:var(--text-3);margin-bottom:2px;">${tp.label}</div>`;
                html += `<div style="font-size:1.1rem;font-weight:700;font-family:var(--font-serif);color:var(--text-1);">${tp.data.gan_zhi || ''}</div>`;
                html += `</div>`;
            }
        });
        html += `</div></div>`;
    }

    // ═══ 起运+节气 合并卡片 ═══
    const hasQiYun = qiYunDetail.text;
    const hasJieQi = jieQiRange.prev_name;
    if (hasQiYun || hasJieQi) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        if (hasQiYun) {
            html += `<div class="card-title">🕐 起运信息</div>`;
            html += `<div class="card-content">`;
            html += `<div>${qiYunDetail.text}</div>`;
            if (qiYunDetail.jiao_yun_text) html += `<div style="margin-top:4px;font-size:0.74rem;color:var(--text-3);">${qiYunDetail.jiao_yun_text}</div>`;
            html += `</div>`;
        }
        if (hasJieQi) {
            if (hasQiYun) html += `<div style="margin:10px 0;border-top:1px solid var(--card-border);"></div>`;
            html += `<div class="card-title">🌿 节气</div>`;
            html += `<div class="card-content">`;
            if (jieQiRange.prev_name) html += `<div>前：${jieQiRange.prev_name} ${jieQiRange.prev_time || ''}</div>`;
            if (jieQiRange.next_name) html += `<div>后：${jieQiRange.next_name} ${jieQiRange.next_time || ''}</div>`;
            if (jieQiRange.after_text) html += `<div style="margin-top:4px;color:var(--text-3);font-size:0.72rem;">${jieQiRange.after_text}</div>`;
            html += `</div>`;
        }
        html += `</div>`;
    }

    // ═══ 性格简析与命理提示 ═══
    const personality = data.personality || {};
    if (personality.summary) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">🎭 性格简析</div>`;
        html += `<div style="font-size:0.84rem;color:var(--text-2);line-height:1.7;margin-bottom:8px;">${personality.summary}</div>`;
        // 性格特征标签
        if (personality.traits && personality.traits.length > 0) {
            html += `<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">`;
            personality.traits.forEach(t => {
                html += `<span style="font-size:0.72rem;padding:3px 10px;border-radius:20px;background:var(--tag-bg);color:var(--accent);border:1px solid var(--accent-glow);">${t}</span>`;
            });
            html += `</div>`;
        }
        // 神煞提示
        if (personality.sha_hints && personality.sha_hints.length > 0) {
            html += `<div style="font-size:0.76rem;color:var(--text-3);margin-bottom:6px;">💡 ${personality.sha_hints.join('；')}</div>`;
        }
        // 负面特征
        if (personality.negative) {
            html += `<div style="font-size:0.74rem;color:var(--danger);margin-bottom:6px;">⚠️ 需注意：${personality.negative}</div>`;
        }
        html += `</div>`;

        // 命理提示卡片
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">📜 命理提示</div>`;
        html += `<div style="font-size:0.82rem;color:var(--text-2);line-height:1.7;margin-bottom:8px;">${personality.advice || ''}</div>`;
        if (personality.career) html += `<div style="font-size:0.78rem;color:var(--info);margin-bottom:4px;">💼 事业：${personality.career}</div>`;
        if (personality.wealth) html += `<div style="font-size:0.78rem;color:var(--success);margin-bottom:4px;">💰 财运：${personality.wealth}</div>`;
        if (personality.relationship) html += `<div style="font-size:0.78rem;color:var(--danger);">💕 感情：${personality.relationship}</div>`;
        html += `</div>`;
    }

    // ═══ 胎元命宫+胎息 合并卡片 ═══
    const taiXi = data.tai_xi || {};
    const hasTMS = taiMingShen.tai_yuan || taiMingShen.ming_gong || taiMingShen.shen_gong;
    const hasTaiXi = taiXi.gan_zhi;
    if (hasTMS || hasTaiXi) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">🔮 胎元宫息</div>`;
        html += `<div class="card-content">`;
        if (taiMingShen.tai_yuan) html += `<div class="mingli-row"><span class="ml-label">胎元</span><span class="ml-value">${wxSpanBZ(taiMingShen.tai_yuan.gan_zhi)}</span><span class="ml-sub">${taiMingShen.tai_yuan.nayin || ''}</span></div>`;
        if (taiMingShen.ming_gong) html += `<div class="mingli-row"><span class="ml-label">命宫</span><span class="ml-value">${wxSpanBZ(taiMingShen.ming_gong.gan_zhi)}</span><span class="ml-sub">${taiMingShen.ming_gong.nayin || ''}</span></div>`;
        if (taiMingShen.shen_gong) html += `<div class="mingli-row"><span class="ml-label">身宫</span><span class="ml-value">${wxSpanBZ(taiMingShen.shen_gong.gan_zhi)}</span><span class="ml-sub">${taiMingShen.shen_gong.nayin || ''}</span></div>`;
        if (hasTaiXi) html += `<div class="mingli-row"><span class="ml-label">胎息</span><span class="ml-value">${wxSpanBZ(taiXi.gan_zhi)}</span><span class="ml-sub">${taiXi.nayin || ''}</span></div>`;
        html += `</div></div>`;
    }

    // ═══ 命卦+星宿 合并卡片 ═══
    const mingGua = data.ming_gua || {};
    const xingSu = data.xing_su || '';
    if (mingGua.gua_name || xingSu) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">🧭 命理信息</div>`;
        html += `<div class="card-content">`;
        if (mingGua.gua_name) html += `<div class="mingli-row"><span class="ml-label">命卦</span><span class="ml-value">${mingGua.gua_name}</span><span class="ml-sub">（${mingGua.group || ''}）</span></div>`;
        if (xingSu) html += `<div class="mingli-row"><span class="ml-label">星宿</span><span class="ml-value">${xingSu}</span></div>`;
        html += `</div></div>`;
    }

    // ═══ 袁天罡称骨 ═══
    const chengGu = data.cheng_gu || {};
    if (chengGu.weight) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">⚖️ 袁天罡称骨</div>`;
        html += `<div class="card-content">`;
        // 骨重大字+进度条
        html += `<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:2px;">`;
        html += `<span style="font-size:1.2rem;font-weight:700;color:var(--accent);">${chengGu.weight}</span>`;
        html += `<span style="font-size:0.72rem;color:var(--text-3);">满分7两2钱</span>`;
        html += `</div>`;
        // 进度条（基于 weight_gram，满值 7.2）
        const weightGram = chengGu.weight_gram || 0;
        const maxWeight = 7.2;
        const barPct = Math.min(100, Math.round((weightGram / maxWeight) * 100));
        html += `<div class="chenggu-bar-track"><div class="chenggu-bar-fill" style="width:${barPct}%"></div></div>`;
        // 各柱骨重明细
        if (chengGu.details) {
            const pillarNames = {year: '年柱', month: '月柱', day: '日柱', hour: '时柱'};
            html += `<div style="display:flex;flex-wrap:wrap;gap:4px 12px;font-size:0.74rem;color:var(--text-3);margin-bottom:8px;">`;
            for (const [p, name] of Object.entries(pillarNames)) {
                const d = chengGu.details[p] || {};
                html += `<span>${name} ${d.gan || ''}${d.zhi || ''} ${d.pillar_w || 0}两</span>`;
            }
            html += `</div>`;
        }
        // 判词（可展开）
        if (chengGu.poem) {
            html += `<div id="chenggu-poem" style="font-size:0.82rem;color:var(--text-2);line-height:1.7;max-height:3.4em;overflow:hidden;cursor:pointer;transition:max-height 0.3s ease;" onclick="this.style.maxHeight=this.style.maxHeight==='3.4em'?'30em':'3.4em'">${chengGu.poem}<span style="color:var(--accent);font-size:0.72rem;display:block;margin-top:2px;">▼ 点击展开</span></div>`;
        }
        html += `</div></div>`;
    }

    // ═══ 五行统计可视化 ═══
    const wxKeys = ['金','木','水','火','土'];
    const wxColors = {'金':'#ef9104','木':'#07e930','水':'#2e83f6','火':'#d30505','土':'#8b6d03'};
    const wxTotal = wxKeys.reduce((s, k) => s + (wx[k] || 0), 0);
    if (wxTotal > 0) {
        const s = getSettings();
        const defaultWxView = s.wx_display || 'count';
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">🔥 五行统计</div>`;
        // 视图切换按钮
        html += `<div class="wx-view-toggle">`;
        html += `<button class="${defaultWxView==='count'?'active':''}" onclick="switchWxView('count',this)">个数</button>`;
        html += `<button class="${defaultWxView==='energy'?'active':''}" onclick="switchWxView('energy',this)">能量</button>`;
        html += `<button class="${defaultWxView==='canggan'?'active':''}" onclick="switchWxView('canggan',this)">含藏干</button>`;
        html += `</div>`;
        // 个数视图
        const maxWx = Math.max(...wxKeys.map(k => wx[k] || 0), 1);
        html += `<div id="wxViewCount" style="${defaultWxView!=='count'?'display:none;':''}">`;
        wxKeys.forEach(k => {
            const cnt = wx[k] || 0;
            const pct = Math.round((cnt / maxWx) * 100);
            html += `<div class="wx-bar">`;
            html += `<span class="wx-name" style="color:${wxColors[k]}">${k}</span>`;
            html += `<div class="wx-track"><div class="wx-fill" style="width:${pct}%;background:${wxColors[k]}"></div></div>`;
            html += `<span class="wx-count" style="color:${wxColors[k]}">${cnt}</span>`;
            html += `</div>`;
        });
        html += `</div>`;
        // 能量视图 - 基于月令旺衰加权
        const wxEnergy = calcWxEnergy(data);
        const maxEnergy = Math.max(...wxKeys.map(k => wxEnergy[k] || 0), 1);
        html += `<div id="wxViewEnergy" style="${defaultWxView!=='energy'?'display:none;':''}">`;
        wxKeys.forEach(k => {
            const val = wxEnergy[k] || 0;
            const pct = Math.round((val / maxEnergy) * 100);
            html += `<div class="wx-bar">`;
            html += `<span class="wx-name" style="color:${wxColors[k]}">${k}</span>`;
            html += `<div class="wx-track"><div class="wx-fill" style="width:${pct}%;background:${wxColors[k]}"></div></div>`;
            html += `<span class="wx-count" style="color:${wxColors[k]}">${val.toFixed(1)}</span>`;
            html += `</div>`;
        });
        html += `</div>`;
        // 含藏干视图
        const cgWx = data.cang_gan_with_wx || {};
        const wxCangGan = calcWxCangGan(data);
        const maxCangGan = Math.max(...wxKeys.map(k => wxCangGan[k] || 0), 1);
        html += `<div id="wxViewCanggan" style="${defaultWxView!=='canggan'?'display:none;':''}">`;
        wxKeys.forEach(k => {
            const val = wxCangGan[k] || 0;
            const pct = Math.round((val / maxCangGan) * 100);
            html += `<div class="wx-bar">`;
            html += `<span class="wx-name" style="color:${wxColors[k]}">${k}</span>`;
            html += `<div class="wx-track"><div class="wx-fill" style="width:${pct}%;background:${wxColors[k]}"></div></div>`;
            html += `<span class="wx-count" style="color:${wxColors[k]}">${val}</span>`;
            html += `</div>`;
        });
        html += `</div>`;
        // 缺五行提示
        const lackWx = data.lack_wuxing || [];
        if (lackWx.length > 0) {
            html += `<div style="margin-top:8px;padding:8px 12px;border-radius:10px;background:rgba(220,100,60,0.08);border:1px solid rgba(220,100,60,0.15);font-size:0.84rem;color:var(--danger);display:flex;align-items:center;gap:6px;">`;
            html += `<span style="font-size:1.1em;">⚠️</span>`;
            html += `<span>五行缺${lackWx.map(k => `<b style="color:${wxColors[k]}">${k}</b>`).join('、')}</span>`;
            html += `</div>`;
        } else {
            html += `<div style="margin-top:8px;padding:8px 12px;border-radius:10px;background:rgba(110,195,135,0.08);border:1px solid rgba(110,195,135,0.15);font-size:0.84rem;color:var(--success);display:flex;align-items:center;gap:6px;">`;
            html += `<span style="font-size:1.1em;">✅</span>`;
            html += `<span>五行俱全</span>`;
            html += `</div>`;
        }
        html += `</div>`;
    }

    // ═══ 日主强弱分析 ═══
    // 统一使用后端 wang_shuai_detail.strength 作为结论，避免前后端算法矛盾
    const riZhuResult = calcRiZhuStrength(data);
    const wsDetailForStrength = data.wang_shuai_detail || {};
    const strengthLabel = wsDetailForStrength.strength || riZhuResult.label;
    const strengthIsStrong = ['身旺','偏旺'].includes(strengthLabel);
    const strengthColorMap = {'身旺':'#07e930','偏旺':'#3CB371','中和':'#ef9104','偏弱':'#CD853F','身弱':'#d30505'};
    html += `<div class="riZhu-strength" style="margin-bottom:14px;">`;
    html += `<div class="strength-label">💪 日主强弱分析</div>`;
    html += `<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">`;
    html += `<span style="font-size:0.84rem;font-weight:700;color:${strengthColorMap[strengthLabel]||'#ef9104'};">${strengthLabel}</span>`;
    html += `<span style="font-size:0.72rem;color:var(--text-3);">印比 ${riZhuResult.yinBiPct}% / 财官杀 ${riZhuResult.caiGuanShaPct}%</span>`;
    html += `</div>`;
    html += `<div class="strength-bar-track">`;
    html += `<div class="strength-bar-fill yin-bi" style="width:${riZhuResult.yinBiPct}%"></div>`;
    html += `</div>`;
    html += `<div class="strength-legend">`;
    html += `<div class="legend-item"><span class="legend-dot" style="background:#07e930;"></span>印比（生助）</div>`;
    html += `<div class="legend-item"><span class="legend-dot" style="background:#d30505;"></span>财官杀（克泄耗）</div>`;
    html += `</div>`;
    html += `</div>`;

    // ═══ 日干旺衰详细分析（时安八字风格） ═══
    const wsDetail = data.wang_shuai_detail || {};
    if (wsDetail.detail) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">📊 日干旺衰详细分析</div>`;
        // 综合判定
        const strengthColor = {'身旺':'#07e930','偏旺':'#3CB371','中和':'#ef9104','偏弱':'#CD853F','身弱':'#d30505'};
        html += `<div style="text-align:center;margin-bottom:10px;">`;
        html += `<span style="font-size:1.2rem;font-weight:700;color:${strengthColor[wsDetail.strength]||'var(--text-1)'};">${wsDetail.strength}</span>`;
        html += `<span style="font-size:0.72rem;color:var(--text-3);margin-left:6px;">(综合得分 ${wsDetail.score}/8)</span>`;
        html += `</div>`;
        // 四维度
        const dims = [
            {key:'ling', label:'得令/失令', icon:'👑'},
            {key:'di', label:'得地/失地', icon:'🏰'},
            {key:'sheng', label:'得生/失生', icon:'💧'},
            {key:'zhu', label:'得助/失助', icon:'🤝'},
        ];
        dims.forEach(dim => {
            const d = wsDetail.detail[dim.key] || {};
            const status = d.status;
            html += `<div style="display:flex;align-items:flex-start;gap:8px;padding:6px 0;border-bottom:1px solid var(--card-border);">`;
            html += `<span style="font-size:0.9em;">${dim.icon}</span>`;
            html += `<div style="flex:1;">`;
            html += `<div style="display:flex;justify-content:space-between;align-items:center;">`;
            html += `<span style="font-size:0.82rem;font-weight:600;">${dim.label}</span>`;
            html += `<span style="font-size:0.76rem;font-weight:600;color:${status?'#07e930':'#d30505'};">${status?'✓ 得':'✗ 失'}${dim.key==='ling'?'令':dim.key==='di'?'地':dim.key==='sheng'?'生':'助'}</span>`;
            html += `</div>`;
            html += `<div style="font-size:0.72rem;color:var(--text-3);margin-top:2px;">${d.text || ''}</div>`;
            html += `</div></div>`;
        });
        html += `</div>`;
    }

    // ═══ 空亡 ═══
    if (kong.length > 0) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">⊘ 空亡</div>`;
        html += `<div class="card-content">${kong.join('、')}</div>`;
        html += `</div>`;
    }

    // ═══ 旺相休囚死 ═══
    if (wangXiangXiu.length > 0) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">⚖️ 五行旺相休囚死</div>`;
        html += `<div class="wxxs-list">`;
        wangXiangXiu.forEach(w => {
            let cls = '';
            if (w.includes('旺')) cls = 'wx-wang';
            else if (w.includes('相')) cls = 'wx-xiang';
            else if (w.includes('休')) cls = 'wx-xiu';
            else if (w.includes('囚')) cls = 'wx-qiu';
            else if (w.includes('死')) cls = 'wx-si';
            html += `<span class="wxxs-tag ${cls}">${w}</span>`;
        });
        html += `</div></div>`;
    }

    // ═══ 神煞 ═══
    const ssList = data.shen_sha || [];
    if (ssList.length > 0) {
        html += `<div style="margin-bottom:14px;">`;
        html += `<div style="font-size:1rem;font-weight:700;margin-bottom:10px;color:var(--text-1);font-family:var(--font-serif);">✨ 神煞</div>`;
        html += `<div style="display:flex;flex-wrap:wrap;gap:6px 8px;">`;
        ssList.forEach(s => {
            html += `<span style="display:inline-block;padding:4px 10px;border-radius:14px;font-size:0.78rem;background:var(--tag-bg);border:1px solid var(--card-border);color:var(--text-2);">${s}</span>`;
        });
        html += `</div></div>`;
    }

    // ═══ 格局分析 ═══
    const geju = data.geju || {};
    if (geju.geju) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">🏯 格局</div>`;
        html += `<div class="card-content">`;
        html += `<div class="mingli-row"><span class="ml-label">格局</span><span class="ml-value" style="color:var(--accent);">${geju.geju}</span></div>`;
        if (geju.desc) html += `<div style="font-size:0.72rem;color:var(--text-3);margin-top:4px;padding-left:54px;">${geju.desc}</div>`;
        html += `</div></div>`;
    }

    // ═══ 调候用神 ═══
    const tiaohou = data.tiaohou || {};
    if (tiaohou.yong_shen) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">🔑 调候用神</div>`;
        html += `<div class="card-content">`;
        html += `<div class="mingli-row"><span class="ml-label">用神</span><span class="ml-value" style="color:#07e930;">${tiaohou.yong_shen}${GAN_WUXING_JS[tiaohou.yong_shen]||''}</span></div>`;
        html += `<div class="mingli-row"><span class="ml-label">喜神</span><span class="ml-value" style="color:#2e83f6;">${tiaohou.xi_shen}${GAN_WUXING_JS[tiaohou.xi_shen]||''}</span></div>`;
        html += `<div class="mingli-row"><span class="ml-label">忌神</span><span class="ml-value" style="color:#d30505;">${tiaohou.ji_shen}${GAN_WUXING_JS[tiaohou.ji_shen]||''}</span></div>`;
        if (tiaohou.desc) html += `<div style="font-size:0.72rem;color:var(--text-3);margin-top:4px;padding-left:54px;">${tiaohou.desc}</div>`;
        html += `</div></div>`;
    }

    // ═══ 干支关系 ═══
    const gzRel = data.ganzhi_relations || {};
    const relTypes = [
        {key:'gan_he', title:'天干五合', icon:'🤝'},
        {key:'gan_chong', title:'天干相冲', icon:'⚡'},
        {key:'zhi_liu_he', title:'地支六合', icon:'🤝'},
        {key:'zhi_san_he', title:'地支三合', icon:'🔺'},
        {key:'zhi_liu_chong', title:'地支六冲', icon:'⚡'},
        {key:'zhi_san_xing', title:'地支三刑', icon:'⚠️'},
        {key:'zhi_liu_hai', title:'地支六害', icon:'⛔'},
        {key:'zhi_liu_po', title:'地支六破', icon:'💔'},
    ];
    let hasRel = false;
    relTypes.forEach(rt => { if ((gzRel[rt.key]||[]).length > 0) hasRel = true; });
    if (hasRel) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">🔗 干支关系</div>`;
        html += `<div class="card-content">`;
        relTypes.forEach(rt => {
            const items = gzRel[rt.key] || [];
            if (items.length > 0) {
                items.forEach(item => {
                    const pillarMap = {year:'年',month:'月',day:'日',hour:'时'};
                    let loc = '';
                    if (item.from && item.to) {
                        loc = `${pillarMap[item.from]||item.from}${pillarMap[item.to]||item.to}`;
                    } else if (item.pillars) {
                        loc = item.pillars.map(p => pillarMap[p]||p).join('');
                    }
                    html += `<div class="mingli-row"><span class="ml-label">${rt.icon}</span><span class="ml-value">${relationLabelBZ(item.desc || '')}</span><span class="ml-sub">${loc}</span></div>`;
                });
            }
        });
        html += `</div></div>`;
    }

    // ═══ 古籍参考 ═══
    const gujiRefs = data.guji_refs || [];
    if (gujiRefs.length > 0) {
        html += `<div class="info-card" style="margin-bottom:14px;">`;
        html += `<div class="card-title">📖 古籍参考</div>`;
        html += `<div class="card-content">`;

        gujiRefs.forEach((ref, idx) => {
            const sourceColors = {'穷通宝鉴': '#ef9104', '三命通会': '#2e83f6', '滴天髓': '#07e930'};
            const sColor = sourceColors[ref.source] || 'var(--accent)';
            html += `<div style="margin-bottom:${idx < gujiRefs.length - 1 ? '12px' : '0'};">`;
            html += `<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">`;
            html += `<span style="display:inline-block;padding:2px 8px;border-radius:10px;background:${sColor}22;color:${sColor};font-size:0.72rem;font-weight:600;">${ref.source}</span>`;
            html += `<span style="font-size:0.8rem;color:var(--text-1);font-weight:600;">${ref.title}</span>`;
            html += `</div>`;
            html += `<div id="gujiText_${idx}" style="font-size:0.78rem;color:var(--text-2);line-height:1.7;padding:8px 12px;border-radius:8px;background:var(--section-alt);max-height:${ref.text.length > 80 ? '3.4em' : 'none'};overflow:hidden;transition:max-height 0.4s var(--ease);position:relative;">`;
            html += _escHtml(ref.text);
            if (ref.text.length > 80) {
                html += `<div id="gujiFade_${idx}" style="position:absolute;bottom:0;left:0;right:0;height:1.8em;background:linear-gradient(transparent,var(--section-alt));pointer-events:none;"></div>`;
            }
            html += `</div>`;
            if (ref.text.length > 80) {
                html += `<button id="gujiBtn_${idx}" onclick="_toggleGujiText(${idx})" style="margin-top:4px;padding:2px 10px;border-radius:6px;border:1px solid var(--card-border);background:transparent;color:var(--text-3);font-size:0.7rem;cursor:pointer;transition:0.2s;">展开全文</button>`;
            }
            html += `</div>`;
        });

        html += `</div></div>`;
    }

    // ═══ 智能四柱图示 ═══
    html += `<div class="info-card" style="margin-bottom:14px;">`;
    html += `<div class="card-title">🔮 四柱关系图</div>`;
    html += `<div class="card-content" style="overflow-x:auto;">`;
    html += renderSizhuDiagram(data);
    html += `</div></div>`;

    return html;
}

// ═══════════════════════════════════════════════════════════════
// 智能四柱图示（SVG渲染）
// ═══════════════════════════════════════════════════════════════

function renderSizhuDiagram(data) {
    const fp = data.four_pillars || {};
    const ss = data.shi_shen || {};
    const gzRel = data.ganzhi_relations || {};

    // 五行颜色
    const WX_COLOR = {'金':'#ef9104','木':'#07e930','水':'#2e83f6','火':'#d30505','土':'#8b6d03'};
    const GAN_WX = GAN_WUXING_JS || {};

    // 四柱数据
    const pillars = ['year', 'month', 'day', 'hour'];
    const pillarNames = ['年柱', '月柱', '日柱', '时柱'];
    const pillarData = pillars.map(p => ({
        key: p,
        name: pillarNames[pillars.indexOf(p)],
        gan: fp[p]?.gan || '',
        zhi: fp[p]?.zhi || '',
        ganZhi: fp[p]?.gan_zhi || '',
        ganWx: GAN_WX[fp[p]?.gan] || '',
        zhiWx: {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}[fp[p]?.zhi] || '',
        shiShen: p === 'day' ? '日主' : (ss[p + '_gan'] || ''),
    }));

    // SVG 参数
    const W = 520, H = 260;
    const pillarX = [80, 190, 300, 410]; // 各柱中心X
    const ganY = 60;   // 天干中心Y
    const zhiY = 170;  // 地支中心Y
    const boxW = 80, boxH = 40;

    let svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:${W}px;font-family:var(--font-sans);">`;

    // ── 背景 ──
    svg += `<defs>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
    </defs>`;

    // ── 柱名标签 ──
    pillarData.forEach((pd, i) => {
        svg += `<text x="${pillarX[i]}" y="22" text-anchor="middle" fill="var(--text-3)" font-size="11">${pd.name}</text>`;
    });

    // ── 天干框 ──
    pillarData.forEach((pd, i) => {
        const color = WX_COLOR[pd.ganWx] || '#888';
        svg += `<rect x="${pillarX[i]-boxW/2}" y="${ganY-boxH/2}" width="${boxW}" height="${boxH}" rx="10" fill="${color}18" stroke="${color}55" stroke-width="1.5"/>`;
        svg += `<text x="${pillarX[i]}" y="${ganY+1}" text-anchor="middle" dominant-baseline="middle" fill="${color}" font-size="18" font-weight="700" font-family="var(--font-serif)">${pd.gan}</text>`;
        // 十神
        if (pd.shiShen && pd.shiShen !== '日主') {
            svg += `<text x="${pillarX[i]}" y="${ganY+boxH/2+14}" text-anchor="middle" fill="var(--text-3)" font-size="9">${pd.shiShen}</text>`;
        } else if (pd.shiShen === '日主') {
            svg += `<text x="${pillarX[i]}" y="${ganY+boxH/2+14}" text-anchor="middle" fill="var(--accent)" font-size="9" font-weight="600">日主</text>`;
        }
    });

    // ── 地支框 ──
    pillarData.forEach((pd, i) => {
        const color = WX_COLOR[pd.zhiWx] || '#888';
        svg += `<rect x="${pillarX[i]-boxW/2}" y="${zhiY-boxH/2}" width="${boxW}" height="${boxH}" rx="10" fill="${color}18" stroke="${color}55" stroke-width="1.5"/>`;
        svg += `<text x="${pillarX[i]}" y="${zhiY+1}" text-anchor="middle" dominant-baseline="middle" fill="${color}" font-size="18" font-weight="700" font-family="var(--font-serif)">${pd.zhi}</text>`;
        // 五行小标签
        svg += `<text x="${pillarX[i]}" y="${zhiY-boxH/2-6}" text-anchor="middle" fill="${color}88" font-size="8">${pd.ganWx || ''}</text>`;
    });

    // ── 连线：天干关系 ──
    // 天干五合 - 虚线绿色
    const ganHe = gzRel.gan_he || [];
    ganHe.forEach(item => {
        const fromIdx = pillars.indexOf(item.from);
        const toIdx = pillars.indexOf(item.to);
        if (fromIdx >= 0 && toIdx >= 0) {
            const x1 = pillarX[fromIdx], x2 = pillarX[toIdx];
            svg += `<line x1="${x1}" y1="${ganY}" x2="${x2}" y2="${ganY}" stroke="#07e930" stroke-width="2" stroke-dasharray="6,3" opacity="0.7"/>`;
            svg += `<text x="${(x1+x2)/2}" y="${ganY-10}" text-anchor="middle" fill="#07e930" font-size="8">合</text>`;
        }
    });

    // 天干冲 - 红色实线
    const ganChong = gzRel.gan_chong || [];
    ganChong.forEach(item => {
        const fromIdx = pillars.indexOf(item.from);
        const toIdx = pillars.indexOf(item.to);
        if (fromIdx >= 0 && toIdx >= 0) {
            const x1 = pillarX[fromIdx], x2 = pillarX[toIdx];
            svg += `<line x1="${x1}" y1="${ganY+boxH/2}" x2="${x2}" y2="${ganY+boxH/2}" stroke="#d30505" stroke-width="2" opacity="0.7"/>`;
            svg += `<text x="${(x1+x2)/2}" y="${ganY+boxH/2+10}" text-anchor="middle" fill="#d30505" font-size="8">冲</text>`;
        }
    });

    // ── 连线：地支关系 ──
    // 地支六合 - 蓝色虚线
    const zhiLiuHe = gzRel.zhi_liu_he || [];
    zhiLiuHe.forEach(item => {
        const fromIdx = pillars.indexOf(item.from);
        const toIdx = pillars.indexOf(item.to);
        if (fromIdx >= 0 && toIdx >= 0) {
            const x1 = pillarX[fromIdx], x2 = pillarX[toIdx];
            svg += `<line x1="${x1}" y1="${zhiY}" x2="${x2}" y2="${zhiY}" stroke="#2e83f6" stroke-width="2" stroke-dasharray="6,3" opacity="0.7"/>`;
            svg += `<text x="${(x1+x2)/2}" y="${zhiY-10}" text-anchor="middle" fill="#2e83f6" font-size="8">六合</text>`;
        }
    });

    // 地支三合 - 紫色虚线三角形
    const zhiSanHe = gzRel.zhi_san_he || [];
    zhiSanHe.forEach(item => {
        const pKeys = item.pillars || [];
        pKeys.forEach((p1, i) => {
            pKeys.forEach((p2, j) => {
                if (j > i) {
                    const idx1 = pillars.indexOf(p1), idx2 = pillars.indexOf(p2);
                    if (idx1 >= 0 && idx2 >= 0) {
                        svg += `<line x1="${pillarX[idx1]}" y1="${zhiY}" x2="${pillarX[idx2]}" y2="${zhiY}" stroke="#8A2BE2" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.6"/>`;
                    }
                }
            });
        });
        // 标签
        const allIdx = pKeys.map(p => pillars.indexOf(p)).filter(i => i >= 0);
        if (allIdx.length >= 2) {
            const midX = allIdx.reduce((a, b) => a + pillarX[b], 0) / allIdx.length;
            svg += `<text x="${midX}" y="${zhiY+boxH/2+14}" text-anchor="middle" fill="#8A2BE2" font-size="8">三合</text>`;
        }
    });

    // 地支六冲 - 红色实线
    const zhiLiuChong = gzRel.zhi_liu_chong || [];
    zhiLiuChong.forEach(item => {
        const fromIdx = pillars.indexOf(item.from);
        const toIdx = pillars.indexOf(item.to);
        if (fromIdx >= 0 && toIdx >= 0) {
            const x1 = pillarX[fromIdx], x2 = pillarX[toIdx];
            svg += `<line x1="${x1}" y1="${zhiY+boxH/2}" x2="${x2}" y2="${zhiY+boxH/2}" stroke="#d30505" stroke-width="2" opacity="0.7"/>`;
            svg += `<text x="${(x1+x2)/2}" y="${zhiY+boxH/2+12}" text-anchor="middle" fill="#d30505" font-size="8">冲</text>`;
        }
    });

    // 地支三刑 - 橙色
    const zhiSanXing = gzRel.zhi_san_xing || [];
    zhiSanXing.forEach(item => {
        const pKeys = item.pillars || [];
        pKeys.forEach((p1, i) => {
            pKeys.forEach((p2, j) => {
                if (j > i) {
                    const idx1 = pillars.indexOf(p1), idx2 = pillars.indexOf(p2);
                    if (idx1 >= 0 && idx2 >= 0) {
                        svg += `<line x1="${pillarX[idx1]}" y1="${zhiY}" x2="${pillarX[idx2]}" y2="${zhiY}" stroke="#FF8C00" stroke-width="1.5" stroke-dasharray="3,3" opacity="0.6"/>`;
                    }
                }
            });
        });
    });

    // 地支六害 - 灰色
    const zhiLiuHai = gzRel.zhi_liu_hai || [];
    zhiLiuHai.forEach(item => {
        const fromIdx = pillars.indexOf(item.from);
        const toIdx = pillars.indexOf(item.to);
        if (fromIdx >= 0 && toIdx >= 0) {
            svg += `<line x1="${pillarX[fromIdx]}" y1="${zhiY}" x2="${pillarX[toIdx]}" y2="${zhiY}" stroke="#888" stroke-width="1.5" stroke-dasharray="4,4" opacity="0.5"/>`;
            svg += `<text x="${(pillarX[fromIdx]+pillarX[toIdx])/2}" y="${zhiY+boxH/2+12}" text-anchor="middle" fill="#888" font-size="8">害</text>`;
        }
    });

    // ── 图例 ──
    const legendY = H - 16;
    const legends = [
        {label: '五合', color: '#07e930', dash: '6,3'},
        {label: '六冲', color: '#d30505', dash: ''},
        {label: '六合', color: '#2e83f6', dash: '6,3'},
        {label: '三合', color: '#8A2BE2', dash: '4,3'},
        {label: '三刑', color: '#FF8C00', dash: '3,3'},
    ];
    let lx = 30;
    legends.forEach(l => {
        svg += `<line x1="${lx}" y1="${legendY}" x2="${lx+20}" y2="${legendY}" stroke="${l.color}" stroke-width="2" ${l.dash ? `stroke-dasharray="${l.dash}"` : ''} opacity="0.8"/>`;
        svg += `<text x="${lx+25}" y="${legendY+3}" fill="var(--text-3)" font-size="9">${l.label}</text>`;
        lx += 68;
    });

    svg += `</svg>`;
    return svg;
}

// ═══ 五行视图切换 ═══
function switchWxView(view, btn) {
    // 切换按钮状态
    document.querySelectorAll('.wx-view-toggle button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    // 切换视图
    const views = ['Count', 'Energy', 'Canggan'];
    views.forEach(v => {
        const el = $('wxView' + v);
        if (el) el.style.display = 'none';
    });
    const targetId = 'wxView' + view.charAt(0).toUpperCase() + view.slice(1);
    const target = $(targetId);
    if (target) target.style.display = '';
}

// ═══ 五行能量计算（基于月令旺衰加权）═══
function calcWxEnergy(data) {
    const wx = data.wu_xing || {};
    const wxEnergy = {'金':0, '木':0, '水':0, '火':0, '土':0};
    const wangXiangXiu = data.wang_xiang_xiu || [];
    // 旺衰权重：旺=2.0, 相=1.5, 休=1.0, 囚=0.6, 死=0.3
    const wxWeightMap = {'旺':2.0, '相':1.5, '休':1.0, '囚':0.6, '死':0.3};
    // 构建五行→旺衰映射
    const wxWangXiang = {};
    wangXiangXiu.forEach(w => {
        const wxName = w.replace(/[旺相休囚死]/g, '');
        const status = w.replace(/[金木水火土]/g, '');
        wxWangXiang[wxName] = wxWeightMap[status] || 1.0;
    });
    wxKeys_global.forEach(k => {
        const weight = wxWangXiang[k] || 1.0;
        wxEnergy[k] = (wx[k] || 0) * weight;
    });
    return wxEnergy;
}
const wxKeys_global = ['金','木','水','火','土'];

// ═══ 含藏干五行统计 ═══
function calcWxCangGan(data) {
    const cgWx = data.cang_gan_with_wx || {};
    const wxCangGan = {'金':0, '木':0, '水':0, '火':0, '土':0};
    const wxMap = {'金':'金','木':'木','水':'水','火':'火','土':'土'};
    Object.values(cgWx).forEach(arr => {
        (arr || []).forEach(s => {
            // s like "丙火", extract last char
            const wxChar = s.slice(-1);
            if (wxCangGan.hasOwnProperty(wxChar)) wxCangGan[wxChar]++;
        });
    });
    return wxCangGan;
}

// ═══ 日主强弱分析 ═══
function calcRiZhuStrength(data) {
    const fp = data.four_pillars || {};
    const ss = data.shi_shen || {};
    const dayGan = fp.day ? fp.day.gan : '';

    // 印比类：比肩、劫财、正印、偏印（食神不算印比，是泄秀）
    // 财官杀类：正财、偏财、正官、七杀、食神、伤官
    const yinBiShiShen = ['比肩','劫财','正印','偏印'];
    const caiGuanShaShiShen = ['正财','偏财','正官','七杀','食神','伤官'];

    let yinBiCount = 0;
    let caiGuanShaCount = 0;

    // 统计四柱天干十神
    ['year_gan','month_gan','hour_gan'].forEach(k => {
        const shiShen = ss[k] || '';
        if (yinBiShiShen.includes(shiShen)) yinBiCount++;
        else if (caiGuanShaShiShen.includes(shiShen)) caiGuanShaCount++;
    });

    // 统计藏干十神
    const cgss = data.cang_gan_shi_shen || {};
    Object.values(cgss).forEach(arr => {
        (arr || []).forEach(s => {
            if (yinBiShiShen.includes(s)) yinBiCount++;
            else if (caiGuanShaShiShen.includes(s)) caiGuanShaCount++;
        });
    });

    const total = yinBiCount + caiGuanShaCount;
    if (total === 0) return {yinBiPct: 50, caiGuanShaPct: 50, isStrong: true, label: '平衡'};

    const yinBiPct = Math.round((yinBiCount / total) * 100);
    const caiGuanShaPct = 100 - yinBiPct;
    const isStrong = yinBiPct > caiGuanShaPct;
    let label = '';
    if (yinBiPct >= 70) label = '身强';
    else if (yinBiPct >= 55) label = '偏强';
    else if (yinBiPct >= 45) label = '中和';
    else if (yinBiPct >= 30) label = '偏弱';
    else label = '身弱';

    return {yinBiPct, caiGuanShaPct, isStrong, label};
}

// ═══════════════════════════════════════════════════════════════
// Tab2: 基本排盘
// ═══════════════════════════════════════════════════════════════

function renderBasicTab(data) {
    const s = getSettings(); // 读取用户设置
    const fp = data.four_pillars || {};
    const ss = data.shi_shen || {};
    const cg = data.cang_gan || {};
    const cgss = data.cang_gan_shi_shen || {};
    const wx = data.wu_xing || {};
    const kong = data.kong_wang || [];
    const ws = data.wang_shuai || '';
    const dayMasterLabel = data.day_master_label || (data.gender === '女' ? '元女' : '元男');
    const cgWx = data.cang_gan_with_wx || {};
    const xingYun = data.xing_yun || {};
    const diShi = data.di_shi || {};
    const ziZuo = data.zi_zuo || {};
    const kongPerPillar = data.kong_wang_per_pillar || {};
    const ssPerPillar = data.shen_sha_per_pillar || {};
    const wangXiangXiu = data.wang_xiang_xiu || [];
    const taiMingShen = data.tai_ming_shen || {};
    const pillars = ['year','month','day','hour'];
    const pillarNames = ['年柱','月柱','日柱','时柱'];

    let html = '';
    html += `<div class="basic-layout">`;

    // 左侧：四柱表格
    html += `<div class="basic-left">`;

    // 胎命身toggle
    html += `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">`;
    html += `<div style="font-size:1rem;font-weight:700;color:var(--text-1);font-family:var(--font-serif);">🏛 四柱命盘</div>`;
    html += `<button class="tms-toggle${_showTMS?' active':''}" onclick="toggleTMS()"><span class="toggle-dot"></span> 胎命身</button>`;
    html += `</div>`;

    // 表格
    html += `<table class="pillar-table">`;

    // 计算列数
    const colCount = _showTMS ? 8 : 5; // label + 4柱 + (胎元+命宫+身宫)

    // colgroup
    html += `<colgroup>`;
    const colWidth = _showTMS ? '13%' : '16%';
    html += `<col style="width:13%">`;
    for (let i = 0; i < colCount - 1; i++) {
        html += `<col style="width:${(100-13)/(colCount-1)}%">`;
    }
    html += `</colgroup>`;

    // 表头
    html += `<tr>`;
    html += `<th></th>`;
    pillarNames.forEach(n => html += `<th>${n}</th>`);
    if (_showTMS) {
        html += `<th>胎元</th><th>命宫</th><th>身宫</th>`;
    }
    html += `</tr>`;

    // Row 1: 主星 (十神/元男/元女)
    html += `<tr>`;
    html += `<td class="row-label">主星</td>`;
    pillars.forEach(p => {
        const s = p === 'day' ? dayMasterLabel : (ss[p + '_gan'] || '');
        const isDay = p === 'day';
        html += `<td style="color:${isDay?'var(--accent)':'var(--text-2)'};font-weight:${isDay?'700':'400'};font-size:0.82rem;">${s}</td>`;
    });
    if (_showTMS) {
        ['tai_yuan','ming_gong','shen_gong'].forEach(k => {
            const gz = taiMingShen[k] ? taiMingShen[k].gan_zhi : '';
            html += `<td style="color:var(--text-2);font-size:0.82rem;">${gz ? wxSpanBZ(gz.charAt(0)) : ''}</td>`;
        });
    }
    html += `</tr>`;

    // Row 2: 天干
    html += `<tr>`;
    html += `<td class="row-label">天干</td>`;
    pillars.forEach(p => {
        const g = fp[p] ? fp[p].gan : '';
        html += `<td class="gan-cell">${wxSpanBZ(g)}</td>`;
    });
    if (_showTMS) {
        ['tai_yuan','ming_gong','shen_gong'].forEach(k => {
            const gz = taiMingShen[k] ? taiMingShen[k].gan_zhi : '';
            html += `<td class="gan-cell">${gz ? wxSpanBZ(gz.charAt(0)) : ''}</td>`;
        });
    }
    html += `</tr>`;

    // Row 3: 地支
    html += `<tr>`;
    html += `<td class="row-label">地支</td>`;
    pillars.forEach(p => {
        const z = fp[p] ? fp[p].zhi : '';
        html += `<td class="zhi-cell">${wxSpanBZ(z)}</td>`;
    });
    if (_showTMS) {
        ['tai_yuan','ming_gong','shen_gong'].forEach(k => {
            const gz = taiMingShen[k] ? taiMingShen[k].gan_zhi : '';
            html += `<td class="zhi-cell">${gz ? wxSpanBZ(gz.charAt(1)) : ''}</td>`;
        });
    }
    html += `</tr>`;

    // Row 4: 藏干 (cang_gan_with_wx) — 可通过设置隐藏
    if (s.show_canggan !== false) {
    html += `<tr>`;
    html += `<td class="row-label">藏干</td>`;
    pillars.forEach(p => {
        const cgWxList = cgWx[p] || [];
        if (cgWxList.length > 0) {
            html += `<td class="cang-gan-cell">${cgWxList.map(s => wxSpanBZ(s)).join(' ')}</td>`;
        } else {
            const cgList = cg[p] || [];
            html += `<td class="cang-gan-cell">${cgList.map(g => wxSpanBZ(g)).join(' ') || '-'}</td>`;
        }
    });
    if (_showTMS) {
        for (let i = 0; i < 3; i++) html += `<td class="cang-gan-cell">-</td>`;
    }
    html += `</tr>`;
    } // end show_canggan

    // Row 5: 副星 (藏干十神) — 跟随藏干设置
    if (s.show_canggan !== false) {
    html += `<tr>`;
    html += `<td class="row-label">副星</td>`;
    pillars.forEach(p => {
        const cgssList = cgss[p] || [];
        html += `<td style="font-size:0.75rem;color:var(--text-3);">${cgssList.join(' ') || '-'}</td>`;
    });
    if (_showTMS) {
        for (let i = 0; i < 3; i++) html += `<td style="font-size:0.75rem;color:var(--text-3);">-</td>`;
    }
    html += `</tr>`;
    } // end show_canggan (副星跟随)

    // Row 6: 星运 (十二长生-按年支) — 可通过设置隐藏
    if (s.show_xingyun !== false) {
    html += `<tr>`;
    html += `<td class="row-label">星运</td>`;
    pillars.forEach(p => {
        const v = xingYun[p] || '';
        html += `<td style="font-size:0.78rem;color:var(--text-2);">${v || '-'}</td>`;
    });
    if (_showTMS) {
        for (let i = 0; i < 3; i++) html += `<td style="font-size:0.78rem;color:var(--text-2);">-</td>`;
    }
    html += `</tr>`;
    } // end show_xingyun

    // Row 7: 自坐 (十二长生-按日支) — 跟随星运设置
    if (s.show_xingyun !== false) {
    html += `<tr>`;
    html += `<td class="row-label">自坐</td>`;
    pillars.forEach(p => {
        const v = ziZuo[p] || '';
        html += `<td style="font-size:0.78rem;color:var(--text-2);">${v || '-'}</td>`;
    });
    if (_showTMS) {
        for (let i = 0; i < 3; i++) html += `<td style="font-size:0.78rem;color:var(--text-2);">-</td>`;
    }
    html += `</tr>`;
    } // end show_xingyun (自坐跟随)

    // Row 8: 空亡 — 可通过设置隐藏
    if (s.show_kongwang !== false) {
    html += `<tr>`;
    html += `<td class="row-label">空亡</td>`;
    pillars.forEach(p => {
        const v = kongPerPillar[p] || '';
        html += `<td style="font-size:0.78rem;color:var(--danger);">${v || '-'}</td>`;
    });
    if (_showTMS) {
        for (let i = 0; i < 3; i++) html += `<td style="font-size:0.78rem;color:var(--danger);">-</td>`;
    }
    html += `</tr>`;
    } // end show_kongwang

    // Row 9: 纳音 — 可通过设置隐藏
    if (s.show_nayin !== false) {
    html += `<tr>`;
    html += `<td class="row-label">纳音</td>`;
    pillars.forEach(p => {
        const ny = fp[p] ? fp[p].nayin : '';
        html += `<td class="nayin-cell">${ny || '-'}</td>`;
    });
    if (_showTMS) {
        ['tai_yuan','ming_gong','shen_gong'].forEach(k => {
            const ny = taiMingShen[k] ? (taiMingShen[k].nayin || '') : '';
            html += `<td class="nayin-cell">${ny || '-'}</td>`;
        });
    }
    html += `</tr>`;
    } // end show_nayin

    // Row 10: 神煞 — 可通过设置隐藏
    if (s.show_shensha !== false) {
    html += `<tr>`;
    html += `<td class="row-label">神煞</td>`;
    pillars.forEach(p => {
        const ssP = ssPerPillar[p] || [];
        if (ssP.length > 0) {
            html += `<td class="shensha-cell">${ssP.map(s => `<span class="ss-tag">${s}</span>`).join('')}</td>`;
        } else {
            html += `<td class="shensha-cell">-</td>`;
        }
    });
    if (_showTMS) {
        for (let i = 0; i < 3; i++) html += `<td class="shensha-cell">-</td>`;
    }
    html += `</tr>`;
    } // end show_shensha (Row 10)

    html += `</table>`;

    // 大运/流年 — 已移至专业排盘

    html += `</div>`; // basic-left

    // 右侧信息
    html += `<div class="basic-right">`;

    // 五行统计
    const wxOrder = ['金','木','水','火','土'];
    const wxTotal = wxOrder.reduce((s, k) => s + (wx[k] || 0), 0) || 1;
    const wxIcons = {'金':'🔶','木':'🌿','水':'💧','火':'🔥','土':'🏔️'};
    html += `<div class="info-card">`;
    html += `<div class="card-title">⚖️ 五行统计</div>`;
    wxOrder.forEach(w => {
        const cnt = wx[w] || 0;
        const pct = Math.round(cnt / wxTotal * 100);
        const color = WX_COLOR_BZ[w];
        html += `<div class="wx-bar">`;
        html += `<span class="wx-name" style="color:${color};">${w}</span>`;
        html += `<div class="wx-track"><div class="wx-fill" style="width:${pct}%;background:${color};"></div></div>`;
        html += `<span class="wx-count">${cnt}</span>`;
        html += `</div>`;
    });
    html += `</div>`;

    // 空亡 + 旺衰
    html += `<div class="info-card">`;
    html += `<div class="card-title">ℹ️ 其他</div>`;
    html += `<div class="card-content">`;
    if (kong.length > 0) html += `<div>空亡：<b style="color:var(--text-1);">${kong.join('、')}</b></div>`;
    if (ws) {
        const _wsDet = data.wang_shuai_detail || {};
        const _wsDisp = _wsDet.strength || ws;
        html += `<div>日干旺衰：<b style="color:var(--text-1);">${_wsDisp}</b></div>`;
    }
    html += `</div></div>`;

    // 旺相休囚死
    if (wangXiangXiu.length > 0) {
        html += `<div class="info-card">`;
        html += `<div class="card-title">🔄 旺相休囚死</div>`;
        html += `<div class="wxxs-list">`;
        wangXiangXiu.forEach(w => {
            let cls = '';
            if (w.includes('旺')) cls = 'wx-wang';
            else if (w.includes('相')) cls = 'wx-xiang';
            else if (w.includes('休')) cls = 'wx-xiu';
            else if (w.includes('囚')) cls = 'wx-qiu';
            else if (w.includes('死')) cls = 'wx-si';
            html += `<span class="wxxs-tag ${cls}">${w}</span>`;
        });
        html += `</div></div>`;
    }

    html += `</div>`; // basic-right
    html += `</div>`; // basic-layout

    return html;
}

// ═══════════════════════════════════════════════════════════════
// Tab3: 专业细盘
// ═══════════════════════════════════════════════════════════════

function renderProTab(data) {
    const fp = data.four_pillars || {};
    const ss = data.shi_shen || {};
    const cg = data.cang_gan || {};
    const cgss = data.cang_gan_shi_shen || {};
    const wx = data.wu_xing || {};
    const kong = data.kong_wang || [];
    const ws = data.wang_shuai || '';
    const dy = data.da_yun || [];
    const ln = data.liu_nian || [];
    const dyDir = data.da_yun_direction || '顺';
    const qiAge = data.qi_yun_age || 0;
    const dayMasterLabel = data.day_master_label || (data.gender === '女' ? '元女' : '元男');
    const cgWx = data.cang_gan_with_wx || {};
    const xingYun = data.xing_yun || {};
    const diShi = data.di_shi || {};
    const ziZuo = data.zi_zuo || {};
    const kongPerPillar = data.kong_wang_per_pillar || {};
    const ssPerPillar = data.shen_sha_per_pillar || {};
    const wangXiangXiu = data.wang_xiang_xiu || [];
    const qiYunDetail = data.qi_yun_detail || {};
    const xiaoYun = data.xiao_yun || [];
    const _baziDayGan = fp.day ? fp.day.gan : '';
    const taiMingShen = data.tai_ming_shen || {};
    const shengXiao = data.sheng_xiao || '';

    const pillars = ['year','month','day','hour'];
    const pillarNames = ['年柱','月柱','日柱','时柱'];

    // 当前选中的大运
    const activeDy = _activeDayunIdx >= 0 && _activeDayunIdx < dy.length ? dy[_activeDayunIdx] : null;
    // 当前选中的流年
    const activeLn = _activeLiunianIdx >= 0 && _activeLiunianIdx < ln.length ? ln[_activeLiunianIdx] : null;

    // 流年列表：智能显示（默认以当前年份为中心，手动点击大运时显示大运范围）
    const _currentYear = new Date().getFullYear();
    const _inDyRange = activeDy && _currentYear >= activeDy.start_year && _currentYear <= activeDy.end_year;
    let lnInDy;
    if (activeDy) {
        if (_dayunUserSelected && !_inDyRange) {
            // 用户手动点击了不含当前年份的大运：显示该大运的全部流年
            lnInDy = ln.filter(l => l.year >= activeDy.start_year && l.year <= activeDy.end_year);
        } else if (_inDyRange) {
            // 当前年份在大运范围内：以当前年份为中心，限制在大运范围内
            const lnStart = Math.max(activeDy.start_year, _currentYear - 5);
            const lnEnd = Math.min(activeDy.end_year, _currentYear + 5);
            lnInDy = ln.filter(l => l.year >= lnStart && l.year <= lnEnd);
        } else {
            // 当前年份不在大运范围内（未起运等）：以当前年份为中心
            lnInDy = ln.filter(l => l.year >= _currentYear - 5 && l.year <= _currentYear + 5);
        }
    } else {
        lnInDy = [];
    }

    // 数据行定义（四柱与大运共用）— 时安八字专业细盘完整行
    // 时安八字行顺序：十神→天干→地支→藏干→副星→星运→纳音→地势→空亡→神煞
    const rows = [
        { label: '十神', key: 'zhuxing' },
        { label: '天干', key: 'tiangan' },
        { label: '地支', key: 'dizhi' },
        { label: '藏干', key: 'canggan' },
        { label: '副星', key: 'fuxing' },
        { label: '星运', key: 'xingyun' },
        { label: '纳音', key: 'nayin' },
        { label: '地势', key: 'changsheng' },
        { label: '空亡', key: 'kongwang' },
        { label: '神煞', key: 'shensha' },
    ];

    // 判断当前选中的大运是否为起运前（小运期）
    const isPreQiYun = activeDy && activeDy.start_age < qiAge;
    // 左侧标签：起运前显示"小运"，起运后显示"大运"
    const dayunLabel = isPreQiYun ? '小运' : '大运';

    // 流年专用行（不再显示小运行 — 小运信息通过大运区左侧标签标识）
    const lnRows = [...rows];

    let html = '';
    html += `<div class="pro-layout">`;

    // ═══ 时安风格：顶部案例信息行 ═══
    const caseNum = data.case_number || data.id || '';
    html += `<div class="pro-top-bar">`;
    html += `<div class="pro-case-info">`;
    if (caseNum) {
        html += `<span class="pro-case-number">案例${caseNum}</span>`;
    }
    html += `<span class="pro-date-type">${data.birth_lunar ? '农历' : '公历'}</span>`;
    html += `</div>`;
    html += `<div style="display:flex;align-items:center;gap:8px;">`;
    html += `<button class="tms-toggle${_showTMS?' active':''}" onclick="toggleTMS()"><span class="toggle-dot"></span> 胎命身</button>`;
    html += `<button class="nav-edit-btn" onclick="goBack()">✏️ 编辑</button>`;
    html += `</div>`;
    html += `</div>`;

    // ═══ 时安风格：胎元命宫身宫行 ═══
    if (_showTMS) {
        html += `<div class="pro-tms-bar">`;
        ['tai_yuan','ming_gong','shen_gong'].forEach(k => {
            const gz = taiMingShen[k] ? taiMingShen[k].gan_zhi : '';
            const label = {'tai_yuan':'胎元','ming_gong':'命宫','shen_gong':'身宫'}[k];
            const nayin = taiMingShen[k] ? taiMingShen[k].nayin : '';
            html += `<div class="pro-tms-item">`;
            html += `<div class="pro-tms-label">${label}</div>`;
            html += `<div class="pro-tms-value">${gz ? wxSpanBZ(gz) : '-'}${nayin ? `<span style="font-size:0.62rem;color:var(--text-3);margin-left:4px;">${nayin}</span>` : ''}</div>`;
            html += `</div>`;
        });
        html += `</div>`;
    }

    // 起运信息 + 五行统计条（同一行）
    const wxData = data.wu_xing || {};
    const wxCount = wxData;
    const geju = data.geju || {};
    const lackWx = wxData.lack || data.lack_wuxing || [];
    const wangShuai = (data.wang_shuai_detail || {}).strength || data.wang_shuai || '';

    html += `<div class="pro-summary-bar">`;
    // 起运信息
    if (qiYunDetail.text) {
        html += `<span class="qiyun-text" style="font-size:0.72rem;color:var(--text-2);">🕐 ${qiYunDetail.text}${qiYunDetail.jiao_yun_text ? ' · ' + qiYunDetail.jiao_yun_text : ''}</span>`;
    }
    // 五行统计
    const wxItems = [
        {name: '金', count: wxCount['金'] || 0, color: '#ef9104'},
        {name: '木', count: wxCount['木'] || 0, color: '#07e930'},
        {name: '水', count: wxCount['水'] || 0, color: '#2e83f6'},
        {name: '火', count: wxCount['火'] || 0, color: '#d30505'},
        {name: '土', count: wxCount['土'] || 0, color: '#8b6d03'},
    ];
    html += `<div class="pro-wx-bar">`;
    wxItems.forEach(w => {
        html += `<span class="pro-wx-item" style="color:${w.color};">`;
        html += `<span class="wx-dot wx-${w.name === '金' ? 'metal' : w.name === '木' ? 'wood' : w.name === '水' ? 'water' : w.name === '火' ? 'fire' : 'earth'}"></span>`;
        html += `${w.name}${w.count}`;
        html += `</span>`;
    });
    if (lackWx.length > 0) {
        html += `<span class="pro-wx-lack">缺${lackWx.join('')}</span>`;
    }
    html += `</div>`;
    // 旺衰 + 格局
    html += `<div class="pro-geju-info">`;
    if (wangShuai) html += `<span class="pro-ws-tag">${wangShuai}</span>`;
    if (geju.geju) html += `<span class="pro-geju-tag">${geju.geju}</span>`;
    html += `</div>`;
    html += `</div>`;

    // ═══ 统一容器：四柱+大运+流年+流月 ═══
    const pillarColCount = _showTMS ? 7 : 4;
    const totalLeftCols = 1 + pillarColCount;

    html += `<div class="pro-unified-row">`;

    // ── 左侧：四柱 + 流年标签 + 流月标签（固定不滚） ──
    html += `<div class="pro-unified-left" id="proUnifiedLeft">`;
    html += `<table class="pro-unified-table">`;
    // thead: 四柱列头
    html += `<thead><tr>`;
    html += `<th class="col-label"><span>&nbsp;</span><span class="dy-header-age" style="visibility:hidden;">&nbsp;</span></th>`;
    pillars.forEach((n, pi) => {
        const isDayPillar = pillars[pi] === 'day';
        const gz = fp[pillars[pi]] ? fp[pillars[pi]].gan_zhi : '';
        html += `<th class="col-pillar${isDayPillar?' day-pillar-header':''}" onclick="selectDayun(-1)">`;
        html += `<span>${n}</span>`;
        if (gz) html += `<span class="pillar-gz-preview">${wxSpanBZ(gz)}</span>`;
        html += `</th>`;
    });
    if (_showTMS) {
        ['tai_yuan','ming_gong','shen_gong'].forEach(k => {
            const gz = taiMingShen[k] ? taiMingShen[k].gan_zhi : '';
            const label = {'tai_yuan':'胎元','ming_gong':'命宫','shen_gong':'身宫'}[k];
            html += `<th class="col-pillar"><span>${label}</span>${gz ? `<span class="pillar-gz-preview">${wxSpanBZ(gz)}</span>` : ''}</th>`;
        });
    }
    html += `</tr></thead>`;
    html += `<tbody>`;

    // ═══ 四柱区 (10行) ═══
    rows.forEach(row => {
        html += `<tr>`;
        html += `<td class="col-label">${row.label}</td>`;
        pillars.forEach(p => {
            const isDayPillar = p === 'day';
            html += `<td class="col-pillar${isDayPillar?' day-pillar-cell':''}">${_proCellContent(row.key, p, {fp, ss, cg, cgss, cgWx, xingYun, diShi, ziZuo, kongPerPillar, ssPerPillar, dayMasterLabel, taiMingShen, ganzhiRelations: data.ganzhi_relations || {}})}</td>`;
        });
        if (_showTMS) {
            ['tai_yuan','ming_gong','shen_gong'].forEach(k => {
                html += `<td class="col-pillar">${_proTmsCellContent(row.key, k, taiMingShen)}</td>`;
            });
        }
        html += `</tr>`;
    });

    // ═══ 大运/小运区分隔 + 标签 ═══
    html += `<tr class="pro-separator-row"><td colspan="${totalLeftCols}"></td></tr>`;
    html += `<tr class="pro-section-label-row">`;
    html += `<td class="col-label">🎯</td>`;
    html += `<td colspan="${pillarColCount}" class="pro-section-label-text">${dayunLabel} <span class="section-badge">${activeDy ? activeDy.gan_zhi : ''}</span></td>`;
    html += `</tr>`;
    // 大运/小运行标签（与右侧大运数据行对应）
    rows.forEach(row => {
        html += `<tr>`;
        html += `<td class="col-label">${row.label}</td>`;
        html += `<td colspan="${pillarColCount}"></td>`;
        html += `</tr>`;
    });

    // ═══ 流年区 ═══
    if (activeDy && lnInDy.length > 0) {
        // separator
        html += `<tr class="pro-separator-row"><td colspan="${totalLeftCols}"></td></tr>`;
        // section label
        html += `<tr class="pro-section-label-row">`;
        html += `<td class="col-label">📅</td>`;
        html += `<td colspan="${pillarColCount}" class="pro-section-label-text">流年 <span class="section-badge">${activeDy.start_year}-${activeDy.end_year}</span></td>`;
        html += `</tr>`;
        // liunian label rows
        lnRows.forEach(row => {
            html += `<tr>`;
            html += `<td class="col-label">${row.label}</td>`;
            html += `<td colspan="${pillarColCount}"></td>`;
            html += `</tr>`;
        });
    }

    // ═══ 流月区 ═══
    if (activeLn) {
        // separator
        html += `<tr class="pro-separator-row"><td colspan="${totalLeftCols}"></td></tr>`;
        // section label
        html += `<tr class="pro-section-label-row">`;
        html += `<td class="col-label">📆</td>`;
        html += `<td colspan="${pillarColCount}" class="pro-section-label-text">流月 <span class="section-badge">${activeLn.year}年</span></td>`;
        html += `</tr>`;
        // liuyue placeholder row
        html += `<tr id="proLiuYueRowLeft"><td colspan="${totalLeftCols}" style="height:1px;padding:0;"></td></tr>`;
    }

    html += `</tbody></table></div>`;

    // ── 右侧：大运 + 流年 + 流月数据（横滚） ──
    html += `<div class="pro-unified-right" id="proUnifiedRight">`;

    // ── 大运/小运表格 ──
    html += `<table class="pro-unified-table pro-dayun-rows">`;
    html += `<thead><tr>`;
    dy.forEach((d, i) => {
        const isActive = i === _activeDayunIdx;
        const isCurrent = isCurrentDayun(d);
        // 判断该大运是否为起运前（小运期）
        const isPreQi = d.start_age < qiAge;
        const colLabel = isPreQi ? '小运' : '大运';
        html += `<th class="col-dayun${isActive?' dy-active':''}" onclick="selectDayun(${i})" title="${colLabel}">`;
        // 在表头显示"大运"/"小运"标签（直观可见，不仅是tooltip）
        html += `<span style="font-size:0.52rem;color:var(--accent);font-weight:600;display:block;">${colLabel}</span>`;
        html += `<span class="dy-header-year">${d.start_year}</span>`;
        html += `<span class="dy-header-age">${d.start_age}-${d.end_age}岁</span>`;
        if (isCurrent) html += `<span class="dy-header-active-mark">今</span>`;
        html += `</th>`;
    });
    html += `</tr></thead>`;
    html += `<colgroup>`;
    dy.forEach(() => { html += `<col style="width:48px;">`; });
    html += `</colgroup>`;
    html += `<tbody>`;
    rows.forEach(row => {
        html += `<tr>`;
        dy.forEach((d, i) => {
            // 起运前：大运列显示小运干支数据
            const isPreQi = d.start_age < qiAge;
            let cellContent;
            if (isPreQi && xiaoYun.length > 0) {
                // 起运前：用小运数据填充大运列
                cellContent = _proXiaoyunCellContent(row.key, d, _baziDayGan, xiaoYun);
            } else {
                cellContent = _proDayunCellContent(row.key, d, _baziDayGan);
            }
            html += `<td class="col-dayun${i === _activeDayunIdx ? ' dy-active' : ''}" onclick="selectDayun(${i})">${cellContent}</td>`;
        });
        html += `</tr>`;
    });
    html += `</tbody></table>`;

    // ── 流年区 ──
    if (activeDy && lnInDy.length > 0) {
        // separator
        html += `<div class="pro-section-divider"></div>`;
        // liunian table
        html += `<table class="pro-unified-table pro-liunian-rows">`;
        // liunian year header row
        html += `<thead><tr>`;
        lnInDy.forEach((l, i) => {
            const realIdx = ln.indexOf(l);
            const isActive = realIdx === _activeLiunianIdx;
            const isCurrent = l.year === new Date().getFullYear();
            html += `<th class="col-liunian${isActive?' ln-active':''}" onclick="selectLiunian(${realIdx})">`;
            html += `<span>${l.year}</span>`;
            if (isCurrent) html += `<span style="font-size:0.5rem;color:var(--accent);display:block;">今</span>`;
            html += `</th>`;
        });
        html += `</tr></thead>`;
        html += `<colgroup>`;
        lnInDy.forEach(() => { html += `<col style="width:48px;">`; });
        html += `</colgroup>`;
        html += `<tbody>`;
        lnRows.forEach(row => {
            html += `<tr>`;
            lnInDy.forEach((l, i) => {
                const realIdx = ln.indexOf(l);
                const isActive = realIdx === _activeLiunianIdx;
                let cellContent;
                if (row.key === 'xiaoyun') {
                    const xygz = l.xiao_yun_gan_zhi || '';
                    if (xygz) {
                        cellContent = `<span class="gz-cell" style="font-size:0.82rem;color:var(--info);">${wxSpanBZ(xygz)}</span>`;
                    } else {
                        cellContent = '-';
                    }
                } else {
                    cellContent = _proLiunianCellContent(row.key, l, _baziDayGan);
                }
                html += `<td class="col-liunian${isActive?' ln-active':''}" onclick="selectLiunian(${realIdx})">${cellContent}</td>`;
            });
            html += `</tr>`;
        });
        html += `</tbody></table>`;
    }

    // ── 流月区 ──
    if (activeLn) {
        html += `<div class="pro-section-divider"></div>`;
        html += `<div id="proLiuYueRow" class="pro-liuyue-area"></div>`;
    }

    html += `</div>`; // pro-unified-right

    html += `</div>`; // pro-unified-row

    // 流日展开区
    html += `<div id="proDrillArea" style="margin-top:8px;"></div>`;

    // ═══ 冲合关系可视化（时安风格） ═══
    const gr = data.ganzhi_relations || {};
    const allRelations = [];
    (gr.gan_he || []).forEach(r => allRelations.push({...r, type: '合', color: '#07e930', level: 'gan'}));
    (gr.gan_chong || []).forEach(r => allRelations.push({...r, type: '冲', color: '#d30505', level: 'gan'}));
    (gr.zhi_liu_he || []).forEach(r => allRelations.push({...r, type: '合', color: '#07e930', level: 'zhi'}));
    (gr.zhi_san_he || []).forEach(r => allRelations.push({...r, type: '三合', color: '#2e83f6', level: 'zhi'}));
    (gr.zhi_ban_he || []).forEach(r => allRelations.push({...r, type: '半合', color: '#5bc0de', level: 'zhi'}));
    (gr.zhi_an_he || []).forEach(r => allRelations.push({...r, type: '暗合', color: '#8e6fbf', level: 'zhi'}));
    (gr.zhi_san_hui || []).forEach(r => allRelations.push({...r, type: '三会', color: '#e67e22', level: 'zhi'}));
    (gr.zhi_liu_chong || []).forEach(r => allRelations.push({...r, type: '冲', color: '#d30505', level: 'zhi'}));
    (gr.zhi_liu_hai || []).forEach(r => allRelations.push({...r, type: '害', color: '#ef9104', level: 'zhi'}));
    (gr.zhi_liu_po || []).forEach(r => allRelations.push({...r, type: '破', color: '#888', level: 'zhi'}));
    (gr.zhi_san_xing || []).forEach(r => allRelations.push({...r, type: '刑', color: '#d30505', level: 'zhi'}));

    if (allRelations.length > 0) {
        html += `<div style="margin-top:12px;">`;
        html += `<div class="pro-section-title">🔗 冲合关系</div>`;
        html += `<div class="relation-tags">`;
        allRelations.forEach(r => {
            const label = r.level === 'gan' ? '干' : '支';
            html += `<span class="relation-tag" style="border-color:${r.color};color:${r.color};">${label}${r.type} ${relationLabelBZ(r.desc || '')}</span>`;
        });
        html += `</div></div>`;
    }

    // 旺相休囚死
    if (wangXiangXiu.length > 0) {
        html += `<div style="margin-top:12px;">`;
        html += `<div class="pro-section-title">🔄 旺相休囚死</div>`;
        html += `<div class="wxxs-list">`;
        wangXiangXiu.forEach(w => {
            let cls = '';
            if (w.includes('旺')) cls = 'wx-wang';
            else if (w.includes('相')) cls = 'wx-xiang';
            else if (w.includes('休')) cls = 'wx-xiu';
            else if (w.includes('囚')) cls = 'wx-qiu';
            else if (w.includes('死')) cls = 'wx-si';
            html += `<span class="wxxs-tag ${cls}">${w}</span>`;
        });
        html += `</div></div>`;
    }

    // ═══ 参考用神 + 称骨（时安风格底部信息） ═══
    const tiaohou = data.tiaohou || {};
    const chengGu = data.cheng_gu || {};
    const gejuDesc = geju.desc || '';

    html += `<div class="pro-bottom-info">`;
    // 参考用神/调候
    if (tiaohou.yong_shen || tiaohou.tiao_hou) {
        html += `<div class="pro-bottom-card">`;
        html += `<div class="pro-bottom-card-title">⚡ 参考用神</div>`;
        html += `<div class="pro-bottom-card-content">`;
        if (tiaohou.yong_shen) html += `<span class="info-tag yong-tag">用 ${tiaohou.yong_shen}</span>`;
        if (tiaohou.tiao_hou) html += `<span class="info-tag tiao-tag">候 ${tiaohou.tiao_hou}</span>`;
        if (tiaohou.xi_shen) html += `<span class="info-tag xi-tag">喜 ${tiaohou.xi_shen}</span>`;
        if (tiaohou.ji_shen) html += `<span class="info-tag ji-tag">忌 ${tiaohou.ji_shen}</span>`;
        html += `</div></div>`;
    }
    // 格局
    if (gejuDesc) {
        html += `<div class="pro-bottom-card">`;
        html += `<div class="pro-bottom-card-title">🏛 格局</div>`;
        html += `<div class="pro-bottom-card-content">${gejuDesc}</div>`;
        html += `</div>`;
    }
    // 袁天罡称骨
    if (chengGu.weight) {
        html += `<div class="pro-bottom-card">`;
        html += `<div class="pro-bottom-card-title">⚖ 袁天罡称骨</div>`;
        html += `<div class="pro-bottom-card-content">`;
        html += `<span class="chenggu-weight">${chengGu.weight}</span>`;
        if (chengGu.poem) html += `<span class="chenggu-poem">${chengGu.poem}</span>`;
        html += `</div></div>`;
    }
    html += `</div>`;

    html += `</div>`; // pro-layout

    // 异步加载流月
    if (activeLn) {
        setTimeout(() => loadProLiuYueHorizontal(), 50);
    }

    // 同步左右两表垂直滚动
    setTimeout(() => {
        const leftSec = document.getElementById('proUnifiedLeft');
        const rightSec = document.getElementById('proUnifiedRight');
        if (leftSec && rightSec) {
            rightSec.addEventListener('scroll', () => {
                leftSec.scrollTop = rightSec.scrollTop;
            });
            leftSec.addEventListener('scroll', () => {
                rightSec.scrollTop = leftSec.scrollTop;
            });
        }
    }, 100);

    return html;
}

// ═══════════════════════════════════════════════════════════════
// 专业细盘 - 单元格内容渲染
// ═══════════════════════════════════════════════════════════════

function _csClass(name) {
    // 长生十二运颜色类
    if (name === '帝旺') return 'cs-wang';
    if (name === '临官') return 'cs-xiang';
    if (name === '长生' || name === '冠带') return 'cs-xiang';
    if (name === '衰' || name === '病') return 'cs-qiu';
    if (name === '死' || name === '墓' || name === '绝') return 'cs-si';
    if (name === '沐浴' || name === '胎' || name === '养') return 'cs-xiu';
    return '';
}

// 四柱单元格内容
function _proCellContent(key, p, ctx) {
    const {fp, ss, cg, cgss, cgWx, xingYun, diShi, ziZuo, kongPerPillar, ssPerPillar, dayMasterLabel, taiMingShen} = ctx;
    const isDay = p === 'day';
    switch (key) {
        case 'zhuxing': {
            const s = isDay ? dayMasterLabel : (ss[p + '_gan'] || '');
            return `<span style="color:${isDay?'var(--accent)':'var(--text-2)'};font-weight:${isDay?'700':'400'};font-size:0.76rem;">${s}</span>`;
        }
        case 'tiangan': {
            const gan = fp[p] ? fp[p].gan : '';
            const isDayGan = isDay;
            return `<span class="gz-cell${isDayGan?' day-master-gan':''}">${wxSpanBZ(gan)}</span>`;
        }
        case 'dizhi':
            return `<span class="gz-cell">${wxSpanBZ(fp[p] ? fp[p].zhi : '')}</span>`;
        case 'canggan': {
            const cgWxList = cgWx[p] || [];
            if (cgWxList.length > 0) {
                return `<span class="cg-cell">${cgWxList.map(s => wxSpanBZ(s)).join(' ')}</span>`;
            }
            const cgList = cg[p] || [];
            return `<span class="cg-cell">${cgList.map(g => wxSpanBZ(g)).join(' ') || '-'}</span>`;
        }
        case 'fuxing': {
            const cgssList = cgss[p] || [];
            return `<span class="ss-cell">${cgssList.join(' ') || '-'}</span>`;
        }
        case 'changsheng': {
            // 地势（十二长生 - 天干对自身地支）
            const val = diShi[p] || '';
            const cls = _csClass(val);
            return `<span class="changsheng-cell ${cls}">${val || '-'}</span>`;
        }
        case 'xingyun':
            return `<span class="xingyun-cell">${xingYun[p] || '-'}</span>`;
        case 'zizuo':
            return `<span class="zizuo-cell">${ziZuo[p] || '-'}</span>`;
        case 'kongwang':
            return `<span class="kong-cell">${kongPerPillar[p] || '-'}</span>`;
        case 'nayin':
            return `<span class="nayin-cell">${fp[p] ? fp[p].nayin : '-'}</span>`;
        case 'shensha': {
            const ssP = ssPerPillar[p] || [];
            if (ssP.length > 0) {
                return `<span class="shensha-cell">${ssP.map(s => `<span class="ss-tag">${s}</span>`).join('')}</span>`;
            }
            return '-';
        }
        case 'xiaoyun':
            return '-';
        case 'chonghe': {
            const gr = ctx.ganzhiRelations || {};
            const rels = [];
            const pillarLabel = {'year':'年','month':'月','day':'日','hour':'时'}[p] || p;
            (gr.gan_he || []).forEach(r => {
                if (r.from === p || r.to === p) rels.push(`<span style="color:#07e930;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`);
            });
            (gr.gan_chong || []).forEach(r => {
                if (r.from === p || r.to === p) rels.push(`<span style="color:#d30505;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`);
            });
            (gr.zhi_liu_he || []).forEach(r => {
                if (r.from === p || r.to === p) rels.push(`<span style="color:#07e930;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`);
            });
            (gr.zhi_liu_chong || []).forEach(r => {
                if (r.from === p || r.to === p) rels.push(`<span style="color:#d30505;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`);
            });
            (gr.zhi_liu_hai || []).forEach(r => {
                if (r.from === p || r.to === p) rels.push(`<span style="color:#ef9104;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`);
            });
            return rels.length > 0 ? rels.join(' ') : '-';
        }
        default: return '-';
    }
}

// 胎命身单元格内容
function _proTmsCellContent(key, k, taiMingShen) {
    const gz = taiMingShen[k] ? taiMingShen[k].gan_zhi : '';
    switch (key) {
        case 'tiangan':
            return gz ? `<span class="gz-cell">${wxSpanBZ(gz.charAt(0))}</span>` : '-';
        case 'dizhi':
            return gz ? `<span class="gz-cell">${wxSpanBZ(gz.charAt(1))}</span>` : '-';
        case 'nayin':
            return `<span class="nayin-cell">${taiMingShen[k] ? (taiMingShen[k].nayin || '-') : '-'}</span>`;
        default: return '-';
    }
}

// 大运单元格内容
function _proDayunCellContent(key, d, dayGan) {
    switch (key) {
        case 'zhuxing':
            return `<span style="color:var(--text-2);font-size:0.76rem;">${d.gan_shishen_abbrev || ''}</span>`;
        case 'tiangan':
            return `<span class="gz-cell">${wxSpanBZ(d.gan)}</span>`;
        case 'dizhi':
            return `<span class="gz-cell">${wxSpanBZ(d.zhi)}</span>`;
        case 'canggan': {
            const cg = d.cang_gan || [];
            return `<span class="cg-cell">${cg.map(g => wxSpanBZ(g)).join(' ') || '-'}</span>`;
        }
        case 'fuxing': {
            const cgss = d.cang_gan_shi_shen || [];
            return `<span class="ss-cell">${cgss.join(' ') || '-'}</span>`;
        }
        case 'changsheng': {
            const val = d.chang_sheng || '';
            const cls = _csClass(val);
            return `<span class="changsheng-cell ${cls}">${val || '-'}</span>`;
        }
        case 'xingyun':
            return `<span class="xingyun-cell">${d.xing_yun || '-'}</span>`;
        case 'zizuo':
            return `<span class="zizuo-cell">${d.zi_zuo || '-'}</span>`;
        case 'kongwang':
            return `<span class="kong-cell">${d.kong_wang || '-'}</span>`;
        case 'nayin':
            return `<span class="nayin-cell">${d.nayin || '-'}</span>`;
        case 'xiaoyun':
            return '-';
        case 'shensha': {
            const ss = d.shen_sha || [];
            if (ss.length > 0) {
                return `<span class="shensha-cell">${ss.map(s => `<span class="ss-tag">${s}</span>`).join('')}</span>`;
            }
            return '-';
        }
        case 'chonghe': {
            const pr = d.pillar_relations || {};
            const allRels = [
                ...(pr.gan_he || []).map(r => `<span style="color:#07e930;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`),
                ...(pr.gan_chong || []).map(r => `<span style="color:#d30505;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`),
                ...(pr.zhi_liu_he || []).map(r => `<span style="color:#07e930;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`),
                ...(pr.zhi_liu_chong || []).map(r => `<span style="color:#d30505;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`),
                ...(pr.zhi_liu_hai || []).map(r => `<span style="color:#ef9104;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`),
            ];
            return allRels.length > 0 ? allRels.join(' ') : '-';
        }
        default: return '-';
    }
}

// 起运前小运单元格内容（在大运列位置显示小运数据）
function _proXiaoyunCellContent(key, d, dayGan, xiaoYunList) {
    // d 是起运前的大运项，包含 start_age 和 end_age
    // 取该年龄段中间的小运干支
    const midAge = Math.floor((d.start_age + d.end_age) / 2);
    const xyIdx = midAge - 1; // xiaoYunList[0] = age 1
    const xy = (xiaoYunList && xyIdx >= 0 && xyIdx < xiaoYunList.length) ? xiaoYunList[xyIdx] : null;
    if (!xy) return '-';

    const xyGan = xy.gan || '';
    const xyZhi = xy.zhi || '';

    switch (key) {
        case 'zhuxing':
            return `<span style="color:var(--text-2);font-size:0.76rem;">${xy.gan_shishen_abbrev || (xyGan ? getShiShenLocal(dayGan, xyGan) : '')}</span>`;
        case 'tiangan':
            return xyGan ? `<span class="gz-cell">${wxSpanBZ(xyGan)}</span>` : '-';
        case 'dizhi':
            return xyZhi ? `<span class="gz-cell">${wxSpanBZ(xyZhi)}</span>` : '-';
        case 'canggan': {
            const cg = CANG_GAN_LOCAL[xyZhi] || [];
            return `<span class="cg-cell">${cg.map(g => wxSpanBZ(g)).join(' ') || '-'}</span>`;
        }
        case 'fuxing': {
            const cg = CANG_GAN_LOCAL[xyZhi] || [];
            const cgss = cg.map(g => getShiShenLocal(dayGan, g));
            return `<span class="ss-cell">${cgss.join(' ') || '-'}</span>`;
        }
        case 'changsheng':
        case 'xingyun':
        case 'zizuo':
        case 'nayin':
        case 'kongwang':
        case 'shensha':
        case 'chonghe':
            return '-';
        default: return '-';
    }
}

// 本地十神计算（小运单元格用）
function getShiShenLocal(dayGan, targetGan) {
    return (SS_TABLE[dayGan] || {})[targetGan] || '';
}

// 流年单元格内容
function _proLiunianCellContent(key, l, dayGan) {
    switch (key) {
        case 'zhuxing':
            return `<span style="color:var(--text-2);font-size:0.74rem;">${l.gan_shishen_abbrev || ''}</span>`;
        case 'tiangan':
            return `<span class="gz-cell" style="font-size:1rem;">${wxSpanBZ(l.gan)}</span>`;
        case 'dizhi':
            return `<span class="gz-cell" style="font-size:1rem;">${wxSpanBZ(l.zhi)}</span>`;
        case 'canggan': {
            const cg = l.cang_gan || [];
            return `<span class="cg-cell">${cg.map(g => wxSpanBZ(g)).join(' ') || '-'}</span>`;
        }
        case 'fuxing': {
            const cgss = l.cang_gan_shi_shen || [];
            return `<span class="ss-cell">${cgss.join(' ') || '-'}</span>`;
        }
        case 'changsheng': {
            const val = l.chang_sheng || '';
            const cls = _csClass(val);
            return `<span class="changsheng-cell ${cls}">${val || '-'}</span>`;
        }
        case 'xingyun':
            return `<span class="xingyun-cell">${l.xing_yun || '-'}</span>`;
        case 'zizuo':
            return `<span class="zizuo-cell">${l.zi_zuo || '-'}</span>`;
        case 'kongwang':
            return `<span class="kong-cell">${l.kong_wang || '-'}</span>`;
        case 'nayin':
            return `<span class="nayin-cell">${l.nayin || '-'}</span>`;
        case 'xiaoyun': {
            const xygz = l.xiao_yun_gan_zhi || '';
            if (xygz) {
                return `<span class="gz-cell" style="font-size:0.84rem;color:var(--info);">${xygz.charAt(0) ? wxSpanBZ(xygz.charAt(0)) : ''}${xygz.charAt(1) ? wxSpanBZ(xygz.charAt(1)) : ''}</span>`;
            }
            return '-';
        }
        case 'shensha': {
            const ss = l.shen_sha || [];
            if (ss.length > 0) {
                return `<span class="shensha-cell">${ss.map(s => `<span class="ss-tag">${s}</span>`).join('')}</span>`;
            }
            return '-';
        }
        case 'chonghe': {
            const pr = l.pillar_relations || {};
            const allRels = [
                ...(pr.gan_he || []).map(r => `<span style="color:#07e930;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`),
                ...(pr.gan_chong || []).map(r => `<span style="color:#d30505;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`),
                ...(pr.zhi_liu_he || []).map(r => `<span style="color:#07e930;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`),
                ...(pr.zhi_liu_chong || []).map(r => `<span style="color:#d30505;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`),
                ...(pr.zhi_liu_hai || []).map(r => `<span style="color:#ef9104;font-size:0.7rem;">${relationLabelBZ(r.desc)}</span>`),
            ];
            return allRels.length > 0 ? allRels.join(' ') : '-';
        }
        default: return '-';
    }
}

function isCurrentDayun(d) {
    // 使用 start_year/end_year 判断当前年份是否在该大运/小运范围内
    const currentYear = new Date().getFullYear();
    return currentYear >= d.start_year && currentYear <= d.end_year;
}

// ═══════════════════════════════════════════════════════════════
// 胎命身toggle
// ═══════════════════════════════════════════════════════════════

function toggleTMS() {
    _showTMS = !_showTMS;
    // 同步导航栏胎命身按钮状态
    const navTmsBtn = $('navTmsBtn');
    if (navTmsBtn) navTmsBtn.classList.toggle('active', _showTMS);
    if (_baziData) {
        // 重新渲染当前tab
        if (_activeTab === 'basic') {
            $('panelBasic').innerHTML = renderBasicTab(_baziData);
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// 专业排盘 - 大运/流年选择
// ═══════════════════════════════════════════════════════════════

function selectDayun(idx) {
    // 始终选中大运（不允许取消，保持专业盘交互一致总有一个大运被选中）
    _activeDayunIdx = idx;
    _dayunUserSelected = true; // 标记为用户手动选择
    // 自动选中该大运对应的流年（优先当前年份，否则大运起始年）
    _activeLiunianIdx = _findLiunianIdxForDayun(idx);
    if (_baziData) {
        // 同步更新基本排盘Tab中的大运/流年高亮
        $('panelBasic').innerHTML = renderBasicTab(_baziData);
        // 重新渲染专业排盘Tab（大运/流年选择变化需要更新高亮和内容）
        $('panelWzpro').innerHTML = renderProTab(_baziData);
        // 选中大运后自动滚动到选中项
        setTimeout(() => {
            // 滚动基本排盘的流年选中项
            const activeLnItem = document.querySelector('#baziLiuNianContainer .ln-item.active');
            if (activeLnItem) activeLnItem.scrollIntoView({behavior:'smooth', block:'center'});
            // 滚动专业排盘的选中项
            const activeDyEl = document.querySelector('.col-dayun.dy-active');
            if (activeDyEl) activeDyEl.scrollIntoView({behavior:'smooth', block:'nearest', inline:'center'});
        }, 50);
    }
    // 大运切换后重新加载流月
    if (typeof loadProLiuYueHorizontal === 'function') {
        loadProLiuYueHorizontal();
    }
    if (typeof loadProLiuYue === 'function') {
        loadProLiuYue();
    }
}

// 根据大运索引找到对应的流年索引（优先当前年，否则大运起始年）
function _findLiunianIdxForDayun(dyIdx) {
    if (!_baziData) return -1;
    const dy = _baziData.da_yun || [];
    const ln = _baziData.liu_nian || [];
    if (dyIdx < 0 || dyIdx >= dy.length) return -1;

    const activeDy = dy[dyIdx];
    const currentYear = new Date().getFullYear();

    // 优先找当前年份
    if (currentYear >= activeDy.start_year && currentYear <= activeDy.end_year) {
        const idx = ln.findIndex(l => l.year === currentYear);
        if (idx >= 0) return idx;
    }

    // 否则找大运起始年份
    const idx = ln.findIndex(l => l.year === activeDy.start_year);
    return idx;
}

function selectLiunian(idx) {
    _activeLiunianIdx = idx;
    if (_baziData) {
        // 同步更新基本排盘Tab中的流年高亮
        $('panelBasic').innerHTML = renderBasicTab(_baziData);
        // 重新渲染专业排盘Tab（流年选择变化需要更新高亮和内容）
        $('panelWzpro').innerHTML = renderProTab(_baziData);
    }
    // 流年变化时重新加载流月
    if (typeof loadProLiuYueHorizontal === 'function') {
        loadProLiuYueHorizontal();
    }
    if (typeof loadProLiuYue === 'function') {
        loadProLiuYue();
    }
}

// ═══════════════════════════════════════════════════════════════
// 专业细盘 - 流月加载
// ═══════════════════════════════════════════════════════════════

function loadProLiuYue() {
    if (!_baziData) return;
    const dy = _baziData.da_yun || [];
    if (_activeDayunIdx < 0 || _activeDayunIdx >= dy.length) return;
    const activeDy = dy[_activeDayunIdx];
    const _baziDayGan = _baziData.four_pillars && _baziData.four_pillars.day ? _baziData.four_pillars.day.gan : '';

    const listEl = document.getElementById('proLiuYueList');
    if (!listEl) return;
    listEl.innerHTML = '<div style="text-align:center;padding:8px;color:var(--text-3);font-size:0.72rem;">🔄 加载中...</div>';

    // 使用流年中间年份加载流月
    const targetYear = _activeLiunianIdx >= 0 ? (_baziData.liu_nian[_activeLiunianIdx] || {}).year : activeDy.start_year;

    apiFetch('/api/bazi/liu-yue', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ year: targetYear, dayGan: _baziDayGan })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const liuYue = data.liu_yue || [];
            const currentBaziMonth = data.current_bazi_month || null;
            const isCurrentYear = targetYear === new Date().getFullYear();
            let html = '<div class="liuyue-list">';
            liuYue.forEach(m => {
                const jieName = m.jie_name || MONTH_CN[m.month_num - 1];
                const isCurrent = isCurrentYear && currentBaziMonth && m.month_num === currentBaziMonth;
                const activeCls = isCurrent ? ' active' : '';
                const activeStyle = isCurrent ? 'background:var(--accent-glow);font-weight:700;' : '';
                html += `<div class="liuyue-card${activeCls}" style="${activeStyle}" onclick="loadProLiuRi(${targetYear}, ${m.month_num}, '${_baziDayGan}')">`;
                html += `<span class="ly-name">${jieName}</span>`;
                html += `<span class="ly-gz">${wxSpanBZ(m.gan_zhi)}</span>`;
                html += `<span class="ly-ss">${m.shi_shen_gan || ''}</span>`;
                html += `</div>`;
            });
            html += '</div>';
            listEl.innerHTML = html;
        } else {
            listEl.innerHTML = `<div style="color:var(--danger);font-size:0.72rem;">加载失败</div>`;
        }
    })
    .catch(() => {
        listEl.innerHTML = `<div style="color:var(--danger);font-size:0.72rem;">网络错误</div>`;
    });
}

// 横版流月加载
function loadProLiuYueHorizontal() {
    if (!_baziData) return;
    const dy = _baziData.da_yun || [];
    if (_activeDayunIdx < 0 || _activeDayunIdx >= dy.length) return;
    const activeDy = dy[_activeDayunIdx];
    const _baziDayGan = _baziData.four_pillars && _baziData.four_pillars.day ? _baziData.four_pillars.day.gan : '';
    const ln = _baziData.liu_nian || [];
    const targetYear = _activeLiunianIdx >= 0 ? (ln[_activeLiunianIdx] || {}).year : activeDy.start_year;

    const rowEl = document.getElementById('proLiuYueRow');
    if (!rowEl) return;
    rowEl.innerHTML = '<div style="text-align:center;padding:8px;color:var(--text-3);font-size:0.72rem;">🔄 加载中...</div>';

    apiFetch('/api/bazi/liu-yue', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ year: targetYear, dayGan: _baziDayGan })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const liuYue = data.liu_yue || [];
            const currentBaziMonth = data.current_bazi_month || null;
            const isCurrentYear = targetYear === new Date().getFullYear();

            let html = '';
            // 时安风格：简洁流月，月份名+干支两行
            html += `<div class="pro-ly-shiAn-style">`;
            liuYue.forEach((m, i) => {
                const jieName = m.jie_name || MONTH_CN[m.month_num - 1];
                const isCurrent = isCurrentYear && currentBaziMonth && m.month_num === currentBaziMonth;
                const activeCls = isCurrent ? ' ly-current' : '';
                html += `<div class="ly-shiAn-card${activeCls}" onclick="loadProLiuRi(${targetYear}, ${m.month_num}, '${_baziDayGan}')">`;
                html += `<span class="ly-shiAn-name">${jieName}</span>`;
                html += `<span class="ly-shiAn-gz">${wxSpanBZ(m.gan_zhi)}</span>`;
                if (m.shi_shen_gan) html += `<span class="ly-shiAn-ss">${m.shi_shen_gan}</span>`;
                html += `</div>`;
            });
            html += `</div>`;
            rowEl.innerHTML = html;
        } else {
            rowEl.innerHTML = `<div style="color:var(--danger);font-size:0.72rem;padding:8px;">加载失败</div>`;
        }
    })
    .catch(() => {
        rowEl.innerHTML = `<div style="color:var(--danger);font-size:0.72rem;padding:8px;">网络错误</div>`;
    });
}

function loadProLiuRi(year, baziMonth, dayGan) {
    const drillArea = document.getElementById('proDrillArea');
    if (!drillArea) return;
    drillArea.innerHTML = '<div style="text-align:center;padding:16px;color:var(--text-3);font-size:0.85rem;">🔄 加载流日...</div>';

    apiFetch('/api/bazi/liu-ri', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ year, baziMonth, dayGan })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            drillArea.innerHTML = renderProLiuRi(data, year, baziMonth, dayGan);
        } else {
            drillArea.innerHTML = `<div style="color:var(--danger);padding:10px;font-size:0.85rem;">❌ ${data.error || '加载失败'}</div>`;
        }
    })
    .catch(() => {
        drillArea.innerHTML = `<div style="color:var(--danger);padding:10px;font-size:0.85rem;">❌ 网络错误</div>`;
    });
}

function renderProLiuRi(apiData, year, baziMonth, dayGan) {
    const liuRi = apiData.liu_ri || [];
    const jieName = apiData.jie_name || '';
    const startDate = apiData.start_date || '';
    const endDate = apiData.end_date || '';
    const monthZhi = apiData.month_zhi || '';
    const now = new Date();
    const todayStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;

    const LUNAR_DAY_CN = ['初一','初二','初三','初四','初五','初六','初七','初八','初九','初十',
        '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十',
        '廿一','廿二','廿三','廿四','廿五','廿六','廿七','廿八','廿九','三十'];

    function extractLunarDisplay(lunarStr) {
        if (!lunarStr) return '';
        const match = lunarStr.match(/年(.+)/);
        if (!match) return '';
        const afterYear = match[1];
        const monthMatch = afterYear.match(/^(闰?[一二三四五六七八九十冬腊]+月)(.+)/);
        if (monthMatch) {
            const monthName = monthMatch[1];
            const dayName = monthMatch[2];
            if (dayName === '初一') return monthName;
            return dayName;
        }
        return afterYear;
    }

    let html = `<div style="border-top:1px solid var(--card-border);padding-top:14px;">`;
    html += `<div class="drill-title">🗓️ ${year}年${monthZhi}月（${jieName}起） <span style="font-weight:400;font-size:0.78rem;color:var(--text-3);">${startDate} ~ ${endDate}</span></div>`;

    let currentMonth = -1;
    liuRi.forEach((d, idx) => {
        const showMonth = d.month;
        if (showMonth !== currentMonth) {
            if (currentMonth !== -1) html += `</div>`;
            currentMonth = showMonth;
            html += `<div style="font-size:0.76rem;color:var(--text-3);margin:6px 0 4px;padding-left:2px;">${showMonth}月</div>`;
            html += `<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:2px;margin-bottom:2px;">`;
            ['日','一','二','三','四','五','六'].forEach(wd => {
                html += `<div style="text-align:center;font-size:0.62rem;color:var(--text-3);padding:2px;">${wd}</div>`;
            });
            html += `</div>`;
            html += `<div class="liuri-grid">`;
            const firstDayWeek = new Date(d.year || year, showMonth - 1, d.day || 1).getDay();
            for (let i = 0; i < firstDayWeek; i++) html += `<div></div>`;
        }

        const dateStr = d.date_str || `${d.year || year}-${String(showMonth).padStart(2,'0')}-${String(d.day).padStart(2,'0')}`;
        const isCurrent = dateStr === todayStr;
        const lunarDisplay = extractLunarDisplay(d.lunar_str);
        const isLunarMonth = lunarDisplay && lunarDisplay.endsWith('月');

        html += `<div class="lr-item${isCurrent?' active':''}" data-day="${d.day}" data-gan="${d.gan}" onclick="loadProLiuShi('${d.gan}', '${dayGan}')">`;
        html += `<span class="lr-day" style="color:${isCurrent?'#fff':'var(--text-1)'};">${d.day}</span>`;
        const lunarColor = isCurrent ? 'rgba(255,255,255,0.7)' : (isLunarMonth ? 'var(--accent)' : 'var(--text-3)');
        html += `<span class="lr-lunar" style="color:${lunarColor};${isLunarMonth?'font-weight:600;':''}">${lunarDisplay}</span>`;
        html += `<span class="lr-gz" style="color:${isCurrent?'#fff':'var(--text-1)'};">${isCurrent ? d.gan_zhi : wxSpanBZ(d.gan_zhi)}</span>`;
        html += `</div>`;
    });

    if (currentMonth !== -1) html += `</div>`;
    html += `</div>`;
    return html;
}

function loadProLiuShi(dayGan, dayZhuGan) {
    const drillArea = document.getElementById('proDrillArea');
    if (!drillArea) return;

    // 添加流时面板
    let shiDiv = document.getElementById('proLiuShiPanel');
    if (!shiDiv) {
        shiDiv = document.createElement('div');
        shiDiv.id = 'proLiuShiPanel';
        shiDiv.style.cssText = 'margin-top:12px;border-top:1px solid var(--card-border);padding-top:14px;';
        drillArea.appendChild(shiDiv);
    }
    shiDiv.innerHTML = '<div style="text-align:center;padding:12px;color:var(--text-3);font-size:0.85rem;">🔄 加载流时...</div>';

    apiFetch('/api/bazi/liu-shi', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ dayGan, dayZhuGan })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            renderProLiuShi(data.liu_shi, dayGan, shiDiv);
        } else {
            shiDiv.innerHTML = `<div style="color:var(--danger);font-size:0.85rem;">❌ ${data.error || '加载失败'}</div>`;
        }
    })
    .catch(() => {
        shiDiv.innerHTML = `<div style="color:var(--danger);font-size:0.85rem;">❌ 网络错误</div>`;
    });
}

function renderProLiuShi(liuShi, dayGan, container) {
    const now = new Date();
    const currentHour = now.getHours();
    let currentZhiIdx = 0;
    if (currentHour === 23 || currentHour === 0) currentZhiIdx = 0;
    else currentZhiIdx = Math.floor((currentHour + 1) / 2) % 12;

    let html = `<div class="drill-title">⏰ ${dayGan}日 流时</div>`;
    html += `<div class="liushi-grid">`;
    liuShi.forEach((s, idx) => {
        const isCurrent = idx === currentZhiIdx;
        const bgColor = isCurrent ? 'var(--accent)' : 'transparent';
        const textColor = isCurrent ? '#fff' : 'var(--text-1)';
        const borderCol = isCurrent ? 'var(--accent)' : 'var(--card-border)';
        html += `<div class="ls-item" style="border-color:${borderCol};background:${bgColor};">`;
        html += `<div class="ls-time" style="color:${isCurrent?'rgba(255,255,255,0.7)':'var(--text-3)'};">${s.hour_str}</div>`;
        html += `<div class="ls-gz" style="color:${textColor};">${isCurrent ? s.gan_zhi : wxSpanBZ(s.gan_zhi)}</div>`;
        html += `<div class="ls-ss" style="color:${isCurrent?'rgba(255,255,255,0.7)':'var(--text-3)'};">${s.shi_shen_gan}</div>`;
        html += `</div>`;
    });
    html += `</div>`;
    container.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════
// 基本排盘 - 流年→流月→流日→流时 交互展开
// ═══════════════════════════════════════════════════════════════

function toggleBaziLiuYue(el, year, dayGan) {
    const panel = document.getElementById('baziLiuYuePanel');
    const riPanel = document.getElementById('baziLiuRiPanel');
    const shiPanel = document.getElementById('baziLiuShiPanel');

    // 同步流年选中状态到专业排盘
    if (_baziData) {
        const ln = _baziData.liu_nian || [];
        const lnIdx = ln.findIndex(l => l.year === year);
        if (lnIdx >= 0) {
            _activeLiunianIdx = lnIdx;
            // 确保对应大运也被选中
            const dy = _baziData.da_yun || [];
            const dyIdx = dy.findIndex(d => year >= d.start_year && year <= d.end_year);
            if (dyIdx >= 0 && _activeDayunIdx !== dyIdx) {
                _activeDayunIdx = dyIdx;
                _dayunUserSelected = false; // 自动同步，不算用户手动选择
            }
        }
    }

    if (_baziActiveYear === year) {
        panel.style.display = 'none';
        riPanel.style.display = 'none';
        shiPanel.style.display = 'none';
        el.style.background = '';
        el.style.boxShadow = '';
        _baziActiveYear = null;
        _baziActiveMonth = null;
        _baziActiveDayGz = null;
        return;
    }

    document.querySelectorAll('.ln-item').forEach(item => {
        const isNow = parseInt(item.dataset.year) === new Date().getFullYear();
        item.style.background = isNow ? 'var(--accent-glow)' : '';
        item.style.boxShadow = '';
        item.classList.remove('active');
    });

    el.style.background = 'var(--accent)';
    el.style.boxShadow = '0 2px 12px rgba(0,0,0,0.15)';
    el.classList.add('active');

    _baziActiveYear = year;
    _baziActiveMonth = null;
    _baziActiveDayGz = null;

    riPanel.style.display = 'none';
    shiPanel.style.display = 'none';

    panel.innerHTML = '<div style="text-align:center;padding:16px;color:var(--text-3);font-size:0.85rem;">🔄 加载流月...</div>';
    panel.style.display = 'block';

    apiFetch('/api/bazi/liu-yue', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ year, dayGan })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            renderBaziLiuYue(data.liu_yue, year, dayGan, data.current_bazi_month);
        } else {
            panel.innerHTML = `<div style="color:var(--danger);padding:10px;font-size:0.85rem;">❌ ${data.error || '加载失败'}</div>`;
        }
    })
    .catch(() => {
        panel.innerHTML = `<div style="color:var(--danger);padding:10px;font-size:0.85rem;">❌ 网络错误</div>`;
    });
}

function renderBaziLiuYue(liuYue, year, dayGan, currentBaziMonth) {
    const panel = document.getElementById('baziLiuYuePanel');
    const now = new Date();
    const isCurrentYear = year === now.getFullYear();
    // 使用后端基于节气计算的当前八字月份，而非公历月份
    const currentMonth = currentBaziMonth || null;

    let html = `<div class="drill-title">📆 ${year}年 流月</div>`;
    html += `<div class="liuyue-grid">`;

    liuYue.forEach(m => {
        const isCurrent = isCurrentYear && currentMonth && m.month_num === currentMonth;
        const bgColor = isCurrent ? 'var(--accent)' : 'transparent';
        const textColor = isCurrent ? '#fff' : 'var(--text-1)';
        const borderCol = isCurrent ? 'var(--accent)' : 'var(--card-border)';

        html += `<div class="ly-item${isCurrent?' active':''}" style="border-color:${borderCol};background:${bgColor};" data-month="${m.month_num}" onclick="toggleBaziLiuRi(this, ${year}, ${m.month_num}, '${dayGan}')">`;
        html += `<div class="ly-month" style="color:${isCurrent?'rgba(255,255,255,0.7)':'var(--text-3)'};">${MONTH_CN[m.month_num - 1]}</div>`;
        html += `<div class="ly-gz" style="color:${textColor};">${isCurrent ? m.gan_zhi : wxSpanBZ(m.gan_zhi)}</div>`;
        html += `<div class="ly-ss" style="color:${isCurrent?'rgba(255,255,255,0.7)':'var(--text-3)'};">${m.shi_shen_gan}</div>`;
        html += `</div>`;
    });

    html += `</div>`;
    panel.innerHTML = html;
}

function toggleBaziLiuRi(el, year, baziMonth, dayGan) {
    const riPanel = document.getElementById('baziLiuRiPanel');
    const shiPanel = document.getElementById('baziLiuShiPanel');

    if (_baziActiveMonth === baziMonth && _baziActiveYear === year) {
        riPanel.style.display = 'none';
        shiPanel.style.display = 'none';
        el.style.background = '';
        el.style.boxShadow = '';
        el.classList.remove('active');
        _baziActiveMonth = null;
        _baziActiveDayGz = null;
        return;
    }

    document.querySelectorAll('.ly-item').forEach(item => {
        item.style.background = '';
        item.style.boxShadow = '';
        item.classList.remove('active');
    });

    el.style.background = 'var(--accent)';
    el.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
    el.classList.add('active');

    _baziActiveMonth = baziMonth;
    _baziActiveYear = year;
    _baziActiveDayGz = null;

    shiPanel.style.display = 'none';

    riPanel.innerHTML = '<div style="text-align:center;padding:16px;color:var(--text-3);font-size:0.85rem;">🔄 加载流日...</div>';
    riPanel.style.display = 'block';

    apiFetch('/api/bazi/liu-ri', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ year, baziMonth, dayGan })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            renderBaziLiuRi(data, year, baziMonth, dayGan);
        } else {
            riPanel.innerHTML = `<div style="color:var(--danger);padding:10px;font-size:0.85rem;">❌ ${data.error || '加载失败'}</div>`;
        }
    })
    .catch(() => {
        riPanel.innerHTML = `<div style="color:var(--danger);padding:10px;font-size:0.85rem;">❌ 网络错误</div>`;
    });
}

function renderBaziLiuRi(apiData, year, baziMonth, dayGan) {
    const riPanel = document.getElementById('baziLiuRiPanel');
    const liuRi = apiData.liu_ri || [];
    const jieName = apiData.jie_name || '';
    const startDate = apiData.start_date || '';
    const endDate = apiData.end_date || '';
    const monthZhi = apiData.month_zhi || '';
    const now = new Date();
    const todayStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;

    function extractLunarDisplay(lunarStr) {
        if (!lunarStr) return '';
        const match = lunarStr.match(/年(.+)/);
        if (!match) return '';
        const afterYear = match[1];
        const monthMatch = afterYear.match(/^(闰?[一二三四五六七八九十冬腊]+月)(.+)/);
        if (monthMatch) {
            const monthName = monthMatch[1];
            const dayName = monthMatch[2];
            if (dayName === '初一') return monthName;
            return dayName;
        }
        return afterYear;
    }

    let html = `<div class="drill-title">🗓️ ${year}年${monthZhi}月（${jieName}起） <span style="font-weight:400;font-size:0.78rem;color:var(--text-3);">${startDate} ~ ${endDate}</span></div>`;

    let currentMonth = -1;
    liuRi.forEach((d, idx) => {
        const showMonth = d.month;
        if (showMonth !== currentMonth) {
            if (currentMonth !== -1) html += `</div>`;
            currentMonth = showMonth;
            html += `<div style="font-size:0.76rem;color:var(--text-3);margin:6px 0 4px;padding-left:2px;">${showMonth}月</div>`;
            html += `<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:2px;margin-bottom:2px;">`;
            ['日','一','二','三','四','五','六'].forEach(wd => {
                html += `<div style="text-align:center;font-size:0.62rem;color:var(--text-3);padding:2px;">${wd}</div>`;
            });
            html += `</div>`;
            html += `<div class="liuri-grid">`;
            const firstDayWeek = new Date(d.year || year, showMonth - 1, d.day || 1).getDay();
            for (let i = 0; i < firstDayWeek; i++) html += `<div></div>`;
        }

        const dateStr = d.date_str || `${d.year || year}-${String(showMonth).padStart(2,'0')}-${String(d.day).padStart(2,'0')}`;
        const isCurrent = dateStr === todayStr;
        const lunarDisplay = extractLunarDisplay(d.lunar_str);
        const isLunarMonth = lunarDisplay && lunarDisplay.endsWith('月');

        html += `<div class="lr-item${isCurrent?' active':''}" data-day="${d.day}" data-gan="${d.gan}" onclick="toggleBaziLiuShi(this, '${d.gan}', '${dayGan}')">`;
        html += `<span class="lr-day" style="color:${isCurrent?'#fff':'var(--text-1)'};">${d.day}</span>`;
        const lunarColor = isCurrent ? 'rgba(255,255,255,0.7)' : (isLunarMonth ? 'var(--accent)' : 'var(--text-3)');
        html += `<span class="lr-lunar" style="color:${lunarColor};${isLunarMonth?'font-weight:600;':''}">${lunarDisplay}</span>`;
        html += `<span class="lr-gz" style="color:${isCurrent?'#fff':'var(--text-1)'};">${isCurrent ? d.gan_zhi : wxSpanBZ(d.gan_zhi)}</span>`;
        html += `</div>`;
    });

    if (currentMonth !== -1) html += `</div>`;
    riPanel.innerHTML = html;
}

function toggleBaziLiuShi(el, dayGan, dayZhuGan) {
    const shiPanel = document.getElementById('baziLiuShiPanel');

    if (_baziActiveDayGz === dayGan + dayZhuGan) {
        shiPanel.style.display = 'none';
        el.style.background = '';
        el.classList.remove('active');
        _baziActiveDayGz = null;
        return;
    }

    document.querySelectorAll('.lr-item').forEach(item => {
        item.style.background = '';
        item.classList.remove('active');
    });

    el.style.background = 'var(--accent)';
    el.classList.add('active');

    _baziActiveDayGz = dayGan + dayZhuGan;

    shiPanel.innerHTML = '<div style="text-align:center;padding:16px;color:var(--text-3);font-size:0.85rem;">🔄 加载流时...</div>';
    shiPanel.style.display = 'block';

    apiFetch('/api/bazi/liu-shi', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ dayGan, dayZhuGan })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            renderBaziLiuShi(data.liu_shi, dayGan);
        } else {
            shiPanel.innerHTML = `<div style="color:var(--danger);padding:10px;font-size:0.85rem;">❌ ${data.error || '加载失败'}</div>`;
        }
    })
    .catch(() => {
        shiPanel.innerHTML = `<div style="color:var(--danger);padding:10px;font-size:0.85rem;">❌ 网络错误</div>`;
    });
}

function renderBaziLiuShi(liuShi, dayGan) {
    const shiPanel = document.getElementById('baziLiuShiPanel');
    const now = new Date();
    const currentHour = now.getHours();
    let currentZhiIdx = 0;
    if (currentHour === 23 || currentHour === 0) currentZhiIdx = 0;
    else currentZhiIdx = Math.floor((currentHour + 1) / 2) % 12;

    let html = `<div class="drill-title">⏰ ${dayGan}日 流时</div>`;
    html += `<div class="liushi-grid">`;
    liuShi.forEach((s, idx) => {
        const isCurrent = idx === currentZhiIdx;
        const bgColor = isCurrent ? 'var(--accent)' : 'transparent';
        const textColor = isCurrent ? '#fff' : 'var(--text-1)';
        const borderCol = isCurrent ? 'var(--accent)' : 'var(--card-border)';

        html += `<div class="ls-item" style="border-color:${borderCol};background:${bgColor};">`;
        html += `<div class="ls-time" style="color:${isCurrent?'rgba(255,255,255,0.7)':'var(--text-3)'};">${s.hour_str}</div>`;
        html += `<div class="ls-gz" style="color:${textColor};">${isCurrent ? s.gan_zhi : wxSpanBZ(s.gan_zhi)}</div>`;
        html += `<div class="ls-ss" style="color:${isCurrent?'rgba(255,255,255,0.7)':'var(--text-3)'};">${s.shi_shen_gan}</div>`;
        html += `</div>`;
    });
    html += `</div>`;
    shiPanel.innerHTML = html;
}

// ═══ 大运跳转流年（基本排盘用，统一走selectDayun逻辑）
function jumpToLiuNian(startYear, endYear, dayGan) {
    if (_baziData) {
        const dy = _baziData.da_yun || [];
        const dyIdx = dy.findIndex(d => d.start_year === startYear && d.end_year === endYear);
        if (dyIdx >= 0) {
            selectDayun(dyIdx);
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// 分享/导出功能
// ═══════════════════════════════════════════════════════════════
function showSharePanel() {
    // 创建分享面板
    let existing = document.getElementById('sharePanel');
    if (existing) { existing.remove(); return; }

    const name = _baziData.name || '命主';
    const fp = _baziData.four_pillars || {};
    const pillars = ['year','month','day','hour'].map(p => {
        const pp = fp[p] || {};
        return (pp.gan||'?') + (pp.zhi||'?');
    }).join(' ');

    const panel = document.createElement('div');
    panel.id = 'sharePanel';
    panel.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:9999;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:24px;width:min(360px,90vw);box-shadow:0 8px 32px rgba(0,0,0,0.3);';
    panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <h3 style="margin:0;font-size:1.1rem;color:var(--text-1);">📤 分享排盘</h3>
            <button onclick="document.getElementById('sharePanel').remove()" style="background:none;border:none;font-size:1.5rem;color:var(--text-3);cursor:pointer;">✕</button>
        </div>
        <div style="background:var(--bg-secondary);border-radius:10px;padding:12px;margin-bottom:16px;">
            <div style="font-size:0.85rem;color:var(--text-2);margin-bottom:4px;">${name} · ${pillars}</div>
            <div style="font-size:0.72rem;color:var(--text-3);">${_baziData.birth_solar || ''}</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:10px;">
            <button onclick="exportAsImage()" style="display:flex;align-items:center;gap:8px;padding:12px 16px;border-radius:10px;border:1px solid var(--border);background:var(--bg-secondary);color:var(--text-1);cursor:pointer;font-size:0.9rem;">
                <span style="font-size:1.2rem;">🖼️</span> 导出图片
            </button>
            <button onclick="copyShareLink()" style="display:flex;align-items:center;gap:8px;padding:12px 16px;border-radius:10px;border:1px solid var(--border);background:var(--bg-secondary);color:var(--text-1);cursor:pointer;font-size:0.9rem;">
                <span style="font-size:1.2rem;">🔗</span> 复制链接
            </button>
            <button onclick="copyShareText()" style="display:flex;align-items:center;gap:8px;padding:12px 16px;border-radius:10px;border:1px solid var(--border);background:var(--bg-secondary);color:var(--text-1);cursor:pointer;font-size:0.9rem;">
                <span style="font-size:1.2rem;">📋</span> 复制八字文本
            </button>
        </div>
    `;
    // 背景遮罩
    const overlay = document.createElement('div');
    overlay.id = 'shareOverlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:9998;background:rgba(0,0,0,0.5);';
    overlay.onclick = () => { document.getElementById('sharePanel').remove(); overlay.remove(); };
    document.body.appendChild(overlay);
    document.body.appendChild(panel);
}

async function exportAsImage() {
    const shareBtn = document.getElementById('sharePanel');
    const overlay = document.getElementById('shareOverlay');
    if (shareBtn) shareBtn.style.display = 'none';
    if (overlay) overlay.style.display = 'none';

    // 隐藏导航栏和操作按钮
    const topnav = document.querySelector('.topnav');
    if (topnav) topnav.style.display = 'none';

    try {
        const target = document.querySelector('.result-container') || document.body;
        const canvas = await html2canvas(target, {
            backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--bg-primary').trim() || '#0a0a0f',
            scale: 2,
            useCORS: true,
            logging: false
        });

        // 创建下载链接
        const link = document.createElement('a');
        const name = (_baziData.name || 'bazi') + '_' + ((_baziData.four_pillars||{}).day||{}).gan + ((_baziData.four_pillars||{}).day||{}).zhi;
        link.download = `八字排盘_${name}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
    } catch (e) {
        console.error('导出图片失败:', e);
        alert('导出失败，请截图分享');
    } finally {
        if (topnav) topnav.style.display = '';
        if (shareBtn) shareBtn.style.display = '';
        if (overlay) overlay.style.display = '';
    }
}

function copyShareLink() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        _showToast('链接已复制到剪贴板');
        document.getElementById('sharePanel')?.remove();
        document.getElementById('shareOverlay')?.remove();
    }).catch(() => {
        // 降级方案
        const input = document.createElement('input');
        input.value = url;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        _showToast('链接已复制到剪贴板');
    });
}

function copyShareText() {
    const name = _baziData.name || '命主';
    const fp = _baziData.four_pillars || {};
    const pillars = ['year','month','day','hour'].map(p => {
        const pp = fp[p] || {};
        return (pp.gan||'?') + (pp.zhi||'?');
    });
    const gender = _baziData.gender || '';
    const birth = _baziData.birth_solar || '';
    const text = `${name}(${gender}) ${birth}\n四柱：${pillars.join(' ')}\n—— 时安解忧屋八字排盘`;

    navigator.clipboard.writeText(text).then(() => {
        _showToast('八字文本已复制');
        document.getElementById('sharePanel')?.remove();
        document.getElementById('shareOverlay')?.remove();
    }).catch(() => {
        const input = document.createElement('input');
        input.value = text;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        _showToast('八字文本已复制');
    });
}

function _showToast(msg) {
    const toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;top:20%;left:50%;transform:translateX(-50%);z-index:99999;background:rgba(0,0,0,0.8);color:#fff;padding:10px 20px;border-radius:8px;font-size:0.9rem;';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
}

// ═══════════════════════════════════════════════════════════════
// 时安八字专业细盘（Shian Pro Pan）— 暗亮双主题
// ═══════════════════════════════════════════════════════════════

let _shianData = null;           // 时安专业盘 数据缓存
let _shiAnLoading = false;
let _shiAnSelectedDayunIdx = -1;
let _shiAnSelectedLiunianIdx = -1;
let _shiAnSelectedLiuyueIdx = -1;
let _shiAnShowTMS = false;
let _shiAnColOrder = 'sz-first'; // 'dy-first' = 大运流年流月|四柱, 'sz-first' = 四柱|大运流年流月
let _shiAnActiveYunType = 'dayun'; // 'dayun' | 'xiaoyun' — 右侧当前激活的运类型（大运或小运）
let _shiAnSelectedXiaoyunIdx = -1; // 右侧小运区域选中的索引

// ── 时安藏干表 ──
const SHIAN_CANG_GAN = {
    '子':['癸'],'丑':['己','癸','辛'],'寅':['甲','丙','戊'],'卯':['乙'],
    '辰':['戊','乙','癸'],'巳':['丙','庚','戊'],'午':['丁','己'],'未':['己','丁','乙'],
    '申':['庚','壬','戊'],'酉':['辛'],'戌':['戊','辛','丁'],'亥':['壬','甲']
};

// ── 时安十神表 ──
const SHIAN_SS_TABLE = {
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
};

// ── 时安十二长生 ──
const SHIAN_CS_TABLE = {'甲':'亥','乙':'午','丙':'寅','丁':'酉','戊':'寅','己':'酉','庚':'巳','辛':'子','壬':'申','癸':'卯'};
const SHIAN_CS_ORDER = ['长生','沐浴','冠带','临官','帝旺','衰','病','死','墓','绝','胎','养'];
const SHIAN_DZ_ORDER = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
const SHIAN_YANG_GAN = ['甲','丙','戊','庚','壬'];

function shiAnCalcChangsheng(dayGan, zhi) {
    const start = SHIAN_CS_TABLE[dayGan];
    if (!start || !zhi) return '';
    const si = SHIAN_DZ_ORDER.indexOf(start), ti = SHIAN_DZ_ORDER.indexOf(zhi);
    if (si < 0 || ti < 0) return '';
    const isYang = SHIAN_YANG_GAN.includes(dayGan);
    const off = isYang ? (ti - si + 12) % 12 : (si - ti + 12) % 12;
    return SHIAN_CS_ORDER[off] || '';
}

function shianGetShiShen(dayGan, targetGan) {
    return (SHIAN_SS_TABLE[dayGan] || {})[targetGan] || '';
}

// ── 时安纳音 ──
const SHIAN_NAYIN = ["海中金","海中金","炉中火","炉中火","大林木","大林木","路旁土","路旁土","剑锋金","剑锋金",
    "山头火","山头火","涧下水","涧下水","城头土","城头土","白蜡金","白蜡金","杨柳木","杨柳木",
    "泉中水","泉中水","屋上土","屋上土","霹雳火","霹雳火","松柏木","松柏木","长流水","长流水",
    "砂石金","砂石金","山下火","山下火","平地木","平地木","壁上土","壁上土","金箔金","金箔金",
    "覆灯火","覆灯火","天河水","天河水","大驿土","大驿土","钗环金","钗环金","桑柘木","桑柘木",
    "大溪水","大溪水","沙中土","沙中土","天上火","天上火","石榴木","石榴木","大海水","大海水"];

function shiAnCalcNayin(gan, zhi) {
    const TG = '甲乙丙丁戊己庚辛壬癸';
    const DZ = '子丑寅卯辰巳午未申酉戌亥';
    const gi = TG.indexOf(gan), zi = DZ.indexOf(zhi);
    if (gi < 0 || zi < 0) return '';
    for (let k = 0; k < 60; k++) {
        if (k % 10 === gi && k % 12 === zi) return SHIAN_NAYIN[k];
    }
    return '';
}

// ── 时安空亡 ──
function shiAnCalcKongwang(gan, zhi) {
    const TG = '甲乙丙丁戊己庚辛壬癸';
    const DZ = '子丑寅卯辰巳午未申酉戌亥';
    const gi = TG.indexOf(gan), zi = DZ.indexOf(zhi);
    if (gi < 0 || zi < 0) return '';
    let idx = -1;
    for (let k = 0; k < 60; k++) {
        if (k % 10 === gi && k % 12 === zi) { idx = k; break; }
    }
    if (idx < 0) return '';
    const xunEnd = idx - (idx % 10) + 9;
    const lastZi = xunEnd % 12;
    return SHIAN_DZ_ORDER[(lastZi + 1) % 12] + SHIAN_DZ_ORDER[(lastZi + 2) % 12];
}

// ── 时安神煞计算（对齐后端 _calc_shen_sha_for_ganzhi） ──
const SHIAN_SS_TIANYI = {'甲':['丑','未'],'乙':['子','申'],'丙':['亥','酉'],'丁':['亥','酉'],'戊':['丑','未'],'己':['子','申'],'庚':['丑','未'],'辛':['子','申'],'壬':['卯','巳'],'癸':['卯','巳']};
const SHIAN_SS_TAIJI = {'甲':['子','午'],'乙':['子','午'],'丙':['卯','酉'],'丁':['卯','酉'],'戊':['辰','戌'],'己':['辰','戌'],'庚':['寅','申'],'辛':['寅','申'],'壬':['巳','亥'],'癸':['巳','亥']};
const SHIAN_SS_WENCHANG = {'甲':'巳','乙':'午','丙':'申','丁':'酉','戊':'申','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'};
const SHIAN_SS_LUSHEN = {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'};
const SHIAN_SS_YANGREN = {'甲':'卯','乙':'辰','丙':'午','丁':'未','戊':'午','己':'未','庚':'酉','辛':'戌','壬':'子','癸':'丑'};
const SHIAN_SS_HONGYAN = {'甲':'午','乙':'申','丙':'寅','丁':'未','戊':'辰','己':'辰','庚':'戌','辛':'酉','壬':'子','癸':'申'};
const SHIAN_SS_XUETANG = {'木':'亥','火':'寅','土':'亥','金':'巳','水':'申'};
const SHIAN_SS_GANWX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'};
const SHIAN_SS_TIANYIYI = {'子':'亥','丑':'寅','寅':'丑','卯':'寅','辰':'卯','巳':'辰','午':'巳','未':'午','申':'未','酉':'申','戌':'酉','亥':'戌'};
const SHIAN_SS_TIANXI = {'子':'酉','丑':'申','寅':'未','卯':'午','辰':'巳','巳':'辰','午':'卯','未':'寅','申':'丑','酉':'子','戌':'亥','亥':'戌'};
const SHIAN_SS_HONGLUAN = {'子':'卯','丑':'寅','寅':'丑','卯':'子','辰':'亥','巳':'戌','午':'酉','未':'申','申':'未','酉':'午','戌':'巳','亥':'辰'};
const SHIAN_SS_SANGMEN = {'子':'戌','丑':'亥','寅':'子','卯':'丑','辰':'寅','巳':'卯','午':'辰','未':'巳','申':'午','酉':'未','戌':'申','亥':'酉'};
const SHIAN_SS_ZAISHA = {'子':'午','丑':'卯','寅':'子','卯':'酉','辰':'午','巳':'卯','午':'子','未':'酉','申':'午','酉':'卯','戌':'子','亥':'酉'};
// 驿马、桃花、华盖、将星、劫煞、亡神 — 年支查
const SHIAN_SS_YIMA = {'申':'寅','子':'寅','辰':'寅','寅':'申','午':'申','戌':'申','巳':'亥','酉':'亥','丑':'亥','亥':'巳','卯':'巳','未':'巳'};
const SHIAN_SS_TAOHUA = {'申':'酉','子':'酉','辰':'酉','寅':'卯','午':'卯','戌':'卯','巳':'午','酉':'午','丑':'午','亥':'子','卯':'子','未':'子'};
const SHIAN_SS_HUAGAI = {'申':'辰','子':'辰','辰':'辰','寅':'戌','午':'戌','戌':'戌','巳':'丑','酉':'丑','丑':'丑','亥':'未','卯':'未','未':'未'};
const SHIAN_SS_JIANGXING = {'申':'子','子':'子','辰':'子','寅':'午','午':'午','戌':'午','巳':'酉','酉':'酉','丑':'酉','亥':'卯','卯':'卯','未':'卯'};
const SHIAN_SS_JIESHA = {'申':'巳','子':'巳','辰':'巳','寅':'亥','午':'亥','戌':'亥','巳':'寅','酉':'寅','丑':'寅','亥':'申','卯':'申','未':'申'};
const SHIAN_SS_WANGSHEN = {'申':'亥','子':'亥','辰':'亥','寅':'巳','午':'巳','戌':'巳','巳':'寅','酉':'寅','丑':'寅','亥':'申','卯':'申','未':'申'};
// 勾煞/绞煞
const SHIAN_SS_GOUJIAO = {'子':{'勾':'辰','绞':'卯'},'丑':{'勾':'巳','绞':'辰'},'寅':{'勾':'午','绞':'巳'},'卯':{'勾':'未','绞':'午'},'辰':{'勾':'申','绞':'未'},'巳':{'勾':'酉','绞':'申'},'午':{'勾':'戌','绞':'酉'},'未':{'勾':'亥','绞':'戌'},'申':{'勾':'子','绞':'亥'},'酉':{'勾':'丑','绞':'子'},'戌':{'勾':'寅','绞':'丑'},'亥':{'勾':'卯','绞':'寅'}};
// 天德贵人（月支对应天干）
const SHIAN_SS_TIANDE = {1:'丁',2:'申',3:'壬',4:'辛',5:'亥',6:'甲',7:'癸',8:'寅',9:'丙',10:'乙',11:'巳',12:'庚'};
// 月德贵人
const SHIAN_SS_YUEDE = {1:'丙',2:'甲',3:'壬',4:'庚',5:'丙',6:'甲',7:'壬',8:'庚',9:'丙',10:'甲',11:'壬',12:'庚'};
// 月德合
const SHIAN_SS_YUEDEHE = {1:'辛',2:'己',3:'丁',4:'乙',5:'辛',6:'己',7:'丁',8:'乙',9:'辛',10:'己',11:'丁',12:'乙'};
// 孤辰/寡宿
const SHIAN_SS_GUCHEN = {'子':'寅','丑':'寅','寅':'巳','卯':'巳','辰':'巳','巳':'申','午':'申','未':'申','申':'亥','酉':'亥','戌':'亥','亥':'寅'};
const SHIAN_SS_GUASU = {'子':'戌','丑':'戌','寅':'丑','卯':'丑','辰':'丑','巳':'辰','午':'辰','未':'辰','申':'未','酉':'未','戌':'未','亥':'戌'};

function shiAnCalcShensha(gan, zhi, dayMaster) {
    if (!gan || !zhi || !dayMaster) return [];
    const stars = [];
    const yearZhi = _shianData ? (_shianData.birth_params ? SHIAN_DZ_ORDER[(((parseInt(_shianData.birth_params.y) - 4) % 12) + 12) % 12] : '') : '';
    const monthZhi = _shianData ? (_shianData.birth_params ? SHIAN_DZ_ORDER[(parseInt(_shianData.birth_params.m) + 1) % 12] : '') : '';
    const dayZhi = _shianData ? (_shianData.sizhu && _shianData.sizhu.day ? _shianData.sizhu.day.dz : '') : '';

    // 天乙贵人
    const gy = SHIAN_SS_TIANYI[dayMaster] || [];
    if (gy.includes(zhi)) stars.push('天乙贵人');
    // 太极贵人
    const tj = SHIAN_SS_TAIJI[dayMaster] || [];
    if (tj.includes(zhi)) stars.push('太极贵人');
    // 文昌贵人
    if (zhi === SHIAN_SS_WENCHANG[dayMaster]) stars.push('文昌贵人');
    // 禄神
    if (zhi === SHIAN_SS_LUSHEN[dayMaster]) stars.push('禄神');
    // 羊刃
    if (zhi === SHIAN_SS_YANGREN[dayMaster]) stars.push('羊刃');
    // 驿马（年支查）
    if (yearZhi && zhi === SHIAN_SS_YIMA[yearZhi]) stars.push('驿马');
    // 桃花（年支查）
    if (yearZhi && zhi === SHIAN_SS_TAOHUA[yearZhi]) stars.push('桃花');
    // 华盖（年支查）
    if (yearZhi && zhi === SHIAN_SS_HUAGAI[yearZhi]) stars.push('华盖');
    // 将星（年支查）
    if (yearZhi && zhi === SHIAN_SS_JIANGXING[yearZhi]) stars.push('将星');
    // 劫煞（年支查）
    if (yearZhi && zhi === SHIAN_SS_JIESHA[yearZhi]) stars.push('劫煞');
    // 亡神（年支查）
    if (yearZhi && zhi === SHIAN_SS_WANGSHEN[yearZhi]) stars.push('亡神');
    // 天德贵人
    if (monthZhi) {
        const monthIdx = SHIAN_DZ_ORDER.indexOf(monthZhi);
        const monthNum = ((monthIdx - 1 + 12) % 12) + 1;
        const tdGan = SHIAN_SS_TIANDE[monthNum];
        if (tdGan && gan === tdGan) stars.push('天德贵人');
        // 月德贵人
        const ydGan = SHIAN_SS_YUEDE[monthNum];
        if (ydGan && gan === ydGan) stars.push('月德贵人');
        // 月德合
        const ydhGan = SHIAN_SS_YUEDEHE[monthNum];
        if (ydhGan && gan === ydhGan) stars.push('月德合');
    }
    // 学堂
    const dmWx = SHIAN_SS_GANWX[dayMaster] || '';
    const xuetangZhi = SHIAN_SS_XUETANG[dmWx] || '';
    if (zhi === xuetangZhi) stars.push('学堂');
    // 正词馆
    if (xuetangZhi) {
        const xtIdx = SHIAN_DZ_ORDER.indexOf(xuetangZhi);
        const cguanZhi = SHIAN_DZ_ORDER[(xtIdx + 6) % 12];
        if (zhi === cguanZhi) stars.push('正词馆');
    }
    // 孤辰/寡宿
    if (yearZhi) {
        if (zhi === SHIAN_SS_GUCHEN[yearZhi]) stars.push('孤辰');
        if (zhi === SHIAN_SS_GUASU[yearZhi]) stars.push('寡宿');
    }
    // 红艳煞
    if (zhi === SHIAN_SS_HONGYAN[dayMaster]) stars.push('红艳煞');
    // 灾煞
    if (yearZhi && zhi === SHIAN_SS_ZAISHA[yearZhi]) stars.push('灾煞');
    // 丧门
    if (yearZhi && zhi === SHIAN_SS_SANGMEN[yearZhi]) stars.push('丧门');
    // 勾煞/绞煞
    if (yearZhi) {
        const gj = SHIAN_SS_GOUJIAO[yearZhi];
        if (gj) {
            if (zhi === gj['勾']) stars.push('勾煞');
            if (zhi === gj['绞']) stars.push('绞煞');
        }
    }
    // 红鸾
    if (yearZhi && zhi === SHIAN_SS_HONGLUAN[yearZhi]) stars.push('红鸾');
    // 天医（月支查）
    if (monthZhi && zhi === SHIAN_SS_TIANYIYI[monthZhi]) stars.push('天医');
    // 天喜（年支查）
    if (yearZhi && zhi === SHIAN_SS_TIANXI[yearZhi]) stars.push('天喜');
    // 空亡（日柱旬空）
    if (dayZhi && dayMaster) {
        const dayKw = shiAnCalcKongwang(dayMaster, dayZhi);
        if (dayKw && dayKw.includes(zhi)) stars.push('空亡');
    }

    return stars;
}

// ── 时安本地计算干支详情 ──
function shiAnComputeGanZhiDetail(ganZhi, dayMaster, shenshaList) {
    if (!ganZhi || ganZhi.length < 2) return {};
    const tg = ganZhi[0], dz = ganZhi[1];
    if (!dayMaster) return { tg, dz };
    const ss = shianGetShiShen(dayMaster, tg);
    const canggan = (SHIAN_CANG_GAN[dz] || []).map(g => ({ gz: g, ss: shianGetShiShen(dayMaster, g) }));
    const xingyun = shiAnCalcChangsheng(dayMaster, dz);
    const zizuo = shiAnCalcChangsheng(tg, dz);
    const nayin = shiAnCalcNayin(tg, dz);
    const kongwang = shiAnCalcKongwang(tg, dz);
    const shensha = shenshaList || shiAnCalcShensha(tg, dz, dayMaster);
    return { tg, dz, ss, canggan, xingyun, zizuo, nayin, kongwang, shensha };
}

// ── 从现有数据构造 时安专业盘 请求参数 ──
function _shiAnBuildParams(data) {
    // 优先从 birth_solar 解析。开启真太阳时时，birth_solar 已是实际排盘时间，
    // 与参考专业盘 URL 中的 sunTime 口径一致。
    const solar = data.birth_solar || data.birth_input || '';
    const useEffectiveSolar = !!data.birth_solar;
    let y, m, d, h, mi, jy;
    if (solar) {
        // 格式: "1990年01月01日 00:00" 或 "1990-01-01 00:00"
        const m1 = solar.match(/(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})/);
        if (m1) { y = parseInt(m1[1]); m = parseInt(m1[2]); d = parseInt(m1[3]); }
        const m2 = solar.match(/(\d{1,2})[:：](\d{1,2})/);
        if (m2) { h = parseInt(m2[1]); mi = parseInt(m2[2]); }
    }
    if (useEffectiveSolar && data.birth_input) {
        const jyParts = data.birth_input.match(/(\d{4})[年\-](\d{1,2})[月\-](\d{1,2}).*?(\d{1,2})[:：](\d{1,2})/);
        if (jyParts) {
            jy = jyParts[1]
                + String(parseInt(jyParts[2])).padStart(2, '0')
                + String(parseInt(jyParts[3])).padStart(2, '0')
                + String(parseInt(jyParts[4])).padStart(2, '0')
                + String(parseInt(jyParts[5])).padStart(2, '0');
            const effective = String(y)
                + String(m).padStart(2, '0')
                + String(d).padStart(2, '0')
                + String(h || 0).padStart(2, '0')
                + String(mi || 0).padStart(2, '0');
            const effectiveBranch = Math.floor((parseInt(effective.slice(8, 10)) + 1) / 2) % 12;
            const originalBranch = Math.floor((parseInt(jy.slice(8, 10)) + 1) / 2) % 12;
            if (effective.slice(0, 8) === jy.slice(0, 8) && effectiveBranch === originalBranch) jy = '';
        }
    }
    // 回退: 从 sessionStorage 取
    if (!y) {
        try {
            const stored = JSON.parse(sessionStorage.getItem('xc_bazi_params') || '{}');
            if (stored.birthDate) {
                const [sy, sm, sd] = stored.birthDate.split('-').map(Number);
                y = sy; m = sm; d = sd;
            }
            if (stored.birthHour) h = parseInt(stored.birthHour);
        } catch(e) {}
    }
    if (!y) return null;
    const s = data.gender === '女' ? 2 : 1;
    return { y, m, d, h: (h !== undefined && h !== null && !isNaN(h)) ? h : 0, mi: mi || 0, s, jy };
}

// ── 吉凶神煞判断 ──
const _JI_SHEN = ['天乙贵人','天德贵人','月德贵人','月德合','文昌贵人','福星贵人','太极贵人','德秀贵人','天厨贵人','国印贵人','驿马','禄神','将星','词馆','正词馆','学堂','天印贵人','天贵','天财','天官','地解','天解','月解','天赦','解神','天医','华盖','金舆','天马','攀鞍','天喜','红鸾'];
function _shiAnSsTagClass(name) {
    if (_JI_SHEN.some(j => name.includes(j))) return 'ji-shen';
    if (['羊刃','桃花','血刃','亡神','劫煞','灾煞','天煞','地煞','白虎','丧门','吊客','披麻','大耗','小耗','病符','官符','五鬼','死符','破碎','飞刃','孤辰','寡宿','孤鸾','八专','九丑','红艳煞','流霞','天罗','地网','铁扫','阎关','迷魂','天厄','天祸','天刑','天狱','天哭','天狗','天刃','天疾','天贼','勾煞','绞煞'].some(x => name.includes(x))) return 'xiong-sha';
    return '';
}

// ═══ 主渲染函数 ═══
function renderShianProTab(data) {
    // 先显示加载占位，异步加载 时安专业盘数据
    const html = `<div class="shiAn-loading" id="shiAnLoading">
        <div class="loading-spinner"></div>
        <div style="font-size:0.85rem;">正在获取时安专业盘数据...</div>
    </div>`;

    // 异步加载
    setTimeout(() => _shiAnLoadData(data), 100);
    return html;
}

async function _shiAnLoadData(data) {
    const params = _shiAnBuildParams(data);
    if (!params) {
        const el = document.getElementById('shiAnLoading');
        if (el) el.innerHTML = `<div class="shiAn-error"><div class="shiAn-error-icon">❌</div><div class="shiAn-error-msg">无法获取出生参数，请从排盘页重新进入</div></div>`;
        return;
    }

    try {
        const jyParam = params.jy ? `&jy=${encodeURIComponent(params.jy)}` : '';
        const url = `/api/bazi/shian-pro?y=${params.y}&m=${params.m}&d=${params.d}&h=${params.h}&mi=${params.mi}&s=${params.s}${jyParam}&_t=${Date.now()}`;
        const resp = await fetch(url, {cache: 'no-cache'});
        if (!resp.ok) {
            const errData = await resp.json().catch(() => ({}));
            throw new Error(errData.error || `API错误 (${resp.status})`);
        }
        const shiAnResult = await resp.json();
        if (!shiAnResult.success) {
            throw new Error(shiAnResult.error || '排盘失败');
        }
        _shianData = shiAnResult;

        // 初始化选中状态
        _shiAnInitSelection(shiAnResult);

        // 用前端计算的流月列表覆盖后端数据（前端有 current 标记，后端没有）
        const initLnList = shiAnResult.liunian_list || [];
        const initLn = initLnList[_shiAnSelectedLiunianIdx] || initLnList[0];
        if (initLn && typeof _shiAnComputeLiuyueList === 'function') {
            const initYear = parseInt(initLn.year);
            if (!isNaN(initYear)) {
                shiAnResult.liuyue_list = _shiAnComputeLiuyueList(initYear);
                // 重新设置流月选中（基于前端计算的 current 标记）
                const curIdx = shiAnResult.liuyue_list.findIndex(m => m.current);
                _shiAnSelectedLiuyueIdx = curIdx >= 0 ? curIdx : 0;
            }
        }

        // 渲染
        const panel = document.getElementById('panelWzpro');
        if (panel) {
            panel.innerHTML = _shianRenderFull(shiAnResult);
            _shiAnInitScrollMasks();
            _shiAnScrollActiveIntoView();
        }

    } catch(e) {
        const el = document.getElementById('shiAnLoading');
        if (el) el.innerHTML = `<div class="shiAn-error"><div class="shiAn-error-icon">❌</div><div class="shiAn-error-msg">${e.message}</div>
            <button class="btn-retry" onclick="_shiAnRetry()">重试</button></div>`;
    }
}

function _shiAnRetry() {
    if (_baziData) _shiAnLoadData(_baziData);
}

function _shiAnInitSelection(data) {
    const dyList = data.dayun_list || [];
    const lnList = data.liunian_list || [];
    _shiAnSelectedDayunIdx = -1;
    _shiAnSelectedLiunianIdx = -1;
    _shiAnSelectedLiuyueIdx = -1;
    _shiAnSelectedXiaoyunIdx = -1;

    // 默认选中当前大运
    for (let i = 0; i < dyList.length; i++) {
        if (dyList[i].current) { _shiAnSelectedDayunIdx = i; break; }
    }
    if (_shiAnSelectedDayunIdx < 0 && dyList.length > 1) _shiAnSelectedDayunIdx = 1;

    // 确保选中的大运包含今年流年（如果后端返回的流年列表不包含当前年份，需要找到包含今年的大运）
    const currentYear = new Date().getFullYear();
    const birthYear = data.birth_year || (data.birth_params ? parseInt(data.birth_params.y) : 0);
    if (birthYear) {
        const curLnYear = lnList.find(l => parseInt(l.year) === currentYear);
        if (!curLnYear) {
            // 当前流年列表不包含今年，找到包含今年流年的大运
            for (let i = 0; i < dyList.length; i++) {
                const dy = dyList[i];
                let sAge, eAge;
                const ageMatch = (dy.age || '').match(/(\d+)~(\d+)/);
                if (ageMatch) { sAge = parseInt(ageMatch[1]); eAge = parseInt(ageMatch[2]); }
                else { sAge = dy.start_age || 1; eAge = dy.end_age || (sAge + 9); }
                const sYear = birthYear + sAge - 1;
                const eYear = birthYear + eAge - 1;
                if (currentYear >= sYear && currentYear <= eYear) {
                    _shiAnSelectedDayunIdx = i;
                    break;
                }
            }
        }
    }

    // 根据当前大运判断默认运类型：
    // - 如果当前大运是起运前（gan_zhi为空/is_pre_qiyun），默认显示小运
    // - 如果已起运（有gan_zhi），默认显示大运，并选中真正的大运项
    const curDy = dyList[_shiAnSelectedDayunIdx] || dyList[0];
    if (curDy && (curDy.is_pre_qiyun || !curDy.gan_zhi)) {
        _shiAnActiveYunType = 'xiaoyun'; // 起运前，默认小运
    } else {
        _shiAnActiveYunType = 'dayun';   // 已起运，默认大运
        // 确保大运模式下选中非pre_qiyun的项
        if (dyList[_shiAnSelectedDayunIdx] && dyList[_shiAnSelectedDayunIdx].is_pre_qiyun) {
            const firstRealIdx = dyList.findIndex(d => !d.is_pre_qiyun);
            if (firstRealIdx >= 0) _shiAnSelectedDayunIdx = firstRealIdx;
        }
    }

    // 根据选中的大运更新流年列表（确保流年列表覆盖当前大运范围）
    _shiAnUpdateLiunianForDayun(_shiAnSelectedDayunIdx);

    // 默认选中当前流年
    const updatedLnList = data.liunian_list || [];
    for (let i = 0; i < updatedLnList.length; i++) {
        if (updatedLnList[i].current) { _shiAnSelectedLiunianIdx = i; break; }
    }
    if (_shiAnSelectedLiunianIdx < 0 && updatedLnList.length > 0) _shiAnSelectedLiunianIdx = 0;

    // 默认选中当前流月（用节气日期精确判断）
    const now = new Date();
    const currentMonth = now.getMonth() + 1;
    const currentDay = now.getDate();
    const jieMonthDays = [
        [2, 4], [3, 5], [4, 5], [5, 5], [6, 5], [7, 7],
        [8, 7], [9, 7], [10, 8], [11, 7], [12, 7], [1, 5]
    ];
    let currentLiuyueIdx = -1;
    // 丑月(索引11)跨年特殊处理：1月5日-2月3日属丑月
    if (currentMonth === 1 && currentDay >= 5) {
        currentLiuyueIdx = 11;
    } else {
        // 从前往后找最后一个满足条件的节气（跳过丑月[1,5]避免误判）
        for (let j = 0; j < jieMonthDays.length - 1; j++) {
            const [jm, jd] = jieMonthDays[j];
            if (currentMonth > jm || (currentMonth === jm && currentDay >= jd)) {
                currentLiuyueIdx = j;
            }
        }
        if (currentLiuyueIdx < 0) currentLiuyueIdx = 11; // 1月1-4日属上年丑月
    }
    _shiAnSelectedLiuyueIdx = currentLiuyueIdx;

    // 默认选中当前年龄对应的小运
    const xyList = _shiAnBuildXiaoyunList(data);
    const curXyIdx = xyList.findIndex(x => x.current);
    _shiAnSelectedXiaoyunIdx = curXyIdx >= 0 ? curXyIdx : 0;

    // 保存初始选中状态到 localStorage
    localStorage.setItem('xc_bazi_shiAnDayunIdx', _shiAnSelectedDayunIdx);
    localStorage.setItem('xc_bazi_shiAnLiunianIdx', _shiAnSelectedLiunianIdx);
    localStorage.setItem('xc_bazi_shiAnLiuyueIdx', _shiAnSelectedLiuyueIdx);
}

// ═══ 保持滚动位置重渲染 ═══
function _shiAnRerenderPanel() {
    const panel = document.getElementById('panelWzpro');
    if (!panel || !_shianData) return;

    // 1. 保存所有 shiAn-yun-items 容器的滚动位置（单行水平滚动模式保存 scrollLeft）
    const scrollPositions = {};
    panel.querySelectorAll('.shiAn-yun-items[data-yun-type]').forEach(el => {
        const t = el.getAttribute('data-yun-type');
        if (t) scrollPositions[t] = { left: el.scrollLeft };
    });

    // 2. 保存左侧排盘表的滚动位置
    const leftTable = panel.querySelector('.shiAn-pan-left');
    const leftScrollLeft = leftTable ? leftTable.scrollLeft : 0;
    const leftScrollTop = leftTable ? leftTable.scrollTop : 0;

    // 3. 保存右侧面板的滚动位置
    const rightPanel = panel.querySelector('.shiAn-pan-right');
    const rightScrollTop = rightPanel ? rightPanel.scrollTop : 0;

    // 4. 保存页面全局滚动
    const pageScrollY = window.scrollY;

    // 5. 重渲染
    panel.innerHTML = _shianRenderFull(_shianData);

    // 6. 恢复 shiAn-yun-items 滚动位置
    panel.querySelectorAll('.shiAn-yun-items[data-yun-type]').forEach(el => {
        const t = el.getAttribute('data-yun-type');
        if (t && scrollPositions[t]) {
            el.scrollLeft = scrollPositions[t].left;
        }
    });

    // 7. 恢复左侧排盘表滚动位置
    const newLeftTable = panel.querySelector('.shiAn-pan-left');
    if (newLeftTable) {
        newLeftTable.scrollLeft = leftScrollLeft;
        newLeftTable.scrollTop = leftScrollTop;
    }

    // 8. 恢复右侧面板滚动位置
    const newRightPanel = panel.querySelector('.shiAn-pan-right');
    if (newRightPanel) {
        newRightPanel.scrollTop = rightScrollTop;
    }

    // 9. 恢复页面全局滚动
    window.scrollTo(0, pageScrollY);

    // 10. 初始化滚动遮罩 + 滚动激活项到可视区
    _shiAnInitScrollMasks();
    _shiAnScrollActiveIntoView();
}

// ═══ 自定义滚动条 + 渐变遮罩 初始化 ═══
function _shiAnInitScrollMasks() {
    document.querySelectorAll('.shiAn-yun-items-wrap').forEach(wrap => {
        const items = wrap.querySelector('.shiAn-yun-items');
        const track = wrap.querySelector('.shiAn-scroll-track');
        const thumb = track ? track.querySelector('.shiAn-scroll-thumb') : null;
        if (!items || !track || !thumb) return;

        // --- 渐变遮罩 ---
        const updateMask = () => {
            const sl = items.scrollLeft;
            const maxScroll = items.scrollWidth - items.clientWidth;
            wrap.classList.toggle('scrolled-end', maxScroll <= 0 || sl >= maxScroll - 2);
            wrap.classList.toggle('scrolled-start', sl <= 2);
        };

        // --- 自定义滚动条 ---
        const updateThumb = () => {
            const ratio = items.clientWidth / items.scrollWidth;
            if (ratio >= 1) {
                track.classList.add('no-scroll');
                return;
            }
            track.classList.remove('no-scroll');
            const thumbWidth = Math.max(30, ratio * track.clientWidth);
            thumb.style.width = thumbWidth + 'px';
            const maxScroll = items.scrollWidth - items.clientWidth;
            const scrollRatio = maxScroll > 0 ? items.scrollLeft / maxScroll : 0;
            const maxThumbLeft = track.clientWidth - thumbWidth;
            thumb.style.left = (scrollRatio * maxThumbLeft) + 'px';
        };

        items.addEventListener('scroll', () => { updateMask(); updateThumb(); }, { passive: true });

        // 点击轨道跳转
        track.addEventListener('mousedown', (e) => {
            if (e.target === thumb) return; // 拖拽另外处理
            const rect = track.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const ratio = items.clientWidth / items.scrollWidth;
            const thumbWidth = Math.max(30, ratio * track.clientWidth);
            const maxThumbLeft = track.clientWidth - thumbWidth;
            const targetLeft = clickX - thumbWidth / 2;
            const scrollRatio = Math.max(0, Math.min(1, targetLeft / maxThumbLeft));
            items.scrollLeft = scrollRatio * (items.scrollWidth - items.clientWidth);
        });

        // 拖拽滑块
        let dragging = false, dragStartX = 0, dragStartScrollLeft = 0;
        thumb.addEventListener('mousedown', (e) => {
            e.preventDefault();
            dragging = true;
            dragStartX = e.clientX;
            dragStartScrollLeft = items.scrollLeft;
            thumb.classList.add('dragging');
            document.body.style.userSelect = 'none';
        });
        document.addEventListener('mousemove', (e) => {
            if (!dragging) return;
            const dx = e.clientX - dragStartX;
            const ratio = items.clientWidth / items.scrollWidth;
            const thumbWidth = Math.max(30, ratio * track.clientWidth);
            const maxThumbLeft = track.clientWidth - thumbWidth;
            const scrollPerPx = (items.scrollWidth - items.clientWidth) / maxThumbLeft;
            items.scrollLeft = dragStartScrollLeft + dx * scrollPerPx;
        });
        document.addEventListener('mouseup', () => {
            if (dragging) {
                dragging = false;
                thumb.classList.remove('dragging');
                document.body.style.userSelect = '';
            }
        });

        // 触摸拖拽
        thumb.addEventListener('touchstart', (e) => {
            dragging = true;
            dragStartX = e.touches[0].clientX;
            dragStartScrollLeft = items.scrollLeft;
            thumb.classList.add('dragging');
        }, { passive: true });
        document.addEventListener('touchmove', (e) => {
            if (!dragging) return;
            const dx = e.touches[0].clientX - dragStartX;
            const ratio = items.clientWidth / items.scrollWidth;
            const thumbWidth = Math.max(30, ratio * track.clientWidth);
            const maxThumbLeft = track.clientWidth - thumbWidth;
            const scrollPerPx = (items.scrollWidth - items.clientWidth) / maxThumbLeft;
            items.scrollLeft = dragStartScrollLeft + dx * scrollPerPx;
        }, { passive: true });
        document.addEventListener('touchend', () => {
            if (dragging) {
                dragging = false;
                thumb.classList.remove('dragging');
            }
        });

        // 初始更新
        updateMask();
        // 延迟一帧更新 thumb（等 DOM 渲染完）
        requestAnimationFrame(() => updateThumb());
    });
}

// ═══ 将选中项滚动到可视区 ═══
function _shiAnScrollActiveIntoView() {
    document.querySelectorAll('.shiAn-yun-items .shiAn-yun-item.shiAn-active').forEach(el => {
        el.scrollIntoView({ inline: 'center', behavior: 'instant', block: 'nearest' });
    });
}

// ═══ 完整渲染 ═══
function _shianRenderFull(data) {
    let html = '';

    // ── 顶部信息栏 ──
    html += _shianRenderTopBar(data);

    // ── 主布局：左排盘表 + 右选择面板 ──
    html += `<div class="shiAn-pan-layout">`;

    // 左侧排盘表
    html += _shianRenderLeftTable(data);

    // 右侧面板
    html += _shianRenderRightPanel(data);

    html += `</div>`; // shiAn-pan-layout

    // ── 干支留意信息盒子（独占一行） ──
    html += _shianRenderGuanxiBox(data);

    // ── 五行旺度条 ──
    html += _shianRenderWuxingBar(data);

    return html;
}

// ── 顶部信息栏 ──
function _shianRenderTopBar(data) {
    const sx = data.shengxiao || '';
    const sxEmoji = SHENGXIAO_EMOJI[sx] || '';
    const name = data.name || '命主';
    const genderLabel = data.gender_label || '';
    const lunar = data.lunar_date || '';
    const solar = data.solar_date || '';

    let html = `<div class="shiAn-top-bar">`;
    html += `<div class="shiAn-case-info">`;
    html += `${sxEmoji ? `<span style="font-size:1.4rem;">${sxEmoji}</span>` : ''}`;
    html += `<div style="display:flex;flex-direction:column;gap:2px;">`;
    html += `<span style="font-weight:700;color:var(--text-1);">${name} <span style="color:var(--accent);font-size:0.78rem;">${genderLabel}</span></span>`;
    html += `<span style="font-size:0.68rem;color:var(--text-3);">阴历：${lunar}</span>`;
    html += `<span style="font-size:0.68rem;color:var(--text-3);">阳历：${solar}</span>`;
    html += `</div>`;
    html += `</div>`;
    html += `<div class="shiAn-top-actions">`;
    html += `<button class="tms-toggle${_shiAnShowTMS?' active':''}" onclick="_shiAnToggleTMS()"><span class="toggle-dot"></span> 胎命身</button>`;
    html += `<button class="tms-toggle layout-toggle${_shiAnColOrder==='sz-first'?' active':''}" onclick="_shiAnToggleColOrder()" title="切换列顺序"><span class="layout-icon">⇄</span> ${_shiAnColOrder==='sz-first'?'四柱前':'大运前'}</button>`;
    html += `</div>`;
    html += `</div>`;
    return html;
}

// ── 胎命身 ──
function _shianRenderTMS(data) {
    const tms = data.tai_ming_shen || {};
    let html = `<div class="shiAn-tms-bar">`;
    ['tai_yuan','ming_gong','shen_gong'].forEach(k => {
        const gz = tms[k] ? tms[k].gan_zhi : (k === 'tai_yuan' ? (data.taiyuan||'') : k === 'ming_gong' ? (data.minggong||'') : (data.shenggong||''));
        const label = {'tai_yuan':'胎元','ming_gong':'命宫','shen_gong':'身宫'}[k];
        const nayin = tms[k] ? tms[k].nayin : '';
        html += `<div class="shiAn-tms-item">`;
        html += `<div class="shiAn-tms-label">${label}</div>`;
        html += `<div class="shiAn-tms-value">${gz ? wxSpanBZ(gz) : '-'}</div>`;
        if (nayin) html += `<div class="shiAn-tms-sub">${nayin}</div>`;
        html += `</div>`;
    });
    // 空亡
    if (data.kongwang) {
        html += `<div class="shiAn-tms-item">`;
        html += `<div class="shiAn-tms-label">空亡</div>`;
        html += `<div class="shiAn-tms-value" style="color:var(--danger);">${data.kongwang}</div>`;
        html += `</div>`;
    }
    html += `</div>`;
    return html;
}

// ── 五行统计 ──
function _shianRenderSummary(data) {
    const wxCount = data.wuxing_count || {};
    const wxWangdu = data.wuxing_wangdu || {};
    const lackWx = data.lack_wuxing || [];
    const ws = (data.wang_shuai_detail || {}).strength || data.wang_shuai || '';
    const geju = data.geju || {};

    let html = `<div class="shiAn-summary-bar">`;
    // 五行统计
    const wxItems = [
        {name: '金', count: wxCount['金']||0, color: '#ef9104'},
        {name: '木', count: wxCount['木']||0, color: '#07e930'},
        {name: '水', count: wxCount['水']||0, color: '#2e83f6'},
        {name: '火', count: wxCount['火']||0, color: '#d30505'},
        {name: '土', count: wxCount['土']||0, color: '#8b6d03'},
    ];
    html += `<div class="shiAn-wx-bar">`;
    wxItems.forEach(w => {
        html += `<span class="shiAn-wx-item" style="color:${w.color};">`;
        html += `<span class="wx-dot wx-${w.name==='金'?'metal':w.name==='木'?'wood':w.name==='水'?'water':w.name==='火'?'fire':'earth'}"></span>`;
        html += `${w.name}${w.count}`;
        html += `</span>`;
    });
    if (lackWx.length > 0) {
        html += `<span class="shiAn-wx-lack">缺${lackWx.join('')}</span>`;
    }
    html += `</div>`;
    // 旺衰+格局
    html += `<div class="shiAn-geju-info">`;
    if (ws) html += `<span class="shiAn-ws-tag">${ws}</span>`;
    if (geju.geju) html += `<span class="shiAn-geju-tag">${geju.geju}</span>`;
    html += `</div>`;
    html += `</div>`;
    return html;
}

// ── 左侧排盘表 ──
function _shianRenderLeftTable(data) {
    const sz = data.sizhu || {};
    const dayMaster = data.day_master || '';
    const dyDetail = _shiAnGetSelectedDayunDetail();
    const lnDetail = _shiAnGetSelectedLiunianDetail();
    const lmDetail = _shiAnGetSelectedLiuyueDetail();
    const xyDetail = _shiAnGetSelectedXiaoyunDetail();

    const cols = _shiAnColOrder === 'sz-first'
        ? ['year', 'month', 'day', 'hour', _shiAnActiveYunType, 'liunian', 'liuyue']
        : [_shiAnActiveYunType, 'liunian', 'liuyue', 'year', 'month', 'day', 'hour'];
    // 列标签：根据当前激活的运类型动态显示"大运"或"小运"
    const _yunLabel = _shiAnActiveYunType === 'xiaoyun' ? '小运' : '大运';
    const colLabels = _shiAnColOrder === 'sz-first'
        ? ['年柱', '月柱', '日柱', '时柱', _yunLabel, '流年', '流月']
        : [_yunLabel, '流年', '流月', '年柱', '月柱', '日柱', '时柱'];
    const colData = _shiAnColOrder === 'sz-first'
        ? [sz.year||{}, sz.month||{}, sz.day||{}, sz.hour||{}, _shiAnActiveYunType === 'xiaoyun' ? xyDetail : dyDetail, lnDetail, lmDetail]
        : [_shiAnActiveYunType === 'xiaoyun' ? xyDetail : dyDetail, lnDetail, lmDetail, sz.year||{}, sz.month||{}, sz.day||{}, sz.hour||{}];

    const rows = [
        {label:'主星', key:'ss', cls:''},
        {label:'天干', key:'tg', cls:'tg-row'},
        {label:'地支', key:'dz', cls:'dz-row'},
        {label:'藏干', key:'cg', cls:'cg-row'},
        {label:'星运', key:'xy', cls:''},
        {label:'自坐', key:'zz', cls:''},
        {label:'空亡', key:'kw', cls:''},
        {label:'纳音', key:'ny', cls:''}
    ];

    const dayPillarIdx = _shiAnColOrder === 'sz-first' ? 2 : 5;

    let html = `<div class="shiAn-pan-left"><div style="min-width:600px;">`;

    // 标题行
    html += `<div class="shiAn-row header-row">`;
    html += `<div class="shiAn-row-item label-cell">日期</div>`;
    colLabels.forEach((l, i) => {
        const isDay = i === dayPillarIdx;
        const cls = isDay ? ' day-pillar-header' : '';
        html += `<div class="shiAn-row-item${cls}">${l}</div>`;
    });
    html += `</div>`;

    // 数据行
    rows.forEach(row => {
        html += `<div class="shiAn-row ${row.cls}">`;
        html += `<div class="shiAn-row-item label-cell">${row.label}</div>`;
        colData.forEach((d, i) => {
            const isDay = i === dayPillarIdx;
            const dayCls = isDay && (row.key === 'tg' || row.key === 'dz') ? ' shiAn-day-pillar-cell' : '';
            html += `<div class="shiAn-row-item${dayCls}">${_shiAnCellContent(row.key, d, dayMaster, isDay)}</div>`;
        });
        html += `</div>`;
    });

    // 神煞分割
    html += `<div class="shiAn-ss-division"></div>`;

    // 神煞行
    html += `<div class="shiAn-row ss-row">`;
    html += `<div class="shiAn-row-item label-cell">神煞</div>`;
    colData.forEach(d => {
        const tags = (d.shensha || []).map(s => {
            const cls = _shiAnSsTagClass(s);
            return `<span class="shiAn-ss-tag ${cls}">${s}</span>`;
        }).join('');
        html += `<div class="shiAn-row-item">${tags || '-'}</div>`;
    });
    html += `</div>`;

    html += `</div></div>`;
    return html;
}

// ── 干支留意 + 五行旺衰盒子 ──
function _shianRenderGuanxiBox(data) {
    const tgRel = data.tg_guanxi || '';
    const dzRel = data.dz_guanxi || '';
    const wxCount = data.wuxing_count || {};
    const wxWangdu = data.wuxing_wangdu || {};
    const lackWx = data.lack_wuxing || [];
    const ws = (data.wang_shuai_detail || {}).strength || data.wang_shuai || '';
    const geju = data.geju || {};

    let hasContent = tgRel || dzRel || ws || geju.geju || lackWx.length > 0;
    if (!hasContent) return '';

    let html = `<div class="shiAn-guanxi-box">`;
    html += `<div class="shiAn-guanxi-box-title"><span class="shiAn-guanxi-box-icon">⚡</span> 干支留意 · 五行旺衰</div>`;
    html += `<div class="shiAn-guanxi-box-body">`;

    // 天干留意
    if (tgRel) {
        html += `<div class="shiAn-guanxi-item">`;
        html += `<span class="shiAn-guanxi-label">天干</span>`;
        html += `<span class="shiAn-guanxi-text">${formatRelationListBZ(tgRel)}</span>`;
        html += `</div>`;
    }
    // 地支留意
    if (dzRel) {
        html += `<div class="shiAn-guanxi-item">`;
        html += `<span class="shiAn-guanxi-label">地支</span>`;
        html += `<span class="shiAn-guanxi-text">${formatRelationListBZ(dzRel)}</span>`;
        html += `</div>`;
    }

    // 五行统计 + 旺衰
    const wxItems = [
        {name: '金', count: wxCount['金']||0},
        {name: '木', count: wxCount['木']||0},
        {name: '水', count: wxCount['水']||0},
        {name: '火', count: wxCount['火']||0},
        {name: '土', count: wxCount['土']||0},
    ];
    let wxHtml = `<div class="shiAn-guanxi-wx-row"><span class="shiAn-guanxi-label">五行</span><span class="shiAn-guanxi-wx-items">`;
    wxItems.forEach(w => {
        wxHtml += `<span class="shiAn-guanxi-wx-tag">${w.name}<b>${w.count}</b></span>`;
    });
    if (lackWx.length > 0) {
        wxHtml += `<span class="shiAn-guanxi-lack">缺${lackWx.join('')}</span>`;
    }
    wxHtml += `</span></div>`;
    html += wxHtml;

    // 旺衰 + 格局
    if (ws || geju.geju) {
        html += `<div class="shiAn-guanxi-item">`;
        if (ws) html += `<span class="shiAn-guanxi-ws-tag">${ws}</span>`;
        if (geju.geju) html += `<span class="shiAn-guanxi-geju-tag">${geju.geju}</span>`;
        html += `</div>`;
    }

    html += `</div>`;
    html += `</div>`;
    return html;
}

// ── 单元格内容 ──
function _shiAnCellContent(key, d, dayMaster, isDay) {
    if (!d || Object.keys(d).length === 0) return '-';
    switch(key) {
        case 'ss': return d.ss || '';
        case 'tg': {
            const gan = d.tg || '';
            if (isDay && gan && dayMaster) {
                return `<span class="shiAn-day-master-gan">${wxSpanBZ(gan)}</span>`;
            }
            return gan ? wxSpanBZ(gan) : '';
        }
        case 'dz': return d.dz ? wxSpanBZ(d.dz) : '';
        case 'cg': {
            const cgs = (d.canggan || []).map(x => {
                const gan = x.gz || '';
                const ss = x.ss || '';
                return `<div class="shiAn-canggan-item">${gan ? wxSpanBZ(gan) : ''}<span class="shiAn-canggan-ss">${ss}</span></div>`;
            }).join('');
            return cgs || '-';
        }
        case 'xy': return d.xingyun || '';
        case 'zz': return d.zizuo || '';
        case 'kw': return d.kongwang ? `<span style="color:var(--danger);">${d.kongwang}</span>` : '';
        case 'ny': return d.nayin || '';
        default: return '';
    }
}

// ── 右侧面板 ──
function _shianRenderRightPanel(data) {
    let html = `<div class="shiAn-pan-right">`;

    // 大运/小运 可切换区域
    html += _shianRenderYunSwitchSection(data);

    // 流年
    html += _shianRenderYunSection('流年', data.liunian_list || [], 'liunian');
    // 流月
    const liuyueLabel = _shiAnActiveYunType === 'xiaoyun' ? '流月' : '流月';
    html += _shianRenderYunSection(liuyueLabel, data.liuyue_list || [], 'liuyue');

    html += `</div>`;
    return html;
}

// ── 大运/小运切换区域 ──
function _shianRenderYunSwitchSection(data) {
    const isDayun = _shiAnActiveYunType === 'dayun';
    const dyList = data.dayun_list || [];
    const xyList = _shiAnBuildXiaoyunList(data);

    let html = `<div class="shiAn-yun-section">`;
    // Tab 切换头
    html += `<div class="shiAn-yun-switch-tabs">`;
    html += `<div class="shiAn-yun-tab${!isDayun ? ' active' : ''}" onclick="_shiAnSwitchYunType('xiaoyun')">小运</div>`;
    html += `<div class="shiAn-yun-tab${isDayun ? ' active' : ''}" onclick="_shiAnSwitchYunType('dayun')">大运</div>`;
    html += `</div>`;

    // 大运列表：过滤掉起运前项（is_pre_qiyun），只显示从起运开始的大运
    const dyListFiltered = dyList.filter(d => !d.is_pre_qiyun);
    // 建立过滤后索引到原始索引的映射
    const dyIdxMap = [];
    dyList.forEach((d, i) => { if (!d.is_pre_qiyun) dyIdxMap.push(i); });

    // 列表内容
    const items = isDayun ? dyListFiltered : xyList;
    const type = isDayun ? 'dayun' : 'xiaoyun';
    html += `<div class="shiAn-yun-items-wrap"><div class="shiAn-yun-items" data-yun-type="${type}">`;
    items.forEach((item, i) => {
        // 大运用原始索引，小运用过滤后索引
        const realIdx = isDayun ? dyIdxMap[i] : i;
        const isActive = (type === 'dayun' && realIdx === _shiAnSelectedDayunIdx) ||
                         (type === 'xiaoyun' && i === _shiAnSelectedXiaoyunIdx);
        const isCurrent = item.current;
        let cls = '';
        if (isActive) cls = ' shiAn-active';
        else if (isCurrent) cls = ' shiAn-current';

        const yearHtml = item.year ? `<span class="shiAn-yun-item-year">${item.year}</span>` : '';
        const ageHtml = item.age ? `<span class="shiAn-yun-item-age">${item.age}</span>` : '';
        const monthNameHtml = item.month_name ? `<span class="shiAn-yun-item-month">${item.month_name}</span>` : '';
        const tgHtml = item.tg ? `<span class="shiAn-yun-item-gz">${item.tg}</span>` : '';
        const dzHtml = item.dz ? `<span class="shiAn-yun-item-gz">${item.dz}</span>` : '';
        const tgSsHtml = item.tgSs ? `<span class="shiAn-yun-item-ss">${item.tgSs}</span>` : '';
        const dzSsHtml = item.dzSs ? `<span class="shiAn-yun-item-ss">${item.dzSs}</span>` : '';

        html += `<div class="shiAn-yun-item${cls}" onclick="_shiAnSelectYun('${type}',${realIdx})">`;
        if (type === 'liuyue') {
            html += monthNameHtml;
        } else if (type === 'dayun') {
            // 大运只显示起运时间（起始年份+起始岁数）
            const dyStartYear = item.start_year || item.year;
            const dyStartAge = item.start_age;
            html += `<span class="shiAn-yun-item-year">${dyStartYear || ''}</span>`;
            if (dyStartAge) {
                html += `<span class="shiAn-yun-item-age">${dyStartAge}岁起</span>`;
            }
        } else {
            html += yearHtml + ageHtml;
        }
        // 天干一行、地支换行，去掉 tgSs/dzSs
        if (item.tg) html += `<div>${tgHtml}</div>`;
        if (item.dz) html += `<div>${dzHtml}</div>`;
        html += `</div>`;
    });
    html += `</div><div class="shiAn-scroll-track" data-scroll-for="${type}"><div class="shiAn-scroll-thumb"></div></div></div></div>`;
    return html;
}

// ── 构建小运列表：根据当前选中的大运范围，生成对应年龄的小运数据 ──
function _shiAnBuildXiaoyunList(data) {
    const dyList = data.dayun_list || [];
    const xyRawList = data.xiaoyun_list || [];
    if (dyList.length === 0 || xyRawList.length === 0) return [];

    const dy = dyList[_shiAnSelectedDayunIdx] || dyList[0];
    if (!dy) return [];

    let startAge, endAge;
    const ageMatch = (dy.age || '').match(/(\d+)~(\d+)/);
    if (ageMatch) {
        startAge = parseInt(ageMatch[1]);
        endAge = parseInt(ageMatch[2]);
    } else {
        startAge = dy.start_age || 1;
        endAge = dy.end_age || (startAge + 9);
    }

    const dayMaster = data.day_master || '';
    const birthYear = data.birth_year || (data.birth_params ? parseInt(data.birth_params.y) : 0);
    const result = [];
    for (let age = startAge; age <= endAge; age++) {
        const xyItem = xyRawList[age - 1]; // xiaoyun_list[0] = 1岁的小运
        if (xyItem) {
            // xyItem 可能是字符串 "甲子" 或对象 {gan_zhi:"甲子"}
            const xyGz = typeof xyItem === 'string' ? xyItem : (xyItem.gan_zhi || xyItem.xiao_yun_gan_zhi || '');
            if (xyGz && xyGz.length >= 2) {
                const tg = xyGz[0];
                const dz = xyGz[1];
                result.push({
                    year: birthYear ? String(birthYear + age - 1) : '',
                    age: `${age}岁`,
                    tg: tg,
                    dz: dz,
                    tgSs: shianGetShiShen(dayMaster, tg),
                    dzSs: shianGetShiShen(dayMaster, (SHIAN_CANG_GAN[dz] || [dz])[0]),
                    gan_zhi: xyGz,
                    current: false,
                    _ageNum: age,
                });
            }
        }
    }
    // 标记当前岁数的小运
    const currentAge = _shiAnCalcCurrentAge(data);
    if (currentAge > 0) {
        const curItem = result.find(r => r._ageNum === currentAge);
        if (curItem) curItem.current = true;
    }
    return result;
}

// ── 计算当前年龄 ──
function _shiAnCalcCurrentAge(data) {
    const birthYear = data.birth_year || (data.birth_params ? parseInt(data.birth_params.y) : 0);
    if (!birthYear) return 0;
    return new Date().getFullYear() - birthYear + 1;
}

function _shianRenderYunSection(title, items, type) {
    let html = `<div class="shiAn-yun-section">`;
    // 流年标题旁添加"今"按钮
    let titleHtml = title;
    if (type === 'liunian') {
        titleHtml = `${title} <span class="shiAn-today-btn" onclick="_shiAnJumpToToday()" title="跳转到今天">今</span>`;
    }
    html += `<div class="shiAn-yun-title">${titleHtml}</div>`;
    html += `<div class="shiAn-yun-items-wrap"><div class="shiAn-yun-items" data-yun-type="${type}">`;
    items.forEach((item, i) => {
        const isActive = (type === 'dayun' && i === _shiAnSelectedDayunIdx) ||
                         (type === 'xiaoyun' && i === _shiAnSelectedXiaoyunIdx) ||
                         (type === 'liunian' && i === _shiAnSelectedLiunianIdx) ||
                         (type === 'liuyue' && i === _shiAnSelectedLiuyueIdx);
        const isCurrent = item.current;
        let cls = '';
        if (isActive) cls = ' shiAn-active';
        else if (isCurrent) cls = ' shiAn-current';

        const yearHtml = item.year ? `<span class="shiAn-yun-item-year">${item.year}</span>` : '';
        const ageHtml = item.age ? `<span class="shiAn-yun-item-age">${item.age}</span>` : '';
        const monthNameHtml = item.month_name ? `<span class="shiAn-yun-item-month">${item.month_name}</span>` : '';
        const tgHtml = item.tg ? `<span class="shiAn-yun-item-gz">${item.tg}</span>` : '';
        const dzHtml = item.dz ? `<span class="shiAn-yun-item-gz">${item.dz}</span>` : '';
        const tgSsHtml = item.tgSs ? `<span class="shiAn-yun-item-ss">${item.tgSs}</span>` : '';
        const dzSsHtml = item.dzSs ? `<span class="shiAn-yun-item-ss">${item.dzSs}</span>` : '';

        html += `<div class="shiAn-yun-item${cls}" onclick="_shiAnSelectYun('${type}',${i})">`;
        // 流月显示月份名；其他显示年份+岁数
        if (type === 'liuyue') {
            html += monthNameHtml;
        } else {
            html += yearHtml + ageHtml;
        }
        // 天干一行、地支换行，去掉 tgSs/dzSs
        if (item.tg) html += `<div>${tgHtml}</div>`;
        if (item.dz) html += `<div>${dzHtml}</div>`;
        html += `</div>`;
    });
    html += `</div><div class="shiAn-scroll-track" data-scroll-for="${type}"><div class="shiAn-scroll-thumb"></div></div></div></div>`;
    return html;
}

// ── 五行旺度条 ──
function _shianRenderWuxingBar(data) {
    const wd = data.wuxing_wangdu || {};
    const wc = data.wuxing_count || {};
    const wxLabel = {water:'水',wood:'木',gold:'金',soil:'土',fire:'火'};
    const wxEn = ['water','wood','gold','soil','fire'];
    const wxColors = {water:{color:'#2e83f6',bg:'rgba(46,131,246,0.1)'}, wood:{color:'#07e930',bg:'rgba(7,233,48,0.1)'}, gold:{color:'#ef9104',bg:'rgba(239,145,4,0.1)'}, soil:{color:'#8b6d03',bg:'rgba(139,109,3,0.1)'}, fire:{color:'#d30505',bg:'rgba(211,5,5,0.1)'}};
    // 旺度排序：旺>相>休>囚>死
    const wsRank = {旺:0, 相:1, 休:2, 囚:3, 死:4};
    const sorted = wxEn.slice().sort((a, b) => {
        const ra = wsRank[wd[wxLabel[a]] || '死'] ?? 4;
        const rb = wsRank[wd[wxLabel[b]] || '死'] ?? 4;
        return ra - rb;
    });
    let html = `<div class="shiAn-wuxing-bar">`;
    sorted.forEach(k => {
        const label = wxLabel[k];
        const ws = wd[label] || '';
        const cnt = wc[label] || 0;
        const clr = wxColors[k];
        html += `<div class="shiAn-wuxing-item" style="color:${clr.color};border:1px solid ${clr.color};background:${clr.bg};">${label}<b>${ws}</b>(${cnt})</div>`;
    });
    html += `</div>`;
    return html;
}

// ── 冲合关系 ──
function _shianRenderRelations(data) {
    const tgRel = data.tg_guanxi || '';
    const dzRel = data.dz_guanxi || '';
    if (!tgRel && !dzRel) return '';

    let html = `<div class="shiAn-relation-section">`;
    html += `<div class="shiAn-relation-title">🔗 冲合关系</div>`;
    html += `<div class="shiAn-relation-tags">`;
    if (tgRel) {
        tgRel.split(/[,，、]/).filter(Boolean).forEach(r => {
            const color = r.includes('合') ? '#07e930' : r.includes('克') || r.includes('冲') ? '#d30505' : '#ef9104';
            html += `<span class="shiAn-relation-tag" style="border-color:${color};color:${color};">干${relationLabelBZ(r)}</span>`;
        });
    }
    if (dzRel) {
        dzRel.split(/[,，、]/).filter(Boolean).forEach(r => {
            const color = r.includes('合') ? '#07e930' : r.includes('冲') || r.includes('刑') || r.includes('害') ? '#d30505' : '#ef9104';
            html += `<span class="shiAn-relation-tag" style="border-color:${color};color:${color};">支${relationLabelBZ(r)}</span>`;
        });
    }
    html += `</div></div>`;
    return html;
}

// ── 干支留意 ──
function _shianRenderGZTip(data) {
    const tgRel = data.tg_guanxi || '';
    const dzRel = data.dz_guanxi || '';
    if (!tgRel && !dzRel) return '';

    let html = `<div style="margin-top:10px;background:var(--card-bg);border:1px solid var(--card-border);border-radius:var(--radius-md);padding:12px 16px;">`;
    if (tgRel) html += `<div style="font-size:0.78rem;color:var(--text-2);line-height:1.8;">天干留意：&nbsp;<span style="color:var(--accent);font-weight:600;">${formatRelationListBZ(tgRel)}</span></div>`;
    if (dzRel) html += `<div style="font-size:0.78rem;color:var(--text-2);line-height:1.8;">地支留意：&nbsp;<span style="color:var(--accent);font-weight:600;">${formatRelationListBZ(dzRel)}</span></div>`;
    html += `</div>`;
    return html;
}

// ═══ 交互：切换大运/小运类型（右侧面板tab切换）═══
function _shiAnSwitchYunType(type) {
    if (!_shianData) return;
    _shiAnActiveYunType = type;

    if (type === 'xiaoyun') {
        // 切换到小运时，确保大运索引正确
        const dyList = _shianData.dayun_list || [];
        const isPreQiyun = dyList[0] && dyList[0].is_pre_qiyun;
        if (isPreQiyun) {
            // 未起运：小运始终基于起运前范围（索引0），恢复并更新流年
            _shiAnSelectedDayunIdx = 0;
            _shiAnUpdateLiunianForDayun(0);
        }
        // 选中当前年龄对应的小运
        const xyList = _shiAnBuildXiaoyunList(_shianData);
        const curIdx = xyList.findIndex(x => x.current);
        _shiAnSelectedXiaoyunIdx = curIdx >= 0 ? curIdx : 0;
    } else {
        // 切换到大运时，确保选中非pre_qiyun的大运
        const dyList = _shianData.dayun_list || [];
        if (dyList[_shiAnSelectedDayunIdx] && dyList[_shiAnSelectedDayunIdx].is_pre_qiyun) {
            // 当前选中的是起运前项，跳到第一个真正的大运
            const firstRealIdx = dyList.findIndex(d => !d.is_pre_qiyun);
            if (firstRealIdx >= 0) {
                _shiAnSelectedDayunIdx = firstRealIdx;
                _shiAnUpdateLiunianForDayun(firstRealIdx);
            }
        }
    }

    // 重渲染（保持滚动位置）
    _shiAnRerenderPanel();
}

// ═══ 交互：点击大运/小运/流年/流月 ═══
function _shiAnSelectYun(type, idx) {
    if (!_shianData) return;

    if (type === 'dayun') {
        _shiAnSelectedDayunIdx = idx;
        _shiAnActiveYunType = 'dayun';
        localStorage.setItem('xc_bazi_shiAnDayunIdx', idx);
        // 更新流年列表（内部已处理流月更新和选中）
        _shiAnUpdateLiunianForDayun(idx);
        _shiAnSelectedLiunianIdx = 0;
        localStorage.setItem('xc_bazi_shiAnLiunianIdx', 0);
    } else if (type === 'xiaoyun') {
        _shiAnSelectedXiaoyunIdx = idx;
        _shiAnActiveYunType = 'xiaoyun';
        // 小运对应的流年：根据小运的年龄推算年份，同步选中对应流年
        const xyList = _shiAnBuildXiaoyunList(_shianData);
        const xyItem = xyList[idx];
        if (xyItem && xyItem.year) {
            const year = parseInt(xyItem.year);
            // 小运列表是基于当前大运范围构建的，对应的流年一定在当前流年列表中
            const lnList = _shianData.liunian_list || [];
            const lnIdx = lnList.findIndex(l => parseInt(l.year) === year);
            if (lnIdx >= 0) {
                _shiAnSelectedLiunianIdx = lnIdx;
                localStorage.setItem('xc_bazi_shiAnLiunianIdx', lnIdx);
                _shiAnUpdateLiuyueForLiunian(lnIdx);
            } else {
                // 流年不在当前列表中（跨大运），需要找到对应大运并更新流年列表
                const dyList = _shianData.dayun_list || [];
                const birthYear = _shianData.birth_year || (_shianData.birth_params ? parseInt(_shianData.birth_params.y) : 0);
                if (birthYear) {
                    const targetDyIdx = dyList.findIndex(dy => {
                        let sAge, eAge;
                        const ageMatch = (dy.age || '').match(/(\d+)~(\d+)/);
                        if (ageMatch) { sAge = parseInt(ageMatch[1]); eAge = parseInt(ageMatch[2]); }
                        else { sAge = dy.start_age || 1; eAge = dy.end_age || (sAge + 9); }
                        return year >= birthYear + sAge - 1 && year <= birthYear + eAge - 1;
                    });
                    if (targetDyIdx >= 0 && targetDyIdx !== _shiAnSelectedDayunIdx) {
                        _shiAnSelectedDayunIdx = targetDyIdx;
                        _shiAnUpdateLiunianForDayun(targetDyIdx);
                        // 在更新后的流年列表中找对应年份
                        const newLnList = _shianData.liunian_list || [];
                        const newLnIdx = newLnList.findIndex(l => parseInt(l.year) === year);
                        if (newLnIdx >= 0) {
                            _shiAnSelectedLiunianIdx = newLnIdx;
                            localStorage.setItem('xc_bazi_shiAnLiunianIdx', newLnIdx);
                            _shiAnUpdateLiuyueForLiunian(newLnIdx);
                        }
                    }
                }
            }
        }
    } else if (type === 'liunian') {
        _shiAnSelectedLiunianIdx = idx;
        // 点击流年时同步小运选中项（仅在当前为小运模式时同步，不强制切换运类型）
        if (_shiAnActiveYunType === 'xiaoyun') {
            const lnList2 = _shianData.liunian_list || [];
            const lnItem2 = lnList2[idx];
            if (lnItem2 && lnItem2.year) {
                const year2 = parseInt(lnItem2.year);
                const birthYear2 = _shianData.birth_year || (_shianData.birth_params ? parseInt(_shianData.birth_params.y) : 0);
                if (birthYear2) {
                    const age2 = year2 - birthYear2 + 1;
                    const xyList2 = _shiAnBuildXiaoyunList(_shianData);
                    const xyIdx2 = xyList2.findIndex(x => x._ageNum === age2);
                    if (xyIdx2 >= 0) {
                        _shiAnSelectedXiaoyunIdx = xyIdx2;
                    }
                }
            }
        }
        localStorage.setItem('xc_bazi_shiAnLiunianIdx', idx);
        // 更新流月列表（内部已处理流月选中）
        _shiAnUpdateLiuyueForLiunian(idx);
    } else if (type === 'liuyue') {
        _shiAnSelectedLiuyueIdx = idx;
        localStorage.setItem('xc_bazi_shiAnLiuyueIdx', idx);
    }

    // 重渲染（保持滚动位置）
    _shiAnRerenderPanel();
}

// ═══ 跳转到今天 ═══
function _shiAnJumpToToday() {
    if (!_shianData) return;

    const now = new Date();
    const currentYear = now.getFullYear();
    const birthYear = _shianData.birth_year || (_shianData.birth_params ? parseInt(_shianData.birth_params.y) : 0);
    if (!birthYear) return;

    // 1. 找到包含今年流年的大运
    const dyList = _shianData.dayun_list || [];
    let targetDyIdx = -1;
    for (let i = 0; i < dyList.length; i++) {
        const dy = dyList[i];
        let sAge, eAge;
        const ageMatch = (dy.age || '').match(/(\d+)~(\d+)/);
        if (ageMatch) { sAge = parseInt(ageMatch[1]); eAge = parseInt(ageMatch[2]); }
        else { sAge = dy.start_age || 1; eAge = dy.end_age || (sAge + 9); }
        const sYear = birthYear + sAge - 1;
        const eYear = birthYear + eAge - 1;
        if (currentYear >= sYear && currentYear <= eYear) {
            targetDyIdx = i;
            break;
        }
    }
    if (targetDyIdx < 0) targetDyIdx = 0;

    // 2. 切换到对应大运并更新流年列表
    _shiAnSelectedDayunIdx = targetDyIdx;
    _shiAnUpdateLiunianForDayun(targetDyIdx);

    // 3. 选中今年的流年
    const lnList = _shianData.liunian_list || [];
    const lnIdx = lnList.findIndex(l => parseInt(l.year) === currentYear);
    if (lnIdx >= 0) {
        _shiAnSelectedLiunianIdx = lnIdx;
        localStorage.setItem('xc_bazi_shiAnLiunianIdx', lnIdx);
        _shiAnUpdateLiuyueForLiunian(lnIdx);
    }

    // 4. 切换到大运模式并选中当前年龄的小运
    _shiAnActiveYunType = 'dayun';
    const currentAge = currentYear - birthYear + 1;
    const xyList = _shiAnBuildXiaoyunList(_shianData);
    const xyIdx = xyList.findIndex(x => x._ageNum === currentAge);
    _shiAnSelectedXiaoyunIdx = xyIdx >= 0 ? xyIdx : 0;

    // 5. 重渲染（保持滚动位置）
    _shiAnRerenderPanel();
}

function _shiAnUpdateLiunianForDayun(dayunIdx) {
    const data = _shianData;
    const dyList = data.dayun_list || [];
    const dy = dyList[dayunIdx];
    if (!dy) return;

    // 计算流年数量：根据大运的岁数范围
    let startAge, endAge;
    if (dayunIdx === 0) {
        // 起运前小运，从 age 字段解析，如 "1~5岁"（从1岁开始）
        const ageMatch = (dy.age || '').match(/(\d+)~(\d+)/);
        if (ageMatch) {
            startAge = parseInt(ageMatch[1]);
            endAge = parseInt(ageMatch[2]);
        } else {
            startAge = 1;
            endAge = dy.end_age || 1;
        }
    } else {
        startAge = dy.start_age || 1;
        endAge = dy.end_age || (startAge + 9);
    }

    const birthYear = data.birth_year || (data.birth_params ? parseInt(data.birth_params.y) : 1990);
    const xyList = data.xiaoyun_list || [];

    const liunianList = [];
    for (let age = startAge; age <= endAge; age++) {
        const targetYear = birthYear + age - 1;  // 1岁=出生当年
        const existing = (data.liunian_list || []).find(ln => parseInt(ln.year) === targetYear);
        if (existing) {
            // 确保age字段和xiao_yun字段存在
            if (!existing.age) existing.age = `${age}岁`;
            if (!existing.xiao_yun && age >= 1 && age <= xyList.length) {
                existing.xiao_yun = xyList[age - 1];
            }
            liunianList.push(existing);
        } else {
            const gz = _shiAnComputeYearGanZhi(targetYear);
            if (gz) {
                const item = {
                    year: String(targetYear),
                    age: `${age}岁`,
                    tg: gz[0], tgSs: shianGetShiShen(data.day_master, gz[0]),
                    dz: gz[1], dzSs: shianGetShiShen(data.day_master, SHIAN_CANG_GAN[gz[1]] ? SHIAN_CANG_GAN[gz[1]][0] : gz[1]),
                    gan_zhi: gz,
                    current: targetYear === new Date().getFullYear(),
                    shensha: shiAnCalcShensha(gz[0], gz[1], data.day_master),
                };
                // 添加小运干支
                if (age >= 1 && age <= xyList.length) {
                    item.xiao_yun = xyList[age - 1];
                }
                liunianList.push(item);
            }
        }
    }
    if (liunianList.length > 0) data.liunian_list = liunianList;
    _shiAnSelectedLiunianIdx = 0;
    localStorage.setItem('xc_bazi_shiAnLiunianIdx', 0);
    _shiAnUpdateLiuyueForLiunian(0);
}

function _shiAnUpdateLiuyueForLiunian(liunianIdx) {
    const data = _shianData;
    const lnList = data.liunian_list || [];
    const ln = lnList[liunianIdx];
    if (!ln) return;

    const targetYear = parseInt(ln.year);
    if (isNaN(targetYear)) return;

    const liuyueList = _shiAnComputeLiuyueList(targetYear);
    data.liuyue_list = liuyueList;
    // 选中当前月份（如果有current标记），否则选第一个
    const curIdx = liuyueList.findIndex(m => m.current);
    _shiAnSelectedLiuyueIdx = curIdx >= 0 ? curIdx : 0;
    localStorage.setItem('xc_bazi_shiAnLiuyueIdx', _shiAnSelectedLiuyueIdx);
}

function _shiAnComputeLiuyueList(year) {
    const TG = '甲乙丙丁戊己庚辛壬癸';
    const lnList = _shianData.liunian_list || [];
    const selectedLn = lnList.find(l => parseInt(l.year) === year);
    // 使用选中流年的天干来推算月干（年上起月法）
    const yearGan = selectedLn ? (selectedLn.tg || '') : '';
    const yearGanIdx = yearGan ? TG.indexOf(yearGan) : -1;
    // 五虎遁：甲己年丙寅起(2), 乙庚年戊寅起(4), 丙辛年庚寅起(6), 丁壬年壬寅起(8), 戊癸年甲寅起(0)
    const monthGanStart = yearGanIdx >= 0 ? [2,4,6,8,0][yearGanIdx % 5] : 0;

    const monthZhis = ['寅','卯','辰','巳','午','未','申','酉','戌','亥','子','丑'];
    const jieNames = ['立春','惊蛰','清明','立夏','芒种','小暑','立秋','白露','寒露','立冬','大雪','小寒'];
    const jieDates = ['2/4','3/5','4/5','5/5','6/5','7/7','8/7','9/7','10/8','11/7','12/7','1/5'];
    const monthNames = ['正月','二月','三月','四月','五月','六月','七月','八月','九月','十月','冬月','腊月'];
    const dayMaster = _shianData.day_master || '';

    // 计算当前节气月索引
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1; // 1-12
    const currentDay = now.getDate();
    let currentLiuyueIdx = -1;
    if (year === currentYear) {
        // 节气月划分：用节气日期判断当前属于哪个节气月
        const jieMonthDays = [
            [2, 4], [3, 5], [4, 5], [5, 5], [6, 5], [7, 7],
            [8, 7], [9, 7], [10, 8], [11, 7], [12, 7], [1, 5]
        ];
        // 丑月(索引11)跨年特殊处理
        if (currentMonth === 1 && currentDay >= 5) {
            currentLiuyueIdx = 11;
        } else {
            // 从前往后找最后一个满足条件的（跳过丑月[1,5]避免误判）
            for (let j = 0; j < jieMonthDays.length - 1; j++) {
                const [jm, jd] = jieMonthDays[j];
                if (currentMonth > jm || (currentMonth === jm && currentDay >= jd)) {
                    currentLiuyueIdx = j;
                }
            }
            if (currentLiuyueIdx < 0) currentLiuyueIdx = 11; // 1月1-4日属上年丑月
        }
    }

    const list = [];
    for (let i = 0; i < 12; i++) {
        const mGanIdx = (monthGanStart + i) % 10;
        const mGan = TG[mGanIdx];
        const mZhi = monthZhis[i];
        list.push({
            jieqi: jieNames[i],
            date: jieDates[i],
            month_name: monthNames[i],
            tg: mGan, tgSs: shianGetShiShen(dayMaster, mGan),
            dz: mZhi, dzSs: shianGetShiShen(dayMaster, SHIAN_CANG_GAN[mZhi] ? SHIAN_CANG_GAN[mZhi][0] : mZhi),
            gan_zhi: mGan + mZhi,
            current: i === currentLiuyueIdx,
            shensha: shiAnCalcShensha(mGan, mZhi, dayMaster),
        });
    }
    return list;
}

function _shiAnComputeYearGanZhi(year) {
    const TG = '甲乙丙丁戊己庚辛壬癸';
    const DZ = '子丑寅卯辰巳午未申酉戌亥';
    const gi = (year - 4) % 10;
    const zi = (year - 4) % 12;
    if (gi < 0 || zi < 0) return null;
    return TG[gi] + DZ[zi];
}

// ── 获取选中的大运/流年/流月详细数据 ──
function _shiAnGetSelectedDayunDetail() {
    if (!_shianData) return {};
    const dyList = _shianData.dayun_details || [];
    const dyListSimple = _shianData.dayun_list || [];
    if (_shiAnSelectedDayunIdx < 1 || _shiAnSelectedDayunIdx >= dyListSimple.length) {
        return { tg:'', dz:'', ss:'小运', canggan:[], xingyun:'', zizuo:'', kongwang:'', nayin:'', shensha:[] };
    }
    const detailIdx = _shiAnSelectedDayunIdx - 1;
    if (detailIdx >= 0 && detailIdx < dyList.length) return dyList[detailIdx];
    const dy = dyListSimple[_shiAnSelectedDayunIdx];
    if (!dy || !dy.gan_zhi) return {};
    return shiAnComputeGanZhiDetail(dy.gan_zhi, _shianData.day_master);
}

function _shiAnGetSelectedLiunianDetail() {
    if (!_shianData) return {};
    const lnList = _shianData.liunian_list || [];
    if (_shiAnSelectedLiunianIdx < 0 || _shiAnSelectedLiunianIdx >= lnList.length) return {};
    const ln = lnList[_shiAnSelectedLiunianIdx];
    if (!ln || !ln.gan_zhi) return {};
    const detail = shiAnComputeGanZhiDetail(ln.gan_zhi, _shianData.day_master, ln.shensha);
    return detail;
}

function _shiAnGetSelectedLiuyueDetail() {
    if (!_shianData) return {};
    const lmList = _shianData.liuyue_list || [];
    if (_shiAnSelectedLiuyueIdx < 0 || _shiAnSelectedLiuyueIdx >= lmList.length) return {};
    const lm = lmList[_shiAnSelectedLiuyueIdx];
    if (!lm || !lm.gan_zhi) return {};
    const detail = shiAnComputeGanZhiDetail(lm.gan_zhi, _shianData.day_master, lm.shensha);
    return detail;
}

function _shiAnGetSelectedXiaoyunDetail() {
    if (!_shianData) return {};
    // 从选中的流年获取对应的小运（每个流年对应一个小运）
    const lnList = _shianData.liunian_list || [];
    if (_shiAnSelectedLiunianIdx >= 0 && _shiAnSelectedLiunianIdx < lnList.length) {
        const ln = lnList[_shiAnSelectedLiunianIdx];
        const xyGz = ln.xiao_yun || '';
        if (xyGz && xyGz.length >= 2) {
            // 小运没有后端神煞数据，使用前端计算
            return shiAnComputeGanZhiDetail(xyGz, _shianData.day_master);
        }
    }
    return {};
}

// ── 胎命身切换 ──
function _shiAnToggleTMS() {
    _shiAnShowTMS = !_shiAnShowTMS;
    if (_shianData) {
        _shiAnRerenderPanel();
    }
}

function _shiAnToggleColOrder() {
    _shiAnColOrder = _shiAnColOrder === 'dy-first' ? 'sz-first' : 'dy-first';
    if (_shianData) {
        _shiAnRerenderPanel();
    }
}
