// ═══ 六爻纳甲专用脚本 ═══
// esc, sanitizeData, apiFetch 由 api-client.js 提供

let lyCurrentMode = 'auto';
let lyManualTosses = Array.from({length:6}, () => [null,null,null]);
let lyManualTossesAI = Array.from({length:6}, () => [null,null,null]);

// ── 起卦方式切换（免费排盘tab） ──
function switchLyMethod(btn, method) {
    btn.parentElement.querySelectorAll('.method-switch-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('#tab-liuyao-free .ly-method-content').forEach(c => c.style.display = 'none');
    const el = document.getElementById('ly-method-' + method);
    if (el) el.style.display = 'block';
    lyCurrentMode = method;
    if (method === 'manual') buildLyTossRows('lyTossRows', lyManualTosses);
}

// ── 起卦方式切换（AI系统tab） ──
function switchLyMethodAI(btn, method) {
    btn.parentElement.querySelectorAll('.method-switch-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('#tab-liuyao-ai .mh-method-content').forEach(c => c.style.display = 'none');
    const el = document.getElementById('lai-method-' + method);
    if (el) el.style.display = 'block';
    if (method === 'manual') buildLyTossRows('lyTossRowsAI', lyManualTossesAI);
}

// ── 生成手动输入行 ──
function buildLyTossRows(containerId, tossArr) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const labels = ['第一次', '第二次', '第三次', '第四次', '第五次', '第六次'];
    container.innerHTML = labels.map((label, i) => `
        <div class="ly-toss-row">
            <div class="ly-toss-label">${label}</div>
            <div class="ly-toss-coins">
                ${[0,1,2].map(j => `
                    <button class="ly-coin-btn" data-toss="${i}" data-coin="${j}" data-container="${containerId}" onclick="selectLyCoin('${containerId}',${i},${j},'front')">字(2)</button>
                    <button class="ly-coin-btn" data-toss="${i}" data-coin="${j}" data-container="${containerId}" onclick="selectLyCoin('${containerId}',${i},${j},'back')">花(3)</button>
                `).join('')}
            </div>
            <div class="ly-toss-result" id="${containerId}-result${i}">—</div>
        </div>
    `).join('');
}

// ── 选择铜钱正反面 ──
function selectLyCoin(containerId, tossIdx, coinIdx, side) {
    const tossArr = containerId === 'lyTossRows' ? lyManualTosses : lyManualTossesAI;
    tossArr[tossIdx][coinIdx] = side === 'front' ? 2 : 3;

    // 更新按钮样式
    document.querySelectorAll(`[data-container="${containerId}"][data-toss="${tossIdx}"][data-coin="${coinIdx}"]`).forEach(btn => {
        btn.classList.remove('sel-front', 'sel-back');
    });
    const cls = side === 'front' ? 'sel-front' : 'sel-back';
    const btns = document.querySelectorAll(`[data-container="${containerId}"][data-toss="${tossIdx}"][data-coin="${coinIdx}"]`);
    btns.forEach(btn => {
        if (btn.textContent.includes(side === 'front' ? '字' : '花')) {
            btn.classList.add(cls);
        }
    });

    // 更新结果显示
    const toss = tossArr[tossIdx];
    if (toss.every(v => v !== null)) {
        const sum = toss.reduce((a, b) => a + b, 0);
        const el = document.getElementById(`${containerId}-result${tossIdx}`);
        if (sum === 9) { el.textContent = '老阳'; el.className = 'ly-toss-result moving'; }
        else if (sum === 7) { el.textContent = '少阳'; el.className = 'ly-toss-result yang'; }
        else if (sum === 8) { el.textContent = '少阴'; el.className = 'ly-toss-result yin'; }
        else if (sum === 6) { el.textContent = '老阴'; el.className = 'ly-toss-result moving'; }
    }
}

// ── 铜钱动画 ──
async function showLyCoinAnimation() {
    return new Promise(resolve => {
        const overlay = document.getElementById('lyCoinOverlay');
        const spinner = document.getElementById('lyCoinSpinner');
        const progress = document.getElementById('lyCoinProgress');
        overlay.classList.add('active');

        let count = 0;
        const interval = setInterval(() => {
            count++;
            spinner.classList.remove('spinning');
            void spinner.offsetWidth;
            spinner.classList.add('spinning');
            progress.textContent = `第 ${count}/6 次摇卦...`;

            if (count >= 6) {
                clearInterval(interval);
                setTimeout(() => {
                    overlay.classList.remove('active');
                    resolve();
                }, 700);
            }
        }, 500);
    });
}

// ── 六爻免费排盘 ──
async function liuyaoFreePaipan() {
    const btn = document.getElementById('lyFreeBtn');
    if (btn.disabled) return;

    const data = { mode: lyCurrentMode };

    if (lyCurrentMode === 'manual') {
        for (let i = 0; i < 6; i++) {
            if (lyManualTosses[i].some(v => v === null)) {
                alert(`请完成第 ${i + 1} 次摇卦的选择`);
                return;
            }
        }
        data.tosses = lyManualTosses.map(t => [...t]);
    }

    // 问事（选填）
    const questionEl = document.getElementById('lf-question');
    if (questionEl && questionEl.value.trim()) {
        data.question = questionEl.value.trim();
    }

    // 铜钱动画
    btn.disabled = true;
    btn.textContent = '摇卦中...';
    await showLyCoinAnimation();

    const resultEl = document.getElementById('lyResult');
    if (!resultEl) { btn.disabled = false; btn.textContent = '🧭 免费排盘'; return; }
    resultEl.style.display = 'block';
    resultEl.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-3);">🧭 排盘计算中...</div>';

    try {
        const resp = await apiFetch('/api/liuyao/paipan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await resp.json();
        if (result.error) {
            resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">${esc(result.error)}</div>`;
            return;
        }
        resultEl.innerHTML = renderLiuyaoResult(sanitizeData(result));
    } catch (e) {
        resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">排盘失败: ${e.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '🧭 免费排盘';
    }
}

// ── 渲染六爻排盘结果 ──
function renderLiuyaoResult(d) {
    const isManual = d.method && d.method.includes('手动');
    let html = '<div class="ly-result-wrap">';

    // ═══ 卦象头部 ═══
    const hasMoving = d.details && d.details.some(x => x.is_moving);
    const movingCount = d.details ? d.details.filter(x => x.is_moving).length : 0;

    html += '<div class="ly-gua-header">';
    html += '<div class="ly-gua-names">';
    // 本卦
    html += `<div class="ly-gua-name-block">
        <div class="ly-gua-name-label">本 卦</div>
        <div class="ly-gua-name-text">${d['本卦'] || ''}</div>
        <div class="ly-gua-trigrams">
            <span class="ly-trigram-badge">${d.upper_nature || ''} ${d.upper_trigram || ''}</span>
            <span class="ly-trigram-badge">${d.lower_nature || ''} ${d.lower_trigram || ''}</span>
        </div>
    </div>`;

    if (hasMoving) {
        html += '<div class="ly-gua-arrow">→</div>';
        html += `<div class="ly-gua-name-block">
            <div class="ly-gua-name-label">变 卦</div>
            <div class="ly-gua-name-text">${d['变卦'] || ''}</div>
            <div class="ly-gua-trigrams">
                <span class="ly-trigram-badge">${d.bian_upper_nature || ''} ${d.bian_upper_trigram || ''}</span>
                <span class="ly-trigram-badge">${d.bian_lower_nature || ''} ${d.bian_lower_trigram || ''}</span>
            </div>
        </div>`;
    }

    html += '</div>'; // .ly-gua-names

    // 元信息
    html += '<div class="ly-gua-meta">';
    html += `<span><span class="ly-meta-label">宫：</span><span class="ly-meta-value">${d.palace_name || ''}宫（${d.palace_element || ''}）</span></span>`;
    html += `<span><span class="ly-meta-label">日辰：</span><span class="ly-meta-value">${d.day_ganzhi || ''}</span></span>`;
    html += `<span><span class="ly-meta-label">月建：</span><span class="ly-meta-value">${d.month_ganzhi || ''}</span></span>`;
    if (hasMoving) {
        html += `<span><span class="ly-meta-label">动爻：</span><span class="ly-meta-value" style="color:var(--danger)">${movingCount}个</span></span>`;
    } else {
        html += `<span><span class="ly-meta-value">静卦（无动爻）</span></span>`;
    }
    html += '</div>';
    html += '</div>'; // .ly-gua-header

    // ═══ 卦象可视化 ═══
    // 手动输入模式：本卦居中/右侧，更突出用户手动输入的卦象
    const guaDisplayClass = isManual ? 'ly-gua-display ly-manual-layout' : 'ly-gua-display';
    html += `<div class="${guaDisplayClass}">`;

    // 构建本卦HTML
    const benGuaHtml = (() => {
        let s = '<div class="ly-gua-block ly-ben-gua-block">';
        s += `<div class="ly-gua-block-title">本卦 · ${d['本卦'] || ''}</div>`;
        s += '<div class="ly-gua-lines">';
        if (d.details) {
            for (let i = d.details.length - 1; i >= 0; i--) {
                s += renderLyYaoLine(d.details[i]);
            }
        }
        s += '</div></div>';
        return s;
    })();

    // 构建变卦HTML
    const bianGuaHtml = hasMoving ? (() => {
        let s = '<div class="ly-gua-block ly-bian-gua-block">';
        s += `<div class="ly-gua-block-title">变卦 · ${d['变卦'] || ''}</div>`;
        s += '<div class="ly-gua-lines">';
        if (d.bian_details) {
            for (let i = d.bian_details.length - 1; i >= 0; i--) {
                s += renderLyYaoLine(d.bian_details[i]);
            }
        }
        s += '</div></div>';
        return s;
    })() : '';

    // 箭头
    const arrowHtml = hasMoving
        ? '<div class="ly-change-arrow"><div class="ly-arrow-sym">⟶</div><div class="ly-arrow-text">变</div></div>'
        : '';

    // 根据模式决定渲染顺序
    if (isManual && hasMoving) {
        // 手动 + 有动爻：变卦(左) → 本卦(右)，本卦更突出
        html += bianGuaHtml + arrowHtml + benGuaHtml;
    } else {
        // 自动模式 或 手动静卦：本卦(左/居中)
        html += benGuaHtml;
        if (hasMoving) {
            html += arrowHtml + bianGuaHtml;
        }
    }

    html += '</div>'; // .ly-gua-display

    // ═══ 明细表格 ═══
    html += '<div style="overflow-x:auto;">';
    html += '<table class="ly-detail-table">';
    html += '<tr><th>爻位</th><th>阴阳</th><th>六亲</th><th>六神</th><th>纳甲</th><th>地支五行</th><th>世应</th><th>动</th></tr>';
    if (d.details) {
        for (let i = d.details.length - 1; i >= 0; i--) {
            const x = d.details[i];
            html += `<tr class="${x.is_moving ? 'moving-row' : ''}">
                <td>${x.name}</td>
                <td>${x.is_yang ? '⚊ 阳' : '⚋ 阴'}</td>
                <td>${x.liuqin}</td>
                <td>${x.liushen}</td>
                <td>${x.naja}</td>
                <td>${x.dizhi_element}</td>
                <td>${x.is_shi ? '世' : x.is_ying ? '应' : ''}</td>
                <td>${x.is_moving ? '⚡ 动' : ''}</td>
            </tr>`;
        }
    }
    html += '</table></div>';

    // ═══ 排盘信息 ═══
    html += '<div class="ly-paipan-meta">';
    html += `<span>🕐 ${new Date().toLocaleString('zh-CN')}</span>`;
    html += `<span>📖 ${d.method || '自动摇卦'}</span>`;
    if (d.question) html += `<span>❓ ${d.question}</span>`;
    html += '</div>';

    // ═══ 免责声明 ═══
    html += '<div class="privacy-note" style="margin-top:16px;">⚠️ 以上内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</div>';

    html += '</div>'; // .ly-result-wrap
    return html;
}

// ── 渲染单行爻线 ──
function renderLyYaoLine(detail) {
    const lineGraphic = detail.is_yang
        ? '<div class="ly-yang-bar"></div>'
        : '<div class="ly-yin-bars"><div class="ly-yin-seg"></div><div class="ly-yin-seg"></div></div>';

    const tags = [];
    tags.push(`<span class="ly-tag ly-tag-liuqin">${detail.liuqin}</span>`);
    tags.push(`<span class="ly-tag ly-tag-liushen">${detail.liushen}</span>`);
    tags.push(`<span class="ly-tag ly-tag-naja">${detail.naja}</span>`);
    if (detail.is_shi) tags.push(`<span class="ly-tag ly-tag-shi">世</span>`);
    if (detail.is_ying) tags.push(`<span class="ly-tag ly-tag-ying">应</span>`);
    if (detail.is_moving) tags.push(`<span class="ly-tag ly-tag-moving">动</span>`);

    return `<div class="ly-yao-line ${detail.is_moving ? 'moving' : ''}">
        <div class="ly-yao-pos">${detail.name}</div>
        <div class="ly-yao-graphic">${lineGraphic}</div>
        <div class="ly-yao-info">${tags.join('')}</div>
    </div>`;
}

// ═══ 一键起卦 + DeepSeek AI解盘 ═══
let _liuyaoAskTimer = null;
let _liuyaoAskEventSource = null;
let _liuyaoAskReasoning = null;

async function liuyaoAskPaipan() {
    // 清除之前的轮询
    if (_liuyaoAskTimer) { clearInterval(_liuyaoAskTimer); _liuyaoAskTimer = null; }
    if (_liuyaoAskEventSource) { _liuyaoAskEventSource.close(); _liuyaoAskEventSource = null; }

    const questionEl = document.getElementById('lai-question');
    const question = questionEl ? questionEl.value.trim() : '';
    if (!question) {
        alert('请输入您的问题');
        questionEl && questionEl.focus();
        return;
    }

    const deepEl = document.getElementById('laiDeepMode');
    const deepAnalysis = deepEl ? deepEl.checked : false;

    // 获取摇卦方式
    const activeMethodBtn = document.querySelector('#tab-liuyao-ai .method-switch-btn.active');
    const mode = activeMethodBtn ? activeMethodBtn.getAttribute('data-method') : 'auto';

    // 手动模式检查
    let tosses = null;
    if (mode === 'manual') {
        for (let i = 0; i < 6; i++) {
            if (lyManualTossesAI[i].some(v => v === null)) {
                alert(`请完成第 ${i + 1} 次摇卦的选择`);
                return;
            }
        }
        tosses = lyManualTossesAI.map(t => [...t]);
    }

    // 显示进度条
    const progressEl = document.getElementById('laiProgress');
    const resultEl = document.getElementById('laiResult');
    if (progressEl) progressEl.style.display = 'block';
    if (resultEl) { resultEl.style.display = 'none'; resultEl.innerHTML = ''; }

    liuyaoUpdateProgress(5, '起卦中...');

    // 禁用按钮
    const btn = document.getElementById('laiAskBtn');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ 处理中...'; }

    // 铜钱动画（自动模式）
    if (mode === 'auto') {
        await showLyCoinAnimation();
        liuyaoUpdateProgress(10, '起卦完成，开始分析...');
    }

    // 发送请求
    try {
        const resp = await apiFetch('/api/liuyao/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, mode, tosses, deep_analysis: deepAnalysis })
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || '请求失败');
        }
        const data = await resp.json();
        if (data.run_id) {
            liuyaoUpdateProgress(15, '起卦完成，开始解卦...');
            _liuyaoAskTimer = setInterval(() => liuyaoPollStatus(data.run_id), 1000);
            liuyaoPollStatus(data.run_id);
        } else {
            throw new Error('未获取到 run_id');
        }
    } catch (e) {
        liuyaoUpdateProgress(0, '');
        if (progressEl) progressEl.style.display = 'none';
        if (resultEl) {
            resultEl.style.display = 'block';
            resultEl.innerHTML = `<div class="qai-error">❌ ${esc(e.message)}</div>`;
        }
        if (btn) { btn.disabled = false; btn.textContent = '🔮 一键起卦 · AI深度解读'; }
    }
}

