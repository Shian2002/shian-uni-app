// ═══ 专属日历页面脚本 ═══
// 通用函数（toggleTheme/showModal/loadCalMonth 等）由 home.js 提供

// 主题初始化
(function(){
    const t=localStorage.getItem('xc_theme');
    if(t){
        document.documentElement.setAttribute('data-theme',t);
        const btn=document.getElementById('themeBtn');
        if(btn) btn.textContent=t==='dark'?'🌙':'☀️';
    }
})();

// 页面加载时自动渲染当月日历
document.addEventListener('DOMContentLoaded', function(){
    const now = new Date();
    if(typeof loadCalMonth === 'function'){
        loadCalMonth(now.getFullYear(), now.getMonth() + 1);
    }
});
