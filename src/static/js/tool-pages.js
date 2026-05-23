// ═══ 工具页面专用脚本 ═══

// ── 工具页 Tab 切换 ──
function switchToolTab(btn) {
    btn.parentElement.querySelectorAll('.tool-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tool-tab-content').forEach(c => c.style.display = 'none');
    const tab = btn.getAttribute('data-tab');
    const el = document.getElementById('tab-' + tab);
    if (el) el.style.display = 'block';
}

// ── 根据URL hash切换tab ──
(function() {
    const hash = window.location.hash.replace('#', '');
    if (hash === 'free') {
        setTimeout(() => {
            const freeTab = document.querySelector('.tool-tab[data-tab$="-free"]');
            if (freeTab) switchToolTab(freeTab);
        }, 100);
    } else if (hash === 'ai') {
        setTimeout(() => {
            const aiTab = document.querySelector('.tool-tab[data-tab$="-ai"]');
            if (aiTab) switchToolTab(aiTab);
        }, 100);
    } else if (hash === 'records') {
        setTimeout(() => {
            const recTab = document.querySelector('.tool-tab[data-tab$="-records"]');
            if (recTab) { switchToolTab(recTab); loadRecords(); }
        }, 100);
    }
})();

// ── 高级选项 ──
function toggleAdvanced(id) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('show');
}

