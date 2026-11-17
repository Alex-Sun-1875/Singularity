import test from 'node:test';
import assert from 'node:assert/strict';
import { GameSession } from '../assets/scripts/core/GameSession';
import {activateCombatLoadout} from '../assets/scripts/features/progression/common/CombatLoadouts';
import {EQUIPMENT} from '../assets/scripts/features/equipment/data/Equipment';
import {awardXp,cumulativeXp,baseMaxHp} from '../assets/scripts/features/progression/common/Progression';
import {AREAS} from '../assets/scripts/features/world/data/WorldData';
import {CAMPAIGN_BATTLES,campaignFighter} from '../assets/scripts/features/campaign/data/CampaignBattles';
import {enemyContentHealth,enemyDamageMultiplier} from '../assets/scripts/features/combat/data/EnemyBalance';
import {CAMPAIGN_PHASES} from '../assets/scripts/features/progression/data/CampaignProgression';
import {EquipmentForging,validateForging,forgingSignature,itemForgingView,forgingStage} from '../assets/scripts/features/crafting/common/EquipmentForging';
import {forgingThreshold,forgingCost,forgingRankWeight,FORGING_EQUIVALENT_RANKS,FORGING_RANK_LEVELS,forgingLevelCap,forgingNextUnlock} from '../assets/scripts/features/crafting/data/EquipmentForging';
import {CultivationRewards,cultivationGemBank,MATERIAL_TIER_LEVELS,materialTierForLevel,materialNextUnlock} from '../assets/scripts/features/crafting/common/CultivationRewards';
import {GemWorkshop,itemGemView,validateGems,gemSignature} from '../assets/scripts/features/gems/common/GemWorkshop';
import {GEM_TIER_LEVELS,GEM_SOCKET_LEVELS,gemTierForLevel,gemSocketCapForLevel,gemNextUnlock,gemTierCap,type GemStat} from '../assets/scripts/features/gems/data/Gems';
import {CAMPAIGN_EQUIPMENT_GROWTH,equipmentSourceAllocation,type EquipmentRewardKind} from '../assets/scripts/features/equipment/data/CampaignEquipmentGrowth';
import {combatRandomRoll} from '../assets/scripts/features/combat/common/PureCombat';
import {Automation,type AutomationStep} from '../assets/scripts/features/automation/common/Automation';
import type { AreaDef, WorldQuery, InteractionDef,InputFrame } from '../assets/scripts/core/Contracts';

function level(g:GameSession,n:number){if(n>1)awardXp(g.state.progression,'fixture',cumulativeXp(n));g.state.player.maxHp=baseMaxHp(g.state.progression);g.state.player.hp=g.state.player.maxHp;g.state.progression.ultimateGiftClaimed=n>=11;activateCombatLoadout(g.state.combat,g.state.progression);}
const world: WorldQuery = {move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0};
const area = (id='S01', enemies:AreaDef['enemies']=[]):AreaDef => ({id,name:id,subtitle:'',kind:'wild',palette:'meadow',width:40,depth:40,spawn:{x:0,z:0},atlas:{x:0,z:0},exits:[],objects:[],buildings:[],obstacles:[],enemies,checkpoint:true});
function at(g:GameSession, action:string, extra:Partial<InteractionDef>={}) { const object={id:action,label:action,action,description:'',x:g.state.player.x,z:g.state.player.z,...extra}; g.interact(object); }
function tick(g:GameSession,t:number,input:InputFrame={x:0,z:0}) { for(let i=0;i<Math.ceil(t/.02);i++)g.advance(.02,input); }

test('campaign forging consumes tier materials, inherits paid ranks without merging and replays exact costs',()=>{
 // Ownership/material arithmetic fixtures never unlock a future chapter.
  const g=new GameSession(73014,world);level(g,80);const s=g.state;
  for(const id of ['DG_L02','LC1_T_E_BOW','LC2_T_L_BOW'])s.inventory[id]=1;
  Object.assign(s.player,{gold:9999,iron:9999,runes:0,cores:0});
  // Arithmetic fixture for a previously harvested ordinary slot. Real death,
  // respawn, duplicate rejection and persistence are exercised by cultivation-rewards.ts.
  g.enter(AREAS.S08);const slot=s.enemies.find(e=>e.respawnSeconds&&!e.bossId)!;
  const slotKey=`S08:${slot.id}`,harvestKey=`${slotKey}:1:ordinary`,cultivation=s.forging.cultivation!;
  cultivation.harvests[harvestKey]={area:'S08',enemy:slot.id,tier:1,kind:'ordinary',count:1500,cycle:1500};
  slot.respawnCount=1500;s.receipts[`hunt-cycle:${slotKey}`]=1500;s.receipts[`supply-cycle:${slotKey}`]=1500;s.receipts[`cultivation:life:${slotKey}`]=1500;
  const bank=cultivationGemBank(s);cultivation.gemBatches.push({after:0,bank});s.gems.bank={...bank};s.gems.revision=1500;
  const materials=new CultivationRewards({state:()=>s,availability:()=>({available:true,reason:''}),id:prefix=>prefix+':'+(++s.sequence),changed:()=>{},emit:()=>{}});
  for(const [tier,count]of [[1,39],[2,12],[3,3]])for(let i=0;i<count;i++){const q=materials.synthesis(tier);assert.ok(q.allowed,q.reason);assert.ok(materials.synthesize(tier,q.token));}
  const forge=new EquipmentForging({state:()=>s,availability:()=>({available:true,reason:''}),id:prefix=>prefix+':'+(++s.sequence),changed:()=>{},recalculate:()=>{},emit:()=>{}});
  const enhance=(id:string)=>{const q=forge.enhancement(id);assert.ok(q.allowed,q.reason);assert.ok(forge.enhance(id,q.token));};
  enhance('DG_L02');
  const history=structuredClone(s.forging.rolls!.DG_L02),oldExperience=s.forging.experience.DG_L02;
  let q=forge.transfer('DG_L02','LC1_T_E_BOW');assert.ok(q.allowed);assert.equal(q.after,1);assert.equal(q.creditedExperience,forgingThreshold(EQUIPMENT.LC1_T_E_BOW,1));assert.notEqual(q.creditedExperience,oldExperience);
  assert.ok(forge.inherit(q.from,q.to,q.token));assert.equal(s.forging.experience.DG_L02,undefined);assert.deepEqual(s.forging.rolls!.DG_L02,history);assert.equal(itemForgingView(s,q.to)!.rank,1);
  enhance('W07');assert.match(forge.transfer('W07','LC1_T_E_BOW').reason,/已有强化/);
  q=forge.transfer('LC1_T_E_BOW','DG_L02');assert.ok(q.allowed);assert.ok(forge.inherit(q.from,q.to,q.token));assert.deepEqual(s.forging.rolls!.DG_L02,history);assert.equal(s.forging.experience.DG_L02,oldExperience);
  enhance('DG_L02');
  const before=JSON.stringify(s.forging);assert.match(forge.enhancement('DG_L02').reason,/符纹不足/);assert.equal(forge.enhance('DG_L02',forge.enhancement('DG_L02').token),false);assert.equal(JSON.stringify(s.forging),before);
  s.player.runes=4;for(let rank=3;rank<=4;rank++)enhance('DG_L02');assert.equal(s.player.runes,0);assert.match(forge.enhancement('DG_L02').reason,/锻造芯不足/);
  s.player.cores=2;enhance('DG_L02');enhance('DG_L02');assert.equal(s.player.cores,0);assert.match(forge.transfer('DG_L02','LC1_T_E_BOW').reason,/上限低于/);
  q=forge.transfer('DG_L02','LC2_T_L_BOW');assert.ok(q.allowed);assert.ok(forge.inherit(q.from,q.to,q.token));assert.equal(itemForgingView(s,q.to)!.rank,6);validateForging(s);
  const cost=s.forging.transactions.find(t=>t.kind==='enhance'&&t.rank===3)!;assert.equal(cost.kind,'enhance');if(cost.kind==='enhance'){cost.runes=0;s.receipts[cost.request]=forgingSignature(cost);assert.throws(()=>validateForging(s));cost.runes=2;s.receipts[cost.request]=forgingSignature(cost);}
  const transfer=s.forging.transactions[s.forging.transactions.length-1];assert.equal(transfer.kind,'transfer');if(transfer.kind==='transfer'){transfer.creditedExperience++;s.receipts[transfer.request]=forgingSignature(transfer);assert.throws(()=>validateForging(s));transfer.creditedExperience--;s.receipts[transfer.request]=forgingSignature(transfer);}validateForging(s);
 const weights=Array.from({length:113},(_,i)=>i+1),total=weights.reduce((a,b)=>a+b,0);
 for(const plan of CAMPAIGN_EQUIPMENT_GROWTH)for(const kind of ['story','exploration','firstBoss'] as EquipmentRewardKind[]){let before=0;const sum={gold:0,iron:0,runes:0,cores:0};for(const weight of weights){const part=equipmentSourceAllocation(plan.chapter,kind,before,weight,total);for(const key of Object.keys(sum) as (keyof typeof sum)[])sum[key]+=part[key];before+=weight;}assert.deepEqual(sum,plan.sources[kind]);}
});

