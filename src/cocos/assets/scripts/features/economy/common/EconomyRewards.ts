import type {AreaDef} from '../../../core/Contracts';
import type {GameState} from '../../../core/GameSession';
import {campaignExperienceSources,campaignExperienceQuote} from '../../progression/data/CampaignExperience';
import {CAMPAIGN_EVENTS} from '../../campaign/data/CampaignEvents';
import {CAMPAIGN_STAGES} from '../../journey/data/CampaignStages';
import {chapterForArea,playableArea,journeyBossKey,PLAYABLE_CHAPTERS} from '../../journey/data/ChapterJourney';
import {CHAPTER_ECONOMY} from '../data/Economy';
import {creditGold} from './GoldWallet';

export interface EconomyReward {source:string;chapter:number;kind:'main'|'fixed'|'boss'|'exploration';gold:number}
const rewards=new Map<string,EconomyReward>(),aliases=new Map<string,string>();
const pool=(chapter:number,kind:EconomyReward['kind'],entries:{source:string;weight:number}[],gold:number)=>{
 const rows=entries.sort((a,b)=>a.source.localeCompare(b.source)),total=rows.reduce((n,e)=>n+e.weight,0);let before=0;
 for(const row of rows){const amount=Math.floor(gold*(before+row.weight)/total)-Math.floor(gold*before/total);rewards.set(row.source,{source:row.source,chapter,kind,gold:amount});before+=row.weight;}
};
/** Installs after the real world/XP catalog. Future chapters get no invented sources. */
export function installEconomyRewards(areas:Record<string,AreaDef>):void {
 rewards.clear();aliases.clear();
 for(const chapter of [1,2]){
  const policy=CHAPTER_ECONOMY[chapter-1],entries=campaignExperienceSources(chapter),mainBoss=PLAYABLE_CHAPTERS.find(c=>c.id===chapter),isBoss=(e:{area?:string;enemyId?:string})=>!!e.enemyId&&!!e.area&&e.area===mainBoss?.arena&&areas[e.area]?.enemies.some(enemy=>enemy.id===e.enemyId&&enemy.bossId===mainBoss?.boss);
  const earlyStages=new Set(CAMPAIGN_STAGES.filter(stage=>stage.chapter===chapter).slice(0,6).map(stage=>stage.id));
  pool(chapter,'main',entries.filter(e=>e.category==='main'&&!e.enemyId).map(e=>({source:e.source,weight:e.weight*(chapter===1&&e.stageId&&earlyStages.has(e.stageId)?2:1)})),policy.main);
  pool(chapter,'fixed',entries.filter(e=>e.category==='main'&&e.enemyId&&!isBoss(e)).map(e=>({source:e.source,weight:e.weight})),policy.fixed);
  const optional=new Map(entries.filter(e=>e.category==='exploration').map(e=>[e.source,{source:e.source,weight:e.weight}]));
  for(const area of Object.values(areas).filter(a=>playableArea(a.id)&&chapterForArea(a.id)===chapter))for(const object of area.objects){
   if(object.action!=='cache'||object.item!=='gold')continue;
   const source=`explore:${area.id}:${object.id}`,alias=object.id.includes('sign')?'design_container_coin_ch01_sign':`coin:${object.id}`;
   aliases.set(alias,source);if(!optional.has(source))optional.set(source,{source,weight:object.amount??1});
  }
  for(const event of Object.values(CAMPAIGN_EVENTS))if(playableArea(event.area)&&chapterForArea(event.area)===chapter&&event.gold&&!campaignExperienceQuote(event.experienceEvent??`campaign:${event.id}`).registered){const source=`campaign:${event.id}`;optional.set(source,{source,weight:event.gold});}
  if(chapter===1)optional.set('dice:inn-lockbox',{source:'dice:inn-lockbox',weight:12});
  pool(chapter,'exploration',Array.from(optional.values()),policy.exploration);
  rewards.set(journeyBossKey(chapter),{source:journeyBossKey(chapter),chapter,kind:'boss',gold:policy.boss});
 }
}
export const economyReward=(source:string)=>rewards.get(aliases.get(source)??source);
export const economyRewardCatalog=()=>Array.from(rewards.values()).map(row=>({...row}));
export function claimEconomyGold(s:GameState,source:string):number {
 const reward=economyReward(source);if(!reward)return 0;const key='economy:gold:'+reward.source;
 if(s.receipts[key]!==undefined)return 0;s.receipts[key]=reward.gold;creditGold(s,reward.gold);return reward.gold;
}
export const ordinaryGold=(chapter:number)=>CHAPTER_ECONOMY[chapter-1]?.ordinaryGold??0;
export function validateEconomyRewards(s:GameState):void {
 for(const [key,value]of Object.entries(s.receipts)){
  if(!key.startsWith('economy:gold:'))continue;
  const source=key.slice('economy:gold:'.length),reward=economyReward(source);
  let proof=s.receipts[source]===true||s.progression.xpReceipts[source]!==undefined;
  if(source.startsWith('enemy:'))proof=s.receipts['kill:'+source.slice(6)]===true;
  if(source.startsWith('explore:'))proof=s.receipts['interaction:'+source.slice(8)]===true;
  if(source==='dice:inn-lockbox')proof=!!s.dice.records['inn-lockbox']?.committed;
  if(!reward||value!==reward.gold||!proof)throw new Error('无效的金币来源凭证');
 }
}
