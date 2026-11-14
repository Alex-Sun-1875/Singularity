import type {Point} from '../../../core/Contracts';
import type {GameState,EnemyState} from '../../../core/GameSession';
import {GROWING_EQUIPMENT,GROWING_BOSS_DROPS,GROWING_SCENES,GROWING_QUESTS} from '../data/GrowingEquipment';
import {validBossEquipmentSource} from './BossLoot';
import {FIELD_DISCOVERIES} from '../../campaign/data/FieldQuests';
import {fieldQuestText as text} from '../../campaign/locales/FieldQuestText';
import {chapterForArea} from '../../journey/data/ChapterJourney';
import {equipmentRandomWord} from './EquipmentDice';

interface Host {state():GameState;grant(item:string,count:number,source:string,at?:Point):void;changed():void;emit(type:string,text?:string,extra?:Record<string,unknown>):void}
export function growingRandom(seed:number,key:string){let n=seed;for(let i=0;i<key.length;i++)n=(n*131+key.charCodeAt(i))%2147483647;return ((n+1)*48271)%2147483647;}
export const growingOwned=(s:GameState,id:string)=>!!s.inventory[id]||s.receipts[`growing-owned:${id}`]!==undefined||!!s.groundLoot?.some(d=>d.item===id);

/** All acquisition routes share one durable item ownership receipt. */
export class GrowingEquipmentLoot {
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 /** One 5% trial per authored investigation or five real wilderness kills. */
 opportunity(){
  const s=this.s,discovery=FIELD_DISCOVERIES.find(d=>d.chapter===chapterForArea(s.area));if(!discovery||s.flags[discovery.flag])return;
  const key=`growing:field:${discovery.chapter}`,cycle=Number(s.receipts[key+':cycle']??0)+1,roll=equipmentRandomWord(s.seed,`${key}:${cycle}`),success=roll/4294967296<.05,result=success?`flag:${discovery.flag}`:'none';
  s.receipts[key+':cycle']=cycle;s.dropRolls[key]={roll,result};s.receipts[`roll:${key}`]=result;
  if(success){s.flags[discovery.flag]=true;this.host.emit('quest',text('ui.discovered',false,{name:discovery.name}),{id:discovery.flag});}
  this.host.changed();
 }
 hunt(){const key=`field:hunt:${chapterForArea(this.s.area)}`,n=(this.s.effectCounters[key]??0)+1;this.s.effectCounters[key]=n;if(n%5===0)this.opportunity();}
 scene(id:string){
  const def=GROWING_SCENES.find(s=>s.id===id&&s.area===this.s.area);if(!def)return;
  const key=`growing:scene:${id}`,old=this.s.dropRolls[key];
  if(def.flag==='dg:dawn-found'){
   if(old){this.host.emit('inspect',text('ui.spent'),{id});return;}
   this.s.dropRolls[key]={roll:0,result:'field-investigation'};this.s.receipts[`roll:${key}`]='field-investigation';this.opportunity();this.host.emit('inspect',this.s.flags[def.flag]?text('ui.dawnTrace'):text('ui.trace'),{id});this.host.changed();return;
  }
  if(old){this.host.emit('inspect',old.result==='none'?'这处发现已经调查过；结果已保存。':def.flag?'这条奇遇线索已经记录，可在地图查看后续行动。':'此处已调查，物品不会重复生成。',{id});return;}
  const roll=growingRandom(this.s.seed,key),success=roll/2147483647<def.chance;
  const result=def.item&&growingOwned(this.s,def.item)?'owned':success?(def.item??`flag:${def.flag}`):'none';
  this.s.dropRolls[key]={roll,result};this.s.receipts[`roll:${key}`]=result;
  if(success&&def.flag){this.s.flags[def.flag]=true;this.host.emit('quest',def.flag==='dg:clock-found'?'发现隐藏任务「逆行的钟声」：在洞厅核对第一处钟纹。':'发现隐藏任务「未写完的墓志」：先核对墓园遗失的姓名。',{id:def.flag});}
  else if(result===def.item)this.host.grant(def.item!,1,key);
  else this.host.emit('inspect',result==='owned'?'这件成长装备已经获得过，本旅程不再生成第二件。':'只发现了旧痕迹，没有稀有物品。可继续探索其他发现。',{id});
  this.host.changed();
 }
}

