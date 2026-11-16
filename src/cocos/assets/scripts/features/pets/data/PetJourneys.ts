import type {AreaDef,EnemySpawn,InteractionDef,Point} from '../../../core/Contracts';
import type {PetSpeciesId,PetSkillId} from './Pets';
import {petReleaseReady} from '../common/PetAccess';
import {petJourneyText as t} from '../locales/PetJourneyText';
// Both world helpers are engine-free; use the same terrain barriers and
// immutable footprint navigation as SceneBuilder's actual collision query.
import {getTerrain} from '../../world/runtime/Terrain';
import {Navigation} from '../../navigation/runtime/Navigation';

export type PetJourneyKind='observe'|'mechanism'|'escort'|'combat'|'invite';
export type PetTrialKind='guard'|'adapt'|'cooperate';
export interface PetJourneyStep {id:string;species:PetSpeciesId;index:number;phase:'acquisition'|'training';kind:PetJourneyKind;label:string;description:string;area:string;point:Point;switches:Point[];route:Point[];spawnPoints:Point[];manuals:PetSkillId[];trial?:PetTrialKind;habit?:boolean;final?:boolean}
export interface PetJourneyDefinition {species:PetSpeciesId;title:string;steps:PetJourneyStep[];acquisitionEnd:number}
type Species=PetSpeciesId;
const definitions:PetJourneyDefinition[]=[];
function build(species:Species,stages:{area:string;kind:PetJourneyKind;label?:string;trial?:PetTrialKind;manuals?:PetSkillId[]}[]){
 const title=t((species+'.title') as Parameters<typeof t>[0]),description=t((species+'.body') as Parameters<typeof t>[0]);
 const stagesAll=[...stages,{area:'S01',kind:'invite' as const,label:t('invitation')}];
 const acquisitionEnd=stagesAll.length-1;
 const training=[{area:stages[0].area,kind:'observe' as const,label:t('habit'),habit:true},{area:stages[0].area,kind:'combat' as const,label:t('guard'),trial:'guard' as const},{area:'S15',kind:'mechanism' as const,label:t('adapt'),trial:'adapt' as const},{area:'S06',kind:'escort' as const,label:t('cooperate'),trial:'cooperate' as const},{area:'S07',kind:'observe' as const,label:t('revisitLook'),revisit:true},{area:'S13',kind:'mechanism' as const,label:t('revisitRepair'),trial:'adapt' as const},{area:'S05',kind:'escort' as const,label:t('revisitEscort'),trial:'cooperate' as const},{area:'S11',kind:'combat' as const,label:t('revisitGuard'),trial:'guard' as const},{area:'S01',kind:'invite' as const,label:t('final'),final:true}];
 const steps:PetJourneyStep[]=[...stagesAll,...training].map((stage,index)=>({id:`petj:${species}:${index}`,species,index,phase:index<=acquisitionEnd?'acquisition':'training',kind:stage.kind,label:stage.label??t(stage.kind==='observe'?'observe':stage.kind==='mechanism'?'repair':stage.kind==='escort'?'escort':'threat'),description:index<=acquisitionEnd?description:'habit' in stage?t('habitBody'):'revisit' in stage?t('revisitLookBody'):'trial' in stage&&stage.trial?t((stage.trial+'Body') as Parameters<typeof t>[0]):t('finalBody'),area:stage.area,point:{x:0,z:0},switches:[],route:[],spawnPoints:[],manuals:'manuals' in stage?stage.manuals??[]:[],...('trial' in stage&&stage.trial?{trial:stage.trial}:{}),...('habit' in stage?{habit:true}:{}),...('final' in stage?{final:true}:{})}));
 definitions.push({species,title,steps,acquisitionEnd});
}
build('ember_fox',[{area:'S03',kind:'mechanism',manuals:['ferocity']},{area:'S05',kind:'escort'}]);
build('stone_turtle',[{area:'S13',kind:'mechanism',manuals:['thick_hide']},{area:'S13',kind:'escort'}]);
build('dew_sprite',[{area:'S06',kind:'observe'},{area:'S15',kind:'mechanism',manuals:['devotion']},{area:'S06',kind:'escort'}]);
build('tabby_cat',[{area:'S07',kind:'observe'},{area:'S07',kind:'mechanism',manuals:['moisture']},{area:'S07',kind:'escort'}]);
build('hunting_dog',[{area:'S19',kind:'observe'},{area:'S19',kind:'mechanism',manuals:['haste']},{area:'S06',kind:'escort'}]);
build('grey_wolf',[{area:'S05',kind:'observe',label:t('clue1')},{area:'S19',kind:'observe',label:t('clue2')},{area:'S06',kind:'mechanism',label:t('clue3')},{area:'S05',kind:'combat',manuals:['headwind']},{area:'S05',kind:'escort',label:t('ecology')}]);
build('mountain_tiger',[{area:'S08',kind:'observe',label:t('clue1')},{area:'S13',kind:'observe',label:t('clue2')},{area:'H04',kind:'mechanism',label:t('clue3')},{area:'S08',kind:'combat',manuals:['keen_edge']},{area:'S08',kind:'mechanism',label:t('ecology')}]);
build('hunting_hawk',[{area:'S11',kind:'observe',label:t('clue1'),manuals:['daybreak']},{area:'H07',kind:'observe',label:t('clue2')},{area:'H01',kind:'mechanism',label:t('clue3')},{area:'H07',kind:'combat'},{area:'H07',kind:'mechanism',label:t('ecology')}]);
build('spotted_deer',[{area:'S14',kind:'observe',label:t('clue1')},{area:'S06',kind:'observe',label:t('clue2')},{area:'S15',kind:'mechanism',label:t('clue3')},{area:'S14',kind:'combat'},{area:'S14',kind:'escort',label:t('ecology')}]);
build('griffin',[{area:'S12',kind:'observe',label:t('record1')},{area:'S15',kind:'observe',label:t('record2')},{area:'H01',kind:'observe',label:t('record3')},{area:'H03',kind:'combat',label:t('guard'),trial:'guard'},{area:'S15',kind:'mechanism',label:t('adapt'),trial:'adapt'},{area:'S06',kind:'escort',label:t('cooperate'),trial:'cooperate'}]);
build('white_tiger',[{area:'S11',kind:'observe',label:t('record1')},{area:'H04',kind:'observe',label:t('record2')},{area:'U1-03',kind:'observe',label:t('record3')},{area:'H04',kind:'combat',label:t('guard'),trial:'guard'},{area:'H07',kind:'mechanism',label:t('adapt'),trial:'adapt'},{area:'H03',kind:'escort',label:t('cooperate'),trial:'cooperate'}]);
build('dragon',[{area:'S09',kind:'observe',label:t('record1')},{area:'U1-01',kind:'observe',label:t('record2')},{area:'H07',kind:'observe',label:t('record3')},{area:'U1-03',kind:'combat',label:t('guard'),trial:'guard'},{area:'U1-02',kind:'mechanism',label:t('adapt'),trial:'adapt'},{area:'S19',kind:'escort',label:t('cooperate'),trial:'cooperate'}]);
export const PET_JOURNEYS:readonly PetJourneyDefinition[]=definitions;
export const PET_JOURNEY_STEPS:readonly PetJourneyStep[]=definitions.flatMap(def=>def.steps);
export const petJourney=(species:string)=>PET_JOURNEYS.find(def=>def.species===species);
export const petJourneyStep=(id:string)=>PET_JOURNEY_STEPS.find(step=>step.id===id);
export const petJourneyObject=(id:string)=>{const direct=petJourneyStep(id);if(direct)return {step:direct,part:-1};const match=/^(petj:[a-z_]+:\d+):switch:([0-2])$/.exec(id),step=match&&petJourneyStep(match[1]);return step?.kind==='mechanism'?{step,part:Number(match![2])}:undefined;};
export const petTrialEnemyId=(step:PetJourneyStep,index:number)=>`petj-trial-${step.species}-${step.index}-${index}`;
export const petTrialKinds=(step:PetJourneyStep):EnemySpawn['kind'][]=>step.phase==='training'?['raider','shield','archer']:['raider','archer'];
export const petTrialBaseHp=(kind:EnemySpawn['kind'])=>kind==='shield'?38:kind==='archer'?24:28;
export function petTrialSpawns(step:PetJourneyStep,level:number):EnemySpawn[]{return petTrialKinds(step).map((kind,index)=>({id:petTrialEnemyId(step,index),kind,level,hp:petTrialBaseHp(kind),trainingEnemy:true,trainingAttacks:true,...(step.spawnPoints[index]??{x:step.point.x+(index-1)*2.6,z:step.point.z+4+index*.5})}));}

