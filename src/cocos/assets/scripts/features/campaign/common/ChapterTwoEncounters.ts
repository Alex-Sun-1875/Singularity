import type {GameState} from '../../../core/GameSession';
import {CHAPTER_TWO_ENCOUNTERS,CHAPTER_TWO_ACTIONS,RIDGE_FIXED_IDS,RIDGE_ALARM_IDS,OATH_INITIAL_IDS,OATH_FIXED_IDS,OATH_SEQUENCE,chapterTwoAction,chapterTwoEventId,type ChapterTwoActionId,type ChapterTwoEncounterId} from '../data/ChapterTwoEncounters';
import {encounterText} from '../locales/ChapterTwoEncounterText';

const key=(id:ChapterTwoEncounterId,part:string)=>`chapter2:${id}:${part}`;
const retiredKey=(id:string)=>'chapter2:retired:'+id;
const encounter=(query:string)=>CHAPTER_TWO_ENCOUNTERS.find(def=>def.id===query||def.area===query||def.taskId===query);
const resolved=(s:GameState,id:ChapterTwoEncounterId)=>s.receipts[key(id,'resolved')];
const choice=(s:GameState)=>s.receipts[key('quarry-rescue','choice')];
const tx=(name:string,values:Record<string,string|number>={})=>encounterText(name,values);
export const chapterTwoEncounterResolved=(s:GameState,query:string)=>{const def=encounter(query);return !!def&&typeof resolved(s,def.id)==='string';};
export const chapterTwoEncounterMethod=(s:GameState,query:string)=>{const def=encounter(query);return def?resolved(s,def.id):undefined;};
export function chapterTwoEnemyRetired(s:GameState,id:string):boolean {
 if(s.receipts[retiredKey(id)]!==true)return false;
 if((RIDGE_FIXED_IDS as readonly string[]).includes(id))return resolved(s,'ridge-post')==='parley'||s.receipts[key('ridge-post','alarm')]===true&&(RIDGE_ALARM_IDS as readonly string[]).includes(id);
 return OATH_FIXED_IDS.includes(id)&&resolved(s,'oath-array')==='mechanism';
}
export const chapterTwoBattleStopped=(s:GameState,area:string)=>area==='U1-06'&&resolved(s,'oath-array')==='mechanism';
export function chapterTwoActionAvailability(s:GameState,id:string):{available:boolean;completed:boolean;reason:string}{
 const action=chapterTwoAction(id),no=(reason:string,completed=false)=>({available:false,completed,reason:tx(reason)});
 if(!action)return no('reason.unavailable');if(chapterTwoEncounterResolved(s,action.encounter))return no('reason.resolved',true);
 if(id==='quarry-survey'&&s.receipts[key('quarry-rescue','survey')])return no('reason.resolved',true);
 if((id==='quarry-witness'||id==='quarry-ledger')&&!s.receipts[key('quarry-rescue','survey')])return no('reason.quarrySurvey');
 if(id==='ridge-parley'&&choice(s)!=='witness')return no('reason.witness');
 if(id==='ridge-alarm'){if(choice(s)!=='ledger')return no('reason.ledger');if(s.receipts[key('ridge-post','alarm')])return no('reason.alarmDone',true);}
 if((id==='ridge-battle'||id==='oath-battle')&&s.receipts[key(action.encounter,'battle-started')])return no('event.battleStarted');
 if(id==='oath-read'&&s.receipts[key('oath-array','read')])return no('reason.resolved',true);
 if(OATH_SEQUENCE.includes(id as ChapterTwoActionId)&&!s.receipts[key('oath-array','read')])return no('reason.oathRead');
 return {available:true,completed:false,reason:tx('reason.ready')};
}
export interface ChapterTwoEncounterRoute {id:string;label:string;method:string;methodLabel:string;available:boolean;completed:boolean;reason:string;eventId:string;area:string;point:{x:number;z:number}}
export interface ChapterTwoEncounterView {id:ChapterTwoEncounterId;area:string;taskId:string;title:string;summary:string;resolved:boolean;combatStarted:boolean;method?:string;outcome:string;clues:{id:string;label:string;known:boolean}[];routes:ChapterTwoEncounterRoute[]}
export function chapterTwoEncounterView(s:GameState,query:string):ChapterTwoEncounterView|undefined {
 const def=encounter(query);if(!def)return;
 const method=resolved(s,def.id),done=typeof method==='string',outcome=def.id==='quarry-rescue'&&done?(choice(s)==='witness'?'rescueWitness':'rescueLedger'):done?method:def.id==='oath-array'?'oathProgress':'pending';
 const clues=[{id:'quarrySurvey',known:!!s.receipts[key('quarry-rescue','survey')]},{id:'witness',known:choice(s)==='witness'},{id:'ledger',known:choice(s)==='ledger'},{id:'oathRead',known:!!s.receipts[key('oath-array','read')]}];
 return {id:def.id,area:def.area,taskId:def.taskId,title:tx(`encounter.${def.text}.title`),summary:tx(`encounter.${def.text}.summary`),resolved:done,combatStarted:s.receipts[key(def.id,'battle-started')]===true,method:done?String(method):undefined,outcome:tx('outcome.'+outcome,{count:Number(s.receipts[key('oath-array','progress')]??0)}),clues:clues.filter(clue=>def.id==='quarry-rescue'?clue.id!=='oathRead':def.id==='ridge-post'?['witness','ledger'].includes(clue.id):clue.id==='oathRead').map(clue=>({...clue,label:tx('clue.'+clue.id)})),routes:CHAPTER_TWO_ACTIONS.filter(action=>action.encounter===def.id).map(action=>({id:action.id,label:tx(`action.${action.id}.label`),method:action.method,methodLabel:tx('method.'+action.method),...chapterTwoActionAvailability(s,action.id),eventId:chapterTwoEventId(action.id),area:action.area,point:{...action.point}}))};
}
export function chapterTwoChoiceHint(dialogueId:string,choiceId:string):string|undefined {const id=dialogueId.startsWith('chapter2:')?dialogueId.slice(9):'';return choiceId==='confirm'&&chapterTwoAction(id)?tx(`action.${id}.hint`):undefined;}
interface Host {state():GameState;withdraw(ids:readonly string[]):void;battleReady():boolean;changed():void;emit(type:string,text:string):void}
export class ChapterTwoEncounters {
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 private notify(text:string,values:Record<string,string|number>={}){this.host.changed();this.host.emit('chapter_two_encounter',tx(text,values));}
 private finish(id:ChapterTwoEncounterId,method:string,retire:readonly string[]=[]) {
  const s=this.s;if(chapterTwoEncounterResolved(s,id))return false;s.receipts[key(id,'resolved')]=method;
  const withdraw=retire.filter(id=>{const enemy=s.enemies.find(enemy=>enemy.id===id);return !enemy||enemy.hp>0;});for(const id of withdraw)s.receipts[retiredKey(id)]=true;
  if(withdraw.length)this.host.withdraw(withdraw);return true;
 }
 perform(id:string):boolean {
  const action=chapterTwoAction(id),s=this.s;if(!action||s.area!==action.area||s.status==='dead'||!chapterTwoActionAvailability(s,id).available)return false;
  if(id==='quarry-survey'){s.receipts[key('quarry-rescue','survey')]=true;this.notify('event.survey');return true;}
  if(id==='quarry-witness'||id==='quarry-ledger'){const version=id==='quarry-witness'?'witness':'ledger';s.receipts[key('quarry-rescue','choice')]=version;this.finish('quarry-rescue','rescue');this.notify('event.'+version);return true;}
  if(id==='ridge-parley'){this.finish('ridge-post','parley',RIDGE_FIXED_IDS);this.notify('event.parley');return true;}
  if(id==='ridge-alarm'){s.receipts[key('ridge-post','alarm')]=true;const ids=RIDGE_ALARM_IDS.filter(id=>s.enemies.some(enemy=>enemy.id===id&&enemy.hp>0));for(const id of ids)s.receipts[retiredKey(id)]=true;this.host.withdraw(ids);this.notify('event.alarm');return true;}
  if(id==='ridge-battle'||id==='oath-battle'){s.receipts[key(action.encounter,'battle-started')]=true;this.notify('event.battleStarted');return true;}
  if(id==='oath-read'){s.receipts[key('oath-array','read')]=true;this.notify('event.oathRead');return true;}
  const progress=Number(s.receipts[key('oath-array','progress')]??0);
  if(OATH_SEQUENCE[progress]!==id){s.receipts[key('oath-array','progress')]=0;s.receipts[key('oath-array','mistakes')]=Math.min(1e6,Number(s.receipts[key('oath-array','mistakes')]??0)+1);this.notify('event.oathWrong');return true;}
  s.receipts[key('oath-array','progress')]=progress+1;
  if(progress+1===OATH_SEQUENCE.length){s.flags.u106_array_stopped=true;this.finish('oath-array','mechanism',OATH_FIXED_IDS);this.notify('event.oathDone');}else this.notify('event.oathStep',{count:progress+1});return true;
 }
 observeCombat():void {
  const s=this.s,def=encounter(s.area);if(!def||def.id==='quarry-rescue'||chapterTwoEncounterResolved(s,def.id))return;
  const ids=def.id==='ridge-post'?RIDGE_FIXED_IDS:OATH_FIXED_IDS;
  const killed=(id:string)=>s.enemies.some(enemy=>enemy.id===id&&enemy.hp<=0)&&s.receipts[`kill:${s.area}:${id}`]===true;
  if(!ids.every(id=>killed(id)||chapterTwoEnemyRetired(s,id))||!ids.some(killed)||!this.host.battleReady())return;
  this.finish(def.id,'battle');this.notify('event.combatDone');
 }
}
/** Validate the bounded encounter receipts and their physical consequences. */
export function validateChapterTwoEncounters(s:GameState):void {
 const r=s.receipts,fail=():never=>{throw new Error('无效的第二章遭遇进度');};
 const booleans=[key('quarry-rescue','survey'),key('ridge-post','alarm'),key('ridge-post','battle-started'),key('oath-array','read'),key('oath-array','battle-started')];
 const allowed=new Set([...booleans,key('quarry-rescue','choice'),key('quarry-rescue','resolved'),key('ridge-post','resolved'),key('oath-array','resolved'),key('oath-array','progress'),key('oath-array','mistakes'),...RIDGE_FIXED_IDS.map(retiredKey),...OATH_FIXED_IDS.map(retiredKey)]);
 for(const name of Object.keys(r))if(name.startsWith('chapter2:')&&!allowed.has(name))return fail();for(const name of booleans)if(r[name]!==undefined&&r[name]!==true)return fail();
 const q=resolved(s,'quarry-rescue'),c=choice(s),ridge=resolved(s,'ridge-post'),oath=resolved(s,'oath-array'),progress=r[key('oath-array','progress')],mistakes=r[key('oath-array','mistakes')];
 // The task's genuine first victory survives an optional, explicitly started
 // Boss rematch. Ordinary guards and reinforcements have no such exception.
 const defeated=(area:string,id:string)=>{const enemies=s.area===area?s.enemies:s.encounters[area]??[],enemy=enemies.find(enemy=>enemy.id===id);if(!enemy||r[`kill:${area}:${id}`]!==true)return false;if(enemy.hp<=0)return true;const source=`boss:v3:${area}:${id}`,life=r[source+':life'],draw=s.dropRolls[source],draws=r['boss:v3:draws'];return area==='U1-06'&&(OATH_INITIAL_IDS as readonly string[]).includes(id)&&enemy.bossId==='ELITE_06'&&Number.isInteger(enemy.respawnCount)&&enemy.respawnCount!>0&&typeof life==='number'&&Number.isInteger(life)&&life>=0&&life<enemy.respawnCount!&&s.flags['boss_defeated:ELITE_06']===true&&!!draw&&typeof r[source+':meta']==='string'&&r['roll:'+source]===draw.result&&typeof draws==='number'&&draws>0;};
 if(q!==undefined&&(q!=='rescue'||!r[key('quarry-rescue','survey')]||!['witness','ledger'].includes(String(c)))||c!==undefined&&(!q||!['witness','ledger'].includes(String(c))))return fail();
 if(ridge!==undefined&&!['parley','battle'].includes(String(ridge))||ridge==='parley'&&c!=='witness'||r[key('ridge-post','alarm')]&&c!=='ledger')return fail();
 if(oath!==undefined&&!['mechanism','battle'].includes(String(oath))||progress!==undefined&&(!Number.isInteger(progress)||Number(progress)<0||Number(progress)>3||!r[key('oath-array','read')])||mistakes!==undefined&&(!Number.isInteger(mistakes)||Number(mistakes)<0||Number(mistakes)>1e6||!r[key('oath-array','read')]))return fail();
 if(oath==='mechanism'&&(progress!==3||!s.flags.u106_array_stopped)||progress===3&&oath!=='mechanism')return fail();
 for(const id of [...RIDGE_FIXED_IDS,...OATH_FIXED_IDS])if(r[retiredKey(id)]!==undefined){if(r[retiredKey(id)]!==true||!chapterTwoEnemyRetired(s,id))return fail();const area=(RIDGE_FIXED_IDS as readonly string[]).includes(id)?'H07':'U1-06',enemies=s.area===area?s.enemies:s.encounters[area]??[];if(enemies.some(enemy=>enemy.id===id)||r[`kill:${area}:${id}`])return fail();}
 for(const def of CHAPTER_TWO_ENCOUNTERS){const method=resolved(s,def.id),hasProgress=Object.keys(r).some(name=>name.startsWith(`chapter2:${def.id}:`));if(hasProgress&&!s.flags[`visited:${def.area}`])return fail();if(!method||def.id==='quarry-rescue')continue;const ids=def.id==='ridge-post'?RIDGE_FIXED_IDS:OATH_FIXED_IDS;if(!ids.every(id=>chapterTwoEnemyRetired(s,id)||defeated(def.area,id)))return fail();if(method==='battle'&&(!ids.some(id=>r[`kill:${def.area}:${id}`]===true)||def.id==='oath-array'&&!s.flags['campaign:battle:oath-line:complete']))return fail();}
 if(s.flags['campaign:battle:oath-line:complete']&&(!OATH_FIXED_IDS.every(id=>defeated('U1-06',id))||r['campaign:wave:oath-line:0']!==true))return fail();
}
