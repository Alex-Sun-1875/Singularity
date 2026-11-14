import {PURE_SKILLS,combatSkillCatalog,type CombatSkillRank} from '../../combat/data/PureSkills';

export type Attribute='strength'|'dexterity'|'intellect'|'vitality';
export interface ProgressionState {
 version:3;xpCurve?:2;level:number;totalXp:number;attributes:Record<Attribute,number>;unspentPoints:number;
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
/** Reward amounts are deliberately independent from this cost curve. */
export const xpToNext=(level:number)=>level>=40?0:100+55*(level-1)+25*(level-1)**2;
export function cumulativeXp(level:number){let n=0;for(let l=1;l<level;l++)n+=xpToNext(l);return n;}
export function levelForXp(total:number){let level=1;while(level<40&&total>=cumulativeXp(level+1))level++;return level;}
const previousCost=(level:number)=>100+35*(level-1)+5*(level-1)**2;
function previousCumulative(level:number){let n=0;for(let l=1;l<level;l++)n+=previousCost(l);return n;}
function previousLevel(total:number){let level=1;while(level<40&&total>=previousCumulative(level+1))level++;return level;}
/** Keep the earned level, fractional progress and all investments when loading V3. */
export function updateExperienceCurve(p:ProgressionState):boolean {
 if(p.xpCurve===2)return false;
 const fraction=p.level<40?(p.totalXp-previousCumulative(p.level))/previousCost(p.level):0;
 const total=Math.max(p.totalXp,cumulativeXp(p.level)+Math.floor(fraction*xpToNext(p.level)));
 if(total>p.totalXp)p.xpReceipts['balance:xp-curve:2']=(p.xpReceipts['balance:xp-curve:2']??0)+total-p.totalXp;
 p.totalXp=total;p.xpCurve=2;return true;
}
export const skillPower=(p:ProgressionState)=>24+1.5*(p.level-1);
export const baseMaxHp=(p:ProgressionState)=>120+5*(p.level-1)+4*(p.attributes.vitality-10);
export const totalSkillPoints=(p:ProgressionState)=>p.level-1+(p.secondChapter?2:0);
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
 const p:ProgressionState={version:3,xpCurve:2,level:1,totalXp:0,attributes:{strength:10,dexterity:10,intellect:10,vitality:10},unspentPoints:0,learned:{},xpReceipts:{},ultimateGiftClaimed:false,skillPoints:0,secondChapter:false};
 for(const id of Object.keys(PURE_SKILLS))p.learned[id]=0;unlockSkills(p);return p;
}
export function progressionView(p:ProgressionState):ProgressionView{return {level:p.level,totalXp:p.totalXp,xp:p.totalXp-cumulativeXp(p.level),xpToNext:xpToNext(p.level),baseSkillPower:skillPower(p),attributes:{...p.attributes},unspentPoints:p.unspentPoints,maxLevel:40,skillPoints:p.skillPoints??0,totalSkillPoints:totalSkillPoints(p)};}
/** One-shot events are deduplicated; hunting aggregates its durable XP receipt. */
export function awardXp(p:ProgressionState,source:string,amount:number,repeat=false):number {
 if(!source||source.length>180||!Number.isInteger(amount)||amount<=0||amount>10000000||!repeat&&p.xpReceipts[source]!==undefined)return 0;
 updateExperienceCurve(p);
 if(p.totalXp+amount>10000000)return 0;
 const old=p.level;p.xpReceipts[source]=(p.xpReceipts[source]??0)+amount;p.totalXp+=amount;p.level=levelForXp(p.totalXp);p.unspentPoints+=(p.level-old)*3;p.skillPoints=(p.skillPoints??0)+p.level-old;unlockSkills(p);return p.level-old;
}
export function skillPlanRemaining(p:ProgressionState,learned:Record<string,number>,legacy:boolean|number=false):number|null {
 const catalog=combatSkillCatalog(typeof legacy==='number'?legacy:legacy?2:4),ids=Object.keys(catalog);if(!learned||Object.keys(learned).length!==ids.length)return null;
 let spent=0;for(const id of ids){const rank=learned[id],unlocked=p.level>=catalog[id].unlockLevel||p.secondChapter;if(!Number.isInteger(rank)||rank<0||rank>5||unlocked!==(rank>0))return null;spent+=skillRankSpent(rank);}
 const remaining=totalSkillPoints(p)-spent;return remaining>=0?remaining:null;
}
export function validateProgression(value:unknown,legacy:boolean|number=false):asserts value is ProgressionState {
 const p=value as ProgressionState,fail=()=>{throw new Error('无效的角色成长存档');};
 if(!p||p.version!==3||p.xpCurve!==undefined&&p.xpCurve!==2||!Number.isInteger(p.totalXp)||p.totalXp<0||p.totalXp>10000000||p.level!==(p.xpCurve===2?levelForXp(p.totalXp):previousLevel(p.totalXp))||!p.attributes||!p.xpReceipts||!p.learned||Array.isArray(p.learned)||typeof p.ultimateGiftClaimed!=='boolean')return fail();
 let spent=0;for(const key of ATTRIBUTES){const v=p.attributes[key];if(!Number.isInteger(v)||v<10||v>80)return fail();spent+=v-10;}
 if(Object.keys(p.attributes).length!==4||!Number.isInteger(p.unspentPoints)||p.unspentPoints<0||spent+p.unspentPoints!==3*(p.level-1))return fail();
 const entries=Object.entries(p.xpReceipts);if(entries.length>20000||entries.some(([k,v])=>!k||k.length>180||!Number.isInteger(v)||v<1||v>10000000)||entries.reduce((sum,[,v])=>sum+v,0)!==p.totalXp)return fail();
 if(typeof p.secondChapter!=='boolean'||p.level>=11&&!p.secondChapter||!Number.isInteger(p.skillPoints)||p.skillPoints!==skillPlanRemaining(p,p.learned,legacy)||!p.secondChapter&&p.ultimateGiftClaimed)return fail();
}
