// ═══ 工具函数 ═══
const $=id=>document.getElementById(id);
function getCSRF(){return document.querySelector('meta[name="csrf-token"]')?.content||'';}
function apiFetch(url,opts={}){const h=opts.headers||{};h['X-CSRFToken']=getCSRF();opts.headers=h;opts.credentials='include';return fetch(url,opts);}

// ═══ 主题切换 ═══
function toggleTheme(){
    const html=document.documentElement;
    const isDark=html.getAttribute('data-theme')==='dark';
    html.setAttribute('data-theme',isDark?'light':'dark');
    $('themeBtn').textContent=isDark?'☀️':'🌙';
    localStorage.setItem('xc_theme',isDark?'light':'dark');
}
(function(){
    const t=localStorage.getItem('xc_theme');
    if(t){document.documentElement.setAttribute('data-theme',t);$('themeBtn').textContent=t==='dark'?'🌙':'☀️';}
})();

// ═══ Tab 切换 ═══
function switchTab(btn){
    document.querySelectorAll('.panel-tab').forEach(t=>t.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c=>c.style.display='none');
    const tab=btn.getAttribute('data-tab');
    const el=$('tab-'+tab);
    if(el) el.style.display='block';
}

// ═══ 模式切换 ═══
function switchMode(btn,mode){
    btn.parentElement.querySelectorAll('.mode-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.advanced-fields').forEach(f=>{
        if(mode==='pro') f.classList.add('show');
        else f.classList.remove('show');
    });
    document.querySelectorAll('.advanced-toggle').forEach(t=>{
        t.style.display=mode==='pro'?'none':'inline';
    });
}

// ═══ 结果模式切换 ═══
function switchResult(btn,mode){
    btn.parentElement.querySelectorAll('.result-mode-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    sessionStorage.setItem('xc_result_mode',mode);
}

// ═══ 高级选项 ═══
function toggleAdvanced(id){
    const el=$(id);
    el.classList.toggle('show');
}

// ═══ 跳转工具页（携带表单数据） ═══
function goTool(type){
    const data={type:type};
    const activeTab=document.querySelector('.panel-tab.active');
    if(activeTab) data.tab=activeTab.getAttribute('data-tab');
    const qaiType=$('qai-type');const qaiTime=$('qai-time');const qaiCal=$('qai-cal');const qaiQuestion=$('qai-question');
    if(qaiType) data.qaiType=qaiType.value;
    if(qaiTime) data.qaiTime=qaiTime.value;
    if(qaiCal) data.qaiCal=qaiCal.value;
    if(qaiQuestion) data.qaiQuestion=qaiQuestion.value;
    const baiGender=$('bai-gender');const baiCal=$('bai-cal');const baiDate=$('bai-date');const baiHour=$('bai-hour');const baiAddr=$('bai-addr');
    if(baiGender) data.baiGender=baiGender.value;
    if(baiCal) data.baiCal=baiCal.value;
    if(baiDate) data.baiDate=baiDate.value;
    if(baiHour) data.baiHour=baiHour.value;
    if(baiAddr) data.baiAddr=baiAddr.value;
    sessionStorage.setItem('xc_form_data',JSON.stringify(data));
    window.location.href='/tool#'+type;
}
function goToolScenario(type,scenario){
    sessionStorage.setItem('xc_scenario',scenario);
    window.location.href='/tool#'+type;
}

// ═══ FAQ ═══
function toggleFaq(el){
    el.classList.toggle('open');
    el.nextElementSibling.classList.toggle('open');
}

// ═══ 移动端菜单 ═══
function openMobileMenu(){$('mobileMenu').classList.add('open');}
function closeMobileMenu(){$('mobileMenu').classList.remove('open');}

// ═══ 登录/注册 ═══
function showLogin(){$('loginModal').classList.add('open');}
function showRegister(){$('registerModal').classList.add('open');}
function closeModal(id){$(id).classList.remove('open');}
let currentUser=null;

async function doLogin(){
    const u=$('loginUser').value.trim(),p=$('loginPass').value;
    if(!u||!p){$('loginError').textContent='请填写完整';return;}
    const r=await apiFetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
    const d=await r.json();
    if(d.error){$('loginError').textContent=d.error;return;}
    currentUser=d;closeModal('loginModal');updateNavUser();
}
async function doRegister(){
    const u=$('regUser').value.trim(),p=$('regPass').value,p2=$('regPass2').value;
    if(!u||!p){$('regError').textContent='请填写完整';return;}
    if(p!==p2){$('regError').textContent='两次密码不一致';return;}
    const r=await apiFetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
    const d=await r.json();
    if(d.error){$('regError').textContent=d.error;return;}
    currentUser=d;closeModal('registerModal');updateNavUser();
}
function updateNavUser(){
    const right=document.querySelector('.topnav-right');
    if(!right){console.warn('[auth] .topnav-right not found');return;}
    if(currentUser){
        console.log('[auth] updating nav for user:', currentUser.username);
        right.innerHTML=`<button class="theme-toggle-nav" onclick="toggleTheme()" id="themeBtn" title="切换主题">🌙</button><div class="nav-user-info"><span class="nav-avatar">${currentUser.username.charAt(0).toUpperCase()}</span><span class="nav-username">${currentUser.username}</span></div><a href="/tool#profile" class="btn btn-outline btn-sm">个人中心</a><button class="btn btn-outline btn-sm" onclick="doLogout()">退出</button>`;
        const t=localStorage.getItem('xc_theme');
        if($('themeBtn'))$('themeBtn').textContent=t==='light'?'☀️':'🌙';
    }else{
        right.innerHTML=`<input type="text" class="topnav-search" placeholder="搜索排盘、术语、案例..."><button class="theme-toggle-nav" onclick="toggleTheme()" id="themeBtn" title="切换主题">🌙</button><span class="nav-auth-btns" id="navAuthBtns"><button class="btn btn-outline btn-sm" onclick="showLogin()">登录</button><button class="btn btn-accent btn-sm" onclick="showRegister()">注册</button></span>`;
        const t=localStorage.getItem('xc_theme');
        if($('themeBtn'))$('themeBtn').textContent=t==='light'?'☀️':'🌙';
    }
}
async function doLogout(){
    await apiFetch('/api/logout',{method:'POST'});
    currentUser=null;location.reload();
}

// ═══ 清空数据 ═══
async function clearAllData(){
    if(!confirm('确认清空所有数据？此操作不可撤销。'))return;
    localStorage.clear();sessionStorage.clear();
    // 尝试清空服务端数据
    try{
        const me=await fetch('/api/me',{credentials:'include'});const d=await me.json();
        if(!d.guest){
            const records=await fetch('/api/records',{credentials:'include'});const rd=await records.json();
            if(rd.records){for(const rec of rd.records){await apiFetch(`/api/records/${rec.id}`,{method:'DELETE'});}}
        }
    }catch(e){}
    alert('已清空所有数据');
}

// ═══ 自动检测登录状态 ═══
async function autoCheckAuth(){
    try{
        const r=await fetch('/api/me',{credentials:'include'});
        const d=await r.json();
        console.log('[auth] /api/me =>', JSON.stringify(d));
        if(!d.guest){currentUser=d;updateNavUser();}
    }catch(e){console.warn('[auth] autoCheckAuth error:',e);}
}

// ═══ Enter键提交 ═══
document.addEventListener('DOMContentLoaded',()=>{
    autoCheckAuth();
    const lp=$('loginPass');if(lp)lp.addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
    const lu=$('loginUser');if(lu)lu.addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
    const rp=$('regPass2');if(rp)rp.addEventListener('keydown',e=>{if(e.key==='Enter')doRegister();});
    // 初始化日历
    const now = new Date();
    loadCalMonth(now.getFullYear(), now.getMonth() + 1);
});

// ═══ 设置默认时间 ═══
(function(){
    const now=new Date();
    const local=new Date(now.getTime()-now.getTimezoneOffset()*60000).toISOString().slice(0,16);
    const qaiTime=$('qai-time');if(qaiTime)qaiTime.value=local;
    const qfTime=$('qf-time');if(qfTime)qfTime.value=local;
    const baiDate=$('bai-date');if(baiDate)baiDate.value=local.slice(0,10);
})();

// ═══ 搜索功能 ═══
const SEARCH_MAP = [
    {kw:['奇门','遁甲','问策','问事','一事一断'],panel:'qimen'},
    {kw:['八字','排盘','四柱','命理','大运','流年'],panel:'paipan'},
    {kw:['六爻','铜钱','起卦','摇卦'],panel:'liuyao'},
    {kw:['梅花','易数','报数','字占'],panel:'meihua'},
    {kw:['紫微','斗数','命盘'],panel:'ziwei'},
    {kw:['择吉','吉日','吉时','婚嫁','搬家','开业'],panel:'zeji'},
    {kw:['黄历','万年历','宜忌','农历','老黄历'],panel:'huangli'},
    {kw:['塔罗','牌阵','抽牌'],panel:'taluo'},
];
function doSearch(){
    const input = document.querySelector('.topnav-search');
    if(!input) return;
    const q = input.value.trim();
    if(!q) return;
    let panel = 'qimen';
    for(const item of SEARCH_MAP){
        if(item.kw.some(k=>q.includes(k))){panel=item.panel;break;}
    }
    window.location.href = '/tool#' + panel;
}
document.querySelector('.topnav-search')?.addEventListener('keydown',function(e){
    if(e.key==='Enter') doSearch();
});

// ═══ 今日黄历 ═══
async function showTodayHuangli(){
    const today = new Date().toISOString().slice(0,10);
    try{
        const r = await fetch('/api/huangli?date='+today);
        const d = await r.json();
        let msg = `📅 ${today}\n`;
        if(d.lunarDate) msg += `🌙 农历：${d.lunarDate}\n`;
        if(d.ganZhiYear) msg += `🐉 ${d.ganZhiYear} 生肖：${d.shengXiao}\n`;
        msg += '\n⚠️ 以上内容仅为民俗文化参考';
        alert(msg);
    }catch(e){alert('查询失败，请稍后重试');}
}

// ═══ 运势日历（吉真万年历风格） ═══
let calYear, calMonth, calMonthData = null, calSelectedDate = null;

async function loadCalMonth(y, m) {
    calYear = y; calMonth = m;
    const grid = $('calGrid');
    if (!grid) return;
    // 标题
    $('calTitle').textContent = `${y}年${m}月`;
    // 加载动画
    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-3);">加载中...</div>';
    try {
        const resp = await fetch(`/api/huangli/month?year=${y}&month=${m}`);
        const data = await resp.json();
        calMonthData = data.days || [];
        renderCalGrid(y, m, calMonthData);
    } catch (e) {
        grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--danger);">加载失败</div>';
    }
}

