import {CAMPAIGN_MAX_LEVEL,attributePointBudget} from '../../progression/data/CampaignProgression';
import type {AreaDef,GameEvent,Point,WorldQuery} from '../../../core/Contracts';
import {GameSession} from '../../../core/GameSession';
import {synchronizeResource} from '../../combat/common/ClassResource';
import {COMBAT_SKILLS,COMBAT_SKILL_LIST} from '../../combat/data/PureSkills';
import {COMBAT_LOADOUTS,prepareCombatLoadout} from '../../progression/common/CombatLoadouts';
import {baseMaxHp,cumulativeXp,unlockSkills,skillRankSpent,totalSkillPoints} from '../../progression/common/Progression';

export type TargetFormation='single'|'cluster'|'line'|'horde';
export const TRAINING_MONSTER_COUNTS=[5,10,20] as const;
const START:Point={x:0,z:-8};
/** Kept outside the campaign atlas and persistence: entering is a session swap. */
export const TRAINING_AREA:AreaDef={id:'TRAINING',name:'技能靶场',subtitle:'独立试放 · 临时角色',kind:'interior',palette:'stone',width:48,depth:48,spawn:START,atlas:{x:0,z:0},checkpoint:true,exits:[],objects:[],buildings:[],obstacles:[],enemies:Array.from({length:5},(_,i)=>({id:`training:target:${i}`,kind:'raider',trainingDummy:true,level:CAMPAIGN_MAX_LEVEL,hp:1000000,x:0,z:0}))};

const GROUP_AREAS:Record<number,AreaDef>=Object.fromEntries(TRAINING_MONSTER_COUNTS.map(count=>[count,{...TRAINING_AREA,enemies:Array.from({length:count},(_,i)=>({id:`training:monster:${i}`,kind:(["raider","raider","shield","raider","archer"] as const)[i%5],trainingEnemy:true,level:CAMPAIGN_MAX_LEVEL,x:0,z:0}))}]));

/** Only practice sessions own dummies. Damage, accuracy, projectiles, statuses
 * and displacement still run through GameSession / PureCombat unchanged. */
