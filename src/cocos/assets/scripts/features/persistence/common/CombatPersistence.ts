import {playerCombatAttributes,validateContactSnapshots} from '../../combat/common/CombatAccuracy';
import {resourceMaximum} from '../../combat/common/ClassResource';
import type {GameState} from '../../../core/GameSession';
import {EQUIPMENT,MERCHANTS,RECIPES,equipmentStackLimit,ITEM_STACK_LIMIT} from '../../equipment/data/Equipment';
import {SUPPLIES,isSupplyId,SUPPLY_LOOT_POLICY,supplyDrop} from '../../equipment/data/Supplies';
import {PURE_SKILLS,LEGACY_COMBAT_SKILLS,combatSkillCatalog} from '../../combat/data/PureSkills';
import {validateProgression,baseMaxHp,allocatedSkillRank} from '../../progression/common/Progression';
import {validateCombat} from '../../combat/common/PureCombat';
import {validateDiceSnapshot} from './CheckPersistence';
import {validEquipmentUpgrade,validateEquipmentOwnership,itemGearBonus} from '../../equipment/common/EquipmentDice';
import {CAMPAIGN_EVENTS} from '../../campaign/data/CampaignEvents';
import {ELITE_LOOT} from '../../campaign/data/CampaignLoot';
import {GROWING_EQUIPMENT,growingStats} from '../../equipment/data/GrowingEquipment';
import {validGrowingSource,validGrowingDropSource,validateGrowingProgress} from '../../equipment/common/GrowingEquipmentLoot';
import {validJourneyItem,validLifecycleTaskItem,validateJourneyProgress} from '../../journey/common/ChapterJourney';
import {validBossEquipmentSource,validateBossLoot} from '../../equipment/common/BossLoot';
import {validateEnemyCombat,validateEnemyHazards,validateEnemyProjectile} from '../../combat/common/EnemyCombat';
import {validateForging,itemForgingBonus} from '../../crafting/common/EquipmentForging';
import {validateHuntingExperience} from '../../progression/common/HuntingExperience';