test('cultivation opens by character level, retains early gems and replays separate socket and gem gates',()=>{
 for(let value=1;value<=80;value++){
  assert.equal(forgingLevelCap(value),FORGING_RANK_LEVELS.filter(level=>level<=value).length);
  assert.equal(gemTierForLevel(value),GEM_TIER_LEVELS.slice(1).filter(level=>level<=value).length);
  assert.equal(gemSocketCapForLevel(value),GEM_SOCKET_LEVELS.filter(level=>level<=value).length);
  assert.equal(materialTierForLevel(value),MATERIAL_TIER_LEVELS.filter(level=>level<=value).length);
 }
 assert.deepEqual(forgingNextUnlock(1),{rank:1,level:10});assert.deepEqual(forgingNextUnlock(47),{rank:5,level:50});assert.equal(forgingNextUnlock(80),undefined);
 assert.equal(FORGING_EQUIVALENT_RANKS[7],15);assert.equal(FORGING_RANK_LEVELS.reduce((sum,_,i)=>sum+forgingRankWeight(i+1),0),15);
 assert.equal(forgingThreshold(EQUIPMENT.DG_A01,8),15586);assert.deepEqual(forgingCost(EQUIPMENT.DG_A01,8),{gold:7350,iron:48,runes:0,cores:5});assert.ok(Object.values(EQUIPMENT).every(item=>item.maxEnhance!<=8));
 assert.deepEqual(gemNextUnlock(1),{tier:2,level:16});assert.deepEqual(materialNextUnlock(24),{tier:3,level:40});
 const g=new GameSession(73102,world),s=g.state;
 assert.equal(forgingStage(s),0);assert.equal(itemGemView(s,'DG_A01')!.opened,0);assert.equal(itemGemView(s,'DG_A01')!.capacity,5);
 s.progression.secondChapter=true;assert.equal(forgingStage(s),0);assert.equal(gemTierCap(s),1);s.progression.secondChapter=false;
 g.enter(AREAS.S02);assert.ok(g.journey.complete('border-traces'));s.inventory.DG_A01=1;s.provenance.DG_A01='fixture:socket-quality';s.player.gold=9999;
 const host={state:()=>s,availability:()=>({available:true,reason:''}),shopAvailability:()=>({available:true,reason:''}),id:(prefix:string)=>prefix+':'+(++s.sequence),changed:()=>{},recalculate:()=>{},emit:()=>{}};
 const workshop=new GemWorkshop(host),materials=new CultivationRewards(host),stat='power' as GemStat;assert.deepEqual(s.gems.bank,{});s.discoveredMerchants.push('jeweler');
 const raise=(value:number)=>{const delta=cumulativeXp(value)-s.progression.totalXp;if(delta>0)awardXp(s.progression,'fixture:gate:'+value,delta);};
 assert.ok(s.progression.level<6);const bank=JSON.stringify(s.gems.bank);assert.equal(workshop.inset('DG_A01',0,stat,1).reasonKey,'reason.socketLocked');assert.equal(JSON.stringify(s.gems.bank),bank);
 raise(6);assert.ok(workshop.purchase('jeweler','GEM_power_1',3));assert.equal(itemGemView(s,'DG_A01')!.opened,1);assert.equal(itemGemView(s,'DG_A01')!.socketCap,1);
 s.gems.items.DG_A01={opened:0,sockets:[null,null,null,null,null]};assert.equal(itemGemView(s,'DG_A01')!.opened,1);assert.ok(workshop.inset('DG_A01',0,stat,1).allowed);delete s.gems.items.DG_A01;
 let q=workshop.inset('DG_A01',0,stat,1);assert.ok(q.allowed,q.reason);assert.ok(workshop.inlay('DG_A01',0,stat,1,q.token));
 assert.equal(workshop.open('DG_A01',1).reasonKey,'reason.socketLocked');assert.match(materials.synthesis(1).reason,/Lv20/);
 const extract=workshop.remove('DG_A01',0);assert.ok(extract.allowed);assert.ok(workshop.extract('DG_A01',0,extract.token));
 const exchange=workshop.exchange(stat);assert.equal(exchange.allowed,false);assert.equal(exchange.reasonKey,'reason.shopOnly');
 raise(15);assert.equal(workshop.synthesis(stat,1).reasonKey,'reason.maxTier');raise(16);g.enter(AREAS.H01);
 const compose=workshop.synthesis(stat,1);assert.ok(compose.allowed,compose.reason);assert.ok(workshop.synthesize(stat,1,compose.token));q=workshop.inset('DG_A01',0,stat,2);assert.ok(q.allowed,q.reason);assert.ok(workshop.inlay('DG_A01',0,stat,2,q.token));
 assert.notEqual(workshop.open('DG_A01',1).reasonKey,'reason.socketLocked');assert.equal(workshop.open('DG_A01',2).reasonKey,'reason.socketLocked');validateGems(s);
 const transaction=s.gems.transactions.find(t=>t.kind==='inlay'&&t.tier===2)!;transaction.level=15;s.receipts[transaction.request]=gemSignature(transaction);assert.throws(()=>validateGems(s));transaction.level=16;s.receipts[transaction.request]=gemSignature(transaction);validateGems(s);
 raise(20);const stone=materials.synthesis(1);assert.ok(stone.allowed,stone.reason);assert.ok(materials.synthesize(1,stone.token));validateForging(s);
 raise(48);assert.equal(gemTierCap(s),4);assert.equal(itemGemView(s,'DG_A01')!.socketCap,3);assert.equal(workshop.open('DG_A01',3).reasonKey,'reason.socketLocked');
 raise(50);assert.notEqual(workshop.open('DG_A01',3).reasonKey,'reason.socketLocked');
});