export class TrainingRange {
 returnNotice?:string;
 monsterCount:number=10;
 get groupMode(){return this.formation==='horde';}
 get area():AreaDef{return this.groupMode?GROUP_AREAS[this.monsterCount]??GROUP_AREAS[10]:TRAINING_AREA;}
 readonly session:GameSession;
 formation:TargetFormation='single';distance=4;unlimitedResource=true;retaliate=false;
 damage=0;hits=0;misses=0;criticalHits=0;lastDamage=0;lastSkill='';
 private startedAt:number|null=null;
 private targets=new Set<string>();
 readonly framingPoints:Point[]=[];
 constructor(world:WorldQuery){
  const game=this.session=new GameSession(73014,world),s=game.state,p=s.progression;
  p.totalXp=cumulativeXp(CAMPAIGN_MAX_LEVEL);p.xpReceipts['training']=p.totalXp;p.level=CAMPAIGN_MAX_LEVEL;p.ultimateGiftClaimed=true;
  // A stable, legal attribute budget makes rank comparisons reproducible.
  const budget=attributePointBudget(p.level),each=Math.floor(budget/4);
  p.attributes={strength:10+each,dexterity:10+each,intellect:10+each,vitality:10+budget-3*each};p.unspentPoints=0;
  unlockSkills(p,true);
  for(const skill of COMBAT_SKILL_LIST)p.learned[skill.id]=1;
  p.skillPoints=totalSkillPoints(p)-Object.values(p.learned).reduce((n,r)=>n+skillRankSpent(r),0);
  s.inventory.W01=1;s.inventory.W07=1;s.inventory.W11=1;
  s.provenance.W01=s.provenance.W07=s.provenance.W11='training';
  s.equipment.weapon=COMBAT_LOADOUTS.FIR.weapon;prepareCombatLoadout(s.combat,s.equipment.weapon,p,'FIR');
  s.player.maxHp=baseMaxHp(p);game.enter(this.area);this.reset();
 }
 reset(){
  const game=this.session,s=game.state;
  game.resetCombatTransient();s.flags[`visited:${TRAINING_AREA.id}`]=false;game.enter(this.area,START);
  s.status='playing';s.player.angle=0;s.player.hp=s.player.maxHp;s.player.shield=0;
  synchronizeResource(s);s.player.focus=s.player.maxFocus;s.player.hurtTime=0;
  s.effectCounters={};s.movedDistance=0;s.player.healthPotions=3;s.player.staminaPotions=2;s.player.manaPotions=2;s.player.focusPotions=2;
  s.cooldowns={};s.combat.cooldowns={};s.combat.ultimateLock=0;s.combat.charge=0;delete s.combat.engagement;
  s.groundLoot=[];s.fireZones=[];s.projectiles=[];s.enemyHazards=[];
  const offsets:Point[]=this.groupMode?Array.from({length:this.area.enemies.length},(_,i)=>({x:((i%5)-2)*1.6,z:Math.floor(i/5)*1.8})):this.formation==='single'?[{x:0,z:0}]:this.formation==='line'?Array.from({length:5},(_,i)=>({x:0,z:i*2})):[{x:0,z:0},{x:-1.4,z:0},{x:1.4,z:0},{x:-.7,z:1.5},{x:.7,z:1.5}];
  this.targets.clear();
  s.enemies.forEach((e,i)=>{
   const offset=offsets[i];e.x=START.x+(offset?.x??0);e.z=START.z+this.distance+(offset?.z??0);
   e.trainingAttacks=!!offset&&(this.groupMode||this.retaliate);e.hp=offset?e.maxHp:0;e.phase=offset?'idle':'dead';e.phaseTime=0;e.angle=Math.PI;e.targetAngle=Math.PI;e.combat=undefined;
   e.markedUntil=0;e.lightningUntil=0;e.pushImmuneUntil=0;e.staggerProtectedUntil=0;delete e.diedAt;
   if(offset)this.targets.add(e.id);
  });
  // Keep the initial wave in view throughout casts and deaths. Bounds change
  // only when the wave is reset; spell release never pumps the camera zoom.
  this.framingPoints.length=0;
  if(this.groupMode){const xs=s.enemies.map(e=>e.x),zs=s.enemies.map(e=>e.z);for(const x of [Math.min(...xs),Math.max(...xs)])for(const z of [Math.min(...zs),Math.max(...zs)])this.framingPoints.push({x,z});}
  this.damage=0;this.hits=0;this.misses=0;this.criticalHits=0;this.lastDamage=0;this.lastSkill='';this.startedAt=null;s.revision++;
 }
 prepareFrame(){
  const s=this.session.state;if(this.unlimitedResource)s.player.focus=s.player.maxFocus;
  // Infinite health without a death/reward cycle. Real damage events retain hpLost.
  if(!this.groupMode)for(const e of s.enemies)if(this.targets.has(e.id))e.hp=e.maxHp;
 }
 observe(events:readonly GameEvent[]){
  for(const event of events){
   if(event.type==='skill_release')this.lastSkill=COMBAT_SKILLS[String(event.skillId)]?.name??String(event.skillId);
   if(!this.targets.has(String(event.id)))continue;
   if(event.type==='hit'){
    const value=Number(event.hpLost);if(!Number.isFinite(value)||value<=0)continue;
    this.startedAt??=this.session.state.time;this.damage+=value;this.lastDamage=value;this.hits++;if(event.critical===true)this.criticalHits++;
   }else if(event.type==='miss')this.misses++;
  }
 }
 get elapsed(){return this.startedAt===null?0:Math.max(0,this.session.state.time-this.startedAt);}
 get dps(){return this.damage/Math.max(1,this.elapsed);}
 get targetCount(){return this.targets.size;}
 get remainingMonsters(){return this.session.state.enemies.filter(e=>this.targets.has(e.id)&&e.hp>0).length;}
 get defeatedMonsters(){return this.targetCount-this.remainingMonsters;}
}
