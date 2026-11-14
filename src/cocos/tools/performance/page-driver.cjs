/* Browser-only performance pilot. Runs the normal ChapterGame frame loop. */
module.exports = async function installDriver() {
  const cc = await System.import('cc');
  const {GameSession} = await System.import('chunks:///_virtual/GameSession.ts');
  const {getArea} = await System.import('chunks:///_virtual/WorldData.ts');
  const {cumulativeXp} = await System.import('chunks:///_virtual/Progression.ts');
  const {prepareCombatLoadout, COMBAT_LOADOUTS} = await System.import('chunks:///_virtual/CombatLoadouts.ts');
  const {CAMPAIGN_SCENES} = await System.import('chunks:///_virtual/CampaignScenes.ts');
  const {ENEMY_COMBAT_PROFILES} = await System.import('chunks:///_virtual/EnemyCombat.ts');
  const {COMBAT_SKILLS,COMBAT_RULES} = await System.import('chunks:///_virtual/PureSkills.ts');
  const {RESOURCE_RULES} = await System.import('chunks:///_virtual/ClassResource.ts');
  const app = cc.director.getScene().getChildByName('ChapterGame').getComponent('ChapterGame');
  const pilot = globalThis.__perf = {app, cc, current: null, measuring: false, frames: [], renderCounters:{drawCalls:[],triangles:[]}, events: {}, actionFrames: 0, movingFrames: 0, liveEnemyFrames: 0, animationModeChanges:0};
  const process = app.process.bind(app);
  app.process = events => {
    if (pilot.measuring) for (const e of events) pilot.events[e.type] = (pilot.events[e.type] || 0) + 1;
    return process(events);
  };
  let vector = {x: 0, z: 0};
  app.touches.vector = () => vector;
  pilot.setup = async spec => {
    pilot.measuring = false; pilot.current = null; vector = {x: 0, z: 0};
    app.menu = 'performance-setup'; app.clearInput(); app.automation.stop();
    const g = new GameSession(19, app.query), family = spec.family || 'WAR';
    g.gainExperience('performance-fixture', cumulativeXp(15));
    const s = g.state;
    s.equipment.weapon = COMBAT_LOADOUTS[family].weapon;
    prepareCombatLoadout(s.combat, s.equipment.weapon, s.progression, family);
    // Acknowledged cinematics are fixture progress, not disabled production logic.
    for (const scene of CAMPAIGN_SCENES) s.receipts[`campaign:seen:${scene.id}`] = true;
    const area = getArea(spec.area || 'U1-06');
    const boss = area.enemies.find(e => e.bossId === 'ELITE_06') || area.enemies.find(e => !e.respawnSeconds);
    const entry = spec.mode === 'idle' || spec.mode === 'run' ? area.spawn : {x: boss.x, z: boss.z - (family === 'WAR' ? 1.6 : 5)};
    g.enter(area, entry); app.session = g; app.trainingRange = undefined;
    app.trackedTaskId = undefined; app.guideTime = .4; app.guideArea = '';
    await app.rebuild();
    app.menu = ''; app.hud.clearModal(); app.modalKey = ''; app.positionCamera(1);
    pilot.current = {...spec, started: s.time, anchor: {...s.player}, lastSkill: -99};
    return {area: s.area, level: s.progression.level, family: s.combat.family, player: {...s.player}, enemies: s.enemies.map(e => ({id:e.id, x:e.x, z:e.z, hp:e.hp, bossId:e.bossId})), frameRate: cc.game.frameRate};
  };
  cc.director.on(cc.Director.EVENT_BEFORE_UPDATE, () => {
    const spec = pilot.current;
    if (!spec || app.loading) return;
    const s = app.session.state, p = s.player, t = s.time - spec.started;
    const enemies = s.enemies.filter(e => e.hp > 0 && (!spec.farmMoving || e.respawnSeconds && (pilot.farmAvoid?.get(e.id)??0)<=s.time));
    let enemy, best = Infinity;
    for (const e of enemies) {const d = Math.hypot(e.x-p.x,e.z-p.z); if(d<best){best=d;enemy=e;}}
    let x = 0, z = 0;
    if (spec.mode === 'run') {x = Math.cos(t * .5); z = Math.sin(t * .5);}
    if (spec.mode === 'move-combat' && enemy) {
      const angle = Math.atan2(p.x-enemy.x,p.z-enemy.z) + .22;
      const radius = spec.family === 'WAR' ? 1.7 : 5;
      x = enemy.x + Math.sin(angle)*radius - p.x; z = enemy.z + Math.cos(angle)*radius - p.z;
    }
    if(spec.farmMoving&&pilot.farmSteering){const movement=pilot.farmSteering(s,enemy);x=movement.x;z=movement.z;}
    const len = Math.hypot(x,z);
    if (len > .02) {
      x /= len; z /= len;
      const r = app.camera.node.right, u = app.camera.node.up, det = r.x*u.z-r.z*u.x;
      const sx = (x*u.z-z*u.x)/det, sz = (z*r.x-x*r.z)/det, scale = Math.max(1,Math.hypot(sx,sz));
      vector = {x:sx/scale,z:sz/scale};
    } else vector = {x:0,z:0};
    const combat = spec.mode.includes('combat') && (!spec.farmMoving || enemy && best<=10 && app.query.visible(p,enemy));
    // Real potion input, finite starting stock and normal cooldown/action gates.
    // A stationary melee fixture must survive the current pursuing boss; never
    // hide death by freezing damage, restoring HP, or replenishing inventory.
    if(combat&&p.hp/p.maxHp<=.6&&p.healthPotions>0&&!(s.cooldowns.consumable>0)){
      app.heldAttack=false;app.pulse={};
      if(!s.action&&!app.aiming)app.click('potion-health');
      return;
    }
    const wantSkill = combat && enemy && spec.skills !== false && t-spec.lastSkill > 2;
    // Release an ongoing bow aim, then submit a skill only in a legal action
    // gap. A pulse discarded by the combat rules is not skill coverage.
    app.heldAttack = combat && !wantSkill && t % .85 < .52;
    if (wantSkill && !s.action) {
      app.pulse = {combatSlot: Math.floor(t/2)%4, target:{x:enemy.x,z:enemy.z}, aim:Math.atan2(enemy.x-p.x,enemy.z-p.z)};
      spec.lastSkill = t;
    }
  });
  let last = 0;
  let animationMode;
  cc.director.on(cc.Director.EVENT_AFTER_DRAW, () => {
    const now = performance.now();
    if(pilot.measuring){
      if(pilot.firstDrawMs===null)pilot.firstDrawMs=now-pilot.measurementStartMs;
      if(last){pilot.frames.push(now-last);const d=cc.director.root.device;pilot.renderCounters.drawCalls.push(d.numDrawCalls);pilot.renderCounters.triangles.push(d.numTris);}
      const s=app.session.state;
      if(s.action||s.combat.casts.length)pilot.actionFrames++;
      if(Math.hypot(vector.x,vector.z)>.1)pilot.movingFrames++;
      if(s.enemies.some(e=>e.hp>0))pilot.liveEnemyFrames++;
      const mode=app.actors.player?.active.get('player')?.animation?.useBakedAnimation;
      if(animationMode!==undefined&&mode!==animationMode)pilot.animationModeChanges++;
      animationMode=mode;
    }
    last=now;
  });
  pilot.begin = () => {pilot.frames=[];pilot.renderCounters={drawCalls:[],triangles:[]};pilot.events={};pilot.actionFrames=0;pilot.movingFrames=0;pilot.liveEnemyFrames=0;pilot.animationModeChanges=0;animationMode=undefined;last=0;pilot.firstDrawMs=null;pilot.measurementStartMs=performance.now();pilot.measuring=true;pilot.startTime=app.session.state.time;pilot.startDistance=app.session.state.movedDistance;};
  pilot.end = () => {
    const measurementEndMs=performance.now();
    pilot.measuring=false;
    const s=app.session.state, d=cc.director.root.device;
    return {frames:pilot.frames,frameClock:{schema:'render-window-clock-v1',durationMs:measurementEndMs-pilot.measurementStartMs,firstDrawMs:pilot.firstDrawMs,lastDrawMs:last?last-pilot.measurementStartMs:null,drawCount:pilot.firstDrawMs===null?0:pilot.frames.length+1},renderCounters:pilot.renderCounters,events:pilot.events,actionFrames:pilot.actionFrames,movingFrames:pilot.movingFrames,liveEnemyFrames:pilot.liveEnemyFrames,animationModeChanges:pilot.animationModeChanges,simulationSeconds:s.time-pilot.startTime,movedMetres:s.movedDistance-pilot.startDistance,status:s.status,area:s.area,player:{hp:s.player.hp,maxHp:s.player.maxHp,healthPotions:s.player.healthPotions},drawCalls:d.numDrawCalls,triangles:d.numTris,gfxBytes:{...d.memoryStatus},models:cc.director.getScene().renderScene.models.length,heapBytes:performance.memory?.usedJSHeapSize??null};
  };
  return {renderer:cc.director.root.device.renderer, canvas:[cc.game.canvas.width,cc.game.canvas.height], frameRate:cc.game.frameRate, cores:navigator.hardwareConcurrency,texturePolicy:{imageCleanup:cc.macro.CLEANUP_IMAGE_CACHE,dynamicAtlasEnabled:cc.dynamicAtlasManager.enabled,atlasCount:cc.dynamicAtlasManager.atlasCount,atlasSize:cc.dynamicAtlasManager.textureSize},workloadRules:{enemyProfiles:ENEMY_COMBAT_PROFILES,skills:COMBAT_SKILLS,combat:COMBAT_RULES,loadouts:COMBAT_LOADOUTS,resource:RESOURCE_RULES}};
};
