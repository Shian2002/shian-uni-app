// ═══════════════════════════════════════════════
// 通用工具（核心由 api-client.js 提供，此处仅保留页面扩展）
// $, getCSRF, apiFetch, esc, escapeHtml, sanitizeData 已在 api-client.js 中定义
// ═══════════════════════════════════════════════

let currentUser=null;
let currentPanel='paipan';
let currentHistoryType='all';
let pendingDeleteId=null;
let historyPage=1;
let historyHasMore=false;

// ═══════════════════════════════════════════════
// 面板切换
// ═══════════════════════════════════════════════
function switchPanel(name){
    currentPanel=name;
    document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
    $(`panel-${name}`).classList.add('active');
    document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
    document.querySelector(`[data-panel="${name}"]`).classList.add('active');
    if(name==='community'){loadCommunityPosts();}
    if(name==='masters'){loadMasters();}
    if(name==='vip'){loadMembership();loadPointLog();}
    if(name==='paid'){loadPaidContents();}
    switchHistoryTab(name);
    location.hash=name;
}

// 支持 hash 路由自动切换面板
const ALL_PANELS=['paipan','qimen','liuyao','meihua','ziwei','zeji','huangli','taluo','community','masters','vip','paid'];
(function(){
    const hash=location.hash.replace('#','');
    if(hash==='profile'){location.href='/profile';return;}
    if(ALL_PANELS.includes(hash)){
        switchPanel(hash);
    }
})();
window.addEventListener('hashchange',function(){
    const hash=location.hash.replace('#','');
    if(ALL_PANELS.includes(hash)) switchPanel(hash);
});

function switchHistoryTab(type){
    currentHistoryType=type;
    document.querySelectorAll('.htab').forEach(t=>t.classList.toggle('active',t.dataset.type===type));
    loadHistory(type);
}
// ═══════════════════════════════════════════════
// 主题切换
// ═══════════════════════════════════════════════
function toggleTheme(){
    const html=document.documentElement;
    const isDark=html.dataset.theme==='dark';
    html.dataset.theme=isDark?'light':'dark';
    $('themeLabel').textContent=isDark?'亮色':'暗色';
    localStorage.setItem('xc_theme',html.dataset.theme);
}

// ═══════════════════════════════════════════════
// 侧边栏移动端
// ═══════════════════════════════════════════════
function toggleSidebar(){
    $('sidebar').classList.toggle('open');
    $('sidebarOverlay').classList.toggle('show');
}
function closeSidebar(){
    $('sidebar').classList.remove('open');
    $('sidebarOverlay').classList.remove('show');
}

// ═══════════════════════════════════════════════
// 模态框
// ═══════════════════════════════════════════════
function showModal(id){document.querySelectorAll('.modal-overlay').forEach(m=>m.classList.remove('show'));$(id).classList.add('show');}
function hideModal(id){$(id).classList.remove('show');}

// ═══════════════════════════════════════════════
// 认证
// ═══════════════════════════════════════════════
async function checkAuth(){
    try{
        const r=await apiFetch('/api/me');
        const d=await r.json();
        if(d.guest){currentUser=null;renderUserArea();}
        else{currentUser=d;renderUserArea();loadHistory(currentHistoryType);loadCollections();loadProfiles();renderAccountInfo();}
    }catch(e){console.error('checkAuth error:',e);currentUser=null;renderUserArea();}
}

function renderUserArea(){
    const el=$('sidebarUser');
    if(currentUser){
        el.innerHTML=`<div class="user-name">${currentUser.username}</div>
            <a href="/profile" class="btn-profile-link">个人中心</a>
            <button class="btn-logout" onclick="doLogout()">退出登录</button>`;
    }else{
        el.innerHTML=`<button class="btn-auth primary" onclick="showModal('loginModal')">登录</button>
            <button class="btn-auth" onclick="showModal('registerModal')">注册</button>`;
    }
}

async function doLogin(){
    const u=$('loginUser').value.trim(),p=$('loginPass').value;
    $('loginError').textContent='';
    if(!u||!p){$('loginError').textContent='请填写用户名和密码';return;}
    try{
        const r=await apiFetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
        const d=await r.json();
        if(d.error){$('loginError').textContent=d.error;return;}
        currentUser=d;hideModal('loginModal');renderUserArea();loadHistory(currentHistoryType);
        $('loginUser').value='';$('loginPass').value='';
    }catch(e){$('loginError').textContent='网络错误，请重试';}
}

async function doRegister(){
    const u=$('regUser').value.trim(),p=$('regPass').value,p2=$('regPass2').value;
    $('regError').textContent='';
    if(!u||!p){$('regError').textContent='请填写用户名和密码';return;}
    if(u.length<2||u.length>20){$('regError').textContent='用户名需2-20个字符';return;}
    if(p.length<6){$('regError').textContent='密码至少6个字符';return;}
    if(p!==p2){$('regError').textContent='两次密码不一致';return;}
    try{
        const r=await apiFetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
        const d=await r.json();
        if(d.error){$('regError').textContent=d.error;return;}
        currentUser=d;hideModal('registerModal');renderUserArea();loadHistory(currentHistoryType);
        $('regUser').value='';$('regPass').value='';$('regPass2').value='';
    }catch(e){$('regError').textContent='网络错误，请重试';}
}

async function doLogout(){
    try{await apiFetch('/api/logout',{method:'POST'});}catch(e){}
    currentUser=null;renderUserArea();$('historyList').innerHTML='';
}

// ═══════════════════════════════════════════════
// 历史记录
// ═══════════════════════════════════════════════
async function loadHistory(type,page){
    if(!currentUser){
        $('historyList').innerHTML=`<div style="padding:16px 20px;color:var(--text-3);font-size:0.75rem;text-align:center;">登录后查看历史记录</div>`;
        return;
    }
    // 收藏tab特殊处理
    if(type==='collection'){await loadCollections();loadCollectionHistory();return;}
    page=page||1;
    try{
        const typeParam=type==='all'?'':type;
        const r=await fetch(`/api/records?app_type=${typeParam}&page=${page}&per_page=20`);
        const d=await r.json();
        const el=$('historyList');
        historyPage=page;
        historyHasMore=d.has_next;
        if(!d.records||!d.records.length){
            if(page===1) el.innerHTML=`<div style="padding:12px 20px;color:var(--text-3);font-size:0.75rem;">暂无记录</div>`;
            return;
        }
        let html=d.records.map(rec=>{
            const t=rec.created_at?new Date(rec.created_at).toLocaleString('zh-CN',{month:'numeric',day:'numeric',hour:'numeric',minute:'numeric'}):'';
            const isCollected=(userCollections||[]).some(c=>c.target_id===rec.id);
            return `<div class="history-item" onclick="viewRecord(${rec.id},'${rec.app_type||type}')">
                <div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-right:60px;">${escapeHtml(rec.question)}</div>
                <div class="hi-time">${t}</div>
                <button class="collection-star${isCollected?' collected':''}" onclick="event.stopPropagation();toggleCollection(${rec.id},this)" title="收藏">${isCollected?'⭐':'☆'}</button>
                <button class="hi-del" title="删除" onclick="event.stopPropagation();requestDelete(${rec.id})">✕</button>
            </div>`;
        }).join('');
        if(d.has_next){
            html+=`<div style="padding:8px 20px;text-align:center;"><button class="btn btn-ghost" style="font-size:0.75rem;" onclick="loadHistory('${type}',${page+1})">加载更多...</button></div>`;
        }
        if(page>1) el.innerHTML+=html; else el.innerHTML=html;
    }catch(e){console.error('loadHistory error:',e);}
}

async function viewRecord(id,type){
    try{
        const r=await fetch(`/api/records/${id}`);
        const d=await r.json();
        if(d.error)return;
        switchPanel(type);
        // 显示跟进区域
        let followupArea=document.getElementById('followupArea_'+id);
        if(!followupArea){
            followupArea=document.createElement('div');
            followupArea.id='followupArea_'+id;
            // 找到当前面板的最后一个card后面插入
            const panel=$(`panel-${type}`);
            if(panel){
                const wrapper=document.createElement('div');
                wrapper.style.cssText='margin-top:16px;';
                wrapper.innerHTML=`<div class="card"><div class="card-header"><span class="ch-icon">📝</span><span class="ch-title">问事跟进</span></div><div class="card-body"><div id="followupArea_${id}"></div></div></div>`;
                // 移除之前的跟进区域
                const prev=panel.querySelector('.followup-wrapper');
                if(prev) prev.remove();
                wrapper.classList.add('followup-wrapper');
                panel.appendChild(wrapper);
            }
        }
        loadFollowups(id,'followupArea_'+id);

        if(type==='qimen'){
            $('qimenResult').style.display='block';
            $('qimenResultHtml').textContent=d.result_html||'（无结果）';
            if(d.qimen){$('qimenChart').style.display='block';renderQimenChart(d.qimen);}
            else{$('qimenChart').style.display='none';}
        }else if(type==='paipan'){
            // paipan 记录显示在日志区
            $('paipanLogBox').textContent=d.result_html||'（无结果）';
            $('paipanLogBox').classList.add('show');
            $('paipanStatusBar').textContent='✅ 历史记录';$('paipanStatusBar').className='status-bar ok';
        }else{
            // 其他工具面板：显示结果
            const resultEl=$(`${type}Result`);
            const resultHtml=$(`${type}ResultHtml`);
            if(resultEl&&resultHtml){
                resultEl.style.display='block';
                resultHtml.textContent=d.result_html||d.result||'（无结果）';
            }
        }
    }catch(e){console.error('viewRecord error:',e);}
}

