// ═══ 梅花易数专用脚本 ═══
// esc, sanitizeData, apiFetch 由 api-client.js 提供

// ── 起卦方式切换（免费排盘tab） ──
function switchMethod(btn, method) {
    btn.parentElement.querySelectorAll('.method-switch-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('#tab-meihua-free .mh-method-content').forEach(c => c.style.display = 'none');
    const el = document.getElementById('mh-method-' + method);
    if (el) el.style.display = 'block';
}

// ── 起卦方式切换（AI系统tab） ──
function switchMethodAI(btn, method) {
    btn.parentElement.querySelectorAll('.method-switch-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('#tab-meihua-ai .mh-method-content').forEach(c => c.style.display = 'none');
    const el = document.getElementById('mai-method-' + method);
    if (el) el.style.display = 'block';
}

// ── 设置默认时间 ──
(function() {
    const now = new Date();
    const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
})();

// ── 梅花日期选择器初始化（仿奇门风格） ──
function mfInitDatePicker() {
    if (!document.getElementById('mfYear')) return;
    const now = new Date();
    const curYear = now.getFullYear();
    ['mf','mai'].forEach(prefix => {
        const yearSel = document.getElementById(prefix + 'Year');
        if (!yearSel) return;
        yearSel.innerHTML = '<option value=\"\" selected disabled>年</option>';
        for (let y = curYear; y >= 1920; y--) {
            const opt = document.createElement('option');
            opt.value = y; opt.textContent = y + '年';
            yearSel.appendChild(opt);
        }
        const monthSel = document.getElementById(prefix + 'Month');
        monthSel.innerHTML = '<option value=\"\" selected disabled>月</option>';
        for (let m = 1; m <= 12; m++) {
            const opt = document.createElement('option');
            opt.value = String(m).padStart(2, '0'); opt.textContent = m + '月';
            monthSel.appendChild(opt);
        }
        const hourSel = document.getElementById(prefix + 'Hour');
        if (hourSel) {
            hourSel.innerHTML = '<option value=\"\" disabled selected>时</option>';
            for (let h = 0; h <= 23; h++) {
                const opt = document.createElement('option');
                opt.value = String(h).padStart(2, '0');
                opt.textContent = h + '时';
                hourSel.appendChild(opt);
            }
        }
        const minSel = document.getElementById(prefix + 'Minute');
        if (minSel) {
            minSel.innerHTML = '<option value=\"\" selected disabled>分</option>';
            for (let m = 0; m <= 59; m++) {
                const opt = document.createElement('option');
                opt.value = String(m).padStart(2, '0'); opt.textContent = m + '分';
                minSel.appendChild(opt);
            }
        }
        // 默认当前时间
        yearSel.value = curYear;
        monthSel.value = String(now.getMonth() + 1).padStart(2, '0');
        if (hourSel) hourSel.value = String(now.getHours()).padStart(2, '0');
        if (minSel) minSel.value = String(now.getMinutes()).padStart(2, '0');
        // 日期
        const fn = prefix === 'mf' ? 'mfOnDateChange' : 'maiOnDateChange';
        if (typeof window[fn] === 'function') window[fn]();
        const daySel = document.getElementById(prefix + 'Day');
        if (daySel) daySel.value = String(now.getDate()).padStart(2, '0');
    });
}
function mfOnDateChange() {
    const yearSel = document.getElementById('mfYear');
    const monthSel = document.getElementById('mfMonth');
    const daySel = document.getElementById('mfDay');
    if (!yearSel || !monthSel || !daySel) return;
    const y = parseInt(yearSel.value);
    const m = parseInt(monthSel.value);
    if (!yearSel.value || !monthSel.value || isNaN(y) || isNaN(m)) {
        daySel.innerHTML = '<option value=\"\" selected disabled>日</option>';
        return;
    }
    const daysInMonth = new Date(y, m, 0).getDate();
    const prevDay = daySel.value;
    daySel.innerHTML = '<option value=\"\" disabled>日</option>';
    for (let d = 1; d <= daysInMonth; d++) {
        const opt = document.createElement('option');
        opt.value = String(d).padStart(2, '0'); opt.textContent = d + '日';
        daySel.appendChild(opt);
    }
    if (prevDay && parseInt(prevDay) <= daysInMonth) daySel.value = prevDay;
}
function maiOnDateChange() {
    const yearSel = document.getElementById('maiYear');
    const monthSel = document.getElementById('maiMonth');
    const daySel = document.getElementById('maiDay');
    if (!yearSel || !monthSel || !daySel) return;
    const y = parseInt(yearSel.value);
    const m = parseInt(monthSel.value);
    if (!yearSel.value || !monthSel.value || isNaN(y) || isNaN(m)) {
        daySel.innerHTML = '<option value=\"\" selected disabled>日</option>';
        return;
    }
    const daysInMonth = new Date(y, m, 0).getDate();
    const prevDay = daySel.value;
    daySel.innerHTML = '<option value=\"\" disabled>日</option>';
    for (let d = 1; d <= daysInMonth; d++) {
        const opt = document.createElement('option');
        opt.value = String(d).padStart(2, '0'); opt.textContent = d + '日';
        daySel.appendChild(opt);
    }
    if (prevDay && parseInt(prevDay) <= daysInMonth) daySel.value = prevDay;
}

// ── 梅花易数免费排盘 ──
async function meihuaFreePaipan() {
    const activeMethod = document.querySelector('.method-switch-btn.active');
    const method = activeMethod ? activeMethod.getAttribute('data-method') : 'time';

    const data = { method: method };

    // 收集输入参数
    if (method === 'time') {
        const yearEl = document.getElementById('mfYear');
        const monthEl = document.getElementById('mfMonth');
        const dayEl = document.getElementById('mfDay');
        const hourEl = document.getElementById('mfHour');
        const minEl = document.getElementById('mfMinute');
        if (yearEl && yearEl.value && monthEl && monthEl.value && dayEl && dayEl.value) {
            const y = yearEl.value, m = monthEl.value, d = dayEl.value;
            const h = hourEl && hourEl.value ? hourEl.value : '12';
            const mi = minEl && minEl.value ? minEl.value : '0';
            data.time = y + '-' + m + '-' + d + 'T' + h + ':' + mi;
        }
    } else if (method === 'number') {
        const num1 = document.getElementById('mf-num1');
        const num2 = document.getElementById('mf-num2');
        if (!num1 || !num1.value) {
            alert('请输入第一个数字');
            return;
        }
        data.num1 = parseInt(num1.value);
        data.num2 = num2 && num2.value ? parseInt(num2.value) : 0;
    } else if (method === 'word') {
        const words = document.getElementById('mf-words');
        if (!words || !words.value.trim()) {
            alert('请输入文字');
            return;
        }
        data.words = words.value.trim();
    }

    // 问事（选填）
    const questionEl = document.getElementById('mf-question');
    if (questionEl && questionEl.value.trim()) {
        data.question = questionEl.value.trim();
    }

    const resultEl = document.getElementById('mhResult');
    if (!resultEl) return;
    resultEl.style.display = 'block';
    resultEl.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-3);">🌸 排盘计算中...</div>';

    try {
        const resp = await apiFetch('/api/meihua/paipan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await resp.json();
        if (result.error) {
            resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">${esc(result.error)}</div>`;
            return;
        }
        resultEl.innerHTML = renderMeihuaResult(sanitizeData(result));
    } catch (e) {
        resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">排盘失败: ${e.message}</div>`;
    }
}

// ── 渲染梅花易数排盘结果 ──
function renderMeihuaResult(d) {
    let html = '<div class="mh-result-wrap">';

    // ═══ 概要信息 ═══
    html += '<div class="mh-summary">';
    html += `<span><b>起卦方式：</b>${d.methodLabel || '时间起卦'}</span>`;
    html += `<span><b>排盘时间：</b>${d.paipanTime || ''}</span>`;
    if (d.ganzhi) {
        html += `<span><b>干支：</b>${d.ganzhi}</span>`;
    }
    html += '</div>';

    // ═══ 本卦 / 互卦 / 变卦 ═══
    html += '<div class="gua-display">';

    // 本卦
    html += renderGuaCard('本卦', d.benGua, 'ben-gua', d.dongYao, d.benGuaYao || null);
    // 互卦
    html += renderGuaCard('互卦', d.huGua, 'hu-gua', 0, d.huGuaYao || null);
    // 变卦
    html += renderGuaCard('变卦', d.bianGua, 'bian-gua', 0, d.bianGuaYao || null);

    html += '</div>';

    // ═══ 体用分析 ═══
    if (d.tiYong) {
        html += '<div class="ti-yong-section">';
        html += '<div class="ti-yong-title">🌸 体用分析</div>';

        html += '<div class="ti-yong-grid">';
        // 体卦
        html += `<div class="ti-yong-box ti">
            <div class="ti-yong-label">体卦（${d.tiYong.tiPosition}）</div>
            <div class="ti-yong-gua">${d.tiYong.tiGua}</div>
            <div class="ti-yong-wx">
                ${d.tiYong.tiTrigram || ''}
                <span class="wx-tag ${wxClass(d.tiYong.tiWuxing)}">${d.tiYong.tiWuxing}</span>
                <span class="ws-tag ${wsClass(d.tiYong.tiWangshuai)}">${d.tiYong.tiWangshuai}</span>
            </div>
        </div>`;
        // 体用关系
        html += `<div class="ti-yong-rel ${relClass(d.tiYong.tiYongRel)}">
            体${d.tiYong.tiWuxing} ${d.tiYong.tiYongRel} 用${d.tiYong.yongWuxing}
        </div>`;
        // 用卦
        html += `<div class="ti-yong-box yong">
            <div class="ti-yong-label">用卦（${d.tiYong.yongPosition}）</div>
            <div class="ti-yong-gua">${d.tiYong.yongGua}</div>
            <div class="ti-yong-wx">
                ${d.tiYong.yongTrigram || ''}
                <span class="wx-tag ${wxClass(d.tiYong.yongWuxing)}">${d.tiYong.yongWuxing}</span>
                <span class="ws-tag ${wsClass(d.tiYong.yongWangshuai)}">${d.tiYong.yongWangshuai}</span>
            </div>
        </div>`;
        html += '</div>';

        // 关系详表
        html += '<table class="mh-analysis-table">';
        html += '<tr><th>分析项</th><th>关系</th><th>吉凶</th></tr>';
        if (d.tiYong.tiYongJiXiong) {
            html += `<tr><td>体用关系</td><td>体${d.tiYong.tiWuxing} ${d.tiYong.tiYongRel} 用${d.tiYong.yongWuxing}</td><td>${d.tiYong.tiYongJiXiong}</td></tr>`;
        }
        if (d.tiYong.tiHuRel) {
            html += `<tr><td>互卦与体</td><td>体${d.tiYong.tiWuxing} ${d.tiYong.tiHuRel} 互${d.tiYong.huWuxing || ''}</td><td>-</td></tr>`;
        }
        if (d.tiYong.tiBianRel) {
            html += `<tr><td>变卦与体</td><td>体${d.tiYong.tiWuxing} ${d.tiYong.tiBianRel} 变${d.tiYong.bianWuxing || ''}</td><td>-</td></tr>`;
        }
        html += '</table>';

        // 断语
        if (d.tiYong.verdict) {
            html += `<div class="mh-verdict">${d.tiYong.verdict}</div>`;
        }

        html += '</div>';
    }

    // ═══ 免责声明 ═══
    html += '<div class="privacy-note" style="margin-top:16px;">⚠️ 以上内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</div>';

    html += '</div>';
    return html;
}

// ── 渲染单个卦象卡片 ──
function renderGuaCard(label, gua, cardClass, dongYao, yaoList) {
    if (!gua) return '';
    const upper = gua.upper || {};
    const lower = gua.lower || {};

    let html = `<div class="gua-card ${cardClass}">`;
    html += `<div class="gua-card-label">${label}</div>`;
    html += `<div class="gua-card-name">${gua.name || ''}</div>`;

    // 六爻图
    if (yaoList && yaoList.length === 6) {
        html += '<div class="gua-yao-wrap">';
        for (let i = 5; i >= 0; i--) {
            const isYang = yaoList[i] === 1;
            const isDong = (i + 1) === dongYao;
            html += `<div class="gua-yao ${isYang ? 'yang' : 'yin'} ${isDong ? 'dong-yao' : ''}">`;
            if (isYang) {
                html += '<div class="gua-yao-line"></div>';
            } else {
                html += '<div class="gua-yao-line"></div><div class="gua-yao-line"></div>';
            }
            html += '</div>';
        }
        html += '</div>';
    } else {
        // 显示上下卦符号
        html += `<div class="gua-trigram">${upper.trigram || ''}${lower.trigram || ''}</div>`;
    }

    // 上下卦信息
    html += '<div class="gua-sub-info">';
    html += `<span>上卦 ${upper.name || ''}·${upper.nature || ''}·${upper.wuxing || ''}</span>`;
    html += `<span>下卦 ${lower.name || ''}·${lower.nature || ''}·${lower.wuxing || ''}</span>`;
    html += '</div>';

    html += '</div>';
    return html;
}

// ── 五行CSS类 ──
function wxClass(wx) {
    const map = { '金': 'jin', '木': 'mu', '水': 'shui', '火': 'huo', '土': 'tu' };
    return map[wx] || '';
}

// ── 旺衰CSS类 ──
function wsClass(ws) {
    const map = { '旺': 'wang', '相': 'xiang', '休': 'xiu', '囚': 'qiu', '死': 'si' };
    return map[ws] || 'xiu';
}

// ── 关系吉凶CSS类 ──
function relClass(rel) {
    if (rel === '被生' || rel === '比和') return 'ji';
    if (rel === '被克') return 'xiong';
    return 'zhong';
}

// ═══ 一键起卦 + DeepSeek AI解盘（仿奇门/六爻） ═══
let _meihuaAskTimer = null;
let _meihuaAskEventSource = null;
let _meihuaAskReasoning = null;

async function meihuaAskPaipan() {
    if (_meihuaAskTimer) { clearInterval(_meihuaAskTimer); _meihuaAskTimer = null; }
    if (_meihuaAskEventSource) { _meihuaAskEventSource.close(); _meihuaAskEventSource = null; }

    const questionEl = document.getElementById('mai-question');
    const question = questionEl ? questionEl.value.trim() : '';
    if (!question) { alert('请输入您的问题'); questionEl && questionEl.focus(); return; }

    const deepEl = document.getElementById('maiDeepMode');
    const deepAnalysis = deepEl ? deepEl.checked : false;

    // 获取起卦方式
    const activeMethodBtn = document.querySelector('#tab-meihua-ai .method-switch-btn.active');
    const method = activeMethodBtn ? activeMethodBtn.getAttribute('data-method') : 'time';

    const data = { method, question, deep_analysis: deepAnalysis };

    if (method === 'time') {
        const yearEl = document.getElementById('maiYear');
        const monthEl = document.getElementById('maiMonth');
        const dayEl = document.getElementById('maiDay');
        const hourEl = document.getElementById('maiHour');
        const minEl = document.getElementById('maiMinute');
        if (yearEl && yearEl.value && monthEl && monthEl.value && dayEl && dayEl.value) {
            const y = yearEl.value, m = monthEl.value, d = dayEl.value;
            const h = hourEl && hourEl.value ? hourEl.value : '12';
            const mi = minEl && minEl.value ? minEl.value : '0';
            data.time = y + '-' + m + '-' + d + 'T' + h + ':' + mi;
        }
    } else if (method === 'number') {
        const num1 = document.getElementById('mai-num1');
        const num2 = document.getElementById('mai-num2');
        if (!num1 || !num1.value) { alert('请输入第一个数字'); return; }
        data.num1 = parseInt(num1.value);
        data.num2 = num2 && num2.value ? parseInt(num2.value) : 0;
    } else if (method === 'word') {
        const words = document.getElementById('mai-words');
        if (!words || !words.value.trim()) { alert('请输入文字'); return; }
        data.words = words.value.trim();
    }

    // 显示进度条
    const progressEl = document.getElementById('maiProgress');
    const resultEl = document.getElementById('maiResult');
    if (progressEl) progressEl.style.display = 'block';
    if (resultEl) { resultEl.style.display = 'none'; resultEl.innerHTML = ''; }

    meihuaUpdateProgress(5, '起卦中...');

    const btn = document.getElementById('maiAskBtn');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ 处理中...'; }

    try {
        const resp = await apiFetch('/api/meihua/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || '请求失败');
        }
        const respData = await resp.json();
        if (respData.run_id) {
            meihuaUpdateProgress(15, '起卦完成，开始解卦...');
            _meihuaAskTimer = setInterval(() => meihuaPollStatus(respData.run_id), 1000);
            meihuaPollStatus(respData.run_id);
        } else {
            throw new Error('未获取到 run_id');
        }
    } catch (e) {
        meihuaUpdateProgress(0, '');
        if (progressEl) progressEl.style.display = 'none';
        if (resultEl) {
            resultEl.style.display = 'block';
            resultEl.innerHTML = `<div class="qai-error">❌ ${esc(e.message)}</div>`;
        }
        if (btn) { btn.disabled = false; btn.textContent = '🔮 一键起卦 · 深度解读'; }
    }
}

function meihuaPollStatus(runId) {
    fetch(`/api/qimen/ask/status?run_id=${runId}&_t=${Date.now()}`)
        .then(r => r.json())
        .then(d => {
            meihuaUpdateProgress(d.progress || 0, d.message || '');
            if (d.phase === 'streaming') {
                if (!_meihuaAskEventSource) meihuaStartSSE(runId);
                if (d.reasoning) _meihuaAskReasoning = d.reasoning;
            } else if (d.phase === 'done') {
                if (_meihuaAskTimer) { clearInterval(_meihuaAskTimer); _meihuaAskTimer = null; }
                if (d.reasoning) _meihuaAskReasoning = d.reasoning;
                if (!_meihuaAskEventSource) {
                    meihuaShowResult(d.result || '', d.reasoning || null);
                } else if (_meihuaAskReasoning) {
                    const rEl = document.getElementById('maiResult');
                    if (rEl && !rEl.querySelector('.qai-reasoning')) {
                        rEl.innerHTML = '<details class="qai-reasoning" open><summary class="qai-reasoning-summary">🧠 思考过程（点击折叠）</summary><div class="qai-reasoning-body">' + qimenRenderMarkdown(_meihuaAskReasoning) + '</div></details>' + rEl.innerHTML;
                    }
                }
                meihuaUpdateProgress(100, '解卦完成！');
                const btn = document.getElementById('maiAskBtn');
                if (btn) { btn.disabled = false; btn.textContent = '🔮 一键起卦 · 深度解读'; }
            } else if (d.phase === 'error') {
                if (_meihuaAskTimer) { clearInterval(_meihuaAskTimer); _meihuaAskTimer = null; }
                if (_meihuaAskEventSource) { _meihuaAskEventSource.close(); _meihuaAskEventSource = null; }
                const rEl = document.getElementById('maiResult');
                if (rEl) { rEl.style.display = 'block'; rEl.innerHTML = `<div class="qai-error">❌ ${esc(d.message)}</div>`; }
                const pEl = document.getElementById('maiProgress');
                if (pEl) pEl.style.display = 'none';
                const btn = document.getElementById('maiAskBtn');
                if (btn) { btn.disabled = false; btn.textContent = '🔮 一键起卦 · 深度解读'; }
            }
        })
        .catch(err => console.warn('轮询出错:', err));
}

function meihuaStartSSE(runId) {
    _meihuaAskEventSource = new EventSource(`/api/qimen/ask/stream?run_id=${runId}`);
    const resultEl = document.getElementById('maiResult');
    if (resultEl) { resultEl.style.display = 'block'; resultEl.innerHTML = ''; }
    _meihuaAskEventSource.onmessage = function(e) {
        try {
            const d = JSON.parse(e.data);
            if (d.type === 'delta') {
                meihuaAppendResult(d.content);
            } else if (d.type === 'done') {
                _meihuaAskEventSource.close(); _meihuaAskEventSource = null;
                const rEl = document.getElementById('maiResult');
                if (_meihuaAskReasoning && rEl && !rEl.querySelector('.qai-reasoning')) {
                    rEl.innerHTML = '<details class="qai-reasoning" open><summary class="qai-reasoning-summary">🧠 思考过程（点击折叠）</summary><div class="qai-reasoning-body">' + qimenRenderMarkdown(_meihuaAskReasoning) + '</div></details>' + rEl.innerHTML;
                }
                meihuaUpdateProgress(100, '解卦完成！');
                const btn = document.getElementById('maiAskBtn');
                if (btn) { btn.disabled = false; btn.textContent = '🔮 一键起卦 · 深度解读'; }
            } else if (d.type === 'error') {
                _meihuaAskEventSource.close(); _meihuaAskEventSource = null;
                if (resultEl) resultEl.innerHTML += `<div class="qai-error">❌ ${esc(d.message)}</div>`;
                const btn = document.getElementById('maiAskBtn');
                if (btn) { btn.disabled = false; btn.textContent = '🔮 一键起卦 · 深度解读'; }
            }
        } catch(e) {}
    };
    _meihuaAskEventSource.onerror = function() {};
}

function meihuaUpdateProgress(progress, message) {
    const fillEl = document.getElementById('maiProgressFill');
    const textEl = document.getElementById('maiStepText');
    if (fillEl) fillEl.style.width = Math.min(progress, 100) + '%';
    if (textEl && message) textEl.textContent = message;
}

function meihuaShowResult(markdownText, reasoningText) {
    const resultEl = document.getElementById('maiResult');
    if (!resultEl) return;
    resultEl.style.display = 'block';
    let html = '';
    if (reasoningText) {
        html += `<details class="qai-reasoning" open><summary class="qai-reasoning-summary">🧠 思考过程（点击折叠）</summary><div class="qai-reasoning-body">${qimenRenderMarkdown(reasoningText)}</div></details>`;
    }
    html += qimenRenderMarkdown(markdownText);
    resultEl.innerHTML = html;
}

function meihuaAppendResult(text) {
    const resultEl = document.getElementById('maiResult');
    if (!resultEl) return;
    resultEl.style.display = 'block';
    if (!resultEl.dataset.streaming) { resultEl.innerHTML = ''; resultEl.dataset.streaming = '1'; }
    const lastNode = resultEl.lastChild;
    if (lastNode && lastNode.nodeType === Node.TEXT_NODE) {
        lastNode.textContent += text;
    } else {
        resultEl.appendChild(document.createTextNode(text));
    }
    resultEl.scrollTop = resultEl.scrollHeight;
}
