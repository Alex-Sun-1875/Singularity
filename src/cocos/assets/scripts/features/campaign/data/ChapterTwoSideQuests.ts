import type {GameState} from '../../../core/GameSession';
import type {CampaignEventDef} from './CampaignEvents';
import {SIDE_BOSSES,SIDE_BOSS_FORGE,SIDE_BOSS_ORDERS,SIDE_BOSS_BRIDGE} from './SideBosses';
import {sideQuestText as text,type ChapterTwoSideQuestMessageKey} from '../locales/ChapterTwoSideQuestText';
import {EARLY_EXISTING_SIDE_EVENTS} from './EarlyChapterContent';

type StepText=`${'forge'|'orders'|'bridge'}.${'request'|'inspect'|'boss'|'settle'}`;
const event=(id:string,area:string,key:StepText,requires:string[],sets:string[],extra:Partial<CampaignEventDef>={}):CampaignEventDef=>({id,area,label:text((key+'.title') as ChapterTwoSideQuestMessageKey),description:text((key+'.body') as ChapterTwoSideQuestMessageKey),requires,sets,optional:true,choices:extra.choices??[{id:'continue',label:text(key.endsWith('inspect')?'action.inspect':key.endsWith('boss')?'action.evidence':'action.continue'),text:text((key+'.done') as ChapterTwoSideQuestMessageKey),sets:[]}],...extra});
// Uses existing models. Shared actor IDs keep each request and settlement on one NPC.
const ida={actor:'side-npc-ida',actorModel:'mine-worker',at:{x:-20,z:-16}};
const luen={actor:'side-npc-luen',actorModel:'mine-worker',at:{x:-22,z:-26}};
const ryn={actor:'side-npc-ryn',actorModel:'raider-shield',at:{x:-24,z:-16}};
const bossEvidence=(bossId:string,key:'forge'|'orders'|'bridge')=>({at:SIDE_BOSSES.find(boss=>boss.bossId===bossId)!.evidencePoint,prerequisiteHints:{['boss_defeated:'+bossId]:text((key+'.requireBoss') as ChapterTwoSideQuestMessageKey)}});
export const CHAPTER_TWO_SIDE_QUEST_EVENTS:CampaignEventDef[]=[
 event('side-forge-request','H01','forge.request',[],['chapter2-side:forge:heard'],ida),
 event('side-forge-inspect','H04','forge.inspect',['chapter2-side:forge:heard'],['chapter2-side:forge:inspected'],{at:{x:-20,z:-12}}),
 event('side-forge-boss','H05','forge.boss',['chapter2-side:forge:inspected','boss_defeated:'+SIDE_BOSS_FORGE],['chapter2-side:forge:evidence'],bossEvidence(SIDE_BOSS_FORGE,'forge')),
 event('side-forge-settle','H01','forge.settle',['chapter2-side:forge:heard','chapter2-side:forge:evidence'],['chapter2-side:forge:complete'],{...ida,gold:120,iron:8,runes:1,experience:900,choices:[
  {id:'tools-first',label:text('forge.tools.label'),text:text('forge.tools.done'),sets:['chapter2-side:forge:public-tools']},
  {id:'pit-first',label:text('forge.pit.label'),text:text('forge.pit.done'),sets:['chapter2-side:forge:safe-pit']},
 ]}),
 event('side-orders-request','U1-07','orders.request',[],['chapter2-side:orders:heard'],luen),
 event('side-orders-inspect','U1-08','orders.inspect',['chapter2-side:orders:heard'],['chapter2-side:orders:inspected'],{at:{x:-16,z:-20}}),
 event('side-orders-boss','U1-09','orders.boss',['chapter2-side:orders:inspected','boss_defeated:'+SIDE_BOSS_ORDERS],['chapter2-side:orders:evidence'],bossEvidence(SIDE_BOSS_ORDERS,'orders')),
 event('side-orders-settle','U1-07','orders.settle',['chapter2-side:orders:heard','chapter2-side:orders:evidence'],['chapter2-side:orders:complete'],{...luen,gold:100,iron:6,runes:2,experience:1000,choices:[
  {id:'seal-core',label:text('orders.seal.label'),text:text('orders.seal.done'),sets:['chapter2-side:orders:sealed']},
  {id:'read-only',label:text('orders.echo.label'),text:text('orders.echo.done'),sets:['chapter2-side:orders:read-only']},
 ]}),
 event('side-bridge-request','H07','bridge.request',[],['chapter2-side:bridge:heard'],ryn),
 event('side-bridge-inspect','H07','bridge.inspect',['chapter2-side:bridge:heard'],['chapter2-side:bridge:inspected'],{at:{x:20,z:-24}}),
 event('side-bridge-boss','H07','bridge.boss',['chapter2-side:bridge:inspected','boss_defeated:'+SIDE_BOSS_BRIDGE],['chapter2-side:bridge:evidence'],bossEvidence(SIDE_BOSS_BRIDGE,'bridge')),
 event('side-bridge-settle','H07','bridge.settle',['chapter2-side:bridge:heard','chapter2-side:bridge:evidence'],['chapter2-side:bridge:complete'],{...ryn,gold:140,iron:8,experience:900,choices:[
  {id:'people-first',label:text('bridge.people.label'),text:text('bridge.people.done'),sets:['chapter2-side:bridge:people-first']},
  {id:'scheduled-freight',label:text('bridge.freight.label'),text:text('bridge.freight.done'),sets:['chapter2-side:bridge:scheduled-freight']},
 ]}),
 ...EARLY_EXISTING_SIDE_EVENTS.filter(event=>event.id.startsWith('side-')),
];
export const CHAPTER_TWO_SIDE_QUESTS=[
 {id:'side-forge',chapter:2,name:text('forge.name'),reward:text('forge.reward'),steps:['side-forge-request','side-forge-inspect','side-forge-boss','side-forge-settle','side-forge-bench-test']},
 {id:'side-orders',chapter:2,name:text('orders.name'),reward:text('orders.reward'),steps:['side-orders-request','side-orders-inspect','side-orders-boss','side-orders-settle','side-orders-isolate-test']},
 {id:'side-bridge',chapter:2,name:text('bridge.name'),reward:text('bridge.reward'),steps:['side-bridge-request','side-bridge-inspect','side-bridge-boss','side-bridge-settle','side-bridge-return-check']},
] as const;
/** Completed campaign dialogue already persists the exact selected outcome. */
export function chapterTwoSideQuestOutcome(s:Pick<GameState,'receipts'>,id:string):string {const quest=CHAPTER_TWO_SIDE_QUESTS.find(q=>q.id===id);if(!quest)return '';for(const step of [...quest.steps].reverse()){if(s.receipts['campaign:'+step]!==true)continue;const selected=s.receipts['campaign:choice:'+step],result=CHAPTER_TWO_SIDE_QUEST_EVENTS.find(e=>e.id===step)?.choices?.find(c=>c.id===selected&&!c.retry);if(result)return result.text;}return '';}
/** Side quests follow chapter access and their own steps, independently of the boss. */
export function chapterTwoSideQuestEventVisible(id:string,s:Pick<GameState,'progression'|'flags'>):boolean {const event=CHAPTER_TWO_SIDE_QUEST_EVENTS.find(e=>e.id===id);if(!event)return true;if(!s.progression.secondChapter||event.requires?.some(flag=>!flag.startsWith('boss_defeated:')&&!s.flags[flag]))return false;return id.endsWith('-settle')||!(event.sets??[]).every(flag=>s.flags[flag]);}
/** Evidence stays inspectable while the world boss is alive; navigation can target that boss first. */
export function chapterTwoSideQuestRequiredBoss(eventId:string):string|undefined {return CHAPTER_TWO_SIDE_QUEST_EVENTS.find(event=>event.id===eventId)?.requires?.find(flag=>flag.startsWith('boss_defeated:'))?.slice(14);}
export function chapterTwoSideQuestNpcVisible(id:string,s:Pick<GameState,'progression'>):boolean {return !['side-npc-ida','side-npc-luen','side-npc-ryn'].includes(id)||s.progression.secondChapter;}
/** Previous solutions change the response, never the availability or reward. */
export function chapterTwoSideQuestResponse(s:Pick<GameState,'receipts'>,id:string):string {if(id==='side-forge'){const choice=s.receipts['chapter2:quarry-rescue:choice'];return text(choice==='witness'?'response.witness':choice==='ledger'?'response.ledger':'response.generic');}if(id==='side-orders'){const method=s.receipts['chapter2:oath-array:resolved'];return method==='mechanism'?text('response.mechanism'):method==='battle'?text('response.battle'):'';}if(id==='side-bridge'){const method=s.receipts['chapter2:ridge-post:resolved'];return method==='parley'?text('response.parley'):method==='battle'?text('response.ridgeBattle'):'';}return '';}
