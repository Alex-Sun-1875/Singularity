import {CAMPAIGN_MAX_LEVEL,combatBudgetLevel} from '../../progression/data/CampaignProgression';
import type {EnemySpawn,InteractionDef,Point,WorldQuery} from '../../../core/Contracts';
import type {EnemyState,GameState} from '../../../core/GameSession';
import {petSpecies,type PetSpeciesId,type PetSkillId} from '../data/Pets';
import {petAccess,petAvailable} from './PetAccess';
import {PET_JOURNEYS,PET_JOURNEY_STEPS,petJourney,petJourneyStep,petJourneyObject,petTrialKinds,petTrialEnemyId,petTrialSpawns,petTrialBaseHp,type PetJourneyStep,type PetTrialKind} from '../data/PetJourneys';
import {petJourneyText as t} from '../locales/PetJourneyText';

type Category='exploration'|'rescue'|'combat'|'mechanism';
interface Completion {v:1;pet:PetSpeciesId|null;at:number}
interface Escort {v:1;x:number;z:number;next:number;metres:number;start:number}
interface Wave {v:2;level:number;at:number}
interface Host {state():GameState;world():WorldQuery;safe():boolean;spawn(enemies:EnemySpawn[]):boolean;changed():void;emit(type:string,text?:string,extra?:Record<string,unknown>):void;reward(source:string):void}
export interface PetJourneyStepView {id:string;objectId:string;species:PetSpeciesId;kind:PetJourneyStep['kind'];label:string;description:string;area:string;point:Point;completed:boolean;active:boolean;phase:PetJourneyStep['phase'];manuals:PetSkillId[];trial?:PetTrialKind}
export interface PetJourneyView {species:PetSpeciesId;title:string;complete:boolean;owned:boolean;steps:PetJourneyStepView[];current?:PetJourneyStepView}
const doneKey=(step:PetJourneyStep)=>'petj:done:'+step.species+':'+step.index;
const mechanismKey=(step:PetJourneyStep)=>'petj:mechanism:'+step.species+':'+step.index;
const changedFlag=(step:PetJourneyStep)=>'petj:changed:'+step.species+':'+step.index;
const escortKey=(step:PetJourneyStep)=>'petj:escort:'+step.species+':'+step.index;
const waveKey=(step:PetJourneyStep)=>'petj:wave:'+step.species+':'+step.index;
const suspendedKey=(step:PetJourneyStep)=>'petj:suspended:'+step.species+':'+step.index;
const defeatedKey=(step:PetJourneyStep,index:number)=>'petj:defeat:'+step.species+':'+step.index+':'+index;
const distance=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
const object=(v:unknown):v is Record<string,any>=>!!v&&typeof v==='object'&&!Array.isArray(v)&&Object.getPrototypeOf(v)===Object.prototype;
const keys=(v:object,names:string[])=>Object.keys(v).sort().join()===names.slice().sort().join();
const number=(v:unknown,min=0,max=Number.MAX_SAFE_INTEGER):v is number=>typeof v==='number'&&Number.isFinite(v)&&v>=min&&v<=max;
const integer=(v:unknown,min=0,max=Number.MAX_SAFE_INTEGER)=>number(v,min,max)&&Number.isSafeInteger(v);
const parse=<T>(value:unknown):T|null=>{if(typeof value!=='string')return null;try{return JSON.parse(value) as T;}catch{return null;}};
const completion=(s:GameState,step:PetJourneyStep):Completion|null=>{const proof=parse<Completion>(s.receipts[doneKey(step)]);return object(proof)&&keys(proof,['v','pet','at'])&&proof.v===1&&number(proof.at,0,s.time)&&(proof.pet===null||typeof proof.pet==='string'&&!!s.pets?.roster[proof.pet])?proof:null;};
const completed=(s:GameState,step:PetJourneyStep)=>{if(!completion(s,step))return false;if(step.kind==='mechanism')return s.receipts[mechanismKey(step)]===3&&s.flags[changedFlag(step)]===true;if(step.kind==='escort'){const e=parse<Escort>(s.receipts[escortKey(step)]);return !!e&&e.next===3&&e.metres>=3&&!!step.route[2]&&distance(e,step.route[2])<=.7;}return step.kind!=='combat'||trialDone(s,step);};
const beforeDone=(s:GameState,step:PetJourneyStep)=>petJourney(step.species)!.steps.slice(0,step.index).every(previous=>completed(s,previous));
const category=(step:PetJourneyStep):Category=>step.kind==='combat'?'combat':step.kind==='mechanism'?'mechanism':step.kind==='escort'?'rescue':'exploration';
const enemyFor=(s:GameState,step:PetJourneyStep,index:number)=>(s.area===step.area?s.enemies:s.encounters[step.area]??[]).find(enemy=>enemy.id===petTrialEnemyId(step,index));
const defeated=(s:GameState,step:PetJourneyStep,index:number)=>{const proof=parse<{v:1;at:number}>(s.receipts[defeatedKey(step,index)]),wave=parse<Wave>(s.receipts[waveKey(step)]);return object(wave)&&wave.v===2&&number(wave.at,0,s.time)&&object(proof)&&keys(proof,['v','at'])&&proof.v===1&&number(proof.at,wave.at,s.time);};
const trialDone=(s:GameState,step:PetJourneyStep)=>petTrialKinds(step).every((_,index)=>defeated(s,step,index));
const acquisitionDone=(s:GameState,species:string)=>{const def=petJourney(species);return !!def&&def.steps.slice(0,def.acquisitionEnd+1).every(step=>completed(s,step));};

