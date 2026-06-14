// ═══ 工具函数（核心由 api-client.js 提供） ═══
// $, getCSRF, apiFetch, esc, sanitizeData, toggleTheme, openMobileMenu, closeMobileMenu 已在 api-client.js 中定义

function fmtBirth(elId) {
    const v = document.getElementById(elId).value;
    if (!v) return '';
    // datetime-local: 2000-08-01T12:00 → 200008011200
    return v.replace(/[-T:]/g, '').substring(0, 12);
}

function relationLabelHepan(desc) {
    const raw = String(desc || '').replace(/\s+/g, '');
    const charSource = raw.replace(/缺[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]+/g, '');
    const chars = charSource.match(/[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]/g) || [];
    const pairText = chars.slice(0, 2).join('');
    const allText = chars.join('');
    const hePairOrder = ['甲己', '乙庚', '丙辛', '丁壬', '戊癸'];
    const relationPairOrder = ['辰丑', '酉戌', '辰卯', '午卯', '巳亥', '辰戌', '丑戌'];
    const orderedPair = (orders) => chars.length >= 2 && chars[0] !== chars[1] ? (orders.find(item => item.includes(chars[0]) && item.includes(chars[1])) || pairText) : pairText;
    const hePairText = orderedPair(hePairOrder);
    const relationPairText = orderedPair(relationPairOrder);
    const juMap = { 子: '水局', 午: '火局', 卯: '木局', 酉: '金局' };
    const huiSets = [
        { zhis: '寅卯辰', ju: '木局' },
        { zhis: '巳午未', ju: '火局' },
        { zhis: '申酉戌', ju: '金局' },
        { zhis: '亥子丑', ju: '水局' },
    ];
    let m = raw.match(/合化([木火土金水])/);
    if (m && pairText) return `${hePairText}合化${m[1]}`;
    if (/六合|相合/.test(raw) && pairText) return `${relationPairText}合`;
    if (raw.includes('相冲') && pairText) return `${relationPairText}冲`;
    if (raw.includes('相破') && pairText) return `${relationPairText}破`;
    if (raw.includes('自刑') && pairText) return `${relationPairText}自刑`;
    if (/无恩之刑|恃势之刑|无礼之刑/.test(raw) && allText) return `${allText}三刑`;
    if (raw.includes('相刑') && pairText) return `${relationPairText}${chars[0] === chars[1] ? '自刑' : '刑'}`;
    if (raw.includes('相害') && pairText) return `${relationPairText}害`;
    if (raw.includes('相克') && pairText) return `${pairText}克`;
    m = raw.match(/拱合([子午卯酉])/);
    if (m && pairText) return `${pairText}拱合${juMap[m[1]] || m[1]}`;
    if (raw.includes('拱会') && pairText) {
        const found = huiSets.find(item => chars.slice(0, 2).every(zhi => item.zhis.includes(zhi)));
        return `${pairText}拱会${found ? found.ju : ''}`;
    }
    m = raw.match(/半合([木火金水])局/);
    if (m && pairText) return `${pairText}半合${m[1]}局`;
    m = raw.match(/三合([木火金水])局/);
    if (m && allText) return `${allText}三合${m[1]}局`;
    m = raw.match(/三会([木火金水])局/);
    if (m && raw.includes('缺') && pairText) return `${pairText}拱会${m[1]}局`;
    if (m && allText) return `${allText}三会${m[1]}局`;
    if (raw.includes('暗合') && pairText) return `${relationPairText}暗合`;
    for (const suffix of ['冲', '害', '破', '合', '克']) {
        if (raw.endsWith(suffix) && pairText) return `${relationPairText}${suffix}`;
    }
    return raw.replace(/相/g, '');
}

// 页面加载时检查是否有来自记录跳转的合盘参数
let _hepanIsReplay = false;  // 回放标记
document.addEventListener('DOMContentLoaded', function() {
    const stored = sessionStorage.getItem('xc_hepan_params');
    if (stored) {
        sessionStorage.removeItem('xc_hepan_params');
        try {
            const params = JSON.parse(stored);
            if (params.person1 && params.person2) {
                // 记住回放标记
                _hepanIsReplay = !!params._replay;
                // 填充表单并自动合盘
                autoHepanFromParams(params);
            }
        } catch(e) {}
    }
});