// ═══════════════════════════════════════════════
// 奇门盘可视化渲染
// ═══════════════════════════════════════════════
function renderQimenChart(data){
    const el=$('qimenChart');
    if(!data){el.style.display='none';return;}
    el.style.display='block';

    const fp=data.fourPillars||{};
    const palaces=data.palaces||data.gong||data.gongWei||[];
    const dayGan=data.dayGan||'';
    const hourGan=data.hourGan||'';
    const luoOrder=[4,9,2,3,5,7,8,1,6];

    // 颜色规则：值符=绿, 值使=绿, 击刑=紫, 门迫=红, 刑+墓=蓝
    const C_ZHIFU='#27AE60';const C_ZHISHI='#27AE60';const C_RUMU='#8B4513';
    const C_JIXING='#9B59B6';const C_MENPO='#E74C3C';const C_XINGMU='#2980B9';
    const C_DEFAULT='#222';const C_KONG='#444';const C_RIGAN='#E74C3C';
    const C_DIGAN='#555';const C_YINGAN='#AAA';const C_MAHORSE='#D4A017';

    const zhiFuStar=data.zhiFuStar||'';
    const zhiShiMen=data.zhiShiMen||'';
    const baguaSimple={'坎':'坎','坤':'坤','震':'震','巽':'巽','中':'中','乾':'乾','兌':'兑','艮':'艮','離':'离'};
    const cBorder='var(--card-border)';

    let html=`<div style="background:var(--card-bg);border-radius:12px;padding:16px;border:1px solid ${cBorder};">`;

    // ═══ 概要信息 ═══
    html+=`<div style="margin-bottom:14px;border-bottom:1px solid ${cBorder};padding-bottom:10px;">`;
    html+=`<div style="font-size:1rem;font-weight:700;margin-bottom:6px;color:var(--accent);letter-spacing:2px;">☯ 奇门遁甲排盘</div>`;
    const panType=data.panType||'拆补法';
    html+=`<div style="display:flex;flex-wrap:wrap;gap:6px 16px;font-size:0.82rem;color:var(--text-2);margin-bottom:4px;">`;
    html+=`<span><b style="color:var(--text-1);">盘式：</b>转盘奇门 · ${escapeHtml(panType)}</span>`;
    if(data.solarDate) html+=`<span><b style="color:var(--text-1);">时间：</b>${escapeHtml(data.solarDate)}</span>`;
    html+=`</div>`;
    // 四柱
    if(fp){
        html+=`<div style="display:flex;flex-wrap:wrap;gap:6px 14px;font-size:0.82rem;margin-bottom:4px;">`;
        if(fp.year) html+=`<span><b style="color:var(--text-1);">年柱</b> ${escapeHtml(fp.year)}</span>`;
        if(fp.month) html+=`<span><b style="color:var(--text-1);">月柱</b> ${escapeHtml(fp.month)}</span>`;
        if(fp.day) html+=`<span><b style="color:var(--text-1);">日柱</b> ${escapeHtml(fp.day)}</span>`;
        if(fp.hour) html+=`<span><b style="color:var(--text-1);">时柱</b> ${escapeHtml(fp.hour)}</span>`;
        html+=`</div>`;
    }
    // 旬空
    const xk=data.xunKong;
    if(xk&&(xk.day||xk.hour)){
        html+=`<div style="font-size:0.82rem;margin-bottom:4px;"><b style="color:var(--text-1);">旬空：</b>`;
        if(xk.day) html+=`日空${escapeHtml(xk.day)}`;
        if(xk.day&&xk.hour) html+=` `;
        if(xk.hour) html+=`时空${escapeHtml(xk.hour)}`;
        html+=`</div>`;
    }
    html+=`<div style="display:flex;flex-wrap:wrap;gap:6px 16px;font-size:0.82rem;margin-bottom:4px;">`;
    if(data.solarTerm) html+=`<span><b style="color:var(--text-1);">节气：</b>${escapeHtml(data.solarTerm)}</span>`;
    if(data.ju) html+=`<span><b style="color:var(--text-1);">局数：</b>${escapeHtml(data.ju)}</span>`;
    if(data.xunShou) html+=`<span><b style="color:var(--text-1);">旬首：</b>${escapeHtml(data.xunShou)}</span>`;
    html+=`</div>`;
    html+=`<div style="display:flex;flex-wrap:wrap;gap:6px 16px;font-size:0.82rem;">`;
            if(data.zhiFu) html+=`<span style="font-weight:600;"><b>值符：</b>${escapeHtml(data.zhiFu)}</span>`;
            if(data.zhiShi) html+=`<span style="font-weight:600;"><b>值使：</b>${escapeHtml(data.zhiShi)}</span>`;
            if(data.tianYi) html+=`<span style="font-weight:500;"><b>天乙：</b>${escapeHtml(data.tianYi)}</span>`;
    const mx=data.maXing||{};const maList=[];
    if(mx['驛馬']||mx['驿马']) maList.push('驿马→'+(mx['驛馬']||mx['驿马']));
    if(mx['丁馬']||mx['丁马']) maList.push('丁马→'+(mx['丁馬']||mx['丁马']));
    if(mx['天馬']||mx['天马']) maList.push('天马→'+(mx['天馬']||mx['天马']));
    if(maList.length) html+=`<span><b style="color:var(--text-1);">马星：</b>${maList.join(' ')}</span>`;
    html+=`</div></div>`;

    // ═══ 九宫格 — 仿热卜布局 v5 ═══
    // 每宫布局（3行2列 + 宫号居中）：
    //   ○八神(左)       天盘干🐎(右)
    //   九星(左)         地盘干(右)
    //   八门 状态(左)    隐干(右)
    //         宫号(居中)
    if(palaces&&Array.isArray(palaces)&&palaces.length>0){
        html+=`<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2px;max-width:420px;margin:0 auto;background:#d5cfc2;border-radius:12px;overflow:hidden;border:2px solid #b8b0a0;box-shadow:0 2px 12px rgba(0,0,0,0.08);">`;
        for(const gongNum of luoOrder){
            const p=palaces[gongNum-1];
            if(!p){html+=`<div style="background:var(--input-bg);aspect-ratio:1;"></div>`;continue;}

            // 中宫：3meta风格 — 排盘概要，五行着色
            if(gongNum===5){
                // 五行颜色
                const WX_GAN={'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'};
                const WX_ZHI={'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'};
                const WX_COLOR={'木':'#27AE60','火':'#E74C3C','土':'#8B6914','金':'#B8860B','水':'#2980B9'};
                function wxColor(ch){const wx=WX_GAN[ch]||WX_ZHI[ch];return wx?WX_COLOR[wx]:C_DEFAULT;}
                function wxSpan(text){let s='';for(const c of text){const clr=wxColor(c);const w=(clr===C_DEFAULT)?'500':'700';s+=`<span style="color:${clr};font-weight:${w};">${escapeHtml(c)}</span>`;}return s;}
                const XUN_MAP={'戊':'甲子','己':'甲戌','庚':'甲申','辛':'甲午','壬':'甲辰','癸':'甲寅'};
                const NUM_CN=['','一','二','三','四','五','六','七','八','九'];
                const BAGUA_NUM={'坎':1,'坤':2,'震':3,'巽':4,'中':5,'乾':6,'兑':7,'艮':8,'离':9};
                const xunRaw=XUN_MAP[data.xunShou]||'';
                const xkH=(data.xunKong&&data.xunKong.hour)||'';
                const xkD=(data.xunKong&&data.xunKong.day)||'';
                const fp5=data.fourPillars||{};
                const juRaw=data.ju||'';
                const ydM=juRaw.match(/([阳阴]遁)/);
                const juNumM=juRaw.match(/[一二三四五六七八九十\d]+/);
                const juNumCn=juNumM?juNumM[0]:'';
                const juYuanM=juRaw.match(/(上元|中元|下元)/);
                const juYuan=juYuanM?juYuanM[0]:'';
                const ydStr=ydM?ydM[1]:'';
                const cn2num={'一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9','十':'10'};
                const juNumArab=cn2num[juNumCn]||juNumCn;
                const juDisplay=ydStr?`${ydStr}${juNumArab}局`:juRaw;
                const zhiFuNum=BAGUA_NUM[data.zhiFuGong]||5;
                const zhiShiNum=BAGUA_NUM[data.zhiShiGong]||2;
                const FS_C='0.68rem';
                const FS_S='0.58rem';
                html+=`<div style="background:#f0ede5;aspect-ratio:1;color:${C_DEFAULT};padding:7px 8px;display:flex;flex-direction:column;justify-content:center;gap:3px;box-sizing:border-box;line-height:1.4;font-size:${FS_C};text-align:center;">`;
                const dateStr=(data.solarDate||'').split(' ')[0];
                if(dateStr) html+=`<div style="font-weight:700;font-size:0.72rem;">${escapeHtml(dateStr)}</div>`;
                // 旬名+空亡
                html+=`<div>${wxSpan(xunRaw+'旬')}`;
                if(xkH){html+=` ${wxSpan(xkH)}<span style="color:${C_DEFAULT};">空</span>`;}
                html+=`</div>`;
                // 四柱逐字着色
                const zhuArr=[];
                const zhuLabels=['年','月','日','时'];
                ['year','month','day','hour'].forEach((k,i)=>{
                    const v=fp5[k];
                    if(v) zhuArr.push(wxSpan(v)+`<span style="color:${C_DEFAULT};font-weight:400;">${zhuLabels[i]}</span>`);
                });
                html+=`<div style="font-size:${FS_S};">${zhuArr.join(' ')}</div>`;
                html+=`<div style="font-weight:600;">${escapeHtml(data.solarTerm||'')} ${escapeHtml(juYuan)} ${escapeHtml(juDisplay)}</div>`;
                html+=`<div>值符天${escapeHtml(data.zhiFuStar||'')}落${NUM_CN[zhiFuNum]}宫</div>`;
                html+=`<div>值使${escapeHtml((data.zhiShiMen||'')+'门')}落${NUM_CN[zhiShiNum]}宫</div>`;
                html+=`</div>`;
                continue;
            }

            const tianGan=p.tianGan||p.tianPan||'';
            const diGan=p.diGan||p.diPan||'';
            const yinGan=p.yinGan||'';
            const shenFull=p.shenFull||p.shen||p.baShen||p.god||'';
            const xingFull=p.xingFull||p.xing||p.skyStar||'';
            const menFull=p.menFull||(p.men||p.baMen||p.door?p.men+'门':'')||'';
            const bagua=p.bagua||'';

            // 3meta数组格式：双星双干时为数组，单值时为字符串
            const xingArr=Array.isArray(p.xing)?p.xing:(p.xing?[p.xing]:[]);
            const tianGanArr=Array.isArray(tianGan)?tianGan:(tianGan?[tianGan]:[]);
            const diGanArr=Array.isArray(diGan)?diGan:(diGan?[diGan]:[]);
            const xingFullArr=Array.isArray(xingFull)?xingFull:(xingFull?[xingFull]:[]);

            const bg='#fff';
            const isZhiFu=xingArr.includes(zhiFuStar);
            const isZhiShi=(p.men===zhiShiMen);
            const hasJiXing=p.isJiXing;const hasDiJiXing=p.isDiJiXing;
            const hasRuMu=p.isRuMu;const hasDiRuMu=p.isDiRuMu;
            const hasMenPo=p.isMenPo;
            const hasXingMu=(hasJiXing&&hasRuMu)||(hasDiJiXing&&hasDiRuMu);
            const hasAnyJiXing=hasJiXing||hasDiJiXing;
            const hasAnyRuMu=hasRuMu||hasDiRuMu;

            const isDayTian=dayGan&&tianGanArr.includes(dayGan);
            const isHourTian=hourGan&&tianGanArr.includes(hourGan);
            const isDayDi=dayGan&&diGanArr.includes(dayGan);
            const isHourDi=hourGan&&diGanArr.includes(hourGan);
            const isDayYin=dayGan&&yinGan===dayGan;
            const isHourYin=hourGan&&yinGan===hourGan;

            // 击刑/入墓逐字标记
            const jiXingTianSet=new Set(p.jiXingTianGans||[]);
            const jiXingDiSet=new Set(p.jiXingDiGans||[]);
            const ruMuTianSet=new Set(p.ruMuTianGans||[]);
            const ruMuDiSet=new Set(p.ruMuDiGans||[]);

            let statusTag='';  // 只保留门迫标签

            const shenColor=C_DEFAULT;const shenWeight='500';
            const xingColor=isZhiFu?C_ZHIFU:C_DEFAULT;const xingWeight=isZhiFu?'700':'500';
            // 值使门绿色，门迫红色：同时存在时显示值使绿+门迫标签
            let menColor=C_DEFAULT;let menWeight='500';
            let menPoTag='';
            if(isZhiShi){menColor=C_ZHISHI;menWeight='700';}
            if(hasMenPo){menPoTag=`<span style="color:${C_MENPO};font-weight:700;font-size:0.58rem;margin-left:2px;">门迫</span>`;if(!isZhiShi){menColor=C_MENPO;menWeight='700';}}
            // 天盘干逐字渲染
            const yinColor=C_YINGAN;const yinWeight='400';

            // 天盘干/地盘干/九星显示（3meta数组格式，双值时拼接）
            // 天盘干逐字渲染：击刑紫色，入墓棕色，其余默认
            let tianHtml='';
            tianGanArr.filter(Boolean).forEach(g=>{
                let c=C_DEFAULT,w='400';
                if(jiXingTianSet.has(g)){c=C_JIXING;w='700';}
                else if(ruMuTianSet.has(g)){c=C_RUMU;w='700';}
                tianHtml+=`<span style="color:${c};font-weight:${w};">${escapeHtml(g)}</span>`;
            });
            // 地盘干逐字渲染
            let diHtml='';
            diGanArr.filter(Boolean).forEach(g=>{
                let c=C_DIGAN,w='400';
                if(jiXingDiSet.has(g)){c=C_JIXING;w='700';}
                else if(ruMuDiSet.has(g)){c=C_RUMU;w='700';}
                diHtml+=`<span style="color:${c};font-weight:${w};">${escapeHtml(g)}</span>`;
            });
            const xingDisplay=xingFullArr.length>1?xingArr.filter(Boolean).join(''):xingFullArr.filter(Boolean).join('');

            const gongLabel=gongNum+'·'+(baguaSimple[bagua]||bagua);

            // 统一字号
            const FS='0.8rem';
            // 外层：统一白色背景，微圆角
            html+=`<div style="background:${bg};aspect-ratio:1;position:relative;color:${C_DEFAULT};padding:8px 10px;display:flex;flex-direction:column;justify-content:space-between;box-sizing:border-box;">`;

            // Row1: 八神○(左) ── 🐎天盘干(右)
            html+=`<div style="display:flex;justify-content:space-between;align-items:center;">`;
            html+=`<span style="color:${shenColor};font-weight:${shenWeight};font-size:${FS};white-space:nowrap;">`;
            if(shenFull) html+=escapeHtml(shenFull);
            if(p.isKong) html+=`<span style="color:${C_KONG};font-size:0.78rem;font-weight:700;margin-left:2px;">○</span>`;
            html+=`</span>`;
            html+=`<span style="display:inline-flex;align-items:center;gap:2px;font-size:${FS};white-space:nowrap;">`;
            if(p.isMa) html+=`<span style="color:${C_MAHORSE};font-size:0.72rem;">🐎</span>`;
            if(tianHtml) html+=tianHtml;
            html+=`</span></div>`;

            // Row2: 九星(左) ── 地盘干(右)
            html+=`<div style="display:flex;justify-content:space-between;align-items:center;">`;
            html+=`<span style="color:${xingColor};font-weight:${xingWeight};font-size:${FS};white-space:nowrap;">`;
            if(xingDisplay) html+=escapeHtml(xingDisplay);
            html+=`</span>`;
            html+=`<span style="font-size:${FS};white-space:nowrap;">`;
            if(diHtml) html+=diHtml;
            html+=`</span></div>`;

            // Row3: 八门+状态(左) ── 隐干(右)
            html+=`<div style="display:flex;justify-content:space-between;align-items:center;">`;
            html+=`<span style="white-space:nowrap;display:inline-flex;align-items:center;">`;
            if(menFull) html+=`<span style="color:${menColor};font-weight:${menWeight};font-size:${FS};">${escapeHtml(menFull)}</span>`;
            if(statusTag) html+=statusTag;
            if(menPoTag) html+=menPoTag;
            html+=`</span>`;
            html+=`<span style="color:${yinColor};font-weight:${yinWeight};font-size:${FS};white-space:nowrap;">`;
            if(yinGan) html+=escapeHtml(yinGan);
            html+=`</span></div>`;

            // 宫号居中叠加
            html+=`<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:0.55rem;color:#d0d0d0;font-weight:400;pointer-events:none;">${gongLabel}</div>`;

            html+=`</div>`;
        }
        html+=`</div>`;

        // 图例
        html+=`<div style="display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:12px;font-size:0.72rem;color:var(--text-3);justify-content:center;align-items:center;">`;
        html+=`<span><span style="color:${C_ZHISHI};font-weight:700;">值使</span></span>`;
        html+=`<span><span style="color:${C_MENPO};font-weight:700;">门迫</span></span>`;
        html+=`<span><span style="color:${C_JIXING};font-weight:700;">击刑</span></span>`;
        html+=`<span><span style="color:${C_RUMU};font-weight:700;">入墓</span></span>`;
        html+=`<span><span style="color:${C_KONG};">○</span>空亡</span>`;
        html+=`<span><span style="color:${C_MAHORSE};">🐎</span>马星</span>`;
        html+=`</div>`;

        // 长生运折叠
        const hasCs=palaces.some(p=>p&&(p.tianCs||p.diCs));
        if(hasCs){
            html+=`<details style="margin-top:8px;font-size:0.78rem;"><summary style="cursor:pointer;color:var(--text-3);">长生十二运</summary>`;
            html+=`<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:3px;margin-top:4px;">`;
            for(const gongNum of luoOrder){
                const p=palaces[gongNum-1];
                if(!p)continue;
                html+=`<div style="background:var(--input-bg);border:1px solid ${cBorder};border-radius:4px;padding:3px;font-size:0.7rem;">`;
                html+=`<b>${gongNum}宫</b> `;
                if(p.tianCs) html+=`天${escapeHtml(p.tianCs)} `;
                if(p.diCs) html+=`地${escapeHtml(p.diCs)}`;
                html+=`</div>`;
            }
            html+=`</div></details>`;
        }
    }

    html+=`<div style="text-align:center;font-size:0.7rem;color:var(--text-3);margin-top:8px;">⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议</div>`;
    html+=`</div>`;

    // 兜底完整数据
    const shown=new Set(['solarDate','lunarDate','solarTerm','fourPillars','ju','juDay','zhiFu','zhiShi','zhiFuStar','zhiFuGong','zhiShiMen','zhiShiGong','tianYi','tianYiStar','tianYiGong','xunKong','xunShou','maXing','palaces','gong','gongWei','panType','dayGan','hourGan']);
    const extras=Object.keys(data).filter(k=>!shown.has(k));
    if(extras.length){
        html+=`<details style="margin-top:8px;"><summary style="cursor:pointer;color:var(--text-3);font-size:0.72rem;">完整原始数据</summary>`;
        html+=`<pre style="font-size:0.65rem;color:var(--text-3);white-space:pre-wrap;margin-top:4px;max-height:300px;overflow:auto;">${escapeHtml(JSON.stringify(data,null,2))}</pre></details>`;
    }

    el.innerHTML=html;
}

