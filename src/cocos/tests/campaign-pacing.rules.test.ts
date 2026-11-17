import test from 'node:test';
import assert from 'node:assert/strict';
import {GameSession} from '../assets/scripts/core/GameSession';
import type {AreaDef,WorldQuery} from '../assets/scripts/core/Contracts';
import {AREAS} from '../assets/scripts/features/world/data/WorldData';
import {CAMPAIGN_CHAPTER_BUDGETS,CAMPAIGN_PACING} from '../assets/scripts/features/progression/data/CampaignProgression';
import {campaignExperienceQuote,campaignExperienceSources,campaignExperienceView,campaignStageExperienceView,validateCampaignExperienceReceipts} from '../assets/scripts/features/progression/data/CampaignExperience';
import {CAMPAIGN_STAGES} from '../assets/scripts/features/journey/data/CampaignStages';
import {cumulativeXp} from '../assets/scripts/features/progression/common/Progression';
import {campaignSourceMaterials} from '../assets/scripts/features/progression/common/CampaignRewards';
import {CAMPAIGN_EVENTS} from '../assets/scripts/features/campaign/data/CampaignEvents';
import {H03_EQUIPMENT_OPTIONS} from '../assets/scripts/features/equipment/data/Equipment';
import {REGIONAL_LOOT_POOLS} from '../assets/scripts/features/campaign/data/CampaignLoot';

const world:WorldQuery={move:(from,delta)=>({x:from.x+delta.x,z:from.z+delta.z}),visible:()=>true,height:()=>0};
const purse=(game:GameSession)=>({xp:game.state.progression.totalXp,gold:game.state.player.gold,iron:game.state.player.iron,runes:game.state.player.runes,cores:game.state.player.cores});

test('registered main stages cover chapter growth while exploration adds an optional reward pool',()=>{
 assert.equal(CAMPAIGN_PACING.chapterActiveDays.reduce((n,days)=>n+days,0),CAMPAIGN_PACING.activeDays);
 for(const chapter of [1,2]){
  const view=campaignExperienceView(chapter)!,budget=CAMPAIGN_CHAPTER_BUDGETS[chapter-1];
  assert.equal(view.main.availableXp,budget.experience.mainXp);
  assert.equal(view.exploration.availableXp,budget.experience.uniqueExplorationXp);
  assert.equal(view.main.availableXp+view.exploration.availableXp,budget.experience.requiredXp+budget.experience.uniqueExplorationXp);
  let previous=budget.experience.entryTotalXp;
  for(const stage of CAMPAIGN_STAGES.filter(stage=>stage.chapter===chapter)){
   const actual=campaignStageExperienceView(stage.id)!;
   assert.equal(actual.budgetXp,stage.targetTotalXp-previous,stage.id);
   assert.equal(actual.nodeXp+actual.completionXp,actual.budgetXp,stage.id);
   previous=stage.targetTotalXp;
  }
  assert.equal(previous,budget.experience.exitTotalXp);
 }
 assert.ok(campaignStageExperienceView('c1-exit')!.targetTotalXp>=cumulativeXp(10));
 assert.ok(campaignStageExperienceView('c2-pressure')!.targetTotalXp>=cumulativeXp(20));
 const branch=campaignStageExperienceView('c2-evidence')!;assert.equal(branch.sources.length,1);assert.equal(branch.completionXp,branch.budgetXp);assert.equal(branch.nodeXp,0);
 for(const id of ['c2-witness-safe','c2-ledger-safe'])assert.equal(campaignExperienceQuote('campaign:'+id).amount,0);
 for(const source of ['M8_XP_1','campaign:u108-exit-check','campaign:dg-dawn-return','campaign:field-bell-return'])assert.equal(campaignExperienceQuote(source).registered,false,source);
 for(const chapter of [3,4,5,6,7,8])assert.equal(campaignExperienceSources(chapter).length,0);
});

test('a real inspect pays once through re-entry, snapshot restore, next day and clock rollback',()=>{
 let now=Date.UTC(2026,10,17,4),game=new GameSession(73014,world,()=>now);
 const area=AREAS['S01-T1'],object=area.objects.find(object=>object.id==='t1-guestbook')!;
 assert.ok(object);game.enter(area,{x:object.x,z:object.z});
 const source=`explore:${area.id}:${object.id}`,quote=campaignExperienceQuote(source),materials=campaignSourceMaterials(source),before=purse(game);
 assert.equal(quote.registered,true);game.interact(object);
 const paid=purse(game);assert.equal(paid.xp-before.xp,quote.amount);
 for(const key of ['gold','iron','runes','cores'] as const)assert.equal(paid[key]-before[key],materials[key]);
 for(const shift of [0,86400000,-172800000]){
  now+=shift;game.enter(area,{x:object.x,z:object.z});game.interact(object);
  game=GameSession.restore(game.snapshot(),world,()=>now);game.enter(area,{x:object.x,z:object.z});game.advance(.01,{x:0,z:0});game.interact(object);
  assert.deepEqual(purse(game),paid);
 }
 assert.equal(game.state.progression.xpReceipts[source],quote.amount);
});