const occupied=(area:AreaDef,p:Point,padding=.9)=>Math.abs(p.x)>area.width/2-4||Math.abs(p.z)>area.depth/2-4||area.obstacles.some(o=>Math.abs(p.x-o.x)<o.width/2+padding&&Math.abs(p.z-o.z)<o.depth/2+padding)||area.buildings.some(o=>Math.abs(p.x-o.x)<o.width/2+padding&&Math.abs(p.z-o.z)<o.depth/2+padding);
/** Content placement uses the existing terrain/obstacle map. No new campaign
 * chapter, platform capability or area ID is introduced. */
export function installPetJourneys(areas:Record<string,AreaDef>):void {
 const taken=new Map<string,Point[]>(),objects=new Map(Object.values(areas).map(area=>[area.id,area.objects.filter(object=>!object.id.startsWith('petj:'))])),plans=new Map<string,{nav:Navigation;anchor:Point}>();
 const plan=(area:AreaDef)=>{let found=plans.get(area.id);if(found)return found;const nav=new Navigation(area.width,area.depth,[...area.obstacles,...getTerrain(area).barriers]);let anchor=area.spawn;if(nav.blocked(anchor,.5)){outer:for(let radius=.5;radius<=12;radius+=.5)for(let index=0;index<24;index++){const point={x:area.spawn.x+Math.cos(index*Math.PI/12)*radius,z:area.spawn.z+Math.sin(index*Math.PI/12)*radius};if(!nav.blocked(point,.5)){anchor=point;break outer;}}}found={nav,anchor};plans.set(area.id,found);return found;};
 const add=(area:AreaDef,object:InteractionDef)=>{objects.get(area.id)!.push(object);if(petReleaseReady()&&!area.objects.some(existing=>existing.id===object.id))area.objects.push(object);};
 const place=(area:AreaDef,preferred:Point,space=2.8):Point=>{
  const used=taken.get(area.id)??[];
  const layout=plan(area);
  for(let ring=0;ring<20;ring++)for(let i=0;i<(ring?16:1);i++){const angle=i*Math.PI/8,p={x:preferred.x+Math.cos(angle)*ring*2.5,z:preferred.z+Math.sin(angle)*ring*2.5};if(!occupied(area,p)&&!layout.nav.blocked(p,.9)&&layout.nav.visible(layout.anchor,p,.5)&&!used.some(q=>Math.hypot(p.x-q.x,p.z-q.z)<space)&&!objects.get(area.id)!.some(o=>Math.hypot(p.x-o.x,p.z-o.z)<2.5)){used.push(p);taken.set(area.id,used);return p;}}
  throw new Error(`No safe pet journey objective location in ${area.id}`);
 };
 for(const step of PET_JOURNEY_STEPS){const area=areas[step.area];if(!area)throw new Error(`Unknown pet venue ${step.area}`);step.point=place(area,{x:area.spawn.x+10,z:area.spawn.z+3});
  const object:InteractionDef={id:step.id,eventId:step.id,action:'pet_journey',label:step.label,description:step.description,radius:1.35,...step.point};add(area,object);
  if(step.kind==='mechanism'){step.switches=[0,1,2].map(index=>place(area,{x:step.point.x+(index-1)*3,z:step.point.z+3}));step.switches.forEach((p,index)=>{const id=step.id+':switch:'+index;add(area,{id,eventId:id,action:'pet_journey',label:t(('switch'+(index+1)) as Parameters<typeof t>[0]),description:step.description,radius:1.35,...p});});}
  if(step.kind==='escort')step.route=[0,1,2].map(index=>place(area,{x:step.point.x+(index+1)*3,z:step.point.z+(index%2?3:0)},1));
  if(step.kind==='combat'){
   const nav=plan(area).nav;step.spawnPoints=[];
   for(let radius=4;radius<=14&&step.spawnPoints.length<petTrialKinds(step).length;radius+=2)for(let index=0;index<24&&step.spawnPoints.length<petTrialKinds(step).length;index++){const p={x:step.point.x+Math.cos(index*Math.PI/12)*radius,z:step.point.z+Math.sin(index*Math.PI/12)*radius};if(!occupied(area,p,.6)&&!nav.blocked(p,.6)&&nav.visible(step.point,p,.6)&&!step.spawnPoints.some(q=>Math.hypot(q.x-p.x,q.z-p.z)<1.5))step.spawnPoints.push(p);}
   if(step.spawnPoints.length!==petTrialKinds(step).length)throw new Error(`No safe companion trial wave in ${step.area}`);
  }
 }
}