test('combat critical rolls are stable, distributed across action IDs and shared by one cast',()=>{
 const thresholds=[.05,.20,.30],totals=[0,0,0];
 const seeds=[1,42,73014,12345,104729,8675309,16777213,268435399,536870909,1073741789,1610612741,2147483646];
 for(const seed of seeds){
  const counts=[0,0,0];
  for(let i=1;i<=10000;i++){
   const id=i%3===0?`${i}:crit`:i%3===1?`action:${i}:crit`:`autoVolley:${i}:crit`,roll=combatRandomRoll(seed,id);
   assert.ok(roll>=0&&roll<1);assert.equal(combatRandomRoll(seed,id),roll);
   thresholds.forEach((chance,j)=>{if(roll<chance)counts[j]++;});
  }
  thresholds.forEach((chance,j)=>{assert.ok(Math.abs(counts[j]/10000-chance)<.018,`seed ${seed}, chance ${chance}: ${counts[j]}/10000`);totals[j]+=counts[j];});
 }
 thresholds.forEach((chance,j)=>assert.ok(Math.abs(totals[j]/120000-chance)<.004,`pooled chance ${chance}: ${totals[j]}/120000`));
 for(const seed of [1,73014,2147483646]){
  const g=new GameSession(seed,world);g.enter(area('S02',[{id:'target',kind:'raider',x:0,z:1,hp:100000,trainingDummy:true}]));
  g.castSkill('WAR_01',{x:0,z:1},0);const cast=g.state.combat.casts[0];assert.ok(cast);
  assert.equal(cast.criticalRoll,combatRandomRoll(g.state.seed,`${cast.id.slice(cast.id.lastIndexOf(':')+1)}:crit`));assert.equal(cast.critical,cast.criticalRoll!<cast.criticalChance!);
  const events=[];for(let i=0;i<50;i++)events.push(...g.advance(.02,{x:0,z:0}));
  const hits=events.filter(e=>e.type==='skill_hit'&&e.castId===cast.id);assert.equal(hits.length,2);assert.ok(hits.every(e=>e.critical===cast.critical));
  g.resetCombatTransient();g.advance(.02,{x:0,z:0,attack:true});const action=g.state.action;assert.ok(action);
  const expected=combatRandomRoll(g.state.seed,`${action.id}:crit`)<.05,basic=[];
  for(let i=0;i<20;i++)basic.push(...g.advance(.02,{x:0,z:0}));
  const contact=basic.find(e=>e.type==='hit'&&e.action===action.id);assert.ok(contact);assert.equal(contact.critical,expected);
 }
});

test('automatic combat saves protection for danger and chooses effective group or single-target damage',()=>{
 const query:WorldQuery={...world,path:(a,b)=>[{x:a.x,z:a.z},{x:b.x,z:b.z}]};
 const fresh=(family:'WAR'|'BOW'='WAR')=>{const g=new GameSession(1,query);g.enter(area());level(g,11);g.applyCombatLoadout(family);return g;};
 const decide=(g:GameSession)=>{const pilot=new Automation() as unknown as {fight(g:GameSession,w:WorldQuery,dt:number,scope:'clear'):AutomationStep|null};const decision=pilot.fight(g,query,.04,'clear');assert.ok(decision);return decision.input;};
 const quiet=fresh();quiet.enter(area('S02',[{id:'target',kind:'raider',x:0,z:1.4,hp:10000,trainingDummy:true}]));
 assert.equal(decide(quiet).combatSlot,0,'full-health approach must use the main skill, not refresh a shield');
 const hurt=fresh();hurt.enter(area('S02',[{id:'target',kind:'raider',x:0,z:1.4,hp:10000,trainingDummy:true}]));hurt.state.player.hp=hurt.state.player.maxHp*.7;
 assert.equal(decide(hurt).combatSlot,2,'hurt characters retain their protection skill');
 const danger=fresh();danger.enter(area('S02',[{id:'target',kind:'raider',x:0,z:1.4,hp:10000}]));Object.assign(danger.state.enemies[0],{phase:'windup',phaseTime:.2,targetAngle:Math.PI});danger.state.combat.cooldowns.COM_01=2;
 assert.equal(decide(danger).combatSlot,2,'an imminent facing attack with dodge unavailable can trigger protection at full health');
 const group=fresh();group.enter(area('S02',[-.25,0,.25].map((x,i)=>({id:'group'+i,kind:'raider',x,z:1.4,hp:10000,trainingDummy:true}))));
 const groupInput=decide(group);assert.ok(groupInput.ultimate||groupInput.combatSlot===3,'real nearby coverage should prefer group damage');
 const boss=fresh('BOW');boss.enter(area('S02',[{id:'boss',kind:'captain',bossId:'BOSS_R1',x:0,z:3,hp:100000}]));Object.assign(boss.state.combat.cooldowns,{BOW_01:10,BOW_02:10,BOW_05:10});
 const bossInput=decide(boss);assert.equal(bossInput.combatSlot,undefined,'a single idle boss does not justify low-damage traps or retreat shots');assert.equal(bossInput.attack,true);
 const chain=fresh();chain.enter(area('S02',[{id:'target',kind:'raider',x:0,z:1.4,hp:10000,trainingDummy:true}]));chain.advance(.02,{x:0,z:0,attack:true});
 const action=chain.state.action!;action.elapsed=action.duration-.01;
 assert.equal(decide(chain).attack,false,'a completed sword cut must leave a decision gap for a ready skill');assert.equal(chain.state.action,action,'the controller does not cancel the current action');
 chain.advance(.02,{x:0,z:0,attack:false});assert.equal(chain.state.action,null);assert.equal(decide(chain).combatSlot,0);
 const sidestep=fresh();sidestep.enter(area('S02',[{id:'target',kind:'raider',x:0,z:1.4,hp:10000,trainingDummy:true}]));sidestep.state.fireZones=[{id:'danger',x:0,z:0,radius:.3,remaining:1,tick:0}];
 const partial:WorldQuery={...query,visible:(_a,b)=>b.x<=.01};
 const evader=new Automation() as unknown as {evade(g:GameSession,w:WorldQuery):AutomationStep|null;evadeGoal:{x:number;z:number}|null};
 const escape=evader.evade(sidestep,partial);assert.ok(escape);const goal=evader.evadeGoal;assert.ok(goal);
 assert.ok(Math.abs(Math.hypot(goal.x,goal.z)-1.6)<1e-8,'a safe nearby step is preferred to the distant ring');assert.ok(partial.visible(sidestep.state.player,goal),'an invisible escape is never selected');
 assert.ok(Math.abs(Math.hypot(goal.x,goal.z-1.4)-1.55)<.2,'the safe step should preserve melee contact distance');assert.equal(escape.input.dash,false,'a nearby step cannot truncate the real 2.8m dodge');
 Object.assign(sidestep.state.player,goal);assert.equal(evader.evade(sidestep,partial),null);assert.equal(evader.evadeGoal,null,'arriving safely does not wait out the fixed evade window');
});

