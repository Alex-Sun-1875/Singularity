import test from 'node:test';
import assert from 'node:assert/strict';
import { AREAS, R1_ROADS, getArea } from '../assets/scripts/features/world/data/WorldData';
import type { AreaDef, Point, WorldQuery } from '../assets/scripts/core/Contracts';
import { Navigation } from '../assets/scripts/features/navigation/runtime/Navigation';
import { GameSession } from '../assets/scripts/core/GameSession';
import {CAMPAIGN_BOSSES,CAMPAIGN_LEVEL_LIST} from '../assets/scripts/features/campaign/data/Campaign';
import {CAMPAIGN_EVENTS} from '../assets/scripts/features/campaign/data/CampaignEvents';
import {awardXp,cumulativeXp} from '../assets/scripts/features/progression/common/Progression';
import {CAMPAIGN_ROADS} from '../assets/scripts/features/world/data/CampaignGeography';

const expectedRoads = `01-02 01-03 01-04 01-20 02-18 02-19 03-04 03-19 04-07 04-08 05-19 05-06 05-07 06-14 06-15 07-08 07-13 07-14 07-17 08-09 08-11 09-10 09-20 10-11 11-12 11-17 12-13 12-16 13-14 13-16 13-17 14-15 15-16`.split(' ').map(edge => edge.split('-').map(id => `S${id}`).sort().join('|')).sort();
const edge = (a: string, b: string) => [a, b].sort().join('|');
const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.z - b.z);
const objects = () => Object.values(AREAS).flatMap(area => area.objects.map(object => ({ area: area.id, ...object })));

test('v3 roads give exactly the approved 33 bidirectional walking connections', () => {
  assert.deepEqual(R1_ROADS.map(([a, b]) => edge(a, b)).sort(), expectedRoads);
  assert.equal(new Set(R1_ROADS.map(([a, b]) => edge(a, b))).size, 33);
  assert.equal(Object.keys(AREAS).filter(id => /^S\d\d$/.test(id)).length, 20);
  for (const [a, b] of R1_ROADS) {
    assert.equal(getArea(a).exits.filter(exit => exit.to === b).length, 1, `${a}→${b}`);
    assert.equal(getArea(b).exits.filter(exit => exit.to === a).length, 1, `${b}→${a}`);
  }
  for (const area of Object.values(AREAS)) for (const exit of area.exits) {
    assert.ok(AREAS[exit.to], `${area.id} must not teleport to unbuilt ${exit.to}`);
    assert.ok(AREAS[exit.to].exits.some(back => back.to === area.id), `${area.id}→${exit.to} has a return`);
    if (/^S\d\d$/.test(area.id) && /^S\d\d$/.test(exit.to)) assert.ok(expectedRoads.includes(edge(area.id, exit.to)));
  }
});

test('town districts and the first underground loop preserve the geography graph', () => {
  const townEdges = new Set(Object.values(AREAS).filter(area => /^S01-T[1-6]$/.test(area.id)).flatMap(area => area.exits.filter(exit => exit.to.startsWith('S01-T')).map(exit => edge(area.id, exit.to))));
  assert.deepEqual([...townEdges].sort(), ['1-2','2-6','6-3','3-4','4-1','5-2','5-6'].map(pair => edge(...pair.split('-').map(id => `S01-T${id}`) as [string,string])).sort());
  const underground = new Set(Object.values(AREAS).filter(area => area.id.startsWith('U1-')).flatMap(area => area.exits.filter(exit => exit.to.startsWith('U1-')).map(exit => edge(area.id, exit.to))));
  assert.deepEqual([...underground].sort(), CAMPAIGN_ROADS.filter(road=>road.a.startsWith('U1-')).map(road=>edge(road.a,road.b)).sort());
  assert.equal(Object.keys(AREAS).filter(id => id.startsWith('U2-')).length,9);
  assert.deepEqual(Object.keys(AREAS).sort(),CAMPAIGN_LEVEL_LIST.map(area=>area.id).sort());
  assert.ok(getArea('S16').exits.some(exit=>exit.to==='H01'));
  assert.ok(getArea('S15').exits.some(exit=>exit.to==='B15'));
  assert.ok(getArea('U2-01').exits.some(exit=>exit.to==='U2-02'&&exit.requires==='u2_deep_gate_open'));
  assert.ok(!objects().some(object=>object.action==='boundary'));
});

