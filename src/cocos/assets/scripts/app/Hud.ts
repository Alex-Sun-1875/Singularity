import {viewportMetrics} from '../platform/ViewportMetrics';
import {skillWeaponRequirement} from '../features/combat/common/SkillWeapons';
import {CompactMask as Mask} from '../shared/ui/CompactMask';
import {CompactGraphics} from '../shared/ui/CompactGraphics';
import {Node,Graphics,Label,Sprite,SpriteFrame,UITransform,Canvas,Camera,Layers,Color,Vec2,Vec3,view,ResolutionPolicy,EventTouch,sys,screen,director,Sorting2D,ButtonComponent as Button,BlockInputEvents} from 'cc';
import type {GameSession} from '../core/GameSession';
import type {AutomationMode,NavigationTarget} from '../features/automation/common/Automation';
import type {JourneyGuidance} from '../features/journey/common/JourneyGuide';
import {QuestTracker,type QuestTrackerLine} from '../features/journey/runtime/QuestTracker';
import {AREAS} from '../features/world/data/WorldData';
import {EQUIPMENT,type ItemDef} from '../features/equipment/data/Equipment';
import {MapPanel} from '../features/navigation/runtime/MapPanel';
import {UiSkin} from '../shared/ui/UiSkin';
import {FeedbackView as F} from '../shared/ui/FeedbackView';
import {navigationFeedback,playerHealthFeedbackRole,type FeedbackRole} from '../shared/ui/FeedbackPalette';
import {UI_COLORS as C,UI_DESIGN_SIZE,UI_HUD_INSETS} from '../shared/ui/UiTheme';
import {UiChrome} from '../shared/ui/UiChrome';
import type {HairstyleOption} from '../features/actors/runtime/Hairstyles';
import {MiniMap,MINIMAP_RENDER_ORDER} from '../features/navigation/runtime/MiniMap';
import {COMBAT_SKILLS} from '../features/combat/data/PureSkills';
import {COMBAT_SKILL_ICONS} from '../features/combat/runtime/CombatSkillIcons';
import {assignedLoadout} from '../features/progression/common/CombatLoadouts';
import {MenuPanel,type MenuChoice,type MenuRow,type MenuPresentation} from '../shared/ui/MenuPanel';
import {AutomationHud,type AutomationExperience} from '../features/automation/runtime/AutomationHud';
import {EquipmentPickupNotice} from '../features/equipment/runtime/EquipmentPickupNotice';
import type {TrainingRange} from '../features/debug/common/TrainingRange';
import {trainingText} from '../features/debug/locales';
import {resourceProfile,skillResourceText} from '../features/combat/common/ClassResource';

export interface HudActions {click(action:string):void;touch(control:string,phase:'start'|'move'|'end'|'cancel',event:EventTouch):void;navigate(target:NavigationTarget):void;}
const TITLES:Record<string,string>={attack:'攻击',dash:'闪避',combat0:'主动一',combat1:'主动二',combat2:'主动三',combat3:'主动四',ultimate:'终极',interact:'交互',map:'地图',inventory:'行囊',checks:'技能',settings:'设置',supplies:'药品',pause:'暂停','potion-health':'生命药','potion-resource':'资源药',rest:'补给'};
const COMBAT_ARC_SPAN=102*Math.PI/180,COMBAT_ARC_CENTER=Math.PI*.75;
const KEYS:Record<string,string>={attack:'J',dash:'空格',combat0:'Q',combat1:'E',combat2:'R',combat3:'T',ultimate:'G',interact:'F',map:'M',inventory:'B',checks:'C',pause:'Esc','potion-health':'5','potion-resource':'6'};

