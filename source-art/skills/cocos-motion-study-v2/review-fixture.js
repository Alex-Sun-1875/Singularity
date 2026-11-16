// Render the existing Cocos battle from its own session clock in a disposable browser context.
// No pose, hit, damage, or projectile events are manufactured by the recorder.
window.installMotionStudy = async function installMotionStudy(setup) {
  const module = name => System.import('chunks:///_virtual/' + name + '.ts');
  const cc = await System.import('cc');
  function findChapter(node) {
    return node?.getComponent('ChapterGame') || node?.children.map(findChapter).find(Boolean);
  }
  const app = findChapter(cc.director.getScene());
  const {AREAS} = await module('WorldData');
  const {BASIC_ATTACK} = await module('GameSession');
  const {COMBAT_SKILLS} = await module('PureSkills');
  const {COMBAT_LOADOUTS} = await module('CombatLoadouts');
  app.enabled = false;
  app.clearInput(false);
  app.session.raiseToMaxLevel();
  const session = app.session, state = session.state, player = state.player;
  const original = {sword: {...BASIC_ATTACK.sword}, war01: {...COMBAT_SKILLS.WAR_01.ranks[0].geometry}, war05: {...COMBAT_SKILLS.WAR_05.ranks[0].geometry}};
  if (setup === 'design') window.applyStudyDimensions(BASIC_ATTACK, COMBAT_SKILLS, COMBAT_LOADOUTS);
  session.enter(AREAS.S04, {x: 10, z: 1.5});
  for (const weapon of ['W01','W07','W11']) state.inventory[weapon] = 1;
  for (const skill of Object.keys(COMBAT_SKILLS)) state.progression.learned[skill] = 1;
  for (const id of Object.keys(state.progression.attributes)) state.progression.attributes[id] = 40;
  session.applyCombatLoadout('WAR','W01');
  const template = state.enemies.find(e => e.kind === 'raider') || state.enemies[0];
  if (!template) throw Error('S04 has no authored target template');
  const targets = Array.from({length: 4}, (_,i) => ({
    ...structuredClone(template), id: 'study-target-' + i, kind:'raider', hp: 100000, maxHp: 100000,
    x: player.x + i + 1, z: player.z, level:1, phase:'idle', trainingDummy:true, trainingAttacks:false,
    phaseTime:0, markedUntil:0, lightningUntil:0, combat:undefined,
  }));
  state.enemies=targets;
  state.status='playing'; state.dialogue=null; state.dice.active=false;
  await app.rebuild();
  if (app.failure || !app.actors.playerModel()) throw Error(app.failure || 'No native player model');
  app.enabled=false;
  app.menu=''; app.hud.clearModal(); app.hud.root.active=false;
  const camera=app.camera, angle=Math.atan2(camera.node.right.x,camera.node.right.z)+.13;
  const forward={x:Math.sin(angle),z:Math.cos(angle)}, side={x:Math.cos(angle),z:-Math.sin(angle)};
  const point=(origin, distance, offset=0)=>({x:origin.x+forward.x*distance+side.x*offset,z:origin.z+forward.z*distance+side.z*offset});
  const possible=[{x:10,z:1.5},{x:6,z:2},{x:4,z:0},{x:0,z:1},{x:-4,z:0}];
  for(let x=-12;x<13;x+=2)for(let z=-10;z<11;z+=2)possible.push({x,z});
  const clear=(origin,q)=>app.world.visible(origin,q) && Math.abs(app.world.height(origin)-app.world.height(q))<.48 && !app.world.navigation?.blocked(q,.35);
  const origin=possible.find(p=>[p,point(p,2.5),point(p,4),point(p,5.4),point(p,6.6,1.1),point(p,5.4,-1.1),point(p,7.3,-.6)].every(q=>clear(p,q)));
  if(!origin)throw Error('No clear patch on S04 for the matched cameras');
  let shot,frame,events,targetPoint,castResult,clipStates,stats,flightSamples;
  function record(batch) {
    for (const e of batch) if (['attack','hit','miss','skill_cast','skill_segment','skill_release','skill_hit','skill_status','projectile','notice'].includes(e.type)) {
      events.push({time:frame/30,type:e.type,skill:e.skillId,id:e.id,target:e.targetId,stage:e.comboStage,segment:e.segment,value:e.value,reason:e.text});
    }
    app.process(batch);
  }
  function tick(input={}) {
    const dt=1/60;
    record(session.advance(dt,{x:0,z:0,aim:angle,...input}));
    app.actors.update(session,dt,false,false);
    app.effects.update(session);
    app.flatWorld?.update(camera,session);
    cc.director.tick(dt);
  }
  function frameCamera(midpoint,halfHeight) {
    const focus=point(origin,midpoint);
    const at=new cc.Vec3(focus.x,app.world.height(focus)+.63,focus.z);
    camera.node.setWorldPosition(at.clone().subtract(camera.node.forward.clone().multiplyScalar(28)));
    camera.orthoHeight=halfHeight;
    camera.camera?.update(true);
    app.flatWorld?.update(camera,session);
  }
  function sample(){
    const canvas=document.getElementById('GameCanvas');
    return canvas.toDataURL('image/jpeg',.96).split(',')[1];
  }
  return globalThis.motionStudy={
    cc,app,state,original,
    async select(def) {
      cc.game.resume(); app.enabled=false;
      session.resetCombatTransient();
      state.sequence=100; state.seed=73014; state.time=10; state.cooldowns={}; state.combat.cooldowns={}; state.combat.ultimateLock=0;
      state.status='playing';state.action=null;state.dialogue=null;state.dice.active=false;state.fireZones=[];state.enemyHazards=[];
      state.combat.buffs={};state.combat.statuses={};delete state.combat.engagement;
      const weapon=def.family==='WAR'?'W01':def.family==='BOW'?'W07':'W11';
      const active=session.applyCombatLoadout(def.family,weapon);
      if(!active && (state.equipment.weapon!==weapon||state.combat.family!==def.family))throw Error('Could not equip '+weapon);
      player.x=origin.x;player.z=origin.z;player.angle=angle;player.hp=player.maxHp;player.focus=player.maxFocus;player.hurtTime=0;
      state.combat.charge=100; state.combat.passiveSlots=[null,null]; state.projectiles=[]; state.effects=[]; state.barrels=[];
      const group=def.targets;
      for(let i=0;i<targets.length;i++){
        const target=targets[i],where=group[i]||[15+i*2,6];
        Object.assign(target,point(origin,...where),{hp:100000,maxHp:100000,phase:'idle',phaseTime:0,hurtTime:0,angle:angle+Math.PI,targetAngle:angle+Math.PI,combat:undefined});
      }
      state.enemies=targets.slice(0,group.length);
      const cast=app.actors.cast??app.actors;
      for(const [i,target] of targets.entries()){
        const actor=cast.active.get(target.id);
        if(actor)actor.root.active=i<group.length;
      }
      if(!state.enemies.every(t=>clear(origin,t)))throw Error('A target lies outside the verified battlefield');
      state.revision++; app.effects.clear();app.impact?.clear();app.enemyFeedback?.clear?.();
      await app.actors.preparePlayerWeapon?.(weapon);
      await app.effects.prepareEquipment(session);
      // prepareEquipment recreates the family-specific pools when the user switches weapon.
      // Bind the battle camera on the prepared instance so the wake points up the actual fall.
      if(setup==='design')for(const pool of [app.effects.blades,app.effects.fireSprites,app.effects.thunderContacts])pool.camera=camera;
      app.actors.update(session,0,false,false);
      const playerActor=app.actors.player??app.actors;
      if(!app.actors.preparePlayerWeapon && playerActor.preparePlayerWeapon)await playerActor.preparePlayerWeapon(weapon);
      frameCamera(def.centre,def.height);
      shot=def;frame=0;events=[];flightSamples=[];clipStates=new Set();stats={maxBlades:0,maxArrows:0,maxFire:0,maxEdges:0};castResult=null;targetPoint={x:targets[0].x,z:targets[0].z};
      cc.game.pause();
      // Prime camera-facing actors and weapon readiness on the real animation clock.
      for(let i=0;i<16;i++)tick();
      frame=0;events=[];
      return {original, variant:setup,geometry:BASIC_ATTACK.sword,skillGeometry:COMBAT_SKILLS[def.id]?.ranks[0]?.geometry,
        loadout:{family:state.combat.family,weapon:state.equipment.weapon,ultimate:state.combat.ultimate},
        origin,targets:state.enemies.map(t=>({id:t.id,x:t.x,z:t.z})),canvas:[cc.game.canvas.width,cc.game.canvas.height],
        player:playerActor.inspect().find(a=>a.id==='player'),scene:state.area,renderer:app.modelPlayer?'Player3DActors':'Actors'};
    },
    next(includeImage=true){
      const time=frame/30, start=shot.start??.30;
      for(let sub=0;sub<2;sub++){
        if(frame===Math.round(start*30)&&sub===0 && shot.id!=='BASIC_WAR'){
          const result=session.castSkill(shot.id,targetPoint,angle);
          castResult=result.map(e=>e.type);record(result);
        }
        tick({attack:shot.id==='BASIC_WAR'&&time>=start&&time<start+.92});
      }
      const model=app.actors.player??app.actors;
      clipStates.add(model.active?.get('player')?.state);
      stats.maxBlades=Math.max(stats.maxBlades,app.effects.blades.inspect().active.length);
      stats.maxArrows=Math.max(stats.maxArrows,state.projectiles.length);
      stats.maxFire=Math.max(stats.maxFire,app.effects.meteor.inspect().active.length);
      if(shot.id==='FIR_02'&&frame%3===0){
        const body=app.effects.fireSprites.items.find(x=>x.root.active&&x.key.startsWith('meteor:')&&x.key.endsWith(':a'));
        if(body){const p=body.root.worldPosition,screen=camera.worldToScreen(p);
          const axis=cc.Vec3.transformQuat(new cc.Vec3(),cc.Vec3.UNIT_X,body.root.worldRotation);
          const end=camera.worldToScreen(p.clone().add(axis));
          flightSamples.push({frame,head:[screen.x,screen.y],axis:[end.x-screen.x,end.y-screen.y],cameraBound:app.effects.fireSprites.camera===camera});}
      }
      const patterns=app.effects.skills.inspectThunder();
      stats.maxEdges=Math.max(stats.maxEdges,0,...patterns.map(p=>p.edges));
      frame++;
      return includeImage?sample():null;
    },
    report(){return {events,frames:frame,shot:shot.id,castResult,clips:[...clipStates],stats,flightSamples};}
  };
};
