/* Browser-only fixture. Inputs go through the normal ChapterGame frame loop. */
module.exports=async function setupFarm({area:areaId,family,level,control='move'}){
 const {app,cc}=__perf;
 await __perf.setup({area:areaId,mode:'idle',family});
 const {cumulativeXp}=await System.import('chunks:///_virtual/Progression.ts');
 const {getArea}=await System.import('chunks:///_virtual/WorldData.ts');
 app.menu='performance-setup';__perf.current=null;app.heldAttack=false;app.pulse={};
 app.session.gainExperience('performance-farm-level',cumulativeXp(level)-app.session.state.progression.totalXp);
 const area=getArea(areaId),spitter=area.enemies.find(e=>e.templateId==='BEAST_ASH_SPITTER');
 let entry=area.spawn;
 if(spitter)for(const offset of [{x:0,z:-6},{x:6,z:0},{x:0,z:6},{x:-6,z:0}]){
  const point={x:spitter.x+offset.x,z:spitter.z+offset.z};
  if(app.query.path(area.spawn,point).length){entry=point;break;}
 }
 app.session.enter(area,entry);await app.rebuild();
 app.menu='';app.hud.clearModal();app.modalKey='';app.guideTime=.4;app.guideArea='';app.trackedTaskId=undefined;app.positionCamera(1);
 if(control==='auto')app.automation.setMode('idle');
 else{
  app.automation.stop();
  const spawns=area.enemies.filter(e=>e.respawnSeconds),p=app.session.state.player;
  // Navigation belongs to the input fixture, not to the gameplay controller.
  // Preselect safe resting points and bound subsequent path requests to1Hz.
  const candidates=[{x:-area.width*.32,z:-area.depth*.32},{x:area.width*.32,z:-area.depth*.32},{x:area.width*.32,z:area.depth*.32},{x:-area.width*.32,z:area.depth*.32},area.spawn];
  const rests=candidates.filter(q=>spawns.every(e=>Math.hypot(e.x-q.x,e.z-q.z)>22)&&area.objects.every(o=>Math.hypot(o.x-q.x,o.z-q.z)>5)&&app.query.path(p,q).length);
  if(!rests.length)throw Error('No safe moving-hunt rest route');
  const navigation=app.world.movementNavigation??app.world.navigation;
  __perf.farmAvoid=new Map();
  let rest=0,route=[],replanAt=-Infinity,progressAt=app.session.state.time,progress={x:p.x,z:p.z},direction=1;
  const movement={x:0,z:0};__perf.farmRoute={pathQueries:0,recoveries:0};
  __perf.farmSteering=(state,enemy)=>{
   const p=state.player;let target;
   if(state.time-progressAt>=2){
    if(Math.hypot(p.x-progress.x,p.z-progress.z)<1){
     if(enemy)__perf.farmAvoid.set(enemy.id,state.time+8);else rest=(rest+1)%rests.length;
     direction=-direction;route=[];__perf.farmRoute.recoveries++;
    }
    progressAt=state.time;progress={x:p.x,z:p.z};
   }
   if(enemy){const radius=family==='WAR'?1.7:5,angle=Math.atan2(p.x-enemy.x,p.z-enemy.z)+direction*.22;target={x:enemy.x+Math.sin(angle)*radius,z:enemy.z+Math.cos(angle)*radius};}
   else{if(Math.hypot(p.x-rests[rest].x,p.z-rests[rest].z)<1)rest=(rest+1)%rests.length;target=rests[rest];}
   let next=target;
   if(!navigation.visible(p,target,.42)){
    if(state.time>=replanAt){route=navigation.path(p,target);replanAt=state.time+1;__perf.farmRoute.pathQueries++;}
    while(route.length&&Math.hypot(route[0].x-p.x,route[0].z-p.z)<.35)route.shift();
    next=route[0]??target;
   }else route=[];
   Object.assign(__perf.farmRoute,{enemy:enemy?.id,target,next,position:{x:p.x,z:p.z}});
   movement.x=next.x-p.x;movement.z=next.z-p.z;return movement;
  };
  __perf.current={area:areaId,mode:'move-combat',family,started:app.session.state.time,anchor:{...p},lastSkill:-99,farmMoving:true};
 }
 // Observe actual world movement, including when native automation owns input.
 if(!__perf.farmMotion){
  const motion=__perf.farmMotion={frames:0,movingFrames:0,activeFrames:0,x:0,z:0};
  const begin=__perf.begin;__perf.begin=()=>{const p=app.session.state.player;motion.frames=0;motion.movingFrames=0;motion.activeFrames=0;motion.x=p.x;motion.z=p.z;begin();};
  cc.director.on(cc.Director.EVENT_AFTER_DRAW,()=>{
   if(!__perf.measuring)return;const s=app.session.state,p=s.player,dx=p.x-motion.x,dz=p.z-motion.z,moved=dx*dx+dz*dz>1e-12;
   motion.frames++;if(moved)motion.movingFrames++;if(moved||s.action||s.combat.casts.length)motion.activeFrames++;motion.x=p.x;motion.z=p.z;
  });
 }
 return {area:app.session.state.area,entry,level:app.session.state.progression.level,weapon:app.session.state.equipment.weapon,family:app.session.state.combat.family,control,automation:app.automation.mode,enemies:app.session.state.enemies.length,spitters:app.session.state.enemies.filter(e=>e.templateId==='BEAST_ASH_SPITTER').length,startHP:app.session.state.player.hp,frameRate:cc.game.frameRate};
};
