/** Production-rule combat evidence in a flat, unobstructed arena.
 * npx tsx tools/encounter-balance.ts --output test-results/encounter-balance.json
 * Optional --levels 1,6,10,11,16,20 --families WAR,BOW,FIR,THU --gear bare,normal,developed
 *          --roles normal,pack,elite,boss --seeds 3 --seconds 120 --mode both|fight|exposure|attack
 * Design only: --target dummy --equipment-policy lifecycle-full
 *              --preparation-gold 100000 --preparation-iron 9999 --gems balanced
 * Gear ownership/initial currency are fixtures, not proof of natural acquisition.
 */
import {writeFileSync} from 'node:fs';
import {GameSession,type EnemyState} from '../assets/scripts/core/GameSession';
import {AREAS} from '../assets/scripts/features/world/data/WorldData';
import {Automation,type AutomationStep} from '../assets/scripts/features/automation/common/Automation';
import {COMBAT_LOADOUTS,activateCombatLoadout,type CombatFamily} from '../assets/scripts/features/progression/common/CombatLoadouts';
import {awardXp,cumulativeXp,type Attribute} from '../assets/scripts/features/progression/common/Progression';
import {COMBAT_SKILLS} from '../assets/scripts/features/combat/data/PureSkills';
import {EQUIPMENT} from '../assets/scripts/features/equipment/data/Equipment';
import {artifactWeaponForStyle,growingStats} from '../assets/scripts/features/equipment/data/GrowingEquipment';
import {LIFECYCLE_ITEMS,lifecyclePhase} from '../assets/scripts/features/equipment/data/EquipmentLifecycle';
import {forgingStage,itemForgingView} from '../assets/scripts/features/crafting/common/EquipmentForging';
import {gemTierCap,gemCapacity,gemUnits,gemBankKey,type GemStat} from '../assets/scripts/features/gems/data/Gems';
import {equippedGearBonus} from '../assets/scripts/features/equipment/common/EquipmentDice';
import {synchronizeResource} from '../assets/scripts/features/combat/common/ClassResource';
import {BUILD_PROFILE} from '../assets/scripts/shared/BuildProfile';
import {enemyContentHealth} from '../assets/scripts/features/combat/data/EnemyBalance';
import {CAMPAIGN_MAX_LEVEL,attributePointBudget,skillPointBudget,combatBudgetLevel} from '../assets/scripts/features/progression/data/CampaignProgression';
import {forgingLevelCap,FORGING_RANK_LEVELS} from '../assets/scripts/features/crafting/data/EquipmentForging';
import {gemSocketCapForLevel} from '../assets/scripts/features/gems/data/Gems';
import {materialStock} from '../assets/scripts/features/crafting/common/CultivationRewards';
import {equipmentGrowthPlan} from '../assets/scripts/features/equipment/data/CampaignEquipmentGrowth';
import {JOURNEY_CHAPTERS} from '../assets/scripts/features/journey/data/ChapterJourney';
import type {AreaDef,EnemySpawn,InputFrame,WorldQuery} from '../assets/scripts/core/Contracts';

