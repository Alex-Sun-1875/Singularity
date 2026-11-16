import type {GameState} from '../../../core/GameSession';
import {playableArea} from '../../journey/data/ChapterJourney';
import type {PetSpeciesId,PetSkillId,PetQuality} from '../data/Pets';
const PET_POLICY={capacity:3,maxBond:100,maxEssence:999999,maxTransactions:20000,maxSources:2048};
const PET_QUALITIES=['普通','珍兽','神兽'];
const PET_PROMOTIONS=[{quality:'珍兽',level:10,bond:20,gold:100,essence:20},{quality:'神兽',level:30,bond:60,gold:350,essence:70}] as const;
const petSpecies=(id:unknown)=>['ember_fox','stone_turtle','dew_sprite'].includes(id as string);
const petSkill=(id:unknown)=>['ferocity','haste','devotion'].includes(id as string);
const integer=(value:unknown,max=Number.MAX_SAFE_INTEGER,min=0):value is number=>typeof value==='number'&&Number.isSafeInteger(value)&&value>=min&&value<=max;
const object=(value:unknown):value is Record<string,any>=>!!value&&typeof value==='object'&&!Array.isArray(value)&&Object.getPrototypeOf(value)===Object.prototype;
const keys=(value:object,wanted:string[])=>Object.keys(value).sort().join()===wanted.slice().sort().join();
const petLevel=(pet:{xp:number})=>Math.floor((1+Math.sqrt(1+pet.xp/7.5))/2);
export interface LegacyPet {id:string;species:PetSpeciesId;quality:PetQuality;xp:number;bond:number;evolution:number;skills:PetSkillId[]}
export type LegacyPetAction={kind:'adopt';species:PetSpeciesId}|{kind:'deploy'|'rest'|'train'|'bond'|'evolve'|'promote';pet:string}|{kind:'learn';pet:string;skill:PetSkillId};
interface DefeatRecord {cycle:number;count:number;boss:boolean;experience:Record<string,number>;discarded?:number}
interface LegacyPetTransaction {request:string;action:LegacyPetAction;gold:number;essence:number;xp:number;level:number;ownerLevel:number;count?:number}
interface LegacyPetDeployment {request:string;active:string|null;count:number}
export interface LegacyPetState {version:1;revision:number;essence:number;active:string|null;roster:Record<string,LegacyPet>;defeats:Record<string,DefeatRecord>;transactions:LegacyPetTransaction[];deployment?:LegacyPetDeployment}
/** Exact v2 attributes are used only while validating a pre-migration save. */
export function legacyPetBonuses(s:GameState){
 const g=s.pets as unknown as LegacyPetState,pet=g.active?g.roster[g.active]:undefined,b={damagePercent:0,maxHpPercent:0,damageReductionPercent:0,healingReceivedPercent:0,resourceRegenPercent:0};if(!pet)return b;
 const growth=Math.log2(petLevel(pet)+1),shared=(1+PET_QUALITIES.indexOf(pet.quality)*.25)*(1+pet.bond*.002),native=shared*(1+(pet.evolution>=1?(pet.species==='ember_fox'?.15:.2):0))*(pet.skills.includes('devotion')?1+pet.bond*.002:1);
 if(pet.species==='ember_fox')b.damagePercent=2*growth*native;
 if(pet.species==='stone_turtle'){b.maxHpPercent=3*growth*native;const reduction=12*growth/(growth+8)*native;b.damageReductionPercent=35*reduction/(35+reduction);}
 if(pet.species==='dew_sprite'){b.healingReceivedPercent=3*growth*native;b.resourceRegenPercent=3*growth*native;}
 if(pet.evolution>=2){if(pet.species==='ember_fox')b.maxHpPercent+=.5*growth*shared;if(pet.species==='stone_turtle')b.resourceRegenPercent+=growth*shared;if(pet.species==='dew_sprite')b.damagePercent+=.5*growth*shared;}
 if(pet.skills.includes('ferocity'))b.damagePercent+=.75*growth*shared;if(pet.skills.includes('haste'))b.resourceRegenPercent+=growth*shared;return b;
}

