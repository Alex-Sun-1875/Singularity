import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {Color,EventTouch,Graphics,Label,Node,UITransform,ButtonComponent as Button,Sprite,sys} from 'cc';
import type {DiceView} from '../../progression/common/SkillChecks';
import {bonusText} from '../../equipment/common/EquipmentDice';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {EquipmentArt} from '../../equipment/runtime/EquipmentArt';
import {Hud} from '../../../app/Hud';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UiChrome} from '../../../shared/ui/UiChrome';
import {equipmentTypeName} from '../../equipment/runtime/EquipmentPresentation';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {RpgPanel} from '../../../shared/ui/RpgPanel';

const DURATION=1;
const T={surface:C.panel,felt:new Color(21,15,10),edge:C.line,gold:C.gold,text:C.ink,muted:C.muted,quiet:F.color('text.disabled'),green:F.color('state.success'),red:F.color('state.failure'),ink:C.dark};
type Point={x:number;y:number;z:number};
type Die={node:Node;graphics:Graphics;face:Label;marks:Label[];caption:Label;radius:number;index:number;cube:boolean;body?:Node;art?:Sprite};
type Control={node:Node;visual:Node;graphics:Graphics;label:Label;enabled:boolean;primary:boolean;title:string;w:number;h:number;pressed:boolean;hover:boolean;selected:boolean};
const PHI=(1+Math.sqrt(5))/2;
const UNIT:Point[]=[[-1,PHI,0],[1,PHI,0],[-1,-PHI,0],[1,-PHI,0],[0,-1,PHI],[0,1,PHI],[0,-1,-PHI],[0,1,-PHI],[PHI,0,-1],[PHI,0,1],[-PHI,0,-1],[-PHI,0,1]].map(([x,y,z])=>{const l=Math.hypot(x,y,z);return{x:x/l,y:y/l,z:z/l};});
const FACES=[[0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],[1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],[3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],[4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1]];
const dot=(a:Point,b:Point)=>a.x*b.x+a.y*b.y+a.z*b.z;
const cross=(a:Point,b:Point):Point=>({x:a.y*b.z-a.z*b.y,y:a.z*b.x-a.x*b.z,z:a.x*b.y-a.y*b.x});
const normal=(v:Point):Point=>{const l=Math.hypot(v.x,v.y,v.z);return{x:v.x/l,y:v.y/l,z:v.z/l};};
const FRONT=normal({x:UNIT[0].x+UNIT[11].x+UNIT[5].x,y:UNIT[0].y+UNIT[11].y+UNIT[5].y,z:UNIT[0].z+UNIT[11].z+UNIT[5].z});
const UP=normal({x:UNIT[0].x-FRONT.x*dot(UNIT[0],FRONT),y:UNIT[0].y-FRONT.y*dot(UNIT[0],FRONT),z:UNIT[0].z-FRONT.z*dot(UNIT[0],FRONT)}),RIGHT=cross(UP,FRONT);
const VERTICES=UNIT.map(v=>({x:dot(v,RIGHT),y:dot(v,UP),z:dot(v,FRONT)}));
const CUBE:Point[]=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]].map(([x,y,z])=>({x:x*.64,y:y*.64,z:z*.64}));
const CUBE_FACES=[[4,5,6,7],[5,1,2,6],[7,6,2,3],[1,0,3,2],[0,4,7,3],[0,1,5,4]];
const signed=(n:number)=>`${n>=0?'+':'−'}${Math.abs(n)}`;
const alpha=(c:Color,a:number)=>new Color(c.r,c.g,c.b,a);