const args=process.argv.slice(2),option=(key:string,fallback:string)=>{const n=args.indexOf('--'+key);return n<0?fallback:args[n+1];};
const levels=option('levels','1,6,10,11,16,20').split(',').map(Number);
const families=option('families','WAR,BOW,FIR,THU').split(',') as CombatFamily[];
type Gear='bare'|'normal'|'developed';type Role='normal'|'pack'|'elite'|'boss';type Behavior='fight'|'exposure'|'attack';
const gears=option('gear','bare,normal,developed').split(',') as Gear[],roles=option('roles','normal,pack,elite,boss').split(',') as Role[];
const seeds=Number(option('seeds','3')),limit=Number(option('seconds','120')),dt=.04,mode=option('mode','both');
const equipmentPolicy=option('equipment-policy','released'),targetMode=option('target','content'),dummyTarget=targetMode==='dummy',plannedBossTarget=targetMode==='planned-boss',lifecycleEquipment=equipmentPolicy.startsWith('lifecycle'),gemProfile=option('gems','none'),dummyRotation=option('dummy-rotation','auto');
const preparationGoldBudget=Number(option('preparation-gold','9999')),preparationIron=Number(option('preparation-iron','500'));
const plannedPhaseCaps=args.includes('--planned-phase-caps');
if(levels.some(level=>!Number.isInteger(level)||level<1||level>CAMPAIGN_MAX_LEVEL))throw new Error(`Balance levels must be integers from1 to${CAMPAIGN_MAX_LEVEL}`);
if(plannedPhaseCaps){
 throw new Error('--planned-phase-caps is obsolete: native character-level cultivation gates are authoritative');
}
if(BUILD_PROFILE.noSkillCooldown||BUILD_PROFILE.monsterExperienceMultiplier!==1)throw new Error('Use normal test rules');
if(levels.some(n=>!Number.isInteger(n)||n<1||n>CAMPAIGN_MAX_LEVEL)||!Number.isInteger(seeds)||seeds<1||!Number.isFinite(limit)||limit<=0)throw new Error('Invalid numerical options');
if(!Number.isInteger(preparationGoldBudget)||preparationGoldBudget<0||preparationGoldBudget>1000000||!Number.isInteger(preparationIron)||preparationIron<0||preparationIron>9999)throw new Error('Invalid finite preparation budget');
const world:WorldQuery={move:(p,d)=>dummyTarget&&'kind' in p?{x:p.x,z:p.z}:({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0,path:(a,b)=>[{x:a.x,z:a.z},{x:b.x,z:b.z}]};
const empty:AreaDef={id:'BALANCE',name:'Offline balance arena',subtitle:'',kind:'wild',palette:'meadow',width:120,depth:120,spawn:{x:0,z:0},atlas:{x:0,z:0},exits:[],objects:[],buildings:[],obstacles:[],enemies:[],checkpoint:true};
const candidates=Object.values(AREAS).flatMap(area=>area.enemies.map(enemy=>({area:area.id,enemy})));
const preparationEvidence=new WeakMap<GameSession,{goldBudget:number;goldSpent:number;goldReserve:number;walletRemaining:number;ironBudget:number;ironSpent:number;drillsSpent:number;crystalUnitsSpent:number;blocked:Record<string,unknown>[]} >();
function roster(level:number,role:Role){
 if(dummyTarget)return {area:'DESIGN_DUMMY',spawns:[{id:'design-dummy',kind:'raider' as const,level,hp:100000000,trainingDummy:true,x:0,z:2.5}]};
 if(plannedBossTarget)return {area:'DESIGN_BOSS_R2_REFERENCE',spawns:[{id:'design-boss-reference',kind:'captain' as const,templateId:'BOSS_R2',bossId:'BOSS_R2',level:lifecyclePhase(level).bossContentLevel,x:0,z:2.5}]};
 const pool=candidates.filter(({area,enemy:e})=>{
  if(level<=20&&!/^(S\d|H\d|U1-)/.test(area))return false;
  const l=e.level??1;if(l>level)return false;
  if(role==='boss')return /^BOSS_R/.test(e.bossId??'');
  if(role==='elite')return !!e.templateId?.includes('ALPHA')||/^ELITE_/.test(e.bossId??'');
  return !e.bossId&&!e.templateId?.includes('ALPHA')&&!!e.packId;
 }).sort((a,b)=>(b.enemy.level??1)-(a.enemy.level??1)||a.area.localeCompare(b.area)||a.enemy.id.localeCompare(b.enemy.id));
 const chosen=pool[0];if(!chosen)return null;
 const selected=role==='pack'?candidates.filter(e=>e.area===chosen.area&&e.enemy.packId===chosen.enemy.packId):[chosen];
 return {area:chosen.area,spawns:selected.map(({enemy:e})=>({...e,x:e.x-chosen.enemy.x,z:e.z-chosen.enemy.z+2.5,respawnSeconds:undefined}))};
}
function prepare(family:CombatFamily,level:number,gear:Gear,seed:number){
 const game=new GameSession(seed,world),s=game.state,p=s.progression;game.enter({...empty,id:'BALANCE_PREP'});
 if(level>1)awardXp(p,'balance-fixture-level',cumulativeXp(level));
 const attributes={strength:10,dexterity:10,intellect:10,vitality:10};
 const attr:Attribute=family==='WAR'?'strength':family==='BOW'?'dexterity':'intellect',points=attributePointBudget(level),offence=Math.min(70,Math.floor(points*2/3));
 attributes[attr]+=offence;let unallocated=points-offence;
 for(const key of ['vitality','dexterity','strength','intellect'] as const){const take=Math.min(80-attributes[key],unallocated);attributes[key]+=take;unallocated-=take;}
 if(unallocated||Object.values(attributes).some(value=>value>80))throw new Error('Attribute fixture exceeds the shared legal budget');
 p.ultimateGiftClaimed=level>=11;
 if(!game.applyAttributePlan(attributes,game.attributePlanToken()))throw new Error('Legal attribute plan rejected');
 activateCombatLoadout(s.combat,p);game.applyCombatLoadout(family,COMBAT_LOADOUTS[family].weapon);
 // Legal, identical priority policy: primary, ultimate, passives, ordinary kit.
 const kit=COMBAT_LOADOUTS[family],priority=[family+'_01',kit.ultimate,family+'_P1',kit.activeSlots[1],kit.activeSlots[3],family+'_P2',kit.activeSlots[2],...Object.keys(p.learned).filter(id=>COMBAT_SKILLS[id]?.style===family&&COMBAT_SKILLS[id].activation==='automatic')];
 let remaining=skillPointBudget(level,p.secondChapter);const plan={...p.learned};
 for(const id of priority){if(!id||!plan[id])continue;while(plan[id]<5&&remaining>=plan[id]){remaining-=plan[id];plan[id]++;}}
 if(!game.applySkillPlan(plan))throw new Error('Legal skill plan rejected');
 for(const slot of ['offhand','head','chest','hands','feet','ringLeft','ringRight','necklace'] as const)s.equipment[slot]=null;
 if(gear!=='bare'){
  let weapon=gear==='developed'?artifactWeaponForStyle[family]:level>=16?`CJ2_HUNT_${family}`:level>=6?`CJ1_HUNT_${family}`:kit.weapon;
  const items=level<3?[]:['A01','A06','A09','A13','J03','J08'];
  if(gear==='developed'&&level>=8){items.splice(items.indexOf('J03'),1,'LC1_T_L');items.splice(items.indexOf('J08'),1,'LC1_B_L');}
  if(level>=14)items.splice(items.indexOf('A09'),1,'LC2_T_E');
  if(lifecycleEquipment&&level>=21){
   const chapter=lifecyclePhase(level).chapter,pool=LIFECYCLE_ITEMS.filter(i=>(i.chapter??99)<=chapter&&(i.requiredLevel??99)<=level);
   if(gear==='normal')weapon=pool.filter(i=>i.slot==='weapon'&&i.quality==='史诗'&&i.id.endsWith('_'+family)).sort((a,b)=>(b.requiredLevel??0)-(a.requiredLevel??0)||(b.power??0)-(a.power??0))[0]?.id??weapon;
   const slots=equipmentPolicy==='lifecycle-full'?['head','chest','hands','feet','ringLeft','necklace','offhand'] as const:['chest','hands','ringLeft','necklace'] as const;
   for(const slot of slots){
    if(slot==='offhand'&&(family!=='WAR'||EQUIPMENT[weapon].twoHanded))continue;
    const replacement=pool.filter(i=>i.slot===slot&&(equipmentPolicy==='lifecycle-full'||gear==='developed'||i.quality==='史诗')).sort((a,b)=>(b.requiredLevel??0)-(a.requiredLevel??0)||(b.quality==='传奇'?1:0)-(a.quality==='传奇'?1:0))[0];
    if(replacement){const index=items.findIndex(id=>EQUIPMENT[id]?.slot===slot);if(index>=0)items.splice(index,1,replacement.id);else items.push(replacement.id);}
   }
  }
  for(const id of [weapon,...items]){const item=EQUIPMENT[id];if(!item||(item.requiredLevel??1)>level)continue;s.inventory[id]=1;s.provenance[id]='balance-fixture';if(!game.equip(id))throw new Error('Fixture equipment rejected: '+id);}
  if(level>=6){
   const blocked:Record<string,unknown>[]=[];
   const hasGemFixture=gear==='developed'&&gemProfile!=='none',plan=equipmentGrowthPlan(lifecyclePhase(level).chapter)!;
   s.player.gold=Math.min(9999,preparationGoldBudget);s.player.iron=preparationIron;
   let goldReserve=preparationGoldBudget-s.player.gold;
   const fundWallet=()=>{const transfer=Math.min(9999-s.player.gold,goldReserve);s.player.gold+=transfer;goldReserve-=transfer;};
   for(const id of Object.values(s.equipment).filter((id):id is string=>typeof id==='string'))for(let n=0;n<FORGING_RANK_LEVELS.length;n++){
    let q=game.forging.enhancement(id);const targetRank=gear==='developed'?(q.view?.cap??0):EQUIPMENT[id].slot==='weapon'?plan.target.mainWeaponRank:plan.target.otherSlotRank;
    if((q.view?.rank??0)>=targetRank)break;
    if(q.step&&q.step.gold>s.player.gold){fundWallet();q=game.forging.enhancement(id);}
    if(!q.allowed){blocked.push({kind:'enhance',id,reason:q.reason,rank:q.view?.rank,targetRank,levelCap:forgingLevelCap(level),itemCap:q.view?.cap,materialTier:q.materialTier,required:q.materialCount,owned:q.materialOwned});break;}
    if(!game.forging.enhance(id,q.token))throw new Error('Enhancement rejected');
   }
   if(hasGemFixture){
    const tier=gemTierCap(s);s.gems.drills=500;
    for(const stat of ['power','criticalChance','criticalDamage','maxHp','armor'] as GemStat[])s.gems.bank[gemBankKey(stat,tier)]=500;
    for(const id of Object.values(s.equipment).filter((id):id is string=>typeof id==='string'))for(let hole=0;hole<Math.min(gemCapacity(EQUIPMENT[id]),gemSocketCapForLevel(level));hole++){
     fundWallet();
     if(hole>0){const open=game.gems.open(id,hole);if(!open.allowed){blocked.push({kind:'gem-open',id,hole,reason:open.reason});break;}if(!game.gems.openSocket(id,hole,open.token))throw new Error('Quoted socket opening rejected');}
     const balanced:GemStat[]=['power','criticalChance','criticalDamage','maxHp','armor'],stat=gemProfile==='power'?'power':balanced[hole%balanced.length],quote=game.gems.inset(id,hole,stat,tier);
     if(!quote.allowed){blocked.push({kind:'gem-inlay',id,hole,tier,reason:quote.reason});break;}if(!game.gems.inlay(id,hole,stat,tier,quote.token))throw new Error('Quoted gem fixture rejected: '+id+'/'+hole);
    }
   }
   preparationEvidence.set(game,{goldBudget:preparationGoldBudget,goldSpent:preparationGoldBudget-goldReserve-s.player.gold,goldReserve,walletRemaining:s.player.gold,ironBudget:preparationIron,ironSpent:preparationIron-s.player.iron,drillsSpent:hasGemFixture?500-s.gems.drills:0,crystalUnitsSpent:hasGemFixture?2500-Object.values(s.gems.bank).reduce((n,value)=>n+value,0):0,blocked});
  }
 }
 // Full health/resource is established once before combat, never replenished.
 s.player.hp=s.player.maxHp;synchronizeResource(s);s.player.focus=s.player.maxFocus;
 return game;
}
type CombatPilot={evade(game:GameSession,world:WorldQuery):AutomationStep|null;fight(game:GameSession,world:WorldQuery,dt:number,scope:'clear'):AutomationStep|null};
function run(family:CombatFamily,level:number,gear:Gear,role:Role,seed:number,behavior:Behavior){
 const selected=roster(level,role);if(!selected)return null;
 const game=prepare(family,level,gear,seed),s=game.state,pilot=new Automation() as unknown as CombatPilot;
 game.enter({...empty,enemies:selected.spawns});
 if(!s.enemies.length)throw new Error('Fixture did not spawn enemies');
 if(plannedBossTarget){
  // Explicit future-design fixture: real existing BOSS_R2 behavior, with HP
  // taken from the shared phase budget. No future boss moves are invented.
  const phase=lifecyclePhase(level),hp=enemyContentHealth({kind:'captain',level:phase.bossContentLevel,bossId:'BOSS_R'+phase.chapter});
  for(const enemy of s.enemies){enemy.maxHp=hp;enemy.hp=hp;}
 }
 const view=game.progressionView(),initial={maximumCharacterLevel:CAMPAIGN_MAX_LEVEL,combatBudgetLevel:combatBudgetLevel(level),attributePointBudget:attributePointBudget(level),skillPointBudget:skillPointBudget(level,s.progression.secondChapter),maxHp:s.player.maxHp,focus:s.player.maxFocus,equipment:{...s.equipment},preparation:preparationEvidence.get(game),cultivation:{rankCap:forgingLevelCap(level),socketCap:gemSocketCapForLevel(level),stones:Object.fromEntries([1,2,3,4,5].map(tier=>[tier,materialStock(s,tier)])),intendedGear:gear,normalTargets:gear==='normal'?equipmentGrowthPlan(lifecyclePhase(level).chapter)?.target:undefined,unformed:!!preparationEvidence.get(game)?.blocked.length,gemStockPolicy:gear!=='developed'||gemProfile==='none'?'none':'finite declared bank/drill fixture; not natural acquisition evidence'},weaponStrength:EQUIPMENT[s.equipment.weapon]?.power??growingStats(s.equipment.weapon,level).power,forgingStage:forgingStage(s),forgingRanks:Object.fromEntries(Object.values(s.equipment).filter((id):id is string=>typeof id==='string').map(id=>[id,itemForgingView(s,id)?.rank??0])),gemTierCap:gemTierCap(s),gemSockets:s.gems.items,gearBonuses:equippedGearBonus(s),criticalChance:view.criticalChance,criticalDamage:view.criticalDamage,effectiveAttributes:view.attributes,attributes:{...s.progression.attributes},skillPointsRemaining:s.progression.skillPoints,learned:Object.fromEntries(Object.entries(s.progression.learned).filter(([id,r])=>r>0&&COMBAT_SKILLS[id].style===family))};
 const enemies=s.enemies.map(e=>({id:e.id,level:e.level,maxHp:e.maxHp,templateId:e.templateId,bossId:e.bossId}));
 let outgoing=0,incoming=0,healing=0,hits=0,critical=0,misses=0,enemyHits=0,healthPotions=0,resourcePotions=0,minimumResource=s.player.focus;
 const releases:Record<string,number>={},damageBySource:Record<string,number>={},hitsBySource:Record<string,number>={},deathTimes:Record<string,number>={};
 for(let frame=0;frame<Math.ceil(limit/dt)&&s.status!=='dead'&&s.enemies.some(e=>e.hp>0);frame++){
  if(dummyTarget)s.combat.engagement={area:s.area,enemyIds:s.enemies.map(e=>e.id)};
  let input:InputFrame={x:0,z:0};
  if(behavior!=='exposure'){
   if(!s.action&&s.player.hp/s.player.maxHp<=.45&&s.player.healthPotions>0&&!(s.cooldowns.consumable>0))game.useConsumable('health');
   input=((behavior==='fight'?pilot.evade(game,world):null)??pilot.fight(game,world,dt,'clear'))?.input??input;
   if(behavior==='attack')input={...input,x:0,z:0,dash:false};
   // A real release at a sword beat boundary exposes the normal skill-choice
   // gap. Without it, continuous auto-chain can starve skills on passive dummies.
   if(dummyTarget&&dummyRotation==='release'&&s.action?.kind==='sword'&&s.action.elapsed+dt>=s.action.duration-1e-8)input.attack=false;
  }
  const events=game.advance(dt,input);minimumResource=Math.min(minimumResource,s.player.focus);
  for(const e of events){
   if(e.type==='hit'){const damage=Number(e.hpLost??0),source=String(e.skillId??e.source);outgoing+=damage;damageBySource[source]=(damageBySource[source]??0)+damage;hitsBySource[source]=(hitsBySource[source]??0)+1;hits++;if(e.critical===true)critical++;}
   if(e.type==='miss')misses++;
   if(e.type==='hurt'){incoming+=Number(e.value??0);enemyHits++;}
   if(e.type==='heal')healing+=Number(e.value??0);
   if(e.type==='consumable'){if(e.health===true)healthPotions++;else resourcePotions++;}
   if(e.type==='skill_release'){const id=String(e.skillId);releases[id]=(releases[id]??0)+1;}
  }
  for(const enemy of s.enemies)if(enemy.hp<=0&&deathTimes[enemy.id]===undefined)deathTimes[enemy.id]=+s.time.toFixed(2);
 }
 const victory=s.enemies.every(e=>e.hp<=0),died=s.status==='dead';
 return {family,level,gear,role,seed,mode:behavior,sourceArea:selected.area,simulation:plannedBossTarget?{behaviorTemplate:'BOSS_R2',healthBudgetChapter:lifecyclePhase(level).chapter,futureBossContentImplemented:false}:undefined,enemyLevel:enemies[0]?.level,enemyCount:enemies.length,enemyHp:enemies.reduce((n,e)=>n+e.maxHp,0),outcome:dummyTarget?'measurement':victory?'victory':died?'dead':'timeout',seconds:+s.time.toFixed(2),dps:+(outgoing/s.time).toFixed(2),hpRemaining:+s.player.hp.toFixed(2),hpFraction:+(s.player.hp/s.player.maxHp).toFixed(3),outgoing,incoming,healing,hits,critical,misses,enemyHits,healthPotions,resourcePotions,minimumResource:+minimumResource.toFixed(2),remainingEnemyHp:s.enemies.reduce((n,e)=>n+e.hp,0),releases,damageBySource,hitsBySource,deathTimes,initial,enemies};
}
const rows=[];
for(const level of levels)for(const role of roles)for(const family of families)for(const gear of gears)for(let seed=0;seed<seeds;seed++)for(const behavior of mode==='both'?['fight','exposure'] as const:[mode as Behavior]){
 const row=run(family,level,gear,role,73014+seed*7919,behavior);if(row)rows.push(row);
}
const groups=new Map<string,typeof rows>();for(const row of rows){const key=[row.level,row.role,row.family,row.gear,row.mode].join('/');groups.set(key,[...groups.get(key)??[],row]);}
const summary=[...groups].map(([key,runs])=>({case:key,victories:runs.filter(r=>r.outcome==='victory').length,deaths:runs.filter(r=>r.outcome==='dead').length,seconds:+(runs.reduce((n,r)=>n+r.seconds,0)/runs.length).toFixed(2),dps:+(runs.reduce((n,r)=>n+r.dps,0)/runs.length).toFixed(2),hpPercent:+(runs.reduce((n,r)=>n+r.hpFraction*100,0)/runs.length).toFixed(1),enemyHp:runs[0].enemyHp,outgoing:+(runs.reduce((n,r)=>n+r.outgoing,0)/runs.length).toFixed(1),incoming:+(runs.reduce((n,r)=>n+r.incoming,0)/runs.length).toFixed(1)}));
const report={scope:'Real GameSession spawn, damage, critical, accuracy, resource, enemy AI and production Automation evade/fight commands. Same legal level/attribute/skill allocation for each gear comparison. No manual health/resource reset during combat; finite native potions. Flat unobstructed arena isolates encounter stats; enemy templates, authored levels, pack spacing and grouping preserved. Gear ownership and initial forging/gem money/materials are fixtures, not natural acquisition/economy proof. Developed is a requested growth-artifact/cultivation profile. Native actual ranks and preparation.blocked determine whether it formed; missing earned stones are never injected. Gems use a finite declared bank only when explicitly requested and obey native level/tier/socket gates. Exposure is idle without attacks, skills, evasions, healing or potions. Attack disables walking, dodge input and automatic evasion, retaining normal production skill/support choices and finite potions; authored rush/retreat skill displacement still runs. Dummy mode uses one declared immovable 100,000,000 HP practice target, forced combat regeneration and finite resource potions; it proves output only, never future content or boss difficulty. Planned-boss mode uses the existing BOSS_R2 attack/movement/guard template with the official content-level health budget for the selected phase; this is an explicit design fixture, never an authored future boss or future map. Optional dummy release rotation releases the sword attack button at a beat boundary to allow the production controller its normal skill decision. Lifecycle equipment policy grants declared future ownership fixtures; production level requirements, forging stage and gem-tier caps are still authoritative. Lifecycle-full additionally replaces future head/feet and equips an eligible WAR single-hand offhand; two-handed weapons never gain an offhand. Native character-level gates are authoritative. The obsolete --planned-phase-caps flag is rejected; no chapter release or secondChapter override supplies cultivation access. Source files, map availability and running browsers are untouched. Content above level 20 can be unpublished; this is not campaign reachability/device acceptance.',maximumCharacterLevel:CAMPAIGN_MAX_LEVEL,target:dummyTarget?'design-dummy':plannedBossTarget?'planned-boss-template':'content',equipmentPolicy:lifecycleEquipment?'future-'+equipmentPolicy+'-fixture':'released',plannedPhaseCaps,journeyAvailability:JOURNEY_CHAPTERS.map(chapter=>({chapter:chapter.id,available:chapter.available})),gemProfile,dummyRotation,preparationGoldBudget,preparationIron,dt,limit,seeds,summary,rows};
const output=option('output','');if(output)writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.table(summary);