// ── 结果模式切换 ──
function switchResult(btn, mode) {
    btn.parentElement.querySelectorAll('.result-mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    sessionStorage.setItem('xc_result_mode', mode);
}

// ── 设置默认时间 ──
(function() {
    const now = new Date();
    const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    const qaiTime = document.getElementById('qai-time');
    if (qaiTime) qaiTime.value = local;
    const qfTime = document.getElementById('qf-time');
    if (qfTime) qfTime.value = local;
    const baiDate = document.getElementById('bai-date');
    if (baiDate) baiDate.value = local.slice(0, 10);
})();

// ── 初始化日期选择器（八字免费版 + 奇门免费版 + 奇门AI版） ──
document.addEventListener('DOMContentLoaded', function() {
    if (typeof wzInitDatePicker === 'function') {
        wzInitDatePicker();
    }
    if (typeof qfInitDatePicker === 'function') {
        qfInitDatePicker();
    }
    if (typeof qaiInitDatePicker === 'function') {
        qaiInitDatePicker();
    }
    if (typeof mfInitDatePicker === 'function') {
        mfInitDatePicker();
    }
    // 监听排盘记录tab切换
    document.querySelectorAll('.tool-tab[data-tab$="-records"]').forEach(tab => {
        tab.addEventListener('click', function() { loadRecords(); });
    });
});

// ═══ 排盘记录（问真风格） ═══

// ── 状态管理 ──
const _recordState = {
    tab: 'paipan',         // 当前Tab: paipan/hepan
    category: '全部',       // 当前分类
    search: '',            // 搜索关键词
    batchMode: false,      // 批量选择模式
    selectedIds: new Set(),// 批量选中的记录ID
    allRecords: [],        // 所有记录缓存
    openDropdown: null,    // 当前打开的下拉菜单
};

// 生肖映射
const SX_EMOJI = ['🐒','🐔','🐕','🐖','🐀','🐄','🐅','🐇','🐉','🐍','🐴','🐑'];
function getShengxiaoEmoji(year) {
    if (!year || isNaN(year)) return '🐵';
    return SX_EMOJI[((year - 4) % 12 + 12) % 12];
}

// 从出生时间提取年份
function extractYear(birthTime) {
    if (!birthTime) return null;
    const m = birthTime.match(/(\d{4})/);
    return m ? parseInt(m[1]) : null;
}

// 格式化出生日期显示
function formatBirthDate(rec) {
    const bt = rec.birth_time || '';
    if (!bt || bt.length < 8) return '';
    const y = bt.slice(0,4), m = bt.slice(4,6), d = bt.slice(6,8);
    const calLabel = (rec.cal_type === '农历') ? '农历' : '阳历';
    return `${calLabel}：${y}年${m}月${d}日`;
}

// 解析四柱天干地支
function parsePillars(pillars) {
    if (!pillars || pillars.length < 8) return null;
    return {
        gan: [pillars[0], pillars[2], pillars[4], pillars[6]],
        zhi: [pillars[1], pillars[3], pillars[5], pillars[7]]
    };
}

// ── 加载记录 ──
function loadRecords() {
    apiFetch('/api/bazi/history')
        .then(r => {
            if (r.status === 401) {
                // 未登录，显示登录提示
                _recordState.allRecords = [];
                filterAndRender();
                const emptyEl = document.getElementById('recordsEmpty');
                if (emptyEl) {
                    emptyEl.style.display = '';
                    emptyEl.innerHTML = `
                        <div class="empty-icon">🔒</div>
                        <div class="empty-text">请先登录查看记录</div>
                        <div class="empty-hint">登录后排盘记录将自动保存到您的账号</div>
                        <button class="btn btn-accent btn-sm" onclick="document.querySelector('.login-btn')?.click?.(); if(typeof openLoginModal==='function')openLoginModal();">去登录</button>
                    `;
                }
                return null;
            }
            return r.json();
        })
        .then(data => {
            if (!data) return;
            if (!data.success) return;
            _recordState.allRecords = data.history || [];
            filterAndRender();
        })
        .catch(() => {
            // 降级：从localStorage读取
            _recordState.allRecords = JSON.parse(localStorage.getItem('bazi_records') || '[]');
            filterAndRender();
        });
}

// ── 过滤并渲染 ──
function filterAndRender() {
    let records = _recordState.allRecords;

    // 1. Tab过滤
    const tab = _recordState.tab;
    records = records.filter(r => {
        const type = r.type || 'paipan';
        return type === tab;
    });

    // 2. 分类过滤
    if (_recordState.category !== '全部') {
        records = records.filter(r => (r.category || '全部') === _recordState.category);
    }

    // 3. 搜索过滤
    const kw = _recordState.search.toLowerCase().trim();
    if (kw) {
        records = records.filter(r => {
            const name = (r.name || '').toLowerCase();
            const pillars = (r.pillars || '').toLowerCase();
            const bt = (r.birth_time || '').toLowerCase();
            return name.includes(kw) || pillars.includes(kw) || bt.includes(kw);
        });
    }

    // 4. 分离星标和普通
    const starred = records.filter(r => r.starred);
    const normal = records.filter(r => !r.starred);

    // 5. 渲染
    renderStarSection(starred);
    renderCaseCards(normal);

    // 6. 空状态
    const emptyEl = document.getElementById('recordsEmpty');
    if (emptyEl) {
        const showEmpty = (starred.length === 0 && normal.length === 0);
        emptyEl.style.display = showEmpty ? '' : 'none';
        if (showEmpty && _recordState.allRecords.length === 0) {
            emptyEl.innerHTML = `
                <div class="empty-icon">📋</div>
                <div class="empty-text">暂无排盘记录</div>
                <div class="empty-hint">排一盘试试吧，记录会自动保存在这里</div>
                <button class="btn btn-accent btn-sm" onclick="switchToolTab(document.querySelector('[data-tab=bazi-free]'))">去排盘</button>
            `;
        }
    }
}

// ── 渲染星标区 ──
function renderStarSection(records) {
    const section = document.getElementById('starSection');
    const container = document.getElementById('starCards');
    if (!section || !container) return;

    if (records.length === 0) {
        section.style.display = 'none';
        return;
    }
    section.style.display = '';
    container.innerHTML = '';
    records.forEach(rec => {
        container.appendChild(createBzCard(rec, true));
    });
}

// ── 渲染案例列表 ──
function renderCaseCards(records) {
    const container = document.getElementById('caseCards');
    if (!container) return;
    container.innerHTML = '';
    if (_recordState.batchMode) {
        container.classList.add('batch-mode');
    } else {
        container.classList.remove('batch-mode');
    }
    records.forEach(rec => {
        container.appendChild(createBzCard(rec, false));
    });
}

// 五行颜色映射
const WUXING_GAN = {
    '甲':'木','乙':'木','丙':'火','丁':'火','戊':'土',
    '己':'土','庚':'金','辛':'金','壬':'水','癸':'水'
};
const WUXING_ZHI = {
    '子':'水','丑':'土','寅':'木','卯':'木','辰':'土',
    '巳':'火','午':'火','未':'土','申':'金','酉':'金',
    '戌':'土','亥':'水'
};
const WUXING_COLORS = {
    '木': { bg: 'rgba(76, 175, 80, 0.75)', text: '#fff' },
    '火': { bg: 'rgba(244, 67, 54, 0.75)', text: '#fff' },
    '土': { bg: 'rgba(255, 152, 0, 0.75)', text: '#fff' },
    '金': { bg: 'rgba(255, 193, 7, 0.85)', text: '#333' },
    '水': { bg: 'rgba(33, 150, 243, 0.75)', text: '#fff' },
};

// ── 创建单个卡片 ──
function createBzCard(rec, isStar) {
    const recId = rec.id || 0;
    const card = document.createElement('div');
    card.className = 'bz-card' + (rec.starred ? ' starred' : '') +
                     ((rec.type === 'hepan') ? ' hepan-card' : '');
    card.dataset.recId = recId;
    card.onclick = function(e) {
        // 忽略菜单/星标/复选框点击
        if (e.target.closest('.card-menu') || e.target.closest('.card-star') || e.target.closest('.batch-checkbox') || e.target.closest('.card-dropdown')) return;
        if (_recordState.batchMode) {
            toggleBatchItem(recId);
            return;
        }
        replayRecord(rec);
    };

    const year = extractYear(rec.birth_time);
    const sxEmoji = getShengxiaoEmoji(year);
    const dateStr = formatBirthDate(rec);
    const pillars = parsePillars(rec.pillars);

    let gzHtml = '';
    if (pillars) {
        gzHtml = `<div class="card-gz">
            <div class="card-gan">${pillars.gan.map(g => {
                const wx = WUXING_GAN[g] || '';
                const c = WUXING_COLORS[wx] || { bg: 'rgba(178,149,91,0.7)', text: '#fff' };
                return `<label style="background:${c.bg};color:${c.text}">${g}</label>`;
            }).join('')}</div>
            <div class="card-zhi">${pillars.zhi.map(z => {
                const wx = WUXING_ZHI[z] || '';
                const c = WUXING_COLORS[wx] || { bg: 'rgba(178,149,91,0.45)', text: '#fff' };
                return `<label style="background:${c.bg};color:${c.text};opacity:0.8">${z}</label>`;
            }).join('')}</div>
        </div>`;
    }

    let hepanHtml = '';
    if (rec.type === 'hepan' && rec.hepan_data) {
        const hd = rec.hepan_data;
        const p1g = hd.person1.gender === '女' ? '♀' : '♂';
        const p2g = hd.person2.gender === '女' ? '♀' : '♂';
        const score = hd.score || 0;
        hepanHtml = `<div class="hepan-info">
            <span>${hd.person1.name} ${p1g}</span>
            <span class="hepan-vs">VS</span>
            <span>${hd.person2.name} ${p2g}</span>
            <span class="hepan-score">${score}分</span>
        </div>`;
    }

    card.innerHTML = `
        <input type="checkbox" class="batch-checkbox" ${_recordState.selectedIds.has(recId)?'checked':''} onchange="toggleBatchItem(${recId})">
        <div class="sx-icon">${sxEmoji}</div>
        <div class="card-userinfo">
            <div class="card-name">${rec.name || '未命名'} <span class="card-sex">${rec.gender || '男'}</span></div>
            ${dateStr ? `<div class="card-date">${dateStr}</div>` : ''}
        </div>
        ${rec.type === 'hepan' ? hepanHtml : gzHtml}
        <span class="card-star ${rec.starred?'starred':''}" onclick="event.stopPropagation();toggleStar(${recId})">${rec.starred?'⭐':'☆'}</span>
        <span class="card-menu" onclick="event.stopPropagation();toggleCardDropdown(this, ${recId})">
            <svg viewBox="0 0 1024 1024" width="16" height="16"><path fill="currentColor" d="M176 416a112 112 0 1 1 0 224 112 112 0 0 1 0-224m336 0a112 112 0 1 1 0 224 112 112 0 0 1 0-224m336 0a112 112 0 1 1 0 224 112 112 0 0 1 0-224"/></svg>
        </span>
        <div class="card-dropdown" id="dropdown-${recId}">
            <button class="card-dropdown-item" onclick="event.stopPropagation();toggleStar(${recId})">${rec.starred ? '取消星标' : '设为星标'}</button>
            <button class="card-dropdown-item" onclick="event.stopPropagation();changeCategory(${recId})">修改分类</button>
            <button class="card-dropdown-item danger" onclick="event.stopPropagation();deleteSingleRecord(${recId})">删除</button>
        </div>
    `;
    return card;
}

// ── 排盘记录跳转 ──
function replayRecord(rec) {
    if (rec.type === 'hepan') {
        // 合盘记录跳转
        if (rec.params) {
            const hepanParams = {...rec.params, _replay: true};
            sessionStorage.setItem('xc_hepan_params', JSON.stringify(hepanParams));
        }
        window.location.href = '/hepan';
        return;
    }
    if (!rec || !rec.params) {
        window.location.href = '/bazi-page#free';
        return;
    }
    const p = rec.params;
    const storeParams = {
        calType: p.calType || p.cal_type || '公历',
        gender: rec.gender || '男',
        name: rec.name || '',
        birthTime: p.birthTime || p.birth_time || '',
        birthAddr: p.birthAddr || p.birth_addr || '',
        isDst: !!p.isDst,
        nightZiMode: p.nightZiMode || p.night_zi_mode || '夜子时不换日',
        useSolarTime: p.useSolarTime !== false,
        isLeapMonth: !!p.isLeapMonth
    };
    if (p.siziPillars) storeParams.siziPillars = p.siziPillars;
    if (p.birthDate) storeParams.birthDate = p.birthDate;
    if (p.birthHour != null) storeParams.birthHour = p.birthHour;
    storeParams._replay = true;  // 标记为回放，不重复保存记录
    sessionStorage.setItem('xc_bazi_params', JSON.stringify(storeParams));
    window.location.href = '/bazi';
}

// ── Tab切换 ──
function switchRecordTab(type) {
    _recordState.tab = type;
    document.querySelectorAll('.record-tab').forEach(t => {
        t.classList.toggle('active', t.getAttribute('data-type') === type);
    });
    filterAndRender();
}

// ── 搜索 ──
function onRecordSearch() {
    const input = document.getElementById('recordSearchInput');
    _recordState.search = input ? input.value : '';
    filterAndRender();
}

// ── 分类选择 ──
function selectCategory(cat) {
    _recordState.category = cat;
    document.querySelectorAll('.cat-tag').forEach(t => {
        t.classList.toggle('active', t.getAttribute('data-cat') === cat);
    });
    filterAndRender();
}

// ── 星标切换 ──
function toggleStar(recId) {
    closeAllDropdowns();
    apiFetch('/api/bazi/history/star', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: recId})
    })
    .then(r => r.json())
    .then(() => { loadRecords(); })
    .catch(() => {});
}

