import {skillResourceText,resourceCostText} from '../../combat/common/ClassResource';
import {Label,Node,Rect,Size,Sprite,SpriteFrame,ScrollView,Vec2} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import {skillPlanRemaining,SKILL_RANK_COSTS} from '../common/Progression';
import {COMBAT_SKILLS,COMBAT_SKILL_LIST,type CombatStyle} from '../../combat/data/PureSkills';
import {COMBAT_LOADOUTS} from '../common/CombatLoadouts';
import type {Hud} from '../../../app/Hud';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {renderCharacterStats} from '../../equipment/runtime/EquipmentPanels';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {COMBAT_SKILL_ICONS} from '../../combat/runtime/CombatSkillIcons';
import {skillRoleLabel,skillRankFacts} from '../../combat/runtime/CombatSkillDescription';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {PreparationSkin as P} from '../../../shared/ui/PreparationSkin';
import {PreparationControls as Controls} from '../../../shared/ui/PreparationControls';
import {FrameCache} from '../../../shared/assets/FrameCache';

type View={family:CombatStyle;selected:string;activeFamily?:CombatStyle;draft?:Record<string,number>;token?:string;notice?:string;scroll?:number};
const views=new WeakMap<GameSession,View>();
const NAMES:Record<CombatStyle,string>={WAR:'破军',BOW:'逐风',FIR:'烈焰',THU:'雷霆',COM:'通用'};
const iconFrames=new FrameCache();
function iconFrame(id:string,owner:Node):Promise<SpriteFrame>{
 const path='ui/combat-relief/'+COMBAT_SKILL_ICONS[id];
 return iconFrames.get(path,owner,()=>UiSkin.frame(path,0,owner).then(source=>{const r=source.rect,inset=Math.min(r.width,r.height)*.047,frame=new SpriteFrame();frame.reset({texture:source.texture,rect:new Rect(r.x+inset,r.y+inset,r.width-2*inset,r.height-2*inset),originalSize:new Size(r.width-2*inset,r.height-2*inset)});frame.packable=false;return frame;}));
}
/** The app prewarms the small skill catalog before exposing the pages. */
export async function preloadCombatSkillIcons(ids:string[],owner:Node){await Promise.all(ids.filter(id=>COMBAT_SKILL_ICONS[id]).map(id=>iconFrame(id,owner)));}
export function discardCombatSkillPreview(game:GameSession){const v=views.get(game);if(v){delete v.draft;delete v.token;v.notice='';}}
function art(ui:RpgPanel,parent:Node,id:string,x:number,y:number,w:number,h:number){const sprite=UiSkin.asset(parent,id,w*ui.scale,h*ui.scale,false);sprite.node.setPosition(x,y);return sprite;}
/** Crop the baked border on a fresh frame; shared HUD textures and their frames remain unchanged. */
function skillIcon(ui:RpgPanel,parent:Node,id:string,size:number){
 const u=ui.scale,node=ui.hud.node('CombatSkillIcon:'+id,parent,0,0,size*u,size*u),motif=ui.hud.node('SkillMotif',node,0,0,(size-3)*u,(size-3)*u),sprite=motif.addComponent(Sprite);
 sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.trim=false;
 const pending=iconFrame(id,motif),ready=iconFrames.getReady('ui/combat-relief/'+COMBAT_SKILL_ICONS[id],motif);
 if(ready)sprite.spriteFrame=ready;else void pending.then(frame=>{if(motif.isValid)sprite.spriteFrame=frame;}).catch(()=>{});
 art(ui,node,'rpg-skill-icon-frame-v6',0,0,size,size);return node;
}
function pips(ui:RpgPanel,parent:Node,x:number,y:number,rank:number,large=false){
 const node=ui.hud.node('SkillRankPips',parent,x,y,90*ui.scale,14*ui.scale),step=large?16:11;
 for(let i=0;i<5;i++)art(ui,node,i<rank?'rpg-skill-rank-on-v6':'rpg-skill-rank-off-v6',(i-2)*step*ui.scale,0,large?10:8.8,large?10:8.8);
}
export function browseCombatFamily(game:GameSession,family:string){if(!Object.prototype.hasOwnProperty.call(NAMES,family))return;const v=views.get(game);if(v){v.family=family as CombatStyle;v.selected=COMBAT_SKILL_LIST.find(s=>s.style===family)!.id;v.scroll=0;}}
export function renderCombatPanel(hud:Hud,game:GameSession,tab:'skills'|'growth'='skills'){
 if(tab==='growth'){renderCharacterStats(hud,game);return;}
 const family=game.state.combat.family??'WAR',v=views.get(game)??{family,selected:COMBAT_LOADOUTS[family].activeSlots[0]!,activeFamily:family};
 if(v.activeFamily!==family){v.family=family;v.selected=COMBAT_LOADOUTS[family].activeSlots[0]!;v.activeFamily=family;v.scroll=0;}
 v.draft={...game.state.progression.learned};v.token=game.skillPlanToken();views.set(game,v);
 const ui=new RpgPanel(hud,game,'skills','CombatPanel',true),u=ui.scale,a=ui.contentTop,b=ui.contentBottom,hu=ui.hit/u,gap=ui.gap/u,p=game.progressionView(),safe=game.preparationAvailability().available,mainBottom=b-hu-gap;
 const left=ui.column(0,190,'CombatFamilySidebar'),catalog=ui.column(198,326,'CombatSkillList'),detail=ui.column(534,310,'CombatSkillDetail');ui.drape(detail,310*u,ui.bodyHeight);
 const T=(value:string,x:number,y:number,w:number,h=25,size=14,color=C.ink)=>ui.text(ui.panel,value,ui.x(x),ui.y(y),w*u,h*u,color,size*u);
 const chooser=ui.button(ui.panel,'',ui.x(99),ui.y(a+hu/2),170*u,'CombatFamilyChooser',true,false,ui.hit,()=>hud.showList('浏览技能流派','浏览技能不会切换当前职业',Object.entries(NAMES).map(([key,name])=>({label:name,detail:key===v.family?'当前浏览':'',selected:key===v.family,action:'combat-family:'+key})),[{back:true,label:'返回技能',action:'checks'}]),'catalog');
 P.art(ui,chooser,'button-dark',0,0,170,35,true);ui.text(chooser,NAMES[v.family]+'技能 ⌄',0,0,158*u,28*u,F.color('state.selected'),17*u).horizontalAlign=Label.HorizontalAlign.CENTER;
 const motif=UiSkin.asset(ui.panel,'rpg-profession-'+(v.family==='COM'?'war':v.family.toLowerCase())+'-v1',162*u,64*u,false);motif.node.setPosition(ui.x(99),ui.y(a+hu+gap+34));
 T(`可用技能点 ${game.state.progression.skillPoints}`,99,mainBottom-40,170,25,13.5,C.gold).horizontalAlign=Label.HorizontalAlign.CENTER;
 T('固定技能栏 · 解锁后原位启用',99,mainBottom-12,170,28,11.5,C.muted).horizontalAlign=Label.HorizontalAlign.CENTER;
 const skills=COMBAT_SKILL_LIST.filter(s=>s.style===v.family),models=game.combatSkillView();if(!skills.some(s=>s.id===v.selected))v.selected=skills[0].id;
 const row=hu+gap,list=ui.scroll(catalog,0,ui.y((a+mainBottom)/2)-ui.bodyY,316*u,(mainBottom-a)*u,skills.length*row*u);list.name='CombatSkillListContent';const scroll=list.parent!.parent!.getComponent(ScrollView)!;if(v.scroll)scroll.scrollToOffset(new Vec2(0,v.scroll),0);
 skills.forEach((skill,i)=>{
  const model=models.find(m=>m.id===skill.id)!,rank=game.state.progression.learned[skill.id]??0,n=ui.button(list,'',0,(-hu/2-i*row)*u,310*u,'CombatSkill:'+skill.id,true,false,ui.hit,()=>{v.selected=skill.id;v.scroll=scroll.getScrollOffset().y;renderCombatPanel(hud,game);},'catalog');
  Controls.rowBackground(ui,n,310,hu-4,v.selected===skill.id);
  skillIcon(ui,n,skill.id,40).setPosition(-123*u,0);const title=ui.text(n,skill.name,-14*u,7*u,154*u,24*u,model.unlocked?C.ink:C.muted,16.5*u);title.enableWrapText=false;title.overflow=Label.Overflow.SHRINK;
  ui.text(n,skillRoleLabel(skill),-14*u,-15*u,154*u,18*u,C.muted,11.5*u);
  const level=ui.text(n,model.unlocked?`${rank}级`:`Lv.${model.requiredLevel}`,112*u,0,72*u,26*u,C.gold,13*u);level.horizontalAlign=Label.HorizontalAlign.RIGHT;
 });
 const skill=COMBAT_SKILLS[v.selected],model=models.find(m=>m.id===skill.id)!,rank=game.state.progression.learned[skill.id]??0,current=skill.ranks[Math.max(0,rank-1)],next=skill.ranks[rank];
 skillIcon(ui,ui.panel,skill.id,43).setPosition(ui.x(568),ui.y(a+25));T(skill.name,710,a+15,212,30,21);T(model.unlocked?`${rank}级 / 5级 · ${skillRoleLabel(skill)}`:`Lv.${model.requiredLevel} 开放`,714,a+41,218,25,13,C.gold);P.rule(ui,ui.panel,ui.x(690),ui.y(a+57),274);
 const facts=skill.mechanic??skill.effect??current.effect??current.upgradeEffect??current.evolution??'',comparison=next?.upgradeEffect??next?.evolution??(rank>=5?'已达到最高等级':''),description=[...skillRankFacts(skill,current),...(skill.type==='passive'||skill.activation==='automatic'?[]:[`冷却 ${current.cooldownSeconds}秒`]),resourceCostText(skill),'',skillResourceText(facts+(comparison?'\n\n下一阶：'+comparison:''))].join('\n'),descriptionH=Math.max(48,description.split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(line.length/18)),0)*18+8),content=ui.scroll(detail,0,ui.y((a+66+mainBottom)/2)-ui.bodyY,284*u,(mainBottom-a-66)*u,descriptionH*u),label=ui.text(content,description,0,-descriptionH*u/2,274*u,descriptionH*u,C.ink,13*u);label.verticalAlign=Label.VerticalAlign.TOP;label.lineHeight=18*u;
 const shownFamily=v.family==='COM'?family:v.family,preset=COMBAT_LOADOUTS[shownFamily],slots=[...preset.activeSlots.map((id,i)=>({id,title:['单','进','辅','群'][i]})),{id:preset.ultimate,title:'终'},{id:shownFamily+'_P1',title:'被1'},{id:shownFamily+'_P2',title:'被2'}];
 P.rule(ui,ui.panel,0,ui.y(b-hu-gap/2),806);T('职业固定配置',99,b-hu/2,170,26,15,C.gold).horizontalAlign=Label.HorizontalAlign.CENTER;
 slots.forEach((slot,i)=>{const x=212+i*(hu+gap+16),n=hud.node('CombatFixedSlot:'+i,ui.panel,ui.x(x),ui.y(b-hu/2),ui.hit,ui.hit),unlocked=models.find(m=>m.id===slot.id)?.unlocked;if(slot.id&&unlocked)skillIcon(ui,n,slot.id,42);else Controls.cardBackground(ui,n,42,42);P.badge(ui,n,slot.title,16*u,-17*u,slot.title.length>1?36:24,'gold',14);});
 ui.footer(safe?'技能位置固定 · 强化自动触发 · 灵泉复苏在补给栏':game.preparationAvailability().reason,[{label:'职业选择',action:'combat-loadout:'+(v.family==='COM'?family:v.family)},{label:'技能加点',action:'allocation-skill:'+skill.id,primary:true},{label:'返回旅途',action:'close'}]);
}
