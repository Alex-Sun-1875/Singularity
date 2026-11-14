import {drawCheckRoll,skillModifiers,type CheckContext} from '../../progression/common/SkillChecks';
import {SKILL_CHECKS,INSPIRATION_SOURCES} from '../../progression/data/SkillChecks';
import {validateEquipmentDice} from '../../equipment/common/EquipmentDice';
const object=(v:unknown):v is Record<string,any>=>!!v&&typeof v==='object'&&!Array.isArray(v)&&Object.getPrototypeOf(v)===Object.prototype;
const exact=(v:Record<string,any>,keys:string[])=>Object.keys(v).length===keys.length&&keys.every(k=>k in v);
const helpLabels:Record<string,string[]>={
 'mira-motive':['已核对的求援抄件'],'mira-terms':['已核对的求援抄件'],'inn-lockbox':['洛恩的工具指引'],
 'grave-record':['信使副本的日期'],'quarry-runes':['洛恩的工具指引'],'undercity-disarm':['原信中的退路提示'],
};
/** Validate saved outcomes against the deterministic draw, not trusted totals. */
export function validateDiceSnapshot(value:unknown,seed:number,flags:Record<string,boolean>,receipts:Record<string,unknown>,area?:string):void {
 const fail=():never=>{throw new Error('无效的 D20 检定存档');};
 if(!object(value)||!exact(value,['inspiration','earned','records','active','gear'])||!Number.isInteger(value.inspiration)||value.inspiration<0||value.inspiration>4||!Array.isArray(value.earned)||value.earned.length>INSPIRATION_SOURCES.length||new Set(value.earned).size!==value.earned.length||value.earned.some((id:any)=>!INSPIRATION_SOURCES.includes(id))||!object(value.records)||Object.keys(value.records).length>Object.keys(SKILL_CHECKS).length||!object(flags)||!object(receipts))return fail();
 validateEquipmentDice(value.gear,seed,receipts,value.active,area);
 const context=(v:unknown,id:string):v is CheckContext=>object(v)&&exact(v,['mode','modifiers','helpDie','helpLabel'])&&['normal','advantage','disadvantage'].includes(v.mode)&&JSON.stringify(v.modifiers)===JSON.stringify(skillModifiers(SKILL_CHECKS[id].skill))&&typeof v.helpDie==='boolean'&&(v.helpLabel===null||helpLabels[id].includes(v.helpLabel))&&(!v.helpDie||v.helpLabel!==null);
 let spent=0;
 for(const [id,r]of Object.entries(value.records)){
  const def=SKILL_CHECKS[id];if(!def||!object(r)||!exact(r,['area','sourceId','context','rolls','committed'])||r.area!==def.area||r.sourceId!==def.sourceId||!context(r.context,id)||!Array.isArray(r.rolls)||r.rolls.length<1||r.rolls.length>5||typeof r.committed!=='boolean')return fail();
  for(let i=0;i<r.rolls.length;i++){
   const roll=r.rolls[i],expected=drawCheckRoll(seed,id,i+1,def.dc,r.context);if(!object(roll)||!exact(roll,Object.keys(expected))||Object.entries(expected).some(([key,v])=>JSON.stringify(roll[key])!==JSON.stringify(v))||i>0&&r.rolls[i-1].success)return fail();
  }
  const last=r.rolls[r.rolls.length-1];spent+=r.rolls.length-1;
  if(r.committed?flags[`check:${id}:${last.success?'passed':'failed'}`]!==true:flags[`check:${id}:passed`]||flags[`check:${id}:failed`])return fail();
  if(flags[`check:${id}:passed`]&&flags[`check:${id}:failed`])return fail();
 }
 if(value.inspiration>Math.min(4,2+value.earned.length-spent))return fail();
 for(const id of Object.keys(SKILL_CHECKS))if((flags[`check:${id}:passed`]||flags[`check:${id}:failed`])&&!value.records[id]?.committed)return fail();
 for(const source of value.earned){
  if(receipts['inspiration:'+source]!==true)return fail();
  const flag=({'read-letter':'read_letter','ask-truth':'truth_asked','release-workers':'workers_released',captain:'captain_defeated'} as Record<string,string>)[source];
  if(flag&&!flags[flag]||source.startsWith('check:')&&!flags[source+':passed'])return fail();
 }
 if(value.active!==null&&!value.active?.id?.startsWith('gear:')){const a=value.active;if(!object(a)||!exact(a,['id','area','sourceId','context'])||!SKILL_CHECKS[a.id]||a.area!==SKILL_CHECKS[a.id].area||a.sourceId!==SKILL_CHECKS[a.id].sourceId||area&&area!==a.area||!context(a.context,a.id))return fail();const r=value.records[a.id];if(r&&(r.committed||JSON.stringify(r.context)!==JSON.stringify(a.context)))return fail();}
}
