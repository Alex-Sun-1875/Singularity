import test from 'node:test';
import assert from 'node:assert/strict';
import {GameSession} from '../assets/scripts/core/GameSession';
import type {AreaDef,GameEvent,Point,WorldQuery} from '../assets/scripts/core/Contracts';
import type {CombatCast} from '../assets/scripts/features/combat/common/PureCombat';
import {warriorUltimateContactSpan,warriorUltimateTouches} from '../assets/scripts/features/combat/common/WarriorUltimate';
import {awardXp,baseMaxHp,cumulativeXp} from '../assets/scripts/features/progression/common/Progression';
import {activateCombatLoadout} from '../assets/scripts/features/progression/common/CombatLoadouts';

const idle={x:0,z:0};
const world:WorldQuery={move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0};
const area=(enemies:AreaDef['enemies']=[]):AreaDef=>({id:enemies.length?'S02':'S01',name:'Wave rules',subtitle:'',kind:'wild',palette:'meadow',width:48,depth:48,spawn:{x:0,z:0},atlas:{x:0,z:0},exits:[],objects:[],buildings:[],obstacles:[],enemies,checkpoint:true});
type Target=Point&{id:string};
type WaveState={origin:Point;angle:number;startedAt:number;previousAge:number;count:number};
type WaveCast=CombatCast&{ultimateWaves?:WaveState};
type WaveHit=GameEvent&{targetId:string;waveIndex:number;segment:number;value:number;waveAge?:number;waveOrigin?:Point};

function tick(game:GameSession,seconds:number,step=1/60):GameEvent[]{
 const events:GameEvent[]=[];
 for(let left=seconds;left>1e-9;){const dt=Math.min(step,left);events.push(...game.advance(dt,idle));left-=dt;}
 return events;
}

function battle(rank:number,targets:Target[]){
 const game=new GameSession(73014,world);game.enter(area());
 awardXp(game.state.progression,'wave-rules-fixture',cumulativeXp(40));
 game.state.player.maxHp=baseMaxHp(game.state.progression);game.state.player.hp=game.state.player.maxHp;
 activateCombatLoadout(game.state.combat,game.state.progression);
 assert.ok(game.applySkillPlan({...game.state.progression.learned,WAR_05:rank}));
 game.enter(area(targets.map(t=>({...t,kind:'raider' as const,hp:100000,trainingDummy:true,trainingAttacks:false}))));
 game.state.combat.passiveSlots=[null,null];
 const events=game.castSkill('WAR_05',{x:0,z:12},0);
 const cast=game.state.combat.casts.find(c=>c.skillId==='WAR_05') as WaveCast|undefined;
 assert.ok(cast,'the real ultimate must be accepted');
 assert.ok(events.some(e=>e.type==='skill_cast'&&e.castId===cast.id));
 return {game,cast,events};
}

function untilFinal(game:GameSession,cast:WaveCast):GameEvent[]{
 const events:GameEvent[]=[];
 for(let frame=0;frame<120&&!cast.ultimateWaves;frame++)events.push(...game.advance(1/60,idle));
 assert.ok(cast.ultimateWaves,'the real final segment must create its moving waves');
 return events;
}

function waveHits(events:GameEvent[]):WaveHit[]{
 return events.filter(e=>e.type==='skill_hit'&&e.skillId==='WAR_05'&&e.phase==='warriorWave') as WaveHit[];
}

function target(game:GameSession,id:string){const e=game.state.enemies.find(e=>e.id===id);assert.ok(e,id);return e;}
function damageBudget(cast:CombatCast){return cast.power*cast.rank.maxDamagePerTargetS*cast.attributeMultiplier*(cast.critical?cast.criticalMultiplier??1.5:1);}
function alongTargets():Target[]{const front=warriorUltimateContactSpan()[1];return [{id:'along-mid',x:0,z:front+1.7},{id:'along-far',x:0,z:front+3.6}];}

test('all five ultimate ranks move one, two or three real waves through each distant target exactly once',()=>{
 for(const [rank,count]of [[1,1],[2,2],[3,2],[4,3],[5,3]]){
  const route=alongTargets(),{game,cast,events}=battle(rank,[...route,{id:'side',x:3,z:route[1].z},{id:'behind',x:0,z:-2}]);
  const initial=game.state.enemies.map(e=>({id:e.id,hp:e.hp}));
  events.push(...untilFinal(game,cast));
  assert.equal(target(game,'along-far').hp,target(game,'along-far').maxHp,'a distant target cannot take the old stationary final hit');
  events.push(...tick(game,.10));
  assert.equal(target(game,'along-far').hp,target(game,'along-far').maxHp,'damage must wait for the visible wave to arrive');
  events.push(...tick(game,2));
  const hits=waveHits(events);
  for(const t of route){
   const contacts=hits.filter(e=>e.targetId===t.id);
   assert.deepEqual(contacts.map(e=>e.waveIndex).sort((a,b)=>a-b),Array.from({length:count},(_,i)=>i),`rank ${rank}, ${t.id}: each emitted wave must hit once`);
   assert.ok(contacts.every(e=>e.segment===2),'wave contacts retain the semantic final segment');
   const dealt=contacts.reduce((sum,e)=>sum+e.value,0);
   assert.ok(Math.abs(dealt-damageBudget(cast)*.6)<=count,`rank ${rank}: the waves share the final sixty-percent budget`);
  }
  for(const id of ['side','behind'])assert.equal(target(game,id).hp,initial.find(e=>e.id===id)!.hp,`${id} must remain outside the moving attack`);
  assert.equal(events.filter(e=>e.type==='skill_hit'&&e.skillId==='WAR_05'&&e.segment===2&&e.phase!=='warriorWave').length,0,'the old instantaneous final fan must not stack with the waves');
  const hp=target(game,'along-far').hp;
  assert.equal(waveHits(tick(game,1)).length,0,'an expired wave cannot hit again');
  assert.equal(target(game,'along-far').hp,hp);
 }
});

