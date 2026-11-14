import test from 'node:test';
import assert from 'node:assert/strict';
import {GameSession,validateSnapshot} from '../assets/scripts/core/GameSession';
import {awardXp,cumulativeXp,baseMaxHp,validateProgression} from '../assets/scripts/features/progression/common/Progression';
import {LEGACY_COMBAT_SKILLS,FOUR_SKILL_COMBAT_SKILLS} from '../assets/scripts/features/combat/data/PureSkills';
import {activateCombatLoadout} from '../assets/scripts/features/progression/common/CombatLoadouts';
import {SaveStore} from '../assets/scripts/features/persistence/common/SaveStore';
import {resetSkillPointPreviewStore,SKILL_POINT_RESET_MARKER,SKILL_POINT_SAVE_PREFIX} from '../assets/scripts/features/persistence/common/DevelopmentSaveReset';
import type {AreaDef,InputFrame,WorldQuery} from '../assets/scripts/core/Contracts';

const world:WorldQuery={move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0};
const area=(enemies:AreaDef['enemies']=[]):AreaDef=>({id:enemies.length?'S02':'S01',name:'营地',subtitle:'',kind:'wild',palette:'meadow',width:40,depth:40,spawn:{x:0,z:0},atlas:{x:0,z:0},exits:[],objects:[],buildings:[],obstacles:[],enemies,checkpoint:true});
function level(g:GameSession,n:number){awardXp(g.state.progression,'fixture:'+n,cumulativeXp(n)-g.state.progression.totalXp);g.state.player.maxHp=baseMaxHp(g.state.progression);g.state.player.hp=g.state.player.maxHp;activateCombatLoadout(g.state.combat,g.state.progression);}
function fresh(n=11){const g=new GameSession(1,world);g.enter(area());level(g,n);return g;}
function tick(g:GameSession,seconds:number,input:InputFrame={x:0,z:0}){const events=[];for(let i=0;i<Math.round(seconds/.02);i++)events.push(...g.advance(.02,input));return events;}
class Memory {data=new Map<string,string>();getItem(k:string){return this.data.get(k)??null;}setItem(k:string,v:string){this.data.set(k,v);}removeItem(k:string){this.data.delete(k);}keys(){return [...this.data.keys()];}}