test('a real cache has a durable exploration proof and rejects forged amounts or unknown exploration IDs',()=>{
 let game=new GameSession(73014,world),area=AREAS['S01-T3'],object=area.objects.find(object=>object.id==='find-j08')!;
 assert.ok(object);game.enter(area,{x:object.x,z:object.z});
 const source=`explore:${area.id}:${object.id}`,quote=campaignExperienceQuote(source),before=game.state.progression.totalXp;
 game.interact(object);assert.equal(game.state.progression.totalXp-before,quote.amount);
 assert.equal(game.state.receipts[`interaction:${area.id}:${object.id}`],true);
 const paid=purse(game);game.interact(object);assert.deepEqual(purse(game),paid);
 game=GameSession.restore(game.snapshot(),world);game.enter(area,{x:object.x,z:object.z});game.interact(object);assert.deepEqual(purse(game),paid);
 const receipts=game.state.progression.xpReceipts,proofs=game.state.receipts;
 assert.throws(()=>validateCampaignExperienceReceipts({...receipts,[source]:quote.amount+1},proofs),/章节经验/);
 assert.throws(()=>validateCampaignExperienceReceipts({...receipts,'explore:S01-T3:unbuilt-cache':1},proofs),/探索经验/);
});


test('existing campaign events award former crafted equipment once and the two safety routes share one weapon',()=>{
 // Controlled cleared-event fixtures include planning areas, not a playable future route.
 const game=new GameSession(73014,world);
 const perform=(id:string,choice?:string)=>{
  const def=CAMPAIGN_EVENTS[id],object=AREAS[def.area].objects.find(object=>object.action==='campaign_event'&&object.eventId===id)!;
  assert.ok(object,id);for(const flag of def.requires??[])game.state.flags[flag]=true;
  if(id==='m3-heat-test')game.state.flags['campaign:battle:workshop-defense:complete']=true;
  const cleared:AreaDef={...AREAS[def.area],enemies:[],objects:[object]};game.enter(cleared,{x:object.x,z:object.z});
  assert.equal(game.campaignEventAvailability(id).available,true,id);game.interact(object);
  if(choice)game.choose('equipment:'+choice);
  assert.equal(game.state.receipts['campaign:'+id],true,id);
 };
 perform('m3-heat-test','W04');assert.equal(game.state.inventory.W04,1);assert.equal(game.state.provenance.W04,'campaign:m3-heat-test');
 for(const id of H03_EQUIPMENT_OPTIONS.filter(id=>id!=='W04'))assert.equal(game.state.inventory[id],undefined,'one trial cannot directly grant the whole set');
 assert.deepEqual(CAMPAIGN_EVENTS['m3-heat-test'].choiceItems,[...H03_EQUIPMENT_OPTIONS]);
 assert.deepEqual(REGIONAL_LOOT_POOLS.R2.filter(p=>H03_EQUIPMENT_OPTIONS.includes(p.id as typeof H03_EQUIPMENT_OPTIONS[number])).map(p=>p.id),[...H03_EQUIPMENT_OPTIONS]);
 perform('u204-recipe');assert.equal(game.state.inventory.J04,1);assert.equal(game.state.provenance.J04,'campaign:u204-recipe');
 game.interact(AREAS['U2-04'].objects.find(o=>o.eventId==='u204-recipe')!);assert.equal(game.state.inventory.J04,1);
 perform('m5-archive','DR3-01');assert.equal(game.state.inventory.A16,1);assert.equal(game.state.provenance.A16,'campaign:m5-archive');
 perform('f04-safety');assert.equal(game.state.inventory.W05,1);const firstSource=game.state.provenance.W05,firstPurse=purse(game);
 perform('f07-safety');assert.equal(game.state.inventory.W05,1);assert.equal(game.state.provenance.W05,firstSource);assert.deepEqual(purse(game),firstPurse);
 assert.equal(game.state.receipts['campaign:f04-safety'],true);assert.equal(game.state.receipts['campaign:f07-safety'],true);
 const restored=GameSession.restore(game.snapshot(),world);assert.equal(restored.state.inventory.W05,1);assert.equal(restored.state.inventory.J04,1);assert.equal(restored.state.inventory.A16,1);
});

test('native highland death and respawn settlements can collect every unchosen H03 equipment option',()=>{
 // Actual reward settlements with controlled enemy health; no item grants or loot rerolls.
 const game=new GameSession(73014,world),scene:AreaDef={...AREAS.H04,objects:[],obstacles:[]};
 game.enter(scene);const targetId=game.state.enemies.find(enemy=>enemy.respawnSeconds)!.id,collected=new Set<string>();
 for(const enemy of game.state.enemies)if(enemy.id!==targetId)enemy.hp=0;
 for(let cycle=0;cycle<1500&&collected.size<H03_EQUIPMENT_OPTIONS.length;cycle++){
  let enemy=game.state.enemies.find(enemy=>enemy.id===targetId)!;
  if(enemy.hp<=0){game.state.time=Math.max(game.state.time,enemy.respawnAt??0)+1;game.state.player.x=scene.width/2-2;game.state.player.z=scene.depth/2-2;game.advance(.02,{x:0,z:0});enemy=game.state.enemies.find(enemy=>enemy.id===targetId)!;}
  assert.ok(enemy.hp>0);enemy.hp=0;game.advance(.02,{x:0,z:0});
  for(const drop of [...game.state.groundLoot])if(H03_EQUIPMENT_OPTIONS.includes(drop.item as typeof H03_EQUIPMENT_OPTIONS[number])){
   game.state.player.x=drop.x;game.state.player.z=drop.z;assert.ok(game.pickupLoot(drop.id).some(event=>event.type==='item'&&event.id===drop.item));collected.add(drop.item);
  }
 }
 assert.deepEqual([...collected].sort(),[...H03_EQUIPMENT_OPTIONS].sort());
 for(const id of collected){assert.ok(game.state.inventory[id]);assert.match(game.state.provenance[id],/^regional:hunt:H04:/);}
 GameSession.restore(game.snapshot(),world);
});