function autoHepanFromParams(params) {
    const p1 = params.person1 || {};
    const p2 = params.person2 || {};
    // 填充第一人
    const name1 = document.getElementById('name1');
    const gender1 = document.getElementById('gender1');
    const birth1 = document.getElementById('birth1');
    const addr1 = document.getElementById('addr1');
    if (name1) name1.value = p1.name || '';
    if (gender1) gender1.value = p1.gender || '男';
    if (addr1) addr1.value = p1.birthAddr || '';
    if (birth1 && p1.birthTime) {
        const bt = p1.birthTime;
        if (bt.length >= 12) {
            birth1.value = bt.slice(0,4) + '-' + bt.slice(4,6) + '-' + bt.slice(6,8) + 'T' + bt.slice(8,10) + ':' + bt.slice(10,12);
        }
    }
    // 填充第二人
    const name2 = document.getElementById('name2');
    const gender2 = document.getElementById('gender2');
    const birth2 = document.getElementById('birth2');
    const addr2 = document.getElementById('addr2');
    if (name2) name2.value = p2.name || '';
    if (gender2) gender2.value = p2.gender || '女';
    if (addr2) addr2.value = p2.birthAddr || '';
    if (birth2 && p2.birthTime) {
        const bt = p2.birthTime;
        if (bt.length >= 12) {
            birth2.value = bt.slice(0,4) + '-' + bt.slice(4,6) + '-' + bt.slice(6,8) + 'T' + bt.slice(8,10) + ':' + bt.slice(10,12);
        }
    }
    // 自动触发合盘
    setTimeout(() => doHepan(), 300);
}

