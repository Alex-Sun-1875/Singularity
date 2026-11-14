import type {AreaDef,EnemySpawn,Point} from '../../../core/Contracts';
import {CAMPAIGN_ENEMY_TEMPLATES} from './Campaign';
import {campaignText} from '../locales';
export interface CampaignWave {label:string;enemies:EnemySpawn[];experience:{id:string;amount:number}[]}
export interface CampaignBattle {id:string;area:string;title:string;waves:CampaignWave[]}
interface CampaignFighter {templateId:string;previousTemplateId?:string;group:string;maxHp:number;damage:number;drops:boolean;deferExperience:boolean}
const fighters=new Map<string,CampaignFighter>();
/** Content-owned tuning; no reward or multiplier fields are trusted from a save. */
export const campaignFighter=(e:Pick<EnemySpawn,'id'|'templateId'>)=>{const tuned=fighters.get(e.id);return tuned&&(tuned.templateId===e.templateId||tuned.previousTemplateId!==undefined&&tuned.previousTemplateId===e.templateId)?tuned:undefined;};
export const combatGroup=(e:Pick<EnemySpawn,'id'|'templateId'|'packId'>)=>e.packId??campaignFighter(e)?.group;
const fullHealth=(e:EnemySpawn)=>{const def=CAMPAIGN_ENEMY_TEMPLATES[e.templateId??''];return Math.round((def?.baseHp??def?.hp??e.hp??72)*(1+.14*((e.level??def?.level??1)-1)));};
const unit=(id:string,templateId:string,x:number,z:number,level:number):EnemySpawn=>({id,kind:templateId.includes('SPITTER')?'archer':'raider',templateId,contentId:templateId,x,z,level});
/** More bodies share the original two units' HP and XP budgets. Only those
 * original IDs roll equipment, currency and supplies; the new bodies cannot
 * advance loot pity or the forty-kill repeatable-hunting reward. */
function swarm(label:string,originals:EnemySpawn[],count:number,filler:string|readonly string[],veteran?:string,previousFiller?:string):CampaignWave {
 const enemies=[...originals];
 const choices=typeof filler==='string'?[filler]:filler;
 for(let i=enemies.length;i<count;i++)enemies.push(unit(`${originals[0].id}-swarm-${i}`,choices[(i-originals.length)%choices.length],0,0,originals[0].level!));
 const health=originals.reduce((n,e)=>n+fullHealth(e),0),weights=enemies.map(e=>e.id===veteran?3:1),total=weights.reduce((n,w)=>n+w,0);
 let assigned=0;
 for(const [i,e]of enemies.entries()){
  const maxHp=i===enemies.length-1?health-assigned:Math.floor(health*weights[i]/total);assigned+=maxHp;
  fighters.set(e.id,{templateId:e.templateId!,...(i>=originals.length&&previousFiller?{previousTemplateId:previousFiller}:{}),group:`battle:${originals[0].id}`,maxHp,damage:i<originals.length?1:.65,drops:i<originals.length,deferExperience:true});
 }
 return {label,enemies,experience:originals.map(e=>({id:e.id,amount:20+8*(e.level!-1)}))};
}
export const CAMPAIGN_BATTLES:CampaignBattle[]=[
 {id:'mill-defense',area:'S07',title:'断轮磨坊攻防',waves:[swarm(campaignText('wave.mill'),[unit('campaign-mill-hound-a','BEAST_DUSK_HOUND',-9,3,4),unit('campaign-mill-hound-b','BEAST_RED_FANG',9,5,4)],5,['BEAST_BRAMBLE_BOAR','BEAST_CAVE_SPIDER','BEAST_RED_FANG'],undefined,'BEAST_RED_FANG')]},
 {id:'workshop-defense',area:'H03',title:'熔镜工位保卫战',waves:[swarm(campaignText('wave.workshopMachine'),[unit('campaign-workshop-crawler','MACHINE_CINDER_CRAWLER',-9,4,11),unit('campaign-workshop-spitter','BEAST_ASH_SPITTER',9,6,11)],5,['BEAST_ROCK_SCORPION','BEAST_BRAMBLE_BOAR','BEAST_SCREE_HOUND'],'campaign-workshop-crawler','BEAST_SCREE_HOUND'),swarm(campaignText('wave.workshopBeasts'),[unit('campaign-workshop-hound-a','BEAST_SCREE_HOUND',-10,8,11),unit('campaign-workshop-hound-b','BEAST_SCREE_HOUND',10,8,11)],5,['BEAST_CAVE_SPIDER','BEAST_ROCK_SCORPION','BEAST_SCREE_HOUND'],undefined,'BEAST_SCREE_HOUND')]},
 {id:'oath-line',area:'U1-06',title:'三誓供能线争夺',waves:[swarm(campaignText('wave.oath'),[unit('campaign-oath-crawler','MACHINE_CINDER_CRAWLER',-8,6,16),unit('campaign-oath-scarab','MACHINE_SCRAP_SCARAB',8,6,16)],8,['BEAST_CAVE_SPIDER','MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB'],'campaign-oath-crawler','MACHINE_SCRAP_SCARAB')]},
];
export const campaignBattle=(area:string)=>CAMPAIGN_BATTLES.find(b=>b.area===area);
export const CAMPAIGN_WAVE_INTERVAL=.7;
/** Match hunting packs' 20% wider spacing for fixed squads and reinforcements. */
export const CAMPAIGN_FORMATION:readonly Point[]=[{x:-1.08,z:-1.56},{x:1.08,z:-1.56},{x:-2.16,z:0},{x:0,z:0},{x:2.16,z:0},{x:0,z:1.56},{x:-1.08,z:1.56},{x:1.08,z:1.56}];

