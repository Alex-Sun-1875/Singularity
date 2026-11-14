import {playerCombatAttributes} from '../../combat/common/CombatAccuracy';
import {RESOURCE_RULES,resourceProfile,skillResourceText,resourceCostText} from '../../combat/common/ClassResource';
import {Label,Node,ScrollView,Vec2} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {COMBAT_LOADOUTS,professionAcceptsItem,type CombatFamily} from '../common/CombatLoadouts';
import {ATTRIBUTES,SKILL_RANK_COSTS,skillPlanRemaining,type Attribute} from '../common/Progression';
import {COMBAT_SKILLS,COMBAT_SKILL_LIST,type CombatStyle} from '../../combat/data/PureSkills';
import {COMBAT_SKILL_ICONS} from '../../combat/runtime/CombatSkillIcons';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {preparationText as t} from '../locales';
import {PreparationSkin as P} from '../../../shared/ui/PreparationSkin';
import {PreparationControls as Controls} from '../../../shared/ui/PreparationControls';
import {PREPARATION_DESIGN as D} from '../../../shared/ui/PreparationTheme';

const FAMILIES=Object.keys(COMBAT_LOADOUTS) as CombatFamily[];
type Draft={attributes:Record<Attribute,number>;learned:Record<string,number>;attributeToken:string;skillToken:string;family:CombatStyle;selected:string;notice:string;skillScroll?:number};
type ProfessionPreview={family:CombatFamily;weapon?:string;token?:string;busy:boolean;notice:string};
const drafts=new WeakMap<GameSession,Draft>(),professions=new WeakMap<GameSession,ProfessionPreview>();
function draft(game:GameSession):Draft {
 let v=drafts.get(game);const s=game.state;
 if(!v){v={attributes:{...s.progression.attributes},learned:{...s.progression.learned},attributeToken:game.attributePlanToken(),skillToken:game.skillPlanToken(),family:s.combat.family,selected:COMBAT_LOADOUTS[s.combat.family].activeSlots[0]!,notice:''};drafts.set(game,v);}
 if(v.attributeToken!==game.attributePlanToken()){v.attributes={...s.progression.attributes};v.attributeToken=game.attributePlanToken();v.notice=t('allocation.stale');}
 if(v.skillToken!==game.skillPlanToken()){v.learned={...s.progression.learned};v.skillToken=game.skillPlanToken();v.notice=t('allocation.stale');}
 return v;
}
export function hasPreparationPreview(game:GameSession){const v=drafts.get(game);return !!v&&(v.attributeToken===game.attributePlanToken()&&ATTRIBUTES.some(k=>v.attributes[k]!==game.state.progression.attributes[k])||v.skillToken===game.skillPlanToken()&&Object.keys(v.learned).some(k=>v.learned[k]!==game.state.progression.learned[k]));}
export function discardPreparationPreview(game:GameSession){drafts.delete(game);}
export function beginAllocation(game:GameSession,skill?:string){const v=draft(game);v.notice='';if(skill&&COMBAT_SKILLS[skill]){v.family=COMBAT_SKILLS[skill].style;v.selected=skill;}else{v.family=game.state.combat.family;v.selected=COMBAT_LOADOUTS[game.state.combat.family].activeSlots[0]!;}}
export function browseAllocationFamily(game:GameSession,family:CombatStyle){if(![...FAMILIES,'COM'].includes(family))return;const v=draft(game);v.family=family;v.skillScroll=0;v.selected=COMBAT_SKILL_LIST.find(s=>s.style===family)!.id;}
export function resetAllocationPreview(game:GameSession,scope:string){const v=draft(game);if(scope==='attributes')v.attributes={strength:10,dexterity:10,intellect:10,vitality:10};else for(const skill of COMBAT_SKILL_LIST)if(v.learned[skill.id]&&(scope==='all'||skill.style===v.family))v.learned[skill.id]=1;v.notice=t('allocation.preview');}
export function chooseProfession(game:GameSession,family=game.state.combat.family,weapon?:string){if(!FAMILIES.includes(family))family=game.state.combat.family;professions.set(game,{family,weapon,busy:false,notice:''});}
export function professionPreview(game:GameSession){if(!professions.has(game))chooseProfession(game);return professions.get(game)!;}
export function professionBusy(game:GameSession,busy:boolean,notice=''){const v=professionPreview(game);v.busy=busy;v.notice=notice;}