test('portals can only first open from the prescribed side without quest locks', () => {
  const exit = (from: string, to: string) => getArea(from).exits.find(e => e.to === to)!;
  for (const [from, to, flag] of [['S07','U1-01','e01_open'],['S13','U1-03','e02_open'],['U1-02','S17','e03_open']]) {
    assert.equal(exit(from, to).unlock, flag);
    assert.equal(exit(from, to).requires, undefined);
    assert.equal(exit(to, from).requires, flag);
    assert.equal(exit(to, from).unlock, undefined);
  }
  assert.equal(exit('S15','U2-01').requires, undefined);
  assert.equal(exit('U2-01','S15').requires, undefined);
  for(const [from,to,flag,eventId]of [['H05','U1-09','e05_open','h05-stop-hoist'],['U1-10','B01','e07_open','u110-open-exit'],['U2-09','F16','e08_open','u209-open-service']]){
    assert.equal(exit(from,to).requires,flag);assert.equal(exit(to,from).requires,flag);
    assert.equal(CAMPAIGN_EVENTS[eventId].area,from);assert.ok(CAMPAIGN_EVENTS[eventId].sets?.includes(flag));
  }
  for(const [from,to,flag]of [['H08','H09','m4_bridge_open'],['B11','B10','harbor_access'],['F12','F13','final_ready'],['F13','F14','boss_defeated:BOSS_R4']])assert.equal(exit(from,to).requires,flag);
});

test('story beats have unique people and independent evidence in their actual locations', () => {
  const all = objects();
  for (const [actor, area] of [['mira','S01-T1'],['lorn','S01-T3'],['nightqi','S05'],['kael','U1-04'],['evelyn','U1-04']]) {
    assert.deepEqual(all.filter(object => object.actor === actor).map(object => object.area), [area]);
  }
  for (const [action, area] of [['offer','S01-T1'],['recover','S04'],['letter','S04'],['captain_gate','S10'],['meeting','U1-04'],['release_workers','U1-05'],['disable_trap','U1-05'],['finish','U1-04']]) {
    assert.deepEqual(all.filter(object => object.action === action).map(object => object.area), [area]);
  }
  assert.ok(getArea('S01-T2').objects.some(object => object.action === 'independent_clue'));
  assert.ok(getArea('S07').objects.some(object => object.action === 'independent_clue'));
  assert.equal(new Set(all.filter(object => object.evidence).map(object => object.evidence)).size, all.filter(object => object.evidence).length);
});

test('permanent equipment sources remain finite and do not duplicate merchant stock', () => {
  const caches = objects().filter(object => object.action === 'cache' && object.item && /^[WAJT]\d\d$/.test(object.item));
  const sources: Record<string,string> = { W08:'S08', A01:'S09', A02:'S11', A06:'S05', A09:'S18', A14:'S20', J08:'S01-T3',J01:'B04',W12:'B08',A03:'B08',J02:'H13',W14:'F11',A15:'U2-07',J07:'F17' };
  assert.deepEqual(caches.map(object => object.item).sort(), Object.keys(sources).sort());
  for (const cache of caches) assert.equal(cache.area, sources[cache.item!]);
  assert.ok(!caches.some(cache=>cache.item?.startsWith('T')));
  assert.ok(getArea('S07').objects.some(object=>object.eventId==='s07-skill-archive'));
  assert.ok(!objects().some(object => object.action === 'cache' && ['A10','A13','J03','W02','T03'].includes(object.item!)));
  assert.deepEqual(objects().filter(object => object.merchant).map(object => [object.area,object.merchant]).sort(), [['S01-T1','mira'],['S01-T3','lorn'],['S05','nightqi'],['H02','severin'],['B03','elise']].sort());
});