function liuyaoPollStatus(runId) {
    fetch(`/api/qimen/ask/status?run_id=${runId}&_t=${Date.now()}`)
        .then(r => r.json())
        .then(data => {
            const phase = data.phase || 'idle';
            const progress = data.progress || 0;
            const message = data.message || '';

            liuyaoUpdateProgress(progress, message);

            if (phase === 'streaming') {
                if (!_liuyaoAskEventSource) {
                    liuyaoStartSSE(runId);
                }
                if (data.reasoning) _liuyaoAskReasoning = data.reasoning;
            } else if (phase === 'done') {
                if (_liuyaoAskTimer) { clearInterval(_liuyaoAskTimer); _liuyaoAskTimer = null; }
                if (data.reasoning) _liuyaoAskReasoning = data.reasoning;
                if (!_liuyaoAskEventSource) {
                    liuyaoShowResult(data.result || '', data.reasoning || null);
                } else {
                    if (_liuyaoAskReasoning) {
                        const rEl = document.getElementById('laiResult');
                        if (rEl && !rEl.querySelector('.qai-reasoning')) {
                            rEl.innerHTML = '<details class="qai-reasoning" open><summary class="qai-reasoning-summary">🧠 思考过程（点击折叠）</summary><div class="qai-reasoning-body">' + qimenRenderMarkdown(_liuyaoAskReasoning) + '</div></details>' + rEl.innerHTML;
                        }
                    }
                }
                liuyaoUpdateProgress(100, '解卦完成！');
                const btn = document.getElementById('laiAskBtn');
                if (btn) { btn.disabled = false; btn.textContent = '🔮 一键起卦 · AI深度解读'; }
            } else if (phase === 'error') {
                if (_liuyaoAskTimer) { clearInterval(_liuyaoAskTimer); _liuyaoAskTimer = null; }
                if (_liuyaoAskEventSource) { _liuyaoAskEventSource.close(); _liuyaoAskEventSource = null; }
                const rEl = document.getElementById('laiResult');
                if (rEl) {
                    rEl.style.display = 'block';
                    rEl.innerHTML = `<div class="qai-error">❌ ${esc(message)}</div>`;
                }
                const pEl = document.getElementById('laiProgress');
                if (pEl) pEl.style.display = 'none';
                const btn = document.getElementById('laiAskBtn');
                if (btn) { btn.disabled = false; btn.textContent = '🔮 一键起卦 · AI深度解读'; }
            }
        })
        .catch(err => console.warn('轮询出错:', err));
}

