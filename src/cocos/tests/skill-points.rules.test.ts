import test from 'node:test';
import assert from 'node:assert/strict';
import {GameSession,validateSnapshot} from '../assets/scripts/core/GameSession';
import {awardXp,cumulativeXp,baseMaxHp,validateProgression} from '../assets/scripts/features/progression/common/Progression';
import {COMBAT_SKILLS,LEGACY_COMBAT_SKILLS,FOUR_SKILL_COMBAT_SKILLS} from '../assets/scripts/features/combat/data/PureSkills';
import {activateCombatLoadout,type CombatFamily} from '../assets/scripts/features/progression/common/CombatLoadouts';
import type {CombatCast} from '../assets/scripts/features/combat/common/PureCombat';
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
 assert.equal(next.combat.version,5);assert.equal(next.combat.activeSlots.length,4);assert.equal(next.progression.learned.FIR_05,3);assert.equal(next.progression.learned.BOW_03,2);assert.equal(next.progression.skillPoints,0);
 assert.equal(next.progression.learned.WAR_04,3);assert.equal(next.progression.learned.COM_02,2);assert.deepEqual(next.combat.loadouts!.BOW!.activeSlots,['BOW_01','BOW_02','BOW_07','BOW_06']);assert.equal(next.combat.loadouts!.FIR!.ultimate,'FIR_05');assert.equal(next.player.gold,123);assert.equal(next.player.hp,50);assert.equal(JSON.stringify(old),original);
 const m=new Memory(),store=new SaveStore(m);assert.ok(store.write(g).ok);assert.deepEqual(new SaveStore(m).load(world).session!.state.progression,next.progression);
 const compact=fresh().snapshot();compact.combat.version=3;compact.progression.learned=Object.fromEntries(Object.keys(FOUR_SKILL_COMBAT_SKILLS).map(id=>[id,1]));compact.progression.learned.THU_03=4;compact.progression.learned.FIR_02=3;compact.progression.skillPoints=3;
 compact.combat.loadouts={WAR:{activeSlots:['WAR_01','WAR_02','WAR_03'],ultimate:'WAR_05'},BOW:{activeSlots:['BOW_07','BOW_06','BOW_01'],ultimate:'BOW_05'},FIR:{activeSlots:['FIR_01','FIR_04','FIR_03'],ultimate:'FIR_02'},THU:{activeSlots:['THU_01','THU_02','THU_03'],ultimate:'THU_05'}} as any;compact.combat.activeSlots=['WAR_01','WAR_02','WAR_03'] as any;compact.combat.cooldowns.THU_03=4;compact.player.focus=37;
 validateSnapshot(compact);const upgraded=GameSession.restore(compact,world),restored=upgraded.snapshot();validateSnapshot(restored);assert.equal(restored.combat.version,5);assert.equal(restored.progression.learned.THU_06,4);assert.equal(restored.progression.learned.THU_03,1);assert.equal(restored.progression.learned.FIR_02,3);assert.equal(restored.progression.learned.FIR_05,1);assert.equal(restored.progression.skillPoints,3);assert.equal(restored.player.focus,37);assert.equal(restored.combat.cooldowns.THU_06,4);
 assert.deepEqual(restored.combat.loadouts!.BOW!.activeSlots,['BOW_01','BOW_02','BOW_07','BOW_06']);assert.deepEqual(restored.combat.loadouts!.FIR!.activeSlots,['FIR_01','FIR_02','FIR_03','FIR_04']);assert.equal(restored.combat.loadouts!.FIR!.ultimate,'FIR_05');assert.deepEqual(GameSession.restore(restored,world).state.progression,restored.progression);
 const forged=structuredClone(old);forged.progression.skillPoints++;assert.throws(()=>GameSession.restore(forged,world));
});
test('fixed profession slots and passives unlock in place and reject all replacement actions',()=>{
 const g=fresh(4);assert.deepEqual(g.state.combat.activeSlots,['WAR_01',null,'WAR_03',null]);assert.deepEqual(g.state.combat.passiveSlots,[null,null]);
 level(g,6);assert.deepEqual(g.state.combat.activeSlots,['WAR_01','WAR_02','WAR_03',null]);assert.deepEqual(g.state.combat.passiveSlots,['WAR_P1',null]);
 level(g,11);const before=JSON.stringify(g.state.combat);assert.equal(g.assignActiveSkill(0,'COM_02'),false);assert.equal(g.assignPassive(0,'BOW_P1'),false);assert.equal(g.assignUltimate(null),false);assert.equal(JSON.stringify(g.state.combat),before);
 assert.ok(g.applyCombatLoadout('BOW'));assert.deepEqual(g.state.combat.activeSlots,['BOW_01','BOW_02','BOW_07','BOW_06']);assert.deepEqual(g.state.combat.passiveSlots,['BOW_P1','BOW_P2']);assert.equal(g.state.combat.ultimate,'BOW_05');
 assert.ok(g.applyCombatLoadout('THU'));assert.deepEqual(g.state.combat.activeSlots,['THU_01','THU_02','THU_06','THU_04']);assert.deepEqual(g.state.combat.passiveSlots,['THU_P1','THU_P2']);assert.equal(g.state.combat.ultimate,'THU_05');
 validateSnapshot(g.snapshot());
});
test('V4 custom slots migrate to fixed roles once without changing investments, resources or cooldown debt',()=>{
 const g=fresh(21),p=g.state.progression;assert.ok(g.applySkillPlan({...p.learned,BOW_03:3,BOW_04:2,THU_03:4,COM_02:3}));
 const old=g.snapshot();old.combat.version=4;old.combat.loadouts!.WAR!.activeSlots=['COM_02','WAR_04','WAR_02','WAR_03'];old.combat.activeSlots=['COM_02','WAR_04','WAR_02','WAR_03'];old.combat.passiveSlots=['BOW_P1','THU_P2'];old.player.focus=37;old.player.hp=50;old.player.gold=123;old.combat.cooldowns={COM_02:7,WAR_04:2.25,BOW_03:4};
 delete old.receipts['skills:fixed-kit:v1'];validateSnapshot(old);const original=JSON.stringify(old),restored=GameSession.restore(old,world).snapshot();validateSnapshot(restored);
 assert.equal(restored.combat.version,5);assert.deepEqual(restored.progression,old.progression);assert.equal(restored.player.focus,37);assert.equal(restored.player.hp,50);assert.equal(restored.player.gold,123);assert.deepEqual(restored.combat.cooldowns,old.combat.cooldowns);assert.deepEqual(restored.combat.activeSlots,['WAR_01','WAR_02','WAR_03','WAR_04']);assert.deepEqual(restored.combat.passiveSlots,['WAR_P1','WAR_P2']);assert.equal(restored.receipts['skills:fixed-kit:v1'],true);assert.equal(JSON.stringify(old),original);
 const again=GameSession.restore(restored,world).snapshot();assert.deepEqual(again.progression,restored.progression);assert.deepEqual(again.combat.cooldowns,restored.combat.cooldowns);assert.deepEqual(again.receipts,restored.receipts);
 for(const corrupt of [(s:typeof restored)=>{s.combat.activeSlots[0]='COM_02';},(s:typeof restored)=>{s.combat.activeSlots[0]=null;},(s:typeof restored)=>{s.combat.passiveSlots[0]='BOW_P1';},(s:typeof restored)=>{s.combat.loadouts!.BOW!.activeSlots[0]='BOW_03';}]){const forged=structuredClone(restored);corrupt(forged);assert.throws(()=>GameSession.restore(forged,world));}
});

