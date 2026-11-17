import {PURE_SKILLS,combatSkillCatalog,type CombatSkillRank} from '../../combat/data/PureSkills';
import {COMBAT_BALANCE} from '../../combat/data/CombatBalance';
import {CAMPAIGN_MAX_LEVEL,xpToNext,cumulativeXp,attributePointBudget,skillPointBudget,combatBudgetLevel} from '../data/CampaignProgression';
export {CAMPAIGN_MAX_LEVEL,xpToNext,cumulativeXp,attributePointBudget,skillPointBudget,combatBudgetLevel} from '../data/CampaignProgression';

export type Attribute='strength'|'dexterity'|'intellect'|'vitality';
export interface ProgressionState {
 version:3;xpCurve:3;level:number;totalXp:number;attributes:Record<Attribute,number>;unspentPoints:number;
 learned:Record<string,number>;xpReceipts:Record<string,number>;ultimateGiftClaimed:boolean;
 skillPoints:number;secondChapter:boolean;
}
export interface ProgressionView {
 level:number;totalXp:number;xp:number;xpToNext:number;baseSkillPower:number;
 attributes:Record<Attribute,number>;unspentPoints:number;maxLevel:number;skillPoints:number;totalSkillPoints:number;
}
export const ATTRIBUTES:Attribute[]=['strength','dexterity','intellect','vitality'];
export const SKILL_RANK_COSTS=[0,0,1,2,3,4] as const;
export const skillRankSpent=(rank:number)=>rank*(rank-1)/2;
export function levelForXp(total:number){let level=1;while(level<CAMPAIGN_MAX_LEVEL&&total>=cumulativeXp(level+1))level++;return level;}
const MAX_TOTAL_XP=10000000;
export const skillPower=(p:ProgressionState)=>COMBAT_BALANCE.skillPowerBase+COMBAT_BALANCE.skillPowerPerLevel*(combatBudgetLevel(p.level)-1);
export const baseMaxHp=(p:ProgressionState)=>Math.round(120+5*(combatBudgetLevel(p.level)-1)+4*(p.attributes.vitality-10));
export const totalSkillPoints=(p:ProgressionState)=>skillPointBudget(p.level,p.secondChapter);
type UnlockProgress=number|Pick<ProgressionState,'level'|'secondChapter'>;
export function skillUnlocked(id:string,progress:UnlockProgress):boolean {
 const d=PURE_SKILLS[id],level=typeof progress==='number'?progress:progress.level;
 return !!d&&(level>=d.unlockLevel||typeof progress!=='number'&&!!progress.secondChapter);
}
export function allocatedSkillRank(p:ProgressionState,id:string):CombatSkillRank|undefined {
 const rank=p.learned[id]??0;
 return rank>0&&skillUnlocked(id,p)?PURE_SKILLS[id]?.ranks[rank-1]:undefined;
}
/** Refresh only free first ranks; investment is never overwritten by XP. */
export function unlockSkills(p:ProgressionState,secondChapter=p.level>=11):boolean {
 const first=secondChapter&&!p.secondChapter;
 if(first){p.secondChapter=true;p.skillPoints=(p.skillPoints??0)+2;}
 for(const id of Object.keys(PURE_SKILLS))if(skillUnlocked(id,p)&&!p.learned[id])p.learned[id]=1;
 return first;
}
export function freshProgression():ProgressionState {
 const p:ProgressionState={version:3,xpCurve:3,level:1,totalXp:0,attributes:{strength:10,dexterity:10,intellect:10,vitality:10},unspentPoints:0,learned:{},xpReceipts:{},ultimateGiftClaimed:false,skillPoints:0,secondChapter:false};
 for(const id of Object.keys(PURE_SKILLS))p.learned[id]=0;unlockSkills(p);return p;
}
export function progressionView(p:ProgressionState):ProgressionView{return {level:p.level,totalXp:p.totalXp,xp:p.totalXp-cumulativeXp(p.level),xpToNext:xpToNext(p.level),baseSkillPower:skillPower(p),attributes:{...p.attributes},unspentPoints:p.unspentPoints,maxLevel:CAMPAIGN_MAX_LEVEL,skillPoints:p.skillPoints??0,totalSkillPoints:totalSkillPoints(p)};}
/** One-shot events are deduplicated; hunting aggregates its durable XP receipt. */
export function awardXp(p:ProgressionState,source:string,amount:number,repeat=false):number {
 if(!source||source.length>180||!Number.isInteger(amount)||amount<=0||amount>MAX_TOTAL_XP||!repeat&&p.xpReceipts[source]!==undefined)return 0;
 if(p.totalXp+amount>MAX_TOTAL_XP)return 0;
 const old=p.level;p.xpReceipts[source]=(p.xpReceipts[source]??0)+amount;p.totalXp+=amount;p.level=levelForXp(p.totalXp);
 p.unspentPoints+=attributePointBudget(p.level)-attributePointBudget(old);
 p.skillPoints=(p.skillPoints??0)+skillPointBudget(p.level,p.secondChapter)-skillPointBudget(old,p.secondChapter);unlockSkills(p);return p.level-old;
}
export function skillPlanRemaining(p:ProgressionState,learned:Record<string,number>,legacy:boolean|number=false):number|null {
 const catalog=combatSkillCatalog(typeof legacy==='number'?legacy:legacy?2:5),ids=Object.keys(catalog);if(!learned||Object.keys(learned).length!==ids.length)return null;
 let spent=0;for(const id of ids){const rank=learned[id],unlocked=p.level>=catalog[id].unlockLevel||p.secondChapter;if(!Number.isInteger(rank)||rank<0||rank>5||unlocked!==(rank>0))return null;spent+=skillRankSpent(rank);}
 const remaining=totalSkillPoints(p)-spent;return remaining>=0?remaining:null;
}
export function validateProgression(value:unknown,legacy:boolean|number=false):asserts value is ProgressionState {
 const p=value as ProgressionState,fail=()=>{throw new Error('无效的角色成长存档');};
 if(!p||p.version!==3||p.xpCurve!==3||!Number.isInteger(p.totalXp)||p.totalXp<0||p.totalXp>MAX_TOTAL_XP||p.level!==levelForXp(p.totalXp)||!p.attributes||Array.isArray(p.attributes)||!p.xpReceipts||Array.isArray(p.xpReceipts)||!p.learned||Array.isArray(p.learned)||typeof p.ultimateGiftClaimed!=='boolean')return fail();
 let spent=0;for(const key of ATTRIBUTES){const v=p.attributes[key];if(!Number.isInteger(v)||v<10||v>80)return fail();spent+=v-10;}
 if(Object.keys(p.attributes).length!==4||!Number.isInteger(p.unspentPoints)||p.unspentPoints<0||spent+p.unspentPoints!==attributePointBudget(p.level))return fail();
 const entries=Object.entries(p.xpReceipts),receiptTotal=entries.reduce((sum,[,v])=>sum+v,0);
 if(entries.length>20000||entries.some(([k,v])=>!k||k.length>180||!Number.isInteger(v)||v<1||v>MAX_TOTAL_XP)||receiptTotal>MAX_TOTAL_XP)return fail();
 if(receiptTotal!==p.totalXp)return fail();
 if(typeof p.secondChapter!=='boolean'||p.level>=11&&!p.secondChapter||!Number.isInteger(p.skillPoints)||p.skillPoints!==skillPlanRemaining(p,p.learned,legacy)||!p.secondChapter&&p.ultimateGiftClaimed)return fail();
}
