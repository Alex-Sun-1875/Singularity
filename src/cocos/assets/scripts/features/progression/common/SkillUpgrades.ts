import {PURE_SKILLS,type CombatSkillRank} from '../../combat/data/PureSkills';
import {allocatedSkillRank} from './Progression';
import type {EnemyState,GameState} from '../../../core/GameSession';
import type {CombatCast,CombatStatus} from '../../combat/common/PureCombat';

type Values=Record<string,number>;
type Host={state():GameState;status(e:EnemyState):CombatStatus;poise(e:EnemyState,value:number,skillId:string):void};
const effects=(r?:CombatSkillRank):Values=>r?.upgradeEffects??{};
const BASIC_KEYS=['slashBasic','shieldBasic','evadeBasic','hunterBasic'];

/** Rank-specific additions share the existing cast, hit, shield and buff paths. */
export class SkillUpgrades {
 private basics=new Map<string,number>();
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 private get b(){return this.s.combat.buffs;}
 private ready(key:string,seconds:number){const k='upgrade:'+key;if((this.s.combat.cooldowns[k]??0)>0)return false;this.s.combat.cooldowns[k]=seconds;return true;}
 passive(c:CombatCast|undefined,id:string):Values {
  if(c){const value=c.passives[id];return value?effects(PURE_SKILLS[id]?.ranks.find(r=>r.primaryValue===value)):{};}
  return this.s.combat.passiveSlots.includes(id)?effects(allocatedSkillRank(this.s.progression,id)):{};
 }
 private grant(key:string,value:number,seconds:number){this.b[key]=value;this.b[key+'Until']=this.s.time+seconds;}
 private take(key:string):number {const value=(this.b[key+'Until']??0)>this.s.time?this.b[key]??0:0;this.b[key]=0;return value;}
 prepare(c:CombatCast){
  const d=PURE_SKILLS[c.skillId],u:Values=c.upgrades={};
  if(d.style==='WAR'&&d.offensive&&this.b.lastWarSkill&&this.b.lastWarSkill!==Object.keys(PURE_SKILLS).indexOf(c.skillId)+1)c.damageBonus+=(this.passive(c,'WAR_P1').alternatePercent??0)/100;
  if(c.skillId==='WAR_01')u.breakPercent=this.take('nextSlashBreak');
  if(c.skillId==='WAR_03')u.shieldPercent=this.take('nextIronShield');
  if(c.skillId==='WAR_05'&&this.s.player.shield>0)u.shieldFinisher=1;
  if(c.skillId==='THU_01')c.damageBonus+=this.take('nextSpear')/100;
  if(c.skillId==='FIR_01'||c.skillId==='FIR_02'&&effects(c.rank).refreshBurn&&this.b.shieldMeteorRefresh)u.burnSeconds=this.take('shieldBurn');
  if(d.style==='BOW'&&(this.b.stationaryFor??0)>=.4){u.stationary=1;u.stationaryBreak=this.passive(c,'BOW_P1').stationaryBreakPercent??0;u.markedCritical=this.passive(c,'BOW_P1').markedCriticalPercent??0;}
 }
 damage(c:CombatCast,e:EnemyState,segment:number):number {
  const fx=effects(c.rank),burning=this.host.status(e).burnUntil>this.s.time;let n=0;
  if(burning){n+=fx.burningBonusPercent??0;if(PURE_SKILLS[c.skillId].style==='FIR')n+=this.passive(c,'FIR_P1').burningBonusPercent??0;if(segment===c.rank.authoredDamageHits-1)n+=fx.finalBurningPercent??0;}
  if(c.upgrades?.shieldFinisher&&segment===c.rank.authoredDamageHits-1)n+=fx.shieldFinisherPercent??0;
  return n/100;
 }
 breakPercent(c:CombatCast,e:EnemyState,segment:number):number {
  let n=c.upgrades?.breakPercent??0;
  if(segment===0&&c.breakHits.length===0)n+=c.upgrades?.stationaryBreak??0;
  const st=this.host.status(e),b=this.b;
  if(PURE_SKILLS[c.skillId].style==='BOW'&&c.skillId!=='BOW_04'&&st.hunterMarkUntil>this.s.time&&(b['markBreakUntil:'+e.id]??0)>this.s.time){n+=b['markBreak:'+e.id]??0;b['markBreak:'+e.id]=0;}
  return n;
 }
 finalBreak(c:CombatCast,segment:number):number {return segment===c.rank.authoredDamageHits-1?(effects(c.rank).finalBreakPercent??0):0;}
 mark(c:CombatCast,e:EnemyState){const n=effects(c.rank).markBreakPercent??0;this.b['markBreak:'+e.id]=n;this.b['markBreakUntil:'+e.id]=this.host.status(e).hunterMarkUntil;}
 hit(c:CombatCast,e:EnemyState,segment:number){
  const fx=effects(c.rank),time=this.s.time,d=PURE_SKILLS[c.skillId],once=(key:string)=>{key='upgrade:'+key;if(c.procs.includes(key))return false;c.procs.push(key);return true;};
  if(d.style==='WAR'&&d.offensive)this.b.lastWarSkill=Object.keys(PURE_SKILLS).indexOf(c.skillId)+1;
  if(fx.finisherBasicPercent&&segment===c.rank.authoredDamageHits-1)this.grant('slashBasic',fx.finisherBasicPercent,3);
  if(fx.nextSlashBreakPercent&&once('slashBreak'))this.grant('nextSlashBreak',fx.nextSlashBreakPercent,3);
  if(fx.nextShieldPercent&&once('ironShield'))this.grant('nextIronShield',fx.nextShieldPercent,4);
  if(fx.refreshBurn&&segment===c.rank.authoredDamageHits-1){const st=this.host.status(e),duration=Math.min(4,3+Math.max(c.passives.FIR_P1??0,c.equipment.includes('J01')?1:0)+(c.upgrades?.burnSeconds??0));if(st.burnUntil>time)st.burnUntil=Math.max(st.burnUntil,time+duration);}
  if(c.procs.includes('passive-ready:THU_P1')&&once('runSpeed')){const percent=this.passive(c,'THU_P1').speedPercent;if(percent)this.grant('thunderSpeed',percent,2);}
 }
 shieldAbsorbed(amount:number){
  if(amount<=0)return;const time=this.s.time,skill=this.b.shieldSkill===1?'WAR_03':'FIR_03',fx=effects(PURE_SKILLS[skill]?.ranks[(this.b.shieldRank??1)-1]);
  if(skill==='WAR_03'&&fx.absorbBasicPercent&&this.ready('shieldBasic',8))this.grant('shieldBasic',fx.absorbBasicPercent,4);
  if(skill==='WAR_03'&&fx.absorbBreakPercent&&this.ready('shieldBreak',8))this.grant('nextSlashBreak',fx.absorbBreakPercent,4);
  if(skill==='FIR_03'&&fx.shieldBurnSeconds&&this.ready('shieldBurn',8)){this.grant('shieldBurn',fx.shieldBurnSeconds,4);this.b.shieldMeteorRefresh=fx.shieldMeteorRefresh??0;}
  if(this.s.player.shield<=0){
   if(skill==='WAR_03'&&fx.brokenReductionPercent&&this.ready('ironBroken',8)){this.b.ironBrokenReduction=fx.brokenReductionPercent;this.b.ironBrokenUntil=time+fx.brokenReductionSeconds;}
   const linger=this.passive(undefined,'WAR_P2').brokenLingerSeconds;
   if(linger&&this.ready('passiveBroken',8))this.b.passiveBrokenUntil=time+linger;
  }
 }
 evade(){const percent=effects(allocatedSkillRank(this.s.progression,'COM_01')).evadeBasicPercent;if(percent&&this.ready('evadeBasic',8))this.grant('evadeBasic',percent,4);}
 basic(action:string):number {
  if(this.basics.has(action))return this.basics.get(action)!;let n=0;for(const key of BASIC_KEYS)n+=this.take(key);
  if(this.basics.size>=32)this.basics.clear();this.basics.set(action,n/100);return n/100;
 }
 thunderThird(e:EnemyState){const r=PURE_SKILLS.THU_03.ranks[(this.b.thunderRank??1)-1],fx=effects(r);if(fx.thirdBreakValue&&e.hp>0)this.host.poise(e,fx.thirdBreakValue,'THU_03');if(fx.nextSpearPercent)this.grant('nextSpear',fx.nextSpearPercent,4);}
 step(dt:number){
  this.b.stationaryFor=this.s.player.movingTime>0?0:Math.min(10,(this.b.stationaryFor??0)+dt);
  if(this.b.bowMovingBasic&&this.b.bowSpeedUntil>this.s.time&&this.s.player.movingTime>=.5){this.grant('hunterBasic',this.b.bowMovingBasic,3);this.b.bowMovingBasic=0;}
 }
 reduction(){return (this.b.ironBrokenUntil??0)>this.s.time?(this.b.ironBrokenReduction??0)/100:0;}
 speed(){return (this.b.thunderSpeedUntil??0)>this.s.time?(this.b.thunderSpeed??0)/100:0;}
 reset(){this.basics.clear();}
}