function text(ui:RpgPanel,value:string,x:number,y:number,w:number,h=24,size=14,color=C.ink,parent=ui.panel){return ui.text(parent,value,ui.x(x),ui.y(y),w*ui.scale,h*ui.scale,color,size*ui.scale);}
function center(ui:RpgPanel,value:string,x:number,y:number,w:number,h=24,size=14,color=C.ink){const l=text(ui,value,x,y,w,h,size,color);l.horizontalAlign=Label.HorizontalAlign.CENTER;return l;}
function top(ui:RpgPanel){return (ui.height/2-ui.bodyTop)/ui.scale;}
function bottom(ui:RpgPanel){return (ui.height/2-ui.bodyBottom)/ui.scale;}
function height(ui:RpgPanel){return ui.height/ui.scale;}
function pane(ui:RpgPanel,left:number,w:number,name:string){return ui.column(left,w,name);}
function art(ui:RpgPanel,id:string,x:number,y:number,w:number,h:number,sliced=false){return P.art(ui,ui.panel,id,ui.x(x),ui.y(y),w,h,sliced);}
function rule(ui:RpgPanel,x:number,y:number,w:number){return P.rule(ui,ui.panel,ui.x(x),ui.y(y),w);}
function skillIcon(ui:RpgPanel,parent:Node,id:string,x:number,y:number,size:number){const path=COMBAT_SKILL_ICONS[id];return Controls.icon(ui,parent,path?'ui/combat-relief/'+path:undefined,x,y,size,'PreparationSkillIcon:'+id);}
function tabButton(ui:RpgPanel,label:string,x:number,y:number,w:number,action:string,selected:boolean,run:()=>void,size=18){return Controls.tab(ui,{label,x,y,width:w,action,selected,run,fontSize:size});}
function plaque(ui:RpgPanel,value:string,x:number,y:number,w:number,size=16){return Controls.identity(ui,{value,x,y,width:w,fontSize:size});}