/** These helpers inspect authored proofs even while the release switch is
 * closed; actions and rewards independently check the switch in their host. */
export function petAcquisitionReady(s:GameState,species:string):boolean {return acquisitionDone(s,species);}
export function petManualUnlocked(s:GameState,skill:string):boolean {return PET_JOURNEY_STEPS.some(step=>step.manuals.some(id=>id===skill)&&completed(s,step));}
export function petJournal(s:GameState,species:string):{id:string;category:Category}[]{return PET_JOURNEY_STEPS.filter(step=>step.kind!=='invite'&&completed(s,step)&&completion(s,step)?.pet===species).map(step=>({id:doneKey(step),category:category(step)}));}
export function petSpeciesProofs(s:GameState,species:string):{habit:boolean;trial:boolean;final:boolean;trials:PetTrialKind[]}{
  const steps=petJourney(species)?.steps.filter(step=>step.phase==='training')??[],earned=steps.filter(step=>completed(s,step)&&completion(s,step)?.pet===species),trials=[...new Set(earned.flatMap(step=>step.trial?[step.trial]:[]))];
 return {habit:earned.some(step=>step.habit),trial:trials.length>0,final:earned.some(step=>step.final),trials};
}
export function petProgressReward(s:GameState,source:string):{pet:string|null;category:'exploration'|'rescue'|'mechanism'|'trial';xp:number;essence:number;bond:number}|null {
 if(!source.startsWith('petj:done:'))return null;const step=petJourneyStep('petj:'+source.slice(10));if(!step)return null;const proof=completion(s,step);if(!proof||!completed(s,step)||!beforeDone(s,step)||proof.pet!==null&&!s.pets.roster[proof.pet])return null;
 if(step.kind==='invite')return {pet:proof.pet,category:'exploration',xp:0,essence:0,bond:0};
 const reward=step.kind==='combat'?{xp:600,essence:25,bond:10}:step.kind==='escort'?{xp:300,essence:15,bond:8}:step.kind==='mechanism'?{xp:250,essence:12,bond:5}:{xp:200,essence:10,bond:5};
 return {pet:proof.pet,category:step.kind==='combat'?'trial':step.kind==='escort'?'rescue':step.kind==='mechanism'?'mechanism':'exploration',...reward};
}
/** Only the fixed, genuinely started trial wave can bypass the ordinary
 * training-area restriction; its opponents never create ordinary loot. */
