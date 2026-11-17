import {Label} from 'cc';
import {trainingText as tr} from '../locales';
import {synchronizeResource} from '../../combat/common/ClassResource';
import type {GameSession} from '../../../core/GameSession';
import {COMBAT_LOADOUTS,prepareCombatLoadout,type CombatFamily} from '../../progression/common/CombatLoadouts';
import {skillRankSpent,totalSkillPoints} from '../../progression/common/Progression';
import {COMBAT_SKILLS,COMBAT_SKILL_LIST,type CombatStyle} from '../../combat/data/PureSkills';
import type {Hud} from '../../../app/Hud';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {COMBAT_SKILL_ICONS} from '../../combat/runtime/CombatSkillIcons';
import {skillRoleLabel,skillRankFacts} from '../../combat/runtime/CombatSkillDescription';

const NAMES:Record<CombatStyle,string>={WAR:'破军',BOW:'逐风',FIR:'烈焰',THU:'雷霆',COM:'通用'};

/** Available only in an isolated training session or the local test=max profile. */
export class SkillEffectDebug {
 private family:CombatStyle='FIR';private selected='FIR_01';private notice=tr('skillNotice');
 private resourcesReady=true;
 preparationFailed(){this.resourcesReady=false;this.notice=tr('skillLoadFailed');}
 handle(action:string,game:GameSession):boolean {
  const command=action.slice('debug:'.length),s=game.state,p=s.progression;
  if(command.startsWith('rank:')){
   const rank=Number(command.slice(5));if(!Number.isInteger(rank)||rank<1||rank>5)return false;
   p.learned[this.selected]=rank;this.notice=`${COMBAT_SKILLS[this.selected].name}已设为${rank}级`;
  }else if(command==='family-rank'||command==='all-rank'){
   const rank=p.learned[this.selected];
   for(const skill of COMBAT_SKILL_LIST)if(command==='all-rank'||skill.style===this.family)p.learned[skill.id]=rank;
   this.notice=`${command==='all-rank'?'全部技能':NAMES[this.family]+'本系技能'}已设为${rank}级`;
  }else if(command.startsWith('slot:')){
   // Legacy debug actions must not bypass the same fixed kit used in play.
   return false;
  }else if(command==='loadout'){
   const skill=COMBAT_SKILLS[this.selected];
   if(this.family!=='COM'){
    const family=this.family as CombatFamily,preset=COMBAT_LOADOUTS[family];
    s.equipment.weapon=preset.weapon;s.equipment.offhand=null;
    prepareCombatLoadout(s.combat,preset.weapon,p,family);
   }else prepareCombatLoadout(s.combat,s.equipment.weapon,p);
   this.notice=skill.activation==='automatic'?`${skill.name}为自动强化，请按正常条件触发`:skill.id==='COM_02'?'灵泉复苏固定在补给栏第三格':skill.type==='passive'?'职业被动固定生效，无需装配':skill.type==='mobility'?tr('mobilityReady'):`${NAMES[this.family]}固定技能栏已就绪`;
  }else if(command==='refill'){
   s.player.hp=s.player.maxHp;s.player.focus=s.player.maxFocus;
   this.notice='生命与当前职业资源已补满';
  }else return false;
  synchronizeResource(s);
  // A level switch starts a clean comparison: no previous-rank cast, payload,
  // burn, shield or buff may survive and be mistaken for the new level.
  game.resetCombatTransient();s.combat.cooldowns={};s.cooldowns.dash=0;s.combat.charge=0;s.combat.ultimateLock=0;
  p.skillPoints=totalSkillPoints(p)-Object.values(p.learned).reduce((n,rank)=>n+skillRankSpent(rank),0);
  s.revision++;game.dirty=true;this.resourcesReady=true;return true;
 }
 render(hud:Hud,game:GameSession,training=false){
  const ui=new RpgPanel(hud,game,'skills','SkillEffectDebug'),gap=ui.gap,usable=ui.width-2*ui.margin,edge=-ui.width/2+ui.margin;
  const familyW=Math.min(160,(usable*.64-4*gap)/5),familyY=ui.bodyTop-ui.hit/2;
  (Object.keys(NAMES) as CombatStyle[]).forEach((family,i)=>ui.button(ui.panel,NAMES[family],edge+familyW/2+i*(familyW+gap),familyY,familyW,'DebugFamily:'+family,true,family===this.family,ui.hit,()=>{this.family=family;this.selected=COMBAT_SKILL_LIST.find(s=>s.style===family)!.id;hud.actions.click('debug:loadout');}));
  ui.text(ui.panel,training?tr('debugTitle'):'技能效果调试 · 临时不保存',ui.width/2-ui.margin-usable*.17,familyY,usable*.34,ui.hit,F.color('state.paused'),ui.font-1).horizontalAlign=Label.HorizontalAlign.RIGHT;
  const top=ui.bodyTop-ui.hit-gap,h=top-ui.bodyBottom,y=(top+ui.bodyBottom)/2,leftW=(usable-gap)*.49,rightW=usable-leftW-gap;
  const catalog=hud.panel(ui.panel,edge+leftW/2,y,leftW,h,C.panel),detail=hud.panel(ui.panel,ui.width/2-ui.margin-rightW/2,y,rightW,h,C.dark);catalog.name='DebugSkillCatalog';detail.name='DebugSkillDetail';
  const skills=COMBAT_SKILL_LIST.filter(s=>s.style===this.family),cols=3,cellW=(leftW-2*gap-(cols-1)*gap)/cols,cellH=ui.hit+ui.font*1.4,contentH=Math.ceil(skills.length/cols)*(cellH+gap),listH=h-ui.hit-3*gap,content=ui.scroll(catalog,0,(ui.hit+gap)/2,leftW-2*gap,listH,contentH);
  skills.forEach((skill,i)=>{
   const x=-(leftW-2*gap)/2+cellW/2+(i%cols)*(cellW+gap),row=-cellH/2-Math.floor(i/cols)*(cellH+gap),rank=game.state.progression.learned[skill.id];
   const node=ui.button(content,'',x,row,cellW,'DebugSkill:'+skill.id,true,this.selected===skill.id,cellH,()=>{this.selected=skill.id;hud.actions.click('debug:loadout');});
   const iconSize=ui.hit*.42,icon=UiSkin.sprite(node,'ui/combat-relief/'+COMBAT_SKILL_ICONS[skill.id],iconSize,iconSize);icon.node.setPosition(-cellW/2+gap+iconSize/2,cellH*.13);
   ui.text(node,skill.name,iconSize/2+gap/2,cellH*.13,cellW-iconSize-3*gap,ui.font*1.6,C.ink,ui.font-2);
   ui.text(node,`${skill.activation==='automatic'?'自动强化':'技能'} ${rank}级`,0,-cellH*.26,cellW-2*gap,ui.font*1.4,C.muted,ui.font-3).horizontalAlign=Label.HorizontalAlign.CENTER;
  });
  const skill=COMBAT_SKILLS[this.selected],rank=game.state.progression.learned[this.selected],data=skill.ranks[Math.max(0,rank-1)],titleY=h/2-gap-ui.font;
  const location=skill.activation==='automatic'?'自动强化 · 按正常条件触发':skill.id==='COM_02'?'补给栏第三格':skill.type==='passive'?'职业被动 · 固定生效':skill.type==='mobility'?'独立闪避按钮':skill.type==='ultimate'?'固定终极末位':'职业技能固定位置';
  ui.text(catalog,location,0,-h/2+gap+ui.hit/2,leftW-2*gap,ui.hit,C.muted,ui.font-2).horizontalAlign=Label.HorizontalAlign.CENTER;
  ui.text(detail,`${skill.name} · 技能${rank}级`,0,titleY,rightW-2*gap,ui.font*1.8,C.gold,ui.font+2);
  const rankW=(rightW-2*gap-4*gap)/5,rankY=titleY-ui.font-ui.hit/2-gap;
  for(let level=1;level<=5;level++)ui.button(detail,`${level}级`,-rightW/2+gap+rankW/2+(level-1)*(rankW+gap),rankY,rankW,'debug:rank:'+level,true,rank===level);
  const textTop=rankY-ui.hit/2-gap,textBottom=-h/2+gap,textH=Math.max(ui.font*2,textTop-textBottom),facts=[skillRoleLabel(skill),...skillRankFacts(skill,data),data.upgradeEffect??data.evolution??skill.effect??'',skill.activation==='automatic'?'满足技能说明中的条件后自动触发，不可手动装槽或施放。':skill.type==='passive'?'使用当前职业固定被动，在正常战斗中观察效果。':skill.id==='COM_02'?'展开补给栏，使用第三格治疗技能。':skill.type==='mobility'?'使用闪避按钮查看效果。':'关闭调试页，使用当前职业固定技能按钮。','切换等级会清除上一轮技能、弹体与增益。'].join('\n\n'),contentHeight=Math.max(textH,Math.ceil(facts.length/Math.max(1,(rightW-4*gap)/ui.font))*(ui.font*1.4)+ui.font*6),scroll=ui.scroll(detail,0,(textTop+textBottom)/2,rightW-2*gap,textH,contentHeight);
  ui.text(scroll,facts,0,-contentHeight/2,rightW-4*gap,contentHeight,C.ink,ui.font-2).verticalAlign=Label.VerticalAlign.TOP;
  ui.footer(this.notice,[training?{label:'靶场设置',action:'training:settings'}:{label:'全部同级',action:'debug:all-rank'},{label:'本系同级',action:'debug:family-rank'},training?{label:'重置本轮',action:'training:reset'}:{label:'补满状态',action:'debug:refill'},this.resourcesReady?{label:'继续试放',action:'close',primary:true}:{label:tr('retrySkills'),action:'debug:loadout',primary:true}]);
 }
}
