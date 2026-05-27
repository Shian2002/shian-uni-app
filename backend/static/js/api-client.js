/**
 * 时安解忧屋 — 统一API客户端与工具函数
 * 所有页面共享：CSRF自动注入、HTML转义、数据清洗、主题切换、导航
 */

// ═══ DOM 快捷选择 ═══
const $ = id => document.getElementById(id);

// ═══ CSRF Token ═══
function getCSRF() {
    const el = document.querySelector('meta[name="csrf-token"]');
    if (!el || !el.content) {
        console.warn('[api-client] CSRF token meta tag missing');
    }
    return el?.content || '';
}

// ═══ 统一 fetch 封装 — 自动携带 CSRF Token ═══
function apiFetch(url, opts = {}) {
    const h = opts.headers || {};
    h['X-CSRFToken'] = getCSRF();
    opts.headers = h;
    opts.credentials = opts.credentials || 'include';
    return fetch(url, opts);
}

// ═══ HTML 转义（防XSS） ═══
function esc(s) {
    if (s == null) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
function escapeHtml(s) { return esc(s); }

// ═══ 递归数据清洗 — 对API返回数据中的所有字符串进行转义 ═══
function sanitizeData(obj) {
    if (typeof obj === 'string') return esc(obj);
    if (Array.isArray(obj)) return obj.map(sanitizeData);
    if (obj && typeof obj === 'object') {
        const r = {};
        for (const k of Object.keys(obj)) r[k] = sanitizeData(obj[k]);
        return r;
    }
    return obj;
}

// ═══ 主题切换 ═══
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    const btn = $('themeBtn');
    if (btn) btn.textContent = isDark ? '☀️' : '🌙';
    localStorage.setItem('xc_theme', isDark ? 'light' : 'dark');
}

// 页面加载时恢复主题
(function() {
    const t = localStorage.getItem('xc_theme');
    if (t) {
        document.documentElement.setAttribute('data-theme', t);
        const btn = $('themeBtn');
        if (btn) btn.textContent = t === 'dark' ? '🌙' : '☀️';
    }
})();

// ═══ 移动端菜单 ═══
function openMobileMenu() {
    const m = $('mobileMenu');
    if (m) { m.classList.add('open'); document.body.style.overflow = 'hidden'; }
}
function closeMobileMenu() {
    const m = $('mobileMenu');
    if (m) { m.classList.remove('open'); document.body.style.overflow = ''; }
}

// ═══ 认证弹窗（占位 — 由各页面或 home.js 扩展） ═══
function showLogin() {
    // 如果页面有自定义登录逻辑，由页面JS覆盖此函数
    if (typeof _showLogin === 'function') { _showLogin(); return; }
    alert('请先访问首页登录');
    window.location.href = '/#login';
}
function showRegister() {
    if (typeof _showRegister === 'function') { _showRegister(); return; }
    alert('请先访问首页注册');
    window.location.href = '/#register';
}