// ── 修改分类 ──
function changeCategory(recId) {
    closeAllDropdowns();
    const cats = ['全部', '客户', '名人', '亲友'];
    const rec = _recordState.allRecords.find(r => r.id === recId);
    const current = rec?.category || '全部';
    const cat = prompt(`请输入分类（${cats.join('/')}）：`, current);
    if (!cat || !cats.includes(cat)) return;
    apiFetch('/api/bazi/history/category', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: recId, category: cat})
    })
    .then(r => r.json())
    .then(() => { loadRecords(); })
    .catch(() => {});
}

// ── 单条删除 ──
function deleteSingleRecord(recId) {
    closeAllDropdowns();
    if (!confirm('确定删除该条记录？')) return;
    apiFetch('/api/bazi/history/delete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: recId})
    })
    .then(r => r.json())
    .then(() => { loadRecords(); })
    .catch(() => {});
}

// ── 下拉菜单 ──
function toggleCardDropdown(el, recId) {
    const dd = document.getElementById('dropdown-' + recId);
    if (!dd) return;
    const wasOpen = dd.classList.contains('show');
    closeAllDropdowns();
    if (!wasOpen) dd.classList.add('show');
}
function closeAllDropdowns() {
    document.querySelectorAll('.card-dropdown.show').forEach(d => d.classList.remove('show'));
}
// 点击空白处关闭下拉
document.addEventListener('click', function(e) {
    if (!e.target.closest('.card-menu') && !e.target.closest('.card-dropdown')) {
        closeAllDropdowns();
    }
});

