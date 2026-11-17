/** Controlled-domain audit: real death/respawn settlement, not natural playtime. */
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import {dirname} from 'node:path';
import {GameSession} from '../assets/scripts/core/GameSession';
import {AREAS} from '../assets/scripts/features/world/data/WorldData';
import {materialStock,materialBalance,validateCultivation} from '../assets/scripts/features/crafting/common/CultivationRewards';
import {validateForging,forgingSignature,type ForgingRecord} from '../assets/scripts/features/crafting/common/EquipmentForging';
import {validateGems} from '../assets/scripts/features/gems/common/GemWorkshop';
import {EQUIPMENT} from '../assets/scripts/features/equipment/data/Equipment';
import {gemCapacity,type GemStat} from '../assets/scripts/features/gems/data/Gems';
import {awardXp,cumulativeXp} from '../assets/scripts/features/progression/common/Progression';
import {activateCombatLoadout,COMBAT_LOADOUTS,type CombatFamily} from '../assets/scripts/features/progression/common/CombatLoadouts';
import {FORGING_RANK_LEVELS} from '../assets/scripts/features/crafting/data/EquipmentForging';
import {artifactWeaponForStyle} from '../assets/scripts/features/equipment/data/GrowingEquipment';
import {equippedGearBonus,combatCriticalChance,combatCriticalMultiplier} from '../assets/scripts/features/equipment/common/EquipmentDice';