// Test real navigation: a 0.6m radius walker must reach every interactive point,
// spawn, exit and reciprocal entry without passing through a collider.
function walkable(area: AreaDef, point: Point): boolean {
  return Math.abs(point.x) <= area.width / 2 - 0.7 && Math.abs(point.z) <= area.depth / 2 - 0.7 && !area.obstacles.some(obstacle => Math.abs(point.x - obstacle.x) < obstacle.width / 2 + 0.7 && Math.abs(point.z - obstacle.z) < obstacle.depth / 2 + 0.7);
}
function reachableCells(area: AreaDef): Set<string> {
  const start = { x: Math.round(area.spawn.x), z: Math.round(area.spawn.z) };
  assert.ok(walkable(area, start), `${area.id} has a safe spawn`);
  const queue = [start], seen = new Set([`${start.x},${start.z}`]);
  for (let i = 0; i < queue.length; i++) {
    const current = queue[i];
    for (const [dx, dz] of [[1,0],[-1,0],[0,1],[0,-1]]) {
      const next = { x: current.x + dx, z: current.z + dz }, key = `${next.x},${next.z}`;
      if (!seen.has(key) && walkable(area, next)) { seen.add(key); queue.push(next); }
    }
  }
  return seen;
}

test('all local points and return entries are collision free and physically reachable', () => {
  const ids: string[] = [];
  for (const area of Object.values(AREAS)) {
    assert.ok(area.width >= (area.kind === 'interior' ? 28 : 90) && area.width <= 160 && area.depth >= (area.kind === 'interior' ? 28 : 90) && area.depth <= 160, `${area.id} has usable landmark space`);
    if (area.kind !== 'interior') assert.ok(area.buildings.length >= 2, `${area.id} has several landmark spaces`);
    const cells = reachableCells(area);
    for (const object of [...area.objects, ...area.exits, ...area.enemies]) {
      ids.push(object.id);
      assert.ok(walkable(area, object), `${area.id}/${object.id} is outside obstacles`);
      assert.ok(cells.has(`${Math.round(object.x)},${Math.round(object.z)}`), `${area.id}/${object.id} has an actual walking approach`);
    }
    for (const exit of area.exits) {
      const destination = getArea(exit.to);
      assert.ok(walkable(destination, exit.entry), `${area.id}/${exit.id} return entry is safe`);
      assert.ok(Math.abs(exit.x) >= area.width / 2 - 3 || Math.abs(exit.z) >= area.depth / 2 - 3 || exit.id.includes('door') || exit.id.includes('E0'), `${area.id}/${exit.id} is on an actual border or doorway`);
      for (const other of area.exits) if (other.id !== exit.id) assert.ok(distance(exit,other) > 3, `${area.id} has distinct walking thresholds for ${exit.id} and ${other.id}`);
    }
    for (const building of area.buildings) assert.ok(area.obstacles.some(obstacle => obstacle.kind === 'building' && obstacle.x === building.x && obstacle.z === building.z && obstacle.width === building.width && obstacle.depth === building.depth), `${area.id}/${building.name} has matching collision`);
    for (const obstacle of area.obstacles) assert.ok(Math.abs(obstacle.x) + obstacle.width / 2 <= area.width / 2 && Math.abs(obstacle.z) + obstacle.depth / 2 <= area.depth / 2, `${area.id} collider remains inside bounds`);
    assert.ok(area.objects.every(object => object.description.length > 12), `${area.id} interactions explain a distinct situation`);
  }
  assert.equal(ids.length, new Set(ids).size, 'all objects, enemies and exits have stable globally unique identities');
});

test('town interiors are furnished rooms at human scale with walls and reachable door openings', () => {
  for (const building of getArea('S01').buildings) {
    const door = getArea('S01').exits.find(exit => exit.to === building.enter)!;
    const angle = (building.rotation ?? 0) * Math.PI / 180;
    const inFront = -(door.x-building.x)*Math.sin(angle)-(door.z-building.z)*Math.cos(angle);
    assert.ok(inFront > building.depth / 2, `${building.name} has its walking threshold in front of the visible door`);
  }
  for (let n = 1; n <= 6; n++) {
    const room = getArea(`S01-T${n}`);
    assert.ok(room.width <= 48 && room.depth <= 40, `${room.id} is a room or compact courtyard, not a field`);
    assert.ok(room.obstacles.filter(o => o.kind === 'wall').length >= 8, `${room.id} has perimeter and internal walls`);
    assert.ok(room.obstacles.filter(o => ['table','bench','shelf','forge'].includes(o.kind!)).length >= 3, `${room.id} has usable room furnishings`);
    for (const exit of room.exits) assert.ok(walkable(room, exit), `${exit.id} goes through a physical wall opening`);
  }
});