function renderCalGrid(year, month, days) {
    const grid = $('calGrid');
    grid.innerHTML = '';
    // 星期头
    const wkNames = ['日','一','二','三','四','五','六'];
    wkNames.forEach((w, i) => {
        const el = document.createElement('div');
        el.className = 'cal-wk' + (i === 0 || i === 6 ? ' weekend' : '');
        el.textContent = w;
        grid.appendChild(el);
    });
    // 空位
    const firstDay = new Date(year, month - 1, 1).getDay();
    for (let i = 0; i < firstDay; i++) {
        const el = document.createElement('div');
        el.className = 'cal-cell empty';
        grid.appendChild(el);
    }
    // 日期格子
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
    days.forEach(d => {
        const el = document.createElement('div');
        const isToday = d.solarDate === todayStr;
        const isSelected = d.solarDate === calSelectedDate;
        const dayOfWeek = new Date(d.solarDate).getDay();
        const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
        el.className = 'cal-cell' + (isToday ? ' today' : '') + (isSelected ? ' selected' : '') + (isWeekend ? ' weekend' : '');
        // 农历显示
        const isMonthFirst = d.lunarDay === 1;
        const lunarClass = isMonthFirst ? 'cal-lunar month-first' : 'cal-lunar';
        const lunarText = d.lunarDisplay || '';
        // 五行色块
        const wxColor = d.wuXingColor || '#888';
        const wxText = d.wuXingDay || '';
        el.innerHTML = `
            <span class="cal-solar">${d.solarDate.split('-')[2]}</span>
            <span class="${lunarClass}">${lunarText}</span>
            <span class="cal-wx" style="color:${wxColor};background:${wxColor}15;border:1px solid ${wxColor}30;">${wxText}</span>
            <span class="cal-gz">${d.ganZhiDay || ''}</span>
        `;
        el.onclick = () => showCalDetail(d);
        grid.appendChild(el);
    });
}

