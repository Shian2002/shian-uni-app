// ═══ 工具函数（核心由 api-client.js 提供） ═══
// $, getCSRF, apiFetch, esc, sanitizeData, toggleTheme, openMobileMenu, closeMobileMenu 已在 api-client.js 中定义

async function loadHistory() {
    try {
        const resp = await apiFetch('/api/bazi/history');
        const data = await resp.json();
        if (!data.success) return;

        const list = document.getElementById('historyList');
        const history = data.history || [];

        if (history.length === 0) {
            list.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><div>暂无排盘记录</div><div style="font-size:0.82rem;margin-top:8px;">排盘后记录会自动保存在这里</div></div>';
            return;
        }

        document.getElementById('clearBtn').style.display = '';

        let html = '';
        for (const item of history) {
            const time = item.created_at ? new Date(item.created_at).toLocaleString('zh-CN', {month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '';
            html += `<div class="record-card" onclick="rePaipan(${encodeURIComponent(JSON.stringify(item.params||{}))})">
                <div class="record-header">
                    <span class="record-name">${esc(item.name || '未命名')}</span>
                    <span class="record-time">${esc(time)}</span>
                </div>
                <div class="record-pillars">${esc(item.pillars || '----')}</div>
                <div class="record-meta">
                    <span>${esc(item.gender || '')}</span>
                    <span>${esc(item.birth_time || '')}</span>
                    <span>${esc(item.cal_type || '公历')}</span>
                    ${item.birth_addr ? `<span>${esc(item.birth_addr)}</span>` : ''}
                </div>
            </div>`;
        }
        list.innerHTML = html;
    } catch(e) {
        console.error('加载历史失败:', e);
    }
}

function rePaipan(params) {
    // 保存参数并跳转到排盘结果页
    sessionStorage.setItem('baziFreeParams', JSON.stringify(params));
    window.location.href = '/bazi';
}

async function clearHistory() {
    if (!confirm('确定要清空所有排盘历史吗？')) return;
    try {
        await apiFetch('/api/bazi/history/clear', {method:'POST'});
        document.getElementById('clearBtn').style.display = 'none';
        loadHistory();
    } catch(e) {}
}

loadHistory();