function liuyaoStartSSE(runId) {
    _liuyaoAskEventSource = new EventSource(`/api/qimen/ask/stream?run_id=${runId}`);
    const resultEl = document.getElementById('laiResult');
    if (resultEl) { resultEl.style.display = 'block'; resultEl.innerHTML = ''; }

    _liuyaoAskEventSource.onmessage = function(e) {
        try {
            const d = JSON.parse(e.data);
            if (d.type === 'delta') {
                liuyaoAppendResult(d.content);
            } else if (d.type === 'done') {
                _liuyaoAskEventSource.close();
                _liuyaoAskEventSource = null;
                const rEl = document.getElementById('laiResult');
                if (_liuyaoAskReasoning && rEl && !rEl.querySelector('.qai-reasoning')) {
                    rEl.innerHTML = '<details class="qai-reasoning" open><summary class="qai-reasoning-summary">🧠 思考过程（点击折叠）</summary><div class="qai-reasoning-body">' + qimenRenderMarkdown(_liuyaoAskReasoning) + '</div></details>' + rEl.innerHTML;
                }
                liuyaoUpdateProgress(100, '解卦完成！');
                const btn = document.getElementById('laiAskBtn');
                if (btn) { btn.disabled = false; btn.textContent = '🔮 一键起卦 · AI深度解读'; }
            } else if (d.type === 'error') {
                _liuyaoAskEventSource.close();
                _liuyaoAskEventSource = null;
                if (resultEl) {
                    resultEl.innerHTML += `<div class="qai-error">❌ ${esc(d.message)}</div>`;
                }
                const btn = document.getElementById('laiAskBtn');
                if (btn) { btn.disabled = false; btn.textContent = '🔮 一键起卦 · AI深度解读'; }
            }
        } catch(e) {}
    };
    _liuyaoAskEventSource.onerror = function() {};
}