function showCalDetail(d) {
    calSelectedDate = d.solarDate;
    // 高亮选中
    document.querySelectorAll('.cal-cell').forEach(c => c.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    const detail = $('calDetail');
    const dateEl = $('calDetailDate');
    const gridEl = $('calDetailGrid');
    dateEl.textContent = `${d.solarDate} ${d.weekday}曜`;
    const wxColor = d.wuXingColor || '#888';
    // 节气
    let solarTermHtml = d.solarTerm ? `<div class="cal-detail-item"><div class="cal-detail-label">节气</div><div class="cal-detail-value" style="color:var(--accent)">${d.solarTerm}</div></div>` : '';
    // 节日
    let festivalHtml = '';
    if (d.gJie) festivalHtml += `<div class="cal-detail-item"><div class="cal-detail-label">公历节日</div><div class="cal-detail-value">${d.gJie}</div></div>`;
    if (d.lJie) festivalHtml += `<div class="cal-detail-item"><div class="cal-detail-label">农历节日</div><div class="cal-detail-value">${d.lJie}</div></div>`;
    // 宜忌（仅 API 数据有）
    let yiJiHtml = '';
    if (d.yi && d.yi !== '日值岁破 大事不宜') {
        yiJiHtml += `<div class="cal-detail-item"><div class="cal-detail-label">宜</div><div class="cal-detail-value" style="color:#228B22">${d.yi}</div></div>`;
    }
    if (d.ji && d.ji !== '日值岁破 大事不宜') {
        yiJiHtml += `<div class="cal-detail-item"><div class="cal-detail-label">忌</div><div class="cal-detail-value" style="color:#DC143C">${d.ji}</div></div>`;
    }
    if (d.yi === '日值岁破 大事不宜' || d.ji === '日值岁破 大事不宜') {
        yiJiHtml += `<div class="cal-detail-item"><div class="cal-detail-label">宜忌</div><div class="cal-detail-value" style="color:#8B4513">日值岁破 大事不宜</div></div>`;
    }
    // 喜神福神财神
    let shenWeiHtml = '';
    if (d.shenWei) {
        const sw = d.shenWei;
        shenWeiHtml = `<div class="cal-detail-item"><div class="cal-detail-label">神位</div><div class="cal-detail-value" style="font-size:0.8em">${sw}</div></div>`;
    }
    // 彭祖百忌
    let pengZuHtml = d.pengZu ? `<div class="cal-detail-item"><div class="cal-detail-label">彭祖百忌</div><div class="cal-detail-value">${d.pengZu}</div></div>` : '';
    // 月相
    let moonHtml = d.moonName ? `<div class="cal-detail-item"><div class="cal-detail-label">月相</div><div class="cal-detail-value">${d.moonName}</div></div>` : '';

    gridEl.innerHTML = `
        ${solarTermHtml}
        ${festivalHtml}
        <div class="cal-detail-item"><div class="cal-detail-label">农历</div><div class="cal-detail-value">${d.lunarMonthName || ''}${d.lunarDayName || ''}</div></div>
        <div class="cal-detail-item"><div class="cal-detail-label">干支年</div><div class="cal-detail-value">${d.ganZhiYear || ''}</div></div>
        <div class="cal-detail-item"><div class="cal-detail-label">干支月</div><div class="cal-detail-value">${d.ganZhiMonth || ''}</div></div>
        <div class="cal-detail-item"><div class="cal-detail-label">干支日</div><div class="cal-detail-value">${d.ganZhiDay || ''}</div></div>
        <div class="cal-detail-item"><div class="cal-detail-label">日干五行</div><div class="cal-detail-value" style="color:${wxColor}">${d.wuXingDay || ''}</div></div>
        <div class="cal-detail-item"><div class="cal-detail-label">纳音</div><div class="cal-detail-value">${d.naYin || ''}</div></div>
        <div class="cal-detail-item"><div class="cal-detail-label">建除</div><div class="cal-detail-value">${d.jianChu || ''}</div></div>
        <div class="cal-detail-item"><div class="cal-detail-label">冲煞</div><div class="cal-detail-value">${d.chong || ''} ${d.sha || ''}</div></div>
        <div class="cal-detail-item"><div class="cal-detail-label">生肖</div><div class="cal-detail-value">${d.shengXiao || ''}年</div></div>
        ${yiJiHtml}
        ${pengZuHtml}
        ${shenWeiHtml}
        ${moonHtml}
    `;
    detail.classList.add('show');
}

function closeCalDetail() {
    $('calDetail').classList.remove('show');
    calSelectedDate = null;
    document.querySelectorAll('.cal-cell.selected').forEach(c => c.classList.remove('selected'));
}

function calPrev() {
    let y = calYear, m = calMonth - 1;
    if (m < 1) { m = 12; y--; }
    loadCalMonth(y, m);
}
function calNext() {
    let y = calYear, m = calMonth + 1;
    if (m > 12) { m = 1; y++; }
    loadCalMonth(y, m);
}
function calToday() {
    const now = new Date();
    loadCalMonth(now.getFullYear(), now.getMonth() + 1);
}

// ═══ 奇门遁甲免费排盘 ═══
async function qimenFreePaipan() {
    const timeInput = $('qf-time');
    const pantypeEl = $('qf-pantype');
    let y, m, d, h = 12, min = 0;
    if (timeInput && timeInput.value) {
        const dt = new Date(timeInput.value);
        y = dt.getFullYear(); m = dt.getMonth() + 1; d = dt.getDate(); h = dt.getHours(); min = dt.getMinutes();
    } else {
        const now = new Date();
        y = now.getFullYear(); m = now.getMonth() + 1; d = now.getDate(); h = now.getHours(); min = now.getMinutes();
    }
    const panType = pantypeEl ? parseInt(pantypeEl.value) : 1;
    const resultEl = $('qfResult');
    resultEl.style.display = 'block';
    resultEl.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-3);">排盘计算中...</div>';

    try {
        const resp = await apiFetch('/api/qimen/paipan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ year: y, month: m, day: d, hour: h, minute: min, panType: panType })
        });
        const data = await resp.json();
        if (data.error) { resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">${data.error}</div>`; return; }
        resultEl.innerHTML = renderQimenPalaceGrid(data);
    } catch (e) {
        resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">排盘失败: ${e.message}</div>`;
    }
}

