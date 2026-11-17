import {creditGold} from '../../economy/common/GoldWallet';
import {claimEconomyGold,ordinaryGold} from '../../economy/common/EconomyRewards';
import type {Point} from '../../../core/Contracts';
import type {EnemyState,GameState} from '../../../core/GameSession';
import {CAMPAIGN_LEVELS} from '../data/Campaign';
import {REGIONAL_LOOT_POOLS,REGION_LOOT,OUTPOST_AREAS,ELITE_LOOT} from '../data/CampaignLoot';
import {MONSTER_BOSS_REWARDS} from '../../world/data/MonsterEcology';
import {supplyDrop,supplySource,type SupplyId} from '../../equipment/data/Supplies';
import {campaignBattle,campaignFighter} from '../data/CampaignBattles';
import {EQUIPMENT,equipmentStackLimit} from '../../equipment/data/Equipment';
import {lifecycleBattlePool} from '../../equipment/data/EquipmentLifecycle';
import {chapterForArea} from '../../journey/data/ChapterJourney';
import {equipmentRandomWord} from '../../equipment/common/EquipmentDice';

interface LootHost {state():GameState;grant(item:string,count:number,source:string,at?:Point):void;supply(item:SupplyId,count:number,source:string,at:Point):void;cultivation?(enemy:EnemyState):void;changed():void;emit(type:string,text?:string,extra?:Record<string,unknown>):void}
function random(seed:number,source:string){let n=seed;for(let i=0;i<source.length;i++)n=(n*131+source.charCodeAt(i))%2147483647;return ((n+1)*48271)%2147483647;}
/** All rolls are keyed to an actual encounter receipt. Loading and peaceful resolutions use the same keys. */
export class CampaignLoot {
 constructor(private host:LootHost){}
 private get s(){return this.host.state();}
 private region(){return CAMPAIGN_LEVELS[this.s.area]?.region??(this.s.area.startsWith('U')?this.s.area.slice(0,2):'R1');}
 private resources(gold:number,iron:number){creditGold(this.s,gold);this.s.player.iron=Math.min(9999,this.s.player.iron+iron);}
 /** Called only by actual deaths, never a peaceful encounter resolution. */
 supplies(enemy:EnemyState){
  if(campaignFighter(enemy)?.drops===false)return;
  if(enemy.hp>0||enemy.phase!=='dead'||enemy.diedAt===undefined)return;
  const cycle=(enemy.respawnCount??0)+1,key=`supply-cycle:${this.s.area}:${enemy.id}`;
  if(Number(this.s.receipts[key]??0)>=cycle)return;
  this.s.receipts[key]=cycle;
  this.host.cultivation?.(enemy);
  const drop=supplyDrop(this.s.seed,this.s.area,enemy,cycle);
  if(drop)this.host.supply(drop.item,drop.count,supplySource(this.s.area,enemy.id,cycle),enemy);
  this.host.changed();
 }
 private draw(source:string,guaranteed=false,cycle?:number,at?:Point){const region=this.region(),rules=REGION_LOOT[region],pool=REGIONAL_LOOT_POOLS[region]??[];if(!rules||!pool.length)return;const key=`regional:${source}`;if(this.s.dropRolls[key])return;
 const drawKey=cycle===undefined?key:`${key}:${cycle}`,roll=equipmentRandomWord(this.s.seed,drawKey)%2147483646+1,pityKey=`pity:${region}`,misses=this.s.effectCounters[pityKey]??0,success=guaranteed||misses>=rules.pityMisses||roll/2147483647<rules.equipmentChance;let result='none';
 if(success){const grade=equipmentRandomWord(this.s.seed,drawKey+':grade')/4294967296,quality=grade<.65?'精良':grade<.99?'稀有':'史诗';
  const selected=quality==='史诗'?lifecycleBattlePool(chapterForArea(this.s.area),'史诗',this.s.combat.family??'WAR').map(id=>({id,weight:1})):pool.filter(p=>EQUIPMENT[p.id]?.quality===quality);
  const choices=selected.length?selected:pool.filter(p=>['精良','稀有'].includes(EQUIPMENT[p.id]?.quality));
  let pick=equipmentRandomWord(this.s.seed,drawKey+':item')/4294967296*choices.reduce((n,p)=>n+p.weight,0);const chosen=choices.find(p=>(pick-=p.weight)<0)??choices[choices.length-1];
  if(chosen){result=chosen.id;if((this.s.inventory[result]??0)>=equipmentStackLimit(result)||this.s.groundLoot.some(d=>d.item===result)){this.resources(rules.duplicateGold,2);this.s.receipts[`duplicate:${key}`]=result;}else this.host.grant(result,1,key,at);}if(!guaranteed)this.s.effectCounters[pityKey]=0;
 }else if(!guaranteed)this.s.effectCounters[pityKey]=misses+1;
 this.s.dropRolls[key]={roll,result};this.s.receipts[`roll:${key}`]=result;this.host.emit('loot_roll',result,{id:key});this.host.changed();
 }
 enemy(e:EnemyState){if(campaignFighter(e)?.drops===false)return;const hunt=MONSTER_BOSS_REWARDS[e.bossId??''];if(hunt){const source=`hunt:${this.s.area}:${e.id}`,key=`event:${source}`;if(this.s.receipts[key])return;this.s.receipts[key]=true;this.resources(0,hunt.iron);claimEconomyGold(this.s,`enemy:${this.s.area}:${e.id}`);if(!this.s.receipts['lifecycle:v3'])this.draw(source,true,undefined,e);this.host.emit('reward',`狩猎完成 · ${hunt.name}`,{id:source});this.host.changed();return;}if(e.bossId)return;let id=e.id;if(e.templateId==='U1-2'){const siblings=this.s.enemies.filter(n=>n.templateId==='U1-2').sort((a,b)=>a.id.localeCompare(b.id)),index=siblings.findIndex(n=>n.id===e.id);id=`beetle-pair:${Math.floor(index/2)}`;if(siblings.slice(Math.floor(index/2)*2,Math.floor(index/2)*2+2).some(n=>n.hp>0))return;}
 const key=`resources:${this.s.area}:${id}`;if(this.s.receipts[key])return;this.s.receipts[key]=true;const rules=REGION_LOOT[this.region()];if(!rules)return;this.resources(0,rules.ordinaryIron);claimEconomyGold(this.s,`enemy:${this.s.area}:${e.id}`);this.draw(`${this.s.area}:${id}`,false,undefined,e);this.host.changed();
 }
 hunt(e:EnemyState):boolean {
  const cycle=(e.respawnCount??0)+1,key=`hunt-cycle:${this.s.area}:${e.id}`;
  if(Number(this.s.receipts[key]??0)>=cycle)return false;
  this.s.receipts[key]=cycle;const rules=REGION_LOOT[this.region()];if(!rules)return false;
  this.resources(ordinaryGold(chapterForArea(this.s.area)),rules.ordinaryIron);
  // Keep one roll per slot; its deterministic seed changes only on a real respawn.
  const source=`hunt:${this.s.area}:${e.id}`,rollKey=`regional:${source}`;
  const previous=this.s.dropRolls[rollKey];
  // Preserve the original ownership proof when a previous draw granted a permanent item.
  if(previous&&previous.result!=='none'&&this.s.provenance[previous.result]===rollKey){
   const archive=`${rollKey}:owned:${previous.result}`;this.s.dropRolls[archive]=previous;this.s.receipts[`roll:${archive}`]=previous.result;
   this.s.provenance[previous.result]=archive;this.s.receipts[`grant:${archive}:${previous.result}`]=true;
  }
  if(previous&&this.s.groundLoot.some(d=>d.source===rollKey)){
   const archive=`${rollKey}:ground:${cycle-1}`;this.s.dropRolls[archive]=previous;this.s.receipts[`roll:${archive}`]=previous.result;
   for(const drop of this.s.groundLoot)if(drop.source===rollKey)drop.source=archive;
  }
  delete this.s.dropRolls[rollKey];
  this.draw(source,false,cycle,e);this.host.changed();return true;
 }
 encounter(at?:Point){const battle=campaignBattle(this.s.area);if(battle&&!this.s.flags[`campaign:battle:${battle.id}:complete`])return;const fixed=this.s.enemies.filter(e=>!e.respawnSeconds);if(!fixed.length||fixed.some(e=>e.hp>0))return;const elite=ELITE_LOOT[this.s.area],rules=REGION_LOOT[this.region()];if(!rules)return;if(elite){const source=elite.eventId,key=`event:${source}`;if(this.s.receipts[key])return;this.s.receipts[key]=true;this.resources(0,rules.eliteIron);if(!this.s.receipts['lifecycle:v3']){this.host.grant(elite.item,1,source,at);this.draw(source,true,undefined,at);}this.host.emit('reward',`精英事件 ${source} 已结算`,{id:source});this.host.changed();}
 if(OUTPOST_AREAS.includes(this.s.area)){const source=`outpost:${this.s.area}`,key=`event:${source}`;if(this.s.receipts[key])return;this.s.receipts[key]=true;this.resources(0,rules.outpostIron);this.draw(source,true,undefined,at);this.host.emit('reward','据点清算已完成',{id:source});this.host.changed();}
 }
}