const world={move:(p:{x:number;z:number},d:{x:number;z:number})=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0};
const game=new GameSession(730171,world),s=game.state;
assert.equal(FORGING_RANK_LEVELS.length,8,'This audit targets the current eight-rank cultivation policy');
const levelPreparations:{reason:string;from:number;level:number;experienceAdded:number}[]=[];
function prepareLevel(session:GameSession,minimum:number,reason:string){
 const p=session.state.progression,from=p.level,target=Math.max(from,minimum),experienceAdded=Math.max(0,cumulativeXp(target)-p.totalXp);
 if(experienceAdded)awardXp(p,'fixture:cultivation-level:'+reason,experienceAdded);
 activateCombatLoadout(session.state.combat,p);session.enter(AREAS.S01);
 levelPreparations.push({reason,from,level:p.level,experienceAdded});
}
game.enter(AREAS.S08);
const id=s.enemies.find(e=>e.respawnSeconds&&!e.bossId)!.id;
const notices:string[]=[];
for(let i=0;i<48;i++){
 const target=s.enemies.find(e=>e.id===id)!;
 assert.ok(target.hp>0,'the actual spawn must be alive before settlement');
 // Controlled health setup exercises the ordinary death path and real receipts.
 target.hp=0;notices.push(...game.advance(.02,{x:0,z:0}).map(e=>e.text??''));
 const marker=JSON.stringify(s.forging.cultivation),bank=JSON.stringify(s.gems.bank);
 assert.equal(game.cultivation.defeat(target),false,'the same corpse cannot pay twice');
 assert.equal(JSON.stringify(s.forging.cultivation),marker);assert.equal(JSON.stringify(s.gems.bank),bank);
 validateForging(s);validateGems(s);
 if(i<47){Object.assign(s.player,{x:AREAS.S08.width/2-2,z:AREAS.S08.depth/2-2});s.time=(target.respawnAt??s.time)+1;game.advance(.02,{x:0,z:0});}
}
assert.equal(materialStock(s,1),16);
assert.equal(Object.values(s.gems.bank).reduce((n,v)=>n+v,0),30,'48 ordinary kills give 6 complete gems');
const restored=GameSession.restore(game.snapshot(),world);
assert.equal(materialStock(restored.state,1),16);validateForging(restored.state);validateGems(restored.state);
restored.enter(AREAS.S01);Object.assign(restored.state.player,{gold:9999,iron:9999,runes:9999,cores:9999});
prepareLevel(restored,FORGING_RANK_LEVELS[0],'chapter-one-rank-one');
const first=restored.forging.enhancement('W01');assert.ok(first.allowed,first.reason);assert.equal(restored.forging.enhance('W01',first.token),true);assert.equal(materialStock(restored.state,1),15);
prepareLevel(restored,FORGING_RANK_LEVELS[1],'chapter-two-rank-two');
const compose=restored.cultivation.synthesis(1);assert.ok(compose.allowed,compose.reason);assert.equal(restored.cultivation.synthesize(1,compose.token),true);assert.equal(materialStock(restored.state,1),12);assert.equal(materialStock(restored.state,2),1);
validateForging(restored.state);validateGems(restored.state);
const bad=structuredClone(restored.state);Object.values(bad.forging.cultivation!.harvests)[0].count+=1;assert.throws(()=>validateCultivation(bad));
const omittedStone=structuredClone(restored.state),omitted=omittedStone.forging.transactions.find(t=>t.kind==='enhance')! as unknown as Record<string,unknown>;
delete omitted.materialTier;delete omitted.materialCount;
omittedStone.receipts[String(omitted.request)]=forgingSignature(omitted as unknown as ForgingRecord);
assert.throws(()=>validateForging(omittedStone),'re-signed enhancement cannot omit its compulsory stone payment');
const badBank=structuredClone(restored.state);const key=Object.keys(badBank.gems.bank)[0];badBank.gems.bank[key]+=5;assert.throws(()=>validateGems(badBank));
const clock=Date.UTC(2026,10,17,4),boostGame=new GameSession(730172,world,()=>clock),bs=boostGame.state;
boostGame.enter(AREAS.S08);const boostId=bs.enemies.find(e=>e.respawnSeconds&&!e.bossId)!.id;
const killAndRespawn=()=>{let e=bs.enemies.find(e=>e.id===boostId)!;if(e.hp<=0){Object.assign(bs.player,{x:AREAS.S08.width/2-2,z:AREAS.S08.depth/2-2});bs.time=(e.respawnAt??bs.time)+1;boostGame.advance(.02,{x:0,z:0});e=bs.enemies.find(e=>e.id===boostId)!;}assert.ok(e.hp>0);e.hp=0;boostGame.advance(.02,{x:0,z:0});};
let preparationKills=0;while(!boostGame.huntingExperience().materialBoost&&preparationKills<500){killAndRespawn();preparationKills++;}
assert.ok(boostGame.huntingExperience().materialBoost,'normal same-day XP cap must activate material compensation');const cappedXp=bs.progression.totalXp,beforeBoost=materialStock(bs,1);
for(let i=0;i<8;i++)killAndRespawn();assert.equal(bs.progression.totalXp,cappedXp);assert.equal(materialStock(bs,1)-beforeBoost,8,'every capped ordinary kill gives one stone');
assert.ok(Object.values(bs.forging.cultivation!.harvests).some(h=>(h.bonusCount??0)>=8));validateForging(bs);validateGems(bs);
const badBonus=structuredClone(bs);Object.values(badBonus.forging.cultivation!.harvests).find(h=>h.bonusCount)!.bonusCount!++;assert.throws(()=>validateCultivation(badBonus));
const boostRead=GameSession.restore(boostGame.snapshot(),world);assert.equal(materialStock(boostRead.state,1),materialStock(bs,1));
boostGame.enter(AREAS.S10);const boss=bs.enemies.find(e=>e.bossId==='BOSS_R1')!,bossBefore=materialStock(bs,1);boss.hp=0;boostGame.advance(.02,{x:0,z:0});assert.equal(materialStock(bs,1)-bossBefore,6,'capped boss awards six stones');assert.equal(boostGame.cultivation.defeat(boss),false);validateForging(bs);validateGems(bs);
boostGame.enter(AREAS.H08);const highBoss=bs.enemies.find(e=>e.bossId==='BOSS_R2')!,secondBefore=materialStock(bs,2);highBoss.hp=0;boostGame.advance(.02,{x:0,z:0});assert.equal(materialStock(bs,2)-secondBefore,6);assert.ok(Object.keys(bs.gems.bank).some(key=>key.endsWith(':2')));validateForging(bs);validateGems(bs);
const equipmentDrop=bs.groundLoot.find(drop=>drop.area===bs.area&&gemCapacity(EQUIPMENT[drop.item])>0)!;assert.ok(equipmentDrop,'real boss equipment is available for the socket audit');Object.assign(bs.player,{x:equipmentDrop.x,z:equipmentDrop.z});boostGame.pickupLoot(equipmentDrop.id);assert.ok(bs.inventory[equipmentDrop.item]);boostGame.enter(AREAS.S01);bs.player.gold=9999;
prepareLevel(boostGame,6,'first-socket');
const firstKey=Object.keys(bs.gems.bank).find(key=>key.endsWith(':1')&&bs.gems.bank[key]>=5)!,gemStat=firstKey.split(':')[0] as GemStat;
const inlay=boostGame.gems.inset(equipmentDrop.item,0,gemStat,1);assert.ok(inlay.allowed,inlay.reason);assert.equal(boostGame.gems.inlay(equipmentDrop.item,0,gemStat,1,inlay.token),true);validateGems(bs);
// Only the synthesis level is prepared; all crystal stock came from real loot/shards.
prepareLevel(boostGame,16,'tier-two-gem');
for(let i=0;i<3;i++){const q=boostGame.gems.exchange('power');assert.ok(q.allowed,q.reason);assert.ok(boostGame.gems.convert('power',q.token));}
const gemCompose=boostGame.gems.synthesis('power',1);assert.ok(gemCompose.allowed,gemCompose.reason);assert.ok(boostGame.gems.synthesize('power',1,gemCompose.token));validateGems(bs);validateForging(bs);
boostGame.enter(AREAS.H17);const otherBoss=bs.enemies.find(e=>e.bossId)!;assert.ok(otherBoss);otherBoss.hp=0;boostGame.advance(.02,{x:0,z:0});validateGems(bs);validateForging(bs);assert.ok(bs.forging.cultivation!.gemBatches.length>1,'gem loot after socket/synthesis is replayed in action order');
prepareLevel(boostGame,FORGING_RANK_LEVELS[1],'earned-boss-item-rank-two');bs.player.gold=9999;
for(let rank=1;rank<=2;rank++){const quote=boostGame.forging.enhancement(equipmentDrop.item);assert.ok(quote.allowed,quote.reason);assert.ok(boostGame.forging.enhance(equipmentDrop.item,quote.token));validateForging(bs);}