function renderQimenPalaceGrid(data) {
    const fp = data.fourPillars || {};
    const palaces = data.palaces || [];
    const dayGan = data.dayGan || '';
    const hourGan = data.hourGan || '';
    // 洛书九宫排列顺序：4(巽) 9(离) 2(坤) / 3(震) 5(中) 7(兑) / 8(艮) 1(坎) 6(乾)
    const luoOrder = [4, 9, 2, 3, 5, 7, 8, 1, 6];

    // 颜色规则：值符=绿, 值使=绿, 击刑=紫, 门迫=红, 刑+墓=蓝
    const C_ZHIFU = '#27AE60';      // 值符 - 绿
    const C_ZHISHI = '#27AE60';     // 值使 - 绿
    const C_RUMU = '#8B4513';       // 入墓 - 棕
    const C_JIXING = '#9B59B6';     // 击刑 - 紫
    const C_MENPO = '#E74C3C';      // 门迫 - 红
    const C_XINGMU = '#2980B9';     // 刑+墓 - 蓝
    const C_DEFAULT = '#222';       // 默认黑色
    const C_KONG = '#444';          // 空亡标记
    const C_RIGAN = '#E74C3C';      // 日干 - 红色
    const C_SHIGAN = '#E74C3C';     // 时干 - 红色
    const C_DIGAN = '#555';         // 地盘干 - 灰色
    const C_YINGAN = '#AAA';        // 隐干 - 深灰
    const C_MAHORSE = '#D4A017';    // 马星 - 金色

    // 值符星/值使门判断（用于宫位着色）
    const zhiFuStar = data.zhiFuStar || '';
    const zhiShiMen = data.zhiShiMen || '';

    let html = `<div style="background:var(--card-bg);border-radius:12px;padding:20px;border:1px solid var(--card-border);">`;

    // ═══ 概要信息区 ═══
    html += `<div style="margin-bottom:16px;border-bottom:1px solid var(--card-border);padding-bottom:12px;">`;
    // 标题行
    html += `<div style="font-size:1.1rem;font-weight:700;margin-bottom:10px;color:var(--accent);letter-spacing:2px;">奇门遁甲排盘</div>`;
    // 盘式+日期
    const panType = data.panType || '拆补法';
    html += `<div style="display:flex;flex-wrap:wrap;gap:6px 16px;font-size:0.82rem;color:var(--text-2);margin-bottom:6px;">`;
    html += `<span><b style="color:var(--text-1);">盘式：</b>转盘奇门 · ${panType}</span>`;
    if (data.solarDate) html += `<span><b style="color:var(--text-1);">时间：</b>${data.solarDate}</span>`;
    html += `</div>`;
    // 四柱
    html += `<div style="display:flex;flex-wrap:wrap;gap:6px 14px;font-size:0.82rem;margin-bottom:6px;">`;
    if (fp.year) html += `<span><b style="color:var(--text-1);">年柱</b> ${fp.year}</span>`;
    if (fp.month) html += `<span><b style="color:var(--text-1);">月柱</b> ${fp.month}</span>`;
    if (fp.day) html += `<span><b style="color:var(--text-1);">日柱</b> ${fp.day}</span>`;
    if (fp.hour) html += `<span><b style="color:var(--text-1);">时柱</b> ${fp.hour}</span>`;
    html += `</div>`;
    // 旬空
    const xk = data.xunKong || {};
    if (xk.day || xk.hour) {
        html += `<div style="font-size:0.82rem;margin-bottom:6px;">`;
        html += `<b style="color:var(--text-1);">旬空：</b>`;
        if (xk.day) html += `日空${xk.day}`;
        if (xk.day && xk.hour) html += ` `;
        if (xk.hour) html += `时空${xk.hour}`;
        html += `</div>`;
    }
    // 节气+局数+旬首
    html += `<div style="display:flex;flex-wrap:wrap;gap:6px 16px;font-size:0.82rem;margin-bottom:6px;">`;
    if (data.solarTerm) html += `<span><b style="color:var(--text-1);">节气：</b>${data.solarTerm}</span>`;
    if (data.ju) html += `<span><b style="color:var(--text-1);">局数：</b>${data.ju}</span>`;
    if (data.xunShou) html += `<span><b style="color:var(--text-1);">旬首：</b>${data.xunShou}</span>`;
    html += `</div>`;
    // 值符值使+马星
    html += `<div style="display:flex;flex-wrap:wrap;gap:6px 16px;font-size:0.82rem;">`;
    if (data.zhiFu) html += `<span style="font-weight:600;"><b>值符：</b>${data.zhiFu}</span>`;
    if (data.zhiShi) html += `<span style="font-weight:600;"><b>值使：</b>${data.zhiShi}</span>`;
    if (data.tianYi) html += `<span style="font-weight:500;"><b>天乙：</b>${data.tianYi}</span>`;
    // 马星概要
    const mx = data.maXing || {};
    const maList = [];
    if (mx['驛馬'] || mx['驿马']) maList.push('驿马→' + (mx['驛馬']||mx['驿马']));
    if (mx['丁馬'] || mx['丁马']) maList.push('丁马→' + (mx['丁馬']||mx['丁马']));
    if (mx['天馬'] || mx['天马']) maList.push('天马→' + (mx['天馬']||mx['天马']));
    if (maList.length) html += `<span><b style="color:var(--text-1);">马星：</b>${maList.join(' ')}</span>`;
    html += `</div>`;
    html += `</div>`;

    // ═══ 九宫格 — 仿热卜标准布局 v5 ═══
    // 每宫布局（3行2列 + 宫号居中）：
    //   ○八神(左)       天盘干马(右)
    //   九星(左)         地盘干(右)
    //   八门 状态(左)    隐干(右)
    //         宫号(居中)
    const baguaSimple = {'坎':'坎','坤':'坤','震':'震','巽':'巽','中':'中','乾':'乾','兌':'兑','艮':'艮','離':'离'};

    html += `<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2px;max-width:420px;margin:0 auto;background:#d5cfc2;border-radius:12px;overflow:hidden;border:2px solid #b8b0a0;box-shadow:0 2px 12px rgba(0,0,0,0.08);">`;

    for (const gongNum of luoOrder) {
        const p = palaces[gongNum - 1];
        if (!p) { html += `<div style="background:#f5f0e8;aspect-ratio:1;"></div>`; continue; }

        // 中宫：3meta风格 — 排盘概要，五行着色
        if (gongNum === 5) {
            // ── 五行颜色 ──
            const WX_GAN = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'};
            const WX_ZHI = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'};
            const WX_COLOR = {'木':'#27AE60','火':'#E74C3C','土':'#8B6914','金':'#B8860B','水':'#2980B9'};
            // 逐字着色函数：天干地支按五行上色，其余黑
            function wxColor(ch) {
                const wx = WX_GAN[ch] || WX_ZHI[ch];
                return wx ? WX_COLOR[wx] : C_DEFAULT;
            }
            function wxSpan(text) {
                // 对text逐字渲染，天干地支按五行着色
                let s = '';
                for (const c of text) {
                    const clr = wxColor(c);
                    const w = (clr === C_DEFAULT) ? '500' : '700';
                    s += `<span style="color:${clr};font-weight:${w};">${c}</span>`;
                }
                return s;
            }

            const XUN_MAP = {'戊':'甲子','己':'甲戌','庚':'甲申','辛':'甲午','壬':'甲辰','癸':'甲寅'};
            const NUM_CN = ['','一','二','三','四','五','六','七','八','九'];
            const BAGUA_NUM = {'坎':1,'坤':2,'震':3,'巽':4,'中':5,'乾':6,'兑':7,'艮':8,'离':9};
            // 旬名（甲辰旬）
            const xunRaw = XUN_MAP[data.xunShou] || '';
            // 空亡
            const xkHour = (data.xunKong && data.xunKong.hour) || '';
            const xkDay = (data.xunKong && data.xunKong.day) || '';
            // 四柱
            const fp5 = data.fourPillars || {};
            // 局解析
            const juRaw = data.ju || '';
            const ydMatch = juRaw.match(/([阳阴]遁)/);
            const juNumMatch = juRaw.match(/[一二三四五六七八九十\d]+/);
            const juNumCn = juNumMatch ? juNumMatch[0] : '';
            const juYuanMatch = juRaw.match(/(上元|中元|下元)/);
            const juYuan = juYuanMatch ? juYuanMatch[0] : '';
            const ydStr = ydMatch ? ydMatch[1] : '';
            const cn2num = {'一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9','十':'10'};
            const juNumArab = cn2num[juNumCn] || juNumCn;
            const juDisplay = ydStr ? `${ydStr}${juNumArab}局` : juRaw;
            const zhiFuNum = BAGUA_NUM[data.zhiFuGong] || 5;
            const zhiShiNum = BAGUA_NUM[data.zhiShiGong] || 2;

            const FS_C = '0.68rem';
            const FS_S = '0.58rem';

            html += `<div style="background:#f0ede5;aspect-ratio:1;color:${C_DEFAULT};padding:7px 8px;display:flex;flex-direction:column;justify-content:center;gap:3px;box-sizing:border-box;line-height:1.4;font-size:${FS_C};text-align:center;">`;
            // 日期
            const dateStr = (data.solarDate || '').split(' ')[0];
            if (dateStr) html += `<div style="font-weight:700;font-size:0.72rem;">${dateStr}</div>`;
            // 旬名 + 空亡
            html += `<div>${wxSpan(xunRaw + '旬')}`;
            if (xkHour) { html += ` ${wxSpan(xkHour)}<span style="color:${C_DEFAULT};">空</span>`; }
            html += `</div>`;
            // 四柱：逐柱着色 "丙午年 壬辰月 丁丑日 庚戌时"
            const zhuArr = [];
            const zhuLabels = ['年','月','日','时'];
            ['year','month','day','hour'].forEach((k,i) => {
                const v = fp5[k];
                if (v) zhuArr.push(wxSpan(v) + `<span style="color:${C_DEFAULT};font-weight:400;">${zhuLabels[i]}</span>`);
            });
            html += `<div style="font-size:${FS_S};">${zhuArr.join(' ')}</div>`;
            // 节气 + 元 + 局
            html += `<div style="font-weight:600;">${data.solarTerm || ''} ${juYuan} ${juDisplay}</div>`;
            // 值符值使（黑色）
            html += `<div>值符天${data.zhiFuStar || ''}落${NUM_CN[zhiFuNum]}宫</div>`;
            html += `<div>值使${(data.zhiShiMen || '') + '门'}落${NUM_CN[zhiShiNum]}宫</div>`;
            html += `</div>`;
            continue;
        }

        const bg = '#fff';
        const xingArr = Array.isArray(p.xing) ? p.xing : (p.xing ? [p.xing] : []);
        const tianGanArr = Array.isArray(p.tianGan) ? p.tianGan : (p.tianGan ? [p.tianGan] : []);
        const diGanArr = Array.isArray(p.diGan) ? p.diGan : (p.diGan ? [p.diGan] : []);
        const xingFullArr = Array.isArray(p.xingFull) ? p.xingFull : (p.xingFull ? [p.xingFull] : []);
        const isZhiFu = xingArr.includes(zhiFuStar);
        const isZhiShi = (p.men === zhiShiMen);
        const hasJiXing = p.isJiXing;
        const hasDiJiXing = p.isDiJiXing;
        const hasRuMu = p.isRuMu;
        const hasDiRuMu = p.isDiRuMu;
        const hasMenPo = p.isMenPo;
        const hasXingMu = (hasJiXing && hasRuMu) || (hasDiJiXing && hasDiRuMu);
        const hasAnyJiXing = hasJiXing || hasDiJiXing;
        const hasAnyRuMu = hasRuMu || hasDiRuMu;

        // 击刑/入墓逐字标记
        const jiXingTianSet = new Set(p.jiXingTianGans || []);
        const jiXingDiSet = new Set(p.jiXingDiGans || []);
        const ruMuTianSet = new Set(p.ruMuTianGans || []);
        const ruMuDiSet = new Set(p.ruMuDiGans || []);

        // 天干判断
        const isDayTian = dayGan && tianGanArr.includes(dayGan);
        const isHourTian = hourGan && tianGanArr.includes(hourGan);
        const isDayDi = dayGan && diGanArr.includes(dayGan);
        const isHourDi = hourGan && diGanArr.includes(hourGan);
        // 隐干判断（日干/时干红色加粗）
        const isDayYin = dayGan && p.yinGan === dayGan;
        const isHourYin = hourGan && p.yinGan === hourGan;

        // 状态标记（击刑/入墓/刑+墓都不显示文字，改为字变色）
        let statusTag = '';

        // ── 八神颜色（值符不绿色） ──
        const shenColor = C_DEFAULT;
        const shenWeight = '500';

        // ── 九星颜色（值符星绿色） ──
        const xingColor = isZhiFu ? C_ZHIFU : C_DEFAULT;
        const xingWeight = isZhiFu ? '700' : '500';

        // ── 八门颜色 ──
        let menColor = C_DEFAULT;
        let menWeight = '500';
        if (isZhiShi) { menColor = C_ZHISHI; menWeight = '700'; }
        if (hasMenPo) { menColor = C_MENPO; menWeight = '700'; }

        // ── 天盘干逐字渲染 ──
        let tianHtml = '';
        tianGanArr.filter(Boolean).forEach(g => {
            let c = C_DEFAULT, w = '400';
            if (jiXingTianSet.has(g)) { c = C_JIXING; w = '700'; }
            else if (ruMuTianSet.has(g)) { c = C_RUMU; w = '700'; }
            tianHtml += `<span style="color:${c};font-weight:${w};">${g}</span>`;
        });

        // ── 地盘干逐字渲染 ──
        let diHtml = '';
        diGanArr.filter(Boolean).forEach(g => {
            let c = C_DIGAN, w = '400';
            if (jiXingDiSet.has(g)) { c = C_JIXING; w = '700'; }
            else if (ruMuDiSet.has(g)) { c = C_RUMU; w = '700'; }
            diHtml += `<span style="color:${c};font-weight:${w};">${g}</span>`;
        });

        // ── 隐干颜色 ──
        const yinColor = C_YINGAN;
        const yinWeight = '400';

        // 宫号（居中叠加层）
        const gongLabel = `${gongNum}·${baguaSimple[p.bagua]||p.bagua}`;

        // 统一字号
        const FS = '0.8rem';
        // 外层：统一白色背景
        html += `<div style="background:${bg};aspect-ratio:1;position:relative;color:${C_DEFAULT};padding:8px 10px;display:flex;flex-direction:column;justify-content:space-between;box-sizing:border-box;">`;

        // ── Row 1: 左─八神○  右─🐎天盘干 ──  ○行内在八神右侧
        html += `<div style="display:flex;justify-content:space-between;align-items:center;">`;
        // 左：八神 + ○
        html += `<span style="color:${shenColor};font-weight:${shenWeight};font-size:${FS};white-space:nowrap;">`;
        if (p.shenFull) html += `${p.shenFull}`;
        if (p.isKong) html += `<span style="color:${C_KONG};font-size:0.78rem;font-weight:700;margin-left:2px;">○</span>`;
        html += `</span>`;
        // 右：🐎 + 天盘干
        html += `<span style="display:inline-flex;align-items:center;gap:2px;font-size:${FS};white-space:nowrap;">`;
        if (p.isMa) html += `<span style="color:${C_MAHORSE};font-size:0.72rem;">🐎</span>`;
        if (tianHtml) html += tianHtml;
        html += `</span>`;
        html += `</div>`;

        // ── Row 2: 左─九星  右─地盘干 ──
        html += `<div style="display:flex;justify-content:space-between;align-items:center;">`;
        // 左：九星
        html += `<span style="color:${xingColor};font-weight:${xingWeight};font-size:${FS};white-space:nowrap;">`;
        const xingDisplay = xingFullArr.length > 1 ? xingArr.filter(Boolean).join("") : xingFullArr.filter(Boolean).join("");
        if (xingDisplay) html += `${xingDisplay}`;
        html += `</span>`;
        // 右：地盘干
        html += `<span style="font-size:${FS};white-space:nowrap;">`;
        if (diHtml) html += diHtml;
        html += `</span>`;
        html += `</div>`;

        // ── Row 3: 左─八门+状态  右─隐干 ──
        html += `<div style="display:flex;justify-content:space-between;align-items:center;">`;
        // 左：八门 + 状态标记
        html += `<span style="white-space:nowrap;display:inline-flex;align-items:center;">`;
        if (p.menFull) html += `<span style="color:${menColor};font-weight:${menWeight};font-size:${FS};">${p.menFull}</span>`;
        if (statusTag) html += statusTag;
        html += `</span>`;
        // 右：隐干
        html += `<span style="color:${yinColor};font-weight:${yinWeight};font-size:${FS};white-space:nowrap;">`;
        if (p.yinGan) html += `${p.yinGan}`;
        html += `</span>`;
        html += `</div>`;

        // ── 宫号居中叠加 ──
        html += `<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:0.55rem;color:#d0d0d0;font-weight:400;pointer-events:none;">${gongLabel}</div>`;

        html += `</div>`;
    }
    html += `</div>`;

    // ═══ 图例 ═══
    html += `<div style="display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:14px;font-size:0.72rem;color:var(--text-3);justify-content:center;align-items:center;">`;
    html += `<span><span style="color:${C_ZHISHI};font-weight:700;">值使</span></span>`;
    html += `<span><span style="color:${C_MENPO};font-weight:700;">门迫</span></span>`;
    html += `<span><span style="color:${C_JIXING};font-weight:700;">击刑</span></span>`;
    html += `<span><span style="color:${C_RUMU};font-weight:700;">入墓</span></span>`;
    html += `<span><span style="color:${C_KONG};">○</span>空亡</span>`;
    html += `<span><span style="color:${C_MAHORSE};">🐎</span>马星</span>`;
    html += `</div>`;

    html += `<div style="text-align:center;font-size:0.72rem;color:var(--text-3);margin-top:10px;">⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议</div>`;
    html += `</div>`;
    return html;
}


