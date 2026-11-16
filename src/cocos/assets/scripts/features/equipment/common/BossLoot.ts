import {equipmentText as tr} from '../locales';
import type {GameState,EnemyState} from '../../../core/GameSession';
import type {Point} from '../../../core/Contracts';
import {EQUIPMENT,equipmentStackLimit} from '../data/Equipment';
import {artifactWeaponForStyle} from '../data/GrowingEquipment';
import {lifecycleBattlePool,lifecycleGroup,LIFECYCLE_GROUPS,releasedEquipmentChapter,mainBossChapter,type LootStyle} from '../data/EquipmentLifecycle';
export {mainBossChapter} from '../data/EquipmentLifecycle';
import {FIELD_QUEST_ITEMS} from '../data/FieldQuestEquipment';
import {chapterForArea,PLAYABLE_CHAPTERS} from '../../journey/data/ChapterJourney';
import {equipmentRandomWord} from './EquipmentDice';
import {BUILD_PROFILE} from '../../../shared/BuildProfile';

export const BOSS_LOOT_POLICY={artifact:.01,legendary:.036,epic:.10,epicPity:10,legendaryPity:50,respawnSeconds:600} as const;
type Meta=[6|7|8,number,number,LootStyle,number,number,number,string,string,string];
interface Host {state():GameState;now():number;grant(id:string,source:string,at:Point):void;changed():void;emit(type:string,text?:string,extra?:Record<string,unknown>):void}
const CLOCK='boss:v3:clock',EPIC='boss:v3:epic-misses',LEGEND='boss:v3:legend-misses',DRAWS='boss:v3:draws';
const styles:LootStyle[]=['WAR','BOW','FIR','THU'];
const ARTIFACT_POOL=['DG_A01','DG_A03','DG_A04','DG_A05','DG_A02'];
const GROWING_LEGEND_POOL:Record<number,string[]>={1:['DG_L01'],2:['DG_L01','DG_L02','DG_L04']};
const owned=(s:GameState,id:string)=>!!s.inventory[id]||!!s.groundLoot.some(d=>d.item===id)||s.receipts[`growing-owned:${id}`]!==undefined;
const atCapacity=(s:GameState,id:string)=>(s.inventory[id]??0)>=equipmentStackLimit(id)||s.groundLoot.some(d=>d.item===id)||equipmentStackLimit(id)===1&&owned(s,id);
const roll=(seed:number,key:string)=>equipmentRandomWord(seed,key)%2147483646+1;
const baseKey=(area:string,id:string)=>`boss:v3:${area}:${id}`;
const guaranteed=()=>BUILD_PROFILE.name==='dev'&&BUILD_PROFILE.guaranteedBossHighTierLoot;
const recordKey=(m:Meta)=>baseKey(m[8],m[9])+(m[0]===7?':dev-artifact':m[0]===8?':dev-legendary':'');
const recordTier=(m:Meta,n:number)=>m[0]===7?3:m[0]===8||guaranteed()?2:bossDropTier(n/2147483647,m[4],m[5]);
const nowSeconds=(s:GameState,now:number)=>Math.max(Number(s.receipts[CLOCK]??0),Math.max(0,Math.min(9999999399,Math.floor((Number.isFinite(now)?now:0)/1000))));
export function bossRewardKind(enemyOrBossId:string|{bossId?:string}|undefined):'fixed'|'random'|null {const id=typeof enemyOrBossId==='string'?enemyOrBossId:enemyOrBossId?.bossId;return !id?null:mainBossChapter(id)?'fixed':'random';}
export const mainBossEquipmentSource=(chapter:number,group:string)=>`boss:fixed:${chapter}:${group}`;
export function mainBossEquipment(chapter:number,style:LootStyle){return LIFECYCLE_GROUPS.filter(g=>g.chapter===chapter&&g.route==='task').map(g=>({group:g.id,item:g.items.find(id=>id.endsWith('_'+style))??g.items[0]}));}
export function mainBossEquipmentView(s:GameState,chapter:number){
 const bossId=PLAYABLE_CHAPTERS.find(c=>c.id===chapter)?.boss,view=bossLootView(s,0),rewards=mainBossEquipment(chapter,view.style).map(reward=>{const source=mainBossEquipmentSource(chapter,reward.group),awarded=typeof s.receipts[source]==='string',item=awarded?String(s.receipts[source]):reward.item;return {group:reward.group,item,awarded,owned:!!s.inventory[item],onGround:s.groundLoot.some(d=>d.source===source&&d.item===item)};});
 return {bossId,style:view.style,rewards,awarded:rewards.length>0&&rewards.every(r=>r.awarded)};
}
export function bossLootView(s:GameState,now:number,boss?:string){
 const remaining=boss?Math.max(0,Number(s.receipts[`boss:v3:ready:${boss}`]??0)-nowSeconds(s,now)):0;
 return {remaining,ready:remaining<=0,epicMisses:Number(s.receipts[EPIC]??0),legendMisses:Number(s.receipts[LEGEND]??0),draws:Number(s.receipts[DRAWS]??0),style:styles.includes(s.receipts['loot:v3:style'] as LootStyle)?s.receipts['loot:v3:style'] as LootStyle:s.combat.family??'WAR' as LootStyle};
}
export function bossDropTier(n:number,epicMisses:number,legendMisses:number){
 if(n<BOSS_LOOT_POLICY.artifact)return 3;
 if(n<BOSS_LOOT_POLICY.artifact+BOSS_LOOT_POLICY.legendary||legendMisses>=49)return 2;
 if(n<BOSS_LOOT_POLICY.artifact+BOSS_LOOT_POLICY.legendary+BOSS_LOOT_POLICY.epic||epicMisses>=9)return 1;
 return 0;
}
function matchesStyle(id:string,style:LootStyle){const item=EQUIPMENT[id];return !item?.weaponFamily||style==='WAR'&&item.kind==='sword'||style==='BOW'&&item.kind==='bow'||style==='FIR'&&item.weaponFamily==='双手火杖'||style==='THU'&&item.weaponFamily==='双手雷杖';}
/** Every random Boss in a chapter uses the same content-owned candidates. */
export function bossRandomPool(chapter:number,tier:number,style:LootStyle):string[]{
 if(tier===3)return [...ARTIFACT_POOL];if(tier!==1&&tier!==2)return [];
 const quality=tier===1?'史诗':'传奇',field=FIELD_QUEST_ITEMS.filter(d=>d.chapter===chapter&&d.quality===quality&&matchesStyle(d.id,style)).map(d=>d.id),growing=tier===2?(GROWING_LEGEND_POOL[chapter]??[]).filter(id=>matchesStyle(id,style)):[];
 return [...new Set([...lifecycleBattlePool(chapter,quality,style),...field,...growing])];
}
const pool=(meta:Meta,tier:number)=>meta[0]===7&&tier===3?[artifactWeaponForStyle[meta[3]],'DG_A02']:bossRandomPool(meta[2],tier,meta[3]);
function initialIndex(seed:number,key:string,meta:Meta,tier:number,candidates:string[]){
 const n=roll(seed,`${key}:${meta[1]}:item`)/2147483647;
 if(tier!==3)return Math.min(candidates.length-1,Math.floor(n*candidates.length));
 const weapons=candidates.length-1;return n<.7?Math.floor(n/.7*weapons):weapons;
}
/** One bounded active record per boss; only actual item proofs are archived. */
export class BossLoot {
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 view(boss?:string){return bossLootView(this.s,this.host.now(),boss);}
 selectStyle(style:string){if(!styles.includes(style as LootStyle))return false;this.s.receipts['loot:v3:style']=style;this.host.changed();return true;}
 beginRematch(boss:string){const n=nowSeconds(this.s,this.host.now());this.s.receipts[CLOCK]=n;this.host.changed();return this.view(boss).ready;}
 private archive(key:string){
  const s=this.s,previous=s.dropRolls[key];if(!previous||!EQUIPMENT[previous.result])return;
  const item=previous.result,inventory=s.provenance[item]===key,ground=s.groundLoot.some(d=>d.source===key);
  if(!inventory&&!ground)return;const archive=`${key}:owned:${item}`;
  s.dropRolls[archive]={...previous};s.receipts[`roll:${archive}`]=item;s.receipts[`${archive}:meta`]=s.receipts[`${key}:meta`];
  if(inventory){s.provenance[item]=archive;s.receipts[`grant:${archive}:${item}`]=true;if(s.receipts[`growing-owned:${item}`]===key)s.receipts[`growing-owned:${item}`]=archive;}
  for(const d of s.groundLoot)if(d.source===key)d.source=archive;
 }
 private draw(e:EnemyState,chapter:number,kind:6|7|8){
  const s=this.s,cycle=e.respawnCount??0,view=this.view();
  const meta:Meta=[kind,cycle,Math.min(2,chapter),view.style,view.epicMisses,view.legendMisses,view.draws+1,e.bossId!,s.area,e.id],key=recordKey(meta);
  this.archive(key);
  const n=roll(s.seed,`${key}:${cycle}:quality`),tier=recordTier(meta,n),candidates=pool(meta,tier);
  let result='none';if(candidates.length){const start=initialIndex(s.seed,key,meta,tier,candidates);let item=candidates[start];for(let i=0;i<candidates.length;i++){const id=candidates[(start+i)%candidates.length];if(!owned(s,id)){item=id;break;}}
   if(owned(s,item)){const stackable=candidates.find(id=>!atCapacity(s,id));if(stackable)item=stackable;}
   result=atCapacity(s,item)?`duplicate:${item}`:item;
   if(result===item)this.host.grant(item,key,e);else {s.player.gold=Math.min(9999,s.player.gold+12+meta[2]*4);s.player.iron=Math.min(9999,s.player.iron+2);}
  }
  s.dropRolls[key]={roll:n,result};s.receipts[`roll:${key}`]=result;s.receipts[`${key}:meta`]=JSON.stringify(meta);s.receipts[`${key}:life`]=cycle;
  s.receipts[EPIC]=tier>=1?0:meta[4]+1;s.receipts[LEGEND]=tier>=2?0:meta[5]+1;s.receipts[DRAWS]=meta[6];
  this.host.emit('loot_roll',result,{id:key,tier,devGuaranteed:guaranteed(),epicMisses:s.receipts[EPIC],legendMisses:s.receipts[LEGEND]});
 }
 defeat(e:EnemyState){
  if(!e.bossId||e.hp>0||e.phase!=='dead'||e.diedAt===undefined||e.respawnSeconds||e.trainingEnemy)return false;
  const s=this.s,cycle=e.respawnCount??0,key=baseKey(s.area,e.id);
  if(Number(s.receipts[`${key}:life`]??-1)>=cycle)return false;
  const chapter=e.lootChapter??chapterForArea(s.area),gold=8+Math.min(2,chapter)*4;
  s.player.gold=Math.min(9999,s.player.gold+gold);s.player.iron=Math.min(9999,s.player.iron+2);
  this.host.emit('reward',tr('loot.bossResources',{gold}),{id:key,gold,iron:2});
  const main=mainBossChapter(e.bossId);
  if(main){if(cycle===0&&PLAYABLE_CHAPTERS.find(c=>c.id===main)?.arena===s.area)for(const reward of mainBossEquipment(main,this.view().style)){const source=mainBossEquipmentSource(main,reward.group);if(s.receipts[source]!==undefined)continue;s.receipts[source]=reward.item;s.receipts[source+':meta']=JSON.stringify([1,this.view().style,e.id]);this.host.grant(reward.item,source,e);}s.receipts[`${key}:life`]=cycle;if(guaranteed()){this.draw(e,chapter,8);this.draw(e,chapter,7);}
  }else {this.draw(e,chapter,6);if(guaranteed())this.draw(e,chapter,7);}
  const now=nowSeconds(s,this.host.now());s.receipts[CLOCK]=now;s.receipts[`boss:v3:ready:${e.bossId}`]=now+600;
  this.host.changed();return true;
 }
 rematchLevel(e:{level?:number}){const chapter=releasedEquipmentChapter(this.s.progression.level),top=chapter===1?10:20;return Math.max(e.level??1,Math.min(this.s.progression.level,top));}
}
export function validMainBossEquipmentSource(s:GameState,id:string,source:string):boolean {
 try{const match=/^boss:fixed:([12]):(LC[12]_T_[EL])$/.exec(source);if(!match||s.receipts[source]!==id)return false;
  const chapter=Number(match[1]),g=lifecycleGroup(match[2]),main=PLAYABLE_CHAPTERS.find(c=>c.id===chapter),raw=s.receipts[source+':meta'];if(!g||g.chapter!==chapter||!main||typeof raw!=='string')return false;
  const meta=JSON.parse(raw);if(!Array.isArray(meta)||meta.length!==3||meta[0]!==1||!styles.includes(meta[1])||typeof meta[2]!=='string'||mainBossEquipment(chapter,meta[1]).find(r=>r.group===g.id)?.item!==id)return false;
  const enemy=(s.area===main.arena?s.enemies:s.encounters[main.arena]??[]).find(e=>e.id===meta[2]);return !!enemy&&enemy.bossId===main.boss&&s.receipts[`kill:${main.arena}:${enemy.id}`]===true&&s.flags[`boss_defeated:${main.boss}`]===true&&Number(s.receipts[baseKey(main.arena,enemy.id)+':life']??-1)>=0;
 }catch{return false;}
}
function readBossRecord(s:GameState,source:string){
 try{
  const raw=s.receipts[`${source}:meta`];if(typeof raw!=='string')return null;const m=JSON.parse(raw) as Meta;
  if(!Array.isArray(m)||m.length!==10||!(m[0]===6||guaranteed()&&(m[0]===7||m[0]===8))||!Number.isInteger(m[1])||m[1]<0||m[1]>1e7||![1,2].includes(m[2])||!styles.includes(m[3])||!Number.isInteger(m[4])||m[4]<0||m[4]>9||!Number.isInteger(m[5])||m[5]<0||m[5]>49||!Number.isInteger(m[6])||m[6]<1||m[6]>Number(s.receipts[DRAWS]??0)||[m[7],m[8],m[9]].some(v=>typeof v!=='string'||!v)||mainBossChapter(m[7])&&m[0]===6)return null;
  const key=recordKey(m),r=s.dropRolls[source];if(!r||source!==key&&source!==`${key}:owned:${r.result}`)return null;
  const enemy=(s.area===m[8]?s.enemies:s.encounters[m[8]]??[]).find(e=>e.id===m[9]);
  if(!enemy||enemy.bossId!==m[7]||Number(s.receipts[`${key}:life`]??-1)<m[1]||!s.receipts[`kill:${m[8]}:${m[9]}`])return null;
  const expected=roll(s.seed,`${key}:${m[1]}:quality`);if(r.roll!==expected||s.receipts[`roll:${source}`]!==r.result)return null;
  const tier=recordTier(m,expected);return {m,key,r,tier,candidates:pool(m,tier)};
 }catch{return null;}
}
function validChoice(s:GameState,id:string,data:NonNullable<ReturnType<typeof readBossRecord>>){
 const {m,key,tier,candidates}=data;if(!candidates.includes(id))return false;
 const start=initialIndex(s.seed,key,m,tier,candidates);for(let i=0;i<candidates.length;i++){const candidate=candidates[(start+i)%candidates.length];if(candidate===id)return true;if(!owned(s,candidate))return false;}return false;
}
export function validBossEquipmentSource(s:GameState,id:string,source:string){const data=readBossRecord(s,source);return !!data&&data.r.result===id&&validChoice(s,id,data);}
export function validateBossLoot(s:GameState){
 const fail=()=>{throw new Error('无效的Boss战利品或刷新记录');};
 for(const key of Object.keys(s.receipts))if(key.startsWith('boss:fixed:')){const source=key.endsWith(':meta')?key.slice(0,-5):key,item=s.receipts[source];if(typeof item!=='string'||!validMainBossEquipmentSource(s,item,source)||!s.inventory[item]&&!s.groundLoot.some(d=>d.item===item&&d.source===source))return fail();}
 for(const main of PLAYABLE_CHAPTERS){const enemy=(s.area===main.arena?s.enemies:s.encounters[main.arena]??[]).find(e=>e.bossId===main.boss);if(enemy&&s.receipts[`kill:${main.arena}:${enemy.id}`]===true)for(const reward of mainBossEquipment(main.id,'WAR')){if(typeof s.receipts[mainBossEquipmentSource(main.id,reward.group)]!=='string')return fail();}}
 for(const [key,value]of Object.entries(s.receipts))if(key.startsWith('boss:v3:')){
  if(key.endsWith(':meta')){if(typeof value!=='string'||value.length>300||!s.dropRolls[key.slice(0,-5)])return fail();continue;}
  const max=key===EPIC?9:key===LEGEND?49:key===DRAWS?1e7:1e10;
  if(typeof value!=='number'||!Number.isInteger(value)||value<0||value>max)return fail();
 }
 if(s.receipts['loot:v3:style']!==undefined&&!styles.includes(s.receipts['loot:v3:style'] as LootStyle))return fail();
 let latest:ReturnType<typeof readBossRecord>=null;
 for(const [source,r]of Object.entries(s.dropRolls))if(source.startsWith('boss:v3:')){
  const data=readBossRecord(s,source);if(!data)return fail();
  if(data.tier===0){if(r.result!=='none')return fail();}
  else if(r.result.startsWith('duplicate:')){const id=r.result.slice(10);if(!owned(s,id)||!validChoice(s,id,data))return fail();}
  else if(!EQUIPMENT[r.result]||!validChoice(s,r.result,data))return fail();
  if(!latest||data.m[6]>latest.m[6])latest=data;
 }
 if(latest&&(latest.m[6]!==Number(s.receipts[DRAWS])||Number(s.receipts[EPIC])!==(latest.tier>=1?0:latest.m[4]+1)||Number(s.receipts[LEGEND])!==(latest.tier>=2?0:latest.m[5]+1)))return fail();
 if(!latest&&Number(s.receipts[DRAWS]??0)!==0)return fail();
}
