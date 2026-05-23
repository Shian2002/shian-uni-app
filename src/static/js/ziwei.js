// ═══ 紫微斗数专用脚本 ═══
// esc, sanitizeData, apiFetch 由 api-client.js 提供

// 紫微API基础地址 — 与六爻/梅花/塔罗统一，使用相对路径
const ZW_API_BASE = '';

let zwLastPanData = null;

// ── Tab切换 ──
function switchZiweiTab(btn) {
    btn.parentElement.querySelectorAll('.tool-tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tool-tab-content').forEach(c => c.style.display = 'none');
    const tabId = 'tab-' + btn.dataset.tab;
    const el = document.getElementById(tabId);
    if (el) el.style.display = 'block';
}

// ── 获取排盘表单数据 ──
function getZwFormData(prefix) {
    prefix = prefix || 'zw-';
    return {
        year: parseInt(document.getElementById(prefix + 'year').value),
        month: parseInt(document.getElementById(prefix + 'month').value),
        day: parseInt(document.getElementById(prefix + 'day').value),
        hour: parseInt(document.getElementById(prefix + 'hour').value),
        minute: parseInt((document.getElementById(prefix + 'minute') || {}).value) || 0,
        gender: document.getElementById(prefix + 'gender').value,
        date_type: document.getElementById(prefix + 'datetype').value,
    };
}

// ── 紫微免费排盘 ──
async function ziweiFreePan() {
    const btn = document.getElementById('zwPanBtn');
    if (btn.disabled) return;

    const data = getZwFormData('zw-');
    btn.disabled = true;
    btn.textContent = '排盘中...';

    const resultEl = document.getElementById('zwPanResult');
    resultEl.style.display = 'block';
    resultEl.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-3);">⭐ 紫微排盘计算中...</div>';

    try {
        const resp = await fetch(ZW_API_BASE + '/api/ziwei/pan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await resp.json();
        // 适配Flask统一返回格式 {code: 0, msg: "success", data: {...}}
        if (result.code !== undefined && result.code !== 0) {
            resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">${esc(result.msg || '排盘失败')}</div>`;
            return;
        }
        const panData = sanitizeData(result.data || result);
        zwLastPanData = panData;
        resultEl.innerHTML = renderZiweiPan(panData);
    } catch (e) {
        resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">排盘失败: ${esc(e.message)}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '⭐ 免费排盘';
    }
}

// ── 紫微推运 ──
async function ziweiHoroscope() {
    const data = getZwFormData('zw-h-');

    // 读取推运日期选择器
    const ty = document.getElementById('zwTargetYear');
    const tm = document.getElementById('zwTargetMonth');
    const td = document.getElementById('zwTargetDay');
    const th = document.getElementById('zwTargetHour');
    const tmi = document.getElementById('zwTargetMinute');
    if (!ty || !ty.value || !tm || !tm.value || !td || !td.value) {
        alert('请选择推运日期');
        return;
    }
    data.target_date = ty.value + '-' + tm.value + '-' + td.value;
    if (th && th.value) data.target_hour = parseInt(th.value);
    if (tmi && tmi.value) data.target_minute = parseInt(tmi.value);

    const resultEl = document.getElementById('zwHoroscopeResult');
    resultEl.style.display = 'block';
    resultEl.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-3);">📅 推运计算中...</div>';

    try {
        const resp = await fetch(ZW_API_BASE + '/api/ziwei/horoscope', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await resp.json();
        // 适配Flask统一返回格式
        if (result.code !== undefined && result.code !== 0) {
            resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">${esc(result.msg || '推运失败')}</div>`;
            return;
        }
        const horoData = sanitizeData(result.data || result);
        resultEl.innerHTML = renderZiweiHoroscope(horoData);
    } catch (e) {
        resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">推运失败: ${e.message}</div>`;
    }
}