/** Explicit strength fixture: only level, artifact ownership and a finite
 * common-currency budget are prepared. Every stone is earned through real
 * death/respawn settlement and native3:1 synthesis; no ledger is fabricated.
 * This proves cultivation and damage arithmetic, not natural playtime/economy.
 */
function intensityFixture(family:CombatFamily){
 const session=new GameSession(730173,world),state=session.state;prepareLevel(session,80,'max-eight-'+family);
 assert.ok(session.applyCombatLoadout(family,COMBAT_LOADOUTS[family].weapon));
 session.enter(AREAS.S08);const targetId=state.enemies.find(enemy=>enemy.respawnSeconds&&!enemy.bossId)!.id;
 let harvestKills=0;
 while(materialStock(state,1)<160&&harvestKills<600){
  let target=state.enemies.find(enemy=>enemy.id===targetId)!;
  if(target.hp<=0){Object.assign(state.player,{x:AREAS.S08.width/2-2,z:AREAS.S08.depth/2-2});state.time=(target.respawnAt??state.time)+1;session.advance(.02,{x:0,z:0});target=state.enemies.find(enemy=>enemy.id===targetId)!;}
  assert.ok(target.hp>0);target.hp=0;session.advance(.02,{x:0,z:0});harvestKills++;
 }
 assert.equal(materialStock(state,1),160);validateForging(state);validateGems(state);
 session.enter(AREAS.S01);const item=artifactWeaponForStyle[family];state.inventory[item]=1;state.provenance[item]='fixture:cultivation-intensity';assert.ok(session.equip(item));
 const goldBudget=20000;state.player.gold=9999;let goldReserve=goldBudget-state.player.gold;state.player.iron=135;state.player.runes=4;state.player.cores=9;
 const fundWallet=()=>{const transfer=Math.min(9999-state.player.gold,goldReserve);state.player.gold+=transfer;goldReserve-=transfer;};
 let synthesisGold=0;const ranks=[];
 const ensureStock=(tier:number,required:number)=>{
  while(materialStock(state,tier)<required){
   assert.ok(tier>1,'finite harvested supply exhausted');ensureStock(tier-1,3);
   fundWallet();const quote=session.cultivation.synthesis(tier-1);assert.ok(quote.allowed,quote.reason);assert.ok(session.cultivation.synthesize(tier-1,quote.token));synthesisGold+=quote.gold;
  }
 };
 for(let rank=1;rank<=FORGING_RANK_LEVELS.length;rank++){
  let quote=session.forging.enhancement(item);ensureStock(quote.materialTier,1);fundWallet();quote=session.forging.enhancement(item);assert.ok(quote.allowed,quote.reason);assert.ok(quote.step);
  const before={gold:state.player.gold,iron:state.player.iron,runes:state.player.runes,cores:state.player.cores};assert.ok(session.forging.enhance(item,quote.token));validateForging(state);
  const paid={gold:before.gold-state.player.gold,iron:before.iron-state.player.iron,runes:before.runes-state.player.runes,cores:before.cores-state.player.cores};
  assert.deepEqual(paid,{gold:quote.step.gold,iron:quote.step.iron,runes:quote.step.runes,cores:quote.step.cores});
  const bonus=equippedGearBonus(state),view=session.progressionView();assert.ok(Object.values(bonus).every(Number.isFinite));
  for(const key of ['strength','dexterity','intellect','vitality'] as const)assert.ok(Number.isInteger(bonus[key]));
  assert.ok(Number.isFinite(view.criticalChance)&&view.criticalChance<=30);assert.ok(Number.isFinite(view.criticalDamage)&&view.criticalDamage<=250);
  ranks.push({rank,paid,stoneTier:quote.materialTier,bonus,criticalChance:view.criticalChance,criticalDamage:view.criticalDamage});
 }
 const maximum=session.forging.enhancement(item);assert.equal(maximum.view?.rank,8);assert.equal(maximum.allowed,false);assert.equal(maximum.step,null);
 const extreme={...equippedGearBonus(state),criticalChance:10000,criticalDamage:10000};assert.equal(combatCriticalChance(state,extreme),.3);assert.equal(combatCriticalMultiplier(state,extreme),2.5);
 session.enter({...AREAS.S01,id:'CULTIVATION_OUTPUT_FIXTURE',spawn:{x:0,z:0},objects:[],exits:[],enemies:[{id:'output-dummy',kind:'raider',level:80,hp:1000000,trainingDummy:true,x:0,z:family==='WAR'?1.2:4}]});
 state.player.focus=state.player.maxFocus;let damage=0,hits=0;
 for(let frame=0;frame<500;frame++){
  const action=state.action,attack=family==='BOW'?(!action||action.kind==='bowAim'&&action.elapsed<.85):true;
  for(const event of session.advance(.02,{x:0,z:0,aim:0,attack})){if(event.type==='hit'){const lost=Number(event.hpLost);assert.ok(Number.isFinite(lost)&&lost>=0);damage+=lost;hits++;}}
 }
 assert.ok(hits>0&&damage>0);validateForging(state);validateGems(state);
 return{family,item,level:80,harvestKills,earnedTierOneStones:160,commonFixture:{goldBudget,iron:135,runes:4,cores:9,artifactOwnership:true,unspentLegalAttributePoints:state.progression.unspentPoints},ranks,synthesisGold,totalGoldSpent:goldBudget-goldReserve-state.player.gold,remainingStones:[1,2,3,4,5].map(tier=>materialStock(state,tier)),maximumRank:maximum.view!.rank,pureExtremeCapProbe:{chance:.3,multiplier:2.5,scope:'API arithmetic probe with explicit extreme input, not reachable equipment stats'},basicDamageProbe:{seconds:10,damage,hits,scope:'Production basic attacks with rank-one skills and unspent attributes, passive dummy; finite-damage smoke, not optimized profession DPS or natural content'}};
}
const intensity=(Object.keys(COMBAT_LOADOUTS) as CombatFamily[]).map(intensityFixture);
const report={intensity,status:'passed',levelPreparations,commonWalletFixture:'gold/iron/runes/cores are prepared up to9999 only for controlled API checks; earned stones and gems are not injected',omittedStonePaymentRejected:true,method:'controlled death health setup; real death/respawn/reward/forge/readback paths',ordinaryKills:48,capPreparationKills:preparationKills,cappedOrdinaryKills:8,cappedOrdinaryStones:8,cappedBossStones:6,chapterTwoBossStones:6,bonusCountSaved:true,bonusCountTamperRejected:true,realBossEquipmentInlaid:true,gemThreeToOneSynthesized:true,postCultivationLootReplayed:true,completeGems:6,stonesFromKills:16,enhancements:3,positivePaidRanks:{starter:1,earnedBossEquipment:2},forgingRankLevels:FORGING_RANK_LEVELS,synthesis:'3 tier I -> 1 tier II',balances:materialBalance(restored.state),corpseRepeatRejected:true,materialCorruptionRejected:true,gemCorruptionRejected:true,noticeSeen:notices.some(t=>t.includes('战利品已自动收集')),naturalDifficultyMeasured:false};
const outputIndex=process.argv.indexOf('--output'),output=outputIndex<0?'test-results/cultivation-level-gates/rules.json':process.argv[outputIndex+1];
mkdirSync(dirname(output),{recursive:true});writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