function skillBattle(family:CombatFamily,plan:Record<string,number>={},count=1){
 const g=fresh(40);assert.ok(g.applyCombatLoadout(family));assert.ok(g.applySkillPlan({...g.state.progression.learned,...plan}));
 g.enter(area(Array.from({length:count},(_,i)=>({id:'target'+i,kind:'raider' as const,x:i===0?0:(i%2?-.25:.25),z:1.2+i*.08,hp:100000,trainingDummy:true}))));return g;
}
function completedSkill(g:GameSession,id:string,seconds=4.2){
 const events=g.castSkill(id,{x:0,z:1.2},0);let releasedCooldown:number|undefined=events.some(e=>e.type==='skill_release'&&e.skillId===id)?g.state.combat.cooldowns[id]:undefined;
 for(let i=0;i<Math.round(seconds/.02);i++){const next=tick(g,.02);events.push(...next);if(releasedCooldown===undefined&&next.some(e=>e.type==='skill_release'&&e.skillId===id))releasedCooldown=g.state.combat.cooldowns[id];}
 assert.ok(releasedCooldown!==undefined,id+' must actually release');return {events,cooldown:releasedCooldown,damage:g.state.enemies.reduce((sum,e)=>sum+e.maxHp-e.hp,0)};
}
test('fixed single-target skills retain one victim through dense groups, deaths and empty fire impacts',()=>{
 for(const family of ['WAR','BOW','FIR','THU'] as const)for(const rank of [1,5]){
  const id=family+'_01',g=skillBattle(family,{[id]:rank},3),result=completedSkill(g,id);
  assert.equal(g.state.enemies.filter(e=>e.hp<e.maxHp).length,1,`${id} rank ${rank} must damage only one clustered enemy`);
  assert.equal(new Set(result.events.filter(e=>e.type==='skill_hit'&&e.skillId===id).map(e=>e.targetId)).size,1);
 }
 const melee=skillBattle('WAR',{WAR_01:5},2);melee.state.enemies[0].trainingDummy=false;melee.state.enemies[0].hp=1;
 const cuts=completedSkill(melee,'WAR_01');assert.equal(melee.state.enemies[0].hp,0);assert.equal(melee.state.enemies[1].hp,melee.state.enemies[1].maxHp);assert.equal(cuts.events.filter(e=>e.type==='skill_hit'&&e.skillId==='WAR_01').length,1);
 let wall=false;const blocked:WorldQuery={...world,visible:(a,b)=>!wall||(a.z<1.2)===(b.z<1.2)},fire=new GameSession(1,blocked);fire.enter(area());level(fire,40);assert.ok(fire.applyCombatLoadout('FIR'));assert.ok(fire.applySkillPlan({...fire.state.progression.learned,FIR_01:5}));
 fire.enter(area([{id:'beside-wall',kind:'raider',x:.75,z:.9,hp:100000,trainingDummy:true}]));fire.castSkill('FIR_01',{x:0,z:6},0);
 for(let i=0;i<30&&!fire.state.projectiles.length;i++)tick(fire,.02);assert.ok(fire.state.projectiles.length);wall=true;
 const impact=tick(fire,1);assert.ok(impact.some(e=>e.type==='skill_segment'&&e.skillId==='FIR_01'&&e.phase==='impact'));assert.equal(fire.state.enemies[0].hp,fire.state.enemies[0].maxHp,'a fireball blocked beside an enemy must not deal splash damage');
});
test('real full casts keep single damage above ultimate above ordinary area, and ultimate cooldown longest',()=>{
 const ordinary={WAR:'WAR_04',BOW:'BOW_02',FIR:'FIR_02',THU:'THU_04'} as const;
 for(const family of ['WAR','BOW','FIR','THU'] as const)for(const rank of [1,5]){
  const ids=[family+'_01',family+'_05',ordinary[family]],results=ids.map(id=>completedSkill(skillBattle(family,{[id]:rank}),id));
  assert.ok(results[0].damage>results[1].damage&&results[1].damage>results[2].damage,`${family} rank ${rank}: ${results.map(r=>r.damage).join(' > ')}`);
  const group=completedSkill(skillBattle(family,{[ids[1]]:rank},3),ids[1]);assert.ok(group.damage>results[1].damage*1.8,`${family} rank ${rank} ultimate group damage ${group.damage} must exceed single-victim damage ${results[1].damage} through actual extra targets`);
  const reduced=ids.slice(1).map(id=>{const g=fresh(40);assert.ok(g.applyCombatLoadout(family));assert.ok(g.applySkillPlan({...g.state.progression.learned,[id]:rank}));g.state.inventory.J04=1;g.state.provenance.J04='fixture';assert.ok(g.equip('J04'));g.enter(area([{id:'target',kind:'raider',x:0,z:1.2,hp:100000,trainingDummy:true}]));return completedSkill(g,id);});
  assert.ok(reduced[0].cooldown>reduced[1].cooldown&&reduced[0].cooldown>results[0].cooldown);assert.ok(Math.abs(reduced[0].cooldown-11.4)<1e-6);
  const dodge=completedSkill(skillBattle(family),'COM_01',.5);assert.equal(dodge.cooldown,2);
 }
});
test('automatic enhancements use real contact, one volley budget, three thunder hits and shared healing input',()=>{
 for(const rank of [1,5]){
  const bow=skillBattle('BOW',{BOW_03:rank,BOW_04:rank});bow.state.enemies[0].z=4;tick(bow,.5);bow.castSkill('BOW_01',{x:0,z:4},0);tick(bow,.6);
  assert.ok(bow.state.combat.buffs.bowVolleyReadyUntil>bow.state.time);const markedUntil=bow.state.combat.statuses.target0.hunterMarkUntil;assert.ok(markedUntil-bow.state.time>(rank===5?9:7));
  let volley:CombatCast|undefined;const events=tick(bow,.1,{x:0,z:0,attack:true,aim:0});
  for(let i=0;i<70;i++){events.push(...tick(bow,.02,{x:0,z:0,aim:0}));volley??=bow.state.combat.casts.find(c=>c.skillId==='BOW_03');}
  const hits=events.filter(e=>e.type==='skill_hit'&&e.skillId==='BOW_03'),arrows=COMBAT_SKILLS.BOW_03.ranks[rank-1].authoredDamageHits;assert.equal(hits.length,arrows);assert.ok(volley);
  const expected=volley.power*volley.rank.maxDamagePerTargetS*volley.attributeMultiplier*(1+COMBAT_SKILLS.BOW_04.ranks[rank-1].markedDirectSkillBonusPercent!/100)*(volley.critical?volley.criticalMultiplier!:1),actual=hits.reduce((sum,e)=>sum+Number(e.value),0);
  assert.ok(Math.abs(actual-expected)<=arrows,`rank ${rank} volley deals its whole budget once: ${actual} vs ${expected}`);assert.equal(bow.state.combat.buffs.bowVolleyReadyUntil,0);assert.ok(bow.state.combat.cooldowns.BOW_03>0);
  tick(bow,1.2);bow.castSkill('BOW_01',{x:0,z:4},0);tick(bow,.5);assert.equal(bow.state.combat.buffs.bowVolleyReadyUntil,0,'a second primary hit during trigger cooldown cannot prepare another volley');assert.equal(bow.state.combat.statuses.target0.hunterMarkUntil,markedUntil);
  const loaded=GameSession.restore(bow.snapshot(),world),resumed=[...tick(loaded,.1,{x:0,z:0,attack:true,aim:0}),...tick(loaded,1,{x:0,z:0,aim:0})];assert.equal(resumed.filter(e=>e.type==='skill_hit'&&e.skillId==='BOW_03').length,0,'save/load must not repeat an already consumed volley');
 }
 for(const hit of [false,true]){
  const thunder=skillBattle('THU',{THU_03:5});thunder.state.enemies[0].z=8;tick(thunder,1.6,{x:0,z:1});thunder.castSkill('THU_01',{x:0,z:hit?8:0},hit?0:Math.PI);tick(thunder,.5);
  assert.equal(thunder.state.combat.buffs.thunderCharges??0,hit?3:0);assert.equal((thunder.state.combat.cooldowns.THU_03??0)>0,hit);
  const basics=tick(thunder,3.6,{x:0,z:0,attack:true,aim:0});assert.equal(basics.filter(e=>e.type==='skill_hit'&&e.skillId==='THU_03').length,hit?3:0);assert.equal(thunder.state.combat.buffs.thunderCharges??0,0);
 }
 const heal=skillBattle('WAR');heal.state.enemies=[];heal.state.player.hp-=80;const before=heal.state.player.hp,events=tick(heal,10,{x:0,z:0,healSkill:true});assert.ok(heal.state.player.hp>before);assert.equal(events.filter(e=>e.type==='skill_release'&&e.skillId==='COM_02').length,1,'holding the supply healing input does not repeatedly cast');assert.equal(events.filter(e=>e.type==='skill_status'&&e.skillId==='COM_02'&&e.status==='heal'&&Number(e.segment)>0).length,3);
});