// ═══════════════════════════════════════════════════════════════
// 八字排盘（免费版）— 问真风格表单
// ═══════════════════════════════════════════════════════════════

// 城市经纬度数据（与后端 bazi_engine.py CITY_LNG 同步经度，前端额外增加纬度）
const WZ_CITY_LNG = {
    '北京':{lng:116.4,lat:39.9},'上海':{lng:121.5,lat:31.2},'天津':{lng:117.2,lat:39.1},'重庆':{lng:106.5,lat:29.6},
    '广州':{lng:113.3,lat:23.1},'深圳':{lng:114.1,lat:22.5},'杭州':{lng:120.2,lat:30.3},'南京':{lng:118.8,lat:32.1},
    '武汉':{lng:114.3,lat:30.6},'成都':{lng:104.1,lat:30.6},'西安':{lng:108.9,lat:34.3},'长沙':{lng:113.0,lat:28.2},
    '郑州':{lng:113.7,lat:34.8},'济南':{lng:117.0,lat:36.7},'沈阳':{lng:123.4,lat:41.8},'哈尔滨':{lng:126.6,lat:45.8},
    '长春':{lng:125.3,lat:43.9},'昆明':{lng:102.7,lat:25.0},'贵阳':{lng:106.7,lat:26.6},'南宁':{lng:108.3,lat:22.8},
    '福州':{lng:119.3,lat:26.1},'合肥':{lng:117.3,lat:31.8},'南昌':{lng:115.9,lat:28.7},'太原':{lng:112.5,lat:37.9},
    '石家庄':{lng:114.5,lat:38.0},'兰州':{lng:103.8,lat:36.1},'西宁':{lng:101.8,lat:36.6},'银川':{lng:106.3,lat:38.5},
    '呼和浩特':{lng:111.7,lat:40.8},'乌鲁木齐':{lng:87.6,lat:43.8},'拉萨':{lng:91.1,lat:29.7},'海口':{lng:110.3,lat:20.0},
    '苏州':{lng:120.6,lat:31.3},'无锡':{lng:120.3,lat:31.6},'宁波':{lng:121.6,lat:29.9},'温州':{lng:120.7,lat:28.0},
    '东莞':{lng:113.7,lat:23.0},'佛山':{lng:113.1,lat:23.0},'珠海':{lng:113.6,lat:22.3},'厦门':{lng:118.1,lat:24.5},
    '青岛':{lng:120.4,lat:36.1},'大连':{lng:121.6,lat:38.9},'烟台':{lng:121.4,lat:37.5},'泉州':{lng:118.6,lat:24.9},
    '常州':{lng:119.9,lat:31.8},'徐州':{lng:117.2,lat:34.3},'绍兴':{lng:120.6,lat:30.0},'嘉兴':{lng:120.7,lat:30.8},
    '金华':{lng:119.6,lat:29.1},'台州':{lng:121.4,lat:28.7},'中山':{lng:113.4,lat:22.5},'惠州':{lng:114.4,lat:23.1},
    '汕头':{lng:116.7,lat:23.4},'湛江':{lng:110.4,lat:21.3},'桂林':{lng:110.3,lat:25.3},'三亚':{lng:109.5,lat:18.3},
    '洛阳':{lng:112.4,lat:34.6},'潍坊':{lng:119.1,lat:36.7},'保定':{lng:115.5,lat:38.9},'唐山':{lng:118.2,lat:39.6},
    '邯郸':{lng:114.5,lat:36.6},'秦皇岛':{lng:119.6,lat:39.9},'包头':{lng:109.8,lat:40.7},'大庆':{lng:125.1,lat:46.6},
    '齐齐哈尔':{lng:123.9,lat:47.4},'吉林':{lng:126.5,lat:43.8},'鞍山':{lng:123.0,lat:41.1},'抚顺':{lng:123.9,lat:41.9},
    '宜昌':{lng:111.3,lat:30.7},'襄阳':{lng:112.1,lat:32.0},'岳阳':{lng:113.1,lat:29.4},'常德':{lng:111.7,lat:29.0},
    '绵阳':{lng:104.7,lat:31.5},'宜宾':{lng:104.6,lat:28.8},'遵义':{lng:106.9,lat:27.7},'曲靖':{lng:103.8,lat:25.5},
    '大理':{lng:100.2,lat:25.6},'丽江':{lng:100.2,lat:26.9},'咸阳':{lng:108.7,lat:34.3},'宝鸡':{lng:107.1,lat:34.4},
    '天水':{lng:105.7,lat:34.6},'广东':{lng:113.3,lat:23.1},'浙江':{lng:120.2,lat:30.3},'江苏':{lng:118.8,lat:32.1},
    '山东':{lng:117.0,lat:36.7},'河南':{lng:113.7,lat:34.8},'河北':{lng:114.5,lat:38.0},'湖南':{lng:113.0,lat:28.2},
    '湖北':{lng:114.3,lat:30.6},'四川':{lng:104.1,lat:30.6},'福建':{lng:119.3,lat:26.1},'安徽':{lng:117.3,lat:31.8},
    '江西':{lng:115.9,lat:28.7},'陕西':{lng:108.9,lat:34.3},'山西':{lng:112.5,lat:37.9},'辽宁':{lng:123.4,lat:41.8},
    '黑龙江':{lng:126.6,lat:45.8},'云南':{lng:102.7,lat:25.0},'贵州':{lng:106.7,lat:26.6},'广西':{lng:108.3,lat:22.8},
    '甘肃':{lng:103.8,lat:36.1},'海南':{lng:110.3,lat:20.0},'内蒙古':{lng:111.7,lat:40.8},'新疆':{lng:87.6,lat:43.8},
    '西藏':{lng:91.1,lat:29.7},'青海':{lng:101.8,lat:36.6},'宁夏':{lng:106.3,lat:38.5}
};

