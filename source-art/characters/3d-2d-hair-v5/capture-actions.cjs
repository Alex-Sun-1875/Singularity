// Adapt the existing native-actor recorder; each frame advances exactly 1/30 s.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const phase=process.argv[2]??'after',out=path.join(__dirname,'runtime',phase);fs.mkdirSync(out,{recursive:true});
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await b.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto((process.env.APPEARANCE_REVIEW_URL??'http://127.0.0.1:7469/')+'?view=2d&player=3d&test=max&revision=native-short-'+phase);await page.waitForFunction(()=>globalThis.System);await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:120000});assert.equal(await page.evaluate(()=>app().failure),'');
 await page.evaluate(()=>{const a=app();a.enabled=false;a.menu='';a.hud.root.active=false;a.manualCameraHeight=2.1;a.positionCamera(1);globalThis.home={x:a.session.state.player.x,z:a.session.state.player.z};
  globalThis.heading=()=>{const r=a.camera.node.right,u=a.camera.node.up,k=u.x*u.x+u.z*u.z;return Math.atan2(r.x+u.x/k,r.z+u.z/k);};
  globalThis.prepare=id=>{a.session.cancelInput();a.session.state.action=null;for(let i=0;i<155;i++){a.session.advance(1/30,{x:0,z:0});a.actors.update(a.session,1/30,false);}a.session.state.inventory[id]=1;if(!a.session.equip(id))throw Error('Equip '+id);a.effects.clear();globalThis.poseClock=0;globalThis.poseName='';};
  globalThis.step=(scenario,i)=>{
   const p=a.actors.player.active.get('player'),angle=heading(),moving=scenario==='run',attack=scenario==='bow'?i>=4&&i<=20||i>=34&&i<=50:scenario==='sword'?i===4||i===24||i===44:scenario==='staff'?i===4||i===28:false;
   const pos=a.session.state.player;pos.x=home.x;pos.z=home.z;p.root.setPosition(home.x,a.world.height(home),home.z);
   a.process(a.session.advance(1/30,{x:moving?Math.sin(angle):0,z:moving?Math.cos(angle):0,aim:angle,attack,dash:scenario==='dodge'&&(i===4||i===32)}));a.actors.update(a.session,1/30,moving,false,1);
   const clip=p.clips[p.state],state=clip&&p.animation.getState(clip.name);
   if(state){if(state.speed!==0){poseClock=poseName===p.state?poseClock+state.speed/30:0;state.time=p.state==='run'||p.state==='idle'||p.state.endsWith('_staff')&&p.state!=='attack_staff'?poseClock%clip.duration:Math.min(clip.duration,poseClock);}poseName=p.state;state.weight=1;state.sample();p.animation.pause();}
   a.world.presentation?.update(a.session);a.effects.update(a.session);a.positionCamera(1/30);a.flatWorld.update(a.camera,a.session);
   return {frame:i,state:p.state,action:a.session.state.action?.kind,elapsed:a.session.state.action?.elapsed,emitted:a.session.state.action?.emitted,speed:p.speed,animationSpeed:state?.speed,clipTime:state?.time,clipDuration:clip?.duration,bowDraw:p.bowHeldDraw,skins:p.model.getComponentsInChildren(cc.SkinnedMeshRenderer).length};
  };
 });
 const rows=[];
 for(const [scenario,id]of [['run','W01'],['bow','W07'],['dodge','W01']]){
  await page.evaluate(id=>prepare(id),id);
  for(let i=0;i<60;i++){
   const info=await page.evaluate(({scenario,i})=>step(scenario,i),{scenario,i});await page.evaluate(()=>new Promise(r=>requestAnimationFrame(r)));const file=scenario+'-'+String(i).padStart(3,'0')+'.jpg';await page.screenshot({path:path.join(out,file),type:'jpeg',quality:93,clip:{x:470,y:150,width:500,height:600}});rows.push({scenario,file,...info});
  }
  console.log('Recorded '+phase+' '+scenario);
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'frames.json'),JSON.stringify({phase,simulationFrameSeconds:1/30,playback:'Normal game speed: GIF uses repeating 30/30/40 ms durations',rows,errors},null,2));console.log(JSON.stringify({phase,frames:rows.length,errors}));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