const freshLegacyPets=():LegacyPetState=>({version:1,revision:0,essence:0,active:null,roster:{},defeats:{},transactions:[]});
function validAction(action:unknown):action is LegacyPetAction {
 if(!object(action)||typeof action.kind!=='string')return false;
 if(action.kind==='adopt')return keys(action,['kind','species'])&&!!petSpecies(action.species);
 if(!['deploy','rest','train','bond','evolve','promote','learn'].includes(action.kind)||typeof action.pet!=='string'||!petSpecies(action.pet))return false;
 return action.kind==='learn'?keys(action,['kind','pet','skill'])&&!!petSkill(action.skill):keys(action,['kind','pet']);
}
function apply(g:LegacyPetState,action:LegacyPetAction,xp:number){
 if(action.kind==='adopt')g.roster[action.species]={id:action.species,species:action.species,quality:'普通',xp:0,bond:0,evolution:0,skills:[]};
 else {const pet=g.roster[action.pet];if(action.kind==='deploy')g.active=pet.id;else if(action.kind==='rest')g.active=null;else if(action.kind==='train')pet.xp+=xp;else if(action.kind==='bond')pet.bond=Math.min(PET_POLICY.maxBond,pet.bond+10);else if(action.kind==='evolve')pet.evolution++;else if(action.kind==='promote')pet.quality=PET_PROMOTIONS[PET_QUALITIES.indexOf(pet.quality)].quality;else if(action.kind==='learn')pet.skills.push(action.skill);}
}
function evidence(s:GameState,key:string,cycle:number){
 const slash=key.indexOf('/'),area=key.slice(0,slash),id=key.slice(slash+1);
 if(slash<1||!playableArea(area))return null;
 const enemy=(s.area===area?s.enemies:s.encounters[area]??[]).find(e=>e.id===id);
 if(!enemy||enemy.trainingEnemy||enemy.trainingDummy)return null;
 if(enemy.respawnSeconds){if(cycle<1||Number(s.receipts[`hunt-cycle:${area}:${id}`]??0)<cycle)return null;}
 else if(enemy.bossId){if(s.receipts[`kill:${area}:${id}`]!==true||cycle>0&&Number(s.receipts[`boss:v3:${area}:${id}:life`]??-1)<cycle)return null;}
 else if(cycle!==0||s.receipts[`kill:${area}:${id}`]!==true)return null;
 return enemy;
}

