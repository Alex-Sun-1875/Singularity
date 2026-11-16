import type {GameState,EnemyState} from '../../../core/GameSession';
import {playableArea} from '../../journey/data/ChapterJourney';
import {PET_POLICY,PET_SPECIES,PET_SKILLS,PET_QUALITIES,PET_PROMOTIONS,PET_RESEARCH_COSTS,PET_RESEARCH_VALUES,petSpecies,petSkill,petSignatureGrowth,type PetSpeciesId,type PetRole,type PetSkillId,type PetQuality,type PetBranch} from '../data/Pets';
import {validateLegacyPets,legacyPetBonuses,type LegacyPetState} from './PetLegacy';
import {petAcquisitionReady,petManualUnlocked,petJournal,petSpeciesProofs,petProgressReward} from './PetJourneys';
import {petAccess,petAvailable} from './PetAccess';

export type {PetSpeciesId,PetRole,PetSkillId,PetQuality,PetBranch} from '../data/Pets';
export interface Pet {id:string;species:PetSpeciesId;quality:PetQuality;xp:number;bond:number;evolution:number;skills:PetSkillId[];signatureRank:1|2|3;branch:PetBranch|null;traitSlots:[PetSkillId|null,PetSkillId|null];catchupLevel:number}
export type PetAction={kind:'adopt';species:PetSpeciesId}|{kind:'deploy'|'rest'|'train'|'bond'|'promote';pet:string}|{kind:'research';skill:PetSkillId}|{kind:'assign';pet:string;slot:0|1;skill:PetSkillId|null}|{kind:'study';pet:string;branch?:PetBranch}|{kind:'branch';pet:string;branch:PetBranch}|{kind:'claim'};
interface DefeatRecord {cycle:number;count:number;boss:boolean;experience:Record<string,number>;discarded:number}
interface ProgressRecord {pet:string|null;xp:number;essence:number;bond:number;discarded:number}
interface Transaction {request:string;action:PetAction;gold:number;essence:number;xp:number;level:number;bond:number;count?:number;catchupLevel?:number}
interface Deployment {request:string;active:string|null;count:number}
interface Configuration {request:string;slots:[PetSkillId|null,PetSkillId|null];count:number}
interface BranchConfiguration {request:string;branch:PetBranch;count:number}
interface LegacyAudit {state:LegacyPetState;receipts:Record<string,string|number|boolean>}
export interface PetState {version:2;revision:number;essence:number;active:string|null;roster:Record<string,Pet>;defeats:Record<string,DefeatRecord>;progress:Record<string,ProgressRecord>;transactions:Transaction[];research:Partial<Record<PetSkillId,number>>;configurations:Record<string,Configuration>;branches:Record<string,BranchConfiguration>;pending:{gold:number;essence:number};deployment?:Deployment;legacy?:LegacyAudit}
export interface PetQuote {allowed:boolean;reason:string;token:string;gold:number;essence:number;description:string;refundGold:number;refundEssence:number}
export interface PetBonuses {damagePercent:number;maxHpPercent:number;damageReductionPercent:number;healingReceivedPercent:number;resourceRegenPercent:number}
export interface PetCombatProfile extends PetBonuses {id:string;species:PetSpeciesId;quality:PetQuality;role:PetRole}
export interface PetSignatureView {name:string;rank:1|2|3;branch:PetBranch|null;description:string;trigger:string;effect:'echo'|'damage'|'reduction'|'resource'|'healing';percent:number;duration:number;cooldown:number;healthThreshold:number;resourceThreshold:number;branches:readonly {id:PetBranch;name:string;description:string}[]}
export interface PetView extends Pet,PetCombatProfile {name:string;level:number;nextXp:number;nativeSkill:string;bonuses:PetBonuses;signature:PetSignatureView;journal:ReturnType<typeof petJournal>;proof:ReturnType<typeof petSpeciesProofs>;evolutionSkills:{id:PetBranch;name:string;description:string;learned:boolean}[]}
interface Host {state():GameState;availability():{available:boolean;reason:string};id(prefix:string):string;changed():void;recalculate?():void;emit(type:string,text:string,extra?:Record<string,unknown>):void}
const copy=<T>(value:T):T=>JSON.parse(JSON.stringify(value));
const integer=(value:unknown,max=Number.MAX_SAFE_INTEGER,min=0):value is number=>typeof value==='number'&&Number.isSafeInteger(value)&&value>=min&&value<=max;
const object=(value:unknown):value is Record<string,any>=>!!value&&typeof value==='object'&&!Array.isArray(value)&&Object.getPrototypeOf(value)===Object.prototype;
const keys=(value:object,wanted:string[])=>Object.keys(value).sort().join()===wanted.slice().sort().join();
function reject(reason:string):never {throw new Error(reason);}
export const freshPets=():PetState=>({version:2,revision:0,essence:0,active:null,roster:{},defeats:{},progress:{},transactions:[],research:{},configurations:{},branches:{},pending:{gold:0,essence:0}});
export const petXpForLevel=(level:number)=>30*(level-1)*level;
export function petLevel(pet:Pick<Pet,'xp'>):number {const level=Math.max(1,Math.floor((1+Math.sqrt(1+pet.xp/7.5))/2));return petXpForLevel(level)>pet.xp?level-1:petXpForLevel(level+1)<=pet.xp?level+1:level;}
const knownBranch=(value:unknown):value is PetBranch=>value==='A'||value==='B';
const traitSlots=(pet:Pet)=>pet.traitSlots.filter((id):id is PetSkillId=>id!==null);
function newPet(species:PetSpeciesId,catchupLevel=1):Pet {return {id:species,species,quality:petSpecies(species)!.nativeQuality,xp:0,bond:0,evolution:0,skills:[],signatureRank:1,branch:null,traitSlots:[null,null],catchupLevel};}
function foundation(legacy?:LegacyAudit):PetState {
 const g=freshPets();if(!legacy)return g;g.legacy=copy(legacy);g.essence=legacy.state.essence;g.active=legacy.state.active;
 const copies:Partial<Record<PetSkillId,number>>={};
 for(const old of Object.values(legacy.state.roster)){
  const pet={...newPet(old.species),...copy(old),signatureRank:(old.evolution+1) as 1|2|3,branch:old.evolution?'A' as const:null,traitSlots:[old.skills[0]??null,old.skills[1]??null] as [PetSkillId|null,PetSkillId|null]};
  g.roster[pet.id]=pet;g.pending.gold+=old.evolution===1?20:old.evolution===2?80:0;
  for(const id of old.skills){g.research[id]=2;copies[id]=(copies[id]??0)+1;}
 }
 for(const count of Object.values(copies)){g.pending.gold+=Math.max(0,count!-1)*50;g.pending.essence+=Math.max(0,count!-1)*10;}
 return g;
}
/** Called after the save has passed its original validator. Paid v1 progress is retained. */
export function migratePets(s:GameState):boolean {
 const raw=s.pets as unknown;if(raw===undefined){s.pets=freshPets();return true;}
 if(object(raw)&&raw.version===1){validateLegacyPets(s,raw as LegacyPetState);const receipts=Object.fromEntries(Object.entries(s.receipts).filter(([key])=>key.startsWith('pet-')));s.pets=foundation({state:raw as LegacyPetState,receipts});return true;}return false;
}
const researchRank=(s:GameState,g:PetState,id:PetSkillId)=>Math.max(g.research[id]??0,petManualUnlocked(s,id)?1:0);
export const petResearchRank=(s:GameState,id:PetSkillId)=>researchRank(s,s.pets,id);
export function petSignatureView(pet:Pet):PetSignatureView {
 const definition=petSpecies(pet.species)!.signature,h=petSignatureGrowth(petLevel(pet)),rank=pet.signatureRank,branch=pet.branch;
 let effect:PetSignatureView['effect']='resource',percent=4+8*h,duration=6,cooldown=20,healthThreshold=0,resourceThreshold=0;
 switch(pet.species){
  case 'ember_fox':effect=branch==='B'?'reduction':'echo';percent=branch==='B'?4+6*h:branch==='A'?6+10*h:4+6*h;duration=branch==='B'?4:0;cooldown=18;break;
  case 'stone_turtle':effect='reduction';percent=branch==='A'?6+10*h:branch==='B'?2+5*h:4+8*h;duration=branch==='B'?4:5;cooldown=rank===3?18:20;healthThreshold=.12;break;
  case 'dew_sprite':effect=branch==='B'?'healing':'resource';percent=branch==='A'?3+5*h:4+6*h;duration=branch==='A'?8:6;break;
  case 'tabby_cat':effect=branch==='B'?'reduction':'damage';percent=branch==='B'?3+5*h:4+6*h;duration=branch==='B'?4:5;cooldown=18;break;
  case 'hunting_dog':effect=branch==='B'?'reduction':'resource';percent=branch==='B'?3+5*h:4+8*h;cooldown=30;break;
  case 'grey_wolf':effect=branch==='B'?'reduction':'damage';percent=branch==='B'?3+5*h:4+6*h;duration=5;break;
  case 'mountain_tiger':effect=branch==='B'?'reduction':'resource';percent=branch==='B'?4+6*h:4+8*h;duration=branch==='B'?4:6;cooldown=22;healthThreshold=.4;break;
  case 'hunting_hawk':effect='damage';percent=branch==='B'?3+4*h:4+6*h;duration=branch==='B'?4:5;break;
  case 'spotted_deer':effect='resource';percent=branch==='B'?3+5*h:4+8*h;duration=5;cooldown=branch==='A'?18:20;resourceThreshold=branch==='B'?.7:.4;break;
  case 'griffin':effect='reduction';percent=branch==='B'?6+8*h:8+12*h;duration=0;cooldown=branch==='B'?36:60;healthThreshold=branch==='B'?.3:0;break;
  case 'white_tiger':effect=branch==='B'?'resource':'echo';percent=branch==='B'?4+8*h:6+8*h;duration=branch==='B'?6:4;cooldown=24;break;
  case 'dragon':effect=branch==='B'?'reduction':'echo';percent=branch==='B'?4+6*h:6+8*h;duration=branch==='B'?4:0;cooldown=24;break;
 }
 if(rank===3&&pet.species!=='stone_turtle')cooldown*=.9;
 const selected=definition.branches.find(value=>value.id===branch);
 let trigger=definition.description;
 switch(pet.species){
  case 'ember_fox':trigger=branch==='A'?'玩家直接命中仍存活的原目标；目标生命不高于35%时强化回响，其余目标使用基础回响。':'玩家直接命中后，原目标仍存活且可见；持续伤害与其他衍生伤害不触发。';break;
  case 'stone_turtle':trigger='单次真实敌方攻击实际掉血达到最大生命12%'+(rank>=2?'，或3秒内至少两次不同攻击累计掉血达到20%':'')+'；只保护后续攻击，不追溯减免触发的一击。';break;
  case 'dew_sprite':trigger='一次真实药水、技能或装备治疗恢复了生命；满血空用与宠物衍生治疗不触发。';break;
  case 'tabby_cat':trigger='3秒内受到两个不同敌人的真实伤害；同一招多段不重复计数。';break;
  case 'hunting_dog':trigger='真正脱战至少6秒后重新进入战斗；开关菜单不算脱战。';break;
  case 'grey_wolf':trigger='6秒内受到三次不同攻击；同一招多段只计一次。';break;
  case 'mountain_tiger':trigger='生命低于40%时，一次真实治疗恢复了生命。';break;
  case 'hunting_hawk':trigger=branch==='B'?'成功闪避一次真实来袭攻击。':'与目标保持至少5米距离，5秒内用不同攻击连续命中同一目标两次；失去视线终止。';break;
  case 'spotted_deer':trigger=`当前职业资源不高于${resourceThreshold*100}%时，成功闪避一次真实来袭攻击。`;break;
  case 'griffin':trigger=branch==='B'?'生命不高于30%时受到一次真实敌方攻击；只减轻这一击，不保证免死。':'真实敌方攻击扣除护盾后将会致命时减轻这一击；减后仍致命则照常死亡，不锁1血。';break;
  case 'white_tiger':trigger=branch==='B'?'成功闪避一次真实来袭攻击。':'一次直接命中后4秒内成功闪避来袭攻击，向仍存活且可见的原目标回击。';break;
  case 'dragon':trigger='从真实敌方控制中恢复后的6秒内，首个合法直接命中；自身施法后摇与环境伤害不触发。';break;
 }
 const effectText=effect==='echo'?`回响为触发命中实际扣血的${percent.toFixed(3)}%`:`${effect==='damage'?'伤害':effect==='reduction'?'独立减伤':effect==='resource'?'职业资源自然恢复':'受治疗'}增益${percent.toFixed(3)}%`;
 const description=trigger+' '+effectText+(selected?' '+selected.name+'：'+selected.description:'');
 return {name:definition.name,rank,branch,description,trigger,effect,percent,duration,cooldown,healthThreshold,resourceThreshold,branches:definition.branches};
}
export const petMetamorphosisTraits=(pet:Pet)=>petSpecies(pet.species)!.signature.branches.map(branch=>({...branch,learned:pet.branch===branch.id}));
export const petEvolutionSkills=petMetamorphosisTraits;
const zeroBonuses=():PetBonuses=>({damagePercent:0,maxHpPercent:0,damageReductionPercent:0,healingReceivedPercent:0,resourceRegenPercent:0});
const ZERO_BONUSES=Object.freeze(zeroBonuses());
function bonuses(s:GameState,pet:Pet,target?:EnemyState):PetBonuses {
 const b=zeroBonuses(),g=Math.log2(petLevel(pet)+1),u=.75+.25*g/(g+4),rank=(id:PetSkillId)=>pet.traitSlots.includes(id)?researchRank(s,s.pets,id):0;
 const shared=(1+PET_QUALITIES.indexOf(pet.quality)*.15)*(1+pet.bond*.002),native=shared*(1+rank('devotion')*2*u/100),p=s.player;
 const nearby=s.enemies.filter(enemy=>enemy.hp>0&&Math.hypot(enemy.x-p.x,enemy.z-p.z)<=3).length,ratio=p.maxHp>0?p.hp/p.maxHp:1;
 let reduction=0;
 switch(pet.species){
  case 'ember_fox':b.damagePercent=2*g;break;
  case 'stone_turtle':b.maxHpPercent=2*g;reduction=1.5*g;break;
  case 'dew_sprite':b.healingReceivedPercent=2*g;b.resourceRegenPercent=2*g;break;
  case 'tabby_cat':b.maxHpPercent=1.2*g;b.damagePercent=nearby>=2?2*g:0;break;
  case 'hunting_dog':b.resourceRegenPercent=2*g;b.healingReceivedPercent=s.combat.engagement?0:1.5*g;break;
  case 'grey_wolf':b.maxHpPercent=.8*g;reduction=Math.min(3,nearby)*g;break;
  case 'mountain_tiger':b.resourceRegenPercent=.8*g;b.healingReceivedPercent=(ratio<=.5?3:.4)*g;break;
  case 'hunting_hawk':b.damagePercent=(target&&Math.hypot(target.x-p.x,target.z-p.z)>=5?2.4:.6)*g;break;
  case 'spotted_deer':b.resourceRegenPercent=((s.combat.buffs['pet:movementGraceUntil']??0)>s.time?3:.6)*g;break;
  case 'griffin':b.maxHpPercent=1.4*g;b.healingReceivedPercent=1.6*g;break;
  case 'white_tiger':b.resourceRegenPercent=g;reduction=.6*g;break;
  case 'dragon':b.maxHpPercent=.8*g;b.damagePercent=(target?.phase==='windup'?1.8:.4)*g;break;
 }
 for(const key of Object.keys(b) as (keyof PetBonuses)[])b[key]*=native;
 reduction*=native;b.damageReductionPercent=35*reduction/(35+reduction);
 b.damagePercent+=rank('ferocity')*PET_RESEARCH_VALUES.ferocity*u;b.resourceRegenPercent+=rank('haste')*PET_RESEARCH_VALUES.haste*u;b.maxHpPercent+=rank('thick_hide')*PET_RESEARCH_VALUES.thick_hide*u;b.healingReceivedPercent+=rank('moisture')*PET_RESEARCH_VALUES.moisture*u;
 if(target&&target.hp>target.maxHp*.8)b.damagePercent+=rank('daybreak')*u;
 if(target&&(target.bossId||target.kind==='captain'||target.templateId?.includes('ALPHA')))b.damagePercent+=rank('keen_edge')*PET_RESEARCH_VALUES.keen_edge*u;
 if(s.flags['pet:reverseWind']||ratio<=.35){const extra=rank('headwind')*u;b.damageReductionPercent=100*(1-(1-b.damageReductionPercent/100)*(1-extra/100));}
 return b;
}
export function petBonuses(s:GameState,target?:EnemyState):Readonly<PetBonuses> {if(!petAvailable(s))return ZERO_BONUSES;if((s.pets as unknown as {version:number})?.version===1)return legacyPetBonuses(s);const pet=s.pets?.active?s.pets.roster[s.pets.active]:undefined;return pet?bonuses(s,pet,target):ZERO_BONUSES;}
/** Save validation only: recognize exact active-pet HP in an older enabled save
 * before the closed runtime removes its effects and clamps current health. */