// ── 性别选择 ──
function wzSelectGender(el) {
    document.querySelectorAll('.wz-gender-btn').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('baziGender').value = el.dataset.value;
}

// ── 历法选择 ──
function wzSelectCal(el) {
    document.querySelectorAll('.wz-cal-btn').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    const calType = el.dataset.value;
    document.getElementById('baziCalType').value = calType;

    // 根据历法模式切换表单区域
    const dateGroup = document.getElementById('baziYear')?.closest('.wz-form-group');
    const addrGroup = document.getElementById('wzAddrGroup');
    const siziGroup = document.getElementById('wzSiziGroup');
    const advancedGroup = document.getElementById('wzAdvancedGroup');

    if (calType === '四柱') {
        // 四柱模式：隐藏日期/地址/高级选项，显示四柱输入
        if (dateGroup) dateGroup.style.display = 'none';
        if (addrGroup) addrGroup.style.display = 'none';
        if (advancedGroup) advancedGroup.style.display = 'none';
        if (siziGroup) siziGroup.style.display = '';
    } else if (calType === '农历') {
        // 农历模式：显示日期/地址/高级选项，隐藏四柱输入
        if (dateGroup) dateGroup.style.display = '';
        if (addrGroup) addrGroup.style.display = '';
        if (advancedGroup) advancedGroup.style.display = '';
        if (siziGroup) siziGroup.style.display = 'none';
        wzUpdateLunarMonthDay();
    } else {
        // 公历模式：显示日期/地址/高级选项，隐藏四柱输入
        if (dateGroup) dateGroup.style.display = '';
        if (addrGroup) addrGroup.style.display = '';
        if (advancedGroup) advancedGroup.style.display = '';
        if (siziGroup) siziGroup.style.display = 'none';
        wzInitSolarMonthDay();
    }
}

// ── 农历月份日期适配 ──
window._lunarMonthsData = null;
window._lunarDayNames = null;

async function wzUpdateLunarMonthDay() {
    const year = parseInt(document.getElementById('baziYear').value);
    if (!year) return;
    try {
        const r = await fetch('/api/bazi/lunar-month-data', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({year: year})
        });
        const data = await r.json();
        if (!data.success) { console.error('Lunar data error:', data.error); return; }

        // 缓存数据
        window._lunarMonthsData = data.months;
        window._lunarDayNames = data.dayNames;

        // 重建月份选择器（农历名称）
        const monthSel = document.getElementById('baziMonth');
        const prevMonth = monthSel.value;
        monthSel.innerHTML = '';
        data.months.forEach(m => {
            const opt = document.createElement('option');
            opt.value = String(m.value).padStart(2, '0');
            opt.textContent = m.label;
            if (m.isLeap) opt.dataset.isLeap = 'true';
            monthSel.appendChild(opt);
        });

        // 更新日期为第一个月的天数
        if (data.months.length > 0) {
            wzUpdateLunarDays(data.months[0].dayCount, data.dayNames);
        }
    } catch(e) {
        console.error('Failed to fetch lunar data:', e);
    }
}

