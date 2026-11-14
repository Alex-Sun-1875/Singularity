/* Real Cocos/Bullet command pilot. No quest, inventory, health or enemy grants. */
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const output = path.resolve(__dirname, '../test-results');
const flatView=(process.env.CHAPTER_URL||'').includes('view=2d');
const resultFile = path.join(output, flatView?'flat2d-browser-playthrough.json':process.env.CHAPTER_URL?'browser-playthrough-release.json':'browser-playthrough.json');
const report = { started: new Date().toISOString(), url: process.env.CHAPTER_URL || 'http://localhost:7456/', status: 'running', stages: [], console: [], network: [], screenshots: [] };
let browser, page;
const persist = () => fs.writeFileSync(resultFile, JSON.stringify(report, null, 2));

async function capture(name) {
  await page.evaluate(async () => {
    const app = globalThis.__chapter.app;
    app.actors.update(app.session, .05, false);
    app.effects.update(app.session);
    app.positionCamera(1);
    app.renderModal();
    app.hud.clearModal();
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  });
  const filename = `${flatView?'flat2d-':''}browser-playthrough-${name}.png`;
  await page.screenshot({ path: path.join(output, filename) });
  report.screenshots.push({ name, file: filename, area: await page.evaluate(() => __chapter.state.area) });
  persist();
}

async function stage(name, method, ...args) {
  const result = await page.evaluate(async ({ method, args }) => {
    await globalThis.__qaPilot[method](...args);
    return globalThis.__qaPilot.snapshot();
  }, { method, args });
  const {visits,history,bundles,...state}=result;
  report.stages.push({ name, ...state });
  report.areas=visits;report.commands=history;report.bundles=bundles;
  persist();
  console.log(JSON.stringify({ stage: name, area: result.area, hp: result.player.hp, virtualSeconds: result.time, actors: result.actors.length, kills: result.kills.length }));
  return result;
}

