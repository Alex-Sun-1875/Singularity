import type {EnemySpawn,Point} from '../../../core/Contracts';
import type {GameState,EnemyState} from '../../../core/GameSession';
import {CAMPAIGN_SCENES,campaignBattle,campaignScene} from '../data/CampaignScenes';
import {CAMPAIGN_WAVE_INTERVAL} from '../../campaign/data/CampaignBattles';
import {chapterTwoBattleStopped} from '../../campaign/common/ChapterTwoEncounters';
import {campaignText as text} from '../../campaign/locales';

interface Host {state():GameState;spawnWave(enemies:EnemySpawn[]):EnemyState[];experience(source:string,amount:number):void;changed():void;emit(type:string,text?:string,extra?:Record<string,unknown>):void}
const distance=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
/** Durable presentation receipts are independent of quest and equipment gates. */
export class CampaignDirector {
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 private queue(id:string){if(this.s.receipts[`campaign:seen:${id}`]||this.s.receipts[`campaign:queued:${id}`])return;this.s.receipts[`campaign:queued:${id}`]=true;this.host.changed();this.host.emit('campaign_scene',undefined,{id});}
 pending(){return CAMPAIGN_SCENES.filter(d=>d.area===this.s.area&&this.s.receipts[`campaign:queued:${d.id}`]&&!this.s.receipts[`campaign:seen:${d.id}`]);}
 finish(id:string){const d=campaignScene(id);if(!d||d.area!==this.s.area||!this.s.receipts[`campaign:queued:${id}`])return false;this.s.receipts[`campaign:seen:${id}`]=true;this.host.changed();return true;}
 replay(id:string){const d=campaignScene(id);return d?.area===this.s.area&&!!this.s.receipts[`campaign:seen:${id}`];}
 task(id:string){for(const scene of CAMPAIGN_SCENES)if(scene.trigger==='task'&&scene.task===id&&scene.area===this.s.area)this.queue(scene.id);}
 tick(){
  const s=this.s;if(s.status==='dead')return;
  for(const d of CAMPAIGN_SCENES){if(d.area!==s.area||d.trigger==='task')continue;
   const boss=d.boss?s.enemies.find(e=>e.bossId===d.boss):undefined;
   if(d.trigger==='victory'){if(boss&&boss.hp<=0&&s.receipts[`kill:${s.area}:${boss.id}`])this.queue(d.id);}
   else if((!d.boss||boss&&boss.hp>0)&&(!d.at&&!boss||distance(s.player,boss??d.at!)<=(d.radius??999)))this.queue(d.id);
  }
  const b=campaignBattle(s.area);if(!b||chapterTwoBattleStopped(s,s.area)||s.flags[`campaign:battle:${b.id}:complete`])return;
  const fixed=s.enemies.filter(e=>!e.respawnSeconds);if(!fixed.length||fixed.some(e=>e.hp>0))return;
  // Preserve the original XP source IDs. Old in-progress waves that already
  // awarded an original kill cannot collect it twice after this content update.
  for(const [i,w]of b.waves.entries())if(s.receipts[`campaign:wave:${b.id}:${i}`])for(const reward of w.experience){
   if(s.receipts[`kill:${s.area}:${reward.id}`])this.host.experience(`enemy:${s.area}:${reward.id}`,reward.amount);
  }
  const wave=b.waves.findIndex((_,i)=>!s.receipts[`campaign:wave:${b.id}:${i}`]);
  if(wave<0){s.flags[`campaign:battle:${b.id}:complete`]=true;s.receipts[`campaign:battle-time:${b.id}`]=s.time;this.host.changed();this.host.emit('campaign_battle',text('battle.complete',{title:b.title}),{id:b.id,complete:true});return;}
  const readyKey=`campaign:wave-ready:${b.id}:${wave}`;
  if(s.receipts[readyKey]===undefined){s.receipts[readyKey]=s.time+CAMPAIGN_WAVE_INTERVAL;this.host.changed();this.host.emit('campaign_wave_ready',text('battle.incoming',{title:b.title}),{id:b.id,wave:wave+2});return;}
  if(s.time<Number(s.receipts[readyKey]))return;
  const def=b.waves[wave],missing=def.enemies.filter(authored=>!s.enemies.some(e=>e.id===authored.id)),spawned=this.host.spawnWave(missing);if(spawned.length!==missing.length){s.receipts[readyKey]=s.time+.5;this.host.changed();return;}s.enemies.push(...spawned);
  s.receipts[`campaign:wave:${b.id}:${wave}`]=true;s.receipts[`campaign:wave-time:${b.id}:${wave}`]=s.time;this.host.changed();this.host.emit('campaign_battle',`${b.title} · ${def.label}`,{id:b.id,wave:wave+2,total:b.waves.length+1,enemies:def.enemies.map(e=>e.id)});
 }
 battleReady(){const b=campaignBattle(this.s.area);return !b||chapterTwoBattleStopped(this.s,this.s.area)||!!this.s.flags[`campaign:battle:${b.id}:complete`];}
 battleHint(){const b=campaignBattle(this.s.area);if(!b||chapterTwoBattleStopped(this.s,this.s.area)||this.s.flags[`campaign:battle:${b.id}:complete`])return '';const waves=b.waves.filter((_,i)=>this.s.receipts[`campaign:wave:${b.id}:${i}`]).length,alive=this.s.enemies.filter(e=>!e.respawnSeconds&&e.hp>0).length;return alive?text('battle.progress',{title:b.title,wave:waves+1,total:b.waves.length+1,alive}):text('battle.incoming',{title:b.title});}
}
