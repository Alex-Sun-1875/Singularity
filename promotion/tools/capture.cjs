// Local promotional capture of the current Cocos build. No runtime source changes.
// Setup is an explicitly requested, disposable level-20 presentation fixture.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),http=require('node:http');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'promotion');
const {chromium,devices}=require(path.join(root,'src/cocos/node_modules/playwright'));
const family=process.argv[2]||'FIR',seconds=Number(process.argv[3]||24),qaOnly=process.argv.includes('--qa'),loadingOnly=process.argv.includes('--loading'),panelsOnly=process.argv.includes('--panels')||qaOnly;
const setups={
 WAR:{name:'破军战技',weapon:'DG_A01',area:'H14',position:{x:16,z:-36}},
 BOW:{name:'逐风弓术',weapon:'DG_A03',area:'H14',position:{x:16,z:-39}},
 FIR:{name:'烈焰秘术',weapon:'DG_A04',area:'H14',position:{x:16,z:-39}},
 THU:{name:'雷霆秘术',weapon:'DG_A05',area:'H14',position:{x:16,z:-39}},
};
if(!setups[family])throw Error('Unknown family');
for(const dir of ['screenshots','videos/raw','records'])fs.mkdirSync(path.join(out,dir),{recursive:true});
const build=path.join(root,'src/cocos/build/'+(panelsOnly||loadingOnly?'concept-2d-promotion-ui':'concept-2d-promotion'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const main=path.join(build,'assets/main',fs.readdirSync(path.join(build,'assets/main')).find(n=>/^index\..*\.js$/.test(n)));
async function mainCapture(){
 const server=http.createServer((req,res)=>{const route=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(build,'.'+(route==='/'?'/index.html':route));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile())return res.writeHead(404).end();const type={'.js':'text/javascript','.html':'text/html','.json':'application/json','.wasm':'application/wasm','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}[path.extname(file)];if(type)res.setHeader('Content-Type',type);fs.createReadStream(file).pipe(res);});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=d3d11','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 const errors=[],consoleErrors=[],report={family,...setups[family],seconds,buildProfile:'test',source:'local HTML rendering of production Cocos assets; not TapTap device recording',version:require(path.join(root,'package.json')).version,mainSha256:sha(main),setup:'Level 20; rank 5 skills (promotional fixture exceeds natural skill-point budget); native level-20 enhancement and gem caps; no monster-stat or damage-rule overrides; no persistent journey writes.'};
 try{
  const dimensions=qaOnly?{width:844,height:390}:{width:960,height:540};
  const context=await browser.newContext({...devices['Pixel 7'],viewport:dimensions,screen:dimensions,deviceScaleFactor:qaOnly?3:2});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
  // Slow only transport in this isolated capture, so the real boot cover can be photographed.
  if(loadingOnly)await page.route('**/assets/**/native/**',async route=>{await new Promise(r=>setTimeout(r,850));await route.continue();});
  await page.addInitScript(()=>{
   globalThis.promoAudioTaps=[];
   if(globalThis.AudioNode){const connect=AudioNode.prototype.connect,seen=new WeakSet(),contexts=new WeakMap();AudioNode.prototype.connect=function(destination,...args){const result=connect.call(this,destination,...args);if(destination===this.context.destination&&!seen.has(this)){seen.add(this);let tap=contexts.get(this.context);if(!tap){tap=this.context.createMediaStreamDestination();contexts.set(this.context,tap);promoAudioTaps.push({context:this.context,tap});}connect.call(this,tap);}return result;};}
  });
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d&hair=dante');
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.findPromoApp=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
  if(loadingOnly){
   await page.waitForFunction(()=>{const a=findPromoApp(),l=a?.loadingScreen;return l?.root?.active&&l?.background?.spriteFrame&&l.progress>=.04&&l.progress<.99;},undefined,{timeout:180000,polling:25});
   const state=await page.evaluate(async()=>{const a=findPromoApp(),l=a.loadingScreen,cc=await System.import('cc');await new Promise(r=>cc.director.once(cc.Director.EVENT_AFTER_DRAW,r));return {active:l.root.active,progress:l.progress,status:l.status,artwork:!!l.background.spriteFrame,menu:a.menu,level:a.session?.state.progression.level};});
   if(!state.active||!state.artwork)throw Error('Native loading screen disappeared before capture');
   await page.screenshot({path:path.join(out,'screenshots','game-loading.jpg'),type:'jpeg',quality:93});
   fs.writeFileSync(path.join(out,'records','game-loading.json'),JSON.stringify({source:report.source,mainSha256:report.mainSha256,buildProfile:'test',state,transportDelayMs:850,progressModified:false,normalSaveModified:false,errors,consoleErrors},null,2));
   console.log(JSON.stringify({phase:'loading-captured',...state,errors}));return;
  }
  async function ready(){const deadline=Date.now()+180000;while(true){if(await page.evaluate(()=>{const a=findPromoApp();return !!(a?.session&&a?.actors&&!a.loading&&!a.preparingPage&&a.platform.auth.ready);}))return;if(Date.now()>deadline)throw Error('Scene readiness timed out');await page.waitForTimeout(200);}}
  await ready();
  report.configuration=await page.evaluate(async({family,setup,allWeapons})=>{
   const mod=n=>System.import('chunks:///_virtual/'+n+'.ts'),a=findPromoApp(),s=a.session.state;
   const [pr,eq,loadout,skills,forgeA,forgeB,gems,world,supplies]=await Promise.all(['Progression','Equipment','CombatLoadouts','PureSkills','EquipmentForging','EquipmentForging2','Gems','WorldData','Supplies'].map(mod));
   const forge=forgeA.forgingThreshold?forgeA:forgeB;
   // No save is exported: the ordinary browser/profile and its journey are untouched.
   a.save=()=>true;a.click('begin');a.enabled=false;a.clearInput(false);a.automation.stop();
   s.progression=pr.freshProgression();const p=s.progression;p.level=20;p.totalXp=pr.cumulativeXp(20);p.xpReceipts={'promotion:level20':p.totalXp};p.secondChapter=true;p.ultimateGiftClaimed=true;p.unspentPoints=0;p.skillPoints=0;
   Object.assign(p.attributes,{strength:10,dexterity:10,intellect:10,vitality:25});p.attributes[family==='WAR'?'strength':family==='BOW'?'dexterity':'intellect']=52;
   for(const id of Object.keys(skills.COMBAT_SKILLS))p.learned[id]=5;
   const worn={weapon:setup.weapon,offhand:null,head:'A02',chest:'LC1_B_E',hands:'LC2_T_E',feet:'SQ_HUNT_BOOTS',ringLeft:'DG_L05',ringRight:'LC1_T_L',necklace:'DG_A02',spells:[null,null]};
   const items=[...new Set([...Object.values(worn).filter(x=>typeof x==='string'),...allWeapons,'DG_L01','DG_L02','DG_L03','DG_L04'])];
   s.inventory={};s.provenance={};for(const id of items){s.inventory[id]=1;s.provenance[id]='promotion:disposable-fixture';}
   Object.assign(s.equipment,worn);loadout.prepareCombatLoadout(s.combat,setup.weapon,p,family);
   // Resolve caps from the current modules. 20 currently allows +2 and tier-II / 2 sockets.
   for(const id of items){const d=eq.EQUIPMENT[id],rank=Math.min(2,d.maxEnhance);s.forging.experience[id]=forge.forgingThreshold(d,rank);s.forging.rolls[id]=forge.forgingRolls(s.seed,d,rank);const count=Math.min(gems.gemCapacity(d),gems.gemSocketCapForLevel(20));s.gems.items[id]={opened:count,sockets:Array.from({length:5},(_,i)=>i<count?{stat:i===0?(d.slot==='weapon'?'power':'maxHp'):'criticalChance',tier:gems.gemTierForLevel(20),units:gems.gemUnits(d)}:null)};}
   a.session.recalculate();Object.assign(s.player,{hp:s.player.maxHp,focus:s.player.maxFocus});for(const d of Object.values(supplies.SUPPLIES))s.player[d.stock]=d.capacity;s.combat.charge=100;s.status='playing';s.dialogue=null;s.dice.active=false;
   const events=[],old=a.process.bind(a);a.process=(batch,...rest)=>{events.push(...batch.map(e=>({time:s.time,...JSON.parse(JSON.stringify(e))})));return old(batch,...rest);};globalThis.promoEvents=events;
   const appearance=await mod('Hairstyles');if(!appearance.rememberHeadgearHidden(true))throw Error('Appearance preference save failed');
   a.session.enter(world.AREAS[setup.area],{x:0,z:-40});a.menu='';a.hud.clearModal();a.returnToMainMenu=false;await a.rebuild();a.enabled=false;
   if(!a.actors.player.playerHairstyles().some(h=>h.id==='dante'&&h.selected)||appearance.headgearVisible(s.equipment.head))throw Error('Expected Dante hairstyle with hidden headgear');
   return {level:p.level,ranks:p.learned,equipment:s.equipment,attributes:p.attributes,forging:s.forging.experience,gemTier:gems.gemTierForLevel(20),sockets:gems.gemSocketCapForLevel(20),enemyCount:s.enemies.length,health:s.player.maxHp,weapon:setup.weapon,appearance:{head:s.equipment.head,hood:false,hidden:appearance.headgearHidden(),hairstyles:a.actors.player.playerHairstyles()}};
  },{family,setup:setups[family],allWeapons:Object.values(setups).map(x=>x.weapon)});
  await ready();
  await page.evaluate(()=>{const a=findPromoApp();a.enabled=false;a.automation.stop();a.toast='';a.toastTime=0;a.music?.start();});
  await page.mouse.click(480,280);
  let rawFile;
  await page.exposeFunction('promoWriteChunk',data=>fs.appendFileSync(rawFile,Buffer.from(data,'base64')));
  await page.evaluate(()=>{
   globalThis.promoStartRecorder=async()=>{
    const cc=await System.import('cc'),stream=cc.game.canvas.captureStream(30);
    for(const {context,tap} of promoAudioTaps){await context.resume();for(const track of tap.stream.getAudioTracks())stream.addTrack(track.clone());}
    const mime=['video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm'].find(x=>MediaRecorder.isTypeSupported(x));
    const recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:16000000,audioBitsPerSecond:192000}),writes=[];
    recorder.ondataavailable=e=>{if(e.data.size)writes.push(e.data.arrayBuffer().then(b=>{let binary='';for(const byte of new Uint8Array(b))binary+=String.fromCharCode(byte);return promoWriteChunk(btoa(binary));}));};
    globalThis.promoRecorder={recorder,writes,stream};recorder.start(1000);return {mime,width:cc.game.canvas.width,height:cc.game.canvas.height,audioTracks:stream.getAudioTracks().length};
   };
   globalThis.promoStopRecorder=async()=>{const {recorder,writes,stream}=promoRecorder;await new Promise(r=>{recorder.onstop=r;recorder.stop();});await Promise.all(writes);for(const track of stream.getTracks())track.stop();};
  });
  async function startRecording(name){rawFile=path.join(out,'videos/raw',name+'.webm');fs.writeFileSync(rawFile,Buffer.alloc(0));return page.evaluate(()=>promoStartRecorder());}
  // Capture management pages before combat, paused on the same H14 stone terrain.
  await page.evaluate(()=>{const a=findPromoApp();a.click('inventory');a.enabled=true;});await ready();
  report.panels={area:await page.evaluate(()=>findPromoApp().session.state.area),position:{x:0,z:-40},menus:['inventory','attributes','checks','profession']};
  console.log(JSON.stringify({phase:'panels',family,area:report.panels.area}));
  if(panelsOnly){
   const panelStart=Date.now(),timeline=[],checks=[],shotDir=qaOnly?path.join(root,'src/cocos/test-results/equipment-inspection'):path.join(out,'screenshots');fs.mkdirSync(shotDir,{recursive:true});if(!qaOnly)await startRecording(family+'-panels');
   async function shot(name,run,wait=2400){
    const start=(Date.now()-panelStart)/1000;if(run)await run();await ready();await page.waitForTimeout(650);
    checks.push(await page.evaluate(async()=>{
     const cc=await System.import('cc'),a=findPromoApp();function all(n){return [n,...n.children.flatMap(all)];}const nodes=all(a.hud.modal),body=nodes.find(n=>n.name==='EquipmentDetailContent');
     if(!body)return {menu:a.menu,area:a.session.state.area};
     const labels=body.children.filter(n=>n.getComponent(cc.Label)),bounds=labels.map(n=>({name:n.name,text:n.getComponent(cc.Label).string,top:n.position.y+n.getComponent(cc.UITransform).height/2,bottom:n.position.y-n.getComponent(cc.UITransform).height/2})).sort((a,b)=>b.top-a.top);
     return {menu:a.menu,area:a.session.state.area,quality:nodes.find(n=>n.name==='EquipmentInspectionQuality')?.getComponent(cc.Label).string,bounds,nonOverlapping:bounds.every((x,i)=>!i||bounds[i-1].bottom>=x.top-.1),scrollbar:!!body.parent.parent.getChildByName('RpgScrollbar')};
    }));
    await page.screenshot({path:path.join(shotDir,`${family}-${name}.jpg`),type:'jpeg',quality:93});await page.waitForTimeout(qaOnly?100:wait);timeline.push({name,start,end:(Date.now()-panelStart)/1000});
   }
   const select=id=>page.evaluate(async id=>{const a=findPromoApp(),panel=await System.import('chunks:///_virtual/EquipmentPanels.ts');panel.recordEquipmentChange(a.session,id,'');a.modalKey='';a.renderModal();},id);
   const scroll=(effect=false)=>page.evaluate(async effect=>{const cc=await System.import('cc'),a=findPromoApp();function all(n){return [n,...n.children.flatMap(all)];}const body=all(a.hud.modal).find(n=>n.name==='EquipmentDetailContent'),sv=body.parent.parent.getComponent(cc.ScrollView),label=body.getChildByName('EquipmentDetailUniqueEffect');if(effect&&label)sv.scrollToOffset(new cc.Vec2(0,-label.position.y-label.getComponent(cc.UITransform).height/2),.6);else sv.scrollToBottom(.6);},effect);
   await shot('artifact',()=>select(setups[family].weapon));if(!qaOnly)fs.copyFileSync(path.join(out,'screenshots',family+'-artifact.jpg'),path.join(out,'screenshots',family+'-inventory.jpg'));
   await shot('artifact-effect',()=>scroll(true));
   await shot('legendary',()=>select({BOW:'DG_L02',WAR:'DG_L01',FIR:'DG_L03',THU:'DG_L04'}[family]));
   await shot('legendary-effect',()=>scroll(true));
   await shot('armor-detail',()=>select('LC1_B_E'));await shot('armor-source',scroll,1000);
   for(const menu of ['attributes','checks','profession'])await shot(menu,()=>page.evaluate(menu=>{const a=findPromoApp();a.click('close');a.click(menu);},menu));
   if(qaOnly)for(const viewport of [{width:932,height:430},{width:1280,height:720}]){await page.setViewportSize(viewport);await page.waitForTimeout(800);await shot('artifact-'+viewport.width,async()=>{await page.evaluate(()=>{const a=findPromoApp();a.click('close');a.click('inventory');});await select(setups[family].weapon);});await shot('armor-source-'+viewport.width,async()=>{await select('LC1_B_E');await scroll();});}
   if(!qaOnly)await page.evaluate(()=>promoStopRecorder());report.panels.timeline=timeline;report.panelChecks=checks;report.errors=errors;report.consoleErrors=consoleErrors;report.mainUnchanged=sha(main)===report.mainSha256;
   fs.writeFileSync(qaOnly?path.join(shotDir,family+'-validation.json'):path.join(out,'records',family+'-panels.json'),JSON.stringify(report,null,2));
   console.log(JSON.stringify({phase:'panels-complete',family,seconds:timeline.at(-1).end,checks:checks.length,nonOverlapping:checks.every(x=>x.nonOverlapping!==false),errors}));
   if(errors.length||!report.mainUnchanged||checks.some(x=>x.area!=='H14'||x.nonOverlapping===false))throw Error('Panel validation failed');return;
  }
  await startRecording(family+'-panels');
  for(const menu of report.panels.menus){
   await page.evaluate(menu=>{const a=findPromoApp();if(a.menu!==menu){a.click('close');a.click(menu);}},menu);await ready();await page.waitForTimeout(900);
   if(menu==='inventory'){await page.evaluate(async()=>{const a=findPromoApp(),panel=await System.import('chunks:///_virtual/EquipmentPanels.ts');panel.recordEquipmentChange(a.session,'LC1_B_E','');a.modalKey='';a.renderModal();});await page.waitForTimeout(400);}
   await page.screenshot({path:path.join(out,'screenshots',`${family}-${menu}.jpg`),type:'jpeg',quality:93});await page.waitForTimeout(2100);
  }
  await page.evaluate(()=>promoStopRecorder());
  // Return to the authored hunting pack. No enemy placement/stat edits are made.
  await page.evaluate(async setup=>{const a=findPromoApp(),world=await System.import('chunks:///_virtual/WorldData.ts');a.enabled=false;a.click('close');a.clearInput(false);a.session.enter(world.AREAS[setup.area],setup.position);a.menu='';await a.rebuild();a.enabled=false;a.toast='';a.toastTime=0;},setups[family]);await ready();
  report.recording=await startRecording(family);
  await page.evaluate(()=>{
   const a=findPromoApp(),s=a.session.state,started=s.time,origin={x:s.player.x,z:s.player.z};let skillIndex=0,nextSkill=started+.55,nextDodge=started+2.6,vx=0,vz=0,tick=0;
   const choices=[{ultimate:true},{combatSlot:3},{combatSlot:1},{combatSlot:0},{combatSlot:2}];globalThis.promoMovement=[];
   globalThis.promoControls=setInterval(()=>{
    if(a.loading||a.menu||s.status!=='playing')return;
    const p=s.player,t=s.time-started,targets=s.enemies.filter(e=>e.hp>0&&a.world.visible(p,e)).sort((u,v)=>Math.hypot(u.x-p.x,u.z-p.z)-Math.hypot(v.x-p.x,v.z-p.z)),target=targets[0];
    if(!target){a.pulse={x:.28*Math.cos(t*.6),z:.28*Math.sin(t*.6)};return;}
    const dx=target.x-p.x,dz=target.z-p.z,distance=Math.max(.01,Math.hypot(dx,dz)),ux=dx/distance,uz=dz/distance,melee=s.combat.family==='WAR';
    const direction=Math.floor(t/4.2)%2===0?1:-1,phase=t%5.5,preferred=melee?1.35:s.combat.family==='FIR'?5.6:6.5;
    const radial=Math.max(-.9,Math.min(.95,(distance-preferred)/(melee?1.4:2.2))),side=(phase<1.5?.88:.5)*direction;
    let moveX=ux*radial-uz*side,moveZ=uz*radial+ux*side;
    const away=Math.hypot(p.x-origin.x,p.z-origin.z);if(away>12){moveX+=(origin.x-p.x)/away*.6;moveZ+=(origin.z-p.z)/away*.6;}
    const magnitude=Math.hypot(moveX,moveZ);if(magnitude>1){moveX/=magnitude;moveZ/=magnitude;}vx=vx*.55+moveX*.45;vz=vz*.55+moveZ*.45;
    // Normal movement vectors, real dodge inputs and native cooldowns; no speed/AI overrides.
    const frame={x:vx,z:vz,aim:Math.atan2(dx,dz),target:{x:target.x,z:target.z},attack:phase>(melee?1.0:1.5)};
    const canDodge=(s.combat.cooldowns.COM_01??0)<=.05&&(!s.action||s.action.kind!=='dash'&&s.action.elapsed>=.35);
    if(s.time>=nextDodge&&canDodge){frame.dash=true;frame.attack=false;nextDodge=s.time+4.8;nextSkill=Math.max(nextSkill,s.time+.5);}
    else if(!s.action&&s.time>=nextSkill){Object.assign(frame,choices[skillIndex++%choices.length]);nextSkill=s.time+2.05;}
    if(p.hp/p.maxHp<.48&&!s.action)a.session.useConsumable('health');
    if(p.focus/p.maxFocus<.3&&!s.action)a.session.useConsumable('resource');
    a.pulse=frame;if(tick++%5===0)promoMovement.push({time:s.time,x:p.x,z:p.z,action:s.action?.kind??'',input:{x:vx,z:vz,dash:!!frame.dash}});
   },45);
   a.enabled=true;
  });
  console.log(JSON.stringify({phase:'recording',family,...report.recording}));
  let elapsed=0;for(const at of [1.3,4.2,7.8,11.5,16.5,21.5].filter(t=>t<seconds)){
   await page.waitForTimeout((at-elapsed)*1000);elapsed=at;await page.screenshot({path:path.join(out,'screenshots',`${family}-${String(at).replace('.','_')}.jpg`),type:'jpeg',quality:93});
  }
  await page.waitForTimeout(Math.max(0,(seconds-elapsed)*1000));
  report.result=await page.evaluate(async()=>{clearInterval(promoControls);await promoStopRecorder();const a=findPromoApp(),s=a.session.state;a.enabled=false;return {level:s.progression.level,hp:s.player.hp,maxHp:s.player.maxHp,kills:s.enemies.filter(e=>e.hp<=0).length,movedDistance:s.movedDistance,movement:promoMovement,events:promoEvents,menu:a.menu,status:s.status};});
  const previous=path.join(out,'records',family+'.json');if(fs.existsSync(previous)){const old=JSON.parse(fs.readFileSync(previous,'utf8'));if(old.mainSha256===report.mainSha256&&old.appearanceCheck)report.appearanceCheck=old.appearanceCheck;}
  report.movementStyle='Role-based lateral movement and kiting; real dodge input; normal collision, speed and cooldowns';
  report.errors=errors;report.consoleErrors=consoleErrors;report.mainUnchanged=sha(main)===report.mainSha256;
  fs.writeFileSync(path.join(out,'records',family+'.json'),JSON.stringify(report,null,2));
  const dodges=report.result.events.filter(e=>e.type==='skill_release'&&e.skillId==='COM_01').length;
  console.log(JSON.stringify({phase:'complete',family,level:report.result.level,kills:report.result.kills,moved:report.result.movedDistance,dodges,errors}));
  if(errors.length||!report.mainUnchanged||report.panels.area!=='H14'||report.result.level!==20||!report.result.events.some(e=>e.type==='skill_hit')||!report.result.kills||report.result.movedDistance<20||!dodges)throw Error('Capture checks failed; inspect report');
 }finally{await browser.close();server.close();}
}
mainCapture().catch(e=>{console.error(e);process.exitCode=1;});