(async () => {
  fs.mkdirSync(output, { recursive: true });
  browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: !process.argv.includes('--headed'), args: ['--enable-unsafe-swiftshader'] });
  page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('console', message => {
    if (['error', 'warning'].includes(message.type())) report.console.push({ type: message.type(), text: message.text() });
    if (message.text().startsWith('[QA]')) console.log(message.text());
  });
  page.on('pageerror', error => report.console.push({ type: 'pageerror', text: error.stack || String(error) }));
  page.on('requestfailed', request => report.network.push({ url: request.url(), error: request.failure()?.errorText }));
  await page.goto(report.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  if(process.env.CHAPTER_URL){
    await page.waitForFunction(()=>globalThis.System);
    await page.evaluate(async()=>{if(!globalThis.__chapter){const engine=await System.import('cc');globalThis.__chapter={get app(){return engine.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');},get state(){return this.app?.session.state;},inspect(){const a=this.app;return {ready:!!a?.actors&&!a.loading&&!a.failure,errors:a?.failure,actors:a?.actors?.inspect()};}};}});
    await page.waitForFunction(()=>globalThis.__chapter?.inspect().ready,null,{timeout:90000});
    await page.evaluate(async()=>{__chapter.areas=(await System.import('chunks:///_virtual/WorldData.ts')).AREAS;});
  }
  await page.waitForFunction(() => globalThis.__chapter?.inspect().ready && globalThis.__chapter?.areas, undefined, { timeout: 90000 });
  // A normal browser gesture enables game audio. The pilot then pauses the
  // normal frame advance and drives the same session against the real world.
  await page.mouse.click(640, 540);
  await page.evaluate(async () => {
    const check = (value, message) => { if (!value) throw new Error(message); };
    const flatRequired=actor=>actor.modelId==='raphael'?['idle','walk','run','attack_sword','attack_bow','attack_staff','spell','dodge','hit','death','interact']:['raider','raider-shield','raider-archer','captain'].includes(actor.modelId)?['idle','walk',actor.modelId==='raider-archer'?'attack_bow':'attack_sword','hit','death']:['idle'];
    const checkFlat=actor=>check(actor.loaded3DModel===false&&actor.reusedConcept===false&&actor.conceptAsset===actor.modelId&&actor.renderer==='native-unlit-quad'&&actor.materialPasses>0&&actor.frame>=0&&flatRequired(actor).every(clip=>actor.clips.includes(clip)),`invalid independent 2D actor: ${JSON.stringify(actor)}`);
    const distance = (a, b) => Math.hypot(a.x - b.x, a.z - b.z);
    const frames = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    class CocosPilot {
      constructor() {
        this.app = __chapter.app; this.app.menu = 'qa'; this.app.clearInput();
        this.areas = __chapter.areas; this.count = 0; this.visits = []; this.history = []; this.events = {};this.bundles=[];
        this.minimumHP = this.game.state.player.hp;
      }
      get game() { return this.app.session; }
      get current() { return this.app.world.area; }
      get nav() { return this.app.world.navigation; }
      snapshot() {
        const s = this.game.state;
        const terrain=this.app.world.terrain;
        return { area: s.area, time: s.time, player: { ...s.player }, objective: this.game.objective(), flags: { ...s.flags }, inventory: { ...s.inventory }, actors: this.app.actors.inspect(), enemies: s.enemies.map(e => ({ id: e.id, kind: e.kind, hp: e.hp, phase: e.phase })), kills: Object.keys(s.receipts).filter(key => key.startsWith('kill:')), visits: this.visits, history: this.history,bundles:this.bundles, eventCounts: this.events, minimumHP: this.minimumHP, terrain:terrain?{height:this.app.world.height(s.player),ramps:terrain.ramps,bridges:terrain.bridges,waters:terrain.waters,barriers:terrain.barriers.length}:null };
      }
      record(events) {
        for (const event of events) this.events[event.type] = (this.events[event.type] || 0) + 1;
        this.app.process(events.filter(event => event.type !== 'travel' && event.type !== 'retry'));
        this.app.menu = 'qa';
      }
      async ready() {
        await frames(); await frames();
        check(!this.app.loading && !this.app.failure, `scene not ready ${this.current.id}: ${this.app.failure}`);
        check(this.app.world.colliders.every(collider => collider.isValid), `invalid Bullet collider ${this.current.id}`);
        const actors = this.app.actors.inspect();
        check(actors.length >= 1 && actors.some(actor => actor.id === 'player'), `missing player prefab ${this.current.id}`);
        const expectedActors = ['player',...this.game.state.enemies.map(enemy => enemy.id),...this.current.objects.filter(object => object.actor).map(object => object.actor)];
        if (this.current.id === 'U1-04') expectedActors.push('mira','kael');
        for (const id of new Set(expectedActors)) check(actors.some(actor => actor.id === id), `missing instantiated actor ${this.current.id}/${id}`);
        const expected = ['idle', 'walk', 'run', 'attack_sword', 'attack_bow', 'attack_staff', 'spell', 'dodge', 'hit', 'death', 'interact'];
        for (const actor of actors) {
          if(actor.profile==='flat-concept-v1')checkFlat(actor);
          else {check(expected.every(clip => actor.clips.includes(clip)), `missing eleven clips ${this.current.id}/${actor.id}: ${actor.clips}`);check(actor.skeletons.length > 0 && actor.skeletons.every(bones => (actor.expectedSkeletonSizes??[53]).includes(bones)), `invalid source-rig skinned prefab ${this.current.id}/${actor.id}: ${actor.skeletons}`);}
        }
        for (const actor of this.app.actors.active.values()) check(actor.model.isValid && (actor.animation||actor.renderer?.mesh) && actor.root.parent === this.app.world.root, `actor not instantiated in current world ${actor.id}`);
        const flat=this.app.flatWorld?.inspect();if(flat)check(flat.ready&&flat.originalVolumeRenderersVisible===0&&flat.unmappedSourceKeys.length===0,`incomplete 2D map ${this.current.id}: ${JSON.stringify(flat)}`);
        this.visits.push({ area: this.current.id, colliders: this.app.world.colliders.length, actors, physics: 'real SceneBuilder/Bullet raycasts', terrain:this.app.world.terrain?{ramps:this.app.world.terrain.ramps,bridges:this.app.world.terrain.bridges,waterCount:this.app.world.terrain.waters.length,barriers:this.app.world.terrain.barriers.length}:null, time: this.game.state.time });
        this.app.menu = 'qa';
      }
      async step(input) {
        this.record(this.game.advance(.05, input));
        this.minimumHP = Math.min(this.minimumHP, this.game.state.player.hp);
        check(this.game.state.status !== 'dead', `pilot died ${this.current.id}: ${JSON.stringify(this.snapshot())}`);
        this.app.actors.update(this.game, .05, Math.hypot(input.x, input.z) > .1);
        this.app.effects.update(this.game);
        if (this.count > 0 && this.count % 600 === 0) console.log(`[QA] ${this.current.id} simulated${Math.round(this.game.state.time)}s hp${this.game.state.player.hp} alive${this.game.state.enemies.filter(enemy=>enemy.hp>0).length}`);
        if (++this.count % 24 === 0) await frames();
      }
      vector(target) {
        const p = this.game.state.player, d = distance(p, target), scale = Math.min(1, d / .18);
        return d > .01 ? { x: (target.x - p.x) / d * scale, z: (target.z - p.z) / d * scale } : { x: 0, z: 0 };
      }
      approach(target) {
        const p = this.game.state.player, route = this.app.world.path(p, target);
        check(route.length, `no real navigation path ${this.current.id}: ${JSON.stringify(p)} -> ${JSON.stringify(target)}`);
        let next = route[1] || target;
        for (let i = 2; i < route.length; i++) { if (!this.nav.visible(p, route[i], .42)) break; next = route[i]; }
        return this.vector(next);
      }
      async fight(enemy) {
        console.log(`[QA] fight ${this.current.id}/${enemy.id}`);
        const startingHP = this.game.state.player.hp;
        for (let n = 0; enemy.hp > 0 && n < 16000; n++) {
          const p = this.game.state.player, d = distance(p, enemy), angle = Math.atan2(enemy.x - p.x, enemy.z - p.z);
          let movement = { x: 0, z: 0 };
          if (d > 6.2 || !this.app.world.visible(p, enemy)) movement = this.approach(enemy);
          else if (d < 4.5 || enemy.kind === 'captain' && enemy.attackKind === 'charge' && ['windup', 'active'].includes(enemy.phase)) {
            let best = -Infinity, target = null;
            for (let k = 0; k < 24; k++) {
              const a = k * Math.PI / 12, q = { x: p.x + Math.sin(a) * 1.6, z: p.z + Math.cos(a) * 1.6 };
              if (!this.app.world.visible(p, q) || !this.nav.visible(p, q, .42)) continue;
              const closest = Math.min(...this.game.state.enemies.filter(enemy => enemy.hp > 0).map(enemy => distance(q, enemy)));
              let score = closest - Math.abs(distance(q, enemy) - 5) * .25;
              if (enemy.kind === 'captain' && enemy.attackKind === 'charge') score += Math.abs(Math.sin(a - enemy.targetAngle)) * 2;
              if (score > best) { best = score; target = q; }
            }
            if (target) movement = this.vector(target);
          }
          await this.step({ ...movement, aim: angle, attack: true });
        }
        check(enemy.hp === 0, `enemy not defeated ${this.current.id}/${enemy.id}: ${JSON.stringify(this.snapshot())}`);
        this.history.push({ action: 'combat', area: this.current.id, enemy: enemy.id, startingHP, endingHP: this.game.state.player.hp, time: this.game.state.time });
      }
      async walk(target,arrival=.7) {
        let route = this.app.world.path(this.game.state.player, target).slice(1);
        for (let n = 0; distance(this.game.state.player, target) > arrival && n < 12000; n++) {
          const threat = this.game.state.enemies.filter(enemy => enemy.hp > 0 && distance(enemy, this.game.state.player) < 6.8).sort((a, b) => distance(a, this.game.state.player) - distance(b, this.game.state.player))[0];
          if (threat) { await this.fight(threat); route = this.app.world.path(this.game.state.player, target).slice(1); continue; }
          while (route.length && distance(this.game.state.player, route[0]) < .16) route.shift();
          await this.step(route.length ? this.vector(route[0]) : this.approach(target));
        }
        check(distance(this.game.state.player, target) <= arrival, `walking stalled ${this.current.id} to ${JSON.stringify(target)} at ${JSON.stringify(this.game.state.player)}`);
        this.game.cancelInput();
      }
      async interact(action) {
        const object = this.current.objects.find(object => object.action === action);
        check(object, `missing ${action} in ${this.current.id}`);
        if(this.nav.blocked(object,.32)){
          // A solid table/chest's interaction anchor is inside its footprint.
          // Walk through real navigation to a legal, visible point within the
          // unchanged core 1.35m interaction radius; never walk through furniture.
          const options=[];for(let i=0;i<32;i++){const angle=i*Math.PI/16,q={x:object.x+Math.sin(angle)*1.28,z:object.z+Math.cos(angle)*1.28};if(this.nav.blocked(q)||!this.app.world.visible(q,object))continue;const path=this.app.world.path(this.game.state.player,q);if(path.length)options.push({q,cost:path.slice(1).reduce((sum,p,i)=>sum+distance(p,path[i]),0)});}
          check(options.length,`no legal interaction approach ${this.current.id}/${object.id}`);options.sort((a,b)=>a.cost-b.cost);await this.walk(options[0].q,.04);
        }else await this.walk(object);
        const events = this.game.interact(object); this.record(events);
        this.history.push({ action, area: this.current.id, object: object.id, distance:distance(this.game.state.player,object),position:{x:this.game.state.player.x,z:this.game.state.player.z},events, time: this.game.state.time });
        check(events.length > 0, `no interaction result ${this.current.id}/${object.id}`);
      }
      async choose(choice) {
        check(this.game.state.dialogue?.options.some(option => option.id === choice), `missing dialogue choice ${choice}`);
        this.record(this.game.choose(choice)); await frames();
      }
      async clear() {
        while (this.game.state.enemies.some(enemy => enemy.hp > 0)) {
          const enemy = this.game.state.enemies.filter(enemy => enemy.hp > 0).sort((a, b) => distance(a, this.game.state.player) - distance(b, this.game.state.player))[0];
          await this.fight(enemy);
        }
        this.game.cancelInput(); await frames();
      }
      async go(id) {
        const queue = [[this.current.id, []]], seen = new Set(); let route;
        while (queue.length) {
          const [at, steps] = queue.shift(); if (at === id) { route = steps; break; }
          if (seen.has(at)) continue; seen.add(at);
          for (const exit of this.areas[at].exits) if (!exit.requires || this.game.state.flags[exit.requires]) queue.push([exit.to, [...steps, exit.id]]);
        }
        check(route, `no open world route ${this.current.id} -> ${id}`);
        for (const exitID of route) {
          const exit = this.current.exits.find(exit => exit.id === exitID); await this.walk(exit);
          const events = this.game.travel(exit);
          check(events.some(event => event.type === 'travel'), `real travel rejected ${exitID}: ${JSON.stringify(events)}`);
          this.history.push({ action: 'travel', from: this.current.id, to: exit.to, exit: exitID, time: this.game.state.time });
          // rebuild enters the destination using the committed reciprocal entry.
          // Never process this travel event as well: that would rebuild twice.
          await this.app.rebuild(); this.app.menu = 'qa'; await this.ready();
          console.log(`[QA] entered ${this.current.id}`);
        }
      }
      async start() {
        check(this.current.id === 'S01-T1', `fresh browser journey should start in T1, got ${this.current.id}`);
        await this.ready(); check(this.game.equip('W11'), 'normal checkpoint staff equip rejected');
        // Validate the two optional merchants as well as every model used by
        // the chapter route. QA instances stay offscreen and are disposed
        // immediately; no session actor, quest, health or inventory is changed.
        for(const model of ['raphael','mira','lorn','nightqi','kael','evelyn','raider','raider-shield','raider-archer','captain']){
          const id=`qa-bundle-${model}`,actor=await this.app.actors.create(id,model,1000,1000);
          check(actor?.model?.isValid,`bundle prefab failed to instantiate actor-${model}`);
          const inspection=this.app.actors.inspect().find(actor=>actor.id===id);
          if(inspection.profile==='flat-concept-v1')checkFlat(inspection);
          else check(['idle','walk','run','attack_sword','attack_bow','attack_staff','spell','dodge','hit','death','interact'].every(name=>inspection.clips.includes(name))&&inspection.skeletons.length>0&&inspection.skeletons.every(bones=>(inspection.expectedSkeletonSizes??[53]).includes(bones)),`invalid bundle rig actor-${model}: ${JSON.stringify(inspection)}`);
          this.bundles.push({bundle:inspection.profile==='flat-concept-v1'?null:`actor-${model}`,model,presentation:inspection.profile,instantiated:true,clips:inspection.clips,skeletons:inspection.skeletons,loaded3DModel:inspection.loaded3DModel});
          actor.root.destroy();this.app.actors.active.delete(id);
        }
        await frames();
      }
      async finish() {
        check(this.game.state.flags.complete, `chapter did not complete: ${this.game.objective()}`);
        check(this.game.state.player.gold === 120, `accepted path gold should be120, got ${this.game.state.player.gold}`);
        check(this.game.state.inventory.W02 === 1, 'captain gate did not grant W02');
        this.app.save(); await frames();
      }
    }
    globalThis.__qaPilot = new CocosPilot();
  });
  await stage('opening', 'start');
  await stage('offer', 'interact', 'offer');
  await stage('accepted-without-copy', 'choose', 'accept');
  await stage('walk-to-cart', 'go', 'S04');
  await stage('cart-guards-defeated', 'clear');
  await stage('relic-recovered', 'interact', 'recover');
  await capture('s04-cart');
  await stage('original-letter', 'interact', 'letter');
  await stage('original-letter-read', 'choose', 'read_letter');
  await stage('underground-before-captain', 'go', 'U1-04');
  await stage('dinner', 'interact', 'meeting');
  await capture('u1-dinner');
  await stage('cooperation-choice', 'choose', 'cooperate');
  await stage('walk-to-workers', 'go', 'U1-05');
  await stage('trap-disabled', 'interact', 'disable_trap');
  await stage('workers-released', 'interact', 'release_workers');
  await stage('walk-to-captain', 'go', 'S10');
  await stage('captain-defeated', 'clear');
  await capture('s10-arena');
  await stage('captain-gate-reward', 'interact', 'captain_gate');
  await stage('return-to-dinner', 'go', 'U1-04');
  await stage('chapter-finished', 'interact', 'finish');
  const final = await stage('verified-final-state', 'finish');
  const {visits,history,bundles,...finalState}=final;report.final=finalState;
  await capture('complete');
  const errors = report.console.filter(event => event.type === 'error' || event.type === 'pageerror');
  assert.equal(errors.length, 0, `Cocos emitted errors: ${JSON.stringify(errors)}`);
  assert.equal(report.network.length, 0, `resource requests failed: ${JSON.stringify(report.network)}`);
  report.status = 'passed'; report.finished = new Date().toISOString(); persist();
  console.log(JSON.stringify({ status: report.status, report: resultFile, areas: [...new Set(final.visits.map(visit => visit.area))], hp: final.player.hp, minimumHP: final.minimumHP, kills: final.kills.length, errors: errors.length, screenshots: report.screenshots }));
})().catch(async error => {
  report.status = 'failed'; report.error = error.stack || String(error); report.finished = new Date().toISOString();
  if (page && !page.isClosed()) {
    try { report.failureState = await page.evaluate(() => globalThis.__qaPilot?.snapshot() || globalThis.__chapter?.inspect() || { body: document.body.innerText.slice(0, 1500) }); } catch (snapshotError) { report.snapshotError = String(snapshotError); }
    try { await capture('failure'); } catch (screenshotError) { report.screenshotError = String(screenshotError); }
  }
  persist(); console.error(error); process.exitCode = 1;
}).finally(async () => {
  try { await page?.close(); } finally { await browser?.close(); }
});
