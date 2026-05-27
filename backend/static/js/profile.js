// ═══ 个人中心页面脚本 ═══

let userProfiles=[];
let currentProfileType='self';

// ═══ 初始化 ═══
document.addEventListener('DOMContentLoaded', function(){
    // home.js 已经有 currentUser 和 auth 逻辑
    // 延迟执行让 home.js 的 autoCheckAuth 先完成
    setTimeout(()=>{
        loadProfiles();
        renderAccountInfo();
    }, 300);

    // 监听登录/注册成功后刷新个人中心数据
    // 通过覆写 updateNavUser 在登录后触发刷新
    const origUpdateNavUser = window.updateNavUser;
    if(origUpdateNavUser){
        window.updateNavUser = function(){
            origUpdateNavUser();
            loadProfiles();
            renderAccountInfo();
        };
    }
});

// ═══ 命盘存档 ═══
async function loadProfiles(){
    const el=$('profileList');
    if(!el) return;
    if(!currentUser){
        el.innerHTML='<div class="profile-empty"><div class="profile-empty-icon">🔒</div><p>登录后管理命盘存档</p><p style="font-size:0.75rem;color:var(--text-3);margin-bottom:16px;">命盘存档跨设备同步，永不丢失</p><button class="btn btn-accent btn-sm" onclick="showLogin()">立即登录</button></div>';
        return;
    }
    try{
        const search=($('profileSearch')?.value||'').trim();
        const sort=$('profileSort')?.value||'last_used';
        let url=`/api/profiles?type=${currentProfileType}&sort=${sort}`;
        if(search) url+=`&search=${encodeURIComponent(search)}`;
        const r=await fetch(url,{credentials:'include'});
        const d=await r.json();
        userProfiles=d.profiles||d||[];
        renderProfiles();
    }catch(e){
        console.error('loadProfiles error:',e);
        el.innerHTML='<div class="profile-empty"><div class="profile-empty-icon">❌</div><p>加载失败</p></div>';
    }
}

function switchProfileTab(type,btn){
    currentProfileType=type;
    document.querySelectorAll('.profile-tab').forEach(t=>t.classList.remove('active'));
    if(btn) btn.classList.add('active');
    loadProfiles();
}

function searchProfiles(){loadProfiles();}

function renderProfiles(){
    const el=$('profileList');
    if(!el) return;
    const typeLabels={self:'自身命盘',customer:'客户命盘',collect:'收藏命盘'};
    const emptyMsg=`暂无${typeLabels[currentProfileType]||'存档'}，点击上方"新增"添加`;
    if(!userProfiles.length){
        el.innerHTML=`<div class="profile-empty"><div class="profile-empty-icon">📭</div><p>${emptyMsg}</p></div>`;
        return;
    }
    el.innerHTML=userProfiles.map(p=>{
        const bt=p.birthTime||p.birth_time||'';
        const timeStr=bt?formatBirthTime(bt.length>=12?bt:bt.padEnd(12,'0')):'—';
        const lastUsed=p.lastUsedAt||p.last_used_at;
        const lastUsedStr=lastUsed?timeAgo(new Date(lastUsed)):'';
        return `<div class="p-card${(p.isDefault||p.is_default)?' is-default':''}">
            <div class="p-card-head">
                <span class="p-card-name">${escapeHtml(p.name||'')}</span>
                ${(p.isDefault||p.is_default)?'<span class="p-card-badge">默认</span>':''}
            </div>
            <div class="p-card-detail">
                性别：${escapeHtml(p.gender||'—')} ｜ 历法：${escapeHtml(p.calType||p.cal_type||'—')}<br>
                出生：${timeStr}<br>
                出生地：${escapeHtml(p.birthAddr||p.birth_addr||'—')}
                ${lastUsedStr?`<br><span style="font-size:0.6875rem;color:var(--text-3);">最近使用：${lastUsedStr}</span>`:''}
            </div>
            <div class="p-card-actions">
                <button class="btn btn-outline btn-sm" onclick="editProfile(${p.id})">编辑</button>
                ${!(p.isDefault||p.is_default)?`<button class="btn btn-outline btn-sm" onclick="setDefaultProfile(${p.id})">设为默认</button>`:''}
                <button class="btn btn-outline btn-sm" style="color:var(--danger);border-color:var(--danger);" onclick="deleteProfile(${p.id})">删除</button>
            </div>
        </div>`;
    }).join('');
}

