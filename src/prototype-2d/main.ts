import {createDemo,EQUIPMENT,type InputFrame,type GameEvent} from './core';

declare const Phaser:any;
const P=64, W=24*P,H=16*P;
const $=<T extends HTMLElement=HTMLElement>(id:string)=>document.getElementById(id) as T;
const bridge=createDemo();
const manifests:Record<string,any>={};
const held=new Set<string>(),keys=new Set<string>();
const toScreen=(p:{x:number;z:number})=>({x:(p.x+12)*P,y:(8-p.z)*P});
let started=false,paused=false,ready=false,move={x:0,z:0},aim:number|undefined;
let scene:TrialScene,noticeUntil=0,lastSave=0,completedShown=false;

function clearInput(){held.clear();keys.clear();move={x:0,z:0};aim=undefined;bridge.game.cancelInput();$('stick').style.transform='translate(-50%,-50%)';document.querySelectorAll('.is-held').forEach(el=>el.classList.remove('is-held'));}
function notice(text:string,seconds=2.8){$('notice').textContent=text;noticeUntil=performance.now()+seconds*1000;$('notice').classList.add('visible');}
function setPause(value:boolean){paused=value;clearInput();$('pause-panel').hidden=!value;$('pause').setAttribute('aria-pressed',String(value));bridge.save();}
function begin(resume=false){if(!ready)return;if(resume&&!bridge.load())notice('未能读取存档，已开始新试炼');started=true;paused=false;completedShown=false;$('intro').hidden=true;$('ending').hidden=true;$('pause-panel').hidden=true;clearInput();scene.refreshActors();bridge.save();}
function restart(){bridge.restart();completedShown=false;started=true;paused=false;$('ending').hidden=true;$('intro').hidden=true;$('pause-panel').hidden=true;clearInput();scene.refreshActors();bridge.save();notice('已回到入口营火，可切换剑、弓或杖');}

function handle(events:GameEvent[]){
 for(const e of events){
  if(e.text&&['notice','inspect','reward','item','demo_complete','checkpoint'].includes(e.type))notice(e.text);
  if(e.type==='hit'&&e.at)scene?.floatText(e.at,String(e.value??''),0xf8d78f);
  if(e.type==='hurt'){scene?.cameras.main.shake(95,.002);scene?.playSound('hit');}
  if(e.type==='hit'){scene?.playSound('hit');}
  if(e.type==='demo_complete')scene?.playSound('complete');
 }
}