export function renderProfessionPanel(hud:Hud,game:GameSession){
 const v=professionPreview(game),ui=new RpgPanel(hud,game,'profession','ProfessionPanel',true),u=ui.scale,gap=ui.gap/u,a=top(ui),b=bottom(ui),current=game.state.combat.family;
 const layout=D.layouts.profession;pane(ui,...layout.portrait,'ProfessionPortrait');const heroTop=ui.referenceLayout?32:a,heroH=b-heroTop-48;art(ui,'hero',103,heroTop+heroH/2,heroH*435/560,heroH);plaque(ui,t('hero',{level:game.state.progression.level}),102,b-32,174,15.5);
 if(ui.referenceLayout)P.caption(ui,ui.panel,t('currentProfession',{name:''}),t(`name.${current}`),ui.x(102),ui.y(b-10),200);else center(ui,t('currentProfession',{name:t(`name.${current}`)}),102,b-10,200,22,12.5,F.color('state.selected'));
 const cardW=(layout.cards.width-gap)/2,cardH=Math.min(layout.cards.maxHeight,(b-a-gap)/2),left=layout.cards.left,cardTop=ui.referenceLayout?layout.cards.referenceTop:a;
 FAMILIES.forEach((family,i)=>{
  const cx=left+cardW/2+i%2*(cardW+gap),cy=cardTop+cardH/2+Math.floor(i/2)*(cardH+gap),selected=v.family===family;
  Controls.professionCard(ui,{x:cx,y:cy,width:cardW,height:cardH,action:'ProfessionCard:'+family,enabled:!v.busy,selected,
   run:()=>{v.family=family;if(v.weapon&&!professionAcceptsItem(family,v.weapon))v.weapon=undefined;v.notice='';renderProfessionPanel(hud,game);},
   image:D.artwork.familyPaintings[family],title:t(`name.${family}`),description:t(`role.${family}`),
   badge:current===family||selected?{label:t(current===family?'current':'preview'),tone:current===family?'teal':'gold'}:undefined});
 });
 const detail=pane(ui,...layout.detail,'ProfessionPreviewDetail');ui.drape(detail,layout.detail[1]*u,ui.bodyHeight);
 const Y=(y:number)=>!ui.referenceLayout?a+12+(y-56)*(b-a-30)/272:y;
 const change=game.combatLoadoutChange(v.family,v.weapon);v.token=change.token;
 text(ui,t(`name.${v.family}`),710,Y(66),234,34,25);P.badge(ui,ui.panel,t(v.family===current?'current':'preview'),ui.x(808),ui.y(Y(66)),48,'gold');
 rule(ui,710,Y(89),236);text(ui,t(`role.${v.family}`),710,Y(107),234,26,15.5);rule(ui,710,Y(123),236);
 const weapon=UiSkin.asset(ui.panel,D.artwork.mainWeaponIcons[v.family],20*u,20*u,false);weapon.node.setPosition(ui.x(606),ui.y(Y(142)));
 text(ui,t('profession.weapon',{name:t(`weapon.${v.family}`)}),729,Y(142),218,25,15);
 art(ui,'stat-power',606,Y(169),19,20);text(ui,t('profession.growth',{name:t(`growth.${v.family}`)}),729,Y(169),218,25,14.5);rule(ui,710,Y(183),236);
 [...(change.activeSlots??[]),change.ultimate].forEach((id,i)=>{if(id)skillIcon(ui,ui.panel,id,ui.x(606+i*49),ui.y(Y(225)),44);});
 rule(ui,710,Y(272),236);art(ui,'info',606,Y(292),16,17);
 text(ui,t('previewOnly'),730,Y(292),214,26,14);
 const extra=change.offhand?t('profession.offhand',{name:EQUIPMENT[change.offhand].name}):change.weapon?t('profession.useWeapon',{name:game.itemView(change.weapon).name}):change.reason;
 if(change.offhand||!change.available)text(ui,extra,710,b-10,236,18,11.5,C.muted);
 const same=v.family===current&&change.weapon===game.state.equipment.weapon;
 ui.footer(v.busy?t('profession.loading'):v.notice||(!change.available?change.reason:t('profession.ready')),[{label:t('profession.cancel'),action:'ProfessionCancel',enabled:!v.busy,run:()=>{chooseProfession(game);renderProfessionPanel(hud,game);}},{label:same?t('profession.noChange'):t('profession.apply',{name:t(`name.${v.family}`).slice(0,2)}),action:'profession-apply',enabled:!v.busy&&!same&&change.available,primary:true},{label:t('return'),action:'close',enabled:!v.busy}]);
}