export function validPetJourneyEnemy(s:GameState,enemy:EnemyState):boolean {
 const step=PET_JOURNEY_STEPS.find(step=>step.kind==='combat'&&petTrialKinds(step).some((_,index)=>enemy.id===petTrialEnemyId(step,index)));if(!step)return false;
 const wave=parse<Wave>(s.receipts[waveKey(step)]),index=petTrialKinds(step).findIndex((_,index)=>enemy.id===petTrialEnemyId(step,index));
 const locations=[...(s.enemies.includes(enemy)?[s.area]:[]),...Object.entries(s.encounters).filter(([,enemies])=>enemies.includes(enemy)).map(([area])=>area)];
 return !!wave&&wave.v===2&&integer(wave.level,1,CAMPAIGN_MAX_LEVEL)&&number(wave.at,0,s.time)&&beforeDone(s,step)&&(locations.length?locations.every(area=>area===step.area):s.area===step.area)&&enemy.trainingEnemy===true&&enemy.trainingAttacks===true&&!enemy.trainingDummy&&!enemy.bossId&&!enemy.packId&&!enemy.respawnSeconds&&enemy.kind===petTrialKinds(step)[index]&&enemy.level===wave.level&&enemy.maxHp===Math.round(petTrialBaseHp(enemy.kind)*(1+.14*(combatBudgetLevel(wave.level)-1)));
}