export class Hud {
 get uiUnit(){return this.touchMode?this.height/Math.max(1,viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio)):1.25;}
 trainingRange:TrainingRange|undefined;private trainingButton:Node|null=null;
 private equipmentNotice=new EquipmentPickupNotice(this);
 private equipmentPickupsAvailable=false;
 showEquipmentPickup(item:ItemDef,count=1){this.equipmentNotice.enqueue(item,count);this.layoutTopMessages();}
 clearEquipmentPickups(){this.equipmentNotice.clear();this.layoutTopMessages();}
 updateEquipmentPickups(dt:number,available:boolean){this.equipmentPickupsAvailable=available;this.equipmentNotice.update(dt,available&&!this.portrait&&!this.automationExpanded&&!this.modal.children.length);this.layoutTopMessages();}
 private guidance:JourneyGuidance|null=null;private guidanceClock=Infinity;
 setGuidance(guide:JourneyGuidance|null){this.guidance=guide;}
 get activeGuidance(){return this.guidance;}
 get portrait():boolean{return this.width<760;}
 previewSource:Node|null=null;
 hairstyles:readonly HairstyleOption[]=[];
 reducedMotion=false;
 skillAimMode:'auto'|'manual'='auto';
 flatMode=false;flatPortrait:SpriteFrame|null=null;
 flatPortraitViewsForWeapon:((weapon:string)=>SpriteFrame[])|null=null;
 private flatHead:SpriteFrame|null=null;private defaultHead:SpriteFrame|null=null;private portraitImage:Sprite|null=null;private portraitSize=64;
 readonly modalDisposers=new Set<()=>void>();
 private miniMap:MiniMap|null=null;private portraitRing:Graphics|null=null;private lastHealth=-1;
 readonly mapTravel={busy:false,error:''};
 private mapPanel=new MapPanel(this);private pixelWidth=0;private pixelHeight=0;
 private pointerTargets=new Set<Node>();private cooldownLabels=new Map<string,Label>();private counts=new Map<string,Label>();
 private skillPointMark?:Node;
 private actionIcons=new Map<string,Sprite>();private cooldownShades=new Map<string,Node>();private iconPaths=new Map<string,string>();
 private actionDiameters=new Map<string,number>();private showSkillNames=false;
 private skillIconGroup='';private iconGroups=new Map<string,string>();
 private combatControls=new Map<string,Node>();private combatLayoutKey='';private dashControl:Node|null=null;
 private combatAnchor={x:0,y:0,unit:0,attackSize:0,bottom:0,joystickRight:0,gap:0};private supplyBelt:Node|null=null;
 private supplyBeltExpanded=false;
 private combatArcActions:string[]=[];private combatUtilityActions:string[]=[];
 private attackRangeY=0;private aimCancelGap=12;
 private mapDock:Node|null=null;private mapDockHome={x:0,y:0};private mapDockSlots:{node:Node;radius:number;interactive:boolean}[]=[];
 private automationHud:AutomationHud|null=null;private automationLabel:Label|null=null;private navigationButton:Node|null=null;
 private questTracker:QuestTracker|null=null;
 private automationState={mode:'manual' as AutomationMode,navigating:false,paused:false,status:'',experience:undefined as AutomationExperience|undefined,taskId:undefined as string|undefined};
 private tooltips=new Map<string,string>();private touchMode=false;private barWidth=176;private disabledShades=new Map<string,Node>();
 private skillDescription:Node|null=null;
 root:Node;camera:Camera;modal:Node;labels=new Map<string,Label>();width:number=UI_DESIGN_SIZE.width;height:number=UI_DESIGN_SIZE.height;
 health:Sprite;focus:Sprite;joystick:Node;joystickRadius=68;cancel:Node;buttonLabels=new Map<string,Label>();
 constructor(scene:Node,readonly actions:HudActions){
  try{this.showSkillNames=sys.localStorage.getItem('sword-fire-ui-skill-names')==='1';}catch{/* Cosmetic preferences cannot prevent boot. */}
  view.setDesignResolutionSize(UI_DESIGN_SIZE.width,UI_DESIGN_SIZE.height,ResolutionPolicy.FIXED_HEIGHT);
  this.root=new Node('Canvas');scene.addChild(this.root);this.root.layer=Layers.Enum.UI_2D;
  const canvas=this.root.addComponent(Canvas);this.camera=new Node('UICamera').addComponent(Camera);scene.addChild(this.camera.node);this.camera.node.setPosition(0,0,1000);this.camera.projection=Camera.ProjectionType.ORTHO;this.camera.orthoHeight=UI_DESIGN_SIZE.height/2;this.camera.clearFlags=Camera.ClearFlag.DEPTH_ONLY;this.camera.visibility=Layers.Enum.UI_2D;this.camera.priority=10;canvas.cameraComponent=this.camera;
  this.root.addComponent(UITransform).setContentSize(UI_DESIGN_SIZE.width,UI_DESIGN_SIZE.height);this.modal=new Node('Modal');this.modal.layer=Layers.Enum.UI_2D;this.modal.addComponent(UITransform).setContentSize(UI_DESIGN_SIZE.width,UI_DESIGN_SIZE.height);this.root.addChild(this.modal);this.build();
 }
 get skillNamesVisible():boolean{return this.showSkillNames;}
 get supplyBeltVisible():boolean{return this.supplyBeltExpanded;}
 toggleSupplyBelt():void{this.supplyBeltExpanded=!this.supplyBeltExpanded;if(this.supplyBelt)this.supplyBelt.active=this.supplyBeltExpanded;}
 get automationView(){return this.automationState;}
 settingsTab:'audio'|'controls'|'journey'='audio';
 get automationExpanded(){return !!this.automationHud?.expanded;}
 isOverAutomation(point:Vec2){return !!this.automationHud?.contains(point);}
 toggleAutomation(){this.automationHud?.toggle();this.layoutTopMessages();}
 collapseAutomation(){this.automationHud?.setExpanded(false);this.layoutTopMessages();}
 get touchTargetSize():number{return this.touchMode?Math.max(80,48*this.height/Math.max(1,screen.windowSize.height/Math.max(1,screen.devicePixelRatio))):44;}
 setSkillNamesVisible(show:boolean):void{
  this.showSkillNames=show;
  for(const [action,label]of this.buttonLabels){
   if(!this.isSkillControl(action))continue;label.node.active=show&&!!this.actionIcons.get(action)?.node.active;
   const diameter=this.actionDiameters.get(action);if(diameter)this.layoutActionIcon(action,diameter);
  }
  try{sys.localStorage.setItem('sword-fire-ui-skill-names',show?'1':'0');}catch{/* Keep the chosen presentation for this session. */}
 }
 private isSkillControl(action:string):boolean{return action==='attack'||action==='dash'||action==='ultimate'||/^combat\d+$/.test(action);}
 isDescribableSkill(action:string):boolean{return action==='dash'||action==='ultimate'||/^combat\d+$/.test(action);}
 isControlReady(action:string):boolean{return !!this.buttonLabels.get(action)?.node.parent?.getComponent(Button)?.interactable;}
 hideSkillDescription():void{if(this.skillDescription){this.skillDescription.removeFromParent();this.skillDescription.destroy();this.skillDescription=null;}}
 showSkillDescription(game:GameSession,action:string):void{
  this.hideSkillDescription();
  const combat=game.state.combat,loadout=assignedLoadout(combat),slot=Number(action.slice(6));
  const equipped=action==='dash'?'COM_01':action==='ultimate'?combat.ultimate:combat.activeSlots[slot];
  const id=equipped??(action==='ultimate'?loadout?.ultimate:loadout?.activeSlots[slot]),def=COMBAT_SKILLS[id??''];
  const model=def?game.combatSkillView([def.id])[0]:undefined,rank=def?.ranks[Math.max(0,(model?.rank??1)-1)],resource=resourceProfile(game.state);
  const kind=def?.type==='ultimate'?'终极技能':def?.type==='mobility'?'闪避技能':'主动技能';
  const title=def?`${def.name} · ${model?.unlocked?`${model.rank}级`: '未解锁'}`:'空技能位';
  const facts=rank?`冷却 ${rank.cooldownSeconds}秒 · ${rank.castRangeMetres?`距离 ${rank.castRangeMetres}米 · `:''}${model?.resourceCost?`消耗 ${model.resourceCost}${resource.name}`:'无消耗'}`:'';
  const mechanic=def?skillResourceText(def.mechanic??def.effect??rank?.effect??''):'';
  const effect=rank?.effect&&rank.effect!==mechanic?skillResourceText(rank.effect):'';
  const upgrade=rank?.upgradeEffect?`本阶效果：${skillResourceText(rank.upgradeEffect)}`:'';
  const body=def?[mechanic,effect,upgrade].filter(Boolean).join('\n'):'前往战斗技能页，将已解锁的技能装入这个位置。';
  const status=!def?'尚未配置':!model?.unlocked?`角色 Lv.${model?.requiredLevel??def.unlockLevel} 解锁`:!equipped?'未配置到技能栏':!model.compatible?skillWeaponRequirement(def):!model.resourceEnough?`${resource.name}不足，需要 ${model.resourceCost}点`:model.cooldown>0?`剩余冷却 ${model.cooldown.toFixed(1)}秒`:!model.ready?'终极技能暂未就绪':'可施放';
  const scale=this.touchMode?this.height/Math.max(1,screen.windowSize.height/Math.max(1,screen.devicePixelRatio)):1;
  const safe=sys.getSafeAreaRect(false),inset=8*scale,left=-this.width/2+Math.max(inset,safe.x),right=-this.width/2+Math.min(this.width-inset,safe.x+safe.width),bottom=-this.height/2+Math.max(inset,safe.y),top=-this.height/2+Math.min(this.height-inset,safe.y+safe.height);
  const padding=16*scale,font=13*scale,line=19*scale;
  let width=Math.min(280*scale,right-left),bodyWidth=width-2*padding;
  // Use the engine's own font measurements; preserve readable type while wrapping Chinese and Latin text.
  const panel=this.skillDescription=this.node('SkillDescription',this.root,0,0,width,0);
  const description=this.text(panel,body,0,0,bodyWidth,font,C.ink,line);description.node.name='SkillDescriptionBody';description.overflow=Label.Overflow.RESIZE_HEIGHT;description.enableWrapText=true;description.lineHeight=line;description.verticalAlign=Label.VerticalAlign.TOP;description.updateRenderData(true);
  let bodyHeight=description.node.getComponent(UITransform)!.height,height=130*scale+bodyHeight;
  while(height>top-bottom&&width<right-left){width=Math.min(width+40*scale,right-left);bodyWidth=width-2*padding;description.node.getComponent(UITransform)!.width=bodyWidth;description.updateRenderData(true);bodyHeight=description.node.getComponent(UITransform)!.height;height=130*scale+bodyHeight;}
  panel.getComponent(UITransform)!.setContentSize(width,height);UiSkin.panel(panel,width,height,C.inset,'panel',false,scale);
  // Frame decoration belongs behind the text, and the popup never owns pointer input.
  description.node.setSiblingIndex(panel.children.length-1);
  const text=(name:string,value:string,y:number,size:number,color:Color,h=22*scale)=>{const label=this.text(panel,value,0,y,bodyWidth,size,color,h);label.node.name=name;label.lineHeight=size*1.4;return label;};
  text('SkillDescriptionTitle',title,height/2-25*scale,16*scale,C.gold);
  text('SkillDescriptionFacts',facts||kind,height/2-51*scale,12*scale,C.ink);
  description.node.setPosition(0,height/2-72*scale-bodyHeight/2);
  const state=text('SkillDescriptionStatus',status,-height/2+43*scale,12*scale,C.ink);F.tint(state,model?.ready&&!!equipped?'state.ready':'state.paused');
  text('SkillDescriptionHelp','松开关闭 · 查看后不会施放',-height/2+22*scale,11*scale,C.muted);
  // Stay near the outer edge and above the held button; tall cards move to its left to clear the finger.
  const control=this.buttonLabels.get(action)!.node.parent!,bounds=control.getComponent(UITransform)!,controlTop=control.position.y+bounds.height/2;
  let x=right-width/2,y=Math.min(top-height/2,controlTop+12*scale+height/2);
  if(y-height/2<controlTop+8*scale)x=Math.max(left+width/2,control.position.x-bounds.width/2-12*scale-width/2);
  panel.setPosition(x,Math.max(bottom+height/2,y));
 }
 private actionIconY(action:string,diameter:number):number{return action.startsWith('potion-')||this.isSkillControl(action)&&!this.showSkillNames?0:diameter*.14;}
 private actionIconSize(action:string,diameter:number):number{return diameter*(this.isSkillControl(action) ? this.showSkillNames ? .44 : this.iconPaths.get(action)?.startsWith('rpg-') ? .75 : .56 : .43);}
 private layoutActionIcon(action:string,diameter:number):void {
  const icon=this.actionIcons.get(action),shade=this.cooldownShades.get(action),size=this.actionIconSize(action,diameter),y=this.actionIconY(action,diameter),clip=icon?.node.parent;
  const clipped=clip?.name==='SkillIconClip';
  if(clipped){clip.getComponent(UITransform)!.setContentSize(size,size);clip.setPosition(0,y);}
  for(const node of [icon?.node,shade])if(node){node.getComponent(UITransform)!.setContentSize(size/node.scale.x,size/node.scale.y);node.setPosition(0,clipped?0:y);}
  this.cooldownLabels.get(action)?.node.setPosition(0,y);
 }
 private actionIconPath(action:string,path:string):string{return `ui/${this.isSkillControl(action)?'combat-relief':'icons'}/${path}`;}
 /** Borrow concept-art frames from the actor presenter; no UI rebuild or asset ownership transfer. */
 setFlatPortrait(frame:SpriteFrame|null,headFrame?:SpriteFrame){this.flatMode=true;this.flatPortrait=frame;this.flatHead=headFrame??frame;this.refreshPortrait();}
 /** Borrow the painted portrait corresponding to the selected hairstyle. */
 setHeadPortrait(frame:SpriteFrame|null){this.flatHead=frame;this.refreshPortrait();}
 private refreshPortrait(){const image=this.portraitImage;if(!image?.isValid)return;const frame=[this.flatHead,this.flatPortrait,this.defaultHead].find(frame=>frame?.isValid);image.node.active=!!frame;image.spriteFrame=frame??null;if(frame){const rect=frame.rect,scale=this.portraitSize/Math.max(1,Math.min(rect.width,rect.height));image.node.getComponent(UITransform)!.setContentSize(rect.width*scale,rect.height*scale);}}
 /** Use the UI camera for screen coordinates, including the native viewport and Canvas transform. */
 touchPosition(node:Node,event:EventTouch):Vec3 {const p=event.getLocation(),world=this.camera.screenToWorld(new Vec3(p.x,p.y,0));return node.getComponent(UITransform)!.convertToNodeSpaceAR(world);}
 isJoystickTouch(point:Vec2):boolean {const base=this.joystick?.parent;return !!base?.activeInHierarchy&&!!base.getComponent(UITransform)?.hitTest(point);}
 node(name:string,parent=this.root,x=0,y=0,w=100,h=40):Node {const n=new Node(name);n.layer=Layers.Enum.UI_2D;parent.addChild(n);n.setPosition(x,y);n.addComponent(UITransform).setContentSize(w,h);return n;}
 panel(parent:Node,x:number,y:number,w:number,h:number,fill=C.panel):Node {
  const n=this.node('Panel',parent,x,y,w,h);UiSkin.panel(n,w,h,fill,'legacy');
  UiSkin.asset(n,'leather-inset-v8',w-10,h-10,false).node.setSiblingIndex(1);UiChrome.frame(this.node('FineOrnament',n,0,0,w,h),w,h);return n;
 }
 text(parent:Node,value:string,x:number,y:number,w=320,size=20,color=C.ink,h=42):Label {const n=this.node('Text',parent,x,y,w,h);const l=n.addComponent(Label);l.string=value;l.fontSize=size;l.lineHeight=size*1.42;l.color=color;l.fontFamily='Microsoft YaHei';l.horizontalAlign=Label.HorizontalAlign.LEFT;l.verticalAlign=Label.VerticalAlign.CENTER;l.overflow=Label.Overflow.SHRINK;return l;}
 button(parent:Node,title:string,x:number,y:number,w:number,h:number,action:string,touch=false):Node {
  const n=this.node(action,parent,x,y,w,h);if(parent===this.root)this.pointerTargets.add(n);
  const button=UiSkin.button(n,w,h);
  const label=this.text(n,title,0,0,w-24,this.touchMode?28:18,C.ink,h-8);label.horizontalAlign=Label.HorizontalAlign.CENTER;
  if(touch){this.buttonLabels.set(action,label);for(const [event,phase]of [[Node.EventType.TOUCH_START,'start'],[Node.EventType.TOUCH_MOVE,'move'],[Node.EventType.TOUCH_END,'end'],[Node.EventType.TOUCH_CANCEL,'cancel']]as const)n.on(event,(e:EventTouch)=>{e.propagationStopped=true;if(button.interactable||this.isDescribableSkill(action)||phase==='end'||phase==='cancel')this.actions.touch(action,phase,e);});}
  else n.on(Button.EventType.CLICK,()=>this.actions.click(action));return n;
 }
 /** Keep a generous native hit target around a smaller, polished-gold circular face. */
 private roundButton(action:string,x:number,y:number,hit:number,diameter:number,touch:boolean,iconPath=action,parent=this.root,iconOnly=false,bezelOrder?:number):Node {
  const n=this.node(action,parent,x,y,hit,hit);this.pointerTargets.add(n);
  this.circularHitArea(n,hit);
  const skill=this.isSkillControl(action),face=this.node('ButtonFace',n,0,0,diameter,diameter);
  // Same shadow, halo and bezel, precomposed into one shared sprite. Keep
  // the pressed transform and hit target, with two fewer translucent draws.
  const faceSize=skill?diameter*1.6:diameter;
  const bezel=UiSkin.asset(face,skill?'hud-skill-face-v19':'unified-gold-medallion-v13',faceSize,faceSize,false),order=bezelOrder??(skill?-30:undefined);if(order!==undefined)this.controlOrder(bezel,order);
  // The broad skill bezel includes its engraved scrollwork in the mipmapped skin.
  if(!skill)UiChrome.circleOrnament(this.node('MetalScrollwork',face),diameter/2);
  const clipDiameter=skill?diameter*.75:diameter-8; // Keep disabled shading inside the thicker metal's inner lip.
  // Keep the original visibility/pressed-transform group; its fill is already circular.
  const clip=this.node('RoundButtonClip',face,0,0,clipDiameter,clipDiameter);clip.active=false;
  const button=n.addComponent(Button);button.target=face;button.transition=Button.Transition.SCALE;button.zoomScale=.94;button.duration=.1;
  const label=this.text(n,TITLES[action]??action,0,-diameter*(skill ? .24 : .29),skill?diameter*.6:diameter-12,this.touchMode?22:12,C.ink,this.touchMode?30:18);label.horizontalAlign=Label.HorizontalAlign.CENTER;label.lineHeight=label.fontSize*1.2;
  label.node.active=!iconOnly&&!action.startsWith('potion-')&&(!this.isSkillControl(action)||this.showSkillNames);
  if(touch){this.buttonLabels.set(action,label);for(const [event,phase]of [[Node.EventType.TOUCH_START,'start'],[Node.EventType.TOUCH_MOVE,'move'],[Node.EventType.TOUCH_END,'end'],[Node.EventType.TOUCH_CANCEL,'cancel']]as const)n.on(event,(e:EventTouch)=>{e.propagationStopped=true;if(button.interactable||this.isDescribableSkill(action)||phase==='end'||phase==='cancel')this.actions.touch(action,phase,e);});}
  else n.on(Button.EventType.CLICK,()=>this.actions.click(action));
  if(skill||iconPath){
   const iconSize=iconOnly?diameter*.58:this.actionIconSize(action,diameter);
   // Skill frames load through setActionIcon so an older asynchronous request
   // cannot overwrite a newly assigned skill or fill a now-empty slot.
   const iconY=iconOnly?0:this.actionIconY(action,diameter),iconParent=skill?this.node('SkillIconClip',n,0,iconY,iconSize,iconSize):n;
   // The HUD-specific image owns its circular alpha; no stencil on this subtree.
   const icon=skill?this.node('ControlIcon',iconParent,0,0,iconSize,iconSize).addComponent(Sprite):UiSkin.sprite(n,this.actionIconPath(action,iconPath),iconSize,iconSize,C.ink);
   icon.sizeMode=Sprite.SizeMode.CUSTOM;icon.trim=false;icon.color=skill?Color.WHITE:C.ink;icon.node.name='ControlIcon';icon.node.active=!!iconPath;icon.node.setPosition(0,skill?0:iconY);
  }
  else{
   const mark=this.node(action==='settings'?'SettingsMark':'PauseMark',n,0,iconOnly?0:diameter*.14,32,32).addComponent(CompactGraphics);mark.strokeColor=C.ink;mark.lineWidth=2.5;
   if(action==='settings'){
    const radius=diameter*(iconOnly ? .26 : .19);for(let i=0;i<32;i++){const a=i*Math.PI/16,r=radius*(i%4<2?1:.76),x=Math.cos(a)*r,y=Math.sin(a)*r;if(i===0)mark.moveTo(x,y);else mark.lineTo(x,y);}mark.close();mark.stroke();mark.circle(0,0,radius*.36);mark.stroke();
   }else for(const x of [-5,5]){mark.moveTo(x,-7);mark.lineTo(x,7);mark.stroke();}
  }
  return n;
 }
 circularHitArea(n:Node,hit:number):void {
  // Circular targets let an evenly spaced arc stay compact without overlapping
  // rectangular corners stealing touches from the neighbouring skill.
  const transform=n.getComponent(UITransform)!,rectangleHit=transform.hitTest.bind(transform),point3=new Vec3(),localPoint=new Vec3();
  transform.hitTest=(point,windowId=0)=>{
   if(!rectangleHit(point,windowId))return false;
   point3.set(point.x,point.y,0);this.camera.screenToWorld(point3,localPoint);transform.convertToNodeSpaceAR(localPoint,localPoint);
   return localPoint.x*localPoint.x+localPoint.y*localPoint.y<=hit*hit/4;
  };
 }
 // Negative orders group skill layers behind ordinary HUD/popups, without moving touch nodes.
 private controlOrder(renderer:Sprite|Graphics,order:number){renderer.node.addComponent(Sorting2D).sortingOrder=order;}
 private iconButton(action:string,x:number,y:number,hit:number,diameter:number,touch=true,iconPath=action,parent=this.root):Node {
  const n=this.roundButton(action,x,y,hit,diameter,touch,iconPath,parent),iconSize=this.actionIconSize(action,diameter),iconY=this.actionIconY(action,diameter);
  const icon=(n.getChildByName('SkillIconClip')??n).getChildByName('ControlIcon')!.getComponent(Sprite)!;
  this.actionIcons.set(action,icon);this.iconPaths.set(action,this.isSkillControl(action)?'':iconPath);this.actionDiameters.set(action,diameter);
  if(this.isSkillControl(action))this.setActionIcon(action,iconPath);
  const shade=this.isSkillControl(action)?UiSkin.sprite(icon.node.parent!,'ui/combat-relief/hud-circular/cooldown',iconSize,iconSize):UiSkin.asset(icon.node.parent!,'mask-cooldown',iconSize,iconSize,false);shade.node.name='CooldownShade';shade.node.setPosition(0,this.isSkillControl(action)?0:iconY);shade.fillType=Sprite.FillType.RADIAL;shade.fillCenter=new Vec2(.5,.5);shade.fillStart=.25;shade.fillRange=-1;shade.type=Sprite.Type.FILLED;shade.node.active=false;this.cooldownShades.set(action,shade.node);
  if(this.isSkillControl(action)){this.controlOrder(icon,-10);this.controlOrder(shade,-5);}
  const clip=n.getChildByName('ButtonFace')!.getChildByName('RoundButtonClip')!,disabled=this.node('DisabledShade',clip,0,0,diameter,diameter),fill=disabled.addComponent(CompactGraphics),radius=clip.getComponent(UITransform)!.width/2;
  // Same color and 64-sided ellipse as the former Mask+Sprite, in one native draw.
  F.ink(fill,'control.disabled','fill',158);
  for(let i=0;i<64;i++){const angle=i*2*Math.PI/64,x=Math.cos(angle)*radius,y=Math.sin(angle)*radius;if(i)fill.lineTo(x,y);else fill.moveTo(x,y);}fill.close();fill.fill();
  if(this.isSkillControl(action))this.controlOrder(fill,-20);disabled.active=false;this.disabledShades.set(action,disabled);
  const cd=this.text(n,'',0,iconY,diameter-8,this.touchMode?26:21,C.ink,diameter-12);cd.horizontalAlign=Label.HorizontalAlign.CENTER;cd.node.active=false;this.cooldownLabels.set(action,cd);
  const count=this.text(n,'',diameter*.3,diameter*.29,36,this.touchMode?21:14,C.gold,28);count.horizontalAlign=Label.HorizontalAlign.CENTER;count.enableWrapText=false;count.enableOutline=true;count.outlineWidth=2;count.outlineColor=C.dark;this.counts.set(action,count);
  n.on(Node.EventType.MOUSE_ENTER,()=>{if(!this.touchMode&&this.labels.get('hint'))this.labels.get('hint')!.string=this.tooltips.get(action)??TITLES[action];});
  n.on(Node.EventType.MOUSE_LEAVE,()=>{if(!this.touchMode&&this.labels.get('hint'))this.labels.get('hint')!.string='WASD 移动   ·   Shift 慢行   ·   滚轮缩放';});this.layoutActionIcon(action,diameter);return n;
 }
 private build(){
  this.hideSkillDescription();
  const size=view.getVisibleSize();this.width=size.width;this.height=size.height;this.root.getComponent(UITransform)!.setContentSize(this.width,this.height);this.camera.orthoHeight=this.height/2;
  this.touchMode=sys.isMobile;this.pointerTargets.clear();this.cooldownLabels.clear();this.counts.clear();this.buttonLabels.clear();this.actionIcons.clear();this.actionDiameters.clear();this.cooldownShades.clear();this.disabledShades.clear();this.iconPaths.clear();this.iconGroups.clear();this.tooltips.clear();
  this.combatControls.clear();this.combatLayoutKey='';this.combatArcActions=[];this.combatUtilityActions=[];
  const cssHeight=Math.max(1,screen.windowSize.height/Math.max(1,screen.devicePixelRatio)),pixelScale=this.height/cssHeight,touchMin=Math.max(80,48*pixelScale),unit=this.touchMode?touchMin:64,gap=this.touchMode?8*pixelScale:12;
  // Safe-area insets already reserve the hardware obstruction. Use a small
  // screen gutter only where it is larger; never add another gutter on top.
  const safe=sys.getSafeAreaRect(false),edge=this.touchMode?UI_HUD_INSETS.information*pixelScale:10,left=-this.width/2+Math.max(edge,safe.x),right=-this.width/2+Math.min(this.width-edge,safe.x+safe.width),top=-this.height/2+Math.min(this.height-edge,safe.y+safe.height),bottom=-this.height/2+Math.max(edge,safe.y);
  const combatEdge=this.touchMode?UI_HUD_INSETS.combat*pixelScale:16,combatRight=Math.min(right,this.width/2-combatEdge),combatBottom=Math.max(bottom,-this.height/2+combatEdge);
  // A compact portrait and two bars anchor the left column; the world stays visible below.
  const statsW=this.touchMode?328:280,statsH=116,stats=this.panel(this.root,left+statsW/2,top-statsH/2,statsW,statsH,new Color(20,15,11,224));stats.name='HeroStatus';this.pointerTargets.add(stats);this.barWidth=statsW-116;
  const portrait=this.node('HeroPortrait',stats,-statsW/2+44,4,76,76),crop=this.node('PortraitClip',portrait,0,0,this.portraitSize,this.portraitSize);crop.addComponent(Mask).type=Mask.Type.GRAPHICS_ELLIPSE;
  const art=this.node('ConceptPortrait',crop,0,0,this.portraitSize,this.portraitSize),image=this.portraitImage=art.addComponent(Sprite);image.sizeMode=Sprite.SizeMode.CUSTOM;image.trim=false;this.refreshPortrait();
  // One owner assigns the image. A late default load must not replace a selected hairstyle.
  void UiSkin.frame('portraits/native-raphael',0,image.node).then(frame=>{this.defaultHead=frame;if(this.portraitImage===image&&image.isValid)this.refreshPortrait();}).catch(error=>console.warn('[HUD] Default portrait unavailable:',error));
  this.portraitRing=UiChrome.circle(portrait,35);this.lastHealth=-1;portrait.on(Node.EventType.TOUCH_END,()=>this.actions.click('checks'));
  const bx=44;
  this.labels.set('name',this.text(stats,'拉斐尔',bx,39,this.barWidth,this.touchMode?23:18,C.gold,28));this.labels.get('name')!.fontFamily='SimSun';
  this.labels.set('health',this.text(stats,'',bx,15,this.barWidth,this.touchMode?21:14,C.ink,28));this.health=UiSkin.bar(this.node('Health',stats,bx,-2,this.barWidth,16),this.barWidth,'health');
  this.labels.set('focus',this.text(stats,'',bx,-22,this.barWidth,this.touchMode?20:13,C.muted,28));this.focus=UiSkin.bar(this.node('Focus',stats,bx,-39,this.barWidth,16),this.barWidth,'focus');
  this.labels.set('stats',this.text(stats,'',-statsW/2+54,-44,92,this.touchMode?17:11,C.muted,22));
  this.labels.set('save',this.text(stats,'',statsW/2-29,40,32,this.touchMode?18:12,C.muted,24));this.labels.get('save')!.horizontalAlign=Label.HorizontalAlign.RIGHT;
  const questExpanded=this.questTracker?.expanded??false;
  this.questTracker=new QuestTracker(this,{left,top:top-statsH-(this.touchMode?16*pixelScale:12),width:statsW,scale:this.touchMode?pixelScale:1.25,hit:this.touchMode?touchMin:48,expanded:questExpanded});
  this.navigationButton=this.questTracker.navigationButton;this.automationLabel=this.questTracker.actionLabel;
  for(const target of [this.questTracker.root,this.questTracker.textButton,this.navigationButton])this.pointerTargets.add(target);
  // Medallion centres sit toward the outer gold lip. Empty mounts remain
  // decorative extension points and never intercept map/world input.
  const toolHit=this.touchMode?touchMin:44,toolFace=this.touchMode?28*pixelScale:32,reserveFace=this.touchMode?18*pixelScale:20;
  const miniRight=Math.min(this.width/2-10,right+12),miniTop=Math.min(this.height/2-10,top+12);
  const attackSize=unit*1.32,maxArcRadius=(unit+gap)/(2*Math.sin(COMBAT_ARC_SPAN/6)),arcStart=COMBAT_ARC_CENTER+COMBAT_ARC_SPAN/2,arcEnd=COMBAT_ARC_CENTER-COMBAT_ARC_SPAN/2;
  // Fit the actual arc/attack hit bounds to the bottom-right edge. A fan
  // centred at 135 degrees leaves equal, minimal attack margins on both axes.
  const ax=combatRight-Math.max(attackSize/2,unit/2+maxArcRadius*Math.max(0,Math.cos(arcEnd))),ay=combatBottom+Math.max(attackSize/2,unit/2+maxArcRadius*Math.max(0,-Math.sin(arcStart)));
  // unified-gold-ring-v16 spans radii 216.5–250.5 in its 512px source.
  // Use the outer gold stroke while keeping the controls overlapping the band;
  // widen their angular spacing rather
  // than pushing them away from the map to fit the native touch targets.
  const miniSize=this.touchMode?256:240,orbitRadius=miniSize*247.5/512;
  const firstAngle=155*Math.PI/180,toolStep=Math.max(40*Math.PI/180,2*Math.asin(Math.min(1,(toolHit+gap)/(2*orbitRadius))));
  // Keep supplies immediately to the right of settings on the same gold rim.
  // Four live mounts share the full touch gap; spread the two empty mounts
  // evenly along the remaining arc.
  const reserveStep=(Math.PI*2-toolStep*3)/3,mountAngles=[...[0,1,2,3].map(i=>firstAngle+toolStep*i),...[1,2].map(i=>firstAngle+toolStep*3+reserveStep*i)];
  const toolActions=['inventory','checks','settings','supplies',undefined,undefined] as const;
  const mountPoints=mountAngles.map((angle,i)=>({x:Math.cos(angle)*orbitRadius,y:Math.sin(angle)*orbitRadius,radius:(toolActions[i]?toolHit:reserveFace)/2}));
  const miniX=miniRight-Math.max(miniSize/2,...mountPoints.map(p=>p.x+p.radius)),miniY=miniTop-Math.max(miniSize/2,...mountPoints.map(p=>p.y+p.radius));
  const miniHost=this.node('MiniMapHost',this.root,miniX,miniY,miniSize,miniSize);this.circularHitArea(miniHost,miniSize);this.pointerTargets.add(miniHost);this.miniMap=new MiniMap(this,miniHost,0,0,miniSize);
  this.mapDock=miniHost;this.mapDockHome={x:miniX,y:miniY};this.mapDockSlots=[];
  const tools=this.node('MapTools',miniHost,0,0,0,0);
  let reservedRims:Graphics|undefined;
  for(let i=0;i<6;i++){
   const {x,y}=mountPoints[i],action=toolActions[i],face=action?toolFace:reserveFace;
   if(action){
    const n=this.roundButton(action,x,y,toolHit,toolFace,false,action==='settings'?'':action==='supplies'?'potion-health':action,tools,true,MINIMAP_RENDER_ORDER.toolBezel);this.mapDockSlots.push({node:n,radius:toolHit/2,interactive:true});
    if(action==='checks'){const mark=this.skillPointMark=this.node('SkillPointMark',n,toolFace*.32,toolFace*.32,0,0),g=mark.addComponent(CompactGraphics);g.fillColor=C.gold;g.strokeColor=C.dark;g.lineWidth=2;g.circle(0,0,3*pixelScale);g.fill();g.stroke();mark.active=false;}
    n.on(Node.EventType.MOUSE_ENTER,()=>{const hint=this.labels.get('hint');if(hint&&!this.touchMode)hint.string=action==='supplies'?`药品 · 点击${this.supplyBeltExpanded?'收起':'展开'}药品栏`:TITLES[action];});
    if(action==='checks'){const count=this.text(n,'',toolFace*.42,toolFace*.42,28,this.touchMode?16:11,C.gold,24);count.horizontalAlign=Label.HorizontalAlign.CENTER;count.enableOutline=true;count.outlineColor=C.dark;count.outlineWidth=2;this.labels.set('checks',count);}
   }else{
    const n=this.node('MapToolReserved:'+(i-2),tools,x,y,face,face),g=reservedRims??(reservedRims=this.node('ReservedRims',tools,0,0,0,0).addComponent(CompactGraphics));g.fillColor=new Color(C.dark.r,C.dark.g,C.dark.b,160);g.circle(x,y,face/2);g.fill();g.strokeColor=new Color(C.gold.r,C.gold.g,C.gold.b,190);g.lineWidth=this.touchMode?1.25*pixelScale:1.25;g.circle(x,y,face/2);g.stroke();g.strokeColor=new Color(C.gold.r,C.gold.g,C.gold.b,95);g.lineWidth=this.touchMode?.65*pixelScale:.65;g.circle(x,y,face*.32);g.stroke();this.mapDockSlots.push({node:n,radius:face/2,interactive:false});
   }
  }
  const joyRoom=this.questTracker.expandedBottom-gap-bottom,joySize=Math.min(312,Math.max(280,touchMin*3),joyRoom),joyRadius=joySize*3/7,knobRadius=joyRadius*7/24;
  this.joystickRadius=joyRadius-knobRadius;
  // Enlarge the base and thumb together, anchored close to the safe bottom-left
  // corner; short screens retain a full touch gap below the utility controls.
  const joy=this.node('Move',this.root,left+joySize/2+8,bottom+joySize/2,joySize,joySize);joy.active=this.touchMode;
  const jg=joy.addComponent(CompactGraphics);jg.fillColor=new Color(20,17,13,145);jg.circle(0,0,joyRadius);jg.fill();jg.strokeColor=new Color(218,185,127,165);jg.lineWidth=2;jg.circle(0,0,joyRadius);jg.stroke();jg.strokeColor=new Color(218,185,127,110);jg.circle(0,0,joyRadius*.8);jg.stroke();
  for(const [x,y]of [[0,1],[0,-1],[1,0],[-1,0]]){jg.moveTo(x*joyRadius*.76,y*joyRadius*.76);jg.lineTo(x*joyRadius*.88,y*joyRadius*.88);jg.stroke();}this.joystick=this.node('Thumb',joy,0,0,knobRadius*2,knobRadius*2);const knob=this.joystick.addComponent(CompactGraphics);knob.fillColor=new Color(230,209,169,200);knob.circle(0,0,knobRadius);knob.fill();if(this.touchMode)this.pointerTargets.add(joy);
  // ChapterGame owns movement through Cocos input; node cancellation must not reset that finger.
  // One attack-centred circular fan, followed by a regular support grid.
  // Keep native touch sizes while reducing the faces and unused panel padding.
  this.combatAnchor={x:ax,y:ay,unit,attackSize,bottom:combatBottom,joystickRight:left+joySize+8,gap};
  this.iconButton('attack',ax,ay,attackSize,attackSize);
  const skillFace=unit-(this.touchMode?4*pixelScale:4);
  this.dashControl=this.iconButton('dash',ax,ay,unit,skillFace);
  for(const action of ['combat0','combat1','combat2','combat3','ultimate']){
   const n=this.iconButton(action,ax,ay,unit,skillFace,true,'');n.active=false;this.combatControls.set(action,n);
   if(action!=='ultimate'){const index=this.text(n,String(Number(action.slice(6))+1),-skillFace*.32,skillFace*.32,24,this.touchMode?17:11,C.muted,24);index.node.name='SkillSlotIndex';index.horizontalAlign=Label.HorizontalAlign.CENTER;}
  }
  const supplySlots=['potion-health','potion-resource',null,null] as const;
  const supplyHit=this.touchMode?touchMin:52,supplyFace=this.touchMode?Math.min(72,supplyHit):48,supplyStep=supplyHit+gap,padding=4*pixelScale;
  const supplies=this.supplyBelt=this.panel(this.root,0,bottom+supplyHit/2+padding,supplySlots.length*supplyHit+(supplySlots.length-1)*gap+2*padding,supplyHit+2*padding,new Color(19,15,11,226));supplies.name='SupplyBelt';this.pointerTargets.add(supplies);
  supplies.active=this.supplyBeltExpanded;
  supplySlots.forEach((action,index)=>{
   const slot=this.node('SupplySlot'+(index+1),supplies,(index-(supplySlots.length-1)/2)*supplyStep,0,supplyHit,supplyHit);
   if(action)this.iconButton(action,0,0,supplyHit,supplyFace,true,action==='potion-health'?'potion-health':'potion-stamina',slot);
   else{
    UiSkin.asset(slot,'unified-gold-medallion-v13',supplyFace,supplyFace,false);
    UiChrome.circleOrnament(this.node('MetalScrollwork',slot),supplyFace/2);
   }
  });
  this.labels.set('toast',this.text(this.root,'',0,top-72,Math.max(240,Math.min(580,this.width-740)),this.touchMode?24:17,C.ink,70));this.labels.get('toast')!.horizontalAlign=Label.HorizontalAlign.CENTER;
  this.equipmentNotice.mount(Math.min(260*(this.touchMode?pixelScale:1.25),this.labels.get('toast')!.node.getComponent(UITransform)!.width),this.touchMode?pixelScale:1.25);
  this.labels.set('compass',this.text(this.root,'',0,top-22,statsW,this.touchMode?21:14,C.gold,36));this.labels.get('compass')!.horizontalAlign=Label.HorizontalAlign.CENTER;
  this.labels.set('hint',this.text(this.root,this.touchMode?'':'WASD 移动 · Shift 慢行 · 滚轮缩放',0,bottom+132,Math.max(220,Math.min(480,this.width-600)),12,C.muted,24));this.labels.get('hint')!.horizontalAlign=Label.HorizontalAlign.CENTER;
  this.attackRangeY=bottom+220;
  const range=this.text(this.root,'',0,this.attackRangeY,Math.max(260,Math.min(520,this.width-620)),this.touchMode?22:16,C.ink,36);range.node.name='AttackRangeHint';range.horizontalAlign=Label.HorizontalAlign.CENTER;range.enableOutline=true;range.outlineWidth=2;range.outlineColor=new Color(9,7,5,240);range.node.active=false;this.labels.set('attack-range',range);
  this.labels.set('weapon',this.text(this.root,'',ax,bottom-4,unit*2.7,this.touchMode?20:13,C.muted,28));this.labels.get('weapon')!.horizontalAlign=Label.HorizontalAlign.CENTER;
  this.labels.get('weapon')!.node.active=false; // Inventory and the attack tooltip already provide weapon details without a permanent bottom gutter.
  // Native shared glyphs retain stable counters instead of uploading a new
  // whole-label canvas whenever HP, resource, currency or cooldown text changes.
  for(const key of ['health','focus','stats','checks']){const label=this.labels.get(key);if(label)label.cacheMode=Label.CacheMode.CHAR;}
  for(const label of this.cooldownLabels.values())label.cacheMode=Label.CacheMode.CHAR;
  for(const label of this.counts.values())label.cacheMode=Label.CacheMode.CHAR;
  for(const key of ['toast','compass','weapon']){const label=this.labels.get(key)!;label.color=key==='compass'?C.route:C.ink;label.enableOutline=true;label.outlineWidth=2;label.outlineColor=new Color(9,7,5,240);}
  const lane=Math.min(-(left+statsW)-gap,miniX-orbitRadius-toolHit/2-gap);
  this.automationHud=new AutomationHud(this,this.touchMode?pixelScale:1.25,top,Math.max(0,2*lane));
  const trainingHit=this.touchMode?touchMin:48,trainingWidth=this.touchMode?120*pixelScale:160;
  this.trainingButton=this.button(this.root,trainingText('toolbar'),0,top-trainingHit/2,trainingWidth,trainingHit,'training:settings');this.trainingButton.active=false;
  // Use the safe bottom lane above supplies; an aiming gesture must never
  // place its cancel target over the player at the centre of the screen.
  const cancelH=this.touchMode?touchMin:44,cancelW=this.touchMode?Math.max(220,120*pixelScale):150;
  this.aimCancelGap=gap;
  this.cancel=this.panel(this.root,supplies.position.x,bottom+supplies.getComponent(UITransform)!.height+gap+cancelH/2,cancelW,cancelH,C.danger);this.cancel.name='CancelAim';this.text(this.cancel,'移到此处取消',0,0,cancelW-20,this.touchMode?24:16,C.ink,48).horizontalAlign=Label.HorizontalAlign.CENTER;this.cancel.active=false;this.pointerTargets.add(this.cancel);
  this.modal.setSiblingIndex(this.root.children.length-1);
  if(this.portrait){const guard=this.node('RotateToLandscape',this.root,0,0,this.width,this.height),g=guard.addComponent(CompactGraphics);g.fillColor=C.background;g.rect(-this.width/2,-this.height/2,this.width,this.height);g.fill();guard.addComponent(BlockInputEvents);this.pointerTargets.add(guard);this.text(guard,'↻',0,100,200,72,C.gold,110).horizontalAlign=Label.HorizontalAlign.CENTER;this.text(guard,'请横屏继续旅途',0,0,this.width-36,25,C.ink,86).horizontalAlign=Label.HorizontalAlign.CENTER;this.text(guard,'旋转设备后可继续操作\n旅途会在此暂停',0,-95,this.width-40,17,C.muted,90).horizontalAlign=Label.HorizontalAlign.CENTER;}

 }
 refreshMiniMap(game:GameSession,worldCamera:Camera,paused=false){if(this.trainingRange)return;if(paused)this.miniMap?.refreshContacts(game);else this.miniMap?.update(game,worldCamera,this.guidance);}
 update(game:GameSession,worldCamera:Camera,toast:string,save:string,compass='',toastRole:FeedbackRole='text.normal'){
  // The HUD reads level/points only. Detailed gear-derived attributes belong
  // to the character panel, rather than a full equipment scan every frame.
  const s=game.state,p=s.player,weapon=EQUIPMENT[s.equipment.weapon],growth=s.progression,combat=s.combat;
  // setAutomation owns final bar visibility; avoid disabling and re-enabling its labels within every training frame.
  const practice=this.trainingRange;if(this.trainingButton)this.trainingButton.active=!!practice&&!this.portrait&&!this.modal.children.length;const mini=this.root.getChildByName('MiniMapHost')??this.mapDock?.getChildByName('MiniMapHost');if(mini)mini.active=!practice;
  this.refreshMiniMap(game,worldCamera);this.labels.get('checks')!.string=growth.unspentPoints?String(growth.unspentPoints):'';this.labels.get('compass')!.string=compass;this.layoutTopMessages();
  this.labels.get('name')!.string=`拉斐尔 · Lv${growth.level}`;this.labels.get('health')!.string=`生命 ${Math.ceil(p.hp)} / ${p.maxHp}${p.shield>0?` 盾${Math.ceil(p.shield)}`:''}`;
  const resource=resourceProfile(s);this.labels.get('focus')!.string=`${resource.name} ${Math.floor(p.focus)} / ${p.maxFocus}`;F.tint(this.labels.get('focus')!,resource.feedback);this.labels.get('save')!.string=save.startsWith('已保存')?'✓':'·';F.tint(this.labels.get('save')!,save.startsWith('已保存')?'state.success':save==='尚未保存'?'state.failure':'state.idle');
  // Expanded training trackers need the final area caption only, without dirtying it with the campaign area first.
  this.guidanceClock+=director.getDeltaTime();
  if(this.guidanceClock+1e-6>=.2){
   this.guidanceClock=0;const guide=this.guidance;this.setQuestLine('area',practice&&!guide?trainingText(practice.groupMode?'hudGroupArea':'hudArea',{count:practice.groupMode?practice.remainingMonsters:practice.targetCount,total:practice.targetCount,distance:practice.distance}):(AREAS[s.area]?.name??s.area)+(guide?.safe?'·安全区':''));
   this.setQuestLine('quest-distance',guide?guide.blocked?'受阻':guide.distance>=1000?`${(guide.distance/1000).toFixed(1)}km`:`${Math.ceil(guide.distance)}m`:'');
   if(guide){const dx=guide.bearing.x-p.x,dz=guide.bearing.z-p.z,r=worldCamera.node.right,u=worldCamera.node.up,angle=Math.atan2(dx*r.x+dz*r.z,dx*u.x+dz*u.z),arrow=['↑','↗','→','↘','↓','↙','←','↖'][(Math.round(angle/(Math.PI/4))+8)%8];this.setQuestLine('objective',guide.blocked?'路线受阻':`${arrow} ${guide.instruction}`);this.setQuestLine('quest-route',guide.blocked?'打开旅程查看':guide.hops?`出口 ${Math.ceil(guide.distance)}m · ${AREAS[guide.nextArea??guide.destination.area].name}`:guide.distance>2?`${Math.ceil(guide.distance)}m · ${guide.detail}`:guide.detail);}
   else if(practice){this.setQuestLine('objective',trainingText(practice.groupMode?'hudGroupProgress':'hudDamage',{damage:practice.damage,hits:practice.hits,kills:practice.defeatedMonsters,total:practice.targetCount}));this.setQuestLine('quest-route',trainingText('hudDps',{dps:Math.round(practice.dps)}));}
   else{this.setQuestLine('objective',game.objective());this.setQuestLine('quest-route','点击查看旅程');}
  }
  this.labels.get('stats')!.string=`金币 ${p.gold}`;
  this.labels.get('weapon')!.string=weapon?.name??'';this.labels.get('toast')!.string=toast;F.tint(this.labels.get('toast')!,toastRole);const healthRole=playerHealthFeedbackRole(p.hp,p.maxHp);F.tint(this.labels.get('health')!,healthRole==='health.player'?'health.text':healthRole);F.tint(this.labels.get('stats')!,'reward.gold');
  for(const[fill,value,max,role]of [[this.health,p.hp,p.maxHp,'health.player'],[this.focus,p.focus,p.maxFocus,resource.feedback]]as const){F.bar(fill,value,max,role);fill.node.active=value>0;}
  if(this.portraitRing&&p.hp!==this.lastHealth){this.lastHealth=p.hp;const g=this.portraitRing;g.clear();UiChrome.drawCircle(g,35);g.lineWidth=2;F.ink(g,playerHealthFeedbackRole(p.hp,p.maxHp),'stroke');const fraction=Math.max(0,p.hp/p.maxHp);if(fraction>0){g.moveTo(0,-37);g.arc(0,0,37,-Math.PI/2,-Math.PI/2+Math.PI*2*fraction,true);g.stroke();}}
  if(this.skillPointMark)this.skillPointMark.active=game.state.progression.skillPoints>0;
  const actions:Record<string,string>={combat0:combat.activeSlots[0],combat1:combat.activeSlots[1],combat2:combat.activeSlots[2],combat3:combat.activeSlots[3],ultimate:combat.ultimate,dash:'COM_01'};
  const loadout=assignedLoadout(combat),skillViews=game.combatSkillView(Object.entries(actions).map(([action,id])=>id??(action.startsWith('combat')?loadout?.activeSlots[Number(action.slice(6))]:action==='ultimate'?loadout?.ultimate:'')).filter(id=>!!id));
  const visible=['combat0','combat1','combat2','combat3','ultimate'];
  this.layoutCombatControls(visible);
  this.buttonLabels.get('attack')!.string=weapon?.kind==='bow'?(this.touchMode?'蓄箭':'蓄力箭'):weapon?.kind==='staff'?'杖弹':'攻击';
  this.skillIconGroup=combat.family??'';
  this.setActionIcon('attack',weapon?.kind==='bow'?'bow':weapon?.kind==='staff'?'staff':'attack');
  this.tooltips.set('attack',`${weapon?.name??'基础攻击'} · 射程${game.basicAttackProfile().rangeMetres}米 · J / 鼠标左键`);
  for(const [action,label]of this.cooldownLabels){
   if(action==='potion-health'||action==='potion-resource'){
    const health=action==='potion-health',stock=health?p.healthPotions:p[resource.stock],remaining=s.cooldowns.consumable??0,full=health?p.hp>=p.maxHp:p.focus>=p.maxFocus,busy=!!s.action||!!s.dialogue||!!s.dice.active||s.status==='dead';
    this.counts.get(action)!.string=String(stock);this.counts.get(action)!.color=stock>0?C.ink:C.red;
    label.string=remaining>1e-6?remaining.toFixed(1):'';label.node.active=remaining>1e-6;
    const shade=this.cooldownShades.get(action)!;shade.active=remaining>1e-6;const sprite=shade.getComponent(Sprite)!;if(sprite.spriteFrame)sprite.fillRange=-Math.min(1,remaining/5);
    const icon=this.actionIcons.get(action)!;icon.node.parent!.getComponent(Button)!.interactable=stock>0&&!full&&!busy&&remaining<=1e-6;F.tint(icon,stock<=0?'text.disabled':health?'damage.taken':resource.feedback);this.setDisabledShade(action,stock<=0||full);
    if(action==='potion-resource')this.setActionIcon(action,resource.icon);
    this.tooltips.set(action,stock<=0?'补给已用尽 · 在安全检查点补满':full?`${health?'生命':resource.name}已满 · 无需使用药水`:health?'5 · 恢复40%生命（至少40点）· 共享5秒药水冷却':`6 · ${resource.potion} · 恢复45%${resource.name}上限 · 共享5秒药水冷却`);continue;
   }
   if(action==='attack'){this.cooldownShades.get(action)!.active=false;this.setDisabledShade(action,false);this.counts.get(action)!.string='';label.node.active=false;continue;}
   const ghost=(action.startsWith('combat')||action==='ultimate')&&!actions[action],id=actions[action]??(ghost?(action==='ultimate'?loadout?.ultimate:loadout?.activeSlots[Number(action.slice(6))]):null),def=COMBAT_SKILLS[id??''],v=skillViews.find(v=>v.id===id),rank=def?.ranks[Math.max(0,(v?.rank??1)-1)],remaining=ghost?0:v?.cooldown??0;
   const blocked=ghost||!v?.unlocked||!v.compatible||!v.resourceEnough;
   const name=this.buttonLabels.get(action)!;name.string=ghost?'':def?(this.touchMode?def.name.slice(0,2):def.name):'';name.node.active=!ghost&&this.showSkillNames;
   this.counts.get(action)!.string='';
   label.string=remaining>0?remaining.toFixed(1):'';label.node.active=remaining>0;
   const shade=this.cooldownShades.get(action)!;shade.active=remaining>0;const sprite=shade.getComponent(Sprite)!;
   if(sprite.spriteFrame)sprite.fillRange=-Math.min(1,remaining/Math.max(.1,rank?.cooldownSeconds??1));
   const icon=this.actionIcons.get(action)!;icon.node.active=!ghost;name.node.parent!.getComponent(Button)!.interactable=!ghost&&!!v?.ready&&s.status!=='dead';
   this.setDisabledShade(action,blocked);F.tint(icon,blocked?'text.disabled':s.action?.skillId===id?'state.running':'icon.normal');
   this.setActionIcon(action,ghost?'':COMBAT_SKILL_ICONS[id??'']??'');
   const reason=!v?.unlocked?`角色Lv${v?.requiredLevel??1}解锁`:!v.compatible?def?skillWeaponRequirement(def):'需要装备对应武器':!v.resourceEnough?`${resource.name}不足，需${v.resourceCost}点；可普攻或使用药水`:remaining>0?'技能冷却中':`${v.resourceCost?`消耗${v.resourceCost}${resource.name} · `:''}${rank?.castRangeMetres??0}米 · ${this.skillAimMode==='auto'?'轻点锁定最近怪物，拖动手动瞄准':'手动瞄准，松开释放'}`;
   this.tooltips.set(action,`${KEYS[action]} · ${def?.name??'空技能位'} · ${reason}`);
  }
 }
 private setDisabledShade(action:string,visible:boolean):void {
  const shade=this.disabledShades.get(action)!;
  shade.active=visible;shade.parent!.active=visible;
 }
 private layoutCombatControls(visible:string[]):void {
  const arc=['combat0','combat1','ultimate','combat3'],utilities=['dash','combat2'],key=utilities.join('|');if(key===this.combatLayoutKey)return;this.combatLayoutKey=key;
  this.combatArcActions=arc;this.combatUtilityActions=utilities;
  const {x,y,unit,attackSize,bottom,joystickRight,gap}=this.combatAnchor,step=unit+gap;
  const angleStep=arc.length>1?COMBAT_ARC_SPAN/(arc.length-1):0,radius=Math.max((attackSize+unit)/2+gap,arc.length>1?step/(2*Math.sin(angleStep/2)):0);
  for(const [action,node]of this.combatControls)node.active=visible.includes(action);
  arc.forEach((action,i)=>{const angle=COMBAT_ARC_CENTER+(arc.length===1?0:COMBAT_ARC_SPAN/2-i*angleStep);this.combatControls.get(action)!.setPosition(x+Math.cos(angle)*radius,y+Math.sin(angle)*radius);});
  const arcLeft=arc.length?Math.min(...arc.map(action=>this.combatControls.get(action)!.position.x-unit/2)):x-attackSize/2;
  const utilityX=arcLeft-gap-unit/2,utilityY=bottom+unit/2,columns=Math.ceil(utilities.length/2);
  utilities.forEach((action,i)=>{const node=action==='dash'?this.dashControl!:this.combatControls.get(action)!;node.setPosition(utilityX-Math.floor(i/2)*step,utilityY+(i%2)*step);});
  // Centre the four supply slots as one group. On short screens clamp
  // the complete belt into the free bottom lane between the two thumb controls.
  const belt=this.supplyBelt!,beltSize=belt.getComponent(UITransform)!,laneLeft=joystickRight+gap,laneRight=utilityX-(columns-1)*step-unit/2-gap;
  const beltX=Math.max(laneLeft+beltSize.width/2,Math.min(0,laneRight-beltSize.width/2));belt.setPosition(beltX,belt.position.y);this.cancel.setPosition(beltX,this.cancel.position.y);
  this.layoutMapDock();
 }
 private layoutMapDock():void {
  const dock=this.mapDock;if(!dock)return;const {gap}=this.combatAnchor,controls=Array.from(this.combatControls.values()).concat(this.dashControl!).filter(n=>n.active);
  // Slide the complete attached compass along the top edge on short screens;
  // never detach a tool or cover a combat control to preserve the decoration.
  let x=this.mapDockHome.x;const y=this.mapDockHome.y;
  for(let attempt=0;attempt<80;attempt++){
   const clear=this.mapDockSlots.every(slot=>controls.every(n=>{
    const radius=n.getComponent(UITransform)!.width/2,p=n.position,margin=slot.interactive?gap:gap/2;
    return Math.hypot(x+slot.node.position.x-p.x,y+slot.node.position.y-p.y)>=slot.radius+radius+margin;
   }));if(clear)break;x-=4;
  }
  dock.setPosition(x,y);
 }
 private setQuestLine(key:QuestTrackerLine,value:string){this.questTracker?.setLine(key,value);}
 setAutomation(mode:AutomationMode,navigating:boolean,status:string,visible:boolean,paused=false,taskId?:string,experience?:AutomationExperience){
  this.automationState.mode=mode;this.automationState.navigating=navigating;this.automationState.status=status;this.automationState.paused=paused;this.automationState.taskId=taskId;this.automationState.experience=experience;
  this.automationHud?.update(this.automationState,visible);if(this.navigationButton)this.navigationButton.active=visible;
  const arrived=!!this.guidance&&!this.guidance.blocked&&!this.guidance.hops&&this.guidance.distance<=1.35;
  const navigationPaused=paused&&mode==='manual';
  const feedback=navigationFeedback({navigating,paused:navigationPaused,arrived,blocked:!!this.guidance?.blocked});this.miniMap?.setNavigationFeedback(feedback.role);
  // Resolve the final caption once: alternating navigation/training text dirties and uploads the label every frame.
  const practice=!!this.trainingRange&&!this.guidance;
  if(this.automationLabel)this.automationLabel.string=practice?trainingText('toolbar'):navigating?'停止':navigationPaused?'继续':arrived?'抵达':'出发';
  this.questTracker?.setFeedback(feedback.role);
  if(this.navigationButton)this.navigationButton.getComponent(Button)!.interactable=practice||navigating||navigationPaused||!!this.guidance&&!this.guidance.blocked&&!arrived;
  this.layoutTopMessages();
 }
 setAimCancelVisible(visible:boolean):void {
  this.cancel.active=visible;
  const hint=this.labels.get('hint');if(hint)hint.node.active=!visible;
  const range=this.labels.get('attack-range');if(range){const top=this.cancel.position.y+this.cancel.getComponent(UITransform)!.height/2;range.node.setPosition(0,visible?Math.max(this.attackRangeY,top+this.aimCancelGap+range.node.getComponent(UITransform)!.height/2):this.attackRangeY);}
 }
 setAttackRangeHint(text:string,valid=true){const label=this.labels.get('attack-range');if(!label)return;label.string=text;label.color=valid?C.ink:C.red;label.node.active=!!text;}
 private layoutTopMessages(){
  const top=this.trainingButton?.active?this.trainingButton.position.y-this.trainingButton.getComponent(UITransform)!.height/2-12:this.automationHud?.visible?this.automationHud.bottom-12:this.height/2-22,compass=this.labels.get('compass'),passiveVisible=!this.automationExpanded&&!this.modal.children.length,toast=this.labels.get('toast');
  if(compass){compass.node.active=passiveVisible;if(compass.node.position.y!==top-18)compass.node.setPosition(0,top-18);}
  if(toast){const y=top-(compass?.string?83:35);this.equipmentNotice.layout(0,y,this.equipmentPickupsAvailable&&passiveVisible&&!this.portrait);toast.node.active=passiveVisible&&!this.equipmentNotice.visible;if(toast.node.position.y!==y)toast.node.setPosition(0,y);}
 }
 private setActionIcon(action:string,path:string){
  const group=this.isSkillControl(action)?this.skillIconGroup:'';
  if(this.iconPaths.get(action)===path&&this.iconGroups.get(action)===group)return;
  this.iconPaths.set(action,path);this.iconGroups.set(action,group);
  const icon=this.actionIcons.get(action)!;icon.spriteFrame=null;
  // Retire the previous image after its last draw, including pending requests.
  // Switching professions must not keep every visited atlas on this HUD node.
  UiSkin.releaseOwner(icon.node);
  const diameter=this.actionDiameters.get(action);if(diameter)this.layoutActionIcon(action,diameter);
  if(!path)return;
  void UiSkin.hudSkillFrame(this.actionIconPath(action,path),icon.node,group).then(frame=>{if(icon.isValid&&this.iconPaths.get(action)===path&&this.iconGroups.get(action)===group)icon.spriteFrame=frame;}).catch(()=>{});
 }
 isOverUI(screenPoint:Vec2):boolean {if(this.automationHud?.contains(screenPoint))return true;for(const node of this.pointerTargets)if(node.isValid&&node.activeInHierarchy&&node.getComponent(UITransform)?.hitTest(screenPoint))return true;return false;}
 clearModal(){for(const dispose of Array.from(this.modalDisposers))dispose();this.modalDisposers.clear();this.mapPanel.hide();for(const child of [...this.modal.children])child.destroy();this.modal.removeAllChildren();}
 show(title:string,body:string,buttons:MenuChoice[],wide=false,presentation:MenuPresentation={}){
  new MenuPanel(this,{width:wide?1000:undefined,...presentation}).show(title,body,buttons);
 }
 showList(title:string,subtitle:string,rows:MenuRow[],footer:MenuChoice[],minimumHit=0,presentation:MenuPresentation={}){
  new MenuPanel(this,{placement:'right',...presentation},minimumHit).showList(title,subtitle,rows,footer);
 }
 atlas(game:GameSession,visited:Record<string,boolean>,selected?:string){this.mapPanel.show(game,visited,selected);}
 atlasKey(code:number):boolean{return this.mapPanel.key(code);}
 // Button.onDisable restores the child target's scale; disable every nested button before destroying any faces.
 private deactivateControls(node:Node){for(const button of node.getComponentsInChildren(Button))button.enabled=false;node.active=false;}
 resize(){const pixels=screen.windowSize;if(pixels.width!==this.pixelWidth||pixels.height!==this.pixelHeight){this.pixelWidth=pixels.width;this.pixelHeight=pixels.height;director.root?.resize(pixels.width,pixels.height);view.setDesignResolutionSize(UI_DESIGN_SIZE.width,UI_DESIGN_SIZE.height,ResolutionPolicy.FIXED_HEIGHT);}const s=view.getVisibleSize();if(Math.abs(s.width-this.width)<1&&Math.abs(s.height-this.height)<1){this.mapPanel.refreshLayout();return false;}const obsolete=this.root.children.filter(child=>child!==this.modal&&child.name!=='CampaignScene');for(const child of obsolete)this.deactivateControls(child);this.miniMap?.destroy();this.miniMap=null;for(const child of obsolete)child.destroy();this.labels.clear();this.build();return true;}
 destroy(){this.deactivateControls(this.root);this.miniMap?.destroy();this.clearModal();this.root.destroy();this.camera.node.destroy();}
}