function liuyaoUpdateProgress(progress, message) {
    const fillEl = document.getElementById('laiProgressFill');
    const textEl = document.getElementById('laiStepText');
    if (fillEl) fillEl.style.width = Math.min(progress, 100) + '%';
    if (textEl && message) textEl.textContent = message;
}

function liuyaoShowResult(markdownText, reasoningText) {
    const resultEl = document.getElementById('laiResult');
    if (!resultEl) return;
    resultEl.style.display = 'block';
    let html = '';
    if (reasoningText) {
        html += `<details class="qai-reasoning" open><summary class="qai-reasoning-summary">🧠 思考过程（点击折叠）</summary><div class="qai-reasoning-body">${qimenRenderMarkdown(reasoningText)}</div></details>`;
    }
    html += qimenRenderMarkdown(markdownText);
    resultEl.innerHTML = html;
}

function liuyaoAppendResult(text) {
    const resultEl = document.getElementById('laiResult');
    if (!resultEl) return;
    resultEl.style.display = 'block';
    if (!resultEl.dataset.streaming) {
        resultEl.innerHTML = '';
        resultEl.dataset.streaming = '1';
    }
    const lastNode = resultEl.lastChild;
    if (lastNode && lastNode.nodeType === Node.TEXT_NODE) {
        lastNode.textContent += text;
    } else {
        resultEl.appendChild(document.createTextNode(text));
    }
    resultEl.scrollTop = resultEl.scrollHeight;
}