function wzUpdateLunarDays(dayCount, dayNames) {
    const daySel = document.getElementById('baziDay');
    const prevDay = daySel.value;
    daySel.innerHTML = '';
    for (let d = 1; d <= dayCount; d++) {
        const opt = document.createElement('option');
        opt.value = String(d).padStart(2, '0');
        opt.textContent = dayNames[d] || d;
        daySel.appendChild(opt);
    }
    // 恢复选中日
    if (parseInt(prevDay) <= dayCount) {
        daySel.value = prevDay;
    }
}

function wzInitSolarMonthDay() {
    // 恢复公历月份1-12
    const monthSel = document.getElementById('baziMonth');
    const curMonth = monthSel.value;
    monthSel.innerHTML = '';
    for (let m = 1; m <= 12; m++) {
        const opt = document.createElement('option');
        opt.value = String(m).padStart(2, '0');
        opt.textContent = m;
        monthSel.appendChild(opt);
    }
    if (curMonth) monthSel.value = curMonth;
    wzUpdateDays();
}

// ── 日期选择器初始化 ──
function wzInitDatePicker() {
    const now = new Date();
    const curYear = now.getFullYear();
    const curMonth = now.getMonth() + 1;
    const curDay = now.getDate();

    // 年份：1920-当前年
    const yearSel = document.getElementById('baziYear');
    for (let y = curYear; y >= 1920; y--) {
        const opt = document.createElement('option');
        opt.value = y; opt.textContent = y;
        if (y === curYear) opt.selected = true;
        yearSel.appendChild(opt);
    }

    // 月份：1-12
    const monthSel = document.getElementById('baziMonth');
    for (let m = 1; m <= 12; m++) {
        const opt = document.createElement('option');
        opt.value = String(m).padStart(2, '0'); opt.textContent = m;
        if (m === curMonth) opt.selected = true;
        monthSel.appendChild(opt);
    }

    // 分钟：0-59（1分钟精度）
    const minSel = document.getElementById('baziMinute');
    if (minSel) {
        const curMinute = now.getMinutes();
        for (let m = 0; m <= 59; m++) {
            const opt = document.createElement('option');
            opt.value = String(m).padStart(2, '0');
            opt.textContent = m;
            if (m === curMinute) opt.selected = true;
            minSel.appendChild(opt);
        }
    }

    // 日期：根据年月动态更新
    wzUpdateDays();

    // 默认选中当前日
    setTimeout(() => {
        const daySel = document.getElementById('baziDay');
        if (daySel && curDay <= daySel.options.length) {
            daySel.value = String(curDay).padStart(2, '0');
        }
    }, 10);
}

function wzUpdateDays() {
    const yearSel = document.getElementById('baziYear');
    const monthSel = document.getElementById('baziMonth');
    const daySel = document.getElementById('baziDay');
    if (!yearSel || !monthSel || !daySel) return;

    const y = parseInt(yearSel.value);
    const m = parseInt(monthSel.value);
    const daysInMonth = new Date(y, m, 0).getDate();
    const prevDay = daySel.value;

    daySel.innerHTML = '';
    for (let d = 1; d <= daysInMonth; d++) {
        const opt = document.createElement('option');
        opt.value = String(d).padStart(2, '0'); opt.textContent = d;
        daySel.appendChild(opt);
    }
    // 恢复之前的选中日
    if (parseInt(prevDay) <= daysInMonth) {
        daySel.value = prevDay;
    }
}

// ── 年份/月份变更处理 ──
function wzOnDateChange() {
    const calType = document.getElementById('baziCalType').value;
    if (calType === '农历') {
        wzUpdateLunarMonthDay();
    } else {
        wzUpdateDays();
    }
    wzUpdateSolarTimeDisplay();
}

function wzOnMonthChange() {
    const calType = document.getElementById('baziCalType').value;
    if (calType === '农历' && window._lunarMonthsData) {
        const monthSel = document.getElementById('baziMonth');
        const selectedVal = monthSel.value;
        const selectedOpt = monthSel.options[monthSel.selectedIndex];
        const isLeap = selectedOpt && selectedOpt.dataset.isLeap === 'true';
        // 找到对应月份的天数
        const mInfo = window._lunarMonthsData.find(m => {
            return String(m.value).padStart(2, '0') === selectedVal && m.isLeap === isLeap;
        });
        if (mInfo) {
            wzUpdateLunarDays(mInfo.dayCount, window._lunarDayNames || {});
        }
    } else {
        wzUpdateDays();
    }
    wzUpdateSolarTimeDisplay();
}

// ── 出生地搜索 ──
let wzAddrSelected = '';
let wzSelectedLng = 0;
let wzSelectedLat = 0;
function wzSearchCity(keyword) {
    const dropdown = document.getElementById('baziAddrDropdown');
    if (!keyword || keyword.trim().length === 0) {
        dropdown.classList.remove('show');
        dropdown.innerHTML = '';
        return;
    }
    const kw = keyword.trim();
    const matches = [];
    for (const [city, data] of Object.entries(WZ_CITY_LNG)) {
        if (city.includes(kw)) {
            matches.push({city, lng: data.lng, lat: data.lat});
            if (matches.length >= 10) break;
        }
    }
    if (matches.length === 0) {
        dropdown.classList.remove('show');
        dropdown.innerHTML = '';
        return;
    }
    dropdown.innerHTML = matches.map(m =>
        `<div class="wz-addr-item" onclick="wzSelectCity('${m.city}',${m.lng},${m.lat})">
            <span>${m.city}</span>
            <span class="wz-addr-lng">E${m.lng}°</span>
        </div>`
    ).join('');
    dropdown.classList.add('show');
}

function wzSelectCity(city, lng, lat) {
    const addrInput = document.getElementById('baziBirthAddr');
    addrInput.value = city;
    wzAddrSelected = city;
    wzSelectedLng = lng;
    wzSelectedLat = lat;
    document.getElementById('baziAddrDropdown').classList.remove('show');

    // 显示经纬度信息
    const infoEl = document.getElementById('baziAddrInfo');
    infoEl.style.display = 'flex';
    document.getElementById('baziAddrLng').textContent = `经度：E${lng}° 纬度：N${lat}°`;

    // 更新真太阳时显示
    wzUpdateSolarTimeDisplay();
}

// ── 真太阳时计算与显示 ──
function wzCalcTrueSolarTime(year, month, day, hour, minute, longitude) {
    // 均时差 (Equation of Time) 近似公式（与 bazi_engine.py 一致）
    const dt = new Date(year, month - 1, day);
    const start = new Date(year, 0, 0);
    const dayOfYear = Math.floor((dt - start) / 86400000);
    const b = 2.0 * Math.PI / 365.0 * (dayOfYear - 81);
    const eotMin = 9.87 * Math.sin(2*b) - 7.53 * Math.cos(b) - 1.5 * Math.sin(b);
    // 经度修正
    const lngOffsetMin = (longitude - 120.0) * 4.0;
    const totalOffsetMin = lngOffsetMin + eotMin;
    // 应用修正
    const solarDate = new Date(year, month - 1, day, hour, minute + totalOffsetMin);
    return solarDate;
}