/** Compact the existing fixed squads along the incoming route. Their identity,
 * level, first-kill XP and loot receipts are retained. Wildlife is untouched. */
export function installCampaignCombat(areas:Record<string,AreaDef>){
 const approaches:Record<string,string>={S07:'S04',S08:'S07',S09:'S08','U1-03':'U1-01',H03:'H02',H04:'H02',H07:'H04'};
 for(const [id,from]of Object.entries(approaches)){
  const area=areas[id],fixed=area.enemies.filter(e=>!e.respawnSeconds&&!e.bossId),entry=areas[from].exits.find(e=>e.to===id)?.entry??area.spawn;
  if(!fixed.length)continue;
  const d=Math.hypot(entry.x,entry.z)||1,forward={x:-entry.x/d,z:-entry.z/d},desired={x:entry.x+forward.x*32,z:entry.z+forward.z*32};
  const ordered=[...fixed].sort((a,b)=>Number(a.kind==='archer')-Number(b.kind==='archer'));
  const positions=(center:Point)=>ordered.map((_,i)=>{const f=CAMPAIGN_FORMATION[i];return {x:center.x+forward.z*f.x+forward.x*f.z,z:center.z-forward.x*f.x+forward.z*f.z};});
  const valid=(p:Point)=>Math.abs(p.x)<area.width/2-4&&Math.abs(p.z)<area.depth/2-4&&Math.hypot(p.x-area.spawn.x,p.z-area.spawn.z)>12&&!area.obstacles.some(o=>Math.abs(p.x-o.x)<o.width/2+1.2&&Math.abs(p.z-o.z)<o.depth/2+1.2)&&!area.enemies.some(e=>e.respawnSeconds&&Math.hypot(p.x-e.x,p.z-e.z)<5)&&!area.objects.some(o=>(o.actor||o.action==='checkpoint')&&Math.hypot(p.x-o.x,p.z-o.z)<8)&&!area.exits.some(e=>Math.hypot(p.x-e.x,p.z-e.z)<16);
  const candidates=[desired];for(let r=3;r<=24;r+=3)for(let a=0;a<12;a++)candidates.push({x:desired.x+Math.cos(a*Math.PI/6)*r,z:desired.z+Math.sin(a*Math.PI/6)*r});
  const center=candidates.find(c=>positions(c).every(valid));
  if(!center)throw new Error(`No safe campaign squad: ${id}`);
  const points=positions(center);
  for(const [i,e]of ordered.entries()){
   Object.assign(e,points[i]);const heavy=e.kind==='shield'||e.templateId==='U1-4';
   fighters.set(e.id,{templateId:e.templateId!,group:`battle:${id}:opening`,maxHp:Math.round(fullHealth(e)*(heavy?.95:.82)),damage:1,drops:true,deferExperience:false});
  }
 }
}