// ── 渲染排盘结果 ──
function renderZiweiPan(d) {
    let html = '<div class="zw-result-wrap">';

    const bi = d.basic_info || {};
    const cp = d.core_palace || {};

    // ═══ 基础信息卡片 ═══
    html += '<div class="zw-basic-card"><div class="zw-basic-grid">';
    html += zwBasicItem('阳历', bi.solar_date);
    html += zwBasicItem('农历', bi.lunar_date);
    html += zwBasicItem('八字', bi.chinese_date);
    html += zwBasicItem('时辰', (bi.shichen || '') + ' ' + (bi.shichen_range || ''));
    html += zwBasicItem('生肖', bi.zodiac);
    html += zwBasicItem('星座', bi.sign);
    html += zwBasicItem('五行局', cp.five_elements_class);
    html += zwBasicItem('命主', cp.soul_star);
    html += zwBasicItem('身主', cp.body_star);
    html += '</div></div>';

    // ═══ 十二宫格 ═══
    const palaces = d.twelve_palaces || [];
    html += '<div class="zw-palace-grid">';

    // 第1行: 巳(4) 午(3) 未(5) 申(6)  → 田宅/官禄/交友/迁移
    html += zwPalaceCell(palaces[4]);
    html += zwPalaceCell(palaces[3]);
    html += zwPalaceCell(palaces[5]);
    html += zwPalaceCell(palaces[6]);

    // 第2行: 辰(2) [中心] 酉(7)  → 福德 [中心] 疾厄
    html += zwPalaceCell(palaces[2]);
    html += `<div class="zw-center-info">
        <div class="zw-center-title">紫微斗数命盘</div>
        <div class="zw-center-wuxing">${cp.five_elements_class || ''}</div>
        <div class="zw-center-soul">命主: ${cp.soul_star || ''}</div>
        <div class="zw-center-soul">身主: ${cp.body_star || ''}</div>
        <div class="zw-center-date">${bi.solar_date || ''} ${bi.shichen || ''}</div>
    </div>`;
    html += zwPalaceCell(palaces[7]);

    // 第3行: 卯(1) [中心续] 戌(8)  → 父母 [中心] 财帛
    html += zwPalaceCell(palaces[1]);
    html += zwPalaceCell(palaces[8]);

    // 第4行: 寅(0) 丑(11) 子(10) 亥(9)  → 命宫/兄弟/夫妻/子女
    html += zwPalaceCell(palaces[0]);
    html += zwPalaceCell(palaces[11]);
    html += zwPalaceCell(palaces[10]);
    html += zwPalaceCell(palaces[9]);

    html += '</div>';

    // ═══ 大限概览 ═══
    if (d.decadal_overview && d.decadal_overview.length > 0) {
        html += '<div class="zw-decadal-card">';
        html += '<div class="zw-decadal-title">📅 大限概览</div>';
        html += '<table class="zw-decadal-table">';
        html += '<tr><th>宫位</th><th>年龄范围</th><th>干支</th></tr>';
        d.decadal_overview.forEach(dec => {
            const range = dec.age_range || [];
            html += `<tr>
                <td>${dec.palace_name || ''}</td>
                <td>${range[0] || ''}-${range[1] || ''}岁</td>
                <td>${dec.ganzhi || ''}</td>
            </tr>`;
        });
        html += '</table></div>';
    }

    // ═══ 免责声明 ═══
    html += '<div class="privacy-note" style="margin-top:16px;">⚠️ 以上内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</div>';
    html += '</div>';
    return html;
}

// ── 渲染推运结果 ──
function renderZiweiHoroscope(d) {
    let html = '<div class="zw-result-wrap">';

    html += `<div class="zw-horoscope-title">🔮 推运信息 - ${d.target_date || ''}</div>`;
    html += '<div class="zw-period-grid">';

    const periods = [
        { key: 'decadal', label: '大限' },
        { key: 'age', label: '小限' },
        { key: 'yearly', label: '流年' },
        { key: 'monthly', label: '流月' },
        { key: 'daily', label: '流日' },
        { key: 'hourly', label: '流时' },
    ];

    periods.forEach(p => {
        const pd = d[p.key];
        if (!pd) return;

        html += '<div class="zw-period-card">';
        html += `<div class="zw-period-name">${pd.name || p.label}</div>`;
        html += `<div class="zw-period-ganzhi">${pd.ganzhi || ''}</div>`;
        if (pd.range) {
            html += `<div class="zw-period-range">${pd.range[0]}-${pd.range[1]}岁</div>`;
        }
        if (pd.nominal_age) {
            html += `<div class="zw-period-range">虚岁${pd.nominal_age}</div>`;
        }
        // 四化标签
        if (pd.mutagen && pd.mutagen.length > 0) {
            html += '<div class="zw-period-mutagen">';
            html += '<span style="color:var(--text-4);font-size:0.6875rem;">四化:</span>';
            pd.mutagen.forEach(m => {
                let mCls = '';
                if (m.includes('禄')) mCls = 'zw-mutagen-lu';
                else if (m.includes('权')) mCls = 'zw-mutagen-quan';
                else if (m.includes('科')) mCls = 'zw-mutagen-ke';
                else if (m.includes('忌')) mCls = 'zw-mutagen-ji';
                html += `<span class="zw-mutagen ${mCls}">${m}</span>`;
            });
            html += '</div>';
        }
        html += '</div>';
    });

    html += '</div>';

    // 免责声明
    html += '<div class="privacy-note" style="margin-top:16px;">⚠️ 以上内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</div>';
    html += '</div>';
    return html;
}