test('second chapter opens every skill at rank one once, with twelve spendable points',()=>{
 const g=fresh(),p=g.state.progression;assert.equal(Object.keys(p.learned).length,33);assert.ok(Object.values(p.learned).every(r=>r===1));assert.equal(p.skillPoints,12);assert.deepEqual(g.state.combat.activeSlots,['WAR_01','WAR_02','WAR_03','WAR_04']);assert.equal(g.state.combat.ultimate,'WAR_05');
 awardXp(p,'fixture:11',cumulativeXp(11));assert.equal(p.skillPoints,12);validateProgression(p);
});
test('player investment survives later character levels and cross-family changes',()=>{
 const g=fresh(),p=g.state.progression,plan={...p.learned,WAR_01:5,WAR_03:2,BOW_06:2};assert.ok(g.applySkillPlan(plan));assert.equal(p.skillPoints,0);
 level(g,21);assert.equal(p.learned.WAR_01,5);assert.equal(p.learned.WAR_03,2);assert.equal(p.skillPoints,10);assert.ok(g.applyCombatLoadout('FIR'));assert.equal(p.learned.WAR_01,5);assert.equal(p.learned.FIR_01,1);validateProgression(p);
});
test('over-budget, locked, fractional and stale preview plans make no mutation',()=>{
 const g=fresh(4),p=g.state.progression,before=JSON.stringify(p);assert.equal(g.applySkillPlan({...p.learned,WAR_01:5}),false);assert.equal(g.applySkillPlan({...p.learned,WAR_02:2}),false);assert.equal(g.applySkillPlan({...p.learned,WAR_01:1.5}),false);assert.equal(JSON.stringify(p),before);
 const token=g.skillPlanToken();level(g,11);assert.equal(g.applySkillPlan({...p.learned,WAR_01:2},token),false);assert.equal(p.learned.WAR_01,1);
});
test('combat blocks allocation even at a checkpoint, and free refund never heals or spends gold',()=>{
 const g=fresh(),p=g.state.progression;assert.ok(g.applySkillPlan({...p.learned,WAR_03:5}));g.state.player.hp=50;g.state.player.gold=123;
 g.enter(area([{id:'danger',kind:'raider',x:0,z:6,hp:1000}]));assert.equal(g.applySkillPlan(Object.fromEntries(Object.entries(p.learned).map(([id,r])=>[id,r?1:0]))),false);
 g.enter(area());assert.ok(g.applySkillPlan(Object.fromEntries(Object.entries(p.learned).map(([id,r])=>[id,r?1:0]))));assert.equal(p.skillPoints,12);assert.equal(g.state.player.hp,50);assert.equal(g.state.player.gold,123);assert.ok(Object.values(p.learned).every(r=>r===1));
});
test('allocated ranks and exact point balance survive verified save and load; forged budget is rejected',()=>{
 const g=fresh(),p=g.state.progression;assert.ok(g.applySkillPlan({...p.learned,THU_02:5,THU_P2:2}));const m=new Memory(),store=new SaveStore(m);assert.ok(store.write(g).ok);const restored=new SaveStore(m).load(world).session!;assert.deepEqual(restored.state.progression,p);assert.equal(restored.state.progression.skillPoints,1);
 const bad=g.snapshot();bad.progression.skillPoints++;assert.throws(()=>validateSnapshot(bad));const old=g.snapshot();(old.progression as any).version=2;assert.throws(()=>validateSnapshot(old));
});
test('authorized development reset removes save slots, backups and charts once, preserving subsequent saves',()=>{
 const m=new Memory();for(const k of ['sword-fire.ch01.a','sword-fire.ch01.backup-1-a','sword-fire-chart:2','sword-fire-chart-index',SKILL_POINT_SAVE_PREFIX+'.a'])m.setItem(k,'old');m.setItem('sword-fire-ui-skill-names','1');m.setItem('unrelated','keep');assert.equal(resetSkillPointPreviewStore(m),5);assert.equal(m.getItem('unrelated'),'keep');assert.equal(m.getItem('sword-fire-ui-skill-names'),'1');assert.equal(m.getItem(SKILL_POINT_RESET_MARKER),'1');
 const store=new SaveStore(m),g=fresh();assert.ok(store.write(g).ok);const before=[...m.data];assert.equal(resetSkillPointPreviewStore(m),0);assert.deepEqual([...m.data],before);assert.ok(new SaveStore(m).load(world).session);
});
test('a failed development erase is retried instead of falsely marking the store clean',()=>{
 const m=new Memory();m.setItem('sword-fire.ch01.a','old');m.removeItem=()=>{};assert.throws(()=>resetSkillPointPreviewStore(m));assert.equal(m.getItem(SKILL_POINT_RESET_MARKER),null);
});
test('rank five is playable at level eleven and its finisher empowers exactly the next basic attack',()=>{
 const g=fresh(),p=g.state.progression;assert.ok(g.applySkillPlan({...p.learned,WAR_01:5}));g.enter(area([{id:'target',kind:'raider',x:0,z:1.2,hp:10000}]));g.state.enemies[0].phase='recovery';g.state.enemies[0].phaseTime=20;g.castSkill('WAR_01',{x:0,z:1.2},0);const hits=tick(g,1).filter(e=>e.type==='skill_hit');assert.equal(hits.length,3);assert.equal(g.state.combat.buffs.slashBasic,20);
 tick(g,.8,{x:0,z:0,attack:true});assert.equal(g.state.combat.buffs.slashBasic,0);assert.equal(p.skillPoints,2);
});
test('V2 and V3 saves restore the skill library once while preserving invested points and durable rewards',()=>{
 const old=fresh().snapshot();old.combat.version=2;
 delete (old.player as any).resourceVersion;delete (old.player as any).staminaPotions;delete (old.player as any).manaPotions;old.player.maxFocus=100;old.player.focus=100;
 old.progression.learned=Object.fromEntries(Object.keys(LEGACY_COMBAT_SKILLS).map(id=>[id,1]));Object.assign(old.progression.learned,{WAR_04:3,BOW_03:2,BOW_04:3,FIR_05:3,THU_04:2,COM_02:2});old.progression.skillPoints=0;
 const families=['WAR','BOW','FIR','THU'] as const;old.combat.loadouts=Object.fromEntries(families.map(family=>[family,{activeSlots:[1,2,3,4].map(n=>family+'_0'+n),ultimate:family+'_05'}])) as any;
 old.combat.activeSlots=['WAR_01','WAR_02','WAR_03','WAR_04'] as any;old.combat.ultimate='WAR_05';old.player.gold=123;old.player.hp=50;
 validateSnapshot(old);const original=JSON.stringify(old),g=GameSession.restore(old,world),next=g.snapshot();validateSnapshot(next);
 assert.equal(next.combat.version,4);assert.equal(next.combat.activeSlots.length,4);assert.equal(next.progression.learned.FIR_05,3);assert.equal(next.progression.learned.BOW_03,2);assert.equal(next.progression.skillPoints,0);
 assert.equal(next.progression.learned.WAR_04,3);assert.equal(next.progression.learned.COM_02,2);assert.deepEqual(next.combat.loadouts!.BOW!.activeSlots,['BOW_01','BOW_02','BOW_03','BOW_04']);assert.equal(next.combat.loadouts!.FIR!.ultimate,'FIR_05');assert.equal(next.player.gold,123);assert.equal(next.player.hp,50);assert.equal(JSON.stringify(old),original);
 const m=new Memory(),store=new SaveStore(m);assert.ok(store.write(g).ok);assert.deepEqual(new SaveStore(m).load(world).session!.state.progression,next.progression);
 const compact=fresh().snapshot();compact.combat.version=3;compact.progression.learned=Object.fromEntries(Object.keys(FOUR_SKILL_COMBAT_SKILLS).map(id=>[id,1]));compact.progression.learned.THU_03=4;compact.progression.learned.FIR_02=3;compact.progression.skillPoints=3;
 compact.combat.loadouts={WAR:{activeSlots:['WAR_01','WAR_02','WAR_03'],ultimate:'WAR_05'},BOW:{activeSlots:['BOW_07','BOW_06','BOW_01'],ultimate:'BOW_05'},FIR:{activeSlots:['FIR_01','FIR_04','FIR_03'],ultimate:'FIR_02'},THU:{activeSlots:['THU_01','THU_02','THU_03'],ultimate:'THU_05'}} as any;compact.combat.activeSlots=['WAR_01','WAR_02','WAR_03'] as any;compact.combat.cooldowns.THU_03=4;compact.player.focus=37;
 validateSnapshot(compact);const upgraded=GameSession.restore(compact,world),restored=upgraded.snapshot();validateSnapshot(restored);assert.equal(restored.combat.version,4);assert.equal(restored.progression.learned.THU_06,4);assert.equal(restored.progression.learned.THU_03,1);assert.equal(restored.progression.learned.FIR_02,3);assert.equal(restored.progression.learned.FIR_05,1);assert.equal(restored.progression.skillPoints,3);assert.equal(restored.player.focus,37);assert.equal(restored.combat.cooldowns.THU_06,4);
 assert.deepEqual(restored.combat.loadouts!.BOW!.activeSlots,['BOW_07','BOW_06','BOW_01','BOW_02']);assert.deepEqual(restored.combat.loadouts!.FIR!.activeSlots,['FIR_01','FIR_04','FIR_03','FIR_02']);assert.equal(restored.combat.loadouts!.FIR!.ultimate,'FIR_05');assert.deepEqual(GameSession.restore(restored,world).state.progression,restored.progression);
 const forged=structuredClone(old);forged.progression.skillPoints++;assert.throws(()=>GameSession.restore(forged,world));
});