// ── 批量删除 ──
function toggleBatchDelete() {
    _recordState.batchMode = !_recordState.batchMode;
    _recordState.selectedIds.clear();
    const btn = document.getElementById('batchDeleteBtn');
    const bar = document.getElementById('batchBar');
    if (btn) btn.classList.toggle('active', _recordState.batchMode);
    if (bar) bar.style.display = _recordState.batchMode ? '' : 'none';
    updateBatchCount();
    filterAndRender();
}
function cancelBatchDelete() {
    _recordState.batchMode = false;
    _recordState.selectedIds.clear();
    const btn = document.getElementById('batchDeleteBtn');
    const bar = document.getElementById('batchBar');
    if (btn) btn.classList.remove('active');
    if (bar) bar.style.display = 'none';
    filterAndRender();
}
function toggleBatchItem(recId) {
    if (_recordState.selectedIds.has(recId)) {
        _recordState.selectedIds.delete(recId);
    } else {
        _recordState.selectedIds.add(recId);
    }
    updateBatchCount();
    filterAndRender();
}
function toggleSelectAll() {
    const all = document.getElementById('batchSelectAll');
    const checked = all ? all.checked : false;
    _recordState.selectedIds.clear();
    if (checked) {
        // 选中当前过滤后的所有记录ID
        let filtered = _recordState.allRecords.filter(r => (r.type || 'paipan') === _recordState.tab);
        if (_recordState.category !== '全部') {
            filtered = filtered.filter(r => (r.category || '全部') === _recordState.category);
        }
        filtered.forEach(r => {
            if (r.id) _recordState.selectedIds.add(r.id);
        });
    }
    updateBatchCount();
    filterAndRender();
}
function updateBatchCount() {
    const countEl = document.getElementById('batchCount');
    if (countEl) countEl.textContent = `已选 ${_recordState.selectedIds.size} 项`;
}
function confirmBatchDelete() {
    if (_recordState.selectedIds.size === 0) { alert('请先选择要删除的记录'); return; }
    if (!confirm(`确定删除选中的 ${_recordState.selectedIds.size} 条记录？`)) return;
    apiFetch('/api/bazi/history/batch-delete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ids: Array.from(_recordState.selectedIds)})
    })
    .then(r => r.json())
    .then(() => {
        cancelBatchDelete();
        loadRecords();
    })
    .catch(() => {});
}

// ── 筛选面板（简化版：切换分类） ──
function toggleFilterPanel() {
    // 简化为分类标签的显隐，已内嵌在页面中
    const catSection = document.querySelector('.record-categories');
    if (catSection) {
        catSection.style.display = catSection.style.display === 'none' ? '' : 'none';
    }
}

// 刷新记录
function refreshRecords() {
    loadRecords();
}

// 清空所有记录
function clearRecords() {
    if (!confirm('确定清空所有排盘记录？此操作不可恢复。')) return;
    apiFetch('/api/bazi/history/clear', { method: 'POST' })
        .then(r => r.json())
        .then(() => { loadRecords(); })
        .catch(() => {});
    localStorage.removeItem('bazi_records');
    loadRecords();
}

// 删除单条记录（兼容旧接口）
function deleteRecord(recId) {
    deleteSingleRecord(recId);
}
