export type DiceMode='normal'|'advantage'|'disadvantage';
export type SkillId='insight'|'persuasion'|'investigation'|'sleight'|'athletics';
export interface CheckModifier {label:string;value:number}
export interface CheckContext {mode:DiceMode;modifiers:CheckModifier[];helpDie:boolean;helpLabel:string|null}
export interface DiceRoll {attempt:number;faces:number[];kept:number;keptIndex:number;bonus:number;assist:number;total:number;success:boolean;critical:'success'|'failure'|null}
export interface CheckRecord {area:string;sourceId:string;context:CheckContext;rolls:DiceRoll[];committed:boolean}
export interface ActiveCheck {id:string;area:string;sourceId:string;context:CheckContext}
export interface DiceState {inspiration:number;earned:string[];records:Record<string,CheckRecord>;active:ActiveCheck|null;gear:import('../../equipment/common/EquipmentDice').EquipmentRollBook}
export interface DiceView {
 id:string;title:string;prompt:string;skillLabel:string;abilityLabel:string;dc:number;mode:DiceMode;modifiers:CheckModifier[];
 help:{label:string;enabled:boolean}|null;roll:DiceRoll|null;attempt:number;inspiration:number;canReroll:boolean;canCancel:boolean;
 successText:string;failureText:string;chance:number;
 gear?:import('../../equipment/common/EquipmentDice').EquipmentDiceView;
}
export const ACTION_NAMES:Record<SkillId,string>={insight:'察迹',persuasion:'对证',investigation:'寻痕',sleight:'拆械',athletics:'破障'};
export const SKILLS:Record<SkillId,{name:string;ability:string;modifier:number;proficiency:number}>={
 insight:{name:'洞悉',ability:'感知',modifier:1,proficiency:0},
 persuasion:{name:'游说',ability:'魅力',modifier:2,proficiency:2},
 investigation:{name:'调查',ability:'智力',modifier:1,proficiency:2},
 sleight:{name:'巧手',ability:'敏捷',modifier:2,proficiency:2},
 athletics:{name:'运动',ability:'力量',modifier:2,proficiency:0},
};
export const freshDiceState=():DiceState=>({inspiration:2,earned:[],records:{},active:null,gear:{}});
export function skillModifiers(skill:SkillId):CheckModifier[]{const s=SKILLS[skill];return[{label:s.ability,value:s.modifier},...(s.proficiency?[{label:'熟练',value:s.proficiency}]:[])];}
export function rollMode(advantage:boolean,disadvantage:boolean):DiceMode{return advantage===disadvantage?'normal':advantage?'advantage':'disadvantage';}
function validContext(context:CheckContext){return !!context&&['normal','advantage','disadvantage'].includes(context.mode)&&Array.isArray(context.modifiers)&&context.modifiers.length<=8&&context.modifiers.every(m=>typeof m.label==='string'&&m.label.length<80&&Number.isInteger(m.value)&&Math.abs(m.value)<=20)&&typeof context.helpDie==='boolean';}
export function resolveCheckRoll(faces:number[],dc:number,context:CheckContext,attempt=1,assist=0):DiceRoll{
 if(!validContext(context)||!Number.isInteger(dc)||dc<1||dc>60||!Number.isInteger(attempt)||attempt<1||!Array.isArray(faces)||faces.length!==(context.mode==='normal'?1:2)||faces.some(n=>!Number.isInteger(n)||n<1||n>20)||!Number.isInteger(assist)||(context.helpDie?(assist<1||assist>4):assist!==0))throw new Error('无效的 D20 检定');
 const kept=context.mode==='disadvantage'?Math.min(...faces):Math.max(...faces),keptIndex=faces.indexOf(kept),bonus=context.modifiers.reduce((sum,m)=>sum+m.value,0),total=kept+bonus+assist;
 return {attempt,faces:[...faces],kept,keptIndex,bonus,assist,total,success:kept===20||kept!==1&&total>=dc,critical:kept===20?'success':kept===1?'failure':null};
}
function randomWord(seed:number,key:string):number{let h=(seed^0x811c9dc5)>>>0;for(let i=0;i<key.length;i++)h=Math.imul(h^key.charCodeAt(i),16777619)>>>0;h^=h>>>16;h=Math.imul(h,0x7feb352d);h^=h>>>15;h=Math.imul(h,0x846ca68b);return(h^(h>>>16))>>>0;}
export function drawCheckRoll(seed:number,id:string,attempt:number,dc:number,context:CheckContext):DiceRoll{
 if(!Number.isInteger(seed)||seed<1||!id||!Number.isInteger(attempt)||attempt<1)throw new Error('无效的检定来源');
 const face=(index:number)=>randomWord(seed,`check:${id}:${attempt}:d20:${index}`)%20+1;
 return resolveCheckRoll(context.mode==='normal'?[face(0)]:[face(0),face(1)],dc,context,attempt,context.helpDie?randomWord(seed,`check:${id}:${attempt}:d4`)%4+1:0);
}
export function checkChance(dc:number,context:CheckContext):number{
 let success=0,total=0;const assist=context.helpDie?[1,2,3,4]:[0];
 for(let a=1;a<=20;a++)for(let b=1;b<=(context.mode==='normal'?1:20);b++)for(const help of assist){if(resolveCheckRoll(context.mode==='normal'?[a]:[a,b],dc,context,1,help).success)success++;total++;}
 return success/total;
}