const record=(v:unknown):v is Record<string,any>=>!!v&&typeof v==='object'&&!Array.isArray(v)&&Object.getPrototypeOf(v)===Object.prototype;
const number=(v:unknown,min=0,max=1e10):v is number=>typeof v==='number'&&Number.isFinite(v)&&v>=min&&v<=max;
const integer=(v:unknown,min=0,max=1e10)=>number(v,min,max)&&Number.isInteger(v);
const point=(v:any)=>record(v)&&number(v.x,-5000,5000)&&number(v.z,-5000,5000);
const area=(id:unknown)=>typeof id==='string'&&/^(S(0[1-9]|1\d|20)|S01-T[1-6]|T[1-6]|H(0[1-9]|1\d|20)|B(0[1-9]|1\d|20)|F(0[1-9]|1\d|20)|U1-(0[1-9]|10)|U2-0[1-9])$/.test(id);
const strings=(v:unknown,max=20000)=>Array.isArray(v)&&v.length<=max&&v.every(k=>typeof k==='string'&&k.length<200);
/** Run only on a validated copy. Historical roll proofs stay intact; retired items do not resume. */
export function migrateRemovedOil(s:GameState):boolean {
 const changed=Object.prototype.hasOwnProperty.call(s.player,'oil')||Object.prototype.hasOwnProperty.call(s.cooldowns,'oil')||!!s.groundLoot?.some(d=>d.item==='SUPPLY_OIL')||s.action?.kind==='oil'||s.projectiles.some(p=>p.kind==='oil');
 const player=s.player as GameState['player']&{oil?:unknown};delete player.oil;delete s.cooldowns.oil;
 if(s.groundLoot)s.groundLoot=s.groundLoot.filter(d=>d.item!=='SUPPLY_OIL');
 return changed;
}
/** Validate only the current save format, including complete gameplay records. */
export function validateCurrentSnapshot(value:unknown):asserts value is GameState {
 const fail=()=>{throw new Error('无效的四系技能存档');};if(!record(value))return fail();const s=value as unknown as GameState;
 const keys=['version','progression','combat','dice','seed','area','time','sequence','revision','status','player','enemies','encounters','projectiles','fireZones','barrels','flags','enemyHazards','inventory','provenance','pending','equipment','dialogue','action','cooldowns','receipts','recipes','merchantStock','discoveredMerchants','checkpoint','dropRolls','movedDistance','effectCounters'];
 if(Object.keys(s).some(k=>!keys.includes(k)&&k!=='forging'&&k!=='groundLoot')||keys.some(k=>!(k in s))||s.version!==3||!integer(s.seed,1,2147483646)||!area(s.area)||!number(s.time)||!integer(s.sequence)||!integer(s.revision)||!['playing','dead','complete'].includes(s.status))return fail();
 const legacy=s.combat?.version===2,skills=combatSkillCatalog(s.combat?.version);validateProgression(s.progression,s.combat?.version);validateDiceSnapshot(s.dice,s.seed,s.flags,s.receipts,s.area);validateForging(s);validateCombat(s.combat,s.progression,Object.fromEntries(Object.keys(s.inventory).map(id=>[id,itemGearBonus(s,id).power+itemForgingBonus(s,id).power])),Object.fromEntries(Object.keys(s.inventory).map(id=>[id,itemForgingBonus(s,id)])));
 const engagement=s.combat.engagement;if(engagement&&(!area(engagement.area)||engagement.quietSince!==undefined&&engagement.quietSince>s.time))return fail();
 const p=s.player;if(!point(p)||!number(p.hp,0,2000)||!integer(p.maxHp,120,2000)||p.hp>p.maxHp||!number(p.focus,0,p.maxFocus)||!(p.resourceVersion===undefined?p.maxFocus===100:p.resourceVersion===1&&integer(p.maxFocus,100,2000)&&integer(p.staminaPotions,0,SUPPLIES.SUPPLY_STAMINA.capacity)&&integer(p.manaPotions,0,SUPPLIES.SUPPLY_MANA.capacity))||'oil' in p&&!integer(p.oil,0,ITEM_STACK_LIMIT)||!integer(p.healthPotions,0,SUPPLIES.SUPPLY_HEALTH.capacity)||!integer(p.focusPotions,0,SUPPLIES.SUPPLY_FOCUS.capacity)||!number(p.angle,-1e6,1e6)||!number(p.hurtTime,0,1)||!number(p.shield,0,p.maxHp*.35+.001)||!number(p.movingTime))return fail();
 if(p.resourceVersion===undefined&&('resourceVersion' in p||'staminaPotions' in p||'manaPotions' in p))return fail();
 for(const field of ['gold','iron','runes','cores'] as const)if(!integer(p[field],0,9999))return fail();
 if(Object.keys(p).some(k=>!['x','z','hp','maxHp','focus','maxFocus','resourceVersion','staminaPotions','manaPotions','oil','healthPotions','focusPotions','gold','iron','runes','cores','angle','hurtTime','shield','movingTime'].includes(k)))return fail();
 for(const field of ['flags','receipts','inventory','provenance','pending','encounters','merchantStock','dropRolls','effectCounters','cooldowns'] as const)if(!record(s[field]))return fail();
 if(Object.values(s.flags).some(v=>typeof v!=='boolean')||Object.values(s.receipts).some(v=>!(typeof v==='boolean'||typeof v==='string'&&v.length<300||number(v))))return fail();
 validateHuntingExperience(s.receipts);
 validateBossLoot(s);
 // Optional only for older V3 saves. New drops must retain a real reward proof.
 if(s.groundLoot!==undefined){
  if(!Array.isArray(s.groundLoot)||s.groundLoot.length>Object.keys(EQUIPMENT).length+SUPPLY_LOOT_POLICY.maxPiles)return fail();
  const ids=new Set<string>(),items=new Set<string>(),supplySources=new Set<string>(),supplyAreas=new Map<string,number>();
  for(const d of s.groundLoot){
   if(!point(d)||Object.keys(d).some(k=>!['id','area','item','source','x','z','createdAt','count','supplyVersion','supplyVersion'].includes(k))||typeof d.id!=='string'||!/^loot:\d+$/.test(d.id)||Number(d.id.slice(5))>s.sequence||ids.has(d.id)||!area(d.area)||typeof d.source!=='string'||!number(d.createdAt,0,s.time))return fail();
   ids.add(d.id);
   if(isSupplyId(d.item)||d.item==='SUPPLY_OIL'){
    const match=/^supply:([^:]+):(.+):([1-9]\d*)$/.exec(d.source),cycle=Number(match?.[3]),encounter=d.area===s.area?s.enemies:s.encounters[d.area];
    if(!match||match[1]!==d.area||!integer(cycle,1,10000001)||!Array.isArray(encounter)||supplySources.has(d.source))return fail();
    const enemy=encounter.find(e=>e?.id===match[2]);
    if(!enemy||cycle>(enemy.respawnCount??0)+1||enemy.hp>0&&cycle===(enemy.respawnCount??0)+1||!number(s.receipts[`supply-cycle:${d.area}:${enemy.id}`],cycle,10000001))return fail();
    if(enemy.respawnSeconds?!number(s.receipts[`hunt-cycle:${d.area}:${enemy.id}`],cycle,10000001):s.receipts[`kill:${d.area}:${enemy.id}`]!==true)return fail();
    if(d.supplyVersion!==undefined&&d.supplyVersion!==2&&d.supplyVersion!==3)return fail();
    const rolled=supplyDrop(s.seed,d.area,enemy,cycle,d.supplyVersion??1);
    if(!rolled||rolled.item!==d.item||!integer(d.count,1,rolled.count))return fail();
    supplySources.add(d.source);supplyAreas.set(d.area,(supplyAreas.get(d.area)??0)+1);
    if(supplySources.size>SUPPLY_LOOT_POLICY.maxPiles||supplyAreas.get(d.area)!>SUPPLY_LOOT_POLICY.maxPilesPerArea)return fail();
    continue;
   }
   if(d.supplyVersion!==undefined||!EQUIPMENT[d.item]||GROWING_EQUIPMENT[d.item]&&s.inventory[d.item]||items.has(d.item)||d.count!==undefined)return fail();
   const rolled=s.dropRolls[d.source]?.result===d.item&&s.receipts[`roll:${d.source}`]===d.item;
   const valid=d.source.startsWith('boss:v3:')?validBossEquipmentSource(s,d.item,d.source):GROWING_EQUIPMENT[d.item]?d.source.startsWith('growing:boss:')&&validGrowingDropSource(s,d.item,d.source):d.source.startsWith('regional:')?rolled:d.source.startsWith('legend:pass:')?s.dropRolls[d.source.slice(7)]?.result===d.item&&s.receipts[`roll:${d.source.slice(7)}`]===d.item&&['L01','L02'].includes(d.item):Object.values(ELITE_LOOT).some(e=>e.eventId===d.source&&e.item===d.item)&&!!s.receipts[`event:${d.source}`];
   if(!valid)return fail();items.add(d.item);
  }
 }
 for(const [id,n]of Object.entries(s.inventory)){if(!EQUIPMENT[id]||!integer(n,1,equipmentStackLimit(id))||typeof s.provenance[id]!=='string')return fail();const source=s.provenance[id];if(['W01','W07','W11'].includes(id)){if(source!=='initial')return fail();}else {if(!s.receipts[`grant:${source}:${id}`])return fail();let valid=false;
 if(GROWING_EQUIPMENT[id])valid=validGrowingSource(s,id,source);
 else if(source.startsWith('boss:v3:'))valid=validBossEquipmentSource(s,id,source);
 else if(source.startsWith('lifecycle:task:'))valid=validLifecycleTaskItem(s,id,source);
 else if(source.startsWith('gear-upgrade:'))valid=validEquipmentUpgrade(s,id,source);
 else if(source.startsWith('journey:'))valid=validJourneyItem(s,id,source);
 else if(id==='W02')valid=source==='reward_ch01_gate_sword'&&!!s.flags.gate_raised&&!!s.flags.captain_defeated&&!!s.receipts.obj_ch01_04;
 else if(id==='W08')valid=source==='design_reward_ch01_oath_sword'&&!!s.receipts[source];
 else if(source===`design_find_${id.toLowerCase()}`)valid=!!s.receipts[source];
 else if(source.startsWith('legend:'))valid=id.startsWith('L')&&s.dropRolls[source.slice(7)]?.result===id&&(/^cache:.+:legend$/.test(source.slice(7))||/^pass:[^:]+:.*warden/.test(source.slice(7)));
 else if(source.startsWith('trade:')){const m=source.slice(6);valid=!!MERCHANTS[m]?.stock[id]&&s.merchantStock[m]?.[id]===0&&Object.values(s.receipts).includes(`${m}:${id}:${MERCHANTS[m].prices[id]}`);}
 else if(source.startsWith('craft:')){const recipe=source.slice(6);valid=RECIPES[recipe]?.item===id&&s.recipes.includes(recipe)&&Object.values(s.receipts).includes(recipe);}
 else if(source.startsWith('campaign:')){const event=CAMPAIGN_EVENTS[source.slice(9)];valid=!!s.receipts[source]&&!!event&&[...event.items??[],...event.choiceItems??[]].includes(id);}
 else if(source.startsWith('regional:'))valid=s.dropRolls[source]?.result===id&&s.receipts[`roll:${source}`]===id;
 else if(/^V_E\d\d$/.test(source))valid=Object.values(ELITE_LOOT).some(e=>e.eventId===source&&e.item===id)&&!!s.receipts[`event:${source}`];
 if(!valid)return fail();}}
 if(['W01','W07','W11'].some(id=>!s.inventory[id])||Object.keys(s.provenance).some(id=>!s.inventory[id])||Object.keys(s.pending).length)return fail();
 const eq=s.equipment,slots=['weapon','offhand','head','chest','hands','feet','ringLeft','ringRight','necklace'] as const;if(!record(eq)||!Array.isArray(eq.spells)||eq.spells.length!==2||eq.spells.some(id=>id!==null)||Object.keys(eq).some(k=>!([...slots,'spells'] as string[]).includes(k)))return fail();
 const equipped:string[]=[];for(const slot of slots){const id=eq[slot];if(id===null&&slot!=='weapon')continue;const d=typeof id==='string'?EQUIPMENT[id]:null;if(!d||!s.inventory[id!]||equipped.includes(id!)||!(d.slot===slot||d.kind==='ring'&&(slot==='ringLeft'||slot==='ringRight')))return fail();equipped.push(id!);}if(EQUIPMENT[eq.weapon].twoHanded&&eq.offhand)return fail();
 validateGrowingProgress(s);
 validateEquipmentOwnership(s);
 if(p.resourceVersion===1&&(legacy||p.maxFocus!==resourceMaximum(s)||s.combat.charge!==0))return fail();
 validateJourneyProgress(s);
 let bonus=equipped.reduce((n,id)=>n+(GROWING_EQUIPMENT[id]?growingStats(id,s.progression.level).maxHp:EQUIPMENT[id].maxHp??0)+itemGearBonus(s,id).maxHp+itemForgingBonus(s,id).maxHp,0);if(equipped.filter(id=>EQUIPMENT[id].set==='oath').length>=2)bonus+=8;if(p.maxHp!==baseMaxHp(s.progression)+bonus)return fail();
 if(!strings(s.recipes)||new Set(s.recipes).size!==s.recipes.length||s.recipes.some(id=>!RECIPES[id])||!strings(s.discoveredMerchants)||s.discoveredMerchants.some(id=>!MERCHANTS[id])||!point(s.checkpoint)||!area(s.checkpoint.area))return fail();
 if(Object.keys(s.merchantStock).length!==Object.keys(MERCHANTS).length)return fail();for(const [id,merchant]of Object.entries(MERCHANTS)){const stock=s.merchantStock[id];if(!record(stock)||Object.keys(stock).length!==Object.keys(merchant.stock).length||Object.keys(merchant.stock).some(key=>!integer(stock[key],0,merchant.stock[key])))return fail();}
 for(const r of [s.cooldowns,s.effectCounters])if(Object.values(r).some(v=>!number(v)))return fail();
 const enemy=(e:any)=>point(e)&&typeof e.id==='string'&&e.id.length<200&&['raider','shield','archer','captain'].includes(e.kind)&&integer(e.maxHp,1,100000)&&number(e.hp,0,e.maxHp)&&integer(e.level,1,40)&&['idle','approach','windup','active','recovery','stagger','dead'].includes(e.phase)&&number(e.phaseTime,-.1,30)&&number(e.angle,-1e6,1e6)&&number(e.targetAngle,-1e6,1e6)&&integer(e.attackCount)&&typeof e.struck==='boolean'&&typeof e.halfAnnounced==='boolean'&&(e.respawnSeconds===undefined||number(e.respawnSeconds,20,120))&&(e.respawnAt===undefined||number(e.respawnAt))&&(e.respawnCount===undefined||integer(e.respawnCount,0,10000000))&&(e.diedAt===undefined||e.hp===0&&e.phase==='dead'&&number(e.diedAt,0,s.time))&&['markedUntil','lightningUntil','pushImmuneUntil','staggerProtectedUntil'].every(k=>number(e[k]));
 if(!Array.isArray(s.enemies)||s.enemies.length>200||!s.enemies.every(enemy)||Object.entries(s.encounters).some(([id,list])=>!area(id)||!Array.isArray(list)||list.length>200||!list.every(enemy)||new Set(list.map(e=>e.id)).size!==list.length)||s.encounters[s.area]&&JSON.stringify(s.enemies)!==JSON.stringify(s.encounters[s.area]))return fail();
 for(const e of [...s.enemies,...Object.values(s.encounters).flat()]){if(e.lootChapter!==undefined&&(!integer(e.lootChapter,1,2)||!e.bossId||!(e.respawnCount!>0)))return fail();if(e.packId!==undefined&&(typeof e.packId!=='string'||e.packId.length>150||!e.respawnSeconds||!e.id.startsWith(`${e.packId}-`)))return fail();validateEnemyCombat(e,s.time);}validateEnemyHazards(s.enemyHazards,s.enemies);
 const feedback=(value:{feedbackTargetId?:string;feedbackTarget?:unknown;feedbackReported?:boolean;feedbackActionId?:string;feedbackFailure?:string})=>
  (value.feedbackTargetId===undefined?value.feedbackTarget===undefined:typeof value.feedbackTargetId==='string'&&value.feedbackTargetId.length<200&&s.enemies.some(e=>e.id===value.feedbackTargetId)&&point(value.feedbackTarget))&&
  (value.feedbackReported===undefined||typeof value.feedbackReported==='boolean')&&
  (value.feedbackActionId===undefined||typeof value.feedbackActionId==='string'&&value.feedbackActionId.length<200)&&
  (value.feedbackFailure===undefined||['blocked','expired'].includes(value.feedbackFailure));
 if(s.action&&!feedback(s.action))return fail();
 if(!Array.isArray(s.projectiles)||s.projectiles.length>1000||s.projectiles.some(q=>!point(q)||!feedback(q)||typeof q.id!=='string'||!['arrow','staff','spell','crossbow','oil','blade','flame'].includes(q.kind)||!['player','enemy'].includes(q.owner)||!number(q.angle,-1e6,1e6)||!number(q.speed,0,100)||!number(q.remaining,0,100)||!number(q.damage,0,50000)||!number(q.age,0,20)||!strings(q.hits)||!integer(q.pierce,1,200)||q.skillId&&(!skills[q.skillId]||!integer(q.rank,1,5)||q.rank!>(s.progression.learned[q.skillId]??0))||q.frozenPath&&(!Array.isArray(q.frozenPath)||q.frozenPath.length!==3||!q.frozenPath.every(point))))return fail();
 for(const q of s.projectiles){if(q.accuracy!==undefined&&!number(q.accuracy,100,q.owner==='player'?playerCombatAttributes(s).accuracy+.0000001:110))return fail();if(q.returning!==false||typeof q.charged!=='boolean'||!['out','back'].includes(q.leg)||q.kind==='spell'||q.owner==='player'&&!EQUIPMENT[q.weapon])return fail();if(q.kind==='oil'&&(q.owner!=='player'||!point(q.origin)||!point(q.target)||!number(q.releasedAt,0,s.time)||!number(q.age,0,.3)||Math.hypot(q.origin!.x-q.target!.x,q.origin!.z-q.target!.z)>4.5+.001))return fail();if(q.skillId){const cast=s.combat.casts.find(c=>c.id===q.castId);if(!cast||cast.skillId!==q.skillId||cast.rank.rank!==q.rank||q.owner!=='player'||!integer(q.segment,0,5)||!point(q.from)||!point(q.previousPosition)||!number(q.width,0,20)||q.targetId&&!s.enemies.some(e=>e.id===q.targetId))return fail();if(q.chainOrigin&&(q.skillId!=='BOW_02'||q.child||!point(q.chainOrigin)||!q.hits.length||q.hits.length>=q.pierce||!q.frozenPath||!number(q.pathProgress,0,1)||!number(q.pathLength,.01,20)||!point(q.target)))return fail();if(q.child&&(q.skillId!=='BOW_02'||!q.targetId||!q.frozenPath||!number(q.pathProgress,0,1)||!number(q.pathLength,.01,20)||!point(q.target)))return fail();}}
 if(!Array.isArray(s.fireZones)||!Array.isArray(s.barrels)||s.fireZones.some(f=>!point(f)||!number(f.remaining,0,5)||!number(f.radius,.1,2)||!number(f.tick,0,.5))||s.barrels.some(b=>!point(b)||!number(b.fuse,-1,1)||typeof b.exploded!=='boolean'))return fail();
 for(const q of s.projectiles)validateEnemyProjectile(q,s.enemies);
 validateContactSnapshots(s);
 if(s.action!==null){const a=s.action;if(a.accuracy!==undefined&&!number(a.accuracy,100,playerCombatAttributes(s).accuracy+.0000001))return fail();if(!record(a)||typeof a.id!=='string'||!number(a.elapsed,0,10000)||!number(a.duration,0,10000)||!number(a.angle,-1e6,1e6)||!strings(a.hits)||typeof a.emitted!=='boolean'||!number(a.damage,0,10000)||a.skillId&&(!skills[a.skillId]||!(s.progression.learned[a.skillId]>0)))return fail();if(a.skillId){const cast=s.combat.casts.find(c=>c.id===a.id);if(!cast||cast.skillId!==a.skillId||a.rank!==cast.rank.rank||!number(a.releaseAt,0,5)||a.kind!==(a.skillId==='COM_01'?'dash':`pure:${a.skillId}`))return fail();}else if(!['sword','staff','bow','bowAim','oil'].includes(a.kind)||a.kind==='oil'&&!point(a.target))return fail();}
 if(s.dialogue!==null&&(!record(s.dialogue)||typeof s.dialogue.id!=='string'||typeof s.dialogue.speaker!=='string'||typeof s.dialogue.text!=='string'||!Array.isArray(s.dialogue.options)||s.dialogue.options.length>30||s.dialogue.options.some(o=>!record(o)||typeof o.id!=='string'||typeof o.label!=='string')))return fail();
 if(!number(s.movedDistance))return fail();
}