function formatBirthTime(bt){
    if(!bt||bt.length<8) return '—';
    const y=bt.slice(0,4),m=bt.slice(4,6),d=bt.slice(6,8);
    const h=bt.length>=10?bt.slice(8,10):'';
    const min=bt.length>=12?bt.slice(10,12):'';
    let s=`${y}-${m}-${d}`;
    if(h) s+=` ${h}:${min||'00'}`;
    return s;
}

function timeAgo(date){
    const now=new Date();
    const diff=Math.floor((now-date)/1000);
    if(diff<60) return '刚刚';
    if(diff<3600) return Math.floor(diff/60)+'分钟前';
    if(diff<86400) return Math.floor(diff/3600)+'小时前';
    if(diff<2592000) return Math.floor(diff/86400)+'天前';
    return date.toLocaleDateString('zh-CN');
}

function showProfileForm(profile){
    $('profileFormCard').style.display='block';
    if(profile){
        $('profileFormTitle').textContent='✎ 编辑存档';
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
        $('profileFormTitle').textContent='✎ 新增存档';
        $('profileEditId').value='';
        $('profileName').value='';
        $('profileGender').value='男';
        $('profileCalType').value='公历';
        $('profileBirthTime').value='';
        $('profileBirthAddr').value='';
        $('profileIsDefault').checked=false;
        $('profileFormType').value=currentProfileType;
    }
    // 滚动到表单位置
    $('profileFormCard').scrollIntoView({behavior:'smooth',block:'center'});
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
    if(!currentUser){alert('请先登录');return;}
    try{
        const r=await fetch(`/api/profiles/export?type=${currentProfileType}`,{credentials:'include'});
        const d=await r.json();
        if(d.error){alert(d.error);return;}
        const blob=new Blob([JSON.stringify(d,null,2)],{type:'application/json'});
        const url=URL.createObjectURL(blob);
        const a=document.createElement('a');
        a.href=url;
        a.download=`shian_profiles_${currentProfileType}_${new Date().toISOString().slice(0,10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }catch(e){alert('导出失败');}
}

// ═══ 账号信息 ═══
function renderAccountInfo(){
    const el=$('accountInfo');
    if(!el) return;
    if(!currentUser){
        el.innerHTML='<div class="profile-empty"><div class="profile-empty-icon">🔒</div><p>登录后查看账号信息</p></div>';
        return;
    }
    const avatarHtml=currentUser.avatar
        ?`<img src="${currentUser.avatar}" class="profile-avatar-img" alt="头像">`
        :currentUser.username.charAt(0).toUpperCase();
    el.innerHTML=`
        <div class="account-info-row" style="align-items:center;">
            <span class="account-info-label">头像</span>
            <span class="profile-avatar-large" onclick="clickProfileAvatar()" title="点击更换头像">${avatarHtml}</span>
            <input type="file" id="profileAvatarInput" accept="image/*" style="display:none" onchange="uploadProfileAvatar(this)">
        </div>
        <div class="account-info-row">
            <span class="account-info-label">用户名</span>
            <span class="account-info-value">${escapeHtml(currentUser.username)}</span>
        </div>
        <div class="account-info-row">
            <span class="account-info-label">注册时间</span>
            <span class="account-info-value">${currentUser.created_at?new Date(currentUser.created_at).toLocaleString('zh-CN'):'—'}</span>
        </div>
    `;
}
function clickProfileAvatar(){
    const inp=$('profileAvatarInput');
    if(inp)inp.click();
}
async function uploadProfileAvatar(input){
    const file=input.files&&input.files[0];
    if(!file)return;
    if(file.size>5*1024*1024){alert('图片大小不能超过5MB');return;}
    const fd=new FormData();
    fd.append('file',file);
    try{
        const r=await apiFetch('/api/avatar',{method:'POST',body:fd});
        const d=await r.json();
        if(d.error){alert(d.error);return;}
        currentUser.avatar=d.url;
        renderAccountInfo();
        if(typeof updateNavUser==='function')updateNavUser();
    }catch(e){alert('头像上传失败，请重试');}
}