test('the near target receives the two real cuts without a stationary third hit before the first wave launches',()=>{
 const {game,cast,events}=battle(5,[{id:'near',x:0,z:1.2}]);
 events.push(...untilFinal(game,cast));
 const cuts=events.filter(e=>e.type==='skill_hit'&&e.skillId==='WAR_05'&&e.targetId==='near'&&e.phase!=='warriorWave');
 assert.deepEqual(cuts.map(e=>e.segment),[0,1]);
 assert.ok(Math.abs(cuts.reduce((sum,e)=>sum+Number(e.value),0)-damageBudget(cast)*.4)<=2);
 assert.equal(waveHits(events).length,0,'final contact starts after its authored launch delay');
});

test('an enemy entering the space behind a departed wave is not hit by the historical travelled path',()=>{
 const {game,cast,events}=battle(1,[{id:'late',x:9,z:1.2}]);
 events.push(...untilFinal(game,cast),...tick(game,.65));
 const late=target(game,'late'),hp=late.hp;late.x=0;
 events.push(...tick(game,1));
 assert.equal(late.hp,hp);
 assert.equal(waveHits(events).filter(e=>e.targetId==='late').length,0);
});

test('a raised target misses the low tail but can intersect the same wave at its high front',()=>{
 const tail={forward:.9,side:0},front={forward:5.25,side:0};
 assert.equal(warriorUltimateTouches(tail,.035,.04,.3),true,'the low tail crosses a standing body on the launch level');
 assert.equal(warriorUltimateTouches(tail,.035,.04,.3,1.1),false,'a body on a raised platform cannot be struck by air passing below its feet');
 assert.equal(warriorUltimateTouches(front,.035,.04,.3,1.1),true,'the high front still damages where its height overlaps the raised body');
});

test('a paused session preserves wave age and resumes the same released cast',()=>{
 const {game,cast,events}=battle(5,alongTargets());events.push(...untilFinal(game,cast),...tick(game,.08));
 const before={time:game.state.time,waves:JSON.stringify(cast.ultimateWaves),hp:game.state.enemies.map(e=>e.hp)};
 game.state.dialogue={id:'wave-pause-fixture',speaker:'',text:'',options:[]};
 assert.deepEqual(game.advance(1,idle),[]);
 assert.equal(game.state.time,before.time);assert.equal(JSON.stringify(cast.ultimateWaves),before.waves);assert.deepEqual(game.state.enemies.map(e=>e.hp),before.hp);
 game.state.dialogue=null;events.push(...tick(game,2));
 for(const id of ['along-mid','along-far'])assert.deepEqual(waveHits(events).filter(e=>e.targetId===id).map(e=>e.waveIndex).sort((a,b)=>a-b),[0,1,2]);
});

test('cancelling before the final release creates no future waves, while a released final cast survives action exit',()=>{
 for(const beforeFinal of [.10,.62]){
  const {game,cast,events}=battle(5,alongTargets());events.push(...tick(game,beforeFinal));
  if(beforeFinal<.49)game.cancelInput();else game.state.action=null;
  events.push(...tick(game,3));
  assert.equal(cast.ultimateWaves,undefined,'an interrupted earlier cut cannot schedule a future final release');
  assert.equal(waveHits(events).length,0);
  assert.ok(game.state.enemies.every(e=>e.hp===e.maxHp));
 }
 const {game,cast,events}=battle(5,alongTargets());events.push(...untilFinal(game,cast),...tick(game,.06));
 const origin={...cast.ultimateWaves!.origin};game.state.action=null;
 game.state.player.x=15;game.state.player.z=-7;game.state.player.angle=Math.PI;
 game.state.progression.learned.WAR_05=1;
 events.push(...tick(game,2));
 for(const id of ['along-mid','along-far']){
  const hits=waveHits(events).filter(e=>e.targetId===id);
  assert.deepEqual(hits.map(e=>e.waveIndex).sort((a,b)=>a-b),[0,1,2],'count and direction are captured at release');
  assert.ok(hits.every(e=>e.rank===5));
  for(const hit of hits)if(hit.waveOrigin)assert.deepEqual(hit.waveOrigin,origin);
 }
 assert.equal(game.state.combat.casts.some(c=>c.id===cast.id),false,'the completed payload must be cleaned up');
});

test('resetting combat clears released wave damage instead of allowing an orphan payload to hit later',()=>{
 const {game,cast}=battle(5,alongTargets());untilFinal(game,cast);tick(game,.06);
 game.resetCombatTransient();const hp=game.state.enemies.map(e=>e.hp);
 const events=tick(game,3);
 assert.equal(waveHits(events).length,0);assert.deepEqual(game.state.enemies.map(e=>e.hp),hp);assert.equal(game.state.combat.casts.length,0);
});

test('sixty-Hz frames and a large advance with internal substeps have the same swept contacts and damage',()=>{
 const fine=battle(5,alongTargets()),coarse=battle(5,alongTargets());
 fine.events.push(...tick(fine.game,3));coarse.events.push(...coarse.game.advance(3,idle));
 const contacts=(events:GameEvent[])=>waveHits(events).map(e=>[e.targetId,e.waveIndex,e.segment,e.value]).sort((a,b)=>String(a).localeCompare(String(b)));
 assert.equal(contacts(fine.events).length,6);
 assert.deepEqual(contacts(coarse.events),contacts(fine.events));
 assert.deepEqual(coarse.game.state.enemies.map(e=>e.hp),fine.game.state.enemies.map(e=>e.hp));
});