// ═══════════════════════════════════════════════
// 删除记录
// ═══════════════════════════════════════════════
function shouldConfirmDelete(){
    return localStorage.getItem('xc_no_delete_confirm')!=='1';
}

function requestDelete(id){
    if(shouldConfirmDelete()){
        pendingDeleteId=id;
        $('noRemindCheck').checked=false;
        showModal('deleteModal');
    }else{
        doDelete(id);
    }
}

async function doDelete(id){
    try{
        const r=await apiFetch(`/api/records/${id}`,{method:'DELETE'});
        const d=await r.json();
        if(d.error){alert(d.error);return;}
    }catch(e){alert('删除失败，请重试');}
    loadHistory(currentHistoryType);
    pendingDeleteId=null;
}

// 绑定删除确认按钮
document.addEventListener('DOMContentLoaded',function(){
    $('confirmDeleteBtn').addEventListener('click',function(){
        if($('noRemindCheck').checked){
            localStorage.setItem('xc_no_delete_confirm','1');
        }
        hideModal('deleteModal');
        if(pendingDeleteId){doDelete(pendingDeleteId);}
    });
});

// ═══════════════════════════════════════════════
// 天机问策
// ═══════════════════════════════════════════════
let qimenPollTimer=null;
let qimenPollCount=0;
const QIMEN_MAX_POLL=200; // 200次 × 1.5秒 = 5分钟上限

async function qimenStart(){
    if(!currentUser){showModal('loginModal');return;}
    const q=$('qimenInput').value.trim();
    if(!q){$('qimenPhase').textContent='请输入问题';$('qimenPhase').style.color='var(--danger)';return;}
    $('qimenStartBtn').disabled=true;
    $('qimenProgress').style.display='block';
    $('qimenResult').style.display='none';
    $('qimenPhase').textContent='准备中...';$('qimenPhase').style.color='';$('qimenPercent').textContent='0%';$('qimenFill').style.width='0%';

    try{
        const fd=new FormData();fd.append('question',q);
        const r=await apiFetch('/start',{method:'POST',body:fd});
        const d=await r.json();
        if(d.error){$('qimenPhase').textContent=d.error;$('qimenPhase').style.color='var(--danger)';$('qimenStartBtn').disabled=false;return;}
        if(d.run_id) qimenPoll(d.run_id);
    }catch(e){
        $('qimenPhase').textContent='网络错误，请重试';$('qimenPhase').style.color='var(--danger)';
        $('qimenStartBtn').disabled=false;
    }
}

function qimenPoll(runId){
    if(qimenPollTimer)clearInterval(qimenPollTimer);
    qimenPollCount=0;
    qimenPollTimer=setInterval(async()=>{
        qimenPollCount++;
        if(qimenPollCount>=QIMEN_MAX_POLL){
            clearInterval(qimenPollTimer);
            $('qimenPhase').textContent='等待超时，请重新问策';$('qimenPhase').style.color='var(--danger)';
            $('qimenStartBtn').disabled=false;
            return;
        }
        try{
            const r=await fetch(`/status?run_id=${runId}`);
            const d=await r.json();
            $('qimenPhase').textContent=d.message||'...';$('qimenPhase').style.color='';
            $('qimenPercent').textContent=d.progress+'%';
            $('qimenFill').style.width=d.progress+'%';
            // Phase 5/6 期间显示键盘警告
            const kw=$('qimenKeyboardWarning');
            if(d.phase==='phase5'||d.phase==='phase5_done'||d.phase==='phase6'){
                kw.style.display='block';
            }else{
                kw.style.display='none';
            }
            if(d.phase==='done'){
                clearInterval(qimenPollTimer);
                $('qimenStartBtn').disabled=false;
                $('qimenResetBtn').style.display='inline-flex';
                if(d.result){$('qimenResult').style.display='block';$('qimenResultHtml').textContent=d.result;}
                if(d.qimen){$('qimenChart').style.display='block';renderQimenChart(d.qimen);}
                loadHistory('qimen');
            }else if(d.phase==='error'){
                clearInterval(qimenPollTimer);
                $('qimenStartBtn').disabled=false;
                $('qimenPhase').textContent=d.message;$('qimenPhase').style.color='var(--danger)';
            }
        }catch(e){/* 单次轮询失败不中断，继续重试 */}
    },1500);
}

function qimenReset(){
    if(qimenPollTimer)clearInterval(qimenPollTimer);
    $('qimenInput').value='';$('qimenProgress').style.display='none';
    $('qimenResult').style.display='none';$('qimenChart').style.display='none';
    $('qimenResetBtn').style.display='none';$('qimenStartBtn').disabled=false;
    $('qimenFill').style.width='0%';$('qimenPhase').textContent='';$('qimenPercent').textContent='';
    $('qimenKeyboardWarning').style.display='none';
}

// ═══════════════════════════════════════════════
// 八字排盘
// ═══════════════════════════════════════════════
let paipanPeople=[];
let _autoParseTimer=null;

$('paipanInput').addEventListener('input',()=>{
    clearTimeout(_autoParseTimer);
    _autoParseTimer=setTimeout(()=>{
        const raw=$('paipanInput').value.trim();
        if(raw.length>10){const p=smartParse(raw);if(p.length){renderPaipanPreview(p);}}
        else{$('paipanPreview').style.display='none';}
    },600);
});

function paipanLog(msg){
    const box=$('paipanLogBox');
    const ts=new Date().toLocaleTimeString('zh-CN',{hour12:false});
    box.textContent+=(box.textContent?'\n':'')+`[${ts}] ${msg}`;
    box.classList.add('show');box.scrollTop=box.scrollHeight;
}

function paipanParse(){
    const raw=$('paipanInput').value.trim();
    if(!raw){$('paipanStatusBar').textContent='⚠️ 请先粘贴数据';$('paipanStatusBar').className='status-bar err';return;}
    const p=smartParse(raw);
    if(!p.length){$('paipanStatusBar').textContent='⚠️ 无法识别';$('paipanStatusBar').className='status-bar err';$('paipanPreview').style.display='none';return;}
    renderPaipanPreview(p);
    $('paipanStatusBar').textContent='✅ 识别 '+p.length+' 人';$('paipanStatusBar').className='status-bar ok';
}

function renderPaipanPreview(people){
    paipanPeople=people;
    if(!people.length){$('paipanPreview').style.display='none';return;}
    $('paipanPreview').style.display='block';
    $('paipanPreviewGrid').innerHTML=people.map((p,i)=>{
        const warns=[];
        if(!p.birthTime||p.birthTime==='000000000000')warns.push('未识别日期');
        if(!p.birthAddr)warns.push('无出生地');
        if(p._genderAssumed)warns.push('性别未识别，默认为男');
        return `<div class="preview-card">
            <div class="pc-name"><span class="num">${i+1}</span>${escapeHtml(p.name)}</div>
            <div class="pc-row"><span class="pc-label">性别：</span><span class="pc-val">${p.gender}${p._genderAssumed?' ⚠️':''}</span></div>
            <div class="pc-row"><span class="pc-label">历法：</span><span class="pc-val">${p.calType}</span></div>
            <div class="pc-row"><span class="pc-label">出生：</span><span class="pc-val">${formatBirthTime(p.birthTime)}</span></div>
            <div class="pc-row"><span class="pc-label">地址：</span><span class="pc-val">${p.birthAddr||'—'}</span></div>
            ${warns.length?`<div class="pc-warn">⚠ ${warns.join(' | ')}</div>`:''}
        </div>`;
    }).join('');
}