/** Native Cocos presentation; deterministic rewards and ownership live in core. */
export class DicePanel {
 private host:Node|null=null;private current:DiceView|null=null;
 private dice:Die[]=[];private controls:Control[]=[];
 private status:Label|null=null;private formula:Label|null=null;private outcome:Label|null=null;
 private rewardHost:Node|null=null;
 private elapsed=DURATION;private builtWidth=0;private builtHeight=0;
 constructor(private readonly hud:Hud){}
 get busy(){return this.elapsed<DURATION&&this.ownsModal();}
 show(view:DiceView):void {
  const previous=this.current,owned=this.ownsModal(),same=owned&&previous?.id===view.id&&previous.roll?.attempt===view.roll?.attempt;
  const newRoll=owned&&previous?.id===view.id&&!!view.roll&&(!previous.roll||previous.roll.attempt!==view.roll.attempt);
  this.elapsed=same&&this.elapsed<DURATION?this.elapsed:newRoll?0:DURATION;this.current=view;this.destroyOwned();this.hud.clearModal();
  this.builtWidth=this.hud.width;this.builtHeight=this.hud.height;
  const narrow=this.hud.width<760,w=Math.max(48,Math.min(sys.isMobile?1440:1160,this.hud.width-(narrow?24:56))),h=Math.max(80,Math.min(648,this.hud.height-44));
  const host=this.hud.node('DiceModal',this.hud.modal,0,0,this.hud.width,this.hud.height);this.host=host;
  const shade=this.hud.node('DiceShade',host,0,0,this.hud.width,this.hud.height),g=shade.addComponent(CompactGraphics);g.fillColor=new Color(12,8,5,238);g.rect(-this.hud.width/2,-this.hud.height/2,this.hud.width,this.hud.height);g.fill();
  for(const event of [Node.EventType.TOUCH_START,Node.EventType.TOUCH_MOVE,Node.EventType.TOUCH_END,Node.EventType.TOUCH_CANCEL])shade.on(event,(e:EventTouch)=>{e.propagationStopped=true;});
  const panel=this.hud.panel(host,0,0,w,h,T.surface);panel.name='DiceFrame';const leather=panel.getChildByName('Skin:ui/quiet-bronze/leather-inset-v8')?.getComponent(Sprite);if(leather)leather.color=new Color(255,255,255,65);
  if(narrow){this.rotation(panel,w,h,view);this.refresh();return;}
  this.landscape(panel,w,h,view);this.refresh();
 }
 private landscape(panel:Node,w:number,h:number,view:DiceView){
  if(view.gear){this.equipmentLayout(panel,w,h,view);return;}
  const sy=h/648,y=(v:number)=>v*sy,pad=38,left=-w/2+pad,right=w/2-pad,split=left+(w-pad*2)*.6,stageW=split-left-28,detail=split+30,detailW=right-detail,center=left+stageW/2,font=sys.isMobile?1.5:1;
  this.label(panel,'旅 途 事 件  /  '+view.skillLabel,left,y(290),w-240,13*font,T.gold,26*sy);
  this.label(panel,`余烬 ${view.inspiration} / 4`,right-170,y(290),170,14*font,T.muted,26*sy,Label.HorizontalAlign.RIGHT);
  this.label(panel,view.title,left,y(246),w-76,32*font,T.gold,50*sy);
  this.label(panel,view.prompt,left,y(196),w-76,17*font,T.text,55*sy);this.line(panel,left,y(160),right,y(160),alpha(T.edge,130));
  const tray=this.hud.node('LeatherDiceTray',panel,center,y(-27),stageW,356*sy);this.tray(tray,stageW,356*sy);
  this.status=this.label(panel,'',left+12,y(127),stageW-24,23*font,T.gold,36*sy,Label.HorizontalAlign.CENTER);
  this.label(panel,view.mode==='advantage'?'线索充分 · 两骰择高':view.mode==='disadvantage'?'局势不利 · 两骰取低':'掷骰点数 + 行动准备达到目标',left+12,y(92),stageW-24,14*font,T.muted,28*sy,Label.HorizontalAlign.CENTER);
  const count=view.mode==='normal'?1:2,radius=Math.min(count===1?104:91,stageW/(count===1?3:5))*sy;
  for(let i=0;i<count;i++){const x=center+(i-(count-1)/2)*stageW/2.45,node=this.hud.node(`D20-${i}`,panel,x,y(-22),radius*2.8,radius*2.8),graphics=node.addComponent(CompactGraphics),face=this.dieLabel(node,`DieFace-${i}`,radius,55),marks=Array.from({length:19},(_,j)=>this.dieLabel(node,`Facet-${i}-${j+1}`,radius,26)),caption=this.label(panel,'',x-stageW/(count*2),y(-141),stageW/count,14*font,T.muted,28*sy,Label.HorizontalAlign.CENTER);this.dice.push({node,graphics,face,marks,caption,radius,index:i,cube:false});}
  this.formula=this.label(panel,'',left+10,y(-184),stageW-20,18*font,T.muted,38*sy,Label.HorizontalAlign.CENTER);
  this.line(panel,split,y(137),split,y(-202),alpha(T.edge,85));this.actionDetails(panel,detail,detailW,sy,view,font);this.footer(panel,w,sy,view);
 }
 private equipmentLayout(panel:Node,w:number,h:number,view:DiceView){
  const sy=h/648,y=(v:number)=>v*sy,f=view.gear!,item=EQUIPMENT[f.item],font=sys.isMobile?1.45:1,left=-w/2+46,content=w-92,artCenter=-w*.225,right=w*.235,rightW=w*.4;
  this.label(panel,'战 利 品  /  余 火 锻 印',left,y(286),content,13*font,T.gold,26*sy,Label.HorizontalAlign.CENTER);
  this.label(panel,item.name,left,y(243),content,34*font,T.gold,52*sy,Label.HorizontalAlign.CENTER);
  this.label(panel,'基础装备保底 · 每件一次免费机遇',left,y(199),content,16*font,T.muted,30*sy,Label.HorizontalAlign.CENTER);
  this.line(panel,left,y(173),left+content,y(173),alpha(T.edge,130));
  const halo=this.hud.node('EquipmentSpotlight',panel,artCenter,y(20),w*.46,300*sy),g=halo.addComponent(CompactGraphics);
  for(let i=18;i>0;i--){g.fillColor=new Color(160,104,38,4);g.ellipse(0,2,(45+i*7)*Math.min(1,w/1160),(38+i*6)*sy);g.fill();}
  g.strokeColor=alpha(T.gold,50);g.lineWidth=1;g.ellipse(0,-116*sy,143,21*sy);g.stroke();
  const crest=this.hud.node('EngravedArtifactSetting',halo,0,0,290,290*sy);UiChrome.circleOrnament(crest,132,.8);
  const art=this.hud.node('EquipmentHero:'+item.id,panel,artCenter,y(24),260,270*sy);EquipmentArt.paintedIcon(art,item,252,268*sy);
  this.label(panel,'已 获 得',artCenter-w*.22,y(166),w*.44,13*font,T.muted,26*sy,Label.HorizontalAlign.CENTER);
  this.label(panel,`${item.quality} · ${equipmentTypeName(item)}`,artCenter-w*.22,y(-130),w*.44,17*font,T.gold,32*sy,Label.HorizontalAlign.CENTER);
  const descriptionW=w*.44,descriptionSize=Math.max(14*font,12*this.hud.height/390),descriptionH=Math.max(62*sy,(Math.ceil(item.description.length/(descriptionW/descriptionSize))+1)*descriptionSize*1.3),description=RpgPanel.scroll(this.hud,panel,artCenter,y(-173),descriptionW,62*sy,descriptionH,this.hud.height/390);
  this.label(description,item.description,-descriptionW/2,-descriptionH/2,descriptionW,descriptionSize,T.muted,descriptionH,Label.HorizontalAlign.CENTER);
  this.line(panel,w*.055,y(142),w*.055,y(-199),alpha(T.edge,90));
  this.status=this.label(panel,'',right-rightW/2,y(142),rightW,23*font,T.gold,38*sy,Label.HorizontalAlign.CENTER);
  const radius=(sys.isMobile?83:79)*sy,node=this.hud.node('D20-0',panel,right,y(26),radius*2.8,radius*2.8),graphics=node.addComponent(CompactGraphics),face=this.dieLabel(node,'DieFace-0',radius,48),marks=Array.from({length:5},(_,j)=>this.dieLabel(node,'Facet-0-'+j,radius,26)),caption=this.label(panel,'',right-rightW/2,y(-84),rightW,14*font,T.muted,28*sy,Label.HorizontalAlign.CENTER),die:Die={node,graphics,face,marks,caption,radius,index:0,cube:true};this.runeArt(die);this.dice.push(die);
  this.formula=this.label(panel,'',right-rightW/2,y(-126),rightW,17*font,T.text,66*sy,Label.HorizontalAlign.CENTER);
  if(!view.roll){
   const upgrade=f.possibleUpgrade?`6 · 升格为更高品质的同部位装备`:'6 · 强效精铸，追加更多属性';
   this.label(panel,upgrade,right-rightW/2,y(-179),rightW,13*font,T.gold,40*sy,Label.HorizontalAlign.CENTER);
  }else if(f.outcome?.upgrade&&!f.upgradeOwned){
   this.rewardHost=this.hud.node('UpgradeDrop',panel,right,y(-180),rightW,60*sy);const upgrade=EQUIPMENT[f.outcome.upgrade],icon=this.hud.node('UpgradeIcon',this.rewardHost,-rightW/2+32,0,58,58*sy);EquipmentArt.paintedIcon(icon,upgrade,56,56*sy);
   this.label(this.rewardHost,'额外发现 · '+upgrade.quality,-rightW/2+74,14*sy,rightW-80,12*font,T.gold,24*sy);this.label(this.rewardHost,upgrade.name,-rightW/2+74,-12*sy,rightW-80,17*font,T.text,32*sy);
  }else if(view.roll)this.label(panel,f.upgradeOwned&&f.outcome?.upgrade?'升格装备已拥有，铸印属性照常追加':'确认后，穿戴这件装备即可生效',right-rightW/2,y(-184),rightW,12*font,T.muted,30*sy,Label.HorizontalAlign.CENTER);
  this.footer(panel,w,sy,view);
 }
 private footer(panel:Node,w:number,sy:number,view:DiceView){
  const left=-w/2+40,available=w-80,y=(v:number)=>v*sy,mobile=sys.isMobile,gap=Math.max(12,8*this.hud.height/390);
  this.line(panel,left,y(-222),left+available,y(-222),alpha(T.edge,135));
  const actions:{title:string;action:string;width:number;primary:boolean}[]=[];
  if(view.canCancel)actions.push({title:view.gear?'直接收下原装':'暂且离开',action:'dice:cancel',width:available*.26,primary:false});
  if(view.roll&&view.canReroll)actions.push({title:`1 余烬重掷（余 ${view.inspiration}）`,action:'dice:reroll',width:available*.43,primary:false});
  actions.push({title:view.roll?view.gear?'收下装备与铸印':'确认行动结果':view.gear?'摇骰，追加铸印':'掷骰，付诸行动',action:view.roll?'dice:continue':'dice:roll',width:available-actions.reduce((n,a)=>n+a.width,0)-gap*actions.length,primary:true});
  let x=left;for(const a of actions){this.control(panel,a.title,x+a.width/2,y(-276),a.width,(mobile?94:72)*sy,a.action,a.primary);x+=a.width+gap;}
 }
 private actionDetails(panel:Node,left:number,w:number,sy:number,view:DiceView,font:number){
  const y=(v:number)=>v*sy;
  this.label(panel,view.skillLabel+' · 行动',left,y(134),w-84,23*font,T.text,38*sy);
  this.label(panel,'所需点数',left+w-84,y(146),84,12*font,T.muted,24*sy,Label.HorizontalAlign.RIGHT);
  const dc=this.label(panel,String(view.dc),left+w-84,y(112),84,37,T.gold,48*sy,Label.HorizontalAlign.RIGHT);dc.fontFamily='Georgia';
  this.label(panel,'准备带来的帮助',left,y(84),w,13*font,T.muted,28*sy);
  const columns=view.modifiers.length>4?2:1,rows=Math.max(1,Math.ceil(view.modifiers.length/columns)),cell=(w-12)/columns,rowH=Math.min(31,105/rows);
  view.modifiers.forEach((m,i)=>{const col=Math.floor(i/rows),row=i%rows,x=left+col*(cell+12);this.label(panel,m.label,x,y(51-row*rowH),cell-48,17*font,T.text,rowH*sy);this.label(panel,signed(m.value),x+cell-48,y(51-row*rowH),48,19,T.gold,rowH*sy,Label.HorizontalAlign.RIGHT);});
  if(!view.roll){
   if(view.help)this.control(panel,`${view.help.enabled?'已采用':'采用线索'} · ${view.help.label}\n额外获得 1—4 点准备`,left+w/2,y(-104),w,76*sy,'dice:help',false,view.help.enabled);
   else this.label(panel,'没有额外线索\n也可以直接尝试，另寻转机。',left,y(-100),w,16*font,T.muted,72*sy);
   this.label(panel,`行动把握  ${Math.round(view.chance*100)}%`,left,y(-181),w,19*font,T.gold,36*sy);
  }else this.outcome=this.label(panel,'',left,y(-115),w,17*font,T.text,150*sy);
 }
 private rotation(panel:Node,w:number,h:number,view:DiceView){
  const sy=h/648,left=-w/2+20,width=Math.max(8,w-40);
  this.label(panel,view.gear?'装 备 锻 印':'旅 途 事 件',left,276*sy,width,14,T.gold,26*sy,Label.HorizontalAlign.CENTER);
  this.label(panel,view.title,left,223*sy,width,25,T.text,68*sy,Label.HorizontalAlign.CENTER);
  this.label(panel,'请旋转到横屏',left,148*sy,width,25,T.gold,42*sy,Label.HorizontalAlign.CENTER).node.name='RotateForDice';
  this.label(panel,'装备与已掷点数都会留在这里',left,104*sy,width,15,T.muted,46*sy,Label.HorizontalAlign.CENTER);
  const count=view.gear?1:view.mode==='normal'?1:2,radius=Math.max(3,Math.min(90,width/(count*2.6)))*sy;
  for(let i=0;i<count;i++){const x=(i-(count-1)/2)*width/count,node=this.hud.node(`D20-${i}`,panel,x,-5*sy,radius*2.8,radius*2.8),graphics=node.addComponent(CompactGraphics),face=this.dieLabel(node,`DieFace-${i}`,radius,view.gear?36:52),marks=Array.from({length:view.gear?5:19},(_,j)=>this.dieLabel(node,`Facet-${i}-${j+1}`,radius,20)),caption=this.label(panel,'',x-width/count/2,-100*sy,width/count,13,T.muted,26*sy,Label.HorizontalAlign.CENTER);this.dice.push({node,graphics,face,marks,caption,radius,index:i,cube:!!view.gear});}
  this.status=this.label(panel,'',left,-151*sy,width,23,T.text,38*sy,Label.HorizontalAlign.CENTER);
  this.formula=this.label(panel,'',left,-196*sy,width,16,T.muted,55*sy,Label.HorizontalAlign.CENTER);
  this.label(panel,view.gear?'横屏后可继续追加铸印或收下装备':`目标 ${view.dc}  ·  余烬 ${view.inspiration}`,left,-246*sy,width,16,T.gold,38*sy,Label.HorizontalAlign.CENTER);
  if(view.canCancel)this.control(panel,view.gear?'直接收下原装':'暂且离开',0,-286*sy,Math.max(24,w-40),48*sy,'dice:cancel',false);
 }
 update(dt:number){if(!this.current)return;if(!this.ownsModal()){this.current=null;this.host=null;this.dice=[];this.controls=[];this.elapsed=DURATION;return;}if(this.hud.width!==this.builtWidth||this.hud.height!==this.builtHeight){this.show(this.current);return;}if(!this.busy)return;this.elapsed=Math.min(DURATION,this.elapsed+Math.max(0,Number.isFinite(dt)?dt:0));this.refresh();}
 clear(){this.destroyOwned();this.current=null;this.elapsed=DURATION;}
 private ownsModal(){return !!this.host&&this.host.isValid&&this.host.parent===this.hud.modal;}
 private destroyOwned(){if(this.host?.isValid){if(this.host.parent===this.hud.modal&&this.hud.modal.children.every(n=>n===this.host))this.hud.clearModal();else this.host.destroy();}this.host=null;this.dice=[];this.controls=[];this.status=null;this.formula=null;this.outcome=null;this.rewardHost=null;}
 private refresh(){
  const v=this.current;if(!v)return;const rolling=this.busy,r=v.roll,gear=v.gear,color=!r||rolling?T.gold:gear?T.gold:r.success?T.green:T.red;
  if(this.status){this.status.string=rolling?gear?'余火淬炼中…':'骰子转动中…':gear?!r?'一次锻印，更多可能':gear.outcome!.name+' · 铸印揭晓':!r?'准备就绪，付诸行动':r.critical==='success'?'绝妙时机':r.critical==='failure'?'局势生变':r.success?'行动达成':'另寻转机';this.status.color=color;}
  if(this.formula){this.formula.string=rolling?gear?'额外属性即将揭晓':'让骰子落定…':gear?!r?'1 · 原装保留    2—5 · 属性追加':bonusText(gear.bonus)||'保留原有品质与效果':r?`${r.kept} ${signed(r.bonus)}${r.assist?` ${signed(r.assist)} 线索`:''} = ${r.total} / ${v.dc}`:'一点意外，也可能改变旅途。';this.formula.color=r&&!rolling?color:T.muted;}
  if(this.outcome){this.outcome.string=rolling?'行动的结果即将揭晓。':r!.success?v.successText:v.failureText;this.outcome.color=rolling?T.muted:T.text;}
  if(this.rewardHost)this.rewardHost.active=!rolling;
  for(const die of this.dice){const kept=!!gear||!r||rolling||die.index===r.keptIndex,face=r?.faces[die.index]??(gear?6:20);die.face.string=String(rolling?1+(Math.floor(this.elapsed*29)+die.index*7)%(gear?6:20):face);
   die.caption.string=rolling?'':gear?!r?'六面锻造骰 · 免费':`掷出 ${face} 点`:!r?'等待投掷':this.dice.length===1?'掷骰点数':kept?'采用此骰':'略过此骰';die.caption.color=kept?T.muted:T.quiet;this.drawDie(die,face,kept,rolling);}
  for(const c of this.controls){c.label.string=rolling&&c.primary?'铸印揭晓中…':c.title;this.paintControl(c,c.enabled&&!rolling);}
 }
 private drawDie(die:Die,face:number,kept:boolean,rolling:boolean){
  if(die.art?.spriteFrame){this.drawRuneArt(die,rolling);return;}
  const g=die.graphics,r=die.radius;g.clear();
  const t=Math.min(1,this.elapsed/DURATION),spin=rolling?Math.pow(1-t,3):0,bounce=rolling?Math.abs(Math.sin(t*Math.PI*3))*Math.pow(1-t,2)*r*.45:0;
  for(let i=8;i>0;i--){g.fillColor=new Color(0,0,0,8+i*2);g.ellipse(6,-r*.83,r*(.68+i*.038),r*(.12+i*.012));g.fill();}
  const ax=(die.cube?-.28:.05)+spin*Math.PI*5,ay=(die.cube?-.36:-.12)+spin*Math.PI*6,az=(die.index%2? .07:-.09)+spin*Math.PI*2,cx=Math.cos(ax),sx=Math.sin(ax),cy=Math.cos(ay),sy=Math.sin(ay),cz=Math.cos(az),sz=Math.sin(az);
  const vertices=(die.cube?CUBE:VERTICES).map(v=>{const y=v.y*cx-v.z*sx,z=v.y*sx+v.z*cx,x=v.x*cy+z*sy,zz=-v.x*sy+z*cy;return{x:x*cz-y*sz,y:x*sz+y*cz,z:zz};});
  const project=(p:Point):Point=>{const perspective=4.8/(4.8-p.z);return{x:p.x*r*perspective,y:p.y*r*perspective+bounce,z:p.z};};
  const surfaces=(die.cube?CUBE_FACES:FACES).map((indices,index)=>{const points=indices.map(i=>vertices[i]),[a,b,c]=points,n=normal(cross({x:b.x-a.x,y:b.y-a.y,z:b.z-a.z},{x:c.x-a.x,y:c.y-a.y,z:c.z-a.z}));return{index,points:points.map(project),n,z:points.reduce((s,p)=>s+p.z,0)/points.length};}).filter(f=>f.n.z>.025).sort((a,b)=>a.z-b.z);
  for(const mark of [die.face,...die.marks])mark.node.active=false;
  for(const s of surfaces){
   const light=Math.max(0,-s.n.x*.45+s.n.y*.65+s.n.z*.62),dim=kept?1:.38,shade=.38+.62*Math.min(1,light);
   const cube=die.cube,base=cube?new Color(126+112*shade,117+108*shade,92+104*shade):new Color(126+112*shade,117+108*shade,92+104*shade);
   const center={x:s.points.reduce((n,p)=>n+p.x,0)/s.points.length,y:s.points.reduce((n,p)=>n+p.y,0)/s.points.length,z:0};
   this.polygon(g,s.points,new Color(base.r*dim,base.g*dim,base.b*dim),cube?new Color(172*dim,145*dim,91*dim):new Color(89*dim,76*dim,48*dim),1.2);
   const inset=s.points.map(p=>({x:center.x+(p.x-center.x)*.94,y:center.y+(p.y-center.y)*.94,z:p.z}));
   this.polygon(g,inset,new Color(base.r*dim,base.g*dim,base.b*dim),new Color(255,237,189,Math.round((cube?50:125)*shade*dim)),.7);
   // Small polished bevels catch the same upper-left key light as the enamel.
   for(let i=0;i<inset.length;i++){const a=inset[i],b=inset[(i+1)%inset.length];g.strokeColor=new Color(255,241,204,Math.round((b.x-a.x+b.y-a.y>0?95:24)*shade*dim));g.lineWidth=cube?2:1.3;g.moveTo(a.x,a.y);g.lineTo(b.x,b.y);g.stroke();}
   if(cube){const inner=inset.map(p=>({x:center.x+(p.x-center.x)*.81,y:center.y+(p.y-center.y)*.81,z:p.z}));this.polygon(g,inner,new Color(base.r*.84*dim,base.g*.84*dim,base.b*.84*dim),new Color(195,167,108,Math.round(72*s.n.z)),.8);}
   const label=s.index===0?die.face:die.marks[s.index-1];if(!label||s.n.z<(cube?.5:.38))continue;
   const a=s.points[0],b=s.points[1],edge=Math.hypot(b.x-a.x,b.y-a.y),size=cube?r*.45:s.index===0?r*.56:r*.28;
   label.node.active=true;label.node.setPosition(center.x,center.y+(cube?0:-r*.035));label.fontSize=size;label.lineHeight=size*1.2;
   label.node.setScale(Math.max(.35,s.n.z),1,1);label.node.setRotationFromEuler(0,0,s.index===0?az*180/Math.PI:Math.atan2(b.y-a.y,b.x-a.x)*180/Math.PI+(cube?0:120));
   if(s.index!==0)label.string=cube?String(1+(face-1+s.index)%6):String(1+(face-1+s.index*7)%20);
   label.color=new Color(52*dim,47*dim,33*dim);label.node.getComponent(UITransform)!.setContentSize(Math.max(20,edge*.8),Math.max(20,r*.9));
  }
 }
 private runeArt(die:Die){
  const r=die.radius,body=this.hud.node('PolishedRuneBody',die.node,0,0,r*2,r*2);die.body=body;
  die.art=UiSkin.sprite(body,'ui/dice/ivory-bronze-v1',r*1.9,r*2.02);die.face.node.setParent(body);die.face.fontFamily='Georgia';
  void UiSkin.frame('ui/dice/ivory-bronze-v1',0,die.node).then(()=>{if(this.ownsModal())this.refresh();}).catch(()=>{});
 }
 private drawRuneArt(die:Die,rolling:boolean){
  const g=die.graphics,r=die.radius;g.clear();const t=Math.min(1,this.elapsed/DURATION),remaining=rolling?Math.pow(1-t,2):0,bounce=rolling?Math.abs(Math.sin(t*Math.PI*3))*Math.pow(1-t,2)*r*.6:0;
  for(let i=8;i>0;i--){g.fillColor=new Color(0,0,0,8+i*2);g.ellipse(3,-r*.98,r*(.67+i*.035)*(1-bounce/(r*3)),r*(.07+i*.01));g.fill();}
  const pose=die.index%2?3:-4,turn=pose+remaining*720*(die.index%2?-1:1),squash=rolling?1-.18*Math.abs(Math.sin(t*Math.PI*7))*(1-t):1;
  die.body!.setPosition(0,bounce);die.body!.setRotationFromEuler(0,0,turn);die.body!.setScale(squash,1,1);
  die.face.node.active=true;die.face.node.setPosition(-r*.13,-r*.22);die.face.node.setRotationFromEuler(0,0,0);die.face.node.setScale(1,1,1);die.face.fontSize=r*.55;die.face.lineHeight=r*.8;die.face.color=new Color(74,47,25);die.face.node.getComponent(UITransform)!.setContentSize(r*1.3,r*1.15);
  for(const mark of die.marks)mark.node.active=false;
 }
 private dieLabel(parent:Node,name:string,r:number,size:number){const l=this.hud.text(parent,'',0,0,r*1.6,size,T.gold,r);l.node.name=name;l.horizontalAlign=Label.HorizontalAlign.CENTER;l.fontFamily='Georgia';l.isBold=true;return l;}
 private control(parent:Node,title:string,x:number,y:number,w:number,h:number,action:string,primary:boolean,selected=false):Control {
  const unit=this.hud.height/390,visualH=Math.min(h,(action==='dice:help'?48:32)*unit),node=this.hud.node(action,parent,x,y,w,h),visual=this.hud.node('ControlSurface',node,0,0,w,visualH);UiSkin.asset(visual,primary?'rpg-button-gold-v3':'rpg-button-dark-v3',w,visualH);const graphics=this.hud.node('ControlTone',visual,0,0,w,visualH).addComponent(CompactGraphics),button=node.addComponent(Button);button.transition=Button.Transition.NONE;
  const label=this.label(visual,title,-w/2+14,0,w-28,action.startsWith('dice:hold')?13:sys.isMobile?24:action==='dice:help'?15:20,T.text,visualH-4,Label.HorizontalAlign.CENTER);
  const c:Control={node,visual,graphics,label,enabled:true,primary,title,w,h:visualH,pressed:false,hover:false,selected};this.controls.push(c);
  node.on(Button.EventType.CLICK,()=>{if(c.enabled&&!this.busy)this.hud.actions.click(action);});
  for(const [event,pressed]of [[Node.EventType.TOUCH_START,true],[Node.EventType.TOUCH_END,false],[Node.EventType.TOUCH_CANCEL,false]] as const)node.on(event,()=>{c.pressed=pressed;this.paintControl(c,c.enabled&&!this.busy);});
  node.on(Node.EventType.MOUSE_ENTER,()=>{c.hover=true;this.paintControl(c,c.enabled&&!this.busy);});node.on(Node.EventType.MOUSE_LEAVE,()=>{c.hover=false;this.paintControl(c,c.enabled&&!this.busy);});return c;
 }
 private paintControl(c:Control,enabled:boolean){
  c.node.getComponent(Button)!.interactable=enabled;const g=c.graphics;g.clear();const {w,h}=c,pressed=enabled&&c.pressed,hover=enabled&&c.hover;
  g.fillColor=!enabled?new Color(0,0,0,130):pressed?new Color(0,0,0,90):hover?new Color(225,175,80,28):c.primary||c.selected?new Color(168,108,32,24):new Color(0,0,0,20);g.roundRect(-w/2+5,-h/2+5,w-10,h-10,3);g.fill();
  if(c.primary||c.selected){g.lineWidth=1;g.strokeColor=alpha(T.gold,enabled?195:55);g.roundRect(-w/2+4,-h/2+4,w-8,h-8,3);g.stroke();}
  c.label.color=enabled?c.primary?T.ink:T.text:T.quiet;
 }
 private tray(parent:Node,w:number,h:number){
  const g=parent.addComponent(CompactGraphics),cut=21,shape=[{x:-w/2+cut,y:h/2,z:0},{x:w/2-cut,y:h/2,z:0},{x:w/2,y:h/2-cut,z:0},{x:w/2,y:-h/2+cut,z:0},{x:w/2-cut,y:-h/2,z:0},{x:-w/2+cut,y:-h/2,z:0},{x:-w/2,y:-h/2+cut,z:0},{x:-w/2,y:h/2-cut,z:0}];
  this.polygon(g,shape,T.felt,alpha(T.edge,65),1);
  for(let i=12;i>0;i--){g.fillColor=new Color(117,75,31,3);g.ellipse(-w*.09,12,w*(.15+i*.022),h*(.14+i*.018));g.fill();}
  // Deterministic, static felt fibres; no texture download or per-frame noise.
  g.strokeColor=new Color(178,145,96,6);g.lineWidth=.6;for(let i=0;i<450;i++){const x=-w/2+26+(i*73.17%(w-52)),y=-h/2+24+(i*31.71%(h-48));g.moveTo(x,y);g.lineTo(x+2,y+1);g.stroke();}
  g.strokeColor=alpha(T.gold,35);g.lineWidth=1;g.ellipse(0,-h*.12,w*.42,h*.25);g.stroke();
 }
 private polygon(g:Graphics,points:Point[],fill:Color,stroke:Color,width:number){g.fillColor=fill;g.strokeColor=stroke;g.lineWidth=width;points.forEach((p,i)=>i?g.lineTo(p.x,p.y):g.moveTo(p.x,p.y));g.close();g.fill();g.stroke();}
 private label(parent:Node,value:string,left:number,y:number,w:number,size:number,color:Color,h:number,align=Label.HorizontalAlign.LEFT){const actual=Math.max(size,12*this.hud.height/390),l=this.hud.text(parent,value,left+w/2,y,Math.max(1,w),actual,color,Math.max(h,actual*1.3));applyRpgFont(l);l.horizontalAlign=align;l.lineHeight=actual*1.3;l.overflow=Label.Overflow.CLAMP;l.enableWrapText=true;return l;}
 private line(parent:Node,x1:number,y1:number,x2:number,y2:number,color:Color=T.edge){const g=this.hud.node('QuietDivider',parent).addComponent(CompactGraphics);g.strokeColor=color;g.lineWidth=1;g.moveTo(x1,y1);g.lineTo(x2,y2);g.stroke();}
}