async function doHepan() {
    const bt1 = fmtBirth('birth1');
    const bt2 = fmtBirth('birth2');
    if (!bt1 || bt1.length < 10) { alert('请输入第一人出生日期'); return; }
    if (!bt2 || bt2.length < 10) { alert('请输入第二人出生日期'); return; }

    const btn = document.getElementById('hepanBtn');
    btn.disabled = true;
    btn.textContent = '计算中...';

    const resultArea = document.getElementById('resultArea');
    resultArea.style.display = 'block';
    resultArea.innerHTML = '<div class="loading">合盘计算中...</div>';

    try {
        const resp = await apiFetch('/api/bazi/hepan', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({
                person1: {
                    name: document.getElementById('name1').value.trim(),
                    gender: document.getElementById('gender1').value,
                    birthTime: bt1,
                    calType: '公历',
                    birthAddr: document.getElementById('addr1').value.trim()
                },
                person2: {
                    name: document.getElementById('name2').value.trim(),
                    gender: document.getElementById('gender2').value,
                    birthTime: bt2,
                    calType: '公历',
                    birthAddr: document.getElementById('addr2').value.trim()
                },
                _replay: _hepanIsReplay   // 回放标记：不重复保存记录
            })
        });
        const data = await resp.json();

        if (!data.success) {
            resultArea.innerHTML = `<div class="loading">❌ ${esc(data.error || '合盘失败')}</div>`;
            return;
        }

        renderHepanResult(sanitizeData(data));
    } catch(e) {
        resultArea.innerHTML = `<div class="loading">❌ 请求失败: ${esc(e.message)}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '💑 开始合盘';
        _hepanIsReplay = false;  // 重置回放标记
    }
}

function wxColor(wx) {
    const m = {'金':'#FFD700','木':'#4CAF50','水':'#4A90D9','火':'#FF6347','土':'#A0522D'};
    return m[wx] || 'var(--text-2)';
}

function renderHepanResult(d) {
    const p1 = d.person1, p2 = d.person2;
    const n1 = p1.name || '甲方', n2 = p2.name || '乙方';
    const score = d.score;
    let scoreColor = score >= 80 ? '#2E8B57' : score >= 60 ? '#DAA520' : '#DC143C';

    let html = '';

    // 评分
    html += `<div class="score-ring">
        <div class="score-value" style="color:${scoreColor};">${score}</div>
        <div class="score-label">合盘评分（满分100）</div>
    </div>`;

    // 基本信息对比
    html += `<div class="summary-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="text-align:center;flex:1;">
                <div style="font-size:1.1rem;font-weight:600;color:var(--accent);">${n1}</div>
                <div style="font-size:0.8rem;color:var(--text-2);margin-top:4px;">${p1.birth}</div>
                <div style="font-size:1.4rem;margin-top:6px;">${['year','month','day','hour'].map(p=>(p1.four_pillars[p]||{}).gan+(p1.four_pillars[p]||{}).zhi).join(' ')}</div>
                ${p1.lack_wuxing && p1.lack_wuxing.length ? `<div style="font-size:0.75rem;color:var(--danger);margin-top:4px;">缺${p1.lack_wuxing.join('')}</div>` : ''}
            </div>
            <div style="font-size:1.5rem;color:var(--accent);">💑</div>
            <div style="text-align:center;flex:1;">
                <div style="font-size:1.1rem;font-weight:600;color:var(--accent);">${n2}</div>
                <div style="font-size:0.8rem;color:var(--text-2);margin-top:4px;">${p2.birth}</div>
                <div style="font-size:1.4rem;margin-top:6px;">${['year','month','day','hour'].map(p=>(p2.four_pillars[p]||{}).gan+(p2.four_pillars[p]||{}).zhi).join(' ')}</div>
                ${p2.lack_wuxing && p2.lack_wuxing.length ? `<div style="font-size:0.75rem;color:var(--danger);margin-top:4px;">缺${p2.lack_wuxing.join('')}</div>` : ''}
            </div>
        </div>
    </div>`;

    // 日主关系
    if (d.day_relation && d.day_relation.length) {
        html += `<div class="compare-section">
            <div class="compare-title">☀️ 日主关系</div>
            <div class="day-relation">
                ${d.day_relation.map(r => `<span class="day-relation-item">${r}</span>`).join('')}
            </div>
        </div>`;
    }

    // 柱位对比
    html += `<div class="compare-section">
        <div class="compare-title">📊 柱位对比</div>`;
    for (const pc of d.pillar_compare) {
        const relsHtml = (pc.relations||[]).map(r =>
            `<span class="rel-tag ${r.positive?'positive':'negative'}">${relationLabelHepan(r.desc)}</span>`
        ).join('') || '<span style="color:var(--text-3);font-size:0.75rem;">无特殊关系</span>';

        html += `<div class="pillar-row">
            <span class="pillar-label">${pc.label}</span>
            <span class="pillar-gz" style="color:var(--info);">${pc.person1}</span>
            <span class="pillar-arrow">⇄</span>
            <span class="pillar-gz" style="color:var(--success);">${pc.person2}</span>
            <span class="pillar-rels">${relsHtml}</span>
        </div>`;
    }
    html += `</div>`;

    // 五行互补
    html += `<div class="compare-section">
        <div class="compare-title">🔄 五行互补</div>
        <table class="wx-table">
            <thead><tr><th>五行</th><th>${n1}</th><th>${n2}</th><th>合计</th><th>状态</th></tr></thead>
            <tbody>`;
    for (const [wx, info] of Object.entries(d.wx_complement)) {
        html += `<tr>
            <td style="color:${wxColor(wx)};font-weight:600;">${wx}</td>
            <td>${info.person1}</td><td>${info.person2}</td><td>${info.total}</td>
            <td><span class="wx-status ${info.status}">${info.status}</span></td>
        </tr>`;
    }
    html += `</tbody></table></div>`;

    // 综合分析
    let summary = '';
    const heCount = d.pillar_compare.reduce((s,pc) => s + (pc.relations||[]).filter(r=>r.positive).length, 0);
    const chongCount = d.pillar_compare.reduce((s,pc) => s + (pc.relations||[]).filter(r=>!r.positive).length, 0);
    const complementCount = Object.values(d.wx_complement).filter(v=>v.status==='互补').length;
    const lackCount = Object.values(d.wx_complement).filter(v=>v.status==='双缺').length;

    if (score >= 80) {
        summary = `${n1}与${n2}八字相合度很高！四柱干支有${heCount}处相合关系，五行有${complementCount}处互补，命理上属于良配。双方能互相助力，感情和谐。`;
    } else if (score >= 60) {
        summary = `${n1}与${n2}八字合盘中规中矩。有${heCount}处相合、${chongCount}处相冲，五行有${complementCount}处互补。整体尚可，需在相处中多包容理解。`;
    } else {
        summary = `${n1}与${n2}八字冲合较多，四柱有${chongCount}处冲害关系，五行有${lackCount}处双缺。命理上需注意磨合，但命盘只是参考，关键在双方用心经营。`;
    }

    html += `<div class="compare-section">
        <div class="compare-title">📜 综合分析</div>
        <div class="summary-card">
            <div class="summary-text">${summary}</div>
        </div>
    </div>`;

    // 免责声明
    html += `<div style="text-align:center;margin:20px 0;font-size:0.72rem;color:var(--text-3);">
        ⚠️ 八字合盘仅供传统文化研究参考，不构成任何决策建议
    </div>`;

    document.getElementById('resultArea').innerHTML = html;
}