async function paipanRun(){
    if(!currentUser){showModal('loginModal');return;}
    const raw=$('paipanInput').value.trim();
    if(!raw){$('paipanStatusBar').textContent='⚠️ 请先输入数据';$('paipanStatusBar').className='status-bar err';return;}
    const people=smartParse(raw);
    renderPaipanPreview(people);
    if(!people.length){$('paipanStatusBar').textContent='⚠️ 无法解析';$('paipanStatusBar').className='status-bar err';return;}

    $('paipanRunBtn').disabled=true;
    $('paipanLogBox').textContent='';
    $('paipanStatusBar').className='status-bar running';$('paipanStatusBar').textContent='排盘中...';
    let ok=0,fail=0;
    for(let i=0;i<people.length;i++){
        paipanLog(`── [${i+1}/${people.length}] ${people[i].name} ──`);
        try{
            const r=await apiFetch('/api/paipan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(people[i])});
            const d=await r.json();
            if(d.success){
                ok++;
                paipanLog('  ✅ 排盘完成');
                if(d.message){
                    // 显示排盘结果
                    paipanLog(d.message.split('\n').map(l=>'    '+l).join('\n'));
                }
            }else{paipanLog('  ❌ '+(d.error||'失败'));fail++;}
        }catch(e){paipanLog('  ❌ 错误：'+e.message);fail++;}
        $('paipanStatsBar').textContent=`进度：${i+1}/${people.length}（成功 ${ok} / 失败 ${fail}）`;
        if(i<people.length-1)await new Promise(r=>setTimeout(r,2000));
    }
    const allOk=ok===people.length;
    paipanLog(`\n═══ 完成！成功 ${ok}/${people.length} ═══`);
    $('paipanStatusBar').textContent=allOk?`✅ 全部完成，共 ${ok} 条`:`⚠️ 完成 ${ok}/${people.length}`;
    $('paipanStatusBar').className=allOk?'status-bar ok':'status-bar err';
    $('paipanRunBtn').disabled=false;
    loadHistory('paipan');
}

function paipanClear(){
    $('paipanInput').value='';$('paipanPreview').style.display='none';
    $('paipanLogBox').textContent='';$('paipanLogBox').classList.remove('show');
    $('paipanStatusBar').textContent='';$('paipanStatsBar').textContent='';
    paipanPeople=[];
}

// ═══════════════════════════════════════════════
// 八字排盘 - 智能解析模块 (从 paipan_tool.html 迁移)
// ═══════════════════════════════════════════════

function parseAddress(rawAddr){
  if(!rawAddr) return null;
  const s=rawAddr.trim().replace(/\s+/g,'');
  if(s.length<2) return null;
  const RE_PROV=/(新疆|西藏|内蒙古|宁夏|广西)?(.*?省|北京市|天津市|上海市|重庆市|香港|澳门)/;
  const RE_CITY=/(.*?(?:市|地区|盟|自治州))/;
  const RE_DISTRICT=/(.*?(?:区|县|市|旗))/;
  const RE_TOWN=/(.*?(?:镇|乡|街道|苏木))/;
  let province='',city='',district='',town='',rest=s;
  const mProv=s.match(RE_PROV);
  if(mProv){province=mProv[0];rest=s.substring(s.indexOf(province)+province.length);
    if(rest.startsWith('自治区')||rest.startsWith('壮族')||rest.startsWith('回族')||rest.startsWith('维吾尔')){
      const extra=/^(自治区|壮族|回族|维吾尔族?)/.exec(rest);if(extra){province+=extra[0];rest=rest.substring(extra[0].length);}
    }
  }
  const mCity=rest.match(RE_CITY);
  if(mCity){city=mCity[0];if(/北京市|天津市|上海市|重庆市/.test(province)){city='';}else{rest=rest.substring(city.length);}}
  if(!city&&province.endsWith('省')){const m2=rest.match(RE_CITY);if(m2){city=m2[0];rest=rest.substring(city.length);}}
  const mDist=rest.match(RE_DISTRICT);if(mDist){district=mDist[0];rest=rest.substring(district.length);}
  const mTown=rest.match(RE_TOWN);if(mTown){town=mTown[0];}
  const parts=[province,city,district].filter(p=>p);
  return {province:province||'—',city:city||(province&&/(北京|天津|上海|重庆)市/.test(province)?province.replace('市',''):'—'),
    district:district||'—',town:town||'—',full:parts.join(''),detail:rest.replace(town,'').trim()||'—',original:rawAddr};
}

function smartParse(text){
  const people=[];
  function tryCommaFormat(txt){
    const lines=txt.split('\n').map(l=>l.trim()).filter(Boolean);
    const results=[];let pendingAddr='';
    for(const line of lines){if(/^(现在居住|现居|居住|住在)/.test(line)){const m=line.match(/(?:现在居住|现居|居住|住在)[：:\s，,，]*(.+)/);if(m)pendingAddr=m[1].trim().replace(/[。，；;！!?.。]+$/,'');}}
    for(const line of lines){
      if(line.length<8)continue;if(/^(现在|居住|地址|手机|电话|微|微信|QQ|邮箱)/.test(line))continue;
      const parts=line.split(/[,，\t]+/).map(p=>p.trim()).filter(p=>p.length>0);if(parts.length<4)continue;
      let name='',gender='',year='',month='',day='',genderIdx=-1;
      for(let i=0;i<parts.length;i++){if(/^[男女]$/.test(parts[i])){gender=parts[i];genderIdx=i;break;}}
      if(genderIdx===0||(genderIdx===-1&&parts.length>=5)){name=parts[0];if(genderIdx===0){year=parts[2]||'';month=parts[3]||'';day=parts[4]||'';}else{year=parts[1]||'';month=parts[2]||'';day=parts[3]||'';}}
      else if(genderIdx>0){name=parts[0];const ds=genderIdx+1;year=parts[ds]||'';month=parts[ds+1]||'';day=parts[ds+2]||'';}
      if(name&&gender&&year){month=String(month).replace(/^0/,'');if(month.length===1)month='0'+month;day=String(day).replace(/^0/,'');if(day.length===1)day='0'+day;
        results.push({name,gender,calType:'公历',birthTime:normalizeDate(`${year}.${month}.${day}`),birthAddr:pendingAddr||'',addrInfo:parseAddress(pendingAddr||'')});}
    }
    return results;
  }
  function tryKeyValueFormat(txt){
    const result=[];let blocks;
    const lines=txt.split('\n').map(l=>l.trim()).filter(Boolean);
    const nameLineCount=lines.filter(l=>/^姓名\s*[：:\s]*/.test(l)).length;
    const genderLineCount=lines.filter(l=>/^性别\s*[：:\s]*[男女]/.test(l)).length;
    if(nameLineCount===1&&genderLineCount>=1){blocks=[txt.trim()];}
    else if(nameLineCount>1||genderLineCount>1){blocks=txt.split(/\n\s*\n/).map(b=>b.trim()).filter(Boolean);if(blocks.length<nameLineCount){blocks=[];let cur='';for(const line of txt.split('\n')){if(/^姓名\s*[：:\s]*/.test(line.trim())){if(cur.trim())blocks.push(cur.trim());cur=line;}else{cur+='\n'+line;}}if(cur.trim())blocks.push(cur.trim());}if(!blocks.length)blocks=[txt.trim()];}
    else{blocks=[];let cur='';for(const line of txt.split('\n')){const t=line.trim();if(/^姓名\s*[：:\s]*/.test(t)){if(cur.trim())blocks.push(cur.trim());cur=t;}else if(t){cur+='\n'+t;}}if(cur.trim())blocks.push(cur.trim());if(!blocks.length)blocks=[txt.trim()];}
    for(const block of blocks){
      const p={name:'',gender:'',calType:'公历',birthTime:'',birthAddr:''};
      for(const line of block.split('\n').map(l=>l.trim()).filter(Boolean)){
        let m;
        m=line.match(/姓名\s*[：:\s]*(.+)/);if(m){p.name=m[1].trim();if(/性别\s*[：:\s]*[男女]/.test(p.name)){const np=p.name.split(/\s+/);for(const part of np){if(/^[男女]$/.test(part)){p.gender=part;break;}if(/性别\s*[：:\s]*([男女])/.test(part)){const gm=part.match(/性别\s*[：:\s]*([男女])/);if(gm)p.gender=gm[1];}}p.name=p.name.replace(/性别\s*[：:\s]*[男女]/g,'').replace(/[男女]$/,'').trim();}}
        m=line.match(/性别\s*[（(][^）)]+[）)]?\s*[：:\s]*([男女])/);if(!m)m=line.match(/性别\s*[：:\s]*([男女])/);if(m&&!p.gender)p.gender=m[1];
        if(/阳历|公历/.test(line)){m=line.match(/(?:阳历|公历)\s*(?:出生)?\s*(?:年月日)?[：:\s]*(.+)/);if(m){let ds=m[1].trim().replace(/[（(]([^）)]+)[）)]/,(a,b)=>b).replace(/阳历|阴历/g,'');const nums=ds.match(/\d+/g);if(nums){const e8=nums.find(n=>n.length===8);if(e8)ds=e8;else if(nums.length>=3)ds=nums[0]+'.'+nums.slice(1).join('.');else ds=nums.join('');}if(ds.length>=6){p.birthTime=normalizeDate(ds);p.calType='公历';continue;}}}
        if(!p.birthTime){m=line.match(/出生\s*日期[：:\s]*(.+)/);if(m){let ds=m[1].trim().replace(/[（(]([^）)]+)[）)]/,(a,b)=>b).replace(/阳历|阴历/g,'');if(ds.length>=6){p.birthTime=normalizeDate(ds);continue;}}}
        if(!p._timeHint){const tm=line.match(/出生时间具体到分\s*(?:[（(][^）)]+[）)]\s*)?[：:\s]*(.+)/);if(tm){p._timeHint=tm[1].trim();continue;}const tm2=line.match(/出生\s*时间\s*(?:具体到分)?\s*[（(][^）)]+[）)]?\s*[：:\s]*(.+)/);if(tm2){p._timeHint=tm2[1].trim();continue;}}
        if((/农历|阴历/.test(line))&&!p.birthTime){m=line.match(/(?:农历|阴历)[^：：]*[：:\s]*(.+)/);if(m){let ds=m[1].trim().replace(/\s+/g,'');ds=ds.replace(/初([0-9])/g,(a,d)=>'0'+d);const lm={'初一':'01','初二':'02','初三':'03','初四':'04','初五':'05','初六':'06','初七':'07','初八':'08','初九':'09','初十':'10','十一':'11','十二':'12','十三':'13','十四':'14','十五':'15','十六':'16','十七':'17','十八':'18','十九':'19','二十':'20','二十一':'21','二十二':'22','二十三':'23','二十四':'24','二十五':'25','二十六':'26','二十七':'27','二十八':'28','二十九':'29','三十':'30'};for(const[cn,num]of Object.entries(lm)){if(ds.includes(cn)){ds=ds.replace(cn,num);break;}}p.birthTime=normalizeDate(ds);p.calType='农历';continue;}}
        m=line.match(/(?:出生地|出生地址|出生.*?地)\s*(?:具体到区)?\s*[：:\s]*(.+)/);if(m){p.birthAddr=m[1].trim();continue;}
        m=line.match(/(?:现居住地址|居住地址|现居地|现居|现住址|现住)\s*(?:具体到区)?\s*[：:\s]*(.+)/);if(m&&!p.birthAddr){p.birthAddr=m[1].trim();continue;}
        m=line.match(/地址\s*[：:\s]*(.+)/);if(m&&!p.birthAddr){p.birthAddr=m[1].trim();continue;}
        if(!p.birthTime&&/\d{4}/.test(line)){const np=line.replace(/[^\d.\-\s:\/]/g,'').trim();if(/^\d{4}/.test(np))p.birthTime=normalizeDate(np);}
      }
      if(p.name){if(!p.gender){p.gender='男';p._genderAssumed=true;}p.addrInfo=parseAddress(p.birthAddr||'');
        if(p._timeHint&&p.birthTime&&p.birthTime.length>=8){let hhmm=parseTimeDesc(p._timeHint);if(!hhmm){const tmm=p._timeHint.match(/(\d{1,2})\s*[:：.]\s*(\d{1,2})/);if(tmm){let h=parseInt(tmm[1]),mi=parseInt(tmm[2]);if(h>=0&&h<=23&&mi>=0&&mi<=59)hhmm=String(h).padStart(2,'0')+String(mi).padStart(2,'0');}}if(hhmm)p.birthTime=p.birthTime.slice(0,8)+hhmm;}delete p._timeHint;result.push(p);}
    }
    return result;
  }
  let results=tryCommaFormat(text);if(!results.length)results=tryKeyValueFormat(text);return results;
}

function normalizeDate(raw){
  if(!raw)return '';raw=raw.replace(/[年月日号]/g,'.').replace(/[（(][^）)]*[）)]/g,' ').replace(/\s+/g,' ').trim();
  while(raw.indexOf('..')>=0)raw=raw.replace('..','.');raw=raw.replace(/^\.|\.$/g,'');
  if(/^\d{8,}$/.test(raw))return raw.padEnd(12,'00').slice(0,12);
  let cleaned=raw.replace(/[\/\-]/g,'.');const dtp=cleaned.split(/\s+/);const dp=dtp[0]||'',tp=dtp[1]||'';
  const ds=dp.split('.');let yy='',mm='',dd='';
  for(let i=0;i<ds.length;i++){const d=ds[i].trim();if(d.length===4&&/^\d{4}$/.test(d)){if(!yy)yy=d;else if(!mm){const mp=d.slice(0,2),dp2=d.slice(2,4);if(parseInt(mp)>=1&&parseInt(mp)<=12&&parseInt(dp2)>=1&&parseInt(dp2)<=31){mm=mp;dd=dp2;}}}else if(d.length===2&&/^\d{1,2}$/.test(d)&&!mm){const n=parseInt(d);if(!yy&&n<=99)yy=(n<50?2000:1900)+n;else if(!mm)mm=d;}else if(!mm&&/^\d{1,2}$/.test(d))mm=d;else if(mm&&!dd&&/^\d{1,2}$/.test(d))dd=d;}
  if(mm&&mm.length===4&&/^\d{4}$/.test(mm)&&!dd){const mp=mm.slice(0,2),dp2=mm.slice(2,4);if(parseInt(mp)>=1&&parseInt(mp)<=12&&parseInt(dp2)>=1&&parseInt(dp2)<=31){mm=mp;dd=dp2;}}
  if(mm&&mm.length===1)mm='0'+mm;if(dd&&dd.length===1)dd='0'+dd;if(!mm)mm='00';if(!dd)dd='00';if(yy&&yy<100)yy=(yy<50?2000:1900)+yy;
  let timeStr='0000';if(tp){const ts=tp.split(/[:：]/);let hh=ts[0]||'00',mi=ts[1]||'00';if(hh.length===1)hh='0'+hh;if(mi.length===1)mi='0'+mi;timeStr=hh+mi;}
  return(String(yy)+mm+dd+timeStr).slice(0,12)||'000000000000';
}

