import {HUNT_EXPERIENCE_POLICY as POLICY,dailyCombatExperienceCap} from '../data/HuntingExperience';
import {BUILD_PROFILE} from '../../../shared/BuildProfile';

type Receipts=Record<string,string|number|boolean>;
const DAY='hunt:daily:day',EARNED='hunt:daily:earned',CARRY='hunt:daily:carry';
const BDAY='battle:daily:day',LEVEL='battle:daily:level',TOTAL='battle:daily:earned';
const calendarDay=(now:number)=>Math.max(0,Math.min(1000000,Math.floor((now+POLICY.utcOffsetHours*3600000)/86400000)));
export function huntingExperienceView(receipts:Receipts,now:number,level=1){
 const stored=Math.max(Number(receipts[BDAY]??0),Number(receipts[DAY]??0));
 const day=Math.max(stored,Number.isFinite(now)?calendarDay(now):stored);
 const startingLevel=Number(receipts[BDAY])===day?Number(receipts[LEVEL]):Math.max(1,Math.min(40,Math.floor(level)));
 const cap=dailyCombatExperienceCap(startingLevel),oldIdle=Number(receipts[DAY])===day?Number(receipts[EARNED]??0):0;
 const actualEarned=Number(receipts[BDAY])===day?Number(receipts[TOTAL]??0):oldIdle;
 const earned=Math.min(cap,actualEarned),idleEarned=Math.min(POLICY.dailyCap,oldIdle);
 const remaining=Math.max(0,cap-actualEarned),idleRemaining=Math.max(0,POLICY.dailyCap-oldIdle);
 const rate=!remaining||!idleRemaining?0:POLICY.rates[Math.min(POLICY.rates.length-1,Math.floor(idleEarned/POLICY.dailyCap*POLICY.rates.length))];
 const unlimited=BUILD_PROFILE.unlimitedDailyExperience&&level<40;
 const devMax=BUILD_PROFILE.unlimitedDailyExperience&&level>=40;
 return {day,startingLevel,earned,actualEarned,cap:unlimited?-1:devMax?0:cap,remaining:unlimited?Infinity:devMax?0:remaining,rate:unlimited?100:devMax?0:rate,idleEarned,idleCap:unlimited?-1:POLICY.dailyCap,idleRemaining:unlimited?Infinity:devMax?0:idleRemaining};
}
/** Freeze before the first playing step or any XP, including exempt quest XP. */
export function ensureDailyExperience(receipts:Receipts,now:number,level:number){
 const view=huntingExperienceView(receipts,now,level);let changed=false;
 if(receipts[BDAY]!==view.day||receipts[LEVEL]===undefined){receipts[BDAY]=view.day;receipts[LEVEL]=view.startingLevel;receipts[TOTAL]=view.actualEarned;changed=true;}
 if(receipts[DAY]!==view.day){receipts[DAY]=view.day;receipts[EARNED]=0;receipts[CARRY]=0;changed=true;}
 return changed;
}
export function takeCombatExperience(receipts:Receipts,now:number,level:number,base:number,levelRemaining:number,idle=false){
 ensureDailyExperience(receipts,now,level);const view=huntingExperienceView(receipts,now,level);
 // Dev never spends the normal shared/idle budgets or applies their diminishing rate.
 if(BUILD_PROFILE.unlimitedDailyExperience)return Math.max(0,Math.min(Math.floor(base),Math.floor(levelRemaining)));
 const scaled=idle?Math.max(0,Math.floor(base))*view.rate+Number(receipts[CARRY]??0):Math.max(0,Math.floor(base))*100;
 const amount=Math.max(0,Math.min(Math.floor(scaled/100),view.remaining,idle?view.idleRemaining:Infinity,Math.floor(levelRemaining)));
 receipts[TOTAL]=view.actualEarned+amount;
 if(idle){receipts[EARNED]=Number(receipts[EARNED]??0)+amount;receipts[CARRY]=amount>=view.remaining||amount>=view.idleRemaining||amount>=levelRemaining?0:scaled%100;}
 return amount;
}
export function takeHuntingExperience(receipts:Receipts,now:number,base:number,levelRemaining:number){return takeCombatExperience(receipts,now,Number(receipts[LEVEL]??1),base,levelRemaining,true);}
export function validateHuntingExperience(receipts:Receipts){
 const valid=(key:string,max:number,min=0)=>typeof receipts[key]==='number'&&Number.isInteger(receipts[key])&&Number(receipts[key])>=min&&Number(receipts[key])<=max;
 const idle=[DAY,EARNED,CARRY],present=idle.filter(k=>receipts[k]!==undefined);
 if(present.length&&(present.length!==3||!valid(DAY,1000000)||!valid(EARNED,5000)||!valid(CARRY,99)||Number(receipts[EARNED])>=5000&&receipts[CARRY]!==0))throw new Error('无效的每日挂机经验记录');
 const battle=[BDAY,LEVEL,TOTAL],count=battle.filter(k=>receipts[k]!==undefined).length;
 if(count&&(count!==3||!valid(BDAY,1000000)||!valid(LEVEL,40,1)||!valid(TOTAL,Math.max(5000,dailyCombatExperienceCap(Number(receipts[LEVEL]))))||!present.length||Number(receipts[DAY])!==Number(receipts[BDAY])||Number(receipts[TOTAL])<Number(receipts[EARNED])))throw new Error('无效的每日战斗经验记录');
}
