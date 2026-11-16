import type {GameState,EnemyState} from '../../../core/GameSession';
import type {CombatCast,CombatStatus} from './PureCombat';
import type {Point} from '../../../core/Contracts';
import {PURE_SKILLS} from '../data/PureSkills';
import {ARTIFACT_WEAPONS} from '../../equipment/data/GrowingEquipment';
import {restorePlayerHealth} from '../../pets/common/PetBenefits';

export interface GrowingPulse {kind:'thunder'|'shadow';castId:string;targets:string[];from:Point;angle:number;power:number;until:number;area:string}
interface Host {state():GameState;visible(a:Point,b:Point):boolean;damage(e:EnemyState,value:number,cast:string,element:string,angle:number):void;shield(amount:number,seconds:number):void;status(e:EnemyState):CombatStatus;emit(type:string,text?:string,extra?:Record<string,unknown>):void;changed():void}
const point=(p:Point):Point=>({x:p.x,z:p.z});
const has=(c:CombatCast,id:string)=>c.equipment.includes(id);
export class GrowingEquipmentCombat {
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 private get c(){return this.s.combat;}
 private equipped(id:string){return Object.values(this.s.equipment).includes(id);}
 private ready(id:string){return !(this.c.cooldowns[id]>0);}
 private pulse(){return this.c.growingPending??=[];}
 private event(id:string,kind:string,at:Point,extra:Record<string,unknown>={}){this.host.emit('growing_proc',undefined,{id,kind,at:point(at),...extra});}
 move(distance:number,dt:number){
  if(!this.equipped('DG_L02'))return;const b=this.c.buffs;
  if(distance/dt>.1){b.dgBowMove=(b.dgBowMove??0)+dt;b.dgBowStill=0;}else{b.dgBowStill=(b.dgBowStill??0)+dt;if(b.dgBowStill>.2)b.dgBowMove=0;}
  if(this.ready('DG_L02')&&(b.dgBowReadyUntil??0)<=this.s.time&&(b.dgBowMove??0)>=2){b.dgBowMove=0;b.dgBowReadyUntil=this.s.time+5;this.event('DG_L02','ready',this.s.player);}
 }
 evade(){if(this.equipped('DG_L06')&&this.ready('DG_L06')){this.c.buffs.dgCounterUntil=this.s.time+4;this.c.cooldowns.DG_L06=8;this.event('DG_L06','ready',this.s.player);}}
 bonus(cast:CombatCast):number {
  if(cast.procs.includes('dg:first-hit'))return 0;cast.procs.push('dg:first-hit');let bonus=0;
  if(has(cast,'DG_L02')&&PURE_SKILLS[cast.skillId].style==='BOW'&&(this.c.buffs.dgBowReadyUntil??0)>this.s.time&&this.ready('DG_L02')){bonus+=.2;this.c.buffs.dgBowReadyUntil=0;this.c.buffs.dgBowMove=0;this.c.cooldowns.DG_L02=6;this.event('DG_L02','bow',this.s.player);}
  if(has(cast,'DG_L06')&&PURE_SKILLS[cast.skillId].type==='active'&&(this.c.buffs.dgCounterUntil??0)>this.s.time){bonus+=.2;this.c.buffs.dgCounterUntil=0;this.event('DG_L06','counter',this.s.player);}
  if(has(cast,'DG_L01')&&PURE_SKILLS[cast.skillId].style==='WAR'&&(this.c.buffs.dgGuardUntil??0)>this.s.time&&this.ready('DG_L01')){this.host.shield(this.s.player.maxHp*.08,3);this.c.buffs.dgGuardUntil=0;this.c.cooldowns.DG_L01=8;cast.procs.push('dg:guard-spent');this.event('DG_L01','shield',this.s.player);}
  return bonus;
 }
 hit(cast:CombatCast,enemy:EnemyState){
  const style=PURE_SKILLS[cast.skillId].style,now=this.s.time;
  if(has(cast,'DG_L01')&&style==='WAR'&&!cast.procs.includes('dg:guard-spent')&&!cast.procs.includes('dg:guard-qualified')){
   const targets=new Set(cast.hits.map(h=>h.slice(h.indexOf(':')+1)));
   if(enemy.bossId||targets.size>=2){cast.procs.push('dg:guard-qualified');this.c.buffs.dgGuardUntil=now+6;this.event('DG_L01','ready',this.s.player);}
  }
  if(has(cast,'DG_L03')&&style==='FIR'&&enemy.hp>0&&this.ready('DG_L03')&&!cast.procs.includes('dg:fire')){
   const st=this.host.status(enemy),remaining=Math.max(0,st.burnUntil-now);
   if(remaining>0&&st.burnDamage>0){const consumed=Math.min(remaining*.5,cast.power*.45/1.2/(st.burnDamage*2));st.burnUntil-=consumed;this.c.cooldowns.DG_L03=5;cast.procs.push('dg:fire');this.host.damage(enemy,consumed*st.burnDamage*2*1.2,`relic:fire:${cast.id}`,'relic',cast.angle);this.event('DG_L03','fire',enemy);}
  }
  if(has(cast,'DG_L04')&&style==='THU'&&enemy.hp>0){
   const pending=this.pulse(),old=pending.find(p=>p.kind==='thunder'&&p.targets[0]===enemy.id&&p.castId!==cast.id);
   if(old){pending.splice(pending.indexOf(old),1);this.host.damage(enemy,old.power*.45,`relic:thunder:${old.castId}`,'relic',cast.angle);this.event('DG_L04','thunder',enemy);}
   else if(this.ready('DG_L04')&&!cast.procs.includes('dg:thunder')){this.c.growingPending=pending.filter(p=>p.kind!=='thunder');this.pulse().push({kind:'thunder',castId:cast.id,targets:[enemy.id],from:point(enemy),angle:cast.angle,power:cast.power,until:now+1.2,area:this.s.area});cast.procs.push('dg:thunder');this.c.cooldowns.DG_L04=5;this.event('DG_L04','thunder-ready',enemy,{duration:1.2});}
  }
  const artifact=ARTIFACT_WEAPONS.find(id=>has(cast,id));
  if(artifact&&(artifact!=='DG_A01'||style==='WAR')&&PURE_SKILLS[cast.skillId].type==='active'){
   if(!cast.procs.includes('dg:shadow-count')){cast.procs.push('dg:shadow-count');const n=Math.min(4,(this.s.effectCounters.dgShadowCasts??0)+1);this.s.effectCounters.dgShadowCasts=n;
    if(n>=4&&this.ready('DG_A01')){this.s.effectCounters.dgShadowCasts=0;this.c.cooldowns.DG_A01=5;cast.procs.push('dg:shadow-active');const from=artifact!=='DG_A01'?enemy:cast.skillId==='WAR_04'?cast.to:this.s.player;this.pulse().push({kind:'shadow',castId:cast.id,targets:[enemy.id],from:point(from),angle:cast.angle,power:cast.power,until:now+.45,area:this.s.area});this.event('DG_A01','shadow-ready',from,{angle:cast.angle,duration:.45});}
   }
   const shadow=this.pulse().find(p=>p.kind==='shadow'&&p.castId===cast.id);if(shadow&&!shadow.targets.includes(enemy.id)&&shadow.targets.length<2)shadow.targets.push(enemy.id);
  }
 }
 burnApplied(cast:CombatCast,enemy:EnemyState){this.c.buffs[`dgBurnRing:${enemy.id}`]=has(cast,'DG_L05')?1:0;}
 kill(action:string,source:string,enemy:EnemyState){
  const cast=this.c.casts.find(c=>c.id===action),wearing=source==='burn'?this.c.buffs[`dgBurnRing:${enemy.id}`]===1:cast?has(cast,'DG_L05'):this.equipped('DG_L05');
  if(!wearing||!['pure','spell','main','skill','basic','burn'].includes(source)||!this.ready('DG_L05')||this.s.player.hp<=0)return;
  const amount=restorePlayerHealth(this.s,(this.s.player.maxHp-this.s.player.hp)*.12);if(amount<=0)return;
  this.c.cooldowns.DG_L05=5;this.host.emit('heal',`迟归者：生命 +${Math.round(amount)}`,{value:amount});this.event('DG_L05','heal',this.s.player);this.host.changed();
 }
 preventDeath(damage:number){
  if(damage<this.s.player.hp||!this.equipped('DG_A02')||!this.ready('DG_A02'))return false;
  this.s.player.hp=1;this.c.cooldowns.DG_A02=120;this.host.shield(this.s.player.maxHp*.2,2);this.host.emit('notice','第二次黎明：保留1点生命，立刻闪避或治疗！');this.event('DG_A02','dawn',this.s.player);this.host.changed();return true;
 }
 step(){
  const now=this.s.time,pending=this.pulse();
  for(const p of [...pending]){
   if(p.area!==this.s.area){pending.splice(pending.indexOf(p),1);continue;}if(now+1e-8<p.until)continue;
   pending.splice(pending.indexOf(p),1);
   for(const id of p.targets){const e=this.s.enemies.find(e=>e.id===id&&e.hp>0);if(!e)continue;
    if(p.kind==='shadow'){const dx=e.x-p.from.x,dz=e.z-p.from.z,angle=Math.atan2(dx,dz),delta=Math.atan2(Math.sin(angle-p.angle),Math.cos(angle-p.angle));if(Math.hypot(dx,dz)>1.8||Math.hypot(dx,dz)>.1&&Math.abs(delta)>55*Math.PI/180||!this.host.visible(p.from,e))continue;}
    this.host.damage(e,p.power*(p.kind==='shadow'?.65:.35),`relic:${p.kind}:${p.castId}`,p.kind==='shadow'?'relicPhysical':'relic',p.angle);
   }
   this.event(p.kind==='shadow'?'DG_A01':'DG_L04',p.kind,p.from,{angle:p.angle});this.host.changed();
  }
 }
}
export function validateGrowingPulses(value:unknown){
 if(value===undefined)return;
 if(!Array.isArray(value)||value.length>4)throw new Error('无效的成长装备延迟效果');
 for(const p of value){if(!p||!['thunder','shadow'].includes(p.kind)||typeof p.castId!=='string'||p.castId.length>200||!Array.isArray(p.targets)||p.targets.length<1||p.targets.length>(p.kind==='shadow'?2:1)||p.targets.some((id:unknown)=>typeof id!=='string'||id.length>200)||!p.from||![p.from.x,p.from.z,p.angle,p.power,p.until].every(Number.isFinite)||Math.abs(p.from.x)>5000||Math.abs(p.from.z)>5000||p.power<0||p.power>10000||p.until<0||p.until>1e10||typeof p.area!=='string'||p.area.length>20)throw new Error('无效的成长装备延迟效果');}
}