function parseTimeDesc(raw){
  if(!raw)return '';const s=raw.replace(/[：:\s]/g,'').trim();if(!s)return '';
  const cnNum={'零':0,'一':1,'二':2,'两':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'十一':11,'十二':12};
  function toN(t){const n=cnNum[t];return n!==undefined?n:parseInt(t);}
  let m=s.match(/(\d{1,2}|[一二三四五六七八九十]{1,2})\s*[:：.点分]\s*(\d{1,2}|[一二三四五六七八九十]{1,2})/);
  if(m){let h=toN(m[1]),mi=toN(m[2]);if(h>=0&&h<=23&&mi>=0&&mi<=59){if(/上午|早上|早|早晨/.test(s)&&h>=12)h-=12;else if(/下午|午后|晚|傍晚|晚上|夜间/.test(s)&&h<12)h+=12;return String(h).padStart(2,'0')+String(mi).padStart(2,'0');}}
  m=s.match(/([一二三四五六七八九十]|\d{1,2})\s*[点多时]/);if(!m)m=s.match(/(凌晨|上午|早上|中午|下午|晚上|半夜)([一二三四五六七八九十\d]{1,2})/);
  if(m){let hp=!!m[2],h=toN(hp?m[2]:m[1]);if(h>=0&&h<=23){if(/下午|午后|晚|傍晚|晚上|夜间|黄昏/.test(s)&&h<12)h+=12;else if(/中午|正午|晌午/.test(s)&&h<10)h+=12;return String(h).padStart(2,'0')+(/多|左右|大约|大概|许/.test(s)?'30':'00');}}
  const tm=[{kw:['子时','半夜','深夜','午夜'],h:'00'},{kw:['丑时'],h:'02'},{kw:['寅时'],h:'04'},{kw:['卯时','黎明','破晓','清晨'],h:'06'},{kw:['辰时','早晨'],h:'08'},{kw:['巳时','上午'],h:'10'},{kw:['午时','中午','正午','晌午'],h:'12'},{kw:['未时'],h:'14'},{kw:['申时','下午','午后'],h:'16'},{kw:['酉时','傍晚','日落'],h:'18'},{kw:['戌时','黄昏','入夜'],h:'20'},{kw:['亥时','夜深','夜晚','晚上'],h:'22'}];
  for(const t of tm){if(t.kw.some(k=>s.indexOf(k)>=0))return t.h+(/多|左右/.test(s)?'30':'00');}
  if(/凌晨|四更/.test(s))return '04'+(/多|左右/.test(s)?'30':'00');return '';
}

function formatBirthTime(bt){
  if(!bt||bt==='000000000000')return '❓未知';
  if(bt.length>=8){const y=bt.slice(0,4),m=bt.slice(4,6),d=bt.slice(6,8);let s=y+'.'+parseInt(m)+'.'+parseInt(d);if(bt.length>=12)s+=' '+bt.slice(8,10)+':'+bt.slice(10,12);return s;}return bt;
}

// ═══════════════════════════════════════════════
// 初始化
// ═══════════════════════════════════════════════
document.addEventListener('DOMContentLoaded',()=>{
    const saved=localStorage.getItem('xc_theme');
    if(saved)document.documentElement.dataset.theme=saved;
    $('themeLabel').textContent=document.documentElement.dataset.theme==='dark'?'暗色':'亮色';
    checkAuth();

    // Enter 键提交登录/注册
    $('loginPass').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
    $('loginUser').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
    $('regPass2').addEventListener('keydown',e=>{if(e.key==='Enter')doRegister();});

    // 读取主页传递的表单数据
    try{
        const formJson=sessionStorage.getItem('xc_form_data');
        if(formJson){
            const fd=JSON.parse(formJson);
            sessionStorage.removeItem('xc_form_data');
            // 如果是问策类型，填充问题
            if(fd.type==='qimen'&&fd.qaiQuestion){
                $('qimenInput').value=fd.qaiQuestion;
                switchPanel('qimen');
            }
            // 梅花易数 — 填充面板并自动起卦
            if(fd.type==='meihua'){
                switchPanel('meihua');
                if(fd.maiMethod){$('meihua-method').value=fd.maiMethod;meihuaMethodChange();}
                if(fd.maiTime){$('meihuaTime').value=fd.maiTime;}
                if(fd.maiQuestion){$('meihua-question').value=fd.maiQuestion;}
                if(fd.maiNum1){$('meihuaNum1').value=fd.maiNum1;}
                if(fd.maiNum2){$('meihuaNum2').value=fd.maiNum2;}
                if(fd.maiWords){$('meihuaChar').value=fd.maiWords;}
                // 自动触发AI起卦
                setTimeout(()=>meihuaStart(),300);
            }
        }
        const scenario=sessionStorage.getItem('xc_scenario');
        if(scenario){
            sessionStorage.removeItem('xc_scenario');
            // 场景预设问题
            const scenarioQuestions={
                '事业财运':'我的事业财运如何？近期有什么需要注意的？',
                '项目回款':'项目回款情况如何？什么时候能收到？',
                '姻缘感情':'我的感情运势如何？近期能否遇到合适的人？',
                '买房租房':'现在买房/租房是否合适？哪个方位比较好？',
                '出行安全':'近期的出行是否安全？有什么需要注意的？',
                '官司诉讼':'官司诉讼的走势如何？对我是否有利？',
                '开业签约':'现在开业/签约是否吉利？什么时间比较好？',
                '结婚搬家':'结婚/搬家选什么时间比较好？需要注意什么？',
                '八字合婚':'',
                '一事一断':'',
                '大运流年':'',
                '姓名测试':'',
                '黄历查询':'今天适合做什么？有什么宜忌？',
                '周公解梦':'',
                '数字五行':'',
                '生肖运势':'',
                '六爻排盘':'',
                '紫微斗数':'',
                '梅花易数':'',
                '手相面相':'',
            };
            const q=scenarioQuestions[scenario];
            if(q){
                const hash=location.hash.replace('#','');
                if(hash==='qimen') $('qimenInput').value=q;
            }
        }
    }catch(e){}
});

// ═══════════════════════════════════════════════
// 通用工具函数（新增工具共用）
// ═══════════════════════════════════════════════
function setDefaultTime(id){
    const el=$(id);if(!el)return;
    const now=new Date();
    el.value=new Date(now.getTime()-now.getTimezoneOffset()*60000).toISOString().slice(0,16);
}
function setDefaultDate(id){
    const el=$(id);if(!el)return;
    const now=new Date();
    el.value=now.toISOString().slice(0,10);
}

// 通用AI工具请求（走后端 /api/tool-run 风格的接口）
async function toolApiRequest(appType, params){
    if(!currentUser){showModal('loginModal');return null;}
    const r=await apiFetch('/api/tool-run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({appType,...params})});
    const d=await r.json();
    if(d.error){alert(d.error);return null;}
    return d;
}

// ═══════════════════════════════════════════════
// 六爻排盘
// ═══════════════════════════════════════════════
function liuyaoStart(){
    const method=$('liuyao-method').value;
    const question=$('liuyao-question').value.trim();
    const params={method,question};
    if(method==='coin') params.coinResult=$('liuyaoCoinResult').value.trim();
    else if(method==='number'){params.num1=parseInt($('liuyaoNum1').value)||0;params.num2=parseInt($('liuyaoNum2').value)||0;}
    else if(method==='time') params.time=$('liuyaoTime').value;
    if(!params.coinResult&&!params.num1&&!params.time&&!question){alert('请输入起卦信息或问题');return;}
    $('liuyaoResult').style.display='block';
    $('liuyaoResultHtml').textContent='正在排盘解读中，请稍候...';
    // 走AI解读接口
    toolApiRequest('liuyao',params).then(d=>{
        if(!d){$('liuyaoResultHtml').textContent='排盘失败，请重试';return;}
        $('liuyaoResultHtml').textContent=d.result||d.message||'解读完成';
        loadHistory('liuyao');
    });
}
function liuyaoClear(){$('liuyaoCoinResult').value='';$('liuyaoNum1').value='';$('liuyaoNum2').value='';$('liuyaoResult').style.display='none';}
// 六爻起卦方式切换
$('liuyao-method').addEventListener('change',function(){
    const v=this.value;
    $('liuyao-coin-input').style.display=v==='coin'?'block':'none';
    $('liuyao-number-input').style.display=v==='number'?'block':'none';
    $('liuyao-time-input').style.display=v==='time'?'block':'none';
});

// ═══════════════════════════════════════════════
// 梅花易数
// ═══════════════════════════════════════════════
function meihuaMethodChange(){
    const v=$('meihua-method').value;
    $('meihua-number-input').style.display=v==='number'?'block':'none';
    $('meihua-char-input').style.display=v==='char'?'block':'none';
}
function meihuaStart(){
    const method=$('meihua-method').value;
    const question=$('meihua-question').value.trim();
    const params={method,question,time:$('meihuaTime').value};
    if(method==='number'){params.num1=parseInt($('meihuaNum1').value)||0;params.num2=parseInt($('meihuaNum2').value)||0;}
    else if(method==='char') params.char=$('meihuaChar').value.trim();
    $('meihuaResult').style.display='block';
    $('meihuaResultHtml').textContent='正在排盘解读中，请稍候...';
    toolApiRequest('meihua',params).then(d=>{
        if(!d){$('meihuaResultHtml').textContent='排盘失败，请重试';return;}
        $('meihuaResultHtml').textContent=d.result||d.message||'解读完成';
        loadHistory('meihua');
    });
}
function meihuaClear(){$('meihuaNum1').value='';$('meihuaNum2').value='';$('meihuaChar').value='';$('meihuaResult').style.display='none';}

// ═══════════════════════════════════════════════
// 紫微斗数
// ═══════════════════════════════════════════════
function ziweiStart(){
    const gender=$('ziwei-gender').value;
    const calType=$('ziwei-cal').value==='lunar'?'农历':'公历';
    const date=$('ziwei-date').value;
    const hour=$('ziwei-hour').value;
    const addr=$('ziwei-addr').value.trim();
    if(!date){alert('请选择出生日期');return;}
    const birthTime=date.replace(/-/g,'')+'0000';
    const params={gender,calType,birthTime,birthAddr:addr,hour,name:'紫微命盘'};
    $('ziweiResult').style.display='block';
    $('ziweiResultHtml').textContent='正在排盘解读中，请稍候...';
    toolApiRequest('ziwei',params).then(d=>{
        if(!d){$('ziweiResultHtml').textContent='排盘失败，请重试';return;}
        $('ziweiResultHtml').textContent=d.result||d.message||'解读完成';
        loadHistory('ziwei');
    });
}
function ziweiClear(){$('ziwei-date').value='';$('ziwei-addr').value='';$('ziweiResult').style.display='none';}

// ═══════════════════════════════════════════════
// 择吉工具
// ═══════════════════════════════════════════════
function zejiStart(){
    const type=$('zeji-type').value;
    const start=$('zeji-start').value;
    const end=$('zeji-end').value;
    const addr=$('zeji-addr').value.trim();
    if(!start){alert('请选择开始日期');return;}
    const params={zejiType:type,startDate:start,endDate:end||start,addr,name:'择吉分析'};
    $('zejiResult').style.display='block';
    $('zejiResultHtml').textContent='正在分析吉日吉时，请稍候...';
    toolApiRequest('zeji',params).then(d=>{
        if(!d){$('zejiResultHtml').textContent='分析失败，请重试';return;}
        $('zejiResultHtml').textContent=d.result||d.message||'分析完成';
        loadHistory('zeji');
    });
}
function zejiClear(){$('zeji-start').value='';$('zeji-end').value='';$('zejiResult').style.display='none';}

// ═══════════════════════════════════════════════
// 黄历万年历
// ═══════════════════════════════════════════════
function huangliQuery(){
    const date=$('huangli-date').value;
    if(!date){alert('请选择日期');return;}
    $('huangliResult').style.display='block';
    $('huangliResultHtml').textContent='查询中...';
    apiFetch('/api/huangli?date='+date).then(r=>r.json()).then(d=>{
        if(d.error){$('huangliResultHtml').textContent=d.error;return;}
        let txt='📅 '+d.solarDate+'（周'+d.weekday+'）\n';
        if(d.solarTerm) txt+='🌱 节气：'+d.solarTerm+'\n';
        if(d.gJie) txt+='🎉 公历节日：'+d.gJie+'\n';
        if(d.lJie) txt+='🎊 农历节日：'+d.lJie+'\n';
        if(d.lunarMonthName) txt+='🌙 农历：'+d.lunarMonthName+d.lunarDayName+'\n';
        if(d.ganZhiYear) txt+='🐉 年柱：'+d.ganZhiYear+' 生肖：'+d.shengXiao+'\n';
        if(d.ganZhiMonth) txt+='📅 月柱：'+d.ganZhiMonth+'\n';
        if(d.ganZhiDay) txt+='📆 日柱：'+d.ganZhiDay+'\n';
        if(d.wuXingDay) txt+='🔥 日干五行：'+d.wuXingDay+'\n';
        if(d.naYin) txt+='🔔 纳音：'+d.naYin+'\n';
        if(d.jianChu) txt+='🏯 建除：'+d.jianChu+'\n';
        if(d.chong) txt+='⚡ 冲煞：'+d.chong+' '+d.sha+'\n';
        if(d.yi) txt+='✅ 宜：'+d.yi+'\n';
        if(d.ji) txt+='❌ 忌：'+d.ji+'\n';
        if(d.pengZu) txt+='📜 彭祖百忌：'+d.pengZu+'\n';
        if(d.shenWei) txt+='🙏 '+d.shenWei+'\n';
        if(d.moonName) txt+='🌙 月相：'+d.moonName+'\n';
        txt+='\n⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议';
        $('huangliResultHtml').textContent=txt;
    }).catch(e=>{$('huangliResultHtml').textContent='查询失败';});
}
function huangliToday(){setDefaultDate('huangli-date');huangliQuery();}
function huangliClear(){$('huangli-date').value='';$('huangliResult').style.display='none';}

// ═══════════════════════════════════════════════
// 塔罗牌
// ═══════════════════════════════════════════════
function taluoStart(){
    const spread=$('taluo-spread').value;
    const question=$('taluo-question').value.trim();
    const params={spread,question,name:'塔罗牌'};
    $('taluoResult').style.display='block';
    $('taluoResultHtml').textContent='正在抽牌解读中，请稍候...';
    toolApiRequest('taluo',params).then(d=>{
        if(!d){$('taluoResultHtml').textContent='抽牌失败，请重试';return;}
        $('taluoResultHtml').textContent=d.result||d.message||'解读完成';
        loadHistory('taluo');
    });
}
function taluoClear(){$('taluo-question').value='';$('taluoResult').style.display='none';}

// ═══════════════════════════════════════════════
// 个人中心 - 命盘存档
// ═══════════════════════════════════════════════
let userProfiles=[];
let userCollections=[];

let currentProfileType = 'self';

async function loadProfiles(){
    if(!currentUser){$('profileList').innerHTML='<div style="color:var(--text-3);font-size:0.8125rem;padding:20px;text-align:center;">登录后管理命盘存档</div>';return;}
    try{
        const search = ($('profileSearch')?.value || '').trim();
        const sort = $('profileSort')?.value || 'last_used';
        let url = `/api/profiles?type=${currentProfileType}&sort=${sort}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        const r=await fetch(url);
        const d=await r.json();
        userProfiles=d.profiles||d||[];
        renderProfiles();
    }catch(e){console.error('loadProfiles error:',e);$('profileList').innerHTML='<div style="color:var(--danger);font-size:0.8125rem;padding:20px;">加载失败</div>';}
}

function switchProfileTab(type, btn){
    currentProfileType = type;
    document.querySelectorAll('.profile-tab').forEach(t => t.classList.remove('active'));
    if(btn) btn.classList.add('active');
    loadProfiles();
}

function searchProfiles(){
    loadProfiles();
}

function renderProfiles(){
    const el=$('profileList');
    const typeLabels = {self:'自身命盘', customer:'客户命盘', collect:'收藏命盘'};
    const emptyMsg = `暂无${typeLabels[currentProfileType]||'存档'}，点击上方"新增"添加`;
    if(!userProfiles.length){el.innerHTML=`<div style="color:var(--text-3);font-size:0.8125rem;padding:20px;text-align:center;">${emptyMsg}</div>`;return;}
    el.innerHTML=userProfiles.map(p=>{
        const bt=p.birthTime||p.birth_time||'';
        const timeStr=bt?formatBirthTime(bt.length>=12?bt:bt.padEnd(12,'0')):'—';
        const lastUsed = p.lastUsedAt || p.last_used_at;
        const lastUsedStr = lastUsed ? timeAgo(new Date(lastUsed)) : '';
        return `<div class="profile-card${p.isDefault||p.is_default?' is-default':''}" onclick="fillFormFromProfile(${p.id})">
            <div class="pc-head">
                <span class="pc-name2">${escapeHtml(p.name||'')}</span>
                ${(p.isDefault||p.is_default)?'<span class="pc-default-badge">默认</span>':''}
            </div>
            <div class="pc-detail">
                性别：${escapeHtml(p.gender||'—')} ｜ 历法：${escapeHtml(p.calType||p.cal_type||'—')}<br>
                出生：${timeStr}<br>
                出生地：${escapeHtml(p.birthAddr||p.birth_addr||'—')}
                ${lastUsedStr?`<br><span style="font-size:0.6875rem;color:var(--text-3);">最近使用：${lastUsedStr}</span>`:''}
            </div>
            <div class="pc-actions" onclick="event.stopPropagation();">
                <button class="btn btn-ghost" style="padding:4px 10px;font-size:0.6875rem;" onclick="editProfile(${p.id})">编辑</button>
                ${!(p.isDefault||p.is_default)?`<button class="btn btn-ghost" style="padding:4px 10px;font-size:0.6875rem;" onclick="setDefaultProfile(${p.id})">设为默认</button>`:''}
                <button class="btn btn-ghost" style="padding:4px 10px;font-size:0.6875rem;color:var(--danger);" onclick="deleteProfile(${p.id})">删除</button>
            </div>
        </div>`;
    }).join('');
}

function timeAgo(date) {
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return '刚刚';
    if (diff < 3600) return Math.floor(diff/60) + '分钟前';
    if (diff < 86400) return Math.floor(diff/3600) + '小时前';
    if (diff < 2592000) return Math.floor(diff/86400) + '天前';
    return date.toLocaleDateString('zh-CN');
}

function showProfileForm(profile){
    $('profileFormCard').style.display='block';
    if(profile){
        $('profileFormTitle').textContent='编辑存档';
        $('profileEditId').value=profile.id;
        $('profileName').value=profile.name||'';
        $('profileGender').value=profile.gender||'男';
        $('profileCalType').value=profile.calType||profile.cal_type||'公历';
        $('profileIsDefault').checked=!!(profile.isDefault||profile.is_default);
        $('profileBirthAddr').value=profile.birthAddr||profile.birth_addr||'';
        $('profileFormType').value=profile.profileType||profile.profile_type||currentProfileType;
        if(profile.birthTime||profile.birth_time){
            const bt=(profile.birthTime||profile.birth_time).padEnd(12,'0');
            const dt=bt.slice(0,4)+'-'+bt.slice(4,6)+'-'+bt.slice(6,8)+'T'+bt.slice(8,10)+':'+bt.slice(10,12);
            $('profileBirthTime').value=dt;
        }else{$('profileBirthTime').value='';}
    }else{
        $('profileFormTitle').textContent='新增存档';
        $('profileEditId').value='';
        $('profileName').value='';
        $('profileGender').value='男';
        $('profileCalType').value='公历';
        $('profileBirthTime').value='';
        $('profileBirthAddr').value='';
        $('profileIsDefault').checked=false;
        $('profileFormType').value=currentProfileType;
    }
}

function hideProfileForm(){$('profileFormCard').style.display='none';}

async function saveProfile(){
    const editId=$('profileEditId').value;
    const name=$('profileName').value.trim();
    if(!name){alert('请输入姓名');return;}
    const data={
        name,
        gender:$('profileGender').value,
        calType:$('profileCalType').value,
        birthAddr:$('profileBirthAddr').value.trim(),
        isDefault:$('profileIsDefault').checked?1:0,
        profileType:$('profileFormType').value||currentProfileType,
    };
    const dt=$('profileBirthTime').value;
    if(dt){data.birthTime=dt.replace(/[-T:]/g,'').padEnd(12,'0').slice(0,12);}
    try{
        let r;
        if(editId){r=await apiFetch(`/api/profiles/${editId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});}
        else{r=await apiFetch('/api/profiles',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});}
        const d=await r.json();
        if(d.error){alert(d.error);return;}
        hideProfileForm();
        loadProfiles();
    }catch(e){alert('保存失败，请重试');}
}