test('safe inventory preparation ends a frozen sword action without changing buffs, shield or time',()=>{
 const g=new GameSession(1,world);g.enter(area());g.advance(.02,{x:0,z:0,attack:true});
 assert.equal(g.state.action?.kind,'sword');assert.equal(g.equipmentAvailability().available,false);
 g.state.player.shield=12;g.state.combat.buffs.fixtureBuffUntil=4;g.state.combat.charge=0;g.state.player.focus=37;const time=g.state.time;
 assert.equal(g.prepareEquipmentChange(),true);assert.equal(g.state.action,null);assert.equal(g.state.time,time);
 assert.equal(g.state.player.shield,12);assert.equal(g.state.combat.buffs.fixtureBuffUntil,4);assert.equal(g.state.combat.charge,0);assert.equal(g.state.player.focus,37);
 assert.equal(g.equip('W07'),true);assert.equal(g.state.equipment.weapon,'W07');
});
test('safe inventory preparation drops harmless player shots but preserves enemy projectiles',()=>{
 const fresh=()=>{const g=new GameSession(1,world);g.enter(area());g.equip('W11');g.advance(.02,{x:0,z:0,attack:true});tick(g,.25);assert(g.state.projectiles.length);return g;};
 const g=fresh();assert.equal(g.prepareEquipmentChange(),true);assert.equal(g.state.projectiles.length,0);assert.equal(g.equip('W07'),true);
 const threatened=fresh();threatened.state.projectiles[0].owner='enemy';const shot=threatened.state.projectiles[0];
 assert.equal(threatened.prepareEquipmentChange(),false);assert.equal(threatened.state.projectiles[0],shot);assert.equal(threatened.equip('W07'),false);
});
test('inventory preparation cannot cancel combat to bypass the equipment lock',()=>{
 const g=new GameSession(1,world);g.enter(area('S02',[{id:'guard',kind:'raider',x:0,z:2}]));g.advance(.02,{x:0,z:0,attack:true});
 const action=g.state.action;assert(action);assert.equal(g.prepareEquipmentChange(),false);assert.equal(g.state.action,action);assert.equal(g.equip('W07'),false);
});
test('rings fill separate slots and explicit slot changes swap existing rings atomically',()=>{
 const g=new GameSession(1,world);g.enter(area());for(const id of ['J03','J04']){g.state.inventory[id]=1;g.state.provenance[id]='fixture';}
 assert.equal(g.equip('J03'),true);assert.equal(g.equip('J04'),true);assert.equal(g.state.equipment.ringLeft,'J03');assert.equal(g.state.equipment.ringRight,'J04');
 assert.equal(g.equipmentChange('J03','ringRight').available,true);assert.equal(g.equip('J03','ringRight'),true);
 assert.equal(g.state.equipment.ringLeft,'J04');assert.equal(g.state.equipment.ringRight,'J03');assert.equal(g.state.inventory.J03,1);assert.equal(g.state.inventory.J04,1);
});

test('equipment and profession changes work away from checkpoints without resetting combat resources',()=>{
 const g=new GameSession(1,world);g.enter({...area('S02'),checkpoint:false});g.state.player.x=10;
 g.state.player.hp=71;g.state.combat.charge=0;g.state.player.focus=37;g.state.combat.ultimateLock=24;g.state.combat.cooldowns.COM_01=2;
 assert.equal(g.preparationAvailability().available,false);assert.equal(g.equipmentAvailability().available,true);
 const change=g.combatLoadoutChange('BOW');assert.equal(change.available,true);assert.equal(g.applyCombatLoadout('BOW',change.weapon,change.token),true);
 assert.equal(g.state.equipment.weapon,'W07');assert.equal(g.state.player.hp,71);assert.equal(g.state.combat.charge,0);assert.equal(g.state.player.focus,37);assert.equal(g.state.combat.ultimateLock,24);assert.equal(g.state.combat.cooldowns.COM_01,2);
});
test('clearing the engaged pack unlocks equipment after one safe second even with distant living enemies',()=>{
 const g=new GameSession(1,world);g.enter({...area('S02',[{id:'guard',kind:'raider',x:0,z:1,hp:20},{id:'other-pack',kind:'raider',x:19,z:19}]),checkpoint:false});
 g.advance(.02,{x:0,z:0,attack:true});tick(g,.25);assert.equal(g.state.enemies[0].hp,0);
 assert.equal(g.equip('W07'),false);tick(g,.7);assert.equal(g.equip('W07'),false);tick(g,.35);
 assert.equal(g.equip('W07'),true);assert(g.state.enemies[1].hp>0);
});
test('retreat needs five safe simulation seconds and survives pause, renewed pursuit, travel and restore',()=>{
 const g=new GameSession(1,world),a=area('S02',[{id:'guard',kind:'raider',x:0,z:8,hp:200}]);g.enter(a);tick(g,.1);
 g.state.player.x=19;g.state.player.z=-19;tick(g,2);const since=g.state.combat.engagement?.quietSince;assert(since!==undefined);
 assert.equal(g.prepareEquipmentChange(),false);assert.equal(g.equip('W07'),false);assert.equal(g.state.combat.engagement?.quietSince,since);
 g.state.player.x=0;g.state.player.z=0;tick(g,.1);assert.equal(g.state.combat.engagement?.quietSince,undefined);
 g.enter({...area('S03'),checkpoint:false});tick(g,2);const restored=GameSession.restore(g.snapshot(),world);restored.enter({...area('S03'),checkpoint:false});
 assert.equal(restored.equip('W07'),false);tick(restored,2.9);assert.equal(restored.equip('W07'),false);tick(restored,.15);assert.equal(restored.equip('W07'),true);
});
test('unrelated distant attack phases and arrows do not lock gear, but incoming arrows and damage over time do',()=>{
 const g=new GameSession(1,world);g.enter({...area('S02',[{id:'distant',kind:'raider',x:19,z:19}]),checkpoint:false});g.state.enemies[0].phase='windup';
 assert.equal(g.equipmentAvailability().available,true);
 const arrow={id:'crossbow:1',kind:'crossbow' as const,x:18,z:18,angle:0,speed:8,remaining:10,damage:14,owner:'enemy' as const,weapon:'crossbow',hits:[],leg:'out' as const,returning:false,charged:false,pierce:1,age:0};
 g.state.projectiles.push(arrow);assert.equal(g.equip('W07'),true);arrow.x=0;arrow.z=8;arrow.angle=Math.PI;assert.equal(g.equip('W11'),false);
 g.state.projectiles=[];g.state.combat.buffs.enemyBurnUntil=g.state.time+3;assert.equal(g.equip('W11'),false);
});
test('equipment queries enforce the selected slot, level and two-handed offhand rule',()=>{
 const g=new GameSession(1,world);g.enter(area());const shield=Object.values(EQUIPMENT).find(d=>d.slot==='offhand')!.id,high=Object.values(EQUIPMENT).find(d=>(d.requiredLevel??1)>1)!.id;
 for(const id of [shield,high]){g.state.inventory[id]=1;g.state.provenance[id]='fixture';}
 assert.equal(g.equipmentChange('W07','head').block,'slot');assert.equal(g.equip('W07','head'),false);assert.equal(g.equipmentChange(high).block,'level');assert.equal(g.equip(high),false);
 assert.equal(g.equip(shield),true);assert.equal(g.equip('W07'),true);assert.equal(g.state.equipment.offhand,null);assert.equal(g.equipmentChange(shield).block,'two-handed');assert.equal(g.equip(shield),false);
});

