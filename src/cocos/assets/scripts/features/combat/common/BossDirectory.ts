import type {AreaDef,EnemySpawn,Point,WorldQuery} from '../../../core/Contracts';
import type {GameSession,EnemyState} from '../../../core/GameSession';
import type {NavigationTarget} from '../../automation/common/Automation';
import {availableRoute} from '../../automation/common/AutomationRoute';
import {playableArea} from '../../journey/data/ChapterJourney';
import {bossKind,BOSS_NOTICE_RANGE} from './BossAwareness';
import {CAMPAIGN_ENEMY_TEMPLATES} from '../../campaign/data/Campaign';
import {peacefulBossRetired} from '../../campaign/common/PeacefulBosses';

export const BOSS_LEVEL_WINDOW=5,BOSS_NOTICE_SECONDS=10;
export type BossAvailability='unseen'|'alive'|'cooldown'|'ready'|'waiting';
export interface BossEntry {
 key:string;area:string;spawn:EnemySpawn;name:string;kind:'boss'|'elite';level:number;
 place:string;state:BossAvailability;remaining:number;cycle:number;followed:boolean;refreshedAt:number;
 enemy?:EnemyState;
}
/** Type first, actual refresh time second, level third; identity breaks exact ties. */
export const compareBossEntries=(a:BossEntry,b:BossEntry)=>Number(b.kind==='boss')-Number(a.kind==='boss')||b.refreshedAt-a.refreshedAt||b.level-a.level||(a.key<b.key?-1:a.key>b.key?1:0);
export interface BossNotice {key:string;token:string;ready:boolean;elapsed:number}
const metres=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
export const bossClock=(seconds:number)=>{const whole=Math.max(0,Math.ceil(seconds));return `${String(Math.floor(whole/60)).padStart(2,'0')}:${String(whole%60).padStart(2,'0')}`;};