// ── 渲染单个宫位 ──
function zwPalaceCell(p) {
    if (!p) return '<div class="zw-palace-cell"></div>';

    let cls = 'zw-palace-cell';
    let badge = '';
    if (p.is_body_palace) { cls += ' is-body'; badge += '<span class="zw-palace-badge zw-badge-body">身</span>'; }
    if (p.name === '命宫') { cls += ' is-soul'; badge += '<span class="zw-palace-badge zw-badge-soul">命</span>'; }

    // 星曜
    let starsHtml = '';
    (p.major_stars || []).forEach(s => {
        let mut = '';
        if (s.mutagen) {
            let mCls = '';
            if (s.mutagen.includes('禄')) mCls = 'zw-mutagen-lu';
            else if (s.mutagen.includes('权')) mCls = 'zw-mutagen-quan';
            else if (s.mutagen.includes('科')) mCls = 'zw-mutagen-ke';
            else if (s.mutagen.includes('忌')) mCls = 'zw-mutagen-ji';
            mut = `<span class="zw-mutagen ${mCls}">${s.mutagen}</span>`;
        }
        const brightness = s.brightness ? `(${s.brightness})` : '';
        starsHtml += `<span class="zw-star-major">${s.name}${brightness}${mut}</span>`;
    });
    (p.minor_stars || []).forEach(s => {
        starsHtml += `<span class="zw-star-minor">${s.name}</span>`;
    });
    (p.adjective_stars || []).slice(0, 4).forEach(s => {
        starsHtml += `<span class="zw-star-adj">${s.name}</span>`;
    });

    // 大限
    let decHtml = '';
    if (p.decadal && p.decadal.range) {
        decHtml = `<div class="zw-palace-decadal">大限: ${p.decadal.range[0]}-${p.decadal.range[1]}岁 ${p.decadal.heavenly_stem || ''}${p.decadal.earthly_branch || ''}</div>`;
    }

    return `<div class="${cls}">
        ${badge}
        <div class="zw-palace-header">
            <span class="zw-palace-name">${p.name}</span>
            <span class="zw-palace-ganzhi">${p.ganzhi || ''}</span>
        </div>
        <div class="zw-palace-stars">${starsHtml}</div>
        ${decHtml}
    </div>`;
}

// ── 基础信息项 ──
function zwBasicItem(label, value) {
    return `<div class="zw-basic-item">
        <span class="zw-basic-label">${label}</span>
        <span class="zw-basic-value">${value || ''}</span>
    </div>`;
}

// ── 推运日期选择器初始化 + 联动 ──
function zwInitTargetDatePicker() {
    var now = new Date();
    var curYear = now.getFullYear();
    ['zwTargetYear','zwTargetMonth','zwTargetHour','zwTargetMinute'].forEach(function(id) {
        var sel = document.getElementById(id);
        if (!sel) return;
        if (id === 'zwTargetYear') {
            sel.innerHTML = '<option value="" selected disabled>年</option>';
            for (var y = curYear + 3; y >= 1920; y--) {
                var o = document.createElement('option');
                o.value = y; o.textContent = y + '年';
                sel.appendChild(o);
            }
            sel.value = curYear;
        } else if (id === 'zwTargetMonth') {
            sel.innerHTML = '<option value="" selected disabled>月</option>';
            for (var m = 1; m <= 12; m++) {
                var o = document.createElement('option');
                o.value = String(m).padStart(2, '0'); o.textContent = m + '月';
                sel.appendChild(o);
            }
            sel.value = String(now.getMonth() + 1).padStart(2, '0');
        } else if (id === 'zwTargetHour') {
            sel.innerHTML = '<option value="" disabled selected>时</option>';
            for (var h = 0; h <= 23; h++) {
                var o = document.createElement('option');
                o.value = String(h).padStart(2, '0'); o.textContent = h + '时';
                sel.appendChild(o);
            }
            sel.value = String(now.getHours()).padStart(2, '0');
        } else if (id === 'zwTargetMinute') {
            sel.innerHTML = '<option value="" selected disabled>分</option>';
            for (var m = 0; m <= 59; m++) {
                var o = document.createElement('option');
                o.value = String(m).padStart(2, '0'); o.textContent = m + '分';
                sel.appendChild(o);
            }
            sel.value = String(now.getMinutes()).padStart(2, '0');
        }
    });
    zwTargetDateChange();
    var daySel = document.getElementById('zwTargetDay');
    if (daySel) daySel.value = String(now.getDate()).padStart(2, '0');
}
function zwTargetDateChange() {
    var yearSel = document.getElementById('zwTargetYear');
    var monthSel = document.getElementById('zwTargetMonth');
    var daySel = document.getElementById('zwTargetDay');
    if (!yearSel || !monthSel || !daySel) return;
    var y = parseInt(yearSel.value);
    var m = parseInt(monthSel.value);
    if (!yearSel.value || !monthSel.value || isNaN(y) || isNaN(m)) {
        daySel.innerHTML = '<option value="" selected disabled>日</option>';
        return;
    }
    var daysInMonth = new Date(y, m, 0).getDate();
    var prevDay = daySel.value;
    daySel.innerHTML = '<option value="" disabled>日</option>';
    for (var d = 1; d <= daysInMonth; d++) {
        var o = document.createElement('option');
        o.value = String(d).padStart(2, '0'); o.textContent = d + '日';
        daySel.appendChild(o);
    }
    if (prevDay && parseInt(prevDay) <= daysInMonth) daySel.value = prevDay;
}

// ── 页面加载后自动初始化推运日期选择器 ──
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(function() {
                if (typeof zwInitTargetDatePicker === 'function') zwInitTargetDatePicker();
            }, 100);
        });
    } else {
        setTimeout(function() {
            if (typeof zwInitTargetDatePicker === 'function') zwInitTargetDatePicker();
        }, 100);
    }
})();