function editProfile(id){
    const p=userProfiles.find(x=>x.id===id);
    if(p) showProfileForm(p);
}

async function setDefaultProfile(id){
    try{
        const r=await apiFetch(`/api/profiles/${id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({isDefault:1})});
        const d=await r.json();
        if(d.error){alert(d.error);return;}
        loadProfiles();
    }catch(e){alert('操作失败');}
}

async function deleteProfile(id){
    if(!confirm('确定要删除该命盘存档吗？')) return;
    try{
        const r=await apiFetch(`/api/profiles/${id}`,{method:'DELETE'});
        const d=await r.json();
        if(d.error){alert(d.error);return;}
        loadProfiles();
    }catch(e){alert('删除失败');}
}

async function exportProfiles(){
    try{
        const r=await fetch(`/api/profiles/export?type=${currentProfileType}`);
        const d=await r.json();
        if(d.error){alert(d.error);return;}
        const blob=new Blob([JSON.stringify(d,null,2)],{type:'application/json'});
        const url=URL.createObjectURL(blob);
        const a=document.createElement('a');
        a.href=url;
        a.download=`xuancetai_${currentProfileType}_${new Date().toISOString().slice(0,10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }catch(e){alert('导出失败');}
}

function fillFormFromProfile(id){
    const p=userProfiles.find(x=>x.id===id);
    if(!p) return;
    // 根据当前面板填入对应表单
    const panel=currentPanel;
    if(panel==='paipan'){
        $('paipanInput').value=[p.name,p.gender,p.cal_type,p.birth_time,p.birth_addr].filter(Boolean).join('，');
    }else if(panel==='ziwei'){
        if(p.gender)$('ziwei-gender').value=p.gender;
        if(p.cal_type)$('ziwei-cal').value=p.cal_type==='农历'?'lunar':'solar';
        if(p.birth_time){
            const bt=p.birth_time.padEnd(12,'0');
            $('ziwei-date').value=bt.slice(0,4)+'-'+bt.slice(4,6)+'-'+bt.slice(6,8);
        }
        if(p.birth_addr)$('ziwei-addr').value=p.birth_addr;
    }else if(panel==='zeji'){
        if(p.birth_addr)$('zeji-addr').value=p.birth_addr;
    }
    // 通用：切换到当前工具面板（不跳转）
    alert('已将「'+p.name+'」的信息填入当前工具表单');
}

// ═══════════════════════════════════════════════
// 个人中心 - 账号信息
// ═══════════════════════════════════════════════
function renderAccountInfo(){
    const el=$('accountInfo');
    if(!currentUser){el.innerHTML='<div style="color:var(--text-3);font-size:0.8125rem;text-align:center;padding:16px;">登录后查看账号信息</div>';return;}
    el.innerHTML=`<div style="display:flex;flex-direction:column;gap:8px;">
        <div style="display:flex;justify-content:space-between;"><span style="color:var(--text-3);">用户名</span><span style="color:var(--text-1);font-weight:500;">${escapeHtml(currentUser.username)}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="color:var(--text-3);">注册时间</span><span style="color:var(--text-1);">${currentUser.created_at?new Date(currentUser.created_at).toLocaleString('zh-CN'):'—'}</span></div>
    </div>`;
}

// ═══════════════════════════════════════════════
// 搜索功能
// ═══════════════════════════════════════════════
let _searchTimer=null;
function searchHistory(query){
    clearTimeout(_searchTimer);
    const q=query.trim();
    if(!q){loadHistory(currentHistoryType);return;}
    _searchTimer=setTimeout(async()=>{
        if(!currentUser){return;}
        try{
            const r=await apiFetch('/api/search?q='+encodeURIComponent(q));
            const d=await r.json();
            const el=$('historyList');
            const records=d.records||d||[];
            if(!records.length){el.innerHTML='<div style="padding:12px 20px;color:var(--text-3);font-size:0.75rem;">无搜索结果</div>';return;}
            el.innerHTML=records.map(rec=>{
                const t=rec.created_at?new Date(rec.created_at).toLocaleString('zh-CN',{month:'numeric',day:'numeric',hour:'numeric',minute:'numeric'}):'';
                const isCollected=(userCollections||[]).some(c=>c.target_id===rec.id);
                return `<div class="history-item" onclick="viewRecord(${rec.id},'${rec.app_type||'qimen'}')">
                    <div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-right:60px;">${escapeHtml(rec.question)}</div>
                    <div class="hi-time">${t}</div>
                    <button class="collection-star${isCollected?' collected':''}" onclick="event.stopPropagation();toggleCollection(${rec.id},this)" title="收藏">${isCollected?'⭐':'☆'}</button>
                    <button class="hi-del" title="删除" onclick="event.stopPropagation();requestDelete(${rec.id})">✕</button>
                </div>`;
            }).join('');
        }catch(e){console.error('searchHistory error:',e);}
    },400);
}

// ═══════════════════════════════════════════════
// 收藏功能
// ═══════════════════════════════════════════════
async function loadCollections(){
    if(!currentUser){userCollections=[];return;}
    try{
        const r=await apiFetch('/api/collections');
        const d=await r.json();
        userCollections=d.collections||d||[];
    }catch(e){userCollections=[];}
}

async function toggleCollection(recordId,btnEl){
    if(!currentUser){showModal('loginModal');return;}
    const existing=(userCollections||[]).find(c=>c.target_id===recordId);
    try{
        if(existing){
            await apiFetch(`/api/collections/${existing.id}`,{method:'DELETE'});
            userCollections=userCollections.filter(c=>c.target_id!==recordId);
            if(btnEl){btnEl.textContent='☆';btnEl.classList.remove('collected');}
        }else{
            const r=await apiFetch('/api/collections',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target_type:'record',target_id:recordId})});
            const d=await r.json();
            if(d.error){alert(d.error);return;}
            if(d.collection) userCollections.push(d.collection);
            if(btnEl){btnEl.textContent='⭐';btnEl.classList.add('collected');}
        }
    }catch(e){alert('操作失败，请重试');}
}

async function loadCollectionHistory(){
    if(!currentUser){$('historyList').innerHTML='<div style="padding:16px 20px;color:var(--text-3);font-size:0.75rem;text-align:center;">登录后查看收藏</div>';return;}
    if(!userCollections.length){$('historyList').innerHTML='<div style="padding:12px 20px;color:var(--text-3);font-size:0.75rem;">暂无收藏</div>';return;}
    // 加载每条收藏对应的记录
    let html='';
    for(const col of userCollections){
        try{
            const r=await fetch(`/api/records/${col.target_id}`);
            const rec=await r.json();
            if(rec.error) continue;
            const t=rec.created_at?new Date(rec.created_at).toLocaleString('zh-CN',{month:'numeric',day:'numeric',hour:'numeric',minute:'numeric'}):'';
            html+=`<div class="history-item" onclick="viewRecord(${rec.id},'${rec.app_type||'qimen'}')">
                <div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-right:60px;">${escapeHtml(rec.question)}</div>
                <div class="hi-time">${t}</div>
                <button class="collection-star collected" onclick="event.stopPropagation();toggleCollection(${rec.id},this);setTimeout(()=>loadCollectionHistory(),500);" title="取消收藏">⭐</button>
                <button class="hi-del" title="删除" onclick="event.stopPropagation();requestDelete(${rec.id})">✕</button>
            </div>`;
        }catch(e){}
    }
    $('historyList').innerHTML=html||'<div style="padding:12px 20px;color:var(--text-3);font-size:0.75rem;">暂无收藏</div>';
}

