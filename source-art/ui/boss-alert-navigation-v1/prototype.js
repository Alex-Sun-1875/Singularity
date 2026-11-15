(() => {
  const $ = s => document.querySelector(s);
  const game = $('#game');
  const targets = [
    {id:'BOSS_R1',chapter:1,name:'灰披队长',full:'裂隘统领·灰披队长',kind:'章节 Boss',level:10,area:'S10',place:'裂隘关',remaining:0,first:false},
    {id:'ELITE_01',chapter:1,name:'断镐监工',kind:'具名精英',level:8,area:'S13',place:'断镐石场',remaining:192},
    {id:'BOSS_R2',chapter:2,name:'守桥铠卫',full:'断岳铁卫·守桥铠卫',kind:'章节 Boss',level:18,area:'H08',place:'断岳前堡',remaining:0,first:false},
    {id:'ELITE_02',chapter:2,name:'裂风督猎',kind:'具名精英',level:17,area:'H14',place:'鹰背岩林',remaining:285},
    {id:'BEAST_RIDGEBREAKER',chapter:2,name:'裂岳獠王',kind:'可选 Boss',level:18,area:'H17',place:'余烬废窑',remaining:0,first:true},
    {id:'ELITE_06',chapter:2,name:'三刃守誓阵',kind:'具名精英',level:16,area:'U1-06',place:'三誓军械廊',remaining:144},
    {id:'ELITE_05',chapter:2,name:'震炉巨像',kind:'具名精英',level:19,area:'U1-07',place:'震炉工坊',remaining:406}
  ];
  const group={id:'hunt-H14-0-0',chapter:2,name:'烬牙群首',kind:'循环精英',level:18,area:'H14',place:'鹰背岩林',remaining:0,first:true,group:true};
  let selected='BOSS_R2',chapter=2,state='notice',timer,expanded=false,resumeState='quiet';
  const followed=new Set();
  const captions={
    notice:['到时只提醒，不接管操作','顶部显示 4 秒，随后收起。点“前往”才开始导航；错过提示，仍可从地图查看。'],
    elite:['精英真正出现后，再发本地提示','循环群首显示 3 秒轻提示；同地图同类 120 秒内合并横幅。点“前往”导航到安全接近点。'],
    list:['地图里集中查看，常驻 HUD 不加一块大面板','选目标后点击“自动前往”。倒计时、地点、是否首次挑战分开表达；更多目标在列表内滚动。'],
    route:['同一块任务框，接过临时导航','蓝色表示寻路中。原任务保留；本段距离与路线段数在展开态显示，点“停止”暂停。'],
    paused:['遇敌先停，继续由玩家决定','任务框变为琥珀色并显示原因。清敌、手动接管、关闭菜单后，都需要点“继续”。'],
    arrived:['抵达入口，开战仍是一次独立操作','先停在安全接近点。“抵达”不代表任务完成；准备好再点场景旁的“发起再战”。'],
    cooldown:['等待时间可见，也可以提前赶路','可开启关注提醒，或提前前往入口。等待不会积累额外次数；到时不自动生成 Boss 或开战。'],
    combat:['战斗时，信息让给预警与操作','新可挑战目标只更新地图与列表；战斗结束后合并提示。保留目标唯一的名称与血条。']
  };
  const chosen=()=>[...targets,group].find(t=>t.id===selected);
  const time=n=>`${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
  function resize(){const scale=$('.viewport').clientWidth/844;game.style.transform=`scale(${scale})`;$('.viewport').style.height=`${390*scale}px`;}
  new ResizeObserver(resize).observe($('.viewport'));
  function drawList(){
    const entries=[...targets,...(selected===group.id?[group]:[])].filter(t=>t.chapter===chapter);
    if(selected===group.id)entries.sort((a,b)=>Number(!!b.group)-Number(!!a.group));
    $('#list-summary').textContent=`已发现目标 · ${entries.filter(t=>!t.remaining).length} 可挑战`;
    $('#boss-list').innerHTML=entries.map(t=>`<button class="boss-row ${t.id===selected?'selected':''}" data-target="${t.id}" aria-pressed="${t.id===selected}"><span class="boss-symbol ${t.kind.includes('精英')?'elite':''}">${t.kind.includes('精英')?'◆':'♛'}</span><span class="boss-meta"><b>${t.name} <small style="display:inline">Lv${t.level}</small></b><small>${t.place} · ${t.area}</small></span><span class="boss-status ${t.remaining?'wait':''}">${t.remaining?time(t.remaining):t.first?'已出现':'可再战'}<small>${t.remaining?'后可再战':t.first?'首次挑战':'冷却结束'}</small></span></button>`).join('');
    document.querySelectorAll('[data-target]').forEach(b=>b.addEventListener('click',()=>{selected=b.dataset.target;drawList();}));
    document.querySelectorAll('[data-chapter]').forEach(b=>{b.classList.toggle('selected',Number(b.dataset.chapter)===chapter);b.setAttribute('aria-pressed',Number(b.dataset.chapter)===chapter);});
    const t=chosen();$('#follow').textContent=followed.has(t.id)?'已关注 ✓':'关注提醒';$('#follow').setAttribute('aria-pressed',followed.has(t.id));
    $('#panel-go').textContent=t.remaining?'提前前往':'自动前往';
    $('#selection-note').textContent=t.group?'仅显示本地循环精英；导航停在安全接近点。':t.remaining?'到时提醒一次；提前抵达也不会自动开战。':t.first?'抵达战场接近点后，由你发起挑战。':'抵达入口后，由你发起再战。';
  }
  function setState(next){
    clearTimeout(timer);state=next;game.dataset.state=next;
    const t=chosen();
    $('.map-count').textContent=`${targets.filter(v=>v.chapter===chapter&&!v.remaining).length+(t.group?1:0)} 可挑战`;
    document.querySelectorAll('[data-state]').forEach(b=>{if(b.tagName==='BUTTON')b.setAttribute('aria-pressed',b.dataset.state===next);});
    const c=captions[next];$('#caption-title').textContent=c[0];$('#caption-text').textContent=c[1];
    $('#notice').style.display=['notice','elite'].includes(next)?'flex':'none';$('#passive-message').style.display='none';
    $('#notice-name').textContent=`${t.name} · ${t.first?'已出现':'可再战'}`;$('#notice-detail').textContent=t.group?`${t.place} · 本地精英`:`${t.place} · ${t.first?'首次挑战':'已准备好'}`;
    $('.notice-crown').textContent=t.group?'◆':'♛';
    $('.notice-crown').style.color=t.group?'var(--amber)':'var(--gold)';
    const tracking=['route','paused','arrived'].includes(next);
    $('#quest').classList.toggle('expanded',expanded||next==='route'||next==='paused');
    $('#quest-place').textContent=tracking?`${t.place} · ${t.remaining?'提前前往':t.first?'安全接近点':'再战入口'}`:'旅程 · 第二章';
    $('#quest-name').textContent=tracking?`${next==='route'?'↗ ':next==='paused'?'Ⅱ ':''}${t.name}`:'夺取石梁前哨';
    $('#quest-progress').textContent=next==='route'?'本段 42m · 第 1/2 段':next==='paused'?'前方有敌人 · 已暂停':next==='arrived'?'入口安全点 · 等待操作':'48m · 固定守军';
    $('#nav-action').textContent=next==='route'?'停止':next==='paused'?'继续':next==='arrived'?'抵达':'出发';
    $('#nav-action').disabled=next==='arrived';
    $('#start-fight').textContent=t.remaining?`${time(t.remaining)} 后可再战`:'发起再战';$('#start-fight').disabled=!!t.remaining;
    $('#start-fight').style.display=next==='arrived'&&!t.first?'block':'none';
    $('#arrival-point small').textContent=t.first?'安全接近点':'再战入口';
    if(next==='arrived'&&t.first){$('#caption-text').textContent='已在安全接近点停下。目标已在场，由玩家决定靠近或攻击，不提供“生成精英”按钮。';}
    $('#fight-label span').textContent=t.name;
    $('#simulate').hidden=!['notice','elite','route','paused','cooldown','combat'].includes(next);
    $('#simulate').textContent=next==='elite'?'演示 3 秒收起':next==='notice'?'演示 4 秒收起':next==='route'?'模拟抵达入口':next==='paused'?'模拟手动接管':next==='cooldown'?'演示冷却结束':'模拟战斗中收到提醒';
    if(next==='list'||next==='cooldown')drawList();
  }
  function navigate(){setState('route');}
  document.querySelectorAll('.state-tabs button').forEach(b=>b.addEventListener('click',()=>{if(b.dataset.state==='elite'){selected=group.id;chapter=2;}else if(b.dataset.state==='cooldown'){selected='ELITE_02';chapter=2;chosen().remaining=285;}else if(['notice','combat','arrived'].includes(b.dataset.state)){selected='BOSS_R2';chapter=2;}setState(b.dataset.state);}));
  document.querySelectorAll('[data-chapter]').forEach(b=>b.addEventListener('click',()=>{chapter=Number(b.dataset.chapter);selected=targets.find(t=>t.chapter===chapter).id;drawList();}));
  $('#map-open').addEventListener('click',()=>{resumeState=['route','paused'].includes(state)?'paused':state==='arrived'?'arrived':'quiet';setState('list');});
  $('#notice-go').addEventListener('click',navigate);$('#panel-go').addEventListener('click',navigate);
  $('#close-panel').addEventListener('click',()=>{setState(resumeState);if(resumeState==='paused')$('#quest-progress').textContent='菜单已关闭 · 点击继续';});
  $('#scrim').addEventListener('click',()=>setState(resumeState));
  captions.quiet=['提示收起后，仍能找到目标','地图保留可挑战数量；点地图查看已发现的首领与精英。原任务与操作保持可用。'];
  $('#quest-info').addEventListener('click',()=>{expanded=!expanded;$('#quest').classList.toggle('expanded',expanded);});
  $('#nav-action').addEventListener('click',()=>{if(state==='route')setState('paused');else navigate();});
  $('#manual').addEventListener('click',()=>{if(['route','paused'].includes(state)){setState('paused');$('#quest-progress').textContent='已手动接管 · 点击继续';}});
  $('#follow').addEventListener('click',()=>{followed.has(selected)?followed.delete(selected):followed.add(selected);drawList();});
  $('#automatic').addEventListener('click',()=>{if(state==='route')setState('paused');$('#passive-message').textContent='自动模式保持原入口';$('#passive-message').style.display='block';timer=setTimeout(()=>$('#passive-message').style.display='none',2400);});
  $('#start-fight').addEventListener('click',()=>setState('combat'));
  $('#show-hit').addEventListener('click',()=>{const on=game.classList.toggle('show-hit');$('#show-hit').setAttribute('aria-pressed',on);$('#show-hit').textContent=on?'隐藏触控范围':'查看触控范围';});
  $('#simulate').addEventListener('click',()=>{
    if(state==='notice'||state==='elite'){const delay=state==='elite'?3000:4000;timer=setTimeout(()=>setState('quiet'),delay);$('#simulate').textContent=`${delay/1000} 秒后收起…`;}
    else if(state==='route')setState('arrived');
    else if(state==='paused'){$('#quest-progress').textContent='已手动接管 · 点击继续';}
    else if(state==='cooldown'){chosen().remaining=0;setState('notice');}
    else if(state==='combat'){$('.map-count').textContent='3 可挑战';$('#caption-text').textContent='已模拟收到新提醒：只更新地图数量，未弹横幅。战斗结束并安全后再汇总。';}
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&['list','cooldown'].includes(state))setState('quiet');});
  $('#roster').innerHTML=targets.map(t=>`<tr><td>第${t.chapter===1?'一':'二'}章</td><td>${t.full??t.name}</td><td>${t.kind}</td><td>Lv${t.level}</td><td>${t.place} <span style="color:#8f9e94">${t.area}</span></td><td>击败后 10 分钟</td></tr>`).join('');
  window.bossPreview={setState,targets,get state(){return state},select(id){selected=id;chapter=chosen().chapter;},get selected(){return selected}};
  setState('notice');resize();
})();
