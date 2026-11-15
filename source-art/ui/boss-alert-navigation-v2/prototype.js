(() => {
  const $=s=>document.querySelector(s),stage=$('#stage');
  const targets=[
    {id:'captain',defeated:false,name:'灰披队长',kind:'章节首领',level:10,place:'裂隘关',area:'S10',time:0,first:true},
    {id:'overseer',defeated:true,name:'断镐监工',kind:'精英',level:8,place:'断镐石场',area:'S13',time:0,first:false},
    {id:'warden',defeated:true,name:'守桥铠卫',kind:'章节首领',level:18,place:'断岳前堡',area:'H08',time:0,first:false},
    {id:'huntmaster',defeated:true,name:'裂风督猎',kind:'精英',level:17,place:'鹰背岩林',area:'H14',time:285,first:false},
    {id:'beast',defeated:false,name:'裂岳獠王',kind:'可选首领',level:18,place:'余烬废窑',area:'H17',time:0,first:true},
    {id:'oath',defeated:true,name:'三刃守誓阵',kind:'精英',level:16,place:'三誓军械廊',area:'U1-06',time:129,first:false},
    {id:'golem',defeated:false,name:'震炉巨像',kind:'精英',level:19,place:'震炉工坊',area:'U1-07',time:0,first:true}
  ];
  const NOTICE_DURATION_MS=10000;
  let level=4,current='overseer',mode='list',expanded=false,returnTo='entry',timer,noticeDeadline=0;
  const follows=new Set(),target=()=>targets.find(t=>t.id===current),eligible=()=>targets.filter(t=>t.defeated&&Math.abs(t.level-level)<=5).sort((a,b)=>Number(b.kind!=='精英')-Number(a.kind!=='精英')||(b.refreshedAt??0)-(a.refreshedAt??0)||b.level-a.level||a.id.localeCompare(b.id));
  const fmt=n=>`${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
  const captions={
    list:['按角色等级筛选，章节页签取消','仅列已击败且等级相差不超过5级的目标；首领优先，再按刷新时间和等级排序。'],
    entry:['固定兽首头像 · 首领与精英入口','头像始终固定，不随当前 Boss 切换；沿用 28 像素单层外框与原数量角标。'],
    notice:['顶部提示显示 10 秒后自动收起','无需点击；点击“前往”立即切入导航，之后仍可从首领入口查看目标。'],
    elite:['精英提示同样在 10 秒后自动收起','只提示当前等级 ±5 级范围的目标；实际生成后才通知。'],
    stack:['首领提示在上，10 秒后自动收起','普通消息向下让位；提示自动收起后，普通消息补回原位。'],
    route:['仍由任务框显示导航','默认单行；点“停止”暂停，点文字展开地点和路线。'],
    paused:['暂停后，需要点“继续”','遇敌、手动接管或打开面板后暂停，不会自行恢复移动。'],
    cooldown:['冷却目标可以提前前往','选择只改变选中态；关注和前往继续使用底部独立按钮。'],
    arrived:['抵达入口，由玩家发起再战','首次目标已在场；复战入口会在满足冷却后提供开战操作。'],
    quiet:['提示收起，入口仍在小地图圆边','点击“首领”查看当前等级相近的目标。']
  };
  function size(){const s=$('.stage-wrap').clientWidth/844;stage.style.transform=`scale(${s})`;$('.stage-wrap').style.height=`${390*s}px`;}
  new ResizeObserver(size).observe($('.stage-wrap'));
  function syncLevel(){
    $('#player-level').value=String(level);$('#hero-name').textContent=`拉斐尔 · Lv${level}`;
    const count=eligible().length;$('#entry-count').textContent=String(count);$('#boss-open').setAttribute('aria-label',`首领与精英：${count} 个等级相近的目标`);
    if(!eligible().some(t=>t.id===current))current=eligible()[0]?.id??'';
  }
  function list(){
    syncLevel();const a=eligible(),t=target(),listHeight=a.length?Math.min(2,a.length)*52+(Math.min(2,a.length)-1)*8:56;
    const panel=$('#target-panel');panel.classList.toggle('single',a.length===1);panel.classList.toggle('empty',!a.length);panel.style.setProperty('--list-height',`${listHeight}px`);
    $('#level-hint').innerHTML=`Lv${Math.max(1,level-5)}–${level+5}<span>${a.length} 个目标</span>`;
    const oldScroll=$('#encounter-list').scrollTop;
    $('#encounter-list').innerHTML=a.length?a.map(v=>`<button class="encounter" data-id="${v.id}" aria-pressed="${v.id===current}"><img src="assets/${v.id}.png" alt=""><span class="info"><span class="name">${v.name}</span><small>${v.place} · Lv${v.level}</small></span><span class="state ${v.time?'wait':''}">${v.time?fmt(v.time):v.first?'已出现':'可再战'}<small>${v.time?'后可再战':v.kind}</small></span></button>`).join(''):`<div class="empty-message">暂无已击败的 Lv${Math.max(1,level-5)}–${level+5} 首领或精英</div>`;
    $('#encounter-list').scrollTop=oldScroll;
    document.querySelectorAll('.encounter').forEach(b=>b.onclick=()=>{current=b.dataset.id;list();});
    $('#selected-detail').textContent=t?(t.time?`${t.place} · ${fmt(t.time)} 后可再战`:`${t.place} · ${t.first?'首次挑战':'抵达入口后发起再战'}`):'击败等级相近的首领或精英后解锁';
    $('#follow span').textContent=t&&follows.has(t.id)?'已关注':'关注提醒';$('#follow').setAttribute('aria-pressed',!!t&&follows.has(t.id));$('#follow').disabled=!t;
    $('#go span').textContent=t?.time?'提前前往':'自动前往';$('#go').disabled=!t;
  }
  function set(next){
    clearTimeout(timer);noticeDeadline=0;syncLevel();mode=next;stage.dataset.mode=next;const t=target(),showNotice=!!t&&['notice','elite','stack'].includes(next);
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.mode===next));
    $('#spawn-notice').hidden=!showNotice;$('#ordinary-message').hidden=next!=='stack';
    if(t){$('#notice-portrait').src=`assets/${t.id}.png`;$('#notice-title').innerHTML=`${t.name} <small>${t.first?'已出现':'可再战'}</small>`;$('#notice-place').textContent=`${t.place} · Lv${t.level}`;}
    const tracking=!!t&&['route','paused','arrived'].includes(next);$('#tracker').classList.toggle('expanded',expanded);
    $('#target').innerHTML=tracking?`${next==='route'?'↗ ':next==='paused'?'Ⅱ ':''}${t.name}${next==='arrived'?'':' <small>35m</small>'}`:'→ 夺回断轮磨坊 <small>35m</small>';
    $('#place').textContent=tracking?`${t.place} · ${t.first?'安全接近点':'首领入口'}`:'断轮磨坊';
    $('#progress').textContent=next==='paused'?'前方有敌人 · 已暂停':next==='arrived'?'已抵达 · 等待现场操作':'本段 35m · 第 1/2 段';
    $('#navigate').textContent=next==='route'?'停止':next==='paused'?'继续':next==='arrived'?'抵达':'出发';$('#navigate').disabled=next==='arrived';
    $('#fight').hidden=!(next==='arrived'&&t&&!t.first);$('#fight').disabled=!!t?.time;$('#fight').textContent=t?.time?'等待冷却':'发起再战';
    const c=captions[next];$('#caption-title').textContent=c[0];$('#caption').textContent=!t&&['notice','elite','stack','route'].includes(next)?'当前没有等级相近的目标，不显示范围外的首领。':c[1];
    $('#demo').textContent=next==='list'?'查看打开入口':next==='entry'?'点击首领按钮试试':next==='notice'||next==='elite'||next==='stack'?'重新播放 10 秒':next==='route'?'模拟抵达':next==='cooldown'?'模拟冷却结束':'查看目标列表';
    if(next==='list'||next==='cooldown')list();
    if(showNotice){noticeDeadline=performance.now()+NOTICE_DURATION_MS;const stacked=next==='stack';timer=setTimeout(()=>{set('quiet');if(stacked)$('#ordinary-message').hidden=false;},NOTICE_DURATION_MS);}
  }
  function changeLevel(value){const next=['route','paused','arrived'].includes(mode)?'list':mode;level=Number(value);syncLevel();set(next);}
  $('#player-level').onchange=e=>changeLevel(e.target.value);
  document.querySelectorAll('.states [data-mode]').forEach(b=>b.onclick=()=>{
    const m=b.dataset.mode,a=eligible();
    if(m==='cooldown'){current=a.find(t=>t.time)?.id??a[0]?.id??'';}
    else if(m==='notice'||m==='stack')current=a.find(t=>!t.time)?.id??a[0]?.id??'';
    else if(m==='elite')current=a.find(t=>t.kind==='精英'&&!t.time)?.id??a[0]?.id??'';
    set(m);
  });
  function open(){returnTo=['route','paused'].includes(mode)?'paused':mode==='arrived'?'arrived':'entry';set('list');}
  $('#boss-open').onclick=open;$('#close').onclick=()=>set(returnTo);$('#veil').onclick=()=>set(returnTo);
  for(const [id,title,description] of [['inventory-open','背包入口','点击后沿用现有背包界面。'],['checks-open','技能入口','点击后沿用现有技能界面，角标继续表示可用技能点。'],['settings-open','设置入口','点击后沿用现有设置界面。']]){
    $('#'+id).onclick=()=>{$('#caption-title').textContent=title;$('#caption').textContent=description+'这里仅展示入口外观与触控范围。';};
  }
  $('#notice-go').onclick=()=>{if(target())set('route');};$('#go').onclick=()=>{if(target())set('route');};
  $('#follow').onclick=()=>{if(!target())return;follows.has(current)?follows.delete(current):follows.add(current);list();};
  $('#navigate').onclick=()=>{if(target())set(mode==='route'?'paused':'route');};
  $('#tracker-text').onclick=()=>{expanded=!expanded;$('#tracker').classList.toggle('expanded',expanded);};
  $('#auto').onclick=()=>{if(mode==='route')set('paused');};
  $('#fight').onclick=()=>{set('quiet');$('#caption-title').textContent='已模拟发起再战';$('#caption').textContent='此处仅演示界面流转，实际战斗沿用游戏规则。';};
  $('#demo').onclick=()=>{
    if(mode==='list')set('entry');else if(mode==='entry')$('#boss-open').focus();
    else if(['notice','elite','stack'].includes(mode))set(mode);
    else if(mode==='route')set('arrived');else if(mode==='cooldown'){if(target()){target().time=0;target().refreshedAt=Date.now();}set('notice');}else open();
  };
  $('#hits').onclick=()=>{const on=stage.classList.toggle('hit-on');$('#hits').setAttribute('aria-pressed',on);};
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&['list','cooldown'].includes(mode))set(returnTo);});
  window.bossPreviewV2={set,changeLevel,get mode(){return mode},targets,get eligible(){return eligible()},get level(){return level},select(id){if(eligible().some(t=>t.id===id))current=id;},get selected(){return current},noticeDurationMs:NOTICE_DURATION_MS,get noticeRemainingMs(){return Math.max(0,noticeDeadline-performance.now())}};
  set('list');size();
})();