test('new journey has three free weapon families and four regular slots and an independent level-gated ultimate',()=>{const g=new GameSession(1,world);g.enter(area());for(const id of ['W01','W07','W11'])assert.equal(g.state.inventory[id],1);assert.equal(g.state.inventory.T01,undefined);assert.deepEqual(g.state.combat.activeSlots,['WAR_01',null,null,null]);assert.equal(g.state.inventory.A05,undefined);});
test('reject then independent discovery permits progress without contract gold',()=>{const g=new GameSession(1,world);g.enter(area());at(g,'offer');g.choose('reject');assert.equal(g.state.player.gold,0);at(g,'independent_clue');at(g,'recover');at(g,'offer');g.choose('accept');assert.equal(g.state.player.gold,0);assert.equal(g.state.receipts.design_reward_coin_ch01_obj01,undefined);assert.ok(g.state.flags.recovered);});
test('contract choices do not mint gold and copy changes later knowledge',()=>{const g=new GameSession(1,world);g.enter(area());at(g,'offer');g.choose('ask_letter');g.choose('accept');at(g,'offer');g.choose('accept');assert.equal(g.state.player.gold,0);g.choose('leave');assert.ok(g.state.flags.saw_copy);at(g,'recover');at(g,'letter');g.choose('read_letter');at(g,'meeting');assert.match(g.state.dialogue!.text,/身份|姓名|谁/);});
test('captain defeat alone does not grant W02 and chapter one does not finish the whole campaign',()=>{const g=new GameSession(1,world);g.enter(area('S10',[{id:'captain',kind:'captain',x:0,z:1,hp:6}]));g.advance(.02,{x:0,z:0,attack:true});tick(g,.25);assert.ok(g.state.flags.captain_defeated);assert.equal(g.state.inventory.W02,undefined);at(g,'captain_gate');assert.equal(g.state.inventory.W02,1);at(g,'recover');at(g,'letter');g.choose('read_letter');at(g,'finish');assert.equal(g.state.flags.chapter1_complete,undefined);at(g,'meeting');g.choose('cooperate');at(g,'release_workers');at(g,'disable_trap');at(g,'finish');assert.ok(g.state.flags.chapter1_complete);assert.equal(g.state.flags.complete,undefined);assert.equal(g.state.status,'playing');assert.equal(g.state.inventory.T03,undefined);GameSession.restore(g.snapshot(),world);});
test('walls and range prevent interaction and exit commits',()=>{const g=new GameSession(1,{...world,visible:()=>false});const a=area();a.exits=[{id:'e',x:0,z:0,to:'S02',label:'road',entry:{x:0,z:0}}];g.enter(a);at(g,'cache',{item:'gold',amount:15});assert.equal(g.state.player.gold,0);g.travel(a.exits[0]);assert.equal(g.state.area,'S01');});
test('sword waits for its active phase and one critical or normal swing hits once',()=>{const g=new GameSession(1,world);g.enter(area('S02',[{id:'r',kind:'raider',x:0,z:1,hp:72}]));const events=g.advance(.02,{x:0,z:0,attack:true});assert.equal(g.state.enemies[0].hp,72);events.push(...g.advance(.23,{x:0,z:0}));assert.ok([20,31].includes(72-g.state.enemies[0].hp));assert.equal(events.filter(e=>e.type==='hit'&&e.id==='r').length,1);assert.equal(g.state.combat.charge,0);assert.equal(g.state.player.focus,100);});
test('bow and staff emit real projectiles and released skills retain cooldown through rest and restore',()=>{const g=new GameSession(1,world);g.enter(area());assert.ok(g.equip('W07'));tick(g,.9,{x:0,z:0,attack:true});assert.equal(g.state.projectiles.length,0);g.advance(.02,{x:0,z:0});tick(g,.13);assert.equal(g.state.projectiles[0].kind,'arrow');tick(g,1);assert.ok(g.equip('W11'));g.advance(.02,{x:0,z:0,attack:true});tick(g,.21);assert.equal(g.state.projectiles[g.state.projectiles.length-1].kind,'staff');tick(g,.7);g.castSkill('FIR_01',{x:0,z:8});const first=g.state.action!.id;tick(g,.3);assert.ok(g.state.combat.cooldowns.FIR_01>0);g.castSkill('FIR_01',{x:0,z:8});assert.equal(g.state.action!.id,first);tick(g,3.1);assert.ok(g.castSkill('FIR_01',{x:0,z:8}).some(e=>e.type==='skill_cast'));tick(g,.8);g.rest();assert.ok(g.state.combat.cooldowns.FIR_01>0);const remaining=g.state.combat.cooldowns.FIR_01;const restored=GameSession.restore(g.snapshot(),world);assert.equal(restored.state.combat.cooldowns.FIR_01,remaining);assert.ok(!restored.castSkill('FIR_01',{x:0,z:8}).some(e=>e.type==='skill_cast'));tick(restored,remaining+.02);assert.ok(restored.castSkill('FIR_01',{x:0,z:8}).some(e=>e.type==='skill_cast'));assert.equal(restored.state.inventory.T01,undefined);});
test('cleared encounter and receipt survive entering again and restore',()=>{const g=new GameSession(2,world);const a=area('S02',[{id:'r',kind:'raider',x:0,z:1,hp:20}]);g.enter(a);g.advance(.02,{x:0,z:0,attack:true});tick(g,.25);const iron=g.state.player.iron;g.enter(a);assert.equal(g.state.enemies[0].hp,0);assert.equal(g.state.player.iron,iron);const r=GameSession.restore(g.snapshot(),world);r.enter(a);assert.equal(r.state.enemies[0].hp,0);assert.equal(r.state.player.iron,iron);});
test('merchant stock is atomic and rest does not restock',()=>{const g=new GameSession(1,world);g.enter(area());g.state.player.gold=200;at(g,'offer');g.choose('accept');at(g,'merchant',{merchant:'mira'});assert.ok(g.buy('mira','J03'));assert.equal(g.state.player.gold,20);assert.equal(g.buy('mira','J03'),false);g.rest();assert.equal(g.state.merchantStock.mira.J03,0);assert.equal(g.state.inventory.T01,undefined);assert.equal('craft' in g,false);assert.equal('craft' in g.forging,false);assert.equal('recipes' in g.state,false);const restored=GameSession.restore(g.snapshot(),world);assert.equal(restored.state.inventory.J03,1);assert.equal(restored.state.merchantStock.mira.J03,0);});
test('snapshot validation rejects nonfinite, unknown catalog and forged reward ownership',()=>{const g=new GameSession(1,world);g.enter(area());for(const change of [(s:any)=>s.player.hp=Infinity,(s:any)=>s.inventory.A05=1,(s:any)=>s.inventory.W02=1,(s:any)=>s.inventory.T01=13,(s:any)=>s.recipes=[]]){const s=g.snapshot();change(s);assert.throws(()=>GameSession.restore(s,world));}});