export class PetJourneys {
 private escortWrite=0;
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 private notify(text:string){this.host.emit('pet_journey',text);}
 private current(species:string){return petJourney(species)?.steps.find(step=>!completed(this.s,step));}
 private point(step:PetJourneyStep):{point:Point;objectId:string}{
  if(step.kind==='mechanism'){const progress=this.s.receipts[mechanismKey(step)];if(typeof progress==='number'&&progress<3)return {point:step.switches[progress]??step.point,objectId:step.id+':switch:'+progress};}
  if(step.kind==='escort'){const e=parse<Escort>(this.s.receipts[escortKey(step)]);if(e&&e.next<3)return {point:{x:e.x,z:e.z},objectId:step.id};}
  return {point:{...step.point},objectId:step.id};
 }
 private stepView(step:PetJourneyStep):PetJourneyStepView{return {id:step.id,species:step.species,kind:step.kind,label:step.label,description:step.description,area:step.area,...this.point(step),completed:completed(this.s,step),active:this.current(step.species)?.id===step.id,phase:step.phase,manuals:[...step.manuals],...(step.trial?{trial:step.trial}:{})};}
 view():PetJourneyView[];
 view(species:string):PetJourneyView|undefined;
 view(species?:string):PetJourneyView[]|PetJourneyView|undefined {
  if(!petAvailable(this.s))return species?undefined:[];
  const all=PET_JOURNEYS.map(def=>({species:def.species,title:def.title,complete:acquisitionDone(this.s,def.species),owned:!!this.s.pets.roster[def.species],steps:def.steps.map(step=>this.stepView(step)),current:this.current(def.species)?this.stepView(this.current(def.species)!):undefined}));return species?all.find(def=>def.species===species):all;
 }
 manualTarget(skill:string):PetJourneyStepView|null {if(!petAvailable(this.s)||petManualUnlocked(this.s,skill))return null;const target=PET_JOURNEY_STEPS.find(step=>step.manuals.some(id=>id===skill));if(!target)return null;return this.stepView(this.current(target.species)??target);}
 visibility(objectId:string):boolean {
  if(!petAvailable(this.s))return false;const found=petJourneyObject(objectId);if(!found||this.current(found.step.species)?.id!==found.step.id)return false;
  const step=found.step;if(step.phase==='training'&&(!this.s.pets.roster[step.species]||this.s.pets.active!==step.species))return false;
  if(step.kind==='mechanism'){const progress=this.s.receipts[mechanismKey(step)];return found.part<0?progress===undefined:progress!==undefined&&Number(progress)<3;}
  return found.part<0;
 }
 availability(objectId:string):{available:boolean;completed:boolean;reason:string}{
  const no=(key:Parameters<typeof t>[0],done=false)=>({available:false,completed:done,reason:t(key)}),found=petJourneyObject(objectId),s=this.s;
  if(!petAvailable(s))return {available:false,completed:false,reason:petAccess(s).reason};if(!found)return no('previous');const step=found.step;
  if(completed(s,step))return no('done',true);if(!beforeDone(s,step))return no('previous');
  if(step.phase==='training'&&!s.pets.roster[step.species])return no('owned');
  if(step.phase==='training'&&s.pets.active!==step.species)return no('deploy');
  if(petSpecies(step.species)?.nativeQuality!=='普通'&&!Object.keys(s.pets.roster).length)return no('first');
  if(s.status==='dead'||s.player.hp<=0||s.dialogue||s.dice.active)return no('safe');
  const point=found.part<0?step.point:step.switches[found.part];if(!point||s.area!==step.area||distance(s.player,point)>1.36||!this.host.world().visible(s.player,point))return no('near');
  if(step.kind==='combat'&&s.receipts[waveKey(step)]&&!trialDone(s,step)){
   const missing=petTrialKinds(step).some((_,index)=>!s.receipts[defeatedKey(step,index)]&&!enemyFor(s,step,index));if(!missing)return no('trialWait');
  }
  if(step.kind==='escort'){const e=parse<Escort>(s.receipts[escortKey(step)]);if(e&&e.next<3)return no('escortWait');}
  if(step.kind==='mechanism'&&found.part<0&&s.receipts[mechanismKey(step)]!==undefined)return no('mechanism');
  if(!this.host.safe())return no('safe');return {available:true,completed:false,reason:t('ready')};
 }
 private finish(step:PetJourneyStep){
  if(completed(this.s,step))return false;
  const proof:Completion={v:1,pet:this.s.pets.active as PetSpeciesId|null,at:this.s.time};this.s.receipts[doneKey(step)]=JSON.stringify(proof);this.host.changed();this.host.reward(doneKey(step));this.notify(step.kind==='invite'&&step.phase==='acquisition'?t('invite'):t('complete',{name:step.label}));return true;
 }
 interact(objectId:string):boolean {
  if(!this.availability(objectId).available)return false;const found=petJourneyObject(objectId)! ,step=found.step,s=this.s;
  if(step.kind==='observe'||step.kind==='invite')return this.finish(step);
  if(step.kind==='mechanism'){
   if(found.part<0){s.receipts[mechanismKey(step)]=0;this.host.changed();this.notify(t('mechanismStart'));return true;}
   const progress=Number(s.receipts[mechanismKey(step)]??-1);if(found.part!==progress){s.receipts[mechanismKey(step)]=0;this.host.changed();this.notify(t('wrong'));return true;}
   s.receipts[mechanismKey(step)]=progress+1;this.host.changed();if(progress===2){s.flags[changedFlag(step)]=true;return this.finish(step);}this.notify(t('mechanism'));return true;
  }
  if(step.kind==='escort'){
   const escort=parse<Escort>(s.receipts[escortKey(step)]);if(escort&&escort.next>=3)return this.finish(step);
   s.receipts[escortKey(step)]=JSON.stringify({v:1,x:step.point.x,z:step.point.z,next:0,metres:0,start:s.time} satisfies Escort);this.host.changed();this.notify(t('escortStart'));return true;
  }
  if(trialDone(s,step))return this.finish(step);
  const existing=parse<Wave>(s.receipts[waveKey(step)]),wave:Wave=existing??{v:2,level:Math.max(1,Math.min(CAMPAIGN_MAX_LEVEL,s.progression.level)),at:s.time};
  const other=PET_JOURNEY_STEPS.some(other=>other.kind==='combat'&&other.id!==step.id&&s.receipts[waveKey(other)]&&!completed(s,other)&&!trialDone(s,other));if(other){this.notify(t('trialBusy'));return false;}
  if(!existing)s.receipts[waveKey(step)]=JSON.stringify(wave);
  const spawns=petTrialSpawns(step,wave.level).map(e=>({...e,hp:Math.round(petTrialBaseHp(e.kind)*(1+.14*(combatBudgetLevel(wave.level)-1)))})).filter((_,index)=>!s.receipts[defeatedKey(step,index)]&&!enemyFor(s,step,index));
  if(!spawns.length||!this.host.spawn(spawns)){if(!existing)delete s.receipts[waveKey(step)];this.notify(t('trialFailed'));return false;}
  delete s.receipts[suspendedKey(step)];this.host.changed();this.notify(t('trialStart'));return true;
 }
 observeCombat(){
  if(!petAvailable(this.s))return;const s=this.s;
  for(const step of PET_JOURNEY_STEPS){if(step.area!==s.area||step.kind!=='combat'||!s.receipts[waveKey(step)]||completed(s,step))continue;
   petTrialKinds(step).forEach((_,index)=>{const enemy=enemyFor(s,step,index),key=defeatedKey(step,index);if(!s.receipts[key]&&enemy&&validPetJourneyEnemy(s,enemy)&&enemy.hp===0&&enemy.phase==='dead'&&enemy.diedAt!==undefined&&enemy.diedAt<=s.time){s.receipts[key]=JSON.stringify({v:1,at:enemy.diedAt});this.host.changed();}});
  }
 }
 step(dt:number){
  if(!petAvailable(this.s)||!Number.isFinite(dt)||dt<=0)return;const s=this.s;if(s.status==='dead'||s.player.hp<=0||s.dialogue||s.dice.active||!this.host.safe())return;
  for(const step of PET_JOURNEY_STEPS){if(step.kind!=='escort'||step.area!==s.area||completed(s,step)||!beforeDone(s,step)||step.phase==='training'&&s.pets.active!==step.species)continue;
   const e=parse<Escort>(s.receipts[escortKey(step)]);if(!e||e.next>=3||distance(s.player,e)>5)continue;const target=step.route[e.next];if(!target)continue;
   if(s.enemies.some(enemy=>enemy.hp>0&&distance(enemy,e)<6&&this.host.world().visible(e,enemy)))continue;
   const world=this.host.world(),path=world.path?.(e,target),next=path?.find(point=>distance(e,point)>.35)??target,d=distance(e,next);if(d>.01){const travel=Math.min(d,Math.min(dt,.1)*1.65),moved=world.move({x:e.x,z:e.z},{x:(next.x-e.x)/d*travel,z:(next.z-e.z)/d*travel},.3);e.metres+=distance(e,moved);e.x=moved.x;e.z=moved.z;}
   if(distance(e,target)<.55)e.next++;s.receipts[escortKey(step)]=JSON.stringify(e);this.escortWrite+=dt;if(this.escortWrite>=.1){this.escortWrite=0;this.host.changed();}
   if(e.next>=3){this.host.changed();this.finish(step);}break;
  }
 }
 escortView():{species:PetSpeciesId;at:Point;walking:boolean}|null {
  if(!petAvailable(this.s)||this.s.status==='dead')return null;
  for(const step of PET_JOURNEY_STEPS){if(step.area!==this.s.area||completed(this.s,step)||!beforeDone(this.s,step))continue;const e=step.kind==='escort'?parse<Escort>(this.s.receipts[escortKey(step)]):null;if(e&&e.next<3)return {species:step.species,at:{x:e.x,z:e.z},walking:this.host.safe()&&distance(e,this.s.player)<=5};
   if(step.kind==='invite'&&step.phase==='acquisition'&&distance(this.s.player,step.point)<24)return {species:step.species,at:{...step.point},walking:false};
  }return null;
 }
 enter(){
  if(petAvailable(this.s))return;
  // A previously enabled controlled save must not keep fighting while closed.
  const s=this.s,isTrial=(enemy:EnemyState)=>enemy.id.startsWith('petj-trial-');let removed=false;
  for(const step of PET_JOURNEY_STEPS)if(step.kind==='combat'&&s.receipts[waveKey(step)]&&!completed(s,step)&&!trialDone(s,step)&&petTrialKinds(step).some((_,index)=>!!enemyFor(s,step,index)))s.receipts[suspendedKey(step)]=JSON.stringify({v:1,at:s.time});
  if(s.enemies.some(isTrial)){s.enemies=s.enemies.filter(enemy=>!isTrial(enemy));removed=true;}
  for(const [area,enemies] of Object.entries(s.encounters))if(enemies.some(isTrial)){s.encounters[area]=enemies.filter(enemy=>!isTrial(enemy));removed=true;}
  if(removed){if(s.combat.engagement){s.combat.engagement.enemyIds=s.combat.engagement.enemyIds.filter(id=>!id.startsWith('petj-trial-'));if(!s.combat.engagement.enemyIds.length)delete s.combat.engagement;}s.projectiles=s.projectiles.filter(projectile=>!projectile.enemyId?.startsWith('petj-trial-'));this.host.changed();}
 }
}

