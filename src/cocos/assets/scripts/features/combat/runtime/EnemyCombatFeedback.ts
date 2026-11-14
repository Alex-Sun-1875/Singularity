import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {Camera,Color,Graphics,Label,Node,Sprite,SpriteFrame,Texture2D,UITransform,UIOpacity,Vec3,builtinResMgr,screen,sys,isValid,director,Director} from 'cc';
import type {GameEvent,Point} from '../../../core/Contracts';
import type {EnemyState,GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import {damageFeedbackRole,type FeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {enemyDisplayName,bossKind} from '../common/BossAwareness';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';

type HealthBar={id:string;node:Node;fill:Node;lag:Node;skin:Graphics;drawnFraction:number;drawnLag:number;drawnOpaque:boolean;name:Label;opacity:UIOpacity;until:number;deathUntil:number;fraction:number;lagFraction:number;width:number;lastHp:number;point:Vec3};
type TextKind='miss'|'damage'|'taken'|'heal'|'absorbed';
type CombatText={id:string;kind:TextKind;role:FeedbackRole;value:number;critical:boolean;lane:number;node:Node;label:Label;opacity:UIOpacity;start:number;until:number;point:Vec3};
type FeedbackTarget=Pick<EnemyState,'id'|'x'|'z'>&Partial<Pick<EnemyState,'kind'|'bossId'>>;
const PLAYER_ID='$player';
// Match the existing encounter limit; allocate only for enemies in the viewport.
const BAR_LIMIT=200,TEXT_LIMIT=24,MISS_SECONDS=.72;
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const scaleX=(node:Node,x:number)=>{const s=node.scale;if(s.x!==x||s.y!==1||s.z!==1)node.setScale(x,1,1);};
const DARK=F.color('text.outline',238),BORDER=F.color('health.enemy');

/** Head-level feedback observes authoritative HP loss, elements and hit outcomes.
 * It never rolls hit chance, infers misses from zero damage, or changes combat.
 * All nodes are bounded pools; positions, opacity and health geometry vary. */
export class EnemyCombatFeedback {
 private static readonly glyphScenes=new WeakSet<Node>();
 async prepareTextGlyphs():Promise<void>{
  if(this.disposed)return;
  this.ensureRoot();while(this.texts.length<TEXT_LIMIT)this.createText();
  const scene=this.hud.root.scene;if(!scene||EnemyCombatFeedback.glyphScenes.has(scene))return;
  const node=this.hud.node('CombatGlyphWarmup',this.hud.root,0,0,900,80),label=this.hud.text(node,'0123456789暴击 吸收 +-',0,0,900,25,F.color('damage.physical'),80);
  label.overflow=Label.Overflow.CLAMP;label.cacheMode=Label.CacheMode.CHAR;
  try{
   for(const critical of [false,true]){
    if(this.disposed||!isValid(node,true))return;
    label.fontSize=critical?(sys.isMobile?30:27):(sys.isMobile?25:22);label.lineHeight=label.fontSize*1.2;
    // Warm only common bow/received-hit text, leaving the shared 1024px atlas
    // available for other styles and the HUD on larger phone viewports.
    for(const role of (critical?['damage.physical']:['damage.physical','damage.taken','damage.miss','state.success']) as readonly FeedbackRole[]){
     label.string=role==='damage.miss'?'MISS':role==='state.success'?'闪避':critical?'0123456789暴击 ':'-0123456789';
     F.combatText(label,role,critical);label.updateRenderData(true);
    }
    node.active=false;await new Promise<void>(resolve=>director.once(Director.EVENT_AFTER_DRAW,resolve));
   }
   if(!this.disposed)EnemyCombatFeedback.glyphScenes.add(scene);
  }finally{if(isValid(node,true)){node.active=false;node.destroy();}}
 }
 private root:Node|undefined;
 private readonly bars:HealthBar[]=[];
 private readonly texts:CombatText[]=[];
 private playerHp:number|undefined;private playerMaxHp=0;
 private readonly lastHp=new Map<string,number>();
 private readonly seen=new Set<string>();
 private area='';private lastTime=-1;private disposed=false;
 private readonly projected=new Vec3();
 private readonly anchor=new Vec3();
 private readonly foot=new Vec3();
 private readonly worldFoot=new Vec3();
 private projectionEpoch=0;private cacheProjection=false;
 private readonly projections=new Map<string,{epoch:number;x:number;y:number;footY:number}>();
 private fillFrame:SpriteFrame|undefined;

 constructor(private readonly hud:Hud,private readonly camera:Camera,private readonly world:SceneBuilder,private readonly headPoint?:(id:string)=>Vec3|undefined){}

 private ensureRoot(){
  if(isValid(this.root,true))return;
  this.bars.length=0;this.texts.length=0;
  this.root=this.hud.node('EnemyCombatFeedback',this.hud.root,0,0,1,1);
  // World labels remain below the portrait, controls and modals.
  this.root.setSiblingIndex(0);
 }

 private head(enemy:FeedbackTarget,out:Vec3):Vec3 {
  const authored=this.headPoint?.(enemy.id);
  if(authored)return out.set(authored);
  out.set(enemy.x,this.world.height(enemy),enemy.z);
  // Flat character height is authored in the same camera plane as its sprite.
  const height=enemy.bossId||enemy.kind==='captain'?2.35:1.85;
  out.add(Vec3.multiplyScalar(this.projected,this.camera.node.up,height));return out;
 }

 private viewportWidth=1;private viewportHeight=1;
 private refreshViewport(){const pixels=screen.windowSize;this.viewportWidth=Math.max(1,pixels.width);this.viewportHeight=Math.max(1,pixels.height);}
 private project(enemy:FeedbackTarget,extraY:number,point:Vec3):boolean {
  let projected=this.cacheProjection?this.projections.get(enemy.id):undefined;
  if(!projected||projected.epoch!==this.projectionEpoch){
   this.head(enemy,this.anchor);this.camera.worldToScreen(this.anchor,this.projected);
   const x=this.projected.x/this.viewportWidth*this.hud.width-this.hud.width/2;
   const y=this.projected.y/this.viewportHeight*this.hud.height-this.hud.height/2;
   if(!Number.isFinite(x+y)||this.projected.z<0||this.projected.z>1)return false;
   this.worldFoot.set(enemy.x,this.world.height(enemy),enemy.z);this.camera.worldToScreen(this.worldFoot,this.foot);
   const footY=this.foot.y/this.viewportHeight*this.hud.height-this.hud.height/2;
   if(!projected)projected={epoch:this.projectionEpoch,x,y,footY};else {projected.epoch=this.projectionEpoch;projected.x=x;projected.y=y;projected.footY=footY;}
   if(this.cacheProjection)this.projections.set(enemy.id,projected);
  }
  const x=projected.x,y=projected.y+extraY,footY=projected.footY,halfW=this.hud.width/2,halfH=this.hud.height/2;
  if(Math.abs(x)>halfW+16||Math.min(y-extraY,footY)>halfH||Math.max(y-extraY,footY)<-halfH)return false;
  point.set(Math.max(-halfW+40,Math.min(halfW-40,x)),Math.max(-halfH+20,Math.min(halfH-42,y)),0);return true;
 }
 private place(node:Node,enemy:FeedbackTarget,extraY:number,point:Vec3):boolean {if(!this.project(enemy,extraY,point))return false;const p=node.position;if(p.x!==point.x||p.y!==point.y||p.z!==point.z)node.setPosition(point);return true;}

 private createBar():HealthBar {
  const node=this.hud.node('EnemyHealth',this.root!,0,0,68,10),skin=node.addComponent(CompactGraphics),opacity=node.addComponent(UIOpacity);
  // Retain the original left-anchored sprites for the lethal opacity fade.
  // At full opacity their two rectangles share the existing background geometry.
  if(!this.fillFrame){this.fillFrame=new SpriteFrame();this.fillFrame.packable=false;this.fillFrame.texture=builtinResMgr.get<Texture2D>('white-texture');}
  const layer=(name:string,color:Color)=>{const n=this.hud.node(name,node,-31,0,62,5);n.getComponent(UITransform)!.setAnchorPoint(0,.5);const sprite=n.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.spriteFrame=this.fillFrame!;sprite.color=color;return n;};
  const lag=layer('RecentHealthLoss',F.color('health.loss')),fill=layer('CurrentHealth',F.color('health.enemy'));
  const name=this.hud.text(node,'',0,sys.isMobile?21:17,230,sys.isMobile?22:16,F.color('text.normal'),30);name.horizontalAlign=Label.HorizontalAlign.CENTER;name.enableOutline=true;name.outlineWidth=2;name.outlineColor=DARK;
  node.active=false;const bar={id:'',node,fill,lag,skin,drawnFraction:-1,drawnLag:-1,drawnOpaque:true,name,opacity,until:0,deathUntil:0,fraction:1,lagFraction:1,width:68,lastHp:0,point:new Vec3()};this.bars.push(bar);return bar;
 }

 /** Preserve each bar's background/fills/name order, including overlapping bars.
  * Only damaged bars retessellate while the delayed loss strip animates. */
 private drawBar(bar:HealthBar):void {
  const fraction=bar.fraction,lag=Math.max(fraction,bar.lagFraction),opaque=bar.opacity.opacity===255;
  // Native Graphics and Sprite apply inherited opacity differently. During the
  // original short lethal fade, retain the original two sprite fills exactly.
  bar.fill.active=bar.lag.active=!opaque;
  if(!opaque){scaleX(bar.fill,fraction);scaleX(bar.lag,lag);}
  if(bar.drawnOpaque===opaque&&(!opaque||bar.drawnFraction===fraction&&bar.drawnLag===lag))return;
  bar.drawnFraction=fraction;bar.drawnLag=lag;bar.drawnOpaque=opaque;const g=bar.skin;g.clear();
  g.fillColor=DARK;g.strokeColor=BORDER;g.lineWidth=1;
  g.roundRect(-34,-5,68,10,2);g.fill();g.stroke();
  if(opaque){
   if(lag>0){F.ink(g,'health.loss');g.rect(-31,-2.5,62*lag,5);g.fill();}
   if(fraction>0){F.ink(g,'health.enemy');g.rect(-31,-2.5,62*fraction,5);g.fill();}
  }
 }

 private showHealth(enemy:EnemyState,now:number,damage=0,finishing=false){
  if(enemy.hp<=0&&!finishing)return;this.ensureRoot();
  let bar=this.bars.find(item=>item.id===enemy.id);
  if(!bar)bar=this.bars.find(item=>!item.id)|| (this.bars.length<BAR_LIMIT?this.createBar():this.bars.reduce((a,b)=>a.until<b.until?a:b));
  const fraction=clamp(enemy.hp/Math.max(1,enemy.maxHp)),known=this.lastHp.get(enemy.id);
  if(bar.id!==enemy.id){bar.lagFraction=clamp((known??enemy.hp+damage)/Math.max(1,enemy.maxHp));bar.lastHp=enemy.hp;}
  else bar.lagFraction=Math.max(bar.lagFraction,bar.fraction);
  // A real lethal contact still needs a readable emptying health bar. This
  // short finish is never created by merely observing an already dead enemy.
  bar.id=enemy.id;bar.fraction=fraction;bar.lastHp=enemy.hp;bar.until=finishing?now+.28:0;bar.deathUntil=bar.until;bar.opacity.opacity=255;bar.node.active=true;
  bar.name.string=enemyDisplayName(enemy);
  bar.name.node.active=true;
  F.tint(bar.name,bossKind(enemy)==='elite'?'identity.elite':enemy.bossId||enemy.kind==='captain'?'identity.boss':'identity.neutral');
 }

 private showText(id:string,kind:TextKind,now:number,value=0,role:FeedbackRole='damage.miss',critical=false,caption?:string){
  this.ensureRoot();
  let item=this.texts.find(text=>text.id===id&&text.kind===kind&&text.role===role&&text.critical===critical&&text.until>now&&(kind==='miss'||now-text.start<.12));
  const accumulated=!!item;item??=this.texts.find(text=>!text.id);
  if(!item&&this.texts.length<TEXT_LIMIT)item=this.createText();
  item??=this.texts.reduce((a,b)=>a.until<b.until?a:b);
  if(!accumulated){item.start=now;item.value=0;item.lane=this.texts.filter(text=>text!==item&&text.id===id&&text.until>now).length%3;}
  if(kind==='miss')item.start=now;
  item.id=id;item.kind=kind;item.role=role;item.critical=critical;item.value+=Math.max(0,value);item.until=now+MISS_SECONDS;
  item.label.fontSize=critical?(sys.isMobile?30:27):(sys.isMobile?25:22);item.label.lineHeight=item.label.fontSize*1.2;
  item.label.string=kind==='miss'?(caption??'MISS'):`${critical?'暴击 ':''}${kind==='heal'?'+':kind==='taken'?'-':kind==='absorbed'?'吸收 ':''}${Math.round(item.value)}`;
  F.combatText(item.label,role,critical);
  // A bounded numeric alphabet reuses native glyphs across simultaneous hits.
  // Long values/captions keep SHRINK, which CHAR does not support in 3.8.8.
  const cached=kind==='miss'?item.label.string==='MISS'||item.label.string==='闪避':Math.round(item.value)<100000;
  item.label.overflow=cached?Label.Overflow.CLAMP:Label.Overflow.SHRINK;
  item.label.cacheMode=cached?Label.CacheMode.CHAR:Label.CacheMode.NONE;
  item.opacity.opacity=255;item.node.active=true;
 }
 private createText():CombatText {
  const node=this.hud.node('CombatText',this.root!,0,0,170,46),label=this.hud.text(node,'',0,0,170,25,F.color('damage.physical'),46);
  label.horizontalAlign=Label.HorizontalAlign.CENTER;node.active=false;
  const item:CombatText={id:'',kind:'damage',role:'damage.physical',value:0,critical:false,lane:0,node,label,opacity:node.addComponent(UIOpacity),start:0,until:0,point:new Vec3()};this.texts.push(item);return item;
 }

 onEvents(events:readonly GameEvent[],game:GameSession):void {
  if(this.disposed||!events.length)return;this.refreshViewport();const state=game.state;
  if(this.area&&this.area!==state.area)this.clear();this.area=state.area;
  const damage=new Map<string,number>();
  for(const event of events){
   if(event.type==='hit'&&event.id&&Number(event.hpLost)>0){
    const value=Number(event.hpLost);damage.set(event.id,(damage.get(event.id)??0)+value);
    this.showText(event.id,'damage',state.time,value,damageFeedbackRole(String(event.element)),event.critical===true);
   }
   if(event.type==='hurt'){
    if(Number(event.hpLost)>0)this.showText(PLAYER_ID,'taken',state.time,Number(event.hpLost),'damage.taken');
    if(Number(event.absorbed)>0)this.showText(PLAYER_ID,'absorbed',state.time,Number(event.absorbed),'damage.absorbed');
   }
   if(event.type==='area'||event.type==='travel'||event.type==='retry'){this.clear();continue;}
   if(event.type==='defeat'&&event.id){this.hideTarget(event.id);continue;}
   if(event.type!=='miss'||!event.id)continue;
   const missId=event.id==='player'?PLAYER_ID:event.id;
   const enemy=state.enemies.find(e=>e.id===missId&&e.hp>0);if(!enemy&&missId!==PLAYER_ID)continue;
   const identity=String(event.action??event.castId??event.projectileId??state.time.toFixed(4));
   const key=`${event.id}:${identity}:${event.projectileId??''}:${event.segment??''}`;
   if(this.seen.has(key))continue;this.seen.add(key);if(this.seen.size>256)this.seen.delete(this.seen.values().next().value!);
   this.showText(missId,'miss',state.time,0,missId===PLAYER_ID?'state.success':'damage.miss',false,missId===PLAYER_ID?'闪避':undefined);
  }
  for(const [id,value]of damage){const enemy=state.enemies.find(e=>e.id===id);if(enemy)this.showHealth(enemy,state.time,value,enemy.hp<=0);}
 }

 update(game:GameSession,paused=false):void {
  if(this.disposed)return;this.refreshViewport();const state=game.state,now=state.time;
  if(paused||state.status==='dead'||this.area&&this.area!==state.area||now<this.lastTime){this.clear();this.area=state.area;this.lastTime=now;return;}
  this.ensureRoot();this.area=state.area;const dt=this.lastTime<0?0:Math.max(0,Math.min(.1,now-this.lastTime));this.lastTime=now;
  if(this.playerHp!==undefined&&state.player.maxHp===this.playerMaxHp&&state.player.hp>this.playerHp)this.showText(PLAYER_ID,'heal',now,state.player.hp-this.playerHp,'damage.heal');
  this.playerHp=state.player.hp;this.playerMaxHp=state.player.maxHp;
  this.projectionEpoch++;this.cacheProjection=true;
  try{
  const enemies=new Map(state.enemies.map(enemy=>[enemy.id,enemy]));
  // Free offscreen/dead slots before assigning bars to newly visible enemies.
  for(const bar of this.bars){const enemy=enemies.get(bar.id);if(bar.id&&(!enemy||enemy.hp<=0&&bar.deathUntil<=now||!this.project(enemy,12,bar.point))){bar.id='';if(isValid(bar.node,true))bar.node.active=false;}}
  for(const enemy of state.enemies){
   const previous=this.lastHp.get(enemy.id);
   // Covers authoritative HP changes even if a future damage source omits its
   // optional presentation event. It still cannot manufacture a MISS.
   if(enemy.hp>0&&this.project(enemy,12,this.anchor))this.showHealth(enemy,now,previous!==undefined?Math.max(0,previous-enemy.hp):0);
   this.lastHp.set(enemy.id,enemy.hp);
  }
  for(const id of this.lastHp.keys())if(!enemies.has(id))this.lastHp.delete(id);
  for(const bar of this.bars){
   if(!bar.id)continue;const enemy=enemies.get(bar.id),finishing=bar.deathUntil>now&&enemy?.hp===0;
   if(!enemy||enemy.hp<=0&&!finishing||!this.place(bar.node,enemy,12,bar.point)){bar.id='';if(isValid(bar.node,true))bar.node.active=false;continue;}
   bar.fraction=clamp(enemy.hp/Math.max(1,enemy.maxHp));
   bar.lagFraction=Math.max(bar.fraction,bar.lagFraction-dt*(finishing?1/.22:.65));
   bar.opacity.opacity=finishing?Math.round(255*clamp((bar.deathUntil-now)/.15)):255;this.drawBar(bar);bar.node.active=true;
  }
  for(const item of this.texts){
   if(!item.id)continue;const enemy=enemies.get(item.id),target:FeedbackTarget|undefined=item.id===PLAYER_ID?{id:PLAYER_ID,x:state.player.x,z:state.player.z}:enemy,progress=clamp((now-item.start)/MISS_SECONDS);
   // Transient attack text stays above the single permanent name/health band.
   const baseY=item.id===PLAYER_ID?30:78;
   if(!target||item.kind==='miss'&&enemy?.hp===0||now>=item.until||!this.project(target,baseY+item.lane*24+progress*40,item.point)){item.id='';item.node.active=false;continue;}
   const x=item.point.x+(item.lane===1?-18:item.lane===2?18:0),p=item.node.position;if(p.x!==x||p.y!==item.point.y||p.z!==0)item.node.setPosition(x,item.point.y,0);
   item.opacity.opacity=Math.round(255*clamp((1-progress)/.55));item.node.active=true;
  }
  }finally{this.cacheProjection=false;}
 }

 private hideTarget(id:string){for(const bar of this.bars)if(bar.id===id){bar.id='';if(isValid(bar.node,true))bar.node.active=false;}for(const text of this.texts)if(text.id===id&&text.kind==='miss'){text.id='';if(isValid(text.node,true))text.node.active=false;}}
 clear(){for(const bar of this.bars){bar.id='';if(isValid(bar.node,true))bar.node.active=false;}for(const item of this.texts){item.id='';if(isValid(item.node,true))item.node.active=false;}this.lastHp.clear();this.seen.clear();this.lastTime=-1;this.playerHp=undefined;}
 inspect(){return{alwaysVisible:true,barLimit:BAR_LIMIT,textLimit:TEXT_LIMIT,allocatedBars:this.bars.length,allocatedTexts:this.texts.length,bars:this.bars.filter(bar=>bar.id&&bar.node.activeInHierarchy).map(bar=>({id:bar.id,hp:bar.lastHp,fraction:bar.fraction,finishing:bar.deathUntil>this.lastTime,persistent:bar.lastHp>0,color:F.color('health.enemy').toHEX(),remaining:bar.deathUntil>this.lastTime?bar.deathUntil-this.lastTime:null,position:{x:bar.point.x,y:bar.point.y}})),texts:this.texts.filter(text=>text.id&&text.node.activeInHierarchy).map(text=>({id:text.id,kind:text.kind,role:text.role,value:text.value,critical:text.critical,text:text.label.string,color:text.label.color.toHEX()})),misses:this.texts.filter(text=>text.kind==='miss'&&text.id&&text.node.activeInHierarchy).map(text=>({id:text.id,text:text.label.string,remaining:text.until-this.lastTime,opacity:text.opacity.opacity,position:{x:text.point.x,y:text.point.y}}))};}
 destroy(){if(this.disposed)return;this.clear();this.disposed=true;if(isValid(this.root,true))this.root.destroy();this.fillFrame?.destroy();this.fillFrame=undefined;this.root=undefined;this.bars.length=0;this.texts.length=0;}
}