export function validGrowingSource(s:GameState,id:string,source:string):boolean {
 if(!GROWING_EQUIPMENT[id]||s.receipts[`growing-owned:${id}`]!==source)return false;
 return validGrowingDropSource(s,id,source);
}
export function validGrowingDropSource(s:GameState,id:string,source:string):boolean {
 if(!GROWING_EQUIPMENT[id])return false;
 if(source.startsWith('boss:v3:'))return validBossEquipmentSource(s,id,source);
 if(source.startsWith('campaign:')){
  // Previously earned unique items retain their issued proof; new rewards use the authored tables.
  const legacy:Record<string,string>={'campaign:dg-lamp-return':'DG_L03','campaign:dg-letter-return':'DG_L05','campaign:dg-dawn-return':'DG_A02'};
  if(legacy[source]===id&&s.receipts[source]===true)return true;
  const q=GROWING_QUESTS.find(q=>`campaign:${q.id}`===source);return !!q&&[...q.items??[],...q.choiceItems??[]].includes(id)&&s.receipts[source]===true&&(q.requires??[]).every(f=>s.flags[f])&&(q.sets??[]).every(f=>s.flags[f]);
 }
 const result=s.dropRolls[source];if(!result||result.result!==id||s.receipts[`roll:${source}`]!==id)return false;
 const scene=GROWING_SCENES.find(d=>`growing:scene:${d.id}`===source&&d.item===id);
 if(scene)return result.roll===growingRandom(s.seed,source)&&result.roll/2147483647<scene.chance;
 for(const [boss,pool]of Object.entries(GROWING_BOSS_DROPS))for(const def of pool)if(`growing:boss:${boss}:${id}`===source&&def.item===id){const cycle=s.receipts[`growing-cycle:${source}`];return typeof cycle==='number'&&Number.isInteger(cycle)&&cycle>=0&&cycle<=1e7&&result.roll===growingRandom(s.seed,`${source}:${cycle}`)&&result.roll/2147483647<def.chance;}
 return false;
}
export function validateGrowingProgress(s:GameState){
 for(const [id]of Object.entries(GROWING_EQUIPMENT))if(s.receipts[`growing-owned:${id}`]!==undefined&&(s.inventory[id]!==1||!validGrowingSource(s,id,s.provenance[id])))throw new Error('无效的成长装备唯一凭证');
 for(const flag of ['dg:clock-found','dg:dawn-found','field:bell-found'])if(s.flags[flag]){
  const field=FIELD_DISCOVERIES.find(d=>d.flag===flag),key=field?`growing:field:${field.chapter}`:'',r=s.dropRolls[key],cycle=s.receipts[key+':cycle'];
  const validField=!!field&&typeof cycle==='number'&&Number.isSafeInteger(cycle)&&cycle>0&&r?.result===`flag:${flag}`&&r.roll===equipmentRandomWord(s.seed,`${key}:${cycle}`)&&r.roll/4294967296<.05&&s.receipts[`roll:${key}`]===r.result;
  const legacy=GROWING_SCENES.some(d=>{const k=`growing:scene:${d.id}`,r=s.dropRolls[k];return d.flag===flag&&r?.result===`flag:${flag}`&&r.roll===growingRandom(s.seed,k)&&r.roll/2147483647<d.chance&&s.receipts[`roll:${k}`]===r.result;});
  if(!validField&&!legacy)throw new Error('无效的隐藏任务发现凭证');
 }
}