/** Bounded authored receipts validate physical mechanism changes, actual escort
 * travel, trial waves and ordered prerequisites; naked progress booleans fail. */
export function validatePetJourneys(s:GameState):void {
 const fail=():never=>{throw new Error('无效的伙伴相遇、护送或试炼凭证');},allowed=new Set<string>(),flagNames=new Set<string>();
 for(const step of PET_JOURNEY_STEPS){allowed.add(doneKey(step));if(step.kind==='mechanism'){allowed.add(mechanismKey(step));flagNames.add(changedFlag(step));}if(step.kind==='escort')allowed.add(escortKey(step));if(step.kind==='combat'){allowed.add(waveKey(step));allowed.add(suspendedKey(step));petTrialKinds(step).forEach((_,index)=>allowed.add(defeatedKey(step,index)));}}
 for(const key of Object.keys(s.receipts))if(key.startsWith('petj:')&&!allowed.has(key))fail();for(const key of Object.keys(s.flags))if(key.startsWith('petj:')&&!flagNames.has(key))fail();
 for(const step of PET_JOURNEY_STEPS){
  const raw=s.receipts[doneKey(step)],proof=completion(s,step),hasData=raw!==undefined||s.receipts[mechanismKey(step)]!==undefined||s.receipts[escortKey(step)]!==undefined||s.receipts[waveKey(step)]!==undefined;
  if(hasData&&(!beforeDone(s,step)||!s.flags['visited:'+step.area]||step.phase==='training'&&!s.pets?.roster[step.species]))fail();
  const previousTimes=petJourney(step.species)!.steps.slice(0,step.index).map(previous=>completion(s,previous)?.at??0),previousTime=Math.max(0,...previousTimes);
  if(raw!==undefined&&(!object(proof)||!keys(proof,['v','pet','at'])||proof.v!==1||!number(proof.at,previousTime,s.time)||proof.pet!==null&&(typeof proof.pet!=='string'||!s.pets?.roster[proof.pet])||step.phase==='training'&&proof.pet!==step.species))fail();
  if(step.kind==='mechanism'){
   const progress=s.receipts[mechanismKey(step)],changed=s.flags[changedFlag(step)];if(progress!==undefined&&!integer(progress,0,3)||changed!==undefined&&changed!==true||changed&&progress!==3||progress===3&&(!proof||changed!==true)||proof&&(progress!==3||changed!==true))fail();
  }
  if(step.kind==='escort'){
   const rawEscort=s.receipts[escortKey(step)],e=parse<Escort>(rawEscort);if(rawEscort!==undefined&&(!object(e)||!keys(e,['v','x','z','next','metres','start'])||e.v!==1||!number(e.x,-5000,5000)||!number(e.z,-5000,5000)||!integer(e.next,0,3)||!number(e.metres,0,1e6)||!number(e.start,0,s.time)||e.metres>(s.time-e.start)*1.65+1))fail();
   if(proof&&(!e||e.next!==3||e.metres<3||!step.route[2]||distance(e,step.route[2])>.7)||e?.next===3&&!proof)fail();
  }
  if(step.kind==='combat'){
   const rawWave=s.receipts[waveKey(step)],wave=parse<Wave>(rawWave);if(rawWave!==undefined&&(!object(wave)||!keys(wave,['v','level','at'])||wave.v!==2||!integer(wave.level,1,CAMPAIGN_MAX_LEVEL)||!number(wave.at,previousTime,s.time)))fail();
   const rawSuspended=s.receipts[suspendedKey(step)],suspended=parse<{v:1;at:number}>(rawSuspended);if(rawSuspended!==undefined&&(!wave||!object(suspended)||!keys(suspended,['v','at'])||suspended.v!==1||!number(suspended.at,wave.at,s.time)))fail();
   petTrialKinds(step).forEach((_,index)=>{const killed=s.receipts[defeatedKey(step,index)],enemy=enemyFor(s,step,index);if(killed!==undefined&&(!defeated(s,step,index)||!wave)||enemy&&!validPetJourneyEnemy(s,enemy)||killed&&enemy&&(enemy.hp!==0||enemy.phase!=='dead'||enemy.diedAt===undefined)||petAvailable(s)&&wave&&!killed&&!enemy&&!suspended)fail();});
   if(proof&&(!wave||!trialDone(s,step)))fail();
  }
 }
 for(const enemies of [s.enemies,...Object.values(s.encounters)])for(const enemy of enemies)if(enemy.id.startsWith('petj-trial-')&&!validPetJourneyEnemy(s,enemy))fail();
}