test('rendered movement navigation can approach actual content and every return landing', () => {
  for (const area of Object.values(AREAS)) {
    const nav = new Navigation(area.width,area.depth,area.obstacles);
    for (const target of [...area.objects,...area.exits]) assert.ok(nav.path(area.spawn,target).length, `${area.id} production navigation reaches ${target.id}`);
    for (const incoming of Object.values(AREAS).flatMap(from => from.exits.filter(exit => exit.to === area.id))) assert.ok(nav.path(incoming.entry,area.spawn).length, `${area.id} can walk inward after ${incoming.id}`);
  }
});

test('encounters leave safe entrances, NPC positions and checkpoints and keep the captain solo', () => {
  for (const area of Object.values(AREAS)) {
    assert.ok(area.enemies.filter(enemy=>!enemy.respawnSeconds).length <= 8 && area.enemies.length <= 29, `${area.id} keeps the fixed encounter budget plus bounded hunting packs`);
    const safePoints = [...area.exits, ...area.objects.filter(object => object.actor || object.action === 'checkpoint')];
    for (const enemy of area.enemies) {
      assert.ok(distance(enemy, area.spawn) >= 12, `${area.id}/${enemy.id} does not attack the checkpoint`);
      for (const point of safePoints) assert.ok(distance(enemy, point) >= 10, `${area.id}/${enemy.id} avoids ${'id' in point ? point.id : 'safe point'}`);
    }
  }
  const boss = getArea('S10');
  assert.deepEqual(boss.enemies.map(enemy => enemy.kind), ['captain']);
  for(const definition of CAMPAIGN_BOSSES){
    const arena=getArea(definition.arena!);
    assert.ok(arena.enemies.some(enemy=>enemy.bossId===definition.id),`${definition.id} appears in its real arena`);
    assert.deepEqual(arena.obstacles.filter(obstacle=>obstacle.kind==='pillar').map(obstacle=>[obstacle.x,obstacle.z]).sort(),[[-11,12],[11,12]]);
    assert.ok(arena.obstacles.filter(obstacle=>obstacle.kind!=='pillar').every(obstacle=>Math.abs(obstacle.x)-obstacle.width/2>=18||Math.abs(obstacle.z-15)-obstacle.depth/2>=13),`${definition.id} has 36×26m firing floor with sparse cover`);
  }
});

test('the existing S08 pass guard supplies one real kill drop and T1 is a safe opening checkpoint', () => {
  const pass = getArea('S08'), eligible = Object.values(AREAS).flatMap(area => area.enemies.filter(enemy => enemy.id.includes('warden')).map(enemy => ({area:area.id,...enemy})));
  assert.deepEqual(eligible.map(enemy => [enemy.area,enemy.id,enemy.kind]), [['S08','s08-pass-warden','raider']]);
  assert.equal(pass.enemies.filter(enemy=>!enemy.templateId?.startsWith('BEAST_')).length,3,'the retained human encounter contains one controller and two melee enemies');
  const nav = new Navigation(pass.width,pass.depth,pass.obstacles);
  const game = new GameSession(73013,{move:(from,delta) => ({x:from.x+delta.x,z:from.z+delta.z}),visible:(from,to) => nav.visible(from,to),height:() => 0});
  game.enter(pass,{x:35,z:-7});
  const guard = game.state.enemies.find(enemy => enemy.id === 's08-pass-warden')!;
  for (let n = 0; n < 200 && guard.hp > 0; n++) game.advance(.05,{x:0,z:0,aim:Math.atan2(guard.x-game.state.player.x,guard.z-game.state.player.z),attack:true});
  assert.equal(guard.hp,0,'normal sword attacks defeat the actual content guard');
  assert.ok(game.state.receipts['kill:S08:s08-pass-warden']);
  assert.ok(game.state.dropRolls['pass:S08:s08-pass-warden'],'the eligible first kill actually records its random result');
  const first = JSON.stringify(game.state.dropRolls);
  game.enter(pass);game.advance(.05,{x:0,z:0});
  assert.equal(JSON.stringify(game.state.dropRolls),first,'reentering the pass does not roll again');
  const opening = new GameSession(1,{move:(from,delta) => ({x:from.x+delta.x,z:from.z+delta.z}),visible:()=>true,height:()=>0});
  opening.enter(getArea('S01-T1'));
  assert.equal(opening.state.checkpoint.area,'S01-T1');
  assert.deepEqual({x:opening.state.checkpoint.x,z:opening.state.checkpoint.z},getArea('S01-T1').spawn);
});