class TrialScene extends Phaser.Scene {
 [key:string]:any;
 actors=new Map<string,any>();
 shadows=new Map<string,any>();
 deathTimes=new Map<string,number>();
 previous=new Map<string,{x:number;z:number}>();
 effects:any;chest:any;chestMark:any;hero:any;lastAction='';soundAt=new Map<string,number>();
 constructor(){super('WhitebranchTrial');}
 preload(){
  this.load.image('hall','assets/whitebranch-hall.png');this.load.image('props','assets/props.png');
  for(const [id,m]of Object.entries(manifests))for(const [action,entry]of Object.entries<any>(m.actions))this.load.spritesheet(`${id}:${action}`,`assets/characters/${id}/${entry.image}`,{frameWidth:m.frameWidth,frameHeight:m.frameHeight});
  for(const name of ['sword','arrow','spell','hit','interact','complete'])this.load.audio(name,`assets/audio/${name}.wav`);
  this.load.on('progress',(p:number)=>{$<HTMLButtonElement>('begin').textContent=`准备旅途 ${Math.round(p*100)}%`;});
  this.load.on('loaderror',(f:any)=>notice(`资源加载失败：${f.key}，请刷新重试`,30));
 }
 create(){
  scene=this;this.add.image(W/2,H/2,'hall').setDisplaySize(W,H).setDepth(-100);
  const t=this.textures.get('props');
  t.add('pillar',0,120,20,390,590);t.add('chest',0,640,100,630,490);t.add('crate',0,60,680,510,590);t.add('brazier',0,760,620,420,620);
  for(const o of bridge.area.obstacles.filter(o=>o.kind==='column')){const p=toScreen(o);this.add.ellipse(p.x,p.y+5,95,40,0x12151a,.30).setDepth(p.y-1);this.add.image(p.x,p.y,'props','pillar').setOrigin(.5,.96).setDisplaySize(126,190).setDepth(p.y);}
  const camp=toScreen({x:-8.3,z:-2.7});this.add.image(camp.x,camp.y,'props','brazier').setOrigin(.5,.97).setDisplaySize(88,130).setDepth(camp.y);
  for(const q of [{x:-9.4,z:3.4},{x:9.3,z:-4.4}]){const p=toScreen(q);this.add.image(p.x,p.y,'props','crate').setOrigin(.5,.96).setDisplaySize(70,80).setDepth(p.y);}
  const c=toScreen({x:8,z:4});this.chest=this.add.image(c.x,c.y,'props','chest').setOrigin(.5,.94).setDisplaySize(104,82).setDepth(c.y);this.chestMark=this.add.text(c.x,c.y-94,'封印匣',{fontFamily:'serif',fontSize:'18px',color:'#f7da9d',stroke:'#201710',strokeThickness:4}).setOrigin(.5,1).setDepth(c.y+1);
  this.effects=this.add.graphics().setDepth(2000);
  this.refreshActors();
  this.cameras.main.setBounds(20,20,W-40,H-40);this.fit();this.scale.on('resize',()=>this.fit());
  this.input.on('pointerdown',(p:any)=>{if(!p.wasTouch&&p.event?.target?.tagName==='CANVAS'&&started&&!paused){held.add('attack');this.aimPointer(p);}});
  this.input.on('pointermove',(p:any)=>{if(!p.wasTouch&&started&&!paused)this.aimPointer(p);});
  this.input.on('pointerup',(p:any)=>{if(!p.wasTouch)held.delete('attack');});
  this.input.on('pointerupoutside',(p:any)=>{if(!p.wasTouch){held.delete('attack');bridge.game.cancelInput();}});
  this.input.mouse?.disableContextMenu();
  ready=true;$<HTMLButtonElement>('begin').disabled=false;$<HTMLButtonElement>('begin').textContent='进入白枝前厅';$('resume').hidden=!bridge.inspect().hasSave;
  (globalThis as any).__demo2d={bridge,scene:this,inspect:()=>({...bridge.inspect(),started,paused,ready,render:'Phaser 3 / pre-rendered 2D sprites'})};
 }
 fit(){this.cameras.main.setZoom(this.scale.height<550?.74:.96);}
 aimPointer(pointer:any){const p=this.cameras.main.getWorldPoint(pointer.x,pointer.y),h=toScreen(bridge.game.state.player);aim=Math.atan2(p.x-h.x,h.y-p.y);}
 refreshActors(){
  for(const a of this.actors.values())a.destroy();for(const a of this.shadows.values())a.destroy();this.actors.clear();this.shadows.clear();this.deathTimes.clear();this.previous.clear();
  const list=[{id:'player',model:'raphael',x:bridge.game.state.player.x,z:bridge.game.state.player.z},...bridge.game.state.enemies.map(e=>({id:e.id,model:'raider',x:e.x,z:e.z}))];
  for(const a of list){const p=toScreen(a),m=manifests[a.model];const shadow=this.add.ellipse(p.x,p.y+5,43,18,0x101515,.34);this.shadows.set(a.id,shadow);const sprite=this.add.sprite(p.x,p.y,`${a.model}:idle`,0).setOrigin(m.origin[0]/m.frameWidth,m.origin[1]/m.frameHeight).setScale(P*m.camera.worldUnitsPerPixel);this.actors.set(a.id,sprite);if(a.id==='demo-archer')sprite.setTint(0xc5d0a3);if(a.id==='player')this.hero=sprite;}
  // A static companion uses the same licensed pre-rendered cast, when available.
  this.companion?.destroy();this.companionLabel?.destroy();
  const m=manifests.mira;if(m){const p=toScreen({x:-7,z:-1});this.companion=this.add.sprite(p.x,p.y,'mira:idle',0).setOrigin(m.origin[0]/m.frameWidth,m.origin[1]/m.frameHeight).setScale(P*m.camera.worldUnitsPerPixel).setDepth(p.y);this.companionLabel=this.add.text(p.x,p.y-112,'弥菈',{fontFamily:'serif',fontSize:'16px',color:'#eee0bd',stroke:'#201710',strokeThickness:4}).setOrigin(.5).setDepth(p.y);}
  this.cameras.main.startFollow(this.hero,true,.12,.12);
 }
 playSound(name:string){if(!started||this.sound.locked)return;const now=performance.now();if(now-(this.soundAt.get(name)??0)<85)return;this.soundAt.set(name,now);this.sound.play(name,{volume:.22});}
 floatText(at:{x:number;z:number},text:string,color:number){const p=toScreen(at),s=this.add.text(p.x,p.y-65,text,{fontSize:'22px',fontFamily:'Georgia,serif',color:'#'+color.toString(16),stroke:'#22140e',strokeThickness:3}).setOrigin(.5).setDepth(2100);this.tweens.add({targets:s,y:s.y-38,alpha:0,duration:650,onComplete:()=>s.destroy()});}
 setActor(id:string,model:string,state:string,angle:number,clock:number,position:{x:number;z:number},hurt=false,fraction?:number){
  const sprite=this.actors.get(id),m=manifests[model];if(!sprite)return;
  let action=m.actions[state]?state:'idle';const meta=m.actions[action];
  // Native model +Z faces upward at yaw0. The atlas row 'down' is the artist's
  // front view; convert the game's north-facing angle to this row convention.
  const index=((Math.round((Math.PI-angle)/(2*Math.PI)*m.directions.length)%m.directions.length)+m.directions.length)%m.directions.length;
  const frame=fraction!==undefined?Math.min(meta.frames-1,Math.floor(Math.max(0,fraction)*meta.frames)):Math.floor(clock*meta.fps)%meta.frames;
  sprite.setTexture(`${model}:${action}`,index*meta.frames+frame);
  const p=toScreen(position);sprite.setPosition(p.x,p.y).setDepth(p.y);sprite.setAlpha(state==='death'?.72:1);
  if(hurt)sprite.setTintFill(0xffb6a3);else if(id==='demo-archer')sprite.setTint(0xc5d0a3);else sprite.clearTint();
  this.shadows.get(id)?.setPosition(p.x,p.y+5).setDepth(p.y-.5).setAlpha(state==='death'?.1:.34);
 }
 drawEffects(){
  const g=this.effects,s=bridge.game.state,p=toScreen(s.player),time=s.time;g.clear();
  g.lineStyle(1.5,0xc9f0d4,.75);g.strokeEllipse(p.x,p.y+6,48,20);
  for(const e of s.enemies){const q=toScreen(e);if(e.hp<=0)continue;g.fillStyle(0x150d0e,.8);g.fillRoundedRect(q.x-25,q.y-108,50,5,2);g.fillStyle(0xb25244,1);g.fillRoundedRect(q.x-25,q.y-108,50*e.hp/e.maxHp,5,2);
   if(e.phase==='windup'){const a=e.targetAngle,span=e.kind==='archer'?.065:.67,r=e.kind==='archer'?300:91;g.fillStyle(0xd85d45,.16+.1*Math.sin(time*12));g.beginPath();g.moveTo(q.x,q.y);for(let i=0;i<=14;i++){const t=a-span+span*2*i/14;g.lineTo(q.x+Math.sin(t)*r,q.y-Math.cos(t)*r*.73);}g.closePath();g.fillPath();g.lineStyle(1.5,0xf78e5d,.7);g.strokePath();}
  }
  const a=s.action;if(a){const h=Math.min(1,a.elapsed/a.duration),isSword=['sword','skill','push'].includes(a.kind);
   if(isSword&&a.elapsed>.08&&a.elapsed<.38){const span=a.kind==='skill'?1.9:1.2,r=a.kind==='push'?55:82;g.lineStyle(a.kind==='skill'?9:5,a.kind==='skill'?0xffd772:0xf9e3ad,Math.sin(Math.min(1,(a.elapsed-.08)/.3)*Math.PI)*.9);g.beginPath();for(let i=0;i<=20;i++){const t=a.angle-span+span*2*i/20,x=p.x+Math.sin(t)*r,y=p.y-Math.cos(t)*r*.72-18;if(i===0)g.moveTo(x,y);else g.lineTo(x,y);}g.strokePath();}
   if(a.kind==='bowAim'){const r=22+Math.min(1,a.elapsed/.8)*14;g.lineStyle(2,0xf3d18a,.8);g.strokeCircle(p.x+Math.sin(a.angle)*60,p.y-Math.cos(a.angle)*60-25,r);}
   if(a.kind.startsWith('spell:')){g.lineStyle(3,0x8bd8f0,1-h);g.strokeEllipse(p.x,p.y,50+h*140,25+h*70);}
   if(a.kind==='dash'){g.lineStyle(3,0xb6e9dc,.3);g.strokeEllipse(p.x,p.y+5,60,25);}
  }
  for(const q of s.projectiles){const o=toScreen(q),c=q.owner==='enemy'?0xff916c:q.kind==='arrow'?0xf8d78d:0x98e5ef;g.lineStyle(q.kind==='arrow'?2.5:5,c,.88);g.lineBetween(o.x-Math.sin(q.angle)*22,o.y+Math.cos(q.angle)*22,o.x,o.y);g.fillStyle(0xfff0cc,1);g.fillCircle(o.x,o.y,q.kind==='arrow'?2:4);}
  for(const f of s.fireZones){const q=toScreen(f);g.fillStyle(0xe89b32,.25);g.fillEllipse(q.x,q.y,f.radius*P*2,f.radius*P*1.4);}
  const c=toScreen({x:8,z:4});if(s.enemies.every(e=>e.hp<=0)&&!bridge.completed){g.lineStyle(2,0xf5d482,.65+.25*Math.sin(time*3));g.strokeEllipse(c.x,c.y,102,46);this.chestMark.setText('封印匣 · 可领取');}
 }
 update(_time:number,delta:number){
  if(!ready)return;
  if(started&&!paused&&!bridge.completed&&bridge.game.state.status!=='dead'&&innerWidth>innerHeight){
   const input:InputFrame={x:move.x+(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0),z:move.z+(keys.has('KeyW')?1:0)-(keys.has('KeyS')?1:0),attack:held.has('attack')||keys.has('KeyJ'),dash:held.has('dash')||keys.has('Space'),skill:held.has('skill')||keys.has('KeyR'),spell:held.has('spell')||keys.has('KeyQ')?0:undefined};
   if(aim!==undefined)input.aim=aim;else if(input.attack||input.skill||input.spell!==undefined){const p=bridge.game.state.player,target=bridge.game.state.enemies.filter(e=>e.hp>0).sort((a,b)=>Math.hypot(a.x-p.x,a.z-p.z)-Math.hypot(b.x-p.x,b.z-p.z))[0];if(target)input.aim=Math.atan2(target.x-p.x,target.z-p.z);}
   handle(bridge.advance(Math.min(.04,delta/1000),input));
  }
  const s=bridge.game.state,a=s.action,p=s.player,old=this.previous.get('player'),moving=old&&Math.hypot(p.x-old.x,p.z-old.z)>.00001;
  const weaponSuffix=s.equipment.weapon==='W07'?'_bow':s.equipment.weapon==='W11'?'_staff':'';
  const type=p.hp<=0?'death':a?.kind==='dash'?'dodge':a?.kind==='bowAim'||a?.kind==='bow'||a?.kind==='skill'&&weaponSuffix==='_bow'?'attack_bow':a?.kind==='staff'||a?.kind==='skill'&&weaponSuffix==='_staff'?'attack_staff':a?.kind.startsWith('spell:')?'attack_staff':a?'attack_sword':(moving?'walk':'idle')+weaponSuffix;
  if(a&&this.lastAction!==a.id){this.lastAction=a.id;this.playSound(a.kind.startsWith('spell')?'spell':a.kind.includes('bow')?'arrow':a.kind==='staff'?'spell':'sword');}
  let fraction=a?a.kind==='bowAim'?Math.min(.65,a.elapsed/.8*.65):a.kind==='bow'?.65+.35*Math.min(.999,a.elapsed/a.duration):Math.min(.999,a.elapsed/a.duration):undefined;
  if(p.hp<=0){if(!this.deathTimes.has('player'))this.deathTimes.set('player',performance.now()/1000);fraction=Math.min(.999,(performance.now()/1000-this.deathTimes.get('player')!)/.9);}
  this.setActor('player','raphael',type,p.angle,s.time,p,p.hurtTime>0,fraction);this.previous.set('player',{x:p.x,z:p.z});
  for(const e of s.enemies){const old=this.previous.get(e.id),moving=old&&Math.hypot(e.x-old.x,e.z-old.z)>.00001;if(e.hp<=0&&!this.deathTimes.has(e.id))this.deathTimes.set(e.id,s.time);const dead=this.deathTimes.get(e.id),suffix=e.kind==='archer'?'_bow':'';this.setActor(e.id,'raider',e.hp<=0?'death':e.phase==='windup'||e.phase==='active'?(e.kind==='archer'?'attack_bow':'attack_sword'):(moving?'walk':'idle')+suffix,e.angle,s.time,e,false,dead!==undefined?Math.min(.999,(s.time-dead)/.9):undefined);this.previous.set(e.id,{x:e.x,z:e.z});}
  this.drawEffects();this.renderHud();
  if(started&&!paused&&performance.now()-lastSave>1800){bridge.save();lastSave=performance.now();}
 }
 renderHud(){
  const s=bridge.game.state,p=s.player,view=bridge.inspect();$('health-fill').style.width=`${100*p.hp/p.maxHp}%`;$('health-text').textContent=`${Math.ceil(p.hp)} / ${p.maxHp}`;$('focus-fill').style.width=`${100*p.focus/p.maxFocus}%`;$('objective').textContent=view.objective;$('kill-count').textContent=`${2-view.enemiesRemaining} / 2`;$('weapon-name').textContent=EQUIPMENT[s.equipment.weapon].name;
  document.querySelectorAll<HTMLElement>('[data-weapon]').forEach(el=>{el.classList.toggle('selected',el.dataset.weapon===s.equipment.weapon);el.setAttribute('aria-pressed',String(el.dataset.weapon===s.equipment.weapon));});
  const interaction=document.querySelector<HTMLElement>('[data-action="interact"]');if(interaction){interaction.classList.toggle('available',!!view.nearby);interaction.title=view.nearby?.label??'靠近目标后交互';}
  if(performance.now()>noticeUntil)$('notice').classList.remove('visible');
  if(started&&(bridge.completed||s.status==='dead')&&!completedShown){completedShown=true;clearInput();$('ending').hidden=false;$('ending-title').textContent=bridge.completed?'封印匣已取回':'在营火旁重整';$('ending-text').textContent=bridge.completed?'白枝前厅已清理。下一段旅程，等你决定。':'观察敌人的红色预警，闪避后再出手。';$('ending-summary').textContent=bridge.completed?`击败守卫 2 / 2 · 生命 ${Math.ceil(p.hp)} · 获得黑契封印 ×3`:'你可以在入口切换武器，再试一次。';bridge.save();}
 }
}

