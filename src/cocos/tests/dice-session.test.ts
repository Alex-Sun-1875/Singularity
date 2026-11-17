import {economyReward} from '../assets/scripts/features/economy/common/EconomyRewards';
import test from 'node:test';import assert from 'node:assert/strict';
import {GameSession,validateSnapshot} from '../assets/scripts/core/GameSession';
import {getArea} from '../assets/scripts/features/world/data/WorldData';
import {drawCheckRoll,skillModifiers} from '../assets/scripts/features/progression/common/SkillChecks';
import {SaveStore} from '../assets/scripts/features/persistence/common/SaveStore';
import type {WorldQuery} from '../assets/scripts/core/Contracts';
const world:WorldQuery={move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0};
function game(seed=1){const g=new GameSession(seed,world);g.enter(getArea('S01-T1'),{x:-5,z:0});return g;}
function openMira(g:GameSession){g.interact(getArea('S01-T1').objects.find(o=>o.id==='t1-mira')!);g.choose('check:mira-motive');}
test('a real dialogue choice opens a pending D20 check and pauses the world',()=>{
 const g=game();openMira(g);assert.equal((g.state as any).dice?.active?.id,'mira-motive');const before=g.state.time;g.advance(1,{x:1,z:0});assert.equal(g.state.time,before);assert.equal(g.state.player.x,-5);
});
test('roll is one command, duplicates are ignored and opening again does not reroll',()=>{
 const g=game() as any;openMira(g);assert.equal(typeof g.rollCheck,'function');g.rollCheck();const first=JSON.stringify(g.state.dice.records);g.rollCheck();assert.equal(JSON.stringify(g.state.dice.records),first);g.cancelCheck();assert.ok(g.state.dice.active,'a rolled result cannot be cancelled');g.finishCheck();g.choose('check:mira-motive');assert.equal(JSON.stringify(g.state.dice.records),first.replace('"committed":false','"committed":true'));
});
test('failure rerolls spend inspiration atomically, success cannot reroll',()=>{
 let seed=1;while(drawCheckRoll(seed+1,'mira-motive',1,12,{mode:'normal',modifiers:skillModifiers('insight'),helpDie:false,helpLabel:null}).success)seed++;
 const g=game(seed) as any;openMira(g);assert.equal(typeof g.rollCheck,'function');g.rollCheck();assert.equal(g.diceView().roll.success,false);const p=g.state.dice.inspiration;g.rollCheck(true,1);assert.equal(g.state.dice.inspiration,p-1);assert.equal(g.state.dice.records['mira-motive'].rolls.length,2);g.rollCheck(true,1);assert.equal(g.state.dice.inspiration,p-1,'duplicate stale attempt cannot spend twice');if(g.diceView().roll.success){g.rollCheck(true,2);assert.equal(g.state.dice.inspiration,p-1);}
});
test('pending result and spent inspiration survive a save/restore without a free reroll',()=>{
 const g=game() as any;openMira(g);assert.equal(typeof g.rollCheck,'function');g.rollCheck();if(!g.diceView().roll.success)g.rollCheck(true,1);const snapshot=g.snapshot(),restored=GameSession.restore(snapshot,world) as any;restored.enter(getArea('S01-T1'),snapshot.player);assert.deepEqual(restored.state.dice,g.state.dice);const before=JSON.stringify(restored.state.dice);restored.rollCheck();assert.equal(JSON.stringify(restored.state.dice),before);validateSnapshot(restored.snapshot());
});
test('old formats and incomplete current saves are rejected without migration',()=>{
 const g=game();for(const version of [1,2]){const old:any=g.snapshot();old.version=version;assert.throws(()=>GameSession.restore(old,world));}
 for(const field of ['dice','enemyHazards']){const incomplete:any=g.snapshot();delete incomplete[field];assert.throws(()=>GameSession.restore(incomplete,world));}
 const incomplete:any=g.snapshot();delete incomplete.dice.gear;assert.throws(()=>GameSession.restore(incomplete,world));
});
test('a real locked chest grants reward once on success and repeated clicks cannot duplicate it',()=>{
 let seed=1;while(!drawCheckRoll(seed+1,'inn-lockbox',1,13,{mode:'normal',modifiers:skillModifiers('sleight'),helpDie:false,helpLabel:null}).success)seed++;
 const g=game(seed) as any,o=getArea('S01-T1').objects.find(o=>o.id==='t1-lockbox');assert.ok(o,'the check must exist as an actual inn interaction');g.enter(getArea('S01-T1'),o);g.interact(o);g.rollCheck();g.finishCheck();assert.equal(g.state.player.gold,economyReward('dice:inn-lockbox')!.gold);assert.equal(g.state.player.iron,2);g.interact(o);g.finishCheck();assert.equal(g.state.player.gold,economyReward('dice:inn-lockbox')!.gold);validateSnapshot(g.snapshot());
});
test('rest never replenishes inspiration and tampered natural results are rejected',()=>{
 const g=game() as any;openMira(g);assert.equal(typeof g.rollCheck,'function');g.rollCheck();const saved=g.snapshot();saved.dice.records['mira-motive'].rolls[0].kept=20;assert.throws(()=>validateSnapshot(saved));g.finishCheck();g.choose('leave');const before=g.state.dice.inspiration;g.rest();assert.equal(g.state.dice.inspiration,before);
});
test('two exhausted inspiration points cannot be replenished by rest or stale reroll input',()=>{
 let seed=1;while([1,2,3].some(attempt=>drawCheckRoll(seed+1,'mira-motive',attempt,12,{mode:'normal',modifiers:skillModifiers('insight'),helpDie:false,helpLabel:null}).success))seed++;
 const g=game(seed) as any;openMira(g);g.rollCheck();g.rollCheck(true,1);g.rollCheck(true,2);assert.equal(g.state.dice.inspiration,0);g.rollCheck(true,3);assert.equal(g.state.dice.records['mira-motive'].rolls.length,3);g.finishCheck();g.choose('reject');g.rest();assert.equal(g.state.dice.inspiration,0);validateSnapshot(g.snapshot());
});
test('available Lorn guidance is optional, locked after rolling and persists its actual d4',()=>{
 const g=game() as any,lorn=getArea('S01-T3').objects.find(o=>o.id==='t3-lorn')!;g.enter(getArea('S01-T3'),lorn);g.interact(lorn);const box=getArea('S01-T1').objects.find(o=>o.id==='t1-lockbox')!;g.enter(getArea('S01-T1'),box);g.interact(box);assert.equal(g.diceView().help.enabled,false);g.toggleCheckHelp();assert.equal(g.diceView().help.enabled,true);g.rollCheck();const roll=g.diceView().roll;assert.ok(roll.assist>=1&&roll.assist<=4);g.toggleCheckHelp();assert.equal(g.diceView().help.enabled,true);assert.equal(g.equip('W07'),false);assert.equal(g.rest(),false);validateSnapshot(g.snapshot());
});
test('accepted successful evidence gives inspiration once and cannot farm investigation rewards',()=>{
 let seed=1;while(!drawCheckRoll(seed+1,'grave-record',1,11,{mode:'normal',modifiers:skillModifiers('investigation'),helpDie:false,helpLabel:null}).success)seed++;
 const g=game(seed) as any,o=getArea('S03').objects.find(o=>o.id==='s03-dated-grave')!;g.enter(getArea('S03'),o);g.interact(o);g.rollCheck();g.finishCheck();assert.equal(g.state.dice.inspiration,3);assert.equal(g.state.flags.independent_clue,true);g.interact(o);g.finishCheck();assert.equal(g.state.dice.inspiration,3);assert.equal(g.state.dice.earned.length,1);validateSnapshot(g.snapshot());
});
test('dual-slot save store writes and restores unaccepted dice results atomically',()=>{
 const memory=new Map<string,string>(),kv={getItem:(k:string)=>memory.get(k)??null,setItem:(k:string,v:string)=>{memory.set(k,v);}},store=new SaveStore(kv),g=game() as any;openMira(g);g.rollCheck();if(!g.diceView().roll.success)g.rollCheck(true,1);assert.equal(store.write(g).ok,true);const restored=new SaveStore(kv).load(world).session!;assert.deepEqual(restored.state.dice,g.state.dice);assert.equal(restored.state.player.gold,g.state.player.gold);
});
test('malformed active sources, impossible balance and invented bonuses are rejected',()=>{
 const g=game() as any;openMira(g);g.rollCheck();const alter=(mutate:(s:any)=>void)=>{const s=g.snapshot();mutate(s);assert.throws(()=>validateSnapshot(s));};
 alter(s=>s.dice.active.area='S20');alter(s=>s.dice.inspiration=4);alter(s=>s.dice.records['mira-motive'].context.modifiers[0].value=20);alter(s=>s.dice.active.id='unbuilt-check');alter(s=>s.dice.records['mira-motive'].rolls[0].total=999);
});
test('a failed precision disarm costs focus but the authored side corridor still resolves rescue',()=>{
 let seed=1;while(drawCheckRoll(seed+1,'undercity-disarm',1,14,{mode:'normal',modifiers:skillModifiers('sleight'),helpDie:false,helpLabel:null}).success)seed++;
 const g=game(seed) as any,meeting=getArea('U1-04').objects.find(o=>o.action==='meeting')!;g.enter(getArea('U1-04'),meeting);g.interact(meeting);g.choose('cooperate');assert.equal(g.state.flags.meeting,true);
 const area=getArea('U1-05'),precision=area.objects.find(o=>o.id==='u105-precision-disarm')!;g.enter(area,precision);g.interact(precision);g.rollCheck();g.finishCheck();assert.equal(g.state.player.focus,80);assert.equal(g.state.flags.trap_disabled,undefined);
 const side=area.objects.find(o=>o.id==='u105-trap')!;g.enter(area,side);g.interact(side);assert.equal(g.state.flags.trap_disabled,true);const workers=area.objects.find(o=>o.action==='release_workers')!;g.enter(area,workers);g.interact(workers);assert.equal(g.state.flags.workers_released,true);validateSnapshot(g.snapshot());
});
