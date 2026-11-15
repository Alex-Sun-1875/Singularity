import {equipmentText as tr} from '../locales';
import type {GameState,EnemyState} from '../../../core/GameSession';
import type {Point} from '../../../core/Contracts';
import {EQUIPMENT,equipmentStackLimit} from '../data/Equipment';
import {GROWING_BOSS_DROPS,artifactWeaponForStyle} from '../data/GrowingEquipment';
import {lifecycleBattlePool,releasedEquipmentChapter,type LootStyle} from '../data/EquipmentLifecycle';
import {chapterForArea} from '../../journey/data/ChapterJourney';
import {equipmentRandomWord} from './EquipmentDice';
import {BUILD_PROFILE} from '../../../shared/BuildProfile';

export const BOSS_LOOT_POLICY={artifact:.01,legendary:.036,epic:.10,epicPity:10,legendaryPity:50,respawnSeconds:600} as const;
type Meta=[3|4|5,number,number,LootStyle,number,number,number,string,string,string];
interface Host {state():GameState;now():number;grant(id:string,source:string,at:Point):void;changed():void;emit(type:string,text?:string,extra?:Record<string,unknown>):void}
const CLOCK='boss:v3:clock',EPIC='boss:v3:epic-misses',LEGEND='boss:v3:legend-misses',DRAWS='boss:v3:draws';
const styles:LootStyle[]=['WAR','BOW','FIR','THU'];
// Frozen order and weights are part of issued save proofs; change the schema for a new pool.
const ARTIFACT_POOL_V4=['DG_A01','DG_A03','DG_A04','DG_A05','DG_A02'] as const;
const owned=(s:GameState,id:string)=>!!s.inventory[id]||!!s.groundLoot.some(d=>d.item===id)||s.receipts[`growing-owned:${id}`]!==undefined;
const atCapacity=(s:GameState,id:string)=>(s.inventory[id]??0)>=equipmentStackLimit(id)||s.groundLoot.some(d=>d.item===id)||equipmentStackLimit(id)===1&&owned(s,id);
const roll=(seed:number,key:string)=>equipmentRandomWord(seed,key)%2147483646+1;
const baseKey=(area:string,id:string)=>`boss:v3:${area}:${id}`;
// Schema 4 normal draws use the frozen all-weapon pool. Legacy dev 4/5
// proofs keep their forced tiers in the isolated dev storage namespace.
const guaranteed=()=>BUILD_PROFILE.name==='dev'&&BUILD_PROFILE.guaranteedBossHighTierLoot;
const recordKey=(m:Meta)=>baseKey(m[8],m[9])+(m[0]===5?':dev-artifact':'');
const recordTier=(m:Meta,n:number)=>guaranteed()&&m[0]===4?2:m[0]===5?3:bossDropTier(n/2147483647,m[4],m[5]);
const nowSeconds=(s:GameState,now:number)=>Math.max(Number(s.receipts[CLOCK]??0),Math.max(0,Math.min(9999999399,Math.floor((Number.isFinite(now)?now:0)/1000))));
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
function pool(meta:Meta,tier:number){
 const [, ,chapter,style,,,,boss]=meta;
 if(tier===3)return meta[0]===4&&!guaranteed()?[...ARTIFACT_POOL_V4]:[artifactWeaponForStyle[style],'DG_A02'];
 if(tier===1)return lifecycleBattlePool(chapter,'史诗',style);
 if(tier===2){const legacy=(GROWING_BOSS_DROPS[boss]??[]).map(d=>d.item).filter(id=>EQUIPMENT[id]?.quality==='传奇'&&(!EQUIPMENT[id].weaponFamily||style==='WAR'&&EQUIPMENT[id].kind==='sword'||style==='BOW'&&EQUIPMENT[id].kind==='bow'||style==='FIR'&&EQUIPMENT[id].weaponFamily==='双手火杖'||style==='THU'&&EQUIPMENT[id].weaponFamily==='双手雷杖'));return [...lifecycleBattlePool(chapter,'传奇',style),...legacy];}
 return [];
}
function initialIndex(seed:number,key:string,meta:Meta,tier:number,candidates:string[]){
 const n=roll(seed,`${key}:${meta[1]}:item`)/2147483647;
 if(tier!==3)return Math.min(candidates.length-1,Math.floor(n*candidates.length));
 if(meta[0]!==4||guaranteed())return n<.7?0:1; // Preserve the original style-bound draws.
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
 private draw(e:EnemyState,chapter:number,kind:3|4|5){
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
  this.host.emit('loot_roll',result,{id:key,tier,devGuaranteed:guaranteed()&&kind!==3,epicMisses:s.receipts[EPIC],legendMisses:s.receipts[LEGEND]});
 }
 defeat(e:EnemyState){
  if(!e.bossId||e.hp>0||e.phase!=='dead')return false;
  const s=this.s,cycle=e.respawnCount??0,key=baseKey(s.area,e.id);
  if(Number(s.receipts[`${key}:life`]??-1)>=cycle)return false;
  const chapter=e.lootChapter??chapterForArea(s.area),gold=8+Math.min(2,chapter)*4;
  s.player.gold=Math.min(9999,s.player.gold+gold);s.player.iron=Math.min(9999,s.player.iron+2);
  this.host.emit('reward',tr('loot.bossResources',{gold}),{id:key,gold,iron:2});
  this.draw(e,chapter,4);
  if(guaranteed())this.draw(e,chapter,5);
  const now=nowSeconds(s,this.host.now());s.receipts[CLOCK]=now;s.receipts[`boss:v3:ready:${e.bossId}`]=now+600;
  this.host.changed();return true;
 }
 rematchLevel(e:{level?:number}){const chapter=releasedEquipmentChapter(this.s.progression.level),top=chapter===1?10:20;return Math.max(e.level??1,Math.min(this.s.progression.level,top));}
}
function readBossRecord(s:GameState,source:string){
 try{
  const raw=s.receipts[`${source}:meta`];if(typeof raw!=='string')return null;const m=JSON.parse(raw) as Meta;
  if(!Array.isArray(m)||m.length!==10||!(m[0]===3||m[0]===4||guaranteed()&&m[0]===5)||!Number.isInteger(m[1])||m[1]<0||m[1]>1e7||![1,2].includes(m[2])||!styles.includes(m[3])||!Number.isInteger(m[4])||m[4]<0||m[4]>9||!Number.isInteger(m[5])||m[5]<0||m[5]>49||!Number.isInteger(m[6])||m[6]<1||m[6]>Number(s.receipts[DRAWS]??0)||[m[7],m[8],m[9]].some(v=>typeof v!=='string'||!v))return null;
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