test('heavy damage interrupts a skill before release and permits free pre-release retry; a successful retry starts cooldown',()=>{const g=new GameSession(1,world);g.enter(area());g.equip('W11');g.enter(area('S02',[{id:'shield',kind:'shield',x:0,z:1}]));const e=g.state.enemies[0];e.phase='active';e.attackKind='charge';e.phaseTime=.2;e.targetAngle=Math.PI;e.angle=Math.PI;g.castSkill('FIR_01',{x:0,z:8});g.advance(.02,{x:0,z:0});assert.equal(g.state.action,null);assert.equal(g.state.combat.cooldowns.FIR_01??0,0);assert.equal(g.state.projectiles.length,0);assert.equal(g.state.inventory.T01,undefined);assert.ok(g.state.player.hp<120);assert.ok(g.castSkill('FIR_01',{x:0,z:8}).some(e=>e.type==='skill_cast'));tick(g,.8);assert.ok(g.state.combat.cooldowns.FIR_01>0);assert.ok(!g.castSkill('FIR_01',{x:0,z:8}).some(e=>e.type==='skill_cast'));});
test('simultaneous lethal fire retains captain defeat through retry and waits for gate',()=>{const g=new GameSession(1,world);const a=area('S10',[{id:'captain',kind:'captain',x:0,z:1,hp:6}]);g.enter(a);g.state.player.hp=3;g.state.fireZones.push({id:'fire',x:0,z:0,remaining:4,tick:0,radius:1.1});g.advance(.3,{x:0,z:0});assert.equal(g.state.status,'dead');assert.ok(g.state.flags.captain_defeated);assert.equal(g.state.inventory.W02,undefined);g.retry();g.enter(a,{x:0,z:0});at(g,'captain_gate');assert.equal(g.state.inventory.W02,1);assert.equal(g.state.enemies[0].hp,0);});
test('primary, dodge, ultimate and equipment cooldown debt survives retry and restore',()=>{const g=new GameSession(1,world);g.enter(area());g.equip('W11');g.castSkill('FIR_01',{x:0,z:8});tick(g,.3);assert.ok(g.state.combat.cooldowns.FIR_01>0);g.state.player.hp=0;g.advance(.02,{x:0,z:0});g.retry();assert.ok(g.state.combat.cooldowns.FIR_01>0);const saved=g.snapshot();saved.combat.cooldowns.FIR_01=2;saved.combat.cooldowns.COM_01=1;saved.combat.cooldowns.skillRetry=.35;saved.combat.cooldowns.A07=3;saved.combat.ultimateLock=1.5;const restored=GameSession.restore(saved,world);assert.equal(restored.combatSkillView().find(v=>v.id==='FIR_01')!.cooldown,2);assert.equal(restored.combatSkillView().find(v=>v.id==='COM_01')!.cooldown,1);assert.equal(restored.state.combat.ultimateLock,1.5);assert.equal(restored.state.combat.cooldowns.A07,3);assert.ok(!restored.castSkill('FIR_01',{x:0,z:8}).some(e=>e.type==='skill_cast'));tick(restored,2.02);assert.ok(restored.castSkill('FIR_01',{x:0,z:8}).some(e=>e.type==='skill_cast'));assert.equal(g.state.inventory.T01,undefined);});
test('projectiles stop at walls instead of dealing ranged damage through cover',()=>{const w={...world,visible:(a:any,b:any)=>!(Math.min(a.z,b.z)<.6&&Math.max(a.z,b.z)>=.6)};const g=new GameSession(1,w);const a=area();g.enter(a);g.equip('W11');a.enemies=[{id:'r',kind:'raider',x:0,z:1.2,hp:72}];g.enter(a);g.state.enemies.push({...({id:'r',kind:'raider',x:0,z:1.2,hp:72,maxHp:72,angle:0,phase:'idle',phaseTime:10,attackCount:0,targetAngle:0,attackKind:'swing',struck:false,markedUntil:0,lightningUntil:0,pushImmuneUntil:0,staggerProtectedUntil:0,halfAnnounced:false} as any)});g.advance(.02,{x:0,z:0,attack:true});tick(g,.6);assert.equal(g.state.enemies[0].hp,72);assert.equal(g.state.projectiles.length,0);});
test('walking away from a merchant cannot submit a remote purchase',()=>{const g=new GameSession(1,world);g.enter(area());g.state.player.gold=200;at(g,'offer');g.choose('accept');at(g,'merchant',{merchant:'mira'});tick(g,1,{x:1,z:0});assert.equal(g.buy('mira','J03'),false);assert.equal(g.state.player.gold,200);});
test('return to a previous area preserves its own defeated encounter after travel save',()=>{const g=new GameSession(1,world);const a=area('S02',[{id:'raider',kind:'raider',x:0,z:1,hp:20}]),b=area('S03',[{id:'archer',kind:'archer',x:5,z:4}]);a.exits=[{id:'road',to:'S03',label:'road',x:0,z:0,entry:{x:0,z:0}}];g.enter(a);g.advance(.02,{x:0,z:0,attack:true});tick(g,.25);g.travel(a.exits[0]);const saved=g.snapshot();const r=GameSession.restore(saved,world);r.enter(b);assert.equal(r.state.enemies[0].id,'archer');r.enter(a);assert.equal(r.state.enemies[0].hp,0);});
test('supply barrels are inspectable and never create combat explosion chains',()=>{const g=new GameSession(1,world),a=area();a.obstacles=[{kind:'barrel',x:0,z:1,width:.4,depth:.4,height:1}];g.enter(a);const before=g.state.player.hp;at(g,'barrel',{z:1});const events=g.advance(1,{x:0,z:0,attack:true});assert.equal(events.filter(e=>e.type==='fuse'||e.type==='explosion').length,0);assert.ok(g.state.barrels.every(b=>!b.exploded&&b.fuse<0));assert.equal(g.state.player.hp,before);});
test('malformed nested records and inconsistent encounter ownership are rejected',()=>{const g=new GameSession(1,world);g.enter(area('S02',[{id:'r',kind:'raider',x:5,z:5}]));for(const change of [(s:any)=>s.enemies[0].extra={x:Infinity},(s:any)=>s.enemies=[],(s:any)=>s.equipment.extra='W01',(s:any)=>s.player.maxHp=160]){const snapshot=g.snapshot();change(snapshot);assert.throws(()=>GameSession.restore(snapshot,world));}});
test('recover requires the cart guards defeated even when they stand farther away',()=>{const g=new GameSession(1,world);g.enter(area('S04',[{id:'guard',kind:'raider',x:10,z:0}]));at(g,'recover');assert.equal(g.state.flags.recovered,undefined);assert.equal(g.state.player.gold,0);});
test('meeting does not claim undisclosed identity when independent explorers never met Mira',()=>{const g=new GameSession(1,world);g.enter(area('U1-04'));at(g,'meeting');assert.doesNotMatch(g.state.dialogue!.text,/承认|接约前已读/);});
test('NightQi shop is unlocked by discovering her and Mira alone requires a contract',()=>{const g=new GameSession(1,world);g.enter(area());at(g,'merchant',{merchant:'nightqi'});assert.ok(g.state.discoveredMerchants.includes('nightqi'));at(g,'merchant',{merchant:'mira'});assert.ok(!g.state.discoveredMerchants.includes('mira'));});
test('workers can leave after clearing guards without forcing optional trap disarm',()=>{const g=new GameSession(1,world);g.enter(area('U1-05'));at(g,'meeting');g.choose('star_copy');at(g,'release_workers');assert.ok(g.state.flags.trap_handled);assert.equal(g.state.flags.trap_disabled,undefined);});
test('input cancellation discards bow aim without turning it into a release',()=>{const g=new GameSession(1,world);g.enter(area());g.equip('W07');tick(g,1,{x:0,z:0,attack:true});g.cancelInput();g.advance(.2,{x:0,z:0});assert.equal(g.state.projectiles.length,0);assert.equal(g.state.action,null);});
test('Mira shop is reachable through her real offer dialogue after accepting',()=>{const g=new GameSession(1,world),a=area();g.state.player.gold=200;a.objects=[{id:'mira',action:'offer',merchant:'mira',label:'Mira',description:'',x:0,z:0}];g.enter(a);g.interact(a.objects[0]);g.choose('accept');g.interact(a.objects[0]);assert.ok(g.choose('shop').some(e=>e.type==='shop'));assert.ok(g.buy('mira','J03'));});
test('canonical fixed reward receipts survive renamed scene object IDs',()=>{const g=new GameSession(1,world);g.enter(area());at(g,'cache',{id:'find-w08',item:'W08'});assert.equal(g.state.receipts.design_reward_ch01_oath_sword,true);at(g,'cache',{id:'find-a01',item:'A01'});assert.equal(g.state.receipts.design_find_a01,true);});
test('the two independent legendary rolls stay deterministic alongside regional drops',()=>{const run=()=>{const g=new GameSession(91,world);g.enter(area('S08',[{id:'pass-warden',kind:'raider',x:0,z:1,hp:20}]));g.advance(.02,{x:0,z:0,attack:true});tick(g,.25);at(g,'cache',{id:'find-w08',item:'W08'});return g;};const g=run(),first=structuredClone(g.state.dropRolls);assert.equal(Object.keys(first).filter(k=>k.startsWith('pass:')||k.startsWith('cache:')).length,2);assert.deepEqual(run().state.dropRolls,first);const loaded=GameSession.restore(g.snapshot(),world);loaded.enter(area('S08',[{id:'pass-warden',kind:'raider',x:0,z:1,hp:20}]));at(loaded,'cache',{id:'find-w08',item:'W08'});assert.deepEqual(loaded.state.dropRolls,first);});
test('inventing a source string does not legitimize forged armor or a legendary',()=>{const g=new GameSession(1,world);g.enter(area());for(const id of ['A01','L01']){const s=g.snapshot();s.inventory[id]=1;s.provenance[id]='legend:fake';s.receipts[`grant:legend:fake:${id}`]=true;s.dropRolls.fake={roll:1,result:id};s.receipts['roll:fake']=id;assert.throws(()=>GameSession.restore(s,world));}});
function legend(id:string,enemies:AreaDef['enemies']){for(let seed=1;seed<1000;seed++){const g=new GameSession(seed,world);g.enter(area());at(g,'cache',{id:'find-w08',item:'W08'});if(g.state.inventory[id]){assert.ok(g.equip(id));g.enter(area('S02',enemies));return g;}}throw new Error('deterministic legend source never yielded '+id);}
test('L02 strengthens the sole BOW01 target without restoring penetration',()=>{const g=legend('L02',Array.from({length:6},(_,i)=>({id:'r'+i,kind:'raider',x:0,z:3+i,hp:2000})));level(g,32);g.state.progression.learned.BOW_01=5;g.state.progression.skillPoints!-=10;activateCombatLoadout(g.state.combat,g.state.progression);for(const e of g.state.enemies){e.phase='recovery';e.phaseTime=20;}g.castSkill('BOW_01',{x:0,z:8},0);const cast=g.state.combat.casts[0],base=cast.power*cast.rank.maxDamagePerTargetS*(cast.critical?1.5:1);tick(g,1);assert.ok(g.state.projectiles.every(q=>!q.returning));assert.equal(g.state.enemies[0].hp,2000-Math.round(base*1.1));assert.equal(g.state.enemies.filter(e=>/^r[1-5]$/.test(e.id)).length,5);assert.ok(g.state.enemies.filter(e=>/^r[1-5]$/.test(e.id)).every(e=>e.hp===2000));assert.equal(g.state.combat.charge,0);});
test('L01 consumes only the single victim lightning mark without recursive attacks',()=>{const g=legend('L01',[{id:'a',kind:'raider',x:0,z:1.5,hp:300},{id:'b',kind:'raider',x:0,z:2,hp:300}]);for(const e of g.state.enemies){e.phase='recovery';e.phaseTime=20;g.state.combat.statuses[e.id]={hunterMarkUntil:0,hunterMarkBonus:0,burnUntil:0,burnNext:0,burnDamage:0,slowUntil:0,slowPercent:0,lightningUntil:7};}g.castSkill('WAR_01',{x:0,z:2},0);tick(g,.8);const cast=g.state.combat.casts[0];assert.ok(!cast||cast.procs.filter(k=>k.startsWith('secondary:')).length<=2);assert.equal(g.state.combat.statuses.a.lightningUntil,0);assert.equal(g.state.combat.statuses.b.lightningUntil,7);assert.equal(g.state.enemies[1].hp,300);assert.ok(g.state.player.focus>=94&&g.state.player.focus<=100);assert.equal(g.state.combat.charge,0);});
test('three nearby barrels do not add damage to an ordinary sword swing',()=>{const g=new GameSession(1,world),a=area('S02',[{id:'r',kind:'raider',x:0,z:1,hp:300}]);a.obstacles=[-.4,0,.4].map(x=>({kind:'barrel',x,z:.9,width:.2,depth:.2,height:1}));g.enter(a);g.advance(.02,{x:0,z:0,attack:true});tick(g,.82);assert.ok([20,31].includes(300-g.state.enemies[0].hp));assert.ok(g.state.barrels.every(b=>!b.exploded));});
test('overlapping fire zones share one delayed contact tick per entity',()=>{const g=new GameSession(1,world);g.enter(area('S02',[{id:'r',kind:'raider',x:0,z:1,hp:300}]));g.state.fireZones.push({id:'f1',x:0,z:1,remaining:4,tick:.01,radius:1.1},{id:'f2',x:0,z:1,remaining:4,tick:.26,radius:1.1});tick(g,.1);assert.equal(g.state.enemies[0].hp,300);tick(g,.65);assert.equal(g.state.enemies[0].hp,294);});
test('A02 increases direct skill damage for a target beyond5m',()=>{const shoot=(z:number)=>{const g=new GameSession(2,world);g.enter(area());g.equip('W11');at(g,'cache',{item:'A02'});g.equip('A02');g.enter(area('S02',[{id:'r',kind:'raider',x:0,z,hp:1000}]));g.state.enemies[0].phase='recovery';g.state.enemies[0].phaseTime=20;g.castSkill('FIR_01',{x:0,z},0);const events=g.advance(.9,{x:0,z:0});return events.find(e=>e.type==='skill_hit')!.value!;};assert.ok(shoot(6)>shoot(4));});
test('A09 requires an actual precision dodge and adds4break to the next WAR skill once',()=>{const g=new GameSession(1,world);g.enter(area());at(g,'cache',{item:'A09'});g.equip('A09');g.enter(area('S02',[{id:'r',kind:'raider',x:0,z:1,hp:200}]));const e=g.state.enemies[0];e.phase='windup';e.phaseTime=.06;e.targetAngle=Math.PI;e.angle=Math.PI;const evades=g.advance(.15,{x:1,z:0,dash:true});assert.ok(evades.some(e=>e.type==='evade'));assert.equal(g.state.flags.counter_ready,true);tick(g,.25);e.x=g.state.player.x;e.z=g.state.player.z+1;e.phase='recovery';e.phaseTime=20;g.castSkill('WAR_01',{x:e.x,z:e.z});const hits=g.advance(.8,{x:0,z:0});assert.equal(hits.filter(e=>e.type==='poise').reduce((n,e)=>n+(e.value??0),0),19);assert.equal(g.state.flags.counter_ready,false);assert.ok(g.state.cooldowns.counter>4);});
test('A13 reduces physical damage during iron shield and enemies never force player displacement',()=>{const charge=(boots:boolean)=>{const g=new GameSession(1,world);g.enter(area());if(boots){g.state.player.gold=200;at(g,'offer');g.choose('accept');at(g,'merchant',{merchant:'lorn'});g.buy('lorn','A13');g.equip('A13');}level(g,8);g.state.combat.activeSlots=['WAR_03',null,null,null];g.enter(area('S02',[{id:'s',kind:'shield',x:0,z:1,hp:105}]));g.state.enemies[0].phase='recovery';g.state.enemies[0].phaseTime=20;g.castSkill('WAR_03');tick(g,.6);const e=g.state.enemies[0];e.phase='windup';e.attackKind='charge';e.phaseTime=.06;e.targetAngle=Math.PI;e.angle=Math.PI;g.state.player.shield=50;const events=g.advance(.15,{x:0,z:0});assert.equal(events.filter(e=>e.type==='player_push').length,0);assert.equal(g.state.player.x,0);assert.equal(g.state.player.z,0);return 50-g.state.player.shield;};assert.ok(charge(true)<charge(false));});
test('holding bow can update aim before its legal release locks the shot',()=>{const g=new GameSession(1,world);g.enter(area());g.equip('W07');tick(g,.8,{x:0,z:0,aim:0,attack:true});g.advance(.02,{x:0,z:0,aim:Math.PI/2,attack:true});g.advance(.02,{x:0,z:0,aim:Math.PI/2});assert.ok(g.state.projectiles[0].x>0);assert.ok(Math.abs(g.state.projectiles[0].z)<.001);});
test('merged fire field freezes its location, slows movement and releases the slow after leaving',()=>{
 const g=new GameSession(1,world);g.enter(area());g.equip('W11');level(g,6);const target={x:0,z:6};g.castSkill('FIR_05',target,Math.PI/2);target.z=30;assert.deepEqual(g.state.action!.target,{x:0,z:6});tick(g,.6);
 g.enter(area('S02',[{id:'pursuer',kind:'raider',x:0,z:6,hp:1000}]));
 // Area changes clear placed effects. Cast the wall in the actual encounter.
 g.state.combat.cooldowns.FIR_05=0;g.castSkill('FIR_05',{x:0,z:6},Math.PI/2);tick(g,.6);assert.equal(g.state.combat.statuses.pursuer.slowPercent,.35);assert.ok(g.state.combat.cooldowns.FIR_05>0);assert.equal(g.state.player.z,0);
 const e=g.state.enemies[0];e.x=8;e.z=8;tick(g,.5);assert.ok(g.state.combat.statuses.pursuer.slowUntil<=g.state.time);
 const bad=new GameSession(1,world);bad.enter(area());bad.equip('W11');level(bad,6);bad.castSkill('FIR_05',{x:0,z:30});assert.equal(bad.state.action,null);assert.equal(bad.state.combat.cooldowns.FIR_05??0,0);
});

