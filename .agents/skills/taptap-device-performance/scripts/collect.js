// Inspector-only instrumentation. No engine getter, gameplay state or storage patches.
({key,seconds,label,operation})=>{
 const c=globalThis.GameGlobal?.cc??globalThis.cc;
 if(!c?.director?.root?.device)throw new Error('The selected target is not a running Cocos game');
 const d=c.director,app=()=>d.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');
 const state=()=>{const a=app(),s=a?.session?.state;return s?{area:s.area,time:s.time,moved:s.movedDistance,hp:s.player.hp,status:s.status,menu:a.menu,loading:a.loading,enemySlots:s.enemies.length,aliveEnemies:s.enemies.filter(e=>e.hp>0).length}:null;};
 const snapshot=()=>{
  const canvas=globalThis.GameGlobal?.canvas??c.game.canvas??globalThis.document?.querySelector('canvas'),v=d.root.device;
  const size=c.screen.windowSize;
  return {version:(globalThis.gameConfig??globalThis.GameGlobal?.gameConfig)?.productVersion??null,engine:c.ENGINE_VERSION??null,scene:d.getScene()?.name,canvas:canvas?[canvas.width,canvas.height]:null,windowPixels:[size.width,size.height],dpr:c.screen.devicePixelRatio,frameRate:c.game.frameRate,state:state(),drawCalls:v.numDrawCalls,triangles:v.numTris,gfxBytes:{...v.memoryStatus}};
 };
 if(operation==='snapshot')return JSON.stringify(snapshot());
 if(operation==='take'){
  const p=globalThis[key];if(!p)throw new Error('Capture expired or target restarted');
  p.stop('collected');
  const result=JSON.stringify(p.data);clearTimeout(p.expiry);delete globalThis[key];return result;
 }
 if(operation==='cleanup'){
  const p=globalThis[key];if(p){p.stop('cleanup');clearTimeout(p.expiry);delete globalThis[key];}
  return JSON.stringify({collectorRemoved:!Object.prototype.hasOwnProperty.call(globalThis,key)});
 }
 if(globalThis[key])throw new Error('Collector already exists');
 if(!(seconds>=1&&seconds<=60))throw new Error('Capture window must be 1–60 seconds');
 const before=snapshot(),start=performance.now();
 const p={data:{label,seconds,start,baseline:before,startState:before.state,frames:[],actionFrames:0,movingFrames:0,truncated:false},previousMoved:before.state?.moved};
 p.stop=reason=>{
  if(p.data.end!==undefined)return;
  d.off(c.Director.EVENT_AFTER_DRAW,p.handler);clearTimeout(p.timer);
  p.data.end=performance.now();p.data.endState=state();p.data.stopReason=reason;
  p.data.finalFrameRate=c.game.frameRate;
 };
 p.handler=()=>{
  const now=performance.now(),v=d.root.device,s=app()?.session?.state;
  // Fixed maximum also protects against broken timers or an unexpectedly high frame rate.
  if(p.data.frames.length>=10000){p.data.truncated=true;p.stop('frame-limit');return;}
  p.data.frames.push([now-start,v.numDrawCalls,v.numTris,v.memoryStatus.bufferSize,v.memoryStatus.textureSize]);
  if(s?.action||s?.combat?.casts?.length)p.data.actionFrames++;
  if(s&&s.movedDistance!==p.previousMoved)p.data.movingFrames++;
  p.previousMoved=s?.movedDistance;
 };
 globalThis[key]=p;d.on(c.Director.EVENT_AFTER_DRAW,p.handler);
 p.timer=setTimeout(()=>p.stop('deadline'),seconds*1000);
 // A lost USB connection must not leave a listener or retained frame buffer running.
 p.expiry=setTimeout(()=>{p.stop('watchdog');delete globalThis[key];},(seconds+20)*1000);
 return JSON.stringify({started:true,key,baseline:before});
}