/** Reads authored content and existing saved clocks; never spawns or heals an enemy. */
export class BossDirectory {
 readonly roster:{key:string;area:string;spawn:EnemySpawn}[];
 private session:GameSession|undefined;
 private scanIn=0;
 private pending:BossNotice[]=[];
 private current:BossNotice|null=null;
 private entries:BossEntry[]=[];
 constructor(private readonly areas:Record<string,AreaDef>){
  this.roster=Object.values(areas).filter(a=>playableArea(a.id)).flatMap(a=>a.enemies.filter(e=>bossKind(e)).map(spawn=>({key:`${a.id}/${spawn.id}`,area:a.id,spawn})));
 }
 get count(){return this.entries.length;}
 list(game:GameSession):BossEntry[]{
  const s=game.state;
  return this.roster.flatMap(({key,area,spawn})=>{
   if(peacefulBossRetired(s,spawn.id))return [];
   const enemy=(s.area===area?s.enemies:s.encounters[area]??[]).find(e=>e.id===spawn.id),level=enemy?.level??spawn.level??1;
   // A visit, first sighting or suppressed hunting spawn is not a previous defeat.
   const cleared=s.receipts[`kill:${area}:${spawn.id}`]===true||(spawn.respawnSeconds?Number(s.receipts[`hunt-cycle:${area}:${spawn.id}`]??0)>0:!!spawn.bossId&&s.flags[`boss_defeated:${spawn.bossId}`]===true);
   if(!cleared||Math.abs(level-s.progression.level)>BOSS_LEVEL_WINDOW)return [];
   const defeated=enemy?enemy.hp<=0:cleared;
   const remaining=defeated?(spawn.respawnSeconds?Math.max(0,Math.ceil((enemy?.respawnAt??s.time)-s.time)):Math.ceil(game.bossLoot.view(spawn.bossId).remaining)):0;
   const state:BossAvailability=!defeated?enemy?'alive':'unseen':remaining?'cooldown':spawn.respawnSeconds?'waiting':'ready';
   const refreshedAt=state==='ready'?Number(s.receipts[`boss:v3:ready:${spawn.bossId}`]??0):enemy?.spawnedAt??0;
   return [{key,area,spawn,enemy,level,remaining,state,refreshedAt,cycle:enemy?.respawnCount??0,
    name:(CAMPAIGN_ENEMY_TEMPLATES[spawn.bossId??spawn.templateId??'']?.name??'灰披队长').split('·').pop()!,kind:bossKind(spawn)!,place:this.areas[area].name,followed:s.receipts[`boss-ui:follow:${key}`]===true}];
  }).sort(compareBossEntries);
 }
 find(game:GameSession,key:string){return this.list(game).find(e=>e.key===key);}
 follow(game:GameSession,key:string){const row=this.find(game,key);if(row)game.setBossPreference(key,!row.followed);}
 navigation(game:GameSession,key:string,world?:WorldQuery):NavigationTarget|null {
  const row=this.find(game,key);if(!row||availableRoute(game,this.areas,row.area)===null)return null;
  const area=this.areas[row.area],rematch=!row.spawn.respawnSeconds&&['ready','cooldown'].includes(row.state)?area.objects.find(o=>o.action==='growing_rematch'&&o.eventId===row.spawn.id):undefined;
  // Stop at the entrance without auto-interacting with a rematch object.
  if(rematch)return {area:row.area,point:{x:rematch.x,z:rematch.z},label:row.name,bossKey:key};
  const origin=row.enemy&&row.state==='alive'?row.enemy:row.spawn,local=game.state.area===row.area;
  const radius=['waiting','cooldown'].includes(row.state)?22:18,p=local?game.state.player:area.spawn;
  if(local&&!['waiting','cooldown'].includes(row.state)&&metres(p,origin)<=radius)return {area:row.area,point:{x:p.x,z:p.z},label:row.name,bossKey:key};
  const angle=Math.atan2(p.z-origin.z,p.x-origin.x);
  for(const offset of [0,1,-1,2,-2,3,-3,4]){
   const a=angle+offset*Math.PI/4,point={x:origin.x+Math.cos(a)*radius,z:origin.z+Math.sin(a)*radius};
   if(Math.abs(point.x)>area.width/2-1||Math.abs(point.z)>area.depth/2-1)continue;
   if(local&&world?.path&&!world.path(p,point).length)continue;
   return {area:row.area,point,label:row.name,bossKey:key};
  }
  return null;
 }
 /** Only visible gameplay time counts toward the ten-second notice lifetime. */
 update(game:GameSession,dt:number,visible:boolean):{entry:BossEntry;ready:boolean}|null {
  if(this.session!==game){this.session=game;this.scanIn=0;this.pending=[];this.current=null;this.entries=[];}
  this.scanIn-=Math.max(0,dt);
  if(this.scanIn<=0){
   this.scanIn=.5;this.entries=this.list(game);
   for(const row of this.entries){
    const ready=row.state==='ready',actual=row.state==='alive'&&row.area===game.state.area&&!!row.enemy&&(row.followed||metres(row.enemy,game.state.player)<=BOSS_NOTICE_RANGE);
    if(!ready&&!actual)continue;
    const token=`${ready?'ready':'alive'}:${row.cycle}`;
    if(game.state.receipts[`boss-ui:noticed:${row.key}`]===token||this.current?.key===row.key&&this.current.token===token||this.pending.some(n=>n.key===row.key&&n.token===token))continue;
    this.pending.push({key:row.key,token,ready,elapsed:0});
   }
   this.pending=this.pending.filter(n=>this.valid(n)).slice(0,this.roster.length);
   this.pending.sort((a,b)=>compareBossEntries(this.entries.find(e=>e.key===a.key)!,this.entries.find(e=>e.key===b.key)!));
  }
  if(this.current&&(!this.valid(this.current)||(visible&&(this.current.elapsed+=Math.max(0,dt))>=BOSS_NOTICE_SECONDS)))this.current=null;
  if(!this.current&&visible){
   this.current=this.pending.shift()??null;
   if(this.current)game.rememberBossNotice(this.current.key,this.current.token);
  }
  const entry=this.current&&this.entries.find(e=>e.key===this.current!.key);
  return visible&&entry?{entry,ready:this.current!.ready}:null;
 }
 private valid(notice:BossNotice){const row=this.entries.find(e=>e.key===notice.key);return !!row&&row.cycle===Number(notice.token.split(':')[1])&&(notice.ready?row.state==='ready':row.state==='alive'&&row.area===this.session?.state.area);}
 dismiss(){this.current=null;}
}