export function validateLegacyPets(s:GameState,g:LegacyPetState,proofs:Record<string,string|number|boolean>=s.receipts):void {
 function invalid():never {throw new Error('无效的宠物、养成或战斗奖励记录');}
 const receiptKeys=Object.keys(proofs).filter(key=>key.startsWith('pet-'));
 if(g===undefined){if(receiptKeys.length)invalid();return;}
 if(!object(g)||!keys(g,['version','revision','essence','active','roster','defeats','transactions',...('deployment' in g?['deployment']:[])])||g.version!==1||!integer(g.revision)||!integer(g.essence,PET_POLICY.maxEssence)||!object(g.roster)||Object.keys(g.roster).length>PET_POLICY.capacity||!object(g.defeats)||Object.keys(g.defeats).length>PET_POLICY.maxSources||!Array.isArray(g.transactions)||g.transactions.length>PET_POLICY.maxTransactions||g.active!==null&&(typeof g.active!=='string'||!g.roster[g.active]))invalid();
 const replay=freshLegacyPets(),earned:Record<string,number>={};let essence=0,kills=0,operations=0;
 for(const [key,record]of Object.entries(g.defeats)){
  if(!object(record)||!keys(record,['cycle','count','boss','experience',...('discarded' in record?['discarded']:[])])||!integer(record.cycle)||!integer(record.count,Math.min(Number.MAX_SAFE_INTEGER,record.cycle+1),1)||typeof record.boss!=='boolean'||!object(record.experience)||record.discarded!==undefined&&!integer(record.discarded))invalid();
  const enemy=evidence(s,key,record.cycle);if(!enemy||record.boss!==!!enemy.bossId||enemy.respawnSeconds&&record.count>record.cycle)invalid();
  let total=0;for(const[id,xp]of Object.entries(record.experience)){if(!petSpecies(id)||!integer(xp,Number.MAX_SAFE_INTEGER,1))invalid();earned[id]=(earned[id]??0)+xp;total+=xp;if(!integer(earned[id])||!integer(total))invalid();}
  const reward=record.count*(record.boss?5:1);if(total>record.count*(record.boss?12:4)||(record.discarded??0)>reward)invalid();essence+=reward-(record.discarded??0);kills+=record.count;
 }
 let sequence=0;const requests=new Set<string>();
 for(const t of g.transactions){
  if(!object(t)||!keys(t,['request','action','gold','essence','xp','level','ownerLevel',...('count' in t?['count']:[])])||!validAction(t.action)||!integer(t.gold)||!integer(t.essence)||!integer(t.xp)||!integer(t.level,Number.MAX_SAFE_INTEGER,1)||!integer(t.ownerLevel,Number.MAX_SAFE_INTEGER,1)||typeof t.request!=='string'||t.count!==undefined&&(t.action.kind!=='train'||!integer(t.count,Math.floor(Number.MAX_SAFE_INTEGER/25),1)))invalid();
  const match=new RegExp(`^pet-${t.action.kind}:(\\d+)$`).exec(t.request),number=Number(match?.[1]);
  if(!match||!integer(number,s.sequence,1)||number<=sequence||requests.has(t.request)||proofs[t.request]!==JSON.stringify(t))invalid();sequence=number;requests.add(t.request);
  const action=t.action,pet=action.kind==='adopt'?undefined:replay.roster[action.pet];let gold=0,cost=0;
  if(action.kind==='adopt'){if(replay.roster[action.species])invalid();if(Object.keys(replay.roster).length){gold=80;cost=20;}}
  else{
   if(!pet)invalid();
   if(action.kind==='deploy'&&replay.active===pet.id||action.kind==='rest'&&replay.active!==pet.id)invalid();
   if(action.kind==='train'){const count=t.count??1;gold=15*count;cost=3*count;if(t.count===undefined?!integer(t.xp,25,1):t.xp!==25*count)invalid();}
   if(action.kind==='bond'){gold=10;cost=2;if(pet.bond>=PET_POLICY.maxBond)invalid();}
   if(action.kind==='evolve'){if(pet.evolution>=2||t.level<(pet.evolution?25:10)||pet.bond<(pet.evolution?60:20))invalid();gold=pet.evolution?300:100;cost=pet.evolution?60:20;}
   if(action.kind==='promote'){const promotion=PET_PROMOTIONS[PET_QUALITIES.indexOf(pet.quality)];if(!promotion||t.level<promotion.level||pet.bond<promotion.bond)invalid();gold=promotion.gold;cost=promotion.essence;}
   if(action.kind==='learn'){if(pet.skills.includes(action.skill)||pet.skills.length>=Number(t.level>=5)+Number(t.level>=15))invalid();gold=50;cost=10;}
  }
  if(t.gold!==gold||t.essence!==cost||action.kind!=='train'&&t.xp!==0||action.kind!=='adopt'&&t.level>petLevel(g.roster[action.pet]??{xp:0}))invalid();essence-=cost;operations+=t.count??1;apply(replay,action,t.xp);
 }
 let active=replay.active;
 if(g.deployment!==undefined){
  const deployment=g.deployment;if(!object(deployment)||!keys(deployment,['request','active','count'])||typeof deployment.request!=='string'||!integer(deployment.count,Number.MAX_SAFE_INTEGER,1)||deployment.active!==null&&(typeof deployment.active!=='string'||!g.roster[deployment.active]))invalid();
  const match=/^pet-deployment:(\d+)$/.exec(deployment.request);if(!match||!integer(Number(match[1]),s.sequence,1)||requests.has(deployment.request)||proofs[deployment.request]!==JSON.stringify(deployment))invalid();
  requests.add(deployment.request);operations+=deployment.count;active=deployment.active;
 }
 if(receiptKeys.length!==requests.size||receiptKeys.some(key=>!requests.has(key))||g.revision!==kills+operations||g.essence!==essence||active!==g.active||Object.keys(g.roster).sort().join()!==Object.keys(replay.roster).sort().join())invalid();
 for(const[id,pet]of Object.entries(g.roster)){
  if(!object(pet)||!keys(pet,['id','species','quality','xp','bond','evolution','skills'])||pet.id!==id||pet.species!==id||!petSpecies(id)||!PET_QUALITIES.includes(pet.quality)||!integer(pet.xp)||!integer(pet.bond,100)||!integer(pet.evolution,2)||!Array.isArray(pet.skills)||pet.skills.length>2||new Set(pet.skills).size!==pet.skills.length||pet.skills.some(skill=>!petSkill(skill)))invalid();
  const expected=replay.roster[id];if(pet.quality!==expected.quality||pet.xp!==expected.xp+(earned[id]??0)||pet.bond!==expected.bond||pet.evolution!==expected.evolution||JSON.stringify(pet.skills)!==JSON.stringify(expected.skills))invalid();
  const level=petLevel(pet);if(pet.evolution>0&&level<10||pet.evolution>1&&level<25||pet.skills.length>Number(level>=5)+Number(level>=15))invalid();
 }
 if(Object.keys(earned).some(id=>!g.roster[id]))invalid();
}