test('hunt-contract interaction reports its prerequisite, commits once, and restores its completed state',()=>{
 const world:WorldQuery={move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0};
 const g=new GameSession(19,world);awardXp(g.state.progression,'fixture',cumulativeXp(18));
 const rockwood=getArea('H14'),action=rockwood.objects.find(o=>o.eventId==='h14-cancel-hunt')!;
 g.enter(rockwood,action);
 const unavailable=g.campaignEventAvailability(action.eventId!);
 assert.equal(unavailable.available,false);assert.equal(unavailable.completed,false);
 assert.match(unavailable.reason,/湿林庄园/);assert.match(unavailable.reason,/被转卖的猎径副图/);
 const hp=g.state.enemies.map(e=>e.hp),blocked=g.interact(action);
 assert.ok(blocked.some(e=>e.type==='notice'&&e.text?.includes('被转卖的猎径副图')));
 assert.equal(g.state.receipts['campaign:h14-cancel-hunt'],undefined);assert.equal(g.state.flags.h14_hunt_cancelled,undefined);assert.deepEqual(g.state.enemies.map(e=>e.hp),hp);
 const estate=getArea('S14'),clue=estate.objects.find(o=>o.evidence==='s14-huntroute')!;
 g.enter(estate,clue);g.interact(clue);assert.equal(g.state.flags['s14-huntroute'],true);
 g.enter(rockwood,action);const ready=g.campaignEventAvailability(action.eventId!);
 assert.equal(ready.available,true);assert.equal(ready.confirmLabel,'缴销猎契');
 const wildlife=g.state.enemies.filter(e=>e.respawnSeconds).map(e=>({id:e.id,hp:e.hp})),done=g.interact(action);
 assert.equal(g.state.flags.h14_hunt_cancelled,true);assert.equal(g.state.receipts['campaign:h14-cancel-hunt'],true);
 assert.ok(g.state.enemies.filter(e=>!e.respawnSeconds).every(e=>e.hp===0));
 assert.deepEqual(g.state.enemies.filter(e=>e.respawnSeconds).map(e=>({id:e.id,hp:e.hp})),wildlife);
 assert.ok(done.some(e=>e.type==='quest'&&e.id==='h14-cancel-hunt'&&e.text?.includes('封锁已解除')));
 const rewards=()=>JSON.stringify({gold:g.state.player.gold,iron:g.state.player.iron,xp:g.state.progression.totalXp,inventory:g.state.inventory,rolls:g.state.dropRolls}),paid=rewards();
 assert.equal(g.campaignEventAvailability(action.eventId!).completed,true);assert.equal(g.approachInteractionVisible(action),false);
 assert.ok(g.interact(action).some(e=>e.type==='inspect'));assert.equal(rewards(),paid,'repeat confirmation never pays again');
 const restored=GameSession.restore(g.snapshot(),world);restored.enter(rockwood,action);
 assert.equal(restored.campaignEventAvailability(action.eventId!).completed,true);
 assert.equal(restored.campaignEventAvailability(action.eventId!).available,false);
 assert.match(restored.campaignEventAvailability(action.eventId!).reason,/猎契已缴销/);
});