function wzUpdateSolarTimeDisplay() {
    const useSolarTime = document.getElementById('baziUseSolarTime');
    if (!useSolarTime || !useSolarTime.checked) {
        document.getElementById('baziAddrSolar').textContent = '真太阳时：关闭';
        return;
    }
    const y = parseInt(document.getElementById('baziYear').value);
    const m = parseInt(document.getElementById('baziMonth').value);
    const d = parseInt(document.getElementById('baziDay').value);
    const h = parseInt(document.getElementById('baziBirthHour').value || '12');
    const min = parseInt(document.getElementById('baziMinute').value || '0');
    if (!y || !m || !d || !wzSelectedLng) {
        document.getElementById('baziAddrSolar').textContent = '真太阳时：--';
        return;
    }
    const solarDt = wzCalcTrueSolarTime(y, m, d, h, min, wzSelectedLng);
    const pad = (n) => String(n).padStart(2, '0');
    document.getElementById('baziAddrSolar').textContent =
        `真太阳时：${solarDt.getFullYear()}-${pad(solarDt.getMonth()+1)}-${pad(solarDt.getDate())} ${pad(solarDt.getHours())}:${pad(solarDt.getMinutes())}`;
}

// 点击外部关闭下拉
document.addEventListener('click', function(e) {
    const dropdown = document.getElementById('baziAddrDropdown');
    if (dropdown && !e.target.closest('.wz-addr-wrap')) {
        dropdown.classList.remove('show');
    }
});

// ── 夏令时开关 ──
function wzToggleDst(el) {
    document.getElementById('dstHint').textContent = el.checked ? '开' : '关';
}

// ── 早晚子时开关 ──
function wzToggleNightZi(el) {
    document.getElementById('nightZiHint').textContent = el.checked ? '子时换日' : '夜子时';
}

// ── 保存案例开关 ──
function wzToggleSaveCase(el) {
    document.getElementById('saveCaseHint').textContent = el.checked ? '保存' : '不保存';
}

// ── 即时起局 ──
async function wzInstantPaipan() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    const day = now.getDate();
    const hour = now.getHours();
    const minute = now.getMinutes();

    // 填入年月日
    const yearSel = document.getElementById('baziYear');
    if (yearSel) yearSel.value = String(year);
    const monthSel = document.getElementById('baziMonth');
    if (monthSel) monthSel.value = String(month).padStart(2, '0');

    // 农历模式需要先刷新月份
    const calType = document.getElementById('baziCalType').value;
    if (calType === '农历') {
        await wzUpdateLunarMonthDay();
    } else {
        wzUpdateDays();
    }

    const daySel = document.getElementById('baziDay');
    if (daySel) daySel.value = String(day).padStart(2, '0');

    // 映射小时到时辰
    const hourSel = document.getElementById('baziBirthHour');
    if (hourSel) {
        let shiValue = '';
        if (hour === 23 || hour === 0) shiValue = '23';
        else if (hour >= 1 && hour < 3) shiValue = '01';
        else if (hour >= 3 && hour < 5) shiValue = '03';
        else if (hour >= 5 && hour < 7) shiValue = '05';
        else if (hour >= 7 && hour < 9) shiValue = '07';
        else if (hour >= 9 && hour < 11) shiValue = '09';
        else if (hour >= 11 && hour < 13) shiValue = '11';
        else if (hour >= 13 && hour < 15) shiValue = '13';
        else if (hour >= 15 && hour < 17) shiValue = '15';
        else if (hour >= 17 && hour < 19) shiValue = '17';
        else if (hour >= 19 && hour < 21) shiValue = '19';
        else if (hour >= 21 && hour < 23) shiValue = '21';
        hourSel.value = shiValue;
    }

    // 填入分钟
    const minSel = document.getElementById('baziMinute');
    if (minSel) minSel.value = String(minute).padStart(2, '0');

    // 显示当前时间
    const preview = document.getElementById('wzInstantPreview');
    const timeStr = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')} ${String(hour).padStart(2,'0')}:${String(minute).padStart(2,'0')}`;

    // 获取四柱预览
    try {
        const hh = hourSel ? hourSel.value : String(hour).padStart(2, '0');
        const mm = String(minute).padStart(2, '0');
        const birthTime = `${year}${String(month).padStart(2,'0')}${String(day).padStart(2,'0')}${hh}${mm}`;
        const r = await fetch('/api/bazi/paipan', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: '', gender: '男', calType: '公历',
                birthTime: birthTime, birthAddr: '',
                isDst: false, nightZiMode: '夜子时不换日'
            })
        });
        const data = await r.json();
        if (data.success && data.four_pillars) {
            const p = data.four_pillars;
            const yz = `${p.year.gan}${p.year.zhi}`;
            const mz = `${p.month.gan}${p.month.zhi}`;
            const dz = `${p.day.gan}${p.day.zhi}`;
            const hz = p.hour ? `${p.hour.gan}${p.hour.zhi}` : '';
            const lunarStr = data.lunar_str || '';
            preview.innerHTML = `<span style="font-size:1.25rem;font-weight:700;">${yz} ${mz} ${dz} ${hz}</span><br><span style="font-size:0.6875rem;letter-spacing:0;">${lunarStr ? '农历：' + lunarStr + '  ' : ''}公历：${timeStr}</span>`;
            preview.style.display = 'block';
        } else {
            preview.textContent = `公历：${timeStr}`;
            preview.style.display = 'block';
        }
    } catch(e) {
        preview.textContent = `公历：${timeStr}`;
        preview.style.display = 'block';
    }
}

// ── 真太阳时开关 ──
function wzToggleSolarTime(el) {
    document.getElementById('solarTimeHint').textContent = el.checked ? '开' : '关';
    // 更新真太阳时信息显示
    const infoEl = document.getElementById('baziAddrInfo');
    if (infoEl && infoEl.style.display !== 'none') {
        wzUpdateSolarTimeDisplay();
    }
}

// ── 提交排盘 ──
async function baziFreePaipan() {
    const name = (document.getElementById("baziName").value || '').trim();
    const gender = document.getElementById("baziGender").value;
    const calType = document.getElementById("baziCalType").value;
    const birthAddr = document.getElementById("baziBirthAddr").value;
    const isDst = document.getElementById("baziIsDst").checked;
    const nightZiMode = document.getElementById("baziNightZi").checked ? '子时换日' : '夜子时不换日';
    const useSolarTime = document.getElementById("baziUseSolarTime").checked;

    let birthTime = '';
    let siziPillars = null;
    let isLeapMonth = false;

    if (calType === '四柱') {
        // 四柱直接输入模式
        const sy = (document.getElementById("siziYear").value || '').trim();
        const sm = (document.getElementById("siziMonth").value || '').trim();
        const sd = (document.getElementById("siziDay").value || '').trim();
        const sh = (document.getElementById("siziHour").value || '').trim();
        if (!sy || !sm || !sd) {
            alert("请至少输入年柱、月柱、日柱");
            return;
        }
        siziPillars = { year: sy, month: sm, day: sd, hour: sh || '' };
    } else {
        // 公历/农历模式
        const year = document.getElementById("baziYear").value;
        const month = document.getElementById("baziMonth").value;
        const day = document.getElementById("baziDay").value;
        const birthHour = document.getElementById("baziBirthHour").value;
        const minute = document.getElementById("baziMinute").value;
        if (!year || !month || !day) { alert("请选择出生日期"); return; }
        const hh = birthHour || '12';
        birthTime = `${year}${month}${day}${hh}${minute || '00'}`;

        // 农历闰月检测
        if (calType === '农历') {
            const monthSel = document.getElementById('baziMonth');
            const selectedOpt = monthSel.options[monthSel.selectedIndex];
            isLeapMonth = selectedOpt && selectedOpt.dataset.isLeap === 'true';
        }
    }

    // 保存参数到 sessionStorage，跳转到独立结果页
    sessionStorage.setItem("xc_bazi_params", JSON.stringify({
        name, gender, calType, birthTime, birthAddr,
        isDst, nightZiMode, siziPillars,
        useSolarTime, isLeapMonth
    }));
    window.location.href = "/bazi";
}

// ── 初始化 ──
document.addEventListener('DOMContentLoaded', function() {
    wzInitDatePicker();
});
