import type {Hud} from '../../../app/Hud';
import type {GameSession} from '../../../core/GameSession';
import type {MenuChoice,MenuRow} from '../../../shared/ui/MenuPanel';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import type {PetAction} from '../common/PetSystem';
import {PET_SKILLS,PET_SPECIES,PET_PROMOTIONS} from '../data/Pets';
import {getArea} from '../../world/data/WorldData';
import {petUiText as t} from '../locales/PetUiText';

export const isPetMenu=(menu:string)=>menu==='pets'||menu.startsWith('pets:');
const encode=(value:unknown)=>encodeURIComponent(JSON.stringify(value));
const petMenu=(id:string)=>'pets:pet:'+encodeURIComponent(id);
const traitMenu=(id:string)=>'pets:traits:'+encodeURIComponent(id);
const signatureMenu=(id:string)=>'pets:signature:'+encodeURIComponent(id);
const previewMenu=(action:PetAction)=>'pets:quote:'+encode(action);
const actionName=(action:PetAction)=>t(('action.'+action.kind) as Parameters<typeof t>[0]);
const number=(value:number)=>String(Math.round(value*100)/100);
const cost=(q:{gold:number;essence:number;allowed:boolean;description:string})=>!q.allowed&&!q.description?t('cost.unavailable'):q.gold||q.essence?t('cost',{gold:q.gold,essence:q.essence}):t('cost.free');
const BONUS_STATS=['damagePercent','maxHpPercent','damageReductionPercent','healingReceivedPercent','resourceRegenPercent'] as const;
const bonusDescription=(bonuses:Record<typeof BONUS_STATS[number],number>)=>BONUS_STATS.filter(stat=>bonuses[stat]>0).map(stat=>t(('bonus.'+stat) as Parameters<typeof t>[0],{value:number(bonuses[stat])})).join('\n');
export const petQualityTone=(quality:string)=>qualityFeedbackRole(quality==='神兽'?'神器':quality==='珍兽'?'史诗':'普通');
const categoryName=(value:string)=>({explore:'探索',exploration:'探索',rescue:'救助',battle:'战斗',combat:'战斗',mechanism:'机关',puzzle:'机关',escort:'护送',trial:'试炼',habitat:'栖地调查',guard:'守护',protection:'守护',adaptability:'应变',cooperation:'协作'} as Record<string,string>)[value]??'同行';
function readAction(encoded:string):PetAction|undefined {
 try{
  const a:unknown=JSON.parse(decodeURIComponent(encoded));if(!a||typeof a!=='object'||Array.isArray(a))return;
  const v=a as Record<string,unknown>,keys=Object.keys(v).sort().join(','),pet=typeof v.pet==='string'&&PET_SPECIES.some(d=>d.id===v.pet),skill=PET_SKILLS.some(d=>d.id===v.skill),branch=v.branch==='A'||v.branch==='B';
  if(v.kind==='adopt'&&keys==='kind,species'&&PET_SPECIES.some(d=>d.id===v.species))return v as unknown as PetAction;
  if(v.kind==='research'&&keys==='kind,skill'&&skill)return v as unknown as PetAction;
  if(v.kind==='assign'&&keys==='kind,pet,skill,slot'&&pet&&(v.slot===0||v.slot===1)&&(v.skill===null||skill))return v as unknown as PetAction;
  if(v.kind==='study'&&pet&&(keys==='kind,pet'||keys==='branch,kind,pet'&&branch))return v as unknown as PetAction;
  if(v.kind==='branch'&&keys==='branch,kind,pet'&&pet&&branch)return v as unknown as PetAction;
  if(['deploy','rest','train','bond','promote'].includes(String(v.kind))&&keys==='kind,pet'&&pet)return v as unknown as PetAction;
  if(v.kind==='claim'&&keys==='kind')return v as unknown as PetAction;
 }catch{/* Invalid routes never create requests. */}return;
}
export function petCommitRequest(command:string):{action:PetAction;token:string}|undefined {
 if(!command.startsWith('pet-commit:'))return;const parts=command.slice(11).split(':');if(parts.length!==2)return;
 const action=readAction(parts[0]);if(!action)return;try{return {action,token:decodeURIComponent(parts[1])};}catch{return;}
}
export function petActionReturnMenu(action:PetAction):string {
 if(action.kind==='adopt')return 'pets:catalog:'+action.species;
 if(action.kind==='research')return 'pets:research:'+action.skill;
 if(action.kind==='assign')return traitMenu(action.pet);
 if(action.kind==='study'||action.kind==='branch')return signatureMenu(action.pet);
 if(action.kind==='claim')return 'pets:journal';
 return petMenu(action.pet);
}
/** All displayed choices come from durable state and quoted operations. */
export function renderPetPanel(hud:Hud,game:GameSession,menu:string):boolean {
 if(!isPetMenu(menu))return false;const v=game.pets.view();if(!v.enabled){hud.clearModal();return true;}
 const journeys=game.petJourneys.view(),back:MenuChoice={back:true,label:t('action.back'),action:'pets'};
 const show=(title:string,body:string,rows:MenuRow[],footer:MenuChoice[]=[back])=>hud.showList(title,body,rows,footer,hud.touchTargetSize,{placement:'center',dismissOnBackdrop:false});
 const quoteRow=(action:PetAction,description:string,label=actionName(action)):MenuRow=>{const q=game.pets.quote(action);return {label,detail:description+'\n'+cost(q)+(q.allowed?'':'\n'+q.reason),action:previewMenu(action),disabled:!q.allowed};};
 const speciesView=(id:string)=>v.species.find(species=>species.id===id),journeyFor=(id:string)=>journeys.find(journey=>journey.species===id);
 const go=(id:string,label=t('step.go')):MenuChoice=>{const journey=journeyFor(id);return {label,action:'pet-go:'+id,disabled:!journey?.current||journey.complete&&!journey.owned};};
 if(menu.startsWith('pets:quote:')){
  const action=readAction(menu.slice(11));if(!action)return renderPetPanel(hud,game,'pets');
  const q=game.pets.quote(action),name=action.kind==='adopt'?speciesView(action.species)?.name:action.kind==='research'?v.research.find(r=>r.id===action.skill)?.name:action.kind==='claim'?t('journal.refund'):v.roster.find(p=>p.id===action.pet)?.name;
  if(!name)return renderPetPanel(hud,game,'pets');const returnMenu=petActionReturnMenu(action),backLabel=action.kind==='adopt'?'action.backCatalog':action.kind==='research'?'action.backResearch':action.kind==='assign'?'action.backTraits':action.kind==='study'||action.kind==='branch'?'action.backSignature':action.kind==='claim'?'action.backJournal':'action.backPet';
  hud.show(t('preview.title',{action:actionName(action),name}),t('preview.description',{description:q.description,cost:cost(q)})+(q.allowed?'':'\n\n'+q.reason),[{back:true,label:t(backLabel),action:returnMenu},{label:actionName(action),action:'pet-commit:'+encode(action)+':'+encodeURIComponent(q.token),primary:true,disabled:!q.allowed}],false,{placement:'center',dismissOnBackdrop:false});return true;
 }
 if(menu==='pets:catalog'||menu==='pets:first'){
  const first=menu==='pets:first',species=v.species.filter(d=>!first||d.nativeQuality==='普通');
  show(t(first?'first.title':'catalog.title'),first?t('catalog.first'):t('index.catalogDetail'),species.map(d=>{const steps=journeyFor(d.id)?.steps.filter(step=>step.phase==='acquisition')??[],done=steps.filter(step=>step.completed).length,total=steps.length;return {label:d.name+' · '+d.nativeQuality,tone:petQualityTone(d.nativeQuality),detail:d.description+'\n'+(d.owned?t('catalog.owned'):t('catalog.progress',{done,total})),action:'pets:catalog:'+d.id};}));return true;
 }
 if(menu.startsWith('pets:catalog:')){
  const id=menu.slice(13),d=speciesView(id),j=journeyFor(id);if(!d||!j)return renderPetPanel(hud,game,'pets:catalog');
  const steps=j.steps.filter(step=>d.owned||step.phase==='acquisition'),acquisition=j.steps.filter(step=>step.phase==='acquisition');
  const rows:MenuRow[]=steps.map(step=>({label:(step.completed?t('step.done'):step.active?t('step.current'):t('step.wait'))+' · '+step.label,detail:t('step.location',{area:getArea(step.area).name,description:step.description}),action:'pet-go:'+id,disabled:!step.active}));
  if(d.owned)rows.unshift({label:t('catalog.owned'),detail:d.signature.name+' · '+d.signature.description,action:petMenu(id)});
  else rows.push(quoteRow({kind:'adopt',species:d.id},d.acquirable?t('catalog.ready'):t('catalog.progress',{done:acquisition.filter(step=>step.completed).length,total:acquisition.length})));
  show(d.name,t('catalog.summary',{quality:d.nativeQuality,role:t(('role.'+d.role) as Parameters<typeof t>[0]),description:d.description}),rows,[{back:true,label:t('action.backCatalog'),action:'pets:catalog'},go(id)]);return true;
 }
 if(menu==='pets:research'||menu.startsWith('pets:research:')){
  const id=menu.slice(14),research=v.research.find(r=>r.id===id);
  if(!research){show(t('research.title'),t('research.description'),v.research.map(r=>({label:r.name,detail:r.description+'\n'+(r.unlocked?t('research.rank',{rank:r.rank}):t('research.locked')),action:'pets:research:'+r.id})));return true;}
  const rows:MenuRow[]=[quoteRow({kind:'research',skill:research.id},research.rank>=5?t('research.maximum'):t('research.permanent'),t('research.preview'))],source=game.petJourneys.manualTarget(research.id);
  if(!research.unlocked&&source)rows.push({label:t('research.source'),detail:getArea(source.area).name+' · '+source.label,action:'pet-manual-go:'+research.id});
  show(research.name,research.description+'\n'+(research.unlocked?t('research.rank',{rank:research.rank}):t('research.locked')),rows,[{back:true,label:t('action.backResearch'),action:'pets:research'}]);return true;
 }
 if(menu==='pets:journal'||menu.startsWith('pets:journal:')){
  const id=menu.slice(13),pet=v.roster.find(p=>p.id===id);
  if(!pet){const rows:MenuRow[]=v.roster.map(p=>({label:p.name,detail:t('journal.records',{name:p.name,count:p.journal.length}),action:'pets:journal:'+p.id}));if(v.pending.gold||v.pending.essence)rows.push(quoteRow({kind:'claim'},t('journal.pending',v.pending)));show(t('journal.title'),t('journal.description'),rows);return true;}
  const allSteps=journeys.flatMap(j=>j.steps),rows:MenuRow[]=pet.journal.map((record,index)=>({label:allSteps.find(step=>step.id===record.id.replace('petj:done:','petj:'))?.label??t('journal.record',{index:index+1}),detail:categoryName(record.category),action:'pets:journal:'+pet.id,disabled:true}));
  if(!rows.length)rows.push({label:t('journal.empty'),detail:'',action:'pets:journal:'+pet.id,disabled:true});
  show(pet.name+' · '+t('journal.title'),t('journal.description')+(pet.level<pet.catchupLevel?'\n'+t('catchup',{level:pet.catchupLevel}):''),rows,[{back:true,label:t('action.backPet'),action:petMenu(pet.id)},go(pet.id,t('journal.story'))]);return true;
 }
 const match=/^pets:(pet|traits|slot|signature|ascend):([^:]+)(?::(0|1))?$/.exec(menu);
 if(match){
  const page=match[1];let id:string;try{id=decodeURIComponent(match[2]);}catch{return renderPetPanel(hud,game,'pets');}const pet=v.roster.find(p=>p.id===id);if(!pet)return renderPetPanel(hud,game,'pets');
  const pback:MenuChoice={back:true,label:t('action.backPet'),action:petMenu(id)},definition=speciesView(pet.species)!;
  if(page==='traits'){
   show(t('traits.title'),pet.name,[0,1].map(slot=>{const skill=pet.traitSlots[slot],r=v.research.find(row=>row.id===skill);return {label:t('traits.slot',{slot:slot+1}),detail:(r?t('traits.current',{name:r.name,rank:r.rank}):t('traits.empty'))+'\n'+t('traits.unlock',{level:slot?15:5}),action:`pets:slot:${id}:${slot}`};}),[pback,{label:t('traits.research'),action:'pets:research'}]);return true;
  }
  if(page==='slot'){
   const slot=Number(match[3]) as 0|1;if(match[3]===undefined)return renderPetPanel(hud,game,traitMenu(id));
   const rows=v.research.map(research=>quoteRow({kind:'assign',pet:id,slot,skill:research.id},research.description+'\n'+(research.unlocked?t('research.rank',{rank:research.rank}):t('research.locked')),research.name));
   if(pet.traitSlots[slot])rows.unshift(quoteRow({kind:'assign',pet:id,slot,skill:null},t('cost.free'),t('traits.remove')));
   show(t('traits.title'),t('traits.select',{name:pet.name,slot:slot+1}),rows,[{back:true,label:t('action.backTraits'),action:traitMenu(id)},{label:t('traits.research'),action:'pets:research'}]);return true;
  }
  if(page==='signature'){
   const skill=pet.signature,status=game.petSkillStatus(id),selected=skill.branches.find(branch=>branch.id===pet.branch),rows:MenuRow[]=[];
   if(pet.signatureRank===1)for(const branch of skill.branches)rows.push(quoteRow({kind:'study',pet:id,branch:branch.id},branch.description+'\n'+t('signature.choose'),t('signature.branch',{name:branch.name})));
   else{
    if(pet.signatureRank<3)rows.push(quoteRow({kind:'study',pet:id},t('signature.next')));
    for(const branch of skill.branches){const row=quoteRow({kind:'branch',pet:id,branch:branch.id},branch.description+'\n'+t('signature.change'),t('signature.branch',{name:branch.name}));rows.push({...row,selected:branch.id===pet.branch,disabled:row.disabled||branch.id===pet.branch});}
   }
   show(t('signature.title'),t('signature.summary',{name:skill.name,rank:pet.signatureRank,branch:selected?.name??t('signature.base')})+'\n'+skill.trigger+'\n'+t(('signature.effect.'+skill.effect) as Parameters<typeof t>[0],{percent:number(skill.percent)})+'\n'+t(skill.duration>0?'signature.timing':'signature.instant',{cooldown:number(skill.cooldown),duration:number(skill.duration)})+'\n'+t('signature.status',{cooldown:number(status.cooldown),duration:number(status.effectSeconds)})+(pet.signatureRank===3?'\n'+t('signature.max'):''),rows,[pback]);return true;
  }
  if(page==='ascend'){
   const target=PET_PROMOTIONS.find(promotion=>pet.quality==='普通'?promotion.quality==='珍兽':pet.quality==='珍兽'?promotion.quality==='神兽':false),rows:MenuRow[]=[
    {label:t('ascend.level',{level:pet.level}),detail:target?t('ascend.level',{level:target.level}):t('quality.path'),action:menu,disabled:true},
    {label:t('ascend.bond',{bond:pet.bond}),detail:target?t('ascend.bond',{bond:target.bond}):'',action:menu,disabled:true},
    {label:t('ascend.records',{count:pet.journal.length,categories:new Set(pet.journal.map(record=>record.category)).size}),detail:pet.journal.map(record=>categoryName(record.category)).filter((value,index,all)=>all.indexOf(value)===index).join(' / '),action:'pets:journal:'+id},
    {label:t('ascend.habit'),detail:t(pet.proof.habit?'proof.yes':'proof.no'),action:'pet-go:'+id},
    {label:t('ascend.trials'),detail:pet.proof.trials.map(categoryName).join(' / ')||t('proof.no'),action:'pet-go:'+id},
    {label:t('ascend.final'),detail:t(pet.proof.final?'proof.yes':'proof.no'),action:'pet-go:'+id},
    quoteRow({kind:'promote',pet:id},t('quality.path'),t('ascend.next')),
   ];show(t('ascend.title'),pet.name+'\n'+t('ascend.summary',{quality:pet.quality}),rows,[pback,go(id,t('journal.story'))]);return true;
  }
  const rows:MenuRow[]=[
   {label:t('detail.native',{name:pet.nativeSkill}),detail:bonusDescription(pet.bonuses),action:menu,disabled:true},
   quoteRow({kind:v.active===id?'rest':'deploy',pet:id},t(v.active===id?'detail.active':'detail.resting')),
   {label:t('traits.title'),detail:pet.traitSlots.map(skill=>v.research.find(r=>r.id===skill)?.name??t('traits.empty')).join(' / '),action:traitMenu(id)},
   {label:t('signature.title'),detail:pet.signature.name+' · '+pet.signatureRank+'阶',action:signatureMenu(id)},
   {label:t('ascend.title'),detail:t('quality.path'),action:'pets:ascend:'+id},
   quoteRow({kind:'train',pet:id},t('detail.train')),quoteRow({kind:'bond',pet:id},t('detail.bond')),
   {label:t('journal.title'),detail:t('journal.records',{name:pet.name,count:pet.journal.length}),action:'pets:journal:'+id},
  ];
  show(pet.name+' · '+t(('role.'+pet.role) as Parameters<typeof t>[0]),t('detail.summary',{quality:pet.quality,level:pet.level,xp:pet.xp,nextXp:pet.nextXp,bond:pet.bond,essence:v.essence})+(pet.level<pet.catchupLevel?'\n'+t('catchup',{level:pet.catchupLevel}):'')+(v.available?'':'\n'+v.reason),rows);return true;
 }
 const active=v.roster.find(pet=>pet.id===v.active),rows:MenuRow[]=v.roster.map(pet=>({label:pet.name+(pet.id===v.active?' · '+t('detail.active'):''),detail:t('index.level',{quality:pet.quality,level:pet.level,role:t(('role.'+pet.role) as Parameters<typeof t>[0]),bond:pet.bond}),action:petMenu(pet.id),tone:petQualityTone(pet.quality)}));
 if(!v.roster.length)rows.push({label:t('index.first'),detail:t('index.firstDetail'),action:'pets:first'});
 rows.push({label:t('index.catalog'),detail:t('index.catalogDetail'),action:'pets:catalog'},{label:t('research.title'),detail:t('research.description'),action:'pets:research'},{label:t('journal.title'),detail:t('journal.description'),action:'pets:journal'});
 show(t('title'),t('index.summary',{active:active?.name??t('index.none'),essence:v.essence,gold:game.state.player.gold})+'\n'+t('index.description'),rows,[{back:true,label:t('action.backJourney'),action:'pause'}]);return true;
}