// ═══════════════════════════════════════════════
// 问事跟进
// ═══════════════════════════════════════════════
async function loadFollowups(recordId,container){
    try{
        const r=await apiFetch('/api/followups?record_id='+recordId);
        const d=await r.json();
        const followups=d.followups||d||[];
        renderFollowups(followups,container);
    }catch(e){console.error('loadFollowups error:',e);}
}

function renderFollowups(followups,container){
    let html='<div class="followup-timeline">';
    for(const fu of followups){
        const fbClass=fu.feedback==='已验证'?'verified':fu.feedback==='部分准确'?'partial':fu.feedback==='不准确'?'inaccurate':'pending';
        const t=fu.created_at?new Date(fu.created_at).toLocaleString('zh-CN'):'';
        html+=`<div class="followup-item">
            <div class="fu-time">${t}</div>
            <div class="fu-note">${escapeHtml(fu.note||'')}</div>
            ${fu.feedback?`<div class="fu-feedback ${fbClass}">${escapeHtml(fu.feedback)}</div>`:''}
        </div>`;
    }
    html+='</div>';
    html+=`<div style="margin-top:12px;">
        <textarea class="input-field" id="followupNote_${container}" rows="2" placeholder="添加跟进备注..." style="min-height:60px;font-size:0.8125rem;"></textarea>
        <div style="display:flex;gap:8px;margin-top:8px;align-items:center;">
            <select class="form-select" id="followupFeedback_${container}" style="width:auto;flex:0 0 auto;font-size:0.75rem;padding:6px 10px;">
                <option value="">选择反馈</option>
                <option value="待验证">待验证</option>
                <option value="已验证">已验证</option>
                <option value="部分准确">部分准确</option>
                <option value="不准确">不准确</option>
            </select>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:0.75rem;" onclick="submitFollowup(${container})">提交跟进</button>
        </div>
    </div>`;
    const el=document.getElementById(container);
    if(el) el.innerHTML=html;
}

async function submitFollowup(recordId){
    const noteEl=document.getElementById('followupNote_'+recordId);
    const fbEl=document.getElementById('followupFeedback_'+recordId);
    if(!noteEl) return;
    const note=noteEl.value.trim();
    if(!note){alert('请输入跟进备注');return;}
    try{
        const r=await apiFetch('/api/followups',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({record_id:recordId,note,feedback:fbEl?fbEl.value:''})});
        const d=await r.json();
        if(d.error){alert(d.error);return;}
        loadFollowups(recordId,'followupArea_'+recordId);
    }catch(e){alert('提交失败，请重试');}
}

// ═══════════════════════════════════════════════
// 社区面板
// ═══════════════════════════════════════════════
let communityCategory='all';
let communityPage=1;
let communitySearchQuery='';
let currentPostId=null;

const CATEGORY_LABELS={share:'分享',discuss:'讨论',ask:'求助',experience:'心得'};

function switchCommunityTab(cat){
    communityCategory=cat; communityPage=1;
    document.querySelectorAll('#communityTabs .ctab').forEach(t=>t.classList.toggle('active',t.dataset.cat===cat));
    loadCommunityPosts();
}

function searchPosts(){
    communitySearchQuery=$('communitySearch').value.trim();
    communityPage=1;
    loadCommunityPosts();
}

async function loadCommunityPosts(){
    const list=$('communityPostList');
    list.innerHTML='<div style="color:var(--text-3);font-size:0.8125rem;text-align:center;padding:40px;">加载中...</div>';
    try{
        let url='/api/posts?page='+communityPage;
        if(communityCategory!=='all') url+='&category='+communityCategory;
        if(communitySearchQuery) url+='&tag='+encodeURIComponent(communitySearchQuery);
        const res=await apiFetch(url);
        const d=await res.json();
        if(!d.posts||d.posts.length===0){
            list.innerHTML='<div style="color:var(--text-3);font-size:0.8125rem;text-align:center;padding:40px;">暂无帖子</div>';
            return;
        }
        list.innerHTML=d.posts.map(p=>`
            <div class="post-card" onclick="openPostDetail(${p.id})">
                ${p.imageUrl?'<div class="post-thumb" style="margin-bottom:8px;border-radius:8px;overflow:hidden;"><img src="'+p.imageUrl+'" style="width:100%;max-height:200px;object-fit:cover;" alt="帖子图片"></div>':''}
                <div class="post-title">${escapeHtml(p.title)}</div>
                <div class="post-meta">
                    <span class="pm-author">${escapeHtml(p.username||'匿名')}</span>
                    <span class="tag-badge">${CATEGORY_LABELS[p.category]||p.category}</span>
                    ${(p.tags||[]).map(t=>'<span class="tag-badge">'+escapeHtml(t)+'</span>').join('')}
                    <span class="pm-stat">❤️ ${p.likesCount||0}</span>
                    <span class="pm-stat">💬 ${p.commentsCount||0}</span>
                    <span>${p.createdAt?new Date(p.createdAt).toLocaleString('zh-CN'):''}</span>
                </div>
            </div>
        `).join('');
    }catch(e){
        list.innerHTML='<div style="color:var(--danger);font-size:0.8125rem;text-align:center;padding:40px;">加载失败</div>';
    }
}

async function openPostDetail(id){
    currentPostId=id;
    $('communityPostList').style.display='none';
    $('communityPostDetail').style.display='block';
    const detail=$('postDetailContent');
    detail.innerHTML='<div style="color:var(--text-3);text-align:center;padding:40px;">加载中...</div>';
    try{
        const res=await apiFetch('/api/posts/'+id);
        const p=await res.json();
        const isLiked=p.isLiked;
        detail.innerHTML=`
            <div class="card">
                <div class="card-header">
                    <span class="ch-title" style="font-size:1rem;">${escapeHtml(p.title)}</span>
                </div>
                <div class="card-body">
                    <div class="post-meta" style="margin-bottom:12px;">
                        <span class="pm-author">${escapeHtml(p.username||'匿名')}</span>
                        <span class="tag-badge">${CATEGORY_LABELS[p.category]||p.category}</span>
                        ${(p.tags||[]).map(t=>'<span class="tag-badge">'+escapeHtml(t)+'</span>').join('')}
                        <span>${p.createdAt?new Date(p.createdAt).toLocaleString('zh-CN'):''}</span>
                    </div>
                    ${p.imageUrl?'<div style="margin-bottom:12px;border-radius:10px;overflow:hidden;"><img src="'+p.imageUrl+'" style="width:100%;max-height:400px;object-fit:cover;border-radius:10px;" alt="帖子图片"></div>':''}
                    <div class="pd-content">${escapeHtml(p.content)}</div>
                    <div class="pd-actions">
                        <button class="like-btn ${isLiked?'liked':''}" onclick="togglePostLike(${id},this)">
                            ${isLiked?'❤️':'🤍'} <span>${p.likesCount||0}</span>
                        </button>
                        ${currentUser&&(p.userId===currentUser.id)?'<button class="btn btn-ghost" style="font-size:0.75rem;color:var(--danger);" onclick="deletePost('+id+')">删除</button>':''}
                    </div>
                    <div style="font-size:0.875rem;color:var(--text-2);margin-bottom:8px;">评论 (${(p.comments||[]).length})</div>
                    <div id="commentList">
                        ${(p.comments||[]).map(c=>`
                            <div class="comment-item">
                                <span class="ci-author">${escapeHtml(c.username||'匿名')}</span>
                                <span class="ci-time">${c.createdAt?new Date(c.createdAt).toLocaleString('zh-CN'):''}</span>
                                ${currentUser&&(c.userId===currentUser.id)?'<button style="float:right;font-size:0.6875rem;color:var(--danger);background:none;border:none;cursor:pointer;" onclick="deleteComment('+c.id+','+id+')">删除</button>':''}
                                <div class="ci-content">${escapeHtml(c.content)}</div>
                                ${(c.replies||[]).map(r=>'<div class="comment-item" style="margin-left:24px;margin-top:8px;border-top:1px solid var(--card-border);padding-top:8px;"><span class="ci-author">'+escapeHtml(r.username||'匿名')+'</span><span class="ci-time">'+(r.createdAt?new Date(r.createdAt).toLocaleString('zh-CN'):'')+'</span>'+(currentUser&&(r.userId===currentUser.id)?'<button style="float:right;font-size:0.6875rem;color:var(--danger);background:none;border:none;cursor:pointer;" onclick="deleteComment('+r.id+','+id+')">删除</button>':'')+'<div class="ci-content">'+escapeHtml(r.content)+'</div></div>').join('')}
                            </div>
                        `).join('')}
                    </div>
                    <div class="comment-input-row">
                        <input type="text" id="commentInput" placeholder="发表评论...">
                        <button class="btn btn-primary" style="padding:6px 14px;font-size:0.8125rem;" onclick="submitComment(${id})">发送</button>
                    </div>
                </div>
            </div>
        `;
    }catch(e){
        detail.innerHTML='<div style="color:var(--danger);text-align:center;padding:40px;">加载失败</div>';
    }
}

function closePostDetail(){
    $('communityPostDetail').style.display='none';
    $('communityPostList').style.display='block';
    currentPostId=null;
}

async function togglePostLike(id,btn){
    if(!currentUser){showModal('loginModal');return;}
    try{
        const res=await apiFetch('/api/posts/'+id+'/like',{method:'POST'});
        const d=await res.json();
        if(d.liked!==undefined){
            btn.classList.toggle('liked',d.liked);
            btn.innerHTML=(d.liked?'❤️':'🤍')+' <span>'+(d.likesCount||0)+'</span>';
        }
    }catch(e){console.error('like error',e);}
}

async function submitComment(postId){
    const input=$('commentInput');
    const content=input.value.trim();
    if(!content){return;}
    try{
        const res=await apiFetch('/api/posts/'+postId+'/comments',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({content})
        });
        const d=await res.json();
        if(d.error){$('newPostError').textContent=d.error;return;}
        input.value='';
        openPostDetail(postId);
    }catch(e){alert('评论失败，请重试');}
}

async function deleteComment(commentId,postId){
    if(!confirm('确定删除该评论？'))return;
    try{
        await apiFetch('/api/comments/'+commentId,{method:'DELETE'});
        openPostDetail(postId);
    }catch(e){alert('删除失败');}
}

async function deletePost(id){
    if(!confirm('确定删除该帖子？'))return;
    try{
        await apiFetch('/api/posts/'+id,{method:'DELETE'});
        closePostDetail();
        loadCommunityPosts();
    }catch(e){alert('删除失败');}
}

let _pendingPostData=null;  // 等待免责确认的帖子数据

function showNewPostModal(){
    if(!currentUser){showModal('loginModal');return;}
    $('newPostTitle').value='';$('newPostContent').value='';
    $('newPostCategory').value='share';$('newPostTags').value='';
    $('newPostError').textContent='';
    // 重置图片
    if($('newPostImage'))$('newPostImage').value='';
    if($('newPostImageName'))$('newPostImageName').textContent='';
    if($('newPostImagePreview'))$('newPostImagePreview').style.display='none';
    showModal('newPostModal');
}

function previewPostImage(input){
    const file=input.files&&input.files[0];
    if(!file)return;
    if(file.size>5*1024*1024){alert('图片不能超过5MB');input.value='';return;}
    const nameEl=$('newPostImageName');
    if(nameEl)nameEl.textContent=file.name;
    // 预览
    const reader=new FileReader();
    reader.onload=function(e){
        const thumb=$('newPostImageThumb');
        const preview=$('newPostImagePreview');
        if(thumb&&preview){thumb.src=e.target.result;preview.style.display='block';}
    };
    reader.readAsDataURL(file);
}

function removePostImage(){
    const input=$('newPostImage');
    if(input)input.value='';
    const nameEl=$('newPostImageName');
    if(nameEl)nameEl.textContent='';
    const preview=$('newPostImagePreview');
    if(preview)preview.style.display='none';
}

// 免责声明确认框复选框控制
document.addEventListener('DOMContentLoaded',function(){
    const cb=$('disclaimerAgree');
    const btn=$('disclaimerConfirmBtn');
    if(cb&&btn){
        cb.addEventListener('change',function(){
            btn.style.opacity=this.checked?'1':'0.5';
            btn.style.cursor=this.checked?'pointer':'not-allowed';
        });
    }
});

function confirmDisclaimer(){
    const cb=$('disclaimerAgree');
    if(!cb||!cb.checked){return;}
    hideModal('disclaimerModal');
    // 重置复选框
    cb.checked=false;
    if($('disclaimerConfirmBtn')){$('disclaimerConfirmBtn').style.opacity='0.5';$('disclaimerConfirmBtn').style.cursor='not-allowed';}
    // 执行之前暂存的发帖操作
    if(_pendingPostData){
        doSubmitNewPost(_pendingPostData);
        _pendingPostData=null;
    }
}

