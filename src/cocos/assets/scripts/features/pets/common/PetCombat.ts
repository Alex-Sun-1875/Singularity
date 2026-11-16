import type {EnemyState,GameState} from '../../../core/GameSession';
import type {GameEvent,Point} from '../../../core/Contracts';
import {petCombatProfile,petSignatureView} from './PetSystem';
import {petSpecies} from '../data/Pets';
import {petAvailable} from './PetAccess';
import {clearPetSkillEffects,petEffectActive,type PetEffectKind} from './PetSkillEffects';

interface Host {
 state():GameState;visible(from:Point,to:Point):boolean;
 echo(target:EnemyState,value:number,pet:string):boolean;
 emit(type:string,text?:string,extra?:Record<string,unknown>):void;changed():void;
}
interface Contact {source:string;attack:string;time:number;hp:number}
const distance=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);

/** One automatic companion skill, driven by committed combat events. Cooldowns
 * live in the ordinary saved simulation-clock ledger. Pending target windows
 * and effects are discarded on scene changes/restore without resetting waits. */
export class PetCombat {
 private configuration='';
 private area='';
 private observedEvents:readonly GameEvent[]|undefined;
 private observedCount=0;
 private readonly casts=new Set<string>();
 private contacts:Contact[]=[];
 private pending:{target:string;damage:number;until:number}|undefined;
 private markedTarget='';private markedCount=0;private markedUntil=0;
 private controlAt=0;private controlUntil=0;
 private lastSlowUntil=0;
 private engaged=false;private quietSince=0;
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 private pet(){return this.s.pets?.active?this.s.pets.roster[this.s.pets.active]:undefined;}
 private ready(){const pet=this.pet();return !!pet&&Math.max(this.s.cooldowns.petSkillShared??0,this.s.cooldowns[`petSkill:${pet.id}`]??0)<=1e-8;}
 status(id:string){
  const s=this.s,active=petAvailable(this.s)&&s.pets?.active===id;
  let effectSeconds=0;if(active&&petEffectActive(s))for(const kind of ['damage','reduction','resource','healing','nextWard'])effectSeconds=Math.max(effectSeconds,(s.combat.buffs[`petfx:${kind}Until`]??0)-s.time);
  return {active,cooldown:petAvailable(this.s)?Math.max(0,s.cooldowns.petSkillShared??0,s.cooldowns[`petSkill:${id}`]??0):0,effectSeconds:Math.max(0,effectSeconds)};
 }
 view(){
  const s=this.s,profile=petCombatProfile(s);if(!profile||s.status==='dead'||s.player.hp<=0)return null;
  const p=s.player,point={x:p.x-Math.sin(p.angle+.7)*.95,z:p.z-Math.cos(p.angle+.7)*.95};
  return {profile,at:this.host.visible(p,point)?point:{x:p.x,z:p.z}};
 }
 clearTransient(){
  clearPetSkillEffects(this.s);this.pending=undefined;this.contacts=[];this.casts.clear();this.markedTarget='';this.markedCount=0;this.markedUntil=0;this.controlAt=0;this.controlUntil=0;this.lastSlowUntil=0;
  delete this.s.combat.buffs['pet:movementSeconds'];delete this.s.combat.buffs['pet:movementGraceUntil'];
  this.engaged=!!this.s.combat.engagement;this.quietSince=this.s.time;
 }
 sync(){
  if(!petAvailable(this.s))return;
  const s=this.s,pet=this.pet(),key=pet?`${pet.id}:${pet.signatureRank}:${pet.branch}:${pet.traitSlots.join(',')}`:'';
  if(key!==this.configuration||s.area!==this.area){this.clearTransient();this.configuration=key;this.area=s.area;}
  this.updateLowHealth();
 }
 private updateLowHealth(){const s=this.s,ratio=s.player.hp/s.player.maxHp;if(ratio<=.35)s.flags['pet:reverseWind']=true;else if(ratio>.4)delete s.flags['pet:reverseWind'];}
 moved(metres:number,seconds:number){
  if(!petAvailable(this.s)||!this.pet())return;const s=this.s,b=s.combat.buffs;
  if(metres>.001){b['pet:movementSeconds']=Math.min(60,(b['pet:movementSeconds']??0)+seconds);if(b['pet:movementSeconds']>=2)b['pet:movementGraceUntil']=s.time+2;}
  else b['pet:movementSeconds']=0;
 }
 step(seconds:number){
  if(!petAvailable(this.s))return;this.sync();const s=this.s,pet=this.pet();
  if(!pet||s.player.hp<=0||s.status==='dead'){if(this.configuration)this.clearTransient();return;}
  if(!Number.isFinite(seconds)||seconds<=0)return;
  if(this.pending&&this.pending.until<s.time)this.pending=undefined;
  if(this.markedTarget){const target=s.enemies.find(enemy=>enemy.id===this.markedTarget);if(s.time>this.markedUntil||!target||target.hp<=0||!this.host.visible(s.player,target)){this.markedTarget='';this.markedCount=0;}}
  const slow=s.combat.buffs.enemySlowUntil??0;
  if(slow>s.time)this.lastSlowUntil=slow;
  else if(this.lastSlowUntil){this.controlAt=this.lastSlowUntil;this.controlUntil=this.controlAt+6;this.lastSlowUntil=0;}
  const combat=!!s.combat.engagement;
  if(!combat){if(this.engaged)this.quietSince=s.time;this.engaged=false;}
  else if(!this.engaged){this.engaged=true;if(pet.species==='hunting_dog'&&s.time-this.quietSince>=6&&this.ready())this.activate();}
 }
 observe(events:readonly GameEvent[]){
  if(!petAvailable(this.s))return;this.sync();
  if(this.observedEvents!==events){this.observedEvents=events;this.observedCount=0;}
  while(this.observedCount<events.length){const event=events[this.observedCount++];
   if(['area','travel','retry','death'].includes(event.type)){this.clearTransient();continue;}
   if(!this.pet()||this.s.status==='dead'||this.s.player.hp<=0)continue;
   if(event.type==='hit'&&event.petEligible===true&&Number(event.hpLost)>0&&event.id)this.onHit(event);
   else if(event.type==='hurt'&&event.petEligible===true&&Number(event.hpLost)>0)this.onHurt(event);
   else if(event.type==='heal'&&Number(event.value)>0&&event.source!=='pet')this.onHeal();
   else if(event.type==='consumable'&&event.health===true&&Number(event.value)>0)this.onHeal();
   else if(event.type==='evade'&&event.timing===true&&event.petEligible===true)this.onEvade();
   else if(event.type==='player_control'&&event.petEligible===true){this.controlAt=this.s.time+Math.max(0,Number(event.duration)||0);this.controlUntil=this.controlAt+6;}
  }
 }
 private stamp(){
  const pet=this.pet();if(!pet||!this.ready())return false;const s=this.s,skill=petSignatureView(pet);
  clearPetSkillEffects(s);s.receipts['petfx:owner']=pet.id;
  s.cooldowns.petSkillShared=skill.cooldown;s.cooldowns[`petSkill:${pet.id}`]=skill.cooldown;
  this.host.emit('pet_skill',`${petSpecies(pet.species)!.name} · ${skill.name}`,{id:pet.id,at:{x:s.player.x,z:s.player.z},skill:skill.name,duration:skill.duration});this.host.changed();return true;
 }
 private activate(effect?:PetEffectKind,percent?:number,duration?:number,target?:EnemyState,ward=false){
  const pet=this.pet();if(!pet)return false;const skill=petSignatureView(pet);if(!this.stamp())return false;
  const kind=effect??skill.effect;if(kind==='echo')return true;
  const key=ward?'nextWard':kind,b=this.s.combat.buffs;
  b[`petfx:${key}Until`]=this.s.time+(duration??skill.duration);b[`petfx:${key}Percent`]=percent??skill.percent;
  if(target)this.s.receipts['petfx:target']=`${this.s.area}/${target.id}`;return true;
 }
 private echo(target:EnemyState,damage:number){
  const pet=this.pet();if(!pet||target.hp<=0||!this.host.visible(this.s.player,target))return false;
  const skill=petSignatureView(pet);if(!this.stamp())return false;
  const percent=pet.species==='ember_fox'&&pet.branch==='A'&&target.hp>target.maxHp*.35?petSignatureView({...pet,branch:null}).percent:skill.percent;
  return this.host.echo(target,damage*percent/100,pet.id);
 }
 private onHit(event:GameEvent){
  const pet=this.pet(),s=this.s,cast=String(event.action??'');if(!pet||!cast||this.casts.has(cast))return;
  this.casts.add(cast);if(this.casts.size>128)this.casts.delete(this.casts.values().next().value!);
  const target=s.enemies.find(enemy=>enemy.id===event.id);if(!target||target.hp<=0||!this.host.visible(s.player,target))return;
  if(pet.species==='ember_fox'&&this.ready()){if(pet.branch==='B')this.activate('reduction',undefined,undefined,undefined,true);else this.echo(target,Number(event.hpLost));}
  else if(pet.species==='hunting_hawk'&&pet.branch!=='B'&&distance(s.player,target)>=5){
   if(this.markedTarget!==target.id||s.time>this.markedUntil){this.markedTarget=target.id;this.markedCount=0;}this.markedCount++;this.markedUntil=s.time+5;
   if(this.markedCount>=2&&this.ready()){this.activate('damage',undefined,undefined,target);this.markedCount=0;}
  }else if(pet.species==='white_tiger'&&pet.branch!=='B'&&this.ready()&&!this.pending)this.pending={target:target.id,damage:Number(event.hpLost),until:s.time+4};
  else if(pet.species==='dragon'&&this.ready()&&this.controlAt>0&&s.time>=this.controlAt&&s.time<=this.controlUntil){this.controlAt=0;this.controlUntil=0;if(pet.branch==='B')this.activate('reduction');else this.echo(target,Number(event.hpLost));}
 }
 private onHurt(event:GameEvent){
  const s=this.s,pet=this.pet();if(!pet)return;this.updateLowHealth();
  const attack=String(event.action??`${event.source}:${s.time}`),contact={source:String(event.source),attack,time:s.time,hp:Number(event.hpLost)};
  if(!this.contacts.some(old=>old.attack===attack))this.contacts.push(contact);
  this.contacts=this.contacts.filter(old=>s.time-old.time<=6).slice(-16);if(!this.ready())return;
  if(pet.species==='stone_turtle'){
   const recent=this.contacts.filter(old=>s.time-old.time<=3),large=contact.hp>=s.player.maxHp*.12,multiple=pet.signatureRank>=2&&recent.length>=2&&recent.reduce((n,v)=>n+v.hp,0)>=s.player.maxHp*.2;
   if(large||multiple){this.activate('reduction',undefined,undefined,undefined,pet.branch!=='B');this.contacts=[];}
  }else if(pet.species==='tabby_cat'){
   const recent=this.contacts.filter(old=>s.time-old.time<=3);if(new Set(recent.map(old=>old.source)).size>=2){this.activate(pet.branch==='B'?'reduction':'damage');this.contacts=[];}
  }else if(pet.species==='grey_wolf'&&this.contacts.length>=3){this.activate(pet.branch==='B'?'reduction':'damage');this.contacts=[];}
 }
 private onHeal(){
  const s=this.s,pet=this.pet();if(!pet||!this.ready())return;this.updateLowHealth();
  if(pet.species==='dew_sprite')this.activate(pet.branch==='B'?'healing':'resource');
  else if(pet.species==='mountain_tiger'){
   const before=(s.combat.buffs['petfx:healAt']??-1)===s.time?s.combat.buffs['petfx:healBeforeRatio']:s.player.hp/s.player.maxHp;
   if(before<.4)this.activate(pet.branch==='B'?'reduction':'resource');
  }
 }
 private onEvade(){
  const s=this.s,pet=this.pet();if(!pet||!this.ready())return;
  if(pet.species==='hunting_hawk'&&pet.branch==='B')this.activate('damage');
  else if(pet.species==='spotted_deer'&&s.player.focus/s.player.maxFocus<=(pet.branch==='B'?.7:.4))this.activate('resource');
  else if(pet.species==='white_tiger'){
   if(pet.branch==='B')this.activate('resource');
   else if(this.pending&&this.pending.until>=s.time){const target=s.enemies.find(enemy=>enemy.id===this.pending!.target),damage=this.pending.damage;this.pending=undefined;if(target)this.echo(target,damage);}
  }
 }
 /** Called after ordinary accuracy, armor and passive pet reduction, before
  * shield absorption. Neither a miss nor a dash can consume this ward. */
 beforeHurt(amount:number,eligible:boolean):number {
  if(!petAvailable(this.s)||!eligible)return amount;this.sync();const s=this.s,pet=this.pet();if(!pet)return amount;
  const b=s.combat.buffs;if(petEffectActive(s)&&(b['petfx:nextWardUntil']??0)>s.time){amount*=1-Math.min(40,b['petfx:nextWardPercent']??0)/100;delete b['petfx:nextWardUntil'];delete b['petfx:nextWardPercent'];}
  if(pet.species==='griffin'&&this.ready()){
   const skill=petSignatureView(pet),threatened=pet.branch==='B'?s.player.hp/s.player.maxHp<=skill.healthThreshold:amount-s.player.shield>=s.player.hp;
   if(threatened&&this.stamp())amount*=1-skill.percent/100;
  }
  return Math.max(1,amount);
 }
}