test('bow trap arms once, roots ordinary pursuers, reduces boss control and rejects blocked placements',()=>{
 const g=new GameSession(1,world);g.enter(area());g.equip('W07');level(g,6);g.enter(area('S02',[{id:'ordinary',kind:'raider',x:0,z:4,hp:1000},{id:'boss',kind:'captain',x:.5,z:4,hp:1000}]));
 for(const e of g.state.enemies){e.phase='recovery';e.phaseTime=20;}
 g.castSkill('BOW_06',{x:0,z:4});tick(g,.3);assert.equal(g.state.combat.buffs['rootUntil:ordinary'],undefined);assert.equal(g.state.enemies[0].hp,1000);
 tick(g,.3);assert.ok(g.state.combat.buffs['rootUntil:ordinary']>g.state.time);assert.equal(g.state.combat.buffs['rootUntil:boss'],undefined);assert.equal(g.state.combat.statuses.ordinary.slowPercent,.35);assert.equal(g.state.combat.statuses.boss.slowPercent,.1);
 const hp=g.state.enemies[0].hp;tick(g,1);assert.equal(g.state.enemies[0].hp,hp);assert.ok(g.state.combat.buffs['rootUntil:ordinary']<g.state.time);assert.equal(g.state.combat.casts.filter(c=>c.skillId==='BOW_06').length,0);assert.ok(g.castSkill('BOW_06',{x:0,z:4}).every(e=>e.type!=='skill_cast'));
 const blocked=new GameSession(1,{...world,visible:()=>false});blocked.enter(area());blocked.equip('W07');level(blocked,6);blocked.castSkill('BOW_06',{x:0,z:4});assert.equal(blocked.state.action,null);assert.equal(blocked.state.combat.cooldowns.BOW_06??0,0);
});

