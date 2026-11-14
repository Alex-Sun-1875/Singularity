import {CompactMask as Mask} from '../../../shared/ui/CompactMask';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {Camera,Color,Graphics,Label,Node,Quat,Sorting2D,director} from 'cc';
import type {Hud} from '../../../app/Hud';
import type {GameSession,EnemyState} from '../../../core/GameSession';
import {bossKind,bossName,nearestBoss,BOSS_NOTICE_RANGE} from '../../combat/common/BossAwareness';
import type {JourneyGuidance} from '../../journey/common/JourneyGuide';
import {objectiveTarget,type ObjectiveTarget} from '../../journey/common/ObjectiveTarget';
import {AREAS} from '../../world/data/WorldData';
import {playableExits} from '../../journey/data/ChapterJourney';
import {LocalCartography as Chart} from './LocalCartography';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import type {FeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {UI_FRAME_GOLD} from '../../../shared/ui/UiChrome';

// These layers follow the chart mask and precede ordinary HUD and popup ink.
export const MINIMAP_RENDER_ORDER={frame:-40,toolBezel:-30} as const;

const position=(node:Node,x:number,y:number)=>{const p=node.position;if(p.x!==x||p.y!==y)node.setPosition(x,y);};

/** Native ellipse Mask clips the metre-based local chart, not a symbolic graph. */
export class MiniMap {
 private host:Node;private terrain:Node;private fog:Node;private pins:Graphics;private bossMarks:Graphics;private heading:Graphics;
 private journey:GameSession|null=null;
 private navigationRole:FeedbackRole='state.idle';
 setNavigationFeedback(role:FeedbackRole){this.navigationRole=role;}
 private guidance:JourneyGuidance|null=null;private guidancePin:{x:number;y:number;offscreen:boolean}|null=null;
 private area='';private updateClock=Infinity;private lastHeading=Infinity;private scale=1;private chartRadius=1;private worldRadius=28;
 private center={x:0,z:0};private playerClamped=false;
 private enemyPins:{id:string;x:number;y:number;boss:boolean}[]=[];
 private bossPins:{id:string;name:string;kind:string;distance:number;x:number;y:number;offscreen:boolean}[]=[];
 private bossContact:{id:string;name:string;kind:string;distance:number}|null=null;
 private objective:ObjectiveTarget|null=null;
 private chartProjection:Node;private chartBasis:Node;private directions:{node:Node;x:number;z:number}[]=[];
 private right={x:1,z:0};private up={x:0,z:1};private bearing=Infinity;private tilt=Infinity;
 private readonly cameraRotation=new Quat(0,0,0,0);
 private exitPins:{id:string;to:string;name:string;distance:number;x:number;y:number;offscreen:boolean;locked:boolean}[]=[];
 constructor(private hud:Hud,parent:Node,x:number,y:number,private size:number){
  this.host=hud.node('CircularMiniMap',parent,x,y,size,size);hud.circularHitArea(this.host,size);const r=size/2;this.chartRadius=size*.425; // Slightly underlap the fixed r216.5/512 bezel aperture.
  const viewport=hud.node('ChartCircle',this.host,0,0,this.chartRadius*2,this.chartRadius*2);viewport.addComponent(Mask).type=Mask.Type.GRAPHICS_ELLIPSE;
  const base=hud.node('ChartBackdrop',viewport,0,0,this.chartRadius*2,this.chartRadius*2).addComponent(CompactGraphics);base.fillColor=C.dark;base.circle(0,0,this.chartRadius);base.fill();
  this.chartProjection=hud.node('CameraGroundProjection',viewport);this.chartBasis=hud.node('CameraAlignedChart',this.chartProjection);this.chartBasis.setScale(1,-1,1);
  this.terrain=hud.node('MinimapTerrain',this.chartBasis);this.terrain.addComponent(CompactGraphics);this.fog=hud.node('ExplorationFog',this.chartBasis);this.fog.addComponent(CompactGraphics);this.pins=hud.node('MinimapPins',viewport).addComponent(CompactGraphics);
  this.heading=hud.node('PlayerHeading',viewport).addComponent(CompactGraphics);
  this.bossMarks=hud.node('BossRadarCrowns',viewport).addComponent(CompactGraphics);
  this.heading.node.setSiblingIndex(viewport.children.length-1); // Keep the player indicator above map contacts.
  // The wider shared-gold bezel contains its own carved vines around the clear chart aperture.
  const frame=UiSkin.asset(this.host,'unified-gold-ring-v16',size,size,false);frame.node.name='CompassGoldFrame';frame.node.addComponent(Sorting2D).sortingOrder=MINIMAP_RENDER_ORDER.frame;this.addDirections(r);
  this.host.on(Node.EventType.TOUCH_END,()=>{Chart.flush();hud.actions.click('map');});
 }
 private addDirections(r:number):void{
  const engraving=this.hud.node('CompassEngraving',this.host,0,0,this.size,this.size);
  for(const [i,title]of ['N','E','S','W'].entries()){
   const angle=i*Math.PI/2,cx=Math.sin(angle)*(r-10),cy=Math.cos(angle)*(r-10);
   const label=this.hud.text(engraving,title,cx,cy,16,10,UI_FRAME_GOLD.light,14);label.node.name='CompassDirection:'+title;label.fontFamily='Georgia';label.isBold=true;label.horizontalAlign=1;label.enableOutline=true;label.outlineWidth=1;label.outlineColor=C.dark;
   // Fixed glyphs can share the native dynamic atlas; SHRINK and styling stay intact.
   label.cacheMode=Label.CacheMode.BITMAP;label.node.addComponent(Sorting2D).sortingOrder=MINIMAP_RENDER_ORDER.frame;
   this.directions.push({node:label.node,x:Math.sin(angle),z:Math.cos(angle)});
  }
 }
 private project(x:number,z:number):{x:number;y:number}{return{x:x*this.right.x+z*this.right.z,y:x*this.up.x+z*this.up.z};}
 private orient(camera:Camera):void{
  const rotation=camera.node.worldRotation;if(Quat.strictEquals(rotation,this.cameraRotation))return;this.cameraRotation.set(rotation);
  const right=camera.node.right,up=camera.node.up,bearing=Math.atan2(right.z,right.x),tilt=Math.hypot(up.x,up.z);
  if(Math.abs(bearing-this.bearing)<.000001&&Math.abs(tilt-this.tilt)<.000001)return;
  this.bearing=bearing;this.tilt=tilt;this.right={x:right.x,z:right.z};this.up={x:up.x,z:up.z};
  // The world camera looks down with world Y upright. Reflect chart +Z, then
  // rotate into its ground bearing and apply the same foreshortening as the view.
  this.chartBasis.setRotationFromEuler(0,0,bearing*180/Math.PI);this.chartProjection.setScale(1,tilt,1);
  for(const direction of this.directions){const p=this.project(direction.x,direction.z),length=Math.hypot(p.x,p.y);direction.node.setPosition(p.x/length*(this.size/2-10),p.y/length*(this.size/2-10));}
 }
 // All chart projection, exploration checks and contact scans share a 200 ms budget.
 private updateDue(){this.updateClock+=director.getDeltaTime();if(this.updateClock+1e-6<.2)return false;this.updateClock=0;return true;}
 update(game:GameSession,camera:Camera,guide:JourneyGuidance|null=null):void{
  if(!this.updateDue())return;
  this.guidance=guide;
  const area=AREAS[game.state.area];if(!area)return;const p=game.state.player,changed=Chart.track(game),areaChanged=this.area!==area.id||this.journey!==game,oldBearing=this.bearing,oldTilt=this.tilt;this.journey=game;
  this.orient(camera);
  const projectionChanged=oldBearing!==this.bearing||oldTilt!==this.tilt,tilt=Math.max(.1,this.tilt);
  // Fit the shorter complete-map dimension to the aperture, compensating for
  // the ground projection. The longer dimension is cropped by the circle.
  const spanX=Math.hypot(this.right.x,this.up.x/(tilt*tilt)),spanZ=Math.hypot(this.right.z,this.up.z/(tilt*tilt));
  if(areaChanged||projectionChanged){
   this.area=area.id;const mapWidth=area.width/spanX,mapHeight=area.depth/spanZ;
   this.worldRadius=Math.max(.1,Math.min(mapWidth,mapHeight)/2);
   this.scale=this.chartRadius/this.worldRadius;const g=this.terrain.getComponent(Graphics)!;g.clear();Chart.drawTerrain(g,area,this.scale,0,0);
  }
  // Clamp the view at real region boundaries, rather than showing empty space
  // beyond the floor. Pins and the player arrow share this exact chart centre.
  const halfX=this.worldRadius*spanX,halfZ=this.worldRadius*spanZ;
  this.center.x=Math.max(-area.width/2+halfX,Math.min(area.width/2-halfX,p.x));this.center.z=Math.max(-area.depth/2+halfZ,Math.min(area.depth/2-halfZ,p.z));
  position(this.terrain,-this.center.x*this.scale,-this.center.z*this.scale);position(this.fog,-this.center.x*this.scale,-this.center.z*this.scale);
  const playerPoint=this.project(p.x-this.center.x,p.z-this.center.z),playerLength=Math.hypot(playerPoint.x,playerPoint.y)*this.scale,playerLimit=this.chartRadius-9;
  // At the extreme corner of a rectangular room, retain a visible player
  // indicator on the rim even when the covered circular view crops that corner.
  this.playerClamped=playerLength>playerLimit;const playerScale=this.playerClamped?playerLimit/playerLength:1;
  position(this.heading.node,playerPoint.x*this.scale*playerScale,playerPoint.y*this.scale*playerScale);
  // Exploration is static between newly revealed cells. Keep its existing GPU
  // geometry instead of tessellating the entire region on a repeating timer.
  // Show the whole regional basemap beneath a light unexplored shade. The full
  // map retains opaque fog and pins still use the original discovery records.
  if(changed||areaChanged||projectionChanged){const fog=this.fog.getComponent(Graphics)!;fog.clear();Chart.drawFog(fog,area,this.scale,0,0,game,.25);}
  this.drawPins(game);
  if(!areaChanged&&p.angle===this.lastHeading&&oldBearing===this.bearing&&oldTilt===this.tilt)return;this.lastHeading=p.angle;
  this.heading.clear();this.heading.fillColor=C.route;this.heading.strokeColor=C.ink;this.heading.lineWidth=1;
  const forward=this.project(Math.sin(p.angle),Math.cos(p.angle)),angle=Math.atan2(forward.x,forward.y),points=[[0,7],[-4,-5],[0,-3],[4,-5]].map(([x,y])=>({x:x*Math.cos(angle)+y*Math.sin(angle),y:-x*Math.sin(angle)+y*Math.cos(angle)}));this.heading.moveTo(points[0].x,points[0].y);for(const q of points.slice(1))this.heading.lineTo(q.x,q.y);this.heading.close();this.heading.fill();this.heading.stroke();
 }
 /** Cinematics freeze the chart projection, but a defeated contact must clear.
  * Avoid rebuilding terrain/fog while the cinematic camera is moving. */
 refreshContacts(game:GameSession){
  if(this.journey!==game||this.area!==game.state.area||!this.updateDue())return;
  const boss=nearestBoss(game),objective=objectiveTarget(game,this.guidance);
  if((boss?.id??'')!==(this.bossContact?.id??'')||(objective?.id??'')!==(this.objective?.id??'')||this.bossPins.some(pin=>!game.state.enemies.some(e=>e.id===pin.id&&e.hp>0)))this.drawPins(game);
 }
 private drawPins(game:GameSession):void{
  const a=AREAS[game.state.area],p=game.state.player,g=this.pins;g.clear();this.bossMarks.clear();this.exitPins=[];this.enemyPins=[];this.bossPins=[];this.bossContact=null;this.objective=objectiveTarget(game,this.guidance);
  const pin=(x:number,z:number,color:Color,quest=false)=>{const q=this.project(x-this.center.x,z-this.center.z),px=q.x*this.scale,py=q.y*this.scale;if(Math.hypot(px,py)>this.chartRadius-4)return;g.fillColor=color;g.strokeColor=C.dark;g.lineWidth=1;if(quest){g.moveTo(px,py+4);g.lineTo(px+4,py);g.lineTo(px,py-4);g.lineTo(px-4,py);g.close();}else g.circle(px,py,2.7);g.fill();g.stroke();};
  const guided=(exit:{id:string;x:number;z:number})=>this.objective?.type==='exit'&&exit.id===this.objective.id;
  const exits=playableExits(a).filter(exit=>guided(exit)||Chart.revealed(a.id,exit,game)).map(exit=>({exit,distance:Math.hypot(exit.x-p.x,exit.z-p.z)})).sort((u,v)=>Number(guided(v.exit))-Number(guided(u.exit))||u.distance-v.distance),placed:{x:number;y:number}[]=[];
  for(const [index,{exit,distance}]of exits.entries()){
   const q=this.project(exit.x-this.center.x,exit.z-this.center.z),dx=q.x*this.scale,dy=q.y*this.scale,length=Math.hypot(dx,dy),limit=this.chartRadius-13,offscreen=length>limit,angle=Math.atan2(dy,dx);
   let px=dx,py=dy;
   if(offscreen){
    // Keep the nearest revealed exit's bearing exact. Only crowded secondary
    // symbols step a little along the rim; their arrow still faces the exit.
    for(const offset of [0,.14,-.14,.28,-.28,.42,-.42]){px=Math.cos(angle+offset)*limit;py=Math.sin(angle+offset)*limit;if(!placed.some(q=>Math.hypot(q.x-px,q.y-py)<16))break;}
   }
   placed.push({x:px,y:py});const locked=!!game.exitRequirement(exit);this.exitPins.push({id:exit.id,to:exit.to,name:AREAS[exit.to]?.name??exit.label,distance,x:px,y:py,offscreen,locked});this.exitRune(g,px,py,index===0,locked);
   if(offscreen){const ux=Math.cos(angle),uy=Math.sin(angle),tx=px+ux*8.5,ty=py+uy*8.5;g.fillColor=locked?C.purple:C.route;g.strokeColor=new Color(16,11,26);g.lineWidth=1.5;g.moveTo(tx+ux*4,ty+uy*4);g.lineTo(tx-ux*2-uy*3,ty-uy*2+ux*3);g.lineTo(tx-ux*2+uy*3,ty-uy*2-ux*3);g.close();g.fill();g.stroke();}
  }
  const focus=nearestBoss(game);
  for(const o of a.objects){if(!game.interactionVisible(o)||!Chart.revealed(a.id,o,game)||['cache','inspect','locked_cache'].includes(o.action)&&!o.actor)continue;const kind=Chart.kind(o);if(kind==='place')continue;pin(o.x,o.z,kind==='npc'?C.green:C.gold,kind==='quest');}
  // Nearby hostiles are radar contacts, including behind cover and exploration
  // fog. Keep the terrain/loot fog intact and never reveal the whole area.
  for(const enemy of game.state.enemies){
   if(enemy.hp<=0||bossKind(enemy)||Math.hypot(enemy.x-p.x,enemy.z-p.z)>28)continue;
   const q=this.project(enemy.x-this.center.x,enemy.z-this.center.z),x=q.x*this.scale,y=q.y*this.scale,boss=!!enemy.bossId,radius=boss?6:4.5;
   if(Math.hypot(x,y)>this.chartRadius-radius-2)continue;
   this.enemyPins.push({id:enemy.id,x,y,boss});g.fillColor=C.red;g.strokeColor=C.dark;g.lineWidth=1.8;
   g.moveTo(x,y+radius);g.lineTo(x+radius,y);g.lineTo(x,y-radius);g.lineTo(x-radius,y);g.close();g.fill();g.stroke();
   if(boss){g.strokeColor=C.red;g.lineWidth=1.5;g.circle(x,y,radius+2.5);g.stroke();}
  }
  this.guidancePin=null;
  // Draw crowns last so quest/ordinary contacts cannot bury a nearby boss.
  // Clamped edge crowns retain a real bearing instead of vanishing at the mask.
  for(const enemy of game.state.enemies)if(enemy!==focus)this.drawBossPin(game,enemy);
  if(focus){
   this.drawBossPin(game,focus);const kind=bossKind(focus)!,distance=Math.hypot(focus.x-p.x,focus.z-p.z);
   this.bossContact={id:focus.id,name:bossName(focus),kind,distance};
  }
  this.bossMarks.node.active=this.bossPins.length>0;
  this.drawObjective();
 }
 // Task ink follows ordinary contacts in the same native Graphics; crowns
 // and the moving player indicator keep their existing higher render layers.
 private drawObjective(){
  const target=this.objective,g=this.pins;if(!target)return;
  const q=this.project(target.point.x-this.center.x,target.point.z-this.center.z),dx=q.x*this.scale,dy=q.y*this.scale,length=Math.hypot(dx,dy),limit=this.chartRadius-22,factor=length>limit?limit/length:1,x=dx*factor,y=dy*factor,offscreen=length>limit,role=target.blocked?'state.blocked':'map.task';
  const boss=this.bossPins.find(pin=>pin.id===target.id),px=boss?.x??x,py=boss?.y??y;this.guidancePin={x:px,y:py,offscreen:boss?.offscreen??offscreen};
  if(boss){
   F.ink(g,role,'stroke');g.lineWidth=2.5;for(const sx of [-1,1])for(const sy of [-1,1]){g.moveTo(px+sx*12,py+sy*18);g.lineTo(px+sx*18,py+sy*18);g.lineTo(px+sx*18,py+sy*12);}g.stroke();
  }else{
   F.ink(g,'text.outline','fill',235);g.circle(px,py,14);g.fill();F.ink(g,role,'stroke');g.lineWidth=2.5;g.circle(px,py,13);g.stroke();F.ink(g,role,'fill');
   g.moveTo(px-6,py-9);g.lineTo(px-6,py+9);g.lineTo(px+8,py+9);g.lineTo(px+3,py+2);g.lineTo(px-6,py+2);g.close();g.fill();g.stroke();
   if(offscreen&&length>0){const ux=dx/length,uy=dy/length,cx=x+ux*17,cy=y+uy*17;g.moveTo(cx+ux*3,cy+uy*3);g.lineTo(cx-ux*2-uy*3,cy-uy*2+ux*3);g.lineTo(cx-ux*2+uy*3,cy-uy*2-ux*3);g.close();g.fill();}
  }
 }
 private drawBossPin(game:GameSession,enemy:EnemyState){
  const kind=bossKind(enemy),p=game.state.player,distance=Math.hypot(enemy.x-p.x,enemy.z-p.z);
  if(!kind||enemy.hp<=0||p.hp<=0||distance>BOSS_NOTICE_RANGE)return;
  const q=this.project(enemy.x-this.center.x,enemy.z-this.center.z),dx=q.x*this.scale,dy=q.y*this.scale,length=Math.hypot(dx,dy),limit=this.chartRadius-21,factor=length>limit?limit/length:1,x=dx*factor,y=dy*factor,offscreen=length>limit,g=this.bossMarks,role=kind==='elite'?'identity.elite':'identity.boss';
  this.bossPins.push({id:enemy.id,name:bossName(enemy),kind,distance,x,y,offscreen});this.enemyPins.push({id:enemy.id,x,y,boss:true});
  F.ink(g,'text.outline','fill',235);g.circle(x,y,14);g.fill();F.ink(g,role,'stroke');g.lineWidth=2;g.circle(x,y,13);g.stroke();
  F.ink(g,role,'fill');F.ink(g,'text.outline','stroke');g.lineWidth=1.8;
  g.moveTo(x-10,y+5);g.lineTo(x-5,y);g.lineTo(x,y+9);g.lineTo(x+5,y);g.lineTo(x+10,y+5);g.lineTo(x+7,y-6);g.lineTo(x-7,y-6);g.close();g.fill();g.stroke();
  F.ink(g,'identity.enemy','fill');g.circle(x,y-2,2);g.fill();
  if(offscreen&&length>0){const ux=dx/length,uy=dy/length,cx=x+ux*16,cy=y+uy*16;F.ink(g,role,'fill');g.moveTo(cx+ux*3,cy+uy*3);g.lineTo(cx-ux*2-uy*3,cy-uy*2+ux*3);g.lineTo(cx-ux*2+uy*3,cy-uy*2-ux*3);g.close();g.fill();}
 }
 private exitRune(g:Graphics,x:number,y:number,primary:boolean,locked:boolean):void{
  const radius=primary?6.5:5.2,ink=new Color(16,11,26),cyan=locked?new Color(131,205,230,145):C.route,purple=locked?new Color(196,165,237,160):C.purple;
  g.strokeColor=ink;g.lineWidth=4;g.circle(x,y,radius);g.stroke();g.strokeColor=purple;g.lineWidth=1.6;g.circle(x,y,radius);g.stroke();
  g.strokeColor=cyan;g.fillColor=ink;g.lineWidth=1.5;g.moveTo(x,y+radius*.54);g.lineTo(x+radius*.46,y);g.lineTo(x,y-radius*.54);g.lineTo(x-radius*.46,y);g.close();g.fill();g.stroke();
  for(let i=0;i<4;i++){const angle=i*Math.PI/2;g.moveTo(x+Math.cos(angle)*(radius-1.1),y+Math.sin(angle)*(radius-1.1));g.lineTo(x+Math.cos(angle)*(radius+1.6),y+Math.sin(angle)*(radius+1.6));}g.stroke();
 }
 inspect(){return{area:this.area,guidance:this.guidance?{instruction:this.guidance.instruction,detail:this.guidance.detail,target:this.guidance.destination.area,point:this.guidance.point,pin:this.guidancePin}:null,revealedExits:this.exitPins.map(pin=>({...pin})),nearestExit:this.exitPins[0]?{...this.exitPins[0]}:null,objective:this.objective?{id:this.objective.id,type:this.objective.type,kind:this.objective.kind,name:this.objective.name,distance:this.objective.distance,blocked:this.objective.blocked,point:{x:this.objective.point.x,z:this.objective.point.z},combinedWithBoss:this.bossContact?.id===this.objective.id}:null,nearbyBoss:this.bossContact,bosses:this.bossPins.map(pin=>({...pin})),chartRadius:this.chartRadius,worldRadius:this.worldRadius,pixelsPerMetre:this.scale,center:{...this.center},playerClamped:this.playerClamped,enemies:this.enemyPins.map(pin=>({...pin}))};}
 destroy():void{Chart.flush();this.host.destroy();}
}
