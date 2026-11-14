import {Label} from 'cc';
import {trainingText as tr} from '../locales';
import {synchronizeResource} from '../../combat/common/ClassResource';
import type {GameSession} from '../../../core/GameSession';
import {COMBAT_LOADOUTS,prepareCombatLoadout,activateCombatLoadout,type CombatFamily} from '../../progression/common/CombatLoadouts';
import {skillRankSpent,totalSkillPoints} from '../../progression/common/Progression';
import {COMBAT_SKILLS,COMBAT_SKILL_LIST,type CombatStyle} from '../../combat/data/PureSkills';
import type {Hud} from '../../../app/Hud';
import {RpgPanel} from '../../../shared/ui/RpgPanel';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {COMBAT_SKILL_ICONS} from '../../combat/runtime/CombatSkillIcons';

const NAMES:Record<CombatStyle,string>={WAR:'破军',BOW:'逐风',FIR:'烈焰',THU:'雷霆',COM:'通用'};

/** Available only in an isolated training session or the local test=max profile. */
export class SkillEffectDebug {
 private family:CombatStyle='FIR';private selected='FIR_01';private notice=tr('skillNotice');
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
   const slot=Number(command.slice(5)),skill=COMBAT_SKILLS[this.selected];
   if(!Number.isInteger(slot)||slot<0||slot>3||skill?.type!=='active'||!['COM',s.combat.family].includes(skill.style)||!p.learned[skill.id])return false;
   prepareCombatLoadout(s.combat,s.equipment.weapon,p);
   const saved=s.combat.loadouts![s.combat.family!]!,other=saved.activeSlots.indexOf(skill.id),previous=saved.activeSlots[slot];
   if(other>=0&&other!==slot)saved.activeSlots[other]=previous;
   saved.activeSlots[slot]=skill.id;activateCombatLoadout(s.combat,p);
   this.notice=tr('slotMoved',{skill:skill.name,slot:slot+1});
  }else if(command==='loadout'){
   const skill=COMBAT_SKILLS[this.selected];
   if(this.family!=='COM'){
    const family=this.family as CombatFamily,preset=COMBAT_LOADOUTS[family];
    s.equipment.weapon=preset.weapon;s.equipment.offhand=null;
    prepareCombatLoadout(s.combat,preset.weapon,p,family);
   }
   if(skill.type==='passive'){s.combat.passiveSlots=s.combat.passiveSlots.map(id=>id===skill.id?null:id) as [string|null,string|null];s.combat.passiveSlots[0]=skill.id;}
   else if(skill.type==='active'&&!s.combat.activeSlots.includes(skill.id)){s.combat.activeSlots[0]=skill.id;s.combat.loadouts![s.combat.family!].activeSlots=[...s.combat.activeSlots];}
   else if(skill.type==='ultimate'){s.combat.ultimate=skill.id;s.combat.loadouts![s.combat.family!].ultimate=skill.id;}
   this.notice=skill.type==='mobility'?tr('mobilityReady'):tr('equipped',{skill:skill.name});
  }else if(command==='refill'){
   s.player.hp=s.player.maxHp;s.player.focus=s.player.maxFocus;
   this.notice='生命与当前职业资源已补满';
  }else return false;
  synchronizeResource(s);
  // A level switch starts a clean comparison: no previous-rank cast, payload,
  // burn, shield or buff may survive and be mistaken for the new level.
  game.resetCombatTransient();s.combat.cooldowns={};s.cooldowns.dash=0;s.combat.charge=0;s.combat.ultimateLock=0;
  p.skillPoints=totalSkillPoints(p)-Object.values(p.learned).reduce((n,rank)=>n+skillRankSpent(rank),0);
  s.revision++;game.dirty=true;return true;
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
   ui.text(node,`技能 ${rank}级`,0,-cellH*.26,cellW-2*gap,ui.font*1.4,C.muted,ui.font-3).horizontalAlign=Label.HorizontalAlign.CENTER;
  });
  const skill=COMBAT_SKILLS[this.selected],rank=game.state.progression.learned[this.selected],data=skill.ranks[rank-1],titleY=h/2-gap-ui.font;
  if(skill.type==='active'){
   const slotW=(leftW-5*gap)/4;
   for(let slot=0;slot<4;slot++)ui.button(catalog,tr('moveToSlot',{slot:slot+1}),-leftW/2+gap+slotW/2+slot*(slotW+gap),-h/2+gap+ui.hit/2,slotW,'debug:slot:'+slot,true,game.state.combat.activeSlots[slot]===skill.id);
  }else ui.button(catalog,tr('equip'),0,-h/2+gap+ui.hit/2,leftW-2*gap,'debug:loadout',true,false);
  ui.text(detail,`${skill.name} · 技能${rank}级`,0,titleY,rightW-2*gap,ui.font*1.8,C.gold,ui.font+2);
  const rankW=(rightW-2*gap-4*gap)/5,rankY=titleY-ui.font-ui.hit/2-gap;
  for(let level=1;level<=5;level++)ui.button(detail,`${level}级`,-rightW/2+gap+rankW/2+(level-1)*(rankW+gap),rankY,rankW,'debug:rank:'+level,true,rank===level);
  const textTop=rankY-ui.hit/2-gap,textBottom=-h/2+gap,textH=Math.max(ui.font*2,textTop-textBottom),facts=[data.upgradeEffect??data.evolution??skill.effect??'',`施放距离 ${data.castRangeMetres}米 · 伤害 ${data.authoredDamageHits}段`,skill.type==='passive'?tr('passiveInstruction'):skill.type==='mobility'?'使用闪避按钮查看效果。':tr('activeInstruction'),'切换等级会清除上一轮技能、弹体与增益。'].join('\n\n'),contentHeight=Math.max(textH,Math.ceil(facts.length/Math.max(1,(rightW-4*gap)/ui.font))*(ui.font*1.4)+ui.font*6),scroll=ui.scroll(detail,0,(textTop+textBottom)/2,rightW-2*gap,textH,contentHeight);
  ui.text(scroll,facts,0,-contentHeight/2,rightW-4*gap,contentHeight,C.ink,ui.font-2).verticalAlign=Label.VerticalAlign.TOP;
  ui.footer(this.notice,[training?{label:'靶场设置',action:'training:settings'}:{label:'全部同级',action:'debug:all-rank'},{label:'本系同级',action:'debug:family-rank'},training?{label:'重置本轮',action:'training:reset'}:{label:'补满状态',action:'debug:refill'},{label:'继续试放',action:'close',primary:true}]);
 }
}