export function petSnapshotMaxHealth(s:GameState,base:number):number {const raw=s.pets as unknown as {version:number}|undefined;if(!raw)return base;const pet=s.pets.active?s.pets.roster[s.pets.active]:undefined;if(!pet)return base;const bonus=raw.version===1?legacyPetBonuses(s):bonuses(s,pet);return Math.round(base*(1+bonus.maxHpPercent/100));}
export function petCombatProfile(s:GameState):PetCombatProfile|null {if(!petAvailable(s)||s.status==='dead'||s.player.hp<=0)return null;const pet=s.pets.active?s.pets.roster[s.pets.active]:undefined;return pet?{id:pet.id,species:pet.species,quality:pet.quality,role:petSpecies(pet.species)!.role,...bonuses(s,pet)}:null;}
function validAction(action:unknown):action is PetAction {
 if(!object(action)||typeof action.kind!=='string')return false;
 if(action.kind==='adopt')return keys(action,['kind','species'])&&!!petSpecies(action.species);
 if(action.kind==='claim')return keys(action,['kind']);
 if(action.kind==='research')return keys(action,['kind','skill'])&&!!petSkill(action.skill);
 if(typeof action.pet!=='string'||!petSpecies(action.pet))return false;
 if(action.kind==='assign')return keys(action,['kind','pet','slot','skill'])&&(action.slot===0||action.slot===1)&&(action.skill===null||!!petSkill(action.skill));
 if(action.kind==='branch')return keys(action,['kind','pet','branch'])&&knownBranch(action.branch);
 if(action.kind==='study')return keys(action,['kind','pet',...('branch' in action?['branch']:[])])&&(action.branch===undefined||knownBranch(action.branch));
 return ['deploy','rest','train','bond','promote'].includes(action.kind)&&keys(action,['kind','pet']);
}
interface Cost {gold:number;essence:number;xp:number;level:number;bond:number;description:string;catchupLevel?:number}
function cost(s:GameState,g:PetState,action:PetAction,historical?:{level:number;bond:number;catchupLevel?:number}):Cost {
 const pet='pet' in action?g.roster[action.pet]:undefined;if('pet' in action&&!pet)reject('尚未与这位伙伴结伴。');
 const level=historical?.level??(pet?petLevel(pet):1),bond=historical?.bond??pet?.bond??0,name=pet?petSpecies(pet.species)!.name:'',q:Cost={gold:0,essence:0,xp:0,level,bond,description:''};
 if(action.kind==='adopt'){
  if(g.roster[action.species])reject('已经与这类伙伴结伴。');if(Object.keys(g.roster).length>=PET_POLICY.capacity)reject('伙伴册已包含全部伙伴。');if(!petAcquisitionReady(s,action.species))reject('请先完成这位伙伴的相遇故事。');
  q.catchupLevel=historical?.catchupLevel??Math.max(1,...Object.values(g.roster).map(petLevel));q.description=`与${petSpecies(action.species)!.name}结伴，加入时1级；追赶基准为${q.catchupLevel}级。`;
 }else if(action.kind==='research'){
  const rank=researchRank(s,g,action.skill);if(!rank)reject('请先通过实际探索、救助或试炼发现这本手册。');if(rank>=5)reject('本手册已研究至V阶，伙伴等级仍可继续成长。');const next=PET_RESEARCH_COSTS[rank+1];q.gold=next.gold;q.essence=next.essence;q.description=`${petSkill(action.skill)!.name}研究至${rank+1}阶，所有伙伴共享研究成果。`;
 }else if(action.kind==='claim'){
  const gold=Math.min(g.pending.gold,Math.max(0,9999-s.player.gold)),essence=Math.min(g.pending.essence,PET_POLICY.maxEssence-g.essence);if(!gold&&!essence)reject(g.pending.gold||g.pending.essence?'请先腾出金币或灵蕴容量。':'没有待领取的旧版投入返还。');q.gold=-gold;q.essence=-essence;q.description=`领取旧版重复投入返还：金币${gold}，灵蕴${essence}。`;
 }else if(pet){
  switch(action.kind){
   case 'deploy':if(g.active===pet.id)reject('伙伴已经出战。');q.description=`让${name}出战，仅这一位伙伴提供战力。`;break;
   case 'rest':if(g.active!==pet.id)reject('伙伴已经休息。');q.description=`让${name}休息。`;break;
   case 'train':if(!integer(pet.xp+25))reject('经验接近存档数值安全精度。');q.gold=15;q.essence=3;q.xp=25;q.description=`培养${name}，获得25经验；手动培养不享受追赶倍率。`;break;
   case 'bond':if(bond>=100)reject('共鸣已经达到100。');q.gold=10;q.essence=2;q.description=`照料${name}，共鸣提高10。`;break;
   case 'assign':{
    if(level<(action.slot===0?5:15))reject(`${action.slot===0?5:15}级开放这个特性槽。`);if(action.skill&&!researchRank(s,g,action.skill))reject('尚未发现或研究这项特性。');if(action.skill&&pet.traitSlots[1-action.slot]===action.skill)reject('两槽不能重复配置同一特性。');if(pet.traitSlots[action.slot]===action.skill)reject('这个槽位已经采用该配置。');q.description=`免费调整${name}的第${action.slot+1}个特性槽，保留研究投入。`;break;
   }
   case 'branch':if(pet.signatureRank<2)reject('伴行技II阶后可选择蜕变路径。');if(pet.branch===action.branch)reject('已经采用这条蜕变路径。');q.description=`免费切换为${petSpecies(pet.species)!.signature.branches.find(value=>value.id===action.branch)!.name}；保留公共冷却。`;break;
   case 'study':{
    if(pet.signatureRank>=3)reject('伴行技已达III阶，伙伴等级仍可继续成长。');const journal=petJournal(s,pet.species),proof=petSpeciesProofs(s,pet.species);
    if(pet.signatureRank===1){if(level<15||bond<20||new Set(journal.map(item=>item.category)).size<3)reject('伴行技II阶需要15级、共鸣20和三类同行纪事。');if(!knownBranch(action.branch))reject('请选择A或B蜕变路径。');q.gold=80;q.essence=20;}
    else {if(level<40||bond<60||!proof.trial)reject('伴行技III阶需要40级、共鸣60和这位伙伴的专属试炼。');q.gold=240;q.essence=60;}
    q.description=`${petSpecies(pet.species)!.signature.name}进修至${pet.signatureRank+1}阶，保留现有冷却。`;break;
   }
   case 'promote':{
    const index=PET_QUALITIES.indexOf(pet.quality),promotion=PET_PROMOTIONS[index];if(!promotion)reject('已经达到神兽品阶，等级与属性仍可继续成长。');const journal=petJournal(s,pet.species),proof=petSpeciesProofs(s,pet.species);
    if(level<promotion.level||bond<promotion.bond)reject(`升格需要${promotion.level}级、共鸣${promotion.bond}。`);
    if(index===0&&(new Set(journal.map(item=>item.category)).size<3||!proof.habit))reject('请完成三类同行纪事与这位伙伴的理解习性委托。');
    if(index===1&&(new Set(journal.map(item=>item.id)).size<8||!['guard','adapt','cooperate'].every(value=>proof.trials.includes(value as 'guard'|'adapt'|'cooperate'))||!proof.final))reject('请完成八条不同纪事、守护／应变／协作三类试炼与最终同行故事。');
    q.gold=promotion.gold;q.essence=promotion.essence;q.description=`${name}升格为${promotion.quality}，保留物种、等级、共鸣与研究；不兑换其他神兽。`;break;
   }
  }
 }
 return q;
}
function applyPaid(g:PetState,action:PetAction,xp:number,catchupLevel?:number){
 if(action.kind==='adopt')g.roster[action.species]=newPet(action.species,catchupLevel??1);
 else if(action.kind==='research')g.research[action.skill]=Math.max(1,g.research[action.skill]??1)+1;
 else if('pet' in action){const pet=g.roster[action.pet];if(action.kind==='train')pet.xp+=xp;else if(action.kind==='bond')pet.bond=Math.min(100,pet.bond+10);else if(action.kind==='study'){pet.signatureRank++;pet.evolution=pet.signatureRank-1;if(action.branch)pet.branch=action.branch;}else if(action.kind==='promote')pet.quality=PET_PROMOTIONS[PET_QUALITIES.indexOf(pet.quality)].quality;}
}
function killEvidence(s:GameState,key:string,cycle:number){
 const slash=key.indexOf('/'),area=key.slice(0,slash),id=key.slice(slash+1);if(slash<1||!playableArea(area))return null;
 const enemy=(s.area===area?s.enemies:s.encounters[area]??[]).find(e=>e.id===id);if(!enemy||enemy.trainingEnemy||enemy.trainingDummy)return null;
 if(enemy.respawnSeconds){if(cycle<1||Number(s.receipts[`hunt-cycle:${area}:${id}`]??0)<cycle)return null;}
 else if(enemy.bossId){if(s.receipts[`kill:${area}:${id}`]!==true||cycle>0&&Number(s.receipts[`boss:v3:${area}:${id}:life`]??-1)<cycle)return null;}
 else if(cycle!==0||s.receipts[`kill:${area}:${id}`]!==true)return null;return enemy;
}
function earnedExperience(pet:Pet,base:number){const limit=petXpForLevel(pet.catchupLevel),gap=Math.max(0,limit-pet.xp);return Math.min(Number.MAX_SAFE_INTEGER-pet.xp,base+Math.min(base*2,gap));}
export class PetSystem {
 constructor(private host:Host){}
 view(){
  const s=this.host.state(),g=s.pets,access=this.host.availability(),feature=petAccess(s),roster:PetView[]=Object.values(g.roster).map(pet=>{const level=petLevel(pet),species=petSpecies(pet.species)!;return {...copy(pet),id:pet.id,role:species.role,...bonuses(s,pet),name:species.name,level,xp:pet.xp-petXpForLevel(level),nextXp:petXpForLevel(level+1)-petXpForLevel(level),nativeSkill:species.nativeSkill,bonuses:bonuses(s,pet),signature:petSignatureView(pet),journal:petJournal(s,pet.species),proof:petSpeciesProofs(s,pet.species),evolutionSkills:petMetamorphosisTraits(pet)};});
  return {enabled:feature.available,available:feature.available&&access.available,reason:feature.available?access.reason:feature.reason,essence:g.essence,active:g.active,roster,pending:{...g.pending},species:PET_SPECIES.map(species=>({...species,owned:!!g.roster[species.id],acquirable:feature.available&&petAcquisitionReady(s,species.id)})),research:PET_SKILLS.map(skill=>{const rank=researchRank(s,g,skill.id),next=PET_RESEARCH_COSTS[Math.min(5,rank+1)];return {...skill,rank,unlocked:rank>0,nextGold:rank<5?next.gold:0,nextEssence:rank<5?next.essence:0};})};
 }
 quote(action:PetAction):PetQuote {
  const s=this.host.state(),g=s.pets,q:PetQuote={allowed:false,reason:'',token:JSON.stringify([g.revision,s.revision,s.sequence,s.player.gold,action]),gold:0,essence:0,description:'',refundGold:0,refundEssence:0};
  try{
   if(!validAction(action))reject('无效的宠物操作。');const feature=petAccess(s);if(!feature.available)reject(feature.reason);const c=cost(s,g,action);q.gold=Math.max(0,c.gold);q.essence=Math.max(0,c.essence);q.refundGold=Math.max(0,-c.gold);q.refundEssence=Math.max(0,-c.essence);q.description=c.description;
   const access=this.host.availability();if(!access.available)reject(access.reason);
   if(!integer(g.revision+1))reject('操作次数接近存档数值安全精度。');if(s.player.gold<c.gold)reject('金币不足。');if(g.essence<c.essence)reject('灵蕴不足。');q.allowed=true;
  }catch(error){q.reason=error instanceof Error?error.message:'无效的宠物操作。';}return q;
 }
 commit(action:PetAction,token:string):boolean {
  const quote=this.quote(action);if(!quote.allowed||quote.token!==token)return false;const s=this.host.state(),g=s.pets,c=cost(s,g,action);let request:string;
  if(action.kind==='deploy'||action.kind==='rest'){
   g.active=action.kind==='deploy'?action.pet:null;const d={request:g.deployment?.request??this.host.id('pet3-deployment'),active:g.active,count:(g.deployment?.count??0)+1};g.deployment=d;request=d.request;s.receipts[request]=JSON.stringify(d);
  }else if(action.kind==='assign'){
   const pet=g.roster[action.pet];pet.traitSlots[action.slot]=action.skill;pet.skills=traitSlots(pet);const previous=g.configurations[pet.id],d={request:previous?.request??this.host.id('pet3-config'),slots:copy(pet.traitSlots),count:(previous?.count??0)+1};g.configurations[pet.id]=d;request=d.request;s.receipts[request]=JSON.stringify(d);
  }else if(action.kind==='branch'){
   const pet=g.roster[action.pet];pet.branch=action.branch;const previous=g.branches[pet.id],d={request:previous?.request??this.host.id('pet3-branch'),branch:action.branch,count:(previous?.count??0)+1};g.branches[pet.id]=d;request=d.request;s.receipts[request]=JSON.stringify(d);
  }else{
   const prior=action.kind==='train'?g.transactions.find(t=>t.action.kind==='train'&&t.action.pet===action.pet):action.kind==='claim'?g.transactions.find(t=>t.action.kind==='claim'):undefined;
   applyPaid(g,action,c.xp,c.catchupLevel);g.essence-=c.essence;s.player.gold-=c.gold;if(action.kind==='claim'){g.pending.gold+=c.gold;g.pending.essence+=c.essence;}
   let t:Transaction;if(prior){t=prior;t.count=(t.count??1)+1;t.gold+=c.gold;t.essence+=c.essence;t.xp+=c.xp;t.level=c.level;t.bond=c.bond;}else{t={request:this.host.id(`pet3-${action.kind}`),action:copy(action),gold:c.gold,essence:c.essence,xp:c.xp,level:c.level,bond:c.bond,...(['train','claim'].includes(action.kind)?{count:1}:{}),...(c.catchupLevel!==undefined?{catchupLevel:c.catchupLevel}:{})};g.transactions.push(t);}request=t.request;s.receipts[request]=JSON.stringify(t);
  }
  g.revision++;this.host.recalculate?.();this.host.changed();this.host.emit('pets',c.description);return true;
 }
 recordDefeat(enemy:EnemyState):boolean {
  const s=this.host.state(),g=s.pets;if(!petAvailable(s)||s.status==='dead'||s.player.hp<=0||enemy.hp>0||enemy.phase!=='dead'||enemy.diedAt!==s.time||!s.enemies.includes(enemy)||enemy.trainingEnemy||enemy.trainingDummy||!Object.keys(g.roster).length)return false;
  const cycle=enemy.respawnSeconds?(enemy.respawnCount??0)+1:enemy.respawnCount??0,key=`${s.area}/${enemy.id}`,old=g.defeats[key],legacy=g.legacy?.state.defeats[key];
  if(!killEvidence(s,key,cycle)||cycle<=Math.max(old?.cycle??-1,legacy?.cycle??-1)||!old&&Object.keys(g.defeats).length>=PET_POLICY.maxSources)return false;
  const record=old??{cycle,count:0,boss:!!enemy.bossId,experience:{},discarded:0},essence=enemy.bossId?5:1,received=Math.min(essence,PET_POLICY.maxEssence-g.essence),pet=g.active?g.roster[g.active]:undefined;
  if(pet){const xp=earnedExperience(pet,enemy.bossId?12:4);pet.xp+=xp;record.experience[pet.id]=(record.experience[pet.id]??0)+xp;}
  record.cycle=cycle;record.count++;record.discarded+=essence-received;g.defeats[key]=record;g.essence+=received;g.revision++;this.host.recalculate?.();this.host.changed();this.host.emit('pets',`灵蕴 +${received}`);return true;
 }
 recordProgress(source:string):boolean {
  const s=this.host.state(),g=s.pets;if(!petAvailable(s)||g.progress[source])return false;const reward=petProgressReward(s,source);if(!reward)return false;
  const pet=reward.pet?g.roster[reward.pet]:undefined;if(reward.pet&&!pet)return false;const xp=pet?earnedExperience(pet,reward.xp):0,bond=pet?Math.min(reward.bond,100-pet.bond):0,received=Math.min(reward.essence,PET_POLICY.maxEssence-g.essence);
  if(pet){pet.xp+=xp;pet.bond+=bond;}g.progress[source]={pet:reward.pet,xp,essence:reward.essence,bond,discarded:reward.essence-received};g.essence+=received;g.revision++;this.host.recalculate?.();this.host.changed();this.host.emit('pets',`同行经验 +${xp} · 灵蕴 +${received}`);return true;
 }
}
/** Rebuild all v3 paid progress and rewards; v1 remains a separately verified audit. */
export function validatePets(s:GameState):void {
 function invalid():never {throw new Error('无效的宠物获取、研究或培养记录');}
 const raw=s.pets as unknown;if(raw===undefined){if(Object.keys(s.receipts).some(key=>key.startsWith('pet-')||key.startsWith('pet3-')))invalid();return;}
 if(object(raw)&&raw.version===1){validateLegacyPets(s,raw as LegacyPetState);return;}
 if(!object(raw)||raw.version!==2)invalid();const g=raw as unknown as PetState;
 if(!keys(g,['version','revision','essence','active','roster','defeats','progress','transactions','research','configurations','branches','pending',...('deployment' in g?['deployment']:[]),...('legacy' in g?['legacy']:[])])||!integer(g.revision)||!integer(g.essence,PET_POLICY.maxEssence)||!object(g.roster)||Object.keys(g.roster).length>12||!object(g.defeats)||Object.keys(g.defeats).length>PET_POLICY.maxSources||!object(g.progress)||Object.keys(g.progress).length>PET_POLICY.maxSources||!Array.isArray(g.transactions)||g.transactions.length>PET_POLICY.maxTransactions||!object(g.research)||!object(g.configurations)||!object(g.branches)||!object(g.pending)||!keys(g.pending,['gold','essence'])||!integer(g.pending.gold)||!integer(g.pending.essence)||g.active!==null&&(typeof g.active!=='string'||!g.roster[g.active]))invalid();
 const requests=new Set<string>();
 if(g.legacy){if(!object(g.legacy)||!keys(g.legacy,['state','receipts'])||!object(g.legacy.receipts))invalid();validateLegacyPets(s,g.legacy.state,g.legacy.receipts);for(const[key,value]of Object.entries(g.legacy.receipts)){if(!key.startsWith('pet-')||s.receipts[key]!==value)invalid();requests.add(key);}}
 const replay=foundation(g.legacy),baseEssence=replay.essence,basePending={...replay.pending};let earnedEssence=0,killOperations=0,paidOperations=0,freeOperations=0;
 const experience:Record<string,number>={},bonds:Record<string,number>={};
 for(const[key,record]of Object.entries(g.defeats)){
  if(!object(record)||!keys(record,['cycle','count','boss','experience','discarded'])||!integer(record.cycle)||!integer(record.count,Number.MAX_SAFE_INTEGER,1)||typeof record.boss!=='boolean'||!object(record.experience)||!integer(record.discarded))invalid();
  const enemy=killEvidence(s,key,record.cycle),old=g.legacy?.state.defeats[key],prior=old?.cycle??-1;if(!enemy||record.boss!==!!enemy.bossId||record.cycle<=prior||record.count>record.cycle-prior)invalid();
  let sum=0;for(const[id,xp]of Object.entries(record.experience)){if(!g.roster[id]||!integer(xp))invalid();experience[id]=(experience[id]??0)+xp;sum+=xp;if(!integer(experience[id])||!integer(sum))invalid();}
  const earned=record.count*(record.boss?5:1);if(sum>record.count*(record.boss?36:12)||record.discarded>earned)invalid();earnedEssence+=earned-record.discarded;killOperations+=record.count;
 }
 for(const[source,record]of Object.entries(g.progress)){
  if(!object(record)||!keys(record,['pet','xp','essence','bond','discarded'])||!integer(record.xp)||!integer(record.essence)||!integer(record.bond,100)||!integer(record.discarded))invalid();const reward=petProgressReward(s,source);
  if(!reward||record.pet!==reward.pet||record.essence!==reward.essence||record.discarded>record.essence||record.xp>reward.xp*3||record.bond>reward.bond||record.pet!==null&&!g.roster[record.pet]||record.pet===null&&(record.xp!==0||record.bond!==0))invalid();
  if(record.pet){experience[record.pet]=(experience[record.pet]??0)+record.xp;bonds[record.pet]=(bonds[record.pet]??0)+record.bond;if(!integer(experience[record.pet]))invalid();}earnedEssence+=record.essence-record.discarded;
 }
 const prove=(request:unknown,value:object,kind:string)=>{if(typeof request!=='string')invalid();const match=new RegExp(`^pet3-${kind}:(\\d+)$`).exec(request);if(!match||!integer(Number(match[1]),s.sequence,1)||requests.has(request)||s.receipts[request]!==JSON.stringify(value))invalid();requests.add(request);return Number(match[1]);};
 let sequence=0,spentEssence=0,claimedGold=0,claimedEssence=0;
 for(const t of g.transactions){
  if(!object(t)||!keys(t,['request','action','gold','essence','xp','level','bond',...('count' in t?['count']:[]),...('catchupLevel' in t?['catchupLevel']:[])])||!validAction(t.action)||!integer(Math.abs(t.gold))||!integer(Math.abs(t.essence))||!integer(t.xp)||!integer(t.level,Number.MAX_SAFE_INTEGER,1)||!integer(t.bond,100)||t.count!==undefined&&(!integer(t.count,Math.floor(Number.MAX_SAFE_INTEGER/25),1)||!['train','claim'].includes(t.action.kind)))invalid();
  if(['deploy','rest','assign','branch'].includes(t.action.kind))invalid();const n=prove(t.request,t,t.action.kind);if(n<=sequence)invalid();sequence=n;
  const action=t.action,pet='pet' in action?replay.roster[action.pet]:undefined;
  if('pet' in action&&(!pet||!g.roster[action.pet]||t.level>petLevel(g.roster[action.pet])||t.bond>g.roster[action.pet].bond))invalid();
  let gold=0,essence=0,xp=0;
  if(action.kind==='claim'){
   if(t.gold>0||t.essence>0||t.xp!==0)invalid();claimedGold-=t.gold;claimedEssence-=t.essence;if(claimedGold>basePending.gold||claimedEssence>basePending.essence)invalid();gold=t.gold;essence=t.essence;
  }else{
   let expected:Cost;try{expected=cost(s,replay,action,{level:t.level,bond:t.bond,catchupLevel:t.catchupLevel});}catch{invalid();}
   gold=expected!.gold;essence=expected!.essence;xp=expected!.xp;
   if(action.kind==='train'){const count=t.count??1;gold*=count;essence*=count;xp*=count;if(!t.count)invalid();}
   if(action.kind==='adopt'){
    if(!integer(t.catchupLevel,Number.MAX_SAFE_INTEGER,1)||t.level!==1||t.bond!==0)invalid();const highest=Math.max(1,...Object.keys(replay.roster).map(id=>petLevel(g.roster[id])));if(t.catchupLevel>highest)invalid();
   }else if(t.catchupLevel!==undefined)invalid();
  }
  if(t.gold!==gold||t.essence!==essence||t.xp!==xp)invalid();spentEssence+=t.essence;paidOperations+=t.count??1;applyPaid(replay,action,t.xp,t.catchupLevel);
 }
 if(Object.keys(g.roster).sort().join()!==Object.keys(replay.roster).sort().join())invalid();
 let active=replay.active;
 if(g.deployment!==undefined){const d=g.deployment;if(!object(d)||!keys(d,['request','active','count'])||!integer(d.count,Number.MAX_SAFE_INTEGER,1)||d.active!==null&&!g.roster[d.active])invalid();prove(d.request,d,'deployment');freeOperations+=d.count;active=d.active;}
 for(const[id,configuration]of Object.entries(g.configurations)){
  if(!g.roster[id]||!object(configuration)||!keys(configuration,['request','slots','count'])||!Array.isArray(configuration.slots)||configuration.slots.length!==2||!integer(configuration.count,Number.MAX_SAFE_INTEGER,1))invalid();
  for(let slot=0;slot<2;slot++){const skill=configuration.slots[slot];if(skill!==null&&(!petSkill(skill)||!researchRank(s,g,skill)||petLevel(g.roster[id])<(slot?15:5)))invalid();}if(configuration.slots[0]!==null&&configuration.slots[0]===configuration.slots[1])invalid();
  prove(configuration.request,configuration,'config');freeOperations+=configuration.count;replay.roster[id].traitSlots=copy(configuration.slots);replay.roster[id].skills=traitSlots(replay.roster[id]);
 }
 for(const[id,configuration]of Object.entries(g.branches)){
  if(!g.roster[id]||!object(configuration)||!keys(configuration,['request','branch','count'])||!knownBranch(configuration.branch)||!integer(configuration.count,Number.MAX_SAFE_INTEGER,1)||replay.roster[id].signatureRank<2)invalid();prove(configuration.request,configuration,'branch');freeOperations+=configuration.count;replay.roster[id].branch=configuration.branch;
 }
 if(Object.keys(g.research).some(id=>!petSkill(id)||!integer(g.research[id as PetSkillId],5,2))||Object.keys(g.research).sort().join()!==Object.keys(replay.research).sort().join()||Object.keys(g.research).some(id=>g.research[id as PetSkillId]!==replay.research[id as PetSkillId]))invalid();
 for(const[id,pet]of Object.entries(g.roster)){
  if(!object(pet)||!keys(pet,['id','species','quality','xp','bond','evolution','skills','signatureRank','branch','traitSlots','catchupLevel'])||pet.id!==id||pet.species!==id||!petSpecies(id)||!PET_QUALITIES.includes(pet.quality)||!integer(pet.xp)||!integer(pet.bond,100)||!integer(pet.signatureRank,3,1)||pet.evolution!==pet.signatureRank-1||pet.branch!==null&&!knownBranch(pet.branch)||pet.signatureRank===1&&pet.branch!==null||pet.signatureRank>1&&pet.branch===null||!integer(pet.catchupLevel,Number.MAX_SAFE_INTEGER,1)||!Array.isArray(pet.traitSlots)||pet.traitSlots.length!==2||!Array.isArray(pet.skills))invalid();
  const expected=replay.roster[id];if(pet.xp!==expected.xp+(experience[id]??0)||pet.bond!==Math.min(100,expected.bond+(bonds[id]??0))||pet.quality!==expected.quality||pet.signatureRank!==expected.signatureRank||pet.branch!==expected.branch||pet.catchupLevel!==expected.catchupLevel||JSON.stringify(pet.traitSlots)!==JSON.stringify(expected.traitSlots)||JSON.stringify(pet.skills)!==JSON.stringify(expected.skills))invalid();
 }
 const allKeys=Object.keys(s.receipts).filter(key=>key.startsWith('pet-')||key.startsWith('pet3-'));
 if(allKeys.length!==requests.size||allKeys.some(key=>!requests.has(key))||g.active!==active||g.essence!==baseEssence+earnedEssence-spentEssence||g.pending.gold!==basePending.gold-claimedGold||g.pending.essence!==basePending.essence-claimedEssence||g.revision!==killOperations+Object.keys(g.progress).length+paidOperations+freeOperations)invalid();
}