async function submitNewPost(){
    const title=$('newPostTitle').value.trim();
    const content=$('newPostContent').value.trim();
    const category=$('newPostCategory').value;
    const tagsStr=$('newPostTags').value.trim();
    if(!title||!content){$('newPostError').textContent='标题和内容不能为空';return;}

    // 暂存数据，弹出免责声明
    _pendingPostData={title,content,category,tagsStr};
    showModal('disclaimerModal');
}

async function doSubmitNewPost(data){
    const {title,content,category,tagsStr}=data;
    const tags=tagsStr?tagsStr.split(/[,，]/).map(t=>t.trim()).filter(Boolean):[];
    const imageInput=$('newPostImage');
    const hasImage=imageInput&&imageInput.files&&imageInput.files[0];

    try{
        let postResult;
        if(hasImage){
            // 先上传图片
            const imgForm=new FormData();
            imgForm.append('file',imageInput.files[0]);
            const upRes=await apiFetch('/api/upload',{method:'POST',body:imgForm});
            const upData=await upRes.json();
            if(upData.error){$('newPostError').textContent=upData.error;return;}

            // 再创建帖子（JSON方式+imageUrl）
            const res=await apiFetch('/api/posts',{
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({title,content,category,tags,imageUrl:upData.url})
            });
            postResult=await res.json();
        }else{
            const res=await apiFetch('/api/posts',{
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({title,content,category,tags})
            });
            postResult=await res.json();
        }
        if(postResult.error){$('newPostError').textContent=postResult.error;return;}
        hideModal('newPostModal');
        loadCommunityPosts();
    }catch(e){$('newPostError').textContent='发布失败，请重试';}
}

// ═══════════════════════════════════════════════
// 大师面板
// ═══════════════════════════════════════════════
let masterSpecialty='all';

function switchMasterTab(spec){
    masterSpecialty=spec;
    document.querySelectorAll('#masterTabs .ctab').forEach(t=>t.classList.toggle('active',t.dataset.spec===spec));
    loadMasters();
}

async function loadMasters(){
    const list=$('masterList');
    list.innerHTML='<div style="color:var(--text-3);font-size:0.8125rem;text-align:center;padding:40px;">加载中...</div>';
    try{
        let url='/api/masters';
        if(masterSpecialty!=='all') url+='?specialty='+encodeURIComponent(masterSpecialty);
        const res=await apiFetch(url);
        const d=await res.json();
        if(!d.masters||d.masters.length===0){
            list.innerHTML='<div style="color:var(--text-3);font-size:0.8125rem;text-align:center;padding:40px;">暂无大师</div>';
            return;
        }
        const avatarEmojis=['🧙','📿','🏯','📜','🌟','☯️','🕯️','🎯'];
        list.innerHTML=d.masters.map((m,i)=>`
            <div class="master-card" onclick="openMasterDetail(${m.id})">
                <div class="mc-avatar">${avatarEmojis[i%avatarEmojis.length]}</div>
                <div class="mc-info">
                    <div class="mc-name">${escapeHtml(m.displayName)}${m.certified?'<span class="cert-badge">✓</span>':''}</div>
                    <div class="mc-title">${escapeHtml(m.title||'')}</div>
                    <div class="mc-tags">${(m.specialties||[]).map(s=>'<span class="tag-badge">'+escapeHtml(s)+'</span>').join('')}</div>
                    <div class="mc-rating">${'★'.repeat(Math.round(m.rating||5))}${'☆'.repeat(5-Math.round(m.rating||5))} <span style="color:var(--text-3);font-size:0.75rem;">${(m.rating||5).toFixed(1)}</span></div>
                </div>
            </div>
        `).join('');
    }catch(e){
        list.innerHTML='<div style="color:var(--danger);font-size:0.8125rem;text-align:center;padding:40px;">加载失败</div>';
    }
}

async function openMasterDetail(id){
    $('masterList').style.display='none';
    $('masterDetail').style.display='block';
    const detail=$('masterDetailContent');
    detail.innerHTML='<div style="color:var(--text-3);text-align:center;padding:40px;">加载中...</div>';
    try{
        const res=await apiFetch('/api/masters/'+id);
        const m=await res.json();
        detail.innerHTML=`
            <div class="master-card" style="cursor:default;">
                <div class="mc-avatar" style="width:64px;height:64px;font-size:2rem;">🧙</div>
                <div class="mc-info">
                    <div class="mc-name" style="font-size:1.125rem;">${escapeHtml(m.displayName)}${m.certified?'<span class="cert-badge">✓</span>':''}</div>
                    <div class="mc-title">${escapeHtml(m.title||'')}</div>
                    <div class="mc-tags">${(m.specialties||[]).map(s=>'<span class="tag-badge">'+escapeHtml(s)+'</span>').join('')}</div>
                    <div class="mc-rating">${'★'.repeat(Math.round(m.rating||5))}${'☆'.repeat(5-Math.round(m.rating||5))} <span style="color:var(--text-3);font-size:0.75rem;">${(m.rating||5).toFixed(1)}</span></div>
                </div>
            </div>
            <div class="master-detail">
                <div class="md-bio">${escapeHtml(m.bio||'暂无简介')}</div>
                <div class="md-specialties"><strong style="color:var(--text-2);font-size:0.8125rem;">专长：</strong>${(m.specialties||[]).map(s=>'<span class="tag-badge" style="margin-left:4px;">'+escapeHtml(s)+'</span>').join('')}</div>
                <button class="md-consult" onclick="alertUpgrade()">咨询大师</button>
            </div>
        `;
    }catch(e){
        detail.innerHTML='<div style="color:var(--danger);text-align:center;padding:40px;">加载失败</div>';
    }
}

function closeMasterDetail(){
    $('masterDetail').style.display='none';
    $('masterList').style.display='block';
}

function showApplyMasterModal(){
    if(!currentUser){showModal('loginModal');return;}
    $('applyMasterName').value='';$('applyMasterTitle').value='';
    $('applyMasterSpec').value='';$('applyMasterBio').value='';
    $('applyMasterError').textContent='';
    showModal('applyMasterModal');
}

async function submitMasterApply(){
    const displayName=$('applyMasterName').value.trim();
    const title=$('applyMasterTitle').value.trim();
    const specStr=$('applyMasterSpec').value.trim();
    const bio=$('applyMasterBio').value.trim();
    if(!displayName||!specStr){$('applyMasterError').textContent='显示名和专长不能为空';return;}
    const specialties=specStr.split(/[,，]/).map(s=>s.trim()).filter(Boolean);
    try{
        const res=await apiFetch('/api/masters/apply',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({displayName,title,specialties,bio})
        });
        const d=await res.json();
        if(d.error){$('applyMasterError').textContent=d.error;return;}
        hideModal('applyMasterModal');
        alert('申请已提交，请等待审核');
    }catch(e){$('applyMasterError').textContent='提交失败，请重试';}
}

// ═══════════════════════════════════════════════
// 会员中心 & 付费内容
// ═══════════════════════════════════════════════

const LEVEL_MAP = {free:'免费用户',basic:'基础会员',premium:'高级会员',vip:'VIP会员'};
const LEVEL_CLASS = {free:'level-free',basic:'level-basic',premium:'level-premium',vip:'level-vip'};

async function loadMembership(){
    if(!currentUser){$('signInBtn')&&($('signInBtn').disabled=true);return;}
    try{
        const res=await apiFetch('/api/membership');
        const d=await res.json();
        const lv=d.level||'free';
        const pts=d.points||0;
        const exp=d.expire_at||null;
        if($('vipLevelText'))$('vipLevelText').textContent=LEVEL_MAP[lv]||lv;
        if($('vipPointsText'))$('vipPointsText').textContent=pts;
        if($('vipExpireText'))$('vipExpireText').textContent=exp?new Date(exp).toLocaleDateString('zh-CN'):'永久';
        if($('vipLevelBadge')){$('vipLevelBadge').textContent=LEVEL_MAP[lv]||lv;$('vipLevelBadge').className='level-badge '+(LEVEL_CLASS[lv]||'level-free');}
        if($('signInBtn')){$('signInBtn').disabled=!!d.signed_in_today;$('signInBtn').textContent=d.signed_in_today?'已签到 ✓':'每日签到 +10积分';}
    }catch(e){console.error('loadMembership error:',e);}
}

async function doSignIn(){
    if(!currentUser){showModal('loginModal');return;}
    try{
        const res=await apiFetch('/api/membership/sign-in',{method:'POST'});
        const d=await res.json();
        if(d.error){alert(d.error);return;}
        alert('签到成功！获得 +10 积分');
        loadMembership();loadPointLog();
    }catch(e){alert('签到失败，请重试');}
}

async function loadPointLog(){
    if(!currentUser)return;
    try{
        const res=await apiFetch('/api/points/log');
        const d=await res.json();
        const list=$('pointLogList');if(!list)return;
        const logs=d.logs||[];
        if(!logs.length){list.innerHTML='<div style="color:var(--text-3);font-size:0.8125rem;text-align:center;padding:20px;">暂无积分记录</div>';return;}
        list.innerHTML=logs.map(l=>`<div class="point-log-item">
            <div style="flex:1"><div class="pl-desc">${escapeHtml(l.description||l.action)}</div><div class="pl-time">${l.created_at?new Date(l.created_at).toLocaleString('zh-CN'):''}</div></div>
            <div class="pl-amount" style="color:${l.points>0?'var(--success)':'var(--danger)'}">${l.points>0?'+':''}${l.points}</div>
        </div>`).join('');
    }catch(e){console.error('loadPointLog error:',e);}
}

function alertUpgrade(){
    if(!currentUser){showModal('loginModal');return;}
    showModal('upgradeModal');
}

let paidCurrentCat='all';
function switchPaidTab(cat){
    paidCurrentCat=cat;
    document.querySelectorAll('#paidTabs .ctab').forEach(t=>{t.classList.toggle('active',t.dataset.cat===cat);});
    loadPaidContents();
}

async function loadPaidContents(){
    try{
        let url='/api/paid-contents?';
        if(paidCurrentCat!=='all')url+='content_type='+paidCurrentCat;
        const res=await apiFetch(url);
        const d=await res.json();
        const list=$('paidContentList');if(!list)return;
        const items=d.contents||[];
        if(!items.length){list.innerHTML='<div style="color:var(--text-3);font-size:0.8125rem;text-align:center;padding:40px;">暂无内容</div>';return;}
        list.innerHTML=items.map(c=>{
            const owned=c.owned||false;
            const priceClass=c.price===0?'free':'';
            return `<div class="content-card" id="cc-${c.id}">
                <div class="cc-title">${escapeHtml(c.title)}</div>
                <div class="cc-meta"><span class="tag-badge">${escapeHtml(c.content_type||'article')}</span>${c.master_name?'<span style="color:var(--text-3);font-size:0.75rem;">by '+escapeHtml(c.master_name)+'</span>':''}</div>
                <div class="cc-preview">${escapeHtml(c.preview||'')}</div>
                <div class="cc-actions">
                    <span class="price-tag ${priceClass}">${c.price===0?'免费':c.price+'积分'}</span>
                    ${owned?'<span class="owned-badge">已拥有 ✓</span>':''}
                    ${!owned&&c.price>0?'<button class="btn btn-primary" style="padding:4px 14px;font-size:0.6875rem;" onclick="purchaseContent('+c.id+')">购买</button>':''}
                    <button class="btn btn-secondary" style="padding:4px 14px;font-size:0.6875rem;" onclick="readContent('+c.id+',${owned})">阅读</button>
                </div>
            </div>`;
        }).join('');
    }catch(e){console.error('loadPaidContents error:',e);}
}

async function purchaseContent(id){
    if(!currentUser){showModal('loginModal');return;}
    if(!confirm('确认花费积分购买此内容？'))return;
    try{
        const res=await apiFetch('/api/paid-contents/'+id+'/purchase',{method:'POST'});
        const d=await res.json();
        if(d.error){alert(d.error);return;}
        alert('购买成功！');
        loadPaidContents();loadMembership();
    }catch(e){alert('购买失败，请重试');}
}

async function readContent(id,owned){
    try{
        const res=await apiFetch('/api/paid-contents/'+id);
        const d=await res.json();
        if(!d.full_content&&!owned){alert('请先购买此内容');return;}
        const cc=$('cc-'+id);if(!cc)return;
        const detail=document.createElement('div');
        detail.className='card';
        detail.style.marginTop='8px';
        detail.innerHTML=`<div class="card-body"><div style="white-space:pre-wrap;line-height:1.8;">${escapeHtml(d.full_content||d.preview||'暂无内容')}</div></div>`;
        cc.appendChild(detail);
    }catch(e){alert('加载失败');}
}

// ═══════════════════════════════════════════════
// 初始化
// ═══════════════════════════════════════════════
document.addEventListener('DOMContentLoaded',function(){
    setDefaultTime('liuyaoTime');
    setDefaultTime('meihuaTime');
    setDefaultDate('ziwei-date');
    setDefaultDate('zeji-start');
    setDefaultDate('zeji-end');
    setDefaultDate('huangli-date');
});