test('blocked nonfinite and disconnected skill targets reject without cooldown or resources',()=>{for(const query of [{...world,visible:()=>false},{...world,height:(p:{x:number;z:number})=>p.x>1?3:0},world]){const g=new GameSession(1,query);g.enter(area());g.equip('W11');g.castSkill('FIR_01',{x:query===world?NaN:4,z:0});g.advance(.5,{x:0,z:0});assert.equal(g.state.combat.cooldowns.FIR_01??0,0);assert.equal(g.state.projectiles.length,0);assert.equal(g.state.action,null);assert.equal(g.state.player.focus,100);}});
test('skill cancellation before release costs nothing and a released projectile retains cooldown through restore',()=>{
 const g=new GameSession(1,world);g.enter(area());g.equip('W11');g.castSkill('FIR_01',{x:0,z:8});tick(g,.1);g.cancelInput();tick(g,.5);assert.equal(g.state.combat.cooldowns.FIR_01??0,0);assert.equal(g.state.projectiles.length,0);
 g.castSkill('FIR_01',{x:0,z:8});tick(g,.28);g.cancelInput();assert.ok(g.state.combat.cooldowns.FIR_01>0);assert.equal(g.state.projectiles.length,1);tick(g,.5);assert.ok(!g.castSkill('FIR_01',{x:0,z:8}).some(e=>e.type==='skill_cast'));
 const remaining=g.state.combat.cooldowns.FIR_01,restored=GameSession.restore(g.snapshot(),world);assert.equal(restored.state.combat.cooldowns.FIR_01,remaining);assert.ok(!restored.castSkill('FIR_01',{x:0,z:8}).some(e=>e.type==='skill_cast'));tick(restored,remaining+.02);assert.ok(restored.castSkill('FIR_01',{x:0,z:8}).some(e=>e.type==='skill_cast'));
});

test('content durability covers world and reinforcements and refreshes wounded saves once without restoring deaths or rewards',()=>{
 const g=new GameSession(1,world);g.enter(AREAS.S02);
 const archived=g.state.enemies[0].id,dead=g.state.enemies[1].id;
 g.enter(AREAS.S03);const current=g.state.enemies[0].id,saved=g.snapshot();
 for(const enemies of [saved.enemies,...Object.values(saved.encounters)])for(const enemy of enemies){
  if(enemy.id===archived||enemy.id===current){enemy.maxHp=100;enemy.hp=25;}
  if(enemy.id===dead){enemy.maxHp=100;enemy.hp=0;enemy.phase='dead';enemy.respawnAt=123;enemy.respawnCount=4;}
 }
 saved.receipts[`kill:S02:${dead}`]=true;
 const restored=GameSession.restore(saved,world),active=restored.state.enemies.find(e=>e.id===current)!;
 assert.equal(active.maxHp,enemyContentHealth(active));assert.equal(active.hp,Math.round(active.maxHp*.25));
 const archivedEnemy=restored.state.encounters.S02.find(e=>e.id===archived)!;
 assert.equal(archivedEnemy.hp,Math.round(archivedEnemy.maxHp*.25));
 const corpse=restored.state.encounters.S02.find(e=>e.id===dead)!;
 assert.equal(corpse.hp,0);assert.equal(corpse.phase,'dead');assert.equal(corpse.respawnAt,123);assert.equal(corpse.respawnCount,4);assert.equal(restored.state.receipts[`kill:S02:${dead}`],true);
 const hp=active.hp;restored.enter(AREAS.S03);restored.enter(AREAS.S02);restored.enter(AREAS.S03);assert.equal(restored.state.enemies.find(e=>e.id===current)!.hp,hp);
 const again=GameSession.restore(restored.snapshot(),world);assert.equal(again.state.enemies.find(e=>e.id===current)!.hp,hp);
 for(const scene of Object.values(AREAS))for(const enemy of scene.enemies){const max=enemyContentHealth(enemy);assert.ok(max>0&&max<=100000&&Number.isInteger(max));}
 const lateBosses=CAMPAIGN_PHASES.map(p=>enemyContentHealth({kind:'captain',bossId:`BOSS_R${p.chapter}`,level:p.recommendedBossLevel}));
 assert.equal(lateBosses[7],63025);assert.ok(lateBosses.every((hp,i)=>hp<=100000&&(i===0||hp>lateBosses[i-1])));
 for(const battle of CAMPAIGN_BATTLES)for(const wave of battle.waves)for(const enemy of wave.enemies){const fighter=campaignFighter(enemy)!;assert.ok(fighter.maxHp>=enemyContentHealth(enemy));assert.equal(fighter.damage,1);}
 const base={kind:'raider' as const,level:11,templateId:'BEAST_SCREE_HOUND'};
 assert.equal(enemyContentHealth({...base,packId:'fixture'} as typeof base),enemyContentHealth(base));
 assert.equal(enemyDamageMultiplier({...base,packId:'fixture'} as typeof base),enemyDamageMultiplier(base));
 const custom=new GameSession(1,world);custom.enter(area('S02',[{id:'custom',kind:'raider',x:8,z:8,level:20,hp:123},{id:'dummy',kind:'raider',x:8,z:10,templateId:'BEAST_HOUND',level:40,hp:100000,trainingDummy:true},{id:'content-default',kind:'raider',x:12,z:12,level:11}]));
 assert.deepEqual(custom.state.enemies.filter(e=>e.id==='custom'||e.id==='dummy').map(e=>e.maxHp),[123,100000]);
 assert.equal(custom.state.enemies.find(e=>e.id==='content-default')!.maxHp,505);
});