function bindControls(){
 const joy=$('joystick');let joyId:number|null=null,center={x:0,y:0};
 const updateJoy=(e:PointerEvent)=>{if(e.pointerId!==joyId)return;const dx=e.clientX-center.x,dy=e.clientY-center.y,r=joy.clientWidth*.34,d=Math.hypot(dx,dy),k=Math.min(1,r/Math.max(.001,d));move={x:dx*k/r,z:-dy*k/r};aim=undefined;$('stick').style.transform=`translate(calc(-50% + ${dx*k}px),calc(-50% + ${dy*k}px))`;};
 joy.addEventListener('pointerdown',e=>{if(!started||paused||joyId!==null)return;joyId=e.pointerId;const r=joy.getBoundingClientRect();center={x:r.left+r.width/2,y:r.top+r.height/2};joy.setPointerCapture(e.pointerId);updateJoy(e);});
 joy.addEventListener('pointermove',updateJoy);for(const ev of ['pointerup','pointercancel','lostpointercapture'])joy.addEventListener(ev,((e:PointerEvent)=>{if(e.pointerId===joyId){joyId=null;move={x:0,z:0};$('stick').style.transform='translate(-50%,-50%)';}}) as EventListener);
 document.querySelectorAll<HTMLElement>('[data-action]').forEach(el=>{const action=el.dataset.action!;let pointer:number|null=null;el.addEventListener('pointerdown',e=>{if(!started||paused||pointer!==null)return;e.preventDefault();pointer=e.pointerId;el.setPointerCapture(pointer);el.classList.add('is-held');if(action==='interact'){handle(bridge.interact());scene.playSound('interact');}else held.add(action);});const release=(e:PointerEvent)=>{if(pointer!==e.pointerId)return;pointer=null;held.delete(action);el.classList.remove('is-held');if(e.type!=='pointerup')bridge.game.cancelInput();};for(const ev of ['pointerup','pointercancel','lostpointercapture'])el.addEventListener(ev,release as EventListener);});
 document.querySelectorAll<HTMLElement>('[data-weapon]').forEach(el=>el.addEventListener('click',()=>{if(bridge.equip(el.dataset.weapon!)){clearInput();notice(`已装备${EQUIPMENT[el.dataset.weapon!].name}`);}else notice(bridge.game.equipmentAvailability().reason);}));
 $('begin').addEventListener('click',()=>begin());$('resume').addEventListener('click',()=>begin(true));$('restart').addEventListener('click',restart);$('again').addEventListener('click',restart);$('pause').addEventListener('click',()=>{if(started)setPause(!paused);});$('continue').addEventListener('click',()=>setPause(false));
 document.addEventListener('keydown',e=>{if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code))e.preventDefault();if(e.code==='Escape'&&!e.repeat&&started)setPause(!paused);if(e.code==='KeyF'&&!e.repeat&&started&&!paused)handle(bridge.interact());if(['Digit1','Digit2','Digit3'].includes(e.code)&&!e.repeat&&started&&!paused){const id={Digit1:'W01',Digit2:'W07',Digit3:'W11'}[e.code]!;if(bridge.equip(id)){clearInput();notice(`已装备${EQUIPMENT[id].name}`);}else notice(bridge.game.equipmentAvailability().reason);}if(!paused)keys.add(e.code);});document.addEventListener('keyup',e=>keys.delete(e.code));
 addEventListener('blur',()=>{clearInput();if(started&&!bridge.completed)setPause(true);});document.addEventListener('visibilitychange',()=>{if(document.hidden){clearInput();if(started)bridge.save();if(started&&!bridge.completed)setPause(true);}});
 addEventListener('pagehide',()=>{if(started)bridge.save();});
}

async function boot(){
 $<HTMLButtonElement>('begin').disabled=true;
 for(const id of ['raphael','raider']){const response=await fetch(`assets/characters/${id}/manifest.json`);if(!response.ok)throw Error(`缺少人物资源：${id}`);manifests[id]=await response.json();}
 // Mira is an optional static companion, never a blocking runtime dependency.
 const mira=await fetch('assets/characters/mira/manifest.json');if(mira.ok)manifests.mira=await mira.json();
 bindControls();new Phaser.Game({type:Phaser.AUTO,parent:'game',backgroundColor:'#171714',width:innerWidth,height:innerHeight,scale:{mode:Phaser.Scale.RESIZE,autoCenter:Phaser.Scale.CENTER_BOTH},render:{antialias:true,roundPixels:false},input:{activePointers:4},audio:{disableWebAudio:false},scene:[TrialScene]});
}
boot().catch(error=>{$<HTMLButtonElement>('begin').textContent='资源未就绪，请刷新';notice(error.message,60);console.error(error);});