function allocationSidebar(ui:RpgPanel,game:GameSession,tab:'attributes'|'skills',remaining:number,spent:number){
 const v=draft(game),u=ui.scale,hu=ui.hit/u,gap=ui.gap/u,a=top(ui),b=bottom(ui),skill=tab==='skills',x=skill?187:93,w=skill?96:160;
 if(skill){pane(ui,0,132,'AllocationHero');const heroTop=!ui.referenceLayout?a:32,h=!ui.referenceLayout?b-a-49:b-heroTop;art(ui,'hero-narrow',66,heroTop+h/2,Math.min(126,h*276/659),h);if(!ui.referenceLayout){plaque(ui,t('hero',{level:game.state.progression.level}),66,b-32,122,12.5);center(ui,t(`name.${game.state.combat.family}`),66,b-11,124,20,12,F.color('state.selected'));}}
 tabButton(ui,t('allocation.attributes'),x,ui.referenceLayout?(skill?62:67):a+hu/2,w,'AllocationTab:attributes',!skill,()=>ui.hud.actions.click('allocation:attributes'),skill?15.5:19);
 tabButton(ui,t('allocation.skills'),x,ui.referenceLayout?(skill?104:108):a+hu*1.5+gap,w,'AllocationTab:skills',skill,()=>ui.hud.actions.click('allocation:skills'),skill?15.5:19);
 if(skill){const cy=!ui.referenceLayout?a+hu*2.5+2*gap:174,n=ui.button(ui.panel,'',ui.x(x),ui.y(cy),w*u,'AllocationFamily',true,false,Math.max(ui.hit,46*u),()=>ui.hud.showList(t('allocation.familyTitle'),t('allocation.familyHint'),[...FAMILIES,'COM' as const].map(f=>({label:t(`name.${f}`),detail:f===game.state.combat.family?t('current'):'',action:'allocation-browse:'+f})),[{label:t('back'),action:'allocation:skills'}]),'catalog');const kind=v.family==='WAR'?'war':v.family==='BOW'?'bow':v.family==='THU'?'thu':'fir',motif=UiSkin.asset(n,'rpg-profession-'+kind+'-v1',90*u,38*u,false);motif.node.setPosition(0,0);if(ui.referenceLayout){plaque(ui,t('hero',{level:game.state.progression.level}),x,214,106,13);P.caption(ui,ui.panel,t('currentProfession',{name:''}),t(`name.${game.state.combat.family}`),ui.x(x),ui.y(237),108,12);rule(ui,x,258,88);}}
 else if(!ui.referenceLayout){const mid=(a+2*hu+gap+b-hu-gap)/2;art(ui,'crest-sword',x,mid-20,26,28);plaque(ui,t('hero',{level:game.state.progression.level}),x,mid+5,146,13.5);center(ui,t(`name.${game.state.combat.family}`),x,mid+25,158,20,12,F.color('state.selected'));}
 else{rule(ui,x,145,146);art(ui,'crest-sword',x,177,47,51);plaque(ui,t('hero',{level:game.state.progression.level}),x,214,138,14.5);P.caption(ui,ui.panel,t('currentProfession',{name:''}),t(`name.${game.state.combat.family}`),ui.x(x),ui.y(237),170);rule(ui,x,257,146);}
 const counterH=!ui.referenceLayout?hu:Math.max(hu,skill?52:60),counterY=!ui.referenceLayout?b-hu/2:skill?292:300,before=skill?game.state.progression.skillPoints:game.state.progression.unspentPoints;
 Controls.pointCounter(ui,{x,y:counterY,width:w,height:counterH,variant:skill?'skill':'attribute',action:'AllocationRespec',enabled:game.preparationAvailability().available,
  title:t(skill?'allocation.remainingSkills':'allocation.remainingAttributes',{before,after:remaining}),subtitle:t(skill?'allocation.skillSpent':'allocation.attributeSpent',{count:spent}),
  run:()=>ui.hud.show(t('allocation.respecTitle'),t('allocation.respecHint'),[...(!skill?[{label:t('allocation.respecAttributes'),action:'allocation-reset:attributes'}]:[{label:t('allocation.respecFamily'),action:'allocation-reset:family'},{label:t('allocation.respecAll'),action:'allocation-reset:all'}]),{label:t('cancel'),action:'allocation:'+tab}])});
}
function allocationScroll(hud:Hud):ScrollView|undefined {const find=(n:Node):Node|undefined=>n.name==='AllocationSkillListContent'?n:n.children.map(find).find(Boolean);return find(hud.modal)?.parent?.parent?.getComponent(ScrollView)??undefined;}
function pair(ui:RpgPanel,before:string,after:string,y:number,color=C.ink){
 const left=text(ui,before,716,y,64,28,16.5,C.ink);left.horizontalAlign=Label.HorizontalAlign.RIGHT;left.enableWrapText=false;left.overflow=Label.Overflow.SHRINK;
 center(ui,'→',766,y,18,28,16.5);const right=text(ui,after,810,y,52,28,16.5,color);right.enableWrapText=false;right.overflow=Label.Overflow.SHRINK;
}
function rankFacts(skill:typeof COMBAT_SKILL_LIST[number],rank:typeof COMBAT_SKILL_LIST[number]['ranks'][number]){
 const values:{label:string;value:number;suffix:string;icon:string}[]=[];
 const add=(label:string,value:number|undefined,suffix='',icon='stat-target')=>{if(typeof value==='number'&&value>0)values.push({label,value,suffix,icon});};
 if(skill.id==='BOW_06'){add(t('fact.damage'),Number(rank.maxDamagePerTargetS.toFixed(3)),'S');add('减速',Math.round((rank.slowPercent??0)*100),'%','stat-radius');}
 else if(skill.id==='FIR_04'){add('减速',Math.round((rank.slowPercent??0)*100),'%','stat-radius');add('冷却',rank.cooldownSeconds,'秒');}
 else if(skill.id==='BOW_07'){add(t('fact.damage'),Number(rank.maxDamagePerTargetS.toFixed(3)),'S');add('撤离',rank.moveMetres,'米','stat-radius');}
 else if(skill.id==='THU_06'){add('移速',Math.round((rank.speedPercent??0)*100),'%','stat-radius');add('减伤',Math.round((rank.reductionPercent??0)*100),'%','stat-life');}
 else if(skill.id==='BOW_02'){add(t('fact.chainTargets'),rank.targetLimit??undefined);add(t('fact.radius'),rank.radiusMetres,'米','stat-radius');}
 else{add(t('fact.targets'),rank.targetLimit??undefined);add(t('fact.radius'),rank.radiusMetres,'米','stat-radius');add(t('fact.range'),rank.rangeMetres,'米','stat-radius');add(t('fact.shield'),rank.shieldMaxHpPercent,'%','stat-life');add(t('fact.angle'),rank.geometry?.angleDegrees,'°','stat-radius');add(t('fact.break'),rank.breakPower);add(t('fact.damage'),rank.maxDamagePerTargetS,'S');}
 return values.slice(0,2);
}
export function renderAllocationPanel(hud:Hud,game:GameSession,tab:'attributes'|'skills'='attributes'){
 const v=draft(game),ui=new RpgPanel(hud,game,'allocation',tab==='attributes'?'AttributeAllocationPanel':'SkillAllocationPanel',true),u=ui.scale,hu=ui.hit/u,gap=ui.gap/u,a=top(ui),b=bottom(ui),safe=game.preparationAvailability().available,refresh=()=>{if(tab==='skills')v.skillScroll=allocationScroll(hud)?.getScrollOffset().y??0;renderAllocationPanel(hud,game,tab);};
 const original=game.state.progression,remaining=tab==='attributes'?3*(original.level-1)-ATTRIBUTES.reduce((n,k)=>n+v.attributes[k]-10,0):skillPlanRemaining(original,v.learned)??0,pending=tab==='attributes'?ATTRIBUTES.some(k=>v.attributes[k]!==original.attributes[k]):Object.keys(v.learned).some(k=>v.learned[k]!==original.learned[k]),spent=(tab==='attributes'?original.unspentPoints:original.skillPoints)-remaining;
 const skillMode=tab==='skills',layout=D.layouts.allocation,sidebar=skillMode?layout.skillSidebar:layout.attributeSidebar;pane(ui,sidebar[0],sidebar[1],'AllocationSidebar');allocationSidebar(ui,game,tab,remaining,spent);
 const rowsLayout=skillMode?layout.skillRows:layout.attributeRows,detailLayout=skillMode?layout.skillDetail:layout.attributeDetail,middle=pane(ui,rowsLayout[0],rowsLayout[1],'AllocationRows'),right=pane(ui,detailLayout[0],detailLayout[1],'AllocationBenefits');ui.drape(right,detailLayout[1]*u,ui.bodyHeight);
 if(!skillMode){
  const rowGap=Math.max(D.attributeRow.gap,gap),rowH=Math.max(hu,Math.min(D.attributeRow.maxHeight,(b-a-3*rowGap)/4)),step=rowH+rowGap;
  ATTRIBUTES.forEach((key,i)=>{
   const cy=a+rowH/2+i*step,before=original.attributes[key],after=v.attributes[key],change=(delta:number)=>{v.attributes[key]+=delta;v.notice=t('allocation.preview');refresh();};
   Controls.attributeRow(ui,{y:cy,height:rowH,label:t(`attribute.${key}`),icon:'attribute-'+key,before,after,
    decrease:{action:'AllocationAttribute:'+key+':-1',enabled:safe&&after>10,run:()=>change(-1)},
    increase:{action:'AllocationAttribute:'+key+':1',enabled:safe&&remaining>0&&after<80,run:()=>change(1)}});
  });
  const Y=(y:number)=>!ui.referenceLayout?a+12+(y-56)*(b-a-30)/272:y;
  text(ui,t('allocation.benefits'),726,Y(66),224,34,24);rule(ui,723,Y(85),212);
  const primary=({WAR:'strength',BOW:'dexterity',FIR:'intellect',THU:'intellect'} as const)[game.state.combat.family],value=game.progressionView().attributes[primary],bonus=(n:number)=>(n>=0?'+':'')+Number(n.toFixed(1))+'%';
  const resource=resourceProfile(game.state),before=playerCombatAttributes(game.state),after=playerCombatAttributes(game.state,v.attributes);
  const metrics=[
   {name:t('allocation.maxHp'),icon:'stat-life',before:String(game.state.player.maxHp),after:String(game.state.player.maxHp+4*(v.attributes.vitality-original.attributes.vitality))},
   {name:t(('allocation.'+primary+'Bonus') as 'allocation.strengthBonus'),icon:'stat-power',before:bonus((value-10)*.8),after:bonus((value+v.attributes[primary]-original.attributes[primary]-10)*.8)},
   {name:t('allocation.resourceMax',{name:resource.name}),icon:'stat-plan',before:String(game.state.player.maxFocus),after:String(game.state.player.maxFocus+RESOURCE_RULES.perAttribute*(v.attributes[resource.attribute]-original.attributes[resource.attribute]))},
   {name:t('allocation.accuracy'),icon:'stat-target',before:before.accuracy.toFixed(1),after:after.accuracy.toFixed(1)},
   {name:t('allocation.evasion'),icon:'stat-radius',before:before.evasion.toFixed(1),after:after.evasion.toFixed(1)},
  ];
  metrics.forEach((metric,i)=>{const y=Y(104+i*35);art(ui,metric.icon,620,y,18,20);text(ui,metric.name,675,y,80,27,14.5);pair(ui,metric.before,metric.after,y,F.color('state.selected'));if(i<4)rule(ui,723,y+15,212);});
  art(ui,'info',620,Y(287),16,17);text(ui,t('allocation.accuracyGrowth'),729,Y(287),196,36,12.5);
 }else{
  const skills=COMBAT_SKILL_LIST.filter(s=>s.style===v.family);if(!skills.some(s=>s.id===v.selected))v.selected=skills[0].id;
  const headingY=!ui.referenceLayout?a+11:54;rule(ui,298,headingY,76);rule(ui,518,headingY,76);center(ui,t('allocation.mainSkills'),408,headingY,300,22,16);const listTop=!ui.referenceLayout?a+28:72,targetH=Math.max(hu,D.skillRow.height),rowH=targetH+gap,list=ui.scroll(middle,0,ui.y((listTop+b)/2)-ui.bodyY,304*u,(b-listTop)*u,skills.length*rowH*u);list.name='AllocationSkillListContent';if(v.skillScroll)list.parent!.parent!.getComponent(ScrollView)!.scrollToOffset(new Vec2(0,v.skillScroll),0);
  skills.forEach((skill,i)=>{
   const rank=v.learned[skill.id]??0,old=original.learned[skill.id]??0,path=COMBAT_SKILL_ICONS[skill.id];
   Controls.skillRow(ui,list,{x:0,y:-targetH/2-i*rowH,height:targetH,action:'AllocationSkill:'+skill.id,run:()=>{v.selected=skill.id;refresh();},
    selected:skill.id===v.selected,changed:rank!==old,title:skill.name,
    level:rank?(old===rank?`${rank}级${skill.type==='ultimate'?'（'+t('allocation.ultimate')+'）':''}`:`${old} → ${rank}级`):t('allocation.locked',{level:skill.unlockLevel}),
    iconPath:path?'ui/combat-relief/'+path:undefined,iconName:'PreparationSkillIcon:'+skill.id});
  });
  const skill=COMBAT_SKILLS[v.selected],rank=v.learned[skill.id]??0,old=original.learned[skill.id]??0,cost=SKILL_RANK_COSTS[rank+1]??0,current=skill.ranks[Math.max(0,old-1)],preview=skill.ranks[Math.max(0,rank-1)],next=skill.ranks[rank],investment=rank*(rank-1)/2-old*(old-1)/2;
  const Y=(y:number)=>!ui.referenceLayout?a+14+(y-56)*.76:y;
  text(ui,skill.name,649,Y(66),130,34,skill.name.length>4?21:24);const level=text(ui,rank?(old===rank?`${rank}级 / 5级`:`${old}级 → ${rank}级 / 5级`):t('allocation.locked',{level:skill.unlockLevel}),777,Y(66),116,28,14,F.color('state.selected'));level.horizontalAlign=Label.HorizontalAlign.RIGHT;
  art(ui,'skill-cost',710,Y(101),176,24,true);center(ui,investment?t('allocation.upgrade',{count:investment}):rank<5?t('allocation.costShort',{count:cost}):t('allocation.maxed'),710,Y(101),170,26,16,C.gold);
  const facts=rankFacts(skill,current),after=rankFacts(skill,preview);
  facts.forEach((fact,i)=>{const y=Y(132+i*32);art(ui,fact.icon,604,y,20,20);text(ui,fact.label,662,y,80,28,15);const val=text(ui,`${fact.value}${fact.suffix} → ${after[i]?.value??fact.value}${fact.suffix}`,768,y,128,28,17,rank!==old?F.color('state.selected'):C.ink);val.horizontalAlign=Label.HorizontalAlign.RIGHT;if(i===0)rule(ui,710,y+12,238);});
  rule(ui,710,Y(180),238);const compact=skill.id==='BOW_02',summary=skill.id==='BOW_06'?t('allocation.trapSummary'):skill.id==='BOW_07'?t('allocation.retreatSummary'):'',description=resourceCostText(skill)+'\n'+skillResourceText(compact?t('allocation.bowChainSummary'):(summary?summary+'\n\n':'')+(skill.mechanic??preview.upgradeEffect??preview.evolution??'')),descH=compact?26:Math.max(42,description.split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(line.length/17)),0)*18),content=ui.scroll(right,0,ui.y(Y(205)+(!ui.referenceLayout?8:0))-ui.bodyY,244*u,42*u,descH*u),desc=ui.text(content,description,0,-descH*u/2,238*u,descH*u,C.ink,13.5*u);desc.verticalAlign=Label.VerticalAlign.TOP;desc.lineHeight=18*u;if(compact){desc.enableWrapText=false;desc.overflow=Label.Overflow.SHRINK;}
  [-1,1].forEach((delta,i)=>P.step(ui,delta<0?'−':'+',650+i*114,!ui.referenceLayout?b-hu/2-25:256,'AllocationRank:'+delta,safe&&rank>0&&(delta<0?rank>1:rank<5&&remaining>=cost),()=>{const plan={...v.learned,[skill.id]:rank+delta};if(skillPlanRemaining(original,plan)!==null){v.learned=plan;v.notice=t('allocation.preview');refresh();}},58));
  art(ui,'info',611,!ui.referenceLayout?b-10:300,16,17);text(ui,t('allocation.free'),740,!ui.referenceLayout?b-10:300,238,20,11.5,C.ink);
 }
 ui.footer(v.notice||(!safe?game.preparationAvailability().reason:pending?t('allocation.preview'):t('allocation.ready')),[{label:t('allocation.undo'),action:'AllocationUndo',enabled:pending,run:()=>{if(tab==='attributes')v.attributes={...original.attributes};else v.learned={...original.learned};v.notice='';refresh();}},{label:t(tab==='attributes'?'allocation.applyAttributes':'allocation.applySkills'),action:'AllocationApply',enabled:safe&&pending&&remaining>=0,primary:true,run:()=>{
  const ok=tab==='attributes'?game.applyAttributePlan(v.attributes,v.attributeToken):game.applySkillPlan(v.learned,v.skillToken);
  if(ok){v.attributeToken=game.attributePlanToken();v.skillToken=game.skillPlanToken();v.attributes={...game.state.progression.attributes};v.learned={...game.state.progression.learned};v.notice=t('allocation.saved');hud.actions.click('allocation-saved');}else{discardPreparationPreview(game);draft(game).notice=t('allocation.stale');refresh();}
 }},{label:t('return'),action:'close'}]);
}
